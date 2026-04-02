"""Analyze AI impact on roles and skills from the skillich taxonomy.

Use this skill to understand how AI is transforming specific roles, which
skills are most/least automatable, and what practitioners should focus on.
"""

from typing import Any, Dict, List, Optional

from core.base import Skill, SkillResult, SkillStatus
from core.taxonomy import TaxonomyLoader


class AIImpactAnalyzerSkill(Skill):

    def __init__(self, taxonomy_dir: str = "taxonomy", loader: Optional[TaxonomyLoader] = None):
        self._loader = loader or TaxonomyLoader(taxonomy_dir)

    @property
    def name(self) -> str:
        return "ai_impact_analyzer"

    @property
    def description(self) -> str:
        return (
            "Analyze how AI impacts tech roles and skills. "
            "Use action='role_impact' to get the AI impact breakdown for a specific role. "
            "Use action='most_automatable' to find the skills most likely to be automated. "
            "Use action='most_resilient' to find skills most resistant to AI automation. "
            "Use action='compare_roles' to compare AI impact across roles in a function."
        )

    @property
    def tags(self) -> List[str]:
        return ["taxonomy", "ai", "impact", "automation", "career"]

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["role_impact", "most_automatable", "most_resilient", "compare_roles"],
                    "description": "The analysis action to perform.",
                },
                "function_id": {
                    "type": "string",
                    "description": "Function ID (e.g., 'engineering'). Required for role_impact and compare_roles.",
                },
                "role_id": {
                    "type": "string",
                    "description": "Role ID. Required for role_impact.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results for most_automatable/most_resilient (default 20).",
                },
            },
            "required": ["action"],
        }

    def execute(self, action: str, **kwargs) -> SkillResult:
        if action == "role_impact":
            return self._role_impact(kwargs.get("function_id", ""), kwargs.get("role_id", ""))
        elif action == "most_automatable":
            return self._by_impact(high=True, limit=kwargs.get("limit", 20))
        elif action == "most_resilient":
            return self._by_impact(high=False, limit=kwargs.get("limit", 20))
        elif action == "compare_roles":
            return self._compare_roles(kwargs.get("function_id", ""))
        else:
            return SkillResult(status=SkillStatus.ERROR, error=f"Unknown action: {action}")

    def _role_impact(self, function_id: str, role_id: str) -> SkillResult:
        summary = self._loader.get_role_ai_summary(function_id, role_id)
        if not summary:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Role '{role_id}' not found in '{function_id}'.",
            )
        role = self._loader.get_role(function_id, role_id)
        skills_ranked = sorted(role.skills, key=lambda s: s.ai_impact_rating, reverse=True)
        summary["skills_by_automation_risk"] = [
            {"name": s.name, "rating": s.ai_impact_rating, "detail": s.ai_impact_detail}
            for s in skills_ranked
        ]
        return SkillResult(status=SkillStatus.SUCCESS, data=summary)

    def _by_impact(self, high: bool, limit: int) -> SkillResult:
        all_skills = []
        for func in self._loader.list_functions():
            for role in func.roles:
                for skill in role.skills:
                    all_skills.append({
                        "skill": skill.name,
                        "role": role.name,
                        "function": func.name,
                        "rating": skill.ai_impact_rating,
                        "detail": skill.ai_impact_detail,
                    })
        all_skills.sort(key=lambda s: s["rating"], reverse=high)
        label = "most_automatable" if high else "most_resilient"
        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={"analysis": label, "skills": all_skills[:limit]},
        )

    def _compare_roles(self, function_id: str) -> SkillResult:
        if not function_id:
            return SkillResult(
                status=SkillStatus.ERROR,
                error="function_id is required for compare_roles",
            )
        roles = self._loader.list_roles(function_id)
        if not roles:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Function '{function_id}' not found.",
            )
        comparison = []
        for role in roles:
            avg_impact = (
                sum(s.ai_impact_rating for s in role.skills) / len(role.skills)
                if role.skills else 0.0
            )
            comparison.append({
                "role": role.name,
                "ai_impact_level": role.ai_impact.level,
                "avg_skill_automation": round(avg_impact, 2),
                "skill_count": len(role.skills),
                "most_automatable_skill": max(role.skills, key=lambda s: s.ai_impact_rating).name if role.skills else None,
                "most_resilient_skill": min(role.skills, key=lambda s: s.ai_impact_rating).name if role.skills else None,
            })
        comparison.sort(key=lambda r: r["avg_skill_automation"], reverse=True)
        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={"function": function_id, "roles": comparison},
        )
