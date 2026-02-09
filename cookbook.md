# Intent-Verified Development: A Practical Cookbook

**The Framework for the AI Agents Era**

**Version:** 1.4  
**Date:** January 23, 2026  
**Updated:** February 9, 2026 (Added assess coverage step to brownfield workflow)

---

## The Problem: Many Turns and Hallucinations

Working with AI agents today has two core pain points:

- **Many turns:** You prompt the AI. It builds wrong. You correct. Wrong again. Repeat.
- **Hallucinations:** AI "fills gaps" in your prompts with plausible but wrong assumptions.

**Why traditional artifacts fail:**

| Artifact | Who Writes | Can AI Verify? | Result |
|----------|-----------|----------------|--------|
| PRD | Human | No | AI reads prose, guesses |
| User Story | Human | No | AI reads prose, guesses |
| Prompt | Human | No | AI reads prompt, guesses |

**Result:** Exhaustion. Wasted time. Distrust of AI.

---

## The Paradigm Shift

### Traditional AI Development (Current Default)
```
Human writes prompt → AI guesses intent → Builds wrong → Many turns of correction
```

### Intent-Verified Development (AI Agents Era)
```
Human describes → AI writes intent → AI implements → AI verifies → Done first try
```

**The key insight:** The AI writes the intent, not you.

---

## The Core Insight

> **AI writes structured intent, implements against it, verifies—so hallucinations are caught and turns drop to one.**

**Scope:** Any AI-produced artifact—code, architecture, documentation, research, books, processes. If AI produces it, it needs paired intent.

| Before (Prompts) | After (IVD) |
|------------------|-------------|
| "Add CSV export" (AI guesses) | AI writes intent with constraints |
| Many turns to get it right | Clarification at intent stage, done first try |
| Hallucinations discovered in review | Hallucinations caught by constraint tests |
| You correct the AI | AI corrects itself |

### Early Detection: Linguistic Mirroring

Before constraints run, check: Did the AI echo your keywords?

```
You: "Add CSV export for admin compliance reporting with ISO dates"

AI: "I'll write the intent artifact for the admin compliance 
     CSV export. Key constraints: admin-only access, ISO 8601 
     date format..."
     
→ AI echoed: "admin", "compliance", "CSV export", "ISO" ✅
→ Proceed to implementation
```

**If AI substitutes terms:**

```
You: "Add CSV export for admin compliance reporting"
AI: "I'll create a data export feature for users..."

→ AI said "users" not "admins", "data export" not "CSV export"
→ STOP. Clarify: "No, specifically for admins only, CSV format."
```

**The rule:** Echoing = understanding. Substitution = hallucination risk.

---

## Getting Started

### For New Projects (Greenfield)

1. **Copy IVD framework** to your project: `cp -r ivd/ /your-project/docs/`
2. **Read core docs:** purpose.md → README.md → cookbook.md (this file) → framework.md
3. **Create first intent:** Use `templates/intent.yaml` as starting point
4. **Start simple:** Module-level intent for your first feature
5. **Expand:** Add workflow/task intents as complexity grows

### For Existing Projects (Brownfield)

**Step 1: Initialize IVD - creates system intent with project context**

```bash
# Scan project and create system_intent.yaml
ivd init --project-root /path/to/your/project

# This captures:
# - Code rules (.cursorrules, lint configs, formatting)
# - Architecture (ARCHITECTURE.md, ADRs, design principles)
# - Tools/scripts (key scripts, CLIs, utilities)
# - Libraries to reuse (internal shared libs)
# - Key paths ("map to the stars": entrypoints, modules, workflows, docs, tests)
# - Existing docs (README, API.md, CONTRIBUTING)
```

**Step 2: Review and enrich system_intent.yaml**

The auto-generated system intent captures what it can detect. You should:
- Add architecture principles not in docs (e.g. "Event-driven with async messaging")
- Add conventions not in config files (e.g. "Use internal/logging for all modules")
- Clarify key_paths if auto-detection missed important directories
- Add libraries_reuse with when_to_use guidance

