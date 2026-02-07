# IVD Framework: Implementation Roadmap

**Purpose:** Building blocks for universal agent knowledge sharing  
**Architecture:** Each block builds on previous blocks toward the ideal implementation  
**Approach:** Foundation-first, composable components

---

## Target Architecture

The ideal IVD agent knowledge sharing system:

```
┌─────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                        │
│  AI-editable config • Self-improvement • Community recipes  │
├─────────────────────────────────────────────────────────────┤
│                     PROTOCOL LAYER                           │
│         MCP Server • Universal Access • Cross-Platform       │
├─────────────────────────────────────────────────────────────┤
│                   CONFIGURATION LAYER                        │
│      Modular .ivd/ • Selective Loading • Migration Path      │
├─────────────────────────────────────────────────────────────┤
│                      TOOLING LAYER                           │
│          CLI • Pre-commit Hooks • CI/CD Integration          │
├─────────────────────────────────────────────────────────────┤
│                    FOUNDATION LAYER                          │
│         JSON Schema • Validation • Structure Definition      │
└─────────────────────────────────────────────────────────────┘
```

Each layer depends on the layers below it. Build from foundation up.

---

## Building Block 1: Foundation Layer

**Purpose:** Define the canonical structure for IVD artifacts  
**Enables:** Everything else (tooling, protocol, intelligence)

### 1.1 JSON Schema Definition

The schema is the source of truth. All other blocks reference it.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "IVD Intent Artifact",
  "type": "object",
  "required": ["scope", "intent", "verification"],
  "properties": {
    "scope": {
      "type": "object",
      "required": ["level", "type", "granularity"],
      "properties": {
        "level": {"enum": ["task", "workflow", "module", "system"]},
        "type": {"enum": ["feature", "pattern", "infrastructure", "process"]},
        "granularity": {"enum": ["fine", "medium", "coarse"]}
      }
    },
    "intent": {
      "type": "object",
      "required": ["summary", "goal", "success_metric"],
      "properties": {
        "summary": {"type": "string", "minLength": 10},
        "goal": {"type": "string", "minLength": 20},
        "success_metric": {"type": "string", "minLength": 10},
        "stakeholders": {"type": "array", "items": {"type": "string"}}
      }
    },
    "verification": {
      "type": "object",
      "required": ["conditions", "evidence"],
      "properties": {
        "conditions": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "evidence": {"type": "array", "items": {"type": "string"}, "minItems": 1}
      }
    },
    "constraints": {"type": "array", "items": {"type": "object"}},
    "rationale": {"type": "object"},
    "alternatives": {"type": "array"},
    "risks": {"type": "array"}
  }
}
```

**Files to Create:**
- `schemas/intent-schema.json` - Intent artifact schema
- `schemas/recipe-schema.json` - Recipe schema
- `schemas/workflow-schema.json` - Workflow-level schema

### 1.2 Core Validation Library

Reusable validation logic used by all other blocks.

```python
# ivd/core/validator.py
"""Core validation library - used by CLI, hooks, MCP server, etc."""

import json
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import jsonschema

@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]
    artifact_type: str
    schema_version: str

class IVDValidator:
    """Central validator for all IVD artifacts."""
    
    def __init__(self, schema_dir: Path = None):
        self.schema_dir = schema_dir or Path(__file__).parent / "schemas"
        self._schemas = {}
    
    def _load_schema(self, artifact_type: str) -> dict:
        """Load and cache schema for artifact type."""
        if artifact_type not in self._schemas:
            schema_path = self.schema_dir / f"{artifact_type}-schema.json"
            with open(schema_path) as f:
                self._schemas[artifact_type] = json.load(f)
        return self._schemas[artifact_type]
    
    def validate(self, artifact: dict, artifact_type: str = "intent") -> ValidationResult:
        """Validate artifact against schema."""
        schema = self._load_schema(artifact_type)
        errors = []
        warnings = []
        
        try:
            jsonschema.validate(instance=artifact, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append(f"{e.message} at {' -> '.join(str(p) for p in e.path)}")
        
        # Additional IVD-specific checks
        warnings.extend(self._check_principle_alignment(artifact))
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            artifact_type=artifact_type,
            schema_version=schema.get("version", "1.0")
        )
    
    def validate_file(self, file_path: Path, artifact_type: str = "intent") -> ValidationResult:
        """Validate YAML file."""
        with open(file_path) as f:
            artifact = yaml.safe_load(f)
        return self.validate(artifact, artifact_type)
    
    def _check_principle_alignment(self, artifact: dict) -> List[str]:
        """Check for IVD principle alignment issues."""
        warnings = []
        
        # Principle 2: Understanding Must Be Executable
        verification = artifact.get("verification", {})
        if not verification.get("conditions"):
            warnings.append("Missing verification conditions (Principle 2)")
        if not verification.get("evidence"):
            warnings.append("Missing verification evidence (Principle 2)")
        
        # Principle 1: Intent is Primary
        intent = artifact.get("intent", {})
        if len(intent.get("goal", "")) < 20:
            warnings.append("Goal should be more detailed (Principle 1)")
        
        return warnings

