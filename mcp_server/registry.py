# mcp_server/registry.py

"""
IVD MCP Tool Registry — registration and dispatch for all 29 tools.

  - 15 core tools (Intent, Implementation, Verification phases)
  - 9  judgment tools (Judgment phase, opt-in via `<project_root>/.judgment/`;
                       server-level opt-out: `IVD_JUDGMENT_TOOLS_ENABLED=false`.
                       See ivd/judgment_layer.md and ivd/judgment/ engine
                       package. Tool #9 — `ivd_judgment_check_installed` —
                       provides workspace-level activation visibility,
                       borrowed from Canon's `canon_check_rules_installed`
                       pattern.)
  - 4  Canon tools  (Human Translation Layer, Phase 0b — hosted inside this
                     IVD MCP server so every existing IVD client picks them
                     up automatically with zero `mcpServers` config edit.
                     Opt-out: `IVD_CANON_TOOLS_ENABLED=false`. See the
                     Canon PRD §11.0b and the Canon Tech Spec §9B.)
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
    review_intent_tool,
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
    judgment_init_tool,
    judgment_capture_tool,
    judgment_codify_tool,
    judgment_save_codified_tool,
    judgment_pair_tool,
    judgment_detect_patterns_tool,
    judgment_inject_context_tool,
    judgment_propose_recommendation_tool,
    judgment_check_installed_tool,
    canon_render_tool,
    canon_check_tool,
    canon_diff_tool,
    canon_check_rules_installed_tool,
)


# =============================================================================
# Tool Definitions (MCP schema)
# =============================================================================

def get_all_tools() -> List[Tool]:
    """Return all 29 IVD MCP tools (16 core + 9 judgment-phase + 4 Canon-phase, IVD v3.1)."""
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
            description="Validate an IVD artifact before finalizing. Checks structure, required sections, and basic compliance. v3.0 adds Judgment-phase artifact types (baseline, ledger_entry, comparison_pair, pattern).",
            inputSchema={"type": "object", "properties": {
                "artifact_yaml": {"type": "string", "description": "YAML content of the artifact to validate"},
                "artifact_type": {"type": "string", "description": "Type of artifact", "enum": ["intent", "recipe", "workflow", "baseline", "ledger_entry", "comparison_pair", "pattern"], "default": "intent"},
            }, "required": ["artifact_yaml"]},
        ),
        Tool(
            name="ivd_review_intent",
            description="Build a human review gate packet for an intent (Fix 2). Ranks constraints by risk, surfaces verification.test_cases as worked examples, lists GUESSED constraints pending sign-off. Structure-only — does not auto-approve.",
            inputSchema={"type": "object", "properties": {
                "artifact_yaml": {"type": "string", "description": "YAML content of the intent artifact"},
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

        # -------------------------------------------------------------------
        # Judgment Phase (IVD v3.0; refactored v3.1) — opt-in via
        # `<project_root>/.judgment/`. All 9 tools are dormant unless that
        # folder exists. Server-level opt-out: IVD_JUDGMENT_TOOLS_ENABLED=false
        # (mirrors Canon's IVD_CANON_TOOLS_ENABLED knob; tools remain
        # registered when disabled and return an `enabled=false` payload).
        # -------------------------------------------------------------------
        Tool(
            name="ivd_judgment_init",
            description="Bootstrap the IVD Judgment phase for a project. Creates `<project_root>/.judgment/` with subfolders (baselines, ledger/{raw,codified,paired,resolved,archived}, patterns, recommendations) and seeds per-domain baseline.yaml files. After this runs, the other 7 ivd_judgment_* tools become active. (IVD v3.0)",
            inputSchema={"type": "object", "properties": {
                "project_root": {"type": "string", "description": "Path to repo root (absolute or relative)."},
                "domains": {"type": "array", "items": {"type": "string"}, "description": "Optional list of domain ids to seed baselines for (e.g. ['gaming', 'orchestration'])."},
            }, "required": []},
        ),
        Tool(
            name="ivd_judgment_capture",
            description="Capture a raw correction in < 30 seconds. Writes a ledger entry in state=raw under `.judgment/ledger/raw/`. Use this the moment a real-world correction surfaces (your review, audience signal, runtime error, etc.). Follow up with ivd_judgment_codify. Dormant unless `.judgment/` exists. (IVD v3.0)",
            inputSchema={"type": "object", "properties": {
                "raw_correction": {"type": "string", "description": "Raw correction text — what was wrong, paste verbatim."},
                "domain": {"type": "string", "description": "Domain id (must match a baseline if you want depth weighting)."},
                "source": {"type": "string", "description": "leo_intuition | audience | runtime | peer_review | automated_test", "default": "leo_intuition"},
                "correction_type": {"type": "string", "description": "regression | wrong_output | missing_feature | hallucination | other", "default": "regression"},
                "agent": {"type": "string", "description": "Optional agent name (e.g. 'gaming_agent')."},
                "model": {"type": "string", "description": "Optional model identifier (e.g. 'gpt-5-codex')."},
                "scope": {"type": "string", "description": "Optional scope (e.g. 'workflow_x' or system path)."},
                "originated_from_tool": {"type": "string", "description": "Optional: the tool that produced the bad output (for tool-originated failure tracking)."},
                "project_root": {"type": "string", "description": "Optional path to repo root."},
            }, "required": ["raw_correction", "domain"]},
        ),
        Tool(
            name="ivd_judgment_codify",
            description="Returns a structured codify prompt for the agent to fill in, plus the original raw correction. The agent fills the 5 codified fields (expected_result, detected_via, diagnosed_cause, proposed_fix, fix_action_type) and then calls ivd_judgment_save_codified to persist. Dormant unless `.judgment/` exists. (IVD v3.0)",
            inputSchema={"type": "object", "properties": {
                "entry_id": {"type": "string", "description": "Ledger entry id returned by ivd_judgment_capture."},
                "project_root": {"type": "string", "description": "Optional path to repo root."},
            }, "required": ["entry_id"]},
        ),
        Tool(
            name="ivd_judgment_save_codified",
            description="Persist the agent-filled codified fields. Validates the 5 required fields and capability_subtype (when fix_action_type=capability_addition), then transitions the ledger entry from raw → codified. Dormant unless `.judgment/` exists. (IVD v3.0)",
            inputSchema={"type": "object", "properties": {
                "entry_id": {"type": "string", "description": "Ledger entry id."},
                "codified_yaml": {"type": "string", "description": "YAML containing a `codified:` block with the 5 required fields, optionally a top-level `leo_domain_depth`."},
                "project_root": {"type": "string", "description": "Optional path to repo root."},
            }, "required": ["entry_id", "codified_yaml"]},
        ),
        Tool(
            name="ivd_judgment_pair",
            description="Capture a comparison_pair entry — the IVD Judgment alternative to A/B testing for real-world data (Pearl Rung-1: association, not intervention). Each diagnostic_hypothesis MUST list at least one competing_hypothesis. New pairs start at injection_status=plausible; need 2+ independent corroborating pairs to be promoted to corroborated and join the What Works injection layer. Dormant unless `.judgment/` exists. (IVD v3.0)",
            inputSchema={"type": "object", "properties": {
                "domain": {"type": "string", "description": "Domain id."},
                "run_a": {"type": "object", "description": "First run: {ref, outcome, inputs, context, metadata}."},
                "run_b": {"type": "object", "description": "Second run: {ref, outcome, inputs, context, metadata}."},
                "observed_differences": {"type": "array", "items": {"type": "string"}, "description": "List of concrete differences between run_a and run_b."},
                "diagnostic_hypotheses": {"type": "array", "items": {"type": "object"}, "description": "List of {hypothesis, competing_hypotheses (>=1), supporting_evidence?}."},
                "notes": {"type": "string", "description": "Optional notes."},
                "project_root": {"type": "string", "description": "Optional path to repo root."},
            }, "required": ["domain", "run_a", "run_b", "observed_differences", "diagnostic_hypotheses"]},
        ),
        Tool(
            name="ivd_judgment_detect_patterns",
            description="Cluster codified ledger entries by (domain, normalized diagnosed_cause). Promotes any cluster with 3+ members (configurable via min_members) to a pattern file under `.judgment/patterns/`. Computes weighted_confidence using leo_domain_depth and freshness using the domain baseline's pattern_half_life_days. Dormant unless `.judgment/` exists. (IVD v3.0)",
            inputSchema={"type": "object", "properties": {
                "domain": {"type": "string", "description": "Optional: limit to one domain."},
                "min_members": {"type": "integer", "description": "Promotion threshold (default 3)."},
                "project_root": {"type": "string", "description": "Optional path to repo root."},
            }, "required": []},
        ),
        Tool(
            name="ivd_judgment_inject_context",
            description="Return prioritized Judgment context for downstream agents. Three layers: (1) distilled patterns (active, freshness ∈ {fresh, aging}, sorted by weighted_confidence × member_count), (2) recent codified corrections in the same domain (last 5), (3) What Works hypotheses (only corroborated comparison pairs). Soft token_budget cap. Use this to inject judgment knowledge into the next agent run's system message. Dormant unless `.judgment/` exists. (IVD v3.0)",
            inputSchema={"type": "object", "properties": {
                "domain": {"type": "string", "description": "Optional: filter all layers to one domain."},
                "task_type": {"type": "string", "description": "Optional: task context hint (e.g. 'generate-script'). Echoed back in response; reserved for task-scoped injection in a future release."},
                "token_budget": {"type": "integer", "description": "Soft token budget for the rendered context (default 1500)."},
                "project_root": {"type": "string", "description": "Optional path to repo root."},
            }, "required": []},
        ),
        Tool(
            name="ivd_judgment_propose_recommendation",
            description="Draft a recommendation against a detected pattern. For prompt_patch and intent_revision fix_action_types, also emits a draft_recipe_yaml the agent can review. For capability_addition, infers capability_subtype (build|buy|hire|partner) from the pattern's members. Recommendation lands in approval=pending_user and awaits your gate. Dormant unless `.judgment/` exists. (IVD v3.0)",
            inputSchema={"type": "object", "properties": {
                "pattern_id": {"type": "string", "description": "Pattern id (filename stem under .judgment/patterns/)."},
                "notes": {"type": "string", "description": "Optional notes."},
                "project_root": {"type": "string", "description": "Optional path to repo root."},
            }, "required": ["pattern_id"]},
        ),
        Tool(
            name="ivd_judgment_check_installed",
            description="Detect Judgment-phase activation across one or more projects. Two modes: (a) workspace_root set — scan recursively (up to max_depth) for `.judgment/` folders and return per-project summaries (engine_version, ivd_version, baseline / ledger / pattern / recommendation counts, domains); (b) workspace_root unset — report on the single project_root. NEVER writes to disk — read-only by design (analog to canon_check_rules_installed's never-writes invariant). Use this to ask 'which projects in my workspace have the Judgment phase activated?' without spelunking the filesystem. (IVD v3.1, R6)",
            inputSchema={"type": "object", "properties": {
                "workspace_root": {"type": "string", "description": "Optional: scan this directory recursively for `.judgment/` folders. When omitted, falls back to project_root mode."},
                "max_depth": {"type": "integer", "description": "Workspace mode only: max recursion depth (default 3). VCS / virtualenv / node_modules dirs are always skipped.", "default": 3},
                "project_root": {"type": "string", "description": "Project mode only: path to repo root (when workspace_root is unset)."},
            }, "required": []},
        ),

        # -------------------------------------------------------------------
        # Canon — Human Translation Layer (Phase 0b, IVD v3.1)
        # Hosted inside this IVD MCP server so every existing IVD client
        # picks them up automatically — zero `mcpServers` config edit.
        # Opt-out: IVD_CANON_TOOLS_ENABLED=false.
        # See canon_layer.md §Phase 0b MCP tools.
        # -------------------------------------------------------------------
        Tool(
            name="canon_render",
            description="Canon — render any AI text as a CanonDocument (Setting Phase, confidence-marked body, verification beats, folk-theory notes, identity statement). Tier 1 from raw `text`; Tier 2 from a structured `contract`. Returns markdown by default plus the audit verdict so the caller can gate downstream actions on it. Reference: ivd/canon_layer.md.",
            inputSchema={"type": "object", "properties": {
                "text": {"type": "string", "description": "Raw AI output to render (Tier 1 path). Provide either `text` or `contract`."},
                "contract": {"type": "object", "description": "Structured CanonContract (Tier 2 path). Fields: setting, body, confidence_marks[], decision_points[], folk_theory_corrections[], identity_statement, domain_pack, stakes."},
                "stakes": {"type": "string", "description": "Stakes hint that gates verification beat emission.", "enum": ["low", "medium", "high", "irreversible"], "default": "medium"},
                "domain_pack": {"type": "string", "description": "Domain pack id (e.g., 'general', 'medical', 'finance'). Default 'general'.", "default": "general"},
                "identity_statement": {"type": "string", "description": "AI identity statement (R14). Default: 'I am an AI assistant.'"},
                "output_format": {"type": "string", "description": "What to return.", "enum": ["markdown", "json", "both"], "default": "markdown"},
            }, "required": []},
        ),
        Tool(
            name="canon_check",
            description="Canon — audit text or a CanonDocument against R-invariants (engine v0.2.0 enforces R1, R2, R5, R10, R13, R14; R13 is the stakes-adaptive format heuristic added in v0.2.0; R3/R4/R6/R7/R8/R9/R11/R12 remain 'partial' by design — see canon_layer.md and audit.py). Returns an AuditReport with per-R findings, severities, an overall verdict in {pass, fail, safety_fail, partial}, and a reproducible hash for R9 diffability. Reference: ivd/canon_layer.md §Audit.",
            inputSchema={"type": "object", "properties": {
                "text": {"type": "string", "description": "Raw text — Canon will Tier-1-render then audit. Provide either `text` or `document`."},
                "document": {"type": "object", "description": "A previously rendered CanonDocument (output of canon_render's `document` field). Audited as-is."},
                "stakes": {"type": "string", "description": "Stakes hint (only used when starting from `text`).", "enum": ["low", "medium", "high", "irreversible"], "default": "medium"},
                "domain_pack": {"type": "string", "description": "Domain pack id (default 'general').", "default": "general"},
            }, "required": []},
        ),
        Tool(
            name="canon_diff",
            description="Canon — diff two AuditReports (before / after) and return per-R movement (fixed, regressed, unchanged) plus before/after hashes. Use to verify that an edit improved Canon compliance without regressing other invariants. Reference: ivd/canon_layer.md §Audit diff.",
            inputSchema={"type": "object", "properties": {
                "before": {"type": "object", "description": "AuditReport from canon_check on the original text."},
                "after":  {"type": "object", "description": "AuditReport from canon_check on the revised text."},
            }, "required": ["before", "after"]},
        ),
        Tool(
            name="canon_check_rules_installed",
            description="Canon — detect whether the IVD + Canon Phase 0a rules block (`<BEGIN-CANON v1.0>` / `<END-CANON v1.0>`) is installed in the active project's agent instruction files (.cursorrules, .clinerules, CLAUDE.md, .github/instructions/canon.md, AGENTS.md, .windsurf/rules/canon.md, optional ~/CLAUDE.md). NEVER writes to disk — when blocks are missing, returns ready-to-paste install_payload entries the AGENT must offer to the user with EXPLICIT permission before editing files. Reference: ivd/canon_layer.md, ivd/recipes/canon-rules.yaml.",
            inputSchema={"type": "object", "properties": {
                "project_root": {"type": "string", "description": "Path to repo root (absolute or relative). Defaults to IVD framework root for testing."},
                "install_missing": {"type": "boolean", "description": "Hint only. The tool never writes to disk regardless of this flag — the agent must obtain explicit user consent and perform the edits itself.", "default": False},
            }, "required": []},
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
    "ivd_review_intent": lambda artifact_yaml, **_: review_intent_tool(artifact_yaml),
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
    # Judgment phase (IVD v3.0) — opt-in via `.judgment/` folder
    "ivd_judgment_init": lambda project_root=None, domains=None, **_: judgment_init_tool(project_root, domains),
    "ivd_judgment_capture": lambda raw_correction, domain, source="leo_intuition", correction_type="regression", agent=None, model=None, scope=None, originated_from_tool=None, project_root=None, **_: judgment_capture_tool(raw_correction, domain, source, correction_type, project_root, agent, model, scope, originated_from_tool),
    "ivd_judgment_codify": lambda entry_id, project_root=None, **_: judgment_codify_tool(entry_id, project_root),
    "ivd_judgment_save_codified": lambda entry_id, codified_yaml, project_root=None, **_: judgment_save_codified_tool(entry_id, codified_yaml, project_root),
    "ivd_judgment_pair": lambda domain, run_a, run_b, observed_differences, diagnostic_hypotheses, notes=None, project_root=None, **_: judgment_pair_tool(domain, run_a, run_b, observed_differences, diagnostic_hypotheses, project_root, notes),
    "ivd_judgment_detect_patterns": lambda domain=None, min_members=3, project_root=None, **_: judgment_detect_patterns_tool(project_root, domain, min_members),
    "ivd_judgment_inject_context": lambda domain=None, task_type=None, token_budget=1500, project_root=None, **_: judgment_inject_context_tool(project_root, domain, task_type, token_budget),
    "ivd_judgment_propose_recommendation": lambda pattern_id, notes=None, project_root=None, **_: judgment_propose_recommendation_tool(pattern_id, project_root, notes),
    "ivd_judgment_check_installed": lambda workspace_root=None, max_depth=3, project_root=None, **_: judgment_check_installed_tool(project_root, workspace_root, max_depth),
    # Canon — Human Translation Layer (Phase 0b, hosted inside this IVD MCP server)
    "canon_render": lambda text=None, contract=None, stakes=None, domain_pack=None, identity_statement=None, output_format="markdown", **_: canon_render_tool(text, contract, stakes, domain_pack, identity_statement, output_format),
    "canon_check":  lambda text=None, document=None, stakes=None, domain_pack=None, **_: canon_check_tool(text, document, stakes, domain_pack),
    "canon_diff":   lambda before, after, **_: canon_diff_tool(before, after),
    "canon_check_rules_installed": lambda project_root=None, install_missing=False, **_: canon_check_rules_installed_tool(project_root, install_missing),
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
