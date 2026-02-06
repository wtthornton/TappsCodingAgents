# Code Quality

## Standards

- **Reviewer:** 7-category scoring (complexity, security, maintainability, test_coverage, performance, structure, devex). Quality gates: overall ≥70 (≥75 for framework).
- **Linting:** Ruff (E, F, I, UP, B rules). Recommended additions: SIM, RUF, PTH, ASYNC, PERF.
- **Type checking:** mypy with `ignore_missing_imports=true`. Recommended: enable `check_untyped_defs`.
- **Security:** Bandit; use `@reviewer *security-scan` and `@ops *audit-security`.

## Workflows

- Use `@simple-mode *build` or `*full` for features so review and test steps run.
- Use `@simple-mode *review <file>` for pre-commit quality checks.

## Recommended Ruff Rule Additions

| Rule Set | What It Catches |
|----------|----------------|
| `SIM` | Simplifiable logic (unnecessary `if/else`, ternary opportunities) |
| `RUF` | Ruff-specific rules (unused `noqa`, mutable defaults) |
| `PTH` | `os.path` → `pathlib.Path` modernization |
| `ASYNC` | Asyncio anti-patterns (blocking in async, missing await) |
| `PERF` | Performance issues (unnecessary list copies, dict comprehensions) |

## Best Practices

1. **Pydantic v2**: Use `model_config = ConfigDict(...)` not raw dict. Use `Annotated` types for reusable validators.
2. **Error handling**: Standardize on one pattern (prefer `Result[T, E]` or custom exception hierarchy).
3. **Path validation**: Centralize in a single `path_security` module; validate at system boundaries.
4. **Secrets**: Use `pydantic.SecretStr` for API keys and tokens; never log secret values.
5. **Subprocess**: Centralize all `subprocess.run` calls through a single helper with timeout, encoding, and security defaults.
6. **Type annotations**: Enable `disallow_untyped_defs` in mypy for new code; add stubs for third-party libs.
7. **Pre-commit hooks**: Add `.pre-commit-config.yaml` with ruff, mypy, bandit, and secrets detection.

## Testing Standards

- Coverage: ≥75% (≥80% for core modules)
- Use `pytest.raises(match=r"...")` for exception message validation
- Use factory fixtures over large fixture files
- Use `pytest-asyncio` with `mode = "auto"` for async test discovery
