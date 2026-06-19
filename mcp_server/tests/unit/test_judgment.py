# mcp_server/tests/unit/test_judgment.py

"""Unit tests for the IVD Judgment phase — engine + MCP-tool facade.

Pins the priority-1 invariants from the Judgment integration spec
and the architectural recommendations from the Judgment-vs-Canon
comparison (ivd/judgment_layer.md):

  judgment_engine_package_isolation
      → schema, store, freshness, detect, inject, validate live in
        ``ivd/judgment/``; the MCP-tool module is a thin facade.

  judgment_typed_artifacts_no_dict_drift
      → ledger entries, comparison pairs, patterns, recommendations,
        baselines all round-trip through @dataclass — runtime + filesystem
        cannot drift independently (the C-1 bug is impossible).

  judgment_engine_version_and_hash
      → Pattern.detection_hash and InjectionResult.injection_hash are
        deterministic and engine_version-stamped (R3, borrowed from Canon's
        AuditReport.hash).

  judgment_mcp_opt_out
      → IVD_JUDGMENT_TOOLS_ENABLED=false disables every judgment tool
        without de-registering them (R4, mirrors IVD_CANON_TOOLS_ENABLED).

  judgment_check_installed_no_writes
      → ivd_judgment_check_installed is read-only (R6, mirrors
        canon_check_rules_installed).

  judgment_activation_gate
      → All judgment tools are dormant unless ``.judgment/`` exists at the
        resolved project root.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Set
from unittest import mock

import pytest
import yaml

from judgment import (
    DEFAULT_HALF_LIFE_DAYS,
    DEPTH_WEIGHT,
    ENGINE_VERSION,
    JUDGMENT_DIRNAME,
    JUDGMENT_SUBDIRS,
    PATTERN_PROMOTION_THRESHOLD,
    Baseline,
    Classification,
    CodifiedFields,
    ComparisonPair,
    Freshness,
    JudgmentStore,
    LedgerEntry,
    Pattern,
    PatternMembership,
    Recommendation,
    age_days,
    detect_patterns,
    freshness_for,
    inject_context,
    slugify,
)
from judgment.schema import _now_iso, _today
from mcp_server.registry import TOOL_HANDLERS, call_tool, get_all_tools
from mcp_server.tools.judgment import (
    _OPT_OUT_ENV,
    _is_judgment_enabled,
    judgment_capture_tool,
    judgment_check_installed_tool,
    judgment_codify_tool,
    judgment_detect_patterns_tool,
    judgment_init_tool,
    judgment_inject_context_tool,
    judgment_pair_tool,
    judgment_propose_recommendation_tool,
    judgment_save_codified_tool,
)


JUDGMENT_TOOL_NAMES: Set[str] = {
    "ivd_judgment_init",
    "ivd_judgment_capture",
    "ivd_judgment_codify",
    "ivd_judgment_save_codified",
    "ivd_judgment_pair",
    "ivd_judgment_detect_patterns",
    "ivd_judgment_inject_context",
    "ivd_judgment_propose_recommendation",
    "ivd_judgment_check_installed",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A fresh, empty project root — no .judgment/ folder yet."""
    return tmp_path


@pytest.fixture
def initialized(project: Path) -> Path:
    """A project where ivd_judgment_init has already run for domain 't'."""
    judgment_init_tool(project_root_arg=str(project), domains=["t"])
    return project


# Module-level counter so successive _seed_codified calls inside a single test
# always produce unique entry IDs (otherwise capture+save would overwrite the
# previous codified entry on disk and the detect/inject layers would see only
# one member, defeating the test).
_SEED_COUNTER = {"n": 0}


def _seed_codified(
    project: Path,
    cause: str,
    fix: str = "fix the thing",
    fix_action: str = "prompt_patch",
    depth: str = "expert",
    raw_correction: str = None,
) -> str:
    """Capture + codify a single ledger entry. Returns the entry_id."""
    _SEED_COUNTER["n"] += 1
    raw = raw_correction or f"raw {cause} #{_SEED_COUNTER['n']}"
    cap = json.loads(
        judgment_capture_tool(
            raw_correction=raw, source="author_intuition", domain="t",
            project_root_arg=str(project),
        )
    )
    codified = {
        "codified": {
            "expected_result": "expected",
            "detected_via": "user_review",
            "diagnosed_cause": cause,
            "proposed_fix": fix,
            "fix_action_type": fix_action,
        },
        "domain_depth": depth,
    }
    judgment_save_codified_tool(
        entry_id=cap["entry_id"],
        codified_yaml=yaml.safe_dump(codified),
        project_root_arg=str(project),
    )
    return cap["entry_id"]