# Singleton instance
_validator = None

def get_validator() -> IVDValidator:
    """Get singleton validator instance."""
    global _validator
    if _validator is None:
        _validator = IVDValidator()
    return _validator
```

### 1.3 File Structure

```
ivd/
├── core/
│   ├── __init__.py
│   ├── validator.py      # Core validation logic
│   └── schemas/
│       ├── intent-schema.json
│       ├── recipe-schema.json
│       └── workflow-schema.json
├── cli/                   # Building Block 2
├── config/                # Building Block 3
├── mcp/                   # Building Block 4
└── intelligence/          # Building Block 5
```

**Verification:**
- All schemas pass JSON Schema meta-validation
- Validation library handles all artifact types
- Unit tests cover all validation paths

**Dependencies:** None (this is the foundation)

### 1.4 Validation Methodology

**Reference:** `research/validation_methodology.md` (IVD-canon document)

The validation methodology defines **how we measure IVD's effectiveness**.

**Key validation categories:**

1. **Context Efficiency** - Measure token reduction (claim: 80-90%)
2. **Alignment Accuracy** - Measure iteration reduction (claim: 30-50%)
3. **Knowledge Durability** - Measure retention after context reset (claim: 90%+)
4. **Recipe Effectiveness** - Measure time savings (claim: 30-50%)
5. **Meta-Validation** - Document self-governance (✓ validated)

**Validation tools required:**

```python
# ivd/core/validation_tools.py
"""Tools for measuring IVD effectiveness."""

import tiktoken
from pathlib import Path
from typing import List, Dict

def count_context_tokens(file_paths: List[str], model: str = "gpt-4") -> Dict:
    """Count total tokens across multiple files."""
    encoding = tiktoken.encoding_for_model(model)
    results = {"files": {}, "total": 0}
    
    for file_path in file_paths:
        content = Path(file_path).read_text()
        tokens = len(encoding.encode(content))
        results["files"][file_path] = tokens
        results["total"] += tokens
    
    return results

def calculate_reduction(baseline_tokens: int, ivd_tokens: int) -> float:
    """Calculate percentage reduction."""
    return (1 - ivd_tokens / baseline_tokens) * 100
```

**Test structure:**

```
tests/validation/
├── context_efficiency/       # Token reduction tests
├── alignment_accuracy/       # Iteration count tests
├── knowledge_durability/     # Context reset tests
├── recipe_effectiveness/     # Time savings tests
└── meta_validation/          # Self-governance evidence
```

**Integration with Foundation:**
- Validation methodology uses core validator
- Success metrics reference JSON Schema validation
- Test paths prove Principle 2 (Understanding Must Be Executable)

**Why it's in Foundation:**
- Defines canonical approach to measuring IVD value
- All other blocks reference it for their own validation
- Proof methodology must exist before building tools

**See:** `research/validation_methodology.md` for complete test designs and code examples

---

## Building Block 2: Tooling Layer

**Purpose:** Developer-facing tools for working with IVD artifacts  
**Depends On:** Foundation Layer (schemas, validator)  
**Enables:** Protocol Layer (MCP server uses same tools)

### 2.1 CLI Tool

The CLI wraps the core validator and adds developer conveniences.

```python
# ivd/cli/main.py
"""IVD CLI - developer interface to IVD tooling."""

import click
from pathlib import Path
from ..core.validator import get_validator, ValidationResult

@click.group()
@click.version_option()
def cli():
    """IVD Framework CLI Tool"""
    pass

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--type', '-t', default='intent', 
              type=click.Choice(['intent', 'recipe', 'workflow']),
              help='Artifact type to validate')
@click.option('--strict', is_flag=True, help='Treat warnings as errors')
def validate(file_path: str, type: str, strict: bool):
    """Validate an IVD artifact."""
    validator = get_validator()
    result = validator.validate_file(Path(file_path), type)
    
    if result.valid and not (strict and result.warnings):
        click.echo(f"✅ {file_path} is valid")
        for warning in result.warnings:
            click.echo(f"   ⚠️  {warning}")
        return
    
    click.echo(f"❌ Validation failed for {file_path}")
    for error in result.errors:
        click.echo(f"   ✗ {error}")
    for warning in result.warnings:
        click.echo(f"   ⚠️  {warning}")
    raise SystemExit(1)

@cli.command()
@click.option('--level', '-l', required=True,
              type=click.Choice(['task', 'workflow', 'module', 'system']))
@click.option('--type', '-t', required=True,
              type=click.Choice(['feature', 'pattern', 'infrastructure', 'process']))
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def generate(level: str, type: str, output: str):
    """Generate an IVD artifact template."""
    from ..core.templates import generate_template
    
    template = generate_template(level, type)
    
    if output:
        Path(output).write_text(template)
        click.echo(f"✅ Generated {output}")
    else:
        click.echo(template)

@cli.command()
@click.argument('query')
@click.option('--path', '-p', type=click.Path(exists=True), 
              help='Path to search in')
