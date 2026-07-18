# ivd/judgment/detect.py

"""
Judgment engine — pattern detection (cluster ledger entries by diagnosed_cause).

The detection algorithm is intentionally conservative:

  1. Read all ledger entries in states (codified, paired, resolved).
  2. Cluster by ``(domain, normalized first-line of diagnosed_cause)``.
  3. Promote any cluster with ``member_count >= PATTERN_PROMOTION_THRESHOLD``.
  4. For each promoted cluster, compute weighted_confidence using the
     Expert Intuition Principle weights (DEPTH_WEIGHT) — entry > baseline.
  5. Compute freshness from the most recent member's timestamp + the
     domain baseline's half_life_days.
  6. Stamp the resulting Pattern with engine_version + reproducible
     detection_hash (R3 — borrowed from Canon's audit hash).

Reference:
  ivd/judgment_layer.md §3.5 (pattern promotion),
                       §3.4 (Expert Intuition weighting).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

from judgment.freshness import age_days, freshness_for
from judgment.schema import (
    DEPTH_WEIGHT,
    ENGINE_VERSION,
    PATTERN_PROMOTION_THRESHOLD,
    Pattern,
    _now_iso,
)
from judgment.store import JudgmentStore, slugify


def detect_patterns(
    store: JudgmentStore,
    domain_filter: str = None,
    min_members: int = PATTERN_PROMOTION_THRESHOLD,
) -> Tuple[List[Pattern], List[Dict[str, Any]], int]:
    """Cluster + promote patterns.

    Returns ``(promoted_patterns, skipped_clusters, scanned_entry_count)``.

    Promoted patterns are *not* persisted by this function — the caller is
    responsible for ``store.write_pattern(p)`` and for stamping member
    ``pattern_membership``. This separation keeps detection unit-testable
    against an in-memory store.
    """
    entries = store.iter_ledger("codified", "paired", "resolved")
    clusters: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)

    for state, fp, payload in entries:
        codified = payload.get("codified") or {}
        cause = (codified.get("diagnosed_cause") or "").strip()
        cls = payload.get("classification") or {}
        ent_domain = cls.get("domain") or "unknown"
        if domain_filter and ent_domain != domain_filter:
            continue
        if not cause:
            continue
        # Cluster key = (domain, normalized first-line of cause)
        key = (ent_domain, slugify(cause.split("\n", 1)[0], 80))
        clusters[key].append(
            {"state": state, "path": str(fp), "id": payload.get("id"), "payload": payload}
        )

    promoted: List[Pattern] = []
    skipped: List[Dict[str, Any]] = []

    for (cluster_domain, cause_slug), members in clusters.items():
        if len(members) < min_members:
            skipped.append({
                "domain": cluster_domain,
                "cause_slug": cause_slug,
                "member_count": len(members),
                "reason": f"below threshold ({min_members})",
            })
            continue

        baseline_raw = store.baseline_raw(cluster_domain)
        half_life = store.half_life_for(cluster_domain)

        weight_sum = 0.0
        depth_counts: Counter = Counter()
        tools_seen: Counter = Counter()
        member_ids: List[str] = []
        last_added = None
        for m in members:
            payload = m["payload"]
            depth = JudgmentStore.depth_for_entry(payload, baseline_raw)
            depth_counts[depth] += 1
            weight_sum += DEPTH_WEIGHT.get(depth, 0.4)
            member_ids.append(payload.get("id"))
            t = payload.get("originated_from_tool")
            if t:
                tools_seen[t] += 1
            ts = (payload.get("changelog") or [{}])[-1].get("date") or payload.get("created")
            last_added = max(filter(None, [last_added, ts]))

        weighted_confidence = round(weight_sum / max(len(members), 1), 3)
        last_ts_iso = last_added if last_added and "T" in (last_added or "") else None
        freshness = freshness_for(age_days(last_ts_iso), half_life)

        causes = Counter(
            (m["payload"].get("codified") or {}).get("diagnosed_cause", "").strip()
            for m in members
        )
        fixes = Counter(
            (m["payload"].get("codified") or {}).get("proposed_fix", "").strip()
            for m in members
        )
        fix_action_types = Counter(
            (m["payload"].get("codified") or {}).get("fix_action_type", "").strip()
            for m in members
        )

        pattern_id = f"{cluster_domain}__{cause_slug}"
        existing = store.read_pattern(pattern_id)
        created_iso = existing.created if existing else _now_iso()

        scope = {
            "systems": list({
                (m["payload"].get("classification") or {}).get("scope")
                for m in members
                if (m["payload"].get("classification") or {}).get("scope")
            }),
            "models": list({
                (m["payload"].get("classification") or {}).get("model")
                for m in members
                if (m["payload"].get("classification") or {}).get("model")
            }),
            "recipes": [],
        }
        agent_class = (members[0]["payload"].get("classification") or {}).get("agent")

        pattern = Pattern(
            id=pattern_id,
            created=created_iso,
            updated=_now_iso(),
            domain=cluster_domain,
            agent_class=agent_class,
            scope=scope,
            diagnosed_cause=causes.most_common(1)[0][0] if causes else "",
            recommended_fix=fixes.most_common(1)[0][0] if fixes else "",
            fix_action_type=fix_action_types.most_common(1)[0][0] if fix_action_types else "",
            # Preserve human-authored craft guidance across re-detection.
            never=(existing.never if existing else []),
            related_files=(existing.related_files if existing else []),
            members=member_ids,
            member_count=len(members),
            depth_distribution=dict(depth_counts),
            weighted_confidence=weighted_confidence,
            half_life_days=half_life,
            last_member_added=last_added,
            freshness=freshness,
            tool_origin={
                "originated_from_tool_counts": dict(tools_seen),
                "net_pattern_delta_note": (
                    "Compute net_pattern_delta out-of-band: "
                    "patterns_introduced_by_tool − patterns_eliminated_by_tool. "
                    "Flag the tool as a deprecation candidate when delta > 0."
                ),
            },
            status=(existing.status if existing else "active"),
            engine_version=ENGINE_VERSION,
        )
        pattern.stamp_hash()
        promoted.append(pattern)

    return promoted, skipped, len(entries)
