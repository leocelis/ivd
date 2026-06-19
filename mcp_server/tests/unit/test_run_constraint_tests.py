# mcp_server/tests/unit/test_run_constraint_tests.py

"""Unit tests for ivd_run_constraint_tests (opt-in test runner)."""

import ast
import json
from pathlib import Path

import yaml

from mcp_server.tools.run_constraint_tests import (
    collect_test_nodes,
    run_constraint_tests_tool,
)
from mcp_server.tools._paths import IVD_FRAMEWORK_ROOT


def _intent_with(constraints_yaml: str, extra: str = "") -> str:
    return (
        "intent:\n"
        "  summary: t\n  goal: t\n  success_metric: t\n"
        f"{constraints_yaml}"
        f"{extra}"
        "rationale:\n  decision: t\n  reasoning: t\n"
        "alternatives:\n  - name: none\n"
        "risks:\n  - condition: none\n"
        "implementation:\n  current: .\n"
        "verification:\n  test_cases: []\n"
    )


class TestOptIn:
    def test_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("IVD_TEST_RUNNER_ENABLED", raising=False)
        result = json.loads(run_constraint_tests_tool("intent:\n  summary: t\n"))
        assert result["enabled"] is False
        assert result["ok"] is False

    def test_enabled_when_env_true(self, monkeypatch):
        monkeypatch.setenv("IVD_TEST_RUNNER_ENABLED", "true")
        yaml_str = _intent_with("constraints: []\n")
        result = json.loads(run_constraint_tests_tool(yaml_str))
        assert result["enabled"] is True
        assert result["ok"] is True
        assert result["tests_run"] == 0


class TestAllowlist:
    def test_collects_only_executable_nodes(self):
        yaml_str = _intent_with(
            "constraints:\n"
            "  - name: good\n    requirement: x\n"
            "    test: mcp_server/tests/unit/test_validate.py::TestValidateArtifact::test_empty_yaml_has_errors\n"
            "  - name: prose\n    requirement: y\n"
            "    test: run manual review\n"
            "  - name: missing\n    requirement: z\n"
            "    test: no/such/file.py::test_x\n"
        )
        import yaml
        artifact = yaml.safe_load(yaml_str)
        nodes = collect_test_nodes(artifact, IVD_FRAMEWORK_ROOT)
        assert len(nodes) == 1
        assert nodes[0][0] == "good"
        assert "test_validate.py" in nodes[0][1]

    def test_runs_allowlisted_test_when_enabled(self, monkeypatch):
        monkeypatch.setenv("IVD_TEST_RUNNER_ENABLED", "true")
        node = "mcp_server/tests/unit/test_validate.py::TestValidateArtifact::test_empty_yaml_has_errors"
        yaml_str = _intent_with(
            "constraints:\n"
            f"  - name: ok\n    requirement: x\n    test: {node}\n"
        )
        result = json.loads(
            run_constraint_tests_tool(yaml_str, project_root_arg=str(IVD_FRAMEWORK_ROOT))
        )
        assert result["tests_run"] == 1
        assert result["all_passed"] is True
        assert result["results"][0]["passed"] is True


class TestValidateIsolation:
    def test_validate_has_no_runner_import(self):
        validate_path = Path(__file__).resolve().parents[2] / "tools" / "validate.py"
        tree = ast.parse(validate_path.read_text(encoding="utf-8"))
        imports = {
            node.names[0].name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert "run_constraint_tests" not in str(imports)
        source = validate_path.read_text(encoding="utf-8")
        assert "run_constraint_tests" not in source
        assert "subprocess" not in source
