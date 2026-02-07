# mcp_server/tools/inversions.py

"""Tool: ivd_propose_inversions — Principle 8: Innovation through Inversion."""

import json
from typing import Optional

from termcolor import colored

LOG = "IVD Tools"


def propose_inversions_tool(
    problem_description: str,
    domain_context: Optional[str] = None,
) -> str:
    """Scaffold inversion opportunities for a problem (Principle 8)."""
    print(colored(f"[{LOG}] ivd_propose_inversions: {problem_description[:60]}...", "cyan"))

    scaffold = {
        "inversion_opportunities": {
            "problem": problem_description,
            "domain_context": domain_context or "",
            "dominant_belief": "",
            "proposed_inversions": [],
        },
        "guidance": {
            "principle_8_steps": [
                "1. State the Default: What is the conventional way? → fill dominant_belief",
                "2. Invert: What would the opposite approach look like? → add 2-4 proposed_inversions",
                "3. Evaluate: For each inversion, add rationale (pros, cons, feasibility)",
                "4. Implement: Set status to chosen | rejected | deferred",
            ],
            "proposed_inversions_schema": {
                "name": "Short label",
                "description": "What the opposite approach is",
                "rationale": "Why promising or why rejected",
                "status": "chosen | rejected | deferred",
            },
            "next_steps": [
                "Fill dominant_belief and proposed_inversions",
                "Optionally use ivd_scaffold to create an intent and paste inversion_opportunities",
                "Ensure chosen inversions are reflected in intent and constraints",
            ],
        },
    }

    print(colored(f"[{LOG}] Inversion scaffold ready", "green"))
    return json.dumps(scaffold, indent=2)
