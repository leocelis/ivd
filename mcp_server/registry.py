# mcp_server/registry.py

"""
IVD MCP Tool Registry — registration and dispatch for all 15 tools.
"""

import json
import time
from typing import Any, Callable, Dict, List, Optional

from mcp.types import Tool

from mcp_server.logger import extract_key_id, extract_origin_ip, log_tool_call
from mcp_server.tools import (
    get_context_tool,
    load_recipe_tool,
    list_recipes_tool,
    load_template_tool,
    validate_artifact_tool,
    init_project_tool,
    scaffold_artifact_tool,
    find_artifacts_tool,
    check_placement_tool,
    list_features_tool,
    assess_coverage_tool,
    propose_inversions_tool,
    discover_goal_tool,
    teach_concept_tool,
    ivd_search_tool,
)


# =============================================================================
# Tool Definitions (MCP schema)
# =============================================================================

def get_all_tools() -> List[Tool]:
    """Return all 15 IVD MCP tools."""
    return [
        Tool(
            name="ivd_get_context",
            description="Get complete IVD context for AI agent - principles, when to use, available resources. Reduces token usage vs reading all files.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="ivd_load_recipe",
            description="Load a specific IVD recipe by name (agent-classifier, workflow-orchestration, etc.). Recipes are proven patterns to use as templates.",
            inputSchema={"type": "object", "properties": {
                "recipe_name": {"type": "string", "description": "Recipe name (e.g., 'agent-classifier', 'workflow-orchestration')"},
            }, "required": ["recipe_name"]},
        ),
        Tool(
            name="ivd_load_template",
            description="Load an IVD artifact template (intent, recipe, task, workflow). Use when no recipe matches your need.",
            inputSchema={"type": "object", "properties": {
                "template_type": {"type": "string", "description": "Template type", "enum": ["intent", "recipe", "task", "workflow"]},
            }, "required": ["template_type"]},
        ),
        Tool(
            name="ivd_list_recipes",
            description="List all available IVD recipes with descriptions and use cases. Use this to discover which recipe fits your need.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="ivd_validate",
            description="Validate an IVD artifact before finalizing. Checks structure, required sections, and basic compliance.",
            inputSchema={"type": "object", "properties": {
                "artifact_yaml": {"type": "string", "description": "YAML content of the artifact to validate"},
                "artifact_type": {"type": "string", "description": "Type of artifact", "enum": ["intent", "recipe", "workflow"], "default": "intent"},
            }, "required": ["artifact_yaml"]},
        ),
        Tool(
            name="ivd_init",
            description="Initialize IVD in an existing project (brownfield). Creates system_intent.yaml at project root with project context. Use this FIRST when adopting IVD in a project with existing code/docs.",
            inputSchema={"type": "object", "properties": {
                "project_root": {"type": "string", "description": "Path to repo root (absolute or relative)."},
                "auto_fill": {"type": "boolean", "description": "If true, scan and pre-fill project context", "default": True},
            }, "required": ["project_root"]},
        ),
        Tool(
            name="ivd_scaffold",
            description="Create a new IVD intent artifact in the correct canonical location (co-locate with implementation). Works for code AND non-code artifacts (documentation, research, books). For standalone docs (runbooks, specs, guides), use module_path to set docs/ location. Before scaffolding: use task-level only for critical functions (10-20%). For non-default repos, pass project_root.",
            inputSchema={"type": "object", "properties": {
                "level": {"type": "string", "description": "Intent level", "enum": ["system", "workflow", "module", "task"]},
                "name": {"type": "string", "description": "Name for the artifact (e.g., 'lead_qualifier')"},
                "module_path": {"type": "string", "description": "Required for module/task level (e.g., 'agent/marketing')"},
                "coordinator_path": {"type": "string", "description": "Optional for workflow level; create alongside coordinator instead of workflows/"},
                "project_root": {"type": "string", "description": "Optional path to repo root."},
            }, "required": ["level", "name"]},
        ),
        Tool(
            name="ivd_find_artifacts",
            description="Discover IVD intent artifacts in a repo. scope=workflow searches workflows/ only; workflow intents alongside coordinator are found with scope=all.",
            inputSchema={"type": "object", "properties": {
                "scope": {"type": "string", "description": "Search scope", "enum": ["all", "workflow", "module", "task", "system"], "default": "all"},
                "project_root": {"type": "string", "description": "Optional path to repo root."},
            }, "required": []},
        ),
        Tool(
            name="ivd_check_placement",
            description="Validate that an IVD artifact is in the correct canonical location per framework (co-locate with code).",
            inputSchema={"type": "object", "properties": {
                "artifact_path": {"type": "string", "description": "Path to the artifact (relative to project_root, or absolute)"},
                "project_root": {"type": "string", "description": "Optional path to repo root."},
            }, "required": ["artifact_path"]},
        ),
        Tool(
            name="ivd_list_features",
            description="Derive feature inventory from all IVD intent artifacts. Use before adding a feature to avoid duplication (large projects).",
            inputSchema={"type": "object", "properties": {
                "root_dir": {"type": "string", "description": "Optional subpath to search"},
                "project_root": {"type": "string", "description": "Optional path to repo root."},
                "category": {"type": "string", "description": "Optional filter by metadata.category"},
                "status": {"type": "string", "description": "Optional filter by metadata.status", "enum": ["implemented", "planned", "deprecated"]},
            }, "required": []},
        ),
        Tool(
            name="ivd_propose_inversions",
            description="Scaffold inversion opportunities for a problem (Principle 8: Innovation through Inversion). Use when designing a new feature that has a conventional approach.",
            inputSchema={"type": "object", "properties": {
                "problem_description": {"type": "string", "description": "What problem are we solving?"},
                "domain_context": {"type": "string", "description": "Optional domain (e.g., data_export, auth)"},
            }, "required": ["problem_description"]},
        ),
        Tool(
            name="ivd_discover_goal",
            description="When the user doesn't know what to ask: propose 2-3 candidate goals or patterns. Use before 'describe -> AI writes intent' (Principle 6 discovery extension).",
            inputSchema={"type": "object", "properties": {
                "domain_or_context": {"type": "string", "description": "Optional domain"},
                "user_hint": {"type": "string", "description": "Optional vague hint from user"},
                "project_root": {"type": "string", "description": "Optional path to repo root; if set, includes existing features"},
            }, "required": []},
        ),
        Tool(
            name="ivd_teach_concept",
            description="When the user lacks technical knowledge: create structured educational artifact explaining a concept they need before IVD flow. Returns YAML with verification questions.",
            inputSchema={"type": "object", "properties": {
                "concept": {"type": "string", "description": "Concept to explain (e.g. 'ETL', 'Saga pattern', 'CDC')"},
                "user_context": {"type": "string", "description": "Optional context about user's situation"},
            }, "required": ["concept"]},
        ),
        Tool(
            name="ivd_search",
            description="Semantic search across IVD framework docs. Use when you need specific IVD guidance on a topic without reading all files. Returns relevant chunks with sources.",
            inputSchema={"type": "object", "properties": {
                "query": {"type": "string", "description": "Natural language question about IVD framework"},
                "top_k": {"type": "integer", "description": "Number of results to return (default: 5)", "default": 5},
            }, "required": ["query"]},
        ),
        Tool(
            name="ivd_assess_coverage",
            description="Assess intent coverage across a project. Scans project structure (directories with code) and compares against existing *_intent.yaml artifacts. Returns coverage report with covered/uncovered modules, coverage %, and prioritized suggestions. The AI agent uses this data to recommend where to add intents.",
            inputSchema={"type": "object", "properties": {
                "project_root": {"type": "string", "description": "Path to repo root (absolute or relative)."},
                "depth": {"type": "string", "description": "Scan depth: 'module' (system + modules) or 'full' (also workflows + task-level).", "enum": ["module", "full"], "default": "module"},
                "include_suggestions": {"type": "boolean", "description": "Include prioritized recommendations for uncovered modules.", "default": True},
            }, "required": ["project_root"]},
        ),
    ]


