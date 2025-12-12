# Release Options - PyPI vs GitHub Releases

You have multiple options for distributing releases.

## Option 1: GitHub Releases (Recommended)

**Pros:**
- No PyPI account required
- Attach built artifacts (`.whl`, `.tar.gz`)
- Users can install directly from GitHub assets

### Create a GitHub Release (script)

```powershell
# Example
$VERSION = "2.0.0"
.\create_github_release.ps1 -Version $VERSION
```

### Manual GitHub Release (web)

- Tag: `v<version>` (example: `v2.0.0`)
- Title: `Release v<version>`
- Attach files from `dist/`

### Install from a GitHub Release

Users can install a wheel asset directly:

```bash
pip install <downloaded-wheel>.whl
```

## Option 2: PyPI

**Pros:**
- Discoverable on PyPI
- Standard install: `pip install tapps-agents`

**Cons:**
- Requires PyPI account + authentication

See `PYPI_UPLOAD_GUIDE.md`.

## Building Artifacts

Use standard Python build tooling:

```bash
python -m pip install --upgrade build
python -m build
```

This outputs artifacts to `dist/`.
