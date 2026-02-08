# mcp_server/tests/unit/test_scaffold.py

"""Unit tests for ivd_scaffold and ivd_init tools."""

import json
from pathlib import Path

from mcp_server.tools.scaffold import scaffold_artifact_tool, init_project_tool


class TestInitProject:
    """Tests for ivd_init."""

    def test_init_creates_system_intent(self, tmp_path):
        # Remove existing system_intent if any
        si = tmp_path / "system_intent.yaml"
        if si.exists():
            si.unlink()

        result = json.loads(init_project_tool(str(tmp_path)))
        assert result["success"] is True
        assert result["written_to_disk"] is True
        assert (tmp_path / "system_intent.yaml").exists()

    def test_init_rejects_if_already_exists(self, tmp_project):
        result = json.loads(init_project_tool(str(tmp_project)))
        assert "error" in result
        assert "already exists" in result["error"]

    def test_init_nonexistent_path_skips_autofill(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist"
        result = json.loads(init_project_tool(str(nonexistent)))
        assert result["success"] is True
        assert result["written_to_disk"] is False
        assert result["auto_fill"] is False

    def test_init_template_content_present(self, tmp_path):
        si = tmp_path / "system_intent.yaml"
        if si.exists():
            si.unlink()
        result = json.loads(init_project_tool(str(tmp_path)))
        assert "template_content" in result
        assert len(result["template_content"]) > 0

    def test_init_has_next_steps(self, tmp_path):
        si = tmp_path / "system_intent.yaml"
        if si.exists():
            si.unlink()
        result = json.loads(init_project_tool(str(tmp_path)))
        assert "next_steps" in result
        assert len(result["next_steps"]) > 0


class TestScaffoldArtifact:
    """Tests for ivd_scaffold."""

    def test_scaffold_module_intent(self, tmp_project):
        result = json.loads(scaffold_artifact_tool(
            "module", "new_feature", module_path="agent/new_feature",
            project_root_arg=str(tmp_project),
        ))
        assert result["success"] is True
        assert result["level"] == "module"
        assert "new_feature_intent.yaml" in result["path"]

    def test_scaffold_task_intent(self, tmp_project):
        result = json.loads(scaffold_artifact_tool(
            "task", "process_data", module_path="agent/my_module",
            project_root_arg=str(tmp_project),
        ))
        assert result["success"] is True
        assert result["level"] == "task"
        assert "intents/" in result["path"]

    def test_scaffold_workflow_intent(self, tmp_project):
        result = json.loads(scaffold_artifact_tool(
            "workflow", "onboarding_flow",
            project_root_arg=str(tmp_project),
        ))
        assert result["success"] is True
        assert result["level"] == "workflow"
        assert "workflows/" in result["path"]

    def test_scaffold_invalid_level(self, tmp_project):
        result = json.loads(scaffold_artifact_tool(
            "invalid_level", "test",
            project_root_arg=str(tmp_project),
        ))
        assert "error" in result

    def test_scaffold_module_without_path_errors(self, tmp_project):
        result = json.loads(scaffold_artifact_tool(
            "module", "test",
            project_root_arg=str(tmp_project),
        ))
        assert "error" in result

    def test_scaffold_duplicate_errors(self, tmp_project):
        # my_module_intent.yaml already exists in tmp_project
        result = json.loads(scaffold_artifact_tool(
            "module", "my_module", module_path="agent/my_module",
            project_root_arg=str(tmp_project),
        ))
        assert "error" in result
        assert "already exists" in result["error"]

    def test_scaffold_includes_template_content(self, tmp_project):
        result = json.loads(scaffold_artifact_tool(
            "module", "brand_new", module_path="agent/brand_new",
            project_root_arg=str(tmp_project),
        ))
        assert "template_content" in result
        assert len(result["template_content"]) > 0

    def test_scaffold_injects_parent_intent(self, tmp_project):
        result = json.loads(scaffold_artifact_tool(
            "module", "child_mod", module_path="agent/child_mod",
            project_root_arg=str(tmp_project),
        ))
        assert "parent_intent" in result.get("template_content", "")
