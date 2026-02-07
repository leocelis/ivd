# IVD Recipe Specification v1.0

**Purpose:** Define reusable patterns and templates for common development scenarios  
**Part of:** Intent-Verified Development (IVD) v1.1  
**Created:** January 23, 2026

---

## What is an IVD Recipe?

An **IVD Recipe** is a reusable pattern that captures how to solve a common development problem. It's a template that can be applied to many similar implementations.

**Key Difference from Intent Artifacts:**

| Intent Artifact | Recipe |
|----------------|--------|
| Specific to ONE implementation | Reusable across MANY implementations |
| Documents "what we built" | Documents "how to build similar things" |
| Lives next to code | Lives in recipes directory |
| Changes with that module | Changes when pattern improves |
| Example: `lead_scorer_intent.yaml` | Example: `agent-classifier.yaml` |

---

## Recipe YAML Schema

```yaml
# recipe_[pattern_name].yaml

recipe:
  name: "Pattern Name"
  version: "1.0"
  category: "agent_patterns|integration_patterns|data_patterns|infrastructure_patterns"
  created: "2026-01-23"
  author: "Team/Person"
  
  description: |
    Clear explanation of what this pattern solves and when to use it.
    Include the problem domain and typical use cases.
  
  applies_to:
    - "Use case 1"
    - "Use case 2"
    - "Use case 3"
  
  when_to_use:
    - "Condition or scenario where this pattern fits"
    - "Another condition"
  
  when_NOT_to_use:
    - "Scenario where this pattern is inappropriate"
    - "Anti-pattern warning"

# ----------------------------------------------------------------------------
# TEMPLATE SECTIONS (to be filled for specific implementation)
# ----------------------------------------------------------------------------

intent_template:
  summary: "[Domain] [action] for [use case]"
  goal: "[Verb] [object] [purpose] for [stakeholder]"
  success_metric: "[Metric name] >= [target value]"
  stakeholders:
    - "[Role 1]"
    - "[Role 2]"

constraints_template:
  - name: "[constraint_category]_[aspect]"
    requirement: "[metric] [operator] [value]"
    typical_values: "[range or common values]"
    test: "tests/test_[module]_[aspect].py"
    consequence_if_violated: "[Impact description]"

rationale_template:
  decision: "Use [approach/technology]"
  reasoning: |
    [Why this approach is appropriate]
    [Trade-offs accepted]
    [Key considerations]
  evidence: "playground/[domain]_[analysis_name].ipynb"
  stakeholder: "[Role] ([Name])"

alternatives_template:
  - name: "[alternative_approach]"
    typical_rejection_reason: "[Why this is usually rejected]"
    when_it_works: "[Scenarios where it's actually better]"
    
  - name: "[another_alternative]"
    typical_rejection_reason: "[Common reason]"

risks_template:
  - condition: "If [metric] [operator] [threshold]"
    impact: "high|medium|low"
    action: "[What to do]"
    monitor: "[Where to watch]"
    severity: "high|medium|low"

# ----------------------------------------------------------------------------
# IMPLEMENTATION PATTERN
# ----------------------------------------------------------------------------

implementation_pattern:
  directory_structure: |
    [module_path]/
    ├── [main_file].py           # [Purpose]
    ├── [main_file]_intent.yaml  # Intent artifact (uses this recipe)
    ├── [support_file].py        # [Purpose]
    └── tests/
        ├── test_[aspect1].py
        └── test_[aspect2].py
  
  code_structure: |
    [Pseudo-code or structure pattern]
    
  key_files:
    - file: "[filename].py"
      purpose: "[What this file does]"
      key_functions:
        - name: "[function_name]"
          purpose: "[What it does]"
          
  dependencies:
    - "[Common library 1]"
    - "[Common library 2]"

# ----------------------------------------------------------------------------
# VERIFICATION PATTERN
# ----------------------------------------------------------------------------

verification_pattern:
  continuous_checks:
    - check: "[What to verify]"
      frequency: "per_request|hourly|daily|weekly"
      command: "[Executable command or test]"
      threshold: "[Acceptable value]"
      
  milestone_checks:
    - milestone: "[Milestone name]"
      validation: "[What to validate]"
      frequency: "weekly|monthly|quarterly"
      
  monitoring_setup:
    - metric: "[Metric name]"
      dashboard: "[Where to view]"
      alert_threshold: "[When to alert]"

# ----------------------------------------------------------------------------
# EXAMPLES
# ----------------------------------------------------------------------------

examples:
  - name: "[Implementation name]"
    location: "[Path to code]"
    domain: "[Domain/industry]"
    customization: "[How it was customized]"
    outcome: "[Results achieved]"
    link_to_intent: "[Path to intent artifact]"
    
  - name: "[Another example]"
    location: "[Path]"
    domain: "[Domain]"
    customization: "[Customization]"

# ----------------------------------------------------------------------------
# BEST PRACTICES
# ----------------------------------------------------------------------------

best_practices:
  - practice: "[Practice description]"
    why: "[Why this matters]"
    example: "[Concrete example]"

common_pitfalls:
  - pitfall: "[What goes wrong]"
    symptom: "[How you detect it]"
    fix: "[How to resolve]"

# ----------------------------------------------------------------------------
# COST & PERFORMANCE
# ----------------------------------------------------------------------------

typical_costs:
  development_complexity: "[Simple/Medium/Complex]"
  infrastructure_cost: "[Monthly cost range]"
  maintenance_effort: "[Hours/month range]"

typical_performance:
  latency: "[Response time range]"
  throughput: "[Operations per second]"
  accuracy: "[Accuracy range]"

# ----------------------------------------------------------------------------
# REFERENCES
# ----------------------------------------------------------------------------

references:
  documentation:
    - "[Path to related docs]"
    - "[Another doc]"
    
  research:
    - "[Research paper or article]"
    - "[Blog post or tutorial]"
    
  tools:
    - name: "[Tool name]"
      purpose: "[What it helps with]"
      link: "[URL or path]"

# ----------------------------------------------------------------------------
# CHANGELOG
# ----------------------------------------------------------------------------

changelog:
  - version: "1.0"
    date: "2026-01-23"
    change: "[What changed]"
    reason: "[Why it changed]"
    author: "[Who made the change]"
```

