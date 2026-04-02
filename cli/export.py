"""Export taxonomy data to CSV and JSON for non-technical users."""

import csv
import io
import json
from typing import Optional

from core.taxonomy import TaxonomyLoader


def export_json(
    loader: TaxonomyLoader,
    function_id: str,
    role_id: Optional[str] = None,
) -> str:
    """Export role(s) as pretty-printed JSON."""
    if role_id:
        role = loader.get_role(function_id, role_id)
        if not role:
            return json.dumps({"error": f"Role '{role_id}' not found in '{function_id}'"})
        return json.dumps(_role_to_dict(role), indent=2)

    roles = loader.list_roles(function_id)
    if not roles:
        return json.dumps({"error": f"Function '{function_id}' not found"})
    return json.dumps([_role_to_dict(r) for r in roles], indent=2)


def export_csv(
    loader: TaxonomyLoader,
    function_id: str,
    role_id: Optional[str] = None,
) -> str:
    """Export role skills as a flat CSV suitable for spreadsheets.

    Columns: function, role, skill_name, category, ai_impact_rating,
             junior, mid, senior, staff, principal
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "function", "role", "skill_name", "category", "ai_impact_rating",
        "junior", "mid", "senior", "staff", "principal",
    ])

    if role_id:
        roles = [loader.get_role(function_id, role_id)]
        if roles[0] is None:
            return f"Error: Role '{role_id}' not found in '{function_id}'"
    else:
        roles = loader.list_roles(function_id)
        if not roles:
            return f"Error: Function '{function_id}' not found"

    for role in roles:
        for skill in role.skills:
            writer.writerow([
                function_id,
                role.name,
                skill.name,
                skill.category,
                skill.ai_impact_rating,
                skill.proficiency.get("junior", ""),
                skill.proficiency.get("mid", ""),
                skill.proficiency.get("senior", ""),
                skill.proficiency.get("staff", ""),
                skill.proficiency.get("principal", ""),
            ])

    return output.getvalue()


def _role_to_dict(role) -> dict:
    """Convert a TaxonomyRole to a serializable dict."""
    return {
        "id": role.id,
        "function": role.function_id,
        "name": role.name,
        "also_known_as": role.also_known_as,
        "description": role.description.strip(),
        "ai_impact": {
            "level": role.ai_impact.level,
            "summary": role.ai_impact.summary.strip(),
            "automating": role.ai_impact.automating,
            "augmenting": role.ai_impact.augmenting,
            "preserving": role.ai_impact.preserving,
        },
        "levels": [
            {
                "id": lvl.id,
                "name": lvl.name,
                "years_experience": lvl.years_experience,
                "summary": lvl.summary,
            }
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
    }
