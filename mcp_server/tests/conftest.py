# mcp_server/tests/conftest.py

"""
Shared fixtures for IVD MCP Server tests.

Provides:
- tmp_project: temporary directory simulating a project with IVD artifacts
- framework_root: path to the real IVD framework root
- sample_intent_yaml: string content of a valid intent artifact
- bad_intent_yaml: string content of an invalid intent artifact
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# IVD repo root (two levels up from tests/)
IVD_ROOT = Path(__file__).parent.parent.parent.resolve()
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def framework_root() -> Path:
    """Path to the real IVD framework root."""
    return IVD_ROOT


# ---------------------------------------------------------------------------
# Temporary project directory
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """
    Create a temporary directory that looks like a minimal IVD project.

    Structure:
        tmp_project/
        ├── system_intent.yaml   (empty placeholder)
        ├── recipes/             (empty dir)
        └── agent/
            └── my_module/
                └── my_module_intent.yaml
    """
    # system intent
    (tmp_path / "system_intent.yaml").write_text(
        "scope:\n  level: system\nintent:\n  summary: test project\n"
    )

    # recipes dir
    (tmp_path / "recipes").mkdir()

    # module with intent and code (so assess_coverage finds it as coverable)
    mod_dir = tmp_path / "agent" / "my_module"
    mod_dir.mkdir(parents=True)
    (mod_dir / "my_module.py").write_text("# test module\n")
    (mod_dir / "my_module_intent.yaml").write_text(
        "scope:\n  level: module\n"
        "metadata:\n  feature_id: my_module\n  category: test\n  status: implemented\n"
        "intent:\n  summary: A test module\n  goal: Testing\n  success_metric: Tests pass\n"
        "constraints:\n  - name: c1\n    requirement: must work\n    test: tests/test.py\n    consequence_if_violated: bad\n"
        "rationale:\n  decision: test\n  reasoning: test\n  evidence: test\n  date: '2026-01-01'\n  stakeholder: test\n"
        "alternatives:\n  - name: none\n    rejected_because: test\n    when_it_works: never\n"
        "risks:\n  - condition: none\n    action: none\n    monitor: none\n    severity: low\n"
        "implementation:\n  current: agent/my_module/\n  version: 1\n"
        "verification:\n  test_cases:\n    - name: t1\n      description: test\n      validates_constraint: c1\n"
        "changelog:\n  - version: 1\n    date: '2026-01-01'\n    change: init\n    reason: test\n"
    )

    return tmp_path


# ---------------------------------------------------------------------------
# YAML content fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_intent_yaml() -> str:
    """Return the content of the valid sample intent fixture."""
    return (FIXTURES_DIR / "sample_intent.yaml").read_text()


@pytest.fixture
def bad_intent_yaml() -> str:
    """Return the content of the invalid intent fixture."""
    return (FIXTURES_DIR / "bad_intent.yaml").read_text()


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _suppress_termcolor(monkeypatch):
    """Suppress colored terminal output during tests to keep logs clean."""
    monkeypatch.setattr("termcolor.colored", lambda text, *a, **kw: text)
