# ==============================================================================
# AI Service — Tool Registry for Agent
# ==============================================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Awaitable

from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ToolResult:
    """Result of a tool execution."""
    output: str
    success: bool = True
    error: str | None = None


@dataclass
class ToolDefinition:
    """Definition of a tool available to the agent."""
    name: str
    description: str
    parameters_schema: dict
    handler: Callable[..., Awaitable[ToolResult]]


class ToolRegistry:
    """
    Registry of tools available to the agent.

    Tools can be registered from:
    - Built-in tools (document search, code execution)
    - Plugins (via Plugin Service)
    - Custom tools added at runtime
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool
        logger.info(f"Tool registered: {tool.name}")

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry."""
        self._tools.pop(name, None)

    def get(self, name: str) -> ToolDefinition | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_tool_descriptions(self) -> str:
        """Generate a formatted string of tool descriptions for the LLM prompt."""
        descriptions = []
        for tool in self._tools.values():
            desc = f"- {tool.name}: {tool.description}"
            if tool.parameters_schema:
                params = json.dumps(tool.parameters_schema, indent=2)
                desc += f"\n  Parameters: {params}"
            descriptions.append(desc)
        return "\n".join(descriptions)

    def get_openai_tool_definitions(self) -> list[dict]:
        """Convert tools to OpenAI function calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters_schema,
                },
            }
            for tool in self._tools.values()
        ]

    async def execute(self, tool_name: str, params: str) -> ToolResult:
        """Execute a tool by name with the given parameters."""
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolResult(
                output=f"Error: Tool '{tool_name}' not found.",
                success=False,
                error=f"Unknown tool: {tool_name}",
            )

        try:
            # Parse parameters
            if isinstance(params, str):
                try:
                    parsed_params = json.loads(params)
                except json.JSONDecodeError:
                    parsed_params = {"input": params}
            else:
                parsed_params = params

            logger.info(
                f"Executing tool: {tool_name}",
                extra={"params": str(parsed_params)[:200]},
            )

            result = await tool.handler(**parsed_params)
            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} — {e}")
            return ToolResult(
                output=f"Error executing {tool_name}: {str(e)}",
                success=False,
                error=str(e),
            )
