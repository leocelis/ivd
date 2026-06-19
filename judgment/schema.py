# ivd/judgment/schema.py

"""
Judgment engine — typed schemas for ledger entries, comparison pairs, patterns,
baselines, recommendations, and injection results.

The engine deliberately uses ``@dataclasses.dataclass`` for every on-disk
artifact. Templates, validators, seeders, and runtime tools all read and write
through these dataclasses so the runtime schema and the file-system schema
cannot drift independently (the C-1 bug we fixed in v3.1 became impossible
once these classes existed).

Reference:
  ivd/judgment_layer.md §2 (artifact catalogue), §3 (state machine),
                       §3.4 (Expert Intuition Principle), §3.6 (freshness).
"""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums and constants surfaced from the schema (single source of truth)
# ---------------------------------------------------------------------------

class LedgerState(str, enum.Enum):
    """The 5 valid states of a ledger entry on disk.

    State transitions are unidirectional: raw → codified → resolved → archived
    (and codified → paired when a comparison_pair joins the entry).
    """

    RAW = "raw"
    CODIFIED = "codified"
    PAIRED = "paired"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class FixActionType(str, enum.Enum):
    """The 4 valid `fix_action_type` values for a codified ledger entry."""

    PROMPT_PATCH = "prompt_patch"
    INTENT_REVISION = "intent_revision"
    CAPABILITY_ADDITION = "capability_addition"
    DOMAIN_REASSESSMENT = "domain_reassessment"


class CapabilitySubtype(str, enum.Enum):
    """The 4 valid `capability_subtype` values when fix_action_type=capability_addition."""

    BUILD = "build"
    BUY = "buy"
    HIRE = "hire"
    PARTNER = "partner"


class DomainDepth(str, enum.Enum):
    """The 4 Expert Intuition depth tiers (judgment_layer.md §3.4)."""

    EXPERT = "expert"
    PRACTITIONER = "practitioner"
    ADJACENT = "adjacent"
    NOVICE = "novice"


class Freshness(str, enum.Enum):
    """The 4 freshness states for a pattern (judgment_layer.md §3.6)."""

    FRESH = "fresh"
    AGING = "aging"
    STALE = "stale"
    EXPIRED = "expired"


class InjectionStatus(str, enum.Enum):
    """The 3 valid `injection_status` values for a comparison_pair."""

    PLAUSIBLE = "plausible"
    CORROBORATED = "corroborated"
    REJECTED = "rejected"


# Domain-depth → confidence weight (canonical, judgment_layer.md §3.4).
# Single source of truth for both detection (engine) and validation.
DEPTH_WEIGHT: Dict[str, float] = {
    DomainDepth.EXPERT.value: 1.0,
    DomainDepth.PRACTITIONER.value: 0.7,
    DomainDepth.ADJACENT.value: 0.4,
    DomainDepth.NOVICE.value: 0.2,
}

# Required codified fields. Surfaced here so seeders, validators, and tests
# all import the same tuple.
REQUIRED_CODIFIED_FIELDS: tuple = (
    "expected_result",
    "detected_via",
    "diagnosed_cause",
    "proposed_fix",
    "fix_action_type",
)

# Default pattern half-life when a baseline does not specify one.
DEFAULT_HALF_LIFE_DAYS: int = 90

# Promotion threshold: number of ledger entries with same diagnosed_cause
# required before the cluster is promoted to a pattern file.
PATTERN_PROMOTION_THRESHOLD: int = 3

# Soft injection token budget (4 chars per token proxy).
DEFAULT_INJECT_TOKEN_BUDGET: int = 1500

# Engine version — stamped on every Pattern, Recommendation, and InjectionResult
# so callers can detect engine-behavior changes by hash comparison (R3 borrowed
# from Canon's AuditReport.engine_version pattern).
ENGINE_VERSION: str = "0.1.0"


# ---------------------------------------------------------------------------
# Helpers (used by dataclasses' to_yaml / from_yaml round-trips)
# ---------------------------------------------------------------------------

