# mcp_server/tests/unit/test_inversions.py

"""Unit tests for ivd_propose_inversions tool."""

import json

from mcp_server.tools.inversions import propose_inversions_tool


class TestProposeInversions:
    """Tests for ivd_propose_inversions."""

    def test_returns_valid_json(self):
        result = propose_inversions_tool("How to handle CSV export for large files")
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_contains_inversion_scaffold(self):
        data = json.loads(propose_inversions_tool("CSV export for large files"))
        assert "inversion_opportunities" in data
        opp = data["inversion_opportunities"]
        assert "problem" in opp
        assert "dominant_belief" in opp
        assert "proposed_inversions" in opp

    def test_problem_captured(self):
        problem = "How to handle user authentication securely"
        data = json.loads(propose_inversions_tool(problem))
        assert data["inversion_opportunities"]["problem"] == problem

    def test_domain_context_captured(self):
        data = json.loads(propose_inversions_tool("file processing", domain_context="data_export"))
        assert data["inversion_opportunities"]["domain_context"] == "data_export"

    def test_domain_context_optional(self):
        data = json.loads(propose_inversions_tool("some problem"))
        assert "domain_context" in data["inversion_opportunities"]

    def test_contains_guidance(self):
        data = json.loads(propose_inversions_tool("test problem"))
        assert "guidance" in data
        assert "principle_8_steps" in data["guidance"]
        assert len(data["guidance"]["principle_8_steps"]) == 4

    def test_guidance_has_schema(self):
        data = json.loads(propose_inversions_tool("test problem"))
        schema = data["guidance"]["proposed_inversions_schema"]
        assert "name" in schema
        assert "description" in schema
        assert "status" in schema
