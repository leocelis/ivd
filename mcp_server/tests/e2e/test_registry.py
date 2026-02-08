# mcp_server/tests/e2e/test_registry.py

"""End-to-end tests for the tool registry and dispatch layer.

Verifies:
- All 14 tools are registered
- call_tool dispatches correctly
- Unknown tools return error
- Tool results are strings (JSON or text)
"""

import json

from mcp_server.registry import get_all_tools, call_tool, TOOL_HANDLERS


class TestToolRegistry:
    """Tests for the tool registry."""

    def test_14_tools_registered(self):
        tools = get_all_tools()
        assert len(tools) == 14

    def test_all_tools_have_names(self):
        tools = get_all_tools()
        names = [t.name for t in tools]
        assert len(set(names)) == 14  # All unique

    def test_expected_tools_present(self):
        tools = get_all_tools()
        names = {t.name for t in tools}
        expected = {
            "ivd_get_context", "ivd_load_recipe", "ivd_load_template",
            "ivd_list_recipes", "ivd_validate", "ivd_init", "ivd_scaffold",
            "ivd_find_artifacts", "ivd_check_placement", "ivd_list_features",
            "ivd_propose_inversions", "ivd_discover_goal", "ivd_teach_concept",
            "ivd_search",
        }
        assert names == expected

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
