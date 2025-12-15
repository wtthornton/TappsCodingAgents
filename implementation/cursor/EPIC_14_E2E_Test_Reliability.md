# Epic 14: E2E Test Reliability & Failure Transparency

## Epic Goal

Eliminate **excessive fallbacks** and **failure masking** in E2E tests. Tests should fail clearly and immediately when functionality is broken, with transparent error messages and no hidden fallback paths that allow tests to pass when they should fail.

## Epic Description

### Existing System Context

- **Current relevant functionality**: E2E tests have multiple fallback paths that mask failures:
  - Scenario validator has fallback paths for artifact location
  - Tests skip instead of failing when dependencies are missing
  - State loading has fallback logic that hides real issues
  - Error handling catches exceptions and continues instead of failing
- **Technology stack**: `pytest`, existing E2E harness, scenario validator in `tests/e2e/fixtures/scenario_validator.py`.
- **Integration points**:
  - `tests/e2e/scenarios/` - scenario tests with fallback logic
  - `tests/e2e/workflows/` - workflow tests with skip logic
  - `tests/e2e/fixtures/scenario_validator.py` - validator with multiple fallback paths
  - `tests/e2e/fixtures/workflow_runner.py` - runner with exception handling

### Enhancement Details

- **What's being added/changed**:
  - **Remove fallback paths**: Eliminate fallback logic that masks failures (e.g., try multiple artifact locations, skip on missing files).
  - **Fail fast**: Tests should fail immediately when dependencies are missing or functionality is broken.
  - **Clear error messages**: Provide specific, actionable error messages that indicate what failed and why.
  - **Strict validation**: Validators should fail on first error, not collect errors and continue.
  - **Dependency checking**: Pre-flight checks for required dependencies (workflow files, templates, etc.).

- **How it integrates**:
  - Refactors existing E2E test utilities to remove fallbacks.
  - Updates scenario validator to fail fast.
  - Enhances error messages throughout E2E suite.
  - Adds dependency validation before test execution.

- **2025 standards / guardrails**:
  - **Fail fast**: Tests should fail immediately when something is wrong, not try multiple fallback paths.
  - **No silent failures**: All failures should be explicit and visible. No catching exceptions and continuing.
  - **Clear errors**: Error messages should be specific and actionable:
    - What failed (specific component, file, assertion)
    - Why it failed (missing dependency, incorrect value, broken functionality)
    - How to fix (suggested action, required setup)
  - **Strict validation**: Validators should fail on first error, not collect errors and continue.
  - **Dependency validation**: Pre-flight checks ensure required dependencies exist before test execution.
  - **No skips for missing dependencies**: Tests should fail if dependencies are missing, not skip (unless explicitly marked as optional).

- **Success criteria**:
  - Tests fail immediately when functionality is broken
  - Error messages are clear and actionable
  - No fallback paths mask failures
  - Dependency validation prevents cryptic failures
  - Test failures are transparent and debuggable

## Stories

1. **Story 14.1: Remove Fallback Paths in Scenario Validator**
   - Refactor `scenario_validator.py` to remove fallback artifact location logic
   - Fail immediately if expected artifacts don't exist at expected locations
   - Add clear error messages indicating expected vs actual artifact locations
   - Remove fallback logic for test file existence checks

2. **Story 14.2: Strict Dependency Validation**
   - Add pre-flight dependency validation:
     - Check workflow files exist before test execution
     - Check scenario templates exist before test setup
     - Check required fixtures are available
     - Validate project structure before execution
   - Fail tests immediately if dependencies are missing (don't skip)
   - Add clear error messages for missing dependencies

3. **Story 14.3: Fail-Fast Error Handling**
   - Remove exception catching that masks failures:
     - Don't catch exceptions and continue in workflow runner
     - Don't catch exceptions and skip in scenario tests
     - Don't catch exceptions and log warnings in validators
   - Let exceptions propagate with clear error messages
   - Add context to exceptions (what was being tested, what failed)

4. **Story 14.4: Clear Error Messages**
   - Enhance error messages throughout E2E suite:
     - Include context (test name, step, workflow)
     - Include expected vs actual values
     - Include suggestions for fixing issues
     - Include stack traces for debugging
   - Create error message utilities in `tests/e2e/fixtures/error_helpers.py`
   - Standardize error message format across E2E suite

5. **Story 14.5: Strict Validation Mode**
   - Add strict validation mode to validators:
     - Fail on first error (don't collect errors and continue)
     - No fallback paths
     - No optional validations that can be skipped
   - Make strict mode default for E2E tests
   - Add relaxed mode for development/debugging (opt-in)

## Compatibility Requirements

- [ ] Existing tests continue to work (but may fail more often due to strict validation)
- [ ] Error messages are backward compatible (don't break test output parsing)
- [ ] Dependency validation is opt-out (can be disabled for specific tests if needed)

## Risk Mitigation

- **Primary Risk**: Strict validation causes more test failures, making tests appear flaky.
- **Mitigation**:
  - Better error messages make failures easier to debug
  - Pre-flight dependency validation prevents cryptic failures
  - Failures are now visible instead of hidden, which is better for reliability
  - Add relaxed mode for development/debugging
- **Rollback Plan**: Can temporarily disable strict validation via markers if needed.

## Definition of Done

- [x] Fallback paths removed from scenario validator
- [x] Dependency validation implemented and tested
- [x] Fail-fast error handling implemented
- [x] Clear error messages added throughout E2E suite
- [x] Strict validation mode implemented and default
- [x] All tests updated to use strict validation
- [ ] Documentation updated with error handling patterns (optional - code is self-documenting)

## Status

**COMPLETED** - All stories implemented:
- ✅ Story 14.1: Remove Fallback Paths in Scenario Validator
- ✅ Story 14.2: Strict Dependency Validation
- ✅ Story 14.3: Fail-Fast Error Handling
- ✅ Story 14.4: Clear Error Messages
- ✅ Story 14.5: Strict Validation Mode

All fallback paths removed, dependency validation added, exception handling fixed, error messages standardized, and strict validation mode implemented as default.

## Story Manager Handoff

"Please develop detailed user stories for Epic 14 (E2E Test Reliability). Key considerations:
- Remove all fallback paths that mask failures
- Add pre-flight dependency validation
- Implement fail-fast error handling
- Create clear, actionable error messages
- Make strict validation the default
- Ensure failures are transparent and debuggable"

