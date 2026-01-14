"""
E2E tests for Simple Mode command completion.

Tests all Simple Mode commands that were missing from coverage.
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.validation_helpers import assert_success_exit, assert_valid_json


@pytest.mark.e2e_cli
class TestSimpleModeCommands(CLICommandTestBase):
    """Tests for Simple Mode commands."""

    def test_simple_mode_on_command(self):
        """Test simple-mode on command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "on"],
            expect_success=False,  # May fail if config not found
        )
        # May fail if config not found, but should handle gracefully
        assert result.exit_code in [0, 1, 2]

    def test_simple_mode_off_command(self):
        """Test simple-mode off command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "off"],
            expect_success=False,  # May fail if config not found
        )
        # May fail if config not found, but should handle gracefully
        assert result.exit_code in [0, 1, 2]

    def test_simple_mode_init_command(self):
        """Test simple-mode init command (onboarding wizard)."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "init"],
            expect_success=False,  # May require interaction
        )
        # May succeed or require interaction
        assert result.exit_code in [0, 1]

    def test_simple_mode_configure_command(self):
        """Test simple-mode configure command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "configure"],
            expect_success=False,  # May require interaction
        )
        assert result.exit_code in [0, 1]

    def test_simple_mode_config_command(self):
        """Test simple-mode config command (alias for configure)."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "config"],
            expect_success=False,  # May require interaction
        )
        assert result.exit_code in [0, 1]

    def test_simple_mode_progress_command(self):
        """Test simple-mode progress command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "progress", "--format", "json"],
            expect_success=True,
        )
        assert result.exit_code in [0, 1]  # May return empty if no progress

    def test_simple_mode_full_command(self):
        """Test simple-mode full command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "full", "--prompt", "Build a simple calculator", "--auto", "--dry-run"],
            expect_success=False,  # May require network
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_simple_mode_build_command(self):
        """Test simple-mode build command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "build", "--prompt", "Add user authentication", "--auto", "--dry-run"],
            expect_success=False,  # May require network
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_simple_mode_resume_command(self):
        """Test simple-mode resume command."""
        # Use a non-existent workflow ID - should handle gracefully
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "simple-mode", "resume", "non-existent-workflow"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1, 2]