def search(query: str, path: str):
    """Search IVD documentation and artifacts."""
    from ..core.search import search_ivd
    
    results = search_ivd(query, Path(path) if path else None)
    
    if not results:
        click.echo(f"No results found for: {query}")
        return
    
    for result in results:
        click.echo(f"📄 {result.file}:{result.line}")
        click.echo(f"   {result.context}")

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--principle', '-p', type=int, help='Check specific principle (1-7)')
def check(file_path: str, principle: int):
    """Check principle alignment for an artifact."""
    from ..core.principles import check_alignment
    
    result = check_alignment(Path(file_path), principle)
    
    click.echo(f"Principle Alignment: {file_path}")
    for p_num, status in result.items():
        icon = "✅" if status.aligned else "❌"
        click.echo(f"  {icon} Principle {p_num}: {status.message}")

if __name__ == '__main__':
    cli()
```

### 2.2 Pre-Commit Hook

Uses the same validator as CLI.

```bash
#!/bin/bash
# .git/hooks/pre-commit
# IVD artifact validation hook

# Find modified intent files
INTENT_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E "intent.*\.yaml$|recipe.*\.yaml$")

if [ -z "$INTENT_FILES" ]; then
    exit 0
fi

echo "🔍 Validating IVD artifacts..."

FAILED=0
for file in $INTENT_FILES; do
    if ! ivd validate "$file" --strict; then
        FAILED=1
    fi
done

if [ $FAILED -ne 0 ]; then
    echo "❌ IVD validation failed. Commit aborted."
    echo "   Run 'ivd validate <file>' for details."
    exit 1
fi

echo "✅ All IVD artifacts valid."
exit 0
```

### 2.3 CI/CD Integration

```yaml
# .github/workflows/ivd-validate.yml
name: IVD Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install IVD CLI
        run: pip install ivd-cli
      
      - name: Validate all IVD artifacts
        run: |
          find . -name "*intent*.yaml" -exec ivd validate {} --strict \;
          find . -name "*recipe*.yaml" -exec ivd validate {} -t recipe --strict \;
```

**Verification:**
- CLI commands work correctly
- Pre-commit hook blocks invalid artifacts
- CI/CD catches validation errors

**Dependencies:** Building Block 1 (Foundation)

### 2.4 Validation Testing Tools

**Reference:** `research/validation_methodology.md`

These tools **measure IVD's effectiveness**, not just artifact validity.

**Purpose:** Prove claims about token reduction, iteration count, knowledge retention

```python
# ivd/tools/validation_suite.py
"""Tools for running IVD effectiveness validation tests."""

import pytest
from pathlib import Path
from typing import List, Dict
from ..core.validation_tools import count_context_tokens, calculate_reduction

class ValidationTestRunner:
    """Run validation experiments to prove IVD claims."""
    
    def test_context_efficiency(
        self,
        baseline_files: List[str],
        workflow_intent: str,
        questions: List[str]
    ) -> Dict:
        """
        Test: Token reduction with workflow intent.
        Claim: 80-90% reduction.
        """
        # Measure baseline
        baseline_result = count_context_tokens(baseline_files)
        baseline_tokens = baseline_result["total"]
        
        # Measure IVD
        ivd_result = count_context_tokens([workflow_intent])
        ivd_tokens = ivd_result["total"]
        
        # Calculate reduction
        reduction_percent = calculate_reduction(baseline_tokens, ivd_tokens)
        
        # Test comprehension (both ways)
        baseline_accuracy = self._test_comprehension(questions, baseline_files)
        ivd_accuracy = self._test_comprehension(questions, [workflow_intent])
        
        return {
            "baseline_tokens": baseline_tokens,
            "ivd_tokens": ivd_tokens,
            "reduction_percent": reduction_percent,
            "baseline_accuracy": baseline_accuracy,
            "ivd_accuracy": ivd_accuracy,
            "claim_validated": reduction_percent >= 80 and ivd_accuracy >= baseline_accuracy,
        }
    
    def test_alignment_accuracy(
        self,
        task: str,
        prose_requirements: str,
        intent_artifact: str
    ) -> Dict:
        """
        Test: Iteration reduction with intent artifacts.
        Claim: 30-50% fewer iterations.
        """
        # Run with prose
        baseline_iterations = self._run_implementation_test(task, prose_requirements)
        
        # Run with intent
        ivd_iterations = self._run_implementation_test(task, intent_artifact)
        
        iteration_reduction = calculate_reduction(
            len(baseline_iterations),
            len(ivd_iterations)
        )
        
        return {
            "baseline_iterations": len(baseline_iterations),
            "ivd_iterations": len(ivd_iterations),
            "iteration_reduction_percent": iteration_reduction,
            "claim_validated": iteration_reduction >= 30,
        }

# CLI integration
@click.command()
@click.option('--test', '-t', required=True,
              type=click.Choice(['context', 'alignment', 'durability', 'recipe']))
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Test configuration file')
def run_validation_test(test: str, config: str):
    """Run IVD effectiveness validation test."""
    runner = ValidationTestRunner()
    
    # Load test config
    test_config = yaml.safe_load(Path(config).read_text())
    
    # Run appropriate test
    if test == 'context':
        result = runner.test_context_efficiency(**test_config)
    elif test == 'alignment':
        result = runner.test_alignment_accuracy(**test_config)
    # ... etc
    
    # Report results
    if result['claim_validated']:
        click.echo(f"✅ Claim VALIDATED: {result}")
    else:
        click.echo(f"❌ Claim NOT validated: {result}")
