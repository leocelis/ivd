# IVD Validation Methodology

**How We Measure the Effectiveness of Intent-Verified Development**

**Governed by:** `ivd_system_intent.yaml` (Principle 2: Understanding Must Be Executable)  
**Version:** 1.0  
**Created:** January 24, 2026

---

## Purpose

IVD makes specific claims about efficiency gains, knowledge capture, and reduced misalignment. This document defines **how we measure and validate those claims** using concrete, repeatable experiments.

**Core principle:** If we claim understanding must be executable, then our validation methodology must be executable too.

---

## Claims to Validate

| Claim | Target Metric | Current Status |
|-------|---------------|----------------|
| 85-95% knowledge capture | Measured via comprehension tests | **Unproven** |
| 40% faster onboarding | Time to first correct implementation | **Unproven** |
| 80-90% reduction in AI context needed | Token count comparison | **Unproven** |
| Fewer iterations to alignment | Rework count on identical tasks | **Partially validated** (meta) |
| Knowledge survives turnover | Comprehension accuracy after context reset | **Unproven** |
| Recipes reduce reinvention by 30-50% | Time saved using recipe vs. from scratch | **Unproven** |

**Status:** Most claims are theoretical. We need empirical evidence.

---

## Validation Categories

### 1. Context Efficiency (Token Reduction)

**Claim:** Workflow-level intents reduce AI context consumption by 80-90%

**Test Design:**

```yaml
test_name: "Context Reduction Test"
hypothesis: "AI agent can understand workflow with <20% tokens using IVD intent vs. reading source files"

setup:
  baseline_group:
    method: "Read source files directly"
    files_to_read: ["file1.py", "file2.py", ..., "fileN.py"]
    task: "Understand end-to-end workflow"
    
  ivd_group:
    method: "Read workflow intent artifact"
    files_to_read: ["workflow_intent.yaml"]
    task: "Understand end-to-end workflow"

measurement:
  - metric: "tokens_consumed"
    baseline_source: "Sum of all source file tokens"
    ivd_source: "Workflow intent YAML token count"
    calculation: "token_reduction_percent = (1 - ivd/baseline) * 100"
    
  - metric: "comprehension_accuracy"
    test: "Ask 10 standardized questions about workflow"
    scoring: "Correct answers / Total questions"
    requirement: "IVD accuracy >= baseline accuracy"

success_criteria:
  - "token_reduction_percent >= 80%"
  - "ivd_comprehension_accuracy >= baseline_comprehension_accuracy"

evidence_path: "tests/validation/context_efficiency/"
```

**Implementation:**

```python
# tests/validation/context_efficiency/test_token_reduction.py
import tiktoken
from pathlib import Path

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def test_context_reduction():
    """
    Test: AI reads source files vs. workflow intent.
    Measure: Token count and comprehension accuracy.
    """
    # Baseline: Read all source files
    source_files = [
        "agent/creative/agent.py",
        "agent/creative/lore_image_utils.py",
        "agent/creative/image_generation_utils.py",
        "ada_libs/image/utils.py",
        "ada_libs/image/config.py",
        "rest_api/image.py",
        "job/creative/generate_article_images_job.py",
    ]
    
    baseline_tokens = 0
    for file_path in source_files:
        content = Path(file_path).read_text()
        baseline_tokens += count_tokens(content)
    
    # IVD: Read workflow intent
    intent_content = Path("workflows/image_generation_intent.yaml").read_text()
    ivd_tokens = count_tokens(intent_content)
    
    # Calculate reduction
    reduction_percent = (1 - ivd_tokens / baseline_tokens) * 100
    
    # Comprehension test (10 questions)
    questions = [
        "What triggers the image generation workflow?",
        "Which component validates image prompts?",
        "Where are generated images stored?",
        "What happens if image generation fails?",
        "How does the workflow handle retries?",
        # ... 5 more questions
    ]
    
    baseline_accuracy = ask_questions_with_context(questions, source_files)
    ivd_accuracy = ask_questions_with_context(questions, ["workflows/image_generation_intent.yaml"])
    
    # Assert success criteria
    assert reduction_percent >= 80, f"Token reduction {reduction_percent}% < 80%"
    assert ivd_accuracy >= baseline_accuracy, f"IVD accuracy {ivd_accuracy} < baseline {baseline_accuracy}"
    
    return {
        "baseline_tokens": baseline_tokens,
        "ivd_tokens": ivd_tokens,
        "reduction_percent": reduction_percent,
        "baseline_accuracy": baseline_accuracy,
        "ivd_accuracy": ivd_accuracy,
    }
```

