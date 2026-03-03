# Chapter 3: The Eight Principles in Depth

Chapter 2 introduced you to **Intent-Verified Development** and gave you the map: the eight principles that make intent verifiable in the AI Agents era. You know the workflow now—you describe, the AI writes intent, you review, the AI implements and verifies. You have seen why it works: executable understanding fails loudly, and hallucinations are caught at the source.

This chapter delivers the deep dive. Each principle is a rule you can state in one line, a pattern you can apply, and a violation you can recognize. By the end, you will understand not just *what* the principles are, but *why* each is essential and how they work together as a system.

Let's begin.

---

## 3.1 Principle 1: Intent is Primary

**Intent is the primary artifact. Code and documentation are derived.**

This is the foundational principle of IVD. Intent describes *what* the system should accomplish and *why*. Code describes *how* it's currently done. Documentation explains the implementation. The flow is: Intent → Implementation + Documentation. Not: Code → Documentation. Not: Documentation → Code.

Intent is technology-agnostic. It says "qualify leads with 85% precision," not "use an XGBoost model with these parameters." When you rewrite from Python to Go, the intent transfers. The *what* and *why* persist; only the *how* changes. Intent is version-controlled—it lives in the repository alongside the code, in the same directory. When the code changes, the intent can verify alignment. When the intent changes, the code must update. This co-location is deliberate: intent that lives in a separate docs repo drifts the moment the code changes.

**What breaks without it:** Code becomes the source of truth. Documentation drifts. The AI has nothing to verify against—it reads code and guesses what the intent was. Knowledge is lost when the team changes, when the language changes, when the framework changes. Intent-as-afterthought is not intent; it is documentation that was already obsolete before it was written.

**Common violations:** Intent added after code (as retrospective documentation). Intent that describes *how* instead of *what* (e.g. "use this library" instead of "achieve this goal"). Intent that lives in a wiki or a separate docs repo where version control doesn't tie it to the code. All three violate the principle: intent must be primary, co-located, and agnostic.

---

## 3.2 Principle 2: Understanding Must Be Executable

**Prose can be wrong silently. Executable understanding fails loudly.**

Every claim in an intent artifact must be verifiable through executable tests. A constraint says "precision must be ≥ 85%"—that constraint links to a test file: `tests/test_precision.py::test_meets_threshold`. A performance target says "p95 latency < 100ms"—that target links to a dashboard or monitoring system. Evidence for a design decision says "threshold validated with stakeholders"—that evidence links to a notebook or meeting notes file in the repository.

This is the shift from *readable* to *executable*. Prose is readable. An intent artifact is also readable—but every claim in it can be *checked*. The AI can run the tests, measure the metrics, and verify the evidence exists. When understanding is executable, it cannot be wrong silently. If the code violates a constraint, the test fails. If evidence is missing, the link is broken. The failure is loud.

**What breaks without it:** Prose claims that cannot be verified. Constraints that have no test—so the AI and the human can only guess whether the implementation satisfies them. Evidence that is "somewhere" but not linked—so it cannot be reproduced. Metrics that cannot be measured—so "success" is subjective. Without executable understanding, the intent artifact is just another document that drifts and lies. With it, the AI can verify and catch hallucinations before they ship.

### The Entropy Argument

Why does prose fail silently while executable constraints fail loudly? The answer is **interpretive entropy**.

Consider a prose statement: "the system should be fast and reliable." How many plausible interpretations does that sentence have? Dozens. "Fast" could mean sub-second response, sub-100ms, or just "faster than the current system." "Reliable" could mean 99.9% uptime, graceful degradation, or simply "doesn't crash." The model must *choose* between these interpretations—and it chooses using **parametric training data**: the most common patterns it absorbed during training. High interpretive entropy means many valid readings; the model picks one, and you discover which one only after reviewing the output.

Now consider an executable constraint: `p95 latency < 200ms`, linked to `tests/test_performance.py::test_p95_latency`. How many plausible interpretations does that have? **One.** The test either passes or fails. There is nothing for the parametric channel to fill. The interpretive entropy is **near-zero**.

This is the mechanism behind Principle 2. Executable understanding reduces interpretive entropy to near-zero. When entropy is zero, there is nothing to guess. When there is nothing to guess, there are no hallucinations. When there are no hallucinations, the test either passes or fails—**loudly**.

