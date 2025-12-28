"""
Tests for global flags with all commands.

Tests --quiet, --verbose, --progress flags with various commands.
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.validation_helpers import assert_success_exit


@pytest.mark.e2e_cli
class TestGlobalFlags(CLICommandTestBase):
    """Tests for global flags."""

    def test_quiet_flag_with_score(self):
        """Test --quiet flag with score command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "--quiet", "reviewer", "score", str(test_file), "--format", "json"]
        )
        assert_success_exit(result)

    def test_verbose_flag_with_score(self):
        """Test --verbose flag with score command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "--verbose", "reviewer", "score", str(test_file), "--format", "json"]
        )
        assert_success_exit(result)

    def test_no_progress_flag_with_score(self):
        """Test --no-progress flag with score command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "--no-progress", "reviewer", "score", str(test_file), "--format", "json"]
        )
        assert_success_exit(result)

    def test_progress_flag_with_score(self):
        """Test --progress flag with score command."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "--progress", "off", "reviewer", "score", str(test_file), "--format", "json"]
        )
        assert_success_exit(result)

    def test_quiet_flag_after_subcommand(self):
        """Test --quiet flag positioned after subcommand."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--quiet", "--format", "json"]
        )
        assert_success_exit(result)

    def test_verbose_flag_with_doctor(self):
        """Test --verbose flag with doctor command."""
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "--verbose", "doctor", "--format", "json"]
        )
        assert_success_exit(result)

