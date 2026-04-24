# ivd/canon/__init__.py

"""
Canon engine — Human Translation Layer for AI output.

Vendored inside the IVD repo at ivd/canon/. Reused across:
  - Phase 0b: Canon MCP tools hosted inside the IVD MCP server
              (canon_render, canon_check, canon_diff)
  - Phase 0c: Canon Dots browser extension (separate repo, imports same code)
  - Phase 2:  Canon SDK (JavaScript/TypeScript and Python) and HTTP API proxy
  - Phase 3:  Enterprise / Canon Protocol Tier 3

Canonical public spec: ivd/canon_layer.md (engine §5, MCP host §9B).

This first cut is deterministic (Tier 1 inference, no LLM call) and stateless;
LLM-augmented Tier 2 paths arrive in a follow-up that is gated behind
IVD_CANON_LLM_PROVIDER. R1, R2, R5, R10, R14 are implemented; R3, R4, R6, R7,
R8, R9, R11, R12, R13 are stubbed and surfaced in AuditReport.partial=True
until they land.
"""

from canon.contract import (
    CanonContract,
    CanonDocument,
    AuditReport,
    AuditDiff,
    Stakes,
    Tier,
)
from canon.infer import infer
from canon.render import render
from canon.audit import audit, diff_audit

__all__ = [
    "CanonContract",
    "CanonDocument",
    "AuditReport",
    "AuditDiff",
    "Stakes",
    "Tier",
    "infer",
    "render",
    "audit",
    "diff_audit",
]

__version__ = "0.1.0"
