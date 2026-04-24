#!/usr/bin/env python3
"""
canon/validation/validate_rules.py  — Option C: Rules Effectiveness Validation

Calls a real LLM with and without the Canon Phase 0a rules block installed,
then scores both responses against the Canon R-invariants (R1, R2, R5, R10, R14)
using the Canon audit engine.

Requires one of:
    OPENAI_API_KEY   (uses gpt-4o-mini by default; override with CANON_LLM_MODEL)
    ANTHROPIC_API_KEY  (uses claude-3-haiku by default)

Run from the ivd/ directory:

    export OPENAI_API_KEY=sk-...
    cd /path/to/ivd
    python -m canon.validation.validate_rules

Output:
    canon/validation/results/rules_<fixture_id>_baseline.json   — without rules
    canon/validation/results/rules_<fixture_id>_rules_on.json   — with rules
    canon/validation/results/rules_report.txt                   — comparison summary
    canon/validation/results/rules_report.json                  — machine-readable

If no LLM key is set, prints clear setup instructions and exits 0.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
THIS_DIR = Path(__file__).parent
IVD_ROOT = THIS_DIR.parent.parent
RESULTS_DIR = THIS_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

if str(IVD_ROOT) not in sys.path:
    sys.path.insert(0, str(IVD_ROOT))

from canon import infer, render, audit          # noqa: E402
from canon.validation.fixtures import FIXTURES  # noqa: E402

# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------
GREEN  = "\033[32m" if sys.stdout.isatty() else ""
RED    = "\033[31m" if sys.stdout.isatty() else ""
YELLOW = "\033[33m" if sys.stdout.isatty() else ""
CYAN   = "\033[36m" if sys.stdout.isatty() else ""
BOLD   = "\033[1m"  if sys.stdout.isatty() else ""
RESET  = "\033[0m"  if sys.stdout.isatty() else ""


# ---------------------------------------------------------------------------
# Load the Canon rules block from the canonical recipe
# ---------------------------------------------------------------------------

def _load_rules_block() -> str:
    """Read the cursorrules_format adapter view from canon-rules.yaml."""
    try:
        import yaml
    except ImportError:
        return ""
    recipe_path = IVD_ROOT / "recipes" / "canon-rules.yaml"
    if not recipe_path.exists():
        return ""
    with recipe_path.open() as f:
        doc = yaml.safe_load(f)
    return doc.get("agent_rules_block", {}).get("cursorrules_format", "")


CANON_RULES_BLOCK = _load_rules_block()


# ---------------------------------------------------------------------------
# LLM backends
# ---------------------------------------------------------------------------

def _call_openai(prompt: str, system: str, model: str) -> Tuple[str, float]:
    import openai
    t0 = time.perf_counter()
    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        temperature=0,
        max_tokens=600,
    )
    elapsed = (time.perf_counter() - t0) * 1000
    return resp.choices[0].message.content or "", elapsed


def _call_anthropic(prompt: str, system: str, model: str) -> Tuple[str, float]:
    import anthropic
    t0 = time.perf_counter()
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=600,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = (time.perf_counter() - t0) * 1000
    return resp.content[0].text, elapsed


def call_llm(prompt: str, system: str) -> Tuple[str, float, str]:
    """Call whichever LLM has a key set. Returns (text, elapsed_ms, model_used)."""
    if os.environ.get("OPENAI_API_KEY"):
        model = os.environ.get("CANON_LLM_MODEL", "gpt-4o-mini")
        text, ms = _call_openai(prompt, system, model)
        return text, ms, f"openai/{model}"
    if os.environ.get("ANTHROPIC_API_KEY"):
        model = os.environ.get("CANON_LLM_MODEL", "claude-3-haiku-20240307")
        text, ms = _call_anthropic(prompt, system, model)
        return text, ms, f"anthropic/{model}"
    raise EnvironmentError("No LLM API key found.")


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_NO_RULES = "You are a helpful AI assistant."

SYSTEM_WITH_RULES = f"You are a helpful AI assistant.\n\n{CANON_RULES_BLOCK}"

PROMPT_TEMPLATE = "{text}"


# ---------------------------------------------------------------------------
# Score one LLM response with the Canon engine
# ---------------------------------------------------------------------------

def score_response(llm_text: str, stakes: str) -> Dict[str, Any]:
    contract = infer(llm_text, stakes=stakes)
    document = render(contract)
    report   = audit(document)

    def _finding(r_name: str):
        return next((f for f in report.findings if f.r == r_name), None)

    r1 = _finding("R1")
    r2 = _finding("R2")
    r5 = _finding("R5")
    r14 = _finding("R14")

    return {
        "audit_overall":  report.overall,
        "audit_partial":  report.partial,
        "R1_status":  r1.status  if r1  else "skipped",
        "R2_status":  r2.status  if r2  else "skipped",
        "R5_status":  r5.status  if r5  else "skipped",
        "R14_status": r14.status if r14 else "skipped",
        "R2_has_glyph":  r2 is not None and r2.status == "pass",
        "R5_beat_emitted": len(document.verification_beats) > 0,
        "body_with_marks": document.body_with_marks,
        "verification_beats": document.verification_beats,
        "identity_statement": document.identity_statement,
        "markdown": document.to_markdown(),
        "hash": report.hash,
    }


# ---------------------------------------------------------------------------
# Run one fixture — baseline then rules-on
# ---------------------------------------------------------------------------

def run_fixture(fx: Dict[str, Any], llm_model_used: str) -> Dict[str, Any]:
    fid    = fx["id"]
    text   = fx["text"]
    stakes = fx.get("stakes", "medium")

    print(f"\n  {CYAN}[{fid}]{RESET}  {fx['label']}  (stakes={stakes})")

    # Baseline (no rules)
    print(f"    → calling LLM without Canon rules …", end=" ", flush=True)
    baseline_text, baseline_ms, _ = call_llm(PROMPT_TEMPLATE.format(text=text), SYSTEM_NO_RULES)
    print(f"{baseline_ms:.0f} ms")
    baseline_score = score_response(baseline_text, stakes)

    # Rules-on
    print(f"    → calling LLM with Canon rules …", end=" ", flush=True)
    rules_text, rules_ms, _ = call_llm(PROMPT_TEMPLATE.format(text=text), SYSTEM_WITH_RULES)
    print(f"{rules_ms:.0f} ms")
    rules_score = score_response(rules_text, stakes)

    # Compare: did each R improve (or stay pass)?
    r_names = ["R1", "R2", "R5", "R14"]
    status_order = {"pass": 2, "partial": 1, "fail": 0, "none": 0, "skipped": -1}

    improvements: Dict[str, str] = {}
    for r in r_names:
        base_s = baseline_score.get(f"{r}_status", "skipped")
        rule_s = rules_score.get(f"{r}_status", "skipped")
        b_val  = status_order.get(base_s, -1)
        r_val  = status_order.get(rule_s, -1)
        if r_val > b_val:
            improvements[r] = "improved"
        elif r_val < b_val:
            improvements[r] = "regressed"
        else:
            improvements[r] = "same"

    result = {
        "fixture_id":    fid,
        "label":         fx["label"],
        "stakes":        stakes,
        "llm_model":     llm_model_used,
        "prompt":        text,
        "baseline": {
            "llm_text":   baseline_text,
            "elapsed_ms": round(baseline_ms, 1),
            "score":      baseline_score,
        },
        "rules_on": {
            "llm_text":   rules_text,
            "elapsed_ms": round(rules_ms, 1),
            "score":      rules_score,
        },
        "improvements": improvements,
        "improved_count":  sum(1 for v in improvements.values() if v == "improved"),
        "regressed_count": sum(1 for v in improvements.values() if v == "regressed"),
    }

    # Save per-fixture
    for variant, data in [("baseline", result["baseline"]), ("rules_on", result["rules_on"])]:
        out = RESULTS_DIR / f"rules_{fid}_{variant}.json"
        with out.open("w") as fh:
            json.dump({**result, "_variant": variant, "data": data}, fh, indent=2, default=str)

    return result


# ---------------------------------------------------------------------------
# Pretty-print one fixture result
# ---------------------------------------------------------------------------

def print_fixture_result(r: Dict[str, Any]) -> None:
    improved  = r["improved_count"]
    regressed = r["regressed_count"]
    total_r   = len(r["improvements"])

    col = GREEN if improved > 0 and regressed == 0 else (YELLOW if regressed > 0 else RESET)
    print(f"\n  {col}[{r['fixture_id']}]{RESET}  {r['label']}")
    print(f"  Model: {r['llm_model']}  stakes={r['stakes']}")
    print(f"  Improved: {GREEN}{improved}{RESET}/{total_r}  Regressed: "
          f"{(RED + str(regressed) + RESET) if regressed else (GREEN + '0' + RESET)}")

    b = r["baseline"]["score"]
    o = r["rules_on"]["score"]
    print(f"\n  {'R':5}  {'Baseline':10}  {'Rules-On':10}  {'Delta':12}")
    print(f"  {'-'*42}")
    for rname in ["R1", "R2", "R5", "R14"]:
        bs = b.get(f"{rname}_status", "?")
        rs = o.get(f"{rname}_status", "?")
        delta = r["improvements"].get(rname, "?")
        col = GREEN if delta == "improved" else (RED if delta == "regressed" else "")
        print(f"  {rname:5}  {bs:10}  {rs:10}  {col}{delta}{RESET}")

    # Side-by-side response snippet
    b_text = r["baseline"]["llm_text"]
    o_text = r["rules_on"]["llm_text"]
    print(f"\n  {BOLD}Baseline response (first 200 chars):{RESET}")
    print(f"    {b_text[:200].replace(chr(10), chr(10) + '    ')}")
    print(f"\n  {BOLD}Rules-on response (first 200 chars):{RESET}")
    print(f"    {o_text[:200].replace(chr(10), chr(10) + '    ')}")


# ---------------------------------------------------------------------------
# No-key fallback
# ---------------------------------------------------------------------------

def print_setup_instructions() -> None:
    rules_preview = CANON_RULES_BLOCK[:500].replace("\n", "\n    ") if CANON_RULES_BLOCK else "(not loaded)"
    print(f"""
{BOLD}{'='*72}{RESET}
{BOLD}  Canon Rules Effectiveness Validation  —  Option C{RESET}
{'='*72}

  {YELLOW}No LLM API key found.{RESET}

  This test compares LLM responses WITH and WITHOUT the Canon Phase 0a
  rules block installed, then scores both using the Canon audit engine.

  {BOLD}Set one of these to run it:{RESET}

    export OPENAI_API_KEY=sk-...
    python -m canon.validation.validate_rules

    export ANTHROPIC_API_KEY=sk-ant-...
    python -m canon.validation.validate_rules

  Optionally override the model:
    export CANON_LLM_MODEL=gpt-4o
    export CANON_LLM_MODEL=claude-3-5-sonnet-20241022

  {BOLD}What it tests:{RESET}
  For each of {len(FIXTURES)} fixture prompts it will call the LLM twice:
    1. System prompt = "You are a helpful AI assistant."
    2. System prompt = (above) + the Canon Phase 0a rules block

  Each response is scored by the Canon audit engine (R1/R2/R5/R14).
  The report shows which Rs improved, stayed the same, or regressed.

  {BOLD}Canon rules block loaded from:{RESET}
    ivd/recipes/canon-rules.yaml → cursorrules_format
  {BOLD}Preview:{RESET}
    {rules_preview}…

