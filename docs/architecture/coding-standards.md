# Coding Standards (Lean BMAD Shard)

## Formatting & Style

- **Black** formatting is the default (line length 88).
- Prefer small, readable functions; refactor early when complexity grows.

## Linting

- **Ruff** is used with a pragmatic rule set (see `pyproject.toml`):
  - enabled: `E`, `F`, `I`, `UP`, `B`
  - line-length warnings (`E501`) are ignored (Black owns formatting)

## Typing

- **mypy** is configured for Python 3.13 (see `pyproject.toml`).
- Type coverage is incremental; keep public APIs typed where feasible.

## Testing

- Use **pytest** with markers (unit/integration/e2e).
- Prefer deterministic tests; avoid unnecessary sleeps/time-based flakiness.
- Prefer parallel execution where safe (`pytest -n auto`).

## Repo-Specific References

- Testing performance: `docs/TEST_PERFORMANCE_GUIDE.md`
- Architecture: `docs/ARCHITECTURE.md`


