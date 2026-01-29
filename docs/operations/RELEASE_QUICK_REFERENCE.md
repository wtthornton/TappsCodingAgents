# Release Quick Reference

> **⚠️ CRITICAL:** See [RELEASE_GUIDE.md](RELEASE_GUIDE.md) for complete documentation.  
> **⚠️ CRITICAL:** Version bump MUST be committed before creating tag. See [RELEASE_VERSION_TAG_WARNING.md](RELEASE_VERSION_TAG_WARNING.md).

## Quick Release (Automated)

```bash
# 1. Update version
.\scripts\update_version.ps1 -Version 3.0.2

# 2. Update CHANGELOG.md (add section for 3.0.2)

# 3. ⚠️ CRITICAL: Commit version bump BEFORE creating tag
git add pyproject.toml tapps_agents/__init__.py CHANGELOG.md docs/implementation/IMPROVEMENT_PLAN.json
git commit -m "Bump version to 3.0.2"
git push origin main

# 4. Validate readiness
.\scripts\validate_release_readiness.ps1 -Version 3.0.2

# 5. Verify HEAD has correct version (CRITICAL!)
git show HEAD:tapps_agents/__init__.py | Select-String '__version__'
# Should show: __version__ = "3.0.2"

# 6. Create and push tag (points to version bump commit)
git tag v3.0.2
git push origin v3.0.2

# 7. Verify tag points to correct commit
git show v3.0.2:tapps_agents/__init__.py | Select-String '__version__'
# Should show: __version__ = "3.0.2"

# 8. GitHub Actions automatically creates release
```

## Manual Release (Windows)

**⚠️ CRITICAL: Version bump must be committed first!**

```powershell
# Step 1: Update version (if not already done)
.\scripts\update_version.ps1 -Version 3.0.2

# Step 2: Update CHANGELOG.md

# Step 3: Commit version bump (CRITICAL!)
git add pyproject.toml tapps_agents/__init__.py CHANGELOG.md docs/implementation/IMPROVEMENT_PLAN.json
git commit -m "Bump version to 3.0.2"
git push origin main

# Step 4: Create release (script verifies version in HEAD)
.\scripts\create_github_release.ps1 -Version 3.0.2 -SkipVersionUpdate
```

## Validation Only

```powershell
.\scripts\validate_release_readiness.ps1 -Version 3.0.2
```

## Workflow Dispatch (GitHub UI)

1. Go to Actions → Release
2. Click "Run workflow"
3. Enter version: `3.0.2`
4. Run workflow (release creation triggers PyPI publish automatically)

## Common Commands

### Update Version Only
```powershell
.\scripts\update_version.ps1 -Version 3.0.2
```

### Update Version (Skip Docs)
```powershell
.\scripts\update_version.ps1 -Version 3.0.2 -SkipDocs
```

### Create Draft Release
```powershell
.\scripts\create_github_release.ps1 -Version 3.0.2 -Draft
```

### Create Prerelease
```powershell
.\scripts\create_github_release.ps1 -Version 3.0.2 -Prerelease
```

### Upload to PyPI
```powershell
.\scripts\upload_to_pypi.ps1 -Repository pypi -Token $env:TWINE_PASSWORD
```

## Troubleshooting

### Version Mismatch
```powershell
.\scripts\update_version.ps1 -Version 3.0.2
```

### Tag Already Exists
```bash
git tag -d v3.0.2
git push origin :refs/tags/v3.0.2
```

### Check Release Status
```bash
gh release view v3.0.2
```

## Files

- **📘 Main Guide**: `docs/operations/RELEASE_GUIDE.md` - **Canonical release documentation**
- **⚠️ Critical Warning**: `docs/operations/RELEASE_VERSION_TAG_WARNING.md` - Version tag requirements
- **Release Workflow**: `.github/workflows/release.yml`
- **Validation Script**: `scripts/validate_release_readiness.ps1`
- **Release Script**: `scripts/create_github_release.ps1`
- **Version Script**: `scripts/update_version.ps1`