**Step 3: Assess coverage**

```bash
# See which modules have intents and which don't (prioritized)
ivd_assess_coverage(project_root="/path/to/your/project")

# Returns: covered modules, uncovered modules (high/medium/low priority),
# coverage %, and suggestions for where to start.
# Use this report to decide which modules get intents first.
```

**Step 4: Create intents for high-priority modules (start small)**

```bash
# Create intent for existing module (focus on high-priority from coverage report)
ivd scaffold --level module --name lead_scorer --module-path agent/lead_scorer

# The created intent auto-references:
# parent_intent: "../../system_intent.yaml"
```

**Step 5: Expand gradually**

- Don't create intents for entire codebase at once (overwhelming)
- Create intents when you touch a module (refactor, feature, bug fix)
- After 3-5 modules have intents, patterns become clear
- Team learns IVD through practice, not big-bang adoption
- Re-run `ivd_assess_coverage` periodically to track progress

---

### Check Before Building

#### In Large Projects: Check for Duplicate Features

Avoid duplicate features by checking what already exists before scaffolding:

1. **List features:** Use the IVD feature-list tool (e.g. `ivd_list_features`) to get an aggregated view of all intent artifacts.
2. **Filter by category or tags:** e.g. "data_export", "admin", "compliance".
3. **Check for existing:** If something equivalent exists (same `feature_id` or similar summary), extend or reuse—don't create a duplicate.
4. **Then scaffold:** If no match, add optional `metadata` (`feature_id`, `category`, `tags`, `status`) to the new intent so it appears in future lists.

See `framework.md` → "Feature Inventory (Large Projects)" for the full schema and conventions.

#### In Existing Projects: Load Project Context First

Before creating a new intent in an existing project, load the project context:

1. **Read system intent:** Load `system_intent.yaml` (or `{project}_system_intent.yaml`) at repo root
2. **Check code rules:** Follow `.cursorrules`, lint configs, formatting standards from `project_context.code_rules`
3. **Follow architecture:** Apply design principles, patterns from `project_context.architecture`
4. **Reuse tools/scripts:** Reference existing scripts from `project_context.tools_scripts` instead of creating new ones
5. **Use shared libraries:** Leverage `project_context.libraries_reuse` instead of reimplementing
6. **Navigate via key_paths:** Use "map to the stars" (`project_context.key_paths`) to find entrypoints, modules, workflows, docs, tests
7. **Reference existing docs:** Link to `project_context.existing_docs` for API refs, runbooks, contributing guidelines

**Example:**

```bash
# Before creating lead_scorer intent:
1. Read: system_intent.yaml
2. Load: project_context.code_rules → ".cursorrules says use black formatting"
3. Load: project_context.architecture → "Event-driven, idempotent operations"
4. Load: project_context.libraries_reuse → "Use internal/logging, internal/auth_utils"
5. Load: project_context.key_paths.modules → "agent/ is where agents live"
6. Create: agent/lead_scorer/lead_scorer_intent.yaml
7. Reference: parent_intent: "../../system_intent.yaml" (auto-loaded by tools)
```

**The AI workflow:**

When you ask an AI agent to create a new intent in an existing project:

```
You: "Create an intent for the lead scorer agent"

AI: 
1. Reads parent_intent (system_intent.yaml)
2. Loads project_context (code rules, architecture, tools, libraries, key_paths)
3. Writes lead_scorer_intent.yaml following:
   - Code rules from project_context
   - Architecture principles from project_context
   - References internal/logging, internal/auth_utils (libraries_reuse)
   - Follows event-driven pattern (architecture principle)
4. Writes implementation that follows conventions
5. Verifies against constraints

Result: Intent and code that fit the project, not isolated/inconsistent additions
```

---

## The Eight Principles

> **📋 Full Principle Details:** See `ivd_system_intent.yaml` for the complete specification of all 8 principles with sub-principles, validation checks, and rejection criteria.

