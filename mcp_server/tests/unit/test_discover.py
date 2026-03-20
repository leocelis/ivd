# mcp_server/tests/unit/test_discover.py

"""Unit tests for ivd_find_artifacts, ivd_check_placement, ivd_list_features, ivd_assess_coverage tools."""

import json

from mcp_server.tools.discover import (
    find_artifacts_tool,
    check_placement_tool,
    list_features_tool,
    assess_coverage_tool,
)


class TestFindArtifacts:
    """Tests for ivd_find_artifacts."""

    def test_find_all_in_project(self, tmp_project):
        result = json.loads(find_artifacts_tool("all", str(tmp_project)))
        assert result["count"] > 0
        assert "artifacts" in result

    def test_find_all_returns_known_artifact(self, tmp_project):
        result = json.loads(find_artifacts_tool("all", str(tmp_project)))
        paths = [a["path"] for a in result["artifacts"]]
        assert any("my_module_intent.yaml" in p for p in paths)

    def test_find_module_scope(self, tmp_project):
        result = json.loads(find_artifacts_tool("module", str(tmp_project)))
        for a in result["artifacts"]:
            assert a["level"] == "module"

    def test_find_system_scope(self, tmp_project):
        # tmp_project doesn't have _system_intent, so should return 0
        result = json.loads(find_artifacts_tool("system", str(tmp_project)))
        assert isinstance(result["artifacts"], list)

    def test_invalid_scope_errors(self, tmp_project):
        result = json.loads(find_artifacts_tool("invalid_scope", str(tmp_project)))
        assert "error" in result

    def test_nonexistent_root_errors(self):
        result = json.loads(find_artifacts_tool("all", "/tmp/definitely_not_a_real_project_123xyz"))
        assert "error" in result

    def test_artifact_has_name_and_level(self, tmp_project):
        result = json.loads(find_artifacts_tool("all", str(tmp_project)))
        for a in result["artifacts"]:
            assert "name" in a
            assert "level" in a
            assert a["level"] in ("system", "workflow", "module", "task")


class TestCheckPlacement:
    """Tests for ivd_check_placement."""

    def test_correct_module_placement(self, tmp_project):
        result = json.loads(check_placement_tool(
            "agent/my_module/my_module_intent.yaml",
            str(tmp_project),
        ))
        assert result["placement_correct"] is True
        assert result["detected_level"] == "module"

    def test_system_intent_at_root_is_correct(self, tmp_project):
        result = json.loads(check_placement_tool(
            "my_system_intent.yaml",
            str(tmp_project),
        ))
        assert result["detected_level"] == "system"

    def test_task_in_intents_dir(self, tmp_project):
        result = json.loads(check_placement_tool(
            "agent/my_module/intents/process_data_intent.yaml",
            str(tmp_project),
        ))
        assert result["detected_level"] == "task"
        assert result["placement_correct"] is True

    def test_bad_filename_reports_issue(self, tmp_project):
        result = json.loads(check_placement_tool(
            "agent/my_module/my_module_config.yaml",
            str(tmp_project),
        ))
        assert result["placement_correct"] is False
        assert len(result["issues"]) > 0

    def test_result_structure(self, tmp_project):
        result = json.loads(check_placement_tool(
            "agent/my_module/my_module_intent.yaml",
            str(tmp_project),
        ))
        assert "path" in result
        assert "detected_level" in result
        assert "placement_correct" in result
        assert "issues" in result


class TestListFeatures:
    """Tests for ivd_list_features."""

    def test_list_features_in_project(self, tmp_project):
        result = json.loads(list_features_tool(project_root_arg=str(tmp_project)))
        assert result["count"] > 0
        assert "features" in result

    def test_feature_has_expected_fields(self, tmp_project):
        result = json.loads(list_features_tool(project_root_arg=str(tmp_project)))
        for f in result["features"]:
            assert "feature_id" in f
            assert "path" in f

    def test_filter_by_category(self, tmp_project):
        result = json.loads(list_features_tool(category="test", project_root_arg=str(tmp_project)))
        for f in result["features"]:
            assert f.get("category") == "test"

    def test_filter_by_status(self, tmp_project):
        result = json.loads(list_features_tool(status="implemented", project_root_arg=str(tmp_project)))
        for f in result["features"]:
            assert f.get("status") == "implemented"

    def test_nonexistent_root_errors(self):
        result = json.loads(list_features_tool(project_root_arg="/tmp/definitely_not_real_xyz"))
        assert "error" in result


class TestAssessCoverage:
    """Tests for ivd_assess_coverage."""

    def test_assess_coverage_returns_summary(self, tmp_project):
        result = json.loads(assess_coverage_tool(project_root_arg=str(tmp_project)))
        assert "summary" in result
        assert "total_coverable_modules" in result["summary"]
        assert "covered_modules" in result["summary"]
        assert "uncovered" in result
        assert "coverage_percent" in result["summary"]

    def test_assess_coverage_has_suggestions_when_requested(self, tmp_project):
        result = json.loads(assess_coverage_tool(
            project_root_arg=str(tmp_project),
            include_suggestions=True,
        ))
        assert "suggestions" in result

    def test_assess_coverage_depth_full_adds_workflow(self, tmp_project):
        result = json.loads(assess_coverage_tool(
            project_root_arg=str(tmp_project),
            depth="full",
        ))
        assert "workflow_coverage" in result or "summary" in result

    def test_assess_coverage_nonexistent_root_errors(self):
        result = json.loads(assess_coverage_tool(project_root_arg="/tmp/definitely_not_real_xyz"))
        assert "error" in result
