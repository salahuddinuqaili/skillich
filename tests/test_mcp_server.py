"""Tests for the MCP server tool functions."""

import json

import pytest

mcp_mod = pytest.importorskip("mcp")

from mcp_server.server import _registry, mcp, explore_roles, analyze_ai_impact  # noqa: E402


class TestMCPTools:
    """Test MCP tool wrappers against the real taxonomy."""

    def test_explore_list_functions(self):
        raw = explore_roles(action="list_functions")
        data = json.loads(raw)
        assert data["status"] == "success"
        assert len(data["data"]["functions"]) >= 7

    def test_explore_list_roles(self):
        raw = explore_roles(action="list_roles", function_id="engineering")
        data = json.loads(raw)
        assert data["status"] == "success"
        assert len(data["data"]["roles"]) >= 10

    def test_explore_get_role(self):
        raw = explore_roles(action="get_role", function_id="engineering", role_id="backend")
        data = json.loads(raw)
        assert data["status"] == "success"
        assert data["data"]["name"] == "Backend Engineer"
        assert len(data["data"]["skills"]) > 0

    def test_explore_search_skills(self):
        raw = explore_roles(action="search_skills", query="system design")
        data = json.loads(raw)
        assert data["status"] == "success"
        assert data["data"]["count"] > 0

    def test_explore_stats(self):
        raw = explore_roles(action="stats")
        data = json.loads(raw)
        assert data["status"] == "success"
        assert data["data"]["functions"] >= 7
        assert data["data"]["roles"] >= 38

    def test_explore_invalid_function(self):
        raw = explore_roles(action="list_roles", function_id="nonexistent")
        data = json.loads(raw)
        assert data["status"] == "error"

    def test_analyze_most_resilient(self):
        raw = analyze_ai_impact(action="most_resilient", limit=5)
        data = json.loads(raw)
        assert data["status"] == "success"
        assert len(data["data"]["skills"]) <= 5

    def test_analyze_most_automatable(self):
        raw = analyze_ai_impact(action="most_automatable", limit=5)
        data = json.loads(raw)
        assert data["status"] == "success"
        assert len(data["data"]["skills"]) <= 5

    def test_analyze_compare_roles(self):
        raw = analyze_ai_impact(action="compare_roles", function_id="engineering")
        data = json.loads(raw)
        assert data["status"] == "success"

    def test_analyze_role_impact(self):
        raw = analyze_ai_impact(
            action="role_impact", function_id="engineering", role_id="backend"
        )
        data = json.loads(raw)
        assert data["status"] == "success"

    def test_registry_has_all_skills(self):
        names = [s.name for s in _registry.list_skills()]
        assert "role_explorer" in names
        assert "ai_impact_analyzer" in names
        assert "skill_assessor" in names
        assert "learning_path" in names

    def test_mcp_server_has_name(self):
        assert mcp.name == "skillich"
