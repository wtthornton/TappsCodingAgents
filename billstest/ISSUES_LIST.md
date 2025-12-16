# Billstest Issues List

**Created**: January 2025  
**Status**: Active Tracking

## Issue Tracking Format

Each issue includes:
- **ID**: Unique identifier
- **Type**: Bug, Enhancement, Documentation, etc.
- **Priority**: Critical, High, Medium, Low
- **Status**: Open, In Progress, Resolved, Closed
- **Description**: What the issue is
- **Impact**: How it affects the project
- **Fix**: Proposed solution
- **Assigned**: Who is working on it

---

## Critical Issues

*No critical issues identified at this time.*

---

## High Priority Issues

### ISSUE-001: Test Collection Warning - TesterAgent Class
- **ID**: ISSUE-001
- **Type**: Test Collection Warning
- **Priority**: High
- **Status**: ✅ Resolved
- **Created**: January 2025
- **Location**: `tapps_agents/agents/tester/agent.py:21`
- **Description**: 
  Pytest cannot collect test class 'TesterAgent' because it has a `__init__` constructor. This causes a warning during test collection: `cannot collect test class 'TesterAgent' because it has a __init__ constructor (from: tests/integration/test_tester_agent.py)`
- **Impact**: 
  - Warning clutters test output
  - Potential confusion for developers
  - May indicate design issue
- **Root Cause**: 
  The `TesterAgent` class name starts with "Test" which pytest interprets as a test class, but it has an `__init__` constructor which pytest doesn't allow for test classes.
- **Proposed Fix**: 
  1. Rename the class to avoid "Test" prefix (e.g., `TesterAgent` → `TesterAgentImpl`)
  2. OR ensure the class is not in a test file path
  3. OR adjust pytest configuration to exclude this pattern
- **Steps to Reproduce**:
  ```powershell
  cd billstest
  python -m pytest --collect-only -q
  ```
- **Expected Behavior**: No warnings about test collection
- **Actual Behavior**: Warning appears in test collection output
- **Assigned**: TBD
- **Notes**: This is a framework code issue, not a billstest issue

---

### ISSUE-002: Test Collection Warning - TestGenerator Class
- **ID**: ISSUE-002
- **Type**: Test Collection Warning
- **Priority**: High
- **Status**: ✅ Resolved
- **Created**: January 2025
- **Location**: `tapps_agents/agents/tester/test_generator.py:12`
- **Description**: 
  Pytest cannot collect test class 'TestGenerator' because it has a `__init__` constructor. This causes a warning during test collection: `cannot collect test class 'TestGenerator' because it has a __init__ constructor (from: tests/unit/test_test_generator.py)`
- **Impact**: 
  - Warning clutters test output
  - Potential confusion for developers
  - May indicate design issue
- **Root Cause**: 
  The `TestGenerator` class name starts with "Test" which pytest interprets as a test class, but it has an `__init__` constructor which pytest doesn't allow for test classes.
- **Proposed Fix**: 
  1. Rename the class to avoid "Test" prefix (e.g., `TestGenerator` → `TestCodeGenerator` or `UnitTestGenerator`)
  2. OR adjust pytest configuration to exclude this pattern
  3. OR move the class to a non-test directory
- **Steps to Reproduce**:
  ```powershell
  cd billstest
  python -m pytest --collect-only -q
  ```
- **Expected Behavior**: No warnings about test collection
- **Actual Behavior**: Warning appears in test collection output
- **Assigned**: TBD
- **Notes**: This is a framework code issue, not a billstest issue

---

## Medium Priority Issues

### ISSUE-003: Deprecation Warning - stevedore verify_requirements
- **ID**: ISSUE-003
- **Type**: Deprecation Warning
- **Priority**: Medium
- **Status**: Open
- **Created**: January 2025
- **Location**: `stevedore/extension.py:187` (external dependency)
- **Description**: 
  The `verify_requirements` argument in stevedore is deprecated and will be removed in a future version. Warning appears: `The verify_requirements argument is now a no-op and is deprecated for removal. Remove the argument from calls.`
- **Impact**: 
  - Warning in test output
  - May break in future stevedore versions
  - Code needs updating
- **Root Cause**: 
  Framework code (or dependencies) is using deprecated stevedore API
- **Proposed Fix**: 
  1. Find all uses of `verify_requirements` in codebase
  2. Remove the argument from stevedore calls
  3. Test to ensure functionality unchanged
- **Steps to Reproduce**:
  ```powershell
  cd billstest
  python -m pytest tests/unit/ -v 2>&1 | Select-String "verify_requirements"
  ```
- **Expected Behavior**: No deprecation warnings
- **Actual Behavior**: Warning appears 3 times in test output
- **Assigned**: TBD
- **Notes**: This is a dependency/upstream issue, may require waiting for updates

