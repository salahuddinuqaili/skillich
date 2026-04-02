"""Assess a person's skills against the skillich taxonomy.

Use this skill to evaluate proficiency levels, identify gaps, and recommend
focus areas for career development.
"""

from typing import Any, Dict, List, Optional

from core.base import Skill, SkillResult, SkillStatus
from core.taxonomy import TaxonomyLoader


LEVEL_ORDER = {"junior": 1, "mid": 2, "senior": 3, "staff": 4, "principal": 5}


class SkillAssessorSkill(Skill):

    def __init__(self, taxonomy_dir: str = "taxonomy", loader: Optional[TaxonomyLoader] = None):
        self._loader = loader or TaxonomyLoader(taxonomy_dir)

    @property
    def name(self) -> str:
        return "skill_assessor"

    @property
    def description(self) -> str:
        return (
            "Assess a person's skills against a target role in the skillich taxonomy. "
            "Provide a list of skill assessments (skill_id and current_level) along with "
            "the target role (function_id and role_id) and target level. Returns a gap "
            "analysis showing which skills need development and which exceed expectations."
        )

    @property
    def tags(self) -> List[str]:
        return ["taxonomy", "assessment", "career", "gap-analysis"]

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "function_id": {
                    "type": "string",
                    "description": "Target function (e.g., 'engineering').",
                },
                "role_id": {
                    "type": "string",
                    "description": "Target role (e.g., 'backend').",
                },
                "target_level": {
                    "type": "string",
                    "enum": ["junior", "mid", "senior", "staff", "principal"],
                    "description": "The proficiency level to assess against.",
                },
                "assessments": {
                    "type": "array",
                    "description": "List of {skill_id, current_level} objects.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "skill_id": {"type": "string"},
                            "current_level": {
                                "type": "string",
                                "enum": ["junior", "mid", "senior", "staff", "principal"],
                            },
                        },
                        "required": ["skill_id", "current_level"],
                    },
                },
            },
            "required": ["function_id", "role_id", "target_level", "assessments"],
        }

    def execute(self, function_id: str, role_id: str, target_level: str,
                assessments: List[Dict], **kwargs) -> SkillResult:
        role = self._loader.get_role(function_id, role_id)
        if not role:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Role '{role_id}' not found in '{function_id}'.",
            )

        target_num = LEVEL_ORDER.get(target_level, 3)
        assessment_map = {a["skill_id"]: a["current_level"] for a in assessments}
        gaps = []
        strengths = []
        on_track = []
        unassessed = []

        for skill in role.skills:
            if skill.id not in assessment_map:
                unassessed.append({
                    "skill": skill.name,
                    "skill_id": skill.id,
                    "target_description": skill.proficiency.get(target_level, ""),
                })
                continue

            current = assessment_map[skill.id]
            current_num = LEVEL_ORDER.get(current, 1)
            delta = current_num - target_num

            entry = {
                "skill": skill.name,
                "skill_id": skill.id,
                "current_level": current,
                "target_level": target_level,
                "delta": delta,
                "current_description": skill.proficiency.get(current, ""),
                "target_description": skill.proficiency.get(target_level, ""),
                "ai_impact_rating": skill.ai_impact_rating,
            }

            if delta < 0:
                gaps.append(entry)
            elif delta > 0:
                strengths.append(entry)
            else:
                on_track.append(entry)

        # Sort gaps by size (biggest first) then by AI resilience (invest in human skills)
        gaps.sort(key=lambda g: (g["delta"], g["ai_impact_rating"]))

        # Priority recommendations: focus on low-AI-impact gaps first (most valuable to develop)
        priority_development = [
            g for g in gaps if g["ai_impact_rating"] < 0.5
        ][:5]

        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={
                "role": role.name,
                "target_level": target_level,
                "summary": {
                    "gaps": len(gaps),
                    "on_track": len(on_track),
                    "strengths": len(strengths),
                    "unassessed": len(unassessed),
                    "total_skills": len(role.skills),
                },
                "gaps": gaps,
                "on_track": on_track,
                "strengths": strengths,
                "unassessed": unassessed,
                "priority_development": priority_development,
                "recommendation": (
                    f"Focus on {len(priority_development)} high-value gaps: "
                    f"skills with low AI automation risk that will remain valuable. "
                    f"{'Consider deprioritizing highly automatable skills.' if any(g['ai_impact_rating'] > 0.7 for g in gaps) else ''}"
                ),
            },
        )
