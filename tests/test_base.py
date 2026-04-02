"""Tests for core.base module."""


from core.base import AsyncSkill, SkillResult, SkillStatus


class TestSkillResult:
    def test_success_result(self):
        r = SkillResult(status=SkillStatus.SUCCESS, data=42)
        assert r.ok
        assert r.to_dict() == {"status": "success", "data": 42}

    def test_error_result(self):
        r = SkillResult(status=SkillStatus.ERROR, error="something broke")
        assert not r.ok
        d = r.to_dict()
        assert d["status"] == "error"
        assert d["error"] == "something broke"

    def test_metadata_and_duration(self):
        r = SkillResult(
            status=SkillStatus.SUCCESS,
            data="ok",
            metadata={"source": "test"},
            duration_ms=12.5,
        )
        d = r.to_dict()
        assert d["metadata"] == {"source": "test"}
        assert d["duration_ms"] == 12.5

    def test_empty_fields_omitted(self):
        r = SkillResult(status=SkillStatus.SUCCESS)
        d = r.to_dict()
        assert "error" not in d
        assert "metadata" not in d
        assert "duration_ms" not in d


class TestSkillInterface:
    def test_required_properties(self, dummy_skill):
        assert dummy_skill.name == "dummy"
        assert isinstance(dummy_skill.description, str)
        assert isinstance(dummy_skill.parameters, dict)
        assert dummy_skill.version == "1.0.0"
        assert dummy_skill.tags == ["test"]

    def test_openai_format(self, dummy_skill):
        tool = dummy_skill.to_openai_tool()
        assert tool["type"] == "function"
        assert tool["function"]["name"] == "dummy"
        assert "parameters" in tool["function"]

    def test_anthropic_format(self, dummy_skill):
        tool = dummy_skill.to_anthropic_tool()
        assert tool["name"] == "dummy"
        assert "input_schema" in tool

    def test_mcp_format(self, dummy_skill):
        tool = dummy_skill.to_mcp_tool()
        assert tool["name"] == "dummy"
        assert "inputSchema" in tool

    def test_execute_returns_skill_result(self, dummy_skill):
        result = dummy_skill.execute(message="hello")
        assert isinstance(result, SkillResult)
        assert result.ok
        assert result.data == {"echo": "hello"}


class TestAsyncSkill:
    def test_async_skill_sync_fallback(self):
        class MyAsyncSkill(AsyncSkill):
            @property
            def name(self):
                return "async_test"

            @property
            def description(self):
                return "Test async"

            @property
            def parameters(self):
                return {"type": "object", "properties": {}}

            async def execute_async(self, **kwargs):
                return SkillResult(status=SkillStatus.SUCCESS, data="async_ok")

        skill = MyAsyncSkill()
        result = skill.execute()
        assert result.ok
        assert result.data == "async_ok"
