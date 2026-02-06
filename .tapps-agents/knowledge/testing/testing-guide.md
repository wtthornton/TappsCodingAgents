# Testing Guide

## Overview

TappsCodingAgents uses pytest for unit and integration tests. 868+ tests across 438 test files. Coverage targets defined in pytest.ini.

## Test Suite

| Test Group | Count | Notes |
|------------|-------|-------|
| Core tests | 368+ | Stable, fast |
| Init autofill | 130+ | Stable |
| Cleanup agent | 86 | 75 unit + 11 integration |
| Other modules | 274+ | Various stability |

## Key Conventions

- Tests live in `tests/` mirroring package structure (`tests/unit/`, `tests/integration/`)
- Use `@pytest.fixture` for shared setup
- Use factory fixtures over large fixture files
- Run: `pytest`, `pytest --cov=tapps_agents`, or `tapps-agents tester test <file>`

## Quick Validation

```bash
# Fast smoke test
python -m pytest tests/ -x --timeout=60 -q

# With coverage
python -m pytest tests/ --cov=tapps_agents --cov-report=term-missing

# Specific module
python -m pytest tests/unit/core/ -x --timeout=60 -q
```

## Coverage

- Target ≥75% (pytest.ini); framework core aims for ≥80%
- Use `tapps-agents simple-mode *test <file>` for generated tests and coverage

## Known Pre-existing Failures

- `test_direct_execution_fallback.py::test_execute_command_with_worktree_path` — pre-existing
- Expert governance/setup_wizard tests — pre-existing failures
- Beads-dependent tests — fail when `bd` environment not configured (BeadsRequiredError)

## Best Practices

1. **Use `pytest.raises(match=r"...")`** for exception message validation
2. **Use factory fixtures** — create data factories for complex test objects
3. **Use `pytest-asyncio`** with `mode = "auto"` for async test discovery
4. **Use `pytest-mock`** for patching — prefer `mocker.patch` over `unittest.mock.patch`
5. **Set timeouts** — use `@pytest.mark.timeout(30)` for potentially slow tests
6. **Parametrize** — use `@pytest.mark.parametrize` for data-driven tests
7. **Isolate state** — reset global/module state in fixtures (see `_reset_state_for_testing()` pattern)
8. **Name tests descriptively** — `test_<function>_<scenario>_<expected>` pattern

## pytest Configuration (pyproject.toml)

```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
timeout = 120
markers = ["slow", "integration", "beads"]
```

## Related

- `docs/test-stack.md` — Testing strategy and infrastructure
- `tapps-agents simple-mode *test <file>` — AI-generated test generation