### 1. Intent is Primary

**Intent survives:**
- Technology changes (Python → Go)
- Rewrites (rule-based → ML)
- Team turnover (knowledge persists)

**Implementation is temporary. Intent is permanent.**

---

### 2. Understanding Must Be Structured

**Prose (hard to verify):**
```markdown
We use 0.70 threshold based on some tests. Sales liked it.
```

**Structured (system can check):**
```yaml
rationale:
  decision: "threshold = 0.70"
  evidence: "playground/threshold_analysis.ipynb"
  stakeholder: "VP Sales (Jane Smith)"
  date: "2025-12-15"
```

---

### 3. Claims Must Be Verifiable

**Every claim links to proof:**

```yaml
constraints:
  - requirement: "precision >= 0.80"
    test: "tests/test_lead_scoring.py::test_precision"
    consequence_if_violated: "Sales wastes time on low-quality leads"
```

**System runs the test. Claim is proven or fails.**

---

### 4. Verification is Continuous

Not "document once and forget." Every PR, every deploy:

```bash
$ verify crm/lead_scoring/

✅ Code threshold (0.70) matches intent
✅ Tests verify precision >= 0.80
✅ Evidence notebook exists and runs
⚠️  Alert: precision at 0.81, approaching minimum
```

---

### 5. AI Writes, Implements, and Verifies

AI doesn't just implement. It writes the intent, implements, and verifies:

```
You: "Add CSV export for admin compliance"

AI: "I'll write the intent artifact first."
    [Writes structured intent with constraints and tests]
    "Does this capture what you meant?"

You: "Yes"

AI: [Implements against intent, runs tests]
    "Done. All constraints verified."
```

---

## The Intent Artifact Schema

```yaml
# {module}_intent.yaml

intent:
  summary: "One-line description"
  goal: "What you're trying to achieve"
  success_metric: "How to measure success"

constraints:
  - requirement: "What must hold true"
    test: "path/to/test.py::test_name"
    consequence_if_violated: "What breaks if this fails"

rationale:
  decision: "The key choice made"
  evidence: "path/to/notebook.ipynb"
  date: "YYYY-MM-DD"
  stakeholder: "Who approved"

alternatives:
  - name: "Alternative approach"
    rejected_because: "Why not chosen"

risks:
  - condition: "When does this become a problem"
    action: "What should happen"

implementation:
  code: "path/to/code.py"
  tests: "path/to/tests/"
```

---

## Example: CRM Lead Scoring

### The Business Context

A CRM system needs to score leads and decide which ones go to the sales team.

**Key decision:** What score threshold qualifies a lead?

---

### Step 1: Create Intent Artifact

```yaml
# crm/lead_scoring/lead_scoring_intent.yaml

intent:
  summary: "Score and qualify leads for sales outreach"
  goal: |
    Identify high-probability leads worth sales time.
    Balance quality (don't waste sales time) vs 
    quantity (enough pipeline for revenue targets).
  success_metric: "Qualified lead conversion rate >= 15%"

constraints:
  - requirement: "precision >= 0.80"
    test: "tests/test_scoring.py::test_precision_threshold"
    consequence_if_violated: "Sales wastes time on unqualified leads"
    
  - requirement: "recall >= 0.60"
    test: "tests/test_scoring.py::test_recall_threshold"
    consequence_if_violated: "Insufficient pipeline for revenue goals"

rationale:
  decision: "Qualification threshold = 0.70"
  methodology: |
    Tested thresholds 0.60, 0.65, 0.70, 0.75, 0.80
    on 500 historical leads. Measured precision/recall
    and gathered sales team feedback.
  evidence: "playground/crm/threshold_analysis_2025-12.ipynb"
  date: "2025-12-15"
  stakeholder: "VP Sales (Jane Smith)"

alternatives:
  - name: "threshold_0.60"
    rejected_because: "75% precision - sales feedback negative"
    
  - name: "threshold_0.80" 
    rejected_because: "50% recall - insufficient pipeline"
    
  - name: "ml_classifier"
    rejected_because: "Overfitting on training data"

risks:
  - condition: "Precision drops below 0.75"
    action: "Alert sales leadership, review threshold"
    
  - condition: "Market conditions change significantly"
    action: "Re-run threshold analysis quarterly"

implementation:
  code: "crm/lead_scoring/scorer.py"
  tests: "tests/test_scoring.py"
```