# ===========================================================================
# 1. Engine package isolation (R1)
# ===========================================================================

class TestJudgmentEnginePackageIsolation:
    """The judgment engine is its own importable package, mirroring ivd/canon/."""

    def test_engine_package_importable(self):
        import judgment
        assert hasattr(judgment, "__version__")
        assert judgment.__version__ == ENGINE_VERSION

    def test_engine_exports_all_artifact_dataclasses(self):
        import judgment
        for name in (
            "LedgerEntry", "ComparisonPair", "Pattern", "Baseline",
            "Recommendation", "Classification", "CodifiedFields",
            "InjectionResult", "PatternMembership",
        ):
            assert hasattr(judgment, name), (
                f"judgment package missing dataclass: {name}"
            )

    def test_engine_submodules_exist(self):
        """Six engine submodules: schema, store, freshness, detect, inject, validate."""
        engine_root = Path(__file__).parent.parent.parent.parent / "judgment"
        for sub in ("schema.py", "store.py", "freshness.py",
                    "detect.py", "inject.py", "validate.py", "__init__.py"):
            assert (engine_root / sub).is_file(), (
                f"Engine submodule missing: judgment/{sub}"
            )

    def test_mcp_facade_imports_engine_not_inline(self):
        """MCP-tool module should import from the engine package, not redefine."""
        facade = (
            Path(__file__).parent.parent.parent / "tools" / "judgment.py"
        )
        text = facade.read_text()
        # The thin-facade refactor must have meaningfully shrunk the file
        # (the original was 1,272 lines; we target ~25% reduction with
        # the long codify prompt template + per-tool docstrings preserved).
        assert facade.stat().st_size > 0
        line_count = len(text.splitlines())
        assert line_count < 1100, (
            f"mcp_server/tools/judgment.py is {line_count} lines — "
            "the thin-facade refactor (R1) should keep this under 1100."
        )
        # And it must import every core engine concept from the package.
        assert "from judgment import" in text, (
            "mcp_server/tools/judgment.py must import from the engine package"
        )
        # Plus a handful of borrowed-from-Canon names that prove the engine
        # actually owns the substance.
        for must in ("JudgmentStore", "Pattern", "detect_patterns",
                     "inject_context", "ENGINE_VERSION"):
            assert must in text, (
                f"Facade must use the engine concept {must!r} — found inline "
                "implementation instead?"
            )


# ===========================================================================
# 2. Typed artifacts — no dict drift (R2)
# ===========================================================================