---

### 2. Alignment Accuracy (Iteration Reduction)

**Claim:** Intent artifacts reduce iterations to acceptable output

**Test Design:**

```yaml
test_name: "Alignment Iteration Test"
hypothesis: "AI produces aligned output faster with structured intent vs. prose requirements"

setup:
  task: "Implement a classifier that categorizes support tickets"
  
  baseline_group:
    input: "prose_requirements.txt"
    content: |
      Build a classifier that categorizes support tickets.
      It should be fast and reliable.
      Handle edge cases appropriately.
      
  ivd_group:
    input: "classifier_intent.yaml"
    content: |
      Full intent artifact with:
      - Explicit success criteria
      - Test paths
      - Behavior specifications
      - Example inputs/outputs

measurement:
  - metric: "iterations_to_acceptable"
    method: "Human judge reviews each iteration"
    scoring: "Count revisions needed to reach 'acceptable'"
    
  - metric: "alignment_score"
    method: "Rubric-based evaluation"
    dimensions:
      - "Meets functional requirements"
      - "Handles edge cases"
      - "Performance meets criteria"
      - "Code quality acceptable"
    scoring: "Average score across dimensions (0-10)"

success_criteria:
  - "ivd_iterations < baseline_iterations"
  - "ivd_alignment_score >= baseline_alignment_score"

evidence_path: "tests/validation/alignment_accuracy/"
```

**Implementation:**

```python
# tests/validation/alignment_accuracy/test_iteration_count.py
from dataclasses import dataclass
from typing import List

@dataclass
class IterationResult:
    iteration_num: int
    output_code: str
    alignment_score: float
    acceptable: bool
    feedback: str

def run_alignment_test(input_type: str, input_content: str, task: str) -> List[IterationResult]:
    """
    Simulate AI implementation with iterative feedback.
    Returns list of iterations until acceptable.
    """
    results = []
    iteration = 1
    acceptable = False
    
    while not acceptable and iteration <= 10:
        # AI generates implementation
        output = generate_implementation(input_content, task, iteration)
        
        # Human judge evaluates
        score = evaluate_alignment(output, task)
        acceptable = score >= 8.0
        feedback = get_feedback(output, task)
        
        results.append(IterationResult(
            iteration_num=iteration,
            output_code=output,
            alignment_score=score,
            acceptable=acceptable,
            feedback=feedback,
        ))
        
        if acceptable:
            break
            
        iteration += 1
    
    return results

def test_alignment_accuracy():
    """Compare iterations needed with prose vs. IVD intent."""
    task = "Implement support ticket classifier"
    
    # Baseline: Prose requirements
    prose_input = Path("tests/fixtures/prose_requirements.txt").read_text()
    baseline_results = run_alignment_test("prose", prose_input, task)
    
    # IVD: Structured intent
    intent_input = Path("tests/fixtures/classifier_intent.yaml").read_text()
    ivd_results = run_alignment_test("ivd", intent_input, task)
    
    # Compare
    baseline_iterations = len(baseline_results)
    ivd_iterations = len(ivd_results)
    
    baseline_final_score = baseline_results[-1].alignment_score
    ivd_final_score = ivd_results[-1].alignment_score
    
    assert ivd_iterations < baseline_iterations, \
        f"IVD iterations ({ivd_iterations}) >= baseline ({baseline_iterations})"
    assert ivd_final_score >= baseline_final_score, \
        f"IVD score ({ivd_final_score}) < baseline ({baseline_final_score})"
    
    return {
        "baseline_iterations": baseline_iterations,
        "ivd_iterations": ivd_iterations,
        "iteration_reduction_percent": (1 - ivd_iterations / baseline_iterations) * 100,
        "baseline_final_score": baseline_final_score,
        "ivd_final_score": ivd_final_score,
    }
```

