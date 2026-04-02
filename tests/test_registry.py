"""Tests for core.registry module."""

import pytest

from core.base import SkillResult


class TestRegistration:
    def test_register_and_retrieve(self, registry, dummy_skill):
        registry.register(dummy_skill)
        assert registry.get_skill("dummy") is dummy_skill

    def test_duplicate_registration_raises(self, registry, dummy_skill):
        registry.register(dummy_skill)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(dummy_skill)

    def test_get_nonexistent_returns_none(self, registry):
        assert registry.get_skill("nonexistent") is None

    def test_list_skills(self, populated_registry):
        skills = populated_registry.list_skills()
        names = {s.name for s in skills}
        assert "calculator" in names
        assert "dummy" in names

    def test_get_skills_by_tag(self, populated_registry):
        math_skills = populated_registry.get_skills_by_tag("math")
        assert len(math_skills) == 1
        assert math_skills[0].name == "calculator"


class TestExecution:
    def test_call_skill_success(self, populated_registry):
        result = populated_registry.call_skill("calculator", operation="add", a=2, b=3)
        assert isinstance(result, SkillResult)
        assert result.ok
        assert result.data["result"] == 5
        assert result.duration_ms is not None

    def test_call_skill_not_found(self, registry):
        result = registry.call_skill("nonexistent")
        assert not result.ok
        assert "not found" in result.error

    def test_call_skill_validation_error(self, populated_registry):
        result = populated_registry.call_skill("calculator", operation="add", a=2)
        assert not result.ok
        assert "Missing required" in result.error

    def test_call_skill_invalid_enum(self, populated_registry):
        result = populated_registry.call_skill("calculator", operation="sqrt", a=4, b=0)
        assert not result.ok

    def test_call_skill_handles_exception(self, populated_registry):
        result = populated_registry.call_skill("dummy")
        assert not result.ok
        assert "Missing required" in result.error


class TestExport:
    def test_to_openai_tools(self, populated_registry):
        tools = populated_registry.to_openai_tools()
        assert len(tools) == 2
        assert all(t["type"] == "function" for t in tools)

    def test_to_anthropic_tools(self, populated_registry):
        tools = populated_registry.to_anthropic_tools()
        assert len(tools) == 2
        assert all("input_schema" in t for t in tools)

    def test_to_mcp_tools(self, populated_registry):
        tools = populated_registry.to_mcp_tools()
        assert len(tools) == 2
        assert all("inputSchema" in t for t in tools)