---

### Step 2: Clean Implementation

```python
# crm/lead_scoring/scorer.py
# Intent: lead_scoring_intent.yaml

from dataclasses import dataclass
from typing import List

# From intent artifact - see lead_scoring_intent.yaml for rationale
QUALIFICATION_THRESHOLD = 0.70


@dataclass
class Lead:
    id: str
    company: str
    score: float
    qualified: bool = False


def qualify_leads(leads: List[Lead]) -> List[Lead]:
    """
    Qualify leads for sales outreach.
    
    Intent: lead_scoring_intent.yaml
    Constraints: precision >= 0.80, recall >= 0.60
    """
    for lead in leads:
        lead.qualified = lead.score >= QUALIFICATION_THRESHOLD
    return leads


def get_qualified_leads(leads: List[Lead]) -> List[Lead]:
    """Return only qualified leads for sales team."""
    return [lead for lead in leads if lead.qualified]
```

---

### Step 3: Tests That Verify Constraints

```python
# tests/test_scoring.py

import pytest
from crm.lead_scoring.scorer import qualify_leads, QUALIFICATION_THRESHOLD

# These tests verify the CONSTRAINTS from lead_scoring_intent.yaml


def test_threshold_matches_intent():
    """Verify code threshold matches declared intent."""
    assert QUALIFICATION_THRESHOLD == 0.70, (
        "Threshold changed! Update lead_scoring_intent.yaml"
    )


def test_precision_threshold():
    """
    Constraint: precision >= 0.80
    Consequence if violated: Sales wastes time on unqualified leads
    """
    # Load historical test data (helper function loads leads with actual outcomes)
    test_leads = load_test_dataset("precision_test_set.json")
    
    qualified = qualify_leads(test_leads)
    true_positives = sum(1 for l in qualified if l.qualified and l.actual_converted)
    false_positives = sum(1 for l in qualified if l.qualified and not l.actual_converted)
    
    precision = true_positives / (true_positives + false_positives)
    
    assert precision >= 0.80, (
        f"Precision {precision:.2f} below minimum 0.80. "
        "Sales will waste time on low-quality leads."
    )


def test_recall_threshold():
    """
    Constraint: recall >= 0.60
    Consequence if violated: Insufficient pipeline for revenue goals
    """
    test_leads = load_test_dataset("recall_test_set.json")
    
    qualified = qualify_leads(test_leads)
    true_positives = sum(1 for l in qualified if l.qualified and l.actual_converted)
    false_negatives = sum(1 for l in qualified if not l.qualified and l.actual_converted)
    
    recall = true_positives / (true_positives + false_negatives)
    
    assert recall >= 0.60, (
        f"Recall {recall:.2f} below minimum 0.60. "
        "Insufficient pipeline for revenue targets."
    )
```

---

### Step 4: Verification (Manual or Automated)

```bash
# Verify intent alignment:

$ python verify_intent.py crm/lead_scoring/

Checking: crm/lead_scoring/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Intent artifact: lead_scoring_intent.yaml (found)

✅ Code alignment:
   QUALIFICATION_THRESHOLD = 0.70 (matches intent)

✅ Constraints verified:
   precision = 0.85 (>= 0.80) ✓
   recall = 0.68 (>= 0.60) ✓

✅ Evidence exists:
   playground/crm/threshold_analysis_2025-12.ipynb ✓
   Last modified: recently

⚠️  Monitoring:
   Precision at 0.85 (healthy)
   Recall at 0.68 (healthy)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTENT VERIFIED ✓
```

---

## What Changes?

### Before IVD

