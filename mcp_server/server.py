"""skillich MCP server -- exposes the skill taxonomy to Claude Desktop and Claude Code."""

import json
import os
from pathlib import Path
from typing import Annotated

from pydantic import Field

try:  # mcp >= 2.0 renamed FastMCP to MCPServer and dropped the fastmcp module
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server


from core.plan import build_plan, confident_match, find_roles
from core.registry import SkillRegistry
from core.taxonomy import TaxonomyLoader
from skills.taxonomy_skills.ai_impact_analyzer import AIImpactAnalyzerSkill
from skills.taxonomy_skills.career_advisor import CareerAdvisorSkill
from skills.taxonomy_skills.learning_path import LearningPathSkill
from skills.taxonomy_skills.role_explorer import RoleExplorerSkill
from skills.taxonomy_skills.skill_assessor import SkillAssessorSkill

# Resolve taxonomy directory: env override or relative to this file
_TAXONOMY_DIR = os.environ.get(
    "SKILLICH_TAXONOMY_DIR",
    str(Path(__file__).resolve().parent.parent / "taxonomy"),
)

# Shared loader and registry -- created once at import time
_loader = TaxonomyLoader(_TAXONOMY_DIR)
_registry = SkillRegistry()
_registry.register(RoleExplorerSkill(loader=_loader))
_registry.register(AIImpactAnalyzerSkill(loader=_loader))
_registry.register(SkillAssessorSkill(loader=_loader))
_registry.register(LearningPathSkill(loader=_loader))
_registry.register(CareerAdvisorSkill(loader=_loader))


def _build_instructions(loader: TaxonomyLoader) -> str:
    """Build MCP instructions dynamically from the live taxonomy so counts are always accurate."""
    stats_result = _registry.call_skill("role_explorer", action="stats")
    if stats_result.ok and stats_result.data:
        s = stats_result.data
        n_functions = s.get("functions", "?")
        n_roles = s.get("roles", "?")
        n_skills = s.get("skills", "?")
    else:
        # Fallback: count directly from loader
        functions = loader.list_functions()
        n_functions = len(functions)
        n_roles = sum(len(loader.list_roles(f.id)) for f in functions)
        n_skills = sum(
            len(loader.get_role(f.id, r.id).skills)
            for f in functions
            for r in loader.list_roles(f.id)
        )
    return (
        f"skillich is an AI career skills taxonomy covering {n_functions} functions, "
        f"{n_roles} roles, and {n_skills} skills — each rated for AI automation impact. "
        "Use these tools to explore roles, analyze AI impact on careers, assess skill gaps, "
        "and generate learning paths. When someone asks what AI means for their job, start with "
        "action_plan(job_title='...') — it takes a plain job title and returns the full "
        "invest / partner / delegate breakdown in one call. Use explore_roles(action='list_functions') "
        "to browse the taxonomy, or explore_roles(action='stats') for a full count."
    )


mcp = _Server(
    "skillich",
    instructions=_build_instructions(_loader),
)



def _call(skill_name: str, **kwargs) -> str:
    """Call a registry skill and return JSON."""
    result = _registry.call_skill(skill_name, **kwargs)
    return json.dumps(result.to_dict(), indent=2)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def explore_roles(
    action: Annotated[
        str,
        Field(description="Action to perform: 'list_functions' (all categories), 'list_roles' (roles in a function), "
        "'get_role' (full detail), 'search_skills' (find skills by keyword), 'stats' (taxonomy counts)"),
    ],
    function_id: Annotated[
        str,
        Field(description="Function category ID, e.g. 'engineering', 'product', 'design', 'data_analytics', "
        "'marketing', 'operations', 'leadership'. Required for list_roles and get_role."),
    ] = "",
    role_id: Annotated[
        str,
        Field(description="Role ID, e.g. 'backend', 'product_manager', 'ux_designer'. Required for get_role."),
    ] = "",
    query: Annotated[
        str,
        Field(description="Search term for search_skills action, e.g. 'system design', 'python', 'leadership'."),
    ] = "",
) -> str:
    """Explore the skillich taxonomy of tech roles and skills.

    Start here to browse functions, roles, skills, and proficiency levels.
    The taxonomy covers Engineering, Product, Design, Data & Analytics,
    Marketing & Growth, Operations, and Leadership.
    """
    kwargs = {"action": action}
    if function_id:
        kwargs["function_id"] = function_id
    if role_id:
        kwargs["role_id"] = role_id
    if query:
        kwargs["query"] = query
    return _call("role_explorer", **kwargs)


