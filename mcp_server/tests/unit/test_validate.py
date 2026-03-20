# mcp_server/tests/unit/test_validate.py

"""Unit tests for ivd_validate tool."""

import json

from mcp_server.tools.validate import validate_artifact_tool


class TestValidateArtifact:
    """Tests for ivd_validate."""

    def test_valid_intent_passes(self, sample_intent_yaml):
        result = json.loads(validate_artifact_tool(sample_intent_yaml, "intent"))
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_invalid_intent_has_errors(self, bad_intent_yaml):
        result = json.loads(validate_artifact_tool(bad_intent_yaml, "intent"))
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_malformed_yaml_returns_parse_error(self):
        result = json.loads(validate_artifact_tool("{{not: valid: yaml: [[[", "intent"))
        assert result["valid"] is False
        assert any("parse error" in e.lower() for e in result["errors"])

    def test_empty_yaml_has_errors(self):
        result = json.loads(validate_artifact_tool("", "intent"))
        assert result["valid"] is False
        assert any("empty" in e.lower() for e in result["errors"])

    def test_missing_constraints_reported(self):
        yaml_str = "intent:\n  summary: test\n  goal: test\n  success_metric: test\n"
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert result["valid"] is False
        error_text = " ".join(result["errors"])
        assert "constraints" in error_text.lower()

    def test_constraint_without_test_warns(self):
        yaml_str = (
            "intent:\n  summary: test\n  goal: test\n  success_metric: test\n"
            "constraints:\n  - name: c1\n    requirement: must work\n"
            "rationale:\n  decision: test\n  reasoning: test\n"
            "alternatives:\n  - name: none\n"
            "risks:\n  - condition: none\n"
            "implementation:\n  current: .\n"
            "verification:\n  test_cases: []\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        # Should warn about missing test field on constraint
        assert any("test" in w.lower() for w in result["warnings"])

    def test_returns_artifact_type(self, sample_intent_yaml):
        result = json.loads(validate_artifact_tool(sample_intent_yaml, "intent"))
        assert result["artifact_type"] == "intent"

    def test_unknown_type_warns(self, sample_intent_yaml):
        result = json.loads(validate_artifact_tool(sample_intent_yaml, "unknown"))
        assert any("unknown" in w.lower() for w in result["warnings"])

    def test_result_structure(self, sample_intent_yaml):
        result = json.loads(validate_artifact_tool(sample_intent_yaml, "intent"))
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert "suggestions" in result
        assert "validation_level" in result
