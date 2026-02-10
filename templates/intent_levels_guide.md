# Intent Levels Guide: System vs Workflow vs Module vs Task

**When to use each level of intent granularity**

**Note:** In IVD, the **AI writes** the intent artifact at any of these levels, not the human. The human describes what they want; the AI produces the structured intent.

**Scope:** IVD supports intent artifacts for **any AI-produced artifact**: code, architecture, documentation, research, books, processes, data pipelines—anything AI creates should have its paired intent, its point of origin.

---

## The Four Levels

```
SYSTEM LEVEL      →  Entire system or product
    ↓ (parent_intent)
WORKFLOW LEVEL    →  Multi-step process (NEW in v1.2)
    ↓ (parent_intent)
MODULE LEVEL      →  Feature, agent, component
    ↓ (parent_intent)
TASK LEVEL        →  Function, method, API endpoint
```

**At all levels:** AI writes the intent, AI implements, AI verifies.

**Linking:** Each level can reference its parent via `parent_intent` to establish hierarchy and inherit context.

---

## Quick Decision Tree

```
Ask: What am I documenting?

├─ Entire product/system? → SYSTEM LEVEL
│  Example: "AI-driven development book" (book_system_intent.yaml)
│
├─ Multi-step process (3+ steps across files)? → WORKFLOW LEVEL
│  Example: "Lead qualification workflow" (lead_qualification_workflow_intent.yaml)
│
├─ Feature/agent/component? → MODULE LEVEL
│  Example: "Lead qualifier agent" (lead_qualifier_intent.yaml)
│
├─ Single function/task? → TASK LEVEL
│  Example: "qualify_lead() function" (qualify_lead_intent.yaml)
│
└─ Documentation, research, or other non-code artifact?
   Ask: Is this a standalone deliverable or does it describe code?
   │
   ├─ Standalone deliverable (runbook, spec, guide)? → Create _intent.yaml alongside it
   │  Example: "Incident response runbook" (docs/operations/runbook_intent.yaml)
   │  Use scope.type: "documentation" and the level that fits (usually MODULE)
   │
   └─ Describes code (README, inline docs)? → Reference in the code intent
      No separate intent needed — add to implementation.documentation in the code's intent
```

---

## System-Level Intents

### When to Use
- Documenting entire product/system
- Multi-phase projects with many components
- High-level strategic initiatives
- Cross-team coordination needed

### Characteristics
- Broad scope (entire product/platform)
- Multiple stakeholders
- Phases and milestones
- High-level success metrics
- Strategic constraints

### Example: Book Project
```yaml
scope:
  level: "system"
  type: "product"
  granularity: "coarse"

intent:
  summary: "Create evidence-based AI development book"
  goal: "Complete methodology validated through real projects"
  success_metric: "Published with 50+ 5-star reviews"
  
phases:
  - phase_1: "Foundation Building"
  - phase_2: "Meeting-Driven Validation"
  - phase_3: "Publication"
```

**What to include:**
- ✅ High-level phases
- ✅ Strategic constraints
- ✅ Multi-stakeholder approval
- ✅ Long-term risks
- ❌ Detailed inputs/outputs (not relevant)
- ❌ Function signatures (too granular)
- ❌ Performance targets (not at this level)

---

## Workflow-Level Intents (NEW in v1.2)

### When to Use
- Documenting multi-step process (3+ steps)
- Process spans multiple modules/files
- AI agents need quick workflow understanding
- Onboarding requires process comprehension
- Business stakeholders need technical flow visibility

### Characteristics
- Medium scope (multi-step process spanning multiple modules)
- Sequential or parallel step execution
- Multiple files/functions collaborate
- Clear data flow between steps
- Error handling at each step
- **Critical for AI agents** (understand process without reading all code)

