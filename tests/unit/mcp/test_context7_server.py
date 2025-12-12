"""
Tests for Context7 MCP Server.
"""

from unittest.mock import Mock

import pytest

from tapps_agents.mcp.servers.context7 import Context7MCPServer
from tapps_agents.mcp.tool_registry import ToolCategory, ToolRegistry


class TestContext7MCPServer:
    """Test Context7MCPServer functionality."""

    @pytest.fixture
    def registry(self):
        """Create tool registry."""
        return ToolRegistry()

    @pytest.fixture
    def server_no_client(self, registry):
        """Create Context7 server without clients."""
        return Context7MCPServer(registry=registry)

    def test_server_initialization(self, registry):
        """Test server initialization."""
        server = Context7MCPServer(registry=registry)

        assert server.registry is not None
        assert server.resolve_library_client is None
        assert server.get_docs_client is None

    def test_server_registers_tools(self, registry):
        """Test that server registers tools on initialization."""
        Context7MCPServer(registry=registry)

        # Check tools are registered
        resolve_tool = registry.get("mcp_Context7_resolve-library-id")
        assert resolve_tool is not None
        assert resolve_tool.category == ToolCategory.CUSTOM

        get_docs_tool = registry.get("mcp_Context7_get-library-docs")
        assert get_docs_tool is not None
        assert get_docs_tool.category == ToolCategory.CUSTOM

    def test_resolve_library_id_no_client(self, server_no_client):
        """Test resolve library ID without client."""
        result = server_no_client.resolve_library_id("react")

        assert isinstance(result, dict)
        assert result["library"] == "react"
        assert result["matches"] == []
        assert "error" in result
        assert "not configured" in result["error"]

    def test_resolve_library_id_with_client_dict(self):
        """Test resolve library ID with client returning dict."""
        registry = ToolRegistry()
        client_func = Mock(
            return_value={
                "library": "react",
                "matches": [
                    {
                        "id": "/facebook/react",
                        "name": "React",
                        "description": "React library",
                    }
                ],
            }
        )

        server = Context7MCPServer(
            registry=registry, resolve_library_client=client_func
        )

        result = server.resolve_library_id("react")

        assert result["library"] == "react"
        assert len(result["matches"]) == 1
        assert result["matches"][0]["id"] == "/facebook/react"
        client_func.assert_called_once_with("react")

    def test_resolve_library_id_with_client_list(self):
        """Test resolve library ID with client returning list."""
        registry = ToolRegistry()
        client_func = Mock(return_value=[{"id": "/facebook/react", "name": "React"}])

        server = Context7MCPServer(
            registry=registry, resolve_library_client=client_func
        )

        result = server.resolve_library_id("react")

        assert result["library"] == "react"
        assert len(result["matches"]) == 1
        assert result["matches"][0]["id"] == "/facebook/react"

    def test_resolve_library_id_with_client_string(self):
        """Test resolve library ID with client returning string."""
        registry = ToolRegistry()
        client_func = Mock(return_value="/facebook/react")

        server = Context7MCPServer(
            registry=registry, resolve_library_client=client_func
        )

        result = server.resolve_library_id("react")

        assert result["library"] == "react"
        assert len(result["matches"]) == 1
        assert result["matches"][0]["id"] == "/facebook/react"

    def test_resolve_library_id_client_exception(self):
        """Test resolve library ID when client raises exception."""
        registry = ToolRegistry()
        client_func = Mock(side_effect=Exception("Network error"))

        server = Context7MCPServer(
            registry=registry, resolve_library_client=client_func
        )

        result = server.resolve_library_id("react")

        assert result["library"] == "react"
        assert result["matches"] == []
        assert "error" in result
        assert "Network error" in result["error"]

    def test_get_library_docs_no_client(self, server_no_client):
        """Test get library docs without client."""
        result = server_no_client.get_library_docs("/facebook/react", "hooks")

        assert isinstance(result, dict)
        assert result["library_id"] == "/facebook/react"
        assert result["topic"] == "hooks"
        assert result["content"] is None
        assert "error" in result
        assert "not configured" in result["error"]

    def test_get_library_docs_with_client_string(self):
        """Test get library docs with client returning string."""
        registry = ToolRegistry()
        client_func = Mock(
            return_value="# React Hooks\n\nUse hooks for state management."
        )

        server = Context7MCPServer(registry=registry, get_docs_client=client_func)

        result = server.get_library_docs("/facebook/react", "hooks", "code", 1)

        assert result["library_id"] == "/facebook/react"
        assert result["topic"] == "hooks"
        assert result["mode"] == "code"
        assert result["page"] == 1
        assert "React Hooks" in result["content"]
        client_func.assert_called_once_with("/facebook/react", "hooks", "code", 1)

    def test_get_library_docs_with_client_dict(self):
        """Test get library docs with client returning dict."""
        registry = ToolRegistry()
        client_func = Mock(
            return_value={
                "content": "# React Hooks\n\nUse hooks.",
                "library_id": "/facebook/react",
                "topic": "hooks",
            }
        )

        server = Context7MCPServer(registry=registry, get_docs_client=client_func)

        result = server.get_library_docs("/facebook/react", "hooks")

        assert result["library_id"] == "/facebook/react"
        assert result["topic"] == "hooks"
        assert "React Hooks" in result["content"]

    def test_get_library_docs_default_parameters(self):
        """Test get library docs with default parameters."""
        registry = ToolRegistry()
        client_func = Mock(return_value="# React Hooks")

        server = Context7MCPServer(registry=registry, get_docs_client=client_func)

        result = server.get_library_docs("/facebook/react")

        assert result["topic"] is None
        assert result["mode"] == "code"
        assert result["page"] == 1
        client_func.assert_called_once_with("/facebook/react", None, "code", 1)

    def test_get_library_docs_client_exception(self):
        """Test get library docs when client raises exception."""
        registry = ToolRegistry()
        client_func = Mock(side_effect=Exception("API error"))

        server = Context7MCPServer(registry=registry, get_docs_client=client_func)

        result = server.get_library_docs("/facebook/react", "hooks")

        assert result["library_id"] == "/facebook/react"
        assert result["topic"] == "hooks"
        assert result["content"] is None
        assert "error" in result
        assert "API error" in result["error"]

    def test_tool_parameters(self, registry):
        """Test that tools have correct parameters defined."""
        Context7MCPServer(registry=registry)

        resolve_tool = registry.get("mcp_Context7_resolve-library-id")
        assert "libraryName" in resolve_tool.parameters
        assert resolve_tool.parameters["libraryName"]["required"] is True

        get_docs_tool = registry.get("mcp_Context7_get-library-docs")
        assert "context7CompatibleLibraryID" in get_docs_tool.parameters
        assert (
            get_docs_tool.parameters["context7CompatibleLibraryID"]["required"] is True
        )
        assert "topic" in get_docs_tool.parameters
        assert get_docs_tool.parameters["topic"]["required"] is False
        assert "mode" in get_docs_tool.parameters
        assert "page" in get_docs_tool.parameters
