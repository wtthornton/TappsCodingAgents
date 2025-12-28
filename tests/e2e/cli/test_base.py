"""
Base classes for CLI command testing.

Provides common setup, teardown, and utilities for CLI tests.
"""

import pytest
from pathlib import Path
from typing import Any

from tests.e2e.fixtures.cli_harness import CLIHarness, CLIResult
from tests.e2e.cli.validation_helpers import (
    assert_success_exit,
    assert_valid_json,
    assert_text_output,
    assert_file_exists,
)


class CLICommandTestBase:
    """Base class for CLI command tests with common setup/teardown."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """Set up isolated test environment for each test."""
        self.cli_harness = CLIHarness(base_path=tmp_path / "cli_tests", default_timeout=180.0)
        self.test_project = self.cli_harness.create_isolated_project(template_type="minimal")
        
        # Create additional test files
        self._create_test_files()
        
        yield
        
        # Cleanup
        self.cli_harness.cleanup()
    
    def setup_method(self):
        """Optional setup method for subclasses."""
        pass

    def _create_test_files(self):
        """Create test files for testing."""
        # Create a simple Python file
        test_file = self.test_project / "test_file.py"
        test_file.write_text(
            '''"""Test file for CLI command tests."""
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
'''
        )
        
        # Create src directory with main.py
        src_dir = self.test_project / "src"
        src_dir.mkdir(exist_ok=True)
        main_file = src_dir / "main.py"
        main_file.write_text(
            '''"""Main module."""
def main():
    print("Hello, World!")
'''
        )

    def run_command(
        self,
        command: list[str],
        cwd: Path | None = None,
        expect_success: bool = True,
        timeout: float | None = None,
    ) -> CLIResult:
        """
        Run a CLI command and optionally assert success.
        
        Args:
            command: Command to run
            cwd: Working directory (defaults to test project)
            expect_success: Whether to assert success
            timeout: Command timeout
            
        Returns:
            CLI execution result
        """
        if cwd is None:
            cwd = self.test_project
        
        result = self.cli_harness.run_command(
            command,
            cwd=cwd,
            timeout=timeout,
        )
        
        if expect_success:
            assert_success_exit(result)
        
        return result

    def get_test_file(self, filename: str = "test_file.py") -> Path:
        """Get path to a test file."""
        return self.test_project / filename

    def create_test_file(self, filename: str, content: str) -> Path:
        """Create a test file with content."""
        file_path = self.test_project / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path


class ParameterizedCommandTest(CLICommandTestBase):
    """Base class for parameterized command tests."""

    def run_command_with_params(
        self,
        agent: str,
        command: str,
        params: dict[str, Any],
        expect_success: bool = True,
    ) -> CLIResult:
        """
        Run a command with parameters.
        
        Args:
            agent: Agent name (or "top-level")
            command: Command name
            params: Parameter dictionary
            expect_success: Whether to assert success
            
        Returns:
            CLI execution result
        """
        cmd = ["python", "-m", "tapps_agents.cli", agent, command]
        
        # Add parameters
        for key, value in params.items():
            if value is None:
                continue
            elif isinstance(value, bool) and value:
                # Boolean flag
                cmd.append(f"--{key}")
            elif isinstance(value, bool) and not value:
                # Skip False flags
                continue
            elif key.startswith("--"):
                # Already formatted
                cmd.append(key)
                if value is not True:
                    cmd.append(str(value))
            else:
                # Regular parameter
                if len(key) == 1:
                    cmd.append(f"-{key}")
                else:
                    cmd.append(f"--{key}")
                if value is not True:
                    cmd.append(str(value))
        
        return self.run_command(cmd, expect_success=expect_success)


class CommandValidationMixin:
    """Mixin providing validation helpers for commands."""

    def validate_json_output(self, result: CLIResult, required_keys: list[str] | None = None) -> dict[str, Any]:
        """Validate JSON output from command."""
        return assert_valid_json(result, required_keys)

    def validate_text_output(self, result: CLIResult, min_length: int = 1) -> str:
        """Validate text output from command."""
        return assert_text_output(result, min_length)

    def validate_file_created(self, result: CLIResult, file_path: Path) -> None:
        """Validate that a file was created."""
        assert_success_exit(result)
        assert_file_exists(file_path)

    def validate_command_success(self, result: CLIResult) -> None:
        """Validate that command succeeded."""
        assert_success_exit(result)

