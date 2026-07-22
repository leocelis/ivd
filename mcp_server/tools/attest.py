# mcp_server/tools/attest.py

"""Tool: ivd_attest — process attestation gate for the IVD workflow.

``ivd_validate`` checks the intent artifact. Nothing checked whether the agent
actually *followed* the method: an agent can skip the Rule 4 stress test,
single-pass nine constraints against Rule 1, never re-read from disk per Rule 2,
and still emit an artifact that validates clean.

That is the read-acknowledge-violate failure mode (framework.md, Principle 6)
turned on IVD's own rules. This tool cannot force compliance — it converts a
silent skip into a reported gap.

Structure-only: no LLM call, no network, no filesystem write. It compares two
documents (the intent artifact and the agent's attestation) and reports.

Verdicts, in increasing severity:
  COMPLIANT   — every checked rule satisfied.
  INCOMPLETE  — the attestation omits something required (coverage, joint verdict).
  VIOLATION   — a mandatory rule was breached (Rule 1 segmentation, Rule 2 re-read).

Honest bound: the attestation is agent-supplied and can be falsified wholesale.
The provenance cross-check is the one assertion derived from the *artifact*
rather than the attestation, so it cannot be overridden by an agent's claim.

Reference: mcp_server/intents/attest_intent.yaml
"""

import json
from typing import Any, Dict, List, Optional, Tuple

import yaml
from termcolor import colored

LOG = "IVD Tools"

# Mirrors validate.py — 3+ constraints is where joint satisfaction and mandatory
# segmentation kick in (Rule 1, Rule 2).
SEGMENTATION_THRESHOLD = 3

VALID_STATUSES = (
    "PASS",
    "FAIL",
    "NEEDS_REVIEW",
    "NEEDS_EXTERNAL_ORACLE",
    "UNVERIFIED",
)

VALID_MODES = ("segmented", "single_pass")

# Rule 4's five adversarial probes.
STRESS_PROBES = (
    "constraint_completeness",
    "implementation_anticipation",
    "assumption_challenge",
    "constraint_satisfiability",
    "knowledge_conflict",
)

_ALLOWED_ORACLE_TYPES = ("golden_fixture", "property_test", "differential_test")


def _load(doc: str, label: str) -> Tuple[Optional[dict], Optional[str]]:
    """Parse a YAML document, returning (parsed, error_message)."""
    try:
        parsed = yaml.safe_load(doc)
    except yaml.YAMLError as e:
        return None, f"{label} is not valid YAML: {e}"
    if not isinstance(parsed, dict):
        return None, f"{label} must be a YAML mapping"
    return parsed, None


def _constraints(artifact: dict) -> List[dict]:
    raw = artifact.get("constraints")
    return [c for c in raw if isinstance(c, dict)] if isinstance(raw, list) else []


def _needs_external_oracle(constraint: dict) -> bool:
    """True when a constraint's only evidence is an AI-written test.

    Rule 3: an ai_generated test alone can never mark a constraint PASS — it
    tends to ratify the code rather than catch it. An execution_derived
    provenance rescues it only with a structural execution_oracle.
    """
    provenance = constraint.get("test_provenance")
    if provenance != "ai_generated":
        return False
    oracle = constraint.get("execution_oracle")
    if isinstance(oracle, dict) and oracle.get("type") in _ALLOWED_ORACLE_TYPES:
        return False
    return True