# =============================================================================
# Tool Handlers (name → function mapping)
# =============================================================================

TOOL_HANDLERS: Dict[str, Callable] = {
    "ivd_get_context": lambda **_: get_context_tool(),
    "ivd_load_recipe": lambda recipe_name, **_: load_recipe_tool(recipe_name),
    "ivd_load_template": lambda template_type, **_: load_template_tool(template_type),
    "ivd_list_recipes": lambda **_: list_recipes_tool(),
    "ivd_validate": lambda artifact_yaml, artifact_type="intent", **_: validate_artifact_tool(artifact_yaml, artifact_type),
    "ivd_init": lambda project_root, auto_fill=True, **_: init_project_tool(project_root, auto_fill),
    "ivd_scaffold": lambda level, name, module_path=None, coordinator_path=None, project_root=None, **_: scaffold_artifact_tool(level, name, module_path, coordinator_path, project_root),
    "ivd_find_artifacts": lambda scope="all", project_root=None, **_: find_artifacts_tool(scope, project_root),
    "ivd_check_placement": lambda artifact_path, project_root=None, **_: check_placement_tool(artifact_path, project_root),
    "ivd_list_features": lambda root_dir=None, category=None, status=None, project_root=None, **_: list_features_tool(root_dir, category, status, project_root),
    "ivd_propose_inversions": lambda problem_description, domain_context=None, **_: propose_inversions_tool(problem_description, domain_context),
    "ivd_discover_goal": lambda domain_or_context=None, user_hint=None, project_root=None, **_: discover_goal_tool(domain_or_context, user_hint, project_root),
    "ivd_teach_concept": lambda concept, user_context=None, **_: teach_concept_tool(concept, user_context),
    "ivd_search": lambda query, top_k=5, **_: ivd_search_tool(query, top_k),
    "ivd_assess_coverage": lambda project_root, depth="module", include_suggestions=True, **_: assess_coverage_tool(project_root, depth, include_suggestions),
}


