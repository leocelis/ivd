# IVD Framework Decision Log

**Purpose:** Track every identified gap in the IVD framework, the analysis performed, and the decision (fix, defer, or reject). This captures both changes made *and* gaps deliberately left unfixed.  
**Format:** Architecture Decision Record (ADR) pattern — one entry per evaluated gap.  
**Canonical reference:** `ivd_system_intent.yaml` changelog captures *what* changed. This file captures *why* — including cases where the answer was "no change needed."

---

## FDR-001: Dynamic AI Agent Roles

**Date:** 2026-02-09  
**Status:** Fixed (Experimental)  
**Identified by:** Framework review  

**Gap:** IVD had no way to express that an AI agent should behave differently depending on context (e.g., "reviewer" vs. "implementer" mode in the same workflow).

**Analysis:** Roles are context-dependent behavioral modes, not identity. They affect how the agent interprets the same intent. Without capturing roles, intent artifacts couldn't fully specify expected agent behavior in multi-mode workflows.

**Decision:** Added `roles` as an **experimental** optional section. Experimental because production evidence is limited — the pattern is sound but hasn't been validated across 5+ implementations (the canonical threshold).

**Changes:** `ivd_system_intent.yaml`, `framework.md`, `templates/intent.yaml`, `mcp_server/tools/scaffold.py`.

---

## FDR-002: AI Authorship and Modification Authority

**Date:** 2026-02-09  
**Status:** Fixed (Experimental, scoped to module/workflow levels)  

**Gap:** IVD didn't capture whether an intent was written by a human or AI, or what authority an AI agent has to modify it autonomously.

**Analysis:** In multi-agent systems, knowing authorship origin and modification authority prevents unauthorized intent drift. However, applying this to every intent level (including task) adds overhead without value.

**Decision:** Added `authorship` as an **experimental** optional section, scoped to module and workflow levels only. Task-level intents are too ephemeral to benefit. Initially scaffolded at all levels — audit caught this as too aggressive, scoped it down.

**Changes:** `ivd_system_intent.yaml`, `framework.md`, `templates/intent.yaml`, `mcp_server/tools/scaffold.py` (scoped injection).

---

## FDR-003: Continuous Evaluation Loops

**Date:** 2026-02-09  
**Status:** Fixed (Experimental)  

**Gap:** IVD's Principle 4 (Continuous Verification) is binary (pass/fail). No mechanism for continuous quality improvement over time — "this workflow worked, but could it work *better*?"

**Analysis:** Self-evaluating workflows (e.g., precision tracking, A/B testing) need a structured place to define evaluation criteria, frequency, and improvement thresholds. This extends P4 from binary verification to continuous improvement.

**Decision:** Added `evaluation` as an **experimental** optional section. Natural extension of P4, but experimental because self-evaluating workflows are an advanced pattern not yet widely validated.

**Changes:** `ivd_system_intent.yaml`, `framework.md`, `templates/intent.yaml`.

---

## FDR-004: Capability Surface Propagation (Multi-Agent Routing)

**Date:** 2026-02-09  
**Status:** Fixed (Canonical)  

**Gap:** IVD had top-down intent propagation (coordinator → agents) via `coordinator-intent-propagation` recipe, but no bottom-up pattern. When a sub-agent's capabilities change, the coordinator's routing knowledge becomes stale. Additionally, LLM-based routing relied on prompt strings that were throwaway — not captured in intent.

**Analysis:** This is a real gap, not a feature request. Without bottom-up propagation, multi-agent systems silently degrade as sub-agents evolve. The `interface` section already captured API surfaces, but lacked a field for the natural-language routing descriptions that LLM coordinators actually use for dispatch decisions.

**Decision:** 
1. New recipe: `agent-capability-propagation.yaml` (bottom-up propagation pattern).
2. New sub-field: `interface.routing` (captures the descriptive string used for LLM routing).
3. Canonical status — the pattern is proven in production multi-agent systems.

**Changes:** `recipes/agent-capability-propagation.yaml` (new), `ivd_system_intent.yaml`, `framework.md`, `templates/intent.yaml`, `mcp_server/tools/scaffold.py`, `mcp_server/tools/validate.py`.

---

## FDR-005: Post-Implementation Verification Protocol

**Date:** 2026-02-09  
**Status:** Fixed (Canonical)  

**Gap:** Principle 4 said "verify" but didn't specify *how*. AI agents declared work "done" without structured verification against intent constraints. Agent instruction files (`.cursorrules`, `.clinerules`) were not recognized as IVD integration surfaces.

**Analysis:** "Verify your implementation" is aspirational without a protocol. The gap wasn't in the principle — it was in the absence of a concrete, step-by-step audit that agents could execute. Additionally, agent instruction files are where runtime enforcement actually lives, and IVD ignored them entirely.

**Decision:** 
1. New recipe: `agent-rules-ivd.yaml` defining a 4-step Post-Implementation Verification Protocol (re-read intent from disk, diff against constraints, check test paths, report PASS/FAIL/NEEDS_REVIEW).
2. Recognize agent instruction files as IVD integration surfaces.
3. `ivd_init` detects agent instruction files and suggests adding the IVD rules block.
4. Canonical status — this is Principle 4 made concrete.

**Changes:** `recipes/agent-rules-ivd.yaml` (new), `ivd_system_intent.yaml`, `framework.md`, `templates/intent.yaml`, `mcp_server/tools/validate.py`, `mcp_server/tools/scaffold.py`.

---

## FDR-006: Intent Stress Test (Pre-Implementation Completeness Check)

**Date:** 2026-02-09  
**Status:** Fixed (Canonical)  

**Gap:** Gaps in intent artifacts were only discovered during implementation — when they're expensive to fix. The P6 workflow went straight from "human reviews intent" to "AI implements." No step existed for the AI to adversarially probe the intent for completeness *before* writing code.

**Analysis:** Human review catches misalignment ("is this what I meant?") but not incompleteness ("what did we both miss?"). The AI sees implementation angles that the human doesn't — integration points, edge cases, data shape decisions. Catching these in intent is cheaper than catching them in code.

**Decision:** Added Step 4 to the P6 workflow: "AI stress-tests intent." Three challenge dimensions: constraint completeness, implementation anticipation, assumption challenge. This is Principle 2 (Understanding Must Be Executable) applied reflexively to the intent itself. Canonical status — it addresses a structural workflow gap, not an optional enhancement.

