# Dot Directories Release Review Plan

**Date:** 2025-01-20  
**Purpose:** Review all `.` (dot) directories and files to ensure proper exclusion from release packages

## Executive Summary

This document reviews all dot-prefixed directories and files in the TappsCodingAgents repository to determine:
1. Which are used at runtime (should NOT be in framework package)
2. Which are development-only (should be excluded)
3. Which are templates that should be packaged (in `tapps_agents/resources/`)
4. Current exclusion status in `MANIFEST.in`

## Current Dot Directories Inventory

Based on repository scan, the following dot directories exist:

| Directory | Size | Runtime Usage | Current Status | Action Required |
|-----------|------|---------------|-----------------|-----------------|
| `.bmad-core` | 931 KB | ❌ No | ✅ Excluded | ✅ None - Already correct |
| `.claude` | 167 KB | ❌ No | ✅ Excluded | ✅ None - Already correct |
| `.cursor` | 3.9 MB | ❌ No | ✅ Excluded | ✅ None - Already correct |
| `.git` | 34 MB | ❌ No | ⚠️ Not explicitly excluded | ⚠️ Add explicit exclusion |
| `.github` | 36 KB | ❌ No | ⚠️ Not explicitly excluded | ⚠️ Add explicit exclusion |
| `.mypy_cache` | 333 MB | ❌ No | ✅ Excluded | ✅ None - Already correct |
| `.pytest_cache` | 372 KB | ❌ No | ✅ Excluded | ✅ None - Already correct |
| `.ruff_cache` | 232 KB | ❌ No | ✅ Excluded | ✅ None - Already correct |
| `.tapps-agents` | 11 MB | ⚠️ User runtime data | ⚠️ Not explicitly excluded | ⚠️ Add explicit exclusion |
| `.venv` | 226 MB | ❌ No | ✅ Excluded | ✅ None - Already correct |

## Current Dot Files Inventory

| File | Runtime Usage | Current Status | Action Required |
|------|---------------|----------------|-----------------|
| `.cursorignore` | ❌ No (template in resources) | ⚠️ Not explicitly excluded | ⚠️ Add explicit exclusion |
| `.cursorrules` | ❌ No | ⚠️ Not explicitly excluded | ⚠️ Add explicit exclusion |
| `.env` | ❌ No (user-specific) | ⚠️ Not explicitly excluded | ⚠️ Add explicit exclusion |
| `.gitignore` | ❌ No (project-specific) | ⚠️ Not explicitly excluded | ⚠️ Add explicit exclusion |

## Detailed Analysis

### ✅ Already Correctly Excluded

#### `.bmad-core/`
- **Status:** ✅ Excluded in `MANIFEST.in` line 12
- **Usage:** Development reference material only
- **Evidence:** Only mentioned in comments/docs, no runtime code access
- **Action:** None needed

#### `.claude/`
- **Status:** ✅ Excluded in `MANIFEST.in` line 13
- **Usage:** Development templates (shipped via `tapps_agents/resources/claude/`)
- **Evidence:** `init_project.py` copies from packaged resources, not from repo `.claude/`
- **Action:** None needed

#### `.cursor/`
- **Status:** ✅ Excluded in `MANIFEST.in` line 14
- **Usage:** Development templates (shipped via `tapps_agents/resources/cursor/`)
- **Evidence:** `init_project.py` copies from packaged resources, not from repo `.cursor/`
- **Action:** None needed

#### `.mypy_cache/`
- **Status:** ✅ Excluded in `MANIFEST.in` line 27
- **Usage:** Build artifact (type checking cache)
- **Action:** None needed

#### `.pytest_cache/`
- **Status:** ✅ Excluded in `MANIFEST.in` line 26
- **Usage:** Build artifact (test execution cache)
- **Action:** None needed

#### `.ruff_cache/`
- **Status:** ✅ Excluded in `MANIFEST.in` line 15
- **Usage:** Build artifact (linting cache)
- **Action:** None needed

