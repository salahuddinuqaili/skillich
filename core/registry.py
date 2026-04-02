"""Skill registry for discovering, loading, and executing skills."""

import importlib
import inspect
import pkgutil
import time
from pathlib import Path
from typing import Dict, List, Optional

from core.base import Skill, SkillResult, SkillStatus
from core.validation import validate_parameters


class SkillRegistry:
    """Central registry for managing skills.

    Handles registration, discovery, validation, and execution of skills.
    Exports skill definitions in OpenAI, Anthropic, and MCP formats.
    """

    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """Register a skill. Raises ValueError if the name is already taken."""
        if skill.name in self._skills:
            raise ValueError(f"Skill with name '{skill.name}' is already registered.")
        self._skills[skill.name] = skill

    def get_skill(self, name: str) -> Optional[Skill]:
        """Retrieve a skill by name, or None if not found."""
        return self._skills.get(name)

    def list_skills(self) -> List[Skill]:
        """Return all registered skills."""
        return list(self._skills.values())

    def get_skills_by_tag(self, tag: str) -> List[Skill]:
        """Return all skills that have the given tag."""
        return [s for s in self._skills.values() if tag in s.tags]

    def call_skill(self, name: str, **kwargs) -> SkillResult:
        """Execute a skill by name with validation and timing.

        Validates parameters against the skill's JSON schema before execution.
        Returns a SkillResult with timing metadata.
        """
        skill = self.get_skill(name)
        if not skill:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Skill '{name}' not found. Available: {list(self._skills.keys())}",
            )

        validation_errors = validate_parameters(skill.parameters, kwargs)
        if validation_errors:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Validation failed: {'; '.join(validation_errors)}",
            )

        start = time.perf_counter()
        try:
            result = skill.execute(**kwargs)
            elapsed = (time.perf_counter() - start) * 1000

            if isinstance(result, SkillResult):
                result.duration_ms = elapsed
                return result

            return SkillResult(
                status=SkillStatus.SUCCESS,
                data=result,
                duration_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"{type(e).__name__}: {e}",
                duration_ms=elapsed,
            )

    def auto_discover(self, package_path: str = "skills") -> int:
        """Scan a package directory for Skill subclasses and register them.

        Returns the number of skills discovered and registered.
        """
        count = 0
        base_path = Path(package_path)

        if not base_path.exists():
            return 0

        for importer, module_name, is_pkg in pkgutil.walk_packages(
            path=[str(base_path)],
            prefix=f"{package_path}.",
        ):
            try:
                module = importlib.import_module(module_name)
            except Exception:
                continue

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, Skill)
                    and obj is not Skill
                    and not inspect.isabstract(obj)
                    and obj.__module__ == module.__name__
                ):
                    try:
                        instance = obj()
                        if instance.name not in self._skills:
                            self.register(instance)
                            count += 1
                    except Exception:
                        continue

        return count

    # -- Export methods --

    def to_openai_tools(self) -> List[Dict]:
        """Export all skills as OpenAI tool definitions."""
        return [skill.to_openai_tool() for skill in self._skills.values()]

    def to_anthropic_tools(self) -> List[Dict]:
        """Export all skills as Anthropic tool_use definitions."""
        return [skill.to_anthropic_tool() for skill in self._skills.values()]

    def to_mcp_tools(self) -> List[Dict]:
        """Export all skills as MCP tool definitions."""
        return [skill.to_mcp_tool() for skill in self._skills.values()]
