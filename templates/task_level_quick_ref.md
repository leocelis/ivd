# Task-Level Intent: Quick Reference

**Essential sections for documenting functions with IVD**

---

## Minimal Task-Level Intent

```yaml
scope:
  level: "task"
  type: "function"

intent:
  summary: "What this function does in one line"
  goal: "Why this function exists"

interface:
  signature: "function_name(param: Type) -> ReturnType"
  
  inputs:
    - name: "param"
      type: "Type"
      description: "What this parameter means"
      required: true
      example: "example_value"
  
  outputs:
    - name: "result"
      type: "ReturnType"
      description: "What gets returned"
      example: "example_result"

constraints:
  - name: "key_requirement"
    requirement: "What must be true"
    test: "path/to/test.py::test_name"

implementation:
  current: "path/to/file.py"
  function: "function_name"
```

---

## Full Task-Level Intent Schema

### 1. SCOPE (Required)
```yaml
scope:
  level: "task"              # Always "task" for functions
  type: "function"           # "function" | "method" | "api" | "endpoint"
  granularity: "fine"        # Always "fine" for task-level
```

### 2. INTENT (Required)
```yaml
intent:
  summary: "One-line description"
  goal: "Detailed explanation of purpose"
  success_metric: "How to measure success"
  stakeholders: ["Who cares"]
```

### 3. INTERFACE (Required for tasks)
```yaml
interface:
  signature: "function(param: Type) -> Return"
  
  inputs:
    - name: "param_name"
      type: "str | int | dict | CustomType"
      description: "What this input represents"
      required: true  # or false
      default: "default_value"  # if not required
      constraints:
        - "validation rule 1"
        - "validation rule 2"
      example: "example_value"
      validation: "How input is validated"
  
  outputs:
    - name: "return_value"
      type: "ReturnType"
      description: "What gets returned"
      structure: "Expected structure"
      constraints:
        - "constraint 1"
      example: "example_output"
    
    - name: "side_effects"
      effects:
        - "Database write"
        - "API call"
  
  exceptions:
    - exception: "ValueError"
      when: "Input validation fails"
      handling: "Raise with message"
  
  dependencies:
    - dependency: "external_service"
      type: "API"
      required: true
      fallback: "Cache or error"
```

### 4. BEHAVIOR (Recommended for tasks)
```yaml
behavior:
  preconditions:
    - "What must be true before calling"
  
  postconditions:
    - "What must be true after calling"
  
  invariants:
    - "What must always be true"
  
  performance:
    - metric: "latency"
      target: "p95 < 200ms"
      critical_threshold: "p95 > 500ms"
```

### 5. CONSTRAINTS (Required)
```yaml
constraints:
  - name: "constraint_id"
    requirement: "What must hold"
    test: "path/to/test"
    consequence_if_violated: "What breaks"
```

### 6. RATIONALE (Required)
```yaml
rationale:
  decision: "Key decision made"
  reasoning: "Why this approach"
  evidence: "Link to validation"
  date: "YYYY-MM-DD"
```

### 7. VERIFICATION (Recommended for tasks)
```yaml
verification:
  test_cases:
    - name: "test_name"
      input: {...}
      expected_output: {...}
      validates_constraint: "constraint_name"
  
  property_tests:
    - property: "idempotency"
      test: "Same input = same output"
```

---

## When to Include Each Section

| Section | Module-Level | Task-Level |
|---------|--------------|------------|
| **scope** | ✅ Required | ✅ Required |
| **intent** | ✅ Required | ✅ Required |
| **interface** | ⚠️ Optional | ✅ Required |
| **behavior** | ❌ Skip | ✅ Recommended |
| **constraints** | ✅ Required | ✅ Required |
| **rationale** | ✅ Required | ✅ Required |
| **alternatives** | ✅ Required | ✅ Required |
| **risks** | ✅ Required | ✅ Required |
| **implementation** | ✅ Required | ✅ Required |
| **verification** | ⚠️ Optional | ✅ Recommended |
| **changelog** | ✅ Required | ✅ Required |

---

## Common Patterns