---

### 3. Knowledge Durability (Comprehension After Context Reset)

**Claim:** Intent artifacts preserve understanding through context resets (simulates team turnover)

**Test Design:**

```yaml
test_name: "Knowledge Durability Test"
hypothesis: "AI maintains comprehension of system after context reset when using IVD"

setup:
  system: "Choose complex module with 5+ files"
  
  baseline_group:
    knowledge_source: "Source code only"
    
  ivd_group:
    knowledge_source: "Source code + intent artifacts"

procedure:
  phase_1_learning:
    - "AI reads knowledge source"
    - "AI answers 10 comprehension questions"
    - "Record: learning_accuracy"
    
  phase_2_reset:
    - "Clear AI context (simulate turnover)"
    - "Wait: 24 hours (simulate time passing)"
    
  phase_3_recall:
    - "AI re-reads knowledge source"
    - "AI answers same 10 questions"
    - "Record: recall_accuracy"

measurement:
  - metric: "knowledge_retention_rate"
    calculation: "recall_accuracy / learning_accuracy"
    
  - metric: "re-onboarding_speed"
    measurement: "Time to answer all questions correctly"

success_criteria:
  - "ivd_retention_rate > baseline_retention_rate"
  - "ivd_re_onboarding_speed < baseline_re_onboarding_speed"

evidence_path: "tests/validation/knowledge_durability/"
```

**Implementation:**

```python
# tests/validation/knowledge_durability/test_context_reset.py
import time
from datetime import datetime, timedelta

def test_knowledge_durability():
    """
    Test comprehension preservation across context resets.
    Simulates team turnover by clearing AI context.
    """
    questions = [
        "What is the primary purpose of this module?",
        "What are the key dependencies?",
        "What happens if X fails?",
        # ... 7 more questions
    ]
    
    # Phase 1: Learning (baseline)
    baseline_context = load_source_files(["module1.py", "module2.py", ...])
    baseline_learning_score = test_comprehension(questions, baseline_context)
    
    # Phase 1: Learning (IVD)
    ivd_context = load_source_files(["module1.py", "module2.py", ...]) + \
                  load_intent_artifacts(["module_intent.yaml"])
    ivd_learning_score = test_comprehension(questions, ivd_context)
    
    # Phase 2: Context Reset (simulate 24h + turnover)
    clear_context()
    time.sleep(1)  # Simulate time passing
    
    # Phase 3: Re-onboarding
    start_time = datetime.now()
    
    baseline_context_reload = load_source_files(["module1.py", "module2.py", ...])
    baseline_recall_score = test_comprehension(questions, baseline_context_reload)
    baseline_time = (datetime.now() - start_time).total_seconds()
    
    clear_context()
    start_time = datetime.now()
    
    ivd_context_reload = load_source_files(["module1.py", "module2.py", ...]) + \
                         load_intent_artifacts(["module_intent.yaml"])
    ivd_recall_score = test_comprehension(questions, ivd_context_reload)
    ivd_time = (datetime.now() - start_time).total_seconds()
    
    # Calculate retention rates
    baseline_retention = baseline_recall_score / baseline_learning_score
    ivd_retention = ivd_recall_score / ivd_learning_score
    
    assert ivd_retention > baseline_retention, \
        f"IVD retention ({ivd_retention}) <= baseline ({baseline_retention})"
    assert ivd_time < baseline_time, \
        f"IVD re-onboarding ({ivd_time}s) >= baseline ({baseline_time}s)"
    
    return {
        "baseline_retention_rate": baseline_retention,
        "ivd_retention_rate": ivd_retention,
        "baseline_re_onboarding_seconds": baseline_time,
        "ivd_re_onboarding_seconds": ivd_time,
        "re_onboarding_speedup_percent": (1 - ivd_time / baseline_time) * 100,
    }
```

---

### 4. Recipe Effectiveness (Time Savings)

**Claim:** Recipes reduce reinvention by 30-50%

**Test Design:**

