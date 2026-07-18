#!/usr/bin/env python3
# examples/intent_demo/run_demo.py

"""
IVD Core Loop — Runnable Showcase
==================================

The 3-minute version of what this whole framework is about: a structured
intent artifact with testable constraints catches a hallucinated
implementation before a human ever has to review it.

Scenario (the same one used throughout the docs):
  You ask an AI agent: "Add export to CSV for admin compliance reporting."
  Without a structured intent, the agent fills the gaps from training-data
  patterns — a plausible, readable, WRONG implementation:
    - no admin check (the prompt never said who can call this)
    - different/renamed columns (a "typical" user export, not YOUR schema)
    - US-formatted dates (the common default, not ISO 8601)

  This demo:
    1. Shows that hallucinated implementation (examples/intent_demo/hallucinated_export.py)
    2. Shows the intent artifact an AI would write instead
       (examples/intent_demo/csv_export_intent.yaml) — three constraints,
       each with a real test
    3. Runs the REAL pytest suite (test_csv_export.py) against the
       hallucinated implementation — watch it fail
    4. Runs the same suite against an implementation written against the
       intent (correct_export.py) — watch it pass

Nothing here is narrated or canned — every PASS/FAIL below is a real
pytest run against real code in this directory.

Run:
    python examples/intent_demo/run_demo.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent

USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def cyan(t):    return _c("36", t)
def green(t):   return _c("32", t)
def yellow(t):  return _c("33", t)
def red(t):     return _c("31", t)
def magenta(t): return _c("35", t)
def bold(t):    return _c("1", t)
def dim(t):     return _c("2", t)


def banner(title: str, color=magenta) -> None:
    line = "═" * 70
    print()
    print(color(line))
    print(color(f"  {title}"))
    print(color(line))


def step(num: int, title: str) -> None:
    print()
    print(cyan(bold(f"━━━ Step {num}: {title} ━━━")))


def narrate(text: str) -> None:
    for line in text.strip().splitlines():
        print(f"  {line.rstrip()}")


def show_file(path: Path, max_lines: int | None = None) -> None:
    lines = path.read_text().splitlines()
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        print(dim(f"  │ {line}"))


def run_pytest(impl_module: str) -> tuple[int, str]:
    """Run test_csv_export.py against a given implementation module. Real subprocess, real pytest."""
    import os
    env = dict(**os.environ, INTENT_DEMO_IMPL=impl_module)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "test_csv_export.py", "-v", "--tb=short", "--no-header"],
        cwd=str(DEMO_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def summarize_pytest_output(output: str) -> None:
    for line in output.splitlines():
        if "PASSED" in line:
            print(f"  {green(line.strip())}")
        elif "FAILED" in line:
            print(f"  {red(line.strip())}")
        elif line.strip().startswith("assert") or "AssertionError" in line or "PermissionError" in line:
            print(f"  {yellow(line.strip())}")


def main() -> int:
    banner("IVD CORE LOOP — RUNNABLE SHOWCASE", magenta)
    narrate(
        "Prompt: \"Add export to CSV for admin compliance reporting.\"\n"
        "\n"
        "Without a structured intent, an AI agent fills in the blanks from\n"
        "training-data patterns. Every PASS/FAIL below is a REAL pytest run —\n"
        "nothing in this demo is narrated or canned.\n"
    )

    step(1, "The vague-prompt implementation (what gap-filling produces)")
    narrate("examples/intent_demo/hallucinated_export.py — plausible, readable, wrong in 3 ways:")
    print()
    show_file(DEMO_DIR / "hallucinated_export.py", max_lines=14)
    print(dim("  │ ..."))

    step(2, "The intent artifact an AI writes instead")
    narrate(
        "examples/intent_demo/csv_export_intent.yaml — three constraints, each\n"
        "with a name, a requirement, and a real test path:\n"
    )
    print()
    show_file(DEMO_DIR / "csv_export_intent.yaml", max_lines=27)

    step(3, "Run the constraint tests against the hallucinated implementation")
    narrate("$ INTENT_DEMO_IMPL=hallucinated_export pytest test_csv_export.py -v\n")
    rc_before, out_before = run_pytest("hallucinated_export")
    summarize_pytest_output(out_before)
    n_failed_before = out_before.count(" FAILED")
    print()
    if n_failed_before == 3:
        print(f"  {red(bold(f'{n_failed_before}/3 constraint tests FAILED'))} — caught before any human reviewed the code.")
    else:
        print(f"  {yellow(f'{n_failed_before}/3 constraint tests failed')} (expected 3/3 — see raw output above).")

    step(4, "Run the SAME tests against an implementation written against the intent")
    narrate("$ INTENT_DEMO_IMPL=correct_export pytest test_csv_export.py -v\n")
    rc_after, out_after = run_pytest("correct_export")
    summarize_pytest_output(out_after)
    n_passed_after = out_after.count(" PASSED")
    print()
    if n_passed_after == 3 and rc_after == 0:
        print(f"  {green(bold(f'{n_passed_after}/3 constraint tests PASSED'))}.")
    else:
        print(f"  {yellow(f'{n_passed_after}/3 passed')} (expected 3/3 — see raw output above).")

    banner("THE POINT", green)
    narrate(
        "The hallucination (no admin check, wrong columns, wrong date format)\n"
        "was never a code-review finding or a bug report. It was a FAILING TEST,\n"
        "caught the moment the constraint-segmented implementation ran — before\n"
        "you, the human, ever had to notice it yourself.\n"
        "\n"
        "This is the entire IVD core loop. Everything else in this repo —\n"
        "Judgment (examples/judgment_demo/), Canon, the 31 MCP tools — builds\n"
        "on top of this same mechanism: structured constraints with real tests\n"
        "behind them.\n"
    )

    ok = (n_failed_before == 3) and (n_passed_after == 3) and (rc_after == 0)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
