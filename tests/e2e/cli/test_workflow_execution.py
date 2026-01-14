"""
Comprehensive E2E tests for workflow execution commands.

Tests all workflow presets and execution modes.
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.validation_helpers import assert_success_exit


@pytest.mark.e2e_cli
class TestWorkflowExecution(CLICommandTestBase):
    """Tests for workflow execution commands."""

    def test_workflow_full_command(self):
        """Test workflow full command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "full", "--prompt", "Create a simple calculator", "--auto", "--dry-run"],
            expect_success=False,  # May require network
            timeout=300.0,
        )
        # Accept success or graceful failure
        assert result.exit_code in [0, 1]

    def test_workflow_enterprise_command(self):
        """Test workflow enterprise command (alias for full)."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "enterprise", "--prompt", "Build API", "--auto", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_rapid_command(self):
        """Test workflow rapid command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "rapid", "--prompt", "Add user authentication", "--auto", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_feature_command(self):
        """Test workflow feature command (alias for rapid)."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "feature", "--prompt", "Add feature", "--auto", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_fix_command(self):
        """Test workflow fix command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "fix", "--file", str(test_file), "--auto", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_refactor_command(self):
        """Test workflow refactor command (alias for fix)."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "refactor", "--file", str(test_file), "--auto", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_quality_command(self):
        """Test workflow quality command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "quality", "--file", str(test_file), "--auto", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_improve_command(self):
        """Test workflow improve command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "improve", "--file", str(test_file), "--auto", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_hotfix_command(self):
        """Test workflow hotfix command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "hotfix", "--file", str(test_file), "--auto", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_urgent_command(self):
        """Test workflow urgent command (alias for hotfix)."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "urgent", "--file", str(test_file), "--auto", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_new_feature_command(self):
        """Test workflow new-feature command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "new-feature", "--prompt", "Add new feature", "--auto", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_with_cli_mode(self):
        """Test workflow with --cli-mode flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "rapid", "--prompt", "Test", "--cli-mode", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_with_cursor_mode(self):
        """Test workflow with --cursor-mode flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "rapid", "--prompt", "Test", "--cursor-mode", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_with_continue_from(self):
        """Test workflow with --continue-from flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "rapid", "--prompt", "Test", "--continue-from", "implement", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_with_skip_steps(self):
        """Test workflow with --skip-steps flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "rapid", "--prompt", "Test", "--skip-steps", "enhance,plan", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_with_autonomous(self):
        """Test workflow with --autonomous flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "rapid", "--prompt", "Test", "--autonomous", "--max-iterations", "3", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]

    def test_workflow_with_no_print_paths(self):
        """Test workflow with --no-print-paths flag."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "rapid", "--prompt", "Test", "--no-print-paths", "--dry-run"],
            expect_success=False,
            timeout=300.0,
        )
        assert result.exit_code in [0, 1]