Prose has high entropy → model fills gaps with parametric knowledge → hallucination. Executable constraints have near-zero entropy → model matches or fails → loud, verifiable signal. That is why prose fails silently and executable understanding fails loudly.

**Common violations:** Constraint with no test path (e.g. "must be fast" with no linked benchmark or threshold). Prose claims without verification (e.g. "this algorithm is optimal" with no proof or experiment link). Evidence that references "the meeting" but has no file or note to verify. All of these reduce intent to prose—and prose fails silently.

---

## 3.3 Principle 3: Bidirectional Synchronization

**Changes flow in any direction: Intent → Code → Docs → Intent, with verification.**

Changes can originate from the intent, from the code, or from the documentation. All directions are valid. You might update the intent (e.g. raise the precision threshold from 85% to 90%) and then update the code and tests to match. You might refactor the code (e.g. rewrite from Python to Go) and then verify the intent constraints still pass. You might clarify the documentation (e.g. update the README to explain an edge case) and then verify it matches the intent and the code.

The key is verification at every change. Intent changes trigger implementation updates. Code changes trigger constraint tests. Documentation changes validate against the intent. This bidirectional flow prevents silent drift. If you change the code without running the constraint tests, the code and intent can diverge and no one notices until the system breaks. If you change the intent without updating the code, the intent is aspirational—it describes what the system *should* do, not what it *does* do. Both are drift, and both are violations.

**What breaks without it:** One-way flow allows silent drift. If changes only flow Intent → Code, then code refactors and fixes accumulate but the intent is never updated—so the intent becomes stale and wrong. If changes only flow Code → Documentation, the intent is never consulted—so intent becomes a relic. Bidirectional sync with verification ensures the three artifacts (intent, code, docs) stay aligned. Without it, you get the traditional failure mode: code works, docs lie, and intent is forgotten.

### Empirical Refinement: When Implementation Reveals New Knowledge

There is a sync direction you may not have considered: **reality → intent**.

You write intent. The AI implements. During implementation, the AI discovers that something in the intent is wrong—not because the intent was poorly written, but because reality differs from your assumptions. The API returns a different format than documented. The model's accuracy is lower than the benchmarks claimed. The latency exceeds documented limits. The dependency has a rate limit no one mentioned.

This is not drift. This is **empirical discovery**. The intent contained assumptions; implementation tested them against reality; reality won.

The protocol is five steps:

1. **STOP.** Do not continue implementing against assumptions you now know are wrong. Building on stale assumptions wastes turns and produces code you will throw away.
2. **RECORD.** Document what the intent assumed versus what you observed. Be specific: "Intent assumed API returns JSON array; actual response is paginated with `next_cursor` field."
3. **UPDATE.** Edit the intent artifact on disk with the empirical evidence. Replace the assumption with the observed behavior.
4. **ENRICH.** Pull in more contextual knowledge—API docs, model cards, actual error responses, performance benchmarks from your test environment. Load the contextual channel with *empirical facts* instead of assumptions.
5. **CONTINUE.** Resume implementation from the corrected intent. The AI now builds against verified reality, not a guess.

Through the cognitive lens: the intent artifact is the **contextual knowledge spine**. When it contains assumptions instead of empirical facts, the model fills gaps with parametric knowledge—the exact gap-filling that causes hallucinations. Updating the intent with empirical evidence replaces stale assumptions with verified facts, loading the contextual channel with accurate information. The model's ~70% contextual reliance now works *for* you, not against you.

The relationship to the **stress test** (Principle 6, Step 4) is complementary: the stress test *anticipates* gaps before implementation—it probes the intent for completeness, missing constraints, and implicit assumptions. Empirical refinement *discovers* gaps during implementation—when running code reveals something no amount of pre-implementation analysis could have predicted. Together, they close the loop: anticipate what you can, discover what you couldn't, and update the intent either way.

**Common violations:** Code change without running constraint tests (drift detection fails). Intent change without implementation plan or PR (intent becomes aspirational, not actual). Documentation that contradicts the intent or the code (no one verified alignment). Implementing against assumptions you *know* are wrong because the intent hasn't been updated yet—building on stale contextual knowledge and letting the parametric channel fill the gaps. All four allow drift—and drift compounds until the cost of re-alignment is prohibitive.

