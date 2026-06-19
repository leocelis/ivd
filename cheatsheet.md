# Intent-Verified Development: Cheat Sheet

**The Framework for the AI Agents Era (v3.1)**

**Core Insight:** The AI writes the intent, implements against it, verifies—so hallucinations are caught and turns drop to one.

**Scope:** Any AI-produced artifact (code, architecture, docs, research, books, processes)—if AI produces it, it needs paired intent.

**Feature inventory (large projects):** Optional `metadata` on intents (`feature_id`, `category`, `tags`, `status`) lets you derive a feature list and avoid duplication. Use the feature-list tool to see what exists before building. No separate inventory file—inventory is derived from intents.

**Existing projects (brownfield):** Use `ivd init` to create system intent with project context (code rules, architecture, tools, "map to the stars"). Then `ivd_assess_coverage` to see which modules have intents and which don't (prioritized). Child intents reference `parent_intent` to inherit conventions.

**Assess Coverage:**

```
ivd_assess_coverage(project_root="/path/to/your/project")
```

Returns: covered modules, uncovered modules (prioritized: high/medium/low), coverage %, and suggestions. Use the report to decide where to add intents first. **Coverage ≠ 100%** — intent belongs where it adds value (critical paths, complex logic, team boundaries), not on every file.

> **📋 Extending IVD?** See `ivd_system_intent.yaml` for rules on adding new patterns

---

## Part 1: The Golden Rules

*The core pain points of the AI Agents era—and how IVD solves them*

### Rule 0: THE AI WRITES THE INTENT (NEW)

**The breakthrough:** You describe what you want. The AI writes structured intent. The AI implements. The AI verifies.

```
WRONG:  You write PRD/user story/prompt → AI reads and guesses → Many turns
RIGHT:  You describe → AI writes intent → AI implements → AI verifies → Done first try
```

**Why this matters:**
- Traditional artifacts (PRDs, user stories, prompts) are prose—AI guesses
- Structured intent is verifiable—AI writes, verifies, self-corrects
- Clarification at intent stage, not after code

---

### Rule 1: SOLVE MANY-TURNS AND HALLUCINATIONS

**The expensive lesson:** AI fills gaps with plausible but wrong assumptions (hallucinations). You correct. Repeat. Many turns.

```
WRONG:  Prompt → Wrong → Correct → Wrong → Correct → (exhaustion)
RIGHT:  Describe → AI writes intent → Review → AI implements → AI verifies → Done
```

**The rule:** If you're correcting AI output more than once, the intent wasn't structured and verifiable.

| Problem | Cause | IVD Solution |
|---------|-------|--------------|
| Many turns | No verifiable intent | AI writes structured intent with constraints |
| Hallucinations | AI fills gaps | AI verifies against constraints, catches itself |
| Exhaustion | Back-and-forth | Clarification at intent stage, not after code |

**Early Signal: Linguistic Mirroring**

Before formal tests, check: Does the AI echo your key terms?

| Your request | AI response | Signal |
|--------------|-------------|--------|
| "admin compliance CSV export" | "admin compliance CSV export..." | ✅ Aligned |
| "admin compliance CSV export" | "data dump for users..." | ❌ Misaligned—clarify |

**Action:** If AI substitutes your terms, clarify before proceeding.

---

### Rule 2: SPECIFIC, NOT GENERAL

**The expensive lesson:** General AI implementations fail. Specific ones succeed.

```
WRONG:  "Check if this fact is accurate"
RIGHT:  "Check if this GAMING fact is accurate against GAMING sources"
```

**The rule:** If your prompt doesn't name the INDUSTRY and USE CASE, it's too general.

---

### Rule 3: INTENT FIRST, CODE LAST

**The expensive lesson:** Going straight from prompt to code causes many turns.

```
WRONG:  Prompt → Code → Hope it works
RIGHT:  Describe → AI writes intent → Review → AI implements → AI verifies
```

**The flow:** Human describes → AI writes intent → Human reviews → AI implements → AI verifies

---

### Rule 4: WHEN USER LACKS KNOWLEDGE, TEACH FIRST

**When:** User says "I don't know what X is" or can't understand concepts in intent.

**Do:** AI creates educational artifact (e.g. `ivd_teach_concept(concept="ETL")`) explaining concept, tradeoffs, verification; user confirms understanding; then standard flow. Recipe: `teaching-before-intent.yaml`.

---

### Rule 5: WHEN USER CAN'T DESCRIBE, RUN DISCOVERY FIRST

