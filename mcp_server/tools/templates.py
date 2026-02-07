# mcp_server/tools/templates.py

"""Tool: ivd_load_template."""

import json
from termcolor import colored
from mcp_server.tools._paths import get_framework_path

LOG = "IVD Tools"

TEMPLATE_MAP = {
    "intent": "intent.yaml",
    "recipe": "recipe.yaml",
    "task": "examples/task-level-intent-example.yaml",
    "workflow": "examples/workflow-lead-qualification-example.yaml",
}


def load_template_tool(template_type: str) -> str:
    """Load an IVD artifact template."""
    print(colored(f"[{LOG}] ivd_load_template: {template_type}", "cyan"))

    if template_type not in TEMPLATE_MAP:
        return json.dumps({
            "error": f"Unknown template type: {template_type}",
            "valid_types": list(TEMPLATE_MAP.keys()),
            "descriptions": {
                "intent": "Full intent artifact (module/system level) ~100 lines",
                "task": "Single-function/simple task ~50 lines",
                "workflow": "Multi-step process ~150 lines",
                "recipe": "Creating a new reusable pattern ~200 lines",
            },
        }, indent=2)

    templates_dir = get_framework_path() / "templates"
    template_file = templates_dir / TEMPLATE_MAP[template_type]

    if not template_file.exists():
        return json.dumps({"error": f"Template file not found: {template_file}"})

    content = template_file.read_text()
    print(colored(f"[{LOG}] Loaded: {template_type} ({len(content)} bytes)", "green"))
    return content
