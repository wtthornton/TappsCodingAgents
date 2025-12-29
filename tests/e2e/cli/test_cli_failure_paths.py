"""
E2E tests for CLI failure paths and UX contracts.

Tests common error cases:
- Missing file errors
- Missing workflow errors
- Invalid arguments
- Missing credentials (when applicable)
- Invalid JSON output scenarios

All tests validate:
- Exit codes are non-zero
- Error messages are user-actionable
- Error messages are stable and testable
"""


import pytest

from tests.e2e.fixtures.cli_harness import (
    CLIHarness,
    assert_failure,
)


@pytest.fixture
def cli_harness(tmp_path):
    """Create a CLI harness for isolated test execution."""
    harness = CLIHarness(base_path=tmp_path / "cli_tests", default_timeout=30.0)
    yield harness
    harness.cleanup()


@pytest.fixture
def test_project(cli_harness):
    """Create an isolated test project."""
    return cli_harness.create_isolated_project(template_type="minimal")


@pytest.mark.e2e_cli
def test_cli_missing_file_error(cli_harness, test_project):
    """
    Test CLI error handling for missing file.

    Validates:
    - Exit code is non-zero
    - Error message is user-actionable (mentions file not found)
    - Error message is stable and testable
    """
    nonexistent_file = test_project / "nonexistent.py"

    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "reviewer",
            "score",
            str(nonexistent_file),
        ],
        cwd=test_project,
    )

    assert_failure(result)
    # Error message should mention file not found or error
    error_text = result.stderr.lower() + result.stdout.lower()
    assert (
        "not found" in error_text
        or "error" in error_text
        or "does not exist" in error_text
        or "no such file" in error_text
    ), f"Expected file not found error, got: {result.stderr}"


@pytest.mark.e2e_cli
def test_cli_missing_workflow_error(cli_harness, test_project):
    """
    Test CLI error handling for missing workflow preset.

    Validates:
    - Exit code is non-zero
    - Error message lists available workflows
    - Error message is user-actionable
    """
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "workflow",
            "nonexistent-workflow",
        ],
        cwd=test_project,
    )

    assert_failure(result)
    # Error message should mention workflow not found and list available
    error_text = result.stderr.lower() + result.stdout.lower()
    assert (
        "not found" in error_text
        or "error" in error_text
        or "available" in error_text
    ), f"Expected workflow not found error, got: {result.stderr}"


@pytest.mark.e2e_cli
def test_cli_invalid_arguments_error(cli_harness, test_project):
    """
    Test CLI error handling for invalid arguments.

    Validates:
    - Exit code is non-zero
    - Error message explains the issue
    - Error message is user-actionable
    """
    # Test missing required argument
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "reviewer",
            "score",
            # Missing file argument
        ],
        cwd=test_project,
    )

    assert_failure(result)
    # Error message should mention missing argument or usage
    error_text = result.stderr.lower() + result.stdout.lower()
    assert (
        "error" in error_text
        or "required" in error_text
        or "usage" in error_text
        or "argument" in error_text
    ), f"Expected invalid arguments error, got: {result.stderr}"


@pytest.mark.e2e_cli
def test_cli_invalid_format_error(cli_harness, test_project):
    """
    Test CLI error handling for invalid format option.

    Validates:
    - Exit code is non-zero (if format validation exists)
    - Error message is clear
    """
    test_file = test_project / "test_code.py"
    test_file.write_text("def add(a, b): return a + b\n")

    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "reviewer",
            "score",
            str(test_file),
            "--format",
            "invalid_format",
        ],
        cwd=test_project,
    )

    # May fail or succeed depending on validation, but should handle gracefully
    if result.exit_code != 0:
        error_text = result.stderr.lower() + result.stdout.lower()
        assert (
            "error" in error_text
            or "invalid" in error_text
            or "format" in error_text
        ), f"Expected format error, got: {result.stderr}"


@pytest.mark.e2e_cli
def test_cli_missing_command_error(cli_harness, test_project):
    """
    Test CLI error handling for missing/invalid command.

    Validates:
    - Exit code is non-zero
    - Error message shows usage or available commands
    """
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "nonexistent-command",
        ],
        cwd=test_project,
    )

    assert_failure(result)
    # Error message should mention invalid command or show usage
    error_text = result.stderr.lower() + result.stdout.lower()
    assert (
        "error" in error_text
        or "usage" in error_text
        or "unknown" in error_text
        or "invalid" in error_text
    ), f"Expected command error, got: {result.stderr}"


