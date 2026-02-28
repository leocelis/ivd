# mcp_server/tools/validate.py

"""Tool: ivd_validate — structure validation for IVD artifacts."""

import json

import yaml
from termcolor import colored

LOG = "IVD Tools"


def validate_artifact_tool(artifact_yaml: str, artifact_type: str = "intent") -> str:
    """Validate an IVD artifact (Phase 1: structure validation)."""
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
            "note": "Schema validation and principle alignment checks coming in Phase 2",
        }, indent=2)

    errors = []
    warnings = []
    suggestions = []

    required_keys = {
        "intent": {
            "top_level": ["intent", "constraints", "rationale", "alternatives", "risks", "implementation", "verification"],
            "intent_fields": ["summary", "goal", "success_metric"],
        },
        "recipe": {
            "top_level": ["recipe", "description", "pattern", "use_cases", "example"],
        },
        "workflow": {
            "top_level": ["workflow", "description", "steps", "dependencies", "error_handling"],
        },
    }

    if artifact_type in required_keys:
        reqs = required_keys[artifact_type]
        missing = [k for k in reqs["top_level"] if k not in artifact]
        if missing:
            errors.extend([f"Missing required top-level key: '{k}'" for k in missing])

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
                for i, c in enumerate(constraints):
                    if isinstance(c, dict) and "test" not in c:
                        missing_test_count += 1
                        warnings.append(f"Constraint #{i+1} missing 'test' field — the Post-Implementation Verification Protocol cannot verify this constraint (Principle 2 + Principle 4)")
                if missing_test_count > 0:
                    warnings.append(f"{missing_test_count}/{len(constraints)} constraints lack test fields — AI agents cannot execute the verification protocol without them. See recipes/agent-rules-ivd.yaml")

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
        suggestions.append("Structure looks good — consider reviewing all 8 principles")

    valid = len(errors) == 0
    result = {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "artifact_type": artifact_type,
        "validation_level": "structure_only",
        "note": "Schema validation and principle alignment checks coming in Phase 2",
    }

    status = "passed" if valid else "failed"
    color = "green" if valid else "red"
    print(colored(f"[{LOG}] Validation {status} ({len(errors)} errors, {len(warnings)} warnings)", color))
    return json.dumps(result, indent=2)