**Changes:** `ivd_system_intent.yaml`, `framework.md`, `README.md`, `templates/intent.yaml`, `recipes/agent-rules-ivd.yaml` (Rule 4), `mcp_server/tools/validate.py`.

---

## FDR-007: Self-Critique / "Challenge Your Assumptions" as Prompting Technique

**Date:** 2026-02-09  
**Status:** No change needed  

**Gap (proposed):** Should IVD prescribe how AI agents perform self-critique — specifically, per-constraint independent verification (separate LLM calls per constraint) rather than holistic review passes?

**Analysis:** Research was conducted across multiple sources:
- **Huang et al. (ICLR 2024, Google DeepMind):** "Large Language Models Cannot Self-Correct Reasoning Yet." Intrinsic self-correction (no external grounding) often degrades performance. The model second-guesses correct answers as often as incorrect ones.
- **2025 recursive self-evaluation study (GPT-4o-mini, Claude, Gemini):** Ungrounded self-critique produces "epistemic stasis" — 55% decline in information change across iterations. Models treat their own output as evidence.
- **Chain of Verification (Meta Research):** Decomposed, independent verification questions outperform holistic review. LLMs are more accurate verifying specific claims than using them in larger generations.
- **ART framework (ACL 2024):** Unconditional self-refinement worsens reasoning tasks. A verification gate (decide *whether* to refine) is required.
- **Multi-Agent Reflexion (2025):** Diverse reasoning perspectives + a judge model outperform single-agent self-reflection.