{'='*72}
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    has_key = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))

    if not has_key:
        print_setup_instructions()
        return 0

    print(f"\n{BOLD}{'='*72}{RESET}")
    print(f"{BOLD}  Canon Rules Effectiveness Validation  —  Option C{RESET}")
    print(f"  Fixtures: {len(FIXTURES)}  |  Results: {RESULTS_DIR}")
    print(f"{BOLD}{'='*72}{RESET}")

    # Detect model
    try:
        _, _, llm_model_used = call_llm("ping", "You are a test. Reply 'ok'.")
    except Exception as e:
        print(f"{RED}LLM connection failed:{RESET} {e}")
        return 1
    print(f"\n  LLM backend: {CYAN}{llm_model_used}{RESET}")

    if not CANON_RULES_BLOCK:
        print(f"{RED}ERROR:{RESET} Could not load Canon rules block from ivd/recipes/canon-rules.yaml")
        return 1
    print(f"  Rules block: {len(CANON_RULES_BLOCK)} chars loaded from canon-rules.yaml")

    results = []
    for fx in FIXTURES:
        r = run_fixture(fx, llm_model_used)
        results.append(r)
        print_fixture_result(r)

    # Aggregate
    total     = len(results)
    total_imp = sum(r["improved_count"] for r in results)
    total_reg = sum(r["regressed_count"] for r in results)
    possible  = total * 4  # R1+R2+R5+R14 per fixture

    pct = (total_imp / possible * 100) if possible else 0

    print(f"\n{BOLD}{'='*72}{RESET}")
    print(f"{BOLD}  Summary{RESET}")
    print(f"{'='*72}")
    print(f"  Fixtures run       : {total}")
    print(f"  R-invariant checks : {possible}  (R1+R2+R5+R14 × {total} fixtures)")
    print(f"  Improved           : {GREEN}{total_imp}{RESET} / {possible}  ({pct:.0f}%)")
    print(f"  Regressed          : {(RED + str(total_reg) + RESET) if total_reg else (GREEN + '0' + RESET)}")
    print(f"  LA1 threshold      : ≥ 60% paired-improvement rate")
    threshold_met = pct >= 60
    col = GREEN if threshold_met else RED
    print(f"  LA1 gate           : {col}{'PASS' if threshold_met else 'FAIL'}{RESET}  ({pct:.0f}% vs 60% threshold)")
    print(f"  Results saved to   : {RESULTS_DIR}/")
    print(f"{'='*72}\n")

    # Save reports
    summary = {
        "total_fixtures": total,
        "possible_checks": possible,
        "improved": total_imp,
        "regressed": total_reg,
        "improvement_pct": round(pct, 1),
        "la1_threshold_pct": 60,
        "la1_pass": threshold_met,
        "llm_model": llm_model_used,
        "fixtures": [
            {
                "id": r["fixture_id"],
                "improved": r["improved_count"],
                "regressed": r["regressed_count"],
                "improvements": r["improvements"],
            }
            for r in results
        ],
    }
    with (RESULTS_DIR / "rules_report.json").open("w") as fh:
        json.dump(summary, fh, indent=2)

    lines = [
        "Canon Rules Effectiveness Validation Report", "=" * 60,
        f"Fixtures   : {total}",
        f"Improved   : {total_imp} / {possible} ({pct:.0f}%)",
        f"Regressed  : {total_reg}",
        f"LA1 gate   : {'PASS' if threshold_met else 'FAIL'} (>= 60% threshold)",
        f"LLM model  : {llm_model_used}",
        "",
    ]
    for r in results:
        lines.append(f"[{r['fixture_id']}] {r['label']}")
        for rname, delta in r["improvements"].items():
            b = r["baseline"]["score"].get(f"{rname}_status", "?")
            o = r["rules_on"]["score"].get(f"{rname}_status", "?")
            lines.append(f"  {rname}: {b} → {o}  ({delta})")
        lines.append("")
    (RESULTS_DIR / "rules_report.txt").write_text("\n".join(lines))
    print("  rules_report.json + rules_report.txt written.\n")

    return 0 if not total_reg else 1


if __name__ == "__main__":
    sys.exit(main())
