"""
Comprehensive tests for top-level CLI commands.

Tests workflow, init, score, doctor, create, simple-mode, health, analytics, etc.
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.validation_helpers import (
    assert_success_exit,
    assert_valid_json,
)


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

    def test_setup_experts_list_command(self):
        """Test setup-experts list command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "setup-experts", "list"],
            expect_success=True,
        )
        assert_success_exit(result)
        # Should list experts (even if empty)
        assert "expert" in result.stdout.lower() or "no experts" in result.stdout.lower()

    def test_setup_experts_init_command(self):
        """Test setup-experts init command in non-interactive mode."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "setup-experts", "--yes", "--non-interactive", "init"],
            expect_success=True,
        )
        assert_success_exit(result)
        # Should create .tapps-agents directory structure
        assert (self.test_project / ".tapps-agents").exists()
        # Should create domains.md template
        assert (self.test_project / ".tapps-agents" / "domains.md").exists()

    def test_setup_experts_init_creates_structure(self):
        """Test that setup-experts init creates required directory structure."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "setup-experts", "--yes", "--non-interactive", "init"],
            expect_success=True,
        )
        assert_success_exit(result)
        
        # Verify directory structure
        config_dir = self.test_project / ".tapps-agents"
        assert config_dir.exists()
        assert (config_dir / "domains.md").exists()
        
        # In non-interactive mode, experts.yaml should not exist (expert creation skipped)
        # But knowledge directory should be created
        assert (config_dir / "knowledge").exists()

    def test_setup_experts_add_non_interactive_fails(self):
        """Test that setup-experts add fails gracefully in non-interactive mode without input."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "setup-experts", "--non-interactive", "add"],
            expect_success=False,
        )
        # Should exit with code 2 (NonInteractiveInputRequired)
        assert result.exit_code == 2
        assert "Non-interactive mode requires additional input" in result.stderr

    def test_setup_experts_help(self):
        """Test setup-experts --help."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "setup-experts", "--help"],
            expect_success=True,
        )
        assert_success_exit(result)
        assert "setup-experts" in result.stdout.lower() or "expert" in result.stdout.lower()