**The research identifies three properties for effective self-correction:**
1. **External grounding** (critique against a concrete artifact, not the model's own reasoning)
2. **Gating** (critique at a specific moment, conditionally — not always)
3. **Decomposition** (per-claim independent verification, not holistic sweeps)

**IVD already provides #1 and #2:**
- The intent artifact (YAML with constraints and test paths) is the external grounding.
- The stress test is gated at a specific workflow stage (after human review, before implementation).
- The verification protocol is gated post-implementation.

**#3 (decomposition) is an agent execution mechanic, not a framework concern.** The intent artifact already decomposes verification into individual constraints with individual test paths. The verification protocol already says "list each constraint and its status." Whether the agent uses separate LLM calls per constraint or processes them in a single pass is how the agent implements the protocol — analogous to IVD requiring test fields but not prescribing pytest vs. unittest.

**Decision:** No change to the framework. IVD already provides the structural solution (grounded, gated verification against a concrete artifact) that the research says works. Prescribing agent-level execution mechanics (separate LLM calls, prompt decomposition) would cross from framework into prompt engineering territory, which is not IVD's domain.

**Key insight for the record:** "Challenge your assumptions" as a generic prompt technique is weak (research confirms it often hurts). What IVD does is structurally different — it's *structured critique against a concrete artifact at a specific workflow stage*. Someone using IVD correctly is already past the problem that "challenge your assumptions" is trying to solve.

---

## FDR-008: Cognitive Architecture of LLMs as Theoretical Foundation for IVD

**Date:** 2026-02-09  
**Status:** Fixed (Canonical)  
**Identified by:** Framework review — observed that IVD explained WHAT to do but not the underlying cognitive mechanism of WHY it works at the LLM architecture level.

**Gap:** IVD's deepest "why" was: *"Prose fails silently. Executable understanding fails loudly."* True, but it explains what happens (constraints catch failures), not why — at the level of how LLMs actually process information. Without this, IVD reads like a methodology preference rather than something grounded in how models cognitively work.

**Research conducted:**
- **Huang et al. (ICLR 2024, Google DeepMind):** "Large Language Models Cannot Self-Correct Reasoning Yet." Intrinsic self-correction (no external grounding) degrades performance. The model cannot critique using the same weights that produced the answer.
- **9-LLM contextual/parametric study (2024):** Models allocate ~70% reliance on contextual knowledge (the prompt) and ~30% on parametric knowledge (training weights), regardless of context size. The model prefers what's in front of it.
- **Lost-in-the-middle (GPT-4, Claude 3, 2024):** Accuracy degrades for information positioned in the middle of long contexts. Effective context window can be 99% smaller than advertised. Information at the edges of a context receives significantly higher attention weights.
- **Proactive interference (2025):** Retrieval accuracy declines log-linearly as semantically similar information accumulates in context, independent of context window size.
- **Recursive self-evaluation (2025, GPT-4o-mini/Claude/Gemini):** Ungrounded self-critique produces "epistemic stasis" — 55% decline in information change across iterations. External grounding rebounds informational change 28% immediately when introduced.

**Analysis:** These findings provide the mechanistic explanation for IVD's core claims:
1. **Why prose fails:** Vague prose underloads the contextual channel (~70% slot), forcing the model to compensate with parametric gap-filling (training-data-averaged patterns). That gap-filling IS hallucination. Not "AI being wrong" — AI using the wrong knowledge system.
2. **Why structured intent works:** Explicit constraints with test paths have near-zero interpretive entropy. The contextual channel is saturated with specific, verifiable information. The parametric channel has nothing to fill.
3. **Why verification Protocol Step 1 ("re-read from disk") is cognitively necessary:** Lost-in-the-middle effect means information discussed early in a long session has degraded attention weight by implementation time. Re-reading repositions it at the top of the context stack where attention is highest.
4. **Why the stress test works:** The intent artifact is the external grounding that makes adversarial self-critique effective. Without the artifact, the model enters epistemic stasis. With it, the model compares against a concrete external reference — the pattern the research says works.

**Decision:** Incorporate as canonical framework foundation. Not a new principle — a theoretical explanation for existing principles. Applied at:
- `ivd_system_intent.yaml`: `cognitive_foundation` field under `principles` (canonical reference)
- `framework.md`: new section "Why This Works: The Cognitive Architecture of LLMs" under The Evolution

**Changes (wave 1):** `ivd_system_intent.yaml` (v2.0), `framework.md` (v2.0).

**Changes (wave 2 — prominence upgrade):** `purpose.md` (new "Two Knowledge Systems" section with table and mechanism), `README.md` (cognitive mechanism in "Why IVD?" section), `recipes/agent-rules-ivd.yaml` (Step 1 `why` updated with lost-in-the-middle rationale), `DECISIONS.md` (this entry updated).

---

## FDR-009: Empirical Refinement During Implementation

**Date:** 2026-02-09  
**Status:** Fixed (Canonical)  
**Identified by:** Framework review — observed that implementation frequently reveals assumptions in the intent that don't match reality (API formats, model accuracy, latency), with no protocol for updating the intent with empirical evidence.

**Gap:** IVD covered two scenarios well:
1. **Code drift** (P3 Bidirectional Sync): code changes, update intent — already handled.
2. **Anticipation** (P6 Intent Stress Test): probe for gaps before implementing — already handled.

But there was no protocol for the third scenario: **reality contradicts the intent's assumptions during implementation.** You wrote the intent from research, documentation, and domain knowledge. You stress-tested it. Then you started implementing and discovered that the API returns logits instead of probabilities, or the p95 latency is 500ms (not 200ms as documented), or the model accuracy is 72% on your actual data (not 85% from the paper). The intent is now wrong — not because of code drift, but because the assumptions that fed it were incomplete or inaccurate.

**Analysis:** This is a distinct failure mode from both code drift and pre-implementation anticipation:
- **Code drift:** Code changed → intent didn't. Direction: code → intent.
- **Stress test:** AI probes intent before implementing → catches reasoning gaps.
- **Empirical refinement:** Implementation reveals new knowledge about reality → intent needs updating. Direction: reality → intent.

Through the cognitive lens: the intent artifact is the contextual knowledge spine (~70% reliance). When it contains assumptions instead of empirical facts, the model fills gaps between those assumptions and observed behavior using parametric knowledge — the exact mechanism that causes hallucinations. Empirical refinement replaces assumptions with observed behavior, strengthening the contextual channel at the point where it was weakest.

**Decision:** Added as **canonical** extension under Principle 3 (Bidirectional Synchronization). The 5-step Empirical Refinement Protocol:
1. **STOP** — do not continue implementing against a stale assumption
2. **RECORD** — document what the intent assumed vs. what was observed
3. **UPDATE** — revise the intent artifact on disk (fix constraint, adjust threshold, add edge case)
4. **ENRICH** — pull more contextual knowledge (API docs, model cards, actual error responses)
5. **CONTINUE** — re-read the updated intent (Verification Protocol Step 1) and continue

If the discovery changes scope significantly, flag for human review before continuing.

**Changes:**
- `framework.md`: new section under Principle 3 "Empirical Refinement: When Implementation Reveals New Knowledge"
- `ivd_system_intent.yaml` (v2.1): `empirical_refinement` canonical extension under P3
- `recipes/agent-rules-ivd.yaml` (v1.2): Rule 5 "Empirical Refinement During Implementation" + common failure + P3 relationship
- `DECISIONS.md`: this entry (FDR-009)

**Relationship to other FDRs:**
- **FDR-006 (Intent Stress Test):** Stress test anticipates before implementation. Empirical refinement discovers during implementation. Together they close the loop.
- **FDR-008 (Cognitive Foundation):** Empirical refinement is grounded in the same cognitive mechanism — stale intent = stale contextual knowledge = parametric gap-filling.

---

## FDR-010: Interpretive Entropy Spectrum — Constraint Design for Non-Code Artifacts

**Date:** 2026-02-09  
**Status:** Fixed (Canonical)  
**Identified by:** Research review — empirical LLM studies on prompt specificity and constraint design revealed that IVD's constraint model was implicitly code-centric, treating all constraints as binary/near-zero-entropy. Creative, narrative, and documentary artifacts require a different approach.

**Gap:** IVD used "near-zero interpretive entropy" as the target for all constraints, with `p95 latency < 200ms` as the canonical example. This is correct for code. But the framework scope states "any AI-produced artifact" — and for creative writing, documentation, marketing copy, and book chapters, the constraint format `requirement: "metric >= threshold"` and `test: "path/to/test.py"` doesn't apply. The gap: no guidance for writing constraints when the artifact is inherently qualitative.

**Evidence base:**
- **CMU 2025** ("What Prompts Don't Say"): Underspecified prompts are 2x as likely to regress; models infer unspecified requirements correctly only 41.1% of the time; the remaining 59% fill from parametric averaged patterns. Fragility persists even with explicit specification when requirements conflict.
- **CS4 2024** (measuring LLM creativity through constraint specificity): Increasing prompt specificity via constraint count measurably reduces LLM reliance on training data patterns. More constraints = less parametric averaging.
- **DETAIL 2024**: Increased prompt specificity improves accuracy, especially for procedural/structured tasks. The specificity–performance relationship is real and measurable.

**Analysis:** Constraints exist on a spectrum of interpretive entropy — how much interpretation space remains between the constraint statement and its verification. Three tiers:
1. **Near-zero**: Binary, measurable, testable. `precision >= 0.85, test: tests/test_precision.py`. Model cannot guess.
2. **Low-qualitative**: Qualitative but decomposed into measurable proxies. `tone: melancholic — no resolution in final paragraph`. Human-review checklist as test. Acceptable for creative artifacts.
3. **High-entropy**: Pure prose. `"write well"`, `"be creative"`. Triggers parametric averaging. **Rejected by IVD.**

For creative artifacts, "write well" must be decomposed: `1,200–1,400 words` + `three scenes, different rooms, no flashbacks` + `first person, present tense` + `melancholic tone: no resolution, no crying` = six low-qualitative or near-zero constraints. The CS4 benchmark demonstrated this decomposition reduces parametric reliance.

**Decision:** Added as **canonical** extension to Principle 2 (Understanding Must Be Executable). The entropy spectrum is now a documented concept in `framework.md` (Principle 2 section), `ivd_system_intent.yaml` (constraint_quality block), `templates/intent.yaml` (constraint comment block), and `recipes/agent-rules-ivd.yaml` (Rule 6). All three tiers are defined with examples; high-entropy constraints are explicitly rejected.

**Changes:**
- `framework.md`: New subsection "Constraint Quality: The Interpretive Entropy Spectrum" under Principle 2
- `ivd_system_intent.yaml` (v2.2): `constraint_quality.entropy_spectrum` block under P2; v2.2 changelog
- `templates/intent.yaml`: Updated constraints block comment with entropy classification and position-bias guidance
- `recipes/agent-rules-ivd.yaml` (v1.3): IVD Rule 6 (constraint quality); updated changelog

**Relationship to other FDRs:**
- **FDR-007 (Self-Critique):** Both address what happens when the contextual channel is underspecified for the task type. FDR-010 addresses it at the constraint-design level.
- **FDR-008 (Cognitive Foundation):** High-entropy constraints trigger parametric gap-filling — same mechanism. FDR-010 operationalizes FDR-008 for constraint writing.

---

## FDR-011: Constraint Satisfiability — Multi-Constraint Failure Mode

**Date:** 2026-02-09  
**Status:** Fixed (Canonical)  
**Identified by:** Research review — UltraBench 2025 and CMU 2025 identified that LLMs fail at simultaneous multi-constraint satisfaction even when each constraint is individually satisfiable at high accuracy.

**Gap:** IVD treated the `constraints` list as a set of independent items, each with its own test. No concept of constraint interaction, conflict, or satisfiability existed. The stress test (Principle 6, Step 4) had three probes — none checked whether the constraint set as a whole could be satisfied simultaneously.

**Evidence base:**
- **UltraBench 2025**: Models exceed 70% accuracy on individual constraints but fail when satisfying all constraints simultaneously. **Position bias** is systematic: constraints listed earlier in the prompt are silently violated when later constraints conflict with them. Structural constraints are harder to satisfy than content-based ones.
- **CMU 2025** ("What Prompts Don't Say"): Conflicting constraints produce 20%+ accuracy drops even when all constraints are individually explicit and well-formed. Standard prompt optimizers provide limited benefit against this failure mode.
- **Multi-dimensional constraint framework 2025** (arXiv): Average accuracy drops from 77.67% at difficulty Level I to 32.96% at Level IV as constraint complexity increases. This is not a model capability issue — it's a constraint interaction issue.

**Analysis:** Three distinct problems:
1. **Conflict**: Two constraints that cannot both be satisfied (e.g., "500 words" + "six detailed sections"). Detectable at intent stage.
2. **Position bias**: Models weight later-listed constraints more heavily. Critical constraints listed first get silently violated when conflicts arise with later constraints.
3. **Complexity cascade**: Each additional constraint reduces the probability of simultaneous full satisfaction. At 5+ constraints, failure is likely without explicit priority ordering.

**Decision:** Added as **canonical** extension to Principle 2 and Principle 6 (stress test). Changes:
- Fourth stress test probe: "Do any two constraints conflict? Can all be satisfied simultaneously? Are critical constraints listed last to counter position bias?"
- `constraint_satisfiability` block added to `templates/intent.yaml` (optional, recommended at 3+ constraints)
- Framework documentation with position-aware constraint ordering guidance
- IVD Rule 4 updated with Probe 4 in `recipes/agent-rules-ivd.yaml`

**Practical rule:** Most critical constraints go **last** in the constraint list. If tone fidelity matters most, declare it last. This is counterintuitive but research-backed.

**Changes:**
- `framework.md`: Constraint satisfiability subsection under Principle 2; Probe 4 added to stress test (Step 4)
- `ivd_system_intent.yaml` (v2.2): `constraint_quality.satisfiability` block; P6 stress test dimensions extended
- `templates/intent.yaml`: `constraint_satisfiability` block (optional, with research citation)
- `recipes/agent-rules-ivd.yaml` (v1.3): Rule 4 Probe 4 with research grounding; Rule 6 SATISFIABILITY CHECK

**Relationship to other FDRs:**
- **FDR-006 (Intent Stress Test):** Probe 4 is a direct extension of the stress test framework. Same mechanism, new dimension.
- **FDR-010 (Entropy Spectrum):** Constraint satisfiability compounds with entropy — high-entropy constraints are harder to check for satisfiability conflicts because their verification is qualitative. Design both together.

---

## FDR-012: Creative Homogenization as a Named Failure Mode

**Date:** 2026-02-09  
**Status:** Fixed (Canonical)  
**Identified by:** Research review — "We're Different, We're the Same" (arXiv 2501.19361, 2025) provided direct empirical evidence of cross-model creative homogenization as a distinct failure mode from hallucination.

**Gap:** IVD's cognitive foundation section named exactly one failure mode of parametric gap-filling: **hallucination** (factually wrong output). For code, this is the primary failure mode. But for creative, narrative, and documentary artifacts, there is a second, equally important failure mode: **homogenization** — output that is not factually wrong but statistically averaged, indistinguishable from other LLM outputs on the same prompt. IVD had no name, definition, or mitigation guidance for this.

**Evidence base:**
- **"We're Different, We're the Same" (arXiv 2501.19361, January 2025)**: Evaluates creative outputs from multiple LLMs using standardized creativity tests. Finding: LLM responses are significantly more similar to each other than human responses are to each other, *even after controlling for response structure and other key variables*. This holds across models from different organizations — shared training data distributions are the likely cause.
- **Homogenization effects on human ideation (2024)**: Users employing LLMs as creative assistants produce more homogeneous outputs than control groups. ChatGPT users generated "less semantically distinct ideas." InstructGPT feedback caused "statistically significant reduction in diversity" between different authors' work.
- **CreativityPrism benchmark (2025)**: Strong performance on one creativity dimension (quality) does not generalize to others (novelty, diversity). Current evaluation metrics often measure quality but miss homogenization.
- **CMU 2025**: Hallucination occurred in 30% of model outputs overall in underspecified contexts, approaching 40% in some models — but the more insidious failure for creative artifacts is homogenized output that passes quality checks but lacks distinctiveness.

**Analysis:** Homogenization and hallucination share the same root cause — parametric gap-filling — but they manifest differently and require different mitigations:

| | Hallucination | Homogenization |
|---|---|---|
| **Output is** | Factually wrong | Factually acceptable but averaged |
| **Primary artifact** | Code, factual content | Creative writing, narrative, marketing |
| **Detection** | Test fails | Human review ("this sounds like every LLM") |
| **Mitigation** | Structured constraints + tests | Distinctiveness constraints + style reference |

IVD's contextual channel mechanism addresses hallucination: saturate the channel with specific constraints, leave nothing for parametric fill. Homogenization requires an additional step: explicitly constrain *distinctiveness* — what makes this output NOT the parametric average. Prohibitions are often more effective than requirements: "no inspirational ending," "no summary paragraph," "no em-dash overuse," "not in the voice of a Harvard Business Review article."

**Decision:** Added as **canonical** named failure mode alongside hallucination. Homogenization is now documented in:
- `framework.md`: Cognitive foundation section — both failure modes named with definitions
- `ivd_system_intent.yaml` (v2.2): `constraint_quality.homogenization_prevention` block
- `recipes/agent-rules-ivd.yaml` (v1.3): Rule 6 HOMOGENIZATION CHECK

**Practical rule for intents:** For any creative or narrative artifact, add at minimum:
1. Voice/tone constraint (decomposed into measurable proxies — see FDR-010)
2. Structure constraint
3. Distinctiveness note: what makes this output NOT the parametric average (reference material, prohibitions, explicit style target)

**Relationship to other FDRs:**
- **FDR-008 (Cognitive Foundation):** Homogenization is the creative-artifact expression of the same parametric gap-filling mechanism. FDR-012 extends FDR-008's vocabulary.
- **FDR-010 (Entropy Spectrum):** High-entropy constraints produce homogenized output. FDR-012 explains *why* high-entropy is dangerous — it's not just imprecision, it's convergence to the statistical mean.

---

## FDR-013: Contextual Knowledge Source Hierarchy and 2-Attempt Enrichment Trigger

**Date:** 2026-02-09  
**Status:** Fixed (Canonical)  
**Identified by:** Production observation — when code doesn't work, searching GitHub for the error immediately surfaces the fix, replacing 5–10 correction turns. The ENRICH step in the Empirical Refinement Protocol existed but had no source ranking and no trigger heuristic — agents iterated indefinitely using parametric variations.

**Gap:** The ENRICH step (Empirical Refinement Protocol, step 4) listed generic examples: "API documentation, model cards, actual error responses, performance benchmarks." Two problems:

1. **No source hierarchy.** Not all contextual knowledge is equal. A GitHub issue with a maintainer-confirmed fix is higher signal than official documentation (which may lag implementation), which is higher signal than the model's parametric knowledge (which already proved insufficient — that's why ENRICH was triggered). Without a ranked hierarchy, agents default to the lowest-effort source — their own parametric knowledge — which is the exact source that already failed.

