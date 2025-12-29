# Release Quick Reference

## Quick Release (Automated)

```bash
# 1. Update version
.\scripts\update_version.ps1 -Version 3.0.2

# 2. Update CHANGELOG.md (add section for 3.0.2)

# 3. Validate readiness
.\scripts\validate_release_readiness.ps1 -Version 3.0.2

# 4. Commit and push
git add pyproject.toml tapps_agents/__init__.py CHANGELOG.md
git commit -m "Bump version to 3.0.2"
git push origin main

# 5. Create and push tag
git tag v3.0.2
git push origin v3.0.2

# 6. GitHub Actions automatically creates release
```

## Manual Release (Windows)

```powershell
.\scripts\create_github_release.ps1 -Version 3.0.2
```

## Validation Only

```powershell
.\scripts\validate_release_readiness.ps1 -Version 3.0.2
```

## Workflow Dispatch (GitHub UI)

1. Go to Actions → Release
2. Click "Run workflow"
3. Enter version: `3.0.2`
4. Optionally check "Skip PyPI upload"
5. Run workflow

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

- **Release Workflow**: `.github/workflows/release.yml`
- **Release Guide**: `docs/RELEASE_GUIDE.md`
- **Process Analysis**: `docs/RELEASE_PROCESS_ANALYSIS.md`
- **Validation Script**: `scripts/validate_release_readiness.ps1`
- **Release Script**: `scripts/create_github_release.ps1`
- **Version Script**: `scripts/update_version.ps1`

