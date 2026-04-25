# ivd/canon/audit.py

"""
Canon Audit layer — checks a CanonDocument against the R-invariants.

Engine v0.1.0 shipped R1, R2, R5, R10, R14 as enforced.
Engine v0.2.0 promotes R13 (stakes-adaptive format) to enforced via a
Tier 1 structural-density heuristic; the remaining 8 partial rules are
either architecturally out-of-scope for a single-turn deterministic audit
(R8/R11 need session state) or carry false-positive risk that exceeds
their value at Tier 1 (R3/R4/R6/R7/R12). They remain instructed via the
Phase 0a rules block.

The audit is deterministic, and its hash is reproducible across runs so
callers can compare verdicts (R9).

Reference: canon_layer.md §Audit layer (R-invariant enforcement), §Audit diff.
"""

from __future__ import annotations

import re
from typing import List

from canon.contract import (
    AuditDiff,
    AuditReport,
    CanonDocument,
    RFinding,
    Stakes,
)

# R2 — explicit confidence-marker shapes. An R2 "pass" requires one of these
# to appear in the body. Bare English words like "verified" / "inferred" /
# "assumed" are INSUFFICIENT — the rule is about Canon markers, not English.
# Two shape families:
#   Rules-block shape (what Phase 0a teaches agents to type):
#       ✓ verified   ~ inferred   ? assumed
#   Renderer shape (what ivd/canon/render.py emits as glyph tags):
#       ● verified   ◐ inferred   ○ assumed   (also wrapped in parens)
# The regex accepts either shape, case-insensitive on the English word.
_R2_MARKER_RE = re.compile(
    r"(?:[✓●]|[~◐]|[?○])\s*(?:verified|inferred|assumed)\b",
    re.IGNORECASE,
)

# Patterns that should never appear in a CanonDocument (safety-critical).
# Aligned with PRD §3 conscious exclusions.
_FORBIDDEN_PATTERNS = [
    (re.compile(r"\bonly\s+\d+\s+(left|spots|seats|remaining)\b", re.I), "manufactured-scarcity"),
    (re.compile(r"\b(act now|don't miss out|limited time only|hurry)\b", re.I), "urgency-manipulation"),
    (re.compile(r"\bbecause you('ve| have)? always trusted\b", re.I), "loyalty-pressure"),
    (re.compile(r"\bI('m| am) sentient\b", re.I), "anthropomorphism-violation"),
    (re.compile(r"\bI feel (sad|happy|angry|upset|excited)\b", re.I), "emotion-claim"),
    (re.compile(r"\bI('m| am) your (friend|companion|family)\b", re.I), "persona-overclaim"),
]

# R13 — stakes-adaptive format. Tier 1 enforces a *structural-density* mismatch
# heuristic, not the full PRD §5.3.5 example-vs-rule mapping table (which
# requires deeper semantic analysis than Tier 1 can do deterministically).
#
# The heuristic catches the two highest-signal failure modes:
#   1. LOW stakes + heavy structure (multi-section answer to a chitchat Q)
#   2. HIGH/IRREVERSIBLE stakes + flat unstructured prose (no headers/lists)
#
# MEDIUM stakes is the relaxed band — never fails R13 by design.
# Domain-pack-specific mapping enforcement is Phase 2 work (see canon_system_intent
# constraint R13_format_selection).
_R13_LOW_STAKES_VERBOSE_WORDS = 200
_R13_HIGH_STAKES_TERSE_WORDS = 50

# Outline-level structural markers: markdown headers (##+), bullet/numbered
# lists, or pipe-table separators. Single-line code fences and inline code
# do NOT count — they are content, not outline structure.
_R13_STRUCTURE_RE = re.compile(
    r"(?m)^(?:\s{0,3})(?:#{2,}\s|[-*+]\s|\d+\.\s|\|.*\|)",
)


def _add(findings: List[RFinding], r: str, status: str, severity: str, detail: str) -> None:
    findings.append(RFinding(r=r, status=status, severity=severity, detail=detail))


def _audit_R1_setting(doc: CanonDocument, findings: List[RFinding]) -> None:
    if doc.setting_phase and len(doc.setting_phase.strip()) >= 8:
        _add(findings, "R1", "pass", "info", "Setting phase present.")
    else:
        _add(findings, "R1", "fail", "warn", "Missing or empty setting phase.")


