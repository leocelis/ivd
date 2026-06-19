# mcp_server/tests/unit/test_client_enforcement.py

"""Unit tests for client_enforcement signals."""

import json

from mcp_server.tools.client_enforcement import (
    build_client_enforcement_from_gating,
    build_client_enforcement_from_review_gate,
)
from mcp_server.tools.review_gate import review_intent_tool
from mcp_server.tools.validate import validate_artifact_tool


def _intent_with(constraints_yaml: str, extra: str = "") -> str:
    return (
        "intent:\n"
        "  summary: t\n  goal: t\n  success_metric: t\n"
        f"{constraints_yaml}"
        f"{extra}"
        "rationale:\n  decision: t\n  reasoning: t\n"
        "alternatives:\n  - name: none\n"
        "risks:\n  - condition: none\n"
        "implementation:\n  current: .\n"
        "verification:\n  test_cases: []\n"
    )


class TestClientEnforcementHelpers:
    def test_from_gating_needs_external_oracle(self):
        gating = {"status": "NEEDS_EXTERNAL_ORACLE", "constraints_needing_external_oracle": ["c1"]}
        ce = build_client_enforcement_from_gating(gating)
        assert ce["implementation_complete_blocked"] is True
        assert "NEEDS_EXTERNAL_ORACLE" in ce["active_gates"]
        assert ce["monitoring_event"] == "verification_gating_active"

    def test_from_gating_none_when_empty(self):
        assert build_client_enforcement_from_gating(None) is None
        assert build_client_enforcement_from_gating({}) is None

    def test_from_review_pending_signoff(self):
        gate = {"status": "PENDING_SIGNOFF", "pending_signoffs": ["risky"]}
        ce = build_client_enforcement_from_review_gate(gate)
        assert ce["implementation_complete_blocked"] is True
        assert "PENDING_SIGNOFF" in ce["active_gates"]
        assert "signoff:risky" in ce["active_gates"]

    def test_from_review_ready_returns_none(self):
        gate = {"status": "READY", "pending_signoffs": []}
        assert build_client_enforcement_from_review_gate(gate) is None


class TestValidateEmitsClientEnforcement:
    def test_unverified_includes_client_enforcement(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: ghost\n    requirement: x\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert "verification_gating" in result
        ce = result.get("client_enforcement")
        assert ce is not None
        assert ce["implementation_complete_blocked"] is True
        assert "UNVERIFIED" in ce["active_gates"]

    def test_clean_intent_has_no_client_enforcement(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: ok\n    requirement: x\n"
            "    test: mcp_server/tests/unit/test_validate.py::TestValidateArtifact::test_empty_yaml_has_errors\n"
            "    test_provenance: human_authored\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert "client_enforcement" not in result


class TestReviewIntentEmitsClientEnforcement:
    def test_pending_signoff_emits_client_enforcement(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: risky\n    requirement: x\n"
            "    test: t.py::t\n"
            "    assumption_status: GUESSED\n"
        )
        result = json.loads(review_intent_tool(yaml_str))
        assert result["review_gate"]["status"] == "PENDING_SIGNOFF"
        ce = result.get("client_enforcement")
        assert ce is not None
        assert ce["monitoring_event"] == "review_gate_pending_signoff"
