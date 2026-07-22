# mcp_server/tests/unit/test_attest.py

"""Unit tests for ivd_attest — the process-attestation gate.

Every test here is the executable half of a constraint in
`mcp_server/intents/attest_intent.yaml`; the node ids match that artifact's
`test:` fields exactly, so `ivd_validate` can resolve them on disk.

Provenance: human_authored. These assertions are the external oracle for the
attest tool — deliberately not generated from the implementation they check
(Rule 3: never let the code-under-test be its own oracle).
"""

import inspect
import json
from pathlib import Path

import yaml

from mcp_server.tools import attest as attest_module
from mcp_server.tools.attest import SEGMENTATION_THRESHOLD, attest_tool
from mcp_server.tools.validate import validate_artifact_tool

# ---------------------------------------------------------------------------
# Builders — keep each test's intent explicit about the one thing it exercises
# ---------------------------------------------------------------------------


def _artifact(n: int = 3, provenance: str = "human_authored") -> str:
    """An intent with `n` constraints, all sharing one test_provenance."""
    constraints = [
        {
            "name": f"c{i}",
            "requirement": f"requirement {i}",
            "test": f"tests/test_x.py::test_c{i}",
            "test_provenance": provenance,
        }
        for i in range(n)
    ]
    return yaml.safe_dump({"constraints": constraints})


def _attestation(**overrides) -> str:
    """A fully-compliant attestation for a 3-constraint intent; override to break one thing."""
    base = {
        "implementation_mode": "segmented",
        "reread_from_disk": True,
        "constraint_status": {"c0": "PASS", "c1": "PASS", "c2": "PASS"},
        "joint_satisfaction": True,
        "stress_test": {"probes_run": list(attest_module.STRESS_PROBES)},
    }
    base.update(overrides)
    return yaml.safe_dump(base)


def _run(artifact: str, attestation: str) -> dict:
    return json.loads(attest_tool(artifact, attestation))


# ---------------------------------------------------------------------------
# Rule 1 — segmentation is mandatory at 3+ constraints
# ---------------------------------------------------------------------------


class TestRuleOneSegmentation:
    def test_single_pass_at_threshold_is_violation(self):
        """constraint: segmentation_violation_detected"""
        result = _run(_artifact(SEGMENTATION_THRESHOLD), _attestation(implementation_mode="single_pass"))

        assert result["verdict"] == "VIOLATION"
        rules = [v["rule"] for v in result["violations"]]
        assert "Rule 1" in rules
        seg = next(v for v in result["violations"] if v["check"] == "segmentation")
        assert str(SEGMENTATION_THRESHOLD) in seg["detail"]

    def test_single_pass_below_threshold_is_allowed(self):
        """Rule 1 permits single-pass for 1-2 constraints — must not over-fire."""
        artifact = _artifact(2)
        attestation = _attestation(
            implementation_mode="single_pass",
            constraint_status={"c0": "PASS", "c1": "PASS"},
            joint_satisfaction=None,
        )
        result = _run(artifact, attestation)

        assert result["verdict"] == "COMPLIANT"
        assert result["violations"] == []

    def test_unreported_mode_at_threshold_is_incomplete(self):
        artifact = _artifact(SEGMENTATION_THRESHOLD)
        attestation = _attestation(implementation_mode=None)
        result = _run(artifact, attestation)

        assert result["verdict"] == "INCOMPLETE"
        assert any(i["check"] == "segmentation" for i in result["incomplete"])


# ---------------------------------------------------------------------------
# Rule 2 step 1 — re-read the intent from disk
# ---------------------------------------------------------------------------


class TestRuleTwoReread:
    def test_missing_reread_is_violation(self):
        """constraint: reread_from_disk_required"""
        result = _run(_artifact(3), _attestation(reread_from_disk=False))

        assert result["verdict"] == "VIOLATION"
        assert any(v["check"] == "reread_from_disk" for v in result["violations"])

    def test_absent_reread_field_is_also_violation(self):
        """Absence must fail closed — silence is not compliance."""
        attestation = yaml.safe_dump({
            "implementation_mode": "segmented",
            "constraint_status": {"c0": "PASS", "c1": "PASS", "c2": "PASS"},
            "joint_satisfaction": True,
        })
        result = _run(_artifact(3), attestation)

        assert result["verdict"] == "VIOLATION"
        assert any(v["check"] == "reread_from_disk" for v in result["violations"])


# ---------------------------------------------------------------------------
# Rule 2 step 4 — per-constraint coverage
# ---------------------------------------------------------------------------


