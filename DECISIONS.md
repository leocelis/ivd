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

**Changes:** `recipes/agent-capability-propagation.yaml` (new), `ivd_system_intent.yaml`, `framework.md`, `templates/intent.yaml`, `mcp_server/tools/scaffold.py`, `mcp_server/tools/validate.py`, book intents (Ch3, Ch9, Ch19).

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

**Changes:** `recipes/agent-rules-ivd.yaml` (new), `ivd_system_intent.yaml`, `framework.md`, `templates/intent.yaml`, `mcp_server/tools/validate.py`, `mcp_server/tools/scaffold.py`, book intents (Ch3, Ch4, Ch17), `book_system_intent.yaml`.

---

## FDR-006: Intent Stress Test (Pre-Implementation Completeness Check)

**Date:** 2026-02-09  
**Status:** Fixed (Canonical)  

**Gap:** Gaps in intent artifacts were only discovered during implementation — when they're expensive to fix. The P6 workflow went straight from "human reviews intent" to "AI implements." No step existed for the AI to adversarially probe the intent for completeness *before* writing code.

**Analysis:** Human review catches misalignment ("is this what I meant?") but not incompleteness ("what did we both miss?"). The AI sees implementation angles that the human doesn't — integration points, edge cases, data shape decisions. Catching these in intent is cheaper than catching them in code.

**Decision:** Added Step 4 to the P6 workflow: "AI stress-tests intent." Three challenge dimensions: constraint completeness, implementation anticipation, assumption challenge. This is Principle 2 (Understanding Must Be Executable) applied reflexively to the intent itself. Canonical status — it addresses a structural workflow gap, not an optional enhancement.

**Changes:** `ivd_system_intent.yaml`, `framework.md`, `README.md`, `templates/intent.yaml`, `recipes/agent-rules-ivd.yaml` (Rule 4), `mcp_server/tools/validate.py`, book intents (Ch3, Ch4), `book_system_intent.yaml`.

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
- Book Ch1 §1.2: cognitive mechanism added to "Why Traditional Artifacts Fail"
- Book Ch2 §2.6: intent artifact as contextual channel saturation; lost-in-the-middle for Protocol Step 1
- Book Ch3 §3.2: entropy argument for Principle 2 (executable understanding)
- Book Ch3 §3.4: lost-in-the-middle explanation for Principle 4 verification protocol
- Book Ch12 §12.1: full theoretical foundation before experiments — the "why" before the "what"

**Commercial rationale:** The best-selling tech books explain WHY at a level that makes readers feel smarter. IVD can now explain that hallucinations are not "AI being wrong" — they're a predictable consequence of loading the wrong knowledge system with the wrong artifact format. That's the sentence that makes someone buy the book and recommend it to every engineer on their team. Quotable: *"Hallucinations aren't AI being wrong. They're AI using the wrong knowledge system — because you didn't feed the right one."*

**Changes (wave 1):** `ivd_system_intent.yaml` (v2.0), `framework.md` (v2.0), book chapter intents: Ch1 (v2.6), Ch2 (v1.5), Ch3 (v1.9), Ch12 (v1.1).

**Changes (wave 2 — prominence upgrade):** `purpose.md` (new "Two Knowledge Systems" section with table and mechanism), `README.md` (cognitive mechanism in "Why IVD?" section), `book_system_intent.yaml` (v2.8, cognitive foundation in book goal/thesis), `recipes/agent-rules-ivd.yaml` (Step 1 `why` updated with lost-in-the-middle rationale), `DECISIONS.md` (this entry updated).

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
- Book Ch3 intent (v2.0): §3.3 required_content extended with empirical refinement + new key_point
- Book Ch2 intent (v1.6): §2.3 workflow note — implementation can trigger refinement loop back to intent
- `book_system_intent.yaml` (v2.9): Ch3 key_points + placeholder updated
- `DECISIONS.md`: this entry (FDR-009)

**Relationship to other FDRs:**
- **FDR-006 (Intent Stress Test):** Stress test anticipates before implementation. Empirical refinement discovers during implementation. Together they close the loop.
- **FDR-008 (Cognitive Foundation):** Empirical refinement is grounded in the same cognitive mechanism — stale intent = stale contextual knowledge = parametric gap-filling.

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
