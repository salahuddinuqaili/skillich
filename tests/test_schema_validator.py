"""Tests for the taxonomy schema validator."""

import os
import tempfile

import pytest
import yaml

jsonschema_mod = pytest.importorskip("jsonschema")

from core.schema_validator import validate_taxonomy  # noqa: E402


VALID_FUNCTION = {
    "function": {
        "id": "test_func",
        "name": "Test Function",
        "description": "A test function for validation.",
        "roles": ["test_role"],
    }
}

VALID_ROLE = {
    "role": {
        "id": "test_role",
        "function": "test_func",
        "name": "Test Role",
        "description": "A test role for validation.",
        "also_known_as": ["Tester"],
        "ai_impact": {
            "level": "moderate",
            "summary": "AI has moderate impact.",
            "automating": ["Simple tasks"],
            "augmenting": ["Complex tasks"],
            "preserving": ["Human tasks"],
        },
        "levels": [
            {"id": "junior", "name": "Junior", "years_experience": "0-2", "summary": "Entry level."},
            {"id": "mid", "name": "Mid", "years_experience": "2-5", "summary": "Mid level."},
            {"id": "senior", "name": "Senior", "years_experience": "5-8", "summary": "Senior level."},
            {"id": "staff", "name": "Staff", "years_experience": "8-12", "summary": "Staff level."},
            {"id": "principal", "name": "Principal", "years_experience": "12+", "summary": "Principal."},
        ],
        "skills": [
            {
                "id": f"skill_{i}",
                "name": f"Skill {i}",
                "category": "technical",
                "description": f"Description for skill {i}.",
                "proficiency": {
                    "junior": "Basic.",
                    "mid": "Intermediate.",
                    "senior": "Advanced.",
                    "staff": "Expert.",
                    "principal": "Visionary.",
                },
                "ai_impact": {"rating": 0.5, "detail": "Moderate AI impact."},
            }
            for i in range(5)
        ],
    }
}


def _write_taxonomy(tmp_dir, func_data, role_data):
    """Write a minimal taxonomy to a temp directory."""
    func_dir = os.path.join(tmp_dir, func_data["function"]["id"])
    os.makedirs(func_dir, exist_ok=True)
    with open(os.path.join(func_dir, "_function.yaml"), "w") as f:
        yaml.dump(func_data, f)
    with open(os.path.join(func_dir, f"{role_data['role']['id']}.yaml"), "w") as f:
        yaml.dump(role_data, f)


class TestValidTaxonomy:

    def test_valid_taxonomy_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_taxonomy(tmp, VALID_FUNCTION, VALID_ROLE)
            report = validate_taxonomy(tmp)
            assert report.ok
            assert report.files_checked == 2

    def test_real_taxonomy_passes(self):
        report = validate_taxonomy("taxonomy")
        assert report.ok, f"Errors: {report.errors[:5]}"
        assert report.files_checked >= 45


class TestInvalidTaxonomy:

    def test_missing_required_field(self):
        bad_role = {
            "role": {
                "id": "test_role",
                "function": "test_func",
                "name": "Test Role",
                # missing description, ai_impact, levels, skills
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            _write_taxonomy(tmp, VALID_FUNCTION, bad_role)
            report = validate_taxonomy(tmp)
            assert not report.ok
            assert any("required" in e.lower() or "description" in e.lower() for e in report.errors)

    def test_invalid_ai_impact_level(self):
        import copy
        bad_role = copy.deepcopy(VALID_ROLE)
        bad_role["role"]["ai_impact"]["level"] = "extreme"
        with tempfile.TemporaryDirectory() as tmp:
            _write_taxonomy(tmp, VALID_FUNCTION, bad_role)
            report = validate_taxonomy(tmp)
            assert not report.ok
            assert any("extreme" in e for e in report.errors)

    def test_invalid_rating_range(self):
        import copy
        bad_role = copy.deepcopy(VALID_ROLE)
        bad_role["role"]["skills"][0]["ai_impact"]["rating"] = 1.5
        with tempfile.TemporaryDirectory() as tmp:
            _write_taxonomy(tmp, VALID_FUNCTION, bad_role)
            report = validate_taxonomy(tmp)
            assert not report.ok

    def test_invalid_category(self):
        import copy
        bad_role = copy.deepcopy(VALID_ROLE)
        bad_role["role"]["skills"][0]["category"] = "magic"
        with tempfile.TemporaryDirectory() as tmp:
            _write_taxonomy(tmp, VALID_FUNCTION, bad_role)
            report = validate_taxonomy(tmp)
            assert not report.ok
            assert any("magic" in e for e in report.errors)

    def test_too_few_skills(self):
        import copy
        bad_role = copy.deepcopy(VALID_ROLE)
        bad_role["role"]["skills"] = bad_role["role"]["skills"][:2]
        with tempfile.TemporaryDirectory() as tmp:
            _write_taxonomy(tmp, VALID_FUNCTION, bad_role)
            report = validate_taxonomy(tmp)
            assert not report.ok

    def test_nonexistent_directory(self):
        report = validate_taxonomy("/nonexistent/path")
        assert not report.ok
        assert any("not found" in e.lower() for e in report.errors)

    def test_missing_function_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            func_dir = os.path.join(tmp, "test_func")
            os.makedirs(func_dir)
            # Write a role but no _function.yaml
            with open(os.path.join(func_dir, "test_role.yaml"), "w") as f:
                yaml.dump(VALID_ROLE, f)
            report = validate_taxonomy(tmp)
            assert not report.ok
            assert any("missing _function.yaml" in e for e in report.errors)
