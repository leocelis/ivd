# mcp_server/tools/recipes.py

"""Tools: ivd_load_recipe, ivd_list_recipes."""

import json
import yaml
from termcolor import colored
from mcp_server.tools._paths import get_framework_path

LOG = "IVD Tools"

# Recipe descriptions
RECIPE_INFO = {
    "agent-classifier": {
        "description": "AI agent that classifies/categorizes data",
        "use_cases": ["lead scoring", "content classification", "sentiment analysis"],
        "complexity": "medium",
    },
    "workflow-orchestration": {
        "description": "Multi-step process across files/functions",
        "use_cases": ["ETL pipelines", "approval workflows", "data processing"],
        "complexity": "high",
    },
    "infra-background-job": {
        "description": "Background job with retry and monitoring",
        "use_cases": ["email sending", "report generation", "data sync"],
        "complexity": "medium",
    },
    "doc-meeting-insights": {
        "description": "Document processing and extraction",
        "use_cases": ["meeting notes", "contract analysis", "research summaries"],
        "complexity": "medium",
    },
    "discovery-before-intent": {
        "description": "When user can't describe what they want: propose goals/recipes/options, user picks, then intent flow (Experimental)",
        "use_cases": ["unsure what to build", "new domain", "explore options"],
        "complexity": "low",
    },
    "teaching-before-intent": {
        "description": "When user lacks technical knowledge: AI creates educational artifact, user confirms understanding, then intent flow (Canonical)",
        "use_cases": ["user doesn't know what ETL is", "unfamiliar patterns", "onboarding"],
        "complexity": "low",
    },
    "coordinator-intent-propagation": {
        "description": "Multi-agent coordination: coordinator writes intent for each specialist",
        "use_cases": ["multi-agent systems", "task delegation", "coordinator patterns"],
        "complexity": "high",
    },
    "data-field-mapping": {
        "description": "Field mapping and data sources for integrations and ETL",
        "use_cases": ["API integrations", "data sync", "ETL pipelines"],
        "complexity": "medium",
    },
    "canon-rules": {
        "description": "Canon — Human Translation Layer (Phase 0a Rules). Pasteable agent rules block (R1, R2, R5, R10, R14) for Cursor / Cline / Claude Code / Copilot / Codex / Windsurf. Composes with the Canon MCP tools (canon_render / canon_check / canon_diff) hosted inside this IVD MCP server.",
        "use_cases": ["make any AI agent's replies legible to humans", "calibrate trust on AI output", "enforce verification beats before irreversible actions", "ship Canon's R-invariants with zero install"],
        "complexity": "low",
    },
}


def load_recipe_tool(recipe_name: str) -> str:
    """Load a specific IVD recipe by name."""
    print(colored(f"[{LOG}] ivd_load_recipe: {recipe_name}", "cyan"))

    recipes_dir = get_framework_path() / "recipes"
    recipe_file = recipes_dir / f"{recipe_name}.yaml"

    if not recipe_file.exists():
        available = [f.stem for f in recipes_dir.glob("*.yaml") if f.stem != "README"]
        return json.dumps({
            "error": f"Recipe '{recipe_name}' not found",
            "available_recipes": available,
        }, indent=2)

    content = recipe_file.read_text()
    print(colored(f"[{LOG}] Loaded: {recipe_name} ({len(content)} bytes)", "green"))
    return content


def _read_recipe_metadata(recipe_file) -> dict:
    """Read description/use_cases/complexity from a recipe YAML file.

    Tries the nested `recipe:` block first (canonical format). Falls back
    to the RECIPE_INFO hardcoded table. Returns a dict with those three keys.
    """
    try:
        data = yaml.safe_load(recipe_file.read_text()) or {}
        block = data.get("recipe") or {}
        desc = block.get("description", "").strip()
        use_cases = block.get("use_cases") or []
        complexity = block.get("complexity", "unknown")
        if desc:
            return {"description": desc, "use_cases": use_cases, "complexity": complexity}
    except Exception:
        pass
    return {}


def list_recipes_tool() -> str:
    """List all available IVD recipes with descriptions."""
    print(colored(f"[{LOG}] ivd_list_recipes", "cyan"))

    recipes_dir = get_framework_path() / "recipes"
    recipe_files = {f.stem: f for f in recipes_dir.glob("*.yaml") if f.stem != "README"}

    recipes_list = []
    for name, recipe_file in sorted(recipe_files.items()):
        # Read metadata from the YAML file first; fall back to hardcoded table.
        info = _read_recipe_metadata(recipe_file)
        if not info.get("description"):
            info = RECIPE_INFO.get(name, {"description": "Recipe available", "use_cases": [], "complexity": "unknown"})
        recipes_list.append({"name": name, **info})

    result = {
        "recipes": recipes_list,
        "count": len(recipes_list),
        "usage": "Use ivd_load_recipe(recipe_name) to load a specific recipe",
    }

    print(colored(f"[{LOG}] Found {len(recipes_list)} recipes", "green"))
    return json.dumps(result, indent=2)
