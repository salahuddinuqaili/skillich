"""Tests for core.audit and the skillich audit CLI command."""

from __future__ import annotations

import json
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from core.audit import _parse_date, find_stale_roles


# ---------------------------------------------------------------------------
# Unit tests: _parse_date
# ---------------------------------------------------------------------------

class TestParseDate:

    def test_valid_date(self):
        assert _parse_date("2024-03-15") == date(2024, 3, 15)

    def test_date_with_surrounding_text(self):
        assert _parse_date("reviewed 2023-11-01 by team") == date(2023, 11, 1)

    def test_empty_string(self):
        assert _parse_date("") is None

    def test_none_like_empty(self):
        assert _parse_date(None) is None  # type: ignore[arg-type]

    def test_invalid_month(self):
        assert _parse_date("2024-13-01") is None

    def test_invalid_day(self):
        assert _parse_date("2024-01-32") is None

    def test_non_date_string(self):
        assert _parse_date("not-a-date") is None


# ---------------------------------------------------------------------------
# Unit tests: find_stale_roles (mocked loader)
# ---------------------------------------------------------------------------

def _stub_role(rd: dict) -> MagicMock:
    role = MagicMock()
    role.id = rd["role_id"]
    role.name = rd["role_name"]
    role.skills = [MagicMock()] * rd.get("skills_count", 3)
    role.ai_impact = MagicMock()
    role.ai_impact.last_reviewed = rd.get("last_reviewed", "")
    role.ai_impact.level = rd.get("ai_level", "moderate")
    role.ai_impact.confidence = rd.get("confidence", "")
    return role


def _make_mock_loader(roles_data: list) -> MagicMock:
    functions: dict = {}
    for rd in roles_data:
        fid = rd["function_id"]
        if fid not in functions:
            fn = MagicMock()
            fn.id = fid
            fn.name = rd["function_name"]
            functions[fid] = fn

    def list_functions():
        return list(functions.values())

    def list_roles(function_id: str):
        return [_stub_role(rd) for rd in roles_data if rd["function_id"] == function_id]

    def get_role(function_id: str, role_id: str):
        for rd in roles_data:
            if rd["function_id"] == function_id and rd["role_id"] == role_id:
                role = _stub_role(rd)
                return role
        return None

    loader = MagicMock()
    loader.list_functions.side_effect = list_functions
    loader.list_roles.side_effect = list_roles
    loader.get_role.side_effect = get_role
    return loader


class TestFindStaleRoles:

    def _fresh(self, days: int = 10) -> str:
        return (date.today() - timedelta(days=days)).isoformat()

    def _stale(self, days: int = 400) -> str:
        return (date.today() - timedelta(days=days)).isoformat()

    def test_all_fresh_returns_empty(self):
        loader = _make_mock_loader([{
            "function_id": "eng", "function_name": "Engineering",
            "role_id": "backend", "role_name": "Backend", "last_reviewed": self._fresh(30),
        }])
        assert find_stale_roles(loader, days=180) == []

    def test_stale_role_returned(self):
        loader = _make_mock_loader([{
            "function_id": "eng", "function_name": "Engineering",
            "role_id": "backend", "role_name": "Backend", "last_reviewed": self._stale(400),
        }])
        result = find_stale_roles(loader, days=180)
        assert len(result) == 1
        assert result[0].role_id == "backend"
        assert result[0].days_since_review == 400

    def test_missing_date_always_stale(self):
        loader = _make_mock_loader([{
            "function_id": "mkt", "function_name": "Marketing",
            "role_id": "writer", "role_name": "Writer", "last_reviewed": "",
        }])
        result = find_stale_roles(loader, days=180)
        assert len(result) == 1
        assert result[0].last_reviewed is None
        assert result[0].days_since_review is None

    def test_mixed_fresh_and_stale(self):
        loader = _make_mock_loader([
            {"function_id": "eng", "function_name": "Eng",
             "role_id": "backend", "role_name": "Backend", "last_reviewed": self._fresh(30)},
            {"function_id": "eng", "function_name": "Eng",
             "role_id": "frontend", "role_name": "Frontend", "last_reviewed": self._stale(400)},
        ])
        result = find_stale_roles(loader, days=180)
        assert len(result) == 1
        assert result[0].role_id == "frontend"

    def test_threshold_boundary(self):
        loader = _make_mock_loader([
            {"function_id": "eng", "function_name": "Eng",
             "role_id": "a", "role_name": "A",
             "last_reviewed": (date.today() - timedelta(days=180)).isoformat()},
            {"function_id": "eng", "function_name": "Eng",
             "role_id": "b", "role_name": "B",
             "last_reviewed": (date.today() - timedelta(days=181)).isoformat()},
        ])
        result = find_stale_roles(loader, days=180)
        ids = {r.role_id for r in result}
        assert "a" not in ids
        assert "b" in ids

    def test_sorted_stalest_first(self):
        loader = _make_mock_loader([
            {"function_id": "eng", "function_name": "Eng",
             "role_id": "a", "role_name": "A", "last_reviewed": self._stale(200)},
            {"function_id": "eng", "function_name": "Eng",
             "role_id": "b", "role_name": "B", "last_reviewed": self._stale(600)},
        ])
        result = find_stale_roles(loader, days=180)
        assert result[0].role_id == "b"

    def test_fields_populated(self):
        loader = _make_mock_loader([{
            "function_id": "mkt", "function_name": "Marketing",
            "role_id": "sdr", "role_name": "SDR",
            "last_reviewed": self._stale(300), "ai_level": "very-high",
            "confidence": "high", "skills_count": 7,
        }])
        r = find_stale_roles(loader, days=180)[0]
        assert r.function_id == "mkt"
        assert r.ai_impact_level == "very-high"
        assert r.confidence == "high"
        assert r.skill_count == 7


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

typer_mod = pytest.importorskip("typer")

from typer.testing import CliRunner  # noqa: E402
from cli.main import app  # noqa: E402

runner = CliRunner()


class TestAuditCommand:

    def test_audit_runs_ok(self):
        result = runner.invoke(app, ["audit", "--stale-after", "1"])
        assert result.exit_code == 0

    def test_audit_json_parseable(self):
        result = runner.invoke(app, ["audit", "--stale-after", "1", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_audit_json_fields(self):
        result = runner.invoke(app, ["audit", "--stale-after", "1", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        if data:
            r = data[0]
            for field in ("function_id", "role_id", "last_reviewed", "days_since_review", "ai_impact_level"):
                assert field in r

    def test_audit_csv_parseable(self):
        result = runner.invoke(app, ["audit", "--stale-after", "1", "--format", "csv"])
        assert result.exit_code == 0

    def test_audit_all_fresh_message(self):
        result = runner.invoke(app, ["audit", "--stale-after", "99999"])
        assert result.exit_code == 0
        assert "fresh" in result.output.lower() or "flagged" in result.output.lower()