```yaml
test_name: "Recipe Time Savings Test"
hypothesis: "Using recipe reduces implementation time by 30-50%"

setup:
  task: "Implement new background job processor"
  
  baseline_group:
    method: "Implement from scratch"
    guidance: "General requirements only"
    
  ivd_group:
    method: "Apply infra-background-job.yaml recipe"
    guidance: "Recipe + requirements"

measurement:
  - metric: "implementation_time"
    start: "Task assignment"
    end: "Tests passing + code review approved"
    
  - metric: "code_quality_score"
    dimensions:
      - "Follows best practices"
      - "Error handling complete"
      - "Tests comprehensive"
      - "Documentation adequate"
    scoring: "Average score (0-10)"

success_criteria:
  - "ivd_time <= baseline_time * 0.7"  # 30% reduction
  - "ivd_quality_score >= baseline_quality_score"

evidence_path: "tests/validation/recipe_effectiveness/"
```

**Implementation:**

```python
# tests/validation/recipe_effectiveness/test_recipe_speedup.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ImplementationResult:
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    tests_passing: bool
    code_quality_score: float
    lines_of_code: int
    test_coverage_percent: float

def test_recipe_effectiveness():
    """
    Compare implementation time/quality with vs. without recipe.
    """
    task = "Implement article summarization background job"
    
    # Baseline: From scratch
    baseline_result = implement_task(
        task=task,
        recipe=None,
        requirements="tests/fixtures/background_job_requirements.txt"
    )
    
    # IVD: Using recipe
    ivd_result = implement_task(
        task=task,
        recipe="recipes/infra-background-job.yaml",
        requirements="tests/fixtures/background_job_requirements.txt"
    )
    
    # Calculate savings
    time_reduction_percent = (1 - ivd_result.duration_seconds / baseline_result.duration_seconds) * 100
    
    assert time_reduction_percent >= 30, \
        f"Time reduction ({time_reduction_percent}%) < 30%"
    assert ivd_result.code_quality_score >= baseline_result.code_quality_score, \
        f"IVD quality ({ivd_result.code_quality_score}) < baseline ({baseline_result.code_quality_score})"
    
    return {
        "baseline_duration_seconds": baseline_result.duration_seconds,
        "ivd_duration_seconds": ivd_result.duration_seconds,
        "time_reduction_percent": time_reduction_percent,
        "baseline_quality_score": baseline_result.code_quality_score,
        "ivd_quality_score": ivd_result.code_quality_score,
    }
```

---

### 5. Meta-Validation (Self-Application)

**Claim:** IVD framework governed its own evolution

**Evidence:**

This is already validated through documented history:

```yaml
test_name: "Meta-Validation"
hypothesis: "IVD principles successfully governed IVD development"

evidence:
  - artifact: "ivd_system_intent.yaml"
    role: "Master intent for IVD framework evolution"
    
  - violation_caught: "Timeline references"
    count: 19
    document: "ivd_implementation_roadmap.md"
    detection: "Cross-check against no_timeline_references constraint"
    resolution: "All instances removed, replaced with complexity descriptors"
    
  - violation_caught: "Summary document (structural_cleanliness)"
    document: "IVD_RECOMMENDATION_VS_RESEARCH.md"
    detection: "Cross-check against structural_cleanliness constraint"
    resolution: "Content merged into canonical sources, file deleted"
    
  - validation_cycle:
    - "Created master intent (ivd_system_intent.yaml)"
    - "Conducted research (agent_knowledge_standards.md)"
    - "Validated research against master intent"
    - "Created implementation roadmap"
    - "Validated roadmap against master intent"
    - "Caught and fixed violations"
    - "Framework governed itself"

measurement:
  - metric: "violations_detected"
    value: 2  # (timeline references + summary doc)
    
  - metric: "violations_resolved"
    value: 2
    
  - metric: "resolution_rate"
    calculation: "100%"

success_criteria:
  - "resolution_rate == 100%"
  - "No violations remain in final artifacts"

status: "VALIDATED ✓"
evidence_path: "research/ivd_implementation_roadmap.md (revision history)"
```

---

## Validation Tools Required

To execute these tests, we need:

### 1. Token Counter

