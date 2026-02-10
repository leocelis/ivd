# Intent-Verified Development: Cheat Sheet

**The Framework for the AI Agents Era (v1.4)**

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

**Teaching:** If the user lacks technical knowledge → AI creates educational artifact (e.g. `ivd_teach_concept(concept="ETL")`) → user understands → then proceed. Recipe: `teaching-before-intent.yaml`.

**Discovery:** *(Experimental)* If the user can't describe yet (but understands concepts) → AI proposes goals/recipes/options (e.g. `ivd_discover_goal`, list recipes) → user picks → then AI writes intent. Recipe: `discovery-before-intent.yaml`.

```
You: "Add export to CSV for admin compliance"

AI: [Writes structured intent with constraints and tests]
    "Here's the intent I wrote. Does this capture what you meant?"

You: "Yes"

AI: [Implements against intent, runs tests, all pass]
    "Done. All constraints verified."
```

AI writes intent, implements, verifies—not just executes prompts.

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
2. Understanding is executable
3. Bidirectional synchronization
4. Continuous verification
5. Layered understanding
6. AI as understanding partner
7. Understanding survives implementation

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
- **`templates/intent_levels_guide.md`** - When to use which intent level
- **`recipes/`** - Reusable pattern templates

---

*"In the AI Agents era, the AI writes the intent, implements against it, and catches its own hallucinations."*