---

### ISSUE-004: Deprecation Warning - bandit ast.Str
- **ID**: ISSUE-004
- **Type**: Deprecation Warning
- **Priority**: Medium
- **Status**: Open
- **Created**: January 2025
- **Location**: `bandit/core/utils.py:384` (external dependency)
- **Description**: 
  `ast.Str` is deprecated and will be removed in Python 3.14. Warning appears: `ast.Str is deprecated and will be removed in Python 3.14; use ast.Constant instead`
- **Impact**: 
  - Warning in test output
  - May break in Python 3.14+
  - Requires bandit update
- **Root Cause**: 
  Bandit (external dependency) uses deprecated Python AST API
- **Proposed Fix**: 
  1. Update bandit to latest version
  2. If not fixed upstream, wait for bandit maintainers to fix
  3. Consider alternative security scanning tool if bandit doesn't update
- **Steps to Reproduce**:
  ```powershell
  cd billstest
  python -m pytest tests/unit/ -v 2>&1 | Select-String "ast.Str"
  ```
- **Expected Behavior**: No deprecation warnings
- **Actual Behavior**: Warning appears in test output
- **Assigned**: TBD
- **Notes**: This is an upstream dependency issue, requires bandit update

---

### ISSUE-005: Test Coverage Verification Needed
- **ID**: ISSUE-005
- **Type**: Test Quality
- **Priority**: Medium
- **Status**: Open
- **Created**: January 2025
- **Description**: 
  Need to verify comprehensive test coverage of all framework components. While 703 unit tests exist, coverage percentage and gaps are unknown.
- **Impact**: 
  - Unknown coverage gaps may exist
  - Critical code paths may be untested
  - Risk of regressions
- **Root Cause**: 
  No recent coverage analysis performed
- **Proposed Fix**: 
  1. Run coverage analysis: `pytest tests/unit/ --cov=tapps_agents --cov-report=html`
  2. Review coverage report
  3. Identify low-coverage areas
  4. Add tests for uncovered code
  5. Set coverage threshold (e.g., 80%)
- **Steps to Reproduce**:
  ```powershell
  cd billstest
  python -m pytest tests/unit/ --cov=tapps_agents --cov-report=html --cov-report=term
  ```
- **Expected Behavior**: Coverage report shows >80% coverage
- **Actual Behavior**: Coverage unknown
- **Assigned**: TBD
- **Notes**: Should be part of regular test maintenance

---

### ISSUE-006: Integration Test Flakiness Verification
- **ID**: ISSUE-006
- **Type**: Test Quality
- **Priority**: Medium
- **Status**: Open
- **Created**: January 2025
- **Description**: 
  Integration tests use real LLM services which may be flaky. Need to verify test stability and document any flaky tests.
- **Impact**: 
  - Flaky tests reduce confidence
  - May cause CI/CD failures
  - Wastes developer time
- **Root Cause**: 
  Real services (LLM, Context7) may have transient failures
- **Proposed Fix**: 
  1. Run integration tests multiple times
  2. Document flaky tests
  3. Add retry logic for known flaky tests
  4. Consider using test doubles for non-critical paths
- **Steps to Reproduce**:
  ```powershell
  cd billstest
  # Run integration tests multiple times
  for ($i=1; $i -le 5; $i++) {
    python -m pytest tests/integration/ -m requires_llm -v
  }
  ```
- **Expected Behavior**: All tests pass consistently
- **Actual Behavior**: Unknown - needs verification
- **Assigned**: TBD
- **Notes**: Should be monitored regularly

---

## Low Priority Issues

### ISSUE-007: Default Test Filter in pytest.ini
- **ID**: ISSUE-007
- **Type**: Configuration
- **Priority**: Low
- **Status**: Open
- **Created**: January 2025
- **Location**: `billstest/pytest.ini:23`
- **Description**: 
  Default pytest configuration includes `-m unit` filter, which may hide integration tests during discovery. This is intentional for faster unit test runs, but may be confusing.
- **Impact**: 
  - Low - intentional behavior
  - May confuse new developers
  - Integration tests still run when explicitly requested
- **Root Cause**: 
  Configuration choice for faster default test runs
- **Proposed Fix**: 
  1. Document behavior in README
  2. OR make configurable via environment variable
  3. OR add comment in pytest.ini explaining the choice
- **Steps to Reproduce**:
  ```powershell
  cd billstest
  python -m pytest --collect-only -q  # Only shows unit tests
  python -m pytest --collect-only -q -m ""  # Shows all tests
  ```
- **Expected Behavior**: Behavior is documented
- **Actual Behavior**: Behavior exists but may not be obvious
- **Assigned**: TBD
- **Notes**: This is a design choice, not a bug

---