2. **No trigger heuristic.** The protocol said ENRICH "if the discovery reveals a knowledge gap" but provided no concrete signal for when an agent should recognize it's stuck. In practice, agents iterate 3, 5, 10 times — producing variations of the same wrong answer, each time making cosmetic changes — because they have no rule that says "stop, this isn't working, go external." This is the most expensive failure mode in AI-assisted development: wasted turns drawing from the same parametric well.

**Analysis through the cognitive lens:**

When code fails and the agent retries without new external data, each attempt draws from the same parametric knowledge that produced the original failure. The parametric channel is frozen and averaged — it contains the popular usage of a library, not the edge case, not the breaking change in v3.2.1, not the workaround from the GitHub issue where the maintainer explains the real behavior.

GitHub issues are the optimal enrichment source for code failures because they contain:
- The actual error message (exact match for context injection)
- The confirmed workaround (empirically validated, not parametrically averaged)
- Version-specific context (what changed and when)
- Maintainer commentary (authoritative, specific)

One GitHub issue thread injects confirmed empirical knowledge into the contextual channel where the model previously had only parametric approximation. This is IVD's core mechanism at the debugging level: the problem is never the model; the problem is what's in the context.

**Decision:** Expanded the ENRICH step with two canonical additions:

**1. Source hierarchy for code failures (ranked by signal):**
1. Actual error message/stack trace — empirical, specific, current
2. GitHub issues and PRs matching the error — maintainer-confirmed, version-specific
3. Library changelogs/release notes — what changed between versions
4. Official documentation — authoritative but may lag implementation
5. Model's parametric knowledge — lowest signal; already proven insufficient

