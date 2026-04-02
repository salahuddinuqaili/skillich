"""Tests for the calculator skill."""



class TestCalculatorSkill:
    def test_add(self, calculator_skill):
        r = calculator_skill.execute(operation="add", a=2, b=3)
        assert r.ok
        assert r.data["result"] == 5

    def test_subtract(self, calculator_skill):
        r = calculator_skill.execute(operation="subtract", a=10, b=4)
        assert r.ok
        assert r.data["result"] == 6

    def test_multiply(self, calculator_skill):
        r = calculator_skill.execute(operation="multiply", a=7, b=6)
        assert r.ok
        assert r.data["result"] == 42

    def test_divide(self, calculator_skill):
        r = calculator_skill.execute(operation="divide", a=10, b=4)
        assert r.ok
        assert r.data["result"] == 2.5

    def test_divide_by_zero(self, calculator_skill):
        r = calculator_skill.execute(operation="divide", a=10, b=0)
        assert not r.ok
        assert "zero" in r.error.lower()

    def test_invalid_operation(self, calculator_skill):
        r = calculator_skill.execute(operation="sqrt", a=9, b=0)
        assert not r.ok

    def test_expression_string(self, calculator_skill):
        r = calculator_skill.execute(operation="add", a=1, b=2)
        assert "1 add 2 = 3" in r.data["expression"]
