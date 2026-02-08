# mcp_server/tests/unit/test_templates.py

"""Unit tests for ivd_load_template tool."""

import json

from mcp_server.tools.templates import load_template_tool


class TestLoadTemplate:
    """Tests for ivd_load_template."""

    def test_load_intent_template(self):
        result = load_template_tool("intent")
        assert len(result) > 100
        # Should contain IVD structure
        assert "intent" in result.lower()

    def test_load_recipe_template(self):
        result = load_template_tool("recipe")
        assert len(result) > 50

    def test_load_task_template(self):
        result = load_template_tool("task")
        assert len(result) > 100

    def test_load_workflow_template(self):
        result = load_template_tool("workflow")
        assert len(result) > 100

    def test_invalid_template_type_returns_error(self):
        result = load_template_tool("nonexistent")
        data = json.loads(result)
        assert "error" in data
        assert "valid_types" in data
        assert set(data["valid_types"]) == {"intent", "recipe", "task", "workflow"}

    def test_all_valid_types_return_content(self):
        for ttype in ["intent", "recipe", "task", "workflow"]:
            result = load_template_tool(ttype)
            # Should NOT be JSON error
            try:
                data = json.loads(result)
                assert "error" not in data, f"{ttype} template returned error: {data}"
            except json.JSONDecodeError:
                pass  # YAML content, not JSON — that's correct
