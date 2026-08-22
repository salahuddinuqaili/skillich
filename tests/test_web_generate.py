"""Tests for the static site generator.

The page's behaviour is covered by web/smoke.test.js (jsdom). These tests guard
the build contract: every placeholder is filled, the embedded JSON is parseable
and can't break out of its script tag, and the plan rules the page ships match
the ones Python uses.
"""

import json
import re

import pytest

from core.plan import INVEST_MAX, PARTNER_MAX
from core.taxonomy import TaxonomyLoader
from web.generate import _script_safe, build_json, build_transitions, render


@pytest.fixture(scope="module")
def loader():
    return TaxonomyLoader("taxonomy")


@pytest.fixture(scope="module")
def transitions(loader):
    return build_transitions(loader)


@pytest.fixture(scope="module")
def page(loader):
    return render(loader)


def _embedded(page: str, element_id: str) -> dict:
    match = re.search(
        r'<script type="application/json" id="%s">(.*?)</script>' % element_id, page, re.S
    )
    assert match, f"no embedded JSON block with id={element_id}"
    return json.loads(match.group(1))


def _const(page: str, name: str) -> dict:
    match = re.search(r"^const %s = (\{.*?\});$" % name, page, re.M)
    assert match, f"no `const {name}` in the page"
    return json.loads(match.group(1))


# --- Build contract ---------------------------------------------------------


def test_no_placeholders_survive(page):
    leftovers = re.findall(r"__[A-Z_]+__", page)
    assert leftovers == [], f"unfilled placeholders: {sorted(set(leftovers))}"


def test_page_is_self_contained(page):
    """A CDN reference would break offline use and the 'one file' promise."""
    assert "<script src=" not in page
    assert 'rel="stylesheet"' not in page
    for host in ("cdn.", "unpkg.com", "jsdelivr", "googleapis.com"):
        assert host not in page, f"external dependency on {host}"


def test_missing_placeholder_is_a_loud_failure(loader, monkeypatch, tmp_path):
    from web import generate

    stub = tmp_path / "template.html"
    stub.write_text("<html>__TAXONOMY_JSON__ only</html>", encoding="utf-8")
    monkeypatch.setattr(generate, "TEMPLATE", stub)
    with pytest.raises(ValueError, match="__RESOURCES_JSON__"):
        generate.render(loader)


# --- Embedded data ----------------------------------------------------------


def test_taxonomy_block_parses_and_is_complete(page, loader):
    data = _embedded(page, "taxonomy-data")
    assert data["stats"] == loader.stats
    assert len(data["functions"]) == loader.stats["functions"]
    roles = [r for f in data["functions"] for r in f["roles"]]
    assert len(roles) == loader.stats["roles"]
    assert all(r["skills"] for r in roles)
    assert all("proficiency" in s for r in roles for s in r["skills"])


def test_every_role_ships_the_levels_the_plan_needs(page):
    for f in _embedded(page, "taxonomy-data")["functions"]:
        for r in f["roles"]:
            assert r["levels"], f"{f['id']}/{r['id']} has no levels"
            assert all(lv["id"] and lv["name"] for lv in r["levels"])


def test_plan_rules_shipped_to_the_browser_match_python(page):
    plan = _const(page, "PLAN")
    assert plan["investMax"] == INVEST_MAX
    assert plan["partnerMax"] == PARTNER_MAX
    assert set(plan["actions"]) == {"invest", "partner", "delegate"}


def test_script_safe_neutralises_a_closing_script_tag():
    payload = json.dumps({"bio": "</script><script>alert(1)</script>"})
    safe = _script_safe(payload)
    assert "</script>" not in safe
    assert json.loads(safe)["bio"] == "</script><script>alert(1)</script>"


def test_no_data_string_can_close_the_script_tag(page):
    body = page.split('id="taxonomy-data">', 1)[1]
    embedded, _ = body.split("</script>", 1)
    assert "<" not in embedded, "raw '<' in embedded JSON could close the tag early"


# --- Transitions ------------------------------------------------------------


def test_transitions_are_precomputed_for_every_role(transitions, loader):
    assert len(transitions) == loader.stats["roles"]
    assert all(isinstance(v, list) for v in transitions.values())


def test_transitions_never_point_at_their_own_role(transitions):
    for key, targets in transitions.items():
        func_id, role_id = key.split("/")
        for t in targets:
            assert (t["function_id"], t["role_id"]) != (func_id, role_id)


def test_transitions_are_ranked_by_overlap(transitions):
    for targets in transitions.values():
        overlaps = [t["skill_overlap_pct"] for t in targets]
        assert overlaps == sorted(overlaps, reverse=True)


def test_transition_payload_is_trimmed(transitions):
    from web.generate import GAP_SKILLS_PER_TRANSITION, TRANSITIONS_PER_ROLE

    for targets in transitions.values():
        assert len(targets) <= TRANSITIONS_PER_ROLE
        for t in targets:
            assert len(t["gap_skills"]) <= GAP_SKILLS_PER_TRANSITION


def test_build_json_attaches_transitions(loader, transitions):
    data = json.loads(build_json(loader, transitions))
    role = next(
        r for f in data["functions"] if f["id"] == "product"
        for r in f["roles"] if r["id"] == "product_manager"
    )
    assert role["transitions"], "product_manager should have transitions"


# --- Page shell -------------------------------------------------------------


def test_hero_is_static_markup_not_javascript(page):
    """The headline must paint before the multi-megabyte payload finishes."""
    head = page.split('id="taxonomy-data"')[0]
    assert 'id="home-hero"' in head
    assert "What is AI doing to your job?" in head
    assert 'id="q"' in head, "the search input must be in the static shell"


def test_social_and_theme_metadata_present(page):
    for tag in ('property="og:title"', 'name="twitter:card"', 'name="theme-color"', 'rel="icon"'):
        assert tag in page, f"missing {tag}"


def test_both_themes_are_defined(page):
    assert "prefers-color-scheme:dark" in page
    assert ':root[data-theme="dark"]' in page


def test_print_stylesheet_exists(page):
    assert "@media print" in page