def _audit_R2_confidence(doc: CanonDocument, findings: List[RFinding]) -> None:
    """R2 pass requires at least one Canon marker shape in the body.

    The rule is deliberately strict: a bare English word like 'verified' is not
    a Canon mark; only the glyph-prefixed forms (✓/●/~/◐/?/○ + verified /
    inferred / assumed) count. This keeps R2 a structural check, not a
    language check.
    """
    count = len(_R2_MARKER_RE.findall(doc.body_with_marks))
    if count > 0:
        _add(findings, "R2", "pass", "info", f"{count} confidence mark(s) present in body.")
    else:
        _add(
            findings,
            "R2",
            "partial",
            "warn",
            "No Canon confidence markers found (expected one of: ✓/● verified, ~/◐ inferred, ?/○ assumed). "
            "Tier 1 inference is conservative; agents following the Phase 0a Canon Rules block will emit these markers.",
        )


def _audit_R5_verification(doc: CanonDocument, findings: List[RFinding]) -> None:
    has_beats = bool(doc.verification_beats)
    irreversible = doc.stakes in (Stakes.HIGH, Stakes.IRREVERSIBLE)
    if irreversible and not has_beats:
        _add(
            findings,
            "R5",
            "fail",
            "safety_fail",
            "High/irreversible stakes but no verification beats emitted.",
        )
    elif has_beats:
        _add(findings, "R5", "pass", "info", f"{len(doc.verification_beats)} verification beat(s) emitted.")
    else:
        _add(findings, "R5", "pass", "info", "No verification beat needed at this stakes level.")


def _audit_R10_folk_theory(doc: CanonDocument, findings: List[RFinding]) -> None:
    triggers = ("the ai understands", "the ai knows", "the ai feels", "the ai thinks", "the ai wants", "the ai believes", "the ai remembers")
    body_lower = doc.body_with_marks.lower()
    triggered = [t for t in triggers if t in body_lower]
    if triggered and not doc.folk_theory_notes:
        _add(
            findings,
            "R10",
            "fail",
            "warn",
            f"Folk-theory trigger(s) {triggered} present but no correcting note.",
        )
    elif triggered:
        _add(findings, "R10", "pass", "info", f"Folk-theory triggers acknowledged via note(s).")
    else:
        _add(findings, "R10", "pass", "info", "No folk-theory triggers detected.")


def _audit_R14_identity(doc: CanonDocument, findings: List[RFinding]) -> None:
    """R14 anthropomorphism ceiling — identity must be present and bounded."""
    body = doc.body_with_marks.lower()
    flagged: List[str] = []
    for pattern, label in _FORBIDDEN_PATTERNS:
        if pattern.search(body):
            flagged.append(label)
    if flagged:
        _add(
            findings,
            "R14",
            "fail",
            "safety_fail",
            f"Forbidden pattern(s) in body: {flagged}",
        )
        return
    if not doc.identity_statement.strip():
        _add(findings, "R14", "fail", "warn", "Missing identity statement.")
        return
    _add(findings, "R14", "pass", "info", "Identity bounded; no forbidden patterns found.")


