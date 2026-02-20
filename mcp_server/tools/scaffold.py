# mcp_server/tools/scaffold.py

"""Tools: ivd_scaffold, ivd_init — create intent artifacts and bootstrap projects."""

import json
from pathlib import Path
from typing import Optional

import yaml
from termcolor import colored

from mcp_server.tools._paths import get_framework_path, project_root

LOG = "IVD Tools"


def init_project_tool(project_root_arg: str, auto_fill: bool = True) -> str:
    """Initialize IVD in an existing project (brownfield)."""
    print(colored(f"[{LOG}] ivd_init: {project_root_arg}", "cyan"))

    try:
        root = Path(project_root_arg).resolve()
        root_exists = root.exists()
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

    system_intent_path = root / "system_intent.yaml"

    if root_exists and system_intent_path.exists():
        return json.dumps({
            "error": "system_intent.yaml already exists",
            "path": str(system_intent_path),
            "suggestion": "Use ivd_scaffold for child intents, or manually update system intent",
        }, indent=2)

    if not root_exists:
        auto_fill = False

    project_context = {}
    scan_summary = {}

    if auto_fill:
        print(colored(f"[{LOG}] Scanning project for context...", "cyan"))

        code_rules = []
        for rule_file in [".cursorrules", "pyproject.toml", ".eslintrc.json", ".prettierrc"]:
            if (root / rule_file).exists():
                code_rules.append({"path": rule_file, "description": f"Code rules ({rule_file})"})
        scan_summary["code_rules"] = len(code_rules)

        architecture = []
        if (root / "docs" / "ARCHITECTURE.md").exists():
            architecture.append({"path": "docs/ARCHITECTURE.md", "description": "System architecture"})
        adr_dir = root / "docs" / "architecture"
        if adr_dir.exists():
            adr_count = len(list(adr_dir.glob("*.md")))
            if adr_count > 0:
                architecture.append({"path": "docs/architecture/", "description": f"{adr_count} ADRs"})
        scan_summary["architecture_docs"] = len(architecture)

        key_paths = {"entrypoints": [], "modules": [], "docs": [], "tests": []}
        for entry in ["api/main.py", "app.py", "main.py"]:
            if (root / entry).exists():
                key_paths["entrypoints"].append({"path": entry, "description": "Entrypoint"})
        for mod_dir in ["agent/", "entity/", "services/", "api/"]:
            if (root / mod_dir.rstrip("/")).is_dir():
                key_paths["modules"].append({"path": mod_dir, "description": "Module directory"})
        if (root / "docs").is_dir():
            key_paths["docs"].append({"path": "docs/", "description": "Documentation"})
        if (root / "tests").is_dir():
            key_paths["tests"].append({"path": "tests/", "description": "Test suites"})
        scan_summary["key_paths"] = sum(len(v) for v in key_paths.values())

        existing_docs = []
        for doc in ["README.md", "docs/API.md", "docs/CONTRIBUTING.md"]:
            if (root / doc).exists():
                existing_docs.append({"path": doc, "description": f"Doc: {doc}"})
        scan_summary["existing_docs"] = len(existing_docs)

        project_context = {k: v for k, v in {
            "code_rules": code_rules or None,
            "architecture": architecture or None,
            "key_paths": key_paths if any(key_paths.values()) else None,
            "existing_docs": existing_docs or None,
        }.items() if v}

    # Load template
    template_path = get_framework_path() / "templates" / "intent.yaml"
    if template_path.exists():
        template_content = template_path.read_text()
    else:
        template_content = "# system_intent.yaml\n# TODO: Fill in IVD sections"

    template_content = template_content.replace('level: "module"', 'level: "system"')
    template_content = template_content.replace('type: "feature"', 'type: "product"')

    if auto_fill and project_context:
        yaml_comment = "\n# AUTO-SCANNED PROJECT CONTEXT (review and adjust):\n"
        for key, count in scan_summary.items():
            yaml_comment += f"# Found: {count} {key}\n"
        template_content = yaml_comment + "\n" + template_content

    written_to_disk = False
    try:
        if root_exists:
            system_intent_path.write_text(template_content)
            written_to_disk = True
    except (OSError, PermissionError):
        pass

    next_steps = [
        "Review and enrich system_intent.yaml",
        "Add architecture principles not auto-detected",
        "Create intents for 3-5 critical modules (ivd_scaffold)",
    ]
    if not written_to_disk:
        next_steps.insert(0, "Create system_intent.yaml with the template_content below")

    result = {
        "success": True,
        "path": "system_intent.yaml",
        "project_root": str(root),
        "written_to_disk": written_to_disk,
        "auto_fill": auto_fill,
        "scan_summary": scan_summary if auto_fill else {},
        "template_content": template_content,
        "next_steps": next_steps,
    }

    if not root_exists:
        result["remote_note"] = "Project root not accessible on server. Auto-scan skipped."

    print(colored(f"[{LOG}] Init {'written' if written_to_disk else 'generated'}", "green"))
    return json.dumps(result, indent=2)


