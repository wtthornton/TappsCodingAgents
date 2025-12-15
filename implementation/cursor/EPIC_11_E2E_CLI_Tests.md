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
   - Define subprocess runner utilities (cwd isolation, env injection, timeout handling).
   - Standardize capturing artifacts for failed CLI runs.

2. **Story 11.2: CLI Golden Paths**
   - Validate a small set of most-used commands end-to-end (review/score/workflow list/start/status).
   - Validate JSON output shape and essential keys.

3. **Story 11.3: CLI Failure Paths + UX Contracts**
   - Validate common error cases: missing file, missing workflow, invalid args, missing credentials.
   - Ensure errors are user-actionable and exit codes are non-zero where appropriate.

## Compatibility Requirements

- [ ] CLI E2E tests are opt-in and do not slow unit-only defaults.
- [ ] Tests are robust on Windows path semantics.
- [ ] No changes required to external services for baseline CLI E2E.

## Risk Mitigation

- **Primary Risk**: CLI output assertions become brittle over time.
- **Mitigation**: Validate stable “contract fields” and avoid over-constraining human-readable text; prefer JSON mode where possible.
- **Rollback Plan**: Reduce scope to contract fields and keep UX text checks to smoke-level assertions.

## Definition of Done

- [ ] CLI E2E harness exists and is reused across CLI tests.
- [ ] Golden-path commands validated via subprocess in isolated sandboxes.
- [ ] Failure paths validated with stable exit-code + message expectations.

## Story Manager Handoff

“Please develop detailed user stories for Epic 11 (E2E CLI Tests). Key considerations:
- Prefer JSON output for stable assertions; avoid brittle string matching.
- Ensure tests run cleanly on Windows (paths, quoting, shells).
- Keep CLI E2E opt-in and fast enough for PR smoke execution.”

