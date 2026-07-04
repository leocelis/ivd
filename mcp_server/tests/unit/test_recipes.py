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
        assert "canon-rules" in names, (
            "canon-rules recipe missing from ivd_list_recipes — "
            "agents cannot discover the Phase 0a rules block via IVD tooling."
        )
        assert "compliance-trustlint" in names, (
            "compliance-trustlint recipe missing — EU AI Act gate not discoverable via IVD tooling."
        )

    def test_canon_rules_recipe_has_description(self):
        data = json.loads(list_recipes_tool())
        canon = next((r for r in data["recipes"] if r["name"] == "canon-rules"), None)
        assert canon is not None
        assert "Canon" in canon["description"] or "Human Translation" in canon["description"]
        assert canon.get("complexity") == "low"


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

    def test_load_canon_rules_recipe(self):
        """canon-rules must be loadable and contain the fence markers and install_targets."""
        result = load_recipe_tool("canon-rules")
        assert "error" not in result.lower() or "BEGIN-CANON" in result
        # Fence convention must be present so the detector can find it.
        assert "<BEGIN-CANON v1.0>" in result
        assert "<END-CANON v1.0>" in result
        # Installation targets manifest must be present.
        assert "install_targets" in result
        # At least the Cursor adapter must ship.
        assert "cursorrules_format" in result
