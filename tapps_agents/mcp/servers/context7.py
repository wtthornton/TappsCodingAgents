"""
Context7 MCP Server - Library documentation resolution and retrieval.
"""

from collections.abc import Callable
from typing import Any

from ..tool_registry import ToolCategory, ToolRegistry


class Context7MCPServer:
    """MCP server for Context7 library documentation."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        resolve_library_client: Callable[[str], Any] | None = None,
        get_docs_client: Callable[
            [str, str | None, str | None, int | None], Any
        ]
        | None = None,
    ):
        """
        Initialize Context7 MCP server.

        Args:
            registry: Optional ToolRegistry instance
            resolve_library_client: Optional function to call MCP Context7 resolve-library-id tool
            get_docs_client: Optional function to call MCP Context7 get-library-docs tool
        """
        self.registry = registry or ToolRegistry()
        self.resolve_library_client = resolve_library_client
        self.get_docs_client = get_docs_client
        self._register_tools()

    def _register_tools(self):
        """Register Context7 tools."""
        self.registry.register(
            name="mcp_Context7_resolve-library-id",
            description="Resolve library/package name to Context7-compatible ID",
            category=ToolCategory.CUSTOM,
            handler=self.resolve_library_id,
            parameters={
                "libraryName": {
                    "type": "string",
                    "required": True,
                    "description": "Library/package name to resolve (e.g., 'react', 'fastapi')",
                }
            },
            cache_strategy="tier2",
            requires_auth=False,
        )

        self.registry.register(
            name="mcp_Context7_get-library-docs",
            description="Fetch up-to-date documentation for a library from Context7",
            category=ToolCategory.CUSTOM,
            handler=self.get_library_docs,
            parameters={
                "context7CompatibleLibraryID": {
                    "type": "string",
                    "required": True,
                    "description": "Context7-compatible library ID (e.g., '/vercel/next.js')",
                },
                "topic": {
                    "type": "string",
                    "required": False,
                    "description": "Focus documentation on specific topic (e.g., 'hooks', 'routing')",
                },
                "mode": {
                    "type": "string",
                    "required": False,
                    "description": "Documentation mode: 'code' (default) for API references, 'info' for conceptual guides",
                    "default": "code",
                },
                "page": {
                    "type": "integer",
                    "required": False,
                    "description": "Page number for pagination (1-10, default: 1)",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            cache_strategy="tier2",
            requires_auth=False,
        )

    def resolve_library_id(self, libraryName: str) -> dict[str, Any]:
        """
        Resolve library name to Context7-compatible ID.

        Args:
            libraryName: Library/package name (e.g., "react", "fastapi")

        Returns:
            Dictionary with list of matching libraries and their Context7 IDs

        Example response:
        {
            "library": "react",
            "matches": [
                {"id": "/facebook/react", "name": "React", "description": "..."},
                ...
            ]
        }
        """
        if self.resolve_library_client:
            try:
                result = self.resolve_library_client(libraryName)
                # Normalize the result format
                if isinstance(result, dict):
                    return result
                elif isinstance(result, list):
                    return {"library": libraryName, "matches": result}
                else:
                    return {
                        "library": libraryName,
                        "matches": [{"id": str(result), "name": libraryName}],
                    }
            except Exception as e:
                return {"library": libraryName, "matches": [], "error": str(e)}
        else:
            # No client available - return empty result
            # In a real scenario, this would call the actual MCP Context7 server
            return {
                "library": libraryName,
                "matches": [],
                "error": "Context7 MCP client not configured",
            }

    def get_library_docs(
        self,
        context7CompatibleLibraryID: str,
        topic: str | None = None,
        mode: str = "code",
        page: int = 1,
    ) -> dict[str, Any]:
        """
        Fetch library documentation from Context7.

        Args:
            context7CompatibleLibraryID: Context7-compatible library ID (e.g., "/vercel/next.js")
            topic: Optional topic to focus on (e.g., "hooks", "routing")
            mode: Documentation mode ("code" or "info")
            page: Page number for pagination (1-10)

        Returns:
            Dictionary with documentation content

        Example response:
        {
            "library_id": "/vercel/next.js",
            "topic": "hooks",
            "content": "# Next.js Hooks\n\n...",
            "mode": "code",
            "page": 1
        }
        """
        if self.get_docs_client:
            try:
                result = self.get_docs_client(
                    context7CompatibleLibraryID, topic, mode, page
                )
                # Normalize the result format
                if isinstance(result, str):
                    return {
                        "library_id": context7CompatibleLibraryID,
                        "topic": topic,
                        "content": result,
                        "mode": mode,
                        "page": page,
                    }
                elif isinstance(result, dict):
                    return result
                else:
                    return {
                        "library_id": context7CompatibleLibraryID,
                        "topic": topic,
                        "content": str(result),
                        "mode": mode,
                        "page": page,
                    }
            except Exception as e:
                return {
                    "library_id": context7CompatibleLibraryID,
                    "topic": topic,
                    "content": None,
                    "error": str(e),
                }
        else:
            # No client available - return error
            # In a real scenario, this would call the actual MCP Context7 server
            return {
                "library_id": context7CompatibleLibraryID,
                "topic": topic,
                "content": None,
                "error": "Context7 MCP client not configured",
            }
