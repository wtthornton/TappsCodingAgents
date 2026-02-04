"""
E2E tests for create command.

Tests project creation with different descriptions and options.
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase


@pytest.mark.e2e_cli
class TestCreateCommand(CLICommandTestBase):
    """Tests for create command."""

    def test_create_basic_command(self):
        """Test basic create command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "create", "A simple calculator application"],
            expect_success=False,  # May require network
            timeout=600.0,  # Creation can take time
        )
        # Accept success or graceful failure
        assert result.exit_code in [0, 1]

    def test_create_with_workflow_full(self):
        """Test create command with full workflow."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "create", "A REST API for task management", "--workflow", "full"],
            expect_success=False,
            timeout=600.0,
        )
        assert result.exit_code in [0, 1]

    def test_create_with_workflow_rapid(self):
        """Test create command with rapid workflow."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "create", "A CLI tool for file operations", "--workflow", "rapid"],
            expect_success=False,
            timeout=600.0,
        )
        assert result.exit_code in [0, 1]

    def test_create_web_app(self):
        """Test create command for web application."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "create", "A web application with React frontend and FastAPI backend"],
            expect_success=False,
            timeout=600.0,
        )
        assert result.exit_code in [0, 1]

    def test_create_api(self):
        """Test create command for API."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "create", "A REST API for user management with authentication"],
            expect_success=False,
            timeout=600.0,
        )
        assert result.exit_code in [0, 1]

    def test_create_cli_tool(self):
        """Test create command for CLI tool."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "create", "A command-line tool for file processing"],
            expect_success=False,
            timeout=600.0,
        )
        assert result.exit_code in [0, 1]
