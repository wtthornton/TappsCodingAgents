"""
Simple validation helpers for CLI test assertions.

These helpers provide simple, non-mocked validation functions
for testing CLI command outputs and behavior.
"""

from pathlib import Path
from typing import Any

from tests.e2e.fixtures.cli_harness import CLIResult


def assert_exit_code(result: CLIResult, expected: int) -> None:
    """
    Assert that CLI result has expected exit code.
    
    Args:
        result: CLI execution result
        expected: Expected exit code
        
    Raises:
        AssertionError: If exit code doesn't match
    """
    assert (
        result.exit_code == expected
    ), f"Expected exit code {expected}, got {result.exit_code}. stderr: {result.stderr[:500]}"


def assert_success_exit(result: CLIResult) -> None:
    """
    Assert that CLI command succeeded (exit code 0).
    
    Args:
        result: CLI execution result
        
    Raises:
        AssertionError: If command failed or timed out
    """
    assert not result.timed_out, f"Command timed out after {result.duration_seconds}s"
    assert_exit_code(result, 0)


def assert_failure_exit(result: CLIResult, min_exit_code: int = 1) -> None:
    """
    Assert that CLI command failed with non-zero exit code.
    
    Args:
        result: CLI execution result
        min_exit_code: Minimum expected exit code (default: 1)
        
    Raises:
        AssertionError: If command succeeded
    """
    assert (
        result.exit_code >= min_exit_code
    ), f"Expected failure (exit code >= {min_exit_code}), got {result.exit_code}"


def assert_valid_json(result: CLIResult, required_keys: list[str] | None = None) -> dict[str, Any]:
    """
    Assert that CLI result has valid JSON output.
    
    Args:
        result: CLI execution result
        required_keys: Optional list of required keys in JSON
        
    Returns:
        Parsed JSON dict
        
    Raises:
        AssertionError: If output is not valid JSON or missing required keys
    """
    json_data = result.json_output()
    assert json_data is not None, f"Expected JSON output, got: {result.stdout[:200]}"
    
    if required_keys:
        missing_keys = [key for key in required_keys if key not in json_data]
        assert (
            not missing_keys
        ), f"JSON output missing required keys: {missing_keys}. Got keys: {list(json_data.keys())}"
    
    return json_data


def assert_text_output(result: CLIResult, min_length: int = 1) -> str:
    """
    Assert that CLI result has non-empty text output.
    
    Args:
        result: CLI execution result
        min_length: Minimum expected output length
        
    Returns:
        Output text
        
    Raises:
        AssertionError: If output is too short
    """
    assert len(result.stdout) >= min_length, f"Expected output length >= {min_length}, got {len(result.stdout)}"
    return result.stdout


def assert_file_exists(file_path: Path, description: str = "file") -> None:
    """
    Assert that a file exists.
    
    Args:
        file_path: Path to file
        description: Description of file for error message
        
    Raises:
        AssertionError: If file doesn't exist
    """
    assert file_path.exists(), f"Expected {description} to exist at {file_path}"


def assert_file_created(result: CLIResult, file_path: Path, description: str = "output file") -> None:
    """
    Assert that a file was created by the command.
    
    Args:
        result: CLI execution result
        file_path: Path to expected file
        description: Description of file for error message
        
    Raises:
        AssertionError: If file doesn't exist or command failed
    """
    assert_success_exit(result)
    assert_file_exists(file_path, description)


def assert_command_parsed(result: CLIResult) -> None:
    """
    Assert that command was parsed successfully (no parse errors).
    
    Args:
        result: CLI execution result
        
    Raises:
        AssertionError: If command parsing failed
    """
    # Parse errors typically result in exit code 2 and error message in stderr
    assert (
        result.exit_code != 2
    ), f"Command parsing failed. stderr: {result.stderr[:500]}"


def assert_output_contains(result: CLIResult, text: str, case_sensitive: bool = False) -> None:
    """
    Assert that output contains specified text.
    
    Args:
        result: CLI execution result
        text: Text to search for
        case_sensitive: Whether search should be case-sensitive
        
    Raises:
        AssertionError: If text not found
    """
    output = result.stdout if case_sensitive else result.stdout.lower()
    search_text = text if case_sensitive else text.lower()
    assert search_text in output, f"Expected output to contain '{text}', got: {result.stdout[:500]}"


def assert_output_not_contains(result: CLIResult, text: str, case_sensitive: bool = False) -> None:
    """
    Assert that output does not contain specified text.
    
    Args:
        result: CLI execution result
        text: Text that should not be present
        case_sensitive: Whether search should be case-sensitive
        
    Raises:
        AssertionError: If text is found
    """
    output = result.stdout if case_sensitive else result.stdout.lower()
    search_text = text if case_sensitive else text.lower()
    assert search_text not in output, f"Expected output to not contain '{text}'"


def assert_no_errors(result: CLIResult) -> None:
    """
    Assert that command produced no errors (exit code 0, no error output).
    
    Args:
        result: CLI execution result
        
    Raises:
        AssertionError: If errors found
    """
    assert_success_exit(result)
    # Check for common error indicators in stderr
    error_indicators = ["error", "exception", "traceback", "failed"]
    stderr_lower = result.stderr.lower()
    found_errors = [indicator for indicator in error_indicators if indicator in stderr_lower]
    assert (
        not found_errors
    ), f"Found error indicators in stderr: {found_errors}. stderr: {result.stderr[:500]}"


def assert_json_structure(result: CLIResult, expected_structure: dict[str, Any]) -> dict[str, Any]:
    """
    Assert that JSON output matches expected structure.
    
    Args:
        result: CLI execution result
        expected_structure: Dictionary with expected keys and types
        
    Returns:
        Parsed JSON dict
        
    Raises:
        AssertionError: If structure doesn't match
    """
    json_data = assert_valid_json(result)
    
    for key, expected_type in expected_structure.items():
        assert key in json_data, f"Missing key '{key}' in JSON output"
        assert isinstance(
            json_data[key], expected_type
        ), f"Key '{key}' has wrong type. Expected {expected_type.__name__}, got {type(json_data[key]).__name__}"
    
    return json_data


def assert_file_content(file_path: Path, expected_content: str | None = None, min_length: int | None = None) -> str:
    """
    Assert that file exists and optionally check content.
    
    Args:
        file_path: Path to file
        expected_content: Optional expected content (substring match)
        min_length: Optional minimum file length
        
    Returns:
        File content
        
    Raises:
        AssertionError: If file doesn't exist or content doesn't match
    """
    assert_file_exists(file_path)
    content = file_path.read_text()
    
    if min_length is not None:
        assert len(content) >= min_length, f"File content too short. Expected >= {min_length}, got {len(content)}"
    
    if expected_content is not None:
        assert expected_content in content, f"Expected content not found in file. Content: {content[:500]}"
    
    return content

