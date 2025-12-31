# Issue 10: Simple Mode Full Workflow Infinite Loop - Test Suite

## Overview

This test suite validates all fixes implemented for Issue 10, which addressed the infinite loop/hang problem in Simple Mode full workflow execution.

## Test Files

### Unit Tests

1. **`test_cursor_executor_issue10_timeout.py`**
   - Tests timeout mechanism
   - Verifies workflow times out after configured timeout
   - Tests timeout error messages and logging
   - Tests workflow completion before timeout

2. **`test_cursor_executor_issue10_initialization.py`**
   - Tests workflow initialization validation
   - Verifies workflow has steps before execution
   - Tests first step readiness validation
   - Tests state creation if missing

3. **`test_cursor_executor_issue10_no_ready_steps.py`**
   - Tests improved no ready steps handling
   - Verifies blocking step detection
   - Tests missing artifact identification
   - Tests multiple blocking steps handling

4. **`test_cursor_executor_issue10_health_check.py`**
   - Tests `get_workflow_health()` method
   - Verifies health information accuracy
   - Tests stuck workflow detection
   - Tests progress percentage calculation

### Integration Tests

5. **`test_simple_mode_full_workflow_issue10.py`**
   - End-to-end Simple Mode full workflow tests
   - Tests with `--auto` flag
   - Tests timeout handling
   - Tests auto-execution warnings
   - Tests progress reporting
   - Tests error handling

## Running the Tests

### Run All Issue 10 Tests

```bash
# Unit tests
pytest tests/unit/workflow/test_cursor_executor_issue10_*.py -v

# Integration tests
pytest tests/integration/test_simple_mode_full_workflow_issue10.py -v -m integration

# All Issue 10 tests
pytest tests/unit/workflow/test_cursor_executor_issue10_*.py tests/integration/test_simple_mode_full_workflow_issue10.py -v
```

### Run Specific Test Categories

```bash
# Timeout tests only
pytest tests/unit/workflow/test_cursor_executor_issue10_timeout.py -v

# Initialization tests only
pytest tests/unit/workflow/test_cursor_executor_issue10_initialization.py -v

# No ready steps tests only
pytest tests/unit/workflow/test_cursor_executor_issue10_no_ready_steps.py -v

# Health check tests only
pytest tests/unit/workflow/test_cursor_executor_issue10_health_check.py -v
```

### Run with Coverage

```bash
pytest tests/unit/workflow/test_cursor_executor_issue10_*.py \
  tests/integration/test_simple_mode_full_workflow_issue10.py \
  --cov=tapps_agents.workflow.cursor_executor \
  --cov=tapps_agents.cli.commands.simple_mode \
  --cov-report=html
```

## Test Coverage

### Timeout Mechanism
- ✅ Workflow times out after configured timeout
- ✅ Timeout uses config value (2x step timeout)
- ✅ Timeout errors are logged
- ✅ Workflow completes successfully before timeout

### Initialization
- ✅ Validates workflow has steps
- ✅ Validates first step readiness
- ✅ Creates state if missing
- ✅ Handles target file correctly

### No Ready Steps Handling
- ✅ Detects workflow completion
- ✅ Provides diagnostics when blocked
- ✅ Identifies missing artifacts
- ✅ Handles multiple blocking steps

### Health Check
- ✅ Returns not_started when workflow not started
- ✅ Returns basic workflow information
- ✅ Detects stuck workflows (no progress in 5 minutes)
- ✅ Doesn't flag as stuck when progress is recent
- ✅ Includes error information
- ✅ Calculates progress percentage correctly

### Integration Tests
- ✅ Simple Mode full with --auto flag
- ✅ Timeout handling
- ✅ Auto-execution warnings
- ✅ Progress reporting
- ✅ Error handling

## Expected Test Results

All tests should pass. The tests are designed to:

1. **Verify fixes work correctly** - All implemented fixes are tested
2. **Prevent regressions** - Tests will fail if fixes are removed
3. **Validate edge cases** - Tests cover various scenarios
4. **Ensure error messages are clear** - Tests verify error messages are actionable

## Notes

- Integration tests require Cursor mode environment (`TAPPS_AGENTS_MODE=cursor`)
- Some integration tests may take longer to run (timeout tests)
- Mocking is used extensively in unit tests to avoid actual workflow execution
- Integration tests use subprocess to test actual CLI behavior

## Troubleshooting

### Tests Fail with "Cursor mode not detected"
- Ensure `TAPPS_AGENTS_MODE=cursor` is set in environment
- Check that `CURSOR_IDE=1` is set

### Integration Tests Timeout
- Increase timeout values in test fixtures if needed
- Check that Background Agents are not required for these tests

### Mock Errors
- Ensure all required mocks are set up in fixtures
- Check that mock return values match expected types

