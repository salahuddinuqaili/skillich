"""Tests for LLM adapter code (testable parts -- no external API calls)."""

import json

from adapters.anthropic_adapter import create_anthropic_tools, handle_tool_use
from adapters.openai_adapter import create_openai_tools, handle_tool_call
from core.registry import SkillRegistry
from skills.common.calculator import CalculatorSkill


def _populated_registry():
    reg = SkillRegistry()
    reg.register(CalculatorSkill())
    return reg


class TestOpenAIAdapter:

    def test_create_tools_format(self):
        tools = create_openai_tools(_populated_registry())
        assert len(tools) == 1
        tool = tools[0]
        assert tool["type"] == "function"
        assert tool["function"]["name"] == "calculator"
        assert "parameters" in tool["function"]

    def test_handle_tool_call_success(self):
        result = handle_tool_call(
            _populated_registry(), "calculator", {"operation": "add", "a": 2, "b": 3}
        )
        assert result["status"] == "success"
        assert result["data"]["result"] == 5

    def test_handle_tool_call_not_found(self):
        result = handle_tool_call(_populated_registry(), "nonexistent", {})
        assert result["status"] == "error"


class TestAnthropicAdapter:

    def test_create_tools_format(self):
        tools = create_anthropic_tools(_populated_registry())
        assert len(tools) == 1
        tool = tools[0]
        assert tool["name"] == "calculator"
        assert "input_schema" in tool

    def test_handle_tool_use_success(self):
        result = handle_tool_use(
            _populated_registry(), "calculator", {"operation": "multiply", "a": 4, "b": 5}
        )
        assert result["status"] == "success"
        assert result["data"]["result"] == 20

    def test_handle_tool_use_validation_error(self):
        result = handle_tool_use(
            _populated_registry(), "calculator", {"operation": "add"}
        )
        assert result["status"] == "error"


class TestExportFormats:
    """Test that export outputs are valid and parseable."""

    def test_csv_export_valid(self):
        import csv
        import io
        from cli.export import export_csv
        from core.taxonomy import TaxonomyLoader

        loader = TaxonomyLoader("taxonomy")
        content = export_csv(loader, "engineering", "backend")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        # Header + data rows
        assert len(rows) > 1
        header = rows[0]
        assert "function" in header
        assert "skill_name" in header
        assert "ai_impact_rating" in header
        # Every row has same number of columns
        for row in rows:
            assert len(row) == len(header)

    def test_json_export_valid(self):
        from cli.export import export_json
        from core.taxonomy import TaxonomyLoader

        loader = TaxonomyLoader("taxonomy")
        content = export_json(loader, "engineering", "backend")
        data = json.loads(content)
        assert data["name"] == "Backend Engineer"
        assert len(data["skills"]) > 0

    def test_json_export_function(self):
        from cli.export import export_json
        from core.taxonomy import TaxonomyLoader

        loader = TaxonomyLoader("taxonomy")
        content = export_json(loader, "engineering")
        data = json.loads(content)
        assert isinstance(data, list)
        assert len(data) >= 10  # engineering has 10 roles