```python
# ivd/tools/token_counter.py
import tiktoken
from pathlib import Path
from typing import List, Dict

def count_file_tokens(file_path: str, model: str = "gpt-4") -> int:
    """Count tokens in a file."""
    content = Path(file_path).read_text()
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(content))

def count_context_tokens(file_paths: List[str], model: str = "gpt-4") -> Dict:
    """Count total tokens across multiple files."""
    results = {}
    total = 0
    
    for file_path in file_paths:
        tokens = count_file_tokens(file_path, model)
        results[file_path] = tokens
        total += tokens
    
    results["total"] = total
    return results
```

### 2. Comprehension Test Framework

```python
# ivd/tools/comprehension_test.py
from dataclasses import dataclass
from typing import List, Callable

@dataclass
class Question:
    id: str
    text: str
    expected_answer: str
    acceptable_variations: List[str]

@dataclass
class ComprehensionResult:
    question_id: str
    answer_given: str
    correct: bool
    explanation: str

def run_comprehension_test(
    questions: List[Question],
    context_provider: Callable[[str], str],  # Function that returns answer given question
) -> List[ComprehensionResult]:
    """Run comprehension test with given context."""
    results = []
    
    for question in questions:
        answer = context_provider(question.text)
        correct = is_answer_correct(answer, question.expected_answer, question.acceptable_variations)
        
        results.append(ComprehensionResult(
            question_id=question.id,
            answer_given=answer,
            correct=correct,
            explanation=f"Expected: {question.expected_answer}, Got: {answer}",
        ))
    
    return results

def calculate_accuracy(results: List[ComprehensionResult]) -> float:
    """Calculate accuracy percentage."""
    correct_count = sum(1 for r in results if r.correct)
    return (correct_count / len(results)) * 100
```

### 3. Alignment Evaluator

```python
# ivd/tools/alignment_evaluator.py
from dataclasses import dataclass
from typing import List

@dataclass
class AlignmentCriteria:
    dimension: str
    weight: float
    description: str
    evaluation_function: callable

@dataclass
class AlignmentScore:
    dimension: str
    score: float  # 0-10
    explanation: str

def evaluate_alignment(
    output: str,
    criteria: List[AlignmentCriteria],
) -> tuple[float, List[AlignmentScore]]:
    """
    Evaluate output against alignment criteria.
    Returns: (weighted_average_score, detailed_scores)
    """
    scores = []
    total_weight = sum(c.weight for c in criteria)
    weighted_sum = 0
    
    for criterion in criteria:
        score = criterion.evaluation_function(output)
        scores.append(AlignmentScore(
            dimension=criterion.dimension,
            score=score,
            explanation=f"{criterion.description}: {score}/10",
        ))
        weighted_sum += score * criterion.weight
    
    average_score = weighted_sum / total_weight
    return average_score, scores
```

### 4. Test Result Aggregator

```python
# ivd/tools/result_aggregator.py
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class ValidationResultAggregator:
    """Aggregate and report validation test results."""
    
    def __init__(self, output_dir: str = "tests/validation/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_result(self, test_name: str, results: Dict):
        """Save test results to JSON."""
        timestamp = datetime.now().isoformat()
        filename = f"{test_name}_{timestamp}.json"
        
        output = {
            "test_name": test_name,
            "timestamp": timestamp,
            "results": results,
        }
        
        (self.output_dir / filename).write_text(json.dumps(output, indent=2))
    
    def generate_report(self, test_results: List[Dict]) -> str:
        """Generate markdown report from test results."""
        report = ["# IVD Validation Report\n"]
        report.append(f"**Generated:** {datetime.now().isoformat()}\n\n")
        
        for result in test_results:
            report.append(f"## {result['test_name']}\n")
            report.append(f"**Status:** {'✓ PASSED' if result['passed'] else '✗ FAILED'}\n\n")
            
            for metric, value in result['metrics'].items():
                report.append(f"- **{metric}:** {value}\n")
            
            report.append("\n")
        
        return "".join(report)
```

---

## Running Validation Suite

### Test Suite Structure

