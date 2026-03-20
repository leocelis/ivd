# mcp_server/tools/learning.py

"""Tools: ivd_discover_goal, ivd_teach_concept — Principle 6 extensions."""

import json
from typing import Optional

import yaml
from termcolor import colored

from mcp_server.tools.recipes import list_recipes_tool
from mcp_server.tools.discover import list_features_tool

LOG = "IVD Tools"


def discover_goal_tool(
    domain_or_context: Optional[str] = None,
    user_hint: Optional[str] = None,
    project_root: Optional[str] = None,
) -> str:
    """Propose 2-3 candidate goals when the user doesn't know what to ask."""
    print(colored(f"[{LOG}] ivd_discover_goal", "cyan"))

    candidates = []

    try:
        recipes_data = json.loads(list_recipes_tool())
        for r in recipes_data.get("recipes", [])[:4]:
            name = r.get("name", "")
            desc = r.get("description", "")
            use_cases = ", ".join(r.get("use_cases", [])[:2]) or "general"
            candidates.append({
                "direction": f"Use recipe **{name}**: {desc}",
                "best_for": use_cases,
                "tradeoff": "Follow recipe template; fill in your domain specifics.",
                "next_step": f"ivd_load_recipe(recipe_name='{name}') then describe your goal.",
            })
    except Exception:
        candidates.append({
            "direction": "Use IVD recipes (agent-classifier, workflow-orchestration, etc.)",
            "best_for": "classification, workflows, background jobs, document extraction",
            "tradeoff": "Pick one recipe then describe your goal.",
            "next_step": "ivd_list_recipes() to choose.",
        })

    if project_root:
        try:
            features_data = json.loads(list_features_tool(project_root_arg=project_root))
            for f in features_data.get("features", [])[:3]:
                fid = f.get("feature_id") or f.get("path", "")
                summary = (f.get("summary") or "")[:80]
                candidates.append({
                    "direction": f"Extend existing: **{fid}** — {summary}",
                    "best_for": "avoid duplication, align with current design",
                    "tradeoff": "Must align with existing intent and constraints.",
                    "next_step": f"Read intent at {f.get('path', '')} then describe extension.",
                })
        except Exception:
            pass

    candidates = candidates[:3]

    result = {
        "purpose": "Discovery before intent: choose a direction, then describe and let AI write intent (Principle 6).",
        "candidate_directions": candidates,
        "usage": "Present these to the user; after they pick, proceed with: describe → AI writes intent → review → implement → verify.",
    }
    if domain_or_context or user_hint:
        result["context_used"] = {"domain_or_context": domain_or_context, "user_hint": user_hint}

    print(colored(f"[{LOG}] Discovery: {len(candidates)} candidates", "green"))
    return json.dumps(result, indent=2)


def teach_concept_tool(
    concept: str,
    user_context: Optional[str] = None,
) -> str:
    """Create structured educational artifact for a concept."""
    print(colored(f"[{LOG}] ivd_teach_concept: {concept}", "cyan"))

    concept_lower = concept.lower()

    if "etl" in concept_lower:
        template = {
            "concept": "ETL (Extract, Transform, Load)",
            "what_it_is": "ETL is a data pipeline pattern: Extract data from sources, Transform it to match target schema/business rules, Load it into a destination system.",
            "why_it_matters_here": user_context or "Relevant for data integration and sync workflows.",
            "key_concepts": [
                {"name": "Extract", "definition": "Read data from source system (API, database, file)", "example": "Pull leads from Salesforce REST API"},
                {"name": "Transform", "definition": "Apply business rules, normalize schema, enrich data", "example": "Convert Status field to lead_stage enum"},
                {"name": "Load", "definition": "Write data to destination system", "example": "Insert/update rows using UPSERT"},
            ],
            "tradeoffs": [
                {"decision": "Batch vs Streaming", "options": [
                    {"name": "Batch", "when": "Daily/hourly sync acceptable", "pros": ["Simpler", "Lower cost"], "cons": ["Data lag"]},
                    {"name": "Streaming", "when": "Sub-second latency needed", "pros": ["Real-time"], "cons": ["More complex", "Higher cost"]},
                ]},
            ],
            "common_patterns": [
                "Incremental batch: daily sync using LastModifiedDate",
                "Full refresh nightly: replace all data (simple, small datasets)",
                "CDC: stream changes as they happen (advanced, real-time)",
            ],
            "next_steps": "Now that you understand ETL, we can: (1) Discovery to pick pattern, (2) Describe requirements, (3) Write intent, (4) Implement.",
            "verification": [
                {"question": "What are the 3 steps of ETL?", "answer": "Extract, Transform, Load"},
                {"question": "When batch vs streaming?", "answer": "Batch for daily/hourly (simpler). Streaming for real-time (complex)."},
            ],
        }
    else:
        template = {
            "concept": concept,
            "what_it_is": f"[AI: Provide 2-3 sentence explanation of {concept}]",
            "why_it_matters_here": user_context or f"[AI: Explain why {concept} is relevant]",
            "key_concepts": [{"name": "[Sub-concept]", "definition": "[What it is]", "example": "[Concrete example]"}],
            "tradeoffs": [{"decision": f"[Key decision about {concept}]", "options": [{"name": "[Option A]", "when": "[When to use]", "pros": ["[+]"], "cons": ["[-]"]}]}],
            "common_patterns": [f"[Pattern 1 for {concept}]", f"[Pattern 2]"],
            "next_steps": f"Now that you understand {concept}, we can: (1) Discovery, (2) Describe requirements, (3) Write intent, (4) Implement.",
            "verification": [{"question": f"[Test question about {concept}]", "answer": "[Expected answer]"}],
        }

    artifact = {
        "education": template,
        "meta": {
            "purpose": f"Structured explanation of {concept} before IVD flow",
            "status": "canonical",
            "principle": "Principle 6: AI as Understanding Partner (teaching extension)",
            "next_action": "User reviews, confirms understanding, then discovery → describe → intent → implement",
        },
    }

    print(colored(f"[{LOG}] Educational artifact created: {concept}", "green"))
    return yaml.dump(artifact, sort_keys=False, default_flow_style=False)
