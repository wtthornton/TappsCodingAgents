# Epic 12: E2E CI/CD Execution (Matrix, Scheduling, Reporting)

## Epic Goal

Integrate the hybrid E2E suite into CI/CD with a clear **execution matrix**, secure handling of real-service credentials, deterministic environment setup, and actionable reporting so E2E results are trustworthy and operationally useful.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Tests are organized and marker-driven; real integration test guidance exists in `tests/integration/README_REAL_TESTS.md`; some tests depend on external services and are designed to skip.
- **Technology stack**: `pytest` with strict markers; optional real providers (Ollama/Anthropic/OpenAI) and Context7 API.
- **Integration points**:
  - CI jobs that run `pytest` by marker slices
  - Secure env var injection for `requires_llm` / `requires_context7`
  - Artifact collection for logs/state/output bundles

### Enhancement Details

- **What’s being added/changed**:
  - CI pipeline matrix:
    - PR: unit + e2e_smoke
    - main: unit + integration (mocked) + e2e_workflow (mocked)
    - nightly: e2e_scenario + real-service suites (requires credentials)
  - Standard reporting:
    - JUnit (for CI UI), and a failure bundle (logs/state/artifacts) for debugging.
  - Guardrails:
    - timeouts, reruns (selective), and cost controls for real-service jobs.
- **How it integrates**:
  - Uses the marker taxonomy from Epic 8 and test suite layout from Epics 9–11.
  - Extends existing real-tests documentation with E2E scheduling guidance.
- **2025 standards / guardrails**:
  - **Fast PR gating**: PR checks must not require external services; run unit + e2e_smoke only (deterministic).
  - **Real-suite isolation**: real LLM/Context7 suites run only on schedule/manual triggers with credential gates (skip, don’t fail).
  - **Security**: CI artifacts must be scrubbed (no secrets/PII); enforce redaction for logs/state bundles before upload.
  - **Observability**: attach correlation IDs to CI logs; always upload failure bundles (state snapshots, logs, outputs) for diagnosis.
  - **Reliability**: enforce timeouts at job and suite level; allow bounded retries for flaky external dependencies only.
  - **Cost controls**: cap total runtime and API usage for real-service jobs; alert on regressions.
- **Success criteria**:
  - CI runs are fast by default and provide deep confidence via scheduled E2E runs.
  - Failures are diagnosable without rerunning locally.

## Stories

1. **Story 12.1: CI Matrix for E2E Slices**
   - **Goal**: Create CI/CD pipeline matrix with proper job separation for different test slices (PR, main, nightly).
   - **Acceptance Criteria**:
     - PR checks job runs `pytest -m "unit or e2e_smoke"` (fast, no external services)
     - Main branch job runs `pytest -m "unit or integration or e2e_workflow"` (mocked by default)
     - Nightly/scheduled job runs `pytest -m "e2e_scenario or (e2e_workflow and requires_llm)"` (real services)
     - All markers are registered in `pytest.ini` and validated with `--strict-markers`
     - Deterministic environment setup (Python version, dependencies, etc.)
     - Jobs are properly isolated (separate jobs for different test slices)
     - Jobs can be triggered manually via `workflow_dispatch`
   - **Deliverables**:
     - Updated GitHub Actions workflow (`.github/workflows/e2e.yml`)
     - CI matrix configuration with proper marker expressions
     - Environment setup steps (Python version, dependencies)
     - Job separation (pr-checks, main-branch, nightly)

2. **Story 12.2: Reporting + Failure Artifact Bundling**
   - **Goal**: Produce consistent test reports and failure artifacts for debugging.
   - **Acceptance Criteria**:
     - JUnit XML reports generated for all test runs (`--junitxml`)
     - JUnit reports uploaded as CI artifacts
     - Failure bundles created on test failures (logs, state snapshots, produced files)
     - Failure bundles are redacted (no secrets/PII)
     - Failure bundles uploaded as CI artifacts
     - Test summaries published in CI output (pass/fail counts, duration)
     - Correlation IDs attached to CI logs and artifacts
     - Artifacts are organized by test run and job
   - **Deliverables**:
     - Pytest JUnit XML report generation
     - Failure artifact bundling utilities
     - Artifact upload steps in CI workflows
     - Artifact redaction utilities (reuse from existing harness)

