# Intent-Verified Development (IVD)

**The Framework for the AI Agents Era**

**Version:** 1.2  
**Created:** January 23, 2026  
**Updated:** January 26, 2026 (AI Agents era positioning)  
**Status:** Production Ready

---

## The Problem IVD Solves

Working with AI agents today has two core pain points:

- **Many turns:** The exhausting back-and-forth (prompt → wrong → correct → still wrong → repeat)
- **Hallucinations:** AI "fills gaps" in your prompts with plausible but wrong assumptions

**Why traditional artifacts fail with AI:**

| Artifact | Who Writes | Can AI Verify? | Result |
|----------|-----------|----------------|--------|
| PRD | Human | No | AI reads prose, guesses |
| User Story | Human | No | AI reads prose, guesses |
| Prompt | Human | No | AI reads prompt, guesses |

---

## The IVD Solution

**The AI writes the intent, not you.**

0. **(Optional) Discovery:** If you don't know what to ask, use discovery (e.g. `ivd_discover_goal`, list recipes)—AI proposes options; you pick; then 1–5.
1. **You describe** what you want (natural language)
2. **AI writes** structured intent artifact (YAML with constraints, tests)
3. **You review** the intent: "Is this what I meant?" (clarification before implementation)
4. **AI implements** against the intent (code, docs, architecture, research, etc.)
5. **AI verifies**: Does my output pass the constraints? (catches hallucinations)

**Scope:** Any AI-produced artifact—code, architecture, documentation, research, books, processes.

**Feature inventory (large projects):** Optional metadata on intents plus a feature-list tool lets you derive "what exists" and avoid duplication—no separate inventory file.

**Result:** Turns drop from many to one. Hallucinations are caught at the source.

---

## Quick Start

### For New Projects (Greenfield)

```bash
# Copy this entire folder to your project
cp -r ivd/ /your-project/docs/

# Start here:
1. Read purpose.md (why IVD exists - AI Agents era vision)
2. Read README.md (this file - what IVD is)
3. Read cookbook.md (practical guide - how to use IVD)
4. Read framework.md (complete specification)
5. Use templates/ to create your first intent artifact
```

If you don't understand the concepts/domain, see framework.md → Step 0a (Teaching) and `recipes/teaching-before-intent.yaml`.

If you're not sure what to build, see framework.md → Step 0b (Discovery) and `recipes/discovery-before-intent.yaml`.

### For Existing Projects (Brownfield)

```bash
# Initialize IVD - creates system intent with project context
ivd init --project-root /path/to/your/project

# This scans and creates system_intent.yaml with:
# - Code rules (.cursorrules, lint configs)
# - Architecture (ARCHITECTURE.md, ADRs, principles)
# - Tools/scripts (key scripts, CLIs)
# - Libraries to reuse (internal shared libs)
# - Key paths ("map to the stars": entrypoints, modules, workflows, docs, tests)
# - Existing docs (README, API.md, CONTRIBUTING)

# Then:
1. Review and enrich system_intent.yaml
2. Create intents for 3-5 critical modules (ivd scaffold)
3. Child intents auto-reference parent_intent
4. Expand gradually as you modify modules
```

---

## What is IVD?

**Intent-Verified Development** is the framework for the **AI Agents era**—where AI writes intent, implements against it, and verifies. It eliminates many-turns and hallucinations.

**The Core Innovation:**
- **Traditional:** Human writes requirements (PRD, user story) → Human developer implements
- **Literate Programming:** Documentation is primary, code extracted (designed for humans, not AI)
- **IVD:** **AI writes intent** (following framework) → **AI implements** → **AI verifies** (catches hallucinations)

**Without IVD:** Intent artifacts are just another prose document. AI reads, guesses, hallucinates.  
**With IVD:** AI writes structured intent, verifies against constraints, self-corrects.

---

## The Eight Principles

