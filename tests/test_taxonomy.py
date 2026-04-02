"""Tests for core.taxonomy module."""

import pytest
import yaml

from core.taxonomy import TaxonomyLoader


FUNCTION_YAML = {
    "function": {
        "id": "test_func",
        "name": "Test Function",
        "description": "A test function for unit tests.",
        "roles": ["test_role"],
        "sources": [{"name": "Test Source", "url": "https://example.com"}],
    }
}

ROLE_YAML = {
    "role": {
        "id": "test_role",
        "function": "test_func",
        "name": "Test Role",
        "also_known_as": ["Tester", "QA"],
        "description": "A test role.",
        "ai_impact": {
            "level": "moderate",
            "summary": "Some tasks automatable.",
            "automating": ["Repetitive task A"],
            "augmenting": ["Complex task B"],
            "preserving": ["Creative task C"],
            "sources": [{"name": "Study X", "url": "https://example.com/study"}],
        },
        "levels": [
            {"id": "junior", "name": "Junior", "years_experience": "0-2", "summary": "Entry level."},
            {"id": "mid", "name": "Mid", "years_experience": "2-5", "summary": "Independent."},
            {"id": "senior", "name": "Senior", "years_experience": "5+", "summary": "Leads."},
        ],
        "skills": [
            {
                "id": "skill_a",
                "name": "Skill A",
                "category": "technical",
                "description": "A technical skill.",
                "proficiency": {
                    "junior": "Basic usage.",
                    "mid": "Independent usage.",
                    "senior": "Expert usage.",
                },
                "ai_impact": {"rating": 0.3, "detail": "Low automation potential."},
            },
            {
                "id": "skill_b",
                "name": "Skill B",
                "category": "communication",
                "description": "A communication skill.",
                "proficiency": {
                    "junior": "Follows scripts.",
                    "mid": "Adapts communication.",
                    "senior": "Shapes strategy.",
                },
                "ai_impact": {"rating": 0.8, "detail": "Highly automatable."},
            },
        ],
    }
}


@pytest.fixture
def taxonomy_dir(tmp_path):
    """Create a temporary taxonomy directory with test data."""
    func_dir = tmp_path / "test_func"
    func_dir.mkdir()

    with open(func_dir / "_function.yaml", "w") as f:
        yaml.dump(FUNCTION_YAML, f)

    with open(func_dir / "test_role.yaml", "w") as f:
        yaml.dump(ROLE_YAML, f)

    return str(tmp_path)


@pytest.fixture
def loader(taxonomy_dir):
    return TaxonomyLoader(taxonomy_dir)


class TestTaxonomyLoader:
    def test_loads_functions(self, loader):
        funcs = loader.list_functions()
        assert len(funcs) == 1
        assert funcs[0].id == "test_func"
        assert funcs[0].name == "Test Function"

    def test_get_function(self, loader):
        func = loader.get_function("test_func")
        assert func is not None
        assert func.id == "test_func"

    def test_get_function_not_found(self, loader):
        assert loader.get_function("nonexistent") is None

    def test_list_roles(self, loader):
        roles = loader.list_roles("test_func")
        assert len(roles) == 1
        assert roles[0].id == "test_role"

    def test_get_role(self, loader):
        role = loader.get_role("test_func", "test_role")
        assert role is not None
        assert role.name == "Test Role"
        assert role.also_known_as == ["Tester", "QA"]

    def test_role_levels(self, loader):
        role = loader.get_role("test_func", "test_role")
        assert len(role.levels) == 3
        assert role.levels[0].id == "junior"

    def test_role_skills(self, loader):
        role = loader.get_role("test_func", "test_role")
        assert len(role.skills) == 2
        assert role.skills[0].name == "Skill A"
        assert role.skills[0].category == "technical"

    def test_skill_proficiency(self, loader):
        role = loader.get_role("test_func", "test_role")
        skill = role.skills[0]
        assert "junior" in skill.proficiency
        assert "mid" in skill.proficiency
        assert "senior" in skill.proficiency

    def test_skill_ai_impact(self, loader):
        role = loader.get_role("test_func", "test_role")
        assert role.skills[0].ai_impact_rating == 0.3
        assert role.skills[1].ai_impact_rating == 0.8

    def test_role_ai_impact(self, loader):
        role = loader.get_role("test_func", "test_role")
        assert role.ai_impact.level == "moderate"
        assert len(role.ai_impact.automating) == 1
        assert len(role.ai_impact.augmenting) == 1
        assert len(role.ai_impact.preserving) == 1

    def test_search_skills(self, loader):
        results = loader.search_skills("technical")
        assert len(results) == 1
        assert results[0].id == "skill_a"

    def test_search_skills_case_insensitive(self, loader):
        results = loader.search_skills("COMMUNICATION")
        assert len(results) == 1

    def test_get_skills_by_ai_impact(self, loader):
        high = loader.get_skills_by_ai_impact(min_rating=0.7)
        assert len(high) == 1
        assert high[0].id == "skill_b"

        low = loader.get_skills_by_ai_impact(max_rating=0.5)
        assert len(low) == 1
        assert low[0].id == "skill_a"

    def test_role_ai_summary(self, loader):
        summary = loader.get_role_ai_summary("test_func", "test_role")
        assert summary["level"] == "moderate"
        assert summary["skill_impact_avg"] == pytest.approx(0.55)

    def test_stats(self, loader):
        s = loader.stats
        assert s["functions"] == 1
        assert s["roles"] == 1
        assert s["skills"] == 2

    def test_empty_directory(self, tmp_path):
        loader = TaxonomyLoader(str(tmp_path))
        assert loader.list_functions() == []

    def test_nonexistent_directory(self):
        loader = TaxonomyLoader("/nonexistent/path")
        assert loader.list_functions() == []
