"""Tests for the CLI commands."""

import json

import pytest

typer_mod = pytest.importorskip("typer")

from typer.testing import CliRunner  # noqa: E402

from cli.main import app  # noqa: E402

runner = CliRunner()


class TestExplore:

    def test_list_functions(self):
        result = runner.invoke(app, ["explore"])
        assert result.exit_code == 0
        assert "engineering" in result.output.lower()

    def test_list_roles(self):
        result = runner.invoke(app, ["explore", "--function", "engineering"])
        assert result.exit_code == 0
        assert "Backend" in result.output

    def test_get_role(self):
        result = runner.invoke(app, ["explore", "--function", "engineering", "--role", "backend"])
        assert result.exit_code == 0
        assert "Backend Engineer" in result.output

    def test_search(self):
        result = runner.invoke(app, ["explore", "--search", "python"])
        assert result.exit_code == 0
        assert "results" in result.output.lower()

    def test_invalid_function(self):
        result = runner.invoke(app, ["explore", "--function", "nonexistent"])
        assert result.exit_code == 1


class TestImpact:

    def test_resilient(self):
        result = runner.invoke(app, ["impact", "--resilient", "--limit", "3"])
        assert result.exit_code == 0
        assert "Resilient" in result.output

    def test_automatable(self):
        result = runner.invoke(app, ["impact", "--automatable", "--limit", "3"])
        assert result.exit_code == 0
        assert "Automatable" in result.output

    def test_compare(self):
        result = runner.invoke(app, ["impact", "--function", "engineering", "--compare"])
        assert result.exit_code == 0
        assert "Backend" in result.output

    def test_role_impact(self):
        result = runner.invoke(app, ["impact", "--function", "engineering", "--role", "backend"])
        assert result.exit_code == 0
        assert "Backend" in result.output

    def test_no_args(self):
        result = runner.invoke(app, ["impact"])
        assert result.exit_code == 1


class TestLearn:

    def test_learning_path(self):
        result = runner.invoke(app, ["learn", "--function", "engineering", "--role", "backend", "--level", "senior"])
        assert result.exit_code == 0
        assert "Learning Path" in result.output


class TestExport:

    def test_csv(self):
        result = runner.invoke(app, ["export", "--function", "engineering", "--role", "backend", "--format", "csv"])
        assert result.exit_code == 0
        assert "function,role,skill_name" in result.output

    def test_json(self):
        result = runner.invoke(app, ["export", "--function", "engineering", "--role", "backend", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "Backend Engineer"

    def test_invalid_format(self):
        result = runner.invoke(app, ["export", "--function", "engineering", "--format", "xml"])
        assert result.exit_code == 1


class TestStats:

    def test_stats(self):
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "functions" in result.output.lower() or "roles" in result.output.lower() or "skills" in result.output.lower()


class TestFormatFlag:
    """--format json/csv on explore, impact, learn, transitions commands."""

    def test_explore_json_functions(self):
        result = runner.invoke(app, ["explore", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "functions" in data
        assert len(data["functions"]) >= 17

    def test_explore_json_role(self):
        result = runner.invoke(app, ["explore", "--function", "engineering", "--role", "backend", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "Backend Engineer"

    def test_explore_json_roles_list(self):
        result = runner.invoke(app, ["explore", "--function", "engineering", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "roles" in data
        assert len(data["roles"]) >= 1

    def test_explore_csv_functions(self):
        result = runner.invoke(app, ["explore", "--format", "csv"])
        assert result.exit_code == 0
        # The functions list is a dict with a 'functions' key — CSV emits key-value pairs
        # At minimum there must be output with the 'functions' key
        assert "functions" in result.output

    def test_impact_json_resilient(self):
        result = runner.invoke(app, ["impact", "--resilient", "--limit", "5", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "skills" in data
        assert len(data["skills"]) <= 5

    def test_impact_json_role(self):
        result = runner.invoke(app, [
            "impact", "--function", "engineering", "--role", "backend", "--format", "json"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "role" in data or "name" in data or "level" in data

    def test_json_output_no_ansi(self):
        """JSON output must contain no ANSI escape codes."""
        result = runner.invoke(app, ["explore", "--format", "json"])
        assert result.exit_code == 0
        assert "\x1b[" not in result.output
        assert "\033[" not in result.output