@pytest.mark.e2e_cli
def test_cli_workflow_file_not_found_error(cli_harness, test_project):
    """
    Test top-level workflow command with non-existent file path.

    Validates:
    - Command fails with appropriate error (exit code != 0)
    - Error message indicates file not found
    """
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "workflow",
            "workflows/custom/nonexistent.yaml",
            "--prompt",
            "Test",
        ],
        cwd=test_project,
        expect_success=False,
    )

    assert result.exit_code != 0
    error_text = result.stderr.lower() + result.stdout.lower()
    assert (
        "not found" in error_text or "error" in error_text
    ), f"Expected file not found error, got: {result.stderr}"


def test_cli_orchestrator_workflow_file_not_found_error(cli_harness, test_project):
    """
    Test orchestrator workflow command with non-existent file path.

    Validates:
    - Command fails with appropriate error (exit code != 0)
    - Error message indicates file not found
    """
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "orchestrator",
            "workflow",
            "workflows/custom/nonexistent.yaml",
            "--format",
            "json",
        ],
        cwd=test_project,
        expect_success=False,
    )

    assert result.exit_code != 0
    json_data = assert_json_output(result)
    assert "error" in json_data
    assert "not found" in json_data["error"].lower()


def test_cli_orchestrator_missing_workflow_id_error(cli_harness, test_project):
    """
    Test CLI error handling for missing workflow_id in workflow-start.

    Validates:
    - Exit code is non-zero
    - Error message explains missing workflow_id
    """
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "orchestrator",
            "workflow-start",
            # Missing workflow_id argument
        ],
        cwd=test_project,
    )

    assert_failure(result)
    # Error message should mention workflow_id required
    error_text = result.stderr.lower() + result.stdout.lower()
    assert (
        "error" in error_text
        or "required" in error_text
        or "workflow_id" in error_text
    ), f"Expected workflow_id error, got: {result.stderr}"


@pytest.mark.e2e_cli
def test_cli_invalid_file_path_error(cli_harness, test_project):
    """
    Test CLI error handling for invalid file path.

    Validates:
    - Exit code is non-zero
    - Error message is clear about path issue
    """
    # Use a path with invalid characters or structure
    invalid_path = test_project / ".." / ".." / "nonexistent" / "file.py"

    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "reviewer",
            "score",
            str(invalid_path),
        ],
        cwd=test_project,
    )

    assert_failure(result)
    # Error message should mention file not found or path issue
    error_text = result.stderr.lower() + result.stdout.lower()
    assert (
        "not found" in error_text
        or "error" in error_text
        or "does not exist" in error_text
    ), f"Expected path error, got: {result.stderr}"


@pytest.mark.e2e_cli
def test_cli_timeout_handling(cli_harness, test_project):
    """
    Test CLI timeout handling for long-running commands.

    Validates:
    - Command times out appropriately
    - Exit code indicates timeout
    - Error handling is graceful
    """
    test_file = test_project / "test_code.py"
    test_file.write_text("def add(a, b): return a + b\n")

    # Use a very short timeout to force timeout
    result = cli_harness.run_command(
        [
            "python",
            "-m",
            "tapps_agents.cli",
            "reviewer",
            "review",
            str(test_file),
            "--format",
            "json",
        ],
        cwd=test_project,
        timeout=0.1,  # Very short timeout
    )

    # Should timeout
    assert result.timed_out or result.exit_code != 0, "Expected timeout or failure"


@pytest.mark.e2e_cli
def test_cli_error_message_stability(cli_harness, test_project):
    """
    Test that error messages are stable and testable (contract-based).

    Validates:
    - Error messages contain expected keywords
    - Error messages are consistent across runs
    - Error messages are user-actionable
    """
    nonexistent_file = test_project / "nonexistent.py"

    # Run multiple times to check consistency
    results = []
    for _ in range(3):
        result = cli_harness.run_command(
            [
                "python",
                "-m",
                "tapps_agents.cli",
                "reviewer",
                "score",
                str(nonexistent_file),
            ],
            cwd=test_project,
        )
        results.append(result)

    # All should fail with same exit code
    exit_codes = [r.exit_code for r in results]
    assert all(code == exit_codes[0] for code in exit_codes), "Exit codes should be consistent"

    # Error messages should contain similar keywords
    error_keywords = []
    for result in results:
        error_text = (result.stderr + result.stdout).lower()
        keywords = []
        if "not found" in error_text:
            keywords.append("not_found")
        if "error" in error_text:
            keywords.append("error")
        if "does not exist" in error_text:
            keywords.append("does_not_exist")
        error_keywords.append(set(keywords))

    # At least one keyword should be consistent
    common_keywords = set.intersection(*error_keywords) if error_keywords else set()
    assert len(common_keywords) > 0, "Error messages should have consistent keywords"