**New engineer asks:** "Why is the threshold 0.70?"

**Answer:** "Um... I think Sarah set it? She left last year. Check git blame maybe?"

### After IVD

**New engineer runs:** `cat lead_scoring_intent.yaml`

**Gets:**
- Goal: Balance quality vs quantity
- Decision: 0.70 threshold
- Evidence: Notebook with analysis
- Alternatives: 0.60 rejected (low precision), 0.80 rejected (low recall)
- Stakeholder: VP Sales approved Dec 2025
- Risks: Alert if precision drops below 0.75

**Onboarding:** 40% faster

---

## When to Use IVD

### DO Create Intent Artifacts For:

✅ Business logic with thresholds or magic numbers  
✅ Decisions that required stakeholder approval  
✅ Logic that's caused production incidents  
✅ Code that confuses new developers  
✅ Algorithms with rejected alternatives  

### DON'T Create Intent Artifacts For:

❌ Simple utility functions  
❌ Self-explanatory CRUD operations  
❌ Temporary or prototype code  
❌ Code where intent is obvious  
❌ **Adding unit tests or test suites** — tests verify existing intent; the intent belongs to the module/function under test, not to "the new tests"

---

## Quick Start Checklist

### Before Writing Code, Ask:

- [ ] **INTENT:** What am I trying to achieve?
- [ ] **CONSTRAINTS:** What must hold true?
- [ ] **RATIONALE:** Why this approach?
- [ ] **ALTERNATIVES:** What else did I consider?
- [ ] **EVIDENCE:** Where's my proof?
- [ ] **RISKS:** What could go wrong?

### If Answers Are Complex:

0. **If you don't understand the domain/concepts:** Use teaching (e.g. `ivd_teach_concept(concept="ETL")`) to get structured explanation with verification; confirm understanding; then continue.
1. **If you don't know what to build:** *(Experimental)* Use discovery (e.g. `ivd_discover_goal`, list recipes) to get 2–3 candidate directions with tradeoffs; choose one, then describe and let AI write intent.
2. Create `{module}_intent.yaml`
3. Fill in the schema
4. Write clean implementation
5. Add tests that verify constraints
6. Link code to intent artifact

---

## The Paradigm in One Sentence

> **Treat understanding like code: make it explicit, version it, test it, and verify it continuously.**

---

## Why `_intent.yaml` Suffix?

IVD uses `{name}_intent.yaml` naming consistently. This section explains why.

### Why Suffix, Not Prefix

| Approach | Example | Issue |
|----------|---------|-------|
| Suffix (current) | `lead_scoring_intent.yaml` | ✅ Sorts near `lead_scoring.py` |
| Prefix | `ivd_scoring.yaml` | ❌ All intents sort together, away from code |

**The suffix maintains IVD Principle 1:** "Intent artifacts live alongside code"

### Why `_intent`, Not `.intent`

| Approach | Example | Issue |
|----------|---------|-------|
| Underscore (current) | `scoring_intent.yaml` | ✅ Standard YAML file |
| Dot notation | `scoring.intent.yaml` | ❌ Confuses tools expecting single extension |

### Discovery Patterns

```bash
# Find all intent artifacts:
find . -name "*_intent.yaml"

# AI agent glob pattern:
**/*_intent.yaml

# Cursor workspace search:
*_intent.yaml
```

### Why NOT Change

- ✅ Pattern is **globally unique** in codebases
- ✅ Works with all AI coding tools (Cursor, Copilot, Claude)
- ✅ Consistent with 60,000+ AGENTS.md projects (simplicity principle)
- ✅ No migration needed for existing artifacts

---

## Summary

| Traditional | Intent-Verified |
|-------------|-----------------|
| Intent mixed in comments | Intent in separate artifact |
| Claims trusted | Claims verified by tests |
| Evidence "somewhere" | Evidence linked and runnable |
| Drifts silently | Drift detected immediately |
| Knowledge lost on turnover | Knowledge survives |
| 10-15% knowledge captured | 85-95% knowledge captured |