@mcp.tool()
def analyze_ai_impact(
    action: Annotated[
        str,
        Field(description="Action: 'role_impact' (AI breakdown for one role), 'most_automatable' (highest-risk skills), "
        "'most_resilient' (safest skills), 'compare_roles' (compare roles in a function)"),
    ],
    function_id: Annotated[
        str,
        Field(description="Function ID. Required for role_impact and compare_roles."),
    ] = "",
    role_id: Annotated[
        str,
        Field(description="Role ID. Required for role_impact."),
    ] = "",
    limit: Annotated[
        int,
        Field(description="Max results for most_automatable / most_resilient (default 20)."),
    ] = 20,
) -> str:
    """Analyze how AI is transforming tech roles and skills.

    Shows which skills are being automated, augmented, or preserved.
    Every skill has an AI impact rating from 0.0 (fully human) to 1.0 (fully automatable).
    Use this to make informed career investment decisions.
    """
    kwargs: dict = {"action": action}
    if function_id:
        kwargs["function_id"] = function_id
    if role_id:
        kwargs["role_id"] = role_id
    if limit != 20:
        kwargs["limit"] = limit
    return _call("ai_impact_analyzer", **kwargs)


@mcp.tool()
def assess_skills(
    function_id: Annotated[str, Field(description="Target function, e.g. 'engineering'.")],
    role_id: Annotated[str, Field(description="Target role, e.g. 'backend'.")],
    target_level: Annotated[
        str,
        Field(description="Level to assess against: 'junior', 'mid', 'senior', 'staff', or 'principal'."),
    ],
    assessments: Annotated[
        str,
        Field(description="JSON array of objects: [{\"skill_id\": \"api_design\", \"current_level\": \"mid\"}, ...]. "
        "Use explore_roles with get_role to find valid skill IDs first."),
    ],
) -> str:
    """Assess your skills against a target role and identify gaps.

    Provide your current proficiency level for each skill and get a gap analysis
    showing where you're behind, on track, or ahead. Gaps are prioritized by
    AI resilience -- skills that AI can't easily replace are flagged as higher priority.
    """
    parsed = json.loads(assessments)
    return _call(
        "skill_assessor",
        function_id=function_id,
        role_id=role_id,
        target_level=target_level,
        assessments=parsed,
    )


@mcp.tool()
def generate_learning_path(
    target_function_id: Annotated[str, Field(description="Target function, e.g. 'engineering'.")],
    target_role_id: Annotated[str, Field(description="Target role, e.g. 'backend'.")],
    target_level: Annotated[
        str,
        Field(description="Target level: 'junior', 'mid', 'senior', 'staff', or 'principal'."),
    ],
    current_level: Annotated[
        str,
        Field(description="Your current level (default 'junior')."),
    ] = "junior",
    current_skills: Annotated[
        str,
        Field(description="Optional JSON array of skill IDs you already have at target level, e.g. '[\"api_design\"]'."),
    ] = "[]",
) -> str:
    """Generate a prioritized learning path for reaching a target role and level.

    Skills are prioritized by a formula: 60% AI resilience + 40% level relevance.
    This means skills that AI can't replace AND that matter most at your target level
    come first. The path is organized into growth phases.
    """
    parsed_skills = json.loads(current_skills)
    return _call(
        "learning_path",
        target_function_id=target_function_id,
        target_role_id=target_role_id,
        target_level=target_level,
        current_level=current_level,
        current_skills=parsed_skills,
    )


