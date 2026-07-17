"""Tests for cross-function compare_roles in AIImpactAnalyzerSkill (Phase 4)."""

from pathlib import Path

import pytest

from core.taxonomy import TaxonomyLoader
from skills.taxonomy_skills.ai_impact_analyzer import AIImpactAnalyzerSkill

_TAXONOMY = str(Path(__file__).resolve().parent.parent / "taxonomy")


@pytest.fixture(scope="module")
def skill():
    loader = TaxonomyLoader(_TAXONOMY)
    return AIImpactAnalyzerSkill(loader=loader)


class TestCompareRolesSingleFunction:
    """Existing single-function behaviour must be unchanged."""

    def test_single_function_returns_roles(self, skill):
        result = skill.execute("compare_roles", function_id="engineering")
        assert result.ok
        assert "roles" in result.data
        assert len(result.data["roles"]) >= 1

    def test_single_function_scope_field(self, skill):
        result = skill.execute("compare_roles", function_id="engineering")
        assert result.ok
        assert result.data.get("scope") == "function"
        assert result.data.get("function") == "engineering"

    def test_single_function_sorted_by_automation(self, skill):
        result = skill.execute("compare_roles", function_id="engineering")
        roles = result.data["roles"]
        scores = [r["avg_skill_automation"] for r in roles]
        assert scores == sorted(scores, reverse=True)

    def test_single_function_role_has_expected_keys(self, skill):
        result = skill.execute("compare_roles", function_id="engineering")
        r = result.data["roles"][0]
        for key in ("role", "role_id", "function", "function_id",
                    "ai_impact_level", "avg_skill_automation", "skill_count"):
            assert key in r, f"missing key: {key}"

    def test_invalid_function_returns_error(self, skill):
        result = skill.execute("compare_roles", function_id="nonexistent_xyz")
        assert not result.ok
        assert "not found" in result.error.lower()


class TestCompareRolesCrossFunction:
    """New cross-function mode: no function_id → whole taxonomy."""

    def test_no_function_id_returns_all_functions(self, skill):
        result = skill.execute("compare_roles")
        assert result.ok
        functions_seen = {r["function_id"] for r in result.data["roles"]}
        # Should span more than one function
        assert len(functions_seen) > 1

    def test_cross_function_scope_field(self, skill):
        result = skill.execute("compare_roles")
        assert result.ok
        assert result.data.get("scope") == "all_functions"

    def test_cross_function_sorted_by_automation(self, skill):
        result = skill.execute("compare_roles")
        scores = [r["avg_skill_automation"] for r in result.data["roles"]]
        assert scores == sorted(scores, reverse=True)

    def test_cross_function_respects_limit(self, skill):
        result = skill.execute("compare_roles", limit=5)
        assert result.ok
        assert len(result.data["roles"]) <= 5

    def test_cross_function_default_limit(self, skill):
        result = skill.execute("compare_roles")
        assert result.ok
        assert len(result.data["roles"]) <= 20

    def test_cross_function_role_has_function_id(self, skill):
        result = skill.execute("compare_roles")
        for r in result.data["roles"]:
            assert "function_id" in r
            assert r["function_id"]  # non-empty

    def test_cross_function_includes_high_impact_roles(self, skill):
        """Top results by automation should include known high-impact functions."""
        result = skill.execute("compare_roles", limit=50)
        # marketing/creative are known high-automation functions
        functions = {r["function_id"] for r in result.data["roles"]}
        high_known = {"marketing", "creative", "legal", "sales"}
        assert functions & high_known, f"expected some high-impact function in top-50, got: {functions}"

    def test_cross_function_vs_single_consistency(self, skill):
        """A role's avg_skill_automation in cross-function == single-function mode."""
        cross = skill.execute("compare_roles", limit=100)
        single = skill.execute("compare_roles", function_id="engineering")

        cross_roles = {r["role_id"]: r for r in cross.data["roles"]}
        for r in single.data["roles"]:
            if r["role_id"] in cross_roles:
                assert cross_roles[r["role_id"]]["avg_skill_automation"] == r["avg_skill_automation"]
