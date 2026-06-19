# mcp_server/tools/client_enforcement.py

"""Machine-readable client enforcement signals for verification gating."""

from typing import Any, Dict, List, Optional


def _active_gates_from_verification_gating(gating: Dict[str, Any]) -> List[str]:
    gates: List[str] = []
    top_status = gating.get("status")
    if top_status:
        gates.append(str(top_status))
    joint = gating.get("joint_satisfaction") or {}
    if isinstance(joint, dict) and joint.get("status"):
        gates.append(f"joint_satisfaction:{joint['status']}")
    conflict = gating.get("conflict_prone") or {}
    if isinstance(conflict, dict) and conflict.get("status"):
        gates.append(f"conflict_prone:{conflict['status']}")
    return gates


def build_client_enforcement_from_gating(
    verification_gating: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Build client_enforcement when ivd_validate reports active verification gating."""
    if not verification_gating:
        return None
    gates = _active_gates_from_verification_gating(verification_gating)
    if not gates:
        return None
    return {
        "implementation_complete_blocked": True,
        "monitoring_event": "verification_gating_active",
        "active_gates": gates,
        "clear_when": [
            "All verification_gating conditions cleared in the intent artifact",
            "Re-run ivd_validate — client_enforcement absent when gating is absent",
        ],
        "recommended_tools": ["ivd_review_intent", "ivd_run_constraint_tests"],
    }


def build_client_enforcement_from_review_gate(
    review_gate: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Build client_enforcement when ivd_review_intent has pending human sign-off."""
    if not review_gate:
        return None
    status = review_gate.get("status")
    pending = review_gate.get("pending_signoffs") or []
    if status != "PENDING_SIGNOFF" and not pending:
        return None
    gates = ["PENDING_SIGNOFF"]
    if pending:
        gates.extend(f"signoff:{name}" for name in pending)
    return {
        "implementation_complete_blocked": True,
        "monitoring_event": "review_gate_pending_signoff",
        "active_gates": gates,
        "clear_when": [
            "Complete review_signoff on each GUESSED constraint (concrete_example, counter_example, human_acknowledged: true)",
            "Re-run ivd_review_intent — status must not be PENDING_SIGNOFF",
        ],
        "recommended_tools": ["ivd_review_intent", "ivd_validate"],
    }
