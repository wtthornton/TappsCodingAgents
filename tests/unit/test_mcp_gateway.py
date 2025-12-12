"""
Unit tests for MCP Gateway.
"""

from pathlib import Path

import pytest

from tapps_agents.mcp import MCPGateway, ToolCategory, ToolRegistry
from tapps_agents.mcp.servers.filesystem import FilesystemMCPServer


@pytest.mark.unit
class TestToolRegistry:
    """Test cases for ToolRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a ToolRegistry instance."""
        return ToolRegistry()

    def test_register_tool(self, registry):
        """Test tool registration."""

        def handler(**kwargs):
            return {"result": "test"}

        registry.register(
            name="test_tool",
            description="Test tool",
            category=ToolCategory.CUSTOM,
            handler=handler,
        )

        tool_def = registry.get("test_tool")
        assert tool_def is not None
        assert tool_def.name == "test_tool"
        assert tool_def.category == ToolCategory.CUSTOM

    def test_list_tools(self, registry):
        """Test listing tools."""

        def handler(**kwargs):
            return {}

        registry.register("tool1", "Tool 1", ToolCategory.CUSTOM, handler)
        registry.register("tool2", "Tool 2", ToolCategory.CUSTOM, handler)

        tools = registry.list_tools()
        assert "tool1" in tools
        assert "tool2" in tools

    def test_list_tools_by_category(self, registry):
        """Test listing tools by category."""

        def handler(**kwargs):
            return {}

        registry.register("fs_tool", "FS Tool", ToolCategory.FILESYSTEM, handler)
        registry.register("git_tool", "Git Tool", ToolCategory.GIT, handler)

        fs_tools = registry.list_tools(ToolCategory.FILESYSTEM)
        assert "fs_tool" in fs_tools
        assert "git_tool" not in fs_tools

    def test_unregister_tool(self, registry):
        """Test tool unregistration."""

        def handler(**kwargs):
            return {}

        registry.register("test_tool", "Test", ToolCategory.CUSTOM, handler)
        assert registry.get("test_tool") is not None

        result = registry.unregister("test_tool")
        assert result is True
        assert registry.get("test_tool") is None


@pytest.mark.unit
class TestMCPGateway:
    """Test cases for MCPGateway."""

    @pytest.fixture
    def gateway(self):
        """Create an MCPGateway instance."""
        return MCPGateway()

    def test_call_tool_success(self, gateway):
        """Test successful tool call."""

        def test_handler(value: int):
            return {"doubled": value * 2}

        gateway.registry.register(
            name="double",
            description="Double a value",
            category=ToolCategory.CUSTOM,
            handler=test_handler,
            parameters={"value": {"type": "integer"}},
        )

        result = gateway.call_tool("double", value=5)
        assert result["success"] is True
        assert result["result"]["doubled"] == 10

    def test_call_tool_not_found(self, gateway):
        """Test tool not found error."""
        with pytest.raises(ValueError, match="Tool not found"):
            gateway.call_tool("nonexistent_tool")

    def test_call_tool_error(self, gateway):
        """Test tool execution error."""

        def failing_handler():
            raise ValueError("Test error")

        gateway.registry.register(
            name="failing",
            description="Failing tool",
            category=ToolCategory.CUSTOM,
            handler=failing_handler,
        )

        result = gateway.call_tool("failing")
        assert result["success"] is False
        assert "error" in result
        assert result["error_type"] == "ValueError"

    def test_list_available_tools(self, gateway):
        """Test listing available tools."""

        def handler():
            return {}

        gateway.registry.register("tool1", "Tool 1", ToolCategory.CUSTOM, handler)
        gateway.registry.register("tool2", "Tool 2", ToolCategory.CUSTOM, handler)

        tools = gateway.list_available_tools()
        assert len(tools) == 2
        assert any(t["name"] == "tool1" for t in tools)

    def test_get_tool_info(self, gateway):
        """Test getting tool information."""

        def handler():
            return {}

        gateway.registry.register(
            name="test_tool",
            description="Test tool description",
            category=ToolCategory.CUSTOM,
            handler=handler,
            parameters={"param": {"type": "string"}},
            cache_strategy="tier1",
        )

        info = gateway.get_tool_info("test_tool")
        assert info is not None
        assert info["name"] == "test_tool"
        assert info["description"] == "Test tool description"
        assert info["cache_strategy"] == "tier1"


@pytest.mark.unit
class TestFilesystemMCPServer:
    """Test cases for FilesystemMCPServer."""

    @pytest.fixture
    def fs_server(self):
        """Create a FilesystemMCPServer instance."""
        return FilesystemMCPServer()

    @pytest.fixture
    def temp_file(self, tmp_path: Path):
        """Create a temporary file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        return test_file

    def test_read_file(self, fs_server, temp_file):
        """Test reading a file."""
        result = fs_server.read_file(str(temp_file))

        assert result["file_path"] == str(temp_file)
        assert result["content"] == "Hello, World!"
        assert result["size"] == 13

    def test_write_file(self, fs_server, tmp_path: Path):
        """Test writing a file."""
        test_file = tmp_path / "output.txt"
        result = fs_server.write_file(str(test_file), "Test content")

        assert result["written"] is True
        assert test_file.exists()
        assert test_file.read_text() == "Test content"

    def test_list_directory(self, fs_server, tmp_path: Path):
        """Test listing a directory."""
        # Create some files
        (tmp_path / "file1.txt").write_text("test")
        (tmp_path / "file2.txt").write_text("test")
        (tmp_path / "subdir").mkdir()

        result = fs_server.list_directory(str(tmp_path))

        assert result["count"] >= 3
        assert any(item["name"] == "file1.txt" for item in result["items"])
        assert any(item["name"] == "subdir" for item in result["items"])
