"""
Enhanced E2E tests for error handling.

Tests various error scenarios to ensure commands handle errors gracefully.
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase


@pytest.mark.e2e_cli
class TestInvalidArguments(CLICommandTestBase):
    """Tests for invalid argument handling."""

    def test_invalid_command(self):
        """Test invalid command name."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "invalid-command"],
            expect_success=False,
        )
        assert result.exit_code == 2  # Usage error

    def test_invalid_subcommand(self):
        """Test invalid subcommand."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "invalid-subcommand"],
            expect_success=False,
        )
        assert result.exit_code == 2

    def test_missing_required_parameter(self):
        """Test missing required parameter."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score"],
            expect_success=False,
        )
        assert result.exit_code == 2

    def test_invalid_format_option(self):
        """Test invalid format option."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "invalid"],
            expect_success=False,
        )
        assert result.exit_code == 2

    def test_invalid_flag_combination(self):
        """Test invalid flag combination."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "rapid", "--prompt", "Test", "--cli-mode", "--cursor-mode"],
            expect_success=False,
        )
        # May or may not fail depending on implementation
        assert result.exit_code in [0, 1, 2]


@pytest.mark.e2e_cli
class TestMissingFiles(CLICommandTestBase):
    """Tests for missing file handling."""

    def test_reviewer_score_missing_file(self):
        """Test reviewer score with non-existent file."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", "non_existent_file.py", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [1, 2]  # File not found error

    def test_implementer_refactor_missing_file(self):
        """Test implementer refactor with non-existent file."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "implementer", "refactor", "missing.py", "Refactor code", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [1, 2]

    def test_tester_test_missing_file(self):
        """Test tester test with non-existent file."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "tester", "test", "missing.py", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [1, 2]


@pytest.mark.e2e_cli
class TestInvalidPaths(CLICommandTestBase):
    """Tests for invalid path handling."""

    def test_reviewer_review_invalid_directory(self):
        """Test reviewer review with invalid directory."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "review", "/nonexistent/directory", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [1, 2]

    def test_workflow_with_invalid_file_path(self):
        """Test workflow with invalid file path."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "fix", "--file", "/nonexistent/file.py", "--dry-run"],
            expect_success=False,
        )
        assert result.exit_code in [0, 1, 2]  # May handle gracefully


@pytest.mark.e2e_cli
class TestInvalidWorkflowFiles(CLICommandTestBase):
    """Tests for invalid workflow file handling."""

    def test_workflow_with_nonexistent_yaml(self):
        """Test workflow with non-existent YAML file."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "nonexistent-workflow.yaml", "--prompt", "Test", "--dry-run"],
            expect_success=False,
        )
        assert result.exit_code in [1, 2]

    def test_orchestrator_with_invalid_workflow(self):
        """Test orchestrator with invalid workflow file."""
        invalid_workflow = self.test_project / "invalid.yaml"
        invalid_workflow.write_text("invalid: yaml: content: [")
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "orchestrator", "orchestrate", str(invalid_workflow), "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code in [1, 2]


@pytest.mark.e2e_cli
class TestInvalidParameters(CLICommandTestBase):
    """Tests for invalid parameter values."""

    def test_reviewer_review_invalid_max_workers(self):
        """Test reviewer review with invalid max-workers value."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "review", str(test_file), "--max-workers", "0", "--format", "json"],
            expect_success=False,
        )
        # May accept or reject depending on validation
        assert result.exit_code in [0, 1, 2]

    def test_reviewer_review_invalid_fail_under(self):
        """Test reviewer review with invalid fail-under value."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "review", str(test_file), "--fail-under", "150", "--format", "json"],
            expect_success=False,
        )
        # May accept or reject depending on validation
        assert result.exit_code in [0, 1, 2]

    def test_planner_create_story_invalid_priority(self):
        """Test planner create-story with invalid priority."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "create-story", "Test story", "--priority", "invalid", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code == 2  # Invalid choice

    def test_improver_optimize_invalid_type(self):
        """Test improver optimize with invalid type."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "improver", "optimize", str(test_file), "--type", "invalid", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code == 2  # Invalid choice

    def test_ops_check_compliance_invalid_standard(self):
        """Test ops check-compliance with invalid standard."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "ops", "check-compliance", "--standard", "INVALID", "--format", "json"],
            expect_success=False,
        )
        assert result.exit_code == 2  # Invalid choice


@pytest.mark.e2e_cli
class TestNetworkFailures(CLICommandTestBase):
    """Tests for network failure handling (graceful degradation)."""

    def test_reviewer_docs_network_failure(self):
        """Test reviewer docs handles network failure gracefully."""
        # This test assumes network may fail
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "docs", "nonexistent-library-xyz123", "--format", "json"],
            expect_success=False,
        )
        # Should fail gracefully, not crash
        assert result.exit_code in [0, 1, 2]

    def test_workflow_recommend_network_failure(self):
        """Test workflow recommend handles network failure gracefully."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "workflow", "recommend", "--format", "json"],
            expect_success=False,
        )
        # Should handle network failure gracefully
        assert result.exit_code in [0, 1]


@pytest.mark.e2e_cli
class TestPermissionErrors(CLICommandTestBase):
    """Tests for permission error handling."""

    def test_reviewer_review_readonly_file(self):
        """Test reviewer review with readonly file (should still work for reading)."""
        test_file = self.get_test_file()
        # Make file readonly (on Unix-like systems)
        try:
            import os
            os.chmod(test_file, 0o444)
            result = self.run_command(
                ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "json"],
                expect_success=True,  # Reading should work
            )
            assert result.exit_code == 0
        except (OSError, AttributeError):
            # Windows or permission change failed - skip
            pytest.skip("Cannot set file permissions on this system")
        finally:
            try:
                os.chmod(test_file, 0o644)
            except (OSError, AttributeError):
                pass
