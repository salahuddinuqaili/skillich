"""Generate the self-contained static web app from the skillich taxonomy.

The page is one file with no network dependencies: taxonomy, learning
resources, plan rules and precomputed career transitions are all inlined.
Markup lives in ``template.html`` next door — the placeholders below are the
only contract between the two.

Usage:
    python web/generate.py              # writes web/index.html
    python web/generate.py out.html     # custom output path
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.plan import plan_constants  # noqa: E402
from core.taxonomy import TaxonomyLoader  # noqa: E402

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "template.html"

# Transitions are O(roles^2 x skills^2) to compute, so they are baked in at
# build time rather than run in the browser on every page load.
TRANSITIONS_PER_ROLE = 4
GAP_SKILLS_PER_TRANSITION = 12


def build_transitions(loader: TaxonomyLoader) -> Dict[str, List[Dict[str, Any]]]:
    """Precompute the top career transitions for every role, keyed 'func/role'."""
    from skills.taxonomy_skills.career_advisor import CareerAdvisorSkill

    advisor = CareerAdvisorSkill(loader=loader)
    out: Dict[str, List[Dict[str, Any]]] = {}
    for func in loader.list_functions():
        for role in loader.list_roles(func.id):
            result = advisor.execute(
                "find_transitions",
                source_function_id=func.id,
                source_role_id=role.id,
                limit=TRANSITIONS_PER_ROLE,
            )
            if not result.ok:
                continue
            trimmed = []
            for t in result.data["transitions"]:
                trimmed.append(
                    {
                        "function": t["function"],
                        "function_id": t["function_id"],
                        "role": t["role"],
                        "role_id": t["role_id"],
                        "skill_overlap_pct": t["skill_overlap_pct"],
                        "skills_to_learn": t["skills_to_learn"],
                        "gap_skills": [
                            {"name": g["name"], "ai_impact_rating": g["ai_impact_rating"]}
                            for g in t["gap_skills"][:GAP_SKILLS_PER_TRANSITION]
                        ],
                    }
                )
            out[f"{func.id}/{role.id}"] = trimmed
    return out


def build_json(loader: TaxonomyLoader, transitions: Dict[str, List[Dict[str, Any]]]) -> str:
    """Serialize the full taxonomy to JSON for embedding in the page."""
    data: Dict[str, Any] = {"functions": []}
    for func in loader.list_functions():
        f = {
            "id": func.id,
            "name": func.name,
            "description": func.description.strip(),
            "roles": [],
        }
        for role in loader.list_roles(func.id):
            r = {
                "id": role.id,
                "name": role.name,
                "also_known_as": role.also_known_as,
                "description": role.description.strip(),
                "ai_impact": {
                    "level": role.ai_impact.level,
                    "summary": role.ai_impact.summary.strip(),
                    "confidence": role.ai_impact.confidence,
                    "last_reviewed": role.ai_impact.last_reviewed,
                    "automating": role.ai_impact.automating,
                    "augmenting": role.ai_impact.augmenting,
                    "preserving": role.ai_impact.preserving,
                },
                "levels": [
                    {"id": lv.id, "name": lv.name, "years_experience": lv.years_experience,
                     "summary": lv.summary}
                    for lv in role.levels
                ],
                "skills": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "category": s.category,
                        "description": s.description,
                        "ai_impact_rating": s.ai_impact_rating,
                        "ai_impact_detail": s.ai_impact_detail.strip(),
                        "proficiency": s.proficiency,
                    }
                    for s in role.skills
                ],
                "transitions": transitions.get(f"{func.id}/{role.id}", []),
            }
            f["roles"].append(r)
        data["functions"].append(f)
    data["stats"] = loader.stats
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def load_resources() -> str:
    """Load the curated learning resources JSON."""
    res_path = HERE / "resources.json"
    if not res_path.exists():
        return "{}"
    with open(res_path, encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_comment", None)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _script_safe(payload: str) -> str:
    """Escape ``<`` so taxonomy prose can never close the script tag it lives in.

    ``\\u003c`` is a valid JSON escape, so the browser parses it back to ``<``.
    """
    return payload.replace("<", "\\u003c")


def render(loader: TaxonomyLoader) -> str:
    """Fill the template's placeholders and return the finished page."""
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE}")

    transitions = build_transitions(loader)
    stats = loader.stats
    html = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "__TAXONOMY_JSON__": _script_safe(build_json(loader, transitions)),
        "__RESOURCES_JSON__": _script_safe(load_resources()),
        "__PLAN_JSON__": _script_safe(
            json.dumps(plan_constants(), ensure_ascii=False, separators=(",", ":"))
        ),
        "__ROLE_COUNT__": str(stats["roles"]),
        "__SKILL_COUNT__": f"{stats['skills']:,}",
    }
    for token, value in replacements.items():
        if token not in html:
            raise ValueError(f"Template is missing the {token} placeholder")
        html = html.replace(token, value)
    return html


def main() -> None:
    taxonomy_dir = str(Path(__file__).resolve().parent.parent / "taxonomy")
    output = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "index.html")

    loader = TaxonomyLoader(taxonomy_dir)
    html = render(loader)

    Path(output).write_text(html, encoding="utf-8")
    size_kb = Path(output).stat().st_size / 1024
    stats = loader.stats
    print(f"Generated {output} ({size_kb:.0f} KB)")
    print(f"  {stats['functions']} functions, {stats['roles']} roles, {stats['skills']} skills")


if __name__ == "__main__":
    main()
