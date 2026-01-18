# Dependency Version Review Report

**Generated:** 2026-01-20  
**Status:** 12 packages need upgrading

## Executive Summary

A comprehensive review of all dependencies in `pyproject.toml` found:

- **Total dependencies checked:** 30
- **Up to date:** 18 (60%)
- **Upgrade needed:** 12 (40%)
- **Errors:** 0

## Packages Needing Upgrade

### ⚠️ HIGH PRIORITY (Major Version Upgrades)

These packages have major version updates available and require testing for compatibility:

#### 1. **aiofiles** (Runtime)
- **Current:** `>=24.1.0`
- **Latest:** `25.1.0`
- **Priority:** HIGH (major version upgrade)
- **Category:** Runtime dependency
- **Recommendation:** Upgrade to `>=25.1.0`
- **Action:** Review release notes for breaking changes, test async file operations

#### 2. **black** (Dev)
- **Current:** `>=25.12.0`
- **Latest:** `26.1.0`
- **Priority:** HIGH (major version upgrade)
- **Category:** Dev dependency (code formatting)
- **Recommendation:** Upgrade to `>=26.1.0`
- **Action:** Review black 26.x release notes, run formatting on codebase to verify compatibility

#### 3. **packaging** (Runtime) ⚠️ **CONSTRAINED**
- **Current:** `>=23.2,<25`
- **Latest:** `25.0`
- **Priority:** HIGH (major version available, but **CONSTRAINED**)
- **Category:** Runtime dependency
- **Recommendation:** **DO NOT UPGRADE** - Constrained for `langchain-core` compatibility
- **Reason:** `langchain-core 0.2.43` requires `packaging>=23.2,<26`. Upgrading to `>=25` would break compatibility.
- **Action:** Monitor `langchain-core` updates for `packaging>=25` support, or evaluate removing `langchain-core` dependency if not needed

### 📦 MEDIUM/LOW PRIORITY (Patch/Minor Updates)

These packages have patch or minor version updates available:

#### 4. **pydantic** (Runtime)
- **Current:** `>=2.12.0`
- **Latest:** `2.12.5`
- **Priority:** LOW (patch version)
- **Category:** Runtime dependency (core framework)
- **Recommendation:** Upgrade to `>=2.12.5`
- **Action:** Safe patch upgrade, includes bug fixes and security patches

#### 5. **httpx** (Runtime)
- **Current:** `>=0.28.0`
- **Latest:** `0.28.1`
- **Priority:** LOW (patch version)
- **Category:** Runtime dependency
- **Recommendation:** Upgrade to `>=0.28.1`
- **Action:** Safe patch upgrade

#### 6. **aiohttp** (Runtime)
- **Current:** `>=3.13.2`
- **Latest:** `3.13.3`
- **Priority:** LOW (patch version)
- **Category:** Runtime dependency
- **Recommendation:** Upgrade to `>=3.13.3`
- **Action:** Safe patch upgrade

#### 7. **psutil** (Runtime)
- **Current:** `>=7.1.0`
- **Latest:** `7.2.1`
- **Priority:** LOW (patch version)
- **Category:** Runtime dependency
- **Recommendation:** Upgrade to `>=7.2.1`
- **Action:** Safe patch upgrade

#### 8. **coverage** (Runtime)
- **Current:** `>=7.13.0`
- **Latest:** `7.13.1`
- **Priority:** LOW (patch version)
- **Category:** Runtime dependency (code analysis)
- **Recommendation:** Upgrade to `>=7.13.1`
- **Action:** Safe patch upgrade

#### 9. **plotly** (Runtime)
- **Current:** `>=6.5.0`
- **Latest:** `6.5.2`
- **Priority:** LOW (patch version)
- **Category:** Runtime dependency (reporting)
- **Recommendation:** Upgrade to `>=6.5.2`
- **Action:** Safe patch upgrade

#### 10. **rich** (Runtime)
- **Current:** `>=14.1.0`
- **Latest:** `14.2.0`
- **Priority:** LOW (patch version)
- **Category:** Runtime dependency (CLI UX)
- **Recommendation:** Upgrade to `>=14.2.0`
- **Action:** Safe patch upgrade

#### 11. **ruff** (Dev)
- **Current:** `>=0.14.10,<1.0`
- **Latest:** `0.14.13`
- **Priority:** LOW (patch version)
- **Category:** Dev dependency (code formatting/linting)
- **Recommendation:** Upgrade to `>=0.14.13,<1.0`
- **Action:** Safe patch upgrade within 0.x series

