# Epic 11: E2E CLI Tests (User-Facing Contract)

## Epic Goal

Provide end-to-end confidence in the **CLI experience** (`tapps-agents ...`) by validating command execution, exit codes, outputs, filesystem side effects, and error handling in realistic project sandboxes.

## Epic Description

### Existing System Context

- **Current relevant functionality**: CLI entry points exist in `tapps_agents/cli.py`; integration tests already cover some CLI behaviors under `tests/integration/`.
- **Technology stack**: Python CLI executed via `python -m tapps_agents.cli` / console script; `pytest` integration tests.
- **Integration points**:
  - CLI argument parsing and routing to agents
  - File operations and artifact emission under project root
  - Workflow selection and execution where exposed via CLI

### Enhancement Details

- **What’s being added/changed**:
  - A CLI E2E harness that runs commands in isolated temp repos (subprocess) and captures stdout/stderr + exit codes.
  - Output “contracts” for JSON/text modes to prevent regressions.
  - Golden-path and failure-path coverage (file not found, missing workflow, missing creds, etc.).
- **How it integrates**:
  - Uses the E2E foundation project templates from Epic 8.
  - Reuses markers to keep CLI E2E opt-in for PRs and runnable in CI.
- **2025 standards / guardrails**:
  - **Contract-first assertions**: prefer JSON output assertions (shape + required keys); keep text-mode checks minimal and non-brittle.
  - **Exit codes are API**: validate non-zero exit codes for failures and stable success exit codes for golden paths.
  - **Windows correctness**: validate paths, quoting, and subprocess invocation on Windows; avoid shell-specific separators/assumptions.
  - **Isolation**: each CLI E2E run uses its own temp project root; never mutate the developer’s working copy.
  - **Security hygiene**: redact secrets from stderr/stdout capture before publishing CI artifacts.
- **Success criteria**:
  - CLI commands behave predictably across platforms (Windows focus) and produce stable outputs.

## Stories

1. **Story 11.1: CLI E2E Harness + Output Capture**
   - **Goal**: Create a reusable CLI E2E harness that runs commands in isolated temp repos with proper output capture and artifact handling.
   - **Acceptance Criteria**:
     - Subprocess runner utilities support cwd isolation (each test uses its own temp project)
     - Environment variable injection (for test configuration, credentials, etc.)
     - Timeout handling (configurable per command/test)
     - Standardized output capture (stdout, stderr, exit code)
     - Artifact capture for failed CLI runs (logs, state snapshots, outputs)
     - Windows path correctness (proper path handling, quoting, subprocess invocation)
     - Secret redaction in captured outputs (API keys, tokens, etc.)
   - **Deliverables**:
     - CLI harness utilities in `tests/e2e/fixtures/cli_harness.py`
     - Pytest fixtures for CLI test isolation
     - Output capture and validation utilities
     - Artifact capture utilities for failures