# =============================================================================
# Dispatch
# =============================================================================

def call_tool(
    tool_name: str,
    arguments: dict,
    api_key: Optional[str] = None,
    request: Optional[Any] = None,
) -> str:
    """
    Execute a tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        api_key: API key (optional, for logging)
        request: Request object (optional, for IP extraction)
    
    Returns:
        Tool execution result as string
    """
    start = time.time()

    if tool_name not in TOOL_HANDLERS:
        # Log unknown tool attempt
        log_tool_call(
            tool=tool_name,
            duration_ms=0,
            status="error",
            key_id=extract_key_id(api_key),
            origin_ip=extract_origin_ip(request),
            payload_preview=json.dumps(arguments),
            response_preview="",
            error=f"Unknown tool '{tool_name}'",
        )
        return f"Error: Unknown tool '{tool_name}'"

    try:
        handler = TOOL_HANDLERS[tool_name]
        result = handler(**arguments)

        elapsed_ms = int((time.time() - start) * 1000)
        
        if isinstance(result, (dict, list)):
            result_str = json.dumps(result, indent=2, default=str)
        else:
            result_str = str(result)

        # Log successful tool call
        log_tool_call(
            tool=tool_name,
            duration_ms=elapsed_ms,
            status="ok",
            key_id=extract_key_id(api_key),
            origin_ip=extract_origin_ip(request),
            payload_preview=json.dumps(arguments),
            response_preview=result_str,
        )
        
        return result_str

    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        
        # Log failed tool call
        log_tool_call(
            tool=tool_name,
            duration_ms=elapsed_ms,
            status="error",
            key_id=extract_key_id(api_key),
            origin_ip=extract_origin_ip(request),
            payload_preview=json.dumps(arguments),
            response_preview="",
            error=str(e),
        )
        
        return f"Error executing {tool_name}: {e}"
