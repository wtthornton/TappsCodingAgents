# Dependency Management Policy

**pyproject.toml** is the single source of truth for dependencies.

## Policy

1. **Runtime dependencies** – Declared in `[project].dependencies`
2. **Optional extras** – Use `[project.optional-dependencies]` for optional features
3. **requirements.txt** – Convenience artifact only; must match pyproject.toml (runtime + dev)
4. **No setup.py** – Removed; `pyproject.toml` is the sole source of package metadata

## Optional Extras

| Extra | Purpose |
|-------|---------|
| `dev` | Development tools (ruff, mypy, pytest, etc.) |
| `reporting` | Plotly for interactive charts (optional; report generator uses Jinja2 by default) |
| `dependency-analysis` | pipdeptree (may conflict with packaging constraint; see DEPENDENCY_CONFLICT_PIPDEPTREE.md) |

## Validation

Run `python scripts/validate_dependencies.py` to verify:

- setup.py is not present (removed in favor of pyproject.toml)
- requirements.txt matches pyproject.toml

## Related

- [DEPENDENCY_CONFLICT_PIPDEPTREE.md](DEPENDENCY_CONFLICT_PIPDEPTREE.md) – pipdeptree/packaging conflict
- [archive/completed-improvements/DEPENDENCY_CLEANUP_2026.md](archive/completed-improvements/DEPENDENCY_CLEANUP_2026.md) – 2026 dependency cleanup