class TestJudgmentTypedArtifactsRoundTrip:
    """Every on-disk artifact round-trips losslessly through its dataclass."""

    def test_ledger_entry_round_trip(self):
        entry = LedgerEntry(
            id="2026-04-24_test",
            created="2026-04-24T20:00:00Z",
            state="codified",
            classification=Classification(
                type="regression", source="author_intuition", domain="gaming",
                agent="g", model="m", scope="s",
            ),
            raw_correction="raw text",
            domain_depth="expert",
            originated_from_tool="some_tool",
            codified=CodifiedFields(
                expected_result="ok", detected_via="user_review",
                diagnosed_cause="x", proposed_fix="y",
                fix_action_type="prompt_patch",
            ),
        )
        d = entry.to_dict()
        rt = LedgerEntry.from_dict(d)
        assert rt.id == entry.id
        assert rt.classification.domain == "gaming"
        assert rt.codified.fix_action_type == "prompt_patch"

    def test_capability_addition_requires_subtype_round_trip(self):
        entry = LedgerEntry(
            id="x", created=_now_iso(), state="codified",
            classification=Classification(domain="t"),
            raw_correction="r",
            codified=CodifiedFields(
                expected_result="ok", detected_via="user_review",
                diagnosed_cause="x", proposed_fix="y",
                fix_action_type="capability_addition",
                capability_subtype="build",
            ),
        )
        rt = LedgerEntry.from_dict(entry.to_dict())
        assert rt.codified.capability_subtype == "build"

    def test_comparison_pair_round_trip(self):
        pair = ComparisonPair(
            id="2026-04-24_pair",
            created=_now_iso(),
            state="paired",
            classification=Classification(type="comparison_pair", domain="t"),
            run_a={"ref": "a"}, run_b={"ref": "b"},
            observed_differences=["d1"],
            diagnostic_hypotheses=[
                {"hypothesis": "h", "competing_hypotheses": ["c"]}
            ],
        )
        rt = ComparisonPair.from_dict(pair.to_dict())
        assert rt.observed_differences == ["d1"]
        assert rt.diagnostic_hypotheses[0]["competing_hypotheses"] == ["c"]
        assert rt.injection_status == "plausible"

    def test_baseline_round_trip(self):
        bl = Baseline(domain_id="t", created=_now_iso(), updated=_now_iso())
        bl.goal_calibration["measurable"] = ["one", "two"]
        rt = Baseline.from_dict(bl.to_dict())
        assert rt.domain_id == "t"
        assert rt.goal_calibration["measurable"] == ["one", "two"]
        assert rt.half_life_days() == DEFAULT_HALF_LIFE_DAYS

    def test_pattern_round_trip_preserves_hash(self):
        p = Pattern(
            id="t__x", created=_now_iso(), updated=_now_iso(), domain="t",
            diagnosed_cause="c", recommended_fix="f",
            fix_action_type="prompt_patch",
            members=["a", "b", "c"], member_count=3,
            weighted_confidence=0.9, half_life_days=90,
        )
        p.stamp_hash()
        h = p.detection_hash
        rt = Pattern.from_dict(p.to_dict())
        assert rt.detection_hash == h
        assert rt.compute_hash() == h

    def test_recommendation_round_trip(self):
        rec = Recommendation(
            id="r", created=_now_iso(), state="draft",
            source_pattern="p", pattern_summary={"domain": "t"},
            fix_action_type="prompt_patch",
        )
        rt = Recommendation.from_dict(rec.to_dict())
        assert rt.source_pattern == "p"
        assert rt.engine_version == ENGINE_VERSION


# ===========================================================================
# 3. Deterministic engine_version + hash (R3)
# ===========================================================================

class TestJudgmentEngineVersionAndHash:
    """Pattern.detection_hash and InjectionResult.injection_hash are deterministic."""

    def test_pattern_hash_is_deterministic(self):
        p1 = Pattern(
            id="t__x", created="c1", updated="u1", domain="t",
            diagnosed_cause="cause", recommended_fix="fix",
            fix_action_type="prompt_patch",
            members=["a", "b", "c"], member_count=3,
            weighted_confidence=0.7, half_life_days=90,
        )
        p2 = Pattern(
            id="t__x", created="c2", updated="u2", domain="t",
            diagnosed_cause="cause", recommended_fix="fix",
            fix_action_type="prompt_patch",
            members=["c", "b", "a"],  # order should not matter
            member_count=3, weighted_confidence=0.7, half_life_days=90,
        )
        assert p1.compute_hash() == p2.compute_hash()

    def test_pattern_hash_changes_with_canonical_field(self):
        base = Pattern(
            id="t__x", created="c", updated="u", domain="t",
            diagnosed_cause="cause", recommended_fix="fix",
            fix_action_type="prompt_patch",
            members=["a"], member_count=1,
            weighted_confidence=0.7, half_life_days=90,
        )
        h_orig = base.compute_hash()
        base.diagnosed_cause = "different"
        assert base.compute_hash() != h_orig

    def test_pattern_engine_version_stamped(self, initialized: Path):
        for i in range(PATTERN_PROMOTION_THRESHOLD):
            _seed_codified(initialized, cause="same cause")
        out = json.loads(judgment_detect_patterns_tool(project_root_arg=str(initialized)))
        assert out["engine_version"] == ENGINE_VERSION
        for p in out["promoted_patterns"]:
            assert p["engine_version"] == ENGINE_VERSION
            assert isinstance(p["detection_hash"], str) and len(p["detection_hash"]) == 64

    def test_inject_context_hash_is_deterministic(self, initialized: Path):
        for i in range(PATTERN_PROMOTION_THRESHOLD):
            _seed_codified(initialized, cause="same cause", raw_correction=f"raw{i}")
        judgment_detect_patterns_tool(project_root_arg=str(initialized))
        a = json.loads(judgment_inject_context_tool(project_root_arg=str(initialized)))
        b = json.loads(judgment_inject_context_tool(project_root_arg=str(initialized)))
        assert a["injection_hash"] == b["injection_hash"]
        assert a["engine_version"] == ENGINE_VERSION


