# Release Process Guide

This document describes the complete process for creating GitHub releases of TappsCodingAgents.

## Overview

The release process automates:
1. Version number updates in all required locations
2. Building distribution packages (sdist + wheel) with only runtime files
3. Creating GitHub releases with the built packages attached
4. Verification of package contents

## Prerequisites

### Required Tools

1. **Python 3.13+** - For building packages
2. **GitHub CLI (gh)** - For creating releases
   - Install: `winget install --id GitHub.cli` or download from https://cli.github.com/
   - Authenticate: `gh auth login`
3. **Build module** (recommended) - For building packages
   - Install: `pip install build`
   - Or use setuptools fallback: `python setup.py sdist bdist_wheel`

### Required Access

- Write access to the GitHub repository
- Authenticated GitHub CLI session

## Version Numbering

TappsCodingAgents follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

### Version Update Locations

When creating a release, version numbers are updated in:
1. `pyproject.toml` - Line 7: `version = "X.Y.Z"`
2. `tapps_agents/__init__.py` - Line 5: `__version__ = "X.Y.Z"`

Both locations are updated atomically by the release scripts.

## Release Workflow

### Quick Start

```powershell
# From project root
.\scripts\create_github_release.ps1 -Version "2.0.6" -ReleaseNotes "Release notes here"
```

This single command:
1. Updates version numbers
2. Cleans build artifacts
3. Builds packages
4. Creates GitHub release

### Step-by-Step Process

#### 1. Pre-Release Checklist

Before creating a release, verify:

- [ ] All tests pass
- [ ] CHANGELOG.md is updated with release notes
- [ ] Version number follows semantic versioning
- [ ] No uncommitted changes (or commit them first)
- [ ] GitHub CLI is authenticated: `gh auth status`

#### 2. Update Version Numbers

**Automatic (recommended):**
```powershell
.\scripts\update_version.ps1 -Version "2.0.6"
```

**Manual:**
- Edit `pyproject.toml`: `version = "2.0.6"`
- Edit `tapps_agents/__init__.py`: `__version__ = "2.0.6"`

#### 3. Build Distribution Packages

**Automatic (recommended):**
The release script builds packages automatically. Or manually:

```powershell
# Using build module (recommended)
python -m build

# Or using setuptools
python setup.py sdist bdist_wheel
```

This creates:
- Source distribution: `dist/tapps-agents-X.Y.Z.tar.gz`
- Wheel distribution: `dist/tapps_agents-X.Y.Z-py3-none-any.whl`

#### 4. Verify Package Contents

**Automatic (if verification script exists):**
The release script runs verification automatically.

**Manual verification:**
```powershell
.\scripts\verify_release_package.ps1 -PackagePath "dist\tapps-agents-2.0.6.whl"
```

Or manually extract and inspect:
```powershell
# Extract wheel
Expand-Archive -Path "dist\tapps_agents-2.0.6-py3-none-any.whl" -DestinationPath "temp_extract"

# Verify contents
# Should contain: tapps_agents/, pyproject.toml, setup.py, README.md, LICENSE
# Should NOT contain: tests/, docs/, examples/, scripts/, etc.
```

#### 5. Create GitHub Release

**Automatic (recommended):**
```powershell
.\scripts\create_github_release.ps1 -Version "2.0.6" -ReleaseNotes "Release notes here"
```

**Options:**
- `-Version "X.Y.Z"` - Version number (required)
- `-Tag "vX.Y.Z"` - Git tag (defaults to "v{Version}")
- `-Title "Release Title"` - Release title (defaults to "Release v{Version}")
- `-ReleaseNotes "Notes"` - Release notes (defaults to CHANGELOG.md entry or "Release {Tag}")
- `-Draft` - Create as draft release
- `-Prerelease` - Mark as pre-release
- `-SkipVersionUpdate` - Skip version update step
- `-SkipBuild` - Skip build step (use existing packages)
- `-Repo "owner/repo"` - Repository (defaults to "wtthornton/TappsCodingAgents")

**Manual (using GitHub CLI):**
```powershell
gh release create v2.0.6 `
  --title "Release v2.0.6" `
  --notes "Release notes here" `
  dist/tapps-agents-2.0.6.tar.gz `
  dist/tapps_agents-2.0.6-py3-none-any.whl
```

#### 6. Post-Release Verification

After creating the release:

1. **Verify on GitHub:**
   - Visit: https://github.com/wtthornton/TappsCodingAgents/releases
   - Verify tag, title, and release notes
   - Verify packages are attached

2. **Test Installation:**
   ```powershell
   # Create test environment
   python -m venv test_env
   test_env\Scripts\activate
   
   # Install from PyPI (if published) or from wheel
   pip install tapps-agents==2.0.6
   # Or: pip install dist/tapps_agents-2.0.6-py3-none-any.whl
   
   # Verify CLI works
   tapps-agents --version
   # Should output: tapps-agents 2.0.6
   
   # Verify agents accessible
   tapps-agents reviewer --help
   ```