**When:** User says "I'm not sure what we need" or is new to the domain/codebase (but understands concepts).

**Do:** *(Experimental)* AI proposes 2–3 candidate goals or patterns (e.g. `ivd_discover_goal`, list recipes); user picks or refines; then standard intent flow. Recipe: `discovery-before-intent.yaml`.

---

## Part 1.5: Existing Projects (Brownfield)

*How to adopt IVD in a project that already has code and docs*

### Bootstrap with ivd_init

```bash
# Create system intent with project context
ivd init --project-root /path/to/your/project

# Auto-scans and captures:
# - Code rules (.cursorrules, lint configs)
# - Architecture (ARCHITECTURE.md, ADRs, principles)
# - Tools/scripts (key scripts, CLIs)
# - Libraries to reuse (internal shared libs)
# - Key paths ("map to the stars": entrypoints, modules, workflows, docs, tests)
# - Existing docs (README, API.md, CONTRIBUTING)
```

### Project Context = "Map to the Stars"

**System intent captures project-wide context so child intents reuse it:**

- **Code rules:** Follow .cursorrules, lint/format configs
- **Architecture:** Apply design principles, patterns from ARCHITECTURE.md/ADRs
- **Tools/scripts:** Reference existing scripts instead of duplicating
- **Libraries:** Reuse internal shared libs (e.g. internal/logging, internal/auth_utils)
- **Key paths:** Navigate via entrypoints, modules, workflows, docs, tests
- **Existing docs:** Link to current API docs, runbooks, contributing guides

### Child Intents Reference Parent

```yaml
# agent/lead_scorer/scorer_intent.yaml
parent_intent: "../../system_intent.yaml"

# AI loads project context from parent:
# - Follows code rules
# - Applies architecture principles
# - Reuses tools/scripts/libraries
# - Navigates via key_paths
```

**The AI workflow:** When creating/modifying a child intent, AI reads parent_intent → loads project_context → follows conventions.

---

## Part 2: The IVD Principles

*The methodology that makes understanding durable*

### Principle 1: Intent is Primary

**Not code. Not documentation. Intent.**

- Code without intent is meaningless
- Documentation without intent is disconnected  
- Intent survives rewrites, team changes, technology shifts
- **Docs as derived artifacts** (READMEs explaining code): reference in the code intent's `implementation.documentation`
- **Docs as primary artifacts** (runbooks, specs, guides): create a dedicated `_intent.yaml` alongside them

---

### Principle 2: Understanding Must Be Executable

**Prose can be wrong silently. Executable understanding fails loudly.**

```yaml
# Don't just write: "precision should be high"
# Write:
constraints:
  - requirement: "precision >= 0.80"
    test: "tests/test_scoring.py::test_precision"
```

**Constraint quality** — not all constraints are equal:
- **Near-zero entropy** ✅: binary, measurable — `p95 < 200ms, test: tests/perf/latency.py`
- **Low-qualitative** ✅: qualitative but decomposed — `tone: melancholic; no resolution in final paragraph`
- **High-entropy** ❌ REJECTED: `"write well"`, `"be creative"` — triggers parametric averaging (homogenization)

**Satisfiability**: check constraint sets for internal conflicts before implementing. List the most critical constraint **last** to counter position bias (LLMs attend strongest to the end).

---

### Principle 3: Bidirectional Synchronization

**Change flows in ANY direction, with verification.**

```
Code changes → Intent must update
Intent changes → Code must update
System detects drift and forces alignment
```

**Example:** Threshold changes from 0.70 to 0.75?  
System asks: "Update intent? Or revert code?"

**Empirical Refinement** *(canonical extension)*: When implementation reveals that intent assumptions are wrong (API returns a different format, latency exceeds documented limits), use the 5-step protocol: STOP → RECORD what was assumed vs. observed → UPDATE the intent on disk → ENRICH with external context → CONTINUE from corrected intent. Source hierarchy for code failures: (1) actual error message, (2) GitHub issues/PRs matching the error, (3) library changelogs, (4) official docs, (5) model's parametric knowledge. **2-attempt rule**: same error twice without new external data = mandatory ENRICH before retrying.

---

### Principle 4: Continuous Verification

**Not "document once and forget." Verify every PR, every deploy.**

```
✓ Code threshold matches intent?
✓ Tests verify constraints?
✓ Evidence (notebooks) still runs?
✓ Documentation is synced?
```

---

