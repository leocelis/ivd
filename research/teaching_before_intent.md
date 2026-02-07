# Teaching Before Intent: When the User Lacks Technical Knowledge

**Purpose:** Document the critical gap (user lacks technical knowledge to understand concepts/patterns, not just goal uncertainty), IVD's response under Principle 6, and the teaching-before-intent pattern.  
**Status:** Canonical (addresses critical bottleneck: lack of technical knowledge is main blocker in project critical paths)  
**References:** `ivd_system_intent.yaml` (principle_6_ai_partner.extensions), `recipes/teaching-before-intent.yaml`, `framework.md` (When the User Lacks Technical Knowledge; Step 0a)

---

## 1. The gap

IVD's canonical workflow assumes the user can **describe** what they want (even roughly): **Human describes → AI writes intent → Human reviews → AI implements → AI verifies.**

"Discovery before intent" addresses: user doesn't know *what* to build (goal uncertainty) → AI proposes options → user picks → then describe.

But there's a deeper gap: **user lacks the technical knowledge to understand domain concepts, patterns, or technologies** needed to:
- Evaluate discovery options (can't choose between "batch ETL" vs "streaming ETL" if they don't know what those mean)
- Review intent artifacts (AI writes intent using "saga pattern" or "CDC" but user can't review it without understanding those concepts)
- Describe requirements (can't describe ETL requirements if they don't know what ETL is)

**This is the critical bottleneck:** Lack of technical knowledge blocks the entire IVD flow. The user is stuck before they can even start.

---

## 2. Real examples

### Example 1: User needs ETL but doesn't know what ETL is

**User:** "I need to sync leads from Salesforce to our analytics database daily."  
**AI (discovery):** "Here are 3 options: (A) Batch ETL with incremental load, (B) Streaming ETL with CDC, (C) Full refresh nightly."  
**User:** "I don't know what any of those mean. What's ETL?"

**Current state:** Discovery assumes user can evaluate options. But if they don't understand the terminology, they're stuck. They need **teaching** before they can proceed.

### Example 2: Reverse engineering existing code

**Context:** AI is writing intent from existing codebase (reverse engineering to document what already exists).  
**AI writes intent:** "This module implements a Saga pattern for distributed transactions with compensating transactions for rollback..."  
**User (reviewing intent):** "I can't review this. I don't know what 'Saga pattern' or 'compensating transaction' means."

**Current state:** User needs to understand the patterns the code uses before they can verify the intent is accurate. They need **contextual teaching** (education section in the intent itself).

### Example 3: New team member onboarding

**User:** "I'm new to this codebase. I see intent references like 'idempotent retry,' 'eventual consistency,' and 'circuit breaker.' What do these mean?"

**Current state:** User needs domain/pattern knowledge before they can work with the intents. They need **structured teaching** of the concepts used in this codebase.

---

## 3. Why discovery before intent doesn't solve this

"Discovery before intent" is for **goal uncertainty**: user doesn't know *what* to build.

"Teaching before intent" is for **knowledge gaps**: user doesn't understand the *concepts/patterns/technologies* needed.

**Different problems, different solutions:**

| Problem | Solution | When | Example |
|---------|----------|------|---------|
| Goal uncertainty | Discovery before intent | User: "I'm not sure what we need" | AI proposes 2-3 options → user picks |
| Knowledge gap | Teaching before intent | User: "I don't know what X is" | AI explains concept → user understands → then proceed |

You can have both:
1. **Teaching** (user learns what ETL is)
2. **Discovery** (user sees options: batch vs streaming)
3. **Describe** (user describes their ETL requirements)
4. **Intent** (AI writes intent)
5. **Implement** → **Verify**

---

## 4. IVD's response: teaching under Principle 6

**Principle 6 (AI as Understanding Partner)** is extended to cover teaching:

- When the user **lacks technical knowledge** to understand concepts, patterns, or technologies, the AI provides **structured teaching before intent**.
- The AI creates an **educational artifact** (YAML, not prose) explaining the concept, why it matters, key tradeoffs, and verification questions.
- The user **reviews, asks clarifying questions, confirms understanding**.
- Then the **standard IVD flow** applies: discovery (if needed) → describe → AI writes intent → review → implement → verify.

No new principle. Teaching is an **optional step 0a** under Principle 6: the AI helps the user gain the knowledge they need before they can participate in the IVD flow.

---

## 5. Pattern: teaching before intent

**When to use:**

- User explicitly asks for explanation ("What is X?" "Can you explain Y?")
- User can't evaluate discovery options because they don't understand the terms
- Reverse engineering: AI writes intent from existing code using patterns user hasn't seen
- User is new to domain/codebase and needs context
- AI detects knowledge gap from user's language (vague terms, incorrect concepts)

**Steps:**

1. **Detect knowledge gap** (user asks explicitly, or AI detects from language/context)
2. **Offer teaching** ("Would you like me to explain [concept] first?")
3. **Create educational artifact** (structured YAML: concept, why it matters, key sub-concepts, tradeoffs, verification)
4. **User reviews**, asks clarifying questions, confirms understanding
5. **Proceed to IVD flow**: discovery (if needed) → describe → intent → implement → verify

**Tools:**

- **ivd_teach_concept** — Creates structured educational artifact explaining a concept (YAML with verification questions)
- **Educational section in intent artifacts** — For reverse engineering, add `education` section to intent YAML so user learns while reviewing

**Recipe:** `recipes/teaching-before-intent.yaml`  
**Framework:** `framework.md` → "When the User Lacks Technical Knowledge: Teaching Before Intent"; Implementation Guide → Step 0a.

---

## 6. Educational artifact structure

Teaching creates a **structured YAML artifact** (not prose) that is **verifiable** (includes questions to confirm understanding).

**Structure:**

```yaml
education:
  concept: "[Concept name]"
  
  what_it_is: |
    [Clear 2-3 sentence explanation]
  
  why_it_matters_here: |
    [Why this concept is relevant to user's current task]
  
  key_concepts:
    - name: "[Sub-concept 1]"
      definition: "[What it is]"
      example: "[Concrete example from user's context]"
  
  tradeoffs:
    - decision: "[Key decision user will make]"
      options:
        - name: "[Option A]"
          when: "[When to use]"
          pros: ["[Advantage]"]
          cons: ["[Disadvantage]"]
  
  common_patterns:
    - "[Pattern 1: brief description]"
  
  next_steps: |
    [What happens next: discovery/describe/intent/implement]
  
  verification:
    - question: "[Test understanding]"
      answer: "[Expected answer]"
```

This follows **Principle 2 (Understanding Must Be Executable)**: verification questions confirm the user actually understands, not just read the explanation.

---

## 7. Reverse engineering use case

When AI writes intent from existing code, the user may not understand the patterns/concepts the code uses.

**Solution:** Add an **`education` section** to the intent artifact itself (contextual learning).

**Example:**

```yaml
intent:
  summary: "Distributed transaction coordinator using Saga pattern"
  goal: "Ensure payment + inventory + shipping either all succeed or all rollback"
  
  education:  # Optional section when user needs concept explanation
    concepts:
      - name: "Saga pattern"
        definition: "Distributed transaction pattern: sequence of local transactions, each with compensating transaction for rollback"
        why_here: "This code implements Saga to coordinate payment, inventory, shipping without distributed locks"
        tradeoff: "Eventual consistency (no ACID) but scales horizontally"
      
      - name: "Compensating transaction"
        definition: "Undo operation that reverses a completed step (e.g. refund payment, release inventory)"
        why_here: "If shipping fails, compensating transactions refund payment and release inventory"
    
    next_steps: |
      Review the constraints below. If Saga pattern is unclear, ask me to explain further.
  
  constraints:
    # ... rest of intent ...
```

User reads `education` first, then reviews `constraints` with new understanding. If still unclear, AI expands explanation or creates standalone educational artifact.

---

## 8. What teaching does and does not do

**Teaching does:**

- Explain **concepts, patterns, technologies** the user needs to understand
- Provide **structured, verifiable** educational artifacts (YAML with verification questions)
- Give **contextual examples** from user's actual project
- Confirm understanding before proceeding to IVD flow

**Teaching does not:**

- Replace discovery (teaching = "what is X?", discovery = "what should I build?")
- Replace intent (teaching output is understanding, not a plan)
- Teach everything (only what's needed for the current task)
- Guarantee user becomes expert (just enough to participate in IVD flow)

---

## 9. Why this is canonical (not experimental)

**Canonical status** is justified because:

1. **Critical bottleneck identified:** Lack of technical knowledge is the main blocker in project critical paths (per user insight)
2. **Clear gap:** User can't review intent if they don't understand the concepts it references
3. **Structured, verifiable solution:** Educational artifacts follow Principle 2 (Understanding Must Be Executable) and Principle 5 (Layered Understanding)
4. **Real use cases:** ETL example, reverse engineering, onboarding — all common, all blocked by knowledge gaps
5. **Fits IVD philosophy:** Teaching is part of "AI as Understanding Partner" (Principle 6), not a separate framework

Unlike "discovery before intent" (experimental because not yet validated in production), **teaching before intent** addresses a proven, critical blocker that has prevented IVD adoption in practice. Making it canonical signals: "IVD is unusable without this."

---

## 10. Open questions and future work

- **Measuring teaching effectiveness:** e.g. verification question pass rate, time to first successful intent review, user confidence ratings
- **When teaching is needed:** heuristics (e.g. detect unfamiliar terms in user's language, check if intent references domain-specific patterns)
- **Depth of teaching:** how detailed should educational artifacts be? (current: "just enough to proceed," but could be configurable)
- **Educational artifact reuse:** can we build a library of common concepts (ETL, Saga, CDC, etc.) so AI doesn't recreate them each time?

---

## 11. References

- **Principle 6:** `ivd_system_intent.yaml` → principle_6_ai_partner (definition, sub-principle "AI teaches when the user lacks technical knowledge", extension "Teaching before intent")
- **Recipe:** `recipes/teaching-before-intent.yaml`
- **Framework:** `framework.md` (Principle 6 subsection; Step 0a)
- **Tool:** `ivd_teach_concept` (MCP IVD tool)
- **Related:** `discovery-before-intent.yaml` (for goal uncertainty, not knowledge gaps)
