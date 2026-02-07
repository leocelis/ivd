# mcp_server/tools/recipes.py

"""Tools: ivd_load_recipe, ivd_list_recipes."""

import json
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


def list_recipes_tool() -> str:
    """List all available IVD recipes with descriptions."""
    print(colored(f"[{LOG}] ivd_list_recipes", "cyan"))

    recipes_dir = get_framework_path() / "recipes"
    actual = [f.stem for f in recipes_dir.glob("*.yaml") if f.stem != "README"]

    recipes_list = []
    for name in actual:
        info = RECIPE_INFO.get(name, {"description": "Recipe available", "use_cases": [], "complexity": "unknown"})
        recipes_list.append({"name": name, **info})

    result = {
        "recipes": recipes_list,
        "count": len(recipes_list),
        "usage": "Use ivd_load_recipe(recipe_name) to load a specific recipe",
    }

    print(colored(f"[{LOG}] Found {len(recipes_list)} recipes", "green"))
    return json.dumps(result, indent=2)