**The breakthrough:** Understanding becomes a first-class, verifiable artifact—not just prose that can be wrong.

---

## NEW in v1.2: Workflow-Level Intents

### The Workflow Problem

**Your AI agent asks:** "How does the lead qualification workflow work?"

**Traditional options:**
- ❌ Read all module docs (5-10 files, 2000+ lines)
- ❌ Read all code (10+ files, 3000+ lines)
- ❌ Trace execution manually (hours of work)

**Result:** Expensive. Slow. Context-heavy.

---

### The Workflow Solution

**Create ONE workflow-level intent artifact** that documents:
- Step-by-step sequence
- File/function mapping at each step
- Business logic context
- Data flow between steps
- Error handling strategies

**AI agent reads ONE file, understands everything.**

**Cost reduction: 80-90% less context needed.**

---

### Example: Lead Qualification Workflow

**The process (5 steps):**

```
1. Validate lead (api/endpoints/leads.py::create_lead)
   ↓
2. Enrich data (jobs/enrich_lead_job.py::enrich_lead_task)
   ↓
3. Score lead (agent/lead_qualifier/scoring.py::calculate_lead_score)
   ↓
4. Qualify decision (agent/lead_qualifier/agent.py::qualify_lead)
   ↓
5. Sync to CRM (integrations/salesforce/sync.py::sync_lead_to_crm)
```

---

### Workflow Intent Artifact (Simplified)

```yaml
# workflows/lead_qualification_workflow_intent.yaml
# (Workflow intents can also live alongside the coordinator file when single-orchestrator; see framework.md.)

scope:
  level: "workflow"
  type: "process"

intent:
  summary: "Lead qualification from intake to CRM sync"
  goal: "Process leads through 5 steps to deliver qualified leads to sales"
  success_metric: "98% completion rate, p95 < 3s, 85% precision"

workflow:
  summary: "Validate → Enrich → Score → Qualify → Sync to CRM"
  trigger: "POST /api/v1/leads"
  
  steps:
    - step: 1
      name: "Validate lead data"
      file: "api/endpoints/leads.py"
      function: "create_lead()"
      description: "Validate required fields, normalize, check duplicates"
      input: "POST /api/v1/leads {email, company}"
      output: "Lead ID in database"
      business_logic: "Required fields: email, company. Duplicate check by email+company"
      performance: "p95 < 100ms"
      
    - step: 2
      name: "Enrich with external data"
      file: "jobs/enrich_lead_job.py"
      function: "enrich_lead_task()"
      description: "Call external APIs for company data"
      input: "Lead ID from step 1"
      output: "Enriched lead (company size, industry, revenue)"
      business_logic: "Clearbit + LinkedIn APIs. Fallback to cached data on failure"
      performance: "p95 < 2s"
      depends_on: [1]
      
    - step: 3
      name: "Calculate lead score"
      file: "agent/lead_qualifier/scoring.py"
      function: "calculate_lead_score()"
      description: "ML model predicts conversion probability"
      input: "Enriched lead from step 2"
      output: "Score 0.0-1.0"
      business_logic: "XGBoost model, trained on 10K conversions"
      performance: "p95 < 200ms"
      depends_on: [2]
      
    - step: 4
      name: "Qualify lead decision"
      file: "agent/lead_qualifier/agent.py"
      function: "qualify_lead()"
      description: "Apply threshold and business rules"
      input: "Score from step 3"
      output: "qualified: true/false"
      business_logic: "Threshold >= 0.70 + company size >= 50 employees"
      performance: "p95 < 10ms"
      depends_on: [3]
      
    - step: 5
      name: "Sync to Salesforce"
      file: "integrations/salesforce/sync.py"
      function: "sync_lead_to_crm()"
      description: "Create Salesforce Lead record"
      input: "Qualified lead from step 4"
      output: "Salesforce Lead ID"
      business_logic: "Only qualified leads synced. Map to Salesforce schema"
      performance: "p95 < 500ms"
      depends_on: [4]
      conditional: "Only if qualified=true"
  
  data_flow:
    - "Raw lead → Validated → Enriched → Scored → Qualified → CRM record"
  
  error_handling:
    - step: 2
      failure_mode: "External API unavailable"
      action: "Use cached data or partial enrichment"
      fallback: "Continue with lower enrichment_confidence"
    
    - step: 5
      failure_mode: "Salesforce API error"
      action: "Queue for retry (background job)"
      fallback: "Exponential backoff, 3 attempts"
  
  orchestration:
    type: "sequential"
    coordinator: "workflows/lead_qualification_coordinator.py"
    description: "Steps execute in order. Each step waits for previous step"

constraints:
  - name: "workflow_completion_rate"
    requirement: ">= 98%"
    consequence_if_violated: "Lost leads, sales team doesn't get leads"
  
  - name: "end_to_end_latency"
    requirement: "p95 < 3 seconds"
    consequence_if_violated: "Poor UX, SLA breach"
```