#### 12. **types-PyYAML** (Dev)
- **Current:** `>=6.0.12`
- **Latest:** `6.0.12.20250915`
- **Priority:** LOW (patch version)
- **Category:** Dev dependency (type stubs)
- **Recommendation:** Upgrade to `>=6.0.12.20250915`
- **Action:** Safe patch upgrade (type stub update)

## Packages Up to Date

The following 18 packages are already at the latest stable versions:

- **Runtime:** `pyyaml`, `radon`, `bandit`, `jinja2`
- **Dev:** `mypy`, `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-mock`, `pytest-timeout`, `pytest-xdist`, `pytest-sugar`, `pytest-html`, `pytest-rich`, `pylint`, `pip-audit`, `pip-tools`
- **Optional:** `pipdeptree`

## Recommended Upgrade Path

### Phase 1: Low-Risk Patch Updates (Immediate)

Upgrade these patch versions immediately - they include bug fixes and security patches:

```toml
# pyproject.toml updates
dependencies = [
    # ... existing ...
    "pydantic>=2.12.5",
    "httpx>=0.28.1",
    "aiohttp>=3.13.3",
    "psutil>=7.2.1",
    "coverage>=7.13.1",
    "plotly>=6.5.2",
    "rich>=14.2.0",
    # ... rest ...
]

[project.optional-dependencies]
dev = [
    # ... existing ...
    "ruff>=0.14.13,<1.0",
    "types-PyYAML>=6.0.12.20250915",
    # ... rest ...
]
```

### Phase 2: Major Version Upgrades (After Testing)

Test these major version upgrades in a development branch:

1. **aiofiles** (`24.1.0` → `25.1.0`)
   - Review [aiofiles changelog](https://github.com/Tinche/aiofiles/releases)
   - Test async file operations
   - Update to: `"aiofiles>=25.1.0"`

2. **black** (`25.12.0` → `26.1.0`)
   - Review [black 26.x release notes](https://black.readthedocs.io/en/stable/change_log.html)
   - Run `black .` to verify formatting compatibility
   - Update to: `"black>=26.1.0"`

### Phase 3: Constrained Package (Monitor)

**packaging** - Keep current constraint until `langchain-core` supports `packaging>=25`:

```toml
# Keep as-is (DO NOT UPGRADE)
"packaging>=23.2,<25",  # Constrained for langchain-core compatibility
```

**Monitor:**
- Check if newer `langchain-core` versions support `packaging>=25`
- Evaluate if `langchain-core` dependency is still needed
- Consider alternative if `langchain-core` compatibility becomes a blocker

## Implementation Steps

1. **Create a feature branch:**
   ```bash
   git checkout -b upgrade-dependencies-2026-01-20
   ```

2. **Apply Phase 1 updates** (patch versions)

3. **Run tests:**
   ```bash
   python -m pytest tests/ -v
   ```

4. **Run linting:**
   ```bash
   ruff check .
   black --check .
   mypy tapps_agents/
   ```

5. **Test installation:**
   ```bash
   pip install -e ".[dev]"
   ```

6. **If Phase 1 passes, proceed with Phase 2** (major versions)

7. **Create PR with detailed testing notes**

## Testing Checklist

For major version upgrades (aiofiles, black):

- [ ] Review release notes/changelog
- [ ] Run full test suite
- [ ] Verify formatting (for black)
- [ ] Check async file operations (for aiofiles)
- [ ] Run linting tools
- [ ] Test CLI commands
- [ ] Verify documentation generation
- [ ] Check CI pipeline

## Additional Notes

### GitHub Actions Versions

Also check GitHub Actions versions in `.github/workflows/ci.yml`:

- `actions/checkout@v4` - Check for `v5` availability
- `actions/setup-python@v5` - Check for updates
- `actions/upload-artifact@v4` - Check for updates
- `codecov/codecov-action@v4` - Check for updates

### Python Version

The project requires **Python >=3.13**. Ensure all dependencies support Python 3.13.

## Automated Checking

Use the provided script to check for updates in the future:

```bash
python scripts/check_dependency_versions.py
```

This script:
- Reads dependencies from `pyproject.toml`
- Checks latest versions on PyPI
- Provides upgrade recommendations with priorities
- Identifies constrained packages that cannot be upgraded

---

**Generated by:** `scripts/check_dependency_versions.py`  
**Next Review:** Recommended quarterly or after major dependency updates