**2. The 2-attempt trigger rule:** If the same error or failure pattern persists after two implementation attempts without new external data, the agent MUST stop and ENRICH before attempting again. Two attempts establish that the parametric channel doesn't have the answer. Further attempts without new contextual knowledge are wasted turns.

**Changes:**
- `framework.md`: ENRICH step expanded with source hierarchy, GitHub as named channel, 2-attempt trigger rule, cognitive rationale for why source ranking matters
- `ivd_system_intent.yaml` (v2.3): ENRICH step updated with source hierarchy (a–e), 2-attempt trigger, cognitive rationale extended
- `recipes/agent-rules-ivd.yaml` (v1.4): Rule 5 ENRICH expanded with source hierarchy + 2-attempt trigger. New `common_failures` entry: "Repeated Iteration Without Enrichment"
- `mcp_server/tools/context.py`: P3 description in `ivd_get_context` now surfaces empirical refinement and 2-attempt rule
- Book Ch3 intent: §3.3 Principle 3 extended with GitHub search as concrete ENRICH example and 2-attempt heuristic

**Relationship to other FDRs:**
- **FDR-009 (Empirical Refinement):** FDR-013 extends step 4 of FDR-009's protocol. The 5-step structure is unchanged; the ENRICH step is now more actionable.
- **FDR-008 (Cognitive Foundation):** Validates the core claim empirically — the problem is what's in the context. GitHub search works because it changes the contextual channel, not the instruction.

---

## FDR-014: Constraint-Segmented Implementation — Mitigating Compliance Degradation During Generation

**Date:** 2026-02-09
**Status:** Accepted — Canonical Extension

**Gap identified:**
Post-implementation audits against intent artifacts consistently surface missed requirements, even when the AI agent explicitly read and acknowledged all constraints before starting. The user-reported pattern: "when you ask to compare [output] with the intent and find gaps, always something comes up." The problem persists across model generations and enforcement hook counts (documented in production in anthropics/claude-code GitHub).

**Evidence base:**

