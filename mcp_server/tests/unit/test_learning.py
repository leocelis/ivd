# mcp_server/tests/unit/test_learning.py

"""Unit tests for ivd_discover_goal and ivd_teach_concept tools."""

import json

import yaml

from mcp_server.tools.learning import discover_goal_tool, teach_concept_tool


class TestDiscoverGoal:
    """Tests for ivd_discover_goal."""

    def test_returns_valid_json(self):
        result = discover_goal_tool()
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_contains_candidates(self):
        data = json.loads(discover_goal_tool())
        assert "candidate_directions" in data
        assert len(data["candidate_directions"]) > 0
        assert len(data["candidate_directions"]) <= 3

    def test_each_candidate_has_fields(self):
        data = json.loads(discover_goal_tool())
        for c in data["candidate_directions"]:
            assert "direction" in c
            assert "best_for" in c
            assert "next_step" in c

    def test_domain_context_included(self):
        data = json.loads(discover_goal_tool(domain_or_context="data_export"))
        assert "context_used" in data
        assert data["context_used"]["domain_or_context"] == "data_export"

    def test_user_hint_included(self):
        data = json.loads(discover_goal_tool(user_hint="something for compliance"))
        assert "context_used" in data
        assert data["context_used"]["user_hint"] == "something for compliance"

    def test_no_context_no_context_field(self):
        data = json.loads(discover_goal_tool())
        assert "context_used" not in data

    def test_project_root_augments_candidates(self, tmp_project):
        data = json.loads(discover_goal_tool(project_root=str(tmp_project)))
        # With a project root, may include existing feature candidates
        assert "candidate_directions" in data


class TestTeachConcept:
    """Tests for ivd_teach_concept."""

    def test_returns_valid_yaml(self):
        result = teach_concept_tool("ETL")
        data = yaml.safe_load(result)
        assert isinstance(data, dict)

    def test_etl_has_structured_content(self):
        data = yaml.safe_load(teach_concept_tool("ETL"))
        education = data["education"]
        assert "concept" in education
        assert "ETL" in education["concept"]
        assert "key_concepts" in education
        assert len(education["key_concepts"]) >= 3  # Extract, Transform, Load

    def test_unknown_concept_returns_template(self):
        data = yaml.safe_load(teach_concept_tool("Saga pattern"))
        education = data["education"]
        assert "concept" in education
        assert education["concept"] == "Saga pattern"
        # Should have placeholder content
        assert "key_concepts" in education

    def test_user_context_captured(self):
        data = yaml.safe_load(teach_concept_tool("CDC", user_context="syncing Salesforce"))
        education = data["education"]
        assert "why_it_matters_here" in education

    def test_has_meta(self):
        data = yaml.safe_load(teach_concept_tool("ETL"))
        assert "meta" in data
        assert "principle" in data["meta"]
        assert "Principle 6" in data["meta"]["principle"]

    def test_has_verification_questions(self):
        data = yaml.safe_load(teach_concept_tool("ETL"))
        education = data["education"]
        assert "verification" in education
        assert len(education["verification"]) > 0
        for v in education["verification"]:
            assert "question" in v
            assert "answer" in v

    def test_has_next_steps(self):
        data = yaml.safe_load(teach_concept_tool("ETL"))
        education = data["education"]
        assert "next_steps" in education
