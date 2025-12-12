"""
MCP Gateway - Unified interface for tool access.
"""

from typing import Any

from .tool_registry import ToolCategory, ToolRegistry


class MCPGateway:
    """Gateway for routing tool requests to appropriate servers."""

    def __init__(self, registry: ToolRegistry | None = None):
        self.registry = registry or ToolRegistry()
        self._servers: dict[ToolCategory, Any] = {}

    def register_server(self, category: ToolCategory, server: Any):
        """
        Register an MCP server for a category.

        Args:
            category: Tool category
            server: Server instance
        """
        self._servers[category] = server

    def call_tool(self, tool_name: str, **kwargs) -> dict[str, Any]:
        """
        Call a tool through the gateway.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments

        Returns:
            Tool result dictionary

        Raises:
            ValueError: If tool not found
            RuntimeError: If tool execution fails
        """
        tool_def = self.registry.get(tool_name)
        if not tool_def:
            raise ValueError(f"Tool not found: {tool_name}")

        try:
            # Execute tool handler
            result = tool_def.handler(**kwargs)

            # Wrap result in standard format
            return {"success": True, "tool": tool_name, "result": result}
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def list_available_tools(
        self, category: ToolCategory | None = None
    ) -> list[dict[str, Any]]:
        """
        List available tools.

        Args:
            category: Optional category filter

        Returns:
            List of tool information dictionaries
        """
        tool_names = self.registry.list_tools(category)

        tools_info = []
        for name in tool_names:
            tool_def = self.registry.get(name)
            if tool_def:
                tools_info.append(
                    {
                        "name": tool_def.name,
                        "description": tool_def.description,
                        "category": tool_def.category.value,
                        "parameters": tool_def.parameters,
                        "cache_strategy": tool_def.cache_strategy,
                        "requires_auth": tool_def.requires_auth,
                    }
                )

        return tools_info

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """
        Get information about a specific tool.

        Args:
            tool_name: Tool name

        Returns:
            Tool information dictionary or None
        """
        tool_def = self.registry.get(tool_name)
        if not tool_def:
            return None

        return {
            "name": tool_def.name,
            "description": tool_def.description,
            "category": tool_def.category.value,
            "parameters": tool_def.parameters,
            "cache_strategy": tool_def.cache_strategy,
            "requires_auth": tool_def.requires_auth,
        }