### Example: Lead Qualification Workflow
```yaml
scope:
  level: "workflow"
  type: "process"
  granularity: "coarse"

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
      business_logic: "Check required fields, normalize email, detect duplicates"
      
    - step: 2
      name: "Enrich with external data"
      file: "jobs/enrich_lead_job.py"
      function: "enrich_lead_task()"
      business_logic: "Call Clearbit, LinkedIn APIs for company data"
      
    # ... steps 3, 4, 5
  
  data_flow:
    - "Raw lead → Validated → Enriched → Scored → Qualified → CRM record"
  
  error_handling:
    - step: 2
      failure_mode: "External API unavailable"
      action: "Use cached data or proceed with partial enrichment"
```

**What to include:**
- ✅ Step-by-step sequence
- ✅ File/function mapping per step
- ✅ Business logic at each step
- ✅ Data flow between steps
- ✅ Error handling strategies
- ✅ Orchestration type (sequential/parallel)
- ✅ Performance targets per step
- ❌ Function signatures (task-level concern)
- ❌ Line-by-line logic (implementation detail)

**Why workflow-level matters:**

**The gap workflow-level fills:**

Without workflow-level:
- ❌ Module-level documents components, not how they connect
- ❌ Task-level documents functions, not the sequence
- ❌ AI agent must read 5-10 files to understand process
- ❌ Developer must trace code to understand flow

With workflow-level:
- ✅ Complete process in ONE file
- ✅ Explicit execution order
- ✅ Business context for each step
- ✅ AI agent reads one file, understands everything
- ✅ 80-90% reduction in context needed

**When to create workflow intent:**
- ✅ Process has 3+ steps across multiple files
- ✅ AI agents frequently ask "how does this work end-to-end?"
- ✅ Onboarding requires hours to understand the flow
- ✅ Business stakeholders need visibility into technical process
- ✅ Process has multiple error paths or fallback strategies

**When NOT to create workflow intent:**
- ❌ Simple 2-step process (use module-level)
- ❌ Single-file implementation (use module-level or task-level)
- ❌ Self-explanatory code flow

**Real-world examples:**
- Lead qualification (5 steps: receive → enrich → score → qualify → sync)
- Article generation (7 steps: trigger → plan → research → draft → fact-check → images → publish)
- ETL pipeline (4 steps: extract → transform → validate → load)
- Order processing (6 steps: receive → validate → inventory → payment → fulfillment → notify)

**See:** `templates/examples/workflow-lead-qualification-example.yaml` (complete 500+ line example)  
**Recipe:** `recipes/workflow-orchestration.yaml` (pattern template)

**Data-heavy workflows:** For workflows involving data movement, integration, or transformation (ETL, sync, reporting), consider adding the optional **field_mapping** section. See `recipes/data-field-mapping.yaml`.

---

## Module-Level Intents

### When to Use
- Documenting feature/component/agent
- Self-contained module with clear purpose
- Multiple functions working together
- Team needs to understand module intent

### Characteristics
- Medium scope (single feature/component with clear boundaries)
- Module/feature/agent boundaries
- Business logic decisions
- Architecture choices
- Integration points

### Example: Lead Qualifier Agent
```yaml
scope:
  level: "module"
  type: "agent"
  granularity: "coarse"

intent:
  summary: "Qualify leads for sales team"
  goal: "Filter pipeline to high-probability leads"
  success_metric: "85% precision, 70% recall"

# Module-level concerns:
- Architecture decisions (why this approach)
- Integration with CRM
- Data sources
- Monitoring strategy

# NOT individual function details
```

**What to include:**
- ✅ Module purpose and scope
- ✅ Architecture decisions
- ✅ Integration points
- ✅ Business constraints
- ✅ Overall approach rationale
- ❌ Individual function I/O (too detailed)
- ❌ Function-level edge cases (separate intents)
- ❌ Line-by-line logic (implementation detail)

