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
        "purpose": "IVD (Intent-Verified Development) makes software understanding executable, verifiable, and durable, and (v3.0) compounds organizational judgment via the opt-in Judgment phase. Intent is the primary artifact — code and docs derive from it.",
        "version": "3.1",
        "phases": [
            "1. Intent — declare what/why, with constraints + tests",
            "2. Implementation — constraint-segmented; AI implements against intent",
            "3. Verification — continuous alignment, post-impl protocol, lost-in-the-middle counter",
            "4. Judgment (NEW in v3.0, opt-in) — capture corrections, cluster patterns, inject context",
        ],
        "core_principles": [
            "1. Intent is Primary — Intent describes WHAT/WHY, code describes HOW",
            "2. Understanding Must Be Executable — Every claim links to verifiable tests",
            "3. Bidirectional Synchronization — Changes flow intent↔code↔docs with verification. Includes Empirical Refinement: when implementation reveals wrong assumptions, STOP→RECORD→UPDATE intent→ENRICH (search GitHub, read changelogs — not just parametric retry)→CONTINUE. 2-attempt rule: same error twice = mandatory external enrichment before retrying.",
            "4. Continuous Verification — Verify alignment at every commit/PR/deploy",
            "5. Layered Understanding — Intent→Constraints→Rationale→Alternatives→Risks",
            "6. AI as Understanding Partner — AI writes intent, stress-tests (constraint completeness, implementation gaps, implicit assumptions, satisfiability), implements using constraint-segmented approach (for 3+ constraints: GROUP→IMPLEMENT→RE-READ from disk→VERIFY per segment→cross-cut sweep; why: read-acknowledge-violate pattern + lost-in-the-middle >30% degradation + constraint compliance orthogonal to task completion), then verifies full cross-cut; teaches when user lacks knowledge; discovers when user can't describe",
            "7. Understanding Survives Implementation — Intent persists through rewrites/tech changes",
            "8. Innovation through Inversion — State default, invert, evaluate, implement; capture in inversion_opportunities",
            "9. Judgment Compounds (v3.0) — Structured corrections from real-world use are the most valuable contextual knowledge — they don't commoditize when models do. Opt-in per project via `<project_root>/.judgment/`. The 4th phase of IVD; canonical doc: judgment_layer.md",
        ],
        "judgment_phase": {
            "status": "opt-in (v3.0; refactored into engine package in v3.1)",
            "activation": "Run ivd_judgment_init at the project root to create the .judgment/ folder. The 9 judgment tools are dormant until that folder exists. Server-level opt-out via IVD_JUDGMENT_TOOLS_ENABLED=false (mirrors Canon's IVD_CANON_TOOLS_ENABLED knob).",
            "engine_package": "ivd/judgment/ — vendored engine (schema, store, freshness, detect, inject, validate). Mirrors ivd/canon/. Stamps engine_version + reproducible hashes on Pattern.detection_hash and InjectionResult.injection_hash.",
            "loop": [
                "0. Baseline & Goal Calibration",
                "1. Capture (raw, < 30s)",
                "2. Codify (5 fields)",
                "3. Pair (optional comparison_pair, Pearl Rung-1)",
                "4. Detect Patterns (3+ entries with same diagnosed_cause)",
                "5. Propose Recommendation (with build|buy|hire|partner sub-types)",
                "6. Approve (you)",
                "7. Apply Fix",
                "8. Inject Context (next runs)",
                "9. Resolve / Archive",
            ],
            "tools": [
                "ivd_judgment_init",
                "ivd_judgment_capture",
                "ivd_judgment_codify",
                "ivd_judgment_save_codified",
                "ivd_judgment_pair",
                "ivd_judgment_detect_patterns",
                "ivd_judgment_inject_context",
                "ivd_judgment_propose_recommendation",
                "ivd_judgment_check_installed",
            ],
            "artifact_types": ["baseline", "ledger_entry", "comparison_pair", "pattern"],
            "canonical_doc": "ivd/judgment_layer.md",
            "opt_out": "Set IVD_JUDGMENT_TOOLS_ENABLED=false on the IVD MCP server to disable all 9 Judgment tools (they remain registered but return a 'disabled' payload). Tool signatures never change mid-major version.",
        },
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
        "canon_layer": {
            "status": "bundled with IVD v3.1 (zero-config adoption)",
            "summary": "Canon — Human Translation Layer for AI output. Ships inside IVD: (a) as the canon-rules recipe for agent instruction files (Phase 0a), and (b) as four MCP tools hosted in the same IVD MCP server (Phase 0b).",
            "tools": [
                "canon_render",
                "canon_check",
                "canon_diff",
                "canon_check_rules_installed",
            ],
            "rules_recipe": "canon-rules",
            "install_flow": [
                "Run canon_check_rules_installed to detect whether the Phase 0a Canon Rules block is installed in the project's agent instruction files (.cursorrules / CLAUDE.md / AGENTS.md / .clinerules / .github/instructions/canon.md / .windsurf/rules/canon.md).",
                "The tool NEVER writes to disk. It returns a per-client install_payload the agent must offer to the user; the agent only edits files with explicit permission.",
                "Once installed, agents following the rules block emit Canon markers (✓ verified / ~ inferred / ? assumed, R5 verification beats on irreversible actions, folk-theory notes, bounded identity) that canon_check can then audit against R1–R14.",
            ],
            "opt_out": "Set IVD_CANON_TOOLS_ENABLED=false on the IVD MCP server to disable all four Canon tools (they remain registered but return a 'disabled' payload). Tool signatures never change mid-major version.",
            "docs": [
                "external/canon/CANON_PRD.md (v0.7)",
                "external/canon/CANON_TECH_SPEC.md (v0.6 §9B, §9C)",
                "external/canon/canon_system_intent.yaml (v5)",
            ],
        },
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
            "(v3.0) When real-world corrections start recurring: ivd_judgment_init to enable the Judgment phase, then ivd_judgment_capture / codify / detect_patterns / inject_context",
        ],
    }

    print(colored(f"[{LOG}] Context loaded ({len(recipes)} recipes)", "green"))
    return json.dumps(context, indent=2)
