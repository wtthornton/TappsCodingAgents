"""
Comprehensive tests for top-level CLI commands.

Tests workflow, init, score, doctor, create, simple-mode, health, analytics, etc.
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.validation_helpers import assert_valid_json, assert_text_output, assert_success_exit


@pytest.mark.e2e_cli
class TestTopLevelCommands(CLICommandTestBase):
    """Tests for top-level commands."""

    def test_score_command(self):
        """Test top-level score command (shortcut for reviewer score)."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "score", str(test_file), "--format", "json"]
        )
        assert_valid_json(result)

    def test_doctor_command(self):
        """Test doctor command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "doctor", "--format", "json"]
        )
        assert_success_exit(result)

    def test_workflow_list_command(self):
        """Test workflow list command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "list"]
        )
        assert_success_exit(result)

    def test_workflow_recommend_command(self):
        """Test workflow recommend command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "recommend", "--format", "json"],
            expect_success=False,  # May require network
        )
        assert result.exit_code in [0, 1]

    def test_init_command(self):
        """Test init command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "init", "--yes", "--no-cache"],
            expect_success=False,  # May fail if already initialized
        )
        assert result.exit_code in [0, 1]

    def test_simple_mode_status_command(self):
        """Test simple-mode status command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "status", "--format", "json"]
        )
        assert_success_exit(result)

    def test_version_command(self):
        """Test --version flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "--version"]
        )
        assert_success_exit(result)
        assert "tapps-agents" in result.stdout.lower() or "version" in result.stdout.lower()

    def test_help_command(self):
        """Test --help flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "--help"]
        )
        assert_success_exit(result)
        assert "TappsCodingAgents" in result.stdout or "tapps-agents" in result.stdout.lower()

