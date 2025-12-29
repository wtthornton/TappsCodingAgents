# Release Guide - Optimized Process

This guide documents the optimized GitHub release process for TappsCodingAgents.

## Overview

The release process has been optimized with:
- ✅ **Automated GitHub Actions workflow** - Cross-platform, no manual intervention
- ✅ **Pre-release validation** - Full test suite, linting, type checking, security scans
- ✅ **Package verification** - Automated package content validation
- ✅ **CHANGELOG.md integration** - Automatic release notes extraction
- ✅ **Optional PyPI publishing** - One-step distribution

## Release Methods

### Method 1: Automated Release (Recommended)

**When to use:** Standard releases after code is merged to main

**Steps:**

1. **Prepare Release:**
   ```bash
   # Update version in code
   .\scripts\update_version.ps1 -Version 3.0.2
   
   # Update CHANGELOG.md with release notes
   # Add section: ## [3.0.2] - YYYY-MM-DD
   ```

2. **Commit and Push:**
   ```bash
   git add pyproject.toml tapps_agents/__init__.py CHANGELOG.md
   git commit -m "Bump version to 3.0.2"
   git push origin main
   ```

3. **Create and Push Tag:**
   ```bash
   git tag v3.0.2
   git push origin v3.0.2
   ```

4. **GitHub Actions Automatically:**
   - ✅ Validates version consistency
   - ✅ Runs full test suite
   - ✅ Runs linting and type checking
   - ✅ Performs security scan
   - ✅ Builds packages (sdist + wheel)
   - ✅ Verifies package contents
   - ✅ Extracts release notes from CHANGELOG.md
   - ✅ Creates GitHub release with packages attached
   - ✅ Optionally publishes to PyPI (if not pre-release)

**View Release:**
- GitHub: https://github.com/wtthornton/TappsCodingAgents/releases/tag/v3.0.2
- PyPI: https://pypi.org/project/tapps-agents/ (if published)

### Method 2: Manual Release Script (Windows)

**When to use:** Quick releases, testing, or when GitHub Actions is unavailable

**Steps:**

```powershell
# Update version and build release
.\scripts\create_github_release.ps1 -Version 3.0.2
```

**What it does:**
- Updates version in `pyproject.toml` and `__init__.py`
- Cleans build artifacts
- Builds packages
- Verifies packages (optional)
- Creates GitHub release

**Options:**
```powershell
# Draft release (for review)
.\scripts\create_github_release.ps1 -Version 3.0.2 -Draft

# Prerelease (alpha, beta, rc)
.\scripts\create_github_release.ps1 -Version 3.0.2 -Prerelease

# Skip version update (if already updated)
.\scripts\create_github_release.ps1 -Version 3.0.2 -SkipVersionUpdate

# Skip build (if already built)
.\scripts\create_github_release.ps1 -Version 3.0.2 -SkipBuild
```

### Method 3: Manual Workflow Dispatch

**When to use:** Trigger release workflow manually from GitHub UI

**Steps:**

1. Go to Actions → Release workflow
2. Click "Run workflow"
3. Enter version (e.g., `3.0.2`)
4. Optionally check "Skip PyPI upload"
5. Click "Run workflow"

**Note:** Version must already be updated in code and tag must exist or be created.

## Release Checklist

### Pre-Release

- [ ] All tests pass locally
- [ ] Version updated in `pyproject.toml` and `tapps_agents/__init__.py`
- [ ] CHANGELOG.md updated with release notes
- [ ] All changes committed and pushed to main
- [ ] CI/CD checks pass on main branch
- [ ] Run release readiness validation: `.\scripts\validate_release_readiness.ps1 -Version 3.0.2`

### Release

- [ ] Create and push version tag
- [ ] Monitor GitHub Actions release workflow
- [ ] Verify release created successfully
- [ ] Verify packages attached correctly
- [ ] Verify release notes extracted correctly

### Post-Release

- [ ] Verify GitHub release page
- [ ] Test installation: `pip install tapps-agents==3.0.2`
- [ ] Verify PyPI publication (if applicable)
- [ ] Announce release (if applicable)

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., `3.0.2`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

**Pre-release versions:**
- Alpha: `3.0.2-alpha.1`
- Beta: `3.0.2-beta.1`
- RC: `3.0.2-rc.1`

## CHANGELOG.md Format

Release notes are automatically extracted from CHANGELOG.md. Use this format:

```markdown
## [3.0.2] - 2026-01-31

### Added
- New feature description

### Changed
- Change description

### Fixed
- Bug fix description

### Removed
- Removed feature description
```

**Important:** The version in brackets must match the release version exactly.

## Package Verification

The release process automatically verifies packages contain:
- ✅ Required files: `tapps_agents/`, `pyproject.toml`, `setup.py`
- ✅ Resources: `tapps_agents/resources/`
- ❌ Excluded files: `tests/`, `docs/`, `scripts/`, etc.

## PyPI Publishing

### Automatic Publishing

PyPI publishing is **automatic** for:
- ✅ Version tags (e.g., `v3.0.2`)
- ✅ Not pre-releases (no `alpha`, `beta`, `rc` in version)
- ✅ Push events (not workflow_dispatch with skip_pypi)

### Manual Publishing

If you need to publish manually:

```powershell
# Upload to TestPyPI first (recommended)
.\scripts\upload_to_pypi.ps1 -Repository testpypi -Token $env:TWINE_PASSWORD

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ tapps-agents

# Upload to PyPI
.\scripts\upload_to_pypi.ps1 -Repository pypi -Token $env:TWINE_PASSWORD
```

### PyPI Token Setup

1. Create API token: https://pypi.org/manage/account/token/
2. Set environment variable:
   ```powershell
   $env:TWINE_PASSWORD = "pypi-your-token-here"
   ```
3. Or use GitHub Secrets for CI/CD: `PYPI_API_TOKEN`

## Troubleshooting

### Release Workflow Fails

**Version mismatch:**
- Ensure version in `pyproject.toml` and `__init__.py` match tag
- Run: `.\scripts\update_version.ps1 -Version 3.0.2`

**Tests fail:**
- Fix failing tests before releasing
- Run tests locally: `pytest tests/`

**Package verification fails:**
- Check `MANIFEST.in` for correct inclusion/exclusion rules
- Review package contents: `python -m build && tar -tzf dist/*.tar.gz`

### Release Already Exists

If release tag already exists:
- Delete release on GitHub (if draft)
- Delete tag: `git tag -d v3.0.2 && git push origin :refs/tags/v3.0.2`
- Recreate release

### PyPI Upload Fails

**Token issues:**
- Verify token is valid and has upload permissions
- Check token format: should start with `pypi-`

**Package already exists:**
- Use `--skip-existing` flag (automatic in workflow)
- Or increment version number

## Best Practices

1. **Always test locally first:**
   ```bash
   python -m build
   pip install dist/tapps_agents-3.0.2-py3-none-any.whl
   ```

2. **Use TestPyPI for validation:**
   - Test package installation before production PyPI

3. **Keep CHANGELOG.md up to date:**
   - Update as you develop features
   - Makes release notes generation easier

4. **Tag from main branch:**
   - Ensures released code matches main branch

5. **Monitor release workflow:**
   - Check GitHub Actions for any failures
   - Verify release artifacts

## Related Documentation

- [Release Process Analysis](RELEASE_PROCESS_ANALYSIS.md) - Detailed analysis of release components
- [CHANGELOG.md](../CHANGELOG.md) - Release history
- [Version Update Script](../scripts/update_version.ps1) - Version management
- [Release Script](../scripts/create_github_release.ps1) - Manual release script