3. **Story 12.3: Real-Service Safety Controls**
   - **Goal**: Implement safety controls for real-service tests (credentials, timeouts, cost limits).
   - **Acceptance Criteria**:
     - Credential presence gates: tests skip (don't fail) if credentials unavailable
     - Token/time budgeting: configurable limits per test suite
     - Per-suite timeouts: configurable timeouts for different test types
     - Scheduled-only enforcement: real-service tests only run on schedule/manual triggers
     - Cost controls: alert on regressions (token usage, API calls)
     - Tests gracefully skip when services unavailable
     - Environment variable validation before test execution
   - **Deliverables**:
     - Credential gate utilities (check for required env vars)
     - Timeout configuration per test suite
     - Cost tracking utilities (token usage, API calls)
     - Scheduled-only job configuration
     - Skip logic for missing credentials

## Compatibility Requirements

- [x] PR checks remain fast and do not require external services.
- [x] Missing credentials never break baseline CI; real suites skip cleanly.
- [x] Reporting artifacts do not leak secrets/PII.

## Risk Mitigation

- **Primary Risk**: CI becomes slow/expensive or flaky due to external services.
- **Mitigation**: Keep PR gating minimal; move real suites to scheduled jobs; add strict timeouts and artifact capture.
- **Rollback Plan**: Disable scheduled real suites temporarily while preserving smoke/workflow suites and reporting.

## Definition of Done

- [x] CI matrix exists and runs the correct marker slices.
- [x] Nightly/pre-release E2E suite runs with real services when available.
- [x] Failures publish actionable artifacts and summaries.
- [x] Security review confirms no secrets are leaked in logs/artifacts.

## Status

**COMPLETE** - All stories (12.1, 12.2, 12.3) have been implemented and verified.

### Completed Stories

1. **Story 12.1: CI Matrix for E2E Slices** ✅
   - Created GitHub Actions workflow (`.github/workflows/e2e.yml`)
   - PR checks job runs `pytest -m "unit or e2e_smoke"` (fast, no external services)
   - Main branch job runs `pytest -m "unit or integration or e2e_workflow"` (mocked by default)
   - Nightly/scheduled job runs `pytest -m "e2e_scenario or (e2e_workflow and requires_llm)"` (real services)
   - All markers registered in `pytest.ini` and validated with `--strict-markers`
   - Deterministic environment setup (Python version, dependencies)
   - Jobs properly isolated (separate jobs for different test slices)
   - Jobs can be triggered manually via `workflow_dispatch`

2. **Story 12.2: Reporting + Failure Artifact Bundling** ✅
   - JUnit XML reports generated for all test runs (`--junitxml`)
   - JUnit reports uploaded as CI artifacts
   - Failure artifact bundling utilities in `tests/e2e/fixtures/ci_artifacts.py`
   - Failure bundles created on test failures (logs, state snapshots, produced files)
   - Failure bundles are redacted (no secrets/PII)
   - Failure bundles uploaded as CI artifacts
   - Test summaries published in CI output (pass/fail counts, duration)
   - Correlation IDs attached to CI logs and artifacts
   - Artifacts organized by test run and job

3. **Story 12.3: Real-Service Safety Controls** ✅
   - Credential gate utilities in `tests/e2e/fixtures/ci_safety.py`
   - Credential presence gates: tests skip (don't fail) if credentials unavailable
   - Token/time budgeting: configurable limits per test suite
   - Per-suite timeouts: configurable timeouts for different test types
   - Scheduled-only enforcement: real-service tests only run on schedule/manual triggers
   - Cost controls: alert on regressions (token usage, API calls)
   - Tests gracefully skip when services unavailable
   - Environment variable validation before test execution

### Key Deliverables

- **CI/CD Workflow**: Complete GitHub Actions workflow with proper job separation
- **Artifact Bundling**: Failure artifact collection and redaction utilities
- **Safety Controls**: Credential gates, timeouts, and cost controls
- **Reporting**: JUnit XML reports and test summaries
- **Documentation**: CI/CD execution guide

### Verification

- CI workflow properly configured with marker expressions
- JUnit reports generated and uploaded as artifacts
- Failure artifacts collected and redacted
- Credential gates skip tests gracefully when credentials unavailable
- Real-service tests only run on schedule/manual triggers
- All artifacts are redacted (no secrets/PII)
- Test summaries published in CI output

### CI/CD Workflow Structure

**PR Checks Job:**
- Runs: `pytest -m "unit or e2e_smoke"`
- Timeout: 10 minutes
- No external services required
- Fast execution (< 1 minute typically)

**Main Branch Job:**
- Runs: `pytest -m "unit or integration or e2e_workflow"`
- Timeout: 30 minutes
- Uses mocked services (no external dependencies)
- Moderate execution time (< 5 minutes typically)

**Nightly Job:**
- Runs: `pytest -m "e2e_scenario or (e2e_workflow and requires_llm) or (e2e_cli and requires_llm)"`
- Timeout: 60 minutes
- Uses real services (requires credentials)
- Longer execution time (10+ minutes)
- Tests skip gracefully if credentials unavailable

## Story Manager Handoff

“Please develop detailed user stories for Epic 12 (E2E CI/CD Execution). Key considerations:
- Keep PR checks fast (unit + e2e_smoke only).
- Run real-service suites on schedule with credential gates and cost/time caps.
- Ensure CI publishes debug artifacts (logs/state/output) and redacts secrets.”

