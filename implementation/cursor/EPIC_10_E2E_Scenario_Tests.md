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
   - Define canonical “small” and “medium” project templates (language/tooling appropriate to this repo).
   - Provide deterministic initial state and expected outputs per scenario.

2. **Story 10.2: Implement 2–3 Tier-1 Scenarios**
   - Scenario A: “Implement a small feature end-to-end”
   - Scenario B: “Fix a bug with tests + review gate”
   - Scenario C: “Refactor + quality gate + docs update”

3. **Story 10.3: Reliability Controls for Long E2E Runs**
   - Timeouts per step and per scenario; capture partial progress on failure.
   - Retry policy for transient external failures (real LLM, Context7).
   - Cost guardrails: cap tokens, limit parallelism, skip on missing credentials.

## Compatibility Requirements

- [ ] Scenario tests do not run in default unit-only suites.
- [ ] Scenario tests can be skipped cleanly when credentials/services are not present.
- [ ] No breaking changes to workflow YAML schema or shipped presets.

## Risk Mitigation

- **Primary Risk**: Scenario tests become too slow/expensive and are skipped or ignored.
- **Mitigation**: Keep scenario count small; run on schedule; enforce time/cost caps; produce high-signal diagnostics.
- **Rollback Plan**: Reclassify scenario suite to nightly/pre-release only while retaining smoke/workflow suites for PR gating.

## Definition of Done

- [ ] 2–3 scenario tests exist and are stable enough for scheduled execution.
- [ ] Each scenario has explicit success criteria and outcome validation.
- [ ] Failures produce a well-defined bundle of debug artifacts (state, logs, outputs).

## Story Manager Handoff

“Please develop detailed user stories for Epic 10 (E2E Scenario Tests). Key considerations:
- Use small/medium project templates to keep runtime and flakiness manageable.
- Treat scenarios as release confidence signals (scheduled runs), not PR blockers by default.
- Include explicit outcome contracts (files/artifacts/gate states) and strong debug capture.”

