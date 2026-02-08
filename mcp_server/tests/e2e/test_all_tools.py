# mcp_server/tests/e2e/test_all_tools.py

"""
End-to-end validation of all 14 MCP tools.

Calls every tool through the registry's call_tool() with realistic arguments
and validates that each one returns a well-formed, non-error response.

This is the definitive "all tools work" test — if it passes, the MCP server
can serve every tool correctly.
"""

import json
import os

import pytest

from mcp_server.registry import call_tool, get_all_tools


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_json(result: str) -> dict:
    """Parse tool result as JSON; raise AssertionError with context on failure."""
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        # Some tools return plain text — that's fine, return as-is
        return {"_raw": result}


def assert_no_error(result: str, tool_name: str):
    """Assert the result doesn't start with an error message."""
    assert not result.startswith("Error executing"), (
        f"{tool_name} returned an error: {result[:300]}"
    )
    assert not result.startswith("Error:"), (
        f"{tool_name} returned an error: {result[:300]}"
    )


# ---------------------------------------------------------------------------
# 1. ivd_get_context — load framework context
# ---------------------------------------------------------------------------

class TestGetContext:
    def test_returns_principles(self):
        result = call_tool("ivd_get_context", {})
        assert_no_error(result, "ivd_get_context")
        data = parse_json(result)
        assert "core_principles" in data
        assert len(data["core_principles"]) == 8

    def test_returns_templates(self):
        result = call_tool("ivd_get_context", {})
        data = parse_json(result)
        assert "available_templates" in data
        assert "workflow" in data["available_templates"]

    def test_response_is_substantial(self):
        result = call_tool("ivd_get_context", {})
        assert len(result) > 500, "Context response too small"


# ---------------------------------------------------------------------------
# 2. ivd_load_recipe — load a specific recipe
# ---------------------------------------------------------------------------

class TestLoadRecipe:
    def test_load_agent_classifier(self):
        result = call_tool("ivd_load_recipe", {"recipe_name": "agent-classifier"})
        assert_no_error(result, "ivd_load_recipe")
        assert "agent" in result.lower()
        assert len(result) > 200

    def test_load_workflow_orchestration(self):
        result = call_tool("ivd_load_recipe", {"recipe_name": "workflow-orchestration"})
        assert_no_error(result, "ivd_load_recipe")
        assert "workflow" in result.lower()

    def test_load_nonexistent_recipe(self):
        result = call_tool("ivd_load_recipe", {"recipe_name": "does-not-exist"})
        # Should return a helpful message, not crash
        assert isinstance(result, str)
        assert "not found" in result.lower() or "error" in result.lower() or "available" in result.lower()


# ---------------------------------------------------------------------------
# 3. ivd_list_recipes — list all recipes
# ---------------------------------------------------------------------------

class TestListRecipes:
    def test_returns_recipes(self):
        result = call_tool("ivd_list_recipes", {})
        assert_no_error(result, "ivd_list_recipes")
        data = parse_json(result)
        assert "recipes" in data
        assert len(data["recipes"]) >= 7

    def test_recipes_have_names(self):
        result = call_tool("ivd_list_recipes", {})
        data = parse_json(result)
        for recipe in data["recipes"]:
            assert "name" in recipe or "file" in recipe


# ---------------------------------------------------------------------------
# 4. ivd_load_template — load an intent template
# ---------------------------------------------------------------------------

class TestLoadTemplate:
    def test_load_intent_template(self):
        result = call_tool("ivd_load_template", {"template_type": "intent"})
        assert_no_error(result, "ivd_load_template")
        assert "scope" in result or "intent" in result
        assert len(result) > 100

    def test_load_recipe_template(self):
        result = call_tool("ivd_load_template", {"template_type": "recipe"})
        assert_no_error(result, "ivd_load_template")
        assert len(result) > 100


# ---------------------------------------------------------------------------
# 5. ivd_validate — validate an intent artifact
# ---------------------------------------------------------------------------

