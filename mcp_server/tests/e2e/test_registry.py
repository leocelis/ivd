# mcp_server/tests/e2e/test_registry.py

"""End-to-end tests for the tool registry and dispatch layer.

Verifies:
- All 30 tools are registered (16 core + 9 judgment + 4 canon + 1 opt-in test runner)
- call_tool dispatches correctly
- Unknown tools return error
- Tool results are strings (JSON or text)
"""

import json

from mcp_server.registry import get_all_tools, call_tool, TOOL_HANDLERS

EXPECTED_TOOL_COUNT = 30


class TestToolRegistry:
    """Tests for the tool registry."""

    def test_expected_tool_count_registered(self):
        tools = get_all_tools()
        assert len(tools) == EXPECTED_TOOL_COUNT

    def test_all_tools_have_names(self):
        tools = get_all_tools()
        names = [t.name for t in tools]
        assert len(set(names)) == EXPECTED_TOOL_COUNT  # All unique

    def test_expected_tools_present(self):
        tools = get_all_tools()
        names = {t.name for t in tools}
        core = {
            "ivd_get_context", "ivd_load_recipe", "ivd_load_template",
            "ivd_list_recipes", "ivd_validate", "ivd_review_intent",
            "ivd_run_constraint_tests",
            "ivd_init", "ivd_scaffold",
            "ivd_find_artifacts", "ivd_check_placement", "ivd_list_features",
            "ivd_assess_coverage",
            "ivd_propose_inversions", "ivd_discover_goal", "ivd_teach_concept",
            "ivd_search",
        }
        judgment = {
            "ivd_judgment_init",
            "ivd_judgment_capture",
            "ivd_judgment_codify",
            "ivd_judgment_save_codified",
            "ivd_judgment_pair",
            "ivd_judgment_detect_patterns",
            "ivd_judgment_inject_context",
            "ivd_judgment_propose_recommendation",
            "ivd_judgment_check_installed",
        }
        canon = {
            "canon_render",
            "canon_check",
            "canon_diff",
            "canon_check_rules_installed",
        }
        expected = core | judgment | canon
        assert names == expected, f"missing: {expected - names}; extra: {names - expected}"

    def test_all_tools_have_input_schema(self):
        tools = get_all_tools()
        for t in tools:
            assert t.inputSchema is not None
            assert "type" in t.inputSchema
            assert t.inputSchema["type"] == "object"

    def test_all_tools_have_handlers(self):
        tools = get_all_tools()
        for t in tools:
            assert t.name in TOOL_HANDLERS, f"Tool {t.name} has no handler"


class TestCallTool:
    """Tests for the call_tool dispatch function."""

    def test_unknown_tool_returns_error(self):
        result = call_tool("nonexistent_tool", {})
        assert "Error" in result or "error" in result

    def test_get_context_via_dispatch(self):
        result = call_tool("ivd_get_context", {})
        assert isinstance(result, str)
        data = json.loads(result)
        assert "core_principles" in data

    def test_list_recipes_via_dispatch(self):
        result = call_tool("ivd_list_recipes", {})
        assert isinstance(result, str)
        data = json.loads(result)
        assert "recipes" in data

    def test_validate_via_dispatch(self):
        yaml_str = "intent:\n  summary: test\n  goal: test\n  success_metric: test\n"
        result = call_tool("ivd_validate", {"artifact_yaml": yaml_str})
        assert isinstance(result, str)
        data = json.loads(result)
        assert "valid" in data

    def test_propose_inversions_via_dispatch(self):
        result = call_tool("ivd_propose_inversions", {"problem_description": "test problem"})
        assert isinstance(result, str)
        data = json.loads(result)
        assert "inversion_opportunities" in data

    def test_teach_concept_via_dispatch(self):
        result = call_tool("ivd_teach_concept", {"concept": "ETL"})
        assert isinstance(result, str)
        assert "ETL" in result

    def test_result_is_always_string(self):
        """call_tool must always return a string, never dict/list."""
        for tool_name in ["ivd_get_context", "ivd_list_recipes"]:
            result = call_tool(tool_name, {})
            assert isinstance(result, str)
