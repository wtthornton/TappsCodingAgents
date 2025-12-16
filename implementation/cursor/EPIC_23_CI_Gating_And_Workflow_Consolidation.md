# Epic 23: CI Gating & Workflow Consolidation (No "False Green")

## Status

**Complete** - All stories completed and acceptance criteria met.

## Epic Goal

Ensure CI results are **trustworthy and enforceable**: failures fail builds, required checks actually gate PRs, and workflows are consolidated to avoid duplication and drift.

## Epic Description

### Existing System Context

- **Current relevant functionality**: GitHub Actions workflows exist for lint/type/test and E2E slices.
- **Technology stack**: GitHub Actions, Python 3.13, pytest, ruff, mypy, codecov.
- **Integration points**:
  - `.github/workflows/ci.yml` (canonical workflow - includes lint, type-check, test)
  - `.github/workflows/e2e.yml` (E2E tests with PR/main/nightly jobs)

### Enhancement Details

- **What’s being improved (no new features)**:
  - Remove “continue-on-error” patterns that allow failures to pass silently in required checks.
  - Reduce redundant workflows and align install/test commands.
  - Harden workflows with least-privilege permissions and clearer reporting.
- **How it integrates**:
  - Keeps existing checks (lint/type/tests/e2e); improves gating and reduces duplication.
- **2025 standards / guardrails**:
  - **Required checks must be deterministic**: PR checks should reliably fail on test failures.
  - **Least privilege**: explicit `permissions:` on workflows/jobs.
  - **Fast PR gating**: keep PR checks fast; deep suites run in scheduled jobs.
  - **Consistent environment**: same install method and Python setup across workflows.
- **Success criteria**:
  - CI status reflects reality; no “green despite failures.”
  - Contributors understand which workflow to rely on and why.

## Stories

1. **Story 23.1: Make test failures fail PR checks** ✅ **Complete**
   - **Goal**: Ensure PR gating is strict where intended.
   - **Acceptance Criteria**:
     - ✅ PR workflows return non-zero when tests fail (removed `continue-on-error` from PR checks in `e2e.yml`).
     - ✅ Artifact upload still occurs on failures (`if: always()`), but does not mask failure status.
     - ✅ Clear job summary indicates failures and how to debug (enhanced test summaries with debugging tips).

2. **Story 23.2: Consolidate overlapping CI workflows** ✅ **Complete**
   - **Goal**: Remove duplication and drift between `ci.yml` and `test.yml`.
   - **Acceptance Criteria**:
     - ✅ Only one canonical unit test workflow remains (`ci.yml` is the canonical workflow; `test.yml` removed).
     - ✅ All workflows use a consistent install strategy per Epic 21 (`pip install -e ".[dev]"`).
     - ✅ Documentation references the canonical workflow (updated epic documentation).

3. **Story 23.3: Add explicit workflow permissions** ✅ **Complete**
   - **Goal**: Reduce attack surface and align with 2025 GitHub security best practices.
   - **Acceptance Criteria**:
     - ✅ Each workflow defines minimal `permissions:` (e.g., `contents: read`, etc.) required for its actions.
     - ✅ Any elevated permissions are justified in comments (`checks: write` for Codecov in `ci.yml`).

4. **Story 23.4: Normalize reporting and artifacts** ✅ **Complete**
   - **Goal**: Make failures diagnosable without reruns.
   - **Acceptance Criteria**:
     - ✅ JUnit XML and coverage artifacts are always uploaded for relevant jobs (all workflows use `if: always()`).
     - ✅ Failure artifacts are captured and redacted where applicable (nightly job already collects failure artifacts).

## Compatibility Requirements

- [x] Existing marker strategy and E2E suite layout remains unchanged.
- [x] CI remains compatible with public forks (no reliance on unavailable secrets for PR checks).

## Risk Mitigation

- **Primary Risk**: Tightening gating could surface existing flakiness.
- **Mitigation**:
  - Keep PR gating to deterministic slices; quarantine flaky suites to nightly.
  - Add bounded retries only for external dependency slices.
- **Rollback Plan**:
  - Temporarily relax the strictest gates while tracking flakiness root causes.

## Definition of Done

- [x] PR checks fail when tests fail (no silent pass).
- [x] CI workflows are consolidated or clearly separated with no duplication.
- [x] Workflows declare least-privilege permissions.
- [x] Artifact and summary reporting is consistent.

## Integration Verification

- **IV1**: A known failing unit test causes PR checks to fail.
- **IV2**: Successful runs produce expected coverage/JUnit artifacts.
- **IV3**: Fork PRs run without secrets and still provide valid results.


