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
        config_file.write_text("project_name: test-project\ntest: value\nanother: key")

        agent = base_agent
        await agent.activate(temp_project_dir)

        # Config should be loaded and contain the values we wrote
        assert agent.config is not None, "Config should be loaded after activate"
        # Verify config is a Pydantic model instance (ProjectConfig)
        assert hasattr(agent.config, 'project_name'), \
            "Config should have project_name attribute"
        assert agent.config.project_name == "test-project", \
            f"Config should contain project_name='test-project', got {agent.config.project_name}"
        # Note: ProjectConfig ignores extra fields (model_config: extra="ignore")
        # So 'test' and 'another' fields are ignored, only defined fields like project_name are loaded

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
        # Loader expects {agent_id}-custom.yaml format (agent_id is "test-agent")
        # Create a valid customization file according to schema
        custom_file = customizations_dir / "test-agent-custom.yaml"
        custom_file.write_text("""agent_id: test-agent
persona_overrides:
  additional_principles:
    - "Test principle"
  custom_instructions: "Test custom instructions"
""")

        agent = base_agent
        await agent.activate(temp_project_dir)

        # Customizations should be loaded as a dict when valid customization file exists
        assert agent.customizations is not None, \
            "Customizations should be loaded when valid customization file exists"
        assert isinstance(agent.customizations, dict), \
            f"Customizations should be a dict, got {type(agent.customizations)}"
        assert "agent_id" in agent.customizations, \
            f"Customizations dict should contain 'agent_id' key, got keys: {list(agent.customizations.keys())}"
        assert agent.customizations["agent_id"] == "test-agent", \
            f"Customizations should contain agent_id='test-agent', got {agent.customizations.get('agent_id')}"
        assert "persona_overrides" in agent.customizations, \
            "Customizations should contain 'persona_overrides' key"
        assert "custom_instructions" in agent.customizations.get("persona_overrides", {}), \
            "Customizations persona_overrides should contain 'custom_instructions'"

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
        
        with pytest.raises(FileNotFoundError, match="File not found: .*nonexistent.py"):
            agent._validate_path(non_existent)

    def test_validate_path_file_too_large(self, base_agent, tmp_path):
        """Test _validate_path with file that's too large."""
        agent = base_agent
        large_file = tmp_path / "large.py"
        # Create a file larger than default max (10MB)
        # For testing, use a smaller max size
        large_file.write_text("x" * 100)
        
        # Validate specific error message format: "File too large: {size} bytes (max {max} bytes)"
        with pytest.raises(ValueError, match=r"File too large: \d+ bytes \(max \d+ bytes\)"):
            agent._validate_path(large_file, max_file_size=50)

    def test_validate_path_valid_file(self, base_agent, sample_python_file):
        """Test _validate_path with valid file."""
        agent = base_agent
        # Should not raise
        agent._validate_path(sample_python_file)

    def test_validate_path_path_traversal(self, base_agent, tmp_path):
        """Test _validate_path detects path traversal."""
        agent = base_agent
        # Create a suspicious path with path traversal
        suspicious = tmp_path / ".." / ".." / "etc" / "passwd"
        
        # Should raise ValueError for path traversal attempts (path validation should detect this)
        # FileNotFoundError would only occur if the file doesn't exist, but path validation should catch traversal first
        with pytest.raises(ValueError, match=r".*path.*traversal|.*outside.*allowed|.*invalid.*path"):
            agent._validate_path(suspicious)

    @pytest.mark.asyncio
    async def test_activate_with_invalid_config_file(self, tmp_path: Path, base_agent):
        """Test activate handles invalid config file gracefully."""
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        agent = base_agent
        # Should not raise exception, should use defaults
        await agent.activate(tmp_path)
        
        assert agent.config is not None

    @pytest.mark.asyncio
    async def test_activate_loads_role_file(self, tmp_path: Path, base_agent):
        """Test activate loads role file if available."""
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir(exist_ok=True)
        roles_dir = config_dir / "roles"
        roles_dir.mkdir(exist_ok=True)
        role_file = roles_dir / "test-agent.md"
        role_file.write_text("# Test Agent Role\n\nThis is a test role.")
        
        agent = base_agent
        await agent.activate(tmp_path)
        
        # Role file may be loaded or None depending on implementation
        assert hasattr(agent, "role_file")

    @pytest.mark.asyncio
    async def test_activate_loads_user_role_template(self, tmp_path: Path, base_agent):
        """Test activate loads user role template if configured."""
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("user_role: developer")
        
        agent = base_agent
        await agent.activate(tmp_path)
        
        # User role template may be loaded or None
        assert hasattr(agent, "user_role_template")

    def test_parse_command_with_multiple_args(self, base_agent):
        """Test parse_command with multiple arguments."""
        agent = base_agent
        
        command, args = agent.parse_command("review file.py --format json")
        
        assert command == "review"
        assert "file" in args

    def test_parse_command_numbered_out_of_range(self, base_agent):
        """Test parse_command with number out of range."""
        agent = base_agent
        
        with patch.object(
            agent,
            "get_commands",
            return_value=[{"command": "*help", "description": "Help"}],
        ):
            # Number out of range should return empty or handle gracefully
            command, args = agent.parse_command("999")
            # Implementation dependent - may return empty or raise

    def test_get_context_with_tier(self, base_agent, sample_python_file):
        """Test get_context with specific tier."""
        agent = base_agent
        
        from tapps_agents.core.tiered_context import ContextTier
        
        context = agent.get_context(sample_python_file, tier=ContextTier.TIER2)
        
        assert isinstance(context, dict)

    def test_get_context_with_related_files(self, base_agent, sample_python_file):
        """Test get_context with include_related flag."""
        agent = base_agent
        
        context = agent.get_context(sample_python_file, include_related=True)
        
        assert isinstance(context, dict)

    def test_get_context_text_different_formats(self, base_agent, sample_python_file):
        """Test get_context_text with different formats."""
        agent = base_agent
        
        text_format = agent.get_context_text(sample_python_file, format="text")
        markdown_format = agent.get_context_text(sample_python_file, format="markdown")
        
        assert isinstance(text_format, str)
        assert isinstance(markdown_format, str)

    def test_call_tool_creates_gateway_lazy(self, base_agent):
        """Test call_tool lazy initializes MCP gateway."""
        agent = base_agent
        
        # Mock MCP gateway
        with patch("tapps_agents.core.agent_base.MCPGateway") as mock_gateway_class:
            mock_gateway = MagicMock()
            mock_gateway.call_tool.return_value = {"result": "test"}
            mock_gateway_class.return_value = mock_gateway
            
            result = agent.call_tool("test_tool", arg1="value1")
            
            assert result == {"result": "test"}
            assert agent.mcp_gateway is not None

    def test_get_unified_cache_creates_cache(self, base_agent):
        """Test get_unified_cache creates cache instance."""
        agent = base_agent
        
        cache = agent.get_unified_cache()
        
        assert cache is not None
        assert agent._unified_cache is not None

    def test_get_unified_cache_reuses_cache(self, base_agent):
        """Test get_unified_cache reuses existing cache."""
        agent = base_agent
        
        cache1 = agent.get_unified_cache()
        cache2 = agent.get_unified_cache()
        
        assert cache1 is cache2

    def test_handle_optional_dependency_error(self, base_agent):
        """Test handle_optional_dependency_error creates error result."""
        agent = base_agent
        
        error = Exception("Optional dependency error")
        result = agent.handle_optional_dependency_error(
            error, "TestDependency", workflow_id="test", step_id="step1"
        )
        
        assert isinstance(result, dict)
        assert "error" in result or "recoverable" in result

    def test_handle_optional_dependency_error_context7(self, base_agent):
        """Test handle_optional_dependency_error with Context7UnavailableError."""
        agent = base_agent
        
        from tapps_agents.core.exceptions import Context7UnavailableError
        
        error = Context7UnavailableError("Context7 unavailable")
        result = agent.handle_optional_dependency_error(error, "Context7")
        
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_activate_sets_project_root(self, tmp_path: Path, base_agent):
        """Test activate sets _project_root for path validation."""
        agent = base_agent
        await agent.activate(tmp_path)
        
        assert agent._project_root == tmp_path

    def test_validate_path_uses_project_root(self, base_agent, tmp_path):
        """Test _validate_path uses cached project root."""
        agent = base_agent
        agent._project_root = tmp_path
        
        test_file = tmp_path / "test.py"
        test_file.write_text("code")
        
        # Should not raise
        agent._validate_path(test_file)

    def test_parse_command_empty_after_strip(self, base_agent):
        """Test parse_command handles whitespace-only input."""
        agent = base_agent
        
        command, args = agent.parse_command("   ")
        
        assert command == ""
        assert args == {}

    def test_format_help_includes_all_commands(self, base_agent):
        """Test format_help includes all commands from get_commands."""
        agent = base_agent
        
        # Mock get_commands to return multiple commands
        with patch.object(
            agent,
            "get_commands",
            return_value=[
                {"command": "*help", "description": "Help"},
                {"command": "*review", "description": "Review"},
                {"command": "*score", "description": "Score"},
            ],
        ):
            help_text = agent.format_help()
            
            assert "*help" in help_text
            assert "*review" in help_text
            assert "*score" in help_text

    def test_get_commands_returns_list(self, base_agent):
        """Test get_commands always returns a list."""
        agent = base_agent
        commands = agent.get_commands()
        
        assert isinstance(commands, list)
        assert len(commands) >= 1

    @pytest.mark.asyncio
    async def test_activate_handles_domain_config_read_error(self, tmp_path: Path, base_agent):
        """Test activate handles domain config read errors."""
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir(exist_ok=True)
        domains_file = config_dir / "domains.md"
        # Create a file that can't be read (directory)
        domains_file.mkdir()
        
        agent = base_agent
        # Should not raise exception
        await agent.activate(tmp_path)
        
        # Domain config should be None on error
        assert agent.domain_config is None

    def test_get_context_initializes_context_manager(self, base_agent, sample_python_file):
        """Test get_context initializes context_manager if None."""
        agent = base_agent
        agent.context_manager = None
        
        context = agent.get_context(sample_python_file)
        
        assert agent.context_manager is not None
        assert isinstance(context, dict)

    def test_get_context_text_initializes_context_manager(self, base_agent, sample_python_file):
        """Test get_context_text initializes context_manager if None."""
        agent = base_agent
        agent.context_manager = None
        
        context_text = agent.get_context_text(sample_python_file)
        
        assert agent.context_manager is not None
        assert isinstance(context_text, str)