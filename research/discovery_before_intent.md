# Discovery Before Intent: When the User Doesn't Know What to Ask

**Purpose:** Document the gap (user lacks knowledge to give clear instructions or know what to ask), IVD's response under Principle 6, and the discovery-before-intent pattern.  
**Status:** Experimental (Principle 6 extension) — requires production validation before canonical  
**References:** `ivd_system_intent.yaml` (principle_6_ai_partner.extensions), `recipes/discovery-before-intent.yaml`, `framework.md` (When the User Cannot Yet Describe; Step 0b)

---

## 1. The gap

IVD's canonical workflow assumes the user can **describe** what they want (even roughly): **Human describes → AI writes intent → Human reviews → AI implements → AI verifies.**

In practice, sometimes:

- The user doesn't have enough domain knowledge to give clear instructions.
- The user doesn't know what to ask or what's possible.
- The user is new to the codebase and can't yet articulate a goal.
- The problem space is unfamiliar (new product area, new tech).

In those cases, "describe" is the bottleneck. If the user can't describe, the rest of the flow still applies once a **direction** is chosen—but we need a way to get to that direction without requiring the user to already know it.

**This is not a failure of IVD.** It is a missing step 0: **discovery** (propose options; user picks; then describe → intent flow).

---

## 2. Principle 8 does not cover this

**Principle 8 (Innovation through Inversion)** is about **solution/design** space: state the default approach, invert it, evaluate, implement. It helps surface better *technical* options (e.g. stream vs load-whole-file) once a goal exists. It does **not** help the user figure out *what* they need or *what* to ask for. So the gap is separate and is addressed under Principle 6.

---

## 3. IVD's response: discovery under Principle 6

**Principle 6 (AI as Understanding Partner)** is extended to cover discovery:

- When the user **cannot yet describe** what they want, the AI supports **discovery before intent**.
- The AI proposes 2–3 **candidate goals or patterns** (e.g. from recipes, existing features) with short tradeoffs.
- The user **picks or refines** ("that one, but for X not Y").
- Then the **standard IVD flow** applies: describe (now with a direction) → AI writes intent → review → implement → verify.

No new principle is introduced. Discovery is an **optional step 0** under Principle 6: the AI helps the user form intent when they can't yet articulate it.

---

## 4. Pattern: discovery before intent

**When to use:**

- User says "I'm not sure what we need" or "I don't know what to ask."
- New domain or unfamiliar codebase.
- User wants to see 2–3 options before committing.

**Steps:**

1. **Detect** need for discovery (user uncertainty or vague hint only).
2. **Gather options:** e.g. `ivd_list_recipes`, `ivd_list_features` (if repo context), `ivd_discover_goal` (domain/hint).
3. **Present and choose:** AI summarizes 2–3 options with one-line tradeoff each; user picks or refines.
4. **Proceed to intent flow:** user describes (with chosen direction) → AI writes intent → review → implement → verify.

**Tools:**

- **ivd_discover_goal** — Proposes 2–3 candidate directions (from recipes and optionally existing features); returns structured options and next_steps.
- **ivd_list_recipes** — List patterns (classifier, workflow, infra, doc, discovery) so user can choose a pattern first.
- **ivd_list_features** — In a repo with intents, show what already exists so "extend X" is an option.

**Recipe:** `recipes/discovery-before-intent.yaml`  
**Framework:** `framework.md` → "When the User Cannot Yet Describe: Discovery Before Intent"; Implementation Guide → Step 0b.

---

## 5. What discovery does and does not do

**Discovery does:**

- Propose a small set of candidate **directions** (goals or patterns).
- Give a one-line **tradeoff** per option so the user can choose.
- Lead into the standard intent flow once the user has a direction.

**Discovery does not:**

- Replace intent. The output of discovery is a **chosen direction**, not a full intent artifact.
- Teach the user in depth (no long tutorials); it only narrows the space so they can describe.
- Guarantee the "right" goal; it reduces the cost of the first description and of the first intent.

---

## 6. Open questions and future work

- **Measuring discovery quality:** e.g. time to first intent, user satisfaction, iteration count after discovery.
- **When discovery is needed:** heuristics (e.g. very short or very vague first message, "explore" vs "build X").
- **Formalizing discovery output:** optional minimal "discovery outcome" (chosen direction + one-line rationale) for traceability without turning it into a full intent.

---

## 7. References

- **Principle 6:** `ivd_system_intent.yaml` → principle_6_ai_partner (definition, sub-principle "AI supports discovery when the user cannot yet describe intent", extension "Discovery before intent").
- **Recipe:** `recipes/discovery-before-intent.yaml`
- **Framework:** `framework.md` (Principle 6 subsection; Step 0b).
- **Tools:** `ivd_discover_goal`, `ivd_list_recipes`, `ivd_list_features` (MCP IVD tools).