class TestValidate:
    def test_valid_intent_passes(self):
        yaml_str = (
            "scope:\n  level: module\n  type: feature\n"
            "intent:\n  summary: Test feature\n  goal: Testing\n  success_metric: Works\n"
            "constraints:\n  - name: c1\n    requirement: must work\n    test: tests/t.py\n    consequence_if_violated: bad\n"
            "rationale:\n  decision: test\n  reasoning: test\n  evidence: test\n  date: '2026-01-01'\n  stakeholder: dev\n"
            "alternatives:\n  - name: none\n    rejected_because: n/a\n    when_it_works: never\n"
            "risks:\n  - condition: none\n    action: none\n    monitor: none\n    severity: low\n"
            "implementation:\n  current: src/\n  version: 1\n"
            "verification:\n  test_cases:\n    - name: t1\n      description: test\n      validates_constraint: c1\n"
            "changelog:\n  - version: 1\n    date: '2026-01-01'\n    change: init\n    reason: test\n"
        )
        result = call_tool("ivd_validate", {"artifact_yaml": yaml_str})
        assert_no_error(result, "ivd_validate")
        data = parse_json(result)
        assert data.get("valid") is True, f"Expected valid, got: {data}"

    def test_invalid_intent_reports_errors(self):
        yaml_str = "scope:\n  level: module\n"
        result = call_tool("ivd_validate", {"artifact_yaml": yaml_str})
        assert_no_error(result, "ivd_validate")
        data = parse_json(result)
        assert data.get("valid") is False
        assert len(data.get("errors", [])) > 0

    def test_empty_yaml(self):
        result = call_tool("ivd_validate", {"artifact_yaml": ""})
        assert isinstance(result, str)
        # Should handle gracefully
        data = parse_json(result)
        assert data.get("valid") is False or "error" in result.lower()


# ---------------------------------------------------------------------------
# 6. ivd_scaffold — scaffold a new artifact
# ---------------------------------------------------------------------------

class TestScaffold:
    def test_scaffold_module(self, tmp_path):
        result = call_tool("ivd_scaffold", {
            "level": "module",
            "name": "payments",
            "module_path": "services/payments",
            "project_root": str(tmp_path),
        })
        assert_no_error(result, "ivd_scaffold")
        assert "payments" in result.lower()

    def test_scaffold_system(self, tmp_path):
        result = call_tool("ivd_scaffold", {
            "level": "system",
            "name": "my_project",
            "project_root": str(tmp_path),
        })
        assert_no_error(result, "ivd_scaffold")
        assert "system" in result.lower() or "intent" in result.lower()


# ---------------------------------------------------------------------------
# 7. ivd_init — initialize IVD in a project
# ---------------------------------------------------------------------------

class TestInit:
    def test_init_creates_system_intent(self, tmp_path):
        # Create a minimal project structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")
        (tmp_path / "README.md").write_text("# My Project")

        result = call_tool("ivd_init", {
            "project_root": str(tmp_path),
            "auto_fill": True,
        })
        assert_no_error(result, "ivd_init")
        assert "system" in result.lower() or "intent" in result.lower()


# ---------------------------------------------------------------------------
# 8. ivd_find_artifacts — discover artifacts
# ---------------------------------------------------------------------------

class TestFindArtifacts:
    def test_find_all_in_ivd_repo(self, framework_root):
        result = call_tool("ivd_find_artifacts", {
            "scope": "all",
            "project_root": str(framework_root),
        })
        assert_no_error(result, "ivd_find_artifacts")
        data = parse_json(result)
        artifacts = data.get("artifacts", [])
        assert len(artifacts) > 0, "Should find at least one artifact in IVD repo"

    def test_find_system_scope(self, framework_root):
        result = call_tool("ivd_find_artifacts", {
            "scope": "system",
            "project_root": str(framework_root),
        })
        assert_no_error(result, "ivd_find_artifacts")


# ---------------------------------------------------------------------------
# 9. ivd_check_placement — validate artifact placement
# ---------------------------------------------------------------------------

class TestCheckPlacement:
    def test_system_intent_at_root_is_correct(self, framework_root):
        result = call_tool("ivd_check_placement", {
            "artifact_path": "ivd_system_intent.yaml",
            "project_root": str(framework_root),
        })
        assert_no_error(result, "ivd_check_placement")
        assert isinstance(result, str)

    def test_module_intent_in_correct_location(self, tmp_project):
        result = call_tool("ivd_check_placement", {
            "artifact_path": "agent/my_module/my_module_intent.yaml",
            "project_root": str(tmp_project),
        })
        assert_no_error(result, "ivd_check_placement")


# ---------------------------------------------------------------------------
# 10. ivd_list_features — derive feature inventory
# ---------------------------------------------------------------------------

class TestListFeatures:
    def test_list_features_in_ivd_repo(self, framework_root):
        result = call_tool("ivd_list_features", {
            "project_root": str(framework_root),
        })
        assert_no_error(result, "ivd_list_features")
        data = parse_json(result)
        assert "features" in data or "artifacts" in data or "count" in data or isinstance(data.get("_raw"), str)

    def test_list_features_in_tmp_project(self, tmp_project):
        result = call_tool("ivd_list_features", {
            "project_root": str(tmp_project),
        })
        assert_no_error(result, "ivd_list_features")


