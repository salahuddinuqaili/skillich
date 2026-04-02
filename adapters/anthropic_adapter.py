"""Anthropic tool_use adapter for skillich skills."""

from typing import Any, Dict, List

from core.registry import SkillRegistry


def create_anthropic_tools(registry: SkillRegistry) -> List[Dict[str, Any]]:
    """Convert all registered skills to Anthropic tool_use format."""
    return registry.to_anthropic_tools()


def handle_tool_use(registry: SkillRegistry, tool_name: str, tool_input: Dict[str, Any]) -> Dict:
    """Execute a skill from an Anthropic tool_use block and return the result."""
    result = registry.call_skill(tool_name, **tool_input)
    return result.to_dict()


def anthropic_message_loop(registry: SkillRegistry, client: Any, model: str = "claude-sonnet-4-20250514",
                           messages: List[Dict] = None, system: str = "") -> str:
    """Run a single message with tool use. Requires anthropic package installed.

    Returns the final assistant text content.
    """
    import json
    tools = create_anthropic_tools(registry)

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=messages,
        tools=tools,
    )

    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = handle_tool_use(registry, block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=tools,
        )

    for block in response.content:
        if hasattr(block, "text"):
            return block.text
    return ""
