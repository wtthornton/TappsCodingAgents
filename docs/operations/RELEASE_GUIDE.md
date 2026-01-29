# Release Guide - Optimized Process

> **📘 CANONICAL DOCUMENTATION** - This is the authoritative guide for release and deployment processes.  
> **Quick Reference:** See [RELEASE_QUICK_REFERENCE.md](RELEASE_QUICK_REFERENCE.md)  
> **Critical Warning:** See [RELEASE_VERSION_TAG_WARNING.md](RELEASE_VERSION_TAG_WARNING.md)

This guide documents the optimized GitHub release process for TappsCodingAgents.

## ⚠️ CRITICAL: Version Bump Must Be Committed Before Tagging

**IMPORTANT:** The release tag **MUST** point to a commit that has the version bump already committed. If you create a tag before committing the version changes, the tag will point to the wrong commit, causing version mismatches for users upgrading.

**Correct Order:**
1. Update version files (via script or manually)
2. **Commit version bump changes** ⚠️ CRITICAL
3. Push to main
4. Create tag (which points to the version bump commit)
5. Create release

**Verification:**
After creating a tag, always verify it points to the correct commit:
```powershell
git show v3.0.2:tapps_agents/__init__.py | Select-String '__version__'
# Should show: __version__ = "3.0.2"
```

