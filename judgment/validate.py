# ivd/judgment/validate.py

"""
Judgment engine — validators for the 4 judgment-phase artifact types.

Validators are pure functions: ``(artifact_dict) -> (errors, warnings)``.
They do not touch the filesystem, do not enforce activation gates, and do
not raise exceptions. The MCP-tool layer calls them and wraps the result.

Reference:
  ivd/judgment_layer.md §2 (artifact catalogue).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from judgment.schema import (
    DEPTH_WEIGHT,
    Freshness,
    PATTERN_PROMOTION_THRESHOLD,
    REQUIRED_CODIFIED_FIELDS,
    CapabilitySubtype,
    FixActionType,
)

# Surfaced as tuples for back-compat with existing imports / tests.
VALID_FIX_ACTION_TYPES = tuple(t.value for t in FixActionType)
VALID_CAPABILITY_SUBTYPES = tuple(s.value for s in CapabilitySubtype)
FRESHNESS_STATES = tuple(f.value for f in Freshness)


def validate_baseline(artifact: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    for f in ("domain_id", "leo_domain_depth", "goal_calibration", "pattern_half_life_policy"):
        if f not in artifact:
            errors.append(f"baseline missing required field '{f}'")
    depth = artifact.get("leo_domain_depth")
    if depth and depth not in DEPTH_WEIGHT:
        warnings.append(
            f"baseline.leo_domain_depth '{depth}' invalid; expected {list(DEPTH_WEIGHT.keys())}"
        )
    gc = artifact.get("goal_calibration") or {}
    if not gc.get("qualitative"):
        warnings.append("baseline.goal_calibration.qualitative is empty")
    if not gc.get("measurable"):
        warnings.append("baseline.goal_calibration.measurable is empty (Principle 2)")
    return errors, warnings


def validate_ledger_entry(artifact: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    for f in ("id", "state", "classification"):
        if f not in artifact:
            errors.append(f"ledger_entry missing required field '{f}'")
    state = artifact.get("state")
    if state in ("codified", "paired", "resolved"):
        codified = artifact.get("codified") or {}
        for f in REQUIRED_CODIFIED_FIELDS:
            if not codified.get(f):
                warnings.append(f"ledger_entry in state '{state}' missing codified.{f}")
        fa = codified.get("fix_action_type")
        if fa and fa not in VALID_FIX_ACTION_TYPES:
            warnings.append(
                f"codified.fix_action_type '{fa}' invalid; expected {list(VALID_FIX_ACTION_TYPES)}"
            )
        if (
            fa == FixActionType.CAPABILITY_ADDITION.value
            and codified.get("capability_subtype") not in VALID_CAPABILITY_SUBTYPES
        ):
            warnings.append(
                "codified.fix_action_type=capability_addition requires capability_subtype "
                f"∈ {list(VALID_CAPABILITY_SUBTYPES)}"
            )
    depth = artifact.get("leo_domain_depth")
    if depth and depth not in DEPTH_WEIGHT:
        warnings.append(f"leo_domain_depth '{depth}' invalid; expected {list(DEPTH_WEIGHT.keys())}")
    return errors, warnings


def validate_comparison_pair(artifact: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    for f in ("id", "run_a", "run_b", "observed_differences", "diagnostic_hypotheses"):
        if f not in artifact:
            errors.append(f"comparison_pair missing required field '{f}'")
    for i, dh in enumerate(artifact.get("diagnostic_hypotheses") or []):
        if not isinstance(dh, dict):
            warnings.append(f"diagnostic_hypotheses[{i}] is not a dict")
            continue
        if not dh.get("hypothesis"):
            warnings.append(f"diagnostic_hypotheses[{i}] missing 'hypothesis'")
        if not dh.get("competing_hypotheses"):
            warnings.append(
                f"diagnostic_hypotheses[{i}] missing 'competing_hypotheses' "
                "— Rung-1 discipline requires at least one rival explanation"
            )
    if artifact.get("injection_status") not in (None, "plausible", "corroborated", "rejected"):
        warnings.append(
            "injection_status should be one of: plausible | corroborated | rejected"
        )
    return errors, warnings


def validate_pattern(artifact: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    for f in ("id", "domain", "diagnosed_cause", "members", "member_count", "weighted_confidence"):
        if f not in artifact:
            errors.append(f"pattern missing required field '{f}'")
    if artifact.get("member_count", 0) < PATTERN_PROMOTION_THRESHOLD:
        warnings.append(
            f"pattern.member_count < {PATTERN_PROMOTION_THRESHOLD} "
            "(below promotion threshold — should not be injected)"
        )
    fr = artifact.get("freshness")
    if fr and fr not in FRESHNESS_STATES:
        warnings.append(f"pattern.freshness '{fr}' invalid; expected {list(FRESHNESS_STATES)}")
    return errors, warnings


VALIDATORS = {
    "baseline": validate_baseline,
    "ledger_entry": validate_ledger_entry,
    "comparison_pair": validate_comparison_pair,
    "pattern": validate_pattern,
}