---

## 3.4 Principle 4: Continuous Verification

**Verify alignment at every commit, every PR, every deploy.**

Verification is not a one-time activity. It is continuous. Your CI/CD pipeline runs constraint tests on every commit. Your deployment validates success metrics. Your sprint retrospective reviews intent accuracy. When code changes, tests run. When intent changes, implementation updates and tests re-run. When metrics drift (e.g. precision drops from 90% to 80%), alerts fire.

Continuous verification catches misalignment early. A constraint test that fails on commit is caught in minutes. The same misalignment discovered six months later—after dozens of features built on the wrong foundation—costs weeks to unwind. The principle is: verify often, fail fast, fix immediately. Drift detected early is cheap. Drift detected late is catastrophic.

**What breaks without it:** One-time verification at initial implementation. The intent and code align on day one—and then code evolves, edge cases are added, refactors happen, and no one re-checks the constraints. Six months later, the system violates the original intent and no one knows until a production incident. Or: intent changes (e.g. new regulatory requirement raises precision threshold) but no one runs the tests, so the code is non-compliant and you only find out during an audit.

Continuous verification answers: *does the output still pass the constraints?* For systems that run repeatedly—autonomous workflows, self-improving agents—the question extends further: *how good is the output, and how can it improve?* An experimental `evaluation` section (Chapter 6) formalizes this continuous improvement loop: evaluate output quality against metrics, propose adjustments within declared boundaries, re-verify, and iterate—bounded by a maximum number of iterations and escalation rules. Evaluation is verification extended from binary (pass/fail) to continuous (quality measurement with structured improvement).

### The Post-Implementation Verification Protocol

Principle 4 becomes concrete for AI agents through the **verification protocol**—a 4-step audit the AI executes after every implementation:

1. **Re-read the intent artifact from disk.** Do not rely on the intent as it exists in the conversation context. Load the file fresh.
2. **Diff the implementation against every constraint.** For each constraint in the intent, check: does the code satisfy it?
3. **Run linked test paths.** Execute every test referenced in the constraints. Collect pass/fail results.
4. **Report: PASS, FAIL, or NEEDS_REVIEW.** If all constraints pass, report PASS. If any fail, fix and re-verify. If a constraint cannot be automatically verified (e.g., requires human judgment), report NEEDS_REVIEW with the specific constraint.

Without this protocol, "continuous verification" is aspirational. With it, the AI has a concrete, repeatable audit it executes after every change.

### Why Re-Reading from Disk Is Cognitively Necessary

Step 1 of the protocol—re-reading the intent artifact from disk—is not a ritual. It is a **cognitive necessity** grounded in how LLMs process long contexts.

Research on long-context models reveals the **lost-in-the-middle effect**: attention degrades log-linearly for information positioned in the middle of a long context window, even in GPT-4 and Claude 3. The *effective* context window can be dramatically smaller than the *advertised* limit for mid-positioned information. As a conversation grows—requirements discussion, intent writing, implementation, debugging—the original intent artifact drifts toward the middle. The model's attention to it weakens. Constraints that were clear at the start become fuzzy by the time verification runs.

Re-reading from disk repositions the ground truth at the **top of the context stack**, where the attention mechanism weights it highest. The model verifies against the full, fresh artifact—not a degraded representation buried in conversation history. This is not a best practice. It is a direct response to how transformer attention works.

### Agent Instruction Files as Runtime Enforcement

The verification protocol needs an enforcement point—somewhere the AI agent is *told* to run it. That enforcement point is the **agent instruction file**: `.cursorrules`, `.clinerules`, or equivalent configuration that the AI agent reads at the start of every session.

The IVD agent rules recipe (`recipes/agent-rules-ivd.yaml`) provides the concrete rules block: after every implementation, re-read intent from disk, diff against constraints, run tests, report result. When you add these rules to your agent's instruction file, the protocol runs automatically. The agent doesn't need to remember; the rules enforce it.

