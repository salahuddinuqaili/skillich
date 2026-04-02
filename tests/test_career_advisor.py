"""Tests for the career advisor skill."""

from core.taxonomy import TaxonomyLoader
from skills.taxonomy_skills.career_advisor import CareerAdvisorSkill


class TestCareerAdvisor:

    def setup_method(self):
        self.loader = TaxonomyLoader("taxonomy")
        self.skill = CareerAdvisorSkill(loader=self.loader)

    def test_find_transitions(self):
        result = self.skill.execute(
            action="find_transitions",
            source_function_id="engineering",
            source_role_id="backend",
        )
        assert result.ok
        transitions = result.data["transitions"]
        assert len(transitions) > 0
        # Full-stack should be a top transition from backend
        top_roles = [t["role_id"] for t in transitions[:5]]
        assert "fullstack" in top_roles

    def test_find_transitions_missing_args(self):
        result = self.skill.execute(action="find_transitions")
        assert not result.ok

    def test_find_transitions_invalid_role(self):
        result = self.skill.execute(
            action="find_transitions",
            source_function_id="engineering",
            source_role_id="nonexistent",
        )
        assert not result.ok

    def test_transferable_skills(self):
        result = self.skill.execute(
            action="transferable_skills",
            function_id="engineering",
            role_id="backend",
        )
        assert result.ok
        skills = result.data["skills"]
        assert len(skills) > 0
        # Each skill should have appears_in_roles count
        assert all("appears_in_roles" in s for s in skills)

    def test_skill_overlap(self):
        result = self.skill.execute(
            action="skill_overlap",
            source_function_id="engineering",
            source_role_id="backend",
            target_function_id="engineering",
            target_role_id="fullstack",
        )
        assert result.ok
        data = result.data
        assert "shared_skills" in data
        assert "source_only" in data
        assert "target_only" in data

    def test_universal_skills(self):
        result = self.skill.execute(action="universal_skills", limit=5)
        assert result.ok
        skills = result.data["skills"]
        assert len(skills) <= 5
        # Universal skills appear in 2+ roles
        assert all(s["appears_in_roles"] >= 2 for s in skills)

    def test_skill_similarity(self):
        sim = self.skill._skill_similarity("System Design & Architecture", "System Design")
        assert sim > 0.5

        sim2 = self.skill._skill_similarity("Python Programming", "JavaScript Development")
        assert sim2 < 0.5


class TestContentValidator:

    def test_content_report(self):
        from core.content_validator import validate_content
        report = validate_content("taxonomy")
        assert report.stats["roles_checked"] >= 38
        assert report.stats["total_skills"] >= 455
