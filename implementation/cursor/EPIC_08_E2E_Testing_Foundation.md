# Epic 8: E2E Testing Foundation (Hybrid Strategy Enablement)

## Epic Goal

Establish a **hybrid E2E testing foundation** (smoke → workflows → scenarios → CLI) with consistent markers, fixtures, project templates, and deterministic harness utilities so E2E tests are reliable, affordable to run, and easy to debug.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Strong unit suite; existing integration tests; some real-service E2E-like tests already exist under `tests/integration/` (e.g. `test_e2e_workflow_real.py`).
- **Technology stack**: `pytest`, `pytest-asyncio`, `pytest-timeout`; workflows defined in YAML under `workflows/`; multi-agent orchestration; optional real dependencies (LLM providers, Context7).
- **Integration points**:
  - `tapps_agents/workflow/*` (parser/executor/state/logging)
  - `tapps_agents/cli.py` (CLI entry point)
  - Existing test markers in `pytest.ini` (`unit`, `integration`, `e2e`, `requires_llm`, `requires_context7`)

### Enhancement Details

- **What’s being added/changed**:
  - A dedicated `tests/e2e/` suite structure aligned to the recommended hybrid model.
  - A reusable E2E harness: project templates, isolation helpers, artifact/state assertions, and cleanup rules.
  - A marker taxonomy that cleanly separates **smoke vs workflow vs scenario vs CLI** and **mocked vs real services**.
- **How it integrates**:
  - Builds on existing `pytest` markers and the workflow/CLI entry points.
  - Establishes conventions used by subsequent E2E epics (workflow/scenario/CLI/CI).
- **2025 standards / guardrails**:
  - **Test pyramid**: PR/CI defaults stay fast (unit-only baseline); E2E smoke is opt-in but designed to be cheap enough for PR gating; workflow/scenario suites are scheduled.
  - **Determinism first**: smoke E2E must be deterministic (no network calls, no real LLM/Context7); use fixed fixtures, seeded randomness, stable clocks where needed.
  - **Strict contracts**: validate stable “contracts” (exit codes, JSON shape, required artifacts, state transitions), not brittle free-form text.
  - **Reliability**: explicit timeouts per test/step; bounded retries only for clearly transient failures; capture partial progress on failure.
  - **Observability**: structured logs + correlation IDs for each E2E run; include state snapshots and step timeline in failure artifacts.
  - **Security hygiene**: never print/store secrets; ensure logs/artifacts are redacted; failure bundles must be safe to upload in CI.
  - **Cross-platform**: Windows-friendly path handling and process execution conventions (no bash-isms).
- **Success criteria**:
  - E2E suite can be invoked via targeted markers without running real external dependencies by default.
  - Deterministic, repeatable test environments with clear failure artifacts and logs.

## Stories

1. **Story 8.1: E2E Suite Layout + Harness Conventions**
   - Define `tests/e2e/` directory layout (smoke/workflows/scenarios/cli/fixtures).
   - Define project template strategy (minimal/small/medium) and deterministic setup/teardown.
   - Define artifact/state/log capture conventions for failures.

2. **Story 8.2: Marker & Execution Matrix**
   - Add marker taxonomy for `e2e_smoke`, `e2e_workflow`, `e2e_scenario`, `e2e_cli`, `e2e_slow`.
   - Define execution matrix: PR/CI default (smoke only), main branch (workflow), nightly (scenario + real).
   - Document how to run each slice locally (with and without real services).

3. **Story 8.3: Smoke E2E Tests (Mocked / Deterministic)**
   - Create smoke tests that validate “vertical slices” without real LLM/Context7:
     - Workflow YAML parse + executor start/advance + persistence.
     - Agent activation lifecycle (activate/run/close) using mocks.
     - Worktree/state cleanup invariants.

## Compatibility Requirements

- [x] Default `pytest` runs remain fast (unit-only by default via `pytest.ini`).
- [x] E2E tests are opt-in via markers; no new required external services for baseline runs.
- [x] New markers don\'t break strict marker configuration.

