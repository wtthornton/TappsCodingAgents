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
- Lock file generation: `pip-tools`

**Note:** `pipdeptree` has been moved to the `[dependency-analysis]` extra due to a dependency conflict:
- `pipdeptree>=2.30.0` requires `packaging>=25`
- TappsCodingAgents constrains `packaging` to `<25,>=23.2` to avoid conflicts with `langchain-core`
- Install separately if needed: `pip install -e ".[dependency-analysis]"` (may cause packaging conflicts)

### Dependency Analysis Extra (`dependency-analysis`)

Optional extra for dependency tree visualization tools:

```bash
pip install -e ".[dependency-analysis]"
```

**Warning:** This extra requires `packaging>=25`, which conflicts with TappsCodingAgents' `packaging<25` constraint. Installing this extra may cause dependency conflicts with `langchain-core` or other packages that require `packaging<25`.

**Includes:**
- `pipdeptree>=2.30.0` - Dependency tree visualization

**Impact:**
- The `DependencyAnalyzer` in the ops agent gracefully handles missing `pipdeptree`
- Dependency analysis works without it, but tree visualization will be unavailable

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

### Lock Files (`requirements-lock.txt`, `requirements-dev-lock.txt`)
- **Reproducible builds** - Pinned exact versions of all dependencies and transitive dependencies
- **Generated from `pyproject.toml`** using `pip-tools` (pip-compile)
- **Should be committed** to version control for reproducibility
- Use for production deployments and CI/CD where exact versions are critical
- Generated with: `python scripts/generate_lock_files.py`
- Install from lock file: `pip install -r requirements-lock.txt` (runtime) or `pip install -r requirements-dev-lock.txt` (dev)

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

**Optional:** If you need dependency tree visualization (may cause packaging conflicts):
```bash
pip install -e ".[dev,dependency-analysis]"
```
**Warning:** The `dependency-analysis` extra requires `packaging>=25`, which conflicts with TappsCodingAgents' `packaging<25` constraint. See [Dependency Analysis Extra](#dependency-analysis-extra-dependency-analysis) for details.

### For CI/Testing
```bash
pip install -e ".[dev]"
```

All CI workflows should use this command for consistency.

### For Reproducible Builds (Production/CI)
```bash
# Install from lock file for exact version reproducibility
pip install -r requirements-dev-lock.txt
```

Lock files ensure all environments (dev, CI, production) use identical dependency versions.

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
5. Regenerate lock files: `python scripts/generate_lock_files.py` (if using lock files)

### Removing Dependencies

1. Remove from `pyproject.toml`
2. Run drift check
3. Update `requirements.txt` if maintained
4. Regenerate lock files: `python scripts/generate_lock_files.py` (if using lock files)

### Handling Transitive Dependency Conflicts

Sometimes transitive dependencies (dependencies of dependencies) can conflict with each other. For example:
- Package A requires `packaging>=25.0`
- Package B (transitive) requires `packaging<25,>=23.2`

**Solution:** Add explicit version constraints to `pyproject.toml` to resolve conflicts:

```toml
dependencies = [
    # ... other dependencies ...
    # Constrain packaging to avoid conflicts with transitive dependencies
    "packaging>=23.2,<25",
]
```

**When to add constraints:**
- When pip reports dependency conflicts during installation
- When transitive dependencies have incompatible version requirements
- When you need to ensure compatibility with specific ecosystem packages (e.g., langchain-core)

**Best practices:**
- Use the most restrictive constraint that satisfies all dependencies
- Document why the constraint exists (add a comment)
- Monitor for updates to conflicting packages that may allow constraint relaxation

## Policy Enforcement

- **CI**: The drift check runs in `.github/workflows/ci.yml` and fails if sources disagree
- **Documentation**: This policy is referenced in `CONTRIBUTING.md` and `docs/DEVELOPER_GUIDE.md`
- **Code Review**: PRs that modify dependencies must update `pyproject.toml` as the primary source

## Migration Notes

If you're migrating from the old system:
- Previously, `requirements.txt` was the primary source
- Now, `pyproject.toml` is authoritative
- `setup.py` no longer reads from `requirements.txt` for dependencies

