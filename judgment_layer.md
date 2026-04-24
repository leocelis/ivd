# IVD Judgment Layer

**Status:** Canonical (IVD v3.0)
**Phase:** Judgment (4th phase, after Intent / Implementation / Verification)
**Activation:** Dormant unless `<project_root>/.judgment/` exists

> **New to Judgment?** Read [`judgment_explained.md`](judgment_explained.md)
> first — it's the plain-English on-ramp that explains what problem Judgment
> solves and how, in 5 minutes, before you dive into this spec.

---

## Why a Judgment Phase?

IVD v2.x makes intent executable and verifiable. That covers the failure modes
of *underspecified* AI work: hallucinations, drift, missed constraints. It does
not cover what happens when the **intent itself was wrong** — when the system
shipped, the verification passed, and reality answered back: *this is not what
we wanted*.

That answer-back is the most expensive signal in the system, and it has been
historically thrown away. The Judgment phase captures it, structures it, and
feeds it back into intent — so future intent is written by an agent that has
*lived through* the prior corrections, not just read the principles.

> *Intent gets you to a defensible first draft. Judgment is what makes the
> hundredth draft compounding.*

The Judgment phase is also the structural answer to AI commoditization: the
model layer is converging toward parity, but **structured organizational
judgment cannot be downloaded**. It can only be accumulated. IVD v3.0 makes
the accumulation mechanism canonical.

---

## Principle 9: Judgment Compounds

> Corrections, when captured, codified, and structured, become the most
> valuable form of contextual knowledge a system has — more valuable than
> training data, more valuable than prompts, more valuable than
> documentation. They are the only knowledge that is **specific to your
> reality**. The Judgment phase exists to make that accumulation
> mechanical.

This is the 9th immutable principle (added in v3.0). It is hierarchical:
Principle 9 builds on 1–8. Without executable intent (P1–4), corrections
cannot be diagnosed. Without layered understanding (P5), patterns cannot be
distinguished from noise. Without AI-as-partner (P6), the loop cannot close
without burning out the human. Without survival across implementation (P7)
and inversion (P8), patterns become brittle.

---

## See it work (5-second runnable showcase)

Before reading the spec, run the showcase:

```bash
python examples/judgment_demo/run_demo.py
```

It walks every step described below — Baseline → Capture × 3 → Codify × 3 → Detect → Inject — against a real `.judgment/` directory, then writes 4 human-readable artifacts (`before.md`, `after.md`, `diff.md`, `llm_responses.md`) showing the agent's system message before vs after Judgment compounds.

With `OPENAI_API_KEY` set, the showcase makes a real `gpt-4o-mini` call (temperature=0, ~$0.001) and prints a verbatim before/after of the Vitest test file the agent generated on the same request — typically 2–3 framework defaults applied before (raw `vi.fn()` API mocks, bare `render()`, `userEvent.click` without `setup()`), and 3/3 of the project's local testing conventions adopted after (`server.use(http.get(...))`, `renderWithProviders(<Foo />)`, `const user = userEvent.setup()`). The project-local strings in the AFTER response — `renderWithProviders`, `src/test/mocks/server`, `src/test/test-utils` — cannot have come from the model's training data and prove the lesson was inherited from the captured Pattern.

Full narrative, verdict, and reproducibility test: [`examples/judgment_demo/README.md`](examples/judgment_demo/README.md).

---

## The Loop (10 Steps)

```
0. Baseline & Goal Calibration  ──┐
                                  │
1. Capture (raw correction)       │  agent + you
2. Codify (5 structured fields)   │
3. Pair (optional comparison)     │
                                  │
4. Detect Patterns ───────────────┤  detector
                                  │
5. Propose Recommendation ────────┤  drafter
                                  │
6. Approve (you)  ────────────────┤  GATE
                                  │
7. Apply Fix                      │  agent
                                  │
8. Inject Context (next runs)     │  injector
                                  │
9. Resolve / Archive              │  bookkeeper
                                  ─┘
```

---

## Step 0 — Baseline & Goal Calibration

