# Release Options - PyPI vs GitHub Releases

You have multiple options for distributing releases.

## Option 0: Install from Source (Recommended for Development)

**Best for:** Developers who want to modify the code or contribute

**Installation Steps:**
```bash
# 1. Clone the repository
git clone https://github.com/wtthornton/TappsCodingAgents.git
cd TappsCodingAgents

# 2. Create and activate virtual environment (project-scoped, not global)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Upgrade pip to latest version (2025 best practice)
python -m pip install --upgrade pip

# 4. Install in editable mode (recommended for development)
pip install -e .

# 5. Verify installation
tapps-agents --version
```

**Why Editable Mode?**
- Changes to source code are immediately available without reinstalling
- Recommended for local development (2025 Python best practice)
- Project-scoped installation (no global system changes)

## Option 1: GitHub Releases (Recommended for End Users)

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
# Download the .whl file from GitHub Releases, then:
pip install <downloaded-wheel>.whl
```

## Option 2: PyPI (Future)

**Pros:**
- Discoverable on PyPI
- Standard install: `pip install tapps-agents`

**Cons:**
- Requires PyPI account + authentication
- Package must be published to PyPI (currently not published)

**Note:** As of January 2026, this package is not published to PyPI. Users should install from source (Option 0) or GitHub Releases (Option 1).

## Building Artifacts

Use standard Python build tooling:

```bash
python -m pip install --upgrade build
python -m build
```

This outputs artifacts to `dist/`.
