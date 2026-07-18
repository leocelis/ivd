# ivd/judgment/inject.py

"""
Judgment engine — prioritized context injection for downstream agents.

Four layers, in priority order:
  1. patterns               — distilled (3+ members), freshness ∈ {fresh, aging},
                              sorted by weighted_confidence × member_count.
  2. recent_corrections     — last 5 codified entries in the same domain
                              (still useful even before a pattern exists).
  3. ruled_out              — REJECTED comparison_pair hypotheses (Pearl Rung-1 →
                              "this was tried and disproven; do not retry it").
                              A hard veto layer: negative knowledge the loop needs
                              so it does not re-derive an already-falsified theory.
  4. what_works             — corroborated comparison_pair hypotheses
                              (Pearl Rung-1 → "this rivals these alternatives").

A soft token budget (4 chars per token proxy) trims the lowest-priority layers
first. The InjectionResult is stamped with engine_version + a reproducible
``injection_hash`` so callers can diff context across runs (R3 — borrowed
from Canon's audit hash).

Reference:
  ivd/judgment_layer.md §4 (injection),
                       §4.2 (freshness gating),
                       §4.3 (Pearl Rung-1 What Works layer).
"""

from __future__ import annotations

import json
from typing import Optional

from judgment.schema import (
    DEFAULT_INJECT_TOKEN_BUDGET,
    Freshness,
    InjectionResult,
    InjectionStatus,
)
from judgment.store import JudgmentStore


def inject_context(
    store: JudgmentStore,
    domain: Optional[str] = None,
    task_type: Optional[str] = None,
    token_budget: int = DEFAULT_INJECT_TOKEN_BUDGET,
) -> InjectionResult:
    """Build a 3-layer InjectionResult from the store, respecting the token budget."""
    char_budget = max(token_budget, 200) * 4

    # Layer 1: patterns
    patterns_layer = []
    for fp, p in store.iter_patterns():
        if domain and p.domain != domain:
            continue
        if p.status not in (None, "active"):
            continue
        if p.freshness == Freshness.EXPIRED.value:
            continue
        patterns_layer.append({
            "pattern_id": p.id,
            "domain": p.domain,
            "diagnosed_cause": p.diagnosed_cause,
            "recommended_fix": p.recommended_fix,
            "fix_action_type": p.fix_action_type,
            "freshness": p.freshness,
            "weighted_confidence": p.weighted_confidence,
            "member_count": p.member_count,
        })
    patterns_layer.sort(
        key=lambda x: (
            -(x.get("weighted_confidence") or 0),
            -(x.get("member_count") or 0),
        )
    )

    # Layer 2: recent codified corrections
    recent_layer = []
    for state, fp, payload in store.iter_ledger("codified", "resolved"):
        cls = payload.get("classification") or {}
        if domain and cls.get("domain") != domain:
            continue
        codified = payload.get("codified") or {}
        recent_layer.append({
            "entry_id": payload.get("id"),
            "domain": cls.get("domain"),
            "expected_result": codified.get("expected_result"),
            "diagnosed_cause": codified.get("diagnosed_cause"),
            "proposed_fix": codified.get("proposed_fix"),
            "fix_action_type": codified.get("fix_action_type"),
            "created": payload.get("created"),
        })
    recent_layer.sort(key=lambda x: (x.get("created") or ""), reverse=True)
    recent_layer = recent_layer[:5]

    # Layer 3: ruled_out — REJECTED comparison pairs (a hard veto: do not retry).
    # Layer 4: what_works — corroborated comparison pairs.
    ruled_out_layer = []
    what_works_layer = []
    for state, fp, payload in store.iter_ledger("paired", "resolved"):
        if payload.get("kind") != "comparison_pair":
            continue
        cls = payload.get("classification") or {}
        if domain and cls.get("domain") != domain:
            continue
        status = payload.get("injection_status")
        if status == InjectionStatus.REJECTED.value:
            for dh in payload.get("diagnostic_hypotheses") or []:
                ruled_out_layer.append({
                    "from_pair": payload.get("id"),
                    "domain": cls.get("domain"),
                    "hypothesis": dh.get("hypothesis"),
                    "competing_hypotheses": dh.get("competing_hypotheses"),
                    "notes": payload.get("notes"),
                })
        elif status == InjectionStatus.CORROBORATED.value:
            for dh in payload.get("diagnostic_hypotheses") or []:
                what_works_layer.append({
                    "from_pair": payload.get("id"),
                    "domain": cls.get("domain"),
                    "hypothesis": dh.get("hypothesis"),
                    "competing_hypotheses": dh.get("competing_hypotheses"),
                })

    rendered = {
        "patterns": patterns_layer,
        "recent_corrections": recent_layer,
        "ruled_out": ruled_out_layer,
        "what_works": what_works_layer,
    }
    text_size = len(json.dumps(rendered))
    truncated = False
    while text_size > char_budget and (
        rendered["patterns"] or rendered["recent_corrections"]
        or rendered["ruled_out"] or rendered["what_works"]
    ):
        if rendered["what_works"]:
            rendered["what_works"].pop()
        elif rendered["recent_corrections"]:
            rendered["recent_corrections"].pop()
        elif rendered["ruled_out"]:
            rendered["ruled_out"].pop()
        elif rendered["patterns"]:
            rendered["patterns"].pop()
        text_size = len(json.dumps(rendered))
        truncated = True

    result = InjectionResult(
        domain_filter=domain,
        task_type=task_type,
        token_budget=token_budget,
        approx_tokens=text_size // 4,
        truncated=truncated,
        context=rendered,
    )
    result.stamp_hash()
    return result
