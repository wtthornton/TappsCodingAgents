# Performance Guide (Lean BMAD Shard)

## What “Performance” Means Here

For this repository (a Python framework), performance is primarily:

- **Fast developer feedback loops** (tests, linting, tooling)
- **Reasonable runtime overhead** in CLI operations and analysis/report generation
- **No accidental regressions** from expensive I/O or unbounded loops

## Practical Guidance

- Prefer parallel test execution when safe (`pytest -n auto`).
- Avoid heavy filesystem I/O in tight loops (especially in tests).
- Add explicit timeouts for external calls (HTTP, subprocess).
- Avoid blocking work inside async functions; use async equivalents where available.

## References

- `CLAUDE.md` (BMAD review baseline)
- `docs/TEST_PERFORMANCE_GUIDE.md`


