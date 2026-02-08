# E2E Scenario Tests

This directory is reserved for future **user-journey** scenario tests (feature implementation, bug fix, refactoring from start to finish).

## Current status

Scenario coverage is provided by:

- **Workflow preset E2E** – Short runs of each preset (fix, full-sdlc, quality, rapid-dev) with mocks in `tests/e2e/workflows/test_preset_workflows.py`.
- **Fix workflow E2E** – Full fix workflow tests in `tests/e2e/workflows/test_quick_fix_workflow.py`.

Dedicated scenario test files (e.g. multi-step user journeys with specific workflows) were removed as part of the [E2E Testing Plan](../../../docs/planning/E2E_TESTING_PLAN.md) and may be re-added later with a deterministic, mock-based design.

## Running tests

```bash
# Preset workflow e2e (includes short runs used as scenario coverage)
pytest tests/e2e/workflows/ -m e2e_workflow -v
```

## References

- [E2E Testing Plan](../../../docs/planning/E2E_TESTING_PLAN.md)
- [E2E Test Suite README](../README.md)
- [Workflow E2E README](../workflows/README.md)