class TestRuleTwoCoverage:
    def test_missing_constraint_status_is_incomplete(self):
        """constraint: per_constraint_coverage_enforced"""
        attestation = _attestation(constraint_status={"c0": "PASS", "c1": "PASS"})  # c2 omitted
        result = _run(_artifact(3), attestation)

        assert result["verdict"] == "INCOMPLETE"
        gap = next(i for i in result["incomplete"] if i["check"] == "coverage")
        assert "c2" in gap["detail"], "the omitted constraint must be named, not just counted"

    def test_unknown_constraint_in_attestation_warns(self):
        attestation = _attestation(
            constraint_status={"c0": "PASS", "c1": "PASS", "c2": "PASS", "ghost": "PASS"}
        )
        result = _run(_artifact(3), attestation)

        assert any("ghost" in w for w in result["warnings"])

    def test_unrecognised_status_warns(self):
        attestation = _attestation(constraint_status={"c0": "probably fine", "c1": "PASS", "c2": "PASS"})
        result = _run(_artifact(3), attestation)

        assert any("probably fine" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Rule 2 — joint satisfaction at 3+ constraints
# ---------------------------------------------------------------------------


class TestRuleTwoJoint:
    def test_joint_required_at_threshold(self):
        """constraint: joint_satisfaction_required_at_threshold"""
        attestation = yaml.safe_dump({
            "implementation_mode": "segmented",
            "reread_from_disk": True,
            "constraint_status": {"c0": "PASS", "c1": "PASS", "c2": "PASS"},
        })
        result = _run(_artifact(3), attestation)

        assert result["verdict"] == "INCOMPLETE"
        assert any(i["check"] == "joint_satisfaction" for i in result["incomplete"])

    def test_joint_not_required_below_threshold(self):
        attestation = yaml.safe_dump({
            "implementation_mode": "segmented",
            "reread_from_disk": True,
            "constraint_status": {"c0": "PASS", "c1": "PASS"},
        })
        result = _run(_artifact(2), attestation)

        assert not any(i["check"] == "joint_satisfaction" for i in result["incomplete"])


# ---------------------------------------------------------------------------
# Rule 3 — provenance cross-check (artifact-derived; overrides the claim)
# ---------------------------------------------------------------------------


class TestProvenanceCrossCheck:
    def test_ai_generated_pass_is_downgraded(self):
        """constraint: provenance_cross_check_overrides_claim

        The load-bearing check: the agent claims PASS, the artifact says the only
        evidence is an AI-written test, and the artifact wins.
        """
        result = _run(_artifact(3, provenance="ai_generated"), _attestation())

        assert len(result["provenance_overrides"]) == 3
        for override in result["provenance_overrides"]:
            assert override["claimed"] == "PASS"
            assert override["effective"] == "NEEDS_EXTERNAL_ORACLE"
        assert all(s == "NEEDS_EXTERNAL_ORACLE" for s in result["effective_constraint_status"].values())

    def test_execution_oracle_rescues_ai_generated(self):
        """An execution_derived oracle is the documented escape hatch — must not over-fire."""
        constraints = [{
            "name": "c0",
            "requirement": "r",
            "test": "tests/test_x.py::test_c0",
            "test_provenance": "ai_generated",
            "execution_oracle": {"type": "golden_fixture"},
        }]
        artifact = yaml.safe_dump({"constraints": constraints})
        attestation = yaml.safe_dump({
            "implementation_mode": "segmented",
            "reread_from_disk": True,
            "constraint_status": {"c0": "PASS"},
        })
        result = _run(artifact, attestation)

        assert result["provenance_overrides"] == []
        assert result["effective_constraint_status"]["c0"] == "PASS"

    def test_human_authored_pass_is_untouched(self):
        result = _run(_artifact(3, provenance="human_authored"), _attestation())

        assert result["provenance_overrides"] == []
        assert result["verdict"] == "COMPLIANT"


# ---------------------------------------------------------------------------
# ivd_validate — termination contract for workflow/system intents
# ---------------------------------------------------------------------------


def _levelled_intent(level: str, evaluation: dict | None = None) -> str:
    doc = {
        "scope": {"level": level},
        "intent": {"summary": "s", "goal": "g", "success_metric": "m"},
        "constraints": [{"name": "c0", "requirement": "r", "test": "t.py::t"}],
        "rationale": {"decision": "d"},
        "alternatives": [{"name": "none"}],
        "risks": [{"condition": "none"}],
        "implementation": {"current": "."},
        "verification": {"test_cases": []},
    }
    if evaluation:
        doc["evaluation"] = evaluation
    return yaml.safe_dump(doc)


class TestTerminationExpectation:
    def test_workflow_without_cycle_warns(self):
        """constraint: termination_expected_for_workflow_system"""
        result = json.loads(validate_artifact_tool(_levelled_intent("workflow"), "intent"))

        assert result["errors"] == [], "termination is a warning, never an error"
        assert any("termination contract" in w for w in result["warnings"])

    def test_system_level_also_warns(self):
        result = json.loads(validate_artifact_tool(_levelled_intent("system"), "intent"))
        assert any("termination contract" in w for w in result["warnings"])

    def test_task_level_is_exempt(self):
        """A task intent is one unit of work, not a loop — must not over-fire."""
        result = json.loads(validate_artifact_tool(_levelled_intent("task"), "intent"))
        assert not any("termination contract" in w for w in result["warnings"])

    def test_complete_cycle_satisfies(self):
        evaluation = {"cycle": {"max_iterations": 3, "stop_when": "criteria met", "escalate_when": "cannot"}}
        result = json.loads(validate_artifact_tool(_levelled_intent("workflow", evaluation), "intent"))
        assert not any("termination contract" in w for w in result["warnings"])

    def test_bound_without_stop_condition_still_warns(self):
        """max_iterations alone is not a termination contract — you also need a stop condition."""
        evaluation = {"cycle": {"max_iterations": 3}}
        result = json.loads(validate_artifact_tool(_levelled_intent("workflow", evaluation), "intent"))
        assert any("termination contract" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Architecture invariant — structure-only
# ---------------------------------------------------------------------------


class TestArchitecture:
    def test_no_side_effects(self):
        """constraint: structure_only_no_side_effects

        Structural assertion: the attest module must not reach for an LLM, the
        network, or the filesystem. Checked against the source rather than by
        mocking, so it holds for any future edit to the module.
        """
        source = inspect.getsource(attest_module)

        for forbidden in ("import openai", "import requests", "import httpx", "urllib.request", "subprocess"):
            assert forbidden not in source, f"attest must stay structure-only — found {forbidden!r}"

        for write_call in ("open(", ".write_text(", ".mkdir(", "shutil."):
            assert write_call not in source, f"attest must not touch the filesystem — found {write_call!r}"

    def test_returns_json_string(self):
        out = attest_tool(_artifact(1), _attestation(constraint_status={"c0": "PASS"}))
        assert isinstance(out, str)
        assert json.loads(out)["tool"] == "ivd_attest"

    def test_malformed_yaml_degrades_gracefully(self):
        result = json.loads(attest_tool("{{not yaml", _attestation()))
        assert result["ok"] is False
        assert "error" in result

    def test_intent_artifact_is_on_disk_and_valid(self):
        """The intent governing this feature must exist and validate (Principle 1)."""
        path = Path(__file__).resolve().parents[3] / "mcp_server" / "intents" / "attest_intent.yaml"
        assert path.is_file(), "attest_intent.yaml must be co-located with the implementation"
        result = json.loads(validate_artifact_tool(path.read_text(), "intent"))
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Joint satisfaction — ALL constraints on the SAME output (Rule 2)
# ---------------------------------------------------------------------------


class TestJointSatisfaction:
    def test_all_constraints_on_one_attestation(self):
        """joint_satisfaction_test for attest_intent.yaml.

        Individual-pass does not imply joint-pass. One attest call, one output,
        every constraint asserted against it simultaneously.
        """
        # An intent that trips segmentation, re-read, coverage, joint AND provenance
        # at once — the maximally-broken case.
        artifact = _artifact(3, provenance="ai_generated")
        attestation = yaml.safe_dump({
            "implementation_mode": "single_pass",          # Rule 1
            "reread_from_disk": False,                     # Rule 2 step 1
            "constraint_status": {"c0": "PASS", "c1": "PASS"},  # c2 omitted -> coverage
            # joint_satisfaction omitted                   -> Rule 2 joint
            "stress_test": {"probes_run": []},             # Rule 4 advisory
        })
        result = _run(artifact, attestation)

        # 1. segmentation_violation_detected
        assert any(v["check"] == "segmentation" for v in result["violations"])
        # 2. reread_from_disk_required
        assert any(v["check"] == "reread_from_disk" for v in result["violations"])
        # 3. per_constraint_coverage_enforced (names the omitted one)
        assert any(i["check"] == "coverage" and "c2" in i["detail"] for i in result["incomplete"])
        # 4. joint_satisfaction_required_at_threshold
        assert any(i["check"] == "joint_satisfaction" for i in result["incomplete"])
        # 5. provenance_cross_check_overrides_claim (claimed PASS -> downgraded)
        assert {o["constraint"] for o in result["provenance_overrides"]} == {"c0", "c1"}
        assert result["effective_constraint_status"]["c0"] == "NEEDS_EXTERNAL_ORACLE"
        # 6. Rule 4 probe coverage surfaced
        assert any("Rule 4 probes" in w for w in result["warnings"])
        # 7. severity ordering holds: a violation outranks incompleteness
        assert result["verdict"] == "VIOLATION"
