# Version Update Script Documentation

**Script:** `scripts/update_version.ps1`  
**Purpose:** Automatically update version numbers across all project files

## Overview

The version update script ensures that version numbers are synchronized across:
- Core package files (`pyproject.toml`, `tapps_agents/__init__.py`)
- All documentation files with version headers
- README.md version badge

This prevents version mismatches and ensures consistency across the entire project.

## Usage

### Basic Usage (Updates Everything)

```powershell
.\scripts\update_version.ps1 -Version "2.4.2"
```

### Core Files Only (Skip Documentation)

```powershell
.\scripts\update_version.ps1 -Version "2.4.2" -SkipDocs
```

## What Gets Updated

### Core Files (Always Updated)
1. **`pyproject.toml`** - Package version
2. **`tapps_agents/__init__.py`** - `__version__` variable

### Documentation Files (Updated unless `-SkipDocs` is used)
3. **`README.md`** - Version badge and status section
4. **`PROJECT_ANALYSIS_2026.md`** - Version header
5. **`docs/ARCHITECTURE.md`** - Version header
6. **`docs/API.md`** - Version header
7. **`docs/DEPLOYMENT.md`** - Version header
8. **`docs/TROUBLESHOOTING.md`** - Version header
9. **`docs/RUNBOOKS.md`** - Version header
10. **`docs/QUICK_START_OPTIMIZATIONS.md`** - Version header
11. **`docs/HARDWARE_RECOMMENDATIONS.md`** - Project version
12. **`docs/README.md`** - Documentation version
13. **`docs/PROJECT_CONTEXT.md`** - Framework version and version header
14. **`requirements/TECH_STACK.md`** - Version header

## Features

### Validation
- ✅ Validates semantic versioning format (X.Y.Z)
- ✅ Checks for version mismatches before updating
- ✅ Verifies updates succeeded after completion

### Safety
- ✅ Shows current versions before updating
- ✅ Prompts for confirmation if versions don't match
- ✅ Lists all files that were updated
- ✅ Provides verification status

### Smart Updates
- ✅ Preserves historical version references in documentation
- ✅ Only updates version headers, not historical mentions
- ✅ Handles different version format patterns (badges, headers, etc.)

## Example Output

```
=== Version Update Script ===

Updating version to: 2.4.2

Current versions:
  pyproject.toml: 2.4.1
  __init__.py:    2.4.1

Updating pyproject.toml...
Updating tapps_agents/__init__.py...

Updating documentation files...
  ✓ Updated: README.md
  ✓ Updated: docs/ARCHITECTURE.md
  ✓ Updated: docs/API.md
  ...

=== Version Update Complete ===

Updated files (14 total):
  - pyproject.toml
  - tapps_agents/__init__.py
  - README.md
  - docs/ARCHITECTURE.md
  ...

New version: 2.4.2

Verification: SUCCESS
  pyproject.toml: 2.4.2
  __init__.py:    2.4.2

Next steps:
  1. Review the changes: git diff
  2. Update CHANGELOG.md with release notes for version 2.4.2
  3. Build packages: python -m build
  4. Create release: .\scripts\create_github_release.ps1 -Version "2.4.2"
```

## Integration with Release Process

The version update script is part of the release workflow:

1. **Update Version** - Run `update_version.ps1`
2. **Update CHANGELOG.md** - Add release notes (manual step)
3. **Build Packages** - `python -m build`
4. **Create Release** - `create_github_release.ps1`

See `docs/RELEASE_PROCESS.md` for the complete release workflow.

## Notes

- **Historical References**: The script intentionally preserves historical version references in documentation (e.g., "Fixed in v2.4.1+") as these provide context about when features were added.

- **CHANGELOG.md**: The script does NOT update CHANGELOG.md automatically. You must manually add the new version entry with release notes.

- **Pattern Matching**: The script uses regex patterns to find and replace version numbers. If you add new documentation files with version headers, you may need to update the script's pattern list.

## Troubleshooting

### Script Can't Find Files

**Issue:** Script reports files not found.

**Solution:**
- Ensure you're running from the project root
- Check that file paths are correct
- Verify the script is in `scripts/update_version.ps1`

### Version Format Invalid

**Issue:** Script rejects version format.

**Solution:**
- Use semantic versioning format: `X.Y.Z` (e.g., `2.4.2`)
- Don't include "v" prefix (the script handles that for git tags)

### Verification Fails

**Issue:** Script reports verification failed.

**Solution:**
- Check file permissions (ensure files are writable)
- Review the diff: `git diff pyproject.toml tapps_agents/__init__.py`
- Manually verify the version strings were updated correctly

## Adding New Files

If you add new documentation files that should be updated:

1. Add the file to the `$docFiles` array in the script
2. Define the regex patterns that match version references in that file
3. Test with a dry run first

Example:
```powershell
@{
    Path = "docs/NEW_FILE.md"
    Patterns = @(
        @{ Pattern = '\*\*Version\*\*:\s*([\d\.]+)'; Replacement = "**Version**: $Version" }
    )
}
```

## Related Scripts

- `scripts/create_github_release.ps1` - Complete release automation
- `scripts/verify_release_package.ps1` - Package verification

## Version History

- **v2.4.2** - Enhanced to update all documentation files automatically
- **v2.0.6** - Initial version (core files only)

