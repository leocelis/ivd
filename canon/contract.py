# ivd/canon/contract.py

"""
Canon Contract — the central intermediate representation.

Tier 1 callers pass raw text; the inferrer derives a CanonContract from it.
Tier 2 callers pass a CanonContract directly. The renderer always operates on
a CanonContract; the audit always operates on a rendered CanonDocument.

Reference: canon_layer.md §Contract schema, §CanonDocument schema, §AuditReport schema.
This module is the dataclass projection of those schemas.
"""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
from typing import Any, Dict, List, Optional


class Stakes(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    IRREVERSIBLE = "irreversible"


class Tier(int, enum.Enum):
    """Canon tier — see PRD v0.7 §10 for the three-tier compatibility model."""

    INFER = 1   # Tier 1: infer Contract from raw text (deterministic, no LLM)
    CONTRACT = 2  # Tier 2: caller supplies Contract
    PROTOCOL = 3  # Tier 3: vendor-native protocol


@dataclasses.dataclass
class ConfidenceMark:
    """One R2 confidence-tier mark on a load-bearing claim."""

    claim: str
    tier: str  # "verified" | "inferred" | "assumed"
    evidence: Optional[str] = None


@dataclasses.dataclass
class DecisionPoint:
    """An R5 decision point: an action that may need a verification beat."""

    action: str
    stakes: Stakes
    reversible: bool
    smallest_undo: Optional[str] = None


@dataclasses.dataclass
class CanonContract:
    """The intermediate representation between raw AI output and CanonDocument.

    Tier 1: produced by canon.infer.infer(text).
    Tier 2: supplied directly by the caller.
    """

    setting: str = ""  # R1: one-sentence framing
    body: str = ""  # the substantive content
    confidence_marks: List[ConfidenceMark] = dataclasses.field(default_factory=list)  # R2
    decision_points: List[DecisionPoint] = dataclasses.field(default_factory=list)  # R5
    folk_theory_corrections: List[str] = dataclasses.field(default_factory=list)  # R10
    identity_statement: str = "I am an AI assistant."  # R14
    domain_pack: str = "general"
    stakes: Stakes = Stakes.MEDIUM

    def to_json(self) -> Dict[str, Any]:
        return {
            "setting": self.setting,
            "body": self.body,
            "confidence_marks": [dataclasses.asdict(m) for m in self.confidence_marks],
            "decision_points": [
                {**dataclasses.asdict(d), "stakes": d.stakes.value} for d in self.decision_points
            ],
            "folk_theory_corrections": self.folk_theory_corrections,
            "identity_statement": self.identity_statement,
            "domain_pack": self.domain_pack,
            "stakes": self.stakes.value,
        }


@dataclasses.dataclass
class CanonDocument:
    """The rendered, human-legible output of the Canon pipeline."""

    setting_phase: str  # R1
    body_with_marks: str  # R2 markers inline
    verification_beats: List[Dict[str, str]] = dataclasses.field(default_factory=list)  # R5
    folk_theory_notes: List[str] = dataclasses.field(default_factory=list)  # R10
    identity_statement: str = ""  # R14
    raw_input: str = ""  # always recoverable per ethics
    domain_pack: str = "general"
    stakes: Stakes = Stakes.MEDIUM

    def to_json(self) -> Dict[str, Any]:
        return {
            "setting_phase": self.setting_phase,
            "body_with_marks": self.body_with_marks,
            "verification_beats": self.verification_beats,
            "folk_theory_notes": self.folk_theory_notes,
            "identity_statement": self.identity_statement,
            "raw_input": self.raw_input,
            "domain_pack": self.domain_pack,
            "stakes": self.stakes.value,
        }

    def to_markdown(self) -> str:
        """Render the document to user-facing markdown (deterministic)."""
        out: List[str] = []
        if self.setting_phase:
            out.append(self.setting_phase.strip())
            out.append("")
        if self.identity_statement:
            out.append(f"_{self.identity_statement.strip()}_")
            out.append("")
        if self.folk_theory_notes:
            for note in self.folk_theory_notes:
                out.append(f"> Note: {note}")
            out.append("")
        out.append(self.body_with_marks.strip())
        if self.verification_beats:
            out.append("")
            out.append("---")
            for beat in self.verification_beats:
                out.append("")
                out.append(f"**ACTION:**     {beat.get('action', '')}")
                out.append(f"**REVERSIBLE:** {beat.get('reversible', '')}")
                out.append(f"**APPROVE?**    {beat.get('approve_prompt', 'reply YES to proceed')}")
        return "\n".join(out).rstrip() + "\n"


@dataclasses.dataclass
class RFinding:
    """One R-invariant audit finding."""

    r: str  # "R1" | "R2" | ...
    status: str  # "pass" | "fail" | "partial" | "skipped"
    severity: str = "info"  # "info" | "warn" | "fail" | "safety_fail"
    detail: str = ""


@dataclasses.dataclass
class AuditReport:
    """The verdict on a CanonDocument — see canon_layer.md §Audit."""

    findings: List[RFinding] = dataclasses.field(default_factory=list)
    overall: str = "pass"  # "pass" | "fail" | "safety_fail" | "partial"
    partial: bool = False  # True when not all R1–R14 are implemented yet
    stakes: Stakes = Stakes.MEDIUM
    domain_pack: str = "general"
    engine_version: str = "0.1.0"

    def _payload(self) -> Dict[str, Any]:
        """Hash-input payload (does NOT include the hash field — avoids recursion)."""
        return {
            "findings": [dataclasses.asdict(f) for f in self.findings],
            "overall": self.overall,
            "partial": self.partial,
            "stakes": self.stakes.value,
            "domain_pack": self.domain_pack,
            "engine_version": self.engine_version,
        }

    def hash(self) -> str:
        """Reproducible hash for R9 (audit reproducibility)."""
        payload = json.dumps(self._payload(), sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_json(self) -> Dict[str, Any]:
        out = self._payload()
        out["hash"] = self.hash() if self.findings else None
        return out


@dataclasses.dataclass
class AuditDiff:
    """Diff between two AuditReports — see canon_layer.md §Audit diff."""

    before_hash: str
    after_hash: str
    fixed: List[str] = dataclasses.field(default_factory=list)
    regressed: List[str] = dataclasses.field(default_factory=list)
    unchanged: List[str] = dataclasses.field(default_factory=list)

    def to_json(self) -> Dict[str, Any]:
        return {
            "before_hash": self.before_hash,
            "after_hash": self.after_hash,
            "fixed": self.fixed,
            "regressed": self.regressed,
            "unchanged": self.unchanged,
            "verdict": (
                "improved" if self.fixed and not self.regressed
                else "regressed" if self.regressed and not self.fixed
                else "mixed" if (self.fixed and self.regressed)
                else "unchanged"
            ),
        }