### Pattern 1: Pure Function
```yaml
interface:
  inputs: [...]
  outputs: [...]
  
behavior:
  invariants:
    - "Pure function (no side effects)"
    - "Deterministic (same input = same output)"
    - "Thread-safe"
```

### Pattern 2: Function with Side Effects
```yaml
interface:
  inputs: [...]
  outputs:
    - name: "result"
      type: "dict"
    - name: "side_effects"
      effects:
        - "Updates database: users table"
        - "Sends email via SendGrid"
```

### Pattern 3: API Endpoint
```yaml
scope:
  type: "api"

interface:
  signature: "POST /api/v1/leads"
  
  inputs:
    - name: "request_body"
      type: "LeadCreateRequest"
      validation: "Pydantic model validation"
  
  outputs:
    - name: "response"
      type: "LeadCreateResponse"
      structure: "HTTP 201 on success, 400 on validation error"
```

### Pattern 4: Async Function
```yaml
interface:
  signature: "async def process(data: Data) -> Result"
  
behavior:
  invariants:
    - "Non-blocking (async/await)"
    - "Can be cancelled"
  
  performance:
    - metric: "concurrency"
      target: "100 concurrent requests"
```

---

## Examples by Function Type

### Data Validation Function
```yaml
scope: {level: "task", type: "function"}
interface:
  inputs:
    - name: "data"
      type: "dict"
      validation: "JSON schema validation"
  outputs:
    - name: "validation_result"
      type: "ValidationResult"
      structure: "{valid: bool, errors: list}"
behavior:
  invariants:
    - "Never modifies input data"
    - "Always returns result (never None)"
```

### API Client Method
```yaml
scope: {level: "task", type: "method"}
interface:
  inputs:
    - name: "endpoint"
      type: "str"
      constraints: ["Valid URL format"]
  outputs:
    - name: "response"
      type: "APIResponse"
  exceptions:
    - exception: "APIError"
      when: "HTTP 5xx or network error"
      handling: "Retry 3 times with exponential backoff"
  dependencies:
    - dependency: "external_api"
      required: true
      fallback: "Raise exception"
```

### Database Query Function
```yaml
scope: {level: "task", type: "function"}
interface:
  outputs:
    - name: "side_effects"
      effects:
        - "Reads from database: leads table"
        - "No writes (read-only)"
behavior:
  preconditions:
    - "Database connection is active"
  performance:
    - metric: "query_time"
      target: "p95 < 100ms"
```

---

## Checklist for Task-Level Intent

Before committing, verify:

- [ ] **Scope** set to `level: "task"`
- [ ] **Interface** section complete:
  - [ ] Signature documented
  - [ ] All inputs listed with types and examples
  - [ ] All outputs listed with types and examples
  - [ ] Exceptions documented
- [ ] **Behavior** section includes:
  - [ ] Preconditions (what must be true before)
  - [ ] Postconditions (what must be true after)
  - [ ] Invariants (what's always true)
  - [ ] Performance targets (if relevant)
- [ ] **Constraints** link to actual tests
- [ ] **Verification** includes test cases:
  - [ ] Happy path
  - [ ] Edge cases
  - [ ] Error handling
- [ ] **Example values** are realistic and valid
- [ ] **Rationale** explains WHY this approach

---

## Quick Start

```bash
# 1. Copy template
cp templates/intent.yaml my_function_intent.yaml

# 2. Set scope
sed -i 's/level: "module"/level: "task"/' my_function_intent.yaml
sed -i 's/type: "feature"/type: "function"/' my_function_intent.yaml

# 3. Fill in interface section (the key difference!)
# 4. Add behavior section
# 5. Add test cases

# See full example:
cat templates/examples/task-level-intent-example.yaml
```

---

## Remember

**Task-level intents are for the CRITICAL 10-20% of functions:**
- ✅ Complex algorithms
- ✅ API endpoints with contracts
- ✅ Functions with history of bugs
- ✅ Reusable utilities
- ✅ Critical business logic

**NOT for every function:**
- ❌ Simple getters/setters
- ❌ Obvious utilities
- ❌ Private helpers

**See full guide:** `templates/intent_levels_guide.md`
