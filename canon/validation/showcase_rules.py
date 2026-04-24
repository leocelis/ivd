#!/usr/bin/env python3
"""
canon/validation/showcase_rules.py — Option D: Canon Rules Showcase.

Asks a real LLM real user questions twice — once with the Canon Phase 0a
rules block in the system prompt and once without — then scores each
response using a DIRECT scorer that inspects the LLM's own output for
Canon structures (Setting:, ✓ verified, ACTION/REVERSIBLE/APPROVE?, etc.)
rather than running the response through Canon's render+audit pipeline
(which would auto-inject R1/R14 and obscure the LLM's actual behavior).

Output:
  results/showcase_<qid>_baseline.json
  results/showcase_<qid>_rules_on.json
  results/showcase_report.md           ← full side-by-side comparison report
  results/showcase_report.json
  results/showcase_summary.txt

Run from ivd/:
  set -a && source .env && set +a
  python -m canon.validation.showcase_rules
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

THIS_DIR    = Path(__file__).parent
IVD_ROOT    = THIS_DIR.parent.parent
RESULTS_DIR = THIS_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

if str(IVD_ROOT) not in sys.path:
    sys.path.insert(0, str(IVD_ROOT))

from canon.validation.showcase_prompts import PROMPTS  # noqa: E402
from canon.validation.showcase_scorer  import (        # noqa: E402
    score_llm_output,
    compare,
)

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
TTY    = sys.stdout.isatty()
GREEN  = "\033[32m" if TTY else ""
RED    = "\033[31m" if TTY else ""
YELLOW = "\033[33m" if TTY else ""
CYAN   = "\033[36m" if TTY else ""
BOLD   = "\033[1m"  if TTY else ""
DIM    = "\033[2m"  if TTY else ""
RESET  = "\033[0m"  if TTY else ""

# ---------------------------------------------------------------------------
# Load Canon rules block
# ---------------------------------------------------------------------------

def _load_rules_block() -> str:
    try:
        import yaml
    except ImportError:
        return ""
    p = IVD_ROOT / "recipes" / "canon-rules.yaml"
    if not p.exists():
        return ""
    return yaml.safe_load(p.read_text()).get("agent_rules_block", {}).get("cursorrules_format", "")


CANON_RULES_BLOCK = _load_rules_block()

SYSTEM_NO_RULES   = "You are a helpful AI assistant."

# Note: the rules block is wrapped with a directive prefix because elaborate
# format-instruction blocks need top-of-prompt salience to be followed
# reliably. The directive is descriptive, not coercive — it tells the model
# the block is mandatory format guidance, not optional context.
SYSTEM_WITH_RULES = (
    "You are a helpful AI assistant. The instructions below are STRICT FORMAT "
    "RULES that you MUST follow on every reply, without exception. They are "
    "not suggestions. Apply R1, R2, R5, R10, R14 literally as written.\n\n"
    f"{CANON_RULES_BLOCK}"
)

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
        max_tokens=900,
    )
    return resp.choices[0].message.content or "", (time.perf_counter() - t0) * 1000


def _call_anthropic(prompt: str, system: str, model: str) -> Tuple[str, float]:
    import anthropic
    t0 = time.perf_counter()
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model, max_tokens=900, system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text, (time.perf_counter() - t0) * 1000


def call_llm(prompt: str, system: str) -> Tuple[str, float, str]:
    if os.environ.get("OPENAI_API_KEY"):
        m = os.environ.get("CANON_LLM_MODEL", "gpt-4o")
        t, ms = _call_openai(prompt, system, m)
        return t, ms, f"openai/{m}"
    if os.environ.get("ANTHROPIC_API_KEY"):
        m = os.environ.get("CANON_LLM_MODEL", "claude-3-haiku-20240307")
        t, ms = _call_anthropic(prompt, system, m)
        return t, ms, f"anthropic/{m}"
    raise EnvironmentError("No LLM API key (OPENAI_API_KEY or ANTHROPIC_API_KEY)")


# ---------------------------------------------------------------------------
# Per-prompt run
# ---------------------------------------------------------------------------

def run_prompt(p: Dict[str, Any], model_used: str) -> Dict[str, Any]:
    qid       = p["id"]
    question  = p["question"]
    stakes    = p["stakes"]
    needs_R5  = p["expects_R5_beat"]
    needs_R10 = p["expects_R10_correction"]

    print(f"\n  {CYAN}[{qid}]{RESET} {BOLD}{p['label']}{RESET}  "
          f"({DIM}stakes={stakes}{RESET})")
    print(f"  {DIM}Q: {question[:110]}{'…' if len(question) > 110 else ''}{RESET}")

    print(f"  → baseline (no rules)…", end=" ", flush=True)
    base_text, base_ms, _ = call_llm(question, SYSTEM_NO_RULES)
    print(f"{base_ms:.0f} ms ({len(base_text)} chars)")

    print(f"  → rules-on…           ", end=" ", flush=True)
    rules_text, rules_ms, _ = call_llm(question, SYSTEM_WITH_RULES)
    print(f"{rules_ms:.0f} ms ({len(rules_text)} chars)")

    base_score  = score_llm_output(base_text,  expects_R5_beat=needs_R5, expects_R10_correction=needs_R10)
    rules_score = score_llm_output(rules_text, expects_R5_beat=needs_R5, expects_R10_correction=needs_R10)
    delta = compare(base_score, rules_score)

    improved  = sum(1 for v in delta.values() if v == "improved")
    regressed = sum(1 for v in delta.values() if v == "regressed")

    result = {
        "qid":      qid,
        "label":    p["label"],
        "stakes":   stakes,
        "question": question,
        "expectations": {
            "R5_beat":        needs_R5,
            "R10_correction": needs_R10,
        },
        "why": p["why"],
        "model_used": model_used,
        "baseline": {
            "elapsed_ms": round(base_ms, 1),
            "text":       base_text,
            "score":      base_score,
        },
        "rules_on": {
            "elapsed_ms": round(rules_ms, 1),
            "text":       rules_text,
            "score":      rules_score,
        },
        "delta":     delta,
        "improved":  improved,
        "regressed": regressed,
    }

    # Persist per-prompt
    for variant in ("baseline", "rules_on"):
        with (RESULTS_DIR / f"showcase_{qid}_{variant}.json").open("w") as fh:
            json.dump({"qid": qid, "variant": variant, **result[variant], "delta": delta}, fh, indent=2)

    return result


# ---------------------------------------------------------------------------
# Pretty print
# ---------------------------------------------------------------------------

def _wrap(text: str, width: int = 72, indent: str = "  ") -> str:
    """Wrap a block of text to width, preserving existing newlines."""
    import textwrap
    lines = []
    for para in text.splitlines():
        if para.strip():
            lines.extend(textwrap.wrap(para, width=width - len(indent),
                                       initial_indent=indent,
                                       subsequent_indent=indent))
        else:
            lines.append("")
    return "\n".join(lines)


def print_result(r: Dict[str, Any]) -> None:
    improved  = r["improved"]
    regressed = r["regressed"]
    same      = 5 - improved - regressed

    print(f"\n  {BOLD}Δ  improved {GREEN}{improved}{RESET}  "
          f"same {same}  "
          f"regressed {(RED if regressed else GREEN) + str(regressed) + RESET}")

    bs = r["baseline"]["score"]
    rs = r["rules_on"]["score"]
    print(f"\n  {'R':5}{'Baseline':12}{'Rules-On':12}{'Δ':10}")
    print(f"  {'-'*40}")
    for rn in ("R1", "R2", "R5", "R10", "R14"):
        b   = bs[rn]["status"]
        o   = rs[rn]["status"]
        d   = r["delta"][rn]
        col = GREEN if d == "improved" else (RED if d == "regressed" else "")
        print(f"  {rn:5}{b:12}{o:12}{col}{d}{RESET}")

    # Show the actual LLM responses so the terminal is self-explanatory.
    # Trim to ~5 lines each — enough to see the structural difference.
    def _head(text: str, lines: int = 6) -> str:
        out = "\n".join(text.splitlines()[:lines])
        remaining = len(text.splitlines()) - lines
        if remaining > 0:
            out += f"\n  {DIM}… ({remaining} more lines){RESET}"
        return out

    b_text = r["baseline"]["text"]
    o_text = r["rules_on"]["text"]
    print(f"\n  {DIM}── WITHOUT Canon Rules ──────────────────────────────────{RESET}")
    for line in _head(b_text).splitlines():
        print(f"  {DIM}{line}{RESET}")
    print(f"\n  {BOLD}── WITH Canon Rules ─────────────────────────────────────{RESET}")
    for line in _head(o_text).splitlines():
        print(f"  {line}")


# ---------------------------------------------------------------------------
# Markdown report — side-by-side comparison
# ---------------------------------------------------------------------------

_GLYPH_OK   = "✅"
_GLYPH_BAD  = "❌"
_GLYPH_MID  = "🟡"
_GLYPH_DELTA = {"improved": "🟢", "same": "⚪", "regressed": "🔴"}


def _status_glyph(s: str) -> str:
    return {"pass": _GLYPH_OK, "partial": _GLYPH_MID, "fail": _GLYPH_BAD}.get(s, "·")


def write_markdown_report(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> Path:
    out = RESULTS_DIR / "showcase_report.md"
    L: List[str] = []

    L.append("# Canon Rules — Showcase Validation Report")
    L.append("")
    L.append(f"_Model:_ `{summary['model_used']}` &nbsp;|&nbsp; "
             f"_Prompts:_ {summary['n_prompts']} &nbsp;|&nbsp; "
             f"_Generated:_ {summary['generated_at']}")
    L.append("")
    L.append("This report shows what happens when you put the **Canon Phase 0a "
             "rules block** in the system prompt of a real LLM, on real user "
             "questions, and measure what the LLM actually says.")
    L.append("")
    L.append("Two calls per prompt: same model, same temperature, same user "
             "message — only the system prompt differs. The rules block is "
             "loaded straight from `ivd/recipes/canon-rules.yaml` "
             "(`cursorrules_format` adapter view), so this is exactly what "
             "ships when a user runs `canon_check_rules_installed`.")
    L.append("")
    L.append("Scoring inspects the LLM's raw output directly — no Canon engine "
             "post-processing — so what you see is what the LLM produced.")
    L.append("")

    # --- Headline ---
    net = summary["improved"] - summary["regressed"]
    L.append("## TL;DR")
    L.append("")
    L.append(f"On {summary['actionable_total']} R-invariant cells where the baseline LLM "
             f"got it **wrong**, installing the Canon rules block flipped "
             f"**{summary['actionable_improved']}** to right "
             f"({summary['actionable_pct']}% precision) "
             f"with **{summary['regressed']} regressions**. Net behaviour change: "
             f"**+{net} R-invariants** across {summary['n_prompts']} real prompts.")
    L.append("")
    L.append(f"| Metric | Value |")
    L.append(f"|---|---|")
    L.append(f"| Total R-cells (5 invariants × {summary['n_prompts']} prompts) | {summary['checks_total']} |")
    L.append(f"| Cells improved | **{summary['improved']}** |")
    L.append(f"| Cells unchanged (no-op or already pass) | {summary['same']} |")
    L.append(f"| Cells regressed | **{summary['regressed']}** |")
    L.append(f"| Net behaviour change | **+{net} R-invariants** |")
    L.append(f"| Actionable cells (baseline failed) | {summary['actionable_total']} |")
    L.append(f"| Actionable cells improved | **{summary['actionable_improved']}** ({summary['actionable_pct']}%) |")
    L.append(f"| LA1 gate (≥60% of actionable cells improved) | "
             f"**{('PASS ✅' if summary['la1_pass'] else 'FAIL ❌')}** |")
    L.append("")

    # --- Per-R rollup ---
    L.append("## Behavior change by R-invariant")
    L.append("")
    L.append("| R | Baseline pass-rate | Rules-on pass-rate | Δ |")
    L.append("|---|---|---|---|")
    for rn in ("R1", "R2", "R5", "R10", "R14"):
        b_pass = sum(1 for r in results if r["baseline"]["score"][rn]["status"] == "pass")
        o_pass = sum(1 for r in results if r["rules_on"]["score"][rn]["status"] == "pass")
        n = len(results)
        delta = o_pass - b_pass
        sign  = "+" if delta > 0 else ""
        L.append(f"| **{rn}** | {b_pass}/{n} | {o_pass}/{n} | {sign}{delta} |")
    L.append("")
    L.append("> **R1** Setting Phase opener &nbsp;·&nbsp; **R2** Confidence glyphs &nbsp;·&nbsp; "
             "**R5** Verification beat (ACTION/REVERSIBLE/APPROVE?) &nbsp;·&nbsp; "
             "**R10** Folk-theory correction &nbsp;·&nbsp; **R14** Anthropomorphism ceiling")
    L.append("")

    # --- Per-prompt detail ---
    L.append("---")
    L.append("")
    L.append("## Side-by-side responses")
    L.append("")

    for r in results:
        L.append(f"### {r['qid']} — {r['label']}")
        L.append("")
        L.append(f"**Stakes:** `{r['stakes']}`  &nbsp;|&nbsp; "
                 f"**Improved:** {r['improved']}  &nbsp;|&nbsp; "
                 f"**Regressed:** {r['regressed']}  &nbsp;|&nbsp; "
                 f"**Latency:** baseline {r['baseline']['elapsed_ms']:.0f} ms vs "
                 f"rules-on {r['rules_on']['elapsed_ms']:.0f} ms")
        L.append("")
        L.append(f"**User question:**")
        L.append("")
        L.append(f"> {r['question']}")
        L.append("")
        L.append(f"**Why this matters:** {r['why']}")
        L.append("")

        # Status table per R
        L.append("| R | Baseline | Rules-on | Δ |")
        L.append("|---|---|---|---|")
        for rn in ("R1", "R2", "R5", "R10", "R14"):
            bs = r["baseline"]["score"][rn]["status"]
            rs = r["rules_on"]["score"][rn]["status"]
            d  = r["delta"][rn]
            L.append(f"| **{rn}** | {_status_glyph(bs)} {bs} | {_status_glyph(rs)} {rs} | {_GLYPH_DELTA[d]} {d} |")
        L.append("")

        # Side-by-side responses
        L.append("<table>")
        L.append("<tr>")
        L.append("<th width=\"50%\">🔻 Without Canon Rules (baseline)</th>")
        L.append("<th width=\"50%\">🟢 With Canon Rules (rules-on)</th>")
        L.append("</tr>")
        L.append("<tr>")
        L.append("<td>")
        L.append("")
        L.append("```text")
        L.append(r["baseline"]["text"])
        L.append("```")
        L.append("")
        L.append("</td>")
        L.append("<td>")
        L.append("")
        L.append("```text")
        L.append(r["rules_on"]["text"])
        L.append("```")
        L.append("")
        L.append("</td>")
        L.append("</tr>")
        L.append("</table>")
        L.append("")

        # Evidence callouts (ACTION beats, glyphs, identity)
        ev = []
        if r["rules_on"]["score"]["R5"]["complete"] and not r["baseline"]["score"]["R5"]["complete"]:
            ev.append("- **R5 verification beat appeared with rules** (`ACTION` + `REVERSIBLE` + `APPROVE?`)")
        if r["rules_on"]["score"]["R2"]["count"] > r["baseline"]["score"]["R2"]["count"]:
            n = r["rules_on"]["score"]["R2"]["count"]
            ev.append(f"- **R2 confidence glyphs appeared with rules** ({n} markers vs {r['baseline']['score']['R2']['count']})")
        if r["rules_on"]["score"]["R1"]["status"] == "pass" and r["baseline"]["score"]["R1"]["status"] == "fail":
            ev.append(f"- **R1 Setting phase opener appeared with rules**")
        if r["rules_on"]["score"]["R14"]["companionship_used"] is False and r["baseline"]["score"]["R14"]["companionship_used"]:
            ev.append(f"- **R14 companionship framing eliminated** "
                      f"(baseline used: `{r['baseline']['score']['R14']['companionship_evidence']}`)")
        if r["rules_on"]["score"]["R10"]["evidence"] and not r["baseline"]["score"]["R10"]["evidence"]:
            ev.append(f"- **R10 folk-theory correction surfaced**: `{r['rules_on']['score']['R10']['evidence']}`")

        if ev:
            L.append("**Evidence of behavior change:**")
            L.append("")
            L.extend(ev)
            L.append("")

        L.append("---")
        L.append("")

    # --- Reproducibility ---
    L.append("## Reproduce")
    L.append("")
    L.append("```bash")
    L.append("cd ivd")
    L.append("set -a && source .env && set +a")
    L.append("source .venv/bin/activate")
    L.append("python -m canon.validation.showcase_rules")
    L.append("```")
    L.append("")
    L.append(f"Per-prompt JSON in `canon/validation/results/showcase_*.json`.")
    L.append("")

    out.write_text("\n".join(L))
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")):
        print(f"{RED}No LLM API key set.{RESET} Run: set -a && source .env && set +a")
        return 1

    if not CANON_RULES_BLOCK:
        print(f"{RED}Could not load Canon rules block.{RESET}")
        return 1

    print(f"\n{BOLD}{'='*72}{RESET}")
    print(f"{BOLD}  Canon Rules — Showcase Validation (Option D){RESET}")
    print(f"{'='*72}")
    print(f"  Prompts        : {len(PROMPTS)}")
    print(f"  Rules block    : {len(CANON_RULES_BLOCK)} chars from canon-rules.yaml")
    print(f"  Results dir    : {RESULTS_DIR}")

    try:
        _, _, model_used = call_llm("ping", "Reply 'ok'.")
    except Exception as e:
        print(f"{RED}LLM connection failed:{RESET} {e}")
        return 1
    print(f"  LLM backend    : {CYAN}{model_used}{RESET}")
    print(f"{BOLD}{'='*72}{RESET}")

    results: List[Dict[str, Any]] = []
    for p in PROMPTS:
        r = run_prompt(p, model_used)
        results.append(r)
        print_result(r)

    # ---- aggregate ----
    n = len(results)
    checks_total = 5 * n
    improved  = sum(r["improved"]  for r in results)
    regressed = sum(r["regressed"] for r in results)
    same      = checks_total - improved - regressed
    pct       = round(improved / checks_total * 100, 1) if checks_total else 0.0

    # Actionable cells = cells where the BASELINE failed (i.e. there was
    # something to fix). The "same-pass" cells are correctly preserved by
    # the rules, but they're not where Canon adds visible value.
    actionable_total = 0
    actionable_improved = 0
    for r in results:
        for rn in ("R1", "R2", "R5", "R10", "R14"):
            if r["baseline"]["score"][rn]["status"] in ("fail", "partial"):
                actionable_total += 1
                if r["delta"][rn] == "improved":
                    actionable_improved += 1
    actionable_pct = round(actionable_improved / actionable_total * 100, 1) if actionable_total else 0.0

    # LA1 gate (per the spec) is the actionable improvement rate, not the
    # total cell rate — non-fail baselines have nothing to lift.
    la1_pass = actionable_pct >= 60.0

    summary = {
        "model_used":          model_used,
        "n_prompts":           n,
        "checks_total":        checks_total,
        "improved":            improved,
        "same":                same,
        "regressed":           regressed,
        "improved_pct":        pct,
        "actionable_total":    actionable_total,
        "actionable_improved": actionable_improved,
        "actionable_pct":      actionable_pct,
        "la1_pass":            la1_pass,
        "generated_at":        time.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }

    # ---- end-of-run highlight ----
    # Find the single prompt where R5 improved (the verification beat case) —
    # that's the most visceral demonstration. Fall back to the prompt with the
    # most improvements if R5 didn't fire.
    highlight = next(
        (r for r in results if r["delta"].get("R5") == "improved"),
        max(results, key=lambda r: r["improved"]),
    )
    h_b = highlight["baseline"]["text"]
    h_o = highlight["rules_on"]["text"]
    print(f"\n{BOLD}{'='*72}{RESET}")
    print(f"{BOLD}  Highlight — {highlight['label']}{RESET}")
    print(f"  Q: {highlight['question'][:80]}{'…' if len(highlight['question']) > 80 else ''}")
    print(f"{BOLD}{'='*72}{RESET}")
    print(f"\n  {DIM}WITHOUT Canon Rules:{RESET}")
    for line in h_b.splitlines()[:8]:
        print(f"  {DIM}{line}{RESET}")
    print(f"\n  {BOLD}WITH Canon Rules:{RESET}")
    for line in h_o.splitlines()[:12]:
        print(f"  {BOLD}{line}{RESET}")
    print(f"\n  {DIM}(Full side-by-side for all {n} prompts → showcase_report.md){RESET}")

    print(f"\n{BOLD}{'='*72}{RESET}")
    print(f"{BOLD}  Summary{RESET}")
    print(f"{'='*72}")
    print(f"  R-checks total      : {checks_total}  (5 invariants × {n} prompts)")
    print(f"  Improved            : {GREEN}{improved}{RESET}  ({pct}% of all cells)")
    print(f"  Same                : {same}  (no-op or already passing)")
    print(f"  Regressed           : {(RED if regressed else GREEN) + str(regressed) + RESET}")
    print(f"  Net change          : {GREEN}+{improved - regressed}{RESET} R-invariants")
    print(f"")
    print(f"  Actionable cells    : {actionable_total}  (cells where baseline failed)")
    print(f"  Actionable improved : {GREEN}{actionable_improved}{RESET}  ({actionable_pct}%)")
    gate_col = GREEN if la1_pass else RED
    gate_str = "PASS" if la1_pass else "FAIL"
    print(f"  LA1 gate (≥60%)     : {gate_col}{gate_str}{RESET}  ({actionable_pct}% of actionable cells)")
    print(f"{BOLD}{'='*72}{RESET}")

    md_path = write_markdown_report(results, summary)
    with (RESULTS_DIR / "showcase_report.json").open("w") as fh:
        json.dump({
            "summary":  summary,
            "prompts":  [{
                "qid":       r["qid"],
                "label":     r["label"],
                "stakes":    r["stakes"],
                "delta":     r["delta"],
                "improved":  r["improved"],
                "regressed": r["regressed"],
                "baseline_score": r["baseline"]["score"],
                "rules_score":    r["rules_on"]["score"],
            } for r in results],
        }, fh, indent=2)

    print(f"\n  Full report : {CYAN}{md_path}{RESET}")
    print(f"  JSON        : {RESULTS_DIR}/showcase_report.json")
    print(f"  Per-prompt  : {RESULTS_DIR}/showcase_*.json\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