## Risk Mitigation

- **Primary Risk**: E2E tests become flaky due to non-deterministic external dependencies.
- **Mitigation**: Separate mocked vs real; smoke tests are fully deterministic; real tests are isolated + retried + scheduled.
- **Rollback Plan**: Keep E2E suite additive; failing E2E tests can be removed from default CI gating while retained for scheduled runs.

## Definition of Done

- [x] `tests/e2e/` structure and conventions are documented and adopted.
- [x] Marker taxonomy exists and supports selective test execution.
- [x] Smoke E2E suite runs reliably on a clean machine with no external services.
- [x] Failure artifacts/logs are produced and easy to inspect.

## Status

**COMPLETE** - All stories (8.1, 8.2, 8.3) have been implemented and verified.

### Completed Stories

1. **Story 8.1: E2E Suite Layout + Harness Conventions** ✅
   - Created `tests/e2e/` directory structure with subdirectories (smoke/workflows/scenarios/cli/fixtures)
   - Implemented project template strategy (minimal/small/medium) in `tests/e2e/fixtures/project_templates.py`
   - Implemented E2E harness utilities in `tests/e2e/fixtures/e2e_harness.py` (correlation IDs, artifact capture, assertions, cleanup)
   - Created shared E2E fixtures in `tests/e2e/conftest.py`
   - Added unit tests for harness utilities in `tests/unit/e2e/test_e2e_harness.py`
   - Created comprehensive documentation in `tests/e2e/README.md`

2. **Story 8.2: Marker & Execution Matrix** ✅
   - Added all E2E markers to `pytest.ini` (e2e_smoke, e2e_workflow, e2e_scenario, e2e_cli, e2e_slow, template_type)
   - Created marker taxonomy documentation in `tests/e2e/MARKER_TAXONOMY.md`
   - Created CI configuration examples in `tests/e2e/CI_EXAMPLES.md`
   - Verified default pytest behavior remains unchanged (unit-only)
   - All markers registered and compatible with `--strict-markers`

3. **Story 8.3: Smoke E2E Tests (Mocked / Deterministic)** ✅
   - Created 5 smoke test files in `tests/e2e/smoke/`:
     - `test_workflow_parsing.py` (4 tests)
     - `test_workflow_executor.py` (6 tests)
     - `test_workflow_persistence.py` (5 tests)
     - `test_agent_lifecycle.py` (5 tests)
     - `test_worktree_cleanup.py` (7 tests)
   - All tests are deterministic (no network calls, mocked services)
   - All tests use `e2e_smoke` marker and E2E harness utilities
   - Created smoke test documentation in `tests/e2e/smoke/README.md`
   - Total of 27 smoke tests covering core vertical slices

### Key Deliverables

- **Directory Structure**: Complete `tests/e2e/` hierarchy with all subdirectories
- **Harness Utilities**: Full-featured E2E harness with project templates, artifact capture, correlation IDs, and secret redaction
- **Marker System**: Complete marker taxonomy integrated into `pytest.ini`
- **Smoke Tests**: 27 deterministic smoke tests covering workflow parsing, execution, persistence, agent lifecycle, and worktree cleanup
- **Documentation**: Comprehensive READMEs, marker taxonomy, and CI examples
- **Unit Tests**: Full test coverage for harness utilities

### Verification

- All tests are discoverable and collectible via pytest
- All markers are registered and work with `--strict-markers`
- Default pytest execution remains unit-only
- Smoke tests run without external dependencies
- All files follow Windows-compatible path handling

## Story Manager Handoff

“Please develop detailed user stories for Epic 8 (E2E Testing Foundation). Key considerations:
- Keep E2E tests deterministic and opt-in by markers.
- Provide reusable fixtures and helpers (project templates, workflow runner, artifact assertions).
- Ensure compatibility with strict markers and current `pytest.ini` defaults.
- Produce clear debug output and artifacts on failure.”

