# Release Options - PyPI vs GitHub Releases

You have **multiple options** for creating and updating releases. **You don't need PyPI!**

## Option 1: GitHub Releases (Recommended - Easiest) ⭐

**Pros:**
- ✅ No PyPI account needed
- ✅ No API tokens required
- ✅ Works with your existing GitHub repo
- ✅ Attach built packages (.whl, .tar.gz)
- ✅ Release notes from RELEASE_NOTES files
- ✅ Users can install directly from GitHub
- ✅ Free and unlimited

**Cons:**
- ⚠️ Not discoverable on PyPI
- ⚠️ Users need to know about your GitHub repo

### Quick Start

**Step 1: Install GitHub CLI (if not installed)**
```powershell
winget install --id GitHub.cli
# OR download from: https://cli.github.com/
```

**Step 2: Authenticate**
```powershell
gh auth login
```

**Step 3: Create Release**
```powershell
.\create_github_release.ps1 -Version "1.6.1"
```

That's it! The script will:
- Read release notes from `RELEASE_NOTES_v1.6.1.md`
- Attach all matching files from `dist/`
- Create the release on GitHub

### Manual GitHub Release (Web Interface)

1. Go to: https://github.com/wtthornton/TappsCodingAgents/releases/new
2. Click "Choose a tag" → Create new tag: `v1.6.1`
3. Title: `Release v1.6.1`
4. Description: Copy from `RELEASE_NOTES_v1.6.1.md`
5. Attach files: Drag `dist/tapps_agents-1.6.1-py3-none-any.whl` and `dist/tapps_agents-1.6.1.tar.gz`
6. Click "Publish release"

### Install from GitHub Release

Users can install directly:
```bash
# From wheel file
pip install https://github.com/wtthornton/TappsCodingAgents/releases/download/v1.6.1/tapps_agents-1.6.1-py3-none-any.whl

# Or download and install
pip install tapps_agents-1.6.1-py3-none-any.whl
```

---

## Option 2: PyPI (Public Package Index)

**Pros:**
- ✅ Discoverable via `pip search` (if enabled)
- ✅ Standard Python package distribution
- ✅ `pip install tapps-agents` works
- ✅ Professional appearance

**Cons:**
- ⚠️ Requires PyPI account and API token
- ⚠️ More setup steps
- ⚠️ Public (if using public PyPI)

### When to Use PyPI
- You want your package discoverable
- You want users to install with just `pip install tapps-agents`
- You're building a library for public use

---

## Option 3: GitHub Releases + PyPI (Best of Both)

**Recommended Approach:**
1. Create GitHub Release (for version control, release notes, downloads)
2. Also publish to PyPI (for easy installation)

This gives you:
- ✅ Version history in GitHub
- ✅ Easy installation via `pip install tapps-agents`
- ✅ Release notes in both places
- ✅ Maximum visibility

---

## Option 4: Private Package Repository

If you need private distribution:

- **CloudRepo**: Private PyPI-compatible repository
- **Anystack**: Private package hosting
- **Self-hosted pypiserver**: Host your own PyPI server

---

## Comparison Table

| Feature | GitHub Releases | PyPI | Both |
|---------|----------------|------|------|
| Setup Complexity | ⭐ Easy | ⭐⭐ Medium | ⭐⭐ Medium |
| Account Required | GitHub (free) | PyPI (free) | Both (free) |
| API Token Needed | No (uses gh CLI) | Yes | Yes (for PyPI) |
| Discoverability | Low | High | High |
| Installation | `pip install <url>` | `pip install tapps-agents` | Both |
| Release Notes | ✅ Yes | ✅ Yes | ✅ Yes |
| Version History | ✅ Yes | ✅ Yes | ✅ Yes |
| Private Packages | ✅ Yes | ❌ No (public) | ✅ Yes (GitHub) |

---

## Recommendation

**For your project, I recommend: GitHub Releases**

Reasons:
1. ✅ You already have GitHub repo
2. ✅ No additional accounts/tokens needed
3. ✅ Release notes already in place
4. ✅ Packages already built
5. ✅ Can add PyPI later if needed

**Quick Command:**
```powershell
.\create_github_release.ps1 -Version "1.6.1"
```

---

## Script Usage

### Basic Release
```powershell
.\create_github_release.ps1 -Version "1.6.1"
```

### Custom Tag
```powershell
.\create_github_release.ps1 -Version "1.6.1" -Tag "v1.6.1-beta"
```

### Draft Release (for review)
```powershell
.\create_github_release.ps1 -Version "1.6.1" -Draft
```

### Pre-release
```powershell
.\create_github_release.ps1 -Version "1.6.1" -Prerelease
```

### Custom Release Notes
```powershell
.\create_github_release.ps1 -Version "1.6.1" -ReleaseNotes "Custom notes here"
```

---

## Next Steps

1. **Install GitHub CLI** (if needed): `winget install --id GitHub.cli`
2. **Authenticate**: `gh auth login`
3. **Create Release**: `.\create_github_release.ps1 -Version "1.6.1"`

That's it! No PyPI needed. 🎉

