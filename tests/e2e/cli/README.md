# E2E CLI Tests

This directory contains end-to-end tests for the CLI interface (`tapps-agents` / `python -m tapps_agents.cli`).

## Overview

CLI E2E tests validate the user-facing CLI contract by:
- Running commands in isolated temp repositories (subprocess execution)
- Validating exit codes, stdout, stderr
- Validating JSON output shape and essential keys
- Testing error handling and user-actionable error messages
- Ensuring Windows path correctness

## Test Structure

### Test Files

- `test_cli_golden_paths.py` - Tests for successful command execution (golden paths)
- `test_cli_failure_paths.py` - Tests for error handling and failure scenarios

## Test Categories

### Golden Path Tests

Tests that validate successful command execution:

- `test_cli_reviewer_score_golden_path` - Reviewer score command with JSON output
- `test_cli_reviewer_review_golden_path` - Reviewer review command with JSON output
- `test_cli_orchestrator_workflow_list_golden_path` - Workflow list command
- `test_cli_workflow_list_golden_path` - Workflow preset list command
- `test_cli_workflow_preset_golden_path` - Workflow preset execution
- `test_cli_score_shortcut_golden_path` - Score shortcut command
- `test_cli_orchestrator_workflow_status_golden_path` - Workflow status command

**Validation:**
- Exit code is 0
- JSON output is valid (when applicable)
- JSON contains required keys
- Output is stable and testable

### Failure Path Tests

Tests that validate error handling:

- `test_cli_missing_file_error` - Missing file error handling
- `test_cli_missing_workflow_error` - Missing workflow error handling
- `test_cli_invalid_arguments_error` - Invalid arguments error handling
- `test_cli_invalid_format_error` - Invalid format option error handling
- `test_cli_missing_command_error` - Missing/invalid command error handling
- `test_cli_orchestrator_missing_workflow_id_error` - Missing workflow_id error
- `test_cli_invalid_file_path_error` - Invalid file path error handling
- `test_cli_timeout_handling` - Timeout handling
- `test_cli_error_message_stability` - Error message consistency

**Validation:**
- Exit code is non-zero
- Error messages are user-actionable
- Error messages are stable and testable (contract-based)
- Error messages contain expected keywords

## CLI Harness

The CLI harness (`tests/e2e/fixtures/cli_harness.py`) provides:

- **Isolated execution**: Each test runs in its own temp project directory
- **Environment injection**: Configurable environment variables
- **Timeout handling**: Configurable timeouts per command
- **Output capture**: stdout, stderr, exit code
- **Secret redaction**: Automatic redaction of API keys and tokens
- **Windows support**: Proper path handling and subprocess invocation

### Usage Example

```python
from tests.e2e.fixtures.cli_harness import CLIHarness, assert_success, assert_json_output

@pytest.fixture
def cli_harness(tmp_path):
    harness = CLIHarness(base_path=tmp_path / "cli_tests")
    yield harness
    harness.cleanup()

def test_my_command(cli_harness, tmp_path):
    project = cli_harness.create_isolated_project()
    result = cli_harness.run_command(
        ["python", "-m", "tapps_agents.cli", "reviewer", "score", "file.py"],
        cwd=project,
    )
    assert_success(result)
    json_data = assert_json_output(result, required_keys=["file"])
```

## Running CLI E2E Tests

### Run All CLI E2E Tests

```bash
# Run all CLI E2E tests
pytest tests/e2e/cli/ -m e2e_cli -v

# Run only golden path tests
pytest tests/e2e/cli/test_cli_golden_paths.py -m e2e_cli -v

# Run only failure path tests
pytest tests/e2e/cli/test_cli_failure_paths.py -m e2e_cli -v
```

### Run with LLM Requirements

Some tests require LLM services (marked with `@pytest.mark.requires_llm`):

```bash
# Run tests that require LLM
pytest tests/e2e/cli/ -m "e2e_cli and requires_llm" -v

# Skip LLM-required tests
pytest tests/e2e/cli/ -m "e2e_cli and not requires_llm" -v
```

### Run Specific Test

```bash
pytest tests/e2e/cli/test_cli_golden_paths.py::test_cli_reviewer_score_golden_path -v
```

## Test Markers

- `@pytest.mark.e2e_cli` - Marks test as CLI E2E test (opt-in for PRs)
- `@pytest.mark.requires_llm` - Test requires LLM service (skipped if unavailable)

## Best Practices

1. **Contract-First Assertions**: Prefer JSON output assertions (shape + required keys) over brittle string matching
2. **Exit Codes are API**: Validate exit codes explicitly (0 for success, non-zero for failures)
3. **Windows Correctness**: Tests should work on Windows (paths, quoting, subprocess)
4. **Isolation**: Each test uses its own temp project (never mutates developer's working copy)
5. **Secret Redaction**: All captured outputs are automatically redacted before publishing
6. **Stable Error Messages**: Test error message keywords, not exact text (allows for minor wording changes)

## Artifact Capture

On test failure, artifacts are automatically captured:

- Command executed
- Exit code
- stdout (redacted)
- stderr (redacted)
- Working directory
- Project artifacts (if applicable)

Artifacts are available in test output and can be used for debugging.

## Windows Support

All tests are designed to work on Windows:

- Path normalization (forward/backward slashes)
- Proper subprocess invocation
- Environment variable handling
- File path quoting

## Integration with CI

CLI E2E tests are:

- **Opt-in by default**: Use `-m e2e_cli` to run (not PR blockers)
- **Fast enough for PR smoke**: Most tests complete in < 30 seconds
- **Scheduled execution**: Can run in nightly/pre-release CI
- **Graceful skipping**: Tests requiring LLM/services skip cleanly when unavailable