Before anything is captured, every domain MUST declare a baseline:
- What does success look like (qualitative + measurable)?
- What risks are we hypothesizing?
- How fast do patterns in this domain age (`pattern_half_life_days`)?
- What's the current scale, and what change should trigger re-baselining?
- What hard signals would force a `domain_reassessment`?

Template: `ivd/templates/baseline.yaml`

A domain without a baseline cannot graduate corrections into recommendations —
the validator rejects pattern-detection runs against undeclared domains.

---

## Step 1 — Capture

`ivd_judgment_capture` writes a raw ledger entry.

**Capture must be cheap.** If it takes more than ~30 seconds, capture rate
collapses and the loop dies. The codify step does the work of structuring; the
capture step only requires:

- `raw_correction` — free text
- `domain` — must match a baseline
- `source` — `leo | audience | runtime | comparison`
- `leo_domain_depth` — `expert | practitioner | adjacent | novice`
- `originated_from_tool` — optional, but always set when known

Template: `ivd/templates/ledger-entry.yaml`

---

## Step 2 — Codify

`ivd_judgment_codify(entry_id)` returns a **structured prompt** that the
agent fills. The prompt forces five fields:

1. `expected_result` — what should have happened
2. `detected_via` — how was the failure caught
3. `diagnosed_cause` — root cause hypothesis
4. `proposed_fix` — specific, actionable
5. `fix_action_type` — one of:
   - `prompt_patch`
   - `intent_revision`
   - `capability_addition` (with `capability_subtype`: `build | buy | hire | partner`)
   - `domain_reassessment`

The agent passes the filled fields to `ivd_judgment_save_codified(entry_id, ...)`.
The validator transitions state `raw → codified` only if all five fields are
non-empty.

