# mcp_server/tools/validate.py

"""Tool: ivd_validate — structure validation for IVD artifacts."""

import json

import yaml
from termcolor import colored

from judgment import VALIDATORS as JUDGMENT_VALIDATORS

LOG = "IVD Tools"

# IVD v3.0: Judgment phase artifact types (opt-in via `.judgment/`)
JUDGMENT_ARTIFACT_TYPES = ("baseline", "ledger_entry", "comparison_pair", "pattern")


def validate_artifact_tool(artifact_yaml: str, artifact_type: str = "intent") -> str:
    """Validate an IVD artifact (structure and required section checks).

    Supported artifact_type values:
      - intent | recipe | workflow                   (core IVD)
      - baseline | ledger_entry | comparison_pair | pattern  (Judgment phase, v3.0)
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
    # Fix 1 (red-team remediation): constraints whose only verification evidence
    # is an AI-authored test cannot clear on their own — reported, never PASS.
    needs_external_oracle = []

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
                missing_test_count = 0
                provenance_absent_count = 0
                for i, c in enumerate(constraints):
                    if not isinstance(c, dict):
                        continue
                    cname = c.get("name", f"#{i+1}")
                    if "test" not in c:
                        missing_test_count += 1
                        warnings.append(f"Constraint #{i+1} missing 'test' field — the Post-Implementation Verification Protocol cannot verify this constraint (Principle 2 + Principle 4)")

                    # Fix 1: test provenance gating (external ground-truth signal).
                    prov = c.get("test_provenance")
                    if prov is None:
                        if "test" in c:
                            provenance_absent_count += 1
                    elif prov not in ALLOWED_PROVENANCE:
                        warnings.append(
                            f"Constraint '{cname}' has unrecognized test_provenance '{prov}' — "
                            f"use one of {', '.join(ALLOWED_PROVENANCE)} (Fix 1: external-oracle gating)"
                        )
                    elif prov == "ai_generated":
                        # An AI-authored test alone is low-trust: it confirms the
                        # code/intent rather than catches it (circularity of error).
                        needs_external_oracle.append(cname)

                    # Fix 4: conflict_prone constraints (idiosyncratic rules the
                    # model's prior may ignore) need an executable test AND an
                    # anti-pattern anchor. Manual flag — no auto-detection.
                    if c.get("conflict_prone") is True:
                        if "test" not in c:
                            warnings.append(
                                f"Constraint '{cname}' is conflict_prone but has no 'test' — "
                                "conflict-prone constraints require an executable test (Fix 4)"
                            )
                        if not c.get("anti_pattern"):
                            warnings.append(
                                f"Constraint '{cname}' is conflict_prone but has no 'anti_pattern' anchor — "
                                "name the common pattern and why this system requires NOT-it (Fix 4)"
                            )

                if missing_test_count > 0:
                    warnings.append(f"{missing_test_count}/{len(constraints)} constraints lack test fields — AI agents cannot execute the verification protocol without them. See recipes/agent-rules-ivd.yaml")

                # Fix 1: nudge declaring provenance so the gate can apply.
                if provenance_absent_count > 0:
                    suggestions.append(
                        f"{provenance_absent_count}/{len(constraints)} constraints declare a test but no "
                        "'test_provenance' (human_authored | execution_derived | ai_generated). Declare it so "
                        "ivd_validate can gate AI-only evidence (Fix 1). The code-under-test must never be its own oracle."
                    )

                # Fix 3: joint constraint satisfaction — individual-pass != joint-pass.
                # 3+ constraints without a satisfiability block is the density-abandonment risk.
                if len(constraints) >= 3 and "constraint_satisfiability" not in artifact:
                    warnings.append(
                        "3+ constraints but no 'constraint_satisfiability' block — add one (conflicts_checked, "
                        "known_tensions, simultaneous_satisfaction) and a joint-satisfaction test that asserts ALL "
                        "constraints hold on the SAME output. Individual-pass does not imply joint-pass (UltraBench 2025; Fix 3)."
                    )

        # Fix 3: when a constraint_satisfiability block exists, check it carries the
        # fields that make joint satisfaction reviewable (report-only — never an error).
        if artifact_type == "intent" and "constraint_satisfiability" in artifact:
            cs = artifact["constraint_satisfiability"]
            if isinstance(cs, dict):
                for field in ("conflicts_checked", "simultaneous_satisfaction"):
                    if field not in cs:
                        warnings.append(f"constraint_satisfiability missing '{field}' (Fix 3: joint satisfaction)")

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

    # Fix 1: external-oracle gating report. Structure-only validation cannot RUN
    # tests, but it can flag constraints whose only declared evidence is an
    # AI-authored test — those can never be auto-marked PASS by the verification
    # protocol; they need a human-authored assertion or an execution-derived
    # oracle (golden output, property/differential test). Report-only: this does
    # NOT affect `valid` (backward compatibility).
    if needs_external_oracle:
        result["verification_gating"] = {
            "constraints_needing_external_oracle": needs_external_oracle,
            "status": "NEEDS_EXTERNAL_ORACLE",
            "note": (
                "These constraints declare an AI-generated test as their only evidence. "
                "An AI-authored test is low-trust (it tends to confirm the code/intent rather "
                "than catch it). Do not report PASS until a human-authored assertion or an "
                "execution-derived oracle clears them. The code-under-test must never be its own oracle."
            ),
        }

    status = "passed" if valid else "failed"
    color = "green" if valid else "red"
    print(colored(f"[{LOG}] Validation {status} ({len(errors)} errors, {len(warnings)} warnings)", color))
    return json.dumps(result, indent=2)
