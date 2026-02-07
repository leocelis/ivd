# mcp_server/tools/context.py

"""Tool: ivd_get_context — curated IVD summary for AI agents."""

import json
from termcolor import colored
from mcp_server.tools._paths import get_framework_path

LOG = "IVD Tools"


def get_context_tool() -> str:
    """Get complete IVD context for AI agent."""
    print(colored(f"[{LOG}] ivd_get_context", "cyan"))

    ivd = get_framework_path()
    recipes_dir = ivd / "recipes"
    recipes = [f.stem for f in recipes_dir.glob("*.yaml") if f.stem != "README"]

    context = {
        "purpose": "IVD (Intent-Verified Development) makes software understanding executable, verifiable, and durable. Intent is the primary artifact — code and docs derive from it.",
        "core_principles": [
            "1. Intent is Primary — Intent describes WHAT/WHY, code describes HOW",
            "2. Understanding Must Be Executable — Every claim links to verifiable tests",
            "3. Bidirectional Synchronization — Changes flow intent↔code↔docs with verification",
            "4. Continuous Verification — Verify alignment at every commit/PR/deploy",
            "5. Layered Understanding — Intent→Constraints→Rationale→Alternatives→Risks",
            "6. AI as Understanding Partner — AI writes intent, implements, verifies; teaches when user lacks knowledge; discovers when user can't describe",
            "7. Understanding Survives Implementation — Intent persists through rewrites/tech changes",
            "8. Innovation through Inversion — State default, invert, evaluate, implement; capture in inversion_opportunities",
        ],
        "when_to_use_ivd": [
            "New AI agents or major agent modifications",
            "New modules/systems with business logic",
            "Features with constraints that must be verified",
            "Multi-step workflows across files/functions",
            "Significant architectural decisions",
        ],
        "when_to_skip_ivd": [
            "Small bug fixes or typo corrections",
            "Simple refactors without logic changes",
            "UI-only changes without business logic",
            "Configuration updates",
            "Minor utility functions",
        ],
        "when_to_use_principle_8_inversion": [
            "Designing: new or major intent (feature, module, redesign)",
            "Problem has a conventional or 'obvious' approach",
            "Stakes matter: performance, scale, security, or maintainability",
            "You want intent to document why the default was rejected or inverted",
        ],
        "when_to_skip_principle_8_inversion": [
            "Small change: bug fix, config, typo, simple refactor",
            "No clear default approach",
            "Obvious solution is good enough",
        ],
        "workflow_placement": "Workflow-level: recommended workflows/; alternative alongside coordinator when single-orchestrator.",
        "placement_per_project": "Intent placement is per-project (co-locate with code). For scaffold/find/check/list_features: pass project_root when working in a repo other than the default.",
        "naming_for_tools": "Module intents must use {module}_intent.yaml pattern (not bare intent.yaml) for tool discovery. Task intents must be in intents/ subfolder.",
        "parent_intent": "Non-system intents should set parent_intent to establish hierarchy.",
        "level_detection": "Tools detect level by path: intents/→task, workflows/→workflow, _system_intent→system, else→module.",
        "available_recipes": recipes,
        "available_templates": ["intent", "recipe", "task", "workflow"],
        "key_metrics": {
            "knowledge_capture": "85-95% (vs 10-15% traditional)",
            "context_reduction": "80-90% reduction in AI agent context needed",
            "onboarding_improvement": "40% faster",
        },
        "next_steps": [
            "For existing projects: Use ivd_init to bootstrap with project context",
            "Use ivd_list_recipes to see detailed recipe descriptions",
            "Use ivd_load_recipe to get a specific recipe pattern",
            "Use ivd_load_template to get a blank template",
            "Use ivd_scaffold to create new intents (auto-links parent_intent)",
            "Use ivd_propose_inversions to brainstorm inversions (Principle 8)",
            "Use ivd_validate to check artifact compliance",
        ],
    }

    print(colored(f"[{LOG}] Context loaded ({len(recipes)} recipes)", "green"))
    return json.dumps(context, indent=2)