#### `.venv/`
- **Status:** ✅ Excluded in `MANIFEST.in` line 31
- **Usage:** Virtual environment (development only)
- **Action:** None needed

### ⚠️ Needs Explicit Exclusion

#### `.git/`
- **Status:** ⚠️ Not explicitly excluded (but git typically ignores itself)
- **Usage:** Git repository metadata
- **Risk:** Low (git usually doesn't include `.git/` in packages)
- **Recommendation:** Add explicit exclusion for safety
- **Action:** Add to `MANIFEST.in`

#### `.github/`
- **Status:** ⚠️ Not explicitly excluded
- **Usage:** CI/CD workflows (GitHub Actions)
- **Risk:** Medium (CI/CD configs shouldn't be in user packages)
- **Recommendation:** Add explicit exclusion
- **Action:** Add to `MANIFEST.in`

#### `.tapps-agents/`
- **Status:** ⚠️ Not explicitly excluded
- **Usage:** **User runtime data** (created by users in their projects, NOT framework data)
- **Risk:** **HIGH** - Framework repo's own `.tapps-agents/` contains test data, worktrees, reports
- **Evidence:** 
  - Code creates `.tapps-agents/` in user projects at runtime
  - Framework repo's `.tapps-agents/` is development/test data
  - Should NOT be shipped
- **Recommendation:** **CRITICAL** - Add explicit exclusion
- **Action:** Add to `MANIFEST.in`

#### `.cursorignore`
- **Status:** ⚠️ Not explicitly excluded
- **Usage:** Template shipped via `tapps_agents/resources/cursor/.cursorignore`
- **Risk:** Low (repo's `.cursorignore` is project-specific)
- **Recommendation:** Add explicit exclusion
- **Action:** Add to `MANIFEST.in`

#### `.cursorrules`
- **Status:** ⚠️ Not explicitly excluded
- **Usage:** Legacy Cursor rules (optional, project-specific)
- **Risk:** Low
- **Recommendation:** Add explicit exclusion
- **Action:** Add to `MANIFEST.in`

#### `.env`
- **Status:** ⚠️ Not explicitly excluded
- **Usage:** User-specific environment variables (may contain secrets)
- **Risk:** **HIGH** - Could contain API keys, secrets
- **Recommendation:** **CRITICAL** - Add explicit exclusion
- **Action:** Add to `MANIFEST.in`

#### `.gitignore`
- **Status:** ⚠️ Not explicitly excluded
- **Usage:** Project-specific git ignore patterns
- **Risk:** Low
- **Recommendation:** Add explicit exclusion
- **Action:** Add to `MANIFEST.in`

## Runtime Usage Analysis

### `.tapps-agents/` - Critical Analysis

**Framework Behavior:**
- Framework code **creates** `.tapps-agents/` in user projects at runtime
- Framework code **reads/writes** to `.tapps-agents/` in user projects
- Framework repo's own `.tapps-agents/` contains:
  - Test data
  - Worktrees from testing
  - Reports from development
  - Cache data

**Conclusion:**
- Framework repo's `.tapps-agents/` is **development/test data**
- Should **NOT** be shipped in package
- Users will create their own `.tapps-agents/` when they run `tapps-agents init`

**Evidence from Code:**
```python
# tapps_agents/core/path_validator.py
# Detects project root by looking for .tapps-agents/
def _detect_project_root() -> Path:
    for parent in [current] + list(current.parents):
        if (parent / ".tapps-agents").exists():
            return parent

# tapps_agents/core/background_wrapper.py
# Creates .tapps-agents/reports in user projects
self.output_dir = self.project_root / ".tapps-agents" / "reports"
```

## Recommended Actions

### Priority 1: Critical Exclusions

1. **`.tapps-agents/`** - User runtime data, contains test artifacts
2. **`.env`** - May contain secrets, user-specific

### Priority 2: Standard Exclusions

3. **`.git/`** - Repository metadata
4. **`.github/`** - CI/CD workflows
5. **`.gitignore`** - Project-specific
6. **`.cursorignore`** - Project-specific (template in resources)
7. **`.cursorrules`** - Legacy, project-specific

## Implementation Plan

### Step 1: Update MANIFEST.in

Add the following exclusions to `MANIFEST.in`:

```manifest
# Exclude dot directories and files
recursive-exclude .git *
recursive-exclude .github *
recursive-exclude .tapps-agents *
global-exclude .cursorignore
global-exclude .cursorrules
global-exclude .env
global-exclude .gitignore
```

**Note:** `.env` should use `global-exclude` pattern to catch `.env`, `.env.local`, `.env.*` variants.

### Step 2: Update verify_release_package.ps1

Add new exclusions to verification script:

```powershell
$excludedPatterns = @(
    # ... existing patterns ...
    ".git\*",
    ".github\*",
    ".tapps-agents\*",
    ".cursorignore",
    ".cursorrules",
    ".env",
    ".gitignore"
)
```

### Step 3: Verify Current Exclusions

Confirm these are already excluded (they should be):
- ✅ `.bmad-core` (line 12)
- ✅ `.claude` (line 13)
- ✅ `.cursor` (line 14)
- ✅ `.ruff_cache` (line 15)
- ✅ `.pytest_cache` (line 26)
- ✅ `.mypy_cache` (line 27)
- ✅ `.venv` (line 31)

### Step 4: Test Package Verification

Run verification script to ensure new exclusions work:
```powershell
.\scripts\verify_release_package.ps1 -PackagePath dist\tapps-agents-*.whl
```

### Step 5: Update Documentation

Update `CHANGELOG.md` to document the new exclusions:
```markdown
### Changed
- Updated MANIFEST.in to exclude additional dot directories (.git, .github, .tapps-agents) and dot files (.env, .gitignore, .cursorignore, .cursorrules)
```

## Verification Checklist

After implementation, verify:

- [ ] `.git/` is not in package
- [ ] `.github/` is not in package
- [ ] `.tapps-agents/` is not in package
- [ ] `.env` is not in package
- [ ] `.gitignore` is not in package
- [ ] `.cursorignore` is not in package (template in resources is OK)
- [ ] `.cursorrules` is not in package
- [ ] All existing exclusions still work
- [ ] `verify_release_package.ps1` passes
- [ ] Package size is reasonable (no large cache directories)

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| `.tapps-agents/` shipped | High | Medium | Explicit exclusion + verification |
| `.env` with secrets shipped | Critical | Low | Explicit exclusion + .gitignore |
| `.git/` shipped | Low | Very Low | Explicit exclusion (defense in depth) |
| Breaking user projects | High | Very Low | Only exclude framework repo's dot dirs, not user's |

## Notes

1. **User Projects:** This plan only excludes dot directories from the **framework package**. User projects will create their own `.tapps-agents/`, `.cursor/`, `.claude/` when they run `tapps-agents init`.

2. **Templates:** Templates for `.cursorignore`, `.cursor/rules/`, `.claude/skills/` are correctly packaged in `tapps_agents/resources/` and copied to user projects by `init_project.py`.

3. **Runtime Data:** The framework creates `.tapps-agents/` in user projects at runtime. The framework repo's own `.tapps-agents/` is development/test data and should not be shipped.

4. **Git Behavior:** Git typically doesn't include `.git/` in packages, but explicit exclusion provides defense in depth.

## Related Files

- `MANIFEST.in` - Package inclusion/exclusion rules
- `scripts/verify_release_package.ps1` - Package verification script
- `CHANGELOG.md` - Release notes
- `tapps_agents/core/init_project.py` - Project initialization (creates user dot dirs)
- `tapps_agents/resources/` - Packaged templates for user projects

