"""
Unit tests for parser argument validation.

Tests to detect documented but missing arguments in parsers.
This helps catch issues where documentation shows arguments that don't exist in parsers.
"""

import argparse
import re
from pathlib import Path

import pytest

from tapps_agents.cli.parsers import (
    improver,
    tester,
)

pytestmark = pytest.mark.unit


class TestParserArgumentValidation:
    """Tests to validate parser arguments match documentation."""

    def test_improver_improve_quality_has_focus_argument(self):
        """Test that improve-quality command has --focus argument."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        improver.add_improver_parser(subparsers)

        # Parse with --focus argument
        args = parser.parse_args([
            "improver", "improve-quality", "test.py", "--focus", "security, maintainability"
        ])
        
        assert hasattr(args, "focus")
        assert args.focus == "security, maintainability"

    def test_tester_test_has_focus_argument(self):
        """Test that tester test command has --focus argument."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        tester.add_tester_parser(subparsers)

        # Parse with --focus argument
        args = parser.parse_args([
            "tester", "test", "test.py", "--focus", "edge cases, error handling"
        ])
        
        assert hasattr(args, "focus")
        assert args.focus == "edge cases, error handling"

    def test_improver_improve_quality_focus_help_text(self):
        """Test that --focus argument help text is present."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        improver.add_improver_parser(subparsers)

        # Get help text for the specific subcommand
        improver_parser = subparsers.choices["improver"]
        improver_subparsers = improver_parser._subparsers._group_actions[0]
        improve_quality_parser = improver_subparsers.choices["improve-quality"]
        help_output = improve_quality_parser.format_help()
        
        # Check that --focus is mentioned in help
        assert "--focus" in help_output or "focus" in help_output.lower()

    def test_tester_test_focus_help_text(self):
        """Test that --focus argument help text is present."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        tester.add_tester_parser(subparsers)

        # Get help text for the specific subcommand
        tester_parser = subparsers.choices["tester"]
        tester_subparsers = tester_parser._subparsers._group_actions[0]
        test_parser = tester_subparsers.choices["test"]
        help_output = test_parser.format_help()
        
        # Check that --focus is mentioned in help
        assert "--focus" in help_output or "focus" in help_output.lower()


class TestDocumentedArgumentsExist:
    """
    Tests to ensure documented arguments actually exist in parsers.
    
    This test class can be extended to check documentation files for
    argument usage and verify they exist in parsers.
    """

    def extract_arguments_from_docs(self, doc_path: Path) -> list[str]:
        """Extract argument names from documentation."""
        if not doc_path.exists():
            return []
        
        content = doc_path.read_text(encoding="utf-8")
        # Look for patterns like --focus, --format, etc.
        pattern = r"--(\w+(?:-\w+)*)"
        matches = re.findall(pattern, content)
        return list(set(matches))

    def test_improver_documented_focus_exists(self):
        """Test that --focus argument documented for improver exists in parser."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        improver.add_improver_parser(subparsers)

        # Try to parse with --focus (should not raise SystemExit)
        try:
            args = parser.parse_args([
                "improver", "improve-quality", "test.py", "--focus", "test"
            ])
            assert hasattr(args, "focus")
        except SystemExit:
            pytest.fail("--focus argument not recognized by parser")

    def test_tester_documented_focus_exists(self):
        """Test that --focus argument documented for tester exists in parser."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        tester.add_tester_parser(subparsers)

        # Try to parse with --focus (should not raise SystemExit)
        try:
            args = parser.parse_args([
                "tester", "test", "test.py", "--focus", "test"
            ])
            assert hasattr(args, "focus")
        except SystemExit:
            pytest.fail("--focus argument not recognized by parser")


class TestParserArgumentCompleteness:
    """Tests to ensure parsers have all expected arguments."""

    def test_improver_improve_quality_has_all_expected_args(self):
        """Test that improve-quality has all expected arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        improver.add_improver_parser(subparsers)

        # Parse with all arguments
        args = parser.parse_args([
            "improver", "improve-quality", "test.py",
            "--focus", "security",
            "--format", "json",
            "--output", "output.json"
        ])

        assert hasattr(args, "file_path")
        assert hasattr(args, "focus")
        assert hasattr(args, "format")
        assert hasattr(args, "output")

    def test_tester_test_has_all_expected_args(self):
        """Test that tester test has all expected arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="agent")
        tester.add_tester_parser(subparsers)

        # Parse with all arguments
        args = parser.parse_args([
            "tester", "test", "test.py",
            "--test-file", "test_test.py",
            "--integration",
            "--focus", "edge cases",
            "--format", "json",
            "--output", "output.json"
        ])

        assert hasattr(args, "file")
        assert hasattr(args, "test_file")
        assert hasattr(args, "integration")
        assert hasattr(args, "focus")
        assert hasattr(args, "format")
        assert hasattr(args, "output")

