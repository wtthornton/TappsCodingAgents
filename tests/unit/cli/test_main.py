"""
Tests for CLI main module - route_command and command routing.

Tests the refactored dictionary dispatch pattern and command routing logic.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.cli.main import (
    _get_agent_command_handlers,
    _get_top_level_command_handlers,
    _handle_cleanup_command,
    _handle_health_command,
    route_command,
)

pytestmark = pytest.mark.unit


class TestAgentCommandHandlers:
    """Tests for agent command handler dictionary."""

    def test_get_agent_command_handlers_returns_dict(self):
        """Test that handler dictionary is returned."""
        handlers = _get_agent_command_handlers()
        assert isinstance(handlers, dict)
        assert len(handlers) > 0

    def test_agent_handlers_include_reviewer(self):
        """Test that reviewer handler is included."""
        handlers = _get_agent_command_handlers()
        assert "reviewer" in handlers
        assert callable(handlers["reviewer"])

    def test_agent_handlers_include_all_agents(self):
        """Test that all expected agents are included."""
        handlers = _get_agent_command_handlers()
        expected_agents = [
            "reviewer",
            "planner",
            "implementer",
            "tester",
            "debugger",
            "documenter",
            "orchestrator",
            "analyst",
            "architect",
            "designer",
            "improver",
            "ops",
            "enhancer",
            "evaluator",
        ]
        for agent in expected_agents:
            assert agent in handlers, f"Agent {agent} not found in handlers"


class TestTopLevelCommandHandlers:
    """Tests for top-level command handler dictionary."""

    def test_get_top_level_command_handlers_returns_dict(self):
        """Test that handler dictionary is returned."""
        handlers = _get_top_level_command_handlers()
        assert isinstance(handlers, dict)
        assert len(handlers) > 0

    def test_top_level_handlers_include_create(self):
        """Test that create handler is included."""
        handlers = _get_top_level_command_handlers()
        assert "create" in handlers
        assert callable(handlers["create"])

    def test_top_level_handlers_include_common_commands(self):
        """Test that common commands are included."""
        handlers = _get_top_level_command_handlers()
        expected_commands = [
            "create",
            "init",
            "workflow",
            "score",
            "doctor",
        ]
        for cmd in expected_commands:
            assert cmd in handlers, f"Command {cmd} not found in handlers"


class TestRouteCommand:
    """Tests for route_command function."""

    def test_route_command_with_reviewer_agent(self):
        """Test routing to reviewer agent."""
        args = MagicMock()
        args.agent = "reviewer"

        with patch("tapps_agents.cli.main.reviewer.handle_reviewer_command") as mock_handler:
            with patch("tapps_agents.core.config.load_config") as mock_config:
                mock_config.return_value.auto_enhancement.enabled = False
                route_command(args)
                mock_handler.assert_called_once_with(args)

    def test_route_command_with_planner_agent(self):
        """Test routing to planner agent."""
        args = MagicMock()
        args.agent = "planner"

        with patch("tapps_agents.cli.main.planner.handle_planner_command") as mock_handler:
            with patch("tapps_agents.core.config.load_config") as mock_config:
                mock_config.return_value.auto_enhancement.enabled = False
                route_command(args)
                mock_handler.assert_called_once_with(args)

    def test_route_command_with_create_command(self):
        """Test routing to create command."""
        args = MagicMock()
        args.agent = "create"

        with patch("tapps_agents.cli.main.top_level.handle_create_command") as mock_handler:
            with patch("tapps_agents.core.config.load_config") as mock_config:
                mock_config.return_value.auto_enhancement.enabled = False
                route_command(args)
                mock_handler.assert_called_once_with(args)

    def test_route_command_with_init_command(self):
        """Test routing to init command."""
        args = MagicMock()
        args.agent = "init"

        with patch("tapps_agents.cli.main.top_level.handle_init_command") as mock_handler:
            with patch("tapps_agents.core.config.load_config") as mock_config:
                mock_config.return_value.auto_enhancement.enabled = False
                route_command(args)
                mock_handler.assert_called_once_with(args)

    def test_route_command_with_workflow_command(self):
        """Test routing to workflow command."""
        args = MagicMock()
        args.agent = "workflow"

        with patch("tapps_agents.cli.main.top_level.handle_workflow_command") as mock_handler:
            with patch("tapps_agents.core.config.load_config") as mock_config:
                mock_config.return_value.auto_enhancement.enabled = False
                route_command(args)
                mock_handler.assert_called_once_with(args)

    def test_route_command_with_cleanup_command(self):
        """Test routing to cleanup command."""
        args = MagicMock()
        args.agent = "cleanup"
        args.cleanup_type = "workflow-docs"

        with patch("tapps_agents.cli.main.top_level.handle_cleanup_workflow_docs_command") as mock_handler:
            with patch("tapps_agents.core.config.load_config") as mock_config:
                mock_config.return_value.auto_enhancement.enabled = False
                route_command(args)
                mock_handler.assert_called_once_with(args)

    def test_route_command_with_health_command(self):
        """Test routing to health command."""
        args = MagicMock()
        args.agent = "health"
        args.command = "check"

        with patch("tapps_agents.cli.commands.health.handle_health_check_command") as mock_handler:
            with patch("tapps_agents.core.config.load_config") as mock_config:
                mock_config.return_value.auto_enhancement.enabled = False
                route_command(args)
                mock_handler.assert_called_once()

    def test_route_command_with_simple_mode_command(self):
        """Test routing to simple-mode command."""
        args = MagicMock()
        args.agent = "simple-mode"

        with patch("tapps_agents.cli.main.simple_mode.handle_simple_mode_command") as mock_handler:
            with patch("tapps_agents.core.config.load_config") as mock_config:
                mock_config.return_value.auto_enhancement.enabled = False
                route_command(args)
                mock_handler.assert_called_once_with(args)

    def test_route_command_with_none_shows_help(self):
        """Test that None agent shows help."""
        args = MagicMock()
        args.agent = None

        with patch("tapps_agents.cli.main.create_root_parser") as mock_parser:
            with patch("tapps_agents.cli.main.register_all_parsers") as mock_register:
                with patch("tapps_agents.core.config.load_config") as mock_config:
                    mock_config.return_value.auto_enhancement.enabled = False
                    mock_parser_instance = MagicMock()
                    mock_parser.return_value = mock_parser_instance
                    route_command(args)
                    mock_parser_instance.print_help.assert_called_once()

    def test_route_command_with_prompt_enhancement_enabled(self):
        """Test that prompt enhancement middleware is applied when enabled."""
        args = MagicMock()
        args.agent = "reviewer"

        with patch("tapps_agents.cli.utils.prompt_enhancer.enhance_prompt_if_needed") as mock_enhance:
            with patch("tapps_agents.cli.main.reviewer.handle_reviewer_command") as mock_handler:
                with patch("tapps_agents.core.config.load_config") as mock_config:
                    mock_config.return_value.auto_enhancement.enabled = True
                    mock_enhance.return_value = args
                    route_command(args)
                    mock_enhance.assert_called_once()
                    mock_handler.assert_called_once_with(args)

    def test_route_command_with_unknown_agent_shows_help(self):
        """Test that unknown agent shows help."""
        args = MagicMock()
        args.agent = "unknown-agent"

        with patch("tapps_agents.cli.main.create_root_parser") as mock_parser:
            with patch("tapps_agents.cli.main.register_all_parsers") as mock_register:
                with patch("tapps_agents.core.config.load_config") as mock_config:
                    mock_config.return_value.auto_enhancement.enabled = False
                    mock_parser_instance = MagicMock()
                    mock_parser.return_value = mock_parser_instance
                    route_command(args)
                    mock_parser_instance.print_help.assert_called_once()


class TestSpecialCommandHandlers:
    """Tests for special command handlers."""

    def test_handle_cleanup_command_workflow_docs(self):
        """Test cleanup command with workflow-docs type."""
        args = MagicMock()
        args.cleanup_type = "workflow-docs"

        with patch("tapps_agents.cli.main.top_level.handle_cleanup_workflow_docs_command") as mock_handler:
            _handle_cleanup_command(args)
            mock_handler.assert_called_once_with(args)

    def test_handle_cleanup_command_unknown_type(self):
        """Test cleanup command with unknown type exits."""
        args = MagicMock()
        args.cleanup_type = "unknown"

        with patch("sys.exit") as mock_exit:
            with patch("sys.stderr"):
                _handle_cleanup_command(args)
                mock_exit.assert_called_once_with(1)

    def test_handle_health_command_check(self):
        """Test health command with check subcommand."""
        args = MagicMock()
        args.command = "check"
        args.check = None
        args.format = "text"
        args.save = True

        with patch("tapps_agents.cli.commands.health.handle_health_check_command") as mock_handler:
            _handle_health_command(args)
            mock_handler.assert_called_once()

    def test_handle_health_command_dashboard(self):
        """Test health command with dashboard subcommand."""
        args = MagicMock()
        args.command = "dashboard"
        args.format = "text"

        with patch("tapps_agents.cli.commands.health.handle_health_dashboard_command") as mock_handler:
            _handle_health_command(args)
            mock_handler.assert_called_once()

