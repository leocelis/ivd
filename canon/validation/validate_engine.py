#!/usr/bin/env python3
"""
canon/validation/validate_engine.py  — Option A: Canon Engine Validation

Runs the full infer → render → audit pipeline against a fixture corpus and
writes human-readable + machine-readable results to results/.

No API key required. Fully deterministic. Run from the ivd/ directory:

    cd /path/to/ivd
    python -m canon.validation.validate_engine

Output:
    canon/validation/results/engine_<fixture_id>.json   — per-fixture full output
    canon/validation/results/engine_report.txt          — human-readable summary
    canon/validation/results/engine_report.json         — machine-readable summary
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Bootstrap: make sure we're running from the ivd/ root
# ---------------------------------------------------------------------------
THIS_DIR = Path(__file__).parent
IVD_ROOT = THIS_DIR.parent.parent   # ivd/canon/validation/../../  = ivd/
RESULTS_DIR = THIS_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

if str(IVD_ROOT) not in sys.path:
    sys.path.insert(0, str(IVD_ROOT))

from canon import infer, render, audit                     # noqa: E402
from canon.validation.fixtures import FIXTURES             # noqa: E402

# ---------------------------------------------------------------------------
# ANSI colours (degrade gracefully when redirected)
# ---------------------------------------------------------------------------
GREEN  = "\033[32m" if sys.stdout.isatty() else ""
RED    = "\033[31m" if sys.stdout.isatty() else ""
YELLOW = "\033[33m" if sys.stdout.isatty() else ""
CYAN   = "\033[36m" if sys.stdout.isatty() else ""
BOLD   = "\033[1m"  if sys.stdout.isatty() else ""
RESET  = "\033[0m"  if sys.stdout.isatty() else ""

PASS = f"{GREEN}PASS{RESET}"
FAIL = f"{RED}FAIL{RESET}"
WARN = f"{YELLOW}WARN{RESET}"


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

def check_R1(document) -> Dict[str, Any]:
    """Setting phase must be non-empty in the rendered document."""
    present = bool(document.setting_phase and document.setting_phase.strip())
    return {"label": "R1 Setting Phase present", "result": "pass" if present else "fail",
            "detail": document.setting_phase[:80] if present else "setting_phase is empty"}


def check_R2_glyph(document, report) -> Dict[str, Any]:
    """R2 audit must be 'pass' (glyphs present) or 'partial' (no glyphs in source)."""
    r2 = next((f for f in report.findings if f.r == "R2"), None)
    if r2 is None:
        return {"label": "R2 Confidence markers", "result": "skip", "detail": "R2 finding missing"}
    has_glyph = r2.status == "pass"
    return {
        "label": "R2 Confidence markers",
        "result": r2.status,
        "detail": r2.detail,
        "has_glyph": has_glyph,
    }


def check_R5_beat(document) -> Dict[str, Any]:
    """R5 verification beat must be emitted when action is irreversible."""
    beats = document.verification_beats or []
    emitted = len(beats) > 0
    detail = beats[0] if beats else "no beats emitted"
    return {"label": "R5 Verification beat", "result": "pass" if emitted else "none",
            "detail": str(detail)[:120], "beats": len(beats)}


def check_R14_identity(document) -> Dict[str, Any]:
    """R14 identity statement must be present in the rendered output."""
    present = bool(document.identity_statement and document.identity_statement.strip())
    return {"label": "R14 Identity statement", "result": "pass" if present else "fail",
            "detail": document.identity_statement if present else "identity_statement is empty"}


# ---------------------------------------------------------------------------
# Run one fixture
# ---------------------------------------------------------------------------

def run_fixture(fx: Dict[str, Any]) -> Dict[str, Any]:
    text   = fx["text"]
    stakes = fx.get("stakes", "medium")
    expect = fx.get("expect", {})

    t0 = time.perf_counter()
    contract = infer(text, stakes=stakes)
    document = render(contract)
    report   = audit(document)
    elapsed  = (time.perf_counter() - t0) * 1000

    checks = {
        "R1": check_R1(document),
        "R2": check_R2_glyph(document, report),
        "R5": check_R5_beat(document),
        "R14": check_R14_identity(document),
    }

    # Expectation assertions
    assertions: List[Dict[str, Any]] = []
    exp_map = {
        "R1_setting_present":  ("R1",  lambda c: c["result"] == "pass"),
        "R2_has_glyph":        ("R2",  lambda c: c.get("has_glyph", False)),
        "R5_beat_emitted":     ("R5",  lambda c: c["beats"] > 0),
        "R14_identity_present":("R14", lambda c: c["result"] == "pass"),
    }
    all_ok = True
    for key, (r, predicate) in exp_map.items():
        if key not in expect:
            continue
        expected_val = expect[key]
        actual_val   = predicate(checks[r])
        ok = (actual_val == expected_val)
        if not ok:
            all_ok = False
        assertions.append({
            "key":     key,
            "expected": expected_val,
            "actual":   actual_val,
            "ok":       ok,
        })

    full_output = {
        "fixture_id":    fx["id"],
        "label":         fx["label"],
        "stakes":        stakes,
        "elapsed_ms":    round(elapsed, 3),
        "audit_overall": report.overall,
        "audit_partial": report.partial,
        "audit_hash":    report.hash,
        "checks":        checks,
        "assertions":    assertions,
        "all_assertions_ok": all_ok,
        "rendered": {
            "setting_phase":        document.setting_phase,
            "body_with_marks":      document.body_with_marks,
            "verification_beats":   document.verification_beats,
            "folk_theory_notes":    document.folk_theory_notes,
            "identity_statement":   document.identity_statement,
        },
        "markdown": document.to_markdown(),
        "audit_findings": [
            {"r": f.r, "status": f.status, "detail": f.detail}
            for f in report.findings
        ],
    }

    # Save per-fixture JSON
    out_path = RESULTS_DIR / f"engine_{fx['id']}.json"
    with out_path.open("w") as fh:
        json.dump(full_output, fh, indent=2, default=str)

    return full_output


# ---------------------------------------------------------------------------
# Pretty-print one result
# ---------------------------------------------------------------------------

def print_fixture_result(r: Dict[str, Any]) -> None:
    status = f"{GREEN}✓{RESET}" if r["all_assertions_ok"] else f"{RED}✗{RESET}"
    print(f"\n{BOLD}[{r['fixture_id']}]{RESET}  {status}  {r['label']}")
    print(f"  stakes={r['stakes']}  elapsed={r['elapsed_ms']:.2f} ms  "
          f"audit={r['audit_overall']}  partial={r['audit_partial']}")

    print(f"\n  {BOLD}Rendered markdown:{RESET}")
    for line in r["markdown"].splitlines():
        print(f"    {line}")

    print(f"\n  {BOLD}Checks:{RESET}")
    for name, c in r["checks"].items():
        sym = GREEN + "✓" + RESET if c["result"] == "pass" else (
              YELLOW + "~" + RESET if c["result"] in ("partial", "none") else
              RED + "✗" + RESET)
        print(f"    {sym} {c['label']:35}  {c['result']:8}  {str(c.get('detail',''))[:70]}")

    if r["assertions"]:
        print(f"\n  {BOLD}Assertions:{RESET}")
        for a in r["assertions"]:
            sym = GREEN + "✓" + RESET if a["ok"] else RED + "✗" + RESET
            print(f"    {sym} {a['key']:35}  expected={str(a['expected']):5}  actual={str(a['actual'])}")

    print(f"\n  {BOLD}Audit findings:{RESET}")
    for f in r["audit_findings"]:
        col = GREEN if f["status"] == "pass" else (YELLOW if f["status"] == "partial" else RED)
        print(f"    {col}{f['r']:5}{RESET}  {f['status']:8}  {f['detail'][:80]}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"\n{BOLD}{'='*72}{RESET}")
    print(f"{BOLD}  Canon Engine Validation  —  Option A{RESET}")
    print(f"  Fixtures: {len(FIXTURES)}  |  Results: {RESULTS_DIR}")
    print(f"{BOLD}{'='*72}{RESET}")

    results = []
    for fx in FIXTURES:
        result = run_fixture(fx)
        results.append(result)
        print_fixture_result(result)

    # Aggregate summary
    total      = len(results)
    ok_count   = sum(1 for r in results if r["all_assertions_ok"])
    fail_count = total - ok_count
    total_ms   = sum(r["elapsed_ms"] for r in results)

    print(f"\n{BOLD}{'='*72}{RESET}")
    print(f"{BOLD}  Summary{RESET}")
    print(f"{'='*72}")
    print(f"  Fixtures run       : {total}")
    print(f"  Assertions OK      : {GREEN}{ok_count}{RESET} / {total}")
    print(f"  Failures           : {(RED + str(fail_count) + RESET) if fail_count else (GREEN + '0' + RESET)}")
    print(f"  Total elapsed      : {total_ms:.2f} ms  ({total_ms/total:.2f} ms avg)")
    print(f"  Results saved to   : {RESULTS_DIR}/")
    print(f"{'='*72}\n")

    # Save machine-readable summary
    summary = {
        "total": total,
        "ok": ok_count,
        "failed": fail_count,
        "avg_ms": round(total_ms / total, 3),
        "fixtures": [
            {
                "id": r["fixture_id"],
                "label": r["label"],
                "ok": r["all_assertions_ok"],
                "elapsed_ms": r["elapsed_ms"],
                "audit_overall": r["audit_overall"],
            }
            for r in results
        ],
    }
    with (RESULTS_DIR / "engine_report.json").open("w") as fh:
        json.dump(summary, fh, indent=2)

    # Save plain-text report (CI-friendly)
    lines = [
        "Canon Engine Validation Report",
        "=" * 60,
        f"Fixtures : {total}",
        f"OK       : {ok_count}",
        f"Failed   : {fail_count}",
        f"Avg ms   : {total_ms/total:.3f}",
        "",
    ]
    for r in results:
        status = "PASS" if r["all_assertions_ok"] else "FAIL"
        lines.append(f"[{status}] {r['fixture_id']:30}  {r['elapsed_ms']:.2f} ms  audit={r['audit_overall']}")
        for a in r["assertions"]:
            ok_str = "ok" if a["ok"] else f"FAIL (expected {a['expected']}, actual {a['actual']})"
            lines.append(f"       {a['key']:35} {ok_str}")
        lines.append("")

    (RESULTS_DIR / "engine_report.txt").write_text("\n".join(lines))
    print(f"  engine_report.json + engine_report.txt written.\n")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
