# mcp_server/tools/run_constraint_tests.py

"""Tool: ivd_run_constraint_tests — opt-in pytest runner for intent-linked tests."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from termcolor import colored

from mcp_server.tools._paths import project_root
from mcp_server.tools.validate import (
    _extract_joint_satisfaction_test,
    _repo_file_missing,
    _test_file_part,
    _test_reference_executable,
)

LOG = "IVD Tools"
_OPT_IN_ENV = "IVD_TEST_RUNNER_ENABLED"
_MAX_TESTS = 20
_DEFAULT_TIMEOUT_SEC = 120


def _is_test_runner_enabled() -> bool:
    """Default disabled — public servers must opt in explicitly."""
    val = os.environ.get(_OPT_IN_ENV, "false")
    return val.strip().lower() in ("true", "1", "yes", "on")


def _disabled_payload() -> Dict[str, Any]:
    return {
        "ok": False,
        "enabled": False,
        "tool": "ivd_run_constraint_tests",
        "message": (
            "Constraint test runner is disabled on this IVD MCP server "
            f"({_OPT_IN_ENV} is not true). Enable locally or in CI with "
            f"{_OPT_IN_ENV}=true. ivd_validate remains structure-only."
        ),
    }


def collect_test_nodes(artifact: dict, root: Path) -> List[Tuple[str, str]]:
    """Return (label, pytest_node_id) pairs allowlisted from the intent only."""
    nodes: List[Tuple[str, str]] = []
    seen: set = set()

    constraints = artifact.get("constraints")
    if isinstance(constraints, list):
        for i, constraint in enumerate(constraints):
            if not isinstance(constraint, dict):
                continue
            test = constraint.get("test")
            if not isinstance(test, str):
                continue
            node = test.strip()
            if not _test_reference_executable(node):
                continue
            if _repo_file_missing(_test_file_part(node), root):
                continue
            if node in seen:
                continue
            label = str(constraint.get("name", f"constraint_{i + 1}"))
            nodes.append((label, node))
            seen.add(node)

    cs = artifact.get("constraint_satisfiability")
    if isinstance(cs, dict):
        joint = _extract_joint_satisfaction_test(cs)
        if joint and _test_reference_executable(joint) and not _repo_file_missing(
            _test_file_part(joint), root
        ):
            if joint not in seen:
                nodes.append(("joint_satisfaction", joint))
                seen.add(joint)

    return nodes[:_MAX_TESTS]


def _run_pytest_node(node: str, cwd: Path, timeout_sec: int) -> Dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", node, "-q", "--tb=short"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return {
            "node_id": node,
            "passed": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-2000:],
            "stderr_tail": (proc.stderr or "")[-2000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "node_id": node,
            "passed": False,
            "exit_code": -1,
            "error": "timeout",
            "stdout_tail": (exc.stdout or "")[-1000:] if exc.stdout else "",
            "stderr_tail": (exc.stderr or "")[-1000:] if exc.stderr else "",
        }


def run_constraint_tests_tool(
    artifact_yaml: str,
    project_root_arg: Optional[str] = None,
    timeout_sec: int = _DEFAULT_TIMEOUT_SEC,
) -> str:
    """Run allowlisted pytest nodes from an intent artifact (opt-in only)."""
    print(colored(f"[{LOG}] ivd_run_constraint_tests", "cyan"))

    if not _is_test_runner_enabled():
        return json.dumps(_disabled_payload(), indent=2)

    try:
        artifact = yaml.safe_load(artifact_yaml)
    except yaml.YAMLError as e:
        return json.dumps({
            "ok": False,
            "enabled": True,
            "errors": [f"YAML parse error: {e}"],
            "results": [],
        }, indent=2)

    if artifact is None or not isinstance(artifact, dict):
        return json.dumps({
            "ok": False,
            "enabled": True,
            "errors": ["Empty or invalid artifact"],
            "results": [],
        }, indent=2)

    root = project_root(project_root_arg, require_exists=True)
    nodes = collect_test_nodes(artifact, root)

    if not nodes:
        return json.dumps({
            "ok": True,
            "enabled": True,
            "project_root": str(root),
            "tests_run": 0,
            "all_passed": True,
            "results": [],
            "note": (
                "No executable pytest node ids found in the intent "
                "(constraints[].test or joint_satisfaction_test with repo files on disk)."
            ),
        }, indent=2)

    per_test_timeout = max(5, timeout_sec // max(len(nodes), 1))
    results = []
    for label, node in nodes:
        outcome = _run_pytest_node(node, root, per_test_timeout)
        outcome["label"] = label
        results.append(outcome)

    all_passed = all(r.get("passed") for r in results)
    payload = {
        "ok": True,
        "enabled": True,
        "project_root": str(root),
        "tests_run": len(results),
        "all_passed": all_passed,
        "results": results,
        "note": (
            "Ran only pytest nodes declared in the intent artifact. "
            "Does not replace ivd_validate (structure-only) or the agent "
            "Post-Implementation Verification Protocol."
        ),
    }
    color = "green" if all_passed else "red"
    print(colored(
        f"[{LOG}] ivd_run_constraint_tests: {len(results)} tests, all_passed={all_passed}",
        color,
    ))
    return json.dumps(payload, indent=2)