---

## Recipe Categories

### **1. Agent Patterns**
Reusable patterns for building AI agents:
- `agent-classifier.yaml` - Classification agents
- `recipe_data_extractor_agent.yaml` - Data extraction agents
- `recipe_workflow_coordinator.yaml` - Workflow orchestration
- `recipe_fact_checker_agent.yaml` - Fact verification agents
- `recipe_content_generator_agent.yaml` - Content creation agents

### **2. Integration Patterns**
Patterns for integrating with external systems:
- `recipe_api_integration.yaml` - REST API integrations
- `recipe_webhook_handler.yaml` - Webhook processing
- `recipe_database_sync.yaml` - Database synchronization
- `recipe_file_processor.yaml` - File processing pipelines

### **3. Data Patterns**
Patterns for data processing:
- `recipe_data_validation_pipeline.yaml` - Data quality validation
- `recipe_etl_workflow.yaml` - Extract, transform, load
- `recipe_data_enrichment.yaml` - Data augmentation
- `recipe_batch_processor.yaml` - Batch processing jobs

### **4. Infrastructure Patterns**
Patterns for infrastructure and operations:
- `infra-monitoring.yaml` - Observability and monitoring
- `infra-error-handling.yaml` - Error handling strategies
- `infra-retry.yaml` - Retry and resilience patterns
- `infra-background-job.yaml` - Background job processing

---

## How to Use Recipes

### **Step 1: Find the Right Recipe**

```bash
# List all recipes
ada recipe list

# Search recipes by category
ada recipe list --category agent_patterns

# Search recipes by keyword
ada recipe search "classifier"
```

### **Step 2: Review the Recipe**

```bash
# View recipe details
cat recipes/agent-classifier.yaml

# Shows:
# - What problem it solves
# - When to use it
# - Template sections
# - Examples
```

### **Step 3: Apply Recipe to Your Implementation**

```bash
# Apply recipe to create intent artifact
ada recipe apply recipe_ai_classifier_agent \
  --module agent/my_classifier \
  --interactive

# This creates:
# agent/my_classifier/my_classifier_intent.yaml
# (pre-filled with recipe template, you fill in specifics)
```

### **Step 4: Fill in Specifics**

The generated intent artifact will have:
- ✅ Structure from recipe (complete)
- 🔲 Placeholders for your specifics (fill these in)
- 📝 Comments explaining what to provide
- 🔗 Link back to recipe

```yaml
# agent/my_classifier/intent.yaml

recipe: "agent-classifier"
recipe_version: "1.0"

# Fill in your specifics below:
intent:
  summary: "Lead scoring classifier for CRM"  # Specific to your use case
  goal: "Qualify leads for sales team"         # Your goal
  success_metric: "15% conversion rate"        # Your metric
  stakeholders: ["VP Sales (Jane)"]            # Your stakeholders
  
# ... rest follows recipe template
```

---

## Creating New Recipes

### **When to Create a Recipe**

