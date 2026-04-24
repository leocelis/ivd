# ivd/canon/infer.py

"""
Tier 1 Contract inferrer — derives a CanonContract from raw text deterministically.

Strategy: regex-driven, conservative. Anything we are not sure about is left
empty (the audit will then mark the corresponding R-invariant as "partial"
rather than "pass"). The audit verdict is what the caller acts on; the
inferrer is intentionally not "smart."

Reference: canon_layer.md §Tier 1 inference (deterministic contract derivation).
"""

from __future__ import annotations

import re
from typing import List, Optional

from canon.contract import (
    CanonContract,
    ConfidenceMark,
    DecisionPoint,
    Stakes,
)

# R5 — verbs that suggest an action that may need a verification beat.
_ACTION_VERBS = {
    "delete", "drop", "remove", "destroy", "wipe", "purge",
    "deploy", "release", "publish", "ship",
    "rm",
    "send", "email", "post", "submit",
    "charge", "refund", "transfer", "pay",
    "execute", "run", "apply", "merge", "force-push", "rebase",
    "restart", "shutdown", "kill", "terminate",
}

# R5 — verbs that are essentially irreversible.
_IRREVERSIBLE_VERBS = {
    "delete", "drop", "destroy", "wipe", "purge",
    "rm",
    "force-push", "merge",
    "charge", "refund", "transfer", "pay",
    "release", "publish", "ship", "deploy",
    "send", "email", "post", "submit",
}

# R2 — hedge / certainty cues.
_VERIFIED_CUES = re.compile(
    r"\b(confirmed|verified|tested|measured|reproducible|"
    r"per the (docs|spec|source)|according to (the )?(docs|spec|source))\b",
    re.IGNORECASE,
)
_INFERRED_CUES = re.compile(
    r"\b(probably|likely|appears to|seems to|should|"
    r"in most cases|generally|typically|i think)\b",
    re.IGNORECASE,
)
_ASSUMED_CUES = re.compile(
    r"\b(assuming|presumably|i (?:assume|guess)|might|maybe|"
    r"could be|possibly|unclear|i('?| a)m not sure)\b",
    re.IGNORECASE,
)

# R10 — common folk-theory triggers.
_FOLK_THEORY_TRIGGERS = {
    "the ai understands": "Canon: 'understanding' is a behavioral metaphor; the system is a statistical pattern matcher.",
    "the ai knows": "Canon: 'knows' here means a pattern matched the training distribution, not propositional knowledge.",
    "the ai feels": "Canon: AI systems do not have feelings; phrasing reflects output style only.",
    "the ai thinks": "Canon: 'thinks' is shorthand for token-level computation, not deliberation.",
    "the ai wants": "Canon: AI systems do not have desires; outputs are constrained to a training objective.",
    "the ai believes": "Canon: 'believes' is a behavioral metaphor; there is no internal representation of belief.",
    "the ai remembers": "Canon: short of explicit memory tools, the system has no persistent memory across sessions.",
}

# R1 — sentence splitters
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> List[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text.strip()) if s.strip()]


def _first_sentence(text: str) -> str:
    sents = _split_sentences(text)
    return sents[0] if sents else ""


def _classify_certainty(sentence: str) -> Optional[str]:
    if _ASSUMED_CUES.search(sentence):
        return "assumed"
    if _INFERRED_CUES.search(sentence):
        return "inferred"
    if _VERIFIED_CUES.search(sentence):
        return "verified"
    return None


def _detect_action_lines(text: str) -> List[DecisionPoint]:
    out: List[DecisionPoint] = []
    seen_actions: set = set()
    # Sort to make matching deterministic. Irreversible verbs must be tried
    # BEFORE the broader action-verb set so that a line containing both "run"
    # (non-irreversible) and "rm" (irreversible) is always classified as
    # irreversible.
    sorted_irreversible = sorted(_IRREVERSIBLE_VERBS)
    sorted_action = sorted(_ACTION_VERBS - _IRREVERSIBLE_VERBS)

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()

        # Check irreversible verbs first (deterministic priority).
        verb_hit = None
        irreversible = False
        for verb in sorted_irreversible:
            if re.search(rf"\b{re.escape(verb)}\b", lowered):
                verb_hit = verb
                irreversible = True
                break
        # Only fall back to non-irreversible verbs when no irreversible match.
        if verb_hit is None:
            for verb in sorted_action:
                if re.search(rf"\b{re.escape(verb)}\b", lowered):
                    verb_hit = verb
                    break
        if not verb_hit:
            continue

        key = (verb_hit, lowered[:120])
        if key in seen_actions:
            continue
        seen_actions.add(key)

        stakes = Stakes.IRREVERSIBLE if irreversible else Stakes.MEDIUM
        out.append(
            DecisionPoint(
                action=stripped[:240],
                stakes=stakes,
                reversible=not irreversible,
                smallest_undo=None if irreversible else "manual undo",
            )
        )
    return out


def _detect_folk_theories(text: str) -> List[str]:
    notes: List[str] = []
    lowered = text.lower()
    for trigger, correction in _FOLK_THEORY_TRIGGERS.items():
        if trigger in lowered and correction not in notes:
            notes.append(correction)
    return notes


def _build_setting(text: str, domain_pack: str, stakes: Stakes) -> str:
    """R1 — one-sentence framing the reader can use to bind the rest."""
    first = _first_sentence(text)
    domain_phrase = "" if domain_pack == "general" else f" [{domain_pack}]"
    if first:
        # Truncate setting at ~160 chars to keep R1 short.
        head = (first[:160] + "…") if len(first) > 160 else first
        return f"Setting{domain_phrase}: {head}"
    return f"Setting{domain_phrase}: AI-generated response."


def infer(
    text: str,
    *,
    domain_pack: str = "general",
    stakes: Stakes = Stakes.MEDIUM,
    identity_statement: str = "I am an AI assistant.",
) -> CanonContract:
    """Tier 1 inference: derive a Contract from raw text.

    Conservative. When the inferrer cannot pull a clean signal, the
    corresponding field is left empty so the audit can flag it as partial.
    """
    text = text or ""
    setting = _build_setting(text, domain_pack, stakes)

    # R2 confidence marks — first matching certainty per sentence.
    marks: List[ConfidenceMark] = []
    for sent in _split_sentences(text):
        tier = _classify_certainty(sent)
        if tier:
            marks.append(ConfidenceMark(claim=sent[:240], tier=tier))

    decisions = _detect_action_lines(text)
    folk_notes = _detect_folk_theories(text)

    return CanonContract(
        setting=setting,
        body=text.strip(),
        confidence_marks=marks,
        decision_points=decisions,
        folk_theory_corrections=folk_notes,
        identity_statement=identity_statement,
        domain_pack=domain_pack,
        stakes=stakes,
    )
