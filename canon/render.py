# ivd/canon/render.py

"""
Narrative renderer — Contract → CanonDocument.

Deterministic. No LLM call. The renderer is the *single* place where Canon
turns structured intent into human-facing prose.

Reference: CANON_TECH_SPEC.md v0.6 §5.3 (renderer rules), §6 (CanonDocument).
"""

from __future__ import annotations

import re
from typing import Dict, List

from canon.contract import (
    CanonContract,
    CanonDocument,
    ConfidenceMark,
    DecisionPoint,
    Stakes,
)


_TIER_GLYPH: Dict[str, str] = {
    "verified": "● verified",
    "inferred": "◐ inferred",
    "assumed":  "○ assumed",
}


def _tag_for(tier: str) -> str:
    return _TIER_GLYPH.get(tier, f"· {tier}")


def _annotate_body_with_marks(body: str, marks: List[ConfidenceMark]) -> str:
    """Insert R2 markers next to each load-bearing claim.

    We only annotate the first occurrence of each claim string so the body
    does not become noisy. Annotations are inline, parenthetical, and short.
    """
    out = body
    seen: set = set()
    for mark in marks:
        claim = (mark.claim or "").strip()
        if not claim or claim in seen:
            continue
        seen.add(claim)
        glyph = _tag_for(mark.tier)
        # Find the claim verbatim; if not present, skip silently.
        idx = out.find(claim)
        if idx == -1:
            continue
        # Insert " (◐ inferred)" right after the claim.
        insert_at = idx + len(claim)
        out = out[:insert_at] + f" ({glyph})" + out[insert_at:]
    return out


def _verification_beat_for(dp: DecisionPoint) -> Dict[str, str]:
    rev = "no — irreversible" if not dp.reversible else f"yes — {dp.smallest_undo or 'reversible'}"
    return {
        "action": dp.action,
        "reversible": rev,
        "approve_prompt": "reply YES to proceed" if not dp.reversible else "reply YES to proceed (reversible)",
        "stakes": dp.stakes.value,
    }


def render(contract: CanonContract) -> CanonDocument:
    """Project a CanonContract into a CanonDocument (deterministic)."""
    body_with_marks = _annotate_body_with_marks(contract.body, contract.confidence_marks)

    # R5 — only emit verification beats for irreversible / high-stakes actions
    # at MEDIUM stakes or above, to avoid R4-violating noise on chit-chat.
    beats: List[Dict[str, str]] = []
    if contract.stakes in (Stakes.MEDIUM, Stakes.HIGH, Stakes.IRREVERSIBLE):
        for dp in contract.decision_points:
            if dp.stakes in (Stakes.HIGH, Stakes.IRREVERSIBLE) or not dp.reversible:
                beats.append(_verification_beat_for(dp))

    return CanonDocument(
        setting_phase=contract.setting or "",
        body_with_marks=body_with_marks,
        verification_beats=beats,
        folk_theory_notes=list(contract.folk_theory_corrections),
        identity_statement=contract.identity_statement or "",
        raw_input=contract.body,
        domain_pack=contract.domain_pack,
        stakes=contract.stakes,
    )