def scaffold_artifact_tool(
    level: str,
    name: str,
    module_path: Optional[str] = None,
    coordinator_path: Optional[str] = None,
    project_root_arg: Optional[str] = None,
) -> str:
    """Create a new IVD intent artifact in the correct canonical location."""
    print(colored(f"[{LOG}] ivd_scaffold: level={level}, name={name}", "cyan"))

    root = project_root(project_root_arg, require_exists=False)
    root_exists = root.exists()

    valid_levels = ["system", "workflow", "module", "task"]
    if level not in valid_levels:
        return json.dumps({"error": f"Invalid level '{level}'", "valid_levels": valid_levels}, indent=2)

    if level in ["module", "task"] and not module_path:
        return json.dumps({"error": f"module_path required for {level}-level intents"}, indent=2)

    # Determine canonical location
    if level == "system":
        rel_path = f"{name}_system_intent.yaml"
    elif level == "workflow":
        base = coordinator_path.rstrip("/") if coordinator_path else "workflows"
        rel_path = f"{base}/{name}_intent.yaml"
    elif level == "module":
        rel_path = f"{module_path}/{name}_intent.yaml"
    elif level == "task":
        rel_path = f"{module_path}/intents/{name}_intent.yaml"

    target_path = root / rel_path

    if root_exists and target_path.exists():
        return json.dumps({"error": "Intent artifact already exists", "path": rel_path}, indent=2)

    # Load template
    templates_dir = get_framework_path() / "templates"
    if level == "workflow":
        tf = templates_dir / "examples" / "workflow-lead-qualification-example.yaml"
    elif level == "task":
        tf = templates_dir / "examples" / "task-level-intent-example.yaml"
    else:
        tf = templates_dir / "intent.yaml"

    template_content = tf.read_text() if tf.exists() else f"# {name}_intent.yaml\n# Level: {level}\n# TODO: Fill in"

    # Auto-inject interface scaffold for agent/service/api module types
    if level == "module" and "interface:" not in template_content:
        interface_scaffold = (
            "\n# ----------------------------------------------------------------------------\n"
            "# INTERFACE (this module exposes callable tools — fill in your tool surface)\n"
            "# ----------------------------------------------------------------------------\n"
            "# interface:\n"
            '#   type: "mcp"   # "mcp" | "agent" | "api" | "cli" | "service"\n'
            "#\n"
            "#   tools:\n"
            '#     - name: "tool_name"\n'
            '#       description: "One-line: what this tool does"\n'
            "#       parameters:\n"
            '#         - name: "param_name"\n'
            '#           type: "string"    # string | number | boolean | object | array\n'
            "#           required: true\n"
            '#           description: "What this parameter is for"\n'
            '#       returns: "What the tool returns"\n'
            '#       test: "tests/test_tool.py::test_tool_name"\n'
        )
        if "intent:" in template_content:
            template_content = template_content.replace(
                "intent:", interface_scaffold + "\nintent:", 1
            )

    # Auto-inject roles scaffold for agent-type modules
    if level == "module" and "roles:" not in template_content:
        roles_scaffold = (
            "\n# ----------------------------------------------------------------------------\n"
            "# ROLES (Experimental — agents with context-dependent behavior)\n"
            "# ----------------------------------------------------------------------------\n"
            "# Uncomment if this agent has 2+ distinct behavioral modes.\n"
            "# Complements interface: interface = WHAT; roles = HOW in each context.\n"
            "# roles:\n"
            '#   default: "implementer"\n'
            "#\n"
            "#   switching:\n"
            '#     mechanism: "user_directed"  # user_directed | context_inferred | explicit_command\n'
            '#     description: "How the agent transitions between roles"\n'
            "#\n"
            "#   definitions:\n"
            '#     - name: "role_name"\n'
            '#       description: "One-line: what this role does"\n'
            '#       when: "Context or trigger that activates this role"\n'
            "#       constraints:\n"
            '#         - "Behavioral guardrail specific to this role"\n'
            '#       tools: ["all"]           # subset of interface.tools, or "all"\n'
            '#       verification: "tests/test_role_name.py"\n'
        )
        if "intent:" in template_content:
            template_content = template_content.replace(
                "intent:", roles_scaffold + "\nintent:", 1
            )

    # Auto-inject authorship scaffold for module/workflow intents (not task/system)
    if level in ("module", "workflow") and "authorship:" not in template_content:
        authorship_scaffold = (
            "\n# ----------------------------------------------------------------------------\n"
            "# AUTHORSHIP (Experimental — who originates and controls this intent)\n"
            "# ----------------------------------------------------------------------------\n"
            "# Uncomment if AI may originate, modify, or extend this intent.\n"
            "# authorship:\n"
            '#   origin: "human_directed"       # human_directed | ai_proposed | ai_autonomous\n'
            '#   human_oversight: "review_required"  # review_required | audit_trail | escalation_only\n'
            "#   ai_authority:\n"
            "#     can_create: false\n"
            '#     can_modify: ["implementation", "verification"]\n'
            '#     requires_approval: ["intent.goal", "constraints"]\n'
            '#   escalation: "When AI confidence < threshold or change impacts other intents"\n'
        )
        if "intent:" in template_content:
            template_content = template_content.replace(
                "intent:", authorship_scaffold + "\nintent:", 1
            )

    # Auto-inject evaluation scaffold for workflow-level intents
    if level == "workflow" and "evaluation:" not in template_content:
        evaluation_scaffold = (
            "\n# ----------------------------------------------------------------------------\n"
            "# EVALUATION (Experimental — continuous improvement loop)\n"
            "# ----------------------------------------------------------------------------\n"
            "# Uncomment if this workflow should improve over iterations.\n"
            "# evaluation:\n"
            "#   criteria:\n"
            '#     - metric: "output_quality_score"\n'
            '#       target: ">= 0.85"\n'
            '#       source: "automated"\n'
            "#   adjustment:\n"
            '#     authority: "ai_proposed"      # human_only | ai_proposed | ai_autonomous\n'
            '#     scope: ["implementation", "workflow_steps"]\n'
            '#     protected: ["intent.goal", "constraints"]\n'
            "#   cycle:\n"
            '#     trigger: "on_completion"\n'
            "#     max_iterations: 3\n"
            '#     stop_when: "All criteria met or max_iterations reached"\n'
            '#     escalate_when: "Cannot meet criteria after max_iterations"\n'
        )
        if "intent:" in template_content:
            template_content = template_content.replace(
                "intent:", evaluation_scaffold + "\nintent:", 1
            )

    # Auto-inject parent_intent
    if level != "system" and "parent_intent:" not in template_content:
        if level == "task":
            parent = f"../{module_path.split('/')[-1]}_intent.yaml"
        elif level == "module":
            parent = "../" * len(Path(module_path).parts) + "system_intent.yaml"
        elif level == "workflow":
            if coordinator_path:
                parent = "../" * len(Path(coordinator_path).parts) + "system_intent.yaml"
            else:
                parent = "../system_intent.yaml"

        lines = template_content.split("\n")
        new_lines = []
        injected = False
        for line in lines:
            if not injected and line.strip() and not line.strip().startswith("#") and ":" in line:
                new_lines.append(f'parent_intent: "{parent}"')
                new_lines.append("")
                injected = True
            new_lines.append(line)
        template_content = "\n".join(new_lines)

    written_to_disk = False
    try:
        if root_exists:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(template_content)
            written_to_disk = True
    except (OSError, PermissionError):
        pass

    next_steps = ["Edit the file to fill in your specific intent details", "Run ivd_validate to check structure"]
    if not written_to_disk:
        next_steps.insert(0, f"Create the file at {rel_path} with the template_content below")

    result = {
        "success": True,
        "path": rel_path,
        "project_root": str(root),
        "written_to_disk": written_to_disk,
        "level": level,
        "name": name,
        "template_content": template_content,
        "next_steps": next_steps,
    }

    print(colored(f"[{LOG}] Scaffold {'written' if written_to_disk else 'generated'}: {rel_path}", "green"))
    return json.dumps(result, indent=2)