### Principle 5: Layered Understanding

**Not just "WHY" - multiple verifiable layers:**

```
Intent → Constraints → Rationale → Alternatives → Risks
(goal)   (must hold)   (evidence)   (rejected)     (monitoring)
```

Each layer is executable, not just readable.

---

### Principle 6: AI as Understanding Partner

**AI writes the intent, implements against it, verifies.**

**The complete workflow:**
```
1. You describe    → natural language
2. AI writes       → structured intent (YAML, constraints, tests)
3. You review      → "Is this what I meant?"
4. AI stress-tests → 4 probes: constraint completeness, implementation gaps,
                     implicit assumptions, constraint satisfiability
5. AI implements   → constraint-segmented (3+ constraints):
                     GROUP by area → IMPLEMENT segment →
                     RE-READ constraints from disk → VERIFY → next segment
6. AI verifies     → full cross-cutting sweep
```

**Why step 5 matters**: LLMs exhibit a read-acknowledge-violate pattern — can recite all constraints then miss them in generation. Step 5 counters this by resetting attention per segment.

**Teaching:** If the user lacks technical knowledge → `ivd_teach_concept(concept="ETL")` → user understands → then proceed. Recipe: `teaching-before-intent.yaml`.

**Discovery:** *(Experimental)* If the user can't describe yet → `ivd_discover_goal` → user picks → AI writes intent. Recipe: `discovery-before-intent.yaml`.

**Multi-Agent Systems:**

```
Human → Coordinator Intent → Agent 1 Intent → Agent 1 verifies
                          → Agent 2 Intent → Agent 2 verifies
                          → Coordinator synthesizes
```

**Rule:** Coordinator writes intent for each agent it delegates to.
**Core principle:** Tools are truth, history is context.
**Recipe:** `recipes/coordinator-intent-propagation.yaml`

---

### Principle 7: Understanding Survives Implementation

**Implementation is temporary. Intent is permanent.**

When you rewrite in Go, or replace with a vendor service, the intent artifact transfers. The WHY persists even when the HOW changes completely.

---

### Principle 8: Innovation through Inversion

**State the default, invert it, evaluate, implement.**

- **Use when:** Designing (new or major intent); problem has a conventional approach; you care about perf/scale/security/maintainability.
- **Skip when:** Small fix (bug, config, refactor); no clear default; obvious solution is good enough.

```yaml
# Optional in intent: inversion_opportunities
# problem, dominant_belief, proposed_inversions (name, description, rationale, status: chosen|rejected|deferred)
# Use ivd_propose_inversions tool to scaffold; then document chosen/rejected in intent.
```

---

### Principle 9: Judgment Compounds *(NEW in v3.0)*

**Corrections from real-world use, captured and structured, compound into the only knowledge that doesn't commoditize when the model layer commoditizes.**

- **Use when:** Project has shipped at least one workflow to a real audience and corrections recur across runs.
- **Skip when:** Single-shot scripts, experiments, or projects where corrections won't recur.
- **Activation:** Opt-in per project via the `.judgment/` folder at the project root.

The 4th IVD phase. Detailed cheatsheet card below in [Part 2.5](#part-25-the-judgment-phase-quick-card-v30).

---

### IVD Agent Rules

Embed IVD verification discipline directly in your agent instruction file (`.cursorrules`, `.clinerules`, Copilot system prompt, etc):

```
Recipe: recipes/agent-rules-ivd.yaml
Tool:   ivd_load_recipe(recipe_name="agent-rules-ivd")
```

**Six rules agents enforce automatically:**
- **Rule 1** — Intent before implementation; constraint-segmented for 3+ constraints
- **Rule 2** — Post-implementation verification protocol (4-step audit)
- **Rule 3** — Every constraint must have a `test` field
- **Rule 4** — Stress-test intent before implementing (4 probes)
- **Rule 5** — Empirical refinement: STOP→RECORD→UPDATE→ENRICH→CONTINUE when implementation reveals wrong assumptions; 2-attempt trigger for external enrichment
- **Rule 6** — Constraint quality: reject high-entropy constraints; check satisfiability

---

## Part 2.5: The Judgment Phase Quick Card (v3.0)

*The 4th IVD phase. Dormant unless `<project_root>/.judgment/` exists.*

> **New to Judgment?** Read [`judgment_explained.md`](judgment_explained.md)
> first for the plain-English "what problem it solves and how" intro,
> then come back here for the 10-step loop and tool reference.

### The 10-Step Loop

```
0. Baseline & Goal Calibration
1. Capture (raw correction, < 30s)
2. Codify (5 structured fields)
3. Pair (optional comparison_pair entry)
4. Detect Patterns (3+ entries with shared diagnosed_cause)
5. Propose Recommendation (with build|buy|hire|partner sub-types)
6. Approve (you — only mandatory human gate)
7. Apply Fix
8. Inject Context (next runs)
9. Resolve / Archive
```

### The 5 Codified Fields (Step 2)

| Field | What |
|---|---|
| `expected_result` | What should have happened |
| `detected_via` | How was it caught (review / test / audience / runtime) |
| `diagnosed_cause` | Root cause hypothesis |
| `proposed_fix` | Specific, actionable |
| `fix_action_type` | `prompt_patch` / `intent_revision` / `capability_addition` / `domain_reassessment` |

### Pattern Confidence Weighting (`domain_depth`)

| Depth | Weight | Meaning |
|---|---|---|
| expert | 1.0 | Built the field; can identify subtle regressions cold |
| practitioner | 0.7 | Ships in this domain weekly |
| adjacent | 0.4 | Fluent but not authoritative |
| novice | 0.2 | Spots obvious wrongs only |

AI reviewers enter as `source: runtime` — **not** weighted by `domain_depth`. They're structural conformance checkers, not quality judges.

### Pattern Freshness

| State | Rule | Injectable? |
|---|---|---|
| `fresh` | age ≤ half_life | yes |
| `aging` | half_life < age ≤ 2× | yes |
| `stale` | 2× < age ≤ 3× | flagged |
| `expired` | age > 3× | **no** |

### Comparison Pair Discipline (Pearl Rung-1)

- Always list ≥ 1 `competing_hypothesis`
- Single pair → `injection_status: plausible`
- 2+ independent pairs (different author/week/model) → `corroborated`
- Only `corroborated` enters the **What Works** injection layer

### The 9 Tools (Dormant unless `.judgment/` exists)

| Tool | Purpose |
|---|---|
| `ivd_judgment_init` | Bootstrap `.judgment/` + per-domain baselines |
| `ivd_judgment_capture` | Write a raw ledger entry |
| `ivd_judgment_codify` | Return structured codify prompt |
| `ivd_judgment_save_codified` | Persist agent's filled codify fields |
| `ivd_judgment_pair` | Capture a comparison_pair entry |
| `ivd_judgment_detect_patterns` | Cluster ledger into patterns |
| `ivd_judgment_inject_context` | Prioritized context for downstream agents |
| `ivd_judgment_propose_recommendation` | Draft recommendation against a pattern |
| `ivd_judgment_check_installed` | Workspace/project activation visibility (read-only; v3.1) |

**Server-level opt-out:** set `IVD_JUDGMENT_TOOLS_ENABLED=false` to disable
all 9 tools without de-registering them (mirrors `IVD_CANON_TOOLS_ENABLED`).

### See it work (5-second runnable showcase)

```bash
python examples/judgment_demo/run_demo.py
```

Walks the full loop end-to-end (capture × 3 → codify × 3 → detect → inject) and writes 4 human-readable artifacts to `examples/judgment_demo/output/` showing the agent's system message before vs after Judgment compounds, plus a side-by-side LLM behavioral diff. Runs offline by default; set `OPENAI_API_KEY` for the live `gpt-4o-mini` call (~$0.001). Full narrative + verdict: [`examples/judgment_demo/README.md`](examples/judgment_demo/README.md).

### Capability Addition Sub-types

| Sub-type | When |
|---|---|
| **build** | Core to differentiation; depth is expert; no buy/partner alternative |
| **buy** | Mature commoditized solution; opportunity cost > license cost |
| **hire** | Capability requires durable human judgment, not automation |
| **partner** | Adjacent capability; partner already excels |

### Templates

`templates/baseline.yaml` · `templates/ledger-entry.yaml` · `templates/comparison-pair.yaml` · `templates/pattern.yaml`

### Recipes

`recipes/capture-correction.yaml` · `recipes/comparison-pair.yaml` · `recipes/distill-pattern.yaml`

### Validator artifact_types (`ivd_validate`)

`ledger_entry` · `comparison_pair` · `pattern` · `baseline`

Full canonical doc: [`judgment_layer.md`](judgment_layer.md). Decision records: `DECISIONS.md` FDR-015, FDR-016.

---

### Recipes and Reusable Patterns (v1.1+)

**Recipes capture how to solve common problems.**

- **Recipe** = Reusable pattern (how to build similar things)
- **Intent Artifact** = Specific implementation (what we built)

```yaml
# Recipe (reusable): agent-classifier.yaml
# Intent (specific): lead_scorer_intent.yaml → uses recipe, fills in specifics
```

---

## The Complete Flow

```
┌─────────────────────────────────────────────────────────┐
│  GOLDEN RULES              →    IVD METHODOLOGY         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Be SPECIFIC            →    Define clear INTENT     │
│     (industry, use case)        (goal, constraints)     │
│                                                         │
│  2. INTENT before CODE     →    DOCUMENT the WHY        │
│                                 (rationale, evidence)   │
│                                                         │
│                            →    Write CLEAN CODE        │
│                                 (references intent)     │
│                                                         │
│                            →    VERIFY continuously     │
│                                 (system checks match)   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Checklist

### Before ANY AI Implementation:

- [ ] **SPECIFIC:** Industry and use case named?
- [ ] **INTENT:** Written down (not just in your head)?
- [ ] **DOCUMENTED:** WHY captured with evidence?
- [ ] **CONSTRAINTS:** What must hold true (testable)?
- [ ] **VERIFIABLE:** Can system check alignment?

---

## Anti-Patterns (Expensive Mistakes)

| Mistake | Cost | Fix |
|---------|------|-----|
| "Works for everything" prompts | Low accuracy | Narrow to specific domain |
| Skipping intent documentation | Knowledge lost | Write intent BEFORE code |
| General-purpose AI agents | Unpredictable | One agent, one specific job |
| Code without context | Unmaintainable | Link every file to intent |
| No verification | Silent drift | Check alignment continuously |
| Intent for every README | Overhead, no value | Only primary docs (guides, runbooks, specs) get intents; derived docs reference the code intent |

---

## The Formula

```
SPECIFIC INTENT + DOCUMENTED RATIONALE + CLEAN CODE + CONTINUOUS VERIFICATION = SUCCESS
```

---

## Remember

**Golden Rules (What):**
1. Be specific, not general
2. Intent first, code last

**IVD Principles (How):**
1. Intent is primary
2. Understanding is executable (constraint quality: entropy spectrum + satisfiability)
3. Bidirectional synchronization (empirical refinement + source hierarchy)
4. Continuous verification (post-implementation protocol: re-read → diff → check tests → report)
5. Layered understanding
6. AI as understanding partner (stress-test → constraint-segmented implement → verify)
7. Understanding survives implementation
8. Innovation through inversion

---

## The One-Liner

> **AI writes intent, implements against it, verifies—so hallucinations are caught and turns drop to one.**

---

## Artifact Placement Quick Reference

| Level | Recommended Location | Example |
|-------|---------------------|---------|
| System | Root: `system_intent.yaml` | `system_intent.yaml` or `{project}_system_intent.yaml` |
| Workflow | `workflows/{name}_intent.yaml` or alongside coordinator when single-orchestrator | `workflows/lead_qualification_intent.yaml` |
| Module | `{module}/{module}_intent.yaml` | `agent/marketing/marketing_intent.yaml` |
| Task | `{module}/intents/{task}_intent.yaml` | `agent/marketing/intents/gen_article_intent.yaml` |
| Variant | `{variant}_{module}_intent.yaml` | `erik_reviewer_intent.yaml` |
| Documentation | `docs/{area}/{name}_intent.yaml` alongside the `.md` | `docs/operations/runbook_intent.yaml` |

**AI Agent Discovery:**
```bash
# Find all intents
find . -name "*_intent.yaml" ! -path "*/framework/*"

# Find workflow intents
ls workflows/*_intent.yaml

# Find task-level intents
find . -path "*/intents/*_intent.yaml"
```

---

## Key References

- **`ivd_system_intent.yaml`** - System intent defining all rules for extending IVD
- **`README.md`** - Quick start guide
- **`cookbook.md`** - Practical implementation guide  
- **`framework.md`** - Complete IVD specification
- **`judgment_layer.md`** - Judgment phase (4th phase, v3.0)
- **`templates/intent_levels_guide.md`** - When to use which intent level
- **`recipes/`** - Reusable pattern templates
- **`DECISIONS.md`** - Architectural Decision Records (ADRs)

---

*"In the AI Agents era, the AI writes the intent, implements against it, and catches its own hallucinations."*
