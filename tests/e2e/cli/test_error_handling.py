"""
Tests for error handling scenarios.

Tests invalid commands, missing arguments, invalid values, etc.
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.validation_helpers import assert_failure_exit


@pytest.mark.e2e_cli
class TestErrorHandling(CLICommandTestBase):
    """Tests for error handling."""

    def test_invalid_command(self):
        """Test invalid command handling."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "invalid-command"],
            expect_success=False,
        )
        assert_failure_exit(result)

    def test_missing_file_argument(self):
        """Test missing file argument."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score"],
            expect_success=False,
        )
        assert_failure_exit(result)

    def test_nonexistent_file(self):
        """Test nonexistent file handling."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", "nonexistent_file.py", "--format", "json"],
            expect_success=False,
        )
        assert_failure_exit(result)

    def test_invalid_format_value(self):
        """Test invalid format value."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "invalid_format"],
            expect_success=False,
        )
        assert_failure_exit(result)

    def test_missing_required_positional(self):
        """Test missing required positional argument."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "planner", "plan"],
            expect_success=False,
        )
        assert_failure_exit(result)