**Large projects (feature inventory):** For large or multi-team projects, add optional **metadata** (`feature_id`, `category`, `tags`, `status`) so the feature list can be derived and duplicates avoided. See `framework.md` → "Feature Inventory (Large Projects)" for the full schema.

**Data integrations:** For modules that integrate with external APIs or databases (CRM, payment systems, data sync), consider adding the optional **field_mapping** section to document field-level mappings and transformations. See `recipes/data-field-mapping.yaml`.

---

## Task-Level Intents

### When to Use
- Documenting critical functions/methods
- Complex algorithms needing explanation
- API endpoints with contracts
- Functions with tricky edge cases
- Reusable utilities with specific behavior

### Characteristics
- Fine scope (single function/method)
- Single function/task
- Clear inputs/outputs
- Specific behavior contract
- Edge cases matter

### Example: qualify_lead() Function
```yaml
scope:
  level: "task"
  type: "function"
  granularity: "fine"

intent:
  summary: "Qualify single lead based on thresholds"
  goal: "Determine if lead meets qualification criteria"
  success_metric: "Function latency < 10ms p95"

interface:
  signature: "qualify_lead(lead: Lead, config: Config) -> Result"
  
  inputs:
    - name: "lead"
      type: "Lead"
      constraints: ["score in [0.0, 1.0]"]
      example: {id: "123", score: 0.75}
  
  outputs:
    - name: "result"
      type: "QualificationResult"
      structure: {qualified: bool, reason: str}
      example: {qualified: true, reason: "..."}

behavior:
  preconditions: ["lead is valid"]
  postconditions: ["result is never None"]
  invariants: ["function is idempotent"]
```

**What to include:**
- ✅ Function signature
- ✅ Input/output specifications
- ✅ Preconditions/postconditions
- ✅ Edge cases and error handling
- ✅ Performance requirements
- ✅ Type constraints
- ✅ Test cases
- ❌ Module-level architecture (parent intent)
- ❌ System-level strategy (too high-level)

---

## When to Use Task-Level Intents

### ✅ DO Create Task-Level Intents For:

1. **Critical business logic functions**
   - Functions that implement key business rules
   - Functions where bugs have high cost
   - Functions that need stakeholder approval
   
2. **API endpoints**
   - Public APIs with contracts
   - Internal APIs with multiple consumers
   - Endpoints with complex request/response
   
3. **Complex algorithms**
   - Non-obvious logic that needs explanation
   - Algorithms with performance requirements
   - Functions with many edge cases
   
4. **Reusable utilities**
   - Functions used across multiple modules
   - Functions with specific behavior contracts
   - Functions that get copied/modified often

5. **Functions with history of bugs**
   - Functions that have been debugged multiple times
   - Functions with production incidents
   - Functions with subtle edge cases

### ❌ DON'T Create Task-Level Intents For:

1. **Trivial functions**
   - Simple getters/setters
   - Obvious utility functions (e.g., `add(a, b)`)
   - One-line wrappers
   
2. **Private implementation details**
   - Internal helper functions
   - Functions that won't be reused
   - Implementation-only concerns
   
3. **Self-explanatory functions**
   - Functions where name + signature explain everything
   - Standard CRUD operations
   - Boilerplate code

4. **Adding tests or test suites**
   - New unit tests, test files, or test suites that verify existing intent
   - Tests are verification of an existing artifact, not a separate deliverable that needs its own intent
   - Create intent for the *module/function under test*; don't create a separate intent for "the new unit tests"

---

## Hierarchy and Relationships

### Parent-Child Relationship

```
# SYSTEM LEVEL: Book Project
book_system_intent.yaml
└─ Phase 2: "Meeting-Driven Validation"
   └─ Deliverable: "Process 50+ meetings"
       └─ WORKFLOW LEVEL: Meeting extraction workflow
          workflows/meeting_extraction_workflow_intent.yaml
          └─ MODULE LEVEL: Meeting Extraction Agent (step 2 in workflow)
             agent/meeting_extractor/meeting_extractor_intent.yaml
             └─ TASK LEVEL: extract_insights() Function
                agent/meeting_extractor/intents/extract_insights_intent.yaml
```

