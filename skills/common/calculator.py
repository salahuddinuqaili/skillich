"""Basic arithmetic skill for LLMs that need precise math."""

from typing import Any, Dict, List

from core.base import Skill, SkillResult, SkillStatus


class CalculatorSkill(Skill):
    """Perform basic arithmetic: addition, subtraction, multiplication, and division.

    Use this when you need exact numeric computation. Do NOT use for symbolic
    math, calculus, or statistics -- those require specialized skills.
    """

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "Perform exact arithmetic: add, subtract, multiply, or divide two numbers. "
            "Returns a precise numeric result. Use this instead of mental math for "
            "any calculation where precision matters."
        )

    @property
    def tags(self) -> List[str]:
        return ["math", "utility", "common"]

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The arithmetic operation to perform.",
                },
                "a": {"type": "number", "description": "The first operand."},
                "b": {"type": "number", "description": "The second operand."},
            },
            "required": ["operation", "a", "b"],
        }

    def execute(self, operation: str, a: float, b: float, **kwargs) -> SkillResult:
        ops = {
            "add": lambda: a + b,
            "subtract": lambda: a - b,
            "multiply": lambda: a * b,
            "divide": lambda: a / b if b != 0 else None,
        }

        if operation not in ops:
            return SkillResult(
                status=SkillStatus.ERROR,
                error=f"Unsupported operation: '{operation}'. Use: add, subtract, multiply, divide.",
            )

        if operation == "divide" and b == 0:
            return SkillResult(
                status=SkillStatus.ERROR,
                error="Cannot divide by zero.",
            )

        result = ops[operation]()
        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={"result": result, "expression": f"{a} {operation} {b} = {result}"},
        )
