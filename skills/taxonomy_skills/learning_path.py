"""Generate learning paths based on current skills and target roles.

Use this to create prioritized development plans that account for AI impact --
focusing investment on skills that will remain valuable.
"""

from typing import Any, Dict, List, Optional

from core.base import Skill, SkillResult, SkillStatus
from core.taxonomy import TaxonomyLoader


LEVEL_ORDER = {"junior": 1, "mid": 2, "senior": 3, "staff": 4, "principal": 5}
LEVEL_NAMES = {1: "junior", 2: "mid", 3: "senior", 4: "staff", 5: "principal"}


class LearningPathSkill(Skill):

    def __init__(self, taxonomy_dir: str = "taxonomy", loader: Optional[TaxonomyLoader] = None):
        self._loader = loader or TaxonomyLoader(taxonomy_dir)

    @property
    def name(self) -> str:
        return "learning_path"

    @property
    def description(self) -> str:
        return (
            "Generate a prioritized learning path for transitioning between roles or "
            "levels. Provide your current role/level and target role/level. The path "
            "prioritizes skills that are most resilient to AI automation and most "
            "critical for the target role. Optionally provide current skill assessments "
            "to personalize the path."
        )

    @property
    def tags(self) -> List[str]:
        return ["taxonomy", "learning", "career", "development"]

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target_function_id": {
                    "type": "string",
                    "description": "Target function (e.g., 'engineering').",
                },
                "target_role_id": {
                    "type": "string",
                    "description": "Target role (e.g., 'backend').",
                },
                "target_level": {
                    "type": "string",
                    "enum": ["junior", "mid", "senior", "staff", "principal"],
                    "description": "Target proficiency level.",
                },
                "current_level": {
                    "type": "string",
                    "enum": ["junior", "mid", "senior", "staff", "principal"],
                    "description": "Current proficiency level (default: junior).",
                },
                "current_skills": {
                    "type": "array",
                    "description": "Optional: list of skill_ids you already have at target level.",
                    "items": {"type": "string"},
                },
            },
            "required": ["target_function_id", "target_role_id", "target_level"],
        }

    def execute(self, target_function_id: str, target_role_id: str,
                target_level: str, current_level: str = "junior",
                current_skills: List[str] = None, **kwargs) -> SkillResult:
        role = self._loader.get_role(target_function_id, target_role_id)
        if not role:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Role '{target_role_id}' not found in '{target_function_id}'.",
            )

        current_skills = set(current_skills or [])
        target_num = LEVEL_ORDER.get(target_level, 3)
        current_num = LEVEL_ORDER.get(current_level, 1)
        levels_to_grow = target_num - current_num

        # Categorize skills by priority
        skills_needed = []
        for skill in role.skills:
            if skill.id in current_skills:
                continue

            # Priority score: lower AI impact = higher priority (invest in human skills)
            # Higher category weight for technical skills at lower levels,
            # leadership/communication at higher levels
            ai_resilience = 1.0 - skill.ai_impact_rating
            level_relevance = 1.0 if skill.category in ("leadership", "communication") and target_num >= 4 else 0.8
            priority = ai_resilience * 0.6 + level_relevance * 0.4

            skills_needed.append({
                "skill_id": skill.id,
                "skill_name": skill.name,
                "category": skill.category,
                "priority_score": round(priority, 2),
                "ai_impact_rating": skill.ai_impact_rating,
                "ai_resilience": round(ai_resilience, 2),
                "target_proficiency": skill.proficiency.get(target_level, ""),
                "current_proficiency": skill.proficiency.get(current_level, ""),
                "growth_description": f"From: {skill.proficiency.get(current_level, 'N/A')} → To: {skill.proficiency.get(target_level, 'N/A')}",
            })

        # Sort by priority (highest first)
        skills_needed.sort(key=lambda s: s["priority_score"], reverse=True)

        # Build phases
        phases = []
        if levels_to_grow > 0:
            phase_size = max(3, len(skills_needed) // min(levels_to_grow, 3))
            for i in range(0, len(skills_needed), phase_size):
                phase_num = i // phase_size + 1
                phase_skills = skills_needed[i:i + phase_size]
                from_level = LEVEL_NAMES.get(min(current_num + phase_num - 1, target_num), current_level)
                to_level = LEVEL_NAMES.get(min(current_num + phase_num, target_num), target_level)
                phases.append({
                    "phase": phase_num,
                    "focus": f"Grow from {from_level} to {to_level}",
                    "skills": phase_skills,
                })
        else:
            phases.append({
                "phase": 1,
                "focus": f"Strengthen {target_level}-level skills",
                "skills": skills_needed,
            })

        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={
                "role": role.name,
                "transition": f"{current_level} → {target_level}",
                "levels_to_grow": levels_to_grow,
                "total_skills_to_develop": len(skills_needed),
                "already_proficient": len(current_skills),
                "phases": phases,
                "ai_strategy": (
                    "This path prioritizes skills with high AI resilience -- skills "
                    "that will remain valuable as AI capabilities grow. Technical "
                    "skills with high automation potential are included but deprioritized. "
                    "Focus your deepest investment on low-AI-impact skills like system "
                    "design, leadership, and cross-functional communication."
                ),
            },
        )