# ===========================================================================
# 4. Server-level opt-out (R4)
# ===========================================================================

class TestJudgmentMcpOptOut:
    """IVD_JUDGMENT_TOOLS_ENABLED=false is the single Judgment opt-out knob."""

    def test_default_is_enabled(self, monkeypatch):
        monkeypatch.delenv(_OPT_OUT_ENV, raising=False)
        assert _is_judgment_enabled() is True

    @pytest.mark.parametrize("val", ["false", "FALSE", "0", "no", "off", "OFF"])
    def test_opt_out_disables_every_judgment_tool(
        self, monkeypatch, val: str, tmp_path: Path
    ):
        monkeypatch.setenv(_OPT_OUT_ENV, val)
        outs = [
            json.loads(judgment_init_tool(project_root_arg=str(tmp_path))),
            json.loads(judgment_capture_tool(
                raw_correction="r", domain="t", project_root_arg=str(tmp_path)
            )),
            json.loads(judgment_codify_tool(
                entry_id="x", project_root_arg=str(tmp_path)
            )),
            json.loads(judgment_save_codified_tool(
                entry_id="x", codified_yaml="codified: {}",
                project_root_arg=str(tmp_path),
            )),
            json.loads(judgment_pair_tool(
                domain="t", run_a={}, run_b={},
                observed_differences=["d"],
                diagnostic_hypotheses=[{"hypothesis": "h", "competing_hypotheses": ["c"]}],
                project_root_arg=str(tmp_path),
            )),
            json.loads(judgment_detect_patterns_tool(project_root_arg=str(tmp_path))),
            json.loads(judgment_inject_context_tool(project_root_arg=str(tmp_path))),
            json.loads(judgment_propose_recommendation_tool(
                pattern_id="x", project_root_arg=str(tmp_path)
            )),
            json.loads(judgment_check_installed_tool(project_root_arg=str(tmp_path))),
        ]
        for out in outs:
            assert out.get("enabled") is False, (
                f"Tool should be disabled when {_OPT_OUT_ENV}={val} but got: {out}"
            )

    def test_opt_out_does_not_unregister_tools(self, monkeypatch):
        """Tool catalogue must remain ABI-stable across the opt-out flip."""
        monkeypatch.setenv(_OPT_OUT_ENV, "false")
        names = {t.name for t in get_all_tools()}
        for name in JUDGMENT_TOOL_NAMES:
            assert name in names, (
                f"{name} must remain registered when opt-out is set "
                "(opt-out toggles behavior, not registration)"
            )


# ===========================================================================
# 5. Activation gate (.judgment/ folder)
# ===========================================================================

class TestJudgmentActivationGate:
    """All tools (except init / check_installed) are dormant without ``.judgment/``."""

    def test_capture_dormant_without_judgment_folder(self, project: Path):
        out = json.loads(judgment_capture_tool(
            raw_correction="r", domain="t", project_root_arg=str(project)
        ))
        assert out["status"] == "dormant"
        assert "ivd_judgment_init" in out["activation"]["tool"]

    def test_detect_patterns_dormant_without_judgment_folder(self, project: Path):
        out = json.loads(judgment_detect_patterns_tool(project_root_arg=str(project)))
        assert out["status"] == "dormant"

    def test_inject_context_dormant_without_judgment_folder(self, project: Path):
        out = json.loads(judgment_inject_context_tool(project_root_arg=str(project)))
        assert out["status"] == "dormant"

    def test_init_creates_full_folder_layout(self, project: Path):
        judgment_init_tool(project_root_arg=str(project), domains=["t"])
        jroot = project / JUDGMENT_DIRNAME
        for sub in JUDGMENT_SUBDIRS:
            assert (jroot / sub).is_dir(), f"Missing subdir: {sub}"
        assert (jroot / "config.yaml").is_file()
        assert (jroot / "baselines" / "t_baseline.yaml").is_file()

    def test_init_is_idempotent(self, project: Path):
        first = json.loads(judgment_init_tool(project_root_arg=str(project)))
        second = json.loads(judgment_init_tool(project_root_arg=str(project)))
        assert first["ok"] and second["ok"]
        # Second run should not double-create anything.
        for path in second["created"]:
            assert path.startswith(JUDGMENT_DIRNAME), path
        # config.yaml should be in already_present on the second run.
        assert any("config.yaml" in p for p in second["already_present"])