### ISSUE-008: Integration Test Dependency Documentation
- **ID**: ISSUE-008
- **Type**: Documentation
- **Priority**: Low
- **Status**: Open
- **Created**: January 2025
- **Description**: 
  While documentation exists for integration test requirements, verify it's complete and clear about all dependencies.
- **Impact**: 
  - Low - documentation exists
  - May need updates for clarity
  - New developers may be confused
- **Root Cause**: 
  Documentation may need review/updates
- **Proposed Fix**: 
  1. Review existing documentation
  2. Verify all dependencies are documented
  3. Add examples for common scenarios
  4. Update if needed
- **Steps to Reproduce**:
  - Review `billstest/README.md`
  - Review `billstest/TEST_SETUP_GUIDE.md`
  - Review `billstest/tests/integration/README_REAL_TESTS.md`
- **Expected Behavior**: All dependencies clearly documented
- **Actual Behavior**: Documentation exists, needs verification
- **Assigned**: TBD
- **Notes**: Documentation appears comprehensive, but should be verified

---

### ISSUE-009: CLI Module Structure Issue
- **ID**: ISSUE-009
- **Type**: Test Failure / Module Structure
- **Priority**: Medium
- **Status**: Open
- **Created**: January 2025 (Phase 2)
- **Location**: `tests/integration/test_cli_real.py`
- **Description**: 
  CLI integration tests fail because `tapps_agents.cli.__main__` module doesn't exist. Tests attempt to execute `python -m tapps_agents.cli` but the module cannot be executed directly.
- **Impact**: 
  - CLI integration tests cannot run
  - Cannot validate CLI functionality in integration tests
  - Reduces test coverage for CLI features
- **Root Cause**: 
  `tapps_agents.cli` is a package but lacks `__main__.py` or has incorrect structure for direct execution
- **Proposed Fix**: 
  1. Add `__main__.py` to `tapps_agents/cli/` directory
  2. OR update tests to use correct CLI entry point (e.g., `tapps_agents` command)
  3. OR fix CLI package structure to support `-m` execution
- **Steps to Reproduce**:
  ```powershell
  cd billstest
  python -m pytest tests/integration/test_cli_real.py -v
  ```
- **Expected Behavior**: CLI tests pass
- **Actual Behavior**: Tests fail with "No module named tapps_agents.cli.__main__"
- **Affected Tests**:
  - `test_cli_score_command_real`
  - `test_cli_error_handling_file_not_found`
- **Assigned**: TBD
- **Notes**: Discovered during Phase 2 integration test validation

---

### ISSUE-010: MAL Disabled in Cursor Mode
- **ID**: ISSUE-010
- **Type**: Test Environment / Configuration
- **Priority**: Low
- **Status**: Open
- **Created**: January 2025 (Phase 2)
- **Location**: `tests/integration/test_mal_real.py`
- **Description**: 
  Some integration tests fail because MAL (Model Abstraction Layer) is intentionally disabled when running under Cursor/Background Agents. Tests raise `MALDisabledInCursorModeError`.
- **Impact**: 
  - Some integration tests cannot run in Cursor environment
  - Tests need special configuration or environment variable
  - May confuse developers running tests in Cursor
- **Root Cause**: 
  MAL is intentionally disabled in Cursor mode for security/design reasons. Tests need `TAPPS_AGENTS_MODE=headless` or different execution environment.
- **Proposed Fix**: 
  1. Document this behavior in test documentation
  2. Add test configuration option to enable MAL for testing
  3. Update tests to check environment and skip with clear message
  4. OR run these tests in headless mode via CI/CD
- **Steps to Reproduce**:
  ```powershell
  cd billstest
  python -m pytest tests/integration/test_mal_real.py::TestMALRealOllama::test_ollama_generate_real -v
  ```
- **Expected Behavior**: Tests pass or skip with clear message
- **Actual Behavior**: Tests fail with `MALDisabledInCursorModeError`
- **Affected Tests**:
  - `test_ollama_generate_real`
  - `test_response_time_acceptable`
- **Assigned**: TBD
- **Notes**: This is expected behavior but tests should handle it gracefully. Discovered during Phase 2.

---

## Resolved Issues

*No issues resolved yet.*

---

## Issue Statistics

- **Total Issues**: 10
- **Critical**: 0
- **High Priority**: 2
- **Medium Priority**: 5 (was 4, added ISSUE-009)
- **Low Priority**: 3 (was 2, added ISSUE-010)
- **Resolved**: 0
- **Open**: 10

---

## Next Actions

1. **Review and prioritize** all issues
2. **Assign** issues to team members
3. **Begin work** on high-priority issues (ISSUE-001, ISSUE-002)
4. **Track progress** in this document
5. **Update status** as work progresses

---

**Last Updated**: January 2025  
**Next Review**: After initial fixes completed