3. **Update Documentation:**
   - Ensure CHANGELOG.md entry is complete
   - Update any version references in documentation if needed

## What Gets Included in Releases

Release packages contain **only runtime files** needed for users to install and use `tapps-agents`.

### Included Files

- `tapps_agents/` - Main package (all Python code + resources)
- `pyproject.toml` - Package metadata
- `setup.py` - Setup script
- `MANIFEST.in` - Package data rules
- `README.md` - User documentation
- `LICENSE` - License file

### Excluded Files

- `tests/` - Test files
- `docs/` - Documentation (available on GitHub)
- `examples/` - Example files
- `scripts/` - Development scripts
- `workflows/` - Workflow definitions
- `requirements/` - Requirements documentation
- `templates/` - Project templates
- `implementation/` - Implementation documentation
- `.claude/`, `.cursor/`, `.bmad-core/` - IDE configurations
- All build artifacts and caches

See `RELEASE_INCLUDES.md` for the complete list.

## Release Scripts

### update_version.ps1

Updates version numbers in `pyproject.toml` and `tapps_agents/__init__.py`.

**Usage:**
```powershell
.\scripts\update_version.ps1 -Version "2.0.6"
```

**Features:**
- Validates semantic versioning format
- Updates both files atomically
- Verifies updates succeeded
- Shows current vs new version

### create_github_release.ps1

Complete release automation script.

**Usage:**
```powershell
.\scripts\create_github_release.ps1 -Version "2.0.6"
```

**Features:**
- Updates version numbers
- Cleans build artifacts
- Builds distribution packages
- Verifies package contents (if script exists)
- Creates GitHub release
- Attaches built packages

### verify_release_package.ps1

Verifies package contents contain only runtime files.

**Usage:**
```powershell
.\scripts\verify_release_package.ps1 -PackagePath "dist\tapps-agents-2.0.6.whl"
```

**Features:**
- Extracts and inspects package
- Verifies included files
- Checks for excluded files
- Reports any issues

## Troubleshooting

### Version Update Fails

**Issue:** Script can't find files or update fails.

**Solution:**
- Ensure you're running from project root
- Check file paths are correct
- Verify write permissions

### Build Fails

**Issue:** `python -m build` fails.

**Solutions:**
- Install build module: `pip install build`
- Or use setuptools: `python setup.py sdist bdist_wheel`
- Check for syntax errors in Python files
- Verify `MANIFEST.in` is correct

### GitHub Release Fails

**Issue:** `gh release create` fails.

**Solutions:**
- Verify GitHub CLI is authenticated: `gh auth status`
- Check repository name is correct
- Verify tag doesn't already exist
- Check network connectivity

### Package Contains Dev Files

**Issue:** Built package includes test files or documentation.

**Solutions:**
- Verify `MANIFEST.in` excludes dev directories
- Check `pyproject.toml` package find configuration
- Review `RELEASE_INCLUDES.md` for exclusion patterns
- Run verification script to identify issues

### Package Too Large

**Issue:** Package size is unexpectedly large.

**Solutions:**
- Verify build artifacts are excluded
- Check for unnecessary files in `tapps_agents/`
- Review `MANIFEST.in` exclusions
- Use verification script to identify large files

## Best Practices

1. **Always test before releasing:**
   - Build packages locally
   - Install and test in clean environment
   - Verify all agents work

2. **Update CHANGELOG.md:**
   - Document all changes
   - Follow Keep a Changelog format
   - Include breaking changes prominently

3. **Use semantic versioning:**
   - MAJOR for breaking changes
   - MINOR for new features
   - PATCH for bug fixes

4. **Create draft releases first:**
   - Use `-Draft` flag for initial release
   - Review on GitHub before publishing
   - Test installation from draft release

5. **Verify package contents:**
   - Always run verification script
   - Manually inspect if needed
   - Ensure no dev files included

6. **Tag releases in git:**
   - Release script creates GitHub release tag
   - Consider creating local git tag: `git tag v2.0.6`
   - Push tags: `git push --tags`

## Automation (Future)

The release process can be automated with:

- **GitHub Actions workflow:**
  - Trigger on version tag push
  - Build packages automatically
  - Create release with packages
  - Publish to PyPI (optional)

- **Version bump automation:**
  - Auto-increment patch/minor/major
  - Generate release notes from commits
  - Update CHANGELOG.md automatically

## Related Documentation

- `RELEASE_INCLUDES.md` - What files are included/excluded
- `MANIFEST.in` - Package inclusion rules
- `CHANGELOG.md` - Release history
- `docs/DEPLOYMENT.md` - Installation guide

## Support

For issues or questions:
- Check troubleshooting section above
- Review script error messages
- Verify prerequisites are met
- Check GitHub repository issues

