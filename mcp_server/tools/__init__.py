# mcp_server/tools/__init__.py

"""
IVD MCP Tools — 14 executable functions for AI agents.

Split into logical modules for maintainability.
"""

from mcp_server.tools.context import get_context_tool
from mcp_server.tools.recipes import load_recipe_tool, list_recipes_tool
from mcp_server.tools.templates import load_template_tool
from mcp_server.tools.validate import validate_artifact_tool
from mcp_server.tools.scaffold import scaffold_artifact_tool, init_project_tool
from mcp_server.tools.discover import (
    find_artifacts_tool,
    check_placement_tool,
    list_features_tool,
)
from mcp_server.tools.inversions import propose_inversions_tool
from mcp_server.tools.learning import discover_goal_tool, teach_concept_tool
from mcp_server.tools.search import ivd_search_tool

__all__ = [
    "get_context_tool",
    "load_recipe_tool",
    "list_recipes_tool",
    "load_template_tool",
    "validate_artifact_tool",
    "scaffold_artifact_tool",
    "init_project_tool",
    "find_artifacts_tool",
    "check_placement_tool",
    "list_features_tool",
    "propose_inversions_tool",
    "discover_goal_tool",
    "teach_concept_tool",
    "ivd_search_tool",
]
