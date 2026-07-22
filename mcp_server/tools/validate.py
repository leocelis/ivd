# mcp_server/tools/validate.py

"""Tool: ivd_validate — structure validation for IVD artifacts."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from termcolor import colored

from judgment import VALIDATORS as JUDGMENT_VALIDATORS
from mcp_server.tools._paths import IVD_FRAMEWORK_ROOT
from mcp_server.tools.client_enforcement import build_client_enforcement_from_gating
from mcp_server.tools.review_gate import validate_assumption_fields

LOG = "IVD Tools"

# External-oracle gating: executable test reference must look like a pytest node id.
_EXECUTABLE_TEST_RE = re.compile(r"\.py::")

# External-oracle gating: execution_oracle types (ground-truth anchors for execution_derived provenance).
_ALLOWED_ORACLE_TYPES = ("golden_fixture", "property_test", "differential_test")
_ALLOWED_PROPERTY_TESTS = ("round_trip", "invariant", "idempotent")
_REPO_PATH_PREFIXES = ("mcp_server/", "tests/", "judgment/", "examples/")

# Joint satisfaction: joint satisfaction + constraint density.
_JOINT_SATISFACTION_THRESHOLD = 3
_CONSTRAINT_BUDGET = 7


def _test_reference_executable(test: object) -> bool:
    """True when test looks like a pytest path (structure-only — does not run tests)."""
    if not isinstance(test, str):
        return False
    text = test.strip()
    if not text or not _EXECUTABLE_TEST_RE.search(text):
        return False
    # Prose disguised as a test: spaces but no repo path segment.
    if " " in text and "/" not in text and not text.startswith(_REPO_PATH_PREFIXES):
        return False
    return True


def _test_file_part(test: str) -> str:
    return test.split("::", 1)[0].strip()


def _looks_like_repo_test_path(file_part: str) -> bool:
    return "/" in file_part or file_part.startswith(_REPO_PATH_PREFIXES)


def _repo_file_missing(file_part: str, root: Path) -> bool:
    if not _looks_like_repo_test_path(file_part):
        return False
    return not (root / file_part).is_file()


def _constraint_is_unverified(constraint: dict, root: Path) -> bool:
    if "test" not in constraint:
        return True
    test = constraint.get("test")
    if not _test_reference_executable(test):
        return True
    return _repo_file_missing(_test_file_part(test), root)


_TERMINATION_LEVELS = ("workflow", "system")
_STOP_FIELDS = ("stop_when", "escalate_when")


def _missing_termination_contract(artifact: dict) -> bool:
    """True when a workflow/system intent declares no bounded-iteration contract.

    Structure-only: checks that `evaluation.cycle` carries `max_iterations` plus at
    least one stop/escalate condition. Task- and module-level intents are exempt —
    they describe a single unit of work, not an execution loop.
    """
    scope = artifact.get("scope")
    if not isinstance(scope, dict) or scope.get("level") not in _TERMINATION_LEVELS:
        return False

    evaluation = artifact.get("evaluation")
    if not isinstance(evaluation, dict):
        return True
    cycle = evaluation.get("cycle")
    if not isinstance(cycle, dict):
        return True

    has_bound = cycle.get("max_iterations") is not None
    has_stop = any(cycle.get(f) for f in _STOP_FIELDS)
    return not (has_bound and has_stop)


def _validate_execution_oracle(
    cname: str,
    oracle: object,
    root: Path,
    warnings: list,
) -> None:
    if not isinstance(oracle, dict):
        warnings.append(
            f"Constraint '{cname}' execution_oracle must be a mapping "
            "(golden_fixture | property_test | differential_test)"
        )
        return

    otype = oracle.get("type")
    if otype not in _ALLOWED_ORACLE_TYPES:
        warnings.append(
            f"Constraint '{cname}' execution_oracle.type '{otype}' unrecognized — "
            f"use one of {', '.join(_ALLOWED_ORACLE_TYPES)}"
        )
        return

    if otype == "golden_fixture":
        for field in ("path", "expected"):
            if field not in oracle:
                warnings.append(
                    f"Constraint '{cname}' execution_oracle (golden_fixture) missing '{field}'"
                )
        for field in ("path", "expected"):
            val = oracle.get(field)
            if isinstance(val, str) and _looks_like_repo_test_path(val):
                if not (root / val).is_file():
                    warnings.append(
                        f"Constraint '{cname}' execution_oracle.{field} not found on disk: {val}"
                    )
    elif otype == "property_test":
        prop = oracle.get("property")
        if prop not in _ALLOWED_PROPERTY_TESTS:
            warnings.append(
                f"Constraint '{cname}' execution_oracle.property '{prop}' unrecognized — "
                f"use one of {', '.join(_ALLOWED_PROPERTY_TESTS)}"
            )
    elif otype == "differential_test":
        if not oracle.get("reference") and not oracle.get("path"):
            warnings.append(
                f"Constraint '{cname}' execution_oracle (differential_test) needs "
                "'reference' or 'path'"
            )
        ref = oracle.get("reference") or oracle.get("path")
        if isinstance(ref, str) and _looks_like_repo_test_path(ref):
            if not (root / ref).is_file():
                warnings.append(
                    f"Constraint '{cname}' execution_oracle reference not found on disk: {ref}"
                )


def _extract_joint_satisfaction_test(cs: dict) -> Optional[str]:
    """Return joint test path from constraint_satisfiability (alias: joint_test)."""
    for key in ("joint_satisfaction_test", "joint_test"):
        val = cs.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _evaluate_joint_satisfaction_gating(
    constraint_count: int,
    artifact: dict,
    root: Path,
) -> Optional[Dict]:
    """Joint satisfaction gating report for 3+ constraints. Report-only — never affects valid."""
    if constraint_count < _JOINT_SATISFACTION_THRESHOLD:
        return None

    base = {
        "constraint_count": constraint_count,
        "budget": _CONSTRAINT_BUDGET,
        "required_report_fields": ["each_constraint_pass", "joint_satisfaction_pass"],
    }
    cs = artifact.get("constraint_satisfiability")

    if not isinstance(cs, dict):
        return {
            **base,
            "status": "MISSING_SATISFIABILITY_BLOCK",
            "joint_satisfaction_test": None,
            "note": (
                "3+ constraints require a constraint_satisfiability block with "
                "joint_satisfaction_test — a single pytest path asserting ALL constraints "
                "hold on the SAME output. Individual-pass does not imply joint-pass."
            ),
        }

    joint_test = _extract_joint_satisfaction_test(cs)
    if not joint_test:
        return {
            **base,
            "status": "MISSING_JOINT_TEST",
            "joint_satisfaction_test": None,
            "note": (
                "constraint_satisfiability exists but joint_satisfaction_test is missing. "
                "Add one executable pytest path that asserts ALL constraints on the SAME output. "
                "Do not report joint_satisfaction_pass until that test passes."
            ),
        }

    if not _test_reference_executable(joint_test) or _repo_file_missing(
        _test_file_part(joint_test), root
    ):
        return {
            **base,
            "status": "JOINT_TEST_UNVERIFIED",
            "joint_satisfaction_test": joint_test,
            "note": (
                "joint_satisfaction_test is missing, prose-only, or its repo file was not found. "
                "Fix the path before reporting joint_satisfaction_pass."
            ),
        }

    if constraint_count > _CONSTRAINT_BUDGET:
        return {
            **base,
            "status": "CONSTRAINT_BUDGET_EXCEEDED",
            "joint_satisfaction_test": joint_test,
            "note": (
                f"Intent has {constraint_count} constraints (budget {_CONSTRAINT_BUDGET}). "
                "Split into sub-module intents rather than packing more constraints into one "
                "artifact. Joint test is declared; still run it for joint_satisfaction_pass."
            ),
        }

    return None


def _evaluate_conflict_prone_gating(
    needing_execution_derived: List[str],
    missing_anchor: List[str],
) -> Optional[Dict]:
    """Conflict-prone gating for manual conflict_prone constraints. Report-only."""
    if not needing_execution_derived and not missing_anchor:
        return None

    gating: Dict = {
        "required_report_fields": ["anti_pattern_in_implementation_prompt"],
    }
    if needing_execution_derived:
        gating["constraints_needing_execution_derived"] = needing_execution_derived
    if missing_anchor:
        gating["constraints_missing_anchor"] = missing_anchor

    if needing_execution_derived and missing_anchor:
        gating["status"] = "MIXED"
        gating["note"] = (
            "conflict_prone constraints need execution_derived provenance with an "
            "execution_oracle AND an anti_pattern anchor injected into the implementation "
            "prompt. Context alone may lose to the model's prior."
        )
    elif needing_execution_derived:
        gating["status"] = "NEEDS_EXECUTION_DERIVED"
        gating["note"] = (
            "conflict_prone constraints require test_provenance: execution_derived and an "
            "execution_oracle block — unusual rules cannot rely on human_authored, ai_generated, "
            "or undeclared provenance."
        )
    else:
        gating["status"] = "MISSING_ANCHOR"
        gating["note"] = (
            "conflict_prone constraints require an executable test and an anti_pattern field "
            "naming the common pattern and why this system requires NOT-it."
        )
    return gating


def _build_verification_gating(
    needs_external_oracle: list,
    constraints_unverified: list,
    joint_satisfaction: Optional[Dict] = None,
    conflict_prone: Optional[Dict] = None,
) -> Optional[Dict]:
    if (
        not needs_external_oracle
        and not constraints_unverified
        and not joint_satisfaction
        and not conflict_prone
    ):
        return None

    gating: dict = {}
    if needs_external_oracle:
        gating["constraints_needing_external_oracle"] = needs_external_oracle
    if constraints_unverified:
        gating["constraints_unverified"] = constraints_unverified

    if needs_external_oracle or constraints_unverified:
        if needs_external_oracle and constraints_unverified:
            gating["status"] = "MIXED"
            gating["note"] = (
                "Some constraints need an external oracle (AI-only test evidence); others are "
                "UNVERIFIED (missing or non-executable test). Do not report PASS on either until "
                "cleared. The code-under-test must never be its own oracle."
            )
        elif needs_external_oracle:
            gating["status"] = "NEEDS_EXTERNAL_ORACLE"
            gating["note"] = (
                "These constraints declare an AI-generated test as their only evidence. "
                "An AI-authored test is low-trust (it tends to confirm the code/intent rather "
                "than catch it). Do not report PASS until a human-authored assertion or an "
                "execution-derived oracle clears them. The code-under-test must never be its own oracle."
            )
        else:
            gating["status"] = "UNVERIFIED"
            gating["note"] = (
                "These constraints have no executable test reference (missing test, prose-only test, "
                "or repo test file not found). Do not report PASS until an executable test with "
                "appropriate provenance clears them."
            )

    if joint_satisfaction:
        gating["joint_satisfaction"] = joint_satisfaction

    if conflict_prone:
        gating["conflict_prone"] = conflict_prone

    return gating

# IVD v3.0: Judgment phase artifact types (opt-in via `.judgment/`)
JUDGMENT_ARTIFACT_TYPES = ("baseline", "ledger_entry", "comparison_pair", "pattern")


def validate_artifact_tool(
    artifact_yaml: str,
    artifact_type: str = "intent",
    project_root: Optional[str] = None,
) -> str:
    """Validate an IVD artifact (structure and required section checks).

    Supported artifact_type values:
      - intent | recipe | workflow                   (core IVD)
      - baseline | ledger_entry | comparison_pair | pattern  (Judgment phase, v3.0)

    When ``project_root`` is set, constraint test paths and execution_oracle
    fixtures resolve against that repo root instead of the IVD framework tree.
    """
    print(colored(f"[{LOG}] ivd_validate: type={artifact_type}", "cyan"))

    try:
        artifact = yaml.safe_load(artifact_yaml)
    except yaml.YAMLError as e:
        return json.dumps({
            "valid": False,
            "errors": [f"YAML parse error: {e}"],
            "warnings": [],
            "suggestions": ["Check YAML syntax — proper indentation, colons, quotes"],
        }, indent=2)

    if artifact is None:
        return json.dumps({
            "valid": False,
            "errors": ["Empty artifact — YAML parsed to nothing"],
            "warnings": [],
            "suggestions": ["Provide a valid YAML artifact with at least an 'intent' section"],
            "artifact_type": artifact_type,
            "validation_level": "structure_only",
            "note": "Validates structure and required sections. Semantic principle alignment is not checked.",
        }, indent=2)

    errors = []
    warnings = []
    suggestions = []
    # External-oracle gating: constraints whose only verification evidence
    # is an AI-authored test cannot clear on their own — reported, never PASS.
    needs_external_oracle = []
    # External-oracle gating: missing / non-executable / absent test file → UNVERIFIED.
    constraints_unverified = []
    constraint_count = 0
    conflict_prone_needing_execution_derived: List[str] = []
    conflict_prone_missing_anchor: List[str] = []
    if project_root:
        framework_root = Path(project_root).expanduser().resolve()
        if not framework_root.is_dir():
            warnings.append(
                f"project_root is not a directory: {framework_root} — "
                "falling back to IVD framework root for test-path checks"
            )
            framework_root = IVD_FRAMEWORK_ROOT
    else:
        framework_root = IVD_FRAMEWORK_ROOT

    # Allowed test provenance tiers (signal hierarchy: ground-truth > proxy > self).
    ALLOWED_PROVENANCE = ("human_authored", "execution_derived", "ai_generated")

    required_keys = {
        "intent": {
            "top_level": ["intent", "constraints", "rationale", "alternatives", "risks", "implementation", "verification"],
            "intent_fields": ["summary", "goal", "success_metric"],
        },
        "recipe": {
            # Recipes have one required top-level key: `recipe:`.
            # description/pattern/use_cases/example are nested inside it, not siblings.
            "top_level": ["recipe"],
            "recipe_fields": ["name", "version", "description"],
        },
        "workflow": {
            "top_level": ["workflow", "description", "steps", "dependencies", "error_handling"],
        },
    }

    # ------------------------------------------------------------------
    # Judgment phase artifact types (IVD v3.0)
    # ------------------------------------------------------------------
    if artifact_type in JUDGMENT_ARTIFACT_TYPES:
        validator = JUDGMENT_VALIDATORS[artifact_type]
        j_errors, j_warnings = validator(artifact)
        errors.extend(j_errors)
        warnings.extend(j_warnings)
        if errors:
            suggestions.append(
                "See `ivd/judgment_layer.md` and `ivd/templates/`-judgment templates "
                "for the canonical schema."
            )
        if not errors and not warnings:
            suggestions.append(
                "Judgment artifact structure looks good — opt-in is per project via "
                "the `.judgment/` folder."
            )
        valid = len(errors) == 0
        result = {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "artifact_type": artifact_type,
            "validation_level": "judgment_structure",
            "note": (
                "Judgment-phase validator (IVD v3.0). Validates structure and required "
                "fields per judgment_layer.md. Activation gate (`.judgment/`) is enforced "
                "at tool-call time, not at validation time."
            ),
        }
        status = "passed" if valid else "failed"
        color = "green" if valid else "red"
        print(colored(
            f"[{LOG}] Validation {status} ({len(errors)} errors, {len(warnings)} warnings)",
            color,
        ))
        return json.dumps(result, indent=2)

    if artifact_type in required_keys:
        reqs = required_keys[artifact_type]
        missing = [k for k in reqs["top_level"] if k not in artifact]
        if missing:
            errors.extend([f"Missing required top-level key: '{k}'" for k in missing])

        if artifact_type == "recipe" and "recipe" in artifact:
            recipe_section = artifact["recipe"]
            if isinstance(recipe_section, dict):
                missing_fields = [f for f in reqs.get("recipe_fields", []) if f not in recipe_section]
                if missing_fields:
                    warnings.extend([f"recipe section missing field: '{f}'" for f in missing_fields])

        if artifact_type == "intent" and "intent" in artifact:
            intent_section = artifact["intent"]
            if isinstance(intent_section, dict):
                missing_fields = [f for f in reqs.get("intent_fields", []) if f not in intent_section]
                if missing_fields:
                    warnings.extend([f"Intent section missing field: '{f}'" for f in missing_fields])

        if artifact_type == "intent" and "constraints" in artifact:
            constraints = artifact["constraints"]
            if isinstance(constraints, list):
                constraint_count = len(constraints)
                missing_test_count = 0
                provenance_absent_count = 0
                assumption_absent_count = 0
                for i, c in enumerate(constraints):
                    if not isinstance(c, dict):
                        continue
                    cname = c.get("name", f"#{i+1}")
                    if _constraint_is_unverified(c, framework_root):
                        constraints_unverified.append(cname)

                    if "test" not in c:
                        missing_test_count += 1
                        warnings.append(f"Constraint #{i+1} missing 'test' field — the Post-Implementation Verification Protocol cannot verify this constraint (Principle 2 + Principle 4)")
                    elif not _test_reference_executable(c.get("test")):
                        warnings.append(
                            f"Constraint '{cname}' test is not an executable pytest reference "
                            "(expected path/to/test.py::test_name) — treat as UNVERIFIED"
                        )
                    elif _repo_file_missing(_test_file_part(c["test"]), framework_root):
                        warnings.append(
                            f"Constraint '{cname}' test file not found on disk: "
                            f"{_test_file_part(c['test'])}"
                        )

                    # External-oracle gating: test provenance gating (external ground-truth signal).
                    prov = c.get("test_provenance")
                    if prov is None:
                        if "test" in c:
                            provenance_absent_count += 1
                    elif prov not in ALLOWED_PROVENANCE:
                        warnings.append(
                            f"Constraint '{cname}' has unrecognized test_provenance '{prov}' — "
                            f"use one of {', '.join(ALLOWED_PROVENANCE)} (external-oracle gating)"
                        )
                    elif prov == "ai_generated":
                        # An AI-authored test alone is low-trust: it confirms the
                        # code/intent rather than catches it (circularity of error).
                        needs_external_oracle.append(cname)
                    elif prov == "execution_derived" and "execution_oracle" not in c:
                        warnings.append(
                            f"Constraint '{cname}' declares test_provenance execution_derived but "
                            "has no execution_oracle block — add golden_fixture, property_test, or "
                            "differential_test so the oracle is structurally anchored"
                        )

                    if "execution_oracle" in c:
                        _validate_execution_oracle(cname, c["execution_oracle"], framework_root, warnings)

                    # Conflict-prone: conflict_prone constraints (idiosyncratic rules the
                    # model's prior may ignore) need an executable test AND an
                    # anti-pattern anchor. Manual flag — no auto-detection.
                    if c.get("conflict_prone") is True:
                        anchor_missing = False
                        if "test" not in c:
                            anchor_missing = True
                            warnings.append(
                                f"Constraint '{cname}' is conflict_prone but has no 'test' — "
                                "conflict-prone constraints require an executable test"
                            )
                        if not c.get("anti_pattern"):
                            anchor_missing = True
                            warnings.append(
                                f"Constraint '{cname}' is conflict_prone but has no 'anti_pattern' anchor — "
                                "name the common pattern and why this system requires NOT-it"
                            )
                        if anchor_missing:
                            conflict_prone_missing_anchor.append(cname)

                        prov = c.get("test_provenance")
                        needs_execution_derived = (
                            prov != "execution_derived"
                            or (prov == "execution_derived" and "execution_oracle" not in c)
                        )
                        if needs_execution_derived:
                            conflict_prone_needing_execution_derived.append(cname)
                            if prov is None:
                                warnings.append(
                                    f"Constraint '{cname}' is conflict_prone but has no test_provenance — "
                                    "declare execution_derived with execution_oracle"
                                )
                            elif prov != "execution_derived":
                                warnings.append(
                                    f"Constraint '{cname}' is conflict_prone but test_provenance is "
                                    f"'{prov}' — conflict-prone constraints require execution_derived "
                                    "with execution_oracle"
                                )

                    assumption_absent_count = validate_assumption_fields(
                        cname, c, warnings, assumption_absent_count
                    )

                if missing_test_count > 0:
                    warnings.append(f"{missing_test_count}/{len(constraints)} constraints lack test fields — AI agents cannot execute the verification protocol without them. See recipes/agent-rules-ivd.yaml")

                # External-oracle gating: nudge declaring provenance so the gate can apply.
                if provenance_absent_count > 0:
                    suggestions.append(
                        f"{provenance_absent_count}/{len(constraints)} constraints declare a test but no "
                        "'test_provenance' (human_authored | execution_derived | ai_generated). Declare it so "
                        "ivd_validate can gate AI-only evidence. The code-under-test must never be its own oracle."
                    )

                if assumption_absent_count > 0:
                    suggestions.append(
                        f"{assumption_absent_count}/{len(constraints)} constraints have no 'assumption_status' "
                        "(KNOWN | ASSUMED | GUESSED). Declare during Rule 4 stress test so ivd_review_intent "
                        "can rank review risk."
                    )

                # Joint satisfaction: joint constraint satisfaction — individual-pass != joint-pass.
                # 3+ constraints without a satisfiability block is the density-abandonment risk.
                if constraint_count >= _JOINT_SATISFACTION_THRESHOLD and "constraint_satisfiability" not in artifact:
                    warnings.append(
                        "3+ constraints but no 'constraint_satisfiability' block — add one (conflicts_checked, "
                        "known_tensions, simultaneous_satisfaction, joint_satisfaction_test) that asserts ALL "
                        "constraints hold on the SAME output. Individual-pass does not imply joint-pass (UltraBench 2025)."
                    )

                if constraint_count > _CONSTRAINT_BUDGET:
                    warnings.append(
                        f"{constraint_count} constraints exceeds budget {_CONSTRAINT_BUDGET} — split into "
                        "sub-module intents rather than packing more constraints into one artifact."
                    )

                # Termination expectation: workflow- and system-level intents describe
                # multi-step or autonomous execution, where "no stopping condition" is a
                # real failure mode (unbounded iteration / unaware of termination).
                # Warning only — never an error, so legacy intents keep validating.
                if _missing_termination_contract(artifact):
                    warnings.append(
                        "workflow/system-level intent has no 'evaluation.cycle' termination contract "
                        "(max_iterations + a stop condition). Unbounded iteration and unclear "
                        "completion are among the largest multi-agent failure modes — declare "
                        "max_iterations, stop_when, and escalate_when."
                    )

        # Joint satisfaction: when a constraint_satisfiability block exists, check joint satisfaction fields.
        if artifact_type == "intent" and "constraint_satisfiability" in artifact:
            cs = artifact["constraint_satisfiability"]
            if isinstance(cs, dict):
                for field in ("conflicts_checked", "simultaneous_satisfaction"):
                    if field not in cs:
                        warnings.append(f"constraint_satisfiability missing '{field}'")
                if constraint_count >= _JOINT_SATISFACTION_THRESHOLD:
                    joint_test = _extract_joint_satisfaction_test(cs)
                    if not joint_test:
                        warnings.append(
                            "constraint_satisfiability missing 'joint_satisfaction_test' — add an executable "
                            "pytest path asserting ALL constraints on the SAME output."
                        )
                    elif not _test_reference_executable(joint_test):
                        warnings.append(
                            f"joint_satisfaction_test '{joint_test}' is not an executable pytest path."
                        )
                    elif _repo_file_missing(_test_file_part(joint_test), framework_root):
                        warnings.append(
                            f"joint_satisfaction_test file not found on disk: "
                            f"{_test_file_part(joint_test)}."
                        )

        # Validate interface section (optional — for agents, MCP servers, APIs, CLIs, services)
        if artifact_type == "intent" and "interface" in artifact:
            iface = artifact["interface"]
            if isinstance(iface, dict):
                if "type" not in iface:
                    warnings.append("interface section missing 'type' field (mcp | agent | api | cli | service)")
                if "tools" not in iface:
                    warnings.append("interface section missing 'tools' list")
                elif isinstance(iface["tools"], list):
                    for i, tool in enumerate(iface["tools"]):
                        if not isinstance(tool, dict):
                            warnings.append(f"interface.tools[{i}] is not a dict")
                            continue
                        tool_name = tool.get("name", f"#{i+1}")
                        for req_field in ["name", "description", "returns", "test"]:
                            if req_field not in tool:
                                warnings.append(f"interface.tools '{tool_name}' missing '{req_field}' (Principle 2)")
                        if "parameters" in tool and isinstance(tool["parameters"], list):
                            for j, param in enumerate(tool["parameters"]):
                                if isinstance(param, dict):
                                    for pf in ["name", "type", "required", "description"]:
                                        if pf not in param:
                                            warnings.append(f"interface.tools '{tool_name}' param #{j+1} missing '{pf}'")
                # Validate interface.routing sub-field (optional — agents consumed by a coordinator)
                if "routing" in iface:
                    routing = iface["routing"]
                    if isinstance(routing, dict):
                        if "description" not in routing or not routing.get("description"):
                            warnings.append("interface.routing missing or empty 'description' (what the coordinator tells the LLM about this agent)")
                        if "consumed_by" not in routing or not routing.get("consumed_by"):
                            warnings.append("interface.routing missing 'consumed_by' (path to coordinator that consumes this agent)")
                        if "keywords" in routing and not isinstance(routing["keywords"], list):
                            warnings.append("interface.routing.keywords should be a list of routing trigger words")

        # Validate roles section (optional — for agents with context-dependent behavior)
        if artifact_type == "intent" and "roles" in artifact:
            roles = artifact["roles"]
            if isinstance(roles, dict):
                if "default" not in roles:
                    warnings.append("roles section missing 'default' field (which role the agent starts in)")
                if "switching" not in roles:
                    warnings.append("roles section missing 'switching' field (how the agent transitions between roles)")
                elif isinstance(roles.get("switching"), dict):
                    if "mechanism" not in roles["switching"]:
                        warnings.append("roles.switching missing 'mechanism' (user_directed | context_inferred | explicit_command)")
                if "definitions" not in roles:
                    warnings.append("roles section missing 'definitions' list")
                elif isinstance(roles["definitions"], list):
                    for i, role in enumerate(roles["definitions"]):
                        if not isinstance(role, dict):
                            warnings.append(f"roles.definitions[{i}] is not a dict")
                            continue
                        role_name = role.get("name", f"#{i+1}")
                        for req_field in ["name", "description", "when", "constraints", "verification"]:
                            if req_field not in role:
                                warnings.append(f"roles.definitions '{role_name}' missing '{req_field}' (Principle 2)")

        # Validate authorship section (optional — for autonomous intent creation)
        if artifact_type == "intent" and "authorship" in artifact:
            auth = artifact["authorship"]
            if isinstance(auth, dict):
                if "origin" not in auth:
                    warnings.append("authorship section missing 'origin' field (human_directed | ai_proposed | ai_autonomous)")
                elif auth["origin"] not in ("human_directed", "ai_proposed", "ai_autonomous"):
                    warnings.append(f"authorship.origin '{auth['origin']}' not recognized — use human_directed | ai_proposed | ai_autonomous")
                if "human_oversight" not in auth:
                    warnings.append("authorship section missing 'human_oversight' field (review_required | audit_trail | escalation_only)")
                if "ai_authority" not in auth:
                    warnings.append("authorship section missing 'ai_authority' (what AI can create/modify)")
                elif isinstance(auth.get("ai_authority"), dict):
                    ai_auth = auth["ai_authority"]
                    for af in ["can_create", "can_modify", "requires_approval"]:
                        if af not in ai_auth:
                            warnings.append(f"authorship.ai_authority missing '{af}' (Principle 2)")
                if "escalation" not in auth:
                    warnings.append("authorship section missing 'escalation' (when AI must stop and ask human)")

        # Validate evaluation section (optional — continuous improvement loop)
        if artifact_type == "intent" and "evaluation" in artifact:
            evl = artifact["evaluation"]
            if isinstance(evl, dict):
                if "criteria" not in evl:
                    warnings.append("evaluation section missing 'criteria' list (what quality metrics to measure)")
                elif isinstance(evl["criteria"], list):
                    for i, crit in enumerate(evl["criteria"]):
                        if isinstance(crit, dict):
                            crit_name = crit.get("metric", f"#{i+1}")
                            for cf in ["metric", "target", "source"]:
                                if cf not in crit:
                                    warnings.append(f"evaluation.criteria '{crit_name}' missing '{cf}' (Principle 2)")
                if "adjustment" not in evl:
                    warnings.append("evaluation section missing 'adjustment' (who can improve and what's protected)")
                elif isinstance(evl.get("adjustment"), dict):
                    adj = evl["adjustment"]
                    for af in ["authority", "scope", "protected"]:
                        if af not in adj:
                            warnings.append(f"evaluation.adjustment missing '{af}'")
                if "cycle" not in evl:
                    warnings.append("evaluation section missing 'cycle' (trigger, max_iterations, stop/escalate conditions)")
                elif isinstance(evl.get("cycle"), dict):
                    cyc = evl["cycle"]
                    for cf in ["trigger", "max_iterations", "stop_when", "escalate_when"]:
                        if cf not in cyc:
                            warnings.append(f"evaluation.cycle missing '{cf}'")

    else:
        warnings.append(f"Unknown artifact_type '{artifact_type}' — validation limited")

    if errors:
        suggestions.append("Add all required sections to make artifact IVD-compliant")
    if warnings:
        suggestions.append("Review IVD principles — all constraints should link to tests")
    if not errors and not warnings:
        suggestions.append("Structure looks good — consider stress-testing intent before implementing (P6 Step 4: edge cases, implementation gaps, implicit assumptions)")

    valid = len(errors) == 0
    result = {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "artifact_type": artifact_type,
        "validation_level": "structure_only",
        "note": "Validates structure and required sections. Semantic principle alignment is not checked.",
    }

    # Verification gating reports: verification gating reports. Structure-only — does NOT affect valid.
    joint_gating = None
    conflict_gating = None
    if artifact_type == "intent":
        joint_gating = _evaluate_joint_satisfaction_gating(
            constraint_count, artifact, framework_root
        )
        conflict_gating = _evaluate_conflict_prone_gating(
            conflict_prone_needing_execution_derived,
            conflict_prone_missing_anchor,
        )
    gating = _build_verification_gating(
        needs_external_oracle,
        constraints_unverified,
        joint_gating,
        conflict_gating,
    )
    if gating:
        result["verification_gating"] = gating
        client_enforcement = build_client_enforcement_from_gating(gating)
        if client_enforcement:
            result["client_enforcement"] = client_enforcement

    status = "passed" if valid else "failed"
    color = "green" if valid else "red"
    print(colored(f"[{LOG}] Validation {status} ({len(errors)} errors, {len(warnings)} warnings)", color))
    return json.dumps(result, indent=2)