### Linking Intents with parent_intent

Every non-system intent should declare `parent_intent` to establish hierarchy and enable tools to load project context.

```yaml
# Task-level intent references parent module intent:
# File: agent/meeting_extractor/intents/extract_insights_intent.yaml
parent_intent: "../meeting_extractor_intent.yaml"
scope:
  level: "task"

# Module-level intent references parent workflow intent:
# File: agent/meeting_extractor/meeting_extractor_intent.yaml
parent_intent: "../../workflows/meeting_extraction_workflow_intent.yaml"
scope:
  level: "module"

# Workflow-level intent references parent system intent:
# File: workflows/meeting_extraction_workflow_intent.yaml
parent_intent: "../book_system_intent.yaml"
scope:
  level: "workflow"
```

**Why parent_intent matters:**
- **Hierarchy:** Establishes clear parent-child relationships
- **Context inheritance:** Child intents can reference project context from system intent
- **Navigation:** Tools can traverse from leaf to root
- **Validation:** Future tools can verify hierarchy consistency

**When parent has project_context (system-level):**
- Child intents inherit code_rules, architecture principles
- Child intents reuse tools_scripts, libraries_reuse
- Child intents navigate via key_paths (entrypoints, modules, workflows, docs, tests)

**When parent has project_context (system-level):**
- Child intents inherit code_rules, architecture principles
- Child intents reuse tools_scripts, libraries_reuse
- Child intents navigate via key_paths (entrypoints, modules, workflows, docs, tests)

**In existing projects (brownfield):**
1. Run `ivd init` to create system_intent.yaml with project_context
2. All child intents reference `parent_intent: "../../system_intent.yaml"`
3. AI loads project context when creating/modifying child intents

---

## Examples by Type

### System Level
- ✅ Product development (system_intent.yaml or {project}_system_intent.yaml)
- ✅ Platform migration project
- ✅ Multi-quarter initiative

### Workflow Level (NEW)
- ✅ Lead qualification workflow (workflows/lead_qualification_workflow_intent.yaml)
- ✅ Article generation workflow (workflows/article_generation_workflow_intent.yaml)
- ✅ ETL data pipeline (workflows/etl_pipeline_workflow_intent.yaml)
- ✅ Order processing workflow (workflows/order_processing_workflow_intent.yaml)

### Module Level
- ✅ Lead qualifier agent (agent/lead_qualifier/lead_qualifier_intent.yaml)
- ✅ Fact checker agent (agent/fact_checker/fact_checker_intent.yaml)
- ✅ Background job processor (jobs/processor/processor_intent.yaml)
- ✅ API integration module (integrations/salesforce/salesforce_intent.yaml)

### Task Level
- ✅ qualify_lead() function (agent/lead_qualifier/intents/qualify_lead_intent.yaml)
- ✅ extract_claims() function (agent/fact_checker/intents/extract_claims_intent.yaml)
- ✅ POST /api/leads endpoint (api/endpoints/intents/create_lead_intent.yaml)
- ✅ retry_with_backoff() utility (utils/intents/retry_intent.yaml)

