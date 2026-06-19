# mcp_server/tools/review_gate.py

"""Tool: ivd_review_intent — human review gate packet."""

import json
import re
from typing import Dict, List, Optional

import yaml
from termcolor import colored

from mcp_server.tools.client_enforcement import build_client_enforcement_from_review_gate

LOG = "IVD Tools"

ALLOWED_ASSUMPTION_STATUS = ("KNOWN", "ASSUMED", "GUESSED")
_CONSEQUENCE_HIGH = re.compile(r"\b(high|critical|severe|catastrophic|unacceptable)\b", re.I)
_CONSEQUENCE_LOW = re.compile(r"\b(low|minor|trivial|negligible)\b", re.I)
_LIKELIHOOD_WEIGHTS = {"GUESSED": 3, "ASSUMED": 2, "KNOWN": 1}


def _consequence_weight(constraint: dict) -> int:
    text = str(constraint.get("consequence_if_violated", ""))
    if _CONSEQUENCE_HIGH.search(text):
        return 3
    if _CONSEQUENCE_LOW.search(text):
        return 1
    return 2


def _likelihood_weight(assumption_status: Optional[str]) -> int:
    if assumption_status in _LIKELIHOOD_WEIGHTS:
        return _LIKELIHOOD_WEIGHTS[assumption_status]
    return 2


def compute_risk_score(constraint: dict) -> int:
    score = _consequence_weight(constraint) * _likelihood_weight(constraint.get("assumption_status"))
    if constraint.get("conflict_prone") is True:
        score += 1
    entropy = str(constraint.get("entropy", "")).lower()
    if entropy and "near-zero" not in entropy:
        score += 1
    if constraint.get("test_provenance") == "ai_generated":
        score += 1
    return min(score, 12)


def signoff_missing_fields(constraint: dict) -> List[str]:
    """Fields still required for a GUESSED constraint review sign-off."""
    if constraint.get("assumption_status") != "GUESSED":
        return []
    signoff = constraint.get("review_signoff")
    if not isinstance(signoff, dict):
        return ["review_signoff", "concrete_example", "counter_example"]
    missing = []
    for field in ("concrete_example", "counter_example"):
        val = signoff.get(field)
        if not isinstance(val, str) or not val.strip():
            missing.append(field)
    if signoff.get("human_acknowledged") is not True:
        missing.append("human_acknowledged")
    return missing


def validate_assumption_fields(
    cname: str,
    constraint: dict,
    warnings: list,
    assumption_absent_count: int,
) -> int:
    """Report-only human review gate checks for ivd_validate. Returns updated absent count."""
    status = constraint.get("assumption_status")
    if status is None:
        return assumption_absent_count + 1
    if status not in ALLOWED_ASSUMPTION_STATUS:
        warnings.append(
            f"Constraint '{cname}' has unrecognized assumption_status '{status}' — "
            f"use one of {', '.join(ALLOWED_ASSUMPTION_STATUS)} (human review gate)"
        )
        return assumption_absent_count
    missing = signoff_missing_fields(constraint)
    if missing:
        warnings.append(
            f"Constraint '{cname}' is GUESSED but review_signoff is incomplete — "
            f"missing: {', '.join(missing)}"
        )
    return assumption_absent_count


def _extract_worked_examples(artifact: dict) -> List[dict]:
    verification = artifact.get("verification")
    if not isinstance(verification, dict):
        return []
    cases = verification.get("test_cases")
    if not isinstance(cases, list):
        return []
    examples = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        examples.append({
            "name": case.get("name", "unnamed"),
            "description": case.get("description"),
            "input": case.get("input"),
            "expected_output": case.get("expected_output"),
            "validates_constraint": case.get("validates_constraint"),
            "source": "verification.test_cases",
        })
    return examples


def build_review_gate(artifact: dict) -> dict:
    constraints = artifact.get("constraints")
    if not isinstance(constraints, list):
        return {
            "status": "NO_CONSTRAINTS",
            "ranked_constraints": [],
            "worked_examples": _extract_worked_examples(artifact),
            "pending_signoffs": [],
            "note": "No constraints block — nothing to rank for human review.",
        }

    ranked = []
    pending = []
    for i, c in enumerate(constraints):
        if not isinstance(c, dict):
            continue
        cname = c.get("name", f"#{i + 1}")
        missing = signoff_missing_fields(c)
        entry = {
            "name": cname,
            "risk_score": compute_risk_score(c),
            "assumption_status": c.get("assumption_status"),
            "consequence_if_violated": c.get("consequence_if_violated"),
            "conflict_prone": c.get("conflict_prone") is True,
            "needs_signoff": c.get("assumption_status") == "GUESSED",
            "signoff_complete": c.get("assumption_status") == "GUESSED" and not missing,
            "missing_signoff_fields": missing,
        }
        ranked.append(entry)
        if missing:
            pending.append(cname)

    ranked.sort(key=lambda x: (-x["risk_score"], x["name"]))

    if pending:
        status = "PENDING_SIGNOFF"
        note = (
            "One or more GUESSED constraints lack a complete review_signoff "
            "(concrete_example, counter_example, human_acknowledged: true). "
            "Present ranked_constraints and worked_examples to the human; do not implement until cleared."
        )
    else:
        guessed = [r["name"] for r in ranked if r.get("assumption_status") == "GUESSED"]
        if guessed:
            status = "APPROVED"
            note = (
                "All GUESSED constraints have complete review_signoff with human_acknowledged. "
                "Proceed to Rule 4 stress test then implementation."
            )
        else:
            status = "READY"
            note = (
                "No GUESSED constraints require sign-off. Review ranked_constraints and "
                "worked_examples before implementation (P6 step 3)."
            )

    return {
        "status": status,
        "ranked_constraints": ranked,
        "worked_examples": _extract_worked_examples(artifact),
        "pending_signoffs": pending,
        "note": note,
    }


def review_intent_tool(artifact_yaml: str) -> str:
    """Build a human review gate packet for an intent artifact."""
    print(colored(f"[{LOG}] ivd_review_intent", "cyan"))

    try:
        artifact = yaml.safe_load(artifact_yaml)
    except yaml.YAMLError as e:
        return json.dumps({
            "ok": False,
            "errors": [f"YAML parse error: {e}"],
            "review_gate": None,
        }, indent=2)

    if artifact is None or not isinstance(artifact, dict):
        return json.dumps({
            "ok": False,
            "errors": ["Empty or invalid artifact"],
            "review_gate": None,
        }, indent=2)

    gate = build_review_gate(artifact)
    result = {
        "ok": True,
        "errors": [],
        "artifact_type": "intent",
        "validation_level": "structure_only",
        "review_gate": gate,
        "note": (
            "Structure-only review packet — does not auto-approve. The agent must obtain "
            "explicit human sign-off on each pending GUESSED constraint before implementing."
        ),
    }
    client_enforcement = build_client_enforcement_from_review_gate(gate)
    if client_enforcement:
        result["client_enforcement"] = client_enforcement
    print(colored(
        f"[{LOG}] review_gate status={gate['status']} pending={len(gate['pending_signoffs'])}",
        "green" if gate["status"] in ("READY", "APPROVED") else "yellow",
    ))
    return json.dumps(result, indent=2)
