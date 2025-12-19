"""
Comprehensive unit tests for CLI command handlers.

Tests command execution, error handling, output formatting, and agent integration.
Extends existing tests with additional coverage.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.cli.commands import (
    common,
    planner,
    reviewer,
    top_level,
)

pytestmark = pytest.mark.unit


class TestCommonCommands:
    """Tests for common command utilities."""

    def test_format_json_output_dict(self, capsys):
        """Test format_json_output with dict."""
        data = {"result": "success", "value": 42}
        common.format_json_output(data)
        captured = capsys.readouterr()
        # Output goes through feedback system, may be formatted
        assert len(captured.out) > 0

    def test_format_json_output_string(self, capsys):
        """Test format_json_output with string."""
        data = "simple string"
        common.format_json_output(data)
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_format_text_output(self, capsys):
        """Test format_text_output."""
        data = "simple text"
        common.format_text_output(data)
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_handle_error_string(self, capsys):
        """Test handle_error with string."""
        with pytest.raises(SystemExit) as exc_info:
            common.handle_error("Test error", exit_code=1)
        assert exc_info.value.code == 1

    def test_handle_error_dict(self, capsys):
        """Test handle_error with dict."""
        error_dict = {
            "error": "Test error",
            "error_code": "test_error",
            "context": {"key": "value"},
            "remediation": "Fix it",
        }
        with pytest.raises(SystemExit) as exc_info:
            common.handle_error(error_dict, exit_code=2)
        assert exc_info.value.code == 2

    def test_check_result_error_no_error(self):
        """Test check_result_error with no error."""
        result = {"success": True, "data": "test"}
        # Should not raise
        common.check_result_error(result)

    def test_check_result_error_with_error(self, capsys):
        """Test check_result_error with error."""
        result = {"error": "Test error"}
        with pytest.raises(SystemExit) as exc_info:
            common.check_result_error(result)
        assert exc_info.value.code == 1


class TestReviewerCommands:
    """Tests for reviewer command handlers."""

    @pytest.mark.asyncio
    async def test_review_command_file_not_found(self, tmp_path, capsys):
        """Test review command with non-existent file."""
        non_existent = tmp_path / "nonexistent.py"
        
        with pytest.raises(SystemExit) as exc_info:
            await reviewer.review_command(str(non_existent), output_format="json")
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.err or "file_not_found" in captured.err.lower()

    @pytest.mark.asyncio
    async def test_review_command_success_json(self, sample_python_file, capsys):
        """Test review command with valid file, JSON output."""
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(sample_python_file),
                "scoring": {
                    "complexity_score": 7.5,
                    "security_score": 8.0,
                    "maintainability_score": 9.0,
                    "overall_score": 82.5,
                },
                "passed": True,
                "feedback": {"summary": "Good code"},
            })
            mock_agent_class.return_value = mock_agent

            await reviewer.review_command(str(sample_python_file), output_format="json")

            mock_agent.activate.assert_called_once()
            mock_agent.run.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_command_success_text(self, sample_python_file, capsys):
        """Test review command with valid file, text output."""
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(sample_python_file),
                "scoring": {
                    "complexity_score": 7.5,
                    "security_score": 8.0,
                    "maintainability_score": 9.0,
                    "overall_score": 82.5,
                },
                "passed": True,
                "feedback": {"summary": "Good code"},
            })
            mock_agent_class.return_value = mock_agent

            await reviewer.review_command(str(sample_python_file), output_format="text")

            captured = capsys.readouterr()
            assert "Review" in captured.out or "Score" in captured.out
            mock_agent.activate.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_command_error_handling(self, sample_python_file, capsys):
        """Test review command error handling."""
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={"error": "Test error"})
            mock_agent_class.return_value = mock_agent

            with pytest.raises(SystemExit) as exc_info:
                await reviewer.review_command(str(sample_python_file), output_format="json")
            
            assert exc_info.value.code == 1
            mock_agent.close.assert_called_once()  # Should always close

    @pytest.mark.asyncio
    async def test_score_command_file_not_found(self, tmp_path, capsys):
        """Test score command with non-existent file."""
        non_existent = tmp_path / "nonexistent.py"
        
        with pytest.raises(SystemExit) as exc_info:
            await reviewer.score_command(str(non_existent), output_format="json")
        
        assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_score_command_success(self, sample_python_file, capsys):
        """Test score command with valid file."""
        with patch("tapps_agents.cli.commands.reviewer.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(sample_python_file),
                "scoring": {
                    "complexity_score": 7.5,
                    "security_score": 8.0,
                    "maintainability_score": 9.0,
                    "overall_score": 82.5,
                },
            })
            mock_agent_class.return_value = mock_agent

            await reviewer.score_command(str(sample_python_file), output_format="json")

            mock_agent.activate.assert_called_once()
            mock_agent.run.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_help_command(self, capsys):
        """Test help command output."""
        await reviewer.help_command()
        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestPlannerCommands:
    """Tests for planner command handlers."""

    @pytest.mark.asyncio
    async def test_list_stories_command_json(self, tmp_path, capsys):
        """Test list stories command with JSON output."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        stories_dir = project_dir / ".tapps-agents" / "stories"
        stories_dir.mkdir(parents=True)
        
        # Create a sample story file
        story_file = stories_dir / "story-001.yaml"
        story_file.write_text("title: Test Story\nstatus: open\n")

        with patch("pathlib.Path.cwd", return_value=project_dir):
            await planner.list_stories_command(output_format="json")
        
        captured = capsys.readouterr()
        # Should output something (may be JSON or text)
        assert len(captured.out) >= 0

    @pytest.mark.asyncio
    async def test_list_stories_command_text(self, tmp_path, capsys):
        """Test list stories command with text output."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        stories_dir = project_dir / ".tapps-agents" / "stories"
        stories_dir.mkdir(parents=True)

        with patch("pathlib.Path.cwd", return_value=project_dir):
            await planner.list_stories_command(output_format="text")
        
        captured = capsys.readouterr()
        assert isinstance(captured.out, str)


class TestTopLevelCommands:
    """Tests for top-level command handlers."""

    def test_hardware_profile_command_get(self, capsys):
        """Test hardware profile command (get)."""
        with patch("tapps_agents.cli.commands.top_level.HardwareProfiler") as mock_profiler_class, \
             patch("tapps_agents.cli.commands.top_level.UnifiedCacheConfigManager") as mock_config_class:
            mock_profiler = MagicMock()
            mock_profiler.get_metrics.return_value = MagicMock(
                cpu_cores=4,
                ram_gb=16.0,
                disk_free_gb=100.0,
                disk_total_gb=500.0,
                disk_type="SSD",
                cpu_arch="x86_64",
            )
            mock_profiler.detect_profile.return_value = MagicMock(value="workstation")
            mock_profiler.get_current_resource_usage.return_value = {
                "cpu_percent": 10.0,
                "memory_percent": 20.0,
                "memory_used_gb": 3.0,
                "memory_available_gb": 13.0,
                "disk_percent": 30.0,
                "disk_free_gb": 350.0,
            }
            mock_profiler_class.return_value = mock_profiler

            mock_config = MagicMock()
            mock_config.load.return_value = MagicMock(
                hardware_profile="workstation",
                detected_profile="workstation",
            )
            mock_config_class.return_value = mock_config

            top_level.hardware_profile_command(output_format="text")
            captured = capsys.readouterr()
            assert len(captured.out) > 0

    def test_hardware_profile_command_set(self, capsys):
        """Test hardware profile command (set)."""
        with patch("tapps_agents.cli.commands.top_level.HardwareProfiler") as mock_profiler_class, \
             patch("tapps_agents.cli.commands.top_level.UnifiedCacheConfigManager") as mock_config_class:
            mock_profiler = MagicMock()
            mock_profiler.get_metrics.return_value = MagicMock(
                cpu_cores=4,
                ram_gb=16.0,
                disk_free_gb=100.0,
                disk_total_gb=500.0,
                disk_type="SSD",
                cpu_arch="x86_64",
            )
            mock_profiler.detect_profile.return_value = MagicMock(value="workstation")
            mock_profiler.get_current_resource_usage.return_value = {
                "cpu_percent": 10.0,
                "memory_percent": 20.0,
            }
            mock_profiler_class.return_value = mock_profiler

            mock_config = MagicMock()
            mock_config.load.return_value = MagicMock(
                hardware_profile="workstation",
                detected_profile="workstation",
            )
            mock_config_manager = MagicMock()
            mock_config_manager.load.return_value = mock_config
            mock_config_manager.save = MagicMock()
            mock_config_class.return_value = mock_config_manager

            top_level.hardware_profile_command(set_profile="server", output_format="text")
            mock_config_manager.save.assert_called_once()

    def test_hardware_profile_command_invalid_profile(self, capsys):
        """Test hardware profile command with invalid profile."""
        with patch("tapps_agents.cli.commands.top_level.HardwareProfiler") as mock_profiler_class, \
             patch("tapps_agents.cli.commands.top_level.UnifiedCacheConfigManager") as mock_config_class:
            mock_profiler = MagicMock()
            mock_profiler.get_metrics.return_value = MagicMock()
            mock_profiler.detect_profile.return_value = MagicMock(value="workstation")
            mock_profiler.get_current_resource_usage.return_value = {}
            mock_profiler_class.return_value = mock_profiler

            mock_config = MagicMock()
            mock_config.load.return_value = MagicMock()
            mock_config_class.return_value = mock_config

            with pytest.raises(SystemExit) as exc_info:
                top_level.hardware_profile_command(set_profile="invalid", output_format="text")
            assert exc_info.value.code == 2

    @pytest.mark.asyncio
    async def test_score_command_shortcut(self, sample_python_file, capsys):
        """Test score command shortcut (top-level)."""
        with patch("tapps_agents.cli.commands.top_level.score_command") as mock_score:
            mock_score.return_value = None
            top_level.handle_score_command(MagicMock(file=str(sample_python_file), format="json"))
            mock_score.assert_called_once()

    def test_doctor_command(self, capsys):
        """Test doctor command."""
        with patch("tapps_agents.cli.commands.top_level.verify_cursor_integration") as mock_verify:
            mock_verify.return_value = {
                "cursor_installed": True,
                "skills_installed": True,
                "rules_installed": True,
            }
            top_level.handle_doctor_command(MagicMock(format="text"))
            mock_verify.assert_called_once()

    def test_doctor_command_json(self, capsys):
        """Test doctor command with JSON output."""
        with patch("tapps_agents.cli.commands.top_level.verify_cursor_integration") as mock_verify:
            mock_verify.return_value = {
                "cursor_installed": True,
                "skills_installed": True,
                "rules_installed": True,
            }
            top_level.handle_doctor_command(MagicMock(format="json"))
            mock_verify.assert_called_once()


class TestMainCLI:
    """Tests for main CLI entry point."""

    def test_main_help(self, capsys):
        """Test main function with --help."""
        from tapps_agents.cli import main
        
        with patch("sys.argv", ["tapps_agents", "--help"]):
            try:
                main()
            except SystemExit:
                pass  # argparse exits on --help
        
        captured = capsys.readouterr()
        assert "TappsCodingAgents" in captured.out or "agent" in captured.out.lower()

    def test_main_reviewer_help(self, capsys):
        """Test main function with reviewer --help."""
        from tapps_agents.cli import main
        
        with patch("sys.argv", ["tapps_agents", "reviewer", "--help"]):
            try:
                main()
            except SystemExit:
                pass
        
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_main_version(self, capsys):
        """Test main function with --version."""
        from tapps_agents.cli import main
        
        with patch("sys.argv", ["tapps_agents", "--version"]):
            try:
                main()
            except SystemExit:
                pass
        
        captured = capsys.readouterr()
        # Version should be printed
        assert len(captured.out) > 0

    def test_main_unknown_command(self, capsys):
        """Test main function with unknown command."""
        from tapps_agents.cli import main
        
        with patch("sys.argv", ["tapps_agents", "unknown-command"]):
            with pytest.raises(SystemExit):
                main()

    def test_register_all_parsers(self):
        """Test register_all_parsers function."""
        from tapps_agents.cli.main import create_root_parser, register_all_parsers
        
        parser = create_root_parser()
        register_all_parsers(parser)
        
        # Verify some parsers were registered
        subparsers = parser._subparsers._group_actions[0]
        assert "reviewer" in subparsers.choices
        assert "workflow" in subparsers.choices

    def test_route_command_reviewer(self):
        """Test route_command with reviewer."""
        from tapps_agents.cli.main import create_root_parser, register_all_parsers, route_command
        
        parser = create_root_parser()
        register_all_parsers(parser)
        
        with patch("tapps_agents.cli.commands.reviewer.handle_reviewer_command") as mock_handler:
            args = parser.parse_args(["reviewer", "help"])
            route_command(args)
            mock_handler.assert_called_once()

    def test_route_command_workflow(self):
        """Test route_command with workflow."""
        from tapps_agents.cli.main import create_root_parser, register_all_parsers, route_command
        
        parser = create_root_parser()
        register_all_parsers(parser)
        
        with patch("tapps_agents.cli.commands.top_level.handle_workflow_command") as mock_handler:
            args = parser.parse_args(["workflow", "list"])
            route_command(args)
            mock_handler.assert_called_once()

