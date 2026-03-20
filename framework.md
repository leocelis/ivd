# Intent-Verified Development (IVD): The Framework for the AI Agents Era

**Purpose:** AI writes intent, implements against it, verifies—for code, docs, architecture, research, and any AI-produced artifact  
**Status:** Production Ready  
**Version:** 2.4  
**Created:** January 23, 2026  
**Updated:** March 19, 2026 (Constraint-Segmented Implementation, FDR-014; constraint quality framework; source hierarchy; cognitive foundation)

> **📋 Framework Evolution Rules:** See `ivd_system_intent.yaml` for the canonical reference on how to extend IVD. All additions to the framework must follow the 8 principles, 4 validation levels, and 6-step canonization process defined in the system intent.

---

## Table of Contents

1. [The Evolution](#the-evolution)
2. [Core Principles](#core-principles)
3. [Intent Artifacts](#intent-artifacts)
4. [Feature Inventory (Large Projects)](#feature-inventory-large-projects)
5. [Intent Coverage Assessment](#intent-coverage-assessment)
6. [Recipes (NEW in v1.1)](#recipes-reusable-patterns)
7. [Verification System](#verification-system)
8. [Implementation Guide](#implementation-guide)
9. [Real-World Example](#real-world-example)
10. [Comparison Matrix](#comparison-matrix)
11. [Extending IVD Framework](#extending-ivd-framework)

---

## The Evolution

### From Traditional to IVD

**Traditional Development:**
```
Human writes requirements (PRD, user story) → Human developer implements
```
*Worked when humans asked clarifying questions. AI doesn't ask—it guesses.*

**Literate Programming (Knuth, 1984):**
```
Write explanation → Write code matching it → Tools verify format
```
*Beautiful for human readers. AI cannot verify prose.*

**AI-Assisted Development (Current Default):**
```
Human writes prompt → AI guesses intent → Builds wrong → Many turns of correction
```
*The many-turns and hallucinations problem.*

**Intent-Verified Development (AI Agents Era):**
```
Human describes → AI writes intent → Human reviews → AI stress-tests → AI implements → AI verifies → Done first try
```
*The AI writes the intent, implements against it, catches its own hallucinations.*

### Why This Works: The Cognitive Architecture of LLMs

IVD works not just because structured artifacts are "better" — it works because of how LLMs process information at a fundamental level.

LLMs have two distinct knowledge systems. **Parametric knowledge** is encoded in the model's weights during training — generalized, frozen, and shared across all users and tasks. **Contextual knowledge** is what's in the current prompt and context window — specific, current, and fully controllable. Research across nine LLMs found that models allocate approximately **70% reliance on contextual knowledge and 30% on parametric knowledge** when generating responses, regardless of context size.

When you give an AI agent vague prose (a PRD, a user story, a natural-language prompt), the contextual channel is underloaded. The model compensates by filling gaps from parametric memory — which encodes averaged patterns from training data, not your specific constraints. That gap-filling produces two distinct failure modes: **hallucination** (factually wrong output) and **homogenization** (factually acceptable but generically averaged output). For code, homogenization is largely invisible — correct code is correct code. For creative work, documentation, marketing copy, and narrative artifacts, homogenization is the primary failure mode: the output isn't wrong, it's indistinguishable from every other LLM output on the same prompt. The problem is not the AI. The problem is that prose doesn't load the contextual channel with enough specificity to prevent parametric gap-filling.

A structured intent artifact — with explicit constraints, test paths, scope boundaries, and rationale — saturates the contextual channel. A constraint like `p95 latency < 200ms` linked to `tests/perf/test_latency.py` has near-zero interpretive entropy. The model cannot guess; it can only match or fail. That is why executable understanding fails loudly.

**The lost-in-the-middle effect** explains why the verification protocol's Step 1 ("re-read the intent from disk") is not a best practice — it is a cognitive necessity. Research shows that LLMs degrade in accuracy for information positioned in the middle of long contexts, even in strong models. The effective context window can differ from the advertised limit by up to 99%. Re-reading the intent artifact before verification repositions the ground truth at the top of the context stack, where the attention mechanism weights it highest.

> **"Hallucinations aren't AI being wrong. They're AI using the wrong knowledge system — because you didn't feed the right one."**

### Why Company-Specific Knowledge Matters

The cognitive mechanism above explains *how* IVD works at the individual developer level. But the strategic implication is larger.

Every company has knowledge that does not exist in any LLM's parametric channel — and never will. Your business rules, your architecture decisions, your compliance requirements, your domain expertise, your internal APIs. This knowledge is **inherently contextual**: it can only enter through the context window. There is no other path.

Generic AI tools — Copilot without project context, ChatGPT with a pasted prompt, Zapier automations, Notion AI — feed generic context. When company-specific gaps appear, the parametric channel fills them with averaged patterns from training data. The AI "knows" what a typical permission model looks like, not what *your* permission model requires. That delta between typical and yours is the hallucination.

**AI capability is commoditized.** Every team has access to the same models. The competitive advantage is not the model — it's whether you've structured your company's unique knowledge so the contextual channel is loaded with **your ground truth** instead of generic approximations. IVD is the framework for doing exactly that: `project_context` sections capture architecture and code rules, organizational recipe libraries encode institutional best practices, and intent artifacts encode the specific constraints and verification criteria that define your system.

Companies that structure their knowledge with IVD get AI that works with their reality. Companies that don't get AI that guesses — faster, but still wrong.

Of all company-specific knowledge, **process knowledge is the most operationally valuable**: your decision points, escalation criteria, approval chains, and compliance gates — the workflows that define how your company actually operates. Generic tools offer generic workflows. IVD's organizational recipe libraries encode your company's actual processes so AI agents execute your workflows correctly, not an averaged approximation of how things "typically" work.

This has a deeper implication for how software is built and bought. Enterprise software has been stuck in a false dichotomy for decades: too rigid (the tool doesn't fit your process) or too configurable (you need a specialist army to make it fit). Both options share the same root problem — software built with generic knowledge, with you paying the cost to inject YOUR knowledge after the fact. When business rules and processes are structured in intent artifacts, the **configuration layer collapses into the contextual knowledge layer.** AI builds software that's custom from day one. The Salesforce admin, the SAP consultant, the ServiceNow specialist — these roles exist because injecting company-specific knowledge into generic platforms is hard. When the knowledge is already structured, the injection cost approaches zero.

---

## Core Principles

### Principle 1: Intent is Primary

**Not code. Not documentation. Not prompts. Structured intent.**

```
HUMAN DESCRIBES (natural language)
    ↓
AI WRITES INTENT (structured YAML)
    ↓
┌───────────────────────────────────┐
│ AI Produces:                       │
│ • Implementation (code, docs, etc.)│
│ • Tests (verification)             │
│ • Documentation (explanation)      │
└───────────────────────────────────┘
    ↓
AI VERIFIES: Does output match intent constraints?
```

**Scope:** Code, architecture, documentation, research, books, processes—any AI-produced artifact.

**Why:**
- Prompts are informal—AI guesses, hallucinates
- PRDs/user stories are prose—AI reads and guesses
- Structured intent is verifiable—AI writes, implements, verifies

---

### Principle 2: Understanding Must Be Executable

**Prose documentation can be wrong. Executable understanding fails loudly.**

**Traditional:**
```python
def qualify_lead(score: float) -> bool:
    """Returns True if score >= 0.70"""
    return score >= 0.70
```

**Intent-Verified:**
```python
@intent("Qualify leads with score >= 0.70")
@constraint("precision >= 0.80")
@constraint("recall >= 0.60")
@validates_with("tests/test_lead_qualification.py")
def qualify_lead(score: float) -> bool:
    return score >= 0.70
```

**The decorators are executable:**
- `@intent` declares what this should do
- `@constraint` declares what must hold true
- `@validates_with` links to tests that verify

**System can check:** Do tests verify the constraints? Does implementation match intent?

The code example above shows the canonical form for a technical constraint. But Principle 2 applies to every artifact type IVD covers — code, architecture, documentation, research, books, marketing copy. For non-technical artifacts, the form of an executable constraint differs. The next two subsections define how.

#### Constraint Quality: The Interpretive Entropy Spectrum

Not all constraints are equal in their verifiability. Constraints exist on a spectrum of **interpretive entropy** — how much interpretive space remains between the constraint and its verification.

**The spectrum (research grounding: CMU 2025 underspecification study; UltraBench 2025; DETAIL 2024):**

```
Near-zero entropy  ──────────────────────────────────────────────────  High entropy
│ p95 latency < 200ms          │ tone: melancholic             │ write well    │
│ precision >= 0.80            │ length: 1,200–1,400 words     │ be creative   │
│ test: tests/perf/latency.py  │ structure: three-act          │ sound natural │
└────────────────────────────  └──────────────────────────────  └──────────────┘
      Binary pass/fail              Qualitative + measurable        Pure prose
      Model cannot guess            Model can evaluate              Model averages
```

**Why entropy matters:** A constraint like `p95 latency < 200ms` has near-zero interpretive entropy — the model cannot guess; it can only match or fail. A constraint like "write well" has near-total entropy — the model fills it from parametric averaged patterns, producing output that is statistically indistinguishable from other LLM outputs (what research calls **creative homogenization**). The 2025 study "We're Different, We're the Same" found LLM outputs are significantly more similar to each other than human outputs are to each other, even across models from different organizations — direct evidence that high-entropy prompts trigger parametric averaging.

**Constraint design rules by artifact type:**

For **code and technical artifacts** — target near-zero entropy. Every constraint must be binary and testable:
```yaml
- name: "latency"
  requirement: "p95 < 200ms"
  test: "tests/perf/test_latency.py::test_p95"
  entropy: "near-zero"
```

For **creative, narrative, and documentary artifacts** — decompose into the lowest-entropy constraints you can construct. Qualitative constraints are acceptable when they include measurable proxies:
```yaml
- name: "tone"
  requirement: "melancholic but not sentimental — no emotional resolution in final paragraph; protagonist does not cry"
  test: "human review against checklist: does final paragraph resolve? does protagonist cry?"
  entropy: "low-qualitative"
  proxy_measurable: true

- name: "length"
  requirement: "1,200–1,400 words"
  test: "wc -w output | awk '$1 >= 1200 && $1 <= 1400'"
  entropy: "near-zero"

- name: "structure"
  requirement: "exactly three scenes, each set in a different room; no flashbacks"
  test: "human review: count scene breaks, verify settings, check for temporal reversals"
  entropy: "low-qualitative"
```

**The key insight for non-code artifacts:** Constraints that feel "creative" are often decomposable into near-zero-entropy sub-constraints. "Write a compelling story" is pure entropy. "1,400 words, three scenes, first person, present tense, melancholic protagonist, no dialogue in final scene" is six near-zero or low-qualitative constraints. The CS4 benchmark (2024) demonstrated this directly: increasing prompt constraint specificity measurably improves creative output quality and reduces reliance on parametric averaging.

#### Constraint Satisfiability: The Multi-Constraint Problem

A critical failure mode that IVD's original constraint model did not address: **constraints can conflict, and LLMs fail disproportionately when all constraints must be satisfied simultaneously.**

**Research grounding (UltraBench 2025, multi-dimensional constraint framework 2025):** Models exceed 70% accuracy on individual constraints but fail when satisfying all constraints at once. The UltraBench study found **position bias** — models prioritize constraints appearing later in the prompt list — causing earlier constraints to be silently violated. The CMU underspecification study found constraint sets where even explicit specification produced 20%+ accuracy drops from this interaction effect.

**This changes how intents must be written.** Before finalizing constraints, the stress test (Principle 6, Step 4) must now include a fourth probe:

**Probe 4 — Constraint conflict check:** "Do any two constraints in this intent conflict? Is it possible to satisfy all constraints simultaneously? Are any constraints likely to be violated due to position bias (appearing early in a long list while later constraints dominate)?"

**Practical rules:**
- **Conflict detection before implementation.** If two constraints can't both be satisfied — a length constraint of 500 words and a structural constraint requiring six detailed sections — the conflict must be resolved at the intent stage, not discovered after implementation.
- **Priority ordering.** When constraint conflicts are possible but not certain, declare a priority order explicitly in the intent. The model follows the priority when simultaneous satisfaction is impossible.
- **Position-aware ordering.** Critical constraints go last in the constraint list. Position bias is real: the model weights later constraints more heavily. If tone fidelity matters most, declare tone last.

```yaml
constraints:
  # Order: less critical first, most critical last (position-bias mitigation)
  - name: "word_count"
    requirement: "1,200–1,400 words"
    test: "wc -w"
    priority: 3

  - name: "structure"
    requirement: "three scenes, different rooms, no flashbacks"
    test: "human checklist"
    priority: 2

  - name: "tone"
    requirement: "melancholic, no resolution, no tears"
    test: "human checklist"
    priority: 1  # highest priority; declared last for position-bias

constraint_satisfiability:
  conflicts_checked: true
  known_tensions:
    - between: ["word_count", "structure"]
      resolution: "If three full scenes require > 1,400 words, reduce non-scene material (transitions, descriptions), not scenes"
  simultaneous_satisfaction: "All constraints satisfiable with known tensions resolved above"
```

---

### Principle 3: Bidirectional Synchronization

**One-way flow (Knuth):** Literate source → tangled code + woven docs

**Bidirectional (IVD):** Any change propagates to others, with verification

```
        INTENT
       ↗  ↑  ↖
      /   |   \
     ↓    |    ↓
  CODE ←→ | ←→ DOCS
     ↓    |    ↓
      \   |   /
       ↘  ↓  ↙
    VERIFICATION
```

**When threshold changes from 0.70 to 0.75:**
1. System detects: "Intent says 0.70, code now says 0.75"
2. System asks: "Update intent? Or revert code?"
3. If intent updates → Docs regenerate, tests rerun
4. If code reverts → Implementation restored to match intent

#### Empirical Refinement: When Implementation Reveals New Knowledge

Bidirectional sync handles *code drift* — you changed the code, now update the intent. But there is a second, equally important direction: **reality contradicts the intent's assumptions.**

This happens constantly during LLM workflow development. Your research says the model should return confidence scores between 0 and 1 — but the actual API returns logits. Your intent assumes p95 latency under 200ms — but the real service has a 500ms cold start. Your constraint says classification accuracy >= 85% — but empirical testing shows 72% on your actual data. The intent was written from research; reality is different.

This is not a code bug. This is new contextual knowledge that the intent didn't have at write time. The intent's assumptions were based on parametric-level information (general knowledge, documentation, research). Implementation revealed empirical evidence that changes what the intent should say.

**The Empirical Refinement Protocol:**

1. **STOP** — Do not continue implementing against a stale assumption. The intent is the contextual knowledge spine; if it's wrong, everything built on it will be wrong.
2. **RECORD** — Document the empirical finding: what the intent assumed vs. what you observed. This is new contextual knowledge.
3. **UPDATE** — Revise the intent artifact on disk: fix the constraint, adjust the threshold, add a new constraint for the discovered edge case, update the rationale with empirical evidence.
4. **ENRICH** — If the discovery reveals a knowledge gap, pull more contextual knowledge into the session. Not all sources are equal. Use the highest-signal source available for the problem type:

   **Source hierarchy for code failures (ranked by signal):**
   1. **The actual error message/stack trace** — empirical, specific, current; paste it into the context verbatim
   2. **GitHub issues and PRs matching the error** — maintainer-confirmed fixes, version-specific behavior, real workarounds from people who hit the exact same problem. This is the single highest-value enrichment channel for code failures — one issue thread can replace 5–10 correction turns because it injects *confirmed empirical knowledge* where the model only had *parametric approximations*
   3. **Library changelogs and release notes** — what changed between versions; explains breaking changes that documentation hasn't caught up to
   4. **Official documentation** — authoritative but often lags implementation; may describe the intended behavior rather than the actual behavior
   5. **The AI's parametric knowledge** — lowest signal; averaged, possibly stale, and already proven insufficient (you're in the ENRICH step because it failed)

   Iterating without enrichment — making repeated implementation attempts using only the model's parametric knowledge — is drawing from the same well that already produced the wrong answer. Each attempt is a parametric variation of the same incorrect pattern.

   **The 2-attempt trigger rule:** If the same error or failure pattern persists after two implementation attempts without new external data, STOP and ENRICH before attempting again. Two attempts establish that the parametric channel doesn't have the answer. Further attempts without new contextual knowledge are wasted turns.

5. **CONTINUE** — Re-read the updated intent (Verification Protocol Step 1) and continue implementing from the corrected version.

If the discovery changes the scope significantly (what was a simple API call now requires retry logic, circuit breakers, and fallback handling), flag for human review before continuing.

**Why this matters through the cognitive lens:** The intent artifact is the spine of contextual knowledge. When it contains assumptions instead of empirical facts, the model fills gaps between those assumptions and reality using parametric knowledge — exactly the gap-filling mechanism that causes hallucinations. Empirical refinement replaces assumptions with observed behavior, strengthening the contextual channel at the exact point where it was weakest. The source hierarchy exists because not all contextual knowledge is equal — a GitHub issue with a confirmed fix is higher signal than documentation that may not cover the edge case, which is higher signal than parametric recall that already failed.

**The stress test (Step 4) anticipates. Empirical refinement discovers.** Together, they close the loop: the stress test catches what you can reason about before building; empirical refinement catches what only running the code reveals.

---

### Principle 4: Continuous Understanding Verification

**Static docs become stale on day 2. Verify continuously.**

```bash
$ ivd verify lead_qualifier

Checking: agent/lead_qualifier/
✅ Intent artifact found: lead_qualifier_intent.yaml
✅ Implementation matches intent: threshold = 0.70
✅ Constraints satisfied:
   - precision = 0.85 (>= 0.80) ✓
   - recall = 0.70 (>= 0.60) ✓
✅ Evidence is current: playground/lead_analysis_2025-12.ipynb (recently run)
✅ Tests passing: 12/12 ✓
⚠️  Risk alert: precision at 0.82, approaching minimum threshold

UNDERSTANDING VERIFIED ✓
```

**Every PR, every deploy, every change:** Verify understanding still matches reality.

#### Post-Implementation Verification Protocol

Principle 4 says *verify continuously*, but what does that concretely mean for an AI agent that just implemented code from an intent artifact? The **Post-Implementation Verification Protocol** is the prescribed 4-step audit that every AI agent must execute after any implementation derived from an intent artifact:

1. **Re-read the literal intent** — Open and re-read the intent artifact from disk. Do not rely on memory or context from earlier in the conversation. The intent may have been updated, or the agent's memory may have drifted during a long session.

2. **Diff each change against constraints** — For every change made during implementation, check: does this change satisfy, violate, or not affect each constraint in the intent artifact? List each constraint and its status.

3. **Check verification criteria** — For each constraint that has a `test` field, verify: does the test path exist? Can the test be run? Does the implementation pass the test? If the test can't be run (e.g., manual review), note what a reviewer should check.

4. **Report results** — Produce a structured report: for each constraint, PASS / FAIL / NEEDS_REVIEW. Do not declare implementation complete until all constraints are PASS or explicitly acknowledged as NEEDS_REVIEW with justification.

**When constraint-segmented implementation (Step 5) was used:** The protocol functions as a cross-cutting final sweep. Per-constraint compliance was already established at the segment level during implementation. The sweep's value is catching inter-constraint gaps — situations where satisfying one segment's constraints introduced a violation in another.

**When single-pass implementation was used (1–2 constraints):** The protocol is the primary verification mechanism. Re-reading from disk (Step 1) is especially critical here — it counteracts the lost-in-the-middle effect by repositioning intent at the top of the attention window.

Without this protocol, the IVD loop is broken: Intent exists → Implementation exists → But no verification connects them. The intent becomes decoration, not a contract.

See: `recipes/agent-rules-ivd.yaml` for the concrete agent instruction rules that enforce this protocol in `.cursorrules`, `.clinerules`, Copilot instructions, or any AI agent configuration file.

---

### Principle 5: Layered Understanding

**Not just "WHY" - multiple layers, each verifiable:**

```
Layer 1: INTENT
"Qualify high-probability leads for sales team"
→ Executable as: acceptance criteria, business metrics

Layer 2: CONSTRAINTS  
"Must maintain precision >= 0.80 and recall >= 0.60"
→ Executable as: property-based tests, invariants

Layer 3: RATIONALE
"0.70 threshold chosen based on Dec 2025 experiment"
→ Executable as: link to notebook that can be re-run

Layer 4: ALTERNATIVES
"Considered 0.60 (rejected: too many false positives) and 0.80 (rejected: insufficient volume)"
→ Executable as: comparison experiments still runnable

Layer 5: RISKS
"If precision drops below 0.75, sales quality suffers"
→ Executable as: monitoring alerts, rollback triggers
```

**Each layer is verifiable, not just readable.**

---

### Principle 6: AI as Understanding Partner

**The AI writes the intent, implements against it, and verifies—not just syncs.**

This is the key principle for the AI Agents era:

```
You: "Add export to CSV for admin compliance reporting"

AI: "I'll write the intent artifact first."
    [Writes structured YAML with constraints and tests]
    
AI: "Here's the intent I wrote:
     - Summary: Export user data to CSV for admin compliance
     - Constraints: admin_only, column_schema, date_format, performance
     - Tests: test_admin_required, test_column_schema, etc.
     
     Does this capture what you meant?"

You: "Yes, exactly."

AI: [Implements against intent, runs tests, all pass]
    "Done. All constraints verified."
```

**The workflow:**
1. Human describes (natural language)
2. AI writes intent (structured YAML)
3. Human reviews intent (clarification before code)
4. AI stress-tests intent (adversarial completeness check)
5. AI implements using constraint-segmented approach
6. AI verifies (full constraint sweep)

**Why this matters:** Clarification at intent stage, not after code. Turns drop to one.

#### Step 4: Intent Stress Test (Before Implementation)

After the human approves the intent and before implementation begins, the AI adversarially probes its own intent artifact for completeness. This catches gaps that are cheaper to fix in intent than in code.

The stress test checks four dimensions:

1. **Constraint completeness:** "What input breaks this? What edge case isn't covered? Are there boundary conditions not captured by any constraint?"
2. **Implementation anticipation:** "What decisions will implementation force that this intent doesn't address? Are there integration points, data shapes, ordering dependencies, or error paths not covered?"
3. **Assumption challenge:** "What am I assuming about the environment, dependencies, or user behavior? Are those assumptions documented or just implicit?"
4. **Constraint satisfiability:** "Do any two constraints conflict? Is simultaneous satisfaction of all constraints possible? Are the most critical constraints listed last to counter position bias?" *(Research grounding: UltraBench 2025 — models exceed 70% on individual constraints but fail at simultaneous satisfaction; position bias causes earlier constraints to be silently violated.)*

If the stress test reveals gaps, the AI updates the intent (adds constraints, test paths, or clarifying notes) before implementing. The human may re-review if the changes are significant.

**Why this step exists:** Intent captures what you know at the time of writing. Implementation forces decisions the intent didn't anticipate. The stress test is a structured way to anticipate those decisions *before* they become implementation rework. It's Principle 2 (Understanding Must Be Executable) applied reflexively — the AI checks whether its own understanding is complete before acting on it. The fourth probe (constraint satisfiability) prevents the especially costly failure mode where all individual constraints are well-formed but the set as a whole is impossible to satisfy simultaneously.

**When to skip:** Trivial changes where the intent is a single constraint with an obvious implementation. The stress test adds value proportional to the complexity of the intent.

#### Step 5: Constraint-Segmented Implementation

After the stress test and before the final verification sweep, implementation itself must account for a documented architectural limitation of transformer-based LLMs: **constraint compliance degrades during long generation spans**.

**The research basis:**

The problem is structural, not a model quality issue:

- **Read-acknowledge-violate pattern** (GitHub anthropics/claude-code #26848, #6120, #32290, #742 — 2025): AI agents read instruction files, can recite constraints verbatim, explicitly confirm understanding — then violate them in the next generation step. Documented systematically across model versions and user tiers. Persists even with 24+ enforcement hooks and 400-line instruction files.
- **Lost-in-the-middle** (Liu et al. 2023, Stanford NLP): Transformers attend strongly to the start and end of context; middle positions degrade by more than 30%. The intent artifact is injected at the top. As the AI generates implementation code, intent tokens are pushed toward the middle. By line 80 of a 200-line implementation, the first constraint listed in the intent is in the low-attention zone.
- **Constraint compliance is orthogonal to task completion** (MOSAIC 2025): producing correct, working code and following all stated constraints are measured separately — they are distinct capabilities. A model can deliver high-quality implementation that misses 2–3 constraints without any tension. The model defaults to "produce correct code" under attention pressure; constraint adherence is secondary.
- **Constraint density degradation** (IFScale 2025): frontier models achieve only 68% accuracy at high instruction density. Degradation is nonlinear — each additional constraint reduces overall compliance probability. The drop is not gradual; there are threshold effects at medium constraint densities.

**The protocol:**

For intents with 3+ constraints, do not implement in a single pass. Use constraint segments:

```
CONSTRAINT-SEGMENTED IMPLEMENTATION:

1. GROUP — After the stress test, group constraints into implementation
   segments by functional area. Example groups:
   - Input validation constraints
   - Core logic / output constraints  
   - Performance / latency constraints
   - Error handling constraints

2. IMPLEMENT one segment

3. RE-READ the constraints for that segment from the intent artifact
   (not from memory — counter lost-in-the-middle)

4. VERIFY the segment satisfies its constraints before proceeding

5. NEXT SEGMENT — repeat steps 2–4

6. CROSS-CUT — after all segments, run the full Post-Implementation
   Verification Protocol as a final sweep for inter-constraint gaps
```

**Why re-reading after each segment works:** Each re-read repositions the constraint text at the top of the context stack, where the transformer's attention mechanism weights it highest. This converts one long generation (where early constraints fade into low-attention middle positions) into multiple short generations, each starting with fresh constraint attention. The cognitive necessity of re-reading intent from disk (established for Verification Protocol Step 1) applies equally here — not as a best practice, but as a structural requirement.

**When to skip:** Intents with 1–2 constraints where a single implementation pass is trivially verifiable. The segmented approach adds value proportional to constraint count. Below 3 constraints, the overhead exceeds the benefit.

**What this changes about post-implementation verification:** When constraint-segmented implementation was used, the Post-Implementation Verification Protocol (Principle 4) functions as a cross-cutting final sweep — most per-constraint compliance is already established at the segment level. The sweep's primary value shifts to catching inter-constraint gaps and verifying that segment-level fixes didn't introduce cross-segment violations.

### When the User Lacks Technical Knowledge: Teaching Before Intent

Sometimes the user lacks the technical knowledge to understand domain concepts, patterns, or technologies needed for the task. They can't review intent if they don't understand what "ETL," "Saga pattern," or "CDC" means. They can't evaluate discovery options if the terminology is unfamiliar.

**This is the critical bottleneck:** Lack of technical knowledge blocks the entire IVD flow before it can even start.

**When to use:** User says "I don't know what X is," user can't evaluate discovery options because they don't understand the terms, reverse engineering (AI writes intent from existing code but user can't review patterns they haven't seen), or user is new to domain/codebase.

**Pattern (Step 0a):**
1. AI detects knowledge gap (user asks explicitly, or AI detects from language/context).
2. AI offers: "Would you like me to explain [concept] first?"
3. AI creates **structured educational artifact** (YAML with verification questions) explaining: what the concept is, why it matters here, key sub-concepts, tradeoffs, common patterns.
4. User reviews, asks clarifying questions, confirms understanding (verification questions check).
5. Standard flow: discovery (if needed) → describe → AI writes intent → review → implement → verify.

**Example:** User needs ETL but doesn't know what ETL is → AI creates educational artifact explaining Extract/Transform/Load, batch vs streaming, incremental vs full refresh, with verification questions → user understands → then discovery (which ETL pattern?) → describe → intent.

**Tools:** Use `ivd_teach_concept` to create educational artifact. **Recipe:** `recipes/teaching-before-intent.yaml`. **Research:** `research/teaching_before_intent.md`.

**For reverse engineering:** When AI writes intent from existing code, add an optional `education` section to the intent itself so the user learns domain patterns while reviewing.

**This is Principle 6 (AI as understanding partner):** the AI helps the user gain the knowledge they need before they can participate in the IVD flow.

### When the User Cannot Yet Describe: Discovery Before Intent *(Experimental)*

Sometimes the user doesn't have enough knowledge to give clear instructions or know what to ask—new to the domain, unfamiliar with the codebase, or unsure of the goal. IVD still applies: use an optional **discovery step** before "Human describes."

> **Status: Experimental** — This pattern is being validated. Use it and report results to help promote it to canonical.

**When to use:** User says "I'm not sure what we need," or the problem is in a new domain, or the user is exploring.

**Pattern:**
1. AI proposes 2–3 candidate goals or patterns (e.g. from recipes, existing features in the repo, or inversion ideas).
2. AI summarizes each option in one line with a short tradeoff.
3. User picks or narrows ("that one, but for compliance not sales").
4. Standard flow: user describes (now with a direction) → AI writes intent → review → implement → verify.

**Tools:** Use `ivd_discover_goal` (or list recipes + list features) to gather options; then proceed to intent writing. **Recipe:** `recipes/discovery-before-intent.yaml`. **Research:** `research/discovery_before_intent.md`.

This is still Principle 6 (AI as understanding partner)—the AI helps the user form intent when they can't yet articulate it.

### Early Verification: Linguistic Mirroring

Before formal constraint tests, you can detect misalignment through **linguistic mirroring**.

**The pattern:** When the AI echoes your key terms in its response, it signals alignment. When it substitutes different terminology, it signals potential misalignment.

```
✅ ALIGNED (AI echoes key terms):
Human: "Add admin compliance CSV export with ISO dates"
AI: "I'll write the intent for the admin compliance CSV export.
     Constraints: admin_only, ISO 8601 date format..."
     
❌ MISALIGNED (AI substitutes terms):
Human: "Add admin compliance CSV export with ISO dates"
AI: "I'll create a data dump feature for users..."
```

**Why this works:** The AI's choice of vocabulary reveals its internal understanding. If it understood "admin compliance", it will use those words. If it generalized to "users" or "data dump", it filled a gap incorrectly.

**When to use:** 
- During the "AI writes intent" step
- Before running formal constraint tests
- As a quick sanity check in conversation

**This is not a replacement for verification.** It's an early signal. Formal constraint tests (Principle 2) are still required.

### Principle 6 in Multi-Agent Systems

When multiple agents collaborate, Principle 6 applies at every level:

```
Human describes
    ↓
Coordinator AI writes COORDINATOR INTENT
    ├─→ What agents to route to
    ├─→ What each should accomplish
    └─→ How to synthesize results
    ↓
For each agent, Coordinator writes AGENT INTENT
    ├─→ Specific task
    ├─→ Constraints
    └─→ Verification criteria
    ↓
Each Agent stress-tests its intent (edge cases, missing constraints)
    ↓
Each Agent implements against its intent
    ↓
Each Agent verifies its output
    ↓
Coordinator synthesizes verified results
```

**The key insight:** Intent doesn't stop at the coordinator. The coordinator produces intent artifacts for each specialist agent. This prevents "coordination errors" where the coordinator routes correctly but passes wrong parameters.

**Core principle:** Tools are truth, history is context. The coordinator uses tools to verify current state—never assumes from chat history.

**Routing Surface:** In LLM-based multi-agent systems, the coordinator decides which agent to call based on **description strings** it reads at runtime — `AGENT_DESCRIPTION`, `COORDINATOR_INSTRUCTIONS`, tool descriptions, or equivalent. This description is the **routing surface**: the actual integration contract between coordinator and agent. IVD captures this surface in the agent's intent via the optional `interface.routing` sub-field (`description`, `keywords`, `consumed_by`), making it verifiable. When agent capabilities change (new tools, modified behavior), the routing surface must update — or the coordinator can't route to the new capability. See the `agent-capability-propagation` recipe for the bottom-up propagation pattern (agent changes → coordinator routing update), which complements the top-down `coordinator-intent-propagation` recipe.

**Recipes:**
- `recipes/coordinator-intent-propagation.yaml` (top-down: coordinator → agents at runtime)
- `recipes/agent-capability-propagation.yaml` (bottom-up: agent changes → coordinator routing)

**Research:** `research/coordinator_agent_design_patterns.md`

---

### Principle 7: Understanding Survives Implementation

**Implementation changes. Languages change. Intent persists.**

```yaml
# lead_qualifier_intent.yaml v3

intent:
  goal: "Qualify high-probability leads for sales team"
  success_metric: "Sales conversion rate >= 15%"

constraints:
  - precision >= 0.80
  - recall >= 0.60

implementation_history:
  - version: 1
    language: Python
    approach: "Rule-based thresholds"
    deprecated: "2025-11-01"
    reason: "Too brittle for changing data"
  
  - version: 2
    language: Python
    approach: "ML classifier"
    deprecated: "2025-12-15"
    reason: "Overfitting, poor generalization"
  
  - version: 3 (current)
    language: Python
    approach: "Statistical threshold with data quality gate"
    file: "agent/lead_qualifier/scoring.py"
    
rationale:
  decision: "threshold = 0.70"
  evidence: "playground/lead_analysis_2025-12.ipynb"
  stakeholder: "VP Sales, approved 2025-12-15"
```

**When you rewrite in Go, or replace with vendor service, intent transfers.**

---

### Principle 8: Innovation through Inversion

**Innovation comes from inverting dominant beliefs—state the default, invert it, evaluate, implement.**

The conventional way to solve a problem is often a "dominant belief." By explicitly stating the default and considering the *opposite* approach, we surface non-obvious solutions. IVD supports this with:

1. **State the Default:** What is the conventional or obvious way to solve this?
2. **Invert:** What would the opposite approach look like?
3. **Evaluate:** Is the inversion promising? (pros, cons, feasibility)
4. **Implement:** If chosen, capture in intent (e.g. `inversion_opportunities`) and verify.

Intent artifacts can include an optional **inversion_opportunities** block: problem, dominant belief(s), and proposed inversions with rationale and status (chosen | rejected | deferred). Use the **ivd_propose_inversions** MCP tool to brainstorm inversions; then document chosen/rejected ones in the intent.

**When to use Principle 8:**
- **Use** when you are *designing* (new or major intent): the problem has a conventional or "obvious" approach, and you care about performance, scale, security, or maintainability. Apply before locking the design.
- **Skip** when the change is small (bug fix, config, refactor), when there is no clear default approach, or when the obvious solution is good enough and you are not optimizing for alternatives.

---

## Intent Artifacts

### What is an Intent Artifact?

A **structured, version-controlled file** that declares:
- What the system should do (goal)
- Why it should do it (rationale)
- What constraints must hold (requirements)
- What alternatives were rejected (context)
- What risks exist (monitoring needs)

**Format:** YAML (structured, readable, diffable, version-controllable)

---

### Intent Artifact Schema

```yaml
# {module}_intent.yaml

# Reference parent intent (for workflow/module/task that's part of larger system)
# Recommended for all non-system intents to establish hierarchy
parent_intent: "../../system_intent.yaml"  # Relative path to parent
# Examples:
#   Task → Module: "../{module}_intent.yaml"
#   Module → Workflow: "../../workflows/{workflow}_intent.yaml"
#   Module → System: "../../system_intent.yaml"
#   Workflow → System: "../system_intent.yaml"

# WHAT should this do?
intent:
  summary: "One-line description"
  goal: "Detailed explanation of purpose"
  success_metric: "How to measure success"
  stakeholders: ["Who cares about this"]

# OPTIONAL: Project context (SYSTEM-LEVEL ONLY - for existing projects)
# project_context:
#   code_rules: [{path, description}]        # .cursorrules, lint configs
#   architecture: [{path, description}]      # ARCHITECTURE.md, ADRs, principles
#   tools_scripts: [{path, description}]     # Key scripts, CLIs, utilities
#   libraries_reuse: [{library, when_to_use}] # Shared internal libraries
#   key_paths:                               # "Map to the stars"
#     entrypoints: [{path, description}]     # API main, worker entry
#     modules: [{path, description}]         # agent/, entity/, integrations/
#     workflows: [{path, description}]       # workflows/
#     docs: [{path, description}]            # docs/, runbooks/
#     tests: [{path, description}]           # tests/
#   existing_docs: [{path, description}]     # README, API.md, CONTRIBUTING

# OPTIONAL: Feature inventory (large projects - avoid duplication)
# metadata:
#   feature_id: "csv_export"           # Stable, unique slug (lowercase, snake_case)
#   category: "data_export"           # Group for filtering (auth, reporting, api)
#   tags: ["admin", "compliance"]     # Searchable keywords
#   status: "implemented"             # implemented | planned | deprecated
#   introduced_version: "1.2.0"       # Optional
#   deprecated_version: null          # Optional (if status: deprecated)

# OPTIONAL: Innovation through Inversion (Principle 8)
# inversion_opportunities:
#   problem: "e.g., CSV processing for large files"
#   dominant_belief: "Load entire file into memory, then parse"
#   proposed_inversions:
#     - name: "Stream rows, never load file"
#       description: "Process row-by-row"
#       rationale: "Better for large files; no random access"
#       status: "chosen"   # chosen | rejected | deferred

# OPTIONAL: Field Mapping (for data-heavy intents)
# field_mapping:
#   summary: "Brief description of what data is being mapped"
#   sources:
#     - system: "source_system_name"
#       type: "database | api | file"
#       location: "table or endpoint"
#   targets:
#     - system: "target_system_name"
#       type: "database | api | file"
#       location: "table or endpoint"
#   mappings:
#     - source_field: "source.field"
#       target_field: "target.field"
#       transformation: "description"
#       required: true
#   verification:
#     schema_validation:
#       - check: "fields exist in schemas"
#         test: "path/to/test"
# 
# Use this section for:
# - API integrations (CRM, payment, external services)
# - ETL pipelines and data synchronization
# - Data import/export features
# See: recipes/data-field-mapping.yaml for complete pattern

# WHAT must hold true?
constraints:
  - name: "constraint_id"
    requirement: "precision >= 0.80"
    test: "path/to/test.py::test_name"
    consequence_if_violated: "What breaks if this fails"

# WHY this approach?
rationale:
  decision: "Key decision made"
  evidence: "Link to validation (notebook, doc, etc.)"
  date: "2026-01-23"
  stakeholder: "Who approved this"

# WHY NOT alternatives?
alternatives:
  - name: "alternative_approach"
    rejected_because: "Reason"
    experiment: "path/to/comparison"
    date_tested: "2026-01-15"

# WHAT could go wrong?
risks:
  - condition: "When does this become a problem?"
    action: "What should happen?"
    monitor: "Where to watch for this"
    severity: "high|medium|low"

# WHERE is this implemented?
implementation:
  current: "path/to/file.py"
  version: 3
  tests: "path/to/tests/"
  documentation: "path/to/docs.md"

# WHEN was this changed?
changelog:
  - version: 3
    date: "2026-01-23"
    change: "Updated threshold from 0.65 to 0.70"
    reason: "Precision was too low"
    evidence: "playground/threshold_tuning_2026-01.ipynb"
```

---

### Where Intent Artifacts Live

```
project/
├── agent/
│   ├── lead_qualifier/
│   │   ├── scoring.py              # Implementation
│   │   ├── scoring_intent.yaml     # ← Intent artifact
│   │   └── tests/                  # Verification
├── playground/
│   └── lead_analysis_2025-12.ipynb # Evidence
└── docs/
    └── agents/
        └── lead_qualifier_DESIGN.md # Generated from intent
```

**Intent artifact lives alongside implementation**, not in separate docs folder.

---

### Intent for Any AI-Produced Artifact

**IVD is not just for code.** Any artifact produced by AI should have its paired intent—its point of origin, its original intention.

#### Scope: Beyond Code

The framework supports intent artifacts for:

- **Code** (functions, agents, services)
- **Architecture** (system designs, diagrams, decisions)
- **Documentation** (guides, specifications, runbooks)
- **Research** (analysis, experiments, findings)
- **Books & Content** (chapters, articles, manuscripts)
- **Processes** (workflows, methodologies, procedures)
- **Data** (schemas, transformations, pipelines)

**Core principle:** If AI produced it, it should have verifiable intent.

#### When Documentation Is Derived vs. Primary

Documentation plays two roles in IVD:

- **Derived artifact:** Documentation that explains code (auto-generated API docs, inline design docs, READMEs describing a module). Reference it in the code intent's `implementation.documentation` field. No separate intent needed.
- **Primary artifact:** Documentation that IS the deliverable (runbook, user guide, architecture decision record, onboarding guide, specification). Create a dedicated `{name}_intent.yaml` alongside it—same pattern as code intents.

**Rule of thumb:** If you removed the code and the document still has value on its own, it's a primary artifact and deserves its own intent.

---

#### Co-location for Non-Code Artifacts

The "intent alongside implementation" principle applies universally:

**Books:**
```
book/
├── book_system_intent.yaml        # Intent for entire book
└── manuscript/
    └── part-1-foundations/
        └── chapter-01-alignment-crisis/
            ├── intent.yaml         # Intent for this chapter
            └── chapter.md          # Implementation (manuscript)
```

**Research:**
```
research/
├── best_selling_programming_books_intent.yaml  # Intent
└── best_selling_programming_books.md          # Implementation (findings)
```

**Architecture:**
```
architecture/
├── decisions/
│   ├── adr_001_intent.yaml        # Intent for decision
│   └── adr_001_database_choice.md # Implementation (ADR)
```

**Documentation (guides, runbooks, specifications):**
```
docs/
├── operations/
│   ├── runbook_incident_response_intent.yaml  # Intent
│   └── runbook_incident_response.md           # Implementation (runbook)
├── onboarding/
│   ├── onboarding_guide_intent.yaml           # Intent
│   └── onboarding_guide.md                    # Implementation (guide)
```

**Processes:**
```
processes/
├── chapter_writing_process_intent.yaml   # Intent (defines process)
└── examples/                              # Implementation (process outputs)
```

**Why this matters:**

1. **Traceability:** Every artifact traces back to its original intent
2. **Verifiability:** AI can verify non-code outputs against constraints
3. **Evolution:** When book chapters need revision, intent survives
4. **Context:** Future AI agents understand WHY something was created
5. **Consistency:** Same methodology for code and non-code work

**Example constraint for book chapter:**

```yaml
# chapter-01/intent.yaml
constraints:
  - name: "paragraph_length"
    requirement: "Most paragraphs 3-5 sentences, max 7"
    test: "visual inspection and readability review"
    
  - name: "author_sourced_examples"
    requirement: "All examples must be labeled as author-sourced or industry-typical"
    test: "grep for unlabeled 'example' instances"
```

**Example constraint for research:**

```yaml
# research/analysis_intent.yaml
constraints:
  - name: "source_validation"
    requirement: "All claims backed by URL or citation"
    test: "Every finding has 'source:' field with URL"
    
  - name: "recency"
    requirement: "Sources from 2024-2026 unless historical context"
    test: "Check all URLs and citations for date"
```

**Example constraint for documentation (runbook):**

```yaml
# docs/operations/runbook_incident_response_intent.yaml
constraints:
  - name: "actionable_steps"
    requirement: "Every section has numbered steps a new engineer can follow"
    test: "Each H2 section contains an ordered list of concrete actions"
    
  - name: "up_to_date_references"
    requirement: "All tool names, URLs, and commands verified against current infra"
    test: "Run every command in dry-run mode; check all URLs return 200"
```

---

### Feature Inventory (Large Projects)

In large projects, **knowing what features exist** prevents duplication and helps AI agents (and humans) load context quickly. IVD supports this **without a separate inventory file**—inventory is **derived** from intent artifacts.

#### How It Works

1. **Optional metadata on intents:** Add a `metadata` block to intent artifacts (see schema above) with:
   - **feature_id:** Stable, unique slug (e.g. `csv_export`, `lead_qualifier`). Use lowercase snake_case.
   - **category:** Group for filtering (e.g. `data_export`, `auth`, `reporting`, `api`). Define a short list per project.
   - **tags:** Searchable keywords (e.g. `admin`, `compliance`, `reporting`).
   - **status:** `implemented` | `planned` | `deprecated`.
   - **introduced_version** / **deprecated_version:** Optional; for history.

2. **Derived inventory:** Use the IVD feature-list tool (e.g. `ivd_list_features`) to scan all `*_intent.yaml` files and return an aggregated list. No separate `feature_inventory.yaml`—inventory is always generated from source, so it cannot drift. IVD placement and tools are **per-project** (co-locate with code in that repo); MCP tools accept an optional `project_root` for use in any repository.

3. **Check before building:** Before adding a new feature, list features (filter by category or tags), check if something equivalent already exists, then scaffold or extend. Prevents duplicate work.

#### When to Use

- **Recommended** for large or multi-team projects where "what already exists?" is hard to see.
- **Optional** for small projects; omit `metadata` and IVD works as before.

#### Conventions

- **feature_id:** Unique in the repo; lowercase snake_case.
- **category:** Agreed short list per project (e.g. 5–10 categories).
- **status:** Exactly one of `implemented`, `planned`, `deprecated`.

---

### Optional Section: Parent Intent (Intent Hierarchy)

For **non-system intents** (workflow, module, task), IVD supports an **optional `parent_intent` field** that links a child intent to its parent — establishing hierarchy and enabling context inheritance.

#### When to Use

Use `parent_intent` when:
- **Any workflow, module, or task intent** that belongs to a project with a system-level intent
- **Multi-level intent hierarchies** (system → workflow → module → task) where child intents should inherit project conventions
- **AI agents** that need to load project-wide context (architecture, code rules, key paths) when creating or modifying child intents

Skip this field when:
- **System-level intents** (they *are* the root; nothing to point to)
- **Standalone intents** with no parent project context
- **Single-file projects** where hierarchy adds no value

#### What It Provides

- **Context inheritance:** AI agents read `parent_intent`, load the parent's `project_context` section, and follow project conventions automatically
- **Hierarchy visibility:** The intent tree (system → workflow → module → task) is explicit, not implicit
- **Consistency:** All child intents reference the same conventions, architecture, and key paths

#### Why It Matters

Without `parent_intent`, every child intent is an island. AI agents creating a new module intent don't know the project uses event-driven architecture, has a shared auth library, or follows specific logging conventions. With `parent_intent`, the agent loads the parent, reads the project context, and follows conventions — **automatically, not by accident** (Principle 7: Understanding Survives Implementation; Principle 5: Layered Understanding).

#### Example

```yaml
# agent/lead_scorer/lead_scorer_intent.yaml

parent_intent: "../../system_intent.yaml"

scope:
  level: "module"
  type: "agent"
  # ...
```

The relative path points to the system intent. AI agents resolve this path, load the parent, and inherit its context. Task intents point to their module; modules point to workflows or directly to the system intent.

---

### Optional Section: Project Context (System-Level Only)

For **system-level intents in existing projects**, IVD supports an **optional `project_context` section** that captures project-wide conventions, architecture, tools, and key paths—enabling all child intents to reuse and reference them.

#### When to Use

Use the `project_context` section when:
- **System-level intent** for a project/product (not workflow/module/task)
- **Existing project** (brownfield) with established conventions, architecture, docs
- **Installing IVD** via `ivd init` in a codebase that already has structure
- **Multiple teams** need consistent reference to project conventions

Skip this section when:
- **Greenfield project** with no existing conventions (conventions emerge as you build)
- **Workflow, module, or task-level** intents (reference `parent_intent` instead)
- **Single-developer hobby project** where conventions are implicit

#### What It Provides

The `project_context` section documents:
- **Code rules:** `.cursorrules`, lint configs, formatting standards
- **Architecture:** Design principles, ADRs, ARCHITECTURE.md references
- **Tools/scripts:** Key scripts, CLIs, utilities (so new intents reference, not duplicate)
- **Libraries to reuse:** Internal shared libraries and when to use them
- **Key paths ("map to the stars"):** Navigable map of entrypoints, modules, workflows, docs, tests
- **Existing docs:** README, API docs, runbooks, CONTRIBUTING

#### Why It Matters

Without project context:
- **Duplication:** New intents recreate existing tools, scripts, libraries
- **Inconsistency:** New intents don't follow project conventions or architecture
- **Lost navigation:** AI agents and developers don't know where key code lives
- **Ignored docs:** New intents don't reference existing documentation

With project context:
- **Reuse:** New intents reference existing tools, scripts, libraries (no duplication)
- **Consistency:** New intents follow project code rules and architecture principles
- **Navigation:** "Map to the stars" (key_paths) shows where entrypoints, modules, workflows, docs, tests live
- **Integration:** New intents link to and extend existing documentation

#### Example Structure

```yaml
# system_intent.yaml (project root)

project_context:
  code_rules:
    - path: ".cursorrules"
      description: "Cursor IDE rules and conventions"
    - path: "pyproject.toml"
      description: "Python formatting (black), linting (ruff), type checking (mypy)"
  
  architecture:
    - path: "docs/ARCHITECTURE.md"
      description: "High-level system architecture and design principles"
    - path: "docs/architecture/"
      description: "Architecture Decision Records (ADRs)"
    - principle: "Event-driven microservices with async messaging (RabbitMQ)"
    - principle: "No direct database access from frontend; all via API"
    - principle: "Idempotent operations for all background jobs"
  
  tools_scripts:
    - path: "scripts/deploy.sh"
      description: "Deployment automation (staging, production)"
    - path: "scripts/db_migrate.py"
      description: "Database migration runner (Alembic wrapper)"
    - path: "tools/data_pipeline/extract.py"
      description: "Data extraction utilities for ETL"
  
  libraries_reuse:
    - library: "internal/auth_utils"
      description: "Authentication and authorization utilities (JWT, RBAC)"
      when_to_use: "All auth-related features; never reimplement auth logic"
    - library: "internal/logging"
      description: "Structured logging with correlation IDs and tracing"
      when_to_use: "All modules and workflows; use log_context decorator"
  
  key_paths:
    entrypoints:
      - path: "api/main.py"
        description: "FastAPI application entrypoint (REST API)"
      - path: "worker/celery_app.py"
        description: "Background job worker (Celery)"
    
    modules:
      - path: "agent/"
        description: "AI agents (classifiers, extractors, coordinators)"
      - path: "entity/"
        description: "Core business entities (User, Lead, Organization)"
      - path: "integrations/"
        description: "External service integrations (Salesforce, Stripe, Twilio)"
    
    workflows:
      - path: "workflows/"
        description: "Multi-step business processes (lead_qualification, onboarding)"
    
    docs:
      - path: "docs/"
        description: "Project documentation (architecture, API, runbooks)"
      - path: "docs/runbooks/"
        description: "Operational runbooks for common incidents"
    
    tests:
      - path: "tests/"
        description: "Test suites (unit, integration, e2e)"
  
  existing_docs:
    - path: "README.md"
      description: "Project overview and quick start"
    - path: "docs/API.md"
      description: "API reference (autogenerated from OpenAPI spec)"
    - path: "docs/CONTRIBUTING.md"
      description: "Contribution guidelines and development setup"
```

#### Child Intents Reference Parent

Once system intent has project context, child intents reference it:

```yaml
# agent/lead_scorer/lead_scorer_intent.yaml

parent_intent: "../../system_intent.yaml"

scope:
  level: "module"
  type: "agent"

intent:
  summary: "Lead scoring agent for CRM pipeline"
  goal: |
    Classify leads as qualified/unqualified using ML model.
    
    Project context:
    - Follows event-driven architecture (principle from parent)
    - Uses internal/logging for structured logging (library from parent)
    - Reuses internal/auth_utils for API authentication (library from parent)
  
  success_metric: "Precision >= 85%"
  stakeholders: ["VP Sales"]

# Implementation references parent context
implementation:
  current: "agent/lead_scorer/scorer.py"
  reuses:
    - library: "internal/logging"
      usage: "@log_context decorator for all public methods"
    - library: "internal/auth_utils"
      usage: "API key validation before scoring"
  
  follows_architecture:
    - "Event-driven: Publishes 'lead.scored' events to RabbitMQ"
    - "Idempotent: Same lead ID + data = same score (no side effects)"
```

**The benefit:** AI agents creating or modifying this intent:
1. Read `parent_intent: "../../system_intent.yaml"`
2. Load project context (code rules, architecture, tools, libraries, key paths)
3. Follow conventions automatically (event-driven, use logging, reuse auth)
4. Reference existing tools/scripts instead of duplicating
5. Navigate via key_paths ("map to the stars") to find related code

---

### Optional Section: Field Mapping (Data-Heavy Intents)

For intents that document data movement, integration, or transformation between systems, IVD supports an **optional `field_mapping` section** that makes field mappings, data sources, and transformations explicit and verifiable.

#### When to Use

Use the `field_mapping` section when:
- **API integrations** (Salesforce, Stripe, HubSpot, external services)
- **ETL pipelines** and data synchronization
- **Database-to-database** transfers
- **Data import/export** features
- **Reporting and analytics** data feeds
- **Field mapping errors** are high-cost (wrong data, compliance issues, data loss)

Skip this section when:
- No external data sources or targets (internal-only logic)
- Trivial 1:1 passthrough mapping with no transformation
- No data quality or compliance requirements

#### What It Provides

The `field_mapping` section documents:
- **Sources:** Which systems, tables, APIs, or files data comes from
- **Targets:** Which systems, tables, APIs, or files data goes to
- **Mappings:** Source field → target field, with transformations and validation
- **Business rules:** Rules that affect mapping (e.g., "only sync qualified leads")
- **Transformations:** How data is converted (e.g., score 0.0-1.0 → 0-100)
- **Verification:** Schema validation, sample data checks, data quality metrics

#### Why It Matters

Field mappings are often undocumented or only in prose, leading to:
- **Bugs** from wrong or outdated mappings
- **Slow onboarding** (developers reverse-engineer mappings from code)
- **AI agents can't understand** or modify integrations
- **Compliance risks** from unclear data lineage

This section makes mappings:
- **Explicit:** Source → target, transformation, validation
- **Verifiable:** Schema checks, sample validation, data quality tests (Principle 2)
- **Discoverable:** In intent artifact alongside workflow/module (Principle 5: Layered Understanding)

#### Example Structure

```yaml
# In workflow-level or module-level intent

field_mapping:
  summary: "Sync qualified leads from internal DB to Salesforce CRM"
  
  sources:
    - system: "internal_db"
      type: "database"
      location: "leads table"
  
  targets:
    - system: "salesforce"
      type: "api"
      location: "Lead object"
  
  mappings:
    - source_field: "internal_db.leads.email"
      target_field: "salesforce.Lead.Email"
      transformation: "none"
      required: true
    
    - source_field: "internal_db.leads.score"
      target_field: "salesforce.Lead.Lead_Score__c"
      transformation: "round(score * 100)"
      data_type: "float → integer"
      example:
        source: 0.87
        target: 87
  
  verification:
    schema_validation:
      - check: "All fields exist in schemas"
        test: "tests/test_schema_conformance.py"
    
    sample_validation:
      - description: "Compare 10 random synced leads"
        test: "tests/test_sync_accuracy.py"
```

**See:** `recipes/data-field-mapping.yaml` for complete pattern, examples, and verification strategies.

---

### Optional Section: Interface (Modules with a Callable Tool Surface)

For modules that **expose tools, commands, or endpoints** to external consumers — agents, MCP servers, APIs, CLIs, or services — IVD supports an **optional `interface` section** that documents the callable tool surface as a verifiable contract.

#### When to Use

Use the `interface` section when:
- **MCP servers** exposing tools to AI agents
- **AI agents** that expose callable tools or actions
- **APIs** (REST, GraphQL, gRPC) with endpoints
- **CLIs** with commands and subcommands
- **Services** with a defined interface consumed by other modules

Skip this section when:
- Internal module with no external interface (internal-only logic)
- The module's interface is a single function (use a task-level intent instead)
- Pure data processing with no callable surface
- Libraries consumed only via import (document via task-level intents per function)

#### What It Provides

The `interface` section documents:
- **Type:** What kind of interface (mcp, agent, api, cli, service)
- **Tools:** Each callable tool/endpoint with name, description, parameters, return type, and test
- **Parameters:** Typed, required/optional, with description — machine-verifiable against implementation
- **Tests:** Each tool links to its test (Principle 2: Understanding Must Be Executable)

#### Why It Matters

Tool surfaces are often undocumented or only discoverable by reading implementation code, leading to:
- **Integration bugs** from wrong parameter types or missing required fields
- **Slow onboarding** (developers guess tool capabilities from source)
- **AI agents can't reason** about what a module can do (they need to read all the code)
- **Drift** between documentation and implementation goes undetected

This section makes tool surfaces:
- **Explicit:** Every tool, its parameters, types, and return values
- **Verifiable:** Each tool links to a test; parameter types checkable against code (Principle 2)
- **Implementation-independent:** Rewrite Python → TypeScript; the interface section still describes the same tools (Principle 7)
- **Discoverable:** In the intent artifact, right next to what the module does and why (Principle 5)

#### Optional Sub-Field: Routing (Agents Consumed by a Coordinator)

For agents that are **consumed by a coordinator** (the coordinator routes requests to this agent based on descriptions), the `interface` section supports an optional `routing` sub-field that captures the **routing surface** — the description the coordinator LLM reads to make routing decisions.

**When to Use:**
- Agent is one of several specialists consumed by a coordinator
- The coordinator uses description strings (not hard-coded routing) to decide which agent handles which request
- Agent capabilities change and the coordinator's routing knowledge must update

**Why It Matters:**
In LLM-based multi-agent systems, the routing surface (the description string) is the **actual runtime interface** between coordinator and agent — as critical as an API contract. Without capturing it in intent, capability changes silently break routing: the coordinator can't discover new capabilities, or still routes to removed ones.

The `routing` sub-field makes this surface:
- **Explicit:** The description the coordinator sees is declared in intent (Principle 1)
- **Verifiable:** Compare `routing.description` keywords against actual `tools` — detect drift (Principle 2)
- **Synchronized:** When `tools` change, `routing.description` must update (Principle 3)
- **Implementation-independent:** Rewrite the agent; the routing description still describes the same capabilities (Principle 7)

**Recipe:** `recipes/agent-capability-propagation.yaml` (bottom-up propagation pattern)

#### Example Structure

```yaml
# In module-level intent for agents, MCP servers, APIs, CLIs, services

interface:
  type: "mcp"   # "mcp" | "agent" | "api" | "cli" | "service"
  
  # Optional — for agents consumed by a coordinator
  routing:
    description: "One-line: what the coordinator tells the LLM about this agent"
    keywords: ["psychology", "therapy", "memory"]
    consumed_by: "agent/coordinator"
  
  tools:
    - name: "ivd_validate"
      description: "Validate structure of an IVD intent artifact"
      parameters:
        - name: "artifact_yaml"
          type: "string"
          required: true
          description: "Raw YAML content of the artifact to validate"
        - name: "artifact_type"
          type: "string"
          required: false
          description: "Type: intent, recipe, workflow (default: intent)"
      returns: "JSON with valid (bool), errors, warnings, suggestions"
      test: "tests/unit/test_validate.py::test_valid_intent"
    
    - name: "ivd_search"
      description: "Semantic search across IVD knowledge base"
      parameters:
        - name: "query"
          type: "string"
          required: true
          description: "Natural language query"
        - name: "top_k"
          type: "number"
          required: false
          description: "Number of results (default: 5)"
      returns: "JSON array of matching chunks with content, source, similarity"
      test: "tests/unit/test_search.py::test_search_returns_results"
```

#### Relationship to Task-Level Intents

The `interface` section provides an **aggregate view** of the module's tool surface. For complex or critical tools, you may **also** create individual task-level intents that go deeper into the tool's internal logic:

```
MODULE INTENT (interface section)     → "These are the 15 tools, their types, their tests"
    ↓
TASK INTENT (per critical tool)       → "This tool's internal logic, edge cases, rationale"
```

They complement each other — the interface is the summary; task intents are the deep-dive.

---

### Optional Section: Roles (Agents with Context-Dependent Behavior) *(Experimental)*

For AI agents that **switch behavioral modes** depending on context — implementer, reviewer, architect, teacher, debugger — IVD supports an **optional `roles` section** that documents each behavioral profile as a verifiable contract.

> **Status: Experimental** — This section is being validated. Apply it to real agents and report results to help promote it to canonical.

#### When to Use

Use the `roles` section when:
- **AI agents** that operate in 2+ distinct behavioral modes (e.g., Cursor's agent/plan/debug/ask modes)
- **Each mode has different constraints** (e.g., reviewer is read-only; implementer can modify files)
- **Each mode uses a different subset of tools** from the agent's `interface`
- **Coordinators need to understand** an agent's behavioral modes for routing decisions

Skip this section when:
- Agent has a single mode (just use `interface`)
- Behavioral differences are trivial (just tone or prompt differences, no constraint changes)
- Each role is a separate agent (use the coordinator-intent-propagation recipe instead)
- The module is not an agent (APIs, CLIs, services don't have roles)

#### What It Provides

The `roles` section documents:
- **Default role:** Which behavioral mode the agent starts in
- **Switching mechanism:** How the agent transitions between roles (user-directed, context-inferred, explicit command)
- **Role definitions:** Each role with name, description, trigger context, constraints, available tools, and verification test

#### Why It Matters

Role behaviors are often undocumented or only exist in system prompts and code, leading to:
- **Behavioral drift** when prompts change but intent doesn't reflect the new behavior
- **Unclear expectations** — users and coordinators don't know what constraints apply in each mode
- **Lost context** — when the agent is rewritten, role definitions disappear with the old code

This section makes role behaviors:
- **Explicit:** Each role's constraints and available tools are declared in intent
- **Verifiable:** Each role links to a test (Principle 2: Understanding Must Be Executable)
- **Implementation-independent:** Rewrite the agent; the roles section still describes the same behavioral modes (Principle 7)
- **Discoverable:** Coordinators and users can read the intent to understand all available modes (Principle 5)

#### Relationship to Interface

The `roles` and `interface` sections complement each other:

```
INTERFACE = WHAT the agent can do (tools, parameters, returns)
ROLES     = HOW the agent behaves in different contexts (constraints, tool subsets)
```

A role may **restrict** which interface tools are available. For example, a "reviewer" role might only allow `read`, `search`, and `validate` tools from the full interface, while an "implementer" role allows all tools.

#### Example Structure

```yaml
roles:
  default: "implementer"

  switching:
    mechanism: "user_directed"
    description: "User selects mode explicitly or agent infers from request context"

  definitions:
    - name: "implementer"
      description: "Writes code, creates files, executes commands"
      when: "User requests building, fixing, creating, or implementing"
      constraints:
        - "Must write/update intent before implementing"
        - "Must verify constraints after implementation"
      tools: ["all"]
      verification: "tests/test_role_implementer.py"

    - name: "reviewer"
      description: "Reviews code for quality, alignment, issues"
      when: "User requests review, audit, check, or code review"
      constraints:
        - "Read-only: no file modifications"
        - "Must cite specific file and line references"
        - "Must check alignment against intent artifact"
      tools: ["read", "search", "validate"]
      verification: "tests/test_role_reviewer.py"

    - name: "architect"
      description: "Designs systems, proposes structure, evaluates tradeoffs"
      when: "User requests design, planning, architecture decisions"
      constraints:
        - "Must present alternatives with tradeoffs (Principle 8)"
        - "Must reference existing architecture from parent_intent"
        - "Read-only: no implementation changes"
      tools: ["read", "search", "scaffold"]
      verification: "tests/test_role_architect.py"
```

#### Relationship to Coordinator Pattern

The `roles` section is for **one agent with multiple modes**. The coordinator-intent-propagation recipe is for **multiple agents, each with its own intent**. They are distinct but compatible:

```
ONE AGENT, MULTIPLE ROLES    → roles section in that agent's intent
MULTIPLE AGENTS              → coordinator recipe, each agent has its own intent
MULTIPLE AGENTS WITH ROLES   → coordinator routes to agents; each agent's intent has roles
```

A coordinator can read an agent's `roles` section to understand not just what the agent can do (`interface`), but how it behaves in different contexts — enabling smarter routing.

---

### Optional Section: Authorship (Who Originates and Controls Intent) *(Experimental)*

In standard IVD, the human describes what they want and the AI writes the intent artifact. But as AI agents become more autonomous — designing workflows, proposing process changes, creating new intents for sub-tasks — the question arises: **who originated this intent, and what can the AI change without asking?**

The **optional `authorship` section** formalizes the trust boundary for intent creation and modification.

> **Status: Experimental** — This section is being validated. Apply it to real autonomous workflows and report results to help promote it to canonical.

#### When to Use

Use the `authorship` section when:
- **AI agents design workflows** — the agent decides what steps to include, where to inject LLM calls, what data to pull
- **Self-improving systems** — the agent may modify its own intent based on evaluation results
- **Autonomous agents** that create sub-task intents without a direct human request
- **Teams need clarity** on what the AI can and cannot change in an intent artifact

Skip this section when:
- Standard IVD workflow (human describes, AI writes, human reviews) — this is the default and doesn't need declaration
- Intent is always human-originated with no AI modification authority
- The module is not autonomous (simple libraries, utilities, static configurations)

#### What It Provides

The `authorship` section declares:
- **Origin:** Who created this intent (human-directed, AI-proposed, AI-autonomous)
- **Human oversight:** What level of review is required (review_required, audit_trail, escalation_only)
- **AI authority:** What the AI can create, modify, and what fields require human approval
- **Escalation:** When the AI must stop and ask a human

#### Why It Matters

Without explicit authorship boundaries:
- **AI silently modifies intent** — changes goal or constraints without human awareness
- **No trust gradient** — everything is either fully human-controlled or fully autonomous, no middle ground
- **Coordinators can't delegate safely** — they don't know which agents have authority to create sub-intents
- **Accountability gap** — when something goes wrong, unclear whether a human approved the intent

This section makes authorship:
- **Explicit:** The trust boundary is declared, not implicit (Principle 1)
- **Verifiable:** Test that AI respects its declared authority — cannot modify protected fields (Principle 2)
- **Graduated:** From human-directed → AI-proposed → AI-autonomous, with appropriate oversight at each level
- **Implementation-independent:** Change the AI framework; the authorship rules still apply (Principle 7)

#### Example Structure

```yaml
authorship:
  origin: "ai_proposed"              # human_directed | ai_proposed | ai_autonomous
  human_oversight: "review_required"  # review_required | audit_trail | escalation_only

  ai_authority:
    can_create: true                  # can AI create new sub-intents?
    can_modify:                       # which sections AI can modify without approval
      - "implementation"
      - "verification"
      - "workflow.steps"
    requires_approval:                # fields that need human sign-off before changes take effect
      - "intent.goal"
      - "intent.success_metric"
      - "constraints"
  
  escalation: "When AI confidence < 80%, when change impacts other intents, or when modification touches protected fields"
```

#### Authorship Levels

The three origin levels represent a spectrum of human involvement:

```
HUMAN_DIRECTED    → Human describes, AI writes, human reviews (current IVD default)
AI_PROPOSED       → AI proposes new intent or modifications, human reviews before activation
AI_AUTONOMOUS     → AI creates/modifies intent within declared boundaries, human audits after
```

Each level requires increasing guardrails:
- **human_directed:** Standard IVD. No authorship section needed (it's the default).
- **ai_proposed:** AI can propose but nothing takes effect without human review. Safe for most workflows.
- **ai_autonomous:** AI operates within `can_modify` boundaries. `requires_approval` fields are locked. Escalation rules are critical.

#### Relationship to Roles

Authorship complements roles: roles define **how an agent behaves** in different contexts; authorship defines **what authority that agent has over intent itself**. An agent in "architect" role might have authority to create new intents (`can_create: true`), while in "implementer" role it can only modify implementation sections.

#### Relationship to Evaluation

Authorship is the **governance layer** for the evaluation loop. When evaluation identifies an improvement, the `adjustment.authority` in the evaluation section must respect the `ai_authority` declared in authorship. If authorship says the AI cannot modify constraints, the evaluation loop cannot relax constraints even if quality would improve.

---

### Optional Section: Evaluation (Continuous Improvement Loop) *(Experimental)*

IVD verification answers: **does the output pass the constraints?** That's binary — pass or fail. But production systems need more: **how good is the output, and how can it improve?**

The **optional `evaluation` section** formalizes the continuous improvement loop: evaluate output quality → identify weakness → propose adjustment → verify the adjustment doesn't violate constraints → apply.

> **Status: Experimental** — This section is being validated. Apply it to real workflows with measurable quality and report results to help promote it to canonical.

#### When to Use

Use the `evaluation` section when:
- **Autonomous workflows** that run repeatedly and should improve over iterations
- **Self-improving agents** that adjust their own process based on output quality
- **Production systems** with quality feedback loops (precision, latency, user satisfaction)
- **AI-designed workflows** where the agent needs to evaluate and refine its own design

Skip this section when:
- One-shot implementations with no iteration cycle
- Task-level intents (too granular for an improvement loop)
- Standard verification (constraints + tests) is sufficient — quality isn't measured on a spectrum
- The system has no feedback mechanism to measure quality

#### What It Provides

The `evaluation` section documents:
- **Criteria:** What quality metrics are measured and their targets (continuous, not binary)
- **Adjustment:** Who has authority to make improvements, what can be changed, and what's protected
- **Cycle:** When evaluation triggers, how many iterations are allowed, when to stop, and when to escalate

#### Why It Matters

Without a formalized evaluation loop:
- **Quality improvement is ad-hoc** — "make it better" with no structure or stopping condition
- **No guardrails on adjustment** — the improvement process might break constraints
- **Infinite iteration risk** — no max_iterations, no escalation, the system loops forever
- **No separation between what CAN and CANNOT change** — improvements might modify the goal itself

This section makes improvement:
- **Structured:** Evaluate → adjust → re-verify is a defined cycle, not informal iteration
- **Bounded:** max_iterations prevents infinite loops; stop_when defines success
- **Safe:** Protected fields cannot be modified by the evaluation loop
- **Escalatable:** When the loop can't improve enough, humans are notified
- **Verifiable:** Evaluation criteria are testable metrics, not aspirational goals (Principle 2)

#### Example Structure

```yaml
evaluation:
  criteria:
    - metric: "classification_precision"
      target: ">= 0.90"
      source: "automated"              # automated | human_review | hybrid
    - metric: "end_to_end_latency"
      target: "p95 < 2s"
      source: "automated"
    - metric: "constraint_pass_rate"
      target: "100%"
      source: "ivd_validate"

  adjustment:
    authority: "ai_proposed"            # human_only | ai_proposed | ai_autonomous
    scope:                              # what CAN be adjusted
      - "implementation"
      - "workflow_steps"
      - "model_parameters"
    protected:                          # what CANNOT be adjusted
      - "intent.goal"
      - "intent.success_metric"
      - "constraints"

  cycle:
    trigger: "on_completion"            # on_completion | on_failure | scheduled | continuous
    max_iterations: 3
    stop_when: "All criteria met or max_iterations reached"
    escalate_when: "Cannot meet criteria after max_iterations"
```

#### The Key Distinction: Verification vs. Evaluation

```
VERIFICATION   → "Does the output pass the constraints?"         (binary: yes/no)
EVALUATION     → "How good is the output? How can it improve?"   (continuous: 0.78 → 0.85 → 0.92)
```

Verification is a gate. Evaluation is a loop. Verification asks pass/fail. Evaluation asks how much better. Both are anchored to intent — but evaluation extends verification with quality measurement, adjustment authority, and bounded iteration.

**Critical rule:** Evaluation NEVER relaxes constraints. Constraints are the floor. Evaluation improves quality above the floor.

#### Relationship to Authorship

The evaluation loop's `adjustment.authority` must respect the authorship section's `ai_authority`. If authorship declares that the AI cannot modify constraints, evaluation cannot relax constraints. If authorship says changes need human review, evaluation proposes adjustments but doesn't apply them until approved.

```
AUTHORSHIP    → Who can change intent, and what fields are protected
EVALUATION    → How to improve quality within those boundaries
```

They work together: authorship sets the rules; evaluation operates within them.

#### Relationship to Constraints

Constraints and evaluation criteria serve different purposes:

```
CONSTRAINTS     → Binary guardrails: "precision >= 85% or fail"
EVALUATION      → Quality targets: "precision is 87%, can we reach 92%?"
```

Constraints define the minimum. Evaluation drives toward the optimum. The evaluation loop cannot change constraints — only improve quality within them.

---

### Intent Levels: System, Workflow, Module, Task

**IVD supports four levels of intent granularity** to match different documentation needs:

```
SYSTEM LEVEL      →  Entire product or platform
    ↓
WORKFLOW LEVEL    →  Multi-step process (NEW in v1.2)
    ↓
MODULE LEVEL      →  Feature, agent, component
    ↓
TASK LEVEL        →  Function, method, API endpoint
```

---

#### System-Level Intents

**For:** Entire products, platforms, or strategic initiatives

**Characteristics:**
- Broad scope (entire product/platform)
- Multiple stakeholders
- Phases and milestones
- High-level success metrics

**Example:** Product development roadmap, multi-quarter platform migration

**File location:** `system_intent.yaml` or `{project}_system_intent.yaml` at repository root

---

#### Workflow-Level Intents (NEW in v1.2)

**For:** Multi-step processes that span multiple modules or functions

**Characteristics:**
- Documents end-to-end process flow
- Maps each step to specific files/functions
- Captures business logic at each step
- Defines error handling and data flow
- **Critical for AI agent understanding**

**Example:** Lead qualification workflow (validate → enrich → score → qualify → sync to CRM)

**File location:**
- **Recommended:** `workflows/{workflow_name}_intent.yaml`
  - *Why:* Centralized location enables `find workflows/ -name "*_intent.yaml"` discovery
  - *AI benefit:* Single search location, lower token cost, consistent context
- **Alternative:** Alongside coordinator file
  - *When:* Workflow is tightly coupled to a single orchestrator AND will never be referenced independently
  - *Trade-off:* Harder to discover all workflows programmatically
- *Decision:* Use `workflows/` by default; use "alongside coordinator" only when the workflow has a single orchestrator and is not referenced elsewhere.

**Why workflow-level matters:**

Traditional documentation forces choice between:
- ❌ **Module-level** - Documents components, but not how they work together
- ❌ **Task-level** - Documents functions, but not the sequence

Workflow-level fills the gap:
- ✅ **End-to-end process** - Complete flow in one file
- ✅ **Step-by-step sequence** - Explicit execution order
- ✅ **File/function mapping** - Know exactly which code runs when
- ✅ **Business logic context** - Why each step exists
- ✅ **AI-friendly** - Agent reads ONE file to understand entire workflow
- ✅ **Cost reduction** - 80-90% less context needed for AI agents

**Workflow schema (key sections):**

```yaml
scope:
  level: "workflow"
  type: "process"

workflow:
  summary: "What this workflow accomplishes"
  trigger: "What initiates the workflow"
  
  steps:
    - step: 1
      name: "Descriptive step name"
      file: "path/to/module.py"
      function: "function_name()"
      description: "What this step does"
      input: "What data comes in"
      output: "What data goes out"
      business_logic: "Key rules and decisions"
      
    - step: 2
      name: "Next step"
      file: "path/to/another_module.py"
      # ... and so on
  
  data_flow:
    - "High-level data transformations"
    - "Input → Step 1 → Step 2 → ... → Output"
  
  error_handling:
    - step: 1
      failure_mode: "What can go wrong"
      action: "What happens when it fails"
      fallback: "Alternative behavior"
  
  orchestration:
    type: "sequential | parallel | mixed"
    coordinator: "path/to/coordinator.py"
```

**When to create workflow intent:**
- Process has 3+ distinct steps across multiple files
- AI agents ask "how does this work end-to-end?"
- Onboarding requires understanding the full flow
- Business stakeholders need technical workflow visibility

**Real-world examples:**
- Lead qualification (5 steps: receive → enrich → score → qualify → sync)
- Article generation (7 steps: trigger → plan → research → draft → fact-check → images → publish)
- ETL pipeline (4 steps: extract → transform → validate → load)
- Order processing (6 steps: receive → validate → inventory check → payment → fulfillment → notification)

**See:** `templates/examples/workflow-lead-qualification-example.yaml` for complete example  
**Recipe:** `recipes/workflow-orchestration.yaml` for workflow pattern template

---

#### Module-Level Intents

**For:** Features, agents, components with clear boundaries

**Characteristics:**
- Medium scope (feature-level)
- Single module or feature
- Business logic decisions
- Architecture choices
- Integration points

**Example:** Lead qualifier agent, fact checker agent, background job processor

**File location:** `{module}/{module}_intent.yaml` alongside implementation

**Note:** For tooling compatibility (MCP tools use glob `**/*_intent.yaml`), module intents must use the `{module}_intent.yaml` pattern. A bare `intent.yaml` without the module name prefix will not be discovered by `ivd_find_artifacts` or `ivd_list_features`.

---

#### Task-Level Intents

**For:** Individual functions, methods, or API endpoints

**Characteristics:**
- Fine scope (function-level)
- Single function/task
- Clear inputs/outputs
- Specific behavior contract
- Edge cases matter

**Example:** `qualify_lead()` function, `extract_claims()` function, `POST /api/leads` endpoint

**File location:** `{module}/intents/{function}_intent.yaml`
  - *Why:* Subdirectory prevents module clutter; clear separation from module-level intent
  - *AI benefit:* `find */intents/ -name "*_intent.yaml"` finds all task-level intents
  - *Tooling:* Tools detect task-level by `intents/` in path; flat placement not supported by discovery tools

---

#### Multi-Intent Naming Convention

A module may require multiple intent artifacts for variants, personas, or configurations:

| Pattern | Use Case | Example | Discovery Pattern |
|---------|----------|---------|-------------------|
| `{module}_intent.yaml` | Primary module intent | `reviewer_intent.yaml` | `{module}_intent.yaml` |
| `{variant}_{module}_intent.yaml` | Variant (persona, config) | `erik_reviewer_intent.yaml` | `*_{module}_intent.yaml` |
| `intents/{function}_intent.yaml` | Task-level intents | `intents/review_article_intent.yaml` | `intents/*_intent.yaml` |

**Naming Rules:**
1. **Primary intent** uses bare module name: `{module}_intent.yaml`
2. **Variants** prepend descriptor: `{variant}_{module}_intent.yaml`
3. **Task-level** uses `intents/` subdirectory: `intents/{function}_intent.yaml`

**AI Agent Discovery:**
```bash
# Find all module-level intents (primary + variants):
find agent/ -maxdepth 2 -name "*_intent.yaml" ! -path "*/intents/*"

# Find all task-level intents:
find agent/ -path "*/intents/*_intent.yaml"

# Find all variants of a specific module:
find agent/reviewer/ -name "*_reviewer_intent.yaml"
```

**Why variants exist:**
- Multiple personas (Erik reviewer vs Sarah reviewer)
- Configuration variants (strict vs lenient)
- Experimental vs production intents

---

#### Level Selection Guide

**Default to MODULE-level** unless:
- ✅ System-level: Multiple teams, multi-quarter scope, strategic initiative
- ✅ Workflow-level: 3+ steps across multiple modules, AI needs process understanding
- ✅ Task-level: Critical function used across modules, complex I/O contract, public API

**The rule:** Use the **highest level** that captures necessary detail.

**Example hierarchy:**

```
SYSTEM: AI Development Book (book_system_intent.yaml)
  └─ WORKFLOW: Meeting extraction workflow (workflows/meeting_extraction_intent.yaml)
      ├─ MODULE: Meeting extractor agent (agent/meeting_extractor/meeting_extractor_intent.yaml)
      │   └─ TASK: extract_insights() function (agent/meeting_extractor/intents/extract_insights_intent.yaml)
      └─ MODULE: Fact checker agent (agent/fact_checker/fact_checker_intent.yaml)
```

**See:** `templates/intent_levels_guide.md` for complete guide on level selection

---

### Intent Coverage Assessment

For **existing projects (brownfield)**, understanding which modules already have intent artifacts—and which don't—is essential before deciding where to invest effort. IVD provides a dedicated tool for this.

#### How It Works

`ivd_assess_coverage` scans a project's directory structure, discovers all `*_intent.yaml` and `*_system_intent.yaml` artifacts, maps them to code directories, and produces a structured report:

- **System-level:** Does the project have a system intent?
- **Module-level:** Which code directories have a co-located intent? Which don't?
- **Coverage %:** Ratio of covered modules to coverable modules.
- **Priority suggestions:** Uncovered modules ranked by heuristic priority (high: API, auth, agents, services, or 5+ code files; medium: 3–4 files; low: fewer).

#### Coverage Levels

| Depth | What it checks |
|-------|----------------|
| `module` (default) | System intent + module-level coverage |
| `full` | System + workflow + module + task-level coverage |

#### When to Use

- **Brownfield adoption:** After `ivd init` and enriching the system intent, run `ivd_assess_coverage` to see where intent exists and where it doesn't. Use the report to prioritize which modules get intents first.
- **Periodic check-in:** Re-run periodically to track coverage progress as the team adds intents incrementally.
- **Onboarding:** New team members can see at a glance which parts of the codebase have explicit intent documentation.

#### Tool Usage

```
# Default: module-level coverage with suggestions
ivd_assess_coverage(project_root="/path/to/project")

# Full depth: includes workflow and task-level analysis
ivd_assess_coverage(project_root="/path/to/project", depth="full")

# Without suggestions (just the data)
ivd_assess_coverage(project_root="/path/to/project", include_suggestions=False)
```

#### Example Output (summary)

```json
{
  "summary": {
    "has_system_intent": true,
    "total_coverable_modules": 8,
    "covered_modules": 3,
    "uncovered_modules": 5,
    "coverage_percent": 37.5,
    "total_intent_artifacts": 5
  },
  "covered": [...],
  "uncovered": [
    {"path": "agent/auth", "code_files": 6, "priority": "high"},
    {"path": "agent/reporting", "code_files": 3, "priority": "medium"}
  ],
  "suggestions": [
    {"action": "Create module-level intents for 2 high-priority module(s)", "priority": "high"}
  ]
}
```

#### AI Agent Workflow

When an AI agent is asked to help adopt IVD in an existing project:

1. Run `ivd_init` → creates system intent with project context
2. Run `ivd_assess_coverage` → structured coverage report
3. Interpret the report: focus on high-priority uncovered modules first
4. Use `ivd_scaffold` for those modules, referencing `parent_intent`
5. Re-run `ivd_assess_coverage` periodically to track progress

#### Coverage ≠ 100%

Not every directory needs an intent artifact. Intent belongs where it adds value:

- **Critical business logic** (auth, payments, scoring)
- **Complex modules** with many code files or non-obvious behavior
- **Team boundaries** where different people or agents work on different parts
- **Frequently changed code** where intent prevents drift

Simple utility directories, configuration, or stable code that rarely changes may not need explicit intent.

---

## Recipes: Reusable Patterns

### What is an IVD Recipe?

**NEW in IVD v1.1:** Recipes are reusable pattern templates that capture how to solve common development problems.

**The key distinction:**

| Intent Artifact | Recipe |
|----------------|--------|
| **Specific** to one implementation | **Reusable** across many implementations |
| Documents "what we built" | Documents "how to build similar things" |
| Lives next to code | Lives in recipes directory |
| Changes with that module | Changes when pattern improves |
| Example: `lead_scorer_intent.yaml` | Example: `agent-classifier.yaml` |

---

### Why Recipes Matter

**The problem recipes solve:**

Without recipes:
- Every developer reinvents solutions to common problems
- Patterns exist in developers' heads, not documented
- New team members learn slowly through trial and error
- Quality varies wildly across similar implementations
- Best practices don't propagate

With recipes:
- ✅ Start from proven patterns
- ✅ Consistent approach to similar problems
- ✅ Faster development (template vs from scratch)
- ✅ Best practices built in
- ✅ Knowledge sharing across team

---

### Recipe Structure

```yaml
# recipe_[pattern_name].yaml

recipe:
  name: "Pattern Name"
  description: "What problem this solves"
  when_to_use: [...]
  when_NOT_to_use: [...]

# Template sections (filled in for specific implementation)
intent_template: {...}
constraints_template: {...}
rationale_template: {...}
alternatives_template: {...}
risks_template: {...}

# Pattern guidance
implementation_pattern: {...}
verification_pattern: {...}
best_practices: [...]
common_pitfalls: [...]

# Real examples
examples: [...]
```

**Full specification:** See `recipe-spec.md`

---

### Recipe Categories

**1. Workflow Patterns** (NEW in v1.2) - Multi-step processes
- `workflow-orchestration.yaml` - Process orchestration (lead qualification, ETL, etc.)
- `workflow-pipeline.yaml` - Data pipelines
- `workflow-event-driven.yaml` - Event-driven workflows

**2. Agent Patterns** - Building AI agents
- `agent-classifier.yaml` - Classification agents
- `agent-extractor.yaml` - Data extraction
- `agent-coordinator.yaml` - Orchestration
- `agent-fact-checker.yaml` - Fact verification

**3. Integration Patterns** - External system integration
- `recipe_api_integration.yaml` - REST API integrations
- `recipe_webhook_handler.yaml` - Webhook processing
- `recipe_database_sync.yaml` - Database synchronization

**4. Data Patterns** - Data processing
- `recipe_data_validation_pipeline.yaml` - Data quality
- `recipe_etl_workflow.yaml` - Extract, transform, load
- `recipe_batch_processor.yaml` - Batch processing

**5. Infrastructure Patterns** - Operations
- `infra-monitoring.yaml` - Observability
- `infra-background-job.yaml` - Async job processing
- `infra-retry.yaml` - Resilience patterns

---

### How Recipes and Intent Artifacts Work Together

```
RECIPE (reusable pattern)
    ↓
Provides template structure
    ↓
INTENT ARTIFACT (specific implementation)
    ↓
References recipe, fills in specifics
    ↓
IMPLEMENTATION (code)
    ↓
Follows pattern from recipe
    ↓
VERIFICATION (tests)
    ↓
Validates constraints from intent
```

**Example:**

```yaml
# recipes/agent-classifier.yaml
# This is the REUSABLE PATTERN

recipe:
  name: "AI Classifier Agent Pattern"
  applies_to:
    - "Classification requiring context understanding"
    - "Quality thresholds are critical"
    
intent_template:
  summary: "[Domain] classifier for [use case]"
  goal: "Classify [items] into [categories] for [stakeholder]"
  success_metric: "[Metric] >= [target]%"
  
constraints_template:
  - name: "classification_accuracy"
    requirement: "accuracy >= [0.80-0.95 typical]"
    test: "tests/test_[module]_accuracy.py"
```

```yaml
# agent/lead_scorer/scorer_intent.yaml
# This is the SPECIFIC IMPLEMENTATION

recipe: "agent-classifier"  # ← Links to pattern
recipe_version: "1.0"

# Now fill in the template with specifics:
intent:
  summary: "Lead scoring classifier for CRM"  # Specific
  goal: "Classify leads as qualified/unqualified for sales team"  # Specific
  success_metric: "Precision >= 85%"  # Specific
  stakeholders: ["VP Sales (Jane Smith)"]  # Specific

constraints:
  - name: "classification_accuracy"
    requirement: "precision >= 0.85"  # Specific (recipe said 0.80-0.95 typical)
    test: "tests/test_scorer_accuracy.py"  # Specific
    consequence_if_violated: "Sales team wastes time on unqualified leads"  # Specific
```

---

### Using Recipes

**Step 1: Find the right recipe**
```bash
ivd recipe list
ivd recipe search "classifier"
```

**Step 2: Apply recipe to your implementation**
```bash
# Copy intent template
cp templates/intent.yaml agent/my_classifier/my_classifier_intent.yaml

# Reference recipe in my_classifier_intent.yaml:
# recipe: "agent-classifier"
# recipe_version: "1.0"
```

**Step 3: Fill in specifics**

Generated intent artifact has:
- ✅ Structure from recipe (complete)
- 🔲 Placeholders for your specifics (fill these in)
- 📝 Comments explaining what to provide

**Step 4: Implement following the pattern**

Recipe provides:
- Directory structure
- Code structure
- Key files and functions
- Best practices
- Common pitfalls to avoid

---

### Creating New Recipes

**When to create a recipe:**
- ✅ You've solved the same problem 2-3 times
- ✅ Pattern is generalizable across domains
- ✅ Other teams could benefit
- ✅ Onboarding would be faster with this template

**Recipe creation:**
```bash
ivd recipe create \
  --from-intent agent/successful_module/module_intent.yaml \
  --name recipe_my_pattern
```

---

### Recipe Evolution

Recipes improve over time:

```yaml
changelog:
  - version: "1.2"
    date: "2026-02-15"
    change: "Added error handling best practices"
    reason: "Production incidents revealed missing error cases"
    
  - version: "1.1"
    date: "2026-01-30"
    change: "Added performance optimization patterns"
    reason: "Performance issues in 3 implementations"
```

**Recipe versioning ensures:**
- Old intent artifacts still reference their recipe version
- New implementations get latest best practices
- Evolution is documented and traceable

---

### Benefits of Recipes

**For Developers:**
- 🚀 Faster development (start from proven pattern)
- 📚 Learn patterns quickly
- ✅ Higher quality (recipes include best practices)
- 🎯 Consistency across similar implementations

**For Teams:**
- 📖 Knowledge sharing (patterns documented)
- 🔄 Consistency (similar problems solved similarly)
- ⚡ Onboarding (new devs learn patterns fast)
- 📈 Quality improvement (recipes evolve with lessons)

**For Organization:**
- 💰 Reduced development cost (less reinvention)
- 📊 Standardization (predictable patterns)
- 🛡️ Risk reduction (proven patterns)
- 🎓 Institutional knowledge (patterns preserved)

---

## Verification System

### Continuous Verification Commands

```bash
# Verify single module
$ ivd verify agent/lead_qualifier

# Verify entire codebase
$ ivd verify --all

# Verify before commit
$ ivd verify --staged

# Deep verification (re-run experiments)
$ ivd verify --deep agent/lead_qualifier
```

---

### What Gets Verified

| Check | Verifies |
|-------|----------|
| **Intent exists** | Module has declared intent |
| **Implementation matches** | Code implements what intent declares |
| **Constraints hold** | Tests validate all stated constraints |
| **Evidence is current** | Linked experiments/notebooks still run |
| **Alternatives documented** | Rejected approaches are recorded |
| **Risks monitored** | Monitoring exists for stated risks |
| **Documentation synced** | Docs reflect current intent |
| **Tests comprehensive** | Coverage matches intent scope |

---

### Verification Reports

```
INTENT VERIFICATION REPORT
Module: agent/lead_qualifier/scoring.py
Intent Artifact: scoring_intent.yaml v3

✅ ALIGNMENT CHECKS
   Code threshold (0.70) matches intent ✓
   Function signature matches intent ✓
   Edge cases handled per intent ✓

✅ CONSTRAINT VALIDATION
   precision >= 0.80: PASS (actual: 0.85)
   recall >= 0.60: PASS (actual: 0.70)

✅ EVIDENCE VERIFICATION
   playground/lead_analysis_2025-12.ipynb:
   - Last run: recently
   - Results match rationale ✓
   - All cells executed successfully ✓

⚠️  RISK MONITORING
   Risk: "precision drops below 0.75"
   Current: 0.82 (within safe range)
   Status: MONITORING (approaching threshold)
   Action: Continue monitoring, no intervention needed

✅ DOCUMENTATION SYNC
   Design doc reflects current intent ✓
   ADR-089 matches decision ✓
   Comments in code cite intent artifact ✓

OVERALL: VERIFIED ✓
Confidence: 95%
Last verified: 2026-01-23 14:30:00 UTC
```

---

## Implementation Guide

### Step 0a: Teaching When You Don't Understand the Domain *(Optional)*

**When:** You lack the technical knowledge to understand concepts, patterns, or technologies needed for the task.

**Signals:**
- You say "I don't know what X is" or "Can you explain Y?"
- You're reviewing intent but can't understand patterns it references (Saga, CDC, etc.)
- You're new to the domain/codebase and see unfamiliar concepts
- Discovery proposed options but you don't understand the terminology

**Process:**
1. **AI detects knowledge gap** (you ask explicitly, or AI detects from your language/context)
2. **AI offers:** "Would you like me to explain [concept] first?"
3. **AI creates educational artifact** (structured YAML) explaining:
   - What the concept is
   - Why it matters for your task
   - Key sub-concepts with examples
   - Tradeoffs (decisions you'll need to make, options with pros/cons)
   - Common patterns
   - Verification questions (to confirm you understand)
4. **You review**, ask clarifying questions, confirm understanding
5. **Proceed:** Now with the knowledge, continue to Step 0b (if needed) or Step 1

**Example:**

```yaml
education:
  concept: "ETL (Extract, Transform, Load)"
  what_it_is: |
    ETL is a data pipeline pattern: Extract data from sources, Transform it to
    match target schema/business rules, Load it into a destination system.
  
  why_it_matters_here: |
    Your project needs to sync lead data from Salesforce to PostgreSQL daily.
  
  key_concepts:
    - name: "Extract"
      definition: "Read data from source system (API, database, file)"
      example: "Pull leads from Salesforce REST API"
    
    - name: "Transform"
      definition: "Apply business rules, normalize schema"
      example: "Convert Salesforce Status to lead_stage enum"
    
    - name: "Load"
      definition: "Write data to destination"
      example: "UPSERT into PostgreSQL analytics.leads table"
  
  tradeoffs:
    - decision: "Batch vs Streaming"
      options:
        - name: "Batch"
          when: "Daily/hourly sync acceptable"
          pros: ["Simpler", "Lower cost"]
          cons: ["Data lag (hours)"]
  
  verification:
    - question: "What are the 3 steps of ETL?"
      answer: "Extract, Transform, Load"
```

**Tools:** `ivd_teach_concept(concept="ETL", user_context="sync Salesforce leads daily")`

**Recipe:** `recipes/teaching-before-intent.yaml`

**Why this matters:** Lack of technical knowledge is the main bottleneck in project critical paths. You can't review intent if you don't understand the concepts it references.

---

### Step 0b: Discovery When You're Not Sure What to Build *(Experimental, Optional)*

**When:** You don't know *what* to build (goal uncertainty), but you have the technical knowledge to evaluate options once presented.

**Note:** If you lack the technical knowledge to understand the *options* themselves, use Step 0a (Teaching) first.

**Signals:**
- You say "I'm not sure what we need" or "What are the options?"
- New domain or unfamiliar codebase
- Exploring what's possible before committing

**Process:**
1. **AI detects** need for discovery
2. **AI proposes** 2–3 candidate directions (from recipes, existing features, inversion ideas)
3. **You pick or refine** ("that one, but for X not Y")
4. **Proceed:** Now with a direction, continue to Step 1 (describe → AI writes intent)

**Tools:** `ivd_discover_goal(domain_or_context="data_export", user_hint="compliance")`

**Recipe:** `recipes/discovery-before-intent.yaml`

---

### Step 0: Installing IVD in an Existing Project (Brownfield)

**When adopting IVD in an existing project with code and docs already in place:**

```bash
# 1. Initialize IVD - creates system intent with project context
$ ivd init --project-root /path/to/your/project

Scanning project...
- Found: .cursorrules
- Found: docs/ARCHITECTURE.md
- Found: scripts/ (5 scripts)
- Found: agent/ (3 agents)
- Found: docs/ (10 docs)

Generated: system_intent.yaml

Project context captured:
✓ Code rules: .cursorrules, pyproject.toml
✓ Architecture: docs/ARCHITECTURE.md, 3 ADRs
✓ Tools/scripts: 5 scripts in scripts/
✓ Key paths: entrypoints, modules, workflows, docs, tests
✓ Existing docs: README.md, API.md, CONTRIBUTING.md

Next steps:
1. Review and enrich system_intent.yaml
2. Assess coverage: ivd_assess_coverage → see which modules need intents
3. Create intents for high-priority modules (ivd scaffold)
4. Reference parent_intent: "../../system_intent.yaml" in child intents
```

**The workflow for existing projects:**

1. **Discover:** Run `ivd init` to scan project and create system_intent.yaml
2. **Enrich:** Review and add architecture principles, conventions not auto-detected
3. **Assess coverage:** Run `ivd_assess_coverage` to see which modules have intents and which don't (prioritized)
4. **Create:** Use `ivd scaffold` for high-priority uncovered modules, referencing parent_intent
5. **Expand:** Gradually add intents for more modules as you modify them; re-run `ivd_assess_coverage` periodically to track progress

**Key differences from greenfield:**
- **System intent first:** Capture existing conventions and "map to the stars" (key paths)
- **Reference parent:** Child intents reference system intent via `parent_intent`
- **Reuse, don't duplicate:** New intents reference existing tools, scripts, libraries
- **Incremental:** Don't create intents for entire codebase at once; start with critical paths
- **Agent rules:** If `.cursorrules` or equivalent agent instruction file exists, add the IVD verification rules (see below)

#### Agent Rules as IVD Integration Surface

AI agent instruction files (`.cursorrules`, `.clinerules`, Copilot system prompts, Aider configuration) are the **runtime enforcement point** for IVD. Without IVD rules in the agent's instructions, nothing enforces the post-implementation verification protocol — the agent implements and moves on.

When `ivd init` scans a project and finds `.cursorrules` or equivalent, it suggests adding the IVD rules block. The block enforces three rules:

1. **Intent Before Implementation:** Read the intent artifact before implementing; understand constraints and test paths.
2. **Post-Implementation Verification Protocol:** After implementation, execute the 4-step audit (re-read intent → diff against constraints → check test paths → report PASS/FAIL/NEEDS_REVIEW).
3. **Constraint Tests Are Mandatory:** Every constraint must have a `test` field. A constraint without a test is an unverifiable claim.

See `recipes/agent-rules-ivd.yaml` for the complete rules block in `.cursorrules`, `.clinerules`, and Copilot formats.

---

### Step 1: Create Intent Artifact for Existing Module

**For a module that already exists:**

```bash
$ ivd intent create agent/lead_qualifier/scoring.py

Analyzing: agent/lead_qualifier/scoring.py

Found threshold: 0.70
Found data_quality check: 0.80

Searching for rationale...
- Checking git history... found commit
- Checking playground/... found lead_analysis_2025-12.ipynb
- Checking docs/... found partial explanation

Loading project context from system_intent.yaml...
- Code rules: .cursorrules (loaded)
- Architecture principles: Event-driven, no direct DB access
- Reusable libraries: internal/auth_utils, internal/logging

Generated: scoring_intent.yaml

Please review and complete:
- [✓] Intent goal extracted
- [✓] Constraints identified from code
- [✓] Evidence linked from git/playground
- [✓] Parent intent: ../../system_intent.yaml (auto-linked)
- [✓] Project context: code rules, architecture loaded
- [?] Stakeholder approval (needs human input)
- [?] Alternatives (needs human input)
- [?] Risk monitoring (needs human input)
```

---

### Step 2: Validate and Enrich

**Human reviews generated intent artifact:**

```yaml
# scoring_intent.yaml (generated, needs review)

intent:
  summary: "Qualify leads based on score and data quality"
  goal: "Filter leads to sales team to maximize conversion rate"
  success_metric: "???" # ← NEEDS INPUT
  stakeholders: ["???"] # ← NEEDS INPUT

constraints:
  - name: "score_threshold"
    requirement: "score >= 0.70"
    test: "tests/test_scoring.py::test_threshold" # ← Verify this exists
    
rationale:
  decision: "threshold = 0.70"
  evidence: "playground/lead_analysis_2025-12.ipynb" # ← Found automatically
  date: "2025-12-15" # ← From git
  stakeholder: "???" # ← NEEDS INPUT

alternatives: [] # ← NEEDS INPUT

risks: [] # ← NEEDS INPUT
```

**Human completes missing pieces:**

```yaml
intent:
  success_metric: "Sales conversion rate >= 15%"
  stakeholders: ["VP Sales", "Sales Operations"]

rationale:
  stakeholder: "VP Sales (Jane Smith)"

alternatives:
  - name: "threshold_0.60"
    rejected_because: "Sales feedback: too many low-quality leads"
    date_tested: "2025-12-01"
  - name: "threshold_0.80"
    rejected_because: "Insufficient pipeline volume"
    date_tested: "2025-12-01"

risks:
  - condition: "precision drops below 0.75"
    action: "Alert sales leadership"
    monitor: "dashboards/lead_quality.json"
    severity: "high"
```

---

### Step 3: Enable Continuous Verification

**Add to CI/CD:**

```yaml
# .github/workflows/verify.yml

name: Intent Verification
on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Verify Intent Alignment
        run: |
          ivd verify --all
          ivd verify --deep --changed-only
```

**Add pre-commit hook:**

```bash
# .git/hooks/pre-commit
#!/bin/bash
ivd verify --staged || exit 1
```

---

### Step 4: Update Intent When Code Changes

**Workflow:**

```
Developer changes threshold: 0.70 → 0.75

$ git add agent/lead_qualifier/scoring.py
$ git commit -m "Increase threshold to 0.75"

[Pre-commit hook runs]
❌ Intent verification FAILED:
   - Code says threshold = 0.75
   - Intent says threshold = 0.70
   - DRIFT DETECTED

Choose action:
1. Update intent to match code (threshold → 0.75)
2. Revert code to match intent (threshold → 0.70)
3. Skip verification (not recommended)

> 1

Updating scoring_intent.yaml...
Re-running validation experiments...
Updating documentation...

✅ Intent updated and verified
✅ Commit proceeding
```

---

## Real-World Example

### Before IVD (Traditional)

```python
# agent/lead_qualifier/scoring.py

def qualify_lead(score: float, data_quality: float) -> bool:
    """Qualify lead based on score and data quality."""
    if score >= 0.70 and data_quality >= 0.80:
        return True
    return False
```

**Problems:**
- No explanation of WHY 0.70 and 0.80
- No link to validation evidence
- No record of alternatives considered
- No way to verify understanding matches reality
- Knowledge lost when developer leaves

---

### After IVD

**Intent Artifact:**

```yaml
# agent/lead_qualifier/lead_qualifier_intent.yaml

intent:
  summary: "Qualify high-probability leads for sales team"
  goal: |
    Filter pipeline to send only leads with high conversion probability
    to sales team. Balance quality (minimize wasted sales time) vs
    quantity (maintain sufficient pipeline for revenue goals).
  success_metric: "Sales conversion rate >= 15%"
  stakeholders: ["VP Sales (Jane Smith)", "Sales Operations"]

constraints:
  - name: "minimum_precision"
    requirement: "precision >= 0.80"
    test: "tests/test_lead_qualification.py::test_precision_threshold"
    consequence_if_violated: "Sales team wastes time on low-quality leads"
    
  - name: "minimum_recall"
    requirement: "recall >= 0.60"
    test: "tests/test_lead_qualification.py::test_recall_threshold"
    consequence_if_violated: "Insufficient pipeline volume for revenue goals"

rationale:
  decision: |
    Score threshold: 0.70
    Data quality threshold: 0.80
    Both must pass for qualification
  evidence: "playground/lead_analysis_2025-12.ipynb"
  date: "2025-12-15"
  stakeholder: "VP Sales (Jane Smith)"
  methodology: |
    Tested thresholds 0.60, 0.65, 0.70, 0.75, 0.80 on 500 historical leads.
    Measured precision, recall, and gathered sales team feedback.
    0.70 provided best balance: 85% precision, 70% recall.

alternatives:
  - name: "rule_based_classification"
    rejected_because: "Too brittle, couldn't adapt to changing lead characteristics"
    experiment: "playground/rule_based_comparison_2025-11.ipynb"
    date_tested: "2025-11-15"
    
  - name: "ml_classifier_v1"
    rejected_because: "Overfitting on training data, poor generalization"
    experiment: "playground/ml_classifier_eval_2025-12.ipynb"
    date_tested: "2025-12-01"
    
  - name: "threshold_0.60"
    rejected_because: "Only 75% precision - sales feedback negative"
    experiment: "playground/threshold_comparison_2025-12.ipynb"
    date_tested: "2025-12-10"
    
  - name: "threshold_0.80"
    rejected_because: "Only 50% recall - insufficient pipeline volume"
    experiment: "playground/threshold_comparison_2025-12.ipynb"
    date_tested: "2025-12-10"

risks:
  - condition: "precision drops below 0.75"
    action: "Alert VP Sales, review threshold increase"
    monitor: "dashboards/lead_quality.json"
    severity: "high"
    
  - condition: "recall drops below 0.50"
    action: "Alert Sales Ops, review threshold decrease"
    monitor: "dashboards/pipeline_volume.json"
    severity: "medium"
    
  - condition: "market conditions change significantly"
    action: "Re-run validation experiment, consider re-tuning"
    monitor: "quarterly review"
    severity: "medium"

implementation:
  current: "agent/lead_qualifier/scoring.py"
  version: 3
  tests: "tests/test_lead_qualification.py"
  documentation: "docs/agents/lead_qualifier_DESIGN.md"
  deployment: "production since 2025-12-20"

changelog:
  - version: 3
    date: "2025-12-15"
    change: "Implemented statistical threshold with data quality gate"
    reason: "ML classifier overfitted, rule-based too brittle"
    evidence: "playground/approach_comparison_2025-12.ipynb"
    approved_by: "VP Sales (Jane Smith)"
    
  - version: 2
    date: "2025-12-01"
    change: "Attempted ML classifier"
    reason: "Wanted adaptive classification"
    deprecated: "2025-12-15"
    deprecated_reason: "Overfitting issues"
    
  - version: 1
    date: "2025-11-01"
    change: "Initial rule-based implementation"
    deprecated: "2025-12-01"
    deprecated_reason: "Too brittle for changing data"
```

**Implementation (Clean):**

```python
# agent/lead_qualifier/scoring.py
# Intent: scoring_intent.yaml v3

from typing import Tuple

# Constants from intent artifact
SCORE_THRESHOLD = 0.70  # See scoring_intent.yaml for rationale
DATA_QUALITY_THRESHOLD = 0.80

def qualify_lead(score: float, data_quality: float) -> bool:
    """
    Qualify lead for sales team.
    
    Full intent and rationale in: scoring_intent.yaml
    
    Constraints (verified in tests):
    - Precision >= 0.80
    - Recall >= 0.60
    
    Args:
        score: Predictive score (0.0-1.0) from lead scoring model
        data_quality: Data completeness score (0.0-1.0)
    
    Returns:
        True if lead qualifies, False otherwise
    """
    return (
        score >= SCORE_THRESHOLD and
        data_quality >= DATA_QUALITY_THRESHOLD
    )
```

**Verification:**

```bash
$ ivd verify agent/lead_qualifier/

✅ Intent artifact: scoring_intent.yaml v3
✅ Implementation matches: thresholds correct
✅ Constraints satisfied:
   - precision = 0.85 (>= 0.80) ✓
   - recall = 0.70 (>= 0.60) ✓
✅ Evidence current: playground/lead_analysis_2025-12.ipynb (recently run)
✅ Tests: 12/12 passing ✓
✅ Risks monitored: dashboards configured ✓
⚠️  Note: precision at 0.82, within acceptable range but monitor trend

UNDERSTANDING VERIFIED ✓
Next review: 2026-04-01 (quarterly)
```

---

## Comparison Matrix

| Aspect | Traditional | Literate (Knuth) | Pragmatic LP | Intent-Verified |
|--------|-------------|------------------|--------------|-----------------|
| **Primary artifact** | Code | Documentation | Code + docs | Intent |
| **Understanding format** | Comments | Prose | Rich comments | Structured YAML |
| **Can diverge?** | Always | No (single source) | Yes (AI helps) | No (verified) |
| **Verification** | None | Manual reading | Manual review | Continuous automated |
| **AI role** | None | None | Synchronizer | Understanding partner |
| **Survives rewrites** | No | Tied to impl | No | Yes |
| **Tooling** | Standard | Specialized | Standard | Standard + verifier |
| **Adoption** | Universal | Failed | Growing | Experimental |
| **Knowledge capture** | 10-15% | 60-80% | 60-80% | 85-95% |

---

## Benefits

### For Development
- **Faster onboarding:** Intent artifacts provide complete context
- **Safer changes:** Verification catches when code drifts from intent
- **Better decisions:** Alternatives and rationale preserved
- **Less duplicate work:** Past experiments documented

### For Maintenance
- **Understanding persists:** Intent survives team turnover
- **Evolution tracked:** Changelog shows why things changed
- **Risks identified:** Know what monitoring is needed
- **Validation easy:** Can re-run evidence experiments

### For Collaboration
- **Clear contracts:** Intent declares what module should do
- **Better reviews:** Review intent alignment, not just code syntax
- **Stakeholder approval:** Link to business decisions
- **Cross-team clarity:** Other teams understand module purpose

---

## Challenges

### Initial Investment
- Creating intent artifacts for existing code takes time
- Requires discipline to maintain
- Team must learn new practices

### Tooling Gap
- `ivd verify` system doesn't exist yet (needs building)
- Integration with existing tools needed
- CI/CD pipelines need updates

### Cultural Shift
- Developers must think "intent first"
- Requires buy-in from entire team
- Management must value knowledge preservation

---

## Getting Started

### Start Small
Don't convert everything at once:

1. **Pick one critical module** with complex business logic (if you don't know what to build, use discovery first *(Experimental)*—see Step 0b and `recipes/discovery-before-intent.yaml`)
2. **Create intent artifact** for it
3. **Set up basic verification** (manual at first)
4. **Learn from experience**
5. **Expand gradually**

### Good Candidates for First Intent Artifacts
- Complex thresholds or validation rules
- Business logic with stakeholder approval
- Modules with high bug rates
- Code that confuses new developers
- Systems with compliance requirements

### Tools to Build
1. `ivd intent create` - Generate intent from existing code
2. `ivd verify` - Check alignment
3. Pre-commit hooks
4. CI/CD integration
5. Intent → documentation generator

---

## Future Vision

### Short Term (2026)
- Prototype `ivd verify` system
- Create intent artifacts for critical modules
- Document patterns and best practices
- Train team on IVD thinking

### Medium Term (2027)
- Full verification in CI/CD
- Intent artifacts as PR requirement for critical paths
- Automated intent drift detection
- Intent-aware code review tools

### Long Term (2028+)
- Industry adoption of intent artifacts
- IDE integration (intent-aware completion)
- AI that reasons about intent alignment
- Intent becomes standard part of codebases

---

## Extending IVD Framework

**Want to add a new intent level, section, or recipe pattern?**

### Master Framework Intent

All extensions to IVD must follow the rules defined in `ivd_system_intent.yaml`:

**The master intent documents:**
- **8 Core Principles** (immutable) - Each with sub-principles, validation checks, and rejection criteria
- **4 Extension Rules** - Adding intent levels, sections, recipes, and documentation standards
- **4 Validation Levels** - Principle alignment, structural integrity, verification coverage, real-world validation
- **Canonization Process** - 6 steps from proposal to canonical status
- **6 Immutable Constraints** - Rules that must always hold true

### Before Proposing a Change

**Read `ivd_system_intent.yaml` to understand:**

1. **What makes something canonical IVD?**
   - Must align with all 8 principles
   - Must pass all 4 validation levels
   - Must have comprehensive examples (500+ lines)
   - Must be validated in production

2. **What's the process for adding something?**
   - Identify gap (5+ real-world cases)
   - Design schema (structured YAML)
   - Create comprehensive example
   - Create recipe pattern (if applicable)
   - Update all core docs
   - Validate against all principles

3. **What will be rejected?**
   - Violates any of the 8 principles
   - Timeline references in documentation
   - No test paths for constraints
   - No evidence for rationale
   - No real-world validation
   - Overlaps with existing patterns
   - Adds bureaucracy without value

### High Bar for Additions

**IVD evolves slowly and deliberately:**
- Each addition must justify its existence
- Each addition must be production-validated
- Each addition must have comprehensive documentation
- Each addition must pass strict validation

**Why?** IVD is about durable understanding. Better to evolve slowly with confidence than quickly with chaos.

---

## Conclusion

**Intent-Verified Development** is the framework for the **AI Agents era**:

- **AI writes the intent** (not humans writing prose)
- **AI implements against the intent** (with constraints to verify)
- **AI catches its own hallucinations** (through executable tests)
- **Turns drop from many to one** (clarification at intent stage)

It acknowledges that in the AI Agents era, **the AI builds, writes, and verifies**. Traditional artifacts (PRDs, user stories, prompts) are prose the AI reads and guesses at. IVD provides structured intent the AI can write, verify, and self-correct against.

**The paradigm shift:** From "prompt the AI and hope" to "AI writes intent, implements, verifies."

---

## Further Reading

### IVD Documentation
- `README.md` - Quick start guide
- `cookbook.md` - Practical implementation guide
- `ivd_system_intent.yaml` - System intent (rules for extending IVD)
- `cheatsheet.md` - Quick reference
- `templates/intent_levels_guide.md` - When to use which intent level

---

**Version:** 2.4  
**Status:** Production Ready  
**Maintained by:** Leo Celis  
**Key Insight:** The AI writes the intent, implements against it (constraint-segmented for 3+ constraints), verifies—eliminating many-turns and hallucinations.
