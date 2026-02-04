# PyPI Deployment Guide

**Last Updated:** 2026-02-04
**Version:** 3.5.40

---

## Overview

This guide documents the complete PyPI deployment process for TappsCodingAgents. The project uses an automated PowerShell script that reads credentials from a `.env` file (git-ignored) for secure deployments.

---

## Prerequisites

**Required Tools:**
- Python 3.10+
- `build` package: `pip install build`
- `twine` package: `pip install twine`

**Required Credentials:**
- PyPI API token (stored in `.env` file)

---

## Credentials Location

### `.env` File (Git-Ignored)

**Location:** `c:\cursor\TappsCodingAgents\.env`

**Format:**
```env
# PyPI / Twine (for scripts/upload_to_pypi.ps1 -Repository pypi)
TWINE_PASSWORD=pypi-<your-token-here>
```

**Important:**
- Never commit `.env` file to git (already in `.gitignore`)
- Token format: `pypi-<long-token-string>`
- Get token from: https://pypi.org/manage/account/token/

---

## Deployment Script

### `scripts/upload_to_pypi.ps1`

Automated PowerShell script that:
1. Reads token from `.env` file automatically
2. Validates package files in `dist/` directory
3. Uploads to PyPI or TestPyPI
4. Clears token from environment after upload

**Usage:**

```powershell
# Production PyPI (default requires explicit -Repository flag)
.\scripts\upload_to_pypi.ps1 -Repository pypi

# Test PyPI (for testing before production)
.\scripts\upload_to_pypi.ps1 -Repository testpypi

# With additional options
.\scripts\upload_to_pypi.ps1 -Repository pypi -SkipExisting -ShowVerbose
```

**Parameters:**
- `-Repository`: `pypi` (production) or `testpypi` (testing)
- `-SkipExisting`: Skip files that already exist on PyPI
- `-ShowVerbose`: Show verbose twine output
- `-Token`: Override token (not recommended, use `.env` instead)

---

## Complete Deployment Process

### Step 1: Update Version Number

**Update these files:**
1. `pyproject.toml` (line 7):
   ```toml
   version = "3.5.40"
   ```

2. `tapps_agents/__init__.py` (lines 27-31):
   ```python
   __version__: str = "3.5.40"
   _version_: str = "3.5.40"
   ```

**Automated Script (Recommended):**
```powershell
.\scripts\update_version.ps1 -Version 3.5.40
```

### Step 2: Commit Version Bump

```bash
git add pyproject.toml tapps_agents/__init__.py
git commit -m "chore: Bump version to 3.5.40"
git push origin main
```

### Step 3: Create Git Tag

```bash
git tag v3.5.40
git push origin v3.5.40
```

### Step 4: Clean Old Build Artifacts

```bash
rm -rf dist/ build/ *.egg-info
```

### Step 5: Build Distribution Packages

```bash
python -m build
```

**Expected Output:**
```
dist/
  tapps_agents-3.5.40-py3-none-any.whl  (2.2 MB)
  tapps_agents-3.5.40.tar.gz            (1.8 MB)
```

### Step 6: Upload to PyPI

```powershell
.\scripts\upload_to_pypi.ps1 -Repository pypi
```

**Expected Output:**
```
=== PyPI Upload Script ===

Using token from .env (C:\cursor\TappsCodingAgents\.env)
Found 2 file(s) to upload:
  - tapps_agents-3.5.40-py3-none-any.whl
  - tapps_agents-3.5.40.tar.gz

Uploading to: pypi
...
View at: https://pypi.org/project/tapps-agents/3.5.40/

=== Upload Successful! ===
```

### Step 7: Verify Installation

```bash
# Check PyPI shows latest version
pip index versions tapps-agents

# Test installation (use virtual environment!)
python -m venv test-env
test-env\Scripts\activate
pip install tapps-agents==3.5.40
tapps-agents --version
deactivate
rm -rf test-env
```

---

## Troubleshooting

### Error: "No module named build"

**Solution:**
```bash
pip install build
```

### Error: "No module named twine"

**Solution:**
```bash
pip install twine
```

### Error: "dist/ folder not found"

