# Epic 10: E2E Scenario Tests (User Journeys)

## Epic Goal

Validate the system against a small set of **realistic user journeys** (feature implementation, bug fix, refactor) to provide high confidence that multi-agent orchestration, artifact handling, quality gates, and reporting work together end-to-end.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Workflows and agents can be invoked via Python API and CLI; quality gates/scoring exist; integration tests include some real LLM coverage.
- **Technology stack**: `pytest`, async execution, optional MAL providers; filesystem-based artifacts under `.tapps-agents/`; worktree isolation.
- **Integration points**:
  - Multi-agent orchestration + workflow executor
  - Reviewer scoring + gate evaluation
  - Tester agent running pytest / test generation paths
  - Artifact creation and retention under project root

### Enhancement Details

- **What’s being added/changed**:
  - Scenario definitions with reproducible inputs (small/medium template repos).
  - Scenario validation packs: expected file changes, expected artifacts, expected test outcomes, expected quality signals.
  - Flake controls: explicit timeouts, bounded retries for external calls, and deterministic fallbacks.
- **How it integrates**:
  - Scenarios reuse the workflow runner/harness established in Epic 9.
  - Scenarios are designed to run in **scheduled** CI (nightly/pre-release) and optionally locally with real services.
- **2025 standards / guardrails**:
  - **Scheduled by default**: scenario E2E are not PR blockers; they run nightly/pre-release with clear ownership and escalation policy for failures.
  - **Cost + time budgets**: per-scenario timeout caps; limit parallelism; enforce token/call budgets for real LLM usage.
  - **Flake management**: bounded retries for transient network/service failures only; record retry counts and reasons; fail fast on deterministic logic errors.
  - **Outcome contracts**: validate stable outcomes (artifacts, tests passing, gate states, report summaries) instead of free-form text.
  - **Observability**: always emit correlation IDs; capture state timeline + key logs + produced artifacts as a failure bundle.
  - **Security hygiene**: strict redaction in logs/artifacts; never persist API keys or model prompts containing secrets.
- **Success criteria**:
  - 2–3 scenarios run to completion and validate outcome contracts (artifacts + gates + reports).
  - Failures produce actionable traces (logs + state snapshots + produced artifacts).

## Stories

1. **Story 10.1: Scenario Templates (Small + Medium Projects)**
   - **Goal**: Define canonical "small" and "medium" project templates with scenario-specific initial state and expected outputs.
   - **Acceptance Criteria**:
     - Small template supports "feature" and "bug_fix" scenarios with deterministic initial state
     - Medium template supports "refactor" scenarios with deterministic initial state
     - Each scenario type has defined expected outputs (file changes, artifacts, test outcomes, quality signals)
     - Templates are deterministic and reproducible (fixed content, seeded randomness if needed)
     - Templates integrate with existing `scenario_templates.py` utilities
   - **Deliverables**:
     - Enhanced scenario template functions in `tests/e2e/fixtures/scenario_templates.py`
     - Expected outputs validation utilities
     - Documentation for each scenario template

2. **Story 10.2: Implement 2–3 Tier-1 Scenarios**
   - **Goal**: Create E2E tests for realistic user journeys that validate multi-agent orchestration end-to-end.
   - **Acceptance Criteria**:
     - **Scenario A (Feature Implementation)**: 
       - Uses small template with feature request
       - Executes workflow to implement feature end-to-end
       - Validates: feature code created, tests pass, quality gates pass, artifacts created
     - **Scenario B (Bug Fix)**:
       - Uses small template with bug report and failing test
       - Executes workflow to fix bug with tests + review gate
       - Validates: bug fixed, tests pass, review gate passes, artifacts created
     - **Scenario C (Refactor)**:
       - Uses medium template with refactor requirements
       - Executes workflow to refactor + quality gate + docs update
       - Validates: refactored code, tests pass, quality maintained/improved, docs updated
     - All scenarios use `e2e_scenario` marker
     - All scenarios validate outcome contracts (artifacts, gates, reports)
     - All scenarios produce failure bundles on failure
   - **Deliverables**:
     - `tests/e2e/scenarios/test_feature_scenario.py`
     - `tests/e2e/scenarios/test_bug_fix_scenario.py`
     - `tests/e2e/scenarios/test_refactor_scenario.py`
     - Scenario validation utilities
     - README documentation

