"""Tests for the MCP server tool functions."""

import json

import pytest

mcp_mod = pytest.importorskip("mcp")

from mcp_server.server import (  # noqa: E402
    _registry,
    action_plan,
    analyze_ai_impact,
    explore_roles,
    mcp,
)


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

    def test_mcp_instructions_reflect_live_taxonomy(self):
        """MCP instructions must contain real counts, not stale hardcoded values."""
        from mcp_server.server import _build_instructions, _loader
        instructions = _build_instructions(_loader)
        # Must not contain the old stale numbers
        assert "38 roles" not in instructions
        assert "455 skills" not in instructions
        assert "7 tech functions" not in instructions
        # Must contain actual live counts (>= known minimums)
        import re
        functions_match = re.search(r"(\d+) functions", instructions)
        roles_match = re.search(r"(\d+) roles", instructions)
        skills_match = re.search(r"(\d+) skills", instructions)
        assert functions_match, "instructions should mention function count"
        assert roles_match, "instructions should mention role count"
        assert skills_match, "instructions should mention skill count"
        assert int(functions_match.group(1)) >= 17
        assert int(roles_match.group(1)) >= 88
        assert int(skills_match.group(1)) >= 1000

    def test_mcp_server_has_correct_name(self):
        assert mcp.name == "skillich"


class TestActionPlanTool:
    """`action_plan` is the one-call answer to 'what does AI mean for my job?'."""

    def test_plan_from_a_plain_job_title(self):
        data = json.loads(action_plan(job_title="electrician"))
        assert data["ok"] is True
        plan = data["data"]
        assert plan["role_name"] == "Electrician"
        assert plan["invest"], "electrician should have resilient skills"
        assert plan["share_url"].endswith(plan["share_path"])
        assert plan["available_levels"]

    def test_plan_honours_an_explicit_level(self):
        data = json.loads(action_plan(job_title="pm", level="senior"))
        assert data["data"]["level_id"] == "senior"

    def test_plan_from_explicit_ids(self):
        data = json.loads(action_plan(function_id="engineering", role_id="backend"))
        assert data["ok"] is True
        assert data["data"]["role_name"] == "Backend Engineer"

    def test_ambiguous_title_returns_candidates_instead_of_guessing(self):
        data = json.loads(action_plan(job_title="engineer"))
        assert data["ok"] is False
        assert "ambiguous" in data["error"]
        assert len(data["candidates"]) > 1

    def test_unknown_title_is_an_honest_miss(self):
        data = json.loads(action_plan(job_title="astronaut"))
        assert data["ok"] is False
        assert "No role matches" in data["error"]

    def test_no_arguments_explains_what_is_needed(self):
        data = json.loads(action_plan())
        assert data["ok"] is False
        assert "job_title" in data["error"]

    def test_transitions_are_opt_in(self):
        without = json.loads(action_plan(job_title="pm"))["data"]
        assert without["transitions"] == []
        with_ = json.loads(action_plan(job_title="pm", include_transitions=True))["data"]
        assert with_["transitions"]

    def test_tool_is_registered_with_the_server(self):
        import asyncio

        names = {t.name for t in asyncio.run(mcp.list_tools())}
        assert "action_plan" in names