### Documentation (Non-Code Primary Artifacts)
- ✅ Incident response runbook (docs/operations/runbook_incident_response_intent.yaml)
- ✅ Onboarding guide (docs/onboarding/onboarding_guide_intent.yaml)
- ✅ API specification (docs/api/api_spec_intent.yaml)
- ❌ Module README (reference in the module's code intent — not a standalone deliverable)

---

## Practical Guidelines

### Start High, Go Low as Needed

```
1. Start with MODULE-level intent for single component
   ↓
2. If you have 3+ steps across modules, create WORKFLOW-level intent
   ↓
3. If you have critical functions, add TASK-level intents
   ↓
4. If you have multiple workflows/modules, consider SYSTEM-level intent
```

### Don't Over-Document

```
BAD:  Task-level intent for every function (too much overhead)
GOOD: Task-level intent for 10-20% of critical functions

BAD:  Module-level intent with function-level details (wrong level)
GOOD: Module-level intent + separate task-level intents for key functions
```

### When to Use Each Level

**SYSTEM-level:** Multi-team, multi-quarter, strategic initiative

**WORKFLOW-level:** 3+ steps across multiple files, AI needs process understanding

**MODULE-level (DEFAULT):** Single component/feature with clear boundaries

**TASK-level:** Critical functions used across modules, complex I/O contracts, public APIs

**The rule:** Use the **highest level** that captures necessary detail. Don't create intents at every level—only where they add value.

---

## Template Selection

```bash
# System-level project
cp templates/intent.yaml system_intent.yaml
# Edit: scope.level = "system"
# Skip: workflow, interface, behavior sections

# Workflow-level process (NEW)
cp templates/intent.yaml workflows/my_workflow_intent.yaml
# Edit: scope.level = "workflow"
# Include: workflow section (steps, data_flow, error_handling, orchestration)
# Skip: interface, behavior sections (those are for task-level)
# See: templates/examples/workflow-lead-qualification-example.yaml

# Module-level feature
cp templates/intent.yaml agent/my_agent/my_agent_intent.yaml
# Edit: scope.level = "module"
# Include: high-level architecture, integration points
# Skip or minimize: workflow, interface sections

# Task-level function
cp templates/intent.yaml agent/my_agent/intents/my_function_intent.yaml
# Edit: scope.level = "task"
# Include: interface, behavior, test_cases (all task-level sections)
# Skip: workflow section
```

---

## File Naming Convention

```
SYSTEM LEVEL:
  system_intent.yaml
  {project}_system_intent.yaml

WORKFLOW LEVEL (NEW):
  workflows/{workflow_name}_intent.yaml
  workflows/lead_qualification_workflow_intent.yaml
  workflows/article_generation_workflow_intent.yaml
  
  OR (if workflow lives with coordinator):
  {coordinator_dir}/workflow_intent.yaml

MODULE LEVEL:
  {module}_intent.yaml
  lead_qualifier_intent.yaml
  fact_checker_intent.yaml

TASK LEVEL:
  {function}_intent.yaml
  qualify_lead_intent.yaml
  extract_claims_intent.yaml
  
  OR (if many tasks in one module):
  intents/
    ├─ qualify_lead.yaml
    ├─ calculate_score.yaml
    └─ validate_data.yaml
```

**Workflow placement:** Use `workflows/` for discoverability; use coordinator dir when the workflow is single-orchestrator and not referenced independently (see framework.md).

---

## Summary

| Level | Scope | Use For | Key Sections |
|-------|-------|---------|--------------|
| **System** | Product/Platform | Strategic initiatives | Phases, high-level metrics |
| **Workflow** | Multi-step process | Process orchestration (3+ steps) | Steps, data_flow, error_handling, orchestration |
| **Module** | Feature/Agent | Business logic, architecture | Architecture decisions, integration |
| **Task** | Function/API | Critical functions, contracts | Interface, behavior, test cases |

**The Rule:** Use the **highest level** that captures the necessary detail.

**Frequency guide:**
- System-level: 1 per major project/product
- Workflow-level: 1 per multi-step process (3-10 workflows per project)
- Module-level: 1 per feature/agent (10-50 modules per project)
- Task-level: Only critical 10-20% of functions

**Remember:** Intent-Verified Development is about preserving understanding, not creating bureaucracy. Apply intents where they add value, not everywhere.

**NEW in v1.2:** Workflow-level intents solve the "expensive AI agent context" problem by documenting complete processes in one file, reducing context needed by 80-90%.
