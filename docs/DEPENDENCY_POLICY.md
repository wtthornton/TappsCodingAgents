# Dependency & Packaging Policy

## Single Source of Truth

**`pyproject.toml` is the authoritative source** for all package metadata and dependencies. All other dependency files (`setup.py`, `requirements.txt`) are either derived from `pyproject.toml` or serve as convenience artifacts only.

## Dependency Channels

### Runtime Dependencies (`dependencies` in `pyproject.toml`)

These are installed when users run:
```bash
pip install tapps-agents
```

**Runtime dependencies** include only what is required for the CLI and core functionality:
- Core framework libraries (pydantic, httpx, pyyaml, aiohttp, psutil)
- Code analysis tools used at runtime (radon, bandit, pylint, coverage)
- Reporting/rendering (jinja2, plotly)

**Runtime dependencies do NOT include:**
- Testing frameworks (pytest, pytest-*)
- Development tools (black, ruff, mypy)
- Build tools (setuptools, wheel - these are build-system requirements)

### Development Dependencies (`dev` extra)

These are installed when developers run:
```bash
pip install -e ".[dev]"
```

**Dev dependencies** include:
- Code formatting: `black`, `ruff`
- Type checking: `mypy`
- Testing: `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-mock`, `pytest-timeout`
- Security auditing: `pip-audit`
- Dependency analysis: `pipdeptree`

### Test Dependencies

Currently, test dependencies are included in the `dev` extra. If needed, a separate `test` extra can be added for CI-only dependencies.

## File Roles

### `pyproject.toml`
- **Authoritative source** for all dependencies and package metadata
- Defines `dependencies` (runtime) and `[project.optional-dependencies]` (extras)
- Must be updated when adding/removing dependencies

### `setup.py`
- **Minimal stub** that reads metadata from `pyproject.toml`
- Does NOT define dependencies directly
- Only provides setuptools configuration for package discovery

### `requirements.txt`
- **Convenience artifact** for developers who prefer `pip install -r requirements.txt`
- **Non-authoritative** - may be generated from `pyproject.toml` or kept in sync manually
- Should match `dependencies + dev` extras for development convenience
- CI workflows should prefer `pip install -e ".[dev]"` over `requirements.txt`

### `MANIFEST.in`
- Defines non-Python files to include in distributions
- Does not affect dependencies

## Install Commands

### For End Users (Runtime)
```bash
pip install tapps-agents
```

### For Developers (Editable + Dev Tools)
```bash
pip install -e ".[dev]"
```

### For CI/Testing
```bash
pip install -e ".[dev]"
```

All CI workflows should use this command for consistency.

## Dependency Drift Prevention

### Drift Check

A dependency drift check runs in CI to ensure:
1. `setup.py` does not define dependencies that differ from `pyproject.toml`
2. `requirements.txt` (if present) matches the expected dependency set

The check is implemented in `scripts/validate_dependencies.py` and runs automatically in CI.

### Adding Dependencies

**Always update `pyproject.toml` first:**
1. Add runtime dependencies to `[project.dependencies]`
2. Add dev/test dependencies to `[project.optional-dependencies.dev]`
3. Run `scripts/validate_dependencies.py` to verify no drift
4. Update `requirements.txt` if it's maintained (optional, for convenience)

### Removing Dependencies

1. Remove from `pyproject.toml`
2. Run drift check
3. Update `requirements.txt` if maintained

## Policy Enforcement

- **CI**: The drift check runs in `.github/workflows/ci.yml` and fails if sources disagree
- **Documentation**: This policy is referenced in `CONTRIBUTING.md` and `docs/DEVELOPER_GUIDE.md`
- **Code Review**: PRs that modify dependencies must update `pyproject.toml` as the primary source

## Migration Notes

If you're migrating from the old system:
- Previously, `requirements.txt` was the primary source
- Now, `pyproject.toml` is authoritative
- `setup.py` no longer reads from `requirements.txt` for dependencies

