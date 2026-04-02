"""OpenAI function calling adapter for skillich skills."""

from typing import Any, Dict, List

from core.registry import SkillRegistry


def create_openai_tools(registry: SkillRegistry) -> List[Dict[str, Any]]:
    """Convert all registered skills to OpenAI function calling format."""
    return registry.to_openai_tools()


def handle_tool_call(registry: SkillRegistry, tool_name: str, arguments: Dict[str, Any]) -> Dict:
    """Execute a skill from an OpenAI tool call and return the result as a dict."""
    result = registry.call_skill(tool_name, **arguments)
    return result.to_dict()


def openai_chat_loop(registry: SkillRegistry, client: Any, model: str = "gpt-4o",
                     messages: List[Dict] = None) -> str:
    """Run a single chat completion with tool use. Requires openai package installed.

    Returns the final assistant message content.
    """
    tools = create_openai_tools(registry)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
    )

    msg = response.choices[0].message

    while msg.tool_calls:
        messages.append(msg)
        for tool_call in msg.tool_calls:
            import json
            args = json.loads(tool_call.function.arguments)
            result = handle_tool_call(registry, tool_call.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
        )
        msg = response.choices[0].message

    return msg.content