```
tests/validation/
├── context_efficiency/
│   ├── test_token_reduction.py
│   ├── fixtures/
│   │   ├── workflow_intent.yaml
│   │   └── source_files/
│   └── results/
│
├── alignment_accuracy/
│   ├── test_iteration_count.py
│   ├── fixtures/
│   │   ├── prose_requirements.txt
│   │   └── classifier_intent.yaml
│   └── results/
│
├── knowledge_durability/
│   ├── test_context_reset.py
│   ├── fixtures/
│   └── results/
│
├── recipe_effectiveness/
│   ├── test_recipe_speedup.py
│   ├── fixtures/
│   └── results/
│
└── meta_validation/
    ├── test_self_governance.py
    └── results/
```

### Running Tests

```bash
# Run all validation tests
python -m pytest tests/validation/ -v --tb=short

# Run specific validation category
python -m pytest tests/validation/context_efficiency/ -v

# Generate validation report
python ivd/tools/generate_validation_report.py \
    --results tests/validation/*/results/*.json \
    --output validation_report.md
```

### CI Integration

```yaml
# .github/workflows/ivd-validation.yml
name: IVD Validation

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pytest tiktoken pyyaml
      
      - name: Run validation suite
        run: |
          pytest tests/validation/ -v --junitxml=validation-results.xml
      
      - name: Generate report
        run: |
          python ivd/tools/generate_validation_report.py \
            --results "tests/validation/*/results/*.json" \
            --output validation_report.md
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: validation-results
          path: |
            validation-results.xml
            validation_report.md
```

---

## Metrics Dashboard

### What to Track Over Time

```yaml
metrics:
  context_efficiency:
    - metric: "token_reduction_percent"
      target: ">= 80%"
      trend: "Higher is better"
      
    - metric: "comprehension_accuracy_ratio"
      target: ">= 1.0"  # IVD accuracy >= baseline
      trend: "Higher is better"
  
  alignment_accuracy:
    - metric: "iteration_reduction_percent"
      target: ">= 30%"
      trend: "Higher is better"
      
    - metric: "alignment_score"
      target: ">= 8.0"
      trend: "Higher is better"
  
  knowledge_durability:
    - metric: "retention_rate"
      target: ">= 0.9"  # 90% retention
      trend: "Higher is better"
      
    - metric: "re_onboarding_speedup_percent"
      target: ">= 40%"
      trend: "Higher is better"
  
  recipe_effectiveness:
    - metric: "time_reduction_percent"
      target: ">= 30%"
      trend: "Higher is better"
      
    - metric: "quality_score"
      target: ">= 8.0"
      trend: "Higher is better"
```

### Visualization

```python
# ivd/tools/metrics_dashboard.py
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

def generate_dashboard(results_dir: str):
    """Generate metrics dashboard from validation results."""
    
    # Load all results
    results = load_all_results(results_dir)
    df = pd.DataFrame(results)
    
    # Create dashboard
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Context Efficiency
    axes[0, 0].plot(df['date'], df['token_reduction_percent'])
    axes[0, 0].axhline(y=80, color='r', linestyle='--', label='Target: 80%')
    axes[0, 0].set_title('Context Efficiency (Token Reduction)')
    axes[0, 0].set_ylabel('Reduction %')
    axes[0, 0].legend()
    
    # Alignment Accuracy
    axes[0, 1].plot(df['date'], df['iteration_reduction_percent'])
    axes[0, 1].axhline(y=30, color='r', linestyle='--', label='Target: 30%')
    axes[0, 1].set_title('Alignment Accuracy (Iteration Reduction)')
    axes[0, 1].set_ylabel('Reduction %')
    axes[0, 1].legend()
    
    # Knowledge Durability
    axes[1, 0].plot(df['date'], df['retention_rate'])
    axes[1, 0].axhline(y=0.9, color='r', linestyle='--', label='Target: 90%')
    axes[1, 0].set_title('Knowledge Durability (Retention Rate)')
    axes[1, 0].set_ylabel('Retention Rate')
    axes[1, 0].legend()
    
    # Recipe Effectiveness
    axes[1, 1].plot(df['date'], df['time_reduction_percent'])
    axes[1, 1].axhline(y=30, color='r', linestyle='--', label='Target: 30%')
    axes[1, 1].set_title('Recipe Effectiveness (Time Savings)')
    axes[1, 1].set_ylabel('Time Reduction %')
    axes[1, 1].legend()
    
    plt.tight_layout()
    plt.savefig('ivd_validation_dashboard.png')
```