@mcp.tool()
def advise_career(
    action: Annotated[
        str,
        Field(description="Action: 'find_transitions' (roles you can move to), 'transferable_skills' (your most portable skills), "
        "'skill_overlap' (compare two roles), 'universal_skills' (most cross-functional skills)"),
    ],
    source_function_id: Annotated[str, Field(description="Your current function ID. Required for find_transitions.")] = "",
    source_role_id: Annotated[str, Field(description="Your current role ID. Required for find_transitions.")] = "",
    function_id: Annotated[str, Field(description="Function ID for transferable_skills or skill_overlap source.")] = "",
    role_id: Annotated[str, Field(description="Role ID for transferable_skills or skill_overlap source.")] = "",
    target_function_id: Annotated[str, Field(description="Target function ID for skill_overlap.")] = "",
    target_role_id: Annotated[str, Field(description="Target role ID for skill_overlap.")] = "",
    limit: Annotated[int, Field(description="Max results (default 10).")] = 10,
) -> str:
    """Analyze career transitions between tech roles.

    Find which roles you can transition to based on skill overlap, discover
    which of your skills are most transferable, and compare the skill gap
    between any two roles. Use this to make data-driven career decisions.
    """
    kwargs: dict = {"action": action}
    if source_function_id:
        kwargs["source_function_id"] = source_function_id
    if source_role_id:
        kwargs["source_role_id"] = source_role_id
    if function_id:
        kwargs["function_id"] = function_id
    if role_id:
        kwargs["role_id"] = role_id
    if target_function_id:
        kwargs["target_function_id"] = target_function_id
    if target_role_id:
        kwargs["target_role_id"] = target_role_id
    if limit != 10:
        kwargs["limit"] = limit
    return _call("career_advisor", **kwargs)


@mcp.tool()
def action_plan(
    job_title: Annotated[
        str,
        Field(description="The person's job title in plain language, e.g. 'product manager', 'electrician', "
        "'paralegal', 'SDR'. Matched against role names, aliases and acronyms."),
    ] = "",
    function_id: Annotated[
        str, Field(description="Function ID, if you already know it. Skips the job-title lookup.")
    ] = "",
    role_id: Annotated[str, Field(description="Role ID, if you already know it. Skips the job-title lookup.")] = "",
    level: Annotated[
        str,
        Field(description="Career level: 'junior', 'mid', 'senior', 'staff' (ids vary by role — the role's "
        "levels are returned in the result). Defaults to mid-level."),
    ] = "",
    include_transitions: Annotated[
        bool, Field(description="Include roles this person's skills already transfer to. Slower.")
    ] = False,
) -> str:
    """Build a personalised AI action plan for a job title.

    Returns the role's skills split into three actions — invest here (AI can't do it),
    partner with AI (AI helps but needs steering), and let AI handle (already automated) —
    plus what "good" looks like at the person's next level, what to stop doing manually,
    and a shareable link. This is the single best tool for "what does AI mean for my job?".
    """
    if not (function_id and role_id):
        if not job_title:
            return json.dumps(
                {"ok": False, "error": "Provide job_title, or both function_id and role_id."},
                indent=2,
            )
        matches = find_roles(_loader, job_title, limit=5)
        if not matches:
            return json.dumps(
                {
                    "ok": False,
                    "error": f"No role matches '{job_title}'.",
                    "hint": "Call explore_roles(action='list_functions') to see what is covered.",
                },
                indent=2,
            )
        # Below the confident-match bar, hand the choice back rather than guessing.
        pick = confident_match(matches)
        if pick is None:
            return json.dumps(
                {
                    "ok": False,
                    "error": f"'{job_title}' is ambiguous — ask which of these they mean.",
                    "candidates": matches,
                },
                indent=2,
            )
        function_id, role_id = pick["function_id"], pick["role_id"]

    transitions = None
    if include_transitions:
        result = _registry.call_skill(
            "career_advisor",
            action="find_transitions",
            source_function_id=function_id,
            source_role_id=role_id,
            limit=5,
        )
        if result.ok:
            transitions = result.data["transitions"]

    plan = build_plan(_loader, function_id, role_id, level or None, transitions=transitions)
    if plan is None:
        return json.dumps(
            {"ok": False, "error": f"Role '{role_id}' not found in function '{function_id}'."},
            indent=2,
        )

    data = plan.to_dict()
    data["available_levels"] = [
        {"id": lv.id, "name": lv.name, "years_experience": lv.years_experience}
        for lv in (_loader.get_role(function_id, role_id).levels)
    ]
    data["share_url"] = "https://salahuddinuqaili.github.io/skillich/" + plan.share_path
    return json.dumps({"ok": True, "data": data}, indent=2, default=str)


def main():
    """Entry point for the skillich MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
