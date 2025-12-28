"""
Tests for output format validation.

Tests json, text, markdown, html outputs for commands that support them.
"""

import pytest

from tests.e2e.cli.test_base import CLICommandTestBase
from tests.e2e.cli.validation_helpers import assert_valid_json, assert_text_output


@pytest.mark.e2e_cli
class TestOutputFormats(CLICommandTestBase):
    """Tests for output formats."""

    def test_json_format(self):
        """Test JSON output format."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "json"]
        )
        assert_valid_json(result)

    def test_text_format(self):
        """Test text output format."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "text"]
        )
        assert_text_output(result)

    def test_markdown_format(self):
        """Test markdown output format."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "markdown"]
        )
        assert_text_output(result)
        # Check for markdown indicators
        assert "#" in result.stdout or "**" in result.stdout or "```" in result.stdout

    def test_html_format(self):
        """Test HTML output format (where supported)."""
        test_file = self.get_test_file()
        result = self.run_command(
            ["python", "-m", "tapps_agents.cli", "reviewer", "score", str(test_file), "--format", "html"]
        )
        assert_text_output(result)
        # Check for HTML indicators
        assert "<html" in result.stdout.lower() or "<!doctype" in result.stdout.lower()

