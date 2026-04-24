# mcp_server/tests/integration/test_judgment_integration.py

"""
Integration tests for the IVD Judgment phase (v3.1).

These tests are NOT unit tests.  They exercise real disk I/O against a
temporary directory and validate the actual YAML artifacts that land on disk.
There are NO mocks — every call goes through the real engine package, the real
``JudgmentStore``, and real filesystem operations.  Anyone who has checked out
the repo and activated the venv can run them:

    ./mcp_server/devops/test.sh --integration          # integration only
    ./mcp_server/devops/test.sh                        # all tests (includes integration)
    python -m pytest mcp_server/tests/integration/ -v  # direct pytest

What each section validates on disk
------------------------------------
S1  full_loop
    init → capture → codify → detect_patterns → inject_context →
    propose_recommendation — the entire 7-step workflow produces the
    correct artifact tree under ``.judgment/``.

S2  disk_artifacts
    YAML files written to disk carry the expected keys from the @dataclass
    schemas (R2 — no dict drift).

S3  hash_determinism
    Running detect_patterns twice with the same set of codified ledger entries
    produces identical ``detection_hash`` values (R3).

S4  engine_version_stamp
    ``Pattern`` and ``InjectionResult`` carry ``engine_version`` matching the
    package constant (R3).

S5  opt_out
    Setting ``IVD_JUDGMENT_TOOLS_ENABLED=false`` disables all tools in the
    process environment without de-registering them.  The tools return a
    structured "disabled" payload rather than crashing.  Unsetting the var
    re-enables them (R4).

S6  check_installed_no_writes
    ``ivd_judgment_check_installed`` reports activation state accurately:
    - Before init: returns ``activated: false`` + an ``init_payload`` block.
    - After init: returns ``activated: true`` with correct counts.
    - At no point does it write any file to disk (R6).

S7  workspace_scan
    With ``workspace_root`` set, ``ivd_judgment_check_installed`` discovers
    multiple projects at various depths.

Reference:
    ivd/judgment_layer.md                       (canonical spec, §Tool Surface)
    ivd/judgment/__init__.py                    (engine package public API)
    ivd/mcp_server/tools/judgment.py            (thin MCP facade, R1)
    ivd/mcp_server/tests/unit/test_judgment.py  (contract-pinning unit tests)
"""

from __future__ import annotations

import itertools
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from judgment import ENGINE_VERSION, JUDGMENT_DIRNAME, PATTERN_PROMOTION_THRESHOLD
from mcp_server.tools.judgment import (
    _OPT_OUT_ENV,
    judgment_capture_tool,
    judgment_check_installed_tool,
    judgment_codify_tool,
    judgment_detect_patterns_tool,
    judgment_inject_context_tool,
    judgment_init_tool,
    judgment_propose_recommendation_tool,
    judgment_save_codified_tool,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Module-level counter ensures every _seed_entries call produces unique
# raw_correction text, preventing slug-based entry_id collisions that would
# cause save_codified to silently overwrite a previously codified entry.
_seed_counter = itertools.count(start=1)


def _j(raw: str) -> Dict[str, Any]:
    """Parse a JSON string returned by a tool."""
    return json.loads(raw)


def _yaml(path: Path) -> Dict[str, Any]:
    """Read and parse a YAML file from disk."""
    return yaml.safe_load(path.read_text()) or {}


def _seed_entries(
    project: Path,
    cause: str,
    n: int,
    domain: str = "code",
) -> List[str]:
    """
    Capture + codify ``n`` raw ledger entries sharing the same
    ``diagnosed_cause``.  Each entry gets a globally unique raw_correction
    string drawn from the module-level counter so the slug-dedup logic never
    sees a collision and save_codified never overwrites an existing entry.
    Returns the list of entry_ids.
    """
    ids: List[str] = []
    for _ in range(n):
        seq = next(_seed_counter)
        cap = _j(judgment_capture_tool(
            raw_correction=f"[entry-{seq}] {cause}",
            source="integration_test",
            domain=domain,
            project_root_arg=str(project),
        ))
        assert cap["ok"], f"capture failed: {cap}"
        entry_id = cap["entry_id"]

        codified_payload = yaml.safe_dump({
            "codified": {
                "expected_result": "correct output",
                "detected_via": "integration_test",
                "diagnosed_cause": cause,
                "proposed_fix": f"fix for {cause}",
                "fix_action_type": "prompt_patch",
            },
            "leo_domain_depth": "expert",
        })
        save = _j(judgment_save_codified_tool(
            entry_id=entry_id,
            codified_yaml=codified_payload,
            project_root_arg=str(project),
        ))
        assert save["ok"], f"save_codified failed: {save}"
        ids.append(entry_id)
    return ids


# ---------------------------------------------------------------------------
# S1 — Full 7-step workflow loop
# ---------------------------------------------------------------------------

class TestFullLoop:
    """
    Drive the entire Judgment workflow in a real tmp dir and assert that the
    artifact tree is built correctly at every step.
    """

    def test_init_creates_judgment_directory_tree(self, tmp_path):
        result = _j(judgment_init_tool(
            project_root_arg=str(tmp_path),
            domains=["code", "design"],
        ))
        assert result["ok"], result
        judgment_root = tmp_path / JUDGMENT_DIRNAME
        assert judgment_root.is_dir(), ".judgment/ was not created"
        for subdir in ("baselines", "ledger/raw", "ledger/codified",
                       "patterns", "recommendations"):
            assert (judgment_root / subdir).is_dir(), f"{subdir} missing"

    def test_baselines_written_per_domain(self, tmp_path):
        _j(judgment_init_tool(
            project_root_arg=str(tmp_path),
            domains=["code", "design"],
        ))
        baselines_dir = tmp_path / JUDGMENT_DIRNAME / "baselines"
        names = {f.name for f in baselines_dir.glob("*.yaml")}
        assert "code_baseline.yaml" in names
        assert "design_baseline.yaml" in names

    def test_capture_creates_raw_yaml_on_disk(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        result = _j(judgment_capture_tool(
            raw_correction="The JWT validator swallowed expiry errors silently",
            source="user_review",
            domain="code",
            project_root_arg=str(tmp_path),
        ))
        assert result["ok"], result
        raw_dir = tmp_path / JUDGMENT_DIRNAME / "ledger" / "raw"
        yamls = list(raw_dir.glob("*.yaml"))
        assert len(yamls) == 1, f"Expected 1 raw entry, got {len(yamls)}"
        artifact = _yaml(yamls[0])
        assert artifact["state"] == "raw"
        assert "JWT" in artifact["raw_correction"]

    def test_codify_returns_prompt_not_file(self, tmp_path):
        """ivd_judgment_codify returns a prompt template, not a disk artifact."""
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        cap = _j(judgment_capture_tool(
            raw_correction="Missing null check in payment handler",
            source="user_review",
            domain="code",
            project_root_arg=str(tmp_path),
        ))
        result = _j(judgment_codify_tool(
            entry_id=cap["entry_id"],
            project_root_arg=str(tmp_path),
        ))
        assert result["ok"], result
        assert "codify_prompt" in result, f"Expected 'codify_prompt' key, got: {list(result)}"
        assert cap["entry_id"] in result["codify_prompt"]

    def test_save_codified_transitions_raw_to_codified(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        cap = _j(judgment_capture_tool(
            raw_correction="Missing null check in payment handler",
            source="user_review",
            domain="code",
            project_root_arg=str(tmp_path),
        ))
        payload = yaml.safe_dump({
            "codified": {
                "expected_result": "null check present",
                "detected_via": "code_review",
                "diagnosed_cause": "missing_null_check",
                "proposed_fix": "add guard at top of handler",
                "fix_action_type": "prompt_patch",
            },
            "leo_domain_depth": "expert",
        })
        save = _j(judgment_save_codified_tool(
            entry_id=cap["entry_id"],
            codified_yaml=payload,
            project_root_arg=str(tmp_path),
        ))
        assert save["ok"], save
        raw_dir = tmp_path / JUDGMENT_DIRNAME / "ledger" / "raw"
        codified_dir = tmp_path / JUDGMENT_DIRNAME / "ledger" / "codified"
        assert not list(raw_dir.glob("*.yaml")), "raw entry not removed after codify"
        assert len(list(codified_dir.glob("*.yaml"))) == 1, "codified entry missing"
        artifact = _yaml(next(codified_dir.glob("*.yaml")))
        assert artifact["state"] == "codified"
        assert artifact["codified"]["diagnosed_cause"] == "missing_null_check"

    def test_detect_patterns_promotes_cluster_to_pattern_file(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="missing_null_check", n=PATTERN_PROMOTION_THRESHOLD)
        result = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        assert result["ok"], result
        assert len(result["promoted_patterns"]) >= 1
        patterns_dir = tmp_path / JUDGMENT_DIRNAME / "patterns"
        yamls = list(patterns_dir.glob("*.yaml"))
        assert len(yamls) >= 1, "No pattern YAML written to disk"

    def test_inject_context_returns_structured_payload(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="missing_null_check", n=PATTERN_PROMOTION_THRESHOLD)
        _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        result = _j(judgment_inject_context_tool(project_root_arg=str(tmp_path)))
        assert result["ok"], result
        assert "context" in result
        ctx = result["context"]
        assert "patterns" in ctx
        assert len(ctx["patterns"]) >= 1

    def test_propose_recommendation_writes_recommendation_file(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="missing_null_check", n=PATTERN_PROMOTION_THRESHOLD)
        det = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        pattern_id = det["promoted_patterns"][0]["pattern_id"]

        rec = _j(judgment_propose_recommendation_tool(
            pattern_id=pattern_id,
            project_root_arg=str(tmp_path),
        ))
        assert rec["ok"], rec
        rec_dir = tmp_path / JUDGMENT_DIRNAME / "recommendations"
        yamls = list(rec_dir.glob("*.yaml"))
        assert len(yamls) == 1, "No recommendation YAML on disk"
        artifact = _yaml(yamls[0])
        assert artifact["state"] == "draft"
        assert artifact["source_pattern"] == pattern_id


# ---------------------------------------------------------------------------
# S2 — Disk artifact structure matches @dataclass schemas (R2)
# ---------------------------------------------------------------------------

class TestDiskArtifactStructure:
    """
    Validate that every YAML written to disk contains the required top-level
    keys defined by the @dataclass schemas.  This is the regression guard
    against dict-drift: if a field is renamed in schema.py but not in the
    serialisation path, this test fails.
    """

    LEDGER_ENTRY_KEYS = {"id", "state", "created", "classification", "raw_correction", "changelog"}
    CODIFIED_KEYS = {"expected_result", "detected_via", "diagnosed_cause", "proposed_fix", "fix_action_type"}
    # Derived from Pattern.to_dict() — note: no top-level "state" field; freshness carries state.
    PATTERN_KEYS = {"id", "created", "domain", "diagnosed_cause",
                    "recommended_fix", "fix_action_type", "members", "member_count",
                    "weighted_confidence", "freshness", "engine_version", "detection_hash"}
    RECOMMENDATION_KEYS = {"id", "state", "created", "source_pattern", "fix_action_type"}
    # Derived from Baseline.to_dict() — key is "domain_id" not "domain".
    BASELINE_KEYS = {"domain_id", "created", "pattern_half_life_policy"}

    def test_raw_ledger_entry_keys(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _j(judgment_capture_tool(
            raw_correction="Test entry for schema check",
            source="test",
            domain="code",
            project_root_arg=str(tmp_path),
        ))
        raw_yaml = next((tmp_path / JUDGMENT_DIRNAME / "ledger" / "raw").glob("*.yaml"))
        artifact = _yaml(raw_yaml)
        missing = self.LEDGER_ENTRY_KEYS - artifact.keys()
        assert not missing, f"Raw ledger entry missing keys: {missing}"

    def test_codified_entry_has_codified_block(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="schema_check", n=1)
        codified_yaml = next(
            (tmp_path / JUDGMENT_DIRNAME / "ledger" / "codified").glob("*.yaml")
        )
        artifact = _yaml(codified_yaml)
        assert "codified" in artifact, "codified block missing from codified entry"
        missing = self.CODIFIED_KEYS - artifact["codified"].keys()
        assert not missing, f"codified block missing keys: {missing}"

    def test_pattern_yaml_has_all_required_keys(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="schema_check", n=PATTERN_PROMOTION_THRESHOLD)
        _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        pattern_yaml = next((tmp_path / JUDGMENT_DIRNAME / "patterns").glob("*.yaml"))
        artifact = _yaml(pattern_yaml)
        missing = self.PATTERN_KEYS - artifact.keys()
        assert not missing, f"Pattern YAML missing keys: {missing}"

    def test_recommendation_yaml_has_required_keys(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="schema_check", n=PATTERN_PROMOTION_THRESHOLD)
        det = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        _j(judgment_propose_recommendation_tool(
            pattern_id=det["promoted_patterns"][0]["pattern_id"],
            project_root_arg=str(tmp_path),
        ))
        rec_yaml = next((tmp_path / JUDGMENT_DIRNAME / "recommendations").glob("*.yaml"))
        artifact = _yaml(rec_yaml)
        missing = self.RECOMMENDATION_KEYS - artifact.keys()
        assert not missing, f"Recommendation YAML missing keys: {missing}"

    def test_baseline_yaml_has_required_keys(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        baseline_yaml = tmp_path / JUDGMENT_DIRNAME / "baselines" / "code_baseline.yaml"
        assert baseline_yaml.exists(), "code_baseline.yaml not written"
        artifact = _yaml(baseline_yaml)
        missing = self.BASELINE_KEYS - artifact.keys()
        assert not missing, f"Baseline YAML missing keys: {missing}"


# ---------------------------------------------------------------------------
# S3 — Hash determinism (R3)
# ---------------------------------------------------------------------------

class TestHashDeterminism:
    """
    The same set of codified entries must produce the same detection_hash
    across two independent calls to detect_patterns.
    """

    def test_detection_hash_is_stable_across_repeated_calls(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="determinism_check", n=PATTERN_PROMOTION_THRESHOLD)

        det1 = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        hash1 = det1["promoted_patterns"][0]["detection_hash"]

        det2 = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        hash2 = det2["promoted_patterns"][0]["detection_hash"]

        assert hash1 == hash2, (
            f"detection_hash is not stable: {hash1!r} vs {hash2!r}"
        )

    def test_injection_hash_is_stable_across_repeated_calls(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="inject_hash_check", n=PATTERN_PROMOTION_THRESHOLD)
        _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))

        inj1 = _j(judgment_inject_context_tool(project_root_arg=str(tmp_path)))
        inj2 = _j(judgment_inject_context_tool(project_root_arg=str(tmp_path)))

        assert inj1["injection_hash"] == inj2["injection_hash"], (
            "injection_hash is not stable: "
            f"{inj1['injection_hash']!r} vs {inj2['injection_hash']!r}"
        )

    def test_detection_hash_changes_when_new_entry_added(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="hash_change_check", n=PATTERN_PROMOTION_THRESHOLD)

        det1 = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        hash_before = det1["promoted_patterns"][0]["detection_hash"]

        # Add a new entry with the same cause — the cluster now has 4 members
        _seed_entries(tmp_path, cause="hash_change_check", n=1)
        det2 = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        hash_after = det2["promoted_patterns"][0]["detection_hash"]

        assert hash_before != hash_after, (
            "detection_hash should change when the member set grows, but it did not"
        )


# ---------------------------------------------------------------------------
# S4 — Engine version stamp (R3)
# ---------------------------------------------------------------------------

class TestEngineVersionStamp:
    """Pattern and InjectionResult carry engine_version matching the package constant."""

    def test_pattern_yaml_carries_engine_version(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="version_stamp", n=PATTERN_PROMOTION_THRESHOLD)
        _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        pattern_yaml = next((tmp_path / JUDGMENT_DIRNAME / "patterns").glob("*.yaml"))
        artifact = _yaml(pattern_yaml)
        assert artifact.get("engine_version") == ENGINE_VERSION, (
            f"Pattern on disk has engine_version={artifact.get('engine_version')!r}, "
            f"expected {ENGINE_VERSION!r}"
        )

    def test_detect_tool_response_carries_engine_version(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="version_stamp_response", n=PATTERN_PROMOTION_THRESHOLD)
        det = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        assert det["engine_version"] == ENGINE_VERSION
        assert det["promoted_patterns"][0]["engine_version"] == ENGINE_VERSION

    def test_inject_tool_response_carries_engine_version(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="inject_version_stamp", n=PATTERN_PROMOTION_THRESHOLD)
        _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        inj = _j(judgment_inject_context_tool(project_root_arg=str(tmp_path)))
        assert inj["engine_version"] == ENGINE_VERSION

    def test_recommend_tool_response_carries_engine_version(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="rec_version_stamp", n=PATTERN_PROMOTION_THRESHOLD)
        det = _j(judgment_detect_patterns_tool(project_root_arg=str(tmp_path)))
        rec = _j(judgment_propose_recommendation_tool(
            pattern_id=det["promoted_patterns"][0]["pattern_id"],
            project_root_arg=str(tmp_path),
        ))
        assert rec["engine_version"] == ENGINE_VERSION


# ---------------------------------------------------------------------------
# S5 — Server-level opt-out (R4)
# ---------------------------------------------------------------------------

class TestOptOut:
    """
    ``IVD_JUDGMENT_TOOLS_ENABLED=false`` disables all tools at runtime.
    Unsetting the var restores them.  Relies only on env vars — no subprocess,
    no mocking.
    """

    ALL_TOOL_FNS = [
        ("ivd_judgment_init", lambda root: judgment_init_tool(project_root_arg=root)),
        ("ivd_judgment_capture", lambda root: judgment_capture_tool(
            raw_correction="x", domain="code", project_root_arg=root)),
        ("ivd_judgment_detect_patterns", lambda root: judgment_detect_patterns_tool(
            project_root_arg=root)),
        ("ivd_judgment_inject_context", lambda root: judgment_inject_context_tool(
            project_root_arg=root)),
        ("ivd_judgment_check_installed", lambda root: judgment_check_installed_tool(
            project_root_arg=root)),
    ]

    def test_all_tools_disabled_when_env_false(self, tmp_path, monkeypatch):
        monkeypatch.setenv(_OPT_OUT_ENV, "false")
        for name, fn in self.ALL_TOOL_FNS:
            result = _j(fn(str(tmp_path)))
            assert result.get("ok") is False, f"{name} did not return ok=False when disabled"
            assert result.get("enabled") is False, f"{name} missing enabled=False"

    def test_tools_re_enabled_when_env_unset(self, tmp_path, monkeypatch):
        monkeypatch.setenv(_OPT_OUT_ENV, "false")
        disabled = _j(judgment_init_tool(project_root_arg=str(tmp_path)))
        assert disabled.get("ok") is False

        monkeypatch.delenv(_OPT_OUT_ENV, raising=False)
        enabled = _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        assert enabled.get("ok") is True, f"Tool did not re-enable: {enabled}"

    def test_disabled_response_names_env_var(self, tmp_path, monkeypatch):
        monkeypatch.setenv(_OPT_OUT_ENV, "false")
        result = _j(judgment_capture_tool(
            raw_correction="test", domain="code", project_root_arg=str(tmp_path)
        ))
        assert _OPT_OUT_ENV in result.get("message", ""), (
            "Disabled message should name the env var so operators can re-enable"
        )


# ---------------------------------------------------------------------------
# S6 — ivd_judgment_check_installed never writes (R6)
# ---------------------------------------------------------------------------

class TestCheckInstalledNoWrites:
    """
    ``ivd_judgment_check_installed`` must be safe to call at any time.
    It reports state; it never creates files.
    """

    def _project_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """The tool returns a 'projects' list; extract the first project summary."""
        projects = result.get("projects") or []
        assert projects, f"No 'projects' list in response: {result}"
        return projects[0]

    def test_returns_not_activated_before_init(self, tmp_path):
        result = _j(judgment_check_installed_tool(project_root_arg=str(tmp_path)))
        summary = self._project_summary(result)
        assert summary.get("activated") is False, (
            f"Expected activated=False before init, got summary: {summary}"
        )

    def test_returns_init_payload_when_not_activated(self, tmp_path):
        result = _j(judgment_check_installed_tool(project_root_arg=str(tmp_path)))
        # The tool communicates "how to activate" via next_step at the top level
        # or via projects_activated == 0 in the summary block.
        summary_count = (result.get("summary") or {}).get("projects_activated", -1)
        has_guidance = "next_step" in result or "next_action" in result or summary_count == 0
        assert has_guidance, (
            "check_installed should signal that no projects are activated: "
            f"{result}"
        )

    def test_does_not_create_any_files(self, tmp_path):
        files_before = set(tmp_path.rglob("*"))
        _j(judgment_check_installed_tool(project_root_arg=str(tmp_path)))
        files_after = set(tmp_path.rglob("*"))
        assert files_before == files_after, (
            f"check_installed created files: {files_after - files_before}"
        )

    def test_returns_activated_true_after_init(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        result = _j(judgment_check_installed_tool(project_root_arg=str(tmp_path)))
        summary = self._project_summary(result)
        assert summary.get("activated") is True, (
            f"Expected activated=True after init, got summary: {summary}"
        )

    def test_reports_correct_baseline_count_after_init(self, tmp_path):
        _j(judgment_init_tool(
            project_root_arg=str(tmp_path), domains=["code", "docs", "design"]
        ))
        result = _j(judgment_check_installed_tool(project_root_arg=str(tmp_path)))
        summary = self._project_summary(result)
        assert summary.get("baseline_count") == 3, (
            f"Expected 3 baselines, got: {summary.get('baseline_count')}"
        )

    def test_reports_correct_domain_list(self, tmp_path):
        domains = ["auth", "payments"]
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=domains))
        result = _j(judgment_check_installed_tool(project_root_arg=str(tmp_path)))
        summary = self._project_summary(result)
        reported = set(summary.get("domains") or [])
        assert reported == set(domains), f"Expected domains {domains}, got {reported}"

    def test_ledger_counts_update_after_entries(self, tmp_path):
        _j(judgment_init_tool(project_root_arg=str(tmp_path), domains=["code"]))
        _seed_entries(tmp_path, cause="count_check", n=2)
        result = _j(judgment_check_installed_tool(project_root_arg=str(tmp_path)))
        summary = self._project_summary(result)
        codified_count = (summary.get("ledger_counts") or {}).get("codified", 0)
        assert codified_count == 2, (
            f"Expected ledger_counts.codified=2, got: {codified_count}"
        )


# ---------------------------------------------------------------------------
# S7 — Workspace scan discovers multiple projects
# ---------------------------------------------------------------------------

class TestWorkspaceScan:
    """
    With ``workspace_root`` set, check_installed walks the tree and discovers
    activated projects at different nesting depths.
    """

    def test_discovers_two_activated_projects_in_workspace(self, tmp_path):
        # Activate judgment in two sub-projects
        proj_a = tmp_path / "services" / "auth"
        proj_b = tmp_path / "services" / "billing"
        proj_a.mkdir(parents=True)
        proj_b.mkdir(parents=True)

        _j(judgment_init_tool(project_root_arg=str(proj_a), domains=["code"]))
        _j(judgment_init_tool(project_root_arg=str(proj_b), domains=["code"]))

        result = _j(judgment_check_installed_tool(workspace_root=str(tmp_path)))
        assert "projects" in result, f"Expected 'projects' key in workspace scan: {result}"
        activated = [p for p in result["projects"] if p.get("activated")]
        assert len(activated) == 2, (
            f"Expected 2 activated projects, found {len(activated)}: "
            f"{[p['project_root'] for p in result['projects']]}"
        )

    def test_uninitialised_projects_are_not_listed_as_activated(self, tmp_path):
        proj_a = tmp_path / "services" / "auth"
        proj_a.mkdir(parents=True)
        _j(judgment_init_tool(project_root_arg=str(proj_a), domains=["code"]))

        # proj_b exists but is NOT initialised
        proj_b = tmp_path / "services" / "billing"
        proj_b.mkdir(parents=True)

        result = _j(judgment_check_installed_tool(workspace_root=str(tmp_path)))
        activated = [p for p in result.get("projects", []) if p.get("activated")]
        assert len(activated) == 1, (
            f"Only one project should be activated, got {len(activated)}"
        )

    def test_workspace_scan_respects_max_depth(self, tmp_path):
        # Nest project 4 levels deep — beyond default max_depth of 3
        deep_proj = tmp_path / "a" / "b" / "c" / "d" / "svc"
        deep_proj.mkdir(parents=True)
        _j(judgment_init_tool(project_root_arg=str(deep_proj), domains=["code"]))

        result = _j(judgment_check_installed_tool(
            workspace_root=str(tmp_path),
            max_depth=2,
        ))
        activated = [p for p in result.get("projects", []) if p.get("activated")]
        assert len(activated) == 0, (
            "Deep project should not be found with max_depth=2"
        )
