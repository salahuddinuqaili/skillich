"""Cross-role skill transfer analysis and career transition advisor.

Use this skill to find which skills transfer between roles, recommend
career transitions based on current skills, and identify the skill delta
needed to move from one role to another.
"""

from typing import Any, Dict, List, Optional

from core.base import Skill, SkillResult, SkillStatus
from core.taxonomy import TaxonomyLoader


class CareerAdvisorSkill(Skill):

    def __init__(self, taxonomy_dir: str = "taxonomy", loader: Optional[TaxonomyLoader] = None):
        self._loader = loader or TaxonomyLoader(taxonomy_dir)

    @property
    def name(self) -> str:
        return "career_advisor"

    @property
    def description(self) -> str:
        return (
            "Analyze career transitions between tech roles. "
            "Use action='find_transitions' with source_function_id and source_role_id "
            "to find roles you can transition to and the skill gap for each. "
            "Use action='transferable_skills' with function_id and role_id to find "
            "which of your skills are valuable across multiple roles. "
            "Use action='skill_overlap' to compare two specific roles and see shared vs unique skills. "
            "Use action='universal_skills' to find the most cross-functional skills in the taxonomy."
        )

    @property
    def tags(self) -> List[str]:
        return ["taxonomy", "career", "transition", "transfer", "advice"]

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["find_transitions", "transferable_skills", "skill_overlap", "universal_skills"],
                    "description": "The analysis action to perform.",
                },
                "source_function_id": {
                    "type": "string",
                    "description": "Source function ID (for find_transitions).",
                },
                "source_role_id": {
                    "type": "string",
                    "description": "Source role ID (for find_transitions).",
                },
                "function_id": {
                    "type": "string",
                    "description": "Function ID (for transferable_skills).",
                },
                "role_id": {
                    "type": "string",
                    "description": "Role ID (for transferable_skills).",
                },
                "target_function_id": {
                    "type": "string",
                    "description": "Target function ID (for skill_overlap).",
                },
                "target_role_id": {
                    "type": "string",
                    "description": "Target role ID (for skill_overlap).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 10).",
                },
            },
            "required": ["action"],
        }

    def execute(self, action: str, **kwargs) -> SkillResult:
        if action == "find_transitions":
            return self._find_transitions(
                kwargs.get("source_function_id", ""),
                kwargs.get("source_role_id", ""),
                kwargs.get("limit", 10),
            )
        elif action == "transferable_skills":
            return self._transferable_skills(
                kwargs.get("function_id", ""),
                kwargs.get("role_id", ""),
            )
        elif action == "skill_overlap":
            return self._skill_overlap(
                kwargs.get("source_function_id", kwargs.get("function_id", "")),
                kwargs.get("source_role_id", kwargs.get("role_id", "")),
                kwargs.get("target_function_id", ""),
                kwargs.get("target_role_id", ""),
            )
        elif action == "universal_skills":
            return self._universal_skills(kwargs.get("limit", 20))
        else:
            return SkillResult(status=SkillStatus.ERROR, error=f"Unknown action: {action}")

    def _build_skill_index(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build an index of skill_name_lower -> list of {function, role, skill}."""
        index: Dict[str, List[Dict[str, Any]]] = {}
        for func in self._loader.list_functions():
            for role in self._loader.list_roles(func.id):
                for skill in role.skills:
                    key = skill.name.lower().strip()
                    if key not in index:
                        index[key] = []
                    index[key].append({
                        "function_id": func.id,
                        "function_name": func.name,
                        "role_id": role.id,
                        "role_name": role.name,
                        "skill": skill,
                    })
        return index

    # Synonyms: map variant terms to a canonical form so matching catches
    # "testing" == "test", "database" == "data modeling", etc.
    _SYNONYMS: dict[str, str] = {
        "testing": "test", "tests": "test", "tested": "test",
        "strategies": "strategy", "strategic": "strategy",
        "designing": "design", "designs": "design",
        "planning": "plan", "plans": "plan",
        "modeling": "model", "models": "model",
        "optimization": "optimize", "optimizing": "optimize", "optimisation": "optimize",
        "management": "manage", "managing": "manage", "manager": "manage",
        "development": "develop", "developing": "develop", "developer": "develop",
        "engineering": "engineer", "engineers": "engineer",
        "communication": "communicate", "communicating": "communicate",
        "analytics": "analysis", "analytical": "analysis", "analyst": "analysis",
        "automation": "automate", "automating": "automate", "automated": "automate",
        "monitoring": "monitor", "monitors": "monitor",
        "programming": "program", "programs": "program",
        "architecture": "architect", "architectural": "architect",
        "infrastructure": "infra",
        "database": "data",
        "security": "secure", "securing": "secure",
        "performance": "perf",
        "observability": "monitor",
        "reliability": "reliable",
        "scalability": "scale", "scaling": "scale",
        "deployment": "deploy", "deploying": "deploy", "deployments": "deploy",
        "integration": "integrate", "integrating": "integrate", "integrations": "integrate",
        "configuration": "config", "configuring": "config",
        "documentation": "docs", "documenting": "docs",
        "leadership": "lead", "leading": "lead",
        "collaboration": "collaborate", "collaborating": "collaborate",
        "mentorship": "mentor", "mentoring": "mentor",
        "negotiation": "negotiate", "negotiating": "negotiate",
        "experimentation": "experiment", "experiments": "experiment",
        "visualization": "visual", "visualizing": "visual",
        "implementation": "implement", "implementing": "implement",
        "frameworks": "framework",
        "services": "service",
        "platforms": "platform",
        "systems": "system",
        "applications": "application", "apps": "application",
        "fundamentals": "fundamental",
        "practices": "practice",
        "techniques": "technique",
        "principles": "principle",
        "patterns": "pattern",
        "pipelines": "pipeline",
        "queries": "query",
        "metrics": "metric",
        "incidents": "incident",
        "vulnerabilities": "vulnerability",
        "compliance": "comply",
        "governance": "govern",
        "budgeting": "budget", "budgets": "budget",
        "forecasting": "forecast", "forecasts": "forecast",
        "recruiting": "recruit", "recruitment": "recruit",
        "onboarding": "onboard",
        "retention": "retain",
        "interviewing": "interview", "interviews": "interview",
        "response": "respond", "responding": "respond",
        "modelling": "model",
    }

    # Domain clusters: groups of terms that are conceptually related even if
    # they don't share a root word.  If skill A contains a term from cluster X
    # and skill B also contains a term from cluster X, that's a partial match.
    _DOMAIN_CLUSTERS: list[set[str]] = [
        {"test", "quality", "qa", "bug", "defect", "coverage"},
        {"data", "sql", "database", "warehouse", "etl", "pipeline", "query"},
        {"cloud", "aws", "azure", "gcp", "infra", "iaas", "paas"},
        {"secure", "vulnerability", "threat", "compliance", "audit", "iam"},
        {"api", "rest", "graphql", "grpc", "endpoint", "gateway"},
        {"ci", "cd", "deploy", "pipeline", "release", "rollout"},
        {"monitor", "alert", "observability", "logging", "trace", "metric"},
        {"frontend", "ui", "ux", "css", "html", "react", "vue", "angular"},
        {"mobile", "ios", "android", "swift", "kotlin", "flutter"},
        {"ml", "machine", "learning", "model", "training", "inference", "ai"},
        {"lead", "mentor", "manage", "coach", "hire", "team"},
        {"perf", "scale", "latency", "throughput", "cache", "optimize"},
        {"agile", "scrum", "sprint", "kanban", "ceremony", "retro"},
        {"communicate", "stakeholder", "present", "write", "negotiate"},
        {"budget", "cost", "finops", "forecast", "revenue", "pricing"},
        {"legal", "contract", "compliance", "regulatory", "policy", "govern"},
        {"recruit", "hire", "interview", "onboard", "talent", "retain"},
        {"content", "copy", "editorial", "brand", "messaging", "tone"},
        {"seo", "sem", "search", "organic", "paid", "keyword", "ranking"},
        {"experiment", "ab", "hypothesis", "variant", "statistical"},
        {"incident", "respond", "manage", "escalate", "postmortem", "oncall"},
        {"model", "data", "schema", "normalize", "warehouse", "dimension"},
    ]

    @classmethod
    def _skill_keywords(cls, name: str) -> set[str]:
        """Extract canonical keywords from a skill name."""
        stop_words = {
            "and", "the", "for", "with", "in", "of", "a", "an", "to", "&",
            "based", "driven",
        }
        words = set()
        for word in name.lower().replace("(", " ").replace(")", " ").replace("/", " ").replace(",", " ").split():
            word = word.strip()
            if len(word) > 2 and word not in stop_words:
                canonical = cls._SYNONYMS.get(word, word)
                words.add(canonical)
        return words

    @classmethod
    def _skill_similarity(cls, name_a: str, name_b: str) -> float:
        """Compute similarity between two skill names using keywords + domain clusters."""
        kw_a = cls._skill_keywords(name_a)
        kw_b = cls._skill_keywords(name_b)
        if not kw_a or not kw_b:
            return 0.0

        # Direct keyword overlap (with synonyms resolved)
        intersection = kw_a & kw_b
        keyword_score = len(intersection) / min(len(kw_a), len(kw_b))

        # Domain cluster overlap: how many shared domains do they touch?
        clusters_a = {i for i, cluster in enumerate(cls._DOMAIN_CLUSTERS) if kw_a & cluster}
        clusters_b = {i for i, cluster in enumerate(cls._DOMAIN_CLUSTERS) if kw_b & cluster}
        shared_clusters = clusters_a & clusters_b
        cluster_score = len(shared_clusters) / max(len(clusters_a | clusters_b), 1) if (clusters_a or clusters_b) else 0.0

        # Weighted combination: keywords matter most, clusters break ties
        return min(keyword_score * 0.7 + cluster_score * 0.3, 1.0)

    def _find_transitions(self, source_func_id: str, source_role_id: str, limit: int) -> SkillResult:
        if not source_func_id or not source_role_id:
            return SkillResult(
                status=SkillStatus.ERROR,
                error="source_function_id and source_role_id are required.",
            )

        source_role = self._loader.get_role(source_func_id, source_role_id)
        if not source_role:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Role '{source_role_id}' not found in '{source_func_id}'.",
            )

        transitions = []
        for func in self._loader.list_functions():
            for role in self._loader.list_roles(func.id):
                if func.id == source_func_id and role.id == source_role_id:
                    continue

                if not role.skills:
                    continue

                # For each target skill, find the best-matching source skill
                matched_count = 0
                gap_skills = []
                for tgt_skill in role.skills:
                    best_sim = 0.0
                    for src_skill in source_role.skills:
                        sim = self._skill_similarity(src_skill.name, tgt_skill.name)
                        # Also match on same category as a baseline signal
                        if src_skill.category == tgt_skill.category and sim > 0:
                            sim = min(sim + 0.1, 1.0)
                        best_sim = max(best_sim, sim)

                    if best_sim >= 0.4:
                        matched_count += 1
                    else:
                        gap_skills.append({
                            "name": tgt_skill.name,
                            "category": tgt_skill.category,
                            "ai_impact_rating": tgt_skill.ai_impact_rating,
                        })

                overlap_pct = matched_count / len(role.skills)

                transitions.append({
                    "function": func.name,
                    "function_id": func.id,
                    "role": role.name,
                    "role_id": role.id,
                    "skill_overlap": matched_count,
                    "skill_overlap_pct": round(overlap_pct, 2),
                    "skills_to_learn": len(gap_skills),
                    "gap_skills": sorted(gap_skills, key=lambda x: x["ai_impact_rating"]),
                })

        transitions.sort(key=lambda x: x["skill_overlap_pct"], reverse=True)

        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={
                "source": f"{source_role.name} ({source_func_id})",
                "transitions": transitions[:limit],
            },
        )

    def _transferable_skills(self, function_id: str, role_id: str) -> SkillResult:
        if not function_id or not role_id:
            return SkillResult(
                status=SkillStatus.ERROR,
                error="function_id and role_id are required.",
            )

        role = self._loader.get_role(function_id, role_id)
        if not role:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Role '{role_id}' not found in '{function_id}'.",
            )

        skill_index = self._build_skill_index()
        transferable = []

        for skill in role.skills:
            key = skill.name.lower().strip()
            occurrences = skill_index.get(key, [])
            other_roles = [
                {"function": o["function_name"], "role": o["role_name"]}
                for o in occurrences
                if not (o["function_id"] == function_id and o["role_id"] == role_id)
            ]
            transferable.append({
                "skill": skill.name,
                "category": skill.category,
                "ai_impact_rating": skill.ai_impact_rating,
                "appears_in_roles": len(occurrences),
                "other_roles": other_roles,
            })

        transferable.sort(key=lambda x: x["appears_in_roles"], reverse=True)

        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={
                "role": role.name,
                "skills": transferable,
            },
        )

    def _skill_overlap(
        self, src_func: str, src_role: str, tgt_func: str, tgt_role: str
    ) -> SkillResult:
        if not all([src_func, src_role, tgt_func, tgt_role]):
            return SkillResult(
                status=SkillStatus.ERROR,
                error="source and target function_id and role_id are all required.",
            )

        source = self._loader.get_role(src_func, src_role)
        target = self._loader.get_role(tgt_func, tgt_role)
        if not source:
            return SkillResult(status=SkillStatus.ERROR, error=f"Source role '{src_role}' not found.")
        if not target:
            return SkillResult(status=SkillStatus.ERROR, error=f"Target role '{tgt_role}' not found.")

        src_map = {s.name.lower().strip(): s for s in source.skills}
        tgt_map = {s.name.lower().strip(): s for s in target.skills}

        shared_keys = set(src_map.keys()) & set(tgt_map.keys())
        src_only = set(src_map.keys()) - set(tgt_map.keys())
        tgt_only = set(tgt_map.keys()) - set(src_map.keys())

        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={
                "source": source.name,
                "target": target.name,
                "shared_skills": [
                    {"name": src_map[k].name, "category": src_map[k].category}
                    for k in sorted(shared_keys)
                ],
                "source_only": [
                    {"name": src_map[k].name, "category": src_map[k].category}
                    for k in sorted(src_only)
                ],
                "target_only": [
                    {"name": tgt_map[k].name, "category": tgt_map[k].category}
                    for k in sorted(tgt_only)
                ],
                "overlap_pct": round(len(shared_keys) / max(len(tgt_map), 1), 2),
            },
        )

    def _universal_skills(self, limit: int) -> SkillResult:
        skill_index = self._build_skill_index()

        universal = []
        for skill_key, occurrences in skill_index.items():
            if len(occurrences) >= 2:
                sample = occurrences[0]["skill"]
                universal.append({
                    "skill": sample.name,
                    "category": sample.category,
                    "appears_in_roles": len(occurrences),
                    "roles": [
                        {"function": o["function_name"], "role": o["role_name"]}
                        for o in occurrences
                    ],
                    "avg_ai_impact": round(
                        sum(o["skill"].ai_impact_rating for o in occurrences) / len(occurrences), 2
                    ),
                })

        universal.sort(key=lambda x: x["appears_in_roles"], reverse=True)

        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={
                "analysis": "universal_skills",
                "description": "Skills that appear across multiple roles -- investing here gives the broadest career optionality.",
                "skills": universal[:limit],
            },
        )