```

**Test suite structure:**

```
tests/validation/
├── context_efficiency/
│   ├── test_token_reduction.py
│   ├── test_comprehension_accuracy.py
│   └── fixtures/
│       ├── sample_image_generation_workflow.yaml
│       └── source_files/
├── alignment_accuracy/
│   ├── test_iteration_count.py
│   └── fixtures/
├── knowledge_durability/
│   ├── test_context_reset.py
│   └── fixtures/
├── recipe_effectiveness/
│   ├── test_time_savings.py
│   └── fixtures/
└── results/
    ├── context_efficiency_2026-01-24.json
    └── validation_report.md
```

**Integration with CI:**

```yaml
# .github/workflows/ivd-effectiveness-validation.yml
name: IVD Effectiveness Validation

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  validate-effectiveness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
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
          path: validation_report.md
```

**Why it's in Tooling:**
- Uses Foundation's validation_tools
- Provides developer-facing CLI commands
- Integrates with CI/CD pipeline
- Generates human-readable reports

**See:** `research/validation_methodology.md` for complete test designs and methodology

**Dependencies:** Building Block 1 (Foundation - validation_tools)

---

## Building Block 3: Configuration Layer

**Purpose:** Modular, scalable IVD configuration  
**Depends On:** Tooling Layer (uses CLI/validator)  
**Enables:** Protocol Layer (MCP server loads config)

### 3.1 Directory Structure

```
.ivd/
├── config.yaml           # Main configuration
├── principles/           # Modular principle files
│   ├── 01-intent-primary.md
│   ├── 02-executable-understanding.md
│   ├── 03-bidirectional-sync.md
│   ├── 04-continuous-verification.md
│   ├── 05-layered-understanding.md
│   ├── 06-ai-partner.md
│   └── 07-survives-transition.md
├── recipes/              # Project recipes
│   └── ...
├── templates/            # Artifact templates
│   └── ...
└── schemas/              # Schema overrides (optional)
```

### 3.2 Configuration Schema

```yaml
# .ivd/config.yaml
ivd:
  version: "2.0"
  
  # Framework location (for reference)
  framework:
    path: "EINs/ein005_books/ivd"
    master_intent: "ivd_system_intent.yaml"
  
  # Principle activation
  principles:
    always_active: [1, 2]     # Always load these
    context_active: [3, 4, 5, 6, 7]  # Load based on task
  
  # Artifact creation rules
  artifacts:
    require_for:
      - "new features"
      - "architectural decisions"
      - "workflow documentation"
      - "pattern recipes"
    optional_for:
      - "bug fixes"
      - "refactoring"
    skip_for:
      - "typos"
      - "formatting"
      - "routine maintenance"
  
  # Validation settings
  validation:
    on_save: false
    on_commit: true
    strict_mode: false
    schema_path: "schemas/"
  
  # Search configuration
  search:
    include:
      - "*.yaml"
      - "*.md"
    exclude:
      - "_private/"
      - "*.pdf"
```

### 3.3 Configuration Loader

```python
# ivd/config/loader.py
"""Configuration loader - provides IVD context to agents and tools."""

from pathlib import Path
from typing import Optional, List, Dict
import yaml