# ===========================================================================
# 6. End-to-end loop (capture → codify → detect → inject → recommend)
# ===========================================================================

class TestJudgmentEndToEndLoop:

    def test_capture_then_codify_transitions_state(self, initialized: Path):
        cap = json.loads(judgment_capture_tool(
            raw_correction="bug here", domain="t",
            project_root_arg=str(initialized),
        ))
        assert cap["state"] == "raw"
        codified = {
            "codified": {
                "expected_result": "ok", "detected_via": "user_review",
                "diagnosed_cause": "x", "proposed_fix": "y",
                "fix_action_type": "prompt_patch",
            },
        }
        sav = json.loads(judgment_save_codified_tool(
            entry_id=cap["entry_id"],
            codified_yaml=yaml.safe_dump(codified),
            project_root_arg=str(initialized),
        ))
        assert sav["state"] == "codified"
        assert (initialized / JUDGMENT_DIRNAME / "ledger" / "codified" /
                f"{cap['entry_id']}.yaml").is_file()
        assert not (initialized / JUDGMENT_DIRNAME / "ledger" / "raw" /
                    f"{cap['entry_id']}.yaml").is_file()

    def test_save_codified_rejects_invalid_fix_action_type(self, initialized: Path):
        cap = json.loads(judgment_capture_tool(
            raw_correction="bad", domain="t",
            project_root_arg=str(initialized),
        ))
        bad = {
            "codified": {
                "expected_result": "ok", "detected_via": "user_review",
                "diagnosed_cause": "x", "proposed_fix": "y",
                "fix_action_type": "MAGIC",
            },
        }
        out = json.loads(judgment_save_codified_tool(
            entry_id=cap["entry_id"],
            codified_yaml=yaml.safe_dump(bad),
            project_root_arg=str(initialized),
        ))
        assert out["ok"] is False
        assert any("fix_action_type" in e for e in out["errors"])

    def test_capability_addition_requires_subtype(self, initialized: Path):
        cap = json.loads(judgment_capture_tool(
            raw_correction="cap", domain="t",
            project_root_arg=str(initialized),
        ))
        bad = {
            "codified": {
                "expected_result": "ok", "detected_via": "user_review",
                "diagnosed_cause": "x", "proposed_fix": "y",
                "fix_action_type": "capability_addition",
                # NB: missing capability_subtype
            },
        }
        out = json.loads(judgment_save_codified_tool(
            entry_id=cap["entry_id"],
            codified_yaml=yaml.safe_dump(bad),
            project_root_arg=str(initialized),
        ))
        assert out["ok"] is False
        assert any("capability_subtype" in e for e in out["errors"])

    def test_detect_patterns_promotes_at_threshold(self, initialized: Path):
        for i in range(PATTERN_PROMOTION_THRESHOLD):
            _seed_codified(initialized, cause="root cause Z", raw_correction=f"r{i}")
        out = json.loads(judgment_detect_patterns_tool(project_root_arg=str(initialized)))
        assert len(out["promoted_patterns"]) == 1
        p = out["promoted_patterns"][0]
        assert p["member_count"] == PATTERN_PROMOTION_THRESHOLD
        assert p["freshness"] in ("fresh", "aging")

    def test_detect_patterns_does_not_promote_below_threshold(
        self, initialized: Path
    ):
        for i in range(PATTERN_PROMOTION_THRESHOLD - 1):
            _seed_codified(initialized, cause="root cause", raw_correction=f"r{i}")
        out = json.loads(judgment_detect_patterns_tool(project_root_arg=str(initialized)))
        assert out["promoted_patterns"] == []
        assert len(out["skipped_clusters"]) >= 1

    def test_inject_context_returns_promoted_patterns(self, initialized: Path):
        for i in range(PATTERN_PROMOTION_THRESHOLD):
            _seed_codified(initialized, cause="root cause", raw_correction=f"r{i}")
        judgment_detect_patterns_tool(project_root_arg=str(initialized))
        out = json.loads(judgment_inject_context_tool(
            project_root_arg=str(initialized), domain="t"
        ))
        assert out["domain_filter"] == "t"
        assert len(out["context"]["patterns"]) == 1
        assert out["context"]["patterns"][0]["weighted_confidence"] >= 0.5

    def test_inject_context_echoes_task_type(self, initialized: Path):
        out = json.loads(judgment_inject_context_tool(
            project_root_arg=str(initialized), task_type="generate-script"
        ))
        assert out["task_type"] == "generate-script"

    def test_propose_recommendation_emits_draft_recipe(self, initialized: Path):
        for i in range(PATTERN_PROMOTION_THRESHOLD):
            _seed_codified(initialized, cause="rc", raw_correction=f"r{i}")
        det = json.loads(judgment_detect_patterns_tool(project_root_arg=str(initialized)))
        pid = det["promoted_patterns"][0]["pattern_id"]
        rec = json.loads(judgment_propose_recommendation_tool(
            pattern_id=pid, project_root_arg=str(initialized)
        ))
        assert rec["fix_action_type"] == "prompt_patch"
        assert rec["draft_recipe_yaml"] is not None
        assert rec["awaiting"] == "user_approval"