---

## First Validation Experiment

### Immediate Test: Context Efficiency on ADA

**Subject:** Image generation workflow in ADA

**Files involved:**
- `agent/creative/agent.py`
- `agent/creative/lore_image_utils.py`
- `agent/creative/image_generation_utils.py`
- `ada_libs/image/utils.py`
- `ada_libs/image/config.py`
- `rest_api/image.py`
- `job/creative/generate_article_images_job.py`

**Test procedure:**

1. **Baseline:** Count tokens in all 7 files
2. **Create:** Workflow-level intent for image generation
3. **IVD:** Count tokens in workflow intent
4. **Compare:** Calculate reduction percentage
5. **Comprehension:** Test AI understanding with 10 questions (both ways)
6. **Validate:** Reduction >= 80%, accuracy >= baseline

**Expected results:**
- Baseline: ~15,000-20,000 tokens (7 files × 400-600 lines × ~2 tokens/line)
- IVD: ~1,500-2,500 tokens (workflow intent YAML)
- Reduction: 85-90%

**Evidence location:** `tests/validation/context_efficiency/results/image_generation_test_<timestamp>.json`

---

## Validation Schedule

### Phase 1: Foundation (Immediate)
- **Meta-validation:** Document existing evidence ✓ (completed)
- **Context efficiency:** Run first test on ADA image generation
- **Build validation tools:** Token counter, comprehension tester

### Phase 2: Core Metrics (Next)
- **Alignment accuracy:** Controlled iteration test
- **Knowledge durability:** Context reset experiment
- **Baseline establishment:** Run tests, record initial metrics

### Phase 3: Continuous Validation (Ongoing)
- **Weekly:** Re-run validation suite
- **Per-release:** Validation report required
- **Quarterly:** Comprehensive validation review

---

## Success Criteria

### Minimum Viable Validation

For IVD claims to be considered **validated**, we need:

1. **Context Efficiency:** >= 3 tests showing >= 80% token reduction
2. **Alignment Accuracy:** >= 2 tests showing >= 30% iteration reduction
3. **Knowledge Durability:** >= 2 tests showing >= 90% retention rate
4. **Recipe Effectiveness:** >= 2 tests showing >= 30% time savings
5. **Meta-validation:** Documented evidence of self-governance ✓

**Current status:**
- Meta-validation: ✓ COMPLETE
- All others: PENDING (tools and tests required)

---

## Integration with IVD Framework

### Principle Alignment

This validation methodology aligns with:

**Principle 2: Understanding Must Be Executable**
- Validation tests are executable code
- Claims are measurable through concrete tests
- Success criteria are programmatically verifiable

**Principle 4: Continuous Verification**
- Validation suite runs on CI
- Metrics tracked over time
- Drift detectable through trend analysis

### Master Intent Reference

This document is governed by `ivd_system_intent.yaml`:

```yaml
# From ivd_system_intent.yaml
constraints:
  no_timeline_references:
    test: "grep -i 'days|weeks|months|timeline' returns nothing"
    status: "✓ COMPLIANT"
    
  structural_cleanliness:
    test: "No summary or temporary documents"
    status: "✓ COMPLIANT (this is a canonical validation methodology)"
```

---

## Conclusion

**What we have:** Theoretical claims and meta-validation  
**What we need:** Empirical evidence from repeatable tests  
**How we get it:** Execute validation suite using tools defined here

**Next step:** Run first context efficiency test on ADA image generation workflow

**Evidence will be stored in:** `tests/validation/*/results/*.json`

---

## References

- **Master Intent:** `ivd_system_intent.yaml`
- **Purpose:** `purpose.md`
- **Implementation:** `ivd_implementation_roadmap.md`
- **Research:** `agent_knowledge_standards.md`

---

*"If understanding must be executable, validation must be executable too."*