Create a recipe when:
- ✅ You've solved the same problem 2-3 times
- ✅ Pattern is generalizable across domains
- ✅ Other teams could benefit from the pattern
- ✅ Onboarding would be faster with this template

**Don't create a recipe for:**
- ❌ One-off unique implementations
- ❌ Domain-specific logic that can't generalize
- ❌ Experimental approaches not yet validated

### **Recipe Creation Process**

```bash
# Start from successful implementation
ada recipe create \
  --from-intent agent/successful_module/module_intent.yaml \
  --name recipe_my_pattern

# This generates:
# 1. Recipe YAML template
# 2. Extracts patterns from your intent
# 3. Generalizes specifics into placeholders
# 4. You review and refine
```

---

## Recipe Evolution

Recipes improve over time as we learn:

```yaml
changelog:
  - version: "1.2"
    date: "2026-02-15"
    change: "Added error handling best practices"
    reason: "Production incidents revealed missing error cases"
    author: "Engineering Team"
    
  - version: "1.1"
    date: "2026-01-30"
    change: "Added performance optimization patterns"
    reason: "Performance issues in 3 implementations"
    author: "Platform Team"
    
  - version: "1.0"
    date: "2026-01-23"
    change: "Initial recipe creation"
    reason: "Pattern used successfully in 4 projects"
    author: "Leo Celis"
```

**Recipe versioning ensures:**
- Old intent artifacts still reference their recipe version
- New implementations get latest best practices
- Evolution is documented and traceable

---

## Recipe Governance

### **Who Can Create Recipes?**
- Any developer who has solved a problem 2-3 times
- Pattern must be reviewed by 2+ team members
- Must include at least one real example

### **Who Maintains Recipes?**
- Original author is default maintainer
- Platform/Architecture team reviews quarterly
- Community contributes improvements

### **Recipe Quality Standards**
- ✅ Clear description and use cases
- ✅ Complete template sections
- ✅ At least one real example
- ✅ Best practices and pitfalls documented
- ✅ Version history maintained

---

## Benefits of Recipes

### **For Developers:**
- 🚀 Faster development (start from proven pattern)
- 📚 Learn patterns quickly
- ✅ Higher quality (recipes include best practices)
- 🎯 Consistency across similar implementations

### **For Teams:**
- 📖 Knowledge sharing (patterns documented)
- 🔄 Consistency (similar problems solved similarly)
- ⚡ Onboarding (new devs learn patterns fast)
- 📈 Quality improvement (recipes evolve with lessons)

### **For Organization:**
- 💰 Reduced development cost (less reinvention)
- 📊 Standardization (predictable patterns)
- 🛡️ Risk reduction (proven patterns)
- 🎓 Institutional knowledge (patterns preserved)

---

## Recipes + Intent Artifacts = Complete IVD

```
RECIPE (reusable pattern)
    ↓
Provides template structure
    ↓
INTENT ARTIFACT (specific implementation)
    ↓
Uses recipe, fills in specifics
    ↓
IMPLEMENTATION (code)
    ↓
Follows pattern from recipe
    ↓
VERIFICATION (tests)
    ↓
Validates constraints from intent
```

**The complete flow:**
1. Find appropriate recipe for your problem
2. Apply recipe to create intent artifact
3. Fill in specifics for your implementation
4. Implement code following recipe pattern
5. Verify implementation matches intent
6. If you improve the pattern, update the recipe

---

## Integration with IVD Tools

```bash
# Recipe management
ada recipe list                          # List all recipes
ada recipe show [recipe_name]            # View recipe
ada recipe apply [recipe] --module [path] # Apply to implementation
ada recipe create --from-intent [path]   # Create new recipe

# Verification includes recipe compliance
ada verify agent/my_module

Checking: agent/my_module/
✅ Intent artifact found: my_module_intent.yaml
✅ Recipe referenced: agent-classifier v1.0
✅ All recipe template sections filled ✓
✅ Implementation follows recipe pattern ✓
⚠️  Recipe has newer version (1.2) - consider upgrading

# Recipe evolution
ada recipe upgrade agent/my_module       # Upgrade to latest recipe version
```

---

## Summary

**Recipes are the "how to build" patterns.**  
**Intent artifacts are the "what we built" documentation.**  
**Together they create reusable, verifiable, maintainable systems.**

The addition of Recipes to IVD v1.1 completes the methodology:
- **Intent artifacts** preserve instance-specific knowledge
- **Recipes** preserve pattern-level knowledge
- **Verification** ensures alignment between pattern and instance
- **Evolution** allows both to improve over time

This is Intent-Verified Development: where understanding is executable, reusable, and durable.
