# ivd/judgment/__init__.py

"""
Judgment engine — Phase 4 of IVD (v3.0+).

Vendored inside the IVD repo at ``ivd/judgment/``. Reused across:
  - mcp_server/tools/judgment.py — the 9 ivd_judgment_* MCP tools
  - mcp_server/tools/validate.py — judgment artifact validation
  - mcp_server/tests/unit/test_judgment.py — unit tests
  - downstream callers that want to operate on .judgment/ folders directly

Source-of-truth chain:
  ivd/judgment_layer.md                                (canonical spec)
  ivd/_private/research/judgment_layer_integration_spec.md
  ivd/ivd_system_intent.yaml                           (system intent v3.1)

Architectural note:
  This package mirrors the structure of ``ivd/canon/`` (the Canon engine
  added in v3.1). Both are vendored engine packages with a thin MCP-tool
  facade in ``mcp_server/tools/``. Both stamp engine_version + reproducible
  hashes on their primary outputs (Canon: AuditReport.hash; Judgment:
  Pattern.detection_hash, InjectionResult.injection_hash).
"""

from judgment.detect import detect_patterns
from judgment.freshness import age_days, freshness_for
from judgment.inject import inject_context
from judgment.schema import (
    DEFAULT_HALF_LIFE_DAYS,
    DEFAULT_INJECT_TOKEN_BUDGET,
    DEPTH_WEIGHT,
    ENGINE_VERSION,
    PATTERN_PROMOTION_THRESHOLD,
    REQUIRED_CODIFIED_FIELDS,
    Baseline,
    CapabilitySubtype,
    Classification,
    CodifiedFields,
    ComparisonPair,
    DomainDepth,
    FixActionType,
    Freshness,
    InjectionResult,
    InjectionStatus,
    LedgerEntry,
    LedgerState,
    Pattern,
    PatternMembership,
    Recommendation,
)
from judgment.store import (
    JUDGMENT_DIRNAME,
    JUDGMENT_SUBDIRS,
    LEDGER_STATES,
    JudgmentStore,
    read_yaml,
    slugify,
    write_yaml,
)
from judgment.validate import (
    FRESHNESS_STATES,
    VALID_CAPABILITY_SUBTYPES,
    VALID_FIX_ACTION_TYPES,
    VALIDATORS,
    validate_baseline,
    validate_comparison_pair,
    validate_ledger_entry,
    validate_pattern,
)

__all__ = [
    # constants
    "DEFAULT_HALF_LIFE_DAYS",
    "DEFAULT_INJECT_TOKEN_BUDGET",
    "DEPTH_WEIGHT",
    "ENGINE_VERSION",
    "PATTERN_PROMOTION_THRESHOLD",
    "REQUIRED_CODIFIED_FIELDS",
    "FRESHNESS_STATES",
    "VALID_CAPABILITY_SUBTYPES",
    "VALID_FIX_ACTION_TYPES",
    "JUDGMENT_DIRNAME",
    "JUDGMENT_SUBDIRS",
    "LEDGER_STATES",
    # enums
    "CapabilitySubtype",
    "DomainDepth",
    "FixActionType",
    "Freshness",
    "InjectionStatus",
    "LedgerState",
    # dataclasses
    "Baseline",
    "Classification",
    "CodifiedFields",
    "ComparisonPair",
    "InjectionResult",
    "LedgerEntry",
    "Pattern",
    "PatternMembership",
    "Recommendation",
    # store
    "JudgmentStore",
    "read_yaml",
    "write_yaml",
    "slugify",
    # detect / inject
    "detect_patterns",
    "inject_context",
    # freshness
    "age_days",
    "freshness_for",
    # validators
    "VALIDATORS",
    "validate_baseline",
    "validate_comparison_pair",
    "validate_ledger_entry",
    "validate_pattern",
]

__version__ = ENGINE_VERSION
