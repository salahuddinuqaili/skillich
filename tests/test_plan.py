"""Tests for the action plan engine — the logic behind `skillich plan`,
the MCP `action_plan` tool, and the web app's plan page."""

import pytest

from core.plan import (
    ACTIONS,
    CONFIDENT_MARGIN,
    INVEST_MAX,
    PARTNER_MAX,
    action_for,
    build_plan,
    confident_match,
    exposure_band,
    find_roles,
    plan_constants,
    score_role,
)
from core.taxonomy import TaxonomyLoader


@pytest.fixture(scope="module")
def loader():
    return TaxonomyLoader("taxonomy")


# --- Action bands -----------------------------------------------------------


@pytest.mark.parametrize(
    "rating,expected",
    [
        (0.0, "invest"),
        (0.05, "invest"),
        (INVEST_MAX, "invest"),
        (INVEST_MAX + 0.01, "partner"),
        (0.45, "partner"),
        (PARTNER_MAX, "partner"),
        (PARTNER_MAX + 0.01, "delegate"),
        (1.0, "delegate"),
    ],
)
def test_action_bands_partition_the_range(rating, expected):
    assert action_for(rating) == expected


def test_every_band_has_user_facing_copy():
    for key in ("invest", "partner", "delegate"):
        assert ACTIONS[key]["label"]
        assert ACTIONS[key]["tip"]
        assert ACTIONS[key]["why"]


@pytest.mark.parametrize(
    "exposure,band",
    [(0.0, "resilient"), (0.29, "resilient"), (0.35, "shifting"),
     (0.5, "exposed"), (0.75, "high-exposure"), (1.0, "high-exposure")],
)
def test_exposure_bands(exposure, band):
    key, headline = exposure_band(exposure)
    assert key == band
    assert headline


# --- Plan construction ------------------------------------------------------


def test_plan_covers_every_skill_exactly_once(loader):
    plan = build_plan(loader, "product", "product_manager", "senior")
    role = loader.get_role("product", "product_manager")
    ids = [s.id for s in plan.invest + plan.partner + plan.delegate]
    assert sorted(ids) == sorted(s.id for s in role.skills)


def test_plan_bands_respect_their_thresholds(loader):
    plan = build_plan(loader, "engineering", "backend", "mid")
    assert all(s.rating <= INVEST_MAX for s in plan.invest)
    assert all(INVEST_MAX < s.rating <= PARTNER_MAX for s in plan.partner)
    assert all(s.rating > PARTNER_MAX for s in plan.delegate)


def test_plan_sorts_each_band_by_career_value(loader):
    plan = build_plan(loader, "marketing", "content_strategist", "mid")
    for band in (plan.invest, plan.partner, plan.delegate):
        assert band == sorted(band, key=lambda s: s.rating)


def test_plan_points_at_the_next_level(loader):
    role = loader.get_role("product", "product_manager")
    first, second = role.levels[0].id, role.levels[1].id
    plan = build_plan(loader, "product", "product_manager", first)
    assert plan.level_id == first
    assert plan.next_level_id == second


def test_top_level_has_no_level_above_it(loader):
    role = loader.get_role("product", "product_manager")
    top = role.levels[-1].id
    plan = build_plan(loader, "product", "product_manager", top)
    assert plan.next_level_id == top


def test_unknown_level_falls_back_instead_of_failing(loader):
    plan = build_plan(loader, "product", "product_manager", "emperor")
    assert plan is not None
    assert plan.level_id in [lv.id for lv in loader.get_role("product", "product_manager").levels]


def test_unknown_role_returns_none(loader):
    assert build_plan(loader, "product", "not_a_role") is None
    assert build_plan(loader, "not_a_function", "backend") is None


def test_every_role_in_the_taxonomy_builds_a_plan(loader):
    for func in loader.list_functions():
        for role in loader.list_roles(func.id):
            plan = build_plan(loader, func.id, role.id)
            assert plan is not None, f"{func.id}/{role.id}"
            assert plan.skill_count == len(role.skills), f"{func.id}/{role.id}"
            assert plan.headline
            assert 0.0 <= plan.exposure <= 1.0


def test_invest_skills_carry_a_concrete_proof_point(loader):
    plan = build_plan(loader, "trades", "electrician", "journeyman")
    assert plan.invest, "electrician should have resilient skills"
    assert all(s.proof for s in plan.invest)


def test_proof_points_vary_within_a_category(loader):
    """Six technical skills must not print the same sentence six times."""
    plan = build_plan(loader, "leadership", "engineering_manager", "senior")
    same_category = [s for s in plan.invest if s.category == "leadership"]
    assert len(same_category) >= 3, "fixture no longer exercises the repeat case"
    assert len({s.proof for s in same_category[:3]}) == 3


def test_proof_point_cycles_deterministically():
    from core.plan import PROOF_POINTS, proof_point

    variants = PROOF_POINTS["technical"]
    assert [proof_point("technical", i) for i in range(len(variants))] == variants
    assert proof_point("technical", len(variants)) == variants[0]
    assert proof_point("technical", 0) == proof_point("technical", 0)


def test_unknown_category_falls_back_without_crashing():
    from core.plan import DEFAULT_PROOF, proof_point

    assert proof_point("astrology", 0) == DEFAULT_PROOF[0]
    assert proof_point("astrology", 99)