3. **Story 10.3: Reliability Controls for Long E2E Runs**
   - **Goal**: Implement timeouts, retries, and cost guardrails to make scenario tests reliable and cost-effective.
   - **Acceptance Criteria**:
     - **Timeout Controls**:
       - Per-scenario timeout caps (configurable, default: 30 minutes)
       - Per-step timeout controls (step-level timeouts)
       - Per-workflow timeout controls (workflow-level timeouts)
       - Timeout violations produce clear error messages and captured state
     - **Partial Progress Capture**:
       - State snapshots captured at timeout points
       - Artifacts created before timeout are preserved
       - Step timeline captured up to timeout point
       - Failure bundles include partial progress information
     - **Retry Policy**:
       - Bounded retries for transient network failures (real LLM, Context7)
       - Bounded retries for transient service failures (API rate limits, temporary unavailability)
       - Retry configuration (max retries: 3, exponential backoff)
       - Retry counts and reasons recorded in logs
       - Fail fast on deterministic logic errors (no retries)
     - **Cost Guardrails**:
       - Token budget tracking for real LLM usage (configurable per scenario)
       - Call budget limits (configurable per scenario)
       - Parallelism limits (max 2 concurrent scenarios)
       - Clean skip when credentials/services are not present
       - Cost reporting in test output
   - **Deliverables**:
     - Reliability controls utilities in `tests/e2e/fixtures/reliability_controls.py`
     - Integration with workflow runner
     - Pytest fixtures for timeout/retry configuration
     - Unit tests for reliability controls

## Compatibility Requirements

- [x] Scenario tests do not run in default unit-only suites.
- [x] Scenario tests can be skipped cleanly when credentials/services are not present.
- [x] No breaking changes to workflow YAML schema or shipped presets.

## Risk Mitigation

- **Primary Risk**: Scenario tests become too slow/expensive and are skipped or ignored.
- **Mitigation**: Keep scenario count small; run on schedule; enforce time/cost caps; produce high-signal diagnostics.
- **Rollback Plan**: Reclassify scenario suite to nightly/pre-release only while retaining smoke/workflow suites for PR gating.

## Definition of Done

- [x] 2–3 scenario tests exist and are stable enough for scheduled execution.
- [x] Each scenario has explicit success criteria and outcome validation.
- [x] Failures produce a well-defined bundle of debug artifacts (state, logs, outputs).

## Status

**COMPLETE** - All stories (10.1, 10.2, 10.3) have been implemented and verified.

### Completed Stories

1. **Story 10.1: Scenario Templates (Small + Medium Projects)** ✅
   - Verified and enhanced scenario templates in `tests/e2e/fixtures/scenario_templates.py`
   - Small template supports "feature" and "bug_fix" scenarios
   - Medium template supports "refactor" scenarios
   - Each scenario type has defined expected outputs (file changes, artifacts, test outcomes, quality signals)
   - Templates are deterministic and reproducible

2. **Story 10.2: Implement 2–3 Tier-1 Scenarios** ✅
   - Created E2E tests for 3 tier-1 scenarios:
     - `test_feature_scenario.py` - Feature implementation scenario
     - `test_bug_fix_scenario.py` - Bug fix scenario
     - `test_refactor_scenario.py` - Refactoring scenario
   - All scenarios use `e2e_scenario` marker
   - All scenarios validate outcome contracts (artifacts, gates, reports)
   - All scenarios produce failure bundles on failure
   - Created scenario validation utilities in `tests/e2e/fixtures/scenario_validator.py`
   - Created comprehensive README documentation

3. **Story 10.3: Reliability Controls for Long E2E Runs** ✅
   - Implemented timeout controls (scenario, step, workflow levels) in `tests/e2e/fixtures/reliability_controls.py`
   - Implemented retry policy for transient failures (bounded retries, exponential backoff)
   - Implemented cost guardrails (token budgets, call limits, parallelism limits)
   - Implemented partial progress capture on failure
   - All controls are configurable via fixtures, environment variables, or test markers

### Key Deliverables

- **Scenario Templates**: Complete scenario template system with expected outputs
- **Scenario Tests**: 3 E2E scenario tests covering feature, bug fix, and refactor journeys
- **Scenario Validator**: Validation utilities for scenario outcomes
- **Reliability Controls**: Timeout, retry, and cost control utilities
- **Documentation**: Comprehensive README for scenario tests

### Verification

- All tests are discoverable and collectible via pytest
- All tests use `e2e_scenario` marker
- Tests run in mocked mode by default (deterministic)
- Tests support real LLM mode behind `requires_llm` marker
- Scenario validation utilities validate all outcome contracts
- Reliability controls provide timeout, retry, and cost management

## Story Manager Handoff

“Please develop detailed user stories for Epic 10 (E2E Scenario Tests). Key considerations:
- Use small/medium project templates to keep runtime and flakiness manageable.
- Treat scenarios as release confidence signals (scheduled runs), not PR blockers by default.
- Include explicit outcome contracts (files/artifacts/gate states) and strong debug capture.”

