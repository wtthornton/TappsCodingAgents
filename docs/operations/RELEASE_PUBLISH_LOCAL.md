# Publish Release Locally (When GitHub Actions Fails)

Use this when the Release or PyPI workflow fails (e.g. runner acquisition, internal server error) and you need to get a version on PyPI and/or create the GitHub release from your machine.

## Prerequisites

- Python 3.12+ with `build` and `twine` (or use project venv)
- **PyPI API token** in `.env`: add `TWINE_PASSWORD=pypi-...` or `PYPI_API_TOKEN=pypi-...`  
  Get token: https://pypi.org/manage/account/token/
- (Optional) `gh` CLI for creating the GitHub release

## 1. Publish to PyPI (required for pip install)

From the **project root**:

```powershell
# Use the tag (version already bumped and committed)
git checkout v3.5.39

# Build packages
python -m pip install build twine --quiet
python -m build

# Upload to PyPI (reads token from .env: TWINE_PASSWORD or PYPI_API_TOKEN)
.\scripts\upload_to_pypi.ps1 -Repository pypi -SkipExisting
```

Then verify: https://pypi.org/project/tapps-agents/

## 2. Create GitHub Release (optional: release page + artifacts)

If the Release workflow never created the release, you can create it and attach the same `dist/` files:

```powershell
# Still on v3.5.39 with dist/ from step 1
$tag = "v3.5.39"

# Create release with notes from CHANGELOG (or use --notes "Release $tag")
gh release create $tag `
  --title "Release $tag" `
  --notes-file release_notes.md `
  dist/*.tar.gz dist/*.whl
```

To generate `release_notes.md` from CHANGELOG for 3.5.39, run this once (PowerShell):

```powershell
$v = "3.5.39"
$content = Get-Content CHANGELOG.md -Raw
if ($content -match "(?s)## \[$v\].*?(?=## \[|\z)") {
  $matches[0].Trim() | Set-Content release_notes.md -Encoding UTF8
} else {
  "Release $tag`n`nSee CHANGELOG.md" | Set-Content release_notes.md -Encoding UTF8
}
```

Or create a minimal release without notes:

```powershell
gh release create v3.5.39 --title "Release v3.5.39" --notes "See CHANGELOG.md" dist/*.tar.gz dist/*.whl
```

## 3. Return to main

```powershell
git checkout main
```

## Summary

| Goal              | Steps                    |
|-------------------|--------------------------|
| Get 3.5.39 on PyPI | 1 only (build + upload)   |
| Also have GitHub release | 1 + 2 (then optional 3) |