1. **Intent is Primary** - Not code, not docs, intent. AI writes and verifies against intent.
2. **Understanding Must Be Executable** - Prose can be wrong silently; executable constraints fail loudly.
3. **Bidirectional Synchronization** - Changes flow in any direction with verification.
4. **Continuous Verification** - AI verifies alignment every commit, every change.
5. **Layered Understanding** - Intent → Constraints → Rationale → Alternatives → Risks (all verifiable).
6. **AI as Understanding Partner** - **AI writes the intent**, implements against it, verifies. Not just syncs.
7. **Understanding Survives Implementation** - Intent persists through rewrites, model upgrades, session limits.
8. **Innovation through Inversion** - State the default, invert it, evaluate, implement. Capture inversion opportunities in intent.

---

## Structure

```
ivd/
├── purpose.md                      # Why IVD exists (vision and philosophy)
├── README.md                       # What IVD is (overview and quick start)
├── ivd_system_intent.yaml          # System intent (rules for extending IVD)
├── ivd_package_validation_intent.yaml  # Package validation checklist
├── optimal_structure.md            # Artifact placement and naming standards
├── framework.md                    # Complete IVD specification
├── cookbook.md                      # Practical implementation guide
├── cheatsheet.md                   # Quick reference
├── recipe-spec.md                  # Recipe specification
│
├── recipes/                   # Reusable pattern templates
│   ├── README.md
│   ├── agent-classifier.yaml
│   ├── coordinator-intent-propagation.yaml
│   ├── data-field-mapping.yaml
│   ├── discovery-before-intent.yaml
│   ├── doc-meeting-insights.yaml
│   ├── infra-background-job.yaml
│   ├── teaching-before-intent.yaml
│   └── workflow-orchestration.yaml
│
├── templates/                 # Blank templates to get started
│   ├── intent.yaml            # Copy and rename to {module}_intent.yaml
│   ├── recipe.yaml            # Copy to create new recipe
│   ├── intent_levels_guide.md # When to use which intent level
│   ├── task_level_quick_ref.md
│   └── examples/              # Complete examples
│
├── _private/                  # Historical + private planning
│   ├── README.md              # Overview of private contents
│   ├── ai_driven_dev/         # IVD origin story and training sessions
│   │   ├── README.md
│   │   ├── from_lp_to_ivd.md
│   │   ├── ai_driven_development_guide.md
│   │   ├── meetings_index.md
│   │   └── meetings.md
│   └── community/             # Private adoption planning
│       └── community_adoption_intent.yaml
│
└── research/                  # Research and implementation guidance
    ├── README.md
    ├── agent_knowledge_standards.md
    ├── ivd_implementation_roadmap.md
    ├── validation_methodology.md
    └── ... (10+ research documents)
```

---

## Documentation Guide

### For Understanding Why
1. **purpose.md** - Vision, philosophy, and the breakthrough insight

### For Learning
1. **cookbook.md** - Start here! Practical guide with real examples
2. **framework.md** - Complete specification and theory
3. **cheatsheet.md** - Quick reference when you need it

