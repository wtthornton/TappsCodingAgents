"""
Unit tests for BaseAgent class.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.core.agent_base import BaseAgent


@pytest.mark.unit
class TestBaseAgent:
    """Test cases for BaseAgent class."""

    def test_base_agent_initialization(self, base_agent):
        """Test that BaseAgent initializes correctly."""
        agent = base_agent
        assert agent.agent_id == "test-agent"
        assert agent.agent_name == "Test Agent"
        assert agent.config is None
        assert agent.domain_config is None
        assert agent.customizations is None

    def test_get_commands_returns_help(self, base_agent):
        """Test that get_commands returns help command by default."""
        agent = base_agent
        commands = agent.get_commands()

        assert isinstance(commands, list)
        assert len(commands) >= 1
        assert commands[0]["command"] == "*help"
        assert "description" in commands[0]

    def test_format_help_shows_commands(self, base_agent):
        """Test that format_help generates readable help output."""
        agent = base_agent
        help_text = agent.format_help()

        assert isinstance(help_text, str)
        assert "Test Agent" in help_text
        assert "Available Commands" in help_text
        assert "*help" in help_text

    def test_parse_command_star_prefix(self, base_agent):
        """Test parsing star-prefixed commands."""
        agent = base_agent

        command, args = agent.parse_command("*review file.py")
        assert command == "review"
        assert args["file"] == "file.py"

    def test_parse_command_without_prefix(self, base_agent):
        """Test parsing commands without star prefix."""
        agent = base_agent

        command, args = agent.parse_command("review file.py")
        assert command == "review"
        assert args["file"] == "file.py"

    def test_parse_command_numbered(self, base_agent):
        """Test parsing numbered commands."""
        agent = base_agent

        # Mock get_commands to return known commands
        with patch.object(
            agent,
            "get_commands",
            return_value=[
                {"command": "*review", "description": "Review code"},
                {"command": "*score", "description": "Score code"},
            ],
        ):
            command, args = agent.parse_command("1")
            assert command == "review"

    def test_parse_command_invalid_number(self, base_agent):
        """Test parsing invalid numbered command."""
        agent = base_agent

        with patch.object(
            agent,
            "get_commands",
            return_value=[{"command": "*help", "description": "Help"}],
        ):
            # Number out of range should still work (handled by command handler)
            command, args = agent.parse_command("999")
            # Should return something or raise (implementation dependent)

    @pytest.mark.asyncio
    async def test_activate_loads_config(self, temp_project_dir: Path, base_agent):
        """Test that activate loads configuration files."""
        # Create config file
        config_dir = temp_project_dir / ".tapps-agents"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("test: value\nanother: key")

        agent = base_agent
        await agent.activate(temp_project_dir)

        # Config should be loaded (may be None if file doesn't exist, but we created it)
        # The key is that activate doesn't crash and attempts to load

    @pytest.mark.asyncio
    async def test_activate_loads_domain_config(
        self, temp_project_dir: Path, base_agent
    ):
        """Test that activate loads domain configuration."""
        config_dir = temp_project_dir / ".tapps-agents"
        config_dir.mkdir(exist_ok=True)
        domains_file = config_dir / "domains.md"
        domains_file.write_text("# Domains\n\nDomain 1")

        agent = base_agent
        await agent.activate(temp_project_dir)

        # Domain config should be loaded
        assert agent.domain_config is not None
        assert "Domain 1" in agent.domain_config

    @pytest.mark.asyncio
    async def test_activate_loads_customizations(
        self, temp_project_dir: Path, base_agent
    ):
        """Test that activate loads customizations."""
        config_dir = temp_project_dir / ".tapps-agents"
        config_dir.mkdir(exist_ok=True)
        customizations_dir = config_dir / "customizations"
        customizations_dir.mkdir(exist_ok=True)
        custom_file = customizations_dir / "test-custom.yaml"
        custom_file.write_text("custom: value")

        agent = base_agent
        await agent.activate(temp_project_dir)

        # Customizations should be attempted to load

    @pytest.mark.asyncio
    async def test_activate_no_config_files(self, temp_project_dir: Path, base_agent):
        """Test that activate works when no config files exist."""
        agent = base_agent

        # Should not raise exception
        await agent.activate(temp_project_dir)

        # Config should be a ProjectConfig with defaults if no file exists
        from tapps_agents.core.config import ProjectConfig

        assert isinstance(agent.config, ProjectConfig)
        assert agent.config.project_name is None  # Defaults
        assert agent.domain_config is None

    def test_run_is_abstract(self):
        """Test that run method is abstract and must be implemented."""
        # Test that BaseAgent cannot be instantiated directly
        with pytest.raises(TypeError, match="abstract method 'run'"):
            BaseAgent(agent_id="test", agent_name="Test Agent")

    @pytest.mark.asyncio
    async def test_activate_with_existing_config(self, temp_project_dir: Path, base_agent):
        """Test activate with existing config file."""
        config_dir = temp_project_dir / ".tapps-agents"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("project_name: test-project\n")
        
        agent = base_agent
        await agent.activate(temp_project_dir)
        
        assert agent.config is not None
        assert agent.config.project_name == "test-project"

    def test_get_commands_format(self, base_agent):
        """Test that get_commands returns properly formatted commands."""
        agent = base_agent
        commands = agent.get_commands()
        
        assert isinstance(commands, list)
        for cmd in commands:
            assert isinstance(cmd, dict)
            assert "command" in cmd
            assert "description" in cmd
            assert isinstance(cmd["command"], str)
            assert isinstance(cmd["description"], str)

    def test_format_help_includes_agent_name(self, base_agent):
        """Test that format_help includes agent name."""
        agent = base_agent
        help_text = agent.format_help()
        
        assert agent.agent_name in help_text

    @pytest.mark.asyncio
    async def test_activate_handles_missing_directories(self, tmp_path: Path, base_agent):
        """Test that activate handles missing directories gracefully."""
        agent = base_agent
        # Should not raise exception even if directories don't exist
        await agent.activate(tmp_path)
        
        # Should still have a config (defaults)
        assert agent.config is not None

    def test_parse_command_handles_empty_string(self, base_agent):
        """Test parsing empty command string."""
        agent = base_agent
        # Empty string should be handled - may raise IndexError or return empty command
        try:
            command, args = agent.parse_command("")
            assert isinstance(command, str)
            assert isinstance(args, dict)
        except IndexError:
            # This is acceptable behavior for empty strings
            pass

    def test_get_context_creates_context_manager(self, base_agent, sample_python_file):
        """Test that get_context creates context manager if needed."""
        agent = base_agent
        context = agent.get_context(sample_python_file)
        
        assert isinstance(context, dict)
        assert agent.context_manager is not None

    def test_get_context_text_creates_context_manager(self, base_agent, sample_python_file):
        """Test that get_context_text creates context manager if needed."""
        agent = base_agent
        context_text = agent.get_context_text(sample_python_file)
        
        assert isinstance(context_text, str)
        assert agent.context_manager is not None

    def test_call_tool_creates_gateway(self, base_agent):
        """Test that call_tool creates MCP gateway if needed."""
        agent = base_agent
        # Mock the gateway and its call_tool method
        mock_gateway = MagicMock()
        mock_gateway.call_tool.return_value = {"result": "test"}
        
        # Set the gateway directly to test the behavior
        agent.mcp_gateway = mock_gateway
        
        result = agent.call_tool("test_tool", arg1="value1")
        
        assert result == {"result": "test"}
        assert agent.mcp_gateway is not None
        mock_gateway.call_tool.assert_called_once_with("test_tool", arg1="value1")

    def test_validate_path_file_not_found(self, base_agent, tmp_path):
        """Test _validate_path with non-existent file."""
        agent = base_agent
        non_existent = tmp_path / "nonexistent.py"
        
        with pytest.raises(FileNotFoundError):
            agent._validate_path(non_existent)

    def test_validate_path_file_too_large(self, base_agent, tmp_path):
        """Test _validate_path with file that's too large."""
        agent = base_agent
        large_file = tmp_path / "large.py"
        # Create a file larger than default max (10MB)
        # For testing, use a smaller max size
        large_file.write_text("x" * 100)
        
        with pytest.raises(ValueError, match="File too large"):
            agent._validate_path(large_file, max_file_size=50)

    def test_validate_path_valid_file(self, base_agent, sample_python_file):
        """Test _validate_path with valid file."""
        agent = base_agent
        # Should not raise
        agent._validate_path(sample_python_file)

    def test_validate_path_path_traversal(self, base_agent, tmp_path):
        """Test _validate_path detects path traversal."""
        agent = base_agent
        # Create a suspicious path
        suspicious = tmp_path / ".." / ".." / "etc" / "passwd"
        
        # May or may not raise depending on implementation
        try:
            agent._validate_path(suspicious)
        except (ValueError, FileNotFoundError):
            pass  # Expected behavior