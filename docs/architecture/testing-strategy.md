# Testing Strategy (Lean BMAD Shard)

## Test Framework

- **pytest** is the primary test runner.
- Async tests use **pytest-asyncio**.

## Test Layers (high level)

- **Unit**: fast, isolated tests (default focus)
- **Integration**: tests that touch real integrations/services
- **E2E**: end-to-end workflows and CLI journeys

## Execution Guidance

- Prefer parallel runs when possible:
  - `pytest tests/ -m unit -n auto`
- Keep unit tests deterministic and fast; isolate external services behind mocks unless an integration test explicitly needs them.

## References

- `docs/TEST_PERFORMANCE_GUIDE.md`
- `tests/README.md`