**Common violations:** No automated constraint tests in CI (so verification is manual and skipped). No review cadence for intent accuracy (so intent drifts from reality). No drift detection mechanism (so silent divergence compounds). Verification only at initial implementation, never again (so the first alignment is the last). AI agent implements but skips verification step (no agent rules enforce the protocol). All five allow drift to compound unchecked—and that is the default mode in most codebases today.

---

## 3.5 Principle 5: Layered Understanding

**Understanding has layers: Intent → Constraints → Rationale → Alternatives → Risks.**

Each layer answers a different question. The *Intent* layer declares what the system should accomplish. The *Constraints* layer declares what must hold true. The *Rationale* layer explains why this approach was chosen. The *Alternatives* layer documents why other approaches were rejected. The *Risks* layer documents what could go wrong and how to monitor for it.

All layers are verifiable, not just prose. Intent has required fields: `summary`, `goal`, `success_metric`. Constraints have required fields: `name`, `requirement`, `test`, `consequence_if_violated`. Rationale has required fields: `decision`, `reasoning`, `evidence`, `date`, `stakeholder`. Each layer is structured YAML that the AI can parse and verify. This is layered understanding as a contract, not as prose that can drift.

**What breaks without it:** Flat documentation. Code with comments that explain *what* but not *why*. A constraint with no context (so when it's violated, no one knows whether to fix the code or relax the constraint). A design decision with no record of alternatives considered (so when performance degrades, the team considers options that were already rejected and doesn't know why). A risk with no monitoring strategy (so the failure is silent until production).

Layered understanding preserves the full context. When a developer joins six months later, they can read the intent (what we're trying to do), the constraints (what must hold), the rationale (why this approach), the alternatives (why not the other way), and the risks (what we're watching for). That is the difference between understanding that survives and understanding that dies with the original implementer.