def attest_tool(artifact_yaml: str, attestation_yaml: str) -> str:
    """Check an agent's process attestation against the intent it implemented."""
    print(colored(f"[{LOG}] ivd_attest", "cyan"))

    artifact, err = _load(artifact_yaml, "artifact_yaml")
    if err:
        return json.dumps({"ok": False, "tool": "ivd_attest", "error": err}, indent=2)

    attestation, err = _load(attestation_yaml, "attestation_yaml")
    if err:
        return json.dumps({"ok": False, "tool": "ivd_attest", "error": err}, indent=2)

    constraints = _constraints(artifact)
    count = len(constraints)

    violations: List[Dict[str, str]] = []
    incomplete: List[Dict[str, str]] = []
    warnings: List[str] = []

    # ── Rule 1: constraint-segmented implementation is mandatory at 3+ ──────
    mode = attestation.get("implementation_mode")
    if mode is not None and mode not in VALID_MODES:
        warnings.append(
            f"implementation_mode '{mode}' unrecognized — use one of {', '.join(VALID_MODES)}"
        )
    if count >= SEGMENTATION_THRESHOLD and mode == "single_pass":
        violations.append({
            "rule": "Rule 1",
            "check": "segmentation",
            "detail": (
                f"{count} constraints implemented single-pass. Rule 1 makes "
                f"constraint-segmented implementation mandatory at "
                f"{SEGMENTATION_THRESHOLD}+ constraints."
            ),
        })
    elif count >= SEGMENTATION_THRESHOLD and mode is None:
        incomplete.append({
            "rule": "Rule 1",
            "check": "segmentation",
            "detail": "implementation_mode not reported (expected 'segmented' or 'single_pass').",
        })

    # ── Rule 2 step 1: re-read the intent from disk ─────────────────────────
    if attestation.get("reread_from_disk") is not True:
        violations.append({
            "rule": "Rule 2 (step 1)",
            "check": "reread_from_disk",
            "detail": (
                "Intent was not re-read from disk before verification. This "
                "counteracts the lost-in-the-middle effect; skipping it means "
                "verifying against possibly-drifted context."
            ),
        })

    # ── Rule 2 step 4: per-constraint coverage ──────────────────────────────
    reported = attestation.get("constraint_status")
    reported = reported if isinstance(reported, dict) else {}

    resolved: Dict[str, str] = {}
    for c in constraints:
        name = c.get("name")
        if not name:
            continue
        claimed = reported.get(name)
        if claimed is None:
            incomplete.append({
                "rule": "Rule 2 (step 4)",
                "check": "coverage",
                "detail": f"Constraint '{name}' has no status in the attestation.",
            })
            continue
        if claimed not in VALID_STATUSES:
            warnings.append(
                f"Constraint '{name}' status '{claimed}' unrecognized — "
                f"use one of {', '.join(VALID_STATUSES)}"
            )
        resolved[name] = claimed

    unknown = set(reported) - {c.get("name") for c in constraints}
    for extra in sorted(unknown):
        warnings.append(f"Attestation reports '{extra}', which is not a constraint in this intent.")

    # ── Rule 3 provenance cross-check (artifact-derived, not self-graded) ───
    # This is the one assertion an agent cannot talk its way past: it is computed
    # from the artifact's own provenance fields, and it overrides the claim.
    overrides: List[Dict[str, str]] = []
    for c in constraints:
        name = c.get("name")
        if not name or name not in resolved:
            continue
        if resolved[name] == "PASS" and _needs_external_oracle(c):
            overrides.append({
                "constraint": name,
                "claimed": "PASS",
                "effective": "NEEDS_EXTERNAL_ORACLE",
                "reason": (
                    "test_provenance is ai_generated with no execution_oracle — "
                    "Rule 3 forbids an AI-written test from marking its own "
                    "implementation PASS."
                ),
            })
            resolved[name] = "NEEDS_EXTERNAL_ORACLE"

    # ── Rule 2: joint satisfaction is required at 3+ constraints ────────────
    joint = attestation.get("joint_satisfaction")
    if count >= SEGMENTATION_THRESHOLD and joint is None:
        incomplete.append({
            "rule": "Rule 2 (joint)",
            "check": "joint_satisfaction",
            "detail": (
                f"{count} constraints require a joint_satisfaction verdict "
                "(true | false | NEEDS_JOINT_TEST). Individual-pass does not "
                "imply joint-pass."
            ),
        })

    # ── Rule 4: stress-test probe coverage (advisory) ───────────────────────
    stress = attestation.get("stress_test")
    probes_run = []
    if isinstance(stress, dict):
        raw_probes = stress.get("probes_run")
        if isinstance(raw_probes, list):
            probes_run = [p for p in raw_probes if isinstance(p, str)]
    missing_probes = [p for p in STRESS_PROBES if p not in probes_run]
    if missing_probes:
        warnings.append(
            "Rule 4 probes not reported as run: " + ", ".join(missing_probes)
        )

    # ── Verdict ─────────────────────────────────────────────────────────────
    if violations:
        verdict = "VIOLATION"
    elif incomplete:
        verdict = "INCOMPLETE"
    else:
        verdict = "COMPLIANT"

    result: Dict[str, Any] = {
        "ok": True,
        "tool": "ivd_attest",
        "verdict": verdict,
        "constraint_count": count,
        "violations": violations,
        "incomplete": incomplete,
        "provenance_overrides": overrides,
        "effective_constraint_status": resolved,
        "warnings": warnings,
        "checks_performed": [
            "Rule 1 — segmentation mandatory at 3+ constraints",
            "Rule 2 step 1 — intent re-read from disk",
            "Rule 2 step 4 — per-constraint status coverage",
            "Rule 2 — joint satisfaction reported at 3+ constraints",
            "Rule 3 — provenance cross-check (artifact-derived, overrides claims)",
            "Rule 4 — stress-test probe coverage (advisory)",
        ],
        "note": (
            "Structure-only: no LLM, no network, no disk write. The attestation is "
            "agent-supplied and can be falsified; provenance_overrides is the one "
            "result derived from the artifact rather than the attestation."
        ),
    }

    colour = {"COMPLIANT": "green", "INCOMPLETE": "yellow", "VIOLATION": "red"}[verdict]
    print(colored(f"[{LOG}] ivd_attest verdict: {verdict}", colour))
    return json.dumps(result, indent=2)