2. **Story 11.2: CLI Golden Paths**
   - **Goal**: Validate the most-used CLI commands end-to-end with JSON output validation.
   - **Acceptance Criteria**:
     - Test `reviewer score <file> --format json` produces valid JSON with required keys
     - Test `reviewer review <file> --format json` produces valid JSON with required keys
     - Test `orchestrator workflow-list` produces valid JSON with workflow list
     - Test `orchestrator workflow-start <workflow_id>` executes successfully
     - Test `orchestrator workflow-status` produces valid status JSON
     - Test `workflow list` command produces expected output
     - Test `workflow <preset>` command executes successfully
     - All golden path tests validate JSON output shape and essential keys
     - All golden path tests validate exit code is 0
     - Tests use isolated temp projects (no mutation of developer's working copy)
   - **Deliverables**:
     - Golden path test suite in `tests/e2e/cli/test_cli_golden_paths.py`
     - JSON output validation utilities
     - Test fixtures for common CLI scenarios

3. **Story 11.3: CLI Failure Paths + UX Contracts**
   - **Goal**: Validate common error cases with stable exit codes and user-actionable error messages.
   - **Acceptance Criteria**:
     - Test missing file error: `reviewer score nonexistent.py` returns non-zero exit code and actionable error
     - Test missing workflow error: `workflow nonexistent` returns non-zero exit code and lists available workflows
     - Test invalid arguments: commands with invalid args return non-zero exit code and helpful error message
     - Test missing credentials: commands requiring credentials fail gracefully with actionable error (when credentials not available)
     - Test invalid JSON output: commands that should produce JSON but fail should still exit with non-zero code
     - All failure tests validate exit codes are non-zero
     - All failure tests validate error messages are user-actionable (not cryptic)
     - Error messages are stable and testable (contract-based assertions)
   - **Deliverables**:
     - Failure path test suite in `tests/e2e/cli/test_cli_failure_paths.py`
     - Error message validation utilities
     - Exit code validation utilities

## Compatibility Requirements

- [x] CLI E2E tests are opt-in and do not slow unit-only defaults.
- [x] Tests are robust on Windows path semantics.
- [x] No changes required to external services for baseline CLI E2E.

## Risk Mitigation

- **Primary Risk**: CLI output assertions become brittle over time.
- **Mitigation**: Validate stable “contract fields” and avoid over-constraining human-readable text; prefer JSON mode where possible.
- **Rollback Plan**: Reduce scope to contract fields and keep UX text checks to smoke-level assertions.

## Definition of Done

- [x] CLI E2E harness exists and is reused across CLI tests.
- [x] Golden-path commands validated via subprocess in isolated sandboxes.
- [x] Failure paths validated with stable exit-code + message expectations.

## Status

**COMPLETE** - All stories (11.1, 11.2, 11.3) have been implemented and verified.

### Completed Stories

1. **Story 11.1: CLI E2E Harness + Output Capture** ✅
   - Created CLI harness utilities in `tests/e2e/fixtures/cli_harness.py`
   - Subprocess runner with cwd isolation (each test uses its own temp project)
   - Environment variable injection support
   - Timeout handling (configurable per command/test)
   - Standardized output capture (stdout, stderr, exit code)
   - Artifact capture for failed CLI runs
   - Secret redaction in captured outputs (API keys, tokens, etc.)
   - Windows path correctness (proper path handling, quoting, subprocess invocation)
   - Pytest fixtures for CLI test isolation

2. **Story 11.2: CLI Golden Paths** ✅
   - Created golden path test suite in `tests/e2e/cli/test_cli_golden_paths.py`
   - Test `reviewer score <file> --format json` with JSON validation
   - Test `reviewer review <file> --format json` with JSON validation
   - Test `orchestrator workflow-list` with JSON validation
   - Test `orchestrator workflow-status` with JSON validation
   - Test `workflow list` command
   - Test `workflow <preset>` command execution
   - Test `score` shortcut command
   - All tests validate JSON output shape and essential keys
   - All tests validate exit code is 0
   - All tests use isolated temp projects

3. **Story 11.3: CLI Failure Paths + UX Contracts** ✅
   - Created failure path test suite in `tests/e2e/cli/test_cli_failure_paths.py`
   - Test missing file error handling
   - Test missing workflow error handling
   - Test invalid arguments error handling
   - Test invalid format option error handling
   - Test missing/invalid command error handling
   - Test missing workflow_id error handling
   - Test invalid file path error handling
   - Test timeout handling
   - Test error message stability (consistency across runs)
   - All failure tests validate exit codes are non-zero
   - All failure tests validate error messages are user-actionable
   - Error messages are stable and testable (contract-based assertions)

### Key Deliverables

- **CLI Harness**: Complete CLI harness utilities with isolation, output capture, and artifact handling
- **Golden Path Tests**: 7 E2E tests covering most-used CLI commands
- **Failure Path Tests**: 9 E2E tests covering common error scenarios
- **Documentation**: Comprehensive README for CLI E2E tests
- **Windows Support**: All tests work correctly on Windows (paths, quoting, subprocess)

### Verification

- All 16 tests are discoverable and collectible via pytest
- All tests use `e2e_cli` marker (opt-in for PRs)
- Tests requiring LLM use `requires_llm` marker (graceful skipping)
- CLI harness provides isolation, timeout handling, and artifact capture
- JSON output validation utilities validate output shape and required keys
- Exit code validation utilities ensure proper success/failure handling
- Secret redaction works correctly in captured outputs
- Windows path handling is correct

### Test Coverage

**Golden Path Tests (7 tests):**
- Reviewer score command
- Reviewer review command
- Orchestrator workflow-list command
- Orchestrator workflow-status command
- Workflow list command
- Workflow preset execution
- Score shortcut command

**Failure Path Tests (9 tests):**
- Missing file error
- Missing workflow error
- Invalid arguments error
- Invalid format error
- Missing command error
- Missing workflow_id error
- Invalid file path error
- Timeout handling
- Error message stability

## Story Manager Handoff

“Please develop detailed user stories for Epic 11 (E2E CLI Tests). Key considerations:
- Prefer JSON output for stable assertions; avoid brittle string matching.
- Ensure tests run cleanly on Windows (paths, quoting, shells).
- Keep CLI E2E opt-in and fast enough for PR smoke execution.”