# ===========================================================================
# 7. ivd_judgment_pair (Pearl Rung-1 discipline)
# ===========================================================================

class TestJudgmentPairRungOneDiscipline:
    """Rung-1: every diagnostic_hypothesis MUST list ≥1 competing_hypothesis."""

    def test_pair_rejects_hypothesis_without_competing(self, initialized: Path):
        out = json.loads(judgment_pair_tool(
            domain="t",
            run_a={"ref": "a"}, run_b={"ref": "b"},
            observed_differences=["d"],
            diagnostic_hypotheses=[{"hypothesis": "h"}],  # no competing
            project_root_arg=str(initialized),
        ))
        assert out["ok"] is False
        assert any("competing_hypotheses" in e for e in out["errors"])

    def test_pair_accepts_hypothesis_with_competing(self, initialized: Path):
        out = json.loads(judgment_pair_tool(
            domain="t",
            run_a={"ref": "a"}, run_b={"ref": "b"},
            observed_differences=["d"],
            diagnostic_hypotheses=[
                {"hypothesis": "h", "competing_hypotheses": ["c1", "c2"]}
            ],
            project_root_arg=str(initialized),
        ))
        assert out["ok"] is True
        assert out["state"] == "paired"
        assert out["injection_status"] == "plausible"


# ===========================================================================
# 8. Freshness math
# ===========================================================================

class TestFreshnessMath:

    def test_freshness_thresholds(self):
        assert freshness_for(None, 90) == "fresh"
        assert freshness_for(0, 90) == "fresh"
        assert freshness_for(89, 90) == "fresh"
        assert freshness_for(91, 90) == "aging"
        assert freshness_for(180, 90) == "aging"
        assert freshness_for(181, 90) == "stale"
        assert freshness_for(270, 90) == "stale"
        assert freshness_for(271, 90) == "expired"
        assert freshness_for(1_000, 90) == "expired"

    def test_age_days_handles_iso_and_date_only(self):
        assert age_days(None) is None
        assert age_days("garbage") is None
        assert age_days("2026-01-01") is not None
        assert age_days("2026-01-01T00:00:00Z") is not None

    def test_propose_recommendation_rejects_expired_pattern(self, initialized: Path):
        # Build a pattern manifest with a forced "expired" freshness on disk
        # and confirm the recommender refuses to act on it.
        for i in range(PATTERN_PROMOTION_THRESHOLD):
            _seed_codified(initialized, cause="rc")
        det = json.loads(judgment_detect_patterns_tool(project_root_arg=str(initialized)))
        pid = det["promoted_patterns"][0]["pattern_id"]
        ppath = initialized / JUDGMENT_DIRNAME / "patterns" / f"{pid}.yaml"
        data = yaml.safe_load(ppath.read_text())
        data["freshness"] = "expired"
        ppath.write_text(yaml.safe_dump(data, sort_keys=False))
        out = json.loads(judgment_propose_recommendation_tool(
            pattern_id=pid, project_root_arg=str(initialized)
        ))
        assert out["ok"] is False
        assert "expired" in out["error"]


