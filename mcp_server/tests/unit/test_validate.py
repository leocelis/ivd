# mcp_server/tests/unit/test_validate.py

"""Unit tests for ivd_validate tool."""

import json

from mcp_server.tools.validate import validate_artifact_tool


# ---------------------------------------------------------------------------
# Helper: build a complete, structurally-valid intent with a given constraints
# block (and optional extra top-level YAML). Lets the external-oracle / joint-
# satisfaction tests assert behavior without tripping required-section errors.
# ---------------------------------------------------------------------------

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


class TestExternalOracleGating:
    """Fix 1 (red-team remediation): test_provenance gating of constraint PASS."""

    def test_ai_generated_flagged_needs_oracle(self):
        """A constraint whose only evidence is an AI-generated test is reported
        NEEDS_EXTERNAL_ORACLE — and the artifact is still structurally valid."""
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: only_ai\n    requirement: x\n    test: t.py::t\n"
            "    test_provenance: ai_generated\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert result["valid"] is True
        assert result["errors"] == []
        gating = result.get("verification_gating")
        assert gating is not None
        assert "only_ai" in gating["constraints_needing_external_oracle"]
        assert gating["status"] == "NEEDS_EXTERNAL_ORACLE"

    def test_human_authored_not_gated(self):
        """human_authored / execution_derived provenance does NOT need an oracle."""
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: human_test\n    requirement: x\n    test: t.py::t\n"
            "    test_provenance: human_authored\n"
            "  - name: exec_test\n    requirement: y\n    test: t.py::u\n"
            "    test_provenance: execution_derived\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert "verification_gating" not in result

    def test_invalid_provenance_warns(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: c1\n    requirement: x\n    test: t.py::t\n"
            "    test_provenance: bogus_value\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert any("provenance" in w.lower() for w in result["warnings"])
        # Bad provenance is a warning, not an error.
        assert result["valid"] is True

    def test_missing_provenance_suggests(self):
        """A test without declared provenance triggers an aggregate suggestion."""
        yaml_str = _intent_with(
            "constraints:\n  - name: c1\n    requirement: x\n    test: t.py::t\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert any("test_provenance" in s for s in result["suggestions"])


class TestConflictProne:
    """Fix 4 (red-team remediation): conflict_prone constraints need anchoring."""

    def test_conflict_prone_requires_antipattern(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: weird_rule\n    requirement: x\n    test: t.py::t\n"
            "    conflict_prone: true\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert any("anti_pattern" in w for w in result["warnings"])

    def test_conflict_prone_with_anchor_passes(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: weird_rule\n    requirement: x\n    test: t.py::t\n"
            "    conflict_prone: true\n"
            "    anti_pattern: 'common pattern is A; this needs NOT-A because reasons'\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert not any("anti_pattern" in w for w in result["warnings"])

    def test_conflict_prone_without_test_warns(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: weird_rule\n    requirement: x\n"
            "    conflict_prone: true\n"
            "    anti_pattern: 'common pattern is A; this needs NOT-A'\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert any("conflict_prone" in w and "test" in w for w in result["warnings"])


class TestJointSatisfaction:
    """Fix 3 (red-team remediation): individual-pass != joint-pass."""

    def test_three_constraints_without_satisfiability_warns(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: a\n    requirement: x\n    test: t.py::a\n"
            "  - name: b\n    requirement: y\n    test: t.py::b\n"
            "  - name: c\n    requirement: z\n    test: t.py::c\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert any("constraint_satisfiability" in w for w in result["warnings"])

    def test_three_constraints_with_block_no_warn(self):
        extra = (
            "constraint_satisfiability:\n"
            "  conflicts_checked: true\n"
            "  simultaneous_satisfaction: all good\n"
        )
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: a\n    requirement: x\n    test: t.py::a\n"
            "  - name: b\n    requirement: y\n    test: t.py::b\n"
            "  - name: c\n    requirement: z\n    test: t.py::c\n",
            extra=extra,
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert not any(
            "3+ constraints but no 'constraint_satisfiability'" in w
            for w in result["warnings"]
        )

    def test_two_constraints_no_joint_warning(self):
        """The joint-satisfaction nudge must not fire below the 3-constraint threshold."""
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: a\n    requirement: x\n    test: t.py::a\n"
            "  - name: b\n    requirement: y\n    test: t.py::b\n"
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert not any("constraint_satisfiability" in w for w in result["warnings"])

    def test_satisfiability_block_missing_field_warns(self):
        extra = "constraint_satisfiability:\n  conflicts_checked: true\n"
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: a\n    requirement: x\n    test: t.py::a\n",
            extra=extra,
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert any("simultaneous_satisfaction" in w for w in result["warnings"])


class TestBackwardCompatibility:
    """The critical constraint: new checks never produce errors or break legacy intents."""

    def test_new_fields_never_produce_errors(self, sample_intent_yaml):
        # Legacy intent (no new fields) stays valid with zero errors.
        legacy = json.loads(validate_artifact_tool(sample_intent_yaml, "intent"))
        assert legacy["valid"] is True
        assert legacy["errors"] == []

        # An intent exercising every new field also adds no errors.
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: a\n    requirement: x\n    test: t.py::a\n"
            "    test_provenance: ai_generated\n"
            "  - name: b\n    requirement: y\n    test: t.py::b\n"
            "    conflict_prone: true\n    anti_pattern: 'A vs NOT-A'\n"
            "    test_provenance: execution_derived\n"
            "  - name: c\n    requirement: z\n    test: t.py::c\n"
            "    test_provenance: human_authored\n",
            extra=(
                "constraint_satisfiability:\n"
                "  conflicts_checked: true\n"
                "  simultaneous_satisfaction: ok\n"
            ),
        )
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert result["errors"] == []
        assert result["valid"] is True

    def test_malformed_constraint_entry_does_not_crash(self):
        """A non-dict constraint entry is skipped, not fatal."""
        yaml_str = _intent_with("constraints:\n  - just a string\n  - 42\n")
        result = json.loads(validate_artifact_tool(yaml_str, "intent"))
        assert "valid" in result  # did not raise
