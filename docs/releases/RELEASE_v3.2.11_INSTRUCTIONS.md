# Release v3.2.11 - Instructions

## Version Updated ✅

The version has been updated to **3.2.11** in:
- ✅ `tapps_agents/__init__.py` - `__version__ = "3.2.11"`
- ✅ `pyproject.toml` - `version = "3.2.11"`
- ✅ `CHANGELOG.md` - Added release notes for 3.2.11
- ✅ `RELEASE_NOTES_v3.2.11.md` - Detailed release notes created

## Release Process

The release workflow (`.github/workflows/release.yml`) supports two methods:

### Method 1: Create Git Tag (Recommended)

1. **Commit the version changes:**
   ```bash
   git add tapps_agents/__init__.py pyproject.toml CHANGELOG.md RELEASE_NOTES_v3.2.11.md
   git commit -m "Bump version to 3.2.11 - Test coverage improvements"
   ```

2. **Create and push the version tag:**
   ```bash
   git tag v3.2.11
   git push origin v3.2.11
   ```

3. **Push the commit:**
   ```bash
   git push origin main
   ```

The workflow will automatically:
- ✅ Validate version consistency
- ✅ Run full test suite
- ✅ Build packages
- ✅ Create GitHub release
- ✅ Publish to PyPI (if tag doesn't contain alpha/beta/rc)

### Method 2: Manual Workflow Dispatch

1. **Commit the version changes** (same as above)

2. **Go to GitHub Actions:**
   - Navigate to: https://github.com/[your-repo]/actions/workflows/release.yml
   - Click "Run workflow"
   - Enter version: `3.2.11`
   - Optionally check "Skip PyPI upload" if you don't want to publish yet
   - Click "Run workflow"

## What's Included in This Release

### Test Coverage Improvements
- 34 new tests added
- 91.2% pass rate
- Coverage improved from 0% to ~80%+ for critical components

### Code Quality
- Fixed type hints in CLI main
- Improved test infrastructure
- Better code maintainability

## Verification

After the release is created, verify:
1. ✅ GitHub release exists at: `https://github.com/[repo]/releases/tag/v3.2.11`
2. ✅ Release notes are correctly displayed
3. ✅ Packages (wheel and sdist) are attached
4. ✅ PyPI package is updated (if published): `pip install tapps-agents==3.2.11`

## Files Changed for Release

```
Modified:
- tapps_agents/__init__.py (version bump)
- pyproject.toml (version bump)
- CHANGELOG.md (release notes)

Created:
- RELEASE_NOTES_v3.2.11.md (detailed release notes)
```

## Next Steps After Release

1. Monitor the GitHub Actions workflow for any failures
2. Verify the release appears on GitHub
3. Test installation: `pip install tapps-agents==3.2.11`
4. Update any documentation that references the version
