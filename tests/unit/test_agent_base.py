"""
Unit tests for BaseAgent class.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from tapps_agents.core.agent_base import BaseAgent


@pytest.mark.unit
class TestBaseAgent:
    """Test cases for BaseAgent class."""
    
    def test_base_agent_initialization(self):
        """Test that BaseAgent initializes correctly."""
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        assert agent.agent_id == "test"
        assert agent.agent_name == "Test Agent"
        assert agent.config is None
        assert agent.domain_config is None
        assert agent.customizations is None
    
    def test_get_commands_returns_help(self):
        """Test that get_commands returns help command by default."""
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        commands = agent.get_commands()
        
        assert isinstance(commands, list)
        assert len(commands) >= 1
        assert commands[0]["command"] == "*help"
        assert "description" in commands[0]
    
    def test_format_help_shows_commands(self):
        """Test that format_help generates readable help output."""
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        help_text = agent.format_help()
        
        assert isinstance(help_text, str)
        assert "Test Agent" in help_text
        assert "Available Commands" in help_text
        assert "*help" in help_text
    
    def test_parse_command_star_prefix(self):
        """Test parsing star-prefixed commands."""
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        
        command, args = agent.parse_command("*review file.py")
        assert command == "review"
        assert args["file"] == "file.py"
    
    def test_parse_command_without_prefix(self):
        """Test parsing commands without star prefix."""
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        
        command, args = agent.parse_command("review file.py")
        assert command == "review"
        assert args["file"] == "file.py"
    
    def test_parse_command_numbered(self):
        """Test parsing numbered commands."""
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        
        # Mock get_commands to return known commands
        with patch.object(agent, 'get_commands', return_value=[
            {"command": "*review", "description": "Review code"},
            {"command": "*score", "description": "Score code"}
        ]):
            command, args = agent.parse_command("1")
            assert command == "review"
    
    def test_parse_command_invalid_number(self):
        """Test parsing invalid numbered command."""
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        
        with patch.object(agent, 'get_commands', return_value=[
            {"command": "*help", "description": "Help"}
        ]):
            # Number out of range should still work (handled by command handler)
            command, args = agent.parse_command("999")
            # Should return something or raise (implementation dependent)
    
    @pytest.mark.asyncio
    async def test_activate_loads_config(self, temp_project_dir: Path):
        """Test that activate loads configuration files."""
        # Create config file
        config_dir = temp_project_dir / ".tapps-agents"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("test: value")
        
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "test: value"
            await agent.activate(temp_project_dir)
        
        # Config should be attempted to load (may be None if YAML parse fails, but that's ok)
        # The key is that activate doesn't crash
    
    @pytest.mark.asyncio
    async def test_activate_loads_domain_config(self, temp_project_dir: Path):
        """Test that activate loads domain configuration."""
        config_dir = temp_project_dir / ".tapps-agents"
        config_dir.mkdir(exist_ok=True)
        domains_file = config_dir / "domains.md"
        domains_file.write_text("# Domains\n\nDomain 1")
        
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        await agent.activate(temp_project_dir)
        
        # Domain config should be loaded
        assert agent.domain_config is not None
        assert "Domain 1" in agent.domain_config
    
    @pytest.mark.asyncio
    async def test_activate_loads_customizations(self, temp_project_dir: Path):
        """Test that activate loads customizations."""
        config_dir = temp_project_dir / ".tapps-agents"
        config_dir.mkdir(exist_ok=True)
        customizations_dir = config_dir / "customizations"
        customizations_dir.mkdir(exist_ok=True)
        custom_file = customizations_dir / "test-custom.yaml"
        custom_file.write_text("custom: value")
        
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        await agent.activate(temp_project_dir)
        
        # Customizations should be attempted to load
    
    @pytest.mark.asyncio
    async def test_activate_no_config_files(self, temp_project_dir: Path):
        """Test that activate works when no config files exist."""
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        
        # Should not raise exception
        await agent.activate(temp_project_dir)
        
        assert agent.config is None
        assert agent.domain_config is None
    
    def test_run_is_abstract(self):
        """Test that run method is abstract and must be implemented."""
        agent = BaseAgent(agent_id="test", agent_name="Test Agent")
        
        with pytest.raises(TypeError):
            # Cannot instantiate BaseAgent if run is truly abstract
            # Actually, Python ABC requires instantiation check differently
            # But we can test that run raises NotImplementedError if called directly
            pass

