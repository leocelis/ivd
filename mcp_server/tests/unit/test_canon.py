# mcp_server/tests/unit/test_canon.py

"""Unit tests for the Canon — Human Translation Layer — as hosted inside IVD.

Enforces the priority-1 constraints declared in the Canon system intent:

  canon_mcp_hosted_inside_ivd
      → the four Canon MCP tools MUST be registered in the existing IVD
        MCP server catalog; no separate Canon binary, no separate
        `mcpServers.canon` entry.

  canon_check_rules_installed_no_writes
      → the canon_check_rules_installed handler MUST perform zero file
        writes. Writing is the agent's responsibility, only after
        explicit user consent.

  canon_mcp_zero_config_default
      → default behavior (with IVD_CANON_TOOLS_ENABLED unset) is
        "enabled + zero config"; `IVD_CANON_TOOLS_ENABLED=false` is the
        single opt-out knob.

Also pins a handful of engine-level invariants so the rest of Canon does
not regress quietly (R2 strictness, audit hash reproducibility, diff
correctness, R5 verification-beat emission for irreversible actions,
ivd_init agent_rules_status reporting).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Set
from unittest import mock

import pytest

from canon import (
    AuditReport,
    audit as canon_audit,
    diff_audit as canon_diff_audit,
    infer as canon_infer,
    render as canon_render_engine,
)
from mcp_server.registry import TOOL_HANDLERS, call_tool, get_all_tools
from mcp_server.tools.canon import (
    _is_canon_enabled,
    canon_check_rules_installed_tool,
    canon_check_tool,
    canon_diff_tool,
    canon_render_tool,
)


CANON_TOOL_NAMES: Set[str] = {
    "canon_render",
    "canon_check",
    "canon_diff",
    "canon_check_rules_installed",
}


# ---------------------------------------------------------------------------
# canon_mcp_hosted_inside_ivd
# ---------------------------------------------------------------------------

class TestCanonHostedInsideIVD:
    """The four Canon tools live inside the IVD MCP server, period."""

    def test_all_four_canon_tools_registered(self):
        names = {t.name for t in get_all_tools()}
        missing = CANON_TOOL_NAMES - names
        assert not missing, f"Canon tools missing from IVD registry: {missing}"

    def test_each_canon_tool_has_handler(self):
        for name in CANON_TOOL_NAMES:
            assert name in TOOL_HANDLERS, f"No handler for {name}"

    def test_each_canon_tool_has_input_schema(self):
        tools = {t.name: t for t in get_all_tools()}
        for name in CANON_TOOL_NAMES:
            tool = tools[name]
            assert tool.inputSchema is not None
            assert tool.inputSchema.get("type") == "object"

    def test_no_separate_canon_server_binary(self):
        """There must not be a standalone Canon MCP main entrypoint."""
        mcp_dir = Path(__file__).parent.parent.parent  # mcp_server/
        forbidden = ["canon_main.py", "canon_server.py", "canon_app.py"]
        for fname in forbidden:
            assert not (mcp_dir / fname).exists(), (
                f"Forbidden separate Canon MCP binary found: {fname}. "
                "Canon tools must live inside the existing IVD MCP server "
                "(constraint canon_mcp_hosted_inside_ivd)."
            )


# ---------------------------------------------------------------------------
# canon_check_rules_installed_no_writes
# ---------------------------------------------------------------------------

class TestCanonCheckRulesInstalledNoWrites:
    """The detection tool NEVER writes to disk. Zero tolerance."""

    def test_no_file_writes_when_block_missing(self, tmp_path: Path):
        # tmp_path is an empty project — no agent files, no rule blocks.
        # Worst case for "maybe I'll helpfully install them" regressions.
        writes: List[str] = []
        real_write = Path.write_text
        real_mkdir = Path.mkdir
        real_open = open

        def track_write(self, *a, **kw):
            writes.append(f"write_text:{self}")
            return real_write(self, *a, **kw)

        def track_mkdir(self, *a, **kw):
            # mkdir under tmp_path is a write to disk too.
            writes.append(f"mkdir:{self}")
            return real_mkdir(self, *a, **kw)

        def track_open(path, mode="r", *a, **kw):
            # Anything other than a read is a write.
            if any(m in mode for m in ("w", "a", "x", "+")):
                writes.append(f"open:{path}:{mode}")
            return real_open(path, mode, *a, **kw)

        with mock.patch.object(Path, "write_text", track_write), \
             mock.patch.object(Path, "mkdir", track_mkdir), \
             mock.patch("builtins.open", track_open):
            out = canon_check_rules_installed_tool(
                project_root_arg=str(tmp_path),
                install_missing=True,  # worst case: hint says install
            )

        # Filter out writes outside the tmp_path sandbox (none should exist
        # but we don't want e.g. a log rotation to false-fail the test).
        sandbox_writes = [w for w in writes if str(tmp_path) in w]
        assert not sandbox_writes, (
            f"canon_check_rules_installed performed file writes under {tmp_path}: "
            f"{sandbox_writes}. This violates canon_check_rules_installed_no_writes."
        )

        payload = json.loads(out)
        assert "permission_discipline" in payload
        assert payload["overall_status"] in {
            "missing", "no_agent_files_detected", "unknown"
        }

    def test_install_payload_present_but_not_applied(self, tmp_path: Path):
        """When a target file exists without the Canon block, the tool returns
        an install_payload — but never actually writes it."""
        (tmp_path / ".cursorrules").write_text("# existing rules\n")
        out = canon_check_rules_installed_tool(
            project_root_arg=str(tmp_path),
            install_missing=False,
        )
        payload = json.loads(out)
        cursor_entries = [
            t for t in payload["per_target"] if t.get("client") == "cursor"
        ]
        assert cursor_entries, "Expected a cursor target entry"
        entry = cursor_entries[0]
        assert entry["file_exists"] is True
        assert entry["canon_block"] in (None, {"present": False}) or not (
            entry.get("canon_block") or {}
        ).get("present")
        assert "install_payload" in entry
        assert entry["install_payload"]["strategy"].startswith(
            "append-fenced-block-to-existing-file"
        )

        # File unchanged on disk (no silent append).
        assert (tmp_path / ".cursorrules").read_text() == "# existing rules\n"

    def test_block_detected_when_fences_present(self, tmp_path: Path):
        (tmp_path / ".cursorrules").write_text(
            "# existing\n"
            "<BEGIN-CANON v1.0>\n"
            "The Canon rules block content would live here.\n"
            "<END-CANON v1.0>\n"
        )
        out = canon_check_rules_installed_tool(project_root_arg=str(tmp_path))
        payload = json.loads(out)
        cursor_entries = [
            t for t in payload["per_target"] if t.get("client") == "cursor"
        ]
        assert cursor_entries
        assert cursor_entries[0]["canon_block"]["present"] is True


# ---------------------------------------------------------------------------
# canon_mcp_zero_config_default (opt-out knob)
# ---------------------------------------------------------------------------

class TestCanonOptOut:
    """IVD_CANON_TOOLS_ENABLED=false is the single opt-out knob."""

    def test_default_is_enabled(self, monkeypatch):
        monkeypatch.delenv("IVD_CANON_TOOLS_ENABLED", raising=False)
        assert _is_canon_enabled() is True

    @pytest.mark.parametrize("val", ["false", "FALSE", "0", "no", "off", "OFF"])
    def test_opt_out_disables_all_four_tools(self, monkeypatch, val, tmp_path):
        monkeypatch.setenv("IVD_CANON_TOOLS_ENABLED", val)
        render_out = json.loads(canon_render_tool(text="hello"))
        check_out = json.loads(canon_check_tool(text="hello"))
        diff_out = json.loads(canon_diff_tool(before={}, after={}))
        rules_out = json.loads(
            canon_check_rules_installed_tool(project_root_arg=str(tmp_path))
        )
        for out in (render_out, check_out, diff_out, rules_out):
            assert out.get("enabled") is False, (
                f"Canon tool should be disabled when IVD_CANON_TOOLS_ENABLED={val} "
                f"but got: {out}"
            )


# ---------------------------------------------------------------------------
# Canon engine invariants (deterministic Tier 1)
# ---------------------------------------------------------------------------

class TestCanonEngine:
    """Pin the deterministic behavior so Phase 0c / 1 / 2 inherit a stable core."""

    def test_infer_render_audit_are_deterministic(self):
        text = "The migration script will delete the old table. It is verified."
        a1 = canon_audit(canon_render_engine(canon_infer(text)))
        a2 = canon_audit(canon_render_engine(canon_infer(text)))
        assert a1.hash() == a2.hash()

    def test_audit_hash_changes_when_input_changes(self):
        a1 = canon_audit(canon_render_engine(canon_infer("alpha")))
        a2 = canon_audit(canon_render_engine(canon_infer("beta, probably")))
        assert a1.hash() != a2.hash()

    def test_R2_requires_glyph_not_bare_word(self):
        """Post-fix: bare English 'verified' no longer satisfies R2."""
        from canon.contract import CanonDocument, Stakes
        doc = CanonDocument(
            setting_phase="Setting: test.",
            body_with_marks="This was not verified and unclear.",
            stakes=Stakes.LOW,
            identity_statement="I am an AI assistant.",
        )
        report = canon_audit(doc)
        r2 = next(f for f in report.findings if f.r == "R2")
        assert r2.status == "partial", (
            f"R2 should be 'partial' when only bare words are present; got {r2.status}"
        )

    def test_R2_passes_with_canon_marker(self):
        from canon.contract import CanonDocument, Stakes
        doc = CanonDocument(
            setting_phase="Setting: test.",
            body_with_marks="Config path is ./conf (✓ verified).",
            stakes=Stakes.LOW,
            identity_statement="I am an AI assistant.",
        )
        report = canon_audit(doc)
        r2 = next(f for f in report.findings if f.r == "R2")
        assert r2.status == "pass"

    def test_R5_emits_verification_beat_for_irreversible(self):
        text = "Delete the production database to clear the stale state."
        document = canon_render_engine(canon_infer(text))
        assert len(document.verification_beats) >= 1
        beat = document.verification_beats[0]
        assert "irreversible" in beat["reversible"].lower()

    # ------------------------------------------------------------------
    # R13 stakes-adaptive format (engine v0.2.0 — structural-density heuristic)
    # ------------------------------------------------------------------

    def test_R13_passes_low_stakes_short(self):
        from canon.contract import CanonDocument, Stakes
        doc = CanonDocument(
            setting_phase="Setting: chitchat.",
            body_with_marks="Yes, that's correct (✓ verified).",
            stakes=Stakes.LOW,
            identity_statement="I am an AI assistant.",
        )
        report = canon_audit(doc)
        r13 = next(f for f in report.findings if f.r == "R13")
        assert r13.status == "pass", r13.detail

    def test_R13_fails_low_stakes_verbose_with_structure(self):
        """Long multi-section reply at low stakes — format too heavy."""
        from canon.contract import CanonDocument, Stakes
        long_body = (
            "## Section 1\n\n"
            + ("Lorem ipsum dolor sit amet consectetur adipiscing elit. " * 20)
            + "\n\n## Section 2\n\n"
            + ("Sed do eiusmod tempor incididunt ut labore et dolore magna. " * 20)
        )
        doc = CanonDocument(
            setting_phase="Setting: simple Q.",
            body_with_marks=long_body,
            stakes=Stakes.LOW,
            identity_statement="I am an AI assistant.",
        )
        report = canon_audit(doc)
        r13 = next(f for f in report.findings if f.r == "R13")
        assert r13.status == "fail", r13.detail
        assert "low stakes" in r13.detail.lower()

    def test_R13_passes_medium_stakes_any_format(self):
        from canon.contract import CanonDocument, Stakes
        doc = CanonDocument(
            setting_phase="Setting: medium-stakes work.",
            body_with_marks="Plain prose answer with no structure (✓ verified).",
            stakes=Stakes.MEDIUM,
            identity_statement="I am an AI assistant.",
        )
        report = canon_audit(doc)
        r13 = next(f for f in report.findings if f.r == "R13")
        assert r13.status == "pass", r13.detail
        assert "medium" in r13.detail.lower() or "relaxed" in r13.detail.lower()

    def test_R13_fails_high_stakes_flat_prose(self):
        """Long flat prose at high stakes — needs outline structure."""
        from canon.contract import CanonDocument, Stakes
        flat = ("This is a long answer that explains the migration in flowing "
                "prose without any headers or lists or tables. " * 10)
        doc = CanonDocument(
            setting_phase="Setting: production migration.",
            body_with_marks=flat,
            stakes=Stakes.HIGH,
            identity_statement="I am an AI assistant.",
        )
        report = canon_audit(doc)
        r13 = next(f for f in report.findings if f.r == "R13")
        assert r13.status == "fail", r13.detail
        assert "high" in r13.detail.lower() and "structure" in r13.detail.lower()

    def test_R13_passes_high_stakes_structured(self):
        from canon.contract import CanonDocument, Stakes
        body = (
            "## Plan\n\n"
            "- Step 1: backup the table\n"
            "- Step 2: run the migration\n"
            "- Step 3: verify row counts\n\n"
            "## Risks\n\n"
            "| Risk | Mitigation |\n"
            "|------|------------|\n"
            "| Data loss | Backup first |\n"
        )
        doc = CanonDocument(
            setting_phase="Setting: production migration plan.",
            body_with_marks=body,
            stakes=Stakes.HIGH,
            identity_statement="I am an AI assistant.",
        )
        report = canon_audit(doc)
        r13 = next(f for f in report.findings if f.r == "R13")
        assert r13.status == "pass", r13.detail

    def test_R13_fails_irreversible_terse_flat(self):
        from canon.contract import CanonDocument, Stakes
        doc = CanonDocument(
            setting_phase="Setting: delete request.",
            body_with_marks="Yes, run it. Should be fine.",
            stakes=Stakes.IRREVERSIBLE,
            identity_statement="I am an AI assistant.",
        )
        report = canon_audit(doc)
        r13 = next(f for f in report.findings if f.r == "R13")
        assert r13.status == "fail", r13.detail
        assert "irreversible" in r13.detail.lower()

    def test_R13_not_in_partial_stubs(self):
        """R13 was promoted to enforced in engine v0.2.0 — must NOT appear
        in the partial-stubs list anymore."""
        from canon.contract import CanonDocument, Stakes
        doc = CanonDocument(
            setting_phase="Setting: x.",
            body_with_marks="hi",
            stakes=Stakes.LOW,
            identity_statement="I am an AI assistant.",
        )
        report = canon_audit(doc)
        r13 = next(f for f in report.findings if f.r == "R13")
        # If R13 ever regresses to "partial" (i.e., back in _audit_partial_stubs)
        # this test fires the alarm.
        assert r13.status in ("pass", "fail"), (
            f"R13 should be enforced (pass/fail) in engine v0.2.0, got {r13.status}"
        )

    def test_engine_version_is_0_2_0(self):
        """Engine version bump is the contract that R13 is now enforced."""
        from canon.contract import CanonDocument, Stakes
        doc = CanonDocument(
            setting_phase="Setting: x.",
            body_with_marks="hi (✓ verified).",
            stakes=Stakes.LOW,
            identity_statement="I am an AI assistant.",
        )
        report = canon_audit(doc)
        assert report.engine_version == "0.2.0", report.engine_version

    def test_canon_diff_marks_fixed_and_regressed(self):
        """A before that failed R2 and an after that passes should mark R2 fixed."""
        from canon.contract import AuditReport, RFinding, Stakes
        before = AuditReport(
            findings=[RFinding(r="R2", status="partial", severity="warn", detail="no marks")],
            overall="partial",
            partial=True,
            stakes=Stakes.LOW,
        )
        after = AuditReport(
            findings=[RFinding(r="R2", status="pass", severity="info", detail="mark present")],
            overall="pass",
            partial=False,
            stakes=Stakes.LOW,
        )
        diff = canon_diff_audit(before, after)
        assert "R2" in diff.fixed
        assert "R2" not in diff.regressed


# ---------------------------------------------------------------------------
# canon_ivd_init_reports_canon_status
# ---------------------------------------------------------------------------

class TestIvdInitCanonStatus:
    """ivd_init's scan surfaces agent_rules_status: {ivd, canon} per detected file."""

    def test_ivd_init_reports_agent_rules_status(self, tmp_path: Path):
        # Create an agent instruction file with the CANON block only.
        (tmp_path / ".cursorrules").write_text(
            "# cursor rules\n"
            "<BEGIN-CANON v1.0>\n"
            "...\n"
            "<END-CANON v1.0>\n"
        )
        # And one with the IVD block only.
        (tmp_path / "CLAUDE.md").write_text(
            "# claude\n"
            "<BEGIN-IVD v1.0>\n"
            "...\n"
            "<END-IVD v1.0>\n"
        )
        result = call_tool("ivd_init", {"project_root": str(tmp_path)})
        payload = json.loads(result)
        status = payload.get("agent_rules_status", {})
        assert ".cursorrules" in status, payload
        assert ".cursorrules" in status and status[".cursorrules"]["canon"] is True
        assert status[".cursorrules"]["ivd"] is False
        assert "CLAUDE.md" in status
        assert status["CLAUDE.md"]["ivd"] is True
        assert status["CLAUDE.md"]["canon"] is False

    def test_ivd_init_scan_summary_counts_canon(self, tmp_path: Path):
        (tmp_path / ".cursorrules").write_text(
            "<BEGIN-CANON v1.0>\n...\n<END-CANON v1.0>\n"
        )
        result = call_tool("ivd_init", {"project_root": str(tmp_path)})
        payload = json.loads(result)
        scan = payload.get("scan_summary", {})
        assert scan.get("agent_files_with_canon") == 1
        assert scan.get("agent_files_with_ivd") == 0

    def test_ivd_init_dangling_begin_without_end_not_counted(self, tmp_path: Path):
        """A broken paste with only BEGIN and no END must not report as installed."""
        (tmp_path / ".cursorrules").write_text(
            "<BEGIN-CANON v1.0>\n"
            "content but somebody deleted the closing fence\n"
        )
        result = call_tool("ivd_init", {"project_root": str(tmp_path)})
        payload = json.loads(result)
        status = payload.get("agent_rules_status", {})
        assert status.get(".cursorrules", {}).get("canon") is False


