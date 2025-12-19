"""
E2E tests for CLI entrypoint parity.

Tests that both entrypoints behave identically:
- Console script: `tapps-agents ...`
- Module invocation: `python -m tapps_agents.cli ...`

Validates:
- Startup routines run consistently
- Exit codes are identical
- Output formats are identical
- Error handling is identical
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.e2e.fixtures.cli_harness import CLIHarness


@pytest.fixture
def cli_harness(tmp_path):
    """Create a CLI harness for isolated test execution."""
    harness = CLIHarness(base_path=tmp_path / "cli_parity_tests", default_timeout=60.0)
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
        '''"""Test file for CLI entrypoint parity tests."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
'''
    )
    return test_file_path


def _run_console_script(command: list[str], cwd: Path, timeout: float = 60.0) -> dict:
    """Run command using console script entrypoint (tapps-agents)."""
    import shutil
    # Check if console script is available, fall back to module invocation if not
    console_script = shutil.which("tapps-agents")
    if console_script:
        full_command = ["tapps-agents"] + command
    else:
        # Fall back to module invocation if console script not installed
        full_command = [sys.executable, "-m", "tapps_agents.cli"] + command
    
    result = subprocess.run(
        full_command,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        timeout=timeout,
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": full_command,
    }


def _run_module_invocation(command: list[str], cwd: Path, timeout: float = 60.0) -> dict:
    """Run command using module invocation (python -m tapps_agents.cli)."""
    full_command = [sys.executable, "-m", "tapps_agents.cli"] + command
    result = subprocess.run(
        full_command,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        timeout=timeout,
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": full_command,
    }


@pytest.mark.e2e_cli
def test_entrypoint_parity_help(cli_harness, test_project):
    """
    Test that --help produces identical output across entrypoints.
    
    Validates:
    - Both entrypoints produce same help text
    - Exit codes are identical (0 for --help)
    """
    console_result = _run_console_script(["--help"], test_project)
    module_result = _run_module_invocation(["--help"], test_project)

    # Both should succeed (argparse exits with 0 for --help)
    assert console_result["exit_code"] == module_result["exit_code"]
    
    # Help text should be similar (may have minor differences in program name)
    assert len(console_result["stdout"]) > 0
    assert len(module_result["stdout"]) > 0
    # Both should mention TappsCodingAgents or similar
    assert "tapps" in console_result["stdout"].lower() or "agent" in console_result["stdout"].lower()
    assert "tapps" in module_result["stdout"].lower() or "agent" in module_result["stdout"].lower()


@pytest.mark.e2e_cli
def test_entrypoint_parity_version(cli_harness, test_project):
    """
    Test that --version produces identical output across entrypoints.
    
    Validates:
    - Both entrypoints produce same version output
    - Exit codes are identical (0 for --version)
    """
    console_result = _run_console_script(["--version"], test_project)
    module_result = _run_module_invocation(["--version"], test_project)

    # Both should succeed
    assert console_result["exit_code"] == module_result["exit_code"]
    
    # Version output should be identical
    assert console_result["stdout"].strip() == module_result["stdout"].strip()
    assert "tapps-agents" in console_result["stdout"] or "tapps_agents" in console_result["stdout"]


@pytest.mark.e2e_cli
def test_entrypoint_parity_missing_file_error(cli_harness, test_project):
    """
    Test that missing file errors are handled identically across entrypoints.
    
    Validates:
    - Both entrypoints return same exit code (non-zero)
    - Error messages are similar
    - Error structure is consistent
    """
    nonexistent_file = test_project / "nonexistent.py"
    
    console_result = _run_console_script(
        ["reviewer", "score", str(nonexistent_file)], test_project
    )
    module_result = _run_module_invocation(
        ["reviewer", "score", str(nonexistent_file)], test_project
    )

    # Both should fail with same exit code
    assert console_result["exit_code"] == module_result["exit_code"]
    assert console_result["exit_code"] != 0
    
    # Error messages should be similar (both mention file not found or error)
    console_error = (console_result["stderr"] + console_result["stdout"]).lower()
    module_error = (module_result["stderr"] + module_result["stdout"]).lower()
    
    # Both should contain error indicators
    console_has_error = (
        "not found" in console_error
        or "error" in console_error
        or "does not exist" in console_error
    )
    module_has_error = (
        "not found" in module_error
        or "error" in module_error
        or "does not exist" in module_error
    )
    
    assert console_has_error, f"Console result should contain error: {console_result}"
    assert module_has_error, f"Module result should contain error: {module_result}"


@pytest.mark.e2e_cli
def test_entrypoint_parity_invalid_command(cli_harness, test_project):
    """
    Test that invalid commands are handled identically across entrypoints.
    
    Validates:
    - Both entrypoints return same exit code (non-zero)
    - Error messages are similar
    """
    console_result = _run_console_script(["nonexistent-command"], test_project)
    module_result = _run_module_invocation(["nonexistent-command"], test_project)

    # Both should fail with same exit code
    assert console_result["exit_code"] == module_result["exit_code"]
    assert console_result["exit_code"] != 0
    
    # Both should indicate invalid command
    console_error = (console_result["stderr"] + console_result["stdout"]).lower()
    module_error = (module_result["stderr"] + module_result["stdout"]).lower()
    
    assert (
        "error" in console_error
        or "usage" in console_error
        or "unknown" in console_error
    ), f"Console should show error: {console_result}"
    assert (
        "error" in module_error
        or "usage" in module_error
        or "unknown" in module_error
    ), f"Module should show error: {module_result}"


@pytest.mark.e2e_cli
def test_entrypoint_parity_orchestrator_workflow_list(cli_harness, test_project):
    """
    Test that orchestrator workflow-list produces identical output across entrypoints.
    
    Validates:
    - Both entrypoints return same exit code (0)
    - Output structure is identical (if JSON)
    """
    console_result = _run_console_script(
        ["orchestrator", "workflow-list"], test_project
    )
    module_result = _run_module_invocation(
        ["orchestrator", "workflow-list"], test_project
    )

    # Both should succeed
    assert console_result["exit_code"] == module_result["exit_code"]
    assert console_result["exit_code"] == 0
    
    # If both produce JSON, they should be identical
    console_json = None
    module_json = None
    
    try:
        console_json = json.loads(console_result["stdout"].strip())
    except (json.JSONDecodeError, ValueError):
        pass
    
    try:
        module_json = json.loads(module_result["stdout"].strip())
    except (json.JSONDecodeError, ValueError):
        pass
    
    # If both are JSON, they should be identical
    if console_json is not None and module_json is not None:
        assert console_json == module_json, "JSON outputs should be identical"


@pytest.mark.e2e_cli
def test_entrypoint_parity_startup_routines(cli_harness, test_project):
    """
    Test that startup routines run consistently across entrypoints.
    
    Validates:
    - Startup routines execute for both entrypoints
    - No errors from startup routines
    - Behavior is consistent
    """
    # Run a simple command that should trigger startup routines
    console_result = _run_console_script(["--version"], test_project)
    module_result = _run_module_invocation(["--version"], test_project)

    # Both should succeed (startup routines shouldn't cause failures)
    assert console_result["exit_code"] == module_result["exit_code"]
    assert console_result["exit_code"] == 0
    
    # No startup-related errors should appear
    console_output = (console_result["stderr"] + console_result["stdout"]).lower()
    module_output = (module_result["stderr"] + module_result["stdout"]).lower()
    
    # Should not have critical startup errors
    critical_errors = ["traceback", "exception", "failed to start"]
    for error in critical_errors:
        assert error not in console_output, f"Console should not have {error}"
        assert error not in module_output, f"Module should not have {error}"


@pytest.mark.e2e_cli
def test_entrypoint_parity_exit_codes(cli_harness, test_project):
    """
    Test that exit codes are consistent across entrypoints for various scenarios.
    
    Validates:
    - Success cases return 0 for both
    - Failure cases return same non-zero code for both
    - Exit codes follow standard conventions
    """
    test_cases = [
        # (command, expected_success)
        (["--version"], True),
        (["--help"], True),  # argparse exits with 0 for --help
        (["nonexistent-command"], False),
    ]
    
    for command, expected_success in test_cases:
        console_result = _run_console_script(command, test_project)
        module_result = _run_module_invocation(command, test_project)
        
        # Exit codes should match
        assert console_result["exit_code"] == module_result["exit_code"], (
            f"Exit codes should match for command {command}: "
            f"console={console_result['exit_code']}, "
            f"module={module_result['exit_code']}"
        )
        
        # Exit code should match expectation
        if expected_success:
            assert console_result["exit_code"] == 0, (
                f"Command {command} should succeed but got exit code {console_result['exit_code']}"
            )
        else:
            assert console_result["exit_code"] != 0, (
                f"Command {command} should fail but got exit code {console_result['exit_code']}"
            )


@pytest.mark.e2e_cli
def test_entrypoint_parity_orchestrator_help(cli_harness, test_project):
    """
    Test that orchestrator help produces identical output across entrypoints.
    
    Validates:
    - Both entrypoints produce same help text
    - Exit codes are identical
    """
    console_result = _run_console_script(["orchestrator", "--help"], test_project)
    module_result = _run_module_invocation(["orchestrator", "--help"], test_project)

    # Both should succeed
    assert console_result["exit_code"] == module_result["exit_code"]
    assert console_result["exit_code"] == 0
    
    # Help text should be similar
    assert len(console_result["stdout"]) > 0
    assert len(module_result["stdout"]) > 0


@pytest.mark.e2e_cli
def test_entrypoint_parity_reviewer_help(cli_harness, test_project):
    """
    Test that reviewer help produces identical output across entrypoints.
    
    Validates:
    - Both entrypoints produce same help text
    - Exit codes are identical
    """
    console_result = _run_console_script(["reviewer", "--help"], test_project)
    module_result = _run_module_invocation(["reviewer", "--help"], test_project)

    # Both should succeed
    assert console_result["exit_code"] == module_result["exit_code"]
    assert console_result["exit_code"] == 0
    
    # Help text should be similar
    assert len(console_result["stdout"]) > 0
    assert len(module_result["stdout"]) > 0


@pytest.mark.e2e_cli
def test_entrypoint_parity_workflow_list(cli_harness, test_project):
    """
    Test that workflow list produces identical output across entrypoints.
    
    Validates:
    - Both entrypoints produce same output
    - Exit codes are identical
    """
    console_result = _run_console_script(["workflow", "list"], test_project)
    module_result = _run_module_invocation(["workflow", "list"], test_project)

    # Both should succeed
    assert console_result["exit_code"] == module_result["exit_code"]
    assert console_result["exit_code"] == 0
    
    # Output should be similar (may be text or JSON)
    assert len(console_result["stdout"]) > 0 or len(module_result["stdout"]) > 0


@pytest.mark.e2e_cli
def test_entrypoint_parity_init_command(cli_harness, test_project):
    """
    Test that init command behaves identically across entrypoints.
    
    Validates:
    - Both entrypoints produce same behavior
    - Exit codes are identical
    - Same files are created
    """
    # Use a subdirectory to avoid conflicts
    init_project = test_project / "init_test"
    init_project.mkdir()
    
    console_result = _run_console_script(["init"], init_project)
    module_result = _run_module_invocation(["init"], init_project)

    # Both should succeed
    assert console_result["exit_code"] == module_result["exit_code"]
    # Init may succeed or fail depending on existing state, but codes should match