**Common violations:** Missing required layer (e.g. intent with no rationale—so no one knows why this approach). Layer missing required fields (e.g. rationale with no evidence—so it's just opinion). Rationale without evidence (so it cannot be verified). Alternative with no rejection reason (so it's not clear whether it was considered). Risk with no monitoring strategy (so you can't tell if the risk is active). All of these reduce understanding to partial knowledge—and partial knowledge guesses to fill the gaps.

---

## 3.6 Principle 6: AI as Understanding Partner

**AI writes the intent, implements against it, and verifies—not just syncs.**

This is the principle that makes IVD the framework for the **AI Agents era**. In traditional development, a human writes requirements and a human developer implements. In IVD, the **AI writes the intent artifact**—not the human. The human describes what they want in natural language. The AI, following the IVD framework, produces a structured intent artifact with constraints and tests. The human reviews: "Is this what I meant?" The AI then implements against the intent it wrote. The AI then verifies: "Does my code pass the constraints?"

The workflow is: **You describe → AI writes intent → You review → AI stress-tests intent → AI implements → AI verifies.** Clarification happens at the intent stage, before a single line of code exists. The stress test catches gaps before implementation begins. The AI catches its own hallucinations through verification—the test fails, the AI fixes, and you never see the wrong version. Turns drop from many to one, or from many to zero if the AI self-corrects before you review.

This is not the AI reading a PRD you wrote and implementing. This is not the AI reading your prompt and guessing what matches. This is the AI *producing understanding* in a form it can later verify against. The shift is profound: the AI is not just an executor; it is a partner in creating, refining, and maintaining understanding. It writes intent, stress-tests it, implements, and checks alignment—continuously.

**What breaks without it:** The AI reads prose (PRD, user story, prompt) and fills in the gaps. You get plausible but wrong output. You correct. The AI tries again. The many-turns problem persists. Hallucinations slip through because there is no structured artifact to verify against—only prose to interpret. This was the failure mode described in Chapter 1. Principle 6 is the antidote: the AI produces the contract, not just the code.

### The Intent Stress Test (Step 4)

After you review the intent and confirm "yes, that's what I meant," the AI does not jump straight to implementation. First, it **stress-tests its own intent**.

The stress test is an adversarial self-check. The AI probes the intent artifact for:
- **Constraint gaps:** Are there behaviors that should be constrained but aren't? (e.g., "What happens when the CSV has 100,000 rows? The intent doesn't say.")
- **Implicit assumptions:** Does the intent assume something that was never stated? (e.g., "The intent assumes a single database, but the architecture uses read replicas.")
- **Implementation decisions not addressed:** Are there choices the AI will have to make during implementation that the intent doesn't cover? (e.g., "Pagination strategy: cursor-based or offset-based? The intent doesn't specify.")

The AI surfaces these gaps *before* writing a single line of code. You review the gaps, clarify, and the AI updates the intent. This catches flaws at the **cheapest possible point**—cheaper than implementation, cheaper than testing, orders of magnitude cheaper than production.

The relationship to **empirical refinement** (Principle 3) is complementary: the stress test *anticipates* gaps before implementation; empirical refinement *discovers* gaps during implementation when running code reveals something no pre-implementation analysis could predict. Together, they close the loop.

**When to skip:** For trivial changes—a config update, a one-line fix, a clear mechanical task—the stress test adds overhead without value. Use it when the intent has meaningful complexity, when the stakes matter, or when you're building something new. Skip it when the change is obvious.

### Linguistic Mirroring as an Alignment Signal

Before the formal stress test, you can detect misalignment through a simpler heuristic: **does the AI echo your key terms?**

When you say "admin compliance CSV export with ISO dates" and the AI writes an intent artifact using "admin compliance CSV export" and "ISO 8601," it is *mirroring* your vocabulary. This signals alignment—the AI understood your key concepts.

When the AI substitutes your terms—"admin" becomes "users," "CSV export" becomes "data dump"—it signals misalignment *before intent is even written*. Catch it here, and you save the cost of writing, reviewing, and stress-testing an intent that was wrong from the start.

**Linguistic mirroring is not verification.** The AI might echo your terms and still produce wrong code. But if it *fails* to echo your terms, you've caught a misunderstanding at the cheapest possible point.

**Common violations:** AI only implements (you write the intent, AI codes—this is traditional, not IVD). AI skips the stress test and discovers gaps during implementation—more expensive, more turns, and the gaps are harder to fix once code exists. No verification step (AI implements but doesn't run constraint tests—so hallucinations slip through). Unstructured prose (intent is natural language paragraphs the AI cannot parse—so it guesses, and guessing is hallucination). The first violation reduces IVD to "another artifact the human writes"; the second wastes the cheapest error-detection point; the third allows hallucinations to ship; the fourth makes verification impossible. All four break the principle.

**When you lack technical knowledge**: Principle 6 covers **teaching**. If you don't understand domain concepts/patterns/technologies (e.g. "What is ETL?" or can't review intent because it references "Saga pattern"), the AI creates structured educational artifacts explaining what you need to know, with verification questions; you confirm understanding; then the workflow runs—you describe, AI writes intent, you review, AI implements and verifies. This addresses the critical bottleneck: you can't participate in IVD if you lack the knowledge to understand the concepts.

**When you can't yet describe what you want** *(Experimental)*: Principle 6 also covers **discovery**. If you lack goal clarity (new domain, unfamiliar codebase, or "I'm not sure what we need") but understand the concepts once explained, the AI can propose 2–3 candidate goals or patterns (e.g. from recipes or existing features) with short tradeoffs; you pick or refine; then the same workflow runs—you describe (now with a direction), AI writes intent, you review, AI implements and verifies. Discovery is part of being an understanding partner, not a separate principle. *(This pattern is being validated; use it and share results to help promote it to canonical.)*

---

## 3.7 Principle 7: Understanding Survives Implementation

**Implementation changes. Languages change. Intent persists.**

Intent artifacts document *what* and *why*, not *how*. When you rewrite from Python to Go, the intent transfers. The system still qualifies leads with 85% precision; only the language and libraries changed. When you replace an XGBoost model with a neural network, the constraints remain: precision, latency, resource limits. The intent artifact does not care about the implementation—it cares about behavior.

This is survival through abstraction. Code is ephemeral. Frameworks are replaced. Languages go out of fashion. The team turns over every two to three years. Intent—if it describes behavior and not implementation—persists through all of it. Constraints like "precision ≥ 85%" are testable in any language. Rationale like "threshold chosen because sales validated" explains the context without locking in the technology. When the next implementer arrives, they read the intent and understand what the system is supposed to do and why, without reverse-engineering old code.

**What breaks without it:** Intent coupled to implementation. An intent artifact that says "use XGBoost with these hyperparameters" is useless when you switch to a neural network—you have to rewrite the intent. A constraint that tests "XGBoost internal state" is not portable to Go. Rationale that does not explain *why* a threshold was chosen—only *how* it was tuned—is lost when the model changes. Intent that documents the implementation instead of the goal dies with the implementation. That is the failure mode of traditional documentation.

This principle extends naturally to how you document an agent's capabilities and behavior. An intent artifact can include an `interface` section that describes the agent's callable tools—name, parameters, returns, test path—without referencing the implementation language or framework. Rewrite the agent from Python to TypeScript; the interface section still describes the same tools. The same is true for behavioral modes: an experimental `roles` section (Chapter 4) can describe how an agent behaves differently in different contexts—reviewer is read-only, implementer can modify files—without tying those definitions to specific code. Both survive rewrites because they describe *what* the agent does and *how it behaves*, not *how it's built*.

**Common violations:** Intent tightly coupled to a specific library (e.g. "use XGBoost" instead of "classify with 85% precision"). Constraint that tests implementation detail, not behavior (e.g. "model must have exactly 10 trees" instead of "precision ≥ 85%"). Rationale missing for major decisions (so when you revisit, you don't know *why* this approach was chosen—you only know *what* the code does). All three make intent fragile. When the implementation changes—and it will—intent is obsolete.

---

## 3.8 Principle 8: Innovation through Inversion

**Innovation comes from inverting dominant beliefs—state the default, invert it, evaluate, implement.**

LLMs have absorbed the conventional way to solve most problems. When you ask an AI to design a CSV export, it defaults to "load file, parse rows, write output." That is the *dominant belief*: the way most developers would do it, the way Stack Overflow answers describe it. It is not always wrong—but it is not always the best.

Principle 8 is a method for surfacing non-obvious solutions. The four steps: **State the Default** (what is the conventional approach?), **Invert** (what if we did the opposite?), **Evaluate** (is the inversion better for this case?), and **Implement** (if yes, capture in intent and verify). The default for CSV export is "load entire file into memory." The inversion: "stream rows; never load the file." The evaluation: streaming is better for large files but loses random access. If your use case is large files and sequential processing, the inversion wins—and you document it in the intent artifact's `inversion_opportunities` block so the decision is explicit and transparent.

**When to use it:** You are designing a new feature or module; the problem has a conventional approach; the stakes matter (performance, scale, security, or maintainability); you want the intent to document why the default was rejected or inverted. Use it when the inversion could make a material difference and you want the reasoning preserved.

**When to skip it:** You are fixing a small bug, updating config, or making a simple refactor. There is no clear conventional approach (e.g. a purely custom business rule). The obvious solution is good enough—you are not optimizing for alternatives. Inversion is a tool for design decisions, not for every line of code. Apply it where it adds value; skip it where the default is fine.

**What breaks without it:** You ship the default approach without ever considering whether an inversion is better. You optimize for "what everyone does" instead of "what this use case needs." You inherit dominant beliefs—load-then-parse, client-sends-all-data, server-does-work—and never question them. Some defaults are good. Others are not. Principle 8 makes the evaluation explicit so innovation is intentional, not accidental.

**Common violations:** Inversion documented in the intent artifact but the implementation contradicts the chosen approach (e.g. you documented "we chose streaming" but the code loads into memory—drift). Dominant belief stated but no evaluation of whether inversion is better (so the decision was never made, only assumed). Inversion applied everywhere (over-application; small fixes do not need it). The first is drift; the second is unexamined default; the third is bureaucracy. All three miss the principle: invert *where it matters*, document the choice, implement and verify.

---

## 3.9 The System View: How Principles Reinforce Each Other

The eight principles are not independent rules. They are a system. Each principle depends on and reinforces the others. Remove one, and the system weakens. Apply all eight, and IVD works.

**Principle 1** (Intent is Primary) enables **Principle 2** (Understanding Must Be Executable). Intent is the contract that tests verify. Without intent as primary, there is nothing structured to make executable. Code cannot verify itself—it can only run. Intent provides the external artifact that says "this is what the code should do," and Principle 2 makes that statement testable.

**Principle 6** (AI as Understanding Partner) depends on Principles 1 through 5. The AI writes intent (Principle 1). The AI writes executable constraints and links to tests (Principle 2). The AI updates intent and code bidirectionally (Principle 3). The AI verifies continuously (Principle 4). The AI produces layered understanding: intent, constraints, rationale, alternatives, risks (Principle 5). Without those five, Principle 6 cannot work—the AI would have no framework to follow, no structure to produce, and no verification to run.

**Principle 8** (Innovation through Inversion) feeds into **Principle 5** (Layered Understanding). When you invert a dominant belief and choose the inversion, that decision belongs in the *Rationale* layer (why this approach) and the *Alternatives* layer (why the default was rejected). The inversion is not separate from understanding—it is part of it. Principle 8 provides the method; Principle 5 provides the structure to preserve the decision.

**Principle 7** (Understanding Survives Implementation) is enabled by Principle 1 (Intent is Primary) and reinforced by Principle 2 (Understanding Must Be Executable). Intent that is technology-agnostic (Principle 1) can transfer to new implementations. Intent that has executable constraints (Principle 2) can verify the new implementation without rewriting the tests. When you rewrite Python → Go, you rewrite the code; you do not rewrite the intent. That is survival.

The principles form a loop: Intent is primary → make it executable → sync bidirectionally → verify continuously → layer the understanding → let AI write and verify → let understanding survive implementation changes → innovate through inversion where it matters. Each principle locks the others in place. That is why the system works. That is why removing even one principle weakens the whole.

You are now ready to build. Chapter 4 turns to the artifact itself—what an intent artifact contains, the four levels (System, Workflow, Module, Task), where intents live, and how to write your first one.

---

## Key Points

- **Principle 1: Intent is the primary artifact.** Code and documentation are derived. Intent is technology-agnostic, version-controlled, and co-located with code.

- **Principle 2: Prose can be wrong silently. Executable understanding fails loudly.** Every claim in intent must be verifiable through tests. Constraints link to test files; evidence links to experiments; metrics are measurable. The mechanism: prose has high interpretive entropy (model fills gaps with parametric training); executable constraints have near-zero entropy (nothing to guess, nothing to hallucinate).

- **Principle 3: Changes flow in any direction—Intent → Code → Docs → Intent—with verification.** Bidirectional sync prevents silent drift. All changes trigger verification. Empirical refinement adds a critical sync direction: reality → intent. When implementation reveals wrong assumptions, STOP, update the intent with empirical evidence, and continue. The stress test (P6) anticipates gaps; empirical refinement discovers them. Together they close the loop.

- **Principle 4: Verify alignment at every commit, every PR, every deploy.** Continuous verification catches misalignment early. Drift detected late is expensive; drift detected immediately is cheap. The verification protocol (4-step audit: re-read from disk, diff constraints, run tests, report PASS/FAIL) makes this concrete for AI agents; agent instruction files (`.cursorrules`, `.clinerules`) enforce it at runtime. Re-reading from disk is cognitively necessary—the lost-in-the-middle effect degrades attention to mid-positioned content.

- **Principle 5: Understanding has layers—Intent, Constraints, Rationale, Alternatives, Risks.** Each layer answers different questions. All layers are verifiable, not just prose.

- **Principle 6: AI writes the intent, implements against it, and verifies—not just syncs.** The key principle for the AI Agents era. The full workflow: describe → AI writes intent → review → AI stress-tests → AI implements → AI verifies. Extensions: teaching before intent (canonical) when you lack domain knowledge; discovery before intent (experimental) when you can't articulate the goal; linguistic mirroring as an early alignment signal; intent stress test (Step 4) as adversarial completeness check before implementing.

- **Principle 7: Implementation changes. Languages change. Intent persists.** Intent documents behavior, not implementation. Constraints are technology-agnostic. Understanding survives rewrites and team turnover.

- **Principle 8: Innovation comes from inverting dominant beliefs.** State the default, invert, evaluate, implement. Use it when designing major features with conventional approaches and high stakes. Skip it for small fixes and obvious solutions.

- **The principles work as a system, not independent rules.** Principle 1 enables Principle 2; Principle 6 depends on 1–5; Principle 8 feeds into Principle 5. Remove one, and the system weakens. Apply all eight, and IVD works.