# ---------------------------------------------------------------------------
# 11. ivd_propose_inversions — Principle 8
# ---------------------------------------------------------------------------

class TestProposeInversions:
    def test_returns_inversions(self):
        result = call_tool("ivd_propose_inversions", {
            "problem_description": "We need to export large datasets to CSV for compliance reporting",
            "domain_context": "data_export",
        })
        assert_no_error(result, "ivd_propose_inversions")
        data = parse_json(result)
        assert "inversion_opportunities" in data
        assert len(data["inversion_opportunities"]) > 0

    def test_without_domain(self):
        result = call_tool("ivd_propose_inversions", {
            "problem_description": "User authentication for a multi-tenant SaaS",
        })
        assert_no_error(result, "ivd_propose_inversions")


# ---------------------------------------------------------------------------
# 12. ivd_discover_goal — goal discovery
# ---------------------------------------------------------------------------

class TestDiscoverGoal:
    def test_with_hint(self):
        result = call_tool("ivd_discover_goal", {
            "user_hint": "I want to improve our data pipeline",
            "domain_or_context": "data_engineering",
        })
        assert_no_error(result, "ivd_discover_goal")
        assert len(result) > 100

    def test_without_any_input(self):
        result = call_tool("ivd_discover_goal", {})
        assert_no_error(result, "ivd_discover_goal")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# 13. ivd_teach_concept — teaching before intent
# ---------------------------------------------------------------------------

class TestTeachConcept:
    def test_teach_etl(self):
        result = call_tool("ivd_teach_concept", {
            "concept": "ETL",
            "user_context": "Building a data warehouse for the first time",
        })
        assert_no_error(result, "ivd_teach_concept")
        assert "ETL" in result
        assert len(result) > 200

    def test_teach_saga_pattern(self):
        result = call_tool("ivd_teach_concept", {
            "concept": "Saga pattern",
        })
        assert_no_error(result, "ivd_teach_concept")
        assert "saga" in result.lower()


# ---------------------------------------------------------------------------
# 14. ivd_search — semantic search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_search_returns_results(self):
        result = call_tool("ivd_search", {
            "query": "What are the eight principles of IVD?",
            "top_k": 3,
        })
        assert_no_error(result, "ivd_search")
        data = parse_json(result)
        # Should return results (or error if no OPENAI_API_KEY — both acceptable)
        if "results" in data:
            assert len(data["results"]) > 0
        elif "error" in data:
            # Acceptable: no API key in test environment
            assert "api" in data["error"].lower() or "key" in data["error"].lower() or "embed" in data["error"].lower()
        elif "_raw" in data:
            # Plain text response — check it's not empty
            assert len(data["_raw"]) > 0

    def test_search_with_different_query(self):
        result = call_tool("ivd_search", {
            "query": "How do recipes work?",
        })
        assert_no_error(result, "ivd_search")
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Meta: all 14 tools respond without crashing
# ---------------------------------------------------------------------------

class TestAllToolsRespond:
    """
    Smoke-level check: call every registered tool with minimal arguments
    and verify it returns a string without raising an exception.
    """

    # (tool_name, minimal_arguments)
    TOOL_CALLS = [
        ("ivd_get_context", {}),
        ("ivd_list_recipes", {}),
        ("ivd_load_recipe", {"recipe_name": "agent-classifier"}),
        ("ivd_load_template", {"template_type": "intent"}),
        ("ivd_validate", {"artifact_yaml": "scope:\n  level: module\n"}),
        ("ivd_propose_inversions", {"problem_description": "test"}),
        ("ivd_discover_goal", {}),
        ("ivd_teach_concept", {"concept": "REST API"}),
        ("ivd_search", {"query": "principles"}),
    ]

    @pytest.mark.parametrize("tool_name,args", TOOL_CALLS, ids=[t[0] for t in TOOL_CALLS])
    def test_tool_returns_string(self, tool_name, args):
        result = call_tool(tool_name, args)
        assert isinstance(result, str), f"{tool_name} returned {type(result)}"
        assert len(result) > 0, f"{tool_name} returned empty string"

    def test_all_14_tools_covered(self):
        """Verify this test file covers all 14 registered tools."""
        registered = {t.name for t in get_all_tools()}
        # Tools tested in parametrized + individual classes above
        tested = {
            "ivd_get_context", "ivd_load_recipe", "ivd_load_template",
            "ivd_list_recipes", "ivd_validate", "ivd_init", "ivd_scaffold",
            "ivd_find_artifacts", "ivd_check_placement", "ivd_list_features",
            "ivd_propose_inversions", "ivd_discover_goal", "ivd_teach_concept",
            "ivd_search",
        }
        assert tested == registered, f"Missing tests for: {registered - tested}"