def _audit_R13_stakes_format(doc: CanonDocument, findings: List[RFinding]) -> None:
    """R13 stakes-adaptive format — Tier 1 structural-density heuristic.

    Enforces only the structural-density slice of the full PRD §5.3.5 mapping
    (the example-vs-rule axis requires semantic analysis beyond Tier 1). The
    detector catches:
      - LOW stakes + verbose multi-section reply (format too heavy for stakes)
      - HIGH/IRREVERSIBLE stakes + flat unstructured prose (format too light)

    MEDIUM stakes is the relaxed band — passes by design.
    """
    body = doc.body_with_marks or ""
    word_count = len(body.split())
    has_structure = bool(_R13_STRUCTURE_RE.search(body))

    if doc.stakes == Stakes.LOW:
        if word_count > _R13_LOW_STAKES_VERBOSE_WORDS and has_structure:
            _add(
                findings,
                "R13",
                "fail",
                "warn",
                f"Format too heavy for low stakes: {word_count} words with outline structure "
                f"(threshold: <={_R13_LOW_STAKES_VERBOSE_WORDS} words at low stakes).",
            )
            return
        _add(findings, "R13", "pass", "info", f"Format matches low stakes ({word_count} words).")
        return

    if doc.stakes in (Stakes.HIGH, Stakes.IRREVERSIBLE):
        # High/irreversible answers should be either structured OR explicitly
        # short-and-sufficient. A short flat prose answer at irreversible stakes
        # is the failure mode (e.g., "yes, delete it" with no breakdown).
        if word_count >= _R13_HIGH_STAKES_TERSE_WORDS and not has_structure:
            _add(
                findings,
                "R13",
                "fail",
                "warn",
                f"Format too light for {doc.stakes.value} stakes: {word_count} words of flat prose, "
                "no outline structure (headers/lists/tables expected).",
            )
            return
        if word_count < _R13_HIGH_STAKES_TERSE_WORDS and not has_structure:
            _add(
                findings,
                "R13",
                "fail",
                "warn",
                f"Format too light for {doc.stakes.value} stakes: {word_count} words, no structure. "
                "High-stakes responses need either structural markers or substantive depth.",
            )
            return
        _add(
            findings,
            "R13",
            "pass",
            "info",
            f"Format matches {doc.stakes.value} stakes (structured={has_structure}, words={word_count}).",
        )
        return

    # MEDIUM (or any future stakes value) — relaxed band.
    _add(findings, "R13", "pass", "info", "Medium stakes — format band is relaxed.")


def _audit_partial_stubs(findings: List[RFinding]) -> None:
    """The R-invariants not yet enforced in Phase 0b.

    R13 was promoted to enforced in engine v0.2.0 (Tier 1 structural-density
    heuristic). The remaining 8 partial rules are either (a) architecturally
    out-of-scope for a single-turn deterministic audit (R8/R11 need session
    state) or (b) carry false-positive risk that exceeds their value at Tier 1
    (R3/R4/R6/R7/R12). They remain instructed via the Phase 0a rules block.
    """
    for r, why in [
        ("R3",  "working-memory chunking not yet enforced"),
        ("R4",  "dual-encoding (tables / examples) not yet enforced"),
        ("R6",  "loss-frame calibration not yet enforced"),
        ("R7",  "B+I signal injection not yet enforced"),
        ("R8",  "identity preservation across multi-turn not yet enforced"),
        ("R9",  "audit reproducibility check not yet enforced (hash present)"),
        ("R11", "first-output priority not yet enforced"),
        ("R12", "arousal calibration not yet enforced"),
    ]:
        _add(findings, r, "partial", "info", why)


def audit(doc: CanonDocument) -> AuditReport:
    """Run the full audit on a CanonDocument and return an AuditReport."""
    findings: List[RFinding] = []
    _audit_R1_setting(doc, findings)
    _audit_R2_confidence(doc, findings)
    _audit_R5_verification(doc, findings)
    _audit_R10_folk_theory(doc, findings)
    _audit_R13_stakes_format(doc, findings)
    _audit_R14_identity(doc, findings)
    _audit_partial_stubs(findings)

    # Overall verdict.
    overall = "pass"
    if any(f.severity == "safety_fail" for f in findings):
        overall = "safety_fail"
    elif any(f.status == "fail" for f in findings):
        overall = "fail"
    elif any(f.status == "partial" for f in findings):
        overall = "partial"

    return AuditReport(
        findings=findings,
        overall=overall,
        partial=any(f.status == "partial" for f in findings),
        stakes=doc.stakes,
        domain_pack=doc.domain_pack,
        engine_version="0.2.0",
    )


def diff_audit(before: AuditReport, after: AuditReport) -> AuditDiff:
    """Compare two audit reports — for canon_diff."""
    before_status = {f.r: f.status for f in before.findings}
    after_status = {f.r: f.status for f in after.findings}
    fixed: List[str] = []
    regressed: List[str] = []
    unchanged: List[str] = []
    for r in sorted(set(before_status) | set(after_status)):
        b = before_status.get(r, "missing")
        a = after_status.get(r, "missing")
        if b == a:
            unchanged.append(r)
        elif b in ("fail", "safety_fail", "partial") and a == "pass":
            fixed.append(r)
        elif b == "pass" and a in ("fail", "safety_fail", "partial"):
            regressed.append(r)
        else:
            unchanged.append(r)
    return AuditDiff(
        before_hash=before.hash(),
        after_hash=after.hash(),
        fixed=fixed,
        regressed=regressed,
        unchanged=unchanged,
    )