> **Why split codify into prompt + save?** It mirrors P6 ("AI as Understanding
> Partner"): IVD never silently writes the structured fields *for* the agent
> running in the loop. The codify tool gives the agent a thinking scaffold;
> the save tool persists the agent's answer. Audit trail and authorship stay
> intact.

---

## Step 3 — Pair (optional, comparison_pair entries only)

`ivd_judgment_pair(run_a, run_b)` captures two real runs as a single entry of
`entry_type: comparison_pair`.

This is the IVD-canonical alternative to A/B testing for systems where the
A/B harness is impractical (creative pipelines, low volume, multi-agent
runtimes). Grounding: **Pearl's Ladder of Causation** — pair analysis lives
at Rung 1 (association). Hypotheses derived from a single pair are
**plausible**; promotion to **corroborated** requires 2+ independent pairs
reaching the same `diagnosed_cause` via independent routes (different author,
different week, different model where possible).

Codify on a comparison_pair forces the agent to:
- Enumerate `diagnostic_hypotheses` with at least one `competing_hypothesis`
- Pick a single `diagnosed_cause` as the working hypothesis (still a hypothesis)
- Mark `confidence_at_capture` honestly (default: low)

Template: `ivd/templates/comparison-pair.yaml`. Recipe: `recipes/comparison-pair.yaml`.

### Comparison Pair Analysis: Why Not A/B?

A/B requires holding everything else constant. Most production AI systems
cannot:
- Creative outputs are not repeatable in the strict A/B sense
- Multi-agent systems share state across runs
- Low-volume domains never reach statistical significance

Comparison pairs accept the methodological compromise (Rung 1 instead of
Rung 2) in exchange for being executable. The corroboration discipline is
the price paid to keep them honest.

---

## Step 4 — Detect Patterns

`ivd_judgment_detect_patterns()` scans the ledger for clusters where 3+
entries share the same `diagnosed_cause` within the same domain. It either
creates a new `pattern.yaml` under `.judgment/patterns/` or updates an
existing one.

### Confidence math

Each member contributes a weight derived from `leo_domain_depth`:

| depth | weight |
|---|---|
| expert | 1.0 |
| practitioner | 0.7 |
| adjacent | 0.4 |
| novice | 0.2 |

`weighted_confidence` is the sum of member weights, normalized to [0, 1] by a
configurable cap (default: 5 expert-equivalent members = 1.0).

### Pattern freshness

Patterns age. A pattern about claude-3 prompting is stale when the project
moved to claude-4. Each pattern carries a `half_life_days` (defaults to the
domain baseline's `pattern_half_life_days`):

| freshness | rule |
|---|---|
| `fresh` | age ≤ half_life |
| `aging` | half_life < age ≤ 2 × half_life |
| `stale` | 2 × half_life < age ≤ 3 × half_life |
| `expired` | age > 3 × half_life — **NOT injected, not promotable to recommendation** |

### Tool-originated failure tracking

If a pattern's members are dominated by entries with the same
`originated_from_tool`, the tool is flagged in `pattern.originated_from_tools`
and `net_pattern_delta` increments. A tool with positive `net_pattern_delta`
is producing more patterns (failures) than it eliminates — a candidate for
deprecation. This is how the Judgment phase keeps the recipe library honest.

### domain_reassessment

If a `domain_reassessment` recommendation is proposed and approved, the
domain itself is treated as the wrong abstraction. The trigger is one of the
EIN kill-criteria signals — see baseline.yaml § "reassessment_triggers" for
the canonical list. Reassessment forces a baseline rewrite (new
`baseline.version`), and existing patterns are either re-scoped or retired.

---

## Step 5 — Propose Recommendation

`ivd_judgment_propose_recommendation(pattern_id)` drafts a recommendation
document with:

- `recommended_fix`
- `fix_action_type` (and `capability_subtype` if applicable)
- Rationale citing member ledger entries (≥ 3)
- `blast_radius_estimate` (which intents/recipes/agents this touches)
- `rollback_plan`
- **`draft_recipe_yaml`** — when the fix is reusable beyond this domain, the
  drafter emits a starting-point recipe YAML for you to refine

Recipe: `recipes/distill-pattern.yaml`.

### Capability Addition (`build | buy | hire | partner`)

When `fix_action_type == capability_addition`, the recommendation must pick
a sub-type. The decision tree:

- **build** — capability is core to differentiation, depth is expert, no
  reasonable buy/partner alternative within the blast radius.
- **buy** — mature commoditized solution exists, internal opportunity cost >
  license cost.
- **hire** — capability requires durable human judgment, not automation;
  pattern keeps reappearing because no human has authority to decide.
- **partner** — capability is adjacent (not core); a partner already excels.

This is the most strategic output of the loop: it tells you *which tool to
build next*, with explicit rationale rooted in repeated real-world
corrections.

---

## Step 6 — Approve (you)

The only mandatory human gate. Recommendations may be:
- **Approved** → Step 7
- **Modified** → revised recommendation document; back to you
- **Rejected** → kept for audit (not deleted); pattern stays `open`

Authorship metadata records who approved and when.

---

## Step 7 — Apply Fix

Depending on `fix_action_type`:
- `prompt_patch` → edit prompts; bump `prompt_version`
- `intent_revision` → update the relevant intent.yaml; bump version; re-run `ivd_validate`
- `capability_addition` → execute the build/buy/hire/partner sub-workflow
- `domain_reassessment` → rewrite the baseline; re-scope or retire patterns

If `draft_recipe_yaml` was attached, you refine it and saves to
`ivd/recipes/`. The recipe library is how patterns escape the project they
were learned in.

---

## Step 8 — Inject Context

`ivd_judgment_inject_context(domain, agent_class)` returns a structured
context block that downstream agents prepend to their input. The injector
prioritizes by signal strength:

1. **Distilled patterns** (≥ 3 members, fresh or aging) — highest signal
2. **Recent codified corrections** in the same domain (last 3–5 resolved entries)
3. **What Works layer** — corroborated comparison-pair hypotheses, presented
   as **generative guidance** ("when X, prefer Y") rather than failure
   avoidance ("don't do X").

### What Works Layer

Most feedback loops surface only failure modes ("avoid X"). The Judgment
phase intentionally surfaces *positive* guidance derived from corroborated
comparison pairs — because preventing failure is necessary but not
sufficient. Compounding requires the system to learn what *works*, not just
what doesn't.

Only `injection_status: corroborated` hypotheses reach this layer. Plausible
single-pair hypotheses are intentionally withheld.

### Injection budget

The injector enforces a token budget (configurable, default 1500 tokens).
Patterns are added in priority order until the budget is exhausted; the
remainder are summarized as a count ("+ 7 additional patterns omitted for
budget").

---

## Step 9 — Resolve / Archive

When a recommendation is applied:
- All member ledger entries transition `pattern-member → resolved`
- `resolved_by_recommendation_id` and `resolved_at` are set
- The pattern transitions `open → addressed`

After 90 days resolved (configurable), entries transition `resolved →
archived` and stop being injected. The pattern remains visible but is no
longer surfaced in routine context.

If a `addressed` pattern accumulates new members, it transitions to
`re-emerged`, signaling the prior fix did not hold and a deeper recommendation
is needed.

---

## Expert Intuition Principle

your judgment is the highest-bandwidth signal the loop has — but only in
domains where you have expert depth. The depth ladder:

| depth | meaning | weight |
|---|---|---|
| expert | you built the field, can identify subtle regressions cold | 1.0 |
| practitioner | you ships in this domain weekly | 0.7 |
| adjacent | you are fluent but not authoritative | 0.4 |
| novice | you can spot obvious wrongs only | 0.2 |

Erik (and any other AI reviewer) is **not a quality judge**; they are
**structural conformance checkers**. Their corrections enter the ledger as
`source: runtime` (not `leo`) and are not weighted by `leo_domain_depth`.

This separation matters: pattern detection works because expert depth amplifies
weak signals into reliable ones. Treating an AI reviewer's structural complaint
as if it were your expert intuition would dilute the entire ledger.

---

## Schema Authority

| Artifact | Template (canonical) | Recipe |
|---|---|---|
| Baseline | `ivd/templates/baseline.yaml` | — |
| Ledger entry | `ivd/templates/ledger-entry.yaml` | `ivd/recipes/capture-correction.yaml` |
| Comparison pair | `ivd/templates/comparison-pair.yaml` | `ivd/recipes/comparison-pair.yaml` |
| Pattern | `ivd/templates/pattern.yaml` | `ivd/recipes/distill-pattern.yaml` |

`ivd_validate` knows these `artifact_type` values:
`ledger_entry`, `comparison_pair`, `pattern`, `baseline`.

---

## Activation: The `.judgment/` Folder Gate

The Judgment phase is **dormant by default**. All eight `ivd_judgment_*` tools
return a "judgment phase not initialized" error unless the project root contains
a `.judgment/` folder with this layout:

```
<project_root>/.judgment/
├── baselines/        # one per domain
├── ledger/           # ledger entries (raw, codified, paired, pattern-member, resolved, archived)
├── patterns/         # detected patterns
├── recommendations/  # drafted + approved recommendations
└── config.yaml       # injection budget, freshness defaults, weights
```

Bootstrap: `ivd_judgment_init(project_root, domains=[...])` creates the
folder, scaffolds one stub baseline per domain, and writes a default
`config.yaml`.

The opt-in design is deliberate: most projects do not need a Judgment phase
on day one. Forcing it everywhere would dilute the rest of IVD.

---

## Tool Surface (9 tools)

| Tool | Purpose |
|---|---|
| `ivd_judgment_init` | Bootstrap `.judgment/` skeleton + per-domain baselines |
| `ivd_judgment_capture` | Write a raw ledger entry |
| `ivd_judgment_codify` | Return a structured codify prompt for the agent |
| `ivd_judgment_save_codified` | Persist the agent's filled codify fields |
| `ivd_judgment_pair` | Capture a comparison_pair entry |
| `ivd_judgment_detect_patterns` | Scan ledger; create/update patterns |
| `ivd_judgment_inject_context` | Return prioritized context block for downstream agents |
| `ivd_judgment_propose_recommendation` | Draft a recommendation against a pattern |
| `ivd_judgment_check_installed` | Workspace/project activation visibility (read-only; v3.1, R6) |

All 9 are gated by the `.judgment/` folder check (per-project) AND by the
server-level `IVD_JUDGMENT_TOOLS_ENABLED=false` opt-out (mirrors Canon's
`IVD_CANON_TOOLS_ENABLED`; tools remain registered when disabled, returning
an `enabled=false` payload, so the MCP catalog stays ABI-stable). Implementation:
`mcp_server/tools/judgment.py` is a thin facade; substance lives in the
vendored `ivd/judgment/` engine package (schema, store, freshness, detect,
inject, validate). Registered in `mcp_server/registry.py`.

### Engine package (v3.1)

```
ivd/judgment/
  __init__.py          → re-exports the public API
  schema.py            → @dataclass artifacts (LedgerEntry, ComparisonPair,
                         Pattern, Baseline, Recommendation, InjectionResult,
                         …) with to_dict / from_dict round-trips. Also
                         enums (LedgerState, FixActionType, …) so the
                         template, validator, and runtime cannot drift.
  store.py             → JudgmentStore: every filesystem op for .judgment/
  freshness.py         → freshness_for(age, half_life) + age_days(iso)
  detect.py            → detect_patterns(store, …) — clusters codified
                         entries; stamps engine_version + detection_hash
                         on each Pattern (R3, borrowed from Canon's
                         AuditReport.hash).
  inject.py            → inject_context(store, …) — 3-layer payload with
                         engine_version + injection_hash.
  validate.py          → validate_baseline / _ledger_entry / _comparison_pair
                         / _pattern (pure; called by ivd_validate).
```

Architectural pattern mirror-for-mirror with `ivd/canon/` (Canon engine
added in v3.1). Both packages ship engine_version + reproducible hashes on
their primary outputs and expose typed @dataclass schemas as the single
source of truth.

---

## Cross-References

- IVD principles 1–9: `framework.md` § Core Principles
- Master intent (where Principle 9 lives): `ivd_system_intent.yaml`
- Decision record (why bundle into IVD, why v3.0 bump): `DECISIONS.md` ADR-015, ADR-016
- Cookbook chapter "Closing the Loop with Judgment": `cookbook.md`
- Quick reference card: `cheatsheet.md` § Judgment Phase
- Strategic foundation (private): `_private/research/the_judgment_layer_thesis.md`
- Book chapter (private): `_private/book/manuscript/part-3-validation/chapter-17-judgment-loop/`
- Original framework essay (proto-form): `limitless/frameworks/Judgment_Feedback_Loop_Framework.md` *(superseded — header redirect)*

---

## Changelog

- **v1.0** (2026-03-21) — Initial canonical version. Promotes the Judgment Feedback Loop
  framework from `limitless/` to operational IVD canon. Establishes Principle 9, the
  4th IVD phase, the 8 MCP tools, the 4 templates, the 3 recipes, and the `.judgment/`
  activation gate. See `DECISIONS.md` ADR-015 (bundling) and ADR-016 (v3.0 bump).
- **v1.1** (IVD v3.1) — Architectural refactor inspired by Canon (v3.1).
  Extracts `ivd/judgment/` engine package (schema, store, freshness, detect, inject,
  validate); rewrites `mcp_server/tools/judgment.py` as a thin facade. Adds
  typed `@dataclass` schemas for every artifact (`Pattern`, `LedgerEntry`,
  `ComparisonPair`, `Baseline`, `Recommendation`, `InjectionResult`); adds
  `engine_version` + reproducible `detection_hash` / `injection_hash` to
  primary outputs (R3); adds server-level opt-out via
  `IVD_JUDGMENT_TOOLS_ENABLED=false` (R4); adds the 9th tool
  `ivd_judgment_check_installed` for workspace-level visibility (R6,
  read-only). Adds `mcp_server/tests/unit/test_judgment.py` with 53 tests
  across 11 classes (R5). No on-disk schema or wire-protocol changes —
  every existing `.judgment/` folder continues to work.
