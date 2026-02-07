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
                for i, c in enumerate(constraints):
                    if isinstance(c, dict) and "test" not in c:
                        warnings.append(f"Constraint #{i+1} missing 'test' field (Principle 2: Understanding Must Be Executable)")
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