def _resolve_domain_depth(
    data: Dict[str, Any],
    default: Optional[str] = None,
) -> Optional[str]:
    """Read domain_depth; accept legacy on-disk key for backward compatibility."""
    val = data.get("domain_depth")
    if val is None:
        val = data.get("leo_domain_depth")
    if val is None:
        return default
    return val


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _stable_hash(payload: Dict[str, Any]) -> str:
    """Deterministic SHA-256 of a JSON-serialized payload (sorted keys)."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Sub-records
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class Classification:
    """The classification block on a ledger entry / comparison pair."""

    type: str = "regression"
    source: Optional[str] = None
    domain: Optional[str] = None
    agent: Optional[str] = None
    model: Optional[str] = None
    scope: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Classification":
        data = data or {}
        return cls(
            type=data.get("type", "regression"),
            source=data.get("source"),
            domain=data.get("domain"),
            agent=data.get("agent"),
            model=data.get("model"),
            scope=data.get("scope"),
        )


@dataclasses.dataclass
class CodifiedFields:
    """The 5 canonical codified fields plus the optional capability_subtype."""

    expected_result: str
    detected_via: str
    diagnosed_cause: str
    proposed_fix: str
    fix_action_type: str
    capability_subtype: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "expected_result": self.expected_result,
            "detected_via": self.detected_via,
            "diagnosed_cause": self.diagnosed_cause,
            "proposed_fix": self.proposed_fix,
            "fix_action_type": self.fix_action_type,
        }
        if self.capability_subtype is not None:
            d["capability_subtype"] = self.capability_subtype
        return d

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["CodifiedFields"]:
        if not data:
            return None
        return cls(
            expected_result=data.get("expected_result", ""),
            detected_via=data.get("detected_via", ""),
            diagnosed_cause=data.get("diagnosed_cause", ""),
            proposed_fix=data.get("proposed_fix", ""),
            fix_action_type=data.get("fix_action_type", ""),
            capability_subtype=data.get("capability_subtype"),
        )


@dataclasses.dataclass
class PatternMembership:
    pattern_id: str
    joined: str

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ChangelogEntry:
    date: str
    change: str

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Top-level artifacts
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class LedgerEntry:
    """A single ledger entry — the atomic unit of judgment capture.

    State machine: raw → codified → (paired | resolved) → archived.
    The on-disk filename is ``{state}/{id}.yaml`` under ``.judgment/ledger/``.
    """

    id: str
    created: str
    state: str
    classification: Classification
    raw_correction: str
    domain_depth: Optional[str] = None
    originated_from_tool: Optional[str] = None
    codified: Optional[CodifiedFields] = None
    pattern_membership: Optional[PatternMembership] = None
    resolution: Optional[Dict[str, Any]] = None
    changelog: List[ChangelogEntry] = dataclasses.field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created": self.created,
            "state": self.state,
            "classification": self.classification.to_dict(),
            "domain_depth": self.domain_depth,
            "originated_from_tool": self.originated_from_tool,
            "raw_correction": self.raw_correction,
            "codified": self.codified.to_dict() if self.codified else None,
            "pattern_membership": (
                self.pattern_membership.to_dict() if self.pattern_membership else None
            ),
            "resolution": self.resolution,
            "changelog": [c.to_dict() for c in self.changelog],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LedgerEntry":
        pm = data.get("pattern_membership")
        return cls(
            id=data.get("id", ""),
            created=data.get("created", _now_iso()),
            state=data.get("state", "raw"),
            classification=Classification.from_dict(data.get("classification")),
            raw_correction=data.get("raw_correction", ""),
            domain_depth=_resolve_domain_depth(data),
            originated_from_tool=data.get("originated_from_tool"),
            codified=CodifiedFields.from_dict(data.get("codified")),
            pattern_membership=(
                PatternMembership(
                    pattern_id=pm.get("pattern_id", ""),
                    joined=pm.get("joined", ""),
                )
                if isinstance(pm, dict) and pm.get("pattern_id")
                else None
            ),
            resolution=data.get("resolution"),
            changelog=[
                ChangelogEntry(date=c.get("date", ""), change=c.get("change", ""))
                for c in (data.get("changelog") or [])
                if isinstance(c, dict)
            ],
        )


@dataclasses.dataclass
class ComparisonPair:
    """A Pearl Rung-1 comparison pair — alternative to A/B testing.

    Each diagnostic_hypothesis MUST carry at least one ``competing_hypotheses``
    entry. That requirement is the structural mechanism keeping pairs honest at
    Rung 1 (association only).
    """

    id: str
    created: str
    state: str
    classification: Classification
    run_a: Dict[str, Any]
    run_b: Dict[str, Any]
    observed_differences: List[str]
    diagnostic_hypotheses: List[Dict[str, Any]]
    corroboration: Dict[str, Any] = dataclasses.field(
        default_factory=lambda: {"status": "single_pair", "supporting_pair_ids": []}
    )
    injection_status: str = InjectionStatus.PLAUSIBLE.value
    notes: Optional[str] = None
    changelog: List[ChangelogEntry] = dataclasses.field(default_factory=list)
    kind: str = "comparison_pair"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created": self.created,
            "state": self.state,
            "kind": self.kind,
            "classification": self.classification.to_dict(),
            "run_a": self.run_a,
            "run_b": self.run_b,
            "observed_differences": self.observed_differences,
            "diagnostic_hypotheses": self.diagnostic_hypotheses,
            "corroboration": self.corroboration,
            "injection_status": self.injection_status,
            "notes": self.notes,
            "changelog": [c.to_dict() for c in self.changelog],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComparisonPair":
        return cls(
            id=data.get("id", ""),
            created=data.get("created", _now_iso()),
            state=data.get("state", "paired"),
            kind=data.get("kind", "comparison_pair"),
            classification=Classification.from_dict(data.get("classification")),
            run_a=data.get("run_a") or {},
            run_b=data.get("run_b") or {},
            observed_differences=list(data.get("observed_differences") or []),
            diagnostic_hypotheses=list(data.get("diagnostic_hypotheses") or []),
            corroboration=data.get("corroboration")
            or {"status": "single_pair", "supporting_pair_ids": []},
            injection_status=data.get("injection_status", InjectionStatus.PLAUSIBLE.value),
            notes=data.get("notes"),
            changelog=[
                ChangelogEntry(date=c.get("date", ""), change=c.get("change", ""))
                for c in (data.get("changelog") or [])
                if isinstance(c, dict)
            ],
        )


@dataclasses.dataclass
class Pattern:
    """A distilled pattern (3+ ledger entries with the same diagnosed_cause).

    Stamped with ``engine_version`` and a reproducible ``detection_hash`` so
    callers can detect when the engine changed pattern shape underneath them
    (R3 borrowed from Canon's AuditReport.hash() pattern).
    """

    id: str
    created: str
    updated: str
    domain: str
    diagnosed_cause: str
    recommended_fix: str
    fix_action_type: str
    members: List[str]
    member_count: int
    weighted_confidence: float
    half_life_days: int
    last_member_added: Optional[str] = None
    freshness: str = Freshness.FRESH.value
    agent_class: Optional[str] = None
    scope: Dict[str, Any] = dataclasses.field(
        default_factory=lambda: {"systems": [], "models": [], "recipes": []}
    )
    depth_distribution: Dict[str, int] = dataclasses.field(default_factory=dict)
    tool_origin: Dict[str, Any] = dataclasses.field(default_factory=dict)
    status: str = "active"
    engine_version: str = ENGINE_VERSION
    detection_hash: Optional[str] = None

    # NB: detection_hash is computed from the *canonical* fields the engine
    # cares about — change any of them and the hash changes; change a cosmetic
    # field (status, updated, created) and it does not.
    def compute_hash(self) -> str:
        return _stable_hash({
            "id": self.id,
            "domain": self.domain,
            "diagnosed_cause": self.diagnosed_cause,
            "recommended_fix": self.recommended_fix,
            "fix_action_type": self.fix_action_type,
            "members": sorted(self.members),
            "member_count": self.member_count,
            "weighted_confidence": self.weighted_confidence,
            "depth_distribution": self.depth_distribution,
            "freshness": self.freshness,
            "engine_version": self.engine_version,
        })

    def stamp_hash(self) -> "Pattern":
        self.detection_hash = self.compute_hash()
        return self

    def to_dict(self) -> Dict[str, Any]:
        if self.detection_hash is None:
            self.stamp_hash()
        return {
            "id": self.id,
            "created": self.created,
            "updated": self.updated,
            "domain": self.domain,
            "agent_class": self.agent_class,
            "scope": self.scope,
            "diagnosed_cause": self.diagnosed_cause,
            "recommended_fix": self.recommended_fix,
            "fix_action_type": self.fix_action_type,
            "members": self.members,
            "member_count": self.member_count,
            "depth_distribution": self.depth_distribution,
            "weighted_confidence": self.weighted_confidence,
            "half_life_days": self.half_life_days,
            "last_member_added": self.last_member_added,
            "freshness": self.freshness,
            "tool_origin": self.tool_origin,
            "status": self.status,
            "engine_version": self.engine_version,
            "detection_hash": self.detection_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pattern":
        p = cls(
            id=data.get("id", ""),
            created=data.get("created", _now_iso()),
            updated=data.get("updated", _now_iso()),
            domain=data.get("domain", ""),
            diagnosed_cause=data.get("diagnosed_cause", ""),
            recommended_fix=data.get("recommended_fix", ""),
            fix_action_type=data.get("fix_action_type", ""),
            members=list(data.get("members") or []),
            member_count=int(data.get("member_count", 0)),
            weighted_confidence=float(data.get("weighted_confidence", 0.0)),
            half_life_days=int(data.get("half_life_days", DEFAULT_HALF_LIFE_DAYS)),
            last_member_added=data.get("last_member_added"),
            freshness=data.get("freshness", Freshness.FRESH.value),
            agent_class=data.get("agent_class"),
            scope=data.get("scope")
            or {"systems": [], "models": [], "recipes": []},
            depth_distribution=data.get("depth_distribution") or {},
            tool_origin=data.get("tool_origin") or {},
            status=data.get("status", "active"),
            engine_version=data.get("engine_version", ENGINE_VERSION),
            detection_hash=data.get("detection_hash"),
        )
        return p


@dataclasses.dataclass
class Baseline:
    """Per-domain baseline (created by ivd_judgment_init, edited by you)."""

    domain_id: str
    created: str
    updated: str
    domain_depth: str = DomainDepth.PRACTITIONER.value
    goal_calibration: Dict[str, Any] = dataclasses.field(
        default_factory=lambda: {"qualitative": "", "measurable": [], "out_of_scope": []}
    )
    risk_hypotheses: List[Any] = dataclasses.field(default_factory=list)
    pattern_half_life_policy: Dict[str, Any] = dataclasses.field(
        default_factory=lambda: {
            "half_life_days": DEFAULT_HALF_LIFE_DAYS,
            "rationale": "Default; tune once you have data",
        }
    )
    scale_awareness: Dict[str, Any] = dataclasses.field(
        default_factory=lambda: {"current_volume": "TODO", "next_threshold": "TODO"}
    )
    domain_reassessment_triggers: List[str] = dataclasses.field(default_factory=list)
    version: str = "0.1"
    changelog: List[ChangelogEntry] = dataclasses.field(default_factory=list)

    def half_life_days(self) -> int:
        pol = self.pattern_half_life_policy or {}
        days = pol.get("half_life_days") or pol.get("days") or DEFAULT_HALF_LIFE_DAYS
        try:
            return int(days)
        except (TypeError, ValueError):
            return DEFAULT_HALF_LIFE_DAYS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "created": self.created,
            "updated": self.updated,
            "version": self.version,
            "domain_depth": self.domain_depth,
            "goal_calibration": self.goal_calibration,
            "risk_hypotheses": self.risk_hypotheses,
            "pattern_half_life_policy": self.pattern_half_life_policy,
            "scale_awareness": self.scale_awareness,
            "domain_reassessment_triggers": self.domain_reassessment_triggers,
            "changelog": [c.to_dict() for c in self.changelog],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Baseline":
        return cls(
            domain_id=data.get("domain_id", ""),
            created=data.get("created", _now_iso()),
            updated=data.get("updated", _now_iso()),
            version=data.get("version", "0.1"),
            domain_depth=_resolve_domain_depth(
                data, default=DomainDepth.PRACTITIONER.value
            ),
            goal_calibration=data.get("goal_calibration")
            or {"qualitative": "", "measurable": [], "out_of_scope": []},
            risk_hypotheses=list(data.get("risk_hypotheses") or []),
            pattern_half_life_policy=data.get("pattern_half_life_policy")
            or {
                "half_life_days": DEFAULT_HALF_LIFE_DAYS,
                "rationale": "Default; tune once you have data",
            },
            scale_awareness=data.get("scale_awareness")
            or {"current_volume": "TODO", "next_threshold": "TODO"},
            domain_reassessment_triggers=list(
                data.get("domain_reassessment_triggers") or []
            ),
            changelog=[
                ChangelogEntry(date=c.get("date", ""), change=c.get("change", ""))
                for c in (data.get("changelog") or [])
                if isinstance(c, dict)
            ],
        )


@dataclasses.dataclass
class Recommendation:
    """A draft recommendation derived from a detected Pattern, awaiting you."""

    id: str
    created: str
    state: str
    source_pattern: str
    pattern_summary: Dict[str, Any]
    fix_action_type: str
    capability_subtype: Optional[str] = None
    draft_recipe_yaml: Optional[str] = None
    approval: Dict[str, Any] = dataclasses.field(
        default_factory=lambda: {
            "status": "pending_user",
            "approved_by": None,
            "approved_at": None,
        }
    )
    notes: Optional[str] = None
    next_actions: List[str] = dataclasses.field(default_factory=list)
    engine_version: str = ENGINE_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recommendation":
        return cls(
            id=data.get("id", ""),
            created=data.get("created", _now_iso()),
            state=data.get("state", "draft"),
            source_pattern=data.get("source_pattern", ""),
            pattern_summary=data.get("pattern_summary") or {},
            fix_action_type=data.get("fix_action_type", ""),
            capability_subtype=data.get("capability_subtype"),
            draft_recipe_yaml=data.get("draft_recipe_yaml"),
            approval=data.get("approval")
            or {"status": "pending_user", "approved_by": None, "approved_at": None},
            notes=data.get("notes"),
            next_actions=list(data.get("next_actions") or []),
            engine_version=data.get("engine_version", ENGINE_VERSION),
        )


@dataclasses.dataclass
class InjectionResult:
    """The payload returned by the inject layer.

    Stamped with ``engine_version`` and a reproducible ``injection_hash`` so
    callers can detect when the same input would have produced a different
    rendering — useful when diffing context across runs.
    """

    domain_filter: Optional[str]
    task_type: Optional[str]
    token_budget: int
    approx_tokens: int
    truncated: bool
    context: Dict[str, List[Dict[str, Any]]]
    engine_version: str = ENGINE_VERSION
    injection_hash: Optional[str] = None

    def compute_hash(self) -> str:
        return _stable_hash({
            "domain_filter": self.domain_filter,
            "context": self.context,
            "engine_version": self.engine_version,
        })

    def stamp_hash(self) -> "InjectionResult":
        self.injection_hash = self.compute_hash()
        return self

    def to_dict(self) -> Dict[str, Any]:
        if self.injection_hash is None:
            self.stamp_hash()
        return {
            "domain_filter": self.domain_filter,
            "task_type": self.task_type,
            "token_budget": self.token_budget,
            "approx_tokens": self.approx_tokens,
            "truncated": self.truncated,
            "context": self.context,
            "engine_version": self.engine_version,
            "injection_hash": self.injection_hash,
        }
