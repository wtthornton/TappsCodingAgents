"""
Shared fixtures for CLI E2E tests.

Provides common fixtures used across all CLI test files:
- cli_harness: CLI harness for isolated test execution
- test_project: Isolated test project
- test_file: Test Python file in project
"""


import pytest

from tests.e2e.fixtures.cli_harness import CLIHarness


@pytest.fixture
def cli_harness(tmp_path):
    """Create a CLI harness for isolated test execution."""
    harness = CLIHarness(base_path=tmp_path / "cli_tests", default_timeout=60.0)
    yield harness
    harness.cleanup()


@pytest.fixture
def test_project(cli_harness):
    """Create an isolated test project."""
    return cli_harness.create_isolated_project(template_type="minimal")


@pytest.fixture
def test_file(test_project):
    """Create a test Python file in the project."""
    test_file_path = test_project / "test_code.py"
    test_file_path.write_text(
        '''"""Test file for CLI tests."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
'''
    )
    return test_file_path