**Solution:**
```bash
python -m build
```

### Error: "Token required" or "Invalid credentials"

**Problem:** Token not found in `.env` file or environment

**Solution:**
1. Check `.env` file exists: `ls -la .env`
2. Verify token format: `TWINE_PASSWORD=pypi-...`
3. Get new token: https://pypi.org/manage/account/token/
4. Update `.env` file

### Error: "File already exists"

**Problem:** Version already uploaded to PyPI

**Solution:**
1. Bump version number
2. Rebuild packages
3. Or use `-SkipExisting` flag to skip already-uploaded files

---

## Testing Before Production

**Always test on TestPyPI first for major releases:**

```powershell
# Upload to TestPyPI
.\scripts\upload_to_pypi.ps1 -Repository testpypi

# Test installation from TestPyPI
pip install -i https://test.pypi.org/simple/ tapps-agents==3.5.40
```

**Note:** TestPyPI dependencies may not resolve correctly. This is normal for testing.

---

## Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Rotate tokens regularly** - Generate new tokens annually
3. **Use scoped tokens** - Limit token to `tapps-agents` project only
4. **Clear environment after upload** - Script does this automatically
5. **Store backup token securely** - Use password manager, not git

---

## Release Checklist

Before deploying to PyPI:

- [ ] All tests passing (`pytest`)
- [ ] Code review completed
- [ ] CHANGELOG.md updated
- [ ] Release notes created (`docs/releases/RELEASE-{version}.md`)
- [ ] Version bumped in `pyproject.toml` and `__init__.py`
- [ ] Git tag created (`v{version}`)
- [ ] Changes pushed to main branch
- [ ] Distribution packages built (`python -m build`)
- [ ] Uploaded to PyPI (`.\scripts\upload_to_pypi.ps1 -Repository pypi`)
- [ ] Installation verified (`pip install tapps-agents=={version}`)
- [ ] PyPI page checked: https://pypi.org/project/tapps-agents/{version}/

---

## Historical Deployments

### v3.5.40 (2026-02-04)

**Deployed By:** Claude Sonnet 4.5
**Release Notes:** [RELEASE-3.5.40.md](../releases/RELEASE-3.5.40.md)
**PyPI URL:** https://pypi.org/project/tapps-agents/3.5.40/

**Changes:**
- Fixed BUG-003: Implementation step wrong artifacts (4-part fix)
- Fixed BUG-002: CLI quotation parsing refinement
- Updated ADR-002: Equal Platform Support Policy
- Complete release notes and documentation

**Deployment Steps:**
1. Version bump: bf5e1b9
2. Build packages: `python -m build`
3. Upload: `.\scripts\upload_to_pypi.ps1 -Repository pypi`
4. Verified: `pip index versions tapps-agents` shows 3.5.40 as LATEST

### v3.5.39 (Previous)

**PyPI URL:** https://pypi.org/project/tapps-agents/3.5.39/

---

## Quick Reference

**Full Deployment (All Steps):**
```powershell
# 1. Update version
.\scripts\update_version.ps1 -Version 3.5.40

# 2. Commit and tag
git add .
git commit -m "chore: Bump version to 3.5.40"
git tag v3.5.40
git push origin main
git push origin v3.5.40

# 3. Build and upload
rm -rf dist/ build/ *.egg-info
python -m build
.\scripts\upload_to_pypi.ps1 -Repository pypi

# 4. Verify
pip index versions tapps-agents
```

**Quick Upload (Version already bumped):**
```powershell
python -m build
.\scripts\upload_to_pypi.ps1 -Repository pypi
```

---

## Related Documentation

- [RELEASE_GUIDE.md](RELEASE_GUIDE.md) - Complete release process
- [CHANGELOG.md](../../CHANGELOG.md) - Release history
- [scripts/upload_to_pypi.ps1](../../scripts/upload_to_pypi.ps1) - Deployment script
- [.env.example](../../.env.example) - Credentials template

---

**Maintained By:** TappsCodingAgents Team
**Last Deployment:** v3.5.40 (2026-02-04)
**PyPI Project:** https://pypi.org/project/tapps-agents/