---

### What This Enables

**For AI Agents:**
- ✅ Read ONE file to understand complete workflow
- ✅ Know exactly which files/functions to examine
- ✅ See business logic without diving into code
- ✅ Understand error handling paths
- ✅ 80-90% reduction in context needed

**For Developers:**
- ✅ Onboarding: Understand process in 10 minutes (vs hours)
- ✅ Debugging: Know which step failed immediately
- ✅ Changes: See impact of modifying one step
- ✅ Documentation: Business + technical in one place

**For Stakeholders:**
- ✅ Visibility into technical process
- ✅ Understand what each step does (business terms)
- ✅ See error handling strategies
- ✅ Validate process matches requirements

---

### When to Use Workflow-Level Intents

**Create workflow intent when:**
- ✅ Process has 3+ steps across multiple files
- ✅ AI agents frequently ask "how does this work end-to-end?"
- ✅ Onboarding requires hours to understand flow
- ✅ Business stakeholders need technical process visibility
- ✅ Process has multiple error paths or fallback strategies

**DON'T create workflow intent for:**
- ❌ Simple 2-step processes (use module-level)
- ❌ Single-file implementations (use module-level or task-level)
- ❌ Self-explanatory code flows

---

### Complete Example

**See:** `templates/examples/workflow-lead-qualification-example.yaml` (500+ lines)  
**Recipe:** `recipes/workflow-orchestration.yaml` (comprehensive pattern template)

This complete example includes:
- All 5 steps with detailed specifications
- Per-step error handling
- Performance targets per step
- Data transformations
- Orchestration strategy
- Monitoring metrics
- Complete rationale and alternatives
- Real-world validation results

---

## Extending IVD Framework

**Want to propose a new intent level, section, or recipe pattern?**

### Read the Master Intent First

Before proposing any changes to IVD, read `ivd_system_intent.yaml`:

**What it contains:**
- **7 Core Principles** with detailed sub-principles and validation
- **Extension Rules** for adding levels, sections, recipes
- **4-Level Validation Framework** for all additions
- **6-Step Canonization Process** from proposal to canonical
- **High Bar for Additions** - real-world validation required

**Key requirements for any addition:**
1. ✅ Aligns with all 8 principles
2. ✅ Solves real problem (5+ use cases)
3. ✅ Comprehensive example (500+ lines)
4. ✅ Production validation
5. ✅ Passes all validation levels
6. ✅ No principle violations

**IVD evolves slowly and deliberately** - quality over quantity, proven over experimental.

---

**Next Steps:**

1. Pick one complex module in your codebase
2. Create an intent artifact for it
3. **NEW:** If you have a multi-step workflow, create a workflow-level intent
4. Write tests that verify the constraints
5. See if onboarding gets easier and AI agent context costs drop

**Want to extend IVD?** Read `ivd_system_intent.yaml` first.

---

*"In the AI era, code becomes commodity. Understanding becomes the valuable asset. IVD makes understanding durable."*
