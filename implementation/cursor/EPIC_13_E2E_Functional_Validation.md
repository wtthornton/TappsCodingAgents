# Epic 13: E2E Functional Validation & Real Execution Testing

## Epic Goal

Transform E2E tests from **structural validation** (checking that files exist and state has fields) to **functional validation** (verifying that workflows produce correct outcomes, agents execute correctly, and code changes are valid). Tests should fail if functionality is broken, not just if structure is wrong.

## Epic Description

### Existing System Context

- **Current relevant functionality**: E2E tests exist but primarily validate infrastructure (parsing, state structure, file existence). Tests use generic `mock_mal` that returns "Mock LLM response" without simulating real agent behavior.
- **Technology stack**: `pytest`, `pytest-asyncio`, existing E2E harness in `tests/e2e/fixtures/`, workflow executor in `tapps_agents/workflow/executor.py`.
- **Integration points**:
  - `tests/e2e/smoke/` - smoke tests (currently structural only)
  - `tests/e2e/workflows/` - workflow tests (currently run 2-3 steps, no outcome validation)
  - `tests/e2e/scenarios/` - scenario tests (currently check file existence, not correctness)
  - `tests/conftest.py` - `mock_mal` fixture (currently too generic)

### Enhancement Details

- **What's being added/changed**:
  - **Behavioral mocks**: Replace generic `mock_mal` with agent-specific mocks that simulate real behavior (command parsing, response generation, error handling).
  - **Outcome validation**: Add assertions that verify code changes are correct, tests pass, bugs are fixed, features work.
  - **Full workflow execution**: Test complete workflows, not just 2-3 steps.
  - **Content validation**: Validate artifact content quality, not just existence.
  - **Test execution**: Actually run tests in scenario validators, not just check files exist.

- **How it integrates**:
  - Enhances existing E2E test suite without breaking current tests.
  - Builds on existing E2E harness and fixtures.
  - Adds new validation utilities to `tests/e2e/fixtures/`.
  - Extends scenario validator to run tests and validate outcomes.

- **2025 standards / guardrails**:
  - **Functional over structural**: Tests must validate functionality, not just structure. A test should fail if code is wrong, not just if a file is missing.
  - **Behavioral mocks**: Mocks should simulate real agent behavior (command parsing, response generation, error cases), not just return success.
  - **Outcome validation**: Tests must verify:
    - Code changes are correct (not just that files changed)
    - Tests actually pass (run tests, don't just check files exist)
    - Bugs are actually fixed (verify fix correctness, not just bug removal)
    - Features work correctly (validate functionality, not just code exists)
  - **Full execution**: Test complete workflows when possible, or at least validate that partial execution produces correct intermediate results.
  - **Content quality**: Validate artifact content (code quality, documentation completeness), not just existence.
  - **Fail fast**: Remove excessive fallbacks that mask failures. Tests should fail clearly when functionality is broken.

- **Success criteria**:
  - Tests fail when agents produce incorrect output (not just when structure is wrong)
  - Tests validate code correctness, not just file existence
  - Tests actually run test suites and verify results
  - Behavioral mocks simulate real agent behavior
  - Full workflows are tested end-to-end

## Stories

1. **Story 13.1: Behavioral Mock System**
   - Replace generic `mock_mal` with agent-specific behavioral mocks
   - Mocks should simulate:
     - Command parsing and validation
     - Response generation based on input
     - Error handling and edge cases
     - Agent-specific behavior (planner plans, implementer implements, reviewer reviews)
   - Create mock factory utilities in `tests/e2e/fixtures/mock_agents.py`
   - Update existing tests to use behavioral mocks

2. **Story 13.2: Outcome Validation Framework**
   - Create outcome validation utilities in `tests/e2e/fixtures/outcome_validator.py`:
     - Code correctness validation (syntax, logic, style)
     - Test execution and result validation
     - Bug fix correctness validation
     - Feature implementation correctness validation
     - Code quality validation (linting, type checking)
   - Integrate with scenario validator to actually run tests
   - Add content quality checks for artifacts

3. **Story 13.3: Full Workflow Execution Tests**
   - Extend workflow tests to execute complete workflows (not just 2-3 steps)
   - Add validation of:
     - Step execution order correctness
     - Step dependency resolution
     - Intermediate state correctness
     - Final outcome correctness
   - Add tests for gate routing (pass/fail paths)
   - Add tests for error handling and recovery

4. **Story 13.4: Scenario Outcome Validation**
   - Enhance scenario tests to validate actual outcomes:
     - Bug fix tests verify bugs are actually fixed (run tests, check behavior)
     - Feature tests verify features work correctly (run tests, check functionality)
     - Refactor tests verify code quality improved (run linting, type checking)
   - Remove excessive fallbacks that mask failures
   - Add test execution to scenario validator (actually run pytest)
   - Validate code changes are correct, not just that files changed

5. **Story 13.5: Artifact Content Validation**
   - Add content validation utilities:
     - Code quality checks (linting, type checking, complexity)
     - Documentation completeness checks
     - Test coverage validation
     - Artifact structure and content validation
   - Update artifact assertions to validate content, not just existence
   - Add quality gates to scenario tests

## Compatibility Requirements

- [ ] Existing E2E tests continue to pass (structural tests remain valid)
- [ ] New functional tests are additive (don't break existing suite)
- [ ] Behavioral mocks are opt-in (existing tests can still use generic mocks)
- [ ] Test execution is configurable (can be disabled for fast runs)

## Risk Mitigation

- **Primary Risk**: Functional tests are slower and more brittle than structural tests.
- **Mitigation**: 
  - Keep structural tests for fast feedback
  - Functional tests run in scheduled CI, not PR gating
  - Use behavioral mocks for fast execution, real agents for scheduled runs
  - Add timeouts and retries for flaky tests
- **Rollback Plan**: Functional validation can be disabled via markers; structural tests remain as baseline.

## Definition of Done

- [x] Behavioral mock system implemented and documented
- [x] Outcome validation framework created and integrated
- [x] Full workflow execution tests added
- [x] Scenario tests validate actual outcomes
- [x] Artifact content validation implemented
- [x] All new tests pass consistently (test execution integrated)
- [x] Documentation updated with new validation patterns

## Status

**COMPLETED** - All stories implemented:
- ✅ Story 13.1: Behavioral Mock System - Implemented (`tests/e2e/fixtures/mock_agents.py`)
- ✅ Story 13.2: Outcome Validation Framework - Implemented (`tests/e2e/fixtures/outcome_validator.py`)
- ✅ Story 13.3: Full Workflow Execution Tests - Implemented (full workflow execution tests in `test_full_sdlc_workflow.py`, `test_quality_workflow.py`, `test_quick_fix_workflow.py`)
- ✅ Story 13.4: Scenario Outcome Validation - Implemented (enhanced scenario validator with test execution in `scenario_validator.py`)
- ✅ Story 13.5: Artifact Content Validation - Implemented (`tests/e2e/fixtures/content_validator.py`)

All major components implemented and integrated. Behavioral mocks, outcome validation, full workflow execution, scenario outcome validation, and artifact content validation are all in place.

## Story Manager Handoff

"Please develop detailed user stories for Epic 13 (E2E Functional Validation). Key considerations:
- Replace generic mocks with behavioral mocks that simulate real agent behavior
- Add outcome validation (code correctness, test results, bug fixes)
- Test complete workflows, not just 2-3 steps
- Validate artifact content quality, not just existence
- Remove fallbacks that mask failures
- Keep structural tests for fast feedback, add functional tests for comprehensive validation"