# ===========================================================================
# 9. ivd_judgment_check_installed (R6 — workspace-level visibility)
# ===========================================================================

class TestJudgmentCheckInstalledNoWrites:
    """The check tool NEVER writes to disk. Mirrors canon_check_rules_installed."""

    def test_no_writes_when_inactive(self, project: Path):
        writes: List[str] = []
        real_write = Path.write_text
        real_mkdir = Path.mkdir
        real_open = open

        def track_write(self, *a, **kw):
            writes.append(f"write_text:{self}")
            return real_write(self, *a, **kw)

        def track_mkdir(self, *a, **kw):
            writes.append(f"mkdir:{self}")
            return real_mkdir(self, *a, **kw)

        def track_open(path, mode="r", *a, **kw):
            if any(m in mode for m in ("w", "a", "x", "+")):
                writes.append(f"open:{path}:{mode}")
            return real_open(path, mode, *a, **kw)

        with mock.patch.object(Path, "write_text", track_write), \
             mock.patch.object(Path, "mkdir", track_mkdir), \
             mock.patch("builtins.open", track_open):
            judgment_check_installed_tool(project_root_arg=str(project))

        sandbox_writes = [w for w in writes if str(project) in w]
        assert not sandbox_writes, (
            f"check_installed performed file writes: {sandbox_writes}"
        )

    def test_project_mode_reports_inactive(self, project: Path):
        out = json.loads(judgment_check_installed_tool(project_root_arg=str(project)))
        assert out["scope"] == "project"
        assert out["projects"][0]["activated"] is False
        assert "Run ivd_judgment_init" in out["next_step"]

    def test_project_mode_reports_active_with_counts(self, initialized: Path):
        # Seed enough to promote one pattern so counts are non-trivial.
        for i in range(PATTERN_PROMOTION_THRESHOLD):
            _seed_codified(initialized, cause="rc", raw_correction=f"r{i}")
        judgment_detect_patterns_tool(project_root_arg=str(initialized))
        out = json.loads(judgment_check_installed_tool(project_root_arg=str(initialized)))
        proj = out["projects"][0]
        assert proj["activated"] is True
        assert proj["engine_version"] == ENGINE_VERSION
        assert proj["pattern_count"] == 1
        assert "t" in proj["domains"]
        assert sum(proj["ledger_counts"].values()) >= PATTERN_PROMOTION_THRESHOLD

    def test_workspace_mode_finds_activated_projects(self, tmp_path: Path):
        # tmp_path/
        #   a/  (activated)
        #   b/  (not activated)
        a = tmp_path / "a"; a.mkdir()
        b = tmp_path / "b"; b.mkdir()
        judgment_init_tool(project_root_arg=str(a), domains=["g"])
        out = json.loads(judgment_check_installed_tool(workspace_root=str(tmp_path)))
        assert out["scope"] == "workspace"
        assert out["summary"]["projects_scanned"] == 1
        assert out["summary"]["projects_activated"] == 1
        names = [p["project_root"] for p in out["projects"]]
        assert any(str(a) in n for n in names)


# ===========================================================================
# 10. Tool registration & MCP surface
# ===========================================================================

class TestJudgmentMcpSurface:

    def test_all_nine_tools_registered(self):
        names = {t.name for t in get_all_tools()}
        missing = JUDGMENT_TOOL_NAMES - names
        assert not missing, f"Judgment tools missing from registry: {missing}"

    def test_each_judgment_tool_has_handler(self):
        for name in JUDGMENT_TOOL_NAMES:
            assert name in TOOL_HANDLERS, f"No handler for {name}"

    def test_each_judgment_tool_has_input_schema(self):
        tools = {t.name: t for t in get_all_tools()}
        for name in JUDGMENT_TOOL_NAMES:
            tool = tools[name]
            assert tool.inputSchema is not None
            assert tool.inputSchema.get("type") == "object"

    def test_call_tool_dispatches_check_installed(self, tmp_path: Path):
        out = call_tool(
            "ivd_judgment_check_installed",
            {"project_root": str(tmp_path)},
        )
        payload = json.loads(out)
        assert payload["tool"] == "ivd_judgment_check_installed"


