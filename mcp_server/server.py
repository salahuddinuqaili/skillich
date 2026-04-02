"""skillich MCP server -- exposes the skill taxonomy to Claude Desktop and Claude Code."""

import json
import os
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP

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

mcp = FastMCP(
    "skillich",
    instructions=(
        "skillich is an AI skills taxonomy covering 7 tech functions, 38 roles, and 455 skills. "
        "Use these tools to explore roles, analyze AI impact on careers, assess skill gaps, "
        "and generate learning paths. Start with explore_roles to browse the taxonomy."
    ),
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
        "Action to perform: 'list_functions' (all categories), 'list_roles' (roles in a function), "
        "'get_role' (full detail), 'search_skills' (find skills by keyword), 'stats' (taxonomy counts)",
    ],
    function_id: Annotated[
        str,
        "Function category ID, e.g. 'engineering', 'product', 'design', 'data_analytics', "
        "'marketing', 'operations', 'leadership'. Required for list_roles and get_role.",
    ] = "",
    role_id: Annotated[
        str,
        "Role ID, e.g. 'backend', 'product_manager', 'ux_designer'. Required for get_role.",
    ] = "",
    query: Annotated[
        str,
        "Search term for search_skills action, e.g. 'system design', 'python', 'leadership'.",
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
        "Action: 'role_impact' (AI breakdown for one role), 'most_automatable' (highest-risk skills), "
        "'most_resilient' (safest skills), 'compare_roles' (compare roles in a function)",
    ],
    function_id: Annotated[
        str,
        "Function ID. Required for role_impact and compare_roles.",
    ] = "",
    role_id: Annotated[
        str,
        "Role ID. Required for role_impact.",
    ] = "",
    limit: Annotated[
        int,
        "Max results for most_automatable / most_resilient (default 20).",
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
    function_id: Annotated[str, "Target function, e.g. 'engineering'."],
    role_id: Annotated[str, "Target role, e.g. 'backend'."],
    target_level: Annotated[
        str,
        "Level to assess against: 'junior', 'mid', 'senior', 'staff', or 'principal'.",
    ],
    assessments: Annotated[
        str,
        "JSON array of objects: [{\"skill_id\": \"api_design\", \"current_level\": \"mid\"}, ...]. "
        "Use explore_roles with get_role to find valid skill IDs first.",
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
    target_function_id: Annotated[str, "Target function, e.g. 'engineering'."],
    target_role_id: Annotated[str, "Target role, e.g. 'backend'."],
    target_level: Annotated[
        str,
        "Target level: 'junior', 'mid', 'senior', 'staff', or 'principal'.",
    ],
    current_level: Annotated[
        str,
        "Your current level (default 'junior').",
    ] = "junior",
    current_skills: Annotated[
        str,
        "Optional JSON array of skill IDs you already have at target level, e.g. '[\"api_design\"]'.",
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
        "Action: 'find_transitions' (roles you can move to), 'transferable_skills' (your most portable skills), "
        "'skill_overlap' (compare two roles), 'universal_skills' (most cross-functional skills)",
    ],
    source_function_id: Annotated[str, "Your current function ID. Required for find_transitions."] = "",
    source_role_id: Annotated[str, "Your current role ID. Required for find_transitions."] = "",
    function_id: Annotated[str, "Function ID for transferable_skills or skill_overlap source."] = "",
    role_id: Annotated[str, "Role ID for transferable_skills or skill_overlap source."] = "",
    target_function_id: Annotated[str, "Target function ID for skill_overlap."] = "",
    target_role_id: Annotated[str, "Target role ID for skill_overlap."] = "",
    limit: Annotated[int, "Max results (default 10)."] = 10,
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


def main():
    """Entry point for the skillich MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
