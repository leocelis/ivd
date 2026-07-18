# IVD Core Loop — Runnable Showcase

The 30-second version of the whole framework. Run it:

```bash
python examples/intent_demo/run_demo.py
```

Fully offline, no dependencies beyond `pytest` (already in `[dev]`), no API key.

## What it shows

The scenario used throughout the docs: "Add export to CSV for admin compliance
reporting." Without a structured intent, an AI agent fills the gaps with
training-data patterns — a plausible, readable, wrong implementation
([`hallucinated_export.py`](hallucinated_export.py)): no admin check, renamed
columns, US-formatted dates.

[`csv_export_intent.yaml`](csv_export_intent.yaml) is the intent artifact an
AI would write instead — three constraints, each with a real pytest test in
[`test_csv_export.py`](test_csv_export.py).

`run_demo.py` runs that real test suite against both implementations:

- against `hallucinated_export.py` → **3/3 tests fail**
- against `correct_export.py` (written against the intent) → **3/3 tests pass**

Nothing here is narrated or canned. Every PASS/FAIL in the demo output is a
live `pytest` subprocess run against the code in this directory.

## Why this scenario, and not something more "AI"

Because it doesn't need to be. The mechanism IVD is built on — a testable
constraint catching a wrong implementation before a human reviews it — works
identically whether the implementation was written by a person, an AI agent,
or copy-pasted from Stack Overflow. This demo isolates that mechanism from
everything else (LLM calls, MCP tool orchestration, IDE integration) so you
can see it work in under a minute.

For the AI-specific half of IVD — compounding *judgment* from real corrections
across agent runs — see [`../judgment_demo/`](../judgment_demo/).
