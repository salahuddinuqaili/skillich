"""Shared test fixtures for skillich tests."""

import pytest

from core.base import Skill, SkillResult, SkillStatus
from core.registry import SkillRegistry
from skills.common.calculator import CalculatorSkill


class DummySkill(Skill):
    """Minimal skill for testing the framework."""

    @property
    def name(self) -> str:
        return "dummy"

    @property
    def description(self) -> str:
        return "A test skill that echoes input."

    @property
    def tags(self):
        return ["test"]

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message to echo."},
            },
            "required": ["message"],
        }

    def execute(self, message: str, **kwargs) -> SkillResult:
        return SkillResult(status=SkillStatus.SUCCESS, data={"echo": message})


@pytest.fixture
def dummy_skill():
    return DummySkill()


@pytest.fixture
def calculator_skill():
    return CalculatorSkill()


@pytest.fixture
def registry():
    return SkillRegistry()


@pytest.fixture
def populated_registry():
    reg = SkillRegistry()
    reg.register(CalculatorSkill())
    reg.register(DummySkill())
    return reg
