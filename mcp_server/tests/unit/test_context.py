# mcp_server/tests/unit/test_context.py

"""Unit tests for ivd_get_context tool."""

import json

from mcp_server.tools.context import get_context_tool


class TestGetContext:
    """Tests for ivd_get_context."""

    def test_returns_valid_json(self):
        result = get_context_tool()
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_contains_core_principles(self):
        data = json.loads(get_context_tool())
        assert "core_principles" in data
        assert len(data["core_principles"]) == 8

    def test_contains_when_to_use(self):
        data = json.loads(get_context_tool())
        assert "when_to_use_ivd" in data
        assert "when_to_skip_ivd" in data
        assert len(data["when_to_use_ivd"]) > 0
        assert len(data["when_to_skip_ivd"]) > 0

    def test_contains_available_recipes(self):
        data = json.loads(get_context_tool())
        assert "available_recipes" in data
        assert isinstance(data["available_recipes"], list)

    def test_contains_available_templates(self):
        data = json.loads(get_context_tool())
        assert "available_templates" in data
        assert set(data["available_templates"]) == {"intent", "recipe", "task", "workflow"}

    def test_contains_next_steps(self):
        data = json.loads(get_context_tool())
        assert "next_steps" in data
        assert len(data["next_steps"]) > 0

    def test_contains_key_metrics(self):
        data = json.loads(get_context_tool())
        assert "key_metrics" in data
        assert "knowledge_capture" in data["key_metrics"]

    def test_principle_8_inversion_guidance(self):
        data = json.loads(get_context_tool())
        assert "when_to_use_principle_8_inversion" in data
        assert "when_to_skip_principle_8_inversion" in data
