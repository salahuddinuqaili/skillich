"""Explore roles, skills, and proficiency levels from the skillich taxonomy.

This is the primary skill for AI agents to query the skillich knowledge base.
Use this to answer questions about roles, required skills, career levels,
and skill definitions across all tech functions.
"""

from typing import Any, Dict, List, Optional

from core.base import Skill, SkillResult, SkillStatus
from core.taxonomy import TaxonomyLoader


class RoleExplorerSkill(Skill):

    def __init__(self, taxonomy_dir: str = "taxonomy", loader: Optional[TaxonomyLoader] = None):
        self._loader = loader or TaxonomyLoader(taxonomy_dir)

    @property
    def name(self) -> str:
        return "role_explorer"

    @property
    def description(self) -> str:
        return (
            "Explore the skillich taxonomy of tech roles and skills. "
            "Use action='list_functions' to see all function categories. "
            "Use action='list_roles' with function_id to see roles in a function. "
            "Use action='get_role' with function_id and role_id to see full role details "
            "including skills, proficiency levels, and AI impact analysis. "
            "Use action='search_skills' with query to find skills across all roles. "
            "Use action='stats' to get taxonomy statistics."
        )

    @property
    def tags(self) -> List[str]:
        return ["taxonomy", "roles", "skills", "career", "exploration"]

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_functions", "list_roles", "get_role", "search_skills", "stats"],
                    "description": "The exploration action to perform.",
                },
                "function_id": {
                    "type": "string",
                    "description": "Function ID (e.g., 'engineering', 'product', 'design'). Required for list_roles and get_role.",
                },
                "role_id": {
                    "type": "string",
                    "description": "Role ID (e.g., 'backend', 'product_manager'). Required for get_role.",
                },
                "query": {
                    "type": "string",
                    "description": "Search query for search_skills action.",
                },
            },
            "required": ["action"],
        }

    def execute(self, action: str, **kwargs) -> SkillResult:
        if action == "list_functions":
            return self._list_functions()
        elif action == "list_roles":
            return self._list_roles(kwargs.get("function_id", ""))
        elif action == "get_role":
            return self._get_role(kwargs.get("function_id", ""), kwargs.get("role_id", ""))
        elif action == "search_skills":
            return self._search_skills(kwargs.get("query", ""))
        elif action == "stats":
            return SkillResult(status=SkillStatus.SUCCESS, data=self._loader.stats)
        else:
            return SkillResult(status=SkillStatus.ERROR, error=f"Unknown action: {action}")

    def _list_functions(self) -> SkillResult:
        functions = []
        for f in self._loader.list_functions():
            functions.append({
                "id": f.id,
                "name": f.name,
                "description": f.description.strip(),
                "role_count": len(f.roles),
            })
        return SkillResult(status=SkillStatus.SUCCESS, data={"functions": functions})

    def _list_roles(self, function_id: str) -> SkillResult:
        if not function_id:
            return SkillResult(status=SkillStatus.ERROR, error="function_id is required for list_roles")
        roles = self._loader.list_roles(function_id)
        if not roles:
            available = [f.id for f in self._loader.list_functions()]
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Function '{function_id}' not found. Available: {available}",
            )
        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={
                "function_id": function_id,
                "roles": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "also_known_as": r.also_known_as,
                        "skill_count": len(r.skills),
                        "ai_impact_level": r.ai_impact.level,
                    }
                    for r in roles
                ],
            },
        )

    def _get_role(self, function_id: str, role_id: str) -> SkillResult:
        if not function_id or not role_id:
            return SkillResult(
                status=SkillStatus.ERROR,
                error="Both function_id and role_id are required for get_role",
            )
        role = self._loader.get_role(function_id, role_id)
        if not role:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Role '{role_id}' not found in function '{function_id}'.",
            )
        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={
                "id": role.id,
                "name": role.name,
                "description": role.description.strip(),
                "also_known_as": role.also_known_as,
                "ai_impact": {
                    "level": role.ai_impact.level,
                    "summary": role.ai_impact.summary.strip(),
                    "automating": role.ai_impact.automating,
                    "augmenting": role.ai_impact.augmenting,
                    "preserving": role.ai_impact.preserving,
                },
                "levels": [
                    {"id": lvl.id, "name": lvl.name, "years": lvl.years_experience, "summary": lvl.summary}
                    for lvl in role.levels
                ],
                "skills": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "category": s.category,
                        "description": s.description,
                        "ai_impact_rating": s.ai_impact_rating,
                        "proficiency": s.proficiency,
                    }
                    for s in role.skills
                ],
            },
        )

    def _search_skills(self, query: str) -> SkillResult:
        if not query:
            return SkillResult(status=SkillStatus.ERROR, error="query is required for search_skills")
        results = self._loader.search_skills(query)
        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={
                "query": query,
                "count": len(results),
                "skills": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "category": s.category,
                        "description": s.description,
                        "ai_impact_rating": s.ai_impact_rating,
                    }
                    for s in results[:50]  # Limit to 50 results
                ],
            },
        )