# ===========================================================================
# 11. Validators (judgment-phase artifact types)
# ===========================================================================

class TestJudgmentValidators:

    def test_validator_registry_exposes_all_four_types(self):
        from judgment import VALIDATORS
        for t in ("baseline", "ledger_entry", "comparison_pair", "pattern"):
            assert t in VALIDATORS

    def test_baseline_validator_flags_missing_required_fields(self):
        from judgment import validate_baseline
        errs, warns = validate_baseline({})
        assert any("domain_id" in e for e in errs)

    def test_ledger_entry_validator_flags_invalid_fix_action_type(self):
        from judgment import validate_ledger_entry
        errs, warns = validate_ledger_entry({
            "id": "x", "state": "codified", "classification": {"domain": "t"},
            "codified": {
                "expected_result": "x", "detected_via": "x",
                "diagnosed_cause": "x", "proposed_fix": "x",
                "fix_action_type": "MAGIC",
            },
        })
        assert any("fix_action_type" in w for w in warns)

    def test_comparison_pair_validator_demands_competing_hypotheses(self):
        from judgment import validate_comparison_pair
        errs, warns = validate_comparison_pair({
            "id": "x", "run_a": {}, "run_b": {},
            "observed_differences": ["d"],
            "diagnostic_hypotheses": [{"hypothesis": "h"}],
        })
        assert any("competing_hypotheses" in w for w in warns)

    def test_pattern_validator_warns_below_promotion_threshold(self):
        from judgment import validate_pattern
        errs, warns = validate_pattern({
            "id": "p", "domain": "t", "diagnosed_cause": "c",
            "members": ["a"], "member_count": 1, "weighted_confidence": 0.7,
        })
        assert any("promotion threshold" in w for w in warns)


# ===========================================================================
# 12. IVD repo self-activation gate
# ===========================================================================

class TestJudgmentIVDRepoActivation:
    """Verify that the IVD framework repository itself has the Judgment phase
    activated (i.e., .judgment/ exists at the repo root).

    Self-activation gate: the IVD framework repository must have the Judgment phase
    activated (i.e., .judgment/ exists at the repo root).

    The IVD repo previously had not bootstrapped the Judgment loop — it could capture
    corrections about client projects but not about its own engine. This class guards
    against regressing that state.

    If this test fails it means .judgment/ was deleted from the IVD repo root.
    Fix: run ivd_judgment_init with project_root pointing at the IVD repo.
    """

    _IVD_ROOT = Path(__file__).parents[3]  # ivd/mcp_server/tests/unit → ivd/

    def test_judgment_directory_exists_at_ivd_root(self):
        judgment_dir = self._IVD_ROOT / ".judgment"
        assert judgment_dir.is_dir(), (
            f".judgment/ not found at {self._IVD_ROOT}. "
            "Run: ivd_judgment_init with project_root=<ivd_repo_root>"
        )

    def test_judgment_config_is_valid_yaml(self):
        config_path = self._IVD_ROOT / ".judgment" / "config.yaml"
        assert config_path.is_file(), ".judgment/config.yaml missing"
        import yaml
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        assert cfg.get("judgment_phase", {}).get("version") == "1.0", (
            "config.yaml judgment_phase.version must be '1.0'"
        )

    def test_judgment_check_installed_reports_activated_for_ivd_root(self):
        """ivd_judgment_check_installed must return at least one entry with
        activated=true when asked about the IVD repo root."""
        out = call_tool(
            "ivd_judgment_check_installed",
            {"project_root": str(self._IVD_ROOT)},
        )
        payload = json.loads(out)
        assert payload["tool"] == "ivd_judgment_check_installed"
        projects = payload.get("projects", [])
        assert any(p.get("activated") for p in projects), (
            f"No activated Judgment project found for IVD root. "
            f"Got: {json.dumps(projects, indent=2)}"
        )