class IVDConfig:
    """Manages IVD configuration loading and context building."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.ivd_dir = self.project_root / ".ivd"
        self._config = None
    
    @property
    def config(self) -> dict:
        """Load and cache configuration."""
        if self._config is None:
            config_path = self.ivd_dir / "config.yaml"
            if config_path.exists():
                with open(config_path) as f:
                    self._config = yaml.safe_load(f)
            else:
                self._config = self._default_config()
        return self._config
    
    def load_principles(self, principle_ids: List[int] = None) -> str:
        """Load principle content for agent context."""
        principles_dir = self.ivd_dir / "principles"
        if not principles_dir.exists():
            return self._load_from_framework()
        
        ids = principle_ids or self.config["ivd"]["principles"]["always_active"]
        content = []
        
        for p_id in ids:
            p_file = principles_dir / f"{p_id:02d}-*.md"
            matches = list(principles_dir.glob(f"{p_id:02d}-*.md"))
            if matches:
                content.append(matches[0].read_text())
        
        return "\n\n".join(content)
    
    def load_context(self, task_type: str = None, files: List[str] = None) -> str:
        """Build complete IVD context for agent."""
        context_parts = []
        
        # Always load core principles
        context_parts.append("# IVD Framework Context\n")
        context_parts.append(self.load_principles())
        
        # Load task-specific principles
        if task_type in ["workflow", "architecture"]:
            extra_ids = self.config["ivd"]["principles"]["context_active"]
            context_parts.append(self.load_principles(extra_ids))
        
        # Load relevant recipes
        if files:
            recipes = self._find_relevant_recipes(files)
            if recipes:
                context_parts.append("\n# Relevant Recipes\n")
                context_parts.extend(recipes)
        
        return "\n".join(context_parts)
    
    def _find_relevant_recipes(self, files: List[str]) -> List[str]:
        """Find recipes relevant to the given files."""
        recipes_dir = self.ivd_dir / "recipes"
        if not recipes_dir.exists():
            return []
        
        # Logic to match files to recipes
        # (implementation depends on recipe structure)
        return []
    
    def _load_from_framework(self) -> str:
        """Load from main IVD framework when no .ivd/ exists."""
        framework_path = self.config["ivd"]["framework"]["path"]
        # Load from framework location
        return ""
    
    def _default_config(self) -> dict:
        """Default configuration when none exists."""
        return {
            "ivd": {
                "version": "2.0",
                "framework": {
                    "path": "EINs/ein005_books/ivd",
                    "master_intent": "ivd_system_intent.yaml"
                },
                "principles": {
                    "always_active": [1, 2],
                    "context_active": [3, 4, 5, 6, 7]
                },
                "validation": {
                    "on_commit": True,
                    "strict_mode": False
                }
            }
        }
```

### 3.4 Migration Support

```python
# ivd/config/migrate.py
"""Migration utilities for .cursorrules → .ivd/"""

from pathlib import Path
import shutil

def migrate_to_ivd(project_root: Path) -> None:
    """Migrate from .cursorrules to .ivd/ structure."""
    cursorrules = project_root / ".cursorrules"
    ivd_dir = project_root / ".ivd"
    
    if not cursorrules.exists():
        print("No .cursorrules found. Creating fresh .ivd/")
        create_ivd_structure(ivd_dir)
        return
    
    # Create .ivd/ structure
    create_ivd_structure(ivd_dir)
    
    # Parse .cursorrules and extract IVD-related content
    content = cursorrules.read_text()
    ivd_content = extract_ivd_content(content)
    
    # Write to appropriate .ivd/ files
    if ivd_content.get("principles"):
        write_principles(ivd_dir, ivd_content["principles"])
    
    if ivd_content.get("rules"):
        write_config(ivd_dir, ivd_content["rules"])
    
    print(f"✅ Migrated to {ivd_dir}")
    print("   .cursorrules preserved (can be removed after verification)")
```

**Verification:**
- Config loader returns correct context
- Migration preserves all settings
- Backward compatibility with .cursorrules

**Dependencies:** Building Block 2 (Tooling)

---

## Building Block 4: Protocol Layer

**Purpose:** Universal access to IVD via MCP  
**Depends On:** All previous layers  
**Enables:** Intelligence Layer, cross-platform access

### 4.1 MCP Server

```python
# ivd/mcp/server.py
"""IVD MCP Server - universal agent access to IVD framework."""

from mcp.server.fastmcp import FastMCP
from pathlib import Path
from ..core.validator import get_validator
from ..config.loader import IVDConfig

# Initialize MCP server
mcp = FastMCP("IVD Framework", json_response=True)
config = IVDConfig()
validator = get_validator()

# ============================================================================
# RESOURCES - Read-only access to IVD knowledge
# ============================================================================

@mcp.resource("ivd://master-intent")
def get_master_intent() -> str:
    """Get the IVD Framework Master Intent."""
    framework_path = Path(config.config["ivd"]["framework"]["path"])
    intent_file = framework_path / "ivd_system_intent.yaml"
    return intent_file.read_text()

@mcp.resource("ivd://principle/{principle_id}")
def get_principle(principle_id: int) -> str:
    """Get a specific IVD principle (1-7)."""
    return config.load_principles([principle_id])

@mcp.resource("ivd://cookbook")
def get_cookbook() -> str:
    """Get the IVD Cookbook."""
    framework_path = Path(config.config["ivd"]["framework"]["path"])
    return (framework_path / "cookbook.md").read_text()

@mcp.resource("ivd://recipe/{recipe_name}")
def get_recipe(recipe_name: str) -> str:
    """Get a specific recipe by name."""
    recipes_dir = Path(config.config["ivd"]["framework"]["path"]) / "recipes"
    recipe_file = recipes_dir / f"{recipe_name}.yaml"
    if recipe_file.exists():
        return recipe_file.read_text()
    return f"Recipe '{recipe_name}' not found"

@mcp.resource("ivd://template/{template_type}")
def get_template(template_type: str) -> str:
    """Get an artifact template (intent, recipe, workflow)."""
    from ..core.templates import get_template
    return get_template(template_type)

@mcp.resource("ivd://context")
def get_context() -> str:
    """Get full IVD context for current project."""
    return config.load_context()

# ============================================================================
# TOOLS - Executable functions for agents
# ============================================================================

@mcp.tool()
def ivd_validate(artifact_yaml: str, artifact_type: str = "intent") -> dict:
    """Validate an IVD artifact against schema and principles.
    
    Args:
        artifact_yaml: YAML content of the artifact
        artifact_type: Type of artifact (intent, recipe, workflow)
    
    Returns:
        Validation result with errors and warnings
    """
    import yaml
    artifact = yaml.safe_load(artifact_yaml)
    result = validator.validate(artifact, artifact_type)
    
    return {
        "valid": result.valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "artifact_type": result.artifact_type
    }

@mcp.tool()
def ivd_check_principle(artifact_yaml: str, principle_id: int) -> dict:
    """Check if artifact aligns with a specific IVD principle.
    
    Args:
        artifact_yaml: YAML content of the artifact
        principle_id: Principle number (1-7)
    
    Returns:
        Alignment check result
    """
    from ..core.principles import check_single_principle
    import yaml
    
    artifact = yaml.safe_load(artifact_yaml)
    result = check_single_principle(artifact, principle_id)
    
    return {
        "principle": principle_id,
        "aligned": result.aligned,
        "issues": result.issues,
        "suggestions": result.suggestions
    }

@mcp.tool()
def ivd_search(query: str, scope: str = "all") -> list:
    """Search IVD documentation and artifacts.
    
    Args:
        query: Search query
        scope: Search scope (all, principles, recipes, examples)
    
    Returns:
        List of matching results with context
    """
    from ..core.search import search_ivd
    
    results = search_ivd(query, scope)
    return [
        {
            "file": str(r.file),
            "line": r.line,
            "context": r.context,
            "relevance": r.relevance
        }
        for r in results
    ]

@mcp.tool()
def ivd_generate(level: str, artifact_type: str) -> str:
    """Generate an IVD artifact template.
    
    Args:
        level: Intent level (task, workflow, module, system)
        artifact_type: Type (feature, pattern, infrastructure, process)
    
    Returns:
        YAML template for the artifact
    """
    from ..core.templates import generate_template
    return generate_template(level, artifact_type)

@mcp.tool()
def ivd_suggest_recipe(description: str) -> dict:
    """Suggest a recipe pattern for a given task description.
    
    Args:
        description: Description of what you want to build
    
    Returns:
        Suggested recipe with template
    """
    from ..core.recipes import suggest_recipe
    return suggest_recipe(description)

# ============================================================================
# PROMPTS - Pre-written templates for common tasks
# ============================================================================

@mcp.prompt("create-intent")
def create_intent_prompt(feature_description: str) -> str:
    """Prompt template for creating a new intent artifact."""
    return f"""Create an IVD intent artifact for the following feature:

{feature_description}

Requirements:
1. Follow the intent.yaml template structure
2. Include clear goal and success metrics
3. Add verification conditions with test paths
4. Consider constraints and risks
5. Document rationale with evidence

Use `ivd_generate('task', 'feature')` to get the template, then customize it."""

@mcp.prompt("validate-artifact")
def validate_artifact_prompt() -> str:
    """Prompt template for validating an artifact."""
    return """Validate this IVD artifact:

1. Run `ivd_validate(artifact_yaml)` to check schema compliance
2. Check principle alignment with `ivd_check_principle(artifact_yaml, N)` for each principle
3. Review any warnings and fix issues
4. Ensure all verification conditions have test paths
5. Verify evidence links point to existing files"""

# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

def run_server(transport: str = "stdio"):
    """Run the IVD MCP server."""
    mcp.run(transport=transport)

if __name__ == "__main__":
    run_server()
```

### 4.2 MCP Server Configuration

```json
{
  "mcpServers": {
    "ivd-framework": {
      "command": "python",
      "args": ["-m", "ivd.mcp.server"],
      "env": {
        "IVD_PROJECT_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

### 4.3 Resource/Tool Summary

**Resources (Read-Only):**
| URI | Description |
|-----|-------------|
| `ivd://master-intent` | IVD Framework Master Intent |
| `ivd://principle/{1-7}` | Individual principles |
| `ivd://cookbook` | IVD Cookbook |
| `ivd://recipe/{name}` | Specific recipe |
| `ivd://template/{type}` | Artifact templates |
| `ivd://context` | Full project context |

**Tools (Executable):**
| Tool | Description |
|------|-------------|
| `ivd_validate` | Validate artifact against schema |
| `ivd_check_principle` | Check principle alignment |
| `ivd_search` | Search IVD documentation |
| `ivd_generate` | Generate artifact template |
| `ivd_suggest_recipe` | Suggest recipe for task |

**Verification:**
- MCP server responds to all resource requests
- All tools execute correctly
- Cross-platform testing (Claude, ChatGPT, Cursor)

**Dependencies:** Building Blocks 1, 2, 3

---

## Building Block 5: Intelligence Layer

**Purpose:** Self-improving IVD configuration  
**Depends On:** All previous layers  
**Enables:** Continuous framework evolution

### 5.1 AI-Editable Configuration

```python
# ivd/intelligence/self_improvement.py
"""AI-driven configuration improvement system."""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
import yaml

@dataclass
class Improvement:
    """A proposed configuration improvement."""
    id: str
    category: str  # principle, recipe, config
    description: str
    proposed_change: str
    rationale: str
    status: str  # pending, approved, rejected, applied
    created_at: datetime
    created_by: str  # agent identifier

class ImprovementManager:
    """Manages AI-proposed improvements to IVD configuration."""
    
    def __init__(self, ivd_dir: Path):
        self.ivd_dir = ivd_dir
        self.improvements_file = ivd_dir / "improvements.yaml"
    
    def propose(self, improvement: Improvement) -> str:
        """Agent proposes a configuration improvement."""
        improvements = self._load_improvements()
        improvements.append(improvement.__dict__)
        self._save_improvements(improvements)
        return improvement.id
    
    def approve(self, improvement_id: str) -> bool:
        """User approves an improvement for application."""
        improvements = self._load_improvements()
        for imp in improvements:
            if imp["id"] == improvement_id:
                imp["status"] = "approved"
                self._save_improvements(improvements)
                return True
        return False
    
    def apply(self, improvement_id: str) -> bool:
        """Apply an approved improvement."""
        improvements = self._load_improvements()
        for imp in improvements:
            if imp["id"] == improvement_id and imp["status"] == "approved":
                # Apply the change
                success = self._apply_change(imp)
                if success:
                    imp["status"] = "applied"
                    self._save_improvements(improvements)
                return success
        return False
    
    def _apply_change(self, improvement: dict) -> bool:
        """Apply a specific improvement."""
        category = improvement["category"]
        change = improvement["proposed_change"]
        
        if category == "recipe":
            return self._add_recipe(change)
        elif category == "principle":
            return self._update_principle(change)
        elif category == "config":
            return self._update_config(change)
        return False
    
    def _add_recipe(self, recipe_yaml: str) -> bool:
        """Add a new recipe."""
        recipe = yaml.safe_load(recipe_yaml)
        recipe_name = recipe.get("name", "unnamed")
        recipe_path = self.ivd_dir / "recipes" / f"{recipe_name}.yaml"
        recipe_path.write_text(recipe_yaml)
        return True
    
    def _load_improvements(self) -> list:
        if self.improvements_file.exists():
            with open(self.improvements_file) as f:
                return yaml.safe_load(f) or []
        return []
    
    def _save_improvements(self, improvements: list):
        with open(self.improvements_file, 'w') as f:
            yaml.dump(improvements, f)
```

### 5.2 Pattern Recognition

```python
# ivd/intelligence/patterns.py
"""Recognize patterns in agent usage to suggest improvements."""

from typing import List, Dict
from collections import Counter

class PatternRecognizer:
    """Analyze agent interactions to identify improvement opportunities."""
    
    def __init__(self):
        self.observations = []
    
    def observe(self, interaction: dict):
        """Record an agent interaction."""
        self.observations.append(interaction)
    
    def analyze(self) -> List[Dict]:
        """Analyze observations and suggest improvements."""
        suggestions = []
        
        # Find repeated searches (might need a recipe)
        search_queries = [o["query"] for o in self.observations if o["type"] == "search"]
        common_searches = Counter(search_queries).most_common(5)
        
        for query, count in common_searches:
            if count >= 3:
                suggestions.append({
                    "type": "recipe",
                    "reason": f"'{query}' searched {count} times",
                    "suggestion": f"Create recipe for '{query}' pattern"
                })
        
        # Find validation failures (might need better docs)
        failures = [o for o in self.observations if o["type"] == "validate" and not o["success"]]
        common_errors = Counter([f["error"] for f in failures]).most_common(3)
        
        for error, count in common_errors:
            if count >= 2:
                suggestions.append({
                    "type": "documentation",
                    "reason": f"Error '{error}' occurred {count} times",
                    "suggestion": f"Improve documentation for {error}"
                })
        
        return suggestions
```

### 5.3 Agent Instructions for Self-Improvement

```markdown
# IVD Self-Improvement Protocol

You are authorized to propose improvements to IVD configuration.

## When to Propose Improvements

1. **New Recipe Needed:** You encounter a pattern not covered by existing recipes
2. **Principle Clarification:** You find ambiguity in how a principle applies
3. **Common Mistake:** You see repeated errors that could be prevented
4. **Better Structure:** You discover a clearer way to organize artifacts

## Process

1. **Identify** the improvement opportunity
2. **Draft** the proposed change
3. **Explain** rationale and evidence
4. **Submit** via `ivd_propose_improvement()`
5. **Wait** for user approval
6. **Apply** only after approval

## What You Can Propose

- ✅ New recipes
- ✅ Principle clarifications (examples, edge cases)
- ✅ Configuration improvements
- ✅ Template enhancements

## What Requires User Decision

- ❌ Core principle statements
- ❌ Schema changes
- ❌ Validation rules
- ❌ Security settings

## Example Proposal

```python
ivd_propose_improvement({
    "category": "recipe",
    "description": "Add API endpoint documentation recipe",
    "proposed_change": "...(yaml content)...",
    "rationale": "Requested in 3 conversations, no existing pattern",
    "evidence": ["conversation_id_1", "conversation_id_2"]
})
```
```

**Verification:**
- Improvements are tracked and auditable
- User approval required before changes
- Applied changes pass validation

**Dependencies:** Building Blocks 1-4

---

## Building Block 6: Community Layer

**Purpose:** Shared recipes and patterns across teams  
**Depends On:** All previous layers (especially MCP)  
**Enables:** Ecosystem growth

### 6.1 Recipe Repository Structure

```
ivd-community-recipes/
├── workflows/
│   ├── api-development.yaml
│   ├── data-pipeline.yaml
│   └── microservice-deployment.yaml
├── patterns/
│   ├── repository-pattern.yaml
│   ├── factory-pattern.yaml
│   └── observer-pattern.yaml
├── agents/
│   ├── code-reviewer.yaml
│   ├── test-generator.yaml
│   └── documentation-writer.yaml
├── schemas/
│   └── recipe-schema.json
└── .github/
    └── workflows/
        └── validate.yml
```

### 6.2 Contribution Workflow

```yaml
# Recipe contribution requirements
contribution:
  required:
    - valid_schema: true
    - has_example: true
    - has_verification: true
    - passes_ci: true
  
  process:
    1: "Fork repository"
    2: "Create recipe in appropriate category"
    3: "Run local validation: ivd validate-recipe"
    4: "Submit pull request"
    5: "Automated CI validation"
    6: "Maintainer review"
    7: "Merge and publish"
```

### 6.3 Recipe Discovery (via MCP)

```python
@mcp.tool()
def ivd_find_community_recipe(pattern_description: str) -> list:
    """Find community recipes matching a pattern description.
    
    Args:
        pattern_description: What you're trying to build
    
    Returns:
        List of matching community recipes
    """
    # Search community repository
    # Return matching recipes with install instructions
    pass

@mcp.tool()
def ivd_install_recipe(recipe_id: str) -> dict:
    """Install a community recipe into local .ivd/recipes/.
    
    Args:
        recipe_id: Community recipe identifier
    
    Returns:
        Installation result
    """
    # Download and install recipe
    # Validate against local schemas
    pass
```

**Verification:**
- All community recipes pass schema validation
- CI/CD validates on contribution
- Recipes are discoverable via MCP

**Dependencies:** Building Blocks 1-5

---

## Implementation Order

Build in this sequence—each block enables the next:

```
1. FOUNDATION     ─────────────────────────────────────────────►
   │ Schema + Validator
   │
   ▼
2. TOOLING        ─────────────────────────────────────────────►
   │ CLI + Hooks + CI/CD
   │
   ▼
3. CONFIGURATION  ─────────────────────────────────────────────►
   │ .ivd/ structure + Loader
   │
   ▼
4. PROTOCOL       ─────────────────────────────────────────────►
   │ MCP Server
   │
   ▼
5. INTELLIGENCE   ─────────────────────────────────────────────►
   │ Self-improvement
   │
   ▼
6. COMMUNITY      ─────────────────────────────────────────────►
     Recipe sharing
```

Each block is **independently valuable** but **maximally effective when combined**.

---

## Verification Approach

Each building block has verification criteria:

| Block | Automated Tests | Manual Verification |
|-------|-----------------|---------------------|
| Foundation | Schema meta-validation, unit tests | Schema coverage review |
| Tooling | CLI tests, hook tests | Developer experience testing |
| Configuration | Loader tests, migration tests | Team usability testing |
| Protocol | MCP integration tests | Cross-platform testing |
| Intelligence | Improvement workflow tests | Audit log review |
| Community | CI validation | Recipe quality review |

---

## Success Metrics

**Foundation Layer:**
- 100% of IVD artifacts have corresponding schemas
- Validator catches all structural errors
- Zero false positives in validation

**Tooling Layer:**
- CLI available via `pip install ivd-cli`
- Pre-commit hook blocks 100% of invalid artifacts
- CI/CD integration documented and tested

**Configuration Layer:**
- .ivd/ migration preserves all settings
- Context loading reduces token usage by 30%+
- Backward compatible with .cursorrules

**Protocol Layer:**
- MCP server accessible from Claude, ChatGPT, Cursor
- All resources and tools documented
- Sub-second response time

**Intelligence Layer:**
- Improvements tracked and auditable
- User approval workflow functional
- Pattern recognition identifies 80%+ of repeated needs

**Community Layer:**
- 50+ community recipes contributed
- Recipe discovery via MCP functional
- Contribution process takes <10 minutes

---

## Key Principles

1. **Foundation First:** Don't build tools without schemas
2. **Composition Over Configuration:** Each block adds capability
3. **Incremental Value:** Each block is useful on its own
4. **Protocol as Integration:** MCP unifies all blocks
5. **Intelligence as Evolution:** Self-improvement drives growth

---

## What NOT to Build

These are **not building blocks** for this architecture:

- ❌ **RAG/Vector Database** - IVD is ~5k lines (threshold: 50k+)
- ❌ **Embeddings** - Overhead not justified at current scale
- ❌ **Fine-tuning** - IVD evolves too quickly
- ❌ **Multi-agent Orchestration** - Single-agent focus sufficient
- ❌ **Custom Protocols** - Use MCP (industry standard)

If IVD grows 10x, revisit RAG as an **optimization layer** above the Protocol Layer.

---

**Document Version:** 3.0 (Building Blocks Architecture)  
**Status:** Canonical Implementation Guide  
**Approach:** Foundation-first, composable components toward ideal implementation