1. **Read-acknowledge-violate pattern** (GitHub anthropics/claude-code issues #26848, #6120, #32290, #742 — 2025): Users across model tiers document the same pattern — AI reads an instruction file, recites constraints when asked, confirms it will follow them, then violates them during generation. Reported with 24+ enforcement hooks and 400-line instruction files. The issue is systematic, not user error.

2. **Lost-in-the-middle effect** (Liu et al. 2023, Stanford NLP Group): Transformer attention is highest at the beginning and end of context. Information in middle positions degrades by >30%. An intent artifact injected at the top of the context becomes a middle-position document by the time 80+ lines of implementation are generated. Constraints listed in the middle of the artifact are the most vulnerable.

3. **Constraint compliance is orthogonal to task completion** (MOSAIC 2025): Producing correct, working code and following all stated constraints are separately measured capabilities. A model can achieve high task completion scores while missing 2–3 constraints without tension — the model defaults to "produce correct code" and deprioritizes constraint adherence under attention pressure. These are distinct capabilities, not aspects of the same one.

4. **Constraint density degradation** (IFScale 2025): Frontier models achieve ~68% accuracy at high instruction density, with nonlinear degradation — threshold effects appear at medium constraint density. Each additional constraint reduces the probability of full compliance, not proportionally but with cascading effects.

5. **Additional evidence** (CodeIF 2025): Confirms the orthogonality of task-level quality and instruction-following quality as separately evaluable metrics.

**Analysis:**

The failure mode is structural, not model-quality-related. Three architectural factors combine in single-pass implementation:

- **Attention gradient:** Early constraints shift to middle positions during long generation spans; they receive less attention than constraints near the prompt boundary.
- **Capability gap:** Task completion (produce working code) and constraint compliance (follow all stated rules) are orthogonal. Optimizing for one does not guarantee the other.
- **Density cascading:** Adding more constraints to the intent doesn't linearly reduce each constraint's compliance probability — it creates threshold effects where overall compliance drops nonlinearly.

These factors make single-pass implementation of a complex intent architecturally likely to miss constraints, regardless of how thoroughly the AI reviewed the intent before starting.

**Decision: Canonical extension to P4 and P6**

Introduce **Constraint-Segmented Implementation** as a canonical protocol:

- **Trigger:** 3+ constraints in the intent (based on IFScale degradation curve — threshold effects appear at medium density; below 3, single-pass is acceptable)
- **Protocol:** GROUP constraints by functional area → IMPLEMENT one segment → RE-READ constraints for that segment from disk → VERIFY segment → repeat → CROSS-CUT sweep
- **Mechanism:** Each re-read repositions constraint text at the top of the context stack where transformer attention weights it highest. This converts one long attention span into multiple short ones, each starting with fresh constraint attention. The same cognitive mechanism as the Post-Implementation Verification Protocol (re-read from disk), applied during generation.
- **Post-implementation verification role:** When segmented implementation was used, Rule 2 (Post-Implementation Verification Protocol) functions as a cross-cutting final sweep — catching inter-constraint gaps — rather than as the primary per-constraint compliance check.

**What this is NOT:** A workaround for a model deficiency. The lost-in-the-middle effect and constraint compliance orthogonality are inherent to current transformer architectures. Segmented implementation is a protocol that works with the architecture rather than against it.

**Files changed:**
- `framework.md`: Step 5: Constraint-Segmented Implementation added to P6 section; Post-Implementation Verification Protocol updated to note its role when segmented implementation was used
- `ivd_system_intent.yaml` (v2.4): P6 single-agent and multi-agent workflows updated; P4 canonical extension "Constraint-segmented implementation" added with full research citations
- `recipes/agent-rules-ivd.yaml` (v1.5): Rule 1 IMPLEMENT step expanded with full segmented protocol; new `common_failures` entry "Single-Pass Implementation Against Complex Intent"
- `mcp_server/tools/context.py`: P6 description in `ivd_get_context` updated with segmented protocol summary
- Book Ch3 intent: §3.4 and §3.6 updated
- Book Ch1 intent: §1.3 updated with constraint compliance gap

**Relationship to other FDRs:**
- **FDR-011 (Constraint Satisfiability):** FDR-011 addresses conflict detection and priority ordering at intent design time. FDR-014 addresses the implementation phase — how constraints are attended to during code generation. Both target constraint compliance failure but at different stages of the IVD workflow.
- **FDR-009 (Empirical Refinement):** FDR-014 is a sister protocol — both extend P4 and P6 with prescriptive steps that address structural LLM limitations (FDR-009: what to do when the implementation reveals wrong assumptions; FDR-014: how to implement without missing constraints).
- **FDR-008 (Cognitive Foundation):** The mechanism of constraint-segmented implementation (re-reading from disk = fresh contextual injection) is a direct application of the contextual knowledge principle — high-signal context injected at the right moment overrides parametric defaults.

---

## FDR-015: Bundling the Judgment Layer into IVD (rather than a separate plugin/MCP)

**Date:** 2026-03-21  
**Status:** Fixed (Canonical, IVD v3.0)  
**Identified by:** Leo Celis (architectural pivot during JFL design)  

**Gap:** The Judgment Feedback Loop (JFL) — the structured way to capture, codify, cluster, and inject corrections back into agent context — was originally drafted as a standalone framework essay. The deployment question (standalone CLI? Cursor-only rule? separate `@leocelis/judgment-mcp` package? plugin?) had no good answer because JFL only matters once a project already has structured intent — i.e., once IVD is in use. Splitting it from IVD forced users to learn two systems, install two MCPs, and reason about two vocabularies for the same workflow.

**Analysis:**
- **Cognitive cost:** A separate MCP doubles the install surface (two `mcp.json` entries, two version trains, two doc sets) for the same audience.
- **Vocabulary fit:** Judgment-phase concepts (ledger entry, pattern, recommendation) are direct extensions of IVD's existing vocabulary (intent, constraint, recipe). Splitting them creates artificial seams.
- **Industry pattern:** Mature open-source frameworks consistently bundle workflow phases inside the core (Django apps, Rails plugins, Kubernetes controllers) rather than shipping each phase as a separate package the user must wire together.
- **Auto-pickup:** The user's hard requirement was *"agents should pick this up automatically once it exists."* That requires the tools to live in the same MCP the agent is already using.
- **Opt-in:** The phase is genuinely opt-in (most projects don't need it on day one) — but opt-in via a `.judgment/` folder gate inside the existing MCP, not via a separate package.

**Decision:** The Judgment phase ships *inside* the `user-ivd` MCP, as IVD's 4th phase, governed by Principle 9 (Judgment Compounds), behind a `.judgment/`-folder activation gate. Tools are dormant unless the gate is present.

**Why not a plugin architecture:** A plugin layer would itself need a contract, a discovery mechanism, a versioning scheme — all of which already exist inside the IVD canon. Judgment is *not* an optional plugin from IVD's perspective; it's a phase. Phases belong in the framework, not in plugin land.

**Changes:**
- `ivd_system_intent.yaml` (v3.0): Principle 9 added; Validation Level 5 added; canonization process step 4.5 added; new `artifact_types` (ledger_entry, comparison_pair, pattern, baseline)
- `framework.md`: New "Judgment Phase" section; Principle 9 added; ToC bumped
- `judgment_layer.md`: New canonical doc — IVD-native rewrite of the JFL framework
- `templates/`: 4 new templates (`baseline.yaml`, `ledger-entry.yaml`, `comparison-pair.yaml`, `pattern.yaml`)
- `recipes/`: 3 new recipes (`capture-correction.yaml`, `comparison-pair.yaml`, `distill-pattern.yaml`)
- `mcp_server/tools/judgment.py`: 8 new tool handlers (all gated on `.judgment/`)
- `mcp_server/registry.py`: 8 new tool registrations (total tools: 15 → 23 in v3.0; v3.1 added the 9th judgment tool `ivd_judgment_check_installed` and the 4 Canon tools, bringing the total to 28)
- `mcp_server/tools/validate.py`: 4 new artifact validators
- `mcp_server/tools/context.py`: Knowledge surface includes judgment doc

**Relationship to other FDRs:**
- **FDR-008 (Cognitive Foundation):** Judgment phase extends the contextual-knowledge thesis — corrections are the highest-quality contextual signal a system can accumulate, because they came from real-world failure of the model's parametric defaults.
- **FDR-009 (Empirical Refinement):** FDR-009 added "what to do when implementation reveals wrong assumptions during a single project lifecycle." FDR-015 generalizes that loop across projects, audiences, and time, with structured persistence.

---

## FDR-016: Version bump to IVD v3.0 (rather than v2.5)

**Date:** 2026-03-21  
**Status:** Fixed (Canonical)  
**Identified by:** Spec review (FDR-015 follow-up)  

**Gap:** The Judgment phase introduces a new immutable principle (Principle 9), a 4th phase in the IVD lifecycle, a 5th validation level, 4 new artifact types, and 8 new tools. Initially considered as v2.5 (a feature release).

**Analysis:**
- **Immutability is the bright line.** IVD's `principle_immutability` constraint states that the core principle set cannot be silently amended. Adding Principle 9 changes the "immutable-N" set from 8 to 9. That is, by definition, a major version event.
- **Phase change is structural.** Adding a phase changes the IVD lifecycle from a 3-phase loop (Intent / Implementation / Verification) to a 4-phase loop (… + Judgment). Existing intents still work — but downstream tooling that reasoned about the phase set must be aware of the change. Semantic versioning calls for a major bump when the contract changes shape.
- **Opt-in does not change the version semantics.** Even though the Judgment phase is opt-in via `.judgment/`, the *framework* itself ships the new principle, the new validation level, and the new artifact types in its canonical state. Users have to upgrade their understanding of IVD even if they don't activate the phase.
- **No backward-incompatible breakage.** Existing v2.x intents validate cleanly under v3.0. The version bump is structural/communicative, not a forced migration.

**Decision:** IVD bumps from v2.4 → **v3.0** when the Judgment layer ships.

**Changes:**
- `ivd_system_intent.yaml`: `version: "3.0"`, new changelog entry
- `framework.md`, `cookbook.md`, `cheatsheet.md`, `README.md`, `purpose.md`: version refs updated
- `judgment_layer.md`: stamped `IVD v3.0`
- All v3.0 surfaces document Principle 9 explicitly so users understand the immutability shift

**Relationship to other FDRs:**
- **FDR-015:** This is the version-policy companion to FDR-015 (the architectural decision). FDR-015 = *what* changes; FDR-016 = *how loud* the version says it.

---

## FDR-017: ivd_list_features Returns Duplicate Artifacts

**Date:** 2026-05-10
**Status:** Fixed (Canonical)
**Identified by:** MCP tools health audit

**Gap:** `ivd_list_features` iterated two glob patterns (`**/*_intent.yaml` and `**/*_system_intent.yaml`). Since `*_intent.yaml` already matches `*_system_intent.yaml`, every system intent file appeared twice in the result.

**Analysis:** The second glob was added defensively to ensure system intents were always captured. This was unnecessary — the first pattern already covers them. No deduplication logic was present, so callers received duplicate entries and inflated `count`.

**Decision:** Remove the second glob pattern entirely. Add a `seen_paths` set to guard against any future accidental re-traversal. Single glob: `**/*_intent.yaml`.

**Changes:** `mcp_server/tools/discover.py` (`list_features_tool`)

---

## FDR-018: ivd_validate Rejects Valid Recipe Artifacts

**Date:** 2026-05-10
**Status:** Fixed (Canonical)
**Identified by:** MCP tools health audit

**Gap:** `ivd_validate` checked for top-level keys `["recipe", "description", "pattern", "use_cases", "example"]` when `artifact_type="recipe"`. Actual recipe YAML files (including all 17 canonical recipes in `/recipes/`) have only `recipe:` as a top-level block, with `description`, `name`, `version` nested inside it. Running `ivd_validate` on any real recipe reported 4 spurious errors and declared the artifact invalid.

**Analysis:** The validator schema was authored for a hypothetical recipe format that never matched the actual recipe file structure. The canonical format was defined in `ivd_load_recipe` and the recipe files themselves, not in the validator. This is a specification drift bug.

**Decision:** Fix the recipe schema to match the actual format: require only `recipe:` at the top level, and validate `name`, `version`, `description` as nested fields inside the `recipe:` block (same pattern as `intent.summary/goal/success_metric`). This is Canonical because the recipe format is already stable.

**Changes:** `mcp_server/tools/validate.py` (`validate_artifact_tool`)

---

## FDR-019: ivd_init Guard Does Not Detect Existing Named System Intents

**Date:** 2026-05-10
**Status:** Fixed (Canonical)
**Identified by:** MCP tools health audit (test call on /workspace created spurious system_intent.yaml)

**Gap:** `ivd_init` guarded against re-initialization by checking if `system_intent.yaml` (exact name) already exists. It did not check for `*_system_intent.yaml` patterns (e.g., `ivd_system_intent.yaml`, `book_system_intent.yaml`). A repo that already had a named system intent could receive a second, conflicting one.

**Analysis:** The naming convention documented in `framework.md` explicitly supports both `system_intent.yaml` and `{project}_system_intent.yaml`. The guard only protected the bare form. This was a gap in defensive programming — the IVD framework's own repo demonstrated the failure when `ivd_init` wrote a new `system_intent.yaml` alongside the existing `ivd_system_intent.yaml`.

**Decision:** Expand the guard to check both `system_intent.yaml` and any `*_system_intent.yaml` glob match. Return an informative error including the path of the existing artifact.

**Changes:** `mcp_server/tools/scaffold.py` (`init_project_tool`)

---

## FDR-020: ivd_list_recipes Returns Opaque Metadata for 8 of 17 Recipes

**Date:** 2026-05-10
**Status:** Fixed (Canonical)
**Identified by:** MCP tools health audit

**Gap:** `list_recipes_tool` populated metadata from a hardcoded `RECIPE_INFO` dict. Eight recipes had no entry in that dict and fell through to `"description": "Recipe available", "use_cases": [], "complexity": "unknown"`. This made those recipes invisible to `ivd_discover_goal` filtering and unhelpful to callers doing tool selection. The hardcoded table also required manual maintenance on every recipe addition.

**Analysis:** All recipe YAML files already contain `recipe.description`, `recipe.use_cases` (in some), and `recipe.complexity` (in some) as part of their canonical structure. Reading this directly from the file eliminates the maintenance burden and self-documents.

**Decision:** Add `_read_recipe_metadata()` helper that reads `recipe.description/use_cases/complexity` from the YAML file. `RECIPE_INFO` is kept as a fallback for recipes that predate structured metadata (backward compat). Priority: file > hardcoded table > default. This is Canonical.

**Changes:** `mcp_server/tools/recipes.py` (`list_recipes_tool`, new `_read_recipe_metadata`)

---

## FDR-021: ivd_discover_goal Ignores user_hint Parameter

**Date:** 2026-05-10
**Status:** Fixed (Canonical)
**Identified by:** MCP tools health audit

**Gap:** `ivd_discover_goal` accepted a `user_hint` parameter but never used it to filter or rank candidates. The tool always returned the first 4 recipes in filesystem order. A caller providing `"I want to track errors in my Python app"` received the same 4 recipes as a caller providing `"I want to classify leads"`.

**Analysis:** The `user_hint` was stored in `context_used` for transparency but served no functional purpose. Agents and users calling the tool with a hint reasonably expected hint-based relevance. Even simple keyword overlap scoring is substantially better than unordered filesystem traversal.

**Decision:** Add keyword-overlap ranking: tokenize `user_hint` on whitespace, score each recipe by how many tokens appear in `name + description + use_cases`, sort descending, take top 4. This is a deliberate choice against embedding-based semantic ranking — the tool must stay lightweight and work without external API calls. Simple keyword overlap handles the common cases (e.g., "error" → `infra-structured-logging`, "workflow" → `workflow-orchestration`). Canonical.

**Changes:** `mcp_server/tools/learning.py` (`discover_goal_tool`)

---

## FDR-022: ivd_propose_inversions Returns Silent Empty Scaffold

**Date:** 2026-05-10
**Status:** Fixed (Canonical)
**Identified by:** MCP tools health audit

**Gap:** `ivd_propose_inversions` returned an empty `proposed_inversions: []` scaffold with no signal to the calling agent that it was expected to populate it. Agents that parsed the response and saw the empty list could pass it upstream as-is, silently omitting the inversion content that Principle 8 requires.

**Analysis:** The tool is intentionally a scaffold generator, not an AI-generative tool — the calling agent knows the domain and should produce the content. The problem was that this contract was implicit: only the tool description stated it, not the response payload. Agents working from the response alone had no in-band instruction.

**Decision:** Add an `agent_instructions` field directly in the response payload, making the contract explicit and in-band. This follows the same pattern as `ivd_codify`'s `codify_prompt` field: the tool tells the agent exactly what to do next in the response body, not just in documentation. Canonical.

**Changes:** `mcp_server/tools/inversions.py` (`propose_inversions_tool`)

---

## FDR-023: IVD Rules Block in .cursorrules Missing Detection Fence Markers

**Date:** 2026-05-10
**Status:** Fixed (Canonical)
**Identified by:** MCP tools health audit (`ivd_init` scan reported `ivd: false` for .cursorrules)

**Gap:** The IVD framework's own `.cursorrules` contained the IVD verification rules (R1–R6) as raw markdown, without the `<BEGIN-IVD v1.5>` / `<END-IVD v1.5>` fence markers that `canon_check_rules_installed` and `ivd_init` use for detection. The Canon block had correct fences; the IVD block did not. Result: the framework's own repo reported `ivd: false` when its own detection tool ran on it.

**Analysis:** The fence convention was added to the Canon block after the IVD rules block was written. The IVD rules were never retrofitted with fences when the convention was established. The detection regex `<BEGIN-IVD v[\d.]+>` was correct; the file content was not.

**Decision:** Wrap the existing IVD rules section with `<BEGIN-IVD v1.5>` / `<END-IVD v1.5>` fences and add the `Source:` header comment (matching the Canon block's format). Content unchanged — no rules added or removed. Canonical.

**Changes:** `.cursorrules`

---

## FDR-024: No Public Legal Disclaimer Covering AI Limitations, Data Transmission, and Deployer Obligations

**Date:** 2026-05-10
**Status:** Fixed (Canonical)
**Identified by:** Full risk registry and legal risk mapping review (cross-check pass)

**Gap:** IVD had no public document disclosing: (1) inherent LLM behavioral limitations that IVD
mitigates but cannot eliminate; (2) that hosted server tool calls transmit content to US-based
infrastructure (DigitalOcean + OpenAI); (3) scope and conditions of marketing claims;
(4) deployer responsibilities under EU AI Act, GDPR, CCPA/CPRA, and Colorado SB 24-205;
(5) the architectural limitation that the hosted server cannot access local filesystems;
(6) Judgment phase data handling risks (PII, retention, profiling). Gaps 1–6 in
`_private/research/legal_risk_mapping.md` all required a public-facing disclosure.

**Analysis:** The absence of any legal notice constitutes a potential unfair practice under
FTC Act § 5 (15 U.S.C. § 45) for the failure to disclose material facts about the hosted
service. It also creates a GDPR Article 13 gap for EU users (no transparency notice at
point of data collection). The FTC's Operation AI Comply (Sept 2024) and "Keep Your AI
Claims in Check" (Feb 2023) guidance both identify non-disclosure and unsubstantiated
efficacy claims as enforcement priorities. The risk of "intent theater" (R-005) additionally
requires that marketing claims be explicitly scoped to tested conditions.

**Decision:** Create `LEGAL.md` as a public, first-class document in the repo root. It covers
all six compliance gaps identified in the legal risk mapping, with every claim backed by an
official source URL verified on 2026-05-10. Linked from README.md's License section.

**Changes:** `LEGAL.md` (created), `README.md` (Legal section added before License)

---

## Template for New Entries

```markdown
## FDR-NNN: [Gap Title]

**Date:** YYYY-MM-DD  
**Status:** Fixed (Canonical|Experimental) | Deferred to vN.N | No change needed  
**Identified by:** [Who/what surfaced the gap]  

**Gap:** [What's missing or broken]

**Analysis:** [Research, evidence, reasoning]

**Decision:** [What was decided and why]

**Changes:** [Files modified, or "None" if no change needed]
```