If the tag shows the wrong version, see [Version Mismatch in Tag](#version-mismatch-in-tag-critical-issue) in Troubleshooting.

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
- **Publish to PyPI on Release** workflow runs on `release: published` and publishes to PyPI (stable releases only).

**View Release:**
- GitHub: https://github.com/wtthornton/TappsCodingAgents/releases/tag/v3.0.2
- PyPI: https://pypi.org/project/tapps-agents/ (published automatically when release is created)

### Method 2: Manual Release Script (Windows)

**When to use:** Quick releases, testing, or when GitHub Actions is unavailable

**⚠️ CRITICAL: Version Bump Must Be Committed First**

The release script **MUST** be run from a commit that already has the version bump committed. The tag will point to the current HEAD commit, so if the version changes aren't committed, the tag will point to the wrong commit.

**Correct Process:**

```powershell
# Step 1: Update version (updates files but doesn't commit)
.\scripts\update_version.ps1 -Version 3.0.2

# Step 2: Update CHANGELOG.md with release notes
# Add section: ## [3.0.2] - YYYY-MM-DD

# Step 3: Commit version changes (CRITICAL!)
git add pyproject.toml tapps_agents/__init__.py CHANGELOG.md docs/implementation/IMPROVEMENT_PLAN.json
git commit -m "Bump version to 3.0.2"
git push origin main

# Step 4: Create release (tag will point to the version bump commit)
.\scripts\create_github_release.ps1 -Version 3.0.2 -SkipVersionUpdate
```

**What the script does:**
- Verifies current HEAD has correct version (if `-SkipVersionUpdate` not used, updates first)
- Cleans build artifacts
- Builds packages
- Verifies packages (optional)
- Verifies tag target (ensures tag will point to version bump commit)
- Creates GitHub release with tag pointing to current HEAD

**⚠️ Common Mistake:**
If you run `.\scripts\create_github_release.ps1 -Version 3.0.2` without committing the version bump first, the tag will point to the commit BEFORE the version update, causing version mismatches for users upgrading.

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
- [ ] **Version bump changes committed and pushed to main** ⚠️ CRITICAL
- [ ] All other changes committed and pushed to main
- [ ] CI/CD checks pass on main branch
- [ ] Run release readiness validation: `.\scripts\validate_release_readiness.ps1 -Version 3.0.2`
- [ ] **Verify version in HEAD commit matches target version** ⚠️ CRITICAL
  ```powershell
  git show HEAD:pyproject.toml | Select-String '^\s*version\s*='
  git show HEAD:tapps_agents/__init__.py | Select-String '__version__'
  ```

### Release

- [ ] **Tag points to version bump commit** ⚠️ CRITICAL
  - Tag MUST point to commit with version bump
  - Verify: `git show v3.0.2:tapps_agents/__init__.py | Select-String '__version__'`
  - Should show: `__version__ = "3.0.2"`
- [ ] Create and push version tag (if using Method 1)
- [ ] Monitor GitHub Actions release workflow
- [ ] Verify release created successfully
- [ ] Verify packages attached correctly
- [ ] Verify release notes extracted correctly
- [ ] **Verify tag points to correct commit** ⚠️ CRITICAL
  ```powershell
  git rev-parse v3.0.2  # Should match version bump commit
  git show v3.0.2:tapps_agents/__init__.py | Select-String '__version__'  # Should show correct version
  ```

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

### Always Publish on Release

PyPI publishing runs **whenever a release is published** (workflow: **Publish to PyPI on Release**):
- ✅ Trigger: `release: published` (GitHub release created)
- ✅ Applies to releases created by the Release workflow (tag push) or manually (e.g. `gh release create`)
- ✅ Stable releases only (skips tags containing `alpha`, `beta`, `rc`, `test`)
- ✅ Single source of truth: every published release is published to PyPI

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

### Version Mismatch in Tag (CRITICAL ISSUE)

**Symptom:** Tag points to commit with wrong version (e.g., tag `v3.0.2` but code shows `3.0.1`)

**Cause:** Tag was created before version bump was committed, or tag was created pointing to wrong commit.

**Fix:**
```powershell
# 1. Verify the issue
git show v3.0.2:tapps_agents/__init__.py | Select-String '__version__'
# If shows wrong version, continue with fix

# 2. Find the correct commit (version bump commit)
git log --oneline --all | Select-String "Bump version to 3.0.2"
# Note the commit hash (e.g., abc1234)

# 3. Delete incorrect tag (local and remote)
git tag -d v3.0.2
git push origin :refs/tags/v3.0.2

# 4. Create tag pointing to correct commit
git tag v3.0.2 abc1234  # Use commit hash from step 2
git push origin v3.0.2

# 5. Verify fix
git show v3.0.2:tapps_agents/__init__.py | Select-String '__version__'
# Should now show: __version__ = "3.0.2"

# 6. Update GitHub release (if it exists)
# Delete the release on GitHub, then recreate it
# Or use: gh release edit v3.0.2 --target abc1234
```

**Prevention:**
- Always commit version bump BEFORE creating tag
- Use release script with `-SkipVersionUpdate` after committing version bump
- Verify tag points to correct commit before pushing

### Release Workflow Fails

**Version mismatch:**
- Ensure version in `pyproject.toml` and `__init__.py` match tag
- Ensure tag points to commit with version bump
- Run: `.\scripts\update_version.ps1 -Version 3.0.2`
- Commit changes before creating tag

**Tests fail:**
- Fix failing tests before releasing
- Run tests locally: `pytest tests/`

**Package verification fails:**
- Check `MANIFEST.in` for correct inclusion/exclusion rules
- Review package contents: `python -m build && tar -tzf dist/*.tar.gz`

### Release Already Exists

If release tag already exists:
- **First verify tag points to correct commit:**
  ```powershell
  git show v3.0.2:tapps_agents/__init__.py | Select-String '__version__'
  ```
- If tag is correct, just update release on GitHub
- If tag is wrong, fix tag first (see "Version Mismatch in Tag" above)
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

1. **⚠️ CRITICAL: Commit Version Bump Before Tagging**
   - Version bump MUST be committed before creating tag
   - Tag will point to current HEAD, so HEAD must have version bump
   - Always verify: `git show HEAD:tapps_agents/__init__.py | Select-String '__version__'`

2. **Always test locally first:**
   ```bash
   python -m build
   pip install dist/tapps_agents-3.0.2-py3-none-any.whl
   ```

3. **Verify tag points to correct commit:**
   ```powershell
   # After creating tag, verify it points to version bump commit
   git rev-parse v3.0.2  # Get commit hash
   git show v3.0.2:tapps_agents/__init__.py | Select-String '__version__'  # Verify version
   ```

4. **Use TestPyPI for validation:**
   - Test package installation before production PyPI

5. **Keep CHANGELOG.md up to date:**
   - Update as you develop features
   - Makes release notes generation easier

6. **Tag from main branch:**
   - Ensures released code matches main branch
   - Tag must point to commit on main with version bump

7. **Monitor release workflow:**
   - Check GitHub Actions for any failures
   - Verify release artifacts
   - Verify tag points to correct commit

## Related Documentation

- [RELEASE_DOCUMENTATION_INDEX.md](RELEASE_DOCUMENTATION_INDEX.md) - Complete documentation index
- [RELEASE_VERSION_TAG_WARNING.md](RELEASE_VERSION_TAG_WARNING.md) - ⚠️ Critical version tag requirements
- [RELEASE_QUICK_REFERENCE.md](RELEASE_QUICK_REFERENCE.md) - Quick command reference
- [CHANGELOG.md](../CHANGELOG.md) - Release history
- [Version Update Script](../scripts/update_version.ps1) - Version management
- [Release Script](../scripts/create_github_release.ps1) - Manual release script


