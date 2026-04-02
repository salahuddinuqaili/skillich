"""Base classes for all skillich skills."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SkillStatus(Enum):
    """Status of a skill execution."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass
class SkillResult:
    """Standardized return type for all skill executions.

    Every skill returns a SkillResult so agents can reliably parse outputs
    regardless of which skill was invoked.
    """
    status: SkillStatus
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"status": self.status.value}
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        if self.metadata:
            result["metadata"] = self.metadata
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        return result

    @property
    def ok(self) -> bool:
        return self.status == SkillStatus.SUCCESS


class Skill(ABC):
    """Base class for all synchronous skills in skillich.

    A skill is a self-contained capability that an AI agent can invoke.
    Subclass this and implement name, description, parameters, and execute.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this skill. Use snake_case."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """What this skill does. Written for LLM consumption -- be specific
        about when to use it, what it returns, and when NOT to use it."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON Schema for the parameters this skill accepts."""
        ...

    @property
    def version(self) -> str:
        """Semantic version of this skill."""
        return "1.0.0"

    @property
    def tags(self) -> List[str]:
        """Tags for discovery and filtering (e.g., ['math', 'utility'])."""
        return []

    @abstractmethod
    def execute(self, **kwargs) -> SkillResult:
        """Run the skill with the given parameters. Must return a SkillResult."""
        ...

    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def to_anthropic_tool(self) -> Dict[str, Any]:
        """Convert to Anthropic tool_use format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def to_mcp_tool(self) -> Dict[str, Any]:
        """Convert to Model Context Protocol tool definition."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.parameters,
        }


class AsyncSkill(Skill):
    """Base class for skills that require async execution (I/O-bound operations).

    Implement execute_async instead of execute. The synchronous execute()
    is provided as a fallback that runs the async version in an event loop.
    """

    @abstractmethod
    async def execute_async(self, **kwargs) -> SkillResult:
        """Async implementation of the skill."""
        ...

    def execute(self, **kwargs) -> SkillResult:
        """Synchronous fallback -- runs execute_async in an event loop."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, self.execute_async(**kwargs)).result()
        return asyncio.run(self.execute_async(**kwargs))