# ---------------------------------------------------------------------------
# canon_render / canon_check / canon_diff dispatched via call_tool
# ---------------------------------------------------------------------------

class TestCanonRulesSixClients:
    """Six per-client adapter views must carry the SAME content (no drift).

    Maps to canon_system_intent.yaml v5 priority-1 constraint
    `canon_rules_six_clients` (NFR-LA2). The recipe ships ONE canonical Canon
    Rules block plus six per-client adapter views — every adapter view must
    independently mention all 5 R-invariants, both fence markers, all 5
    forbidden patterns by name, and the Phase-0a+0b composition hint.
    """

    @staticmethod
    def _load_recipe() -> Dict[str, Any]:
        import yaml
        from mcp_server.tools._paths import get_framework_path
        with (get_framework_path() / "recipes" / "canon-rules.yaml").open() as f:
            return yaml.safe_load(f)

    @staticmethod
    def _norm(s: str) -> str:
        """Collapse all whitespace + strip comment-prefix `#` markers, lowercase."""
        import re
        # Drop leading "# " or "#" comment markers anywhere on a line first,
        # then collapse whitespace. This survives wrapped comment blocks.
        cleaned = re.sub(r"(?m)^\s*#+\s?", "", s)
        return re.sub(r"\s+", " ", cleaned).lower()

    ADAPTER_KEYS = (
        "cursorrules_format",
        "clinerules_format",
        "claude_code_format",
        "copilot_format",
        "codex_format",
        "windsurf_format",
    )

    def test_all_six_adapter_views_present(self):
        recipe = self._load_recipe()
        adapters = recipe.get("agent_rules_block", {})
        for k in self.ADAPTER_KEYS:
            assert k in adapters, f"Missing adapter view: {k}"

    def test_install_targets_reference_only_existing_adapter_views(self):
        recipe = self._load_recipe()
        adapters = recipe.get("agent_rules_block", {})
        for tgt in recipe.get("install_targets", []):
            view = tgt.get("adapter_view")
            assert view in adapters, (
                f"install_target {tgt.get('client')!r} references adapter_view {view!r} "
                "which does not exist in agent_rules_block"
            )

    def test_each_adapter_mentions_all_five_R_invariants(self):
        recipe = self._load_recipe()
        adapters = recipe["agent_rules_block"]
        for k in self.ADAPTER_KEYS:
            body = self._norm(adapters[k])
            for r in ("r1", "r2", "r5", "r10", "r14"):
                assert r in body, f"{k} missing R-invariant {r!r}"

    def test_each_adapter_carries_fence_markers(self):
        recipe = self._load_recipe()
        adapters = recipe["agent_rules_block"]
        for k in self.ADAPTER_KEYS:
            body = self._norm(adapters[k])
            assert "<begin-canon v1.0>" in body, f"{k} missing BEGIN fence"
            assert "<end-canon v1.0>" in body, f"{k} missing END fence"

    def test_each_adapter_lists_all_five_forbidden_patterns_by_name(self):
        """canon_rules_six_clients: all six adapter views must list the
        same five forbidden patterns by name. Drift here would let the
        manipulation-adjacent patterns leak in via one client."""
        recipe = self._load_recipe()
        adapters = recipe["agent_rules_block"]
        forbidden = [
            "obligation manufacturing",
            "manufactured urgency",
            "fabricated social proof",
            "companionship framing",
            "manufactured negative arousal",
        ]
        drift = []
        for k in self.ADAPTER_KEYS:
            body = self._norm(adapters[k])
            for f in forbidden:
                if f not in body:
                    drift.append((k, f))
        assert not drift, (
            f"Adapter view drift on forbidden-pattern coverage: {drift}. "
            "Each of the 6 per-client views must list all 5 forbidden patterns "
            "(constraint canon_rules_six_clients)."
        )

    def test_each_adapter_includes_composition_hint(self):
        """Phase 0a rules block must instruct the agent to call canon_check
        when the IVD MCP is available (Tech Spec §9A.4 / NFR-LA5)."""
        recipe = self._load_recipe()
        adapters = recipe["agent_rules_block"]
        for k in self.ADAPTER_KEYS:
            body = self._norm(adapters[k])
            assert "canon_check" in body, (
                f"{k} missing the Phase-0a+0b composition hint (call canon_check). "
                "Required by Tech Spec §9A.4 / NFR-LA5."
            )


class TestCanonToolDispatch:
    """Round-trip the full Canon chain through the IVD MCP registry."""

    def test_canon_render_via_dispatch_returns_markdown(self):
        result = call_tool("canon_render", {
            "text": "The config is verified.",
            "stakes": "low",
            "output_format": "markdown",
        })
        payload = json.loads(result)
        assert payload.get("tier") == 1
        assert "audit" in payload
        assert "markdown" in payload

    def test_canon_check_via_dispatch_returns_audit_report(self):
        result = call_tool("canon_check", {"text": "Deploy now."})
        payload = json.loads(result)
        assert "findings" in payload
        assert "overall" in payload
        assert "hash" in payload

    def test_canon_diff_via_dispatch(self):
        before = json.loads(call_tool("canon_check", {"text": "Just hi."}))
        after = json.loads(call_tool("canon_check", {
            "text": "Config path is ./conf (✓ verified).",
        }))
        diff = json.loads(call_tool("canon_diff", {"before": before, "after": after}))
        assert "fixed" in diff
        assert "regressed" in diff
        assert "unchanged" in diff
        assert "verdict" in diff