def test_share_path_matches_the_web_route(loader):
    plan = build_plan(loader, "trades", "electrician", "journeyman")
    assert plan.share_path == "#/plan/trades/electrician/journeyman"


def test_max_per_band_trims_every_band(loader):
    plan = build_plan(loader, "engineering", "backend", "mid", max_per_band=2)
    assert len(plan.invest) <= 2
    assert len(plan.partner) <= 2
    assert len(plan.delegate) <= 2


# --- Serialisation ----------------------------------------------------------


def test_to_dict_is_json_safe(loader):
    import json

    plan = build_plan(loader, "product", "product_manager", "senior")
    data = json.loads(json.dumps(plan.to_dict()))
    assert data["role_name"] == "Product Manager"
    assert data["exposure_percent"] == round(plan.exposure * 100)
    assert data["share_path"].startswith("#/plan/")


def test_markdown_is_a_usable_document(loader):
    plan = build_plan(loader, "product", "product_manager", "senior")
    md = plan.to_markdown()
    assert md.startswith("# Your AI action plan — Product Manager")
    assert "## Invest here" in md
    assert "Where you're going" in md
    assert "template=feedback.yml" in md
    for skill in plan.invest:
        assert skill.name in md


def test_markdown_survives_a_role_with_no_transitions(loader):
    plan = build_plan(loader, "trades", "electrician", "apprentice")
    assert plan.transitions == []
    assert "Where your skills already transfer" not in plan.to_markdown()


# --- Role lookup ------------------------------------------------------------


@pytest.mark.parametrize(
    "query,expected",
    [
        ("product manager", "Product Manager"),
        ("pm", "Product Manager"),
        ("sre", "DevOps / Site Reliability Engineer"),
        ("sdr", "Sales Development Representative"),
        ("electrician", "Electrician"),
        ("backend", "Backend Engineer"),
        ("swe", "Full-Stack Engineer"),
        ("ml", "Machine Learning Engineer"),
        ("recruiter", "Recruiter / Talent Acquisition Specialist"),
        ("PRODUCT MANAGER", "Product Manager"),
        ("  product   manager  ", "Product Manager"),
    ],
)
def test_role_search_finds_what_people_type(loader, query, expected):
    hits = find_roles(loader, query, limit=5)
    assert hits, f"no hits for {query!r}"
    assert hits[0]["role_name"] == expected


def test_role_search_returns_nothing_for_nonsense(loader):
    assert find_roles(loader, "xyzzyplugh") == []
    assert find_roles(loader, "") == []


def test_role_search_respects_the_limit(loader):
    assert len(find_roles(loader, "engineer", limit=3)) == 3


def test_score_role_is_zero_for_an_unrelated_query(loader):
    role = loader.get_role("trades", "electrician")
    assert score_role("quantum chromodynamics", role, "Skilled Trades") == 0.0


# --- Confidence gate --------------------------------------------------------


def test_confident_match_accepts_a_clear_winner(loader):
    pick = confident_match(find_roles(loader, "pm", limit=5))
    assert pick is not None and pick["role_name"] == "Product Manager"


@pytest.mark.parametrize("ambiguous", ["engineer", "ux", "analyst", "manager"])
def test_confident_match_asks_when_the_query_is_generic(loader, ambiguous):
    assert confident_match(find_roles(loader, ambiguous, limit=5)) is None


def test_confident_match_handles_empty_and_single(loader):
    assert confident_match([]) is None
    only = find_roles(loader, "electrician", limit=5)
    assert len(only) == 1
    assert confident_match(only) == only[0]


def test_confidence_margin_is_the_thing_being_measured():
    close = [{"score": 90.0}, {"score": 90.0 - CONFIDENT_MARGIN + 0.1}]
    clear = [{"score": 90.0}, {"score": 90.0 - CONFIDENT_MARGIN}]
    assert confident_match(close) is None
    assert confident_match(clear) is clear[0]


# --- Constants exported to the web app --------------------------------------


def test_plan_constants_carry_everything_the_web_app_needs():
    c = plan_constants()
    assert c["investMax"] == INVEST_MAX
    assert c["partnerMax"] == PARTNER_MAX
    assert set(c["actions"]) == {"invest", "partner", "delegate"}
    assert c["proofPoints"] and c["defaultProof"]
    assert [b["key"] for b in c["exposureBands"]] == [
        "resilient", "shifting", "exposed", "high-exposure"
    ]
    assert c["querySynonyms"]["pm" if "pm" in c["querySynonyms"] else "swe"]
    assert isinstance(c["stopWords"], list)


def test_plan_constants_are_json_serialisable():
    import json

    assert json.loads(json.dumps(plan_constants()))["investMax"] == INVEST_MAX


def test_proof_points_cover_every_category_in_the_taxonomy(loader):
    """A skill with no proof point silently falls back to generic advice."""
    categories = {
        s.category
        for f in loader.list_functions()
        for r in loader.list_roles(f.id)
        for s in r.skills
    }
    proofs = plan_constants()["proofPoints"]
    missing = categories - set(proofs)
    assert not missing, f"no proof point for categories: {sorted(missing)}"
    assert all(len(v) >= 3 for v in proofs.values()), "each category needs variants to cycle"
