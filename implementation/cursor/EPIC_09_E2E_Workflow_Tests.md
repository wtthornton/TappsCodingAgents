# Epic 9: E2E Workflow Tests (Preset Workflows)

## Epic Goal

Create an E2E suite that executes **real workflow YAML presets** end-to-end (with controlled dependencies) and verifies artifacts, state transitions, gates, and failure recovery for the most important workflows shipped in `workflows/` and `workflows/presets/`.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Workflow YAML presets exist (e.g. `full-sdlc.yaml`); executor supports step progression, gates, artifacts, persistence, and logging.
- **Technology stack**: `pytest` + markers; workflow system in `tapps_agents/workflow/*`.
- **Integration points**:
  - `WorkflowParser` + schema validator (YAML parsing + validation)
  - `WorkflowExecutor` (execution, gating, state persistence, artifacts)
  - Agents invoked by workflow steps (via Python API under test)

### Enhancement Details

- **What’s being added/changed**:
  - A **workflow-runner E2E harness** that loads YAML, runs steps, and captures artifacts/state consistently.
  - E2E tests for a small set of “tier-1” workflows:
    - `workflows/presets/full-sdlc.yaml` (core orchestration)
    - `workflows/presets/quality.yaml` or `workflows/multi-agent-review-and-test.yaml` (quality path)
    - `workflows/presets/quick-fix.yaml` (fast path)
  - Gate-path tests: “pass” and “fail” routing (implementation ↔ review loop) under deterministic conditions.
- **How it integrates**:
  - Uses the E2E foundation fixtures from Epic 8.
  - Reuses existing markers (`e2e`, `requires_llm`, etc.) but defaults workflow E2E to **mocked** or **local-only** dependencies unless explicitly enabled.
- **2025 standards / guardrails**:
  - **Scope discipline**: cover only 2–3 tier-1 workflows; keep workflow E2E focused on orchestration correctness and contracts, not exhaustive agent behavior.
  - **Deterministic gates**: gate pass/fail paths must be controllable without real LLM variability (mock scoring/quality signals for routing tests).
  - **State + artifact contracts**: assert workflow state transitions, produced artifacts, and gate decisions; avoid brittle textual assertions.
  - **Reliability**: step-level timeouts and bounded retries; always persist state snapshots on failure to enable repro.
  - **Isolation**: use temp project roots and clean worktrees; ensure cleanup is idempotent and safe.
  - **Security hygiene**: failure bundles must redact secrets/PII and exclude credential material.
- **Success criteria**:
  - Workflow E2E tests validate: parse → start → step execution order → artifacts/state → gate routing → completion.
  - Failures produce actionable logs and captured state for debugging.

## Stories

1. **Story 9.1: Workflow Runner + Assertions**
   - Standard “run workflow” harness that supports:
     - deterministic temp project setup
     - step-by-step execution with captured state snapshots
     - artifact assertions (existence + minimal content checks)
     - controlled gate outcomes (pass/fail) for routing verification

2. **Story 9.2: Tier-1 Preset Workflow E2E Coverage**
   - Implement E2E tests for 2–3 highest value preset workflows.
   - Ensure tests can run in **mocked mode** by default and **real mode** behind markers/env.

3. **Story 9.3: Workflow Failure & Resume E2E**
   - Validate persistence + resume:
     - fail a mid-workflow step deterministically
     - persist state
     - reload and resume from last safe point
     - confirm artifacts/state remain consistent

## Compatibility Requirements

- [x] Workflow E2E tests are opt-in and do not alter default unit-only execution.
- [x] No breaking changes to workflow YAML schema or existing presets.
- [x] Tests do not require real external services unless explicitly enabled.

## Risk Mitigation

- **Primary Risk**: Workflow E2E becomes slow and brittle due to large, multi-step presets.
- **Mitigation**: Use “small project templates” and minimal step payloads; run only 2–3 tier-1 workflows; provide mocked-by-default mode.
- **Rollback Plan**: Keep workflow E2E tests isolated under markers; can be moved to nightly-only without blocking development.

## Definition of Done

- [x] Workflow-runner harness exists and is reused across workflow E2E tests.
- [x] 2–3 preset workflows are covered with deterministic assertions.
- [x] Gate routing is validated (pass/fail paths) with captured debug artifacts.
- [x] Resume-from-state E2E path is validated.

## Status

**COMPLETE** - All stories (9.1, 9.2, 9.3) have been implemented and verified.

### Completed Stories

1. **Story 9.1: Workflow Runner + Assertions** ✅
   - Created workflow runner harness in `tests/e2e/fixtures/workflow_runner.py`
   - Implemented `WorkflowRunner` class with async execution support
   - Implemented `GateController` for deterministic gate outcomes
   - Added state snapshot capture functionality
   - Added artifact assertion utilities
   - Created pytest fixtures in `tests/e2e/conftest.py`
   - Created unit tests in `tests/unit/e2e/test_workflow_runner.py`

2. **Story 9.2: Tier-1 Preset Workflow E2E Coverage** ✅
   - Created E2E tests for 3 tier-1 preset workflows:
     - `test_full_sdlc_workflow.py` (5 tests)
     - `test_quality_workflow.py` (5 tests)
     - `test_quick_fix_workflow.py` (5 tests)
   - All tests use workflow runner harness
   - All tests run in mocked mode by default
   - Tests validate parsing, execution, state transitions, and artifacts
   - Created comprehensive README documentation

3. **Story 9.3: Workflow Failure & Resume E2E** ✅
   - Created E2E tests for workflow failure and resume in `test_workflow_failure_resume.py` (6 tests)
   - Tests validate state persistence on failure
   - Tests validate state loading and consistency
   - Tests validate artifact preservation
   - Tests validate resume from persisted state
   - Tests cover multiple failure scenarios

### Key Deliverables

- **Workflow Runner Harness**: Complete workflow execution utilities with async support
- **Gate Controller**: Deterministic gate outcome control for routing tests
- **E2E Tests**: 21 total tests covering 3 tier-1 workflows and failure/resume scenarios
- **Documentation**: Comprehensive README for workflow E2E tests
- **Unit Tests**: Full test coverage for workflow runner utilities

### Verification

- All tests are discoverable and collectible via pytest
- All tests use `e2e_workflow` marker
- Tests run in mocked mode by default (deterministic)
- Workflow runner integrates with E2E foundation from Epic 8
- State persistence and resume functionality validated

## Story Manager Handoff

“Please develop detailed user stories for Epic 9 (E2E Workflow Tests). Key considerations:
- Focus on a small, high-value subset of shipped workflows.
- Ensure mocked-by-default execution with explicit opt-in to real services.
- Add strong state/artifact assertions and debug capture on failure.
- Include a failure+resume scenario to validate persistence robustness.”

