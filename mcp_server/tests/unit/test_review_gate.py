# mcp_server/tests/unit/test_review_gate.py

"""Unit tests for ivd_review_intent (Fix 2) and validate assumption_status nudges."""

import json

from mcp_server.tools.review_gate import (
    build_review_gate,
    compute_risk_score,
    review_intent_tool,
    signoff_missing_fields,
)
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


class TestReviewGateTool:
    def test_guessed_missing_signoff_pending(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: risky\n    requirement: x\n    test: t.py::t\n"
            "    assumption_status: GUESSED\n"
        )
        result = json.loads(review_intent_tool(yaml_str))
        gate = result["review_gate"]
        assert gate["status"] == "PENDING_SIGNOFF"
        assert "risky" in gate["pending_signoffs"]

    def test_guessed_complete_signoff_approved(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: risky\n    requirement: x\n    test: t.py::t\n"
            "    assumption_status: GUESSED\n"
            "    review_signoff:\n"
            "      concrete_example: 'input X → output Y'\n"
            "      counter_example: 'if wrong, see Z'\n"
            "      human_acknowledged: true\n"
        )
        result = json.loads(review_intent_tool(yaml_str))
        assert result["review_gate"]["status"] == "APPROVED"
        assert result["review_gate"]["pending_signoffs"] == []

    def test_ranks_higher_risk_first(self):
        artifact = {
            "constraints": [
                {
                    "name": "low",
                    "assumption_status": "KNOWN",
                    "consequence_if_violated": "minor issue",
                },
                {
                    "name": "high",
                    "assumption_status": "GUESSED",
                    "consequence_if_violated": "critical failure",
                    "conflict_prone": True,
                },
            ],
            "verification": {"test_cases": []},
        }
        gate = build_review_gate(artifact)
        assert gate["ranked_constraints"][0]["name"] == "high"
        assert gate["ranked_constraints"][0]["risk_score"] >= gate["ranked_constraints"][1]["risk_score"]

    def test_worked_examples_from_verification(self):
        yaml_str = (
            "intent:\n  summary: t\n  goal: t\n  success_metric: t\n"
            "constraints:\n  - name: c1\n    requirement: x\n    test: t.py::t\n"
            "rationale:\n  decision: t\n  reasoning: t\n"
            "alternatives:\n  - name: none\n"
            "risks:\n  - condition: none\n"
            "implementation:\n  current: .\n"
            "verification:\n  test_cases:\n"
            "    - name: happy\n      description: ok\n"
            "      input: {a: 1}\n      expected_output: {b: 2}\n"
            "      validates_constraint: c1\n"
        )
        result = json.loads(review_intent_tool(yaml_str))
        examples = result["review_gate"]["worked_examples"]
        assert len(examples) == 1
        assert examples[0]["name"] == "happy"
        assert examples[0]["source"] == "verification.test_cases"

    def test_ready_when_no_guessed(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: c1\n    requirement: x\n    test: t.py::t\n"
            "    assumption_status: KNOWN\n"
        )
        result = json.loads(review_intent_tool(yaml_str))
        assert result["review_gate"]["status"] == "READY"


class TestReviewGateValidate:
    def test_invalid_assumption_status_warns(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: c1\n    requirement: x\n    test: t.py::t\n"
            "    assumption_status: bogus\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert any("assumption_status" in w for w in result["warnings"])
        assert result["valid"] is True

    def test_guessed_incomplete_signoff_warns(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: c1\n    requirement: x\n    test: t.py::t\n"
            "    assumption_status: GUESSED\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert any("review_signoff" in w for w in result["warnings"])

    def test_missing_assumption_status_suggests(self):
        yaml_str = _intent_with(
            "constraints:\n  - name: c1\n    requirement: x\n    test: t.py::t\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert any("assumption_status" in s for s in result["suggestions"])


class TestReviewGateHelpers:
    def test_signoff_missing_fields(self):
        assert signoff_missing_fields({"assumption_status": "KNOWN"}) == []
        missing = signoff_missing_fields({"assumption_status": "GUESSED"})
        assert "review_signoff" in missing
        partial = signoff_missing_fields({
            "assumption_status": "GUESSED",
            "review_signoff": {
                "concrete_example": "x",
                "counter_example": "y",
                "human_acknowledged": False,
            },
        })
        assert "human_acknowledged" in partial

    def test_compute_risk_score_guessed_beats_known(self):
        low = compute_risk_score({"assumption_status": "KNOWN", "consequence_if_violated": "ok"})
        high = compute_risk_score({
            "assumption_status": "GUESSED",
            "consequence_if_violated": "critical",
            "conflict_prone": True,
        })
        assert high > low
