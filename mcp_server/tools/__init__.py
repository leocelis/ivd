# mcp_server/tools/__init__.py

"""
IVD MCP Tools — 29 executable functions for AI agents.

Split into logical modules for maintainability.
  - 15 core tools (Intent, Implementation, Verification phases)
  - 9  judgment tools (Judgment phase, opt-in via `<project_root>/.judgment/`;
       server-level opt-out: `IVD_JUDGMENT_TOOLS_ENABLED=false`. The 9th tool
       — ``ivd_judgment_check_installed`` — is workspace-level activation
       visibility, mirroring Canon's ``canon_check_rules_installed``.)
  - 4  Canon tools (Human Translation Layer, Phase 0b — hosted inside the IVD
       MCP server; every existing IVD client picks them up on the next IVD
       release with zero `mcpServers` config edit. Opt-out:
       `IVD_CANON_TOOLS_ENABLED=false`.)
"""

from mcp_server.tools.context import get_context_tool
from mcp_server.tools.recipes import load_recipe_tool, list_recipes_tool
from mcp_server.tools.templates import load_template_tool
from mcp_server.tools.validate import validate_artifact_tool
from mcp_server.tools.review_gate import review_intent_tool
from mcp_server.tools.scaffold import scaffold_artifact_tool, init_project_tool
from mcp_server.tools.discover import (
    find_artifacts_tool,
    check_placement_tool,
    list_features_tool,
    assess_coverage_tool,
)
from mcp_server.tools.inversions import propose_inversions_tool
from mcp_server.tools.learning import discover_goal_tool, teach_concept_tool
from mcp_server.tools.search import ivd_search_tool
from mcp_server.tools.judgment import (
    judgment_init_tool,
    judgment_capture_tool,
    judgment_codify_tool,
    judgment_save_codified_tool,
    judgment_pair_tool,
    judgment_detect_patterns_tool,
    judgment_inject_context_tool,
    judgment_propose_recommendation_tool,
    judgment_check_installed_tool,
)
from mcp_server.tools.canon import (
    canon_render_tool,
    canon_check_tool,
    canon_diff_tool,
    canon_check_rules_installed_tool,
)

__all__ = [
    "get_context_tool",
    "load_recipe_tool",
    "list_recipes_tool",
    "load_template_tool",
    "validate_artifact_tool",
    "review_intent_tool",
    "scaffold_artifact_tool",
    "init_project_tool",
    "find_artifacts_tool",
    "check_placement_tool",
    "list_features_tool",
    "assess_coverage_tool",
    "propose_inversions_tool",
    "discover_goal_tool",
    "teach_concept_tool",
    "ivd_search_tool",
    # Judgment phase (v3.0, opt-in; v3.1 added check_installed)
    "judgment_init_tool",
    "judgment_capture_tool",
    "judgment_codify_tool",
    "judgment_save_codified_tool",
    "judgment_pair_tool",
    "judgment_detect_patterns_tool",
    "judgment_inject_context_tool",
    "judgment_propose_recommendation_tool",
    "judgment_check_installed_tool",
    # Canon — Human Translation Layer (Phase 0b, hosted inside the IVD MCP server)
    "canon_render_tool",
    "canon_check_tool",
    "canon_diff_tool",
    "canon_check_rules_installed_tool",
]
