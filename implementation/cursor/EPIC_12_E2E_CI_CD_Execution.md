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
   - Add CI jobs for smoke/workflow/scenario/real suites using marker expressions.
   - Ensure strict marker registration and deterministic env setup.

2. **Story 12.2: Reporting + Failure Artifact Bundling**
   - Produce consistent artifacts on failure: logs, state snapshots, produced files.
   - Publish JUnit + minimal summaries suitable for PR checks.

3. **Story 12.3: Real-Service Safety Controls**
   - Credential presence gates (skip, don’t fail).
   - Token/time budgeting and per-suite timeouts.
   - Scheduled-only enforcement for real LLM/Context7 tests.

## Compatibility Requirements

- [ ] PR checks remain fast and do not require external services.
- [ ] Missing credentials never break baseline CI; real suites skip cleanly.
- [ ] Reporting artifacts do not leak secrets/PII.

## Risk Mitigation

- **Primary Risk**: CI becomes slow/expensive or flaky due to external services.
- **Mitigation**: Keep PR gating minimal; move real suites to scheduled jobs; add strict timeouts and artifact capture.
- **Rollback Plan**: Disable scheduled real suites temporarily while preserving smoke/workflow suites and reporting.

## Definition of Done

- [ ] CI matrix exists and runs the correct marker slices.
- [ ] Nightly/pre-release E2E suite runs with real services when available.
- [ ] Failures publish actionable artifacts and summaries.
- [ ] Security review confirms no secrets are leaked in logs/artifacts.

## Story Manager Handoff

“Please develop detailed user stories for Epic 12 (E2E CI/CD Execution). Key considerations:
- Keep PR checks fast (unit + e2e_smoke only).
- Run real-service suites on schedule with credential gates and cost/time caps.
- Ensure CI publishes debug artifacts (logs/state/output) and redacts secrets.”

