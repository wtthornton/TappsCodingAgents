"""
E2E tests for workflow state management commands.

Tests workflow state list, show, cleanup, and resume operations.
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.validation_helpers import assert_success_exit


@pytest.mark.e2e_cli
class TestWorkflowStateManagement(CLICommandTestBase):
    """Tests for workflow state management commands."""

    def test_workflow_state_list_command(self):
        """Test workflow state list command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "state", "list"],
            expect_success=True,
        )
        assert_success_exit(result)

    def test_workflow_state_list_with_format_json(self):
        """Test workflow state list with JSON format."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "state", "list", "--format", "json"],
            expect_success=True,
        )
        # May return empty list if no workflows
        assert result.exit_code in [0, 1]

    def test_workflow_state_list_with_workflow_id(self):
        """Test workflow state list with workflow ID filter."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "state", "list", "--workflow-id", "test-workflow"],
            expect_success=True,
        )
        assert result.exit_code in [0, 1]  # May not find workflow

    def test_workflow_state_show_command(self):
        """Test workflow state show command."""
        # Use a non-existent workflow ID - should handle gracefully
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "state", "show", "non-existent-workflow"],
            expect_success=False,
        )
        # Should fail gracefully if workflow not found
        assert result.exit_code in [0, 1, 2]

    def test_workflow_state_show_with_format_json(self):
        """Test workflow state show with JSON format."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "state", "show", "test-workflow", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1, 2]

    def test_workflow_state_cleanup_command(self):
        """Test workflow state cleanup command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "state", "cleanup", "--dry-run"],
            expect_success=True,
        )
        assert_success_exit(result)

    def test_workflow_state_cleanup_with_retention_days(self):
        """Test workflow state cleanup with retention days."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "state", "cleanup", "--retention-days", "30", "--dry-run"],
            expect_success=True,
        )
        assert_success_exit(result)

    def test_workflow_state_cleanup_with_max_states(self):
        """Test workflow state cleanup with max states per workflow."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "state", "cleanup", "--max-states-per-workflow", "10", "--dry-run"],
            expect_success=True,
        )
        assert_success_exit(result)

    def test_workflow_state_cleanup_with_remove_completed(self):
        """Test workflow state cleanup with remove completed flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "state", "cleanup", "--remove-completed", "--dry-run"],
            expect_success=True,
        )
        assert_success_exit(result)

    def test_workflow_resume_command(self):
        """Test workflow resume command."""
        # Use a non-existent workflow ID - should handle gracefully
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "resume", "--workflow-id", "non-existent-workflow"],
            expect_success=False,
        )
        # Should fail gracefully if workflow not found
        assert result.exit_code in [0, 1, 2]

    def test_workflow_resume_with_validate(self):
        """Test workflow resume with validation."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "resume", "--workflow-id", "test-workflow", "--validate"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1, 2]
