"""Career narrator skill — generates human-readable career summaries using a local Ollama model.

Uses the skillich taxonomy as grounding to produce concrete, fabrication-free
career guidance. Requires a local Ollama instance; degrades gracefully without one.
"""

import json
import os
from typing import Any, Dict, List, Optional

from core.base import Skill, SkillResult, SkillStatus
from core.taxonomy import TaxonomyLoader


_DEFAULT_ENDPOINT = "http://localhost:11434"
_DEFAULT_MODEL = "gemma4:e4b"


def _ollama_chat(prompt: str, endpoint: str, model: str, timeout: int = 120) -> str:
    """Call Ollama /api/chat and return the response text. Raises on failure."""
    import urllib.request

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        f"{endpoint}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
        return data["message"]["content"].strip()


class CareerNarratorSkill(Skill):
    """Generate human-readable career narratives from skillich taxonomy data.

    Uses a local Ollama model for on-device, privacy-preserving inference.
    Gracefully degrades to raw taxonomy data if Ollama is unreachable.

    Use action='role_summary' to get a plain-English "what this means for your career"
    paragraph for a specific role. Use action='skill_advice' to get concrete next-step
    advice for developing a named skill. Use action='resilience_brief' for a short
    briefing on the most AI-resilient skills in a function.
    """

    def __init__(
        self,
        taxonomy_dir: str = "taxonomy",
        loader: Optional[TaxonomyLoader] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self._loader = loader or TaxonomyLoader(taxonomy_dir)
        self._endpoint = endpoint or os.environ.get("OLLAMA_ENDPOINT", _DEFAULT_ENDPOINT)
        self._model = model or os.environ.get("OLLAMA_MODEL", _DEFAULT_MODEL)

    @property
    def name(self) -> str:
        return "career_narrator"

    @property
    def description(self) -> str:
        return (
            "Generate human-readable career narratives grounded in the skillich taxonomy. "
            "Use action='role_summary' (function_id + role_id) for a plain-English "
            "'what this means for your career' paragraph. "
            "Use action='skill_advice' (skill_name + current_level) for concrete next steps. "
            "Use action='resilience_brief' (function_id) for a short briefing on the "
            "most AI-resilient skills in a function. "
            "Requires a local Ollama instance; returns partial taxonomy data if unavailable."
        )

    @property
    def tags(self) -> List[str]:
        return ["taxonomy", "career", "narrative", "ollama", "local-llm"]

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["role_summary", "skill_advice", "resilience_brief"],
                    "description": "The narrative action to perform.",
                },
                "function_id": {
                    "type": "string",
                    "description": "Function ID. Required for role_summary and resilience_brief.",
                },
                "role_id": {
                    "type": "string",
                    "description": "Role ID. Required for role_summary.",
                },
                "skill_name": {
                    "type": "string",
                    "description": "Skill name to get advice on. Required for skill_advice.",
                },
                "current_level": {
                    "type": "string",
                    "description": "Your current proficiency level (junior/mid/senior). Used for skill_advice.",
                },
            },
            "required": ["action"],
        }

    def execute(self, action: str, **kwargs) -> SkillResult:
        if action == "role_summary":
            return self._role_summary(
                kwargs.get("function_id", ""),
                kwargs.get("role_id", ""),
            )
        elif action == "skill_advice":
            return self._skill_advice(
                kwargs.get("skill_name", ""),
                kwargs.get("current_level", "mid"),
            )
        elif action == "resilience_brief":
            return self._resilience_brief(kwargs.get("function_id", ""))
        else:
            return SkillResult(status=SkillStatus.ERROR, error=f"Unknown action: {action}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Try to call Ollama; return None on any failure."""
        try:
            return _ollama_chat(prompt, self._endpoint, self._model)
        except Exception:
            return None

    def _role_summary(self, function_id: str, role_id: str) -> SkillResult:
        role = self._loader.get_role(function_id, role_id)
        if not role:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Role '{role_id}' not found in '{function_id}'.",
            )

        ai = role.ai_impact
        top_auto = sorted(role.skills, key=lambda s: s.ai_impact_rating, reverse=True)[:3]
        top_safe = sorted(role.skills, key=lambda s: s.ai_impact_rating)[:3]
        avg = sum(s.ai_impact_rating for s in role.skills) / len(role.skills) if role.skills else 0

        # Raw taxonomy data always returned
        raw = {
            "role": role.name,
            "function": function_id,
            "ai_impact_level": ai.level,
            "avg_automation_risk": round(avg, 2),
            "most_at_risk": [s.name for s in top_auto],
            "most_resilient": [s.name for s in top_safe],
            "automating": ai.automating[:3],
            "preserving": ai.preserving[:3],
        }

        prompt = f"""You are a career advisor. Using only the data below, write a 3-sentence
plain-English paragraph explaining what AI means for this role today. Be concrete and specific.
Do not invent facts. Do not use bullet points.

Role: {role.name}
AI impact level: {ai.level}
Average skill automation risk: {avg:.0%}
Skills most at risk of automation: {', '.join(s.name for s in top_auto)}
Skills most resilient to AI: {', '.join(s.name for s in top_safe)}
What AI is automating: {'; '.join(ai.automating[:3])}
What AI is preserving: {'; '.join(ai.preserving[:3])}
Summary: {ai.summary}"""

        narrative = self._call_ollama(prompt)

        if narrative:
            return SkillResult(
                status=SkillStatus.SUCCESS,
                data={**raw, "narrative": narrative, "model": self._model},
                metadata={"ollama_endpoint": self._endpoint},
            )
        else:
            return SkillResult(
                status=SkillStatus.PARTIAL,
                data=raw,
                error=f"Ollama unavailable at {self._endpoint} — returning raw taxonomy data.",
                metadata={"ollama_endpoint": self._endpoint},
            )

    def _skill_advice(self, skill_name: str, current_level: str) -> SkillResult:
        if not skill_name:
            return SkillResult(status=SkillStatus.ERROR, error="skill_name is required.")

        # Search taxonomy for the skill
        results = self._loader.search_skills(skill_name)
        if not results:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Skill '{skill_name}' not found in taxonomy.",
            )
        skill = results[0]

        raw = {
            "skill": skill.name,
            "category": skill.category,
            "ai_impact_rating": skill.ai_impact_rating,
            "ai_impact_detail": skill.ai_impact_detail,
            "current_level": current_level,
            "proficiency_levels": skill.proficiency,
        }

        next_levels = {
            "junior": "mid",
            "mid": "senior",
            "senior": "staff",
            "staff": "principal",
        }
        target_level = next_levels.get(current_level, "senior")
        target_desc = skill.proficiency.get(target_level, "")

        prompt = f"""You are a senior career coach. Give 3 concrete, actionable next steps
for someone at {current_level} level who wants to improve their {skill.name} skill.
Be specific — name real tools, techniques, or projects. Keep it under 100 words total.
Do not use bullet points. Write as a single flowing paragraph.

Skill: {skill.name}
Category: {skill.category}
AI automation risk: {skill.ai_impact_rating:.0%} ({skill.ai_impact_detail})
Target level ({target_level}): {target_desc}"""

        narrative = self._call_ollama(prompt)

        if narrative:
            return SkillResult(
                status=SkillStatus.SUCCESS,
                data={**raw, "advice": narrative, "model": self._model},
                metadata={"ollama_endpoint": self._endpoint},
            )
        else:
            return SkillResult(
                status=SkillStatus.PARTIAL,
                data=raw,
                error=f"Ollama unavailable at {self._endpoint} — returning raw taxonomy data.",
                metadata={"ollama_endpoint": self._endpoint},
            )

    def _resilience_brief(self, function_id: str) -> SkillResult:
        if not function_id:
            return SkillResult(status=SkillStatus.ERROR, error="function_id is required.")

        roles = self._loader.list_roles(function_id)
        if not roles:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Function '{function_id}' not found.",
            )

        # Collect all skills, find lowest-automation ones
        all_skills = [
            (s, role.name)
            for role in roles
            for s in role.skills
        ]
        resilient = sorted(all_skills, key=lambda x: x[0].ai_impact_rating)[:5]

        raw = {
            "function": function_id,
            "top_resilient_skills": [
                {"skill": s.name, "role": r, "rating": s.ai_impact_rating}
                for s, r in resilient
            ],
        }

        skill_lines = "\n".join(
            f"- {s.name} ({r}): {s.ai_impact_rating:.0%} automation risk"
            for s, r in resilient
        )
        prompt = f"""You are a career strategist. In 2 sentences, explain why these skills
are resilient to AI automation and what makes them worth investing in.
Be concrete. Do not use bullet points.

Function: {function_id}
Most resilient skills:
{skill_lines}"""

        narrative = self._call_ollama(prompt)

        if narrative:
            return SkillResult(
                status=SkillStatus.SUCCESS,
                data={**raw, "narrative": narrative, "model": self._model},
                metadata={"ollama_endpoint": self._endpoint},
            )
        else:
            return SkillResult(
                status=SkillStatus.PARTIAL,
                data=raw,
                error=f"Ollama unavailable at {self._endpoint} — returning raw taxonomy data.",
                metadata={"ollama_endpoint": self._endpoint},
            )
