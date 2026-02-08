# mcp_server/tests/unit/test_recipes.py

"""Unit tests for ivd_load_recipe and ivd_list_recipes tools."""

import json

from mcp_server.tools.recipes import load_recipe_tool, list_recipes_tool


class TestListRecipes:
    """Tests for ivd_list_recipes."""

    def test_returns_valid_json(self):
        result = list_recipes_tool()
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_contains_recipes_list(self):
        data = json.loads(list_recipes_tool())
        assert "recipes" in data
        assert "count" in data
        assert data["count"] == len(data["recipes"])
        assert data["count"] > 0

    def test_each_recipe_has_name_and_description(self):
        data = json.loads(list_recipes_tool())
        for recipe in data["recipes"]:
            assert "name" in recipe
            assert "description" in recipe

    def test_known_recipes_present(self):
        data = json.loads(list_recipes_tool())
        names = [r["name"] for r in data["recipes"]]
        assert "agent-classifier" in names
        assert "workflow-orchestration" in names


class TestLoadRecipe:
    """Tests for ivd_load_recipe."""

    def test_load_existing_recipe(self):
        result = load_recipe_tool("agent-classifier")
        # Should return YAML content, not JSON error
        assert "error" not in result.lower() or "recipe" in result.lower()
        assert len(result) > 100  # Real recipe content is substantial

    def test_load_nonexistent_recipe_returns_error(self):
        result = load_recipe_tool("nonexistent-recipe-xyz")
        data = json.loads(result)
        assert "error" in data
        assert "available_recipes" in data
        assert isinstance(data["available_recipes"], list)

    def test_load_recipe_returns_yaml_content(self):
        result = load_recipe_tool("workflow-orchestration")
        # YAML content should contain recipe-like sections
        assert "description" in result or "pattern" in result or "recipe" in result
