"""Taxonomy loader: parses YAML skill taxonomy files into queryable dataclasses."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class TaxonomySkill:
    """A single skill within a role, with proficiency levels and AI impact."""
    id: str
    name: str
    category: str
    description: str
    proficiency: Dict[str, str]
    ai_impact_rating: float
    ai_impact_detail: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaxonomySkill":
        ai = data.get("ai_impact", {})
        return cls(
            id=data["id"],
            name=data["name"],
            category=data.get("category", "technical"),
            description=data.get("description", ""),
            proficiency=data.get("proficiency", {}),
            ai_impact_rating=ai.get("rating", 0.5),
            ai_impact_detail=ai.get("detail", ""),
        )


@dataclass
class TaxonomyLevel:
    """A career level within a role (e.g., junior, mid, senior)."""
    id: str
    name: str
    years_experience: str
    summary: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaxonomyLevel":
        return cls(
            id=data["id"],
            name=data["name"],
            years_experience=data.get("years_experience", ""),
            summary=data.get("summary", ""),
        )


@dataclass
class RoleAIImpact:
    """AI impact analysis for a role."""
    level: str
    summary: str
    automating: List[str]
    augmenting: List[str]
    preserving: List[str]
    sources: List[Dict[str, str]]
    last_reviewed: str = ""
    confidence: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoleAIImpact":
        return cls(
            level=data.get("level", "moderate"),
            summary=data.get("summary", ""),
            automating=data.get("automating", []),
            augmenting=data.get("augmenting", []),
            preserving=data.get("preserving", []),
            sources=data.get("sources", []),
            last_reviewed=data.get("last_reviewed", ""),
            confidence=data.get("confidence", ""),
        )


@dataclass
class TaxonomyRole:
    """A role within a function (e.g., Backend Engineer within Engineering)."""
    id: str
    function_id: str
    name: str
    also_known_as: List[str]
    description: str
    levels: List[TaxonomyLevel]
    skills: List[TaxonomySkill]
    ai_impact: RoleAIImpact

    @classmethod
    def from_dict(cls, data: Dict[str, Any], function_id: str) -> "TaxonomyRole":
        role = data["role"]
        return cls(
            id=role["id"],
            function_id=function_id,
            name=role["name"],
            also_known_as=role.get("also_known_as", []),
            description=role.get("description", ""),
            levels=[TaxonomyLevel.from_dict(lvl) for lvl in role.get("levels", [])],
            skills=[TaxonomySkill.from_dict(s) for s in role.get("skills", [])],
            ai_impact=RoleAIImpact.from_dict(role.get("ai_impact", {})),
        )


@dataclass
class TaxonomyFunction:
    """A top-level function (e.g., Engineering, Product, Design)."""
    id: str
    name: str
    description: str
    roles: List[TaxonomyRole] = field(default_factory=list)
    sources: List[Dict[str, str]] = field(default_factory=list)


class TaxonomyLoader:
    """Loads YAML taxonomy files and provides query methods.

    Usage:
        loader = TaxonomyLoader("taxonomy")
        functions = loader.list_functions()
        role = loader.get_role("engineering", "backend")
    """

    def __init__(self, taxonomy_dir: str = "taxonomy"):
        self._functions: Dict[str, TaxonomyFunction] = {}
        self._load(taxonomy_dir)

    def _load(self, taxonomy_dir: str) -> None:
        base = Path(taxonomy_dir)
        if not base.exists():
            return

        for func_dir in sorted(base.iterdir()):
            if not func_dir.is_dir() or func_dir.name.startswith("_"):
                continue

            func_meta_path = func_dir / "_function.yaml"
            if not func_meta_path.exists():
                continue

            with open(func_meta_path, "r", encoding="utf-8") as f:
                func_data = yaml.safe_load(f)

            func_info = func_data.get("function", {})
            function = TaxonomyFunction(
                id=func_info.get("id", func_dir.name),
                name=func_info.get("name", func_dir.name.title()),
                description=func_info.get("description", ""),
                sources=func_info.get("sources", []),
            )

            for role_file in sorted(func_dir.glob("*.yaml")):
                if role_file.name.startswith("_"):
                    continue

                with open(role_file, "r", encoding="utf-8") as f:
                    role_data = yaml.safe_load(f)

                if role_data and "role" in role_data:
                    role = TaxonomyRole.from_dict(role_data, function.id)
                    function.roles.append(role)

            self._functions[function.id] = function

    # -- Query methods --

    def list_functions(self) -> List[TaxonomyFunction]:
        """Return all loaded functions."""
        return list(self._functions.values())

    def get_function(self, function_id: str) -> Optional[TaxonomyFunction]:
        """Get a function by ID."""
        return self._functions.get(function_id)

    def list_roles(self, function_id: str) -> List[TaxonomyRole]:
        """List all roles within a function."""
        func = self._functions.get(function_id)
        return func.roles if func else []

    def get_role(self, function_id: str, role_id: str) -> Optional[TaxonomyRole]:
        """Get a specific role by function and role ID."""
        for role in self.list_roles(function_id):
            if role.id == role_id:
                return role
        return None

    def search_skills(self, query: str) -> List[TaxonomySkill]:
        """Search all skills across all roles by name or description (case-insensitive)."""
        query_lower = query.lower()
        results = []
        for func in self._functions.values():
            for role in func.roles:
                for skill in role.skills:
                    if query_lower in skill.name.lower() or query_lower in skill.description.lower():
                        results.append(skill)
        return results

    def get_skills_by_ai_impact(
        self, min_rating: float = 0.0, max_rating: float = 1.0
    ) -> List[TaxonomySkill]:
        """Return skills filtered by AI impact rating range."""
        results = []
        for func in self._functions.values():
            for role in func.roles:
                for skill in role.skills:
                    if min_rating <= skill.ai_impact_rating <= max_rating:
                        results.append(skill)
        return results

    def get_role_ai_summary(self, function_id: str, role_id: str) -> Optional[Dict[str, Any]]:
        """Get the AI impact summary for a specific role."""
        role = self.get_role(function_id, role_id)
        if not role:
            return None
        return {
            "role": role.name,
            "level": role.ai_impact.level,
            "summary": role.ai_impact.summary,
            "automating": role.ai_impact.automating,
            "augmenting": role.ai_impact.augmenting,
            "preserving": role.ai_impact.preserving,
            "skill_impact_avg": (
                sum(s.ai_impact_rating for s in role.skills) / len(role.skills)
                if role.skills
                else 0.0
            ),
        }

    @property
    def stats(self) -> Dict[str, int]:
        """Return counts of functions, roles, and skills."""
        total_roles = sum(len(f.roles) for f in self._functions.values())
        total_skills = sum(
            len(r.skills) for f in self._functions.values() for r in f.roles
        )
        return {
            "functions": len(self._functions),
            "roles": total_roles,
            "skills": total_skills,
        }