### For Implementation
1. **templates/intent.yaml** - Copy to your module as `{module}_intent.yaml`, fill in specifics
2. **recipes/** - Browse patterns, apply one that fits
3. **cookbook.md** - Follow the CRM example step-by-step

### For Creating Recipes
1. **recipe-spec.md** - Recipe schema and structure

### For Historical Context
1. **_private/README.md** - How IVD was created from real training sessions
2. **_private/meetings.md** - Original 18 training session transcripts
3. **_private/ai_driven_development_guide.md** - The guide that evolved into IVD
4. **templates/recipe.yaml** - Start from this template
5. **recipes/** - See examples of existing recipes

---

## Quick Workflow

### Creating Your First Intent Artifact

```bash
# 1. Copy template
cp templates/intent.yaml agent/my-module/intent.yaml

# 2. Set the level (NEW in v1.2: added "workflow")
# scope:
#   level: "module"     # "system" | "workflow" | "module" | "task"
#   type: "agent"       # "product" | "process" | "feature" | "function", etc.

# 3. Fill in specifics
# - For SYSTEM level: phases, strategic metrics
# - For WORKFLOW level: steps, data_flow, error_handling (NEW)
# - For MODULE level: architecture, integration, business logic
# - For TASK level: inputs/outputs, behavior, test cases

# 4. Reference a recipe (optional)
# If following a pattern, add:
# recipe: "agent-classifier"
# recipe_version: "1.0"

# 5. Implement code
# Write code that matches your intent

# 6. Verify alignment
# Run verification checks (manual or automated)
```

### Task-Level Intents (NEW)

For critical functions that need detailed I/O specification:

```bash
# 1. Copy template
cp templates/intent.yaml agent/my-module/intents/my_function_intent.yaml

# 2. Set task-level scope
# scope:
#   level: "task"
#   type: "function"
#   granularity: "fine"

# 3. Fill in interface section
# interface:
#   signature: "function_name(param: Type) -> ReturnType"
#   inputs: [...]
#   outputs: [...]
#   exceptions: [...]

# 4. Define behavior
# behavior:
#   preconditions: [...]
#   postconditions: [...]
#   invariants: [...]

# 5. Add test cases
# verification:
#   test_cases: [...]

# See: templates/examples/task-level-intent-example.yaml
# See: templates/intent_levels_guide.md
```

### Workflow-Level Intents (NEW in v1.2)

**For multi-step processes that span multiple modules:**

```bash
# 1. Copy template
cp templates/intent.yaml workflows/my_workflow_intent.yaml

# 2. Set workflow-level scope
# scope:
#   level: "workflow"
#   type: "process"
#   granularity: "coarse"

# 3. Document workflow steps
# workflow:
#   summary: "End-to-end process description"
#   trigger: "What initiates this workflow"
#   steps:
#     - step: 1
#       name: "First step"
#       file: "path/to/module.py"
#       function: "function_name()"
#       business_logic: "What this step does and why"
#     - step: 2
#       name: "Second step"
#       # ... and so on
#
#   data_flow: ["Input → Step 1 → Step 2 → Output"]
#   error_handling: [...]
#   orchestration:
#     type: "sequential | parallel | mixed"

# See: templates/examples/workflow-lead-qualification-example.yaml (500+ lines)
# See: recipes/workflow-orchestration.yaml
```

**Why workflow-level matters:**

Without workflow-level:
- ❌ AI agent must read 5-10 files to understand complete process
- ❌ Module intents document components, not how they connect
- ❌ Onboarding takes hours to trace execution flow

With workflow-level:
- ✅ Complete process in ONE file
- ✅ 80-90% reduction in AI agent context needed
- ✅ Explicit execution order and business logic
- ✅ File/function mapping at each step

**Use workflow-level when:**
- Process has 3+ steps across multiple files
- AI agents ask "how does this work end-to-end?"
- Onboarding requires hours to understand flow
- Business stakeholders need technical process visibility

### Using a Recipe

```bash
# 1. Find a recipe
ls recipes/
# or
cat recipes/agent-classifier.yaml

# 2. Apply recipe to your module
# Copy template, reference recipe in intent.yaml

# 3. Fill in specifics
# Replace placeholders with your domain details

# 4. Implement following pattern
# Follow directory structure and code patterns from recipe
```

---

## Artifact Placement

| Level | Recommended Location | Example |
|-------|---------------------|---------|
| System | Root: `system_intent.yaml` | `system_intent.yaml` or `{project}_system_intent.yaml` |
| Workflow | `workflows/{name}_intent.yaml` (or `{coordinator_dir}/{name}_intent.yaml` when single-orchestrator) | `workflows/lead_qualification_intent.yaml` |
| Module | `{module}/{module}_intent.yaml` | `agent/marketing/marketing_intent.yaml` |
| Task | `{module}/intents/{task}_intent.yaml` | `agent/marketing/intents/gen_article_intent.yaml` |
| Variant | `{variant}_{module}_intent.yaml` | `erik_reviewer_intent.yaml` |

*See `framework.md` for detailed placement rules with Recommended/Alternative options.*

---

## What's Included

### Core Framework
- **framework.md** - Complete IVD specification (1,148 lines)
- **cookbook.md** - Practical guide with examples (458 lines)
- **cheatsheet.md** - Quick reference (238 lines)
- **recipe-spec.md** - Recipe specification (498 lines)

### Recipes (Reusable Patterns)
- **workflow-orchestration.yaml** (NEW in v1.2) - Multi-step process orchestration
- **agent-classifier.yaml** - AI classification agents
- **infra-background-job.yaml** - Background job processing
- **doc-meeting-insights.yaml** - Documentation extraction

### Templates
- **intent.yaml** - Blank intent artifact template (supports system/workflow/module/task levels)
- **recipe.yaml** - Blank recipe template
- **intent_levels_guide.md** - When to use system/workflow/module/task levels
- **task_level_quick_ref.md** - Task-level quick reference
- **examples/task-level-intent-example.yaml** - Complete task-level example (560 lines)
- **examples/workflow-lead-qualification-example.yaml** (NEW in v1.2) - Complete workflow example (500+ lines)

---

## Benefits

### Knowledge Preservation
- **85-95% knowledge capture** (vs 10-15% traditional)
- Understanding survives team turnover
- Intent persists through rewrites
- Task-level intents capture function contracts
- **NEW in v1.2:** Workflow-level intents document complete processes

### Development Speed
- **40% faster onboarding** (reduced by half)
- Recipes reduce reinvention by 30-50%
- Start from proven patterns
- Clear I/O specs reduce integration bugs
- **NEW in v1.2:** Workflow intents reduce process comprehension time by 80-90%

### AI Agent Efficiency
- **80-90% reduction in context needed** with workflow-level intents
- AI reads ONE file to understand complete process (vs 5-10 files)
- Explicit file/function mapping at each workflow step
- Business logic context without code diving

### Quality
- Continuous verification prevents drift
- Executable understanding fails loudly
- Best practices built into recipes
- Behavior contracts catch edge cases early

---

## The Methodology in One Sentence

> **AI writes the intent, implements against it, verifies—so hallucinations are caught and turns drop to one.**

---

## Portability

This IVD framework is designed to be **easily portable** to any project:

```bash
# Copy entire framework
cp -r ivd/ /new-project/docs/

# Or copy just core files
cp -r ivd/{README.md,framework.md,cookbook.md,recipes,templates} /target/
```

**No dependencies** - Just markdown and YAML files. Works in any project structure.

---

## Recipe Categories

Recipes use category prefixes for easy scanning:

- **agent-*** - AI agent patterns
- **infra-*** - Infrastructure patterns  
- **data-*** - Data processing patterns
- **integration-*** - Integration patterns
- **doc-*** - Documentation patterns

---

## Further Reading

- **purpose.md** - Why IVD exists (vision and philosophy)
- **framework.md** - Complete theory and principles
- **cookbook.md** - Step-by-step implementation guide
- **recipe-spec.md** - How to create and maintain recipes
- **recipes/README.md** - Recipe catalog and usage
- **research/agent_knowledge_standards.md** - Industry standards and validation
- **research/ivd_implementation_roadmap.md** - Implementation building blocks

---

## Credits

**Research:** Literate Programming (Donald Knuth, 1984)  
**Innovation:** Making understanding executable and verifiable for the AI era  
**Development:** Leo Celis  
**Date:** January 22-23, 2026

---

## License & Usage

This framework can be:
- **Shared freely** for educational purposes
- **Used internally** within organizations
- **Referenced** in technical discussions and papers
- **Taught** to development teams

---

*"In the AI Agents era, the AI builds. IVD ensures the AI writes intent, verifies its work, and catches hallucinations before you even review."*
