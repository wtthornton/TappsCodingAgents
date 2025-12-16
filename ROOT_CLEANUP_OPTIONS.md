# Root Directory Cleanup Options

## Execution Status

**Status:** ✅ COMPLETED  
**Started:** 2025-12-16  
**Completed:** 2025-12-16  
**Option Selected:** Option 4 - Hybrid Approach

### Progress Tracker

- [x] Step 1: Update .gitignore with coverage patterns ✅
  - Added `.coverage.*` pattern for coverage artifacts with process IDs
  - Added `test-results.xml` and `*.test-results.xml` patterns
  - Cleaned up 13 existing `.coverage.Mini*` files from root directory
  
- [x] Step 2: Update .cursorignore with root file exclusions ✅
  - Added patterns to prevent Cursor from indexing test files, scripts, and temporary docs in root
  
- [x] Step 3: Create target directories ✅
  - Created `docs/status/` for progress/status reports
  - Created `docs/guides/` for quick reference guides
  - Created `docs/releases/` for release notes
  - Created `docs/implementation/` for implementation documentation
  
- [x] Step 4: Move test files to tests/ ✅
  - Moved 7 test files: `test_context.py`, `test_execute_startup.py`, `test_ollama_connection.py`, 
    `test_refactor.py`, `test_simple.py`, `test_single_file_refactor.py`, `test_streaming.py`
  
- [x] Step 5: Move scripts to scripts/ ✅
  - Moved 3 Python scripts: `analyze_and_fix.py`, `analyze_project.py`, `execute_improvements.py`
  - Moved 3 PowerShell scripts: `create_github_release.ps1`, `setup_experts.ps1`, `upload_to_pypi.ps1`
  
- [x] Step 6: Move example files to examples/ ✅
  - Moved `example_bug.py` to `examples/`
  
- [x] Step 7: Move documentation files to docs/ subdirectories ✅
  - Moved ~35 status/progress reports to `docs/status/`
  - Moved 6 quick reference guides to `docs/guides/`
  - Moved 3 release notes to `docs/releases/`
  - Moved 1 implementation doc to `docs/implementation/`
  - Note: Some files were untracked by git, moved using regular file operations
  
- [x] Step 8: Create validation script ✅
  - Created `scripts/validate_root_structure.py`
  - Script validates root directory structure and reports violations
  - Tested and confirmed root is now clean
  
- [x] Step 9: Final verification and status update ✅
  - Validation script confirms root directory structure is valid
  - All files moved successfully
  - Preventive measures in place

### Summary

**Files Moved:**
- 7 test files → `tests/`
- 6 scripts (3 Python + 3 PowerShell) → `scripts/`
- 1 example file → `examples/`
- ~45 documentation files → `docs/` subdirectories

**Files Updated:**
- `.gitignore` - Added coverage and test artifact patterns
- `.cursorignore` - Added root file exclusion patterns

**New Files Created:**
- `scripts/validate_root_structure.py` - Root structure validation script
- `docs/status/`, `docs/guides/`, `docs/releases/`, `docs/implementation/` directories

**Next Steps:**
- This cleanup plan file (`ROOT_CLEANUP_OPTIONS.md`) should be moved to `docs/` after review
- Consider adding validation script to CI/CD pipeline
- Update README.md with new structure information

---

## Research Summary: Python Project Structure Standards

Based on research of Python project structure best practices (PEP 517/518, pyproject.toml standards, and industry conventions), a well-organized Python project root should contain:

### Essential Root Files (Keep in Root)
- `README.md` - Project overview and quick start
- `LICENSE` - License file
- `pyproject.toml` - Modern Python project configuration (PEP 517/518)
- `setup.py` - Legacy build support (optional, can be removed if using pyproject.toml only)
- `requirements.txt` - Dependency list (optional if using pyproject.toml)
- `.gitignore` - Version control exclusions
- `pytest.ini` - Test configuration (optional, can be in pyproject.toml)
- `MANIFEST.in` - Package data inclusion (if needed)
- `SECURITY.md` - Security policy (GitHub standard)
- `CONTRIBUTING.md` - Contribution guidelines (GitHub standard)
- `CHANGELOG.md` - Version history (Keep a Changelog standard)

### Standard Directory Structure
- `src/` or `package_name/` - Source code (your project uses `tapps_agents/`)
- `tests/` - Test suite
- `docs/` - Documentation
- `scripts/` - Utility scripts
- `examples/` - Example code/configurations
- `build/`, `dist/`, `*.egg-info/` - Build artifacts (gitignored)

## Current Root Directory Analysis

### Files That Should Stay in Root ✅
1. `README.md` - Main project documentation
2. `LICENSE` - License file
3. `pyproject.toml` - Project configuration
4. `setup.py` - Build configuration (legacy support)
5. `requirements.txt` - Dependencies
6. `pytest.ini` - Test configuration
7. `MANIFEST.in` - Package manifest
8. `.gitignore` - Git exclusions
9. `SECURITY.md` - Security policy
10. `CONTRIBUTING.md` - Contribution guidelines
11. `CHANGELOG.md` - Version history

### Files/Directories to Reorganize

#### Category 1: Documentation Files (Move to `docs/`)
**Status/Progress Reports:**
- `AGENT_TEST_EXECUTION_GUIDE_UPDATE.md`
- `AUTO_MODE_QUICK_REFERENCE.md`
- `CONTEXT7_INTEGRATION_ARCHITECTURE.md`
- `CONTEXT7_REAL_INTEGRATION_TESTS_SUMMARY.md`
- `CURSOR_INTEGRATION_ANALYSIS.md`
- `CURSOR_RULES_IMPLEMENTATION.md`
- `CURSOR_RULES_SKILLS_UPDATE.md`
- `DOCUMENTATION_UPDATES_TEST_PERFORMANCE.md`
- `E2E_TEST_NEXT_STEPS.md`
- `E2E_TEST_RECOMMENDATIONS.md`
- `E2E_TEST_REVIEW_SUMMARY.md`
- `E2E_TEST_REVIEW.md`
- `ENHANCEMENTS_NOT_COMPLETED.md`
- `INSTALLATION_ANALYSIS.md`
- `INSTALLATION_SUMMARY.md`
- `LINTING_FIX_PLAN.md`
- `LLM_TESTS_OPTIMIZATION_SUMMARY.md`
- `NEXT_STEPS_AND_RECOMMENDATIONS.md`
- `OPTIONAL_STEPS_COMPLETED.md`
- `PHASE_2_EXECUTION_SUMMARY.md`
- `PRODUCTION_READINESS_PLAN.md`
- `PRODUCTION_READINESS_QUICK_START.md`
- `QUALITY_COMPLEXITY_MARATHON_TASKS.md`
- `QUALITY_IMPROVEMENT_PROGRESS.md`
- `QUALITY_IMPROVEMENT_ROADMAP.md`
- `REAL_INTEGRATION_TESTS_SUMMARY.md`
- `RELEASE_OPTIONS.md`
- `REQUIREMENTS_AUTO_MODE_TIMELINE.md`
- `RUN_UNIT_TESTS_REPORT.md`
- `TEST_COVERAGE_ANALYSIS.md`
- `TEST_IMPROVEMENTS_SUMMARY.md`
- `TEST_PERFORMANCE_ANALYSIS.md`
- `TEST_PERFORMANCE_FIXES_APPLIED.md`
- `TWINE_COMMAND_DIAGNOSIS.md`
- `UNIT_TEST_REVIEW_AND_PLAN_PRAGMATIC.md`
- `UNIT_TEST_REVIEW_AND_PLAN.md`
- `UNIT_TEST_REVIEW_SUMMARY.md`

**Quick Reference Guides:**
- `QUICK_START_WORKFLOWS.md`
- `QUICK_START.md`
- `QUICK_UPLOAD.md`
- `UPLOAD_SIMPLE.md`
- `twine-upload-help.txt`
- `twine-upload-quick-reference.md`

**Release Notes:**
- `RELEASE_NOTES_v1.6.1.md`
- `RELEASE_NOTES_v2.0.0.md`
- `RELEASE_NOTES_v2.0.1.md`

**Implementation/Architecture Docs:**
- `README_IMPLEMENTATION.md`
- `PYPI_UPLOAD_GUIDE.md`

**Setup/Installation Guides:**
- `SETUP_GUIDE.md`

**Debug Reports:**
- `debug-report.md`

**Cleanup Plan (Move after cleanup):**
- `ROOT_CLEANUP_OPTIONS.md` - This file itself should be moved to `docs/` after cleanup is complete

#### Category 2: Test Files (Move to `tests/`)
- `test_context.py`
- `test_execute_startup.py`
- `test_ollama_connection.py`
- `test_refactor.py`
- `test_simple.py`
- `test_single_file_refactor.py`
- `test_streaming.py`
- `test-results.xml` (should be gitignored, but move if tracked)

#### Category 3: Scripts (Move to `scripts/`)
- `analyze_and_fix.py`
- `analyze_project.py`
- `execute_improvements.py`
- `create_github_release.ps1` (PowerShell script)
- `setup_experts.ps1` (PowerShell script)
- `upload_to_pypi.ps1` (PowerShell script)

#### Category 4: Example Files (Move to `examples/`)
- `example_bug.py`

#### Category 5: Directories to Review
- `billstest/` - Appears to be test-related, consider moving to `tests/` or `examples/`
- `fixed-code/` - Already gitignored, but consider if it should exist
- `MagicMock/` - Already gitignored, test artifact
- `implementation/` - Contains implementation docs, could move to `docs/implementation/`
- `agents/` - Legacy location for Cursor Skills, consider documenting or removing if unused

## Cleanup Options

### Option 1: Minimal Cleanup (Recommended for Quick Win)
**Goal:** Move only the most obvious clutter without major restructuring.

**Actions:**
1. Move all `test_*.py` files to `tests/`
2. Move all `*.md` files (except essential ones) to `docs/status/` or `docs/archive/`
3. Move utility scripts to `scripts/`
4. Move `example_bug.py` to `examples/`

**Result:** Cleaner root, minimal disruption, easy to reverse.

**Files to Move:**
- ~52 markdown files → `docs/status/` or `docs/guides/` (includes ROOT_CLEANUP_OPTIONS.md after cleanup)
- 7 test files → `tests/`
- 1 test result file → `tests/` or gitignore
- 6 scripts (3 Python + 3 PowerShell) → `scripts/`
- 1 example file → `examples/`

**Files to Gitignore (if not already):**
- `.coverage.*` files (coverage artifacts with process IDs)
- `test-results.xml` (if not already ignored)

### Option 2: Comprehensive Cleanup (Recommended for Long-term)
**Goal:** Full reorganization following Python standards.

**Actions:**
1. **Documentation Organization:**
   - Create `docs/status/` for progress/status reports
   - Create `docs/guides/` for quick reference guides
   - Create `docs/releases/` for release notes
   - Create `docs/implementation/` for implementation docs
   - Move all non-essential markdown files accordingly

2. **Test Organization:**
   - Move all `test_*.py` files to `tests/`
   - Consider creating `tests/integration/` or `tests/unit/` if needed

3. **Script Organization:**
   - Move all Python scripts to `scripts/`
   - Keep PowerShell scripts in `scripts/` (or create `scripts/powershell/`)

4. **Example Organization:**
   - Move `example_bug.py` to `examples/`

5. **Directory Cleanup:**
   - Review `billstest/` - move to `tests/` or `examples/` if appropriate
   - Review `implementation/` - move to `docs/implementation/` if it's documentation
   - Document or remove `agents/` if it's legacy

**Result:** Professional structure, easier navigation, follows standards.

### Option 3: Archive-Based Cleanup (Recommended for Historical Projects)
**Goal:** Preserve history while cleaning up active workspace.

**Actions:**
1. Create `docs/archive/` directory
2. Move all status/progress reports to `docs/archive/status/`
3. Move old release notes to `docs/archive/releases/`
4. Move implementation docs to `docs/archive/implementation/`
5. Keep only current/active documentation in root or `docs/`
6. Move test files and scripts as in Option 1

**Result:** Clean active workspace, preserved history, easy to reference old docs.

### Option 4: Hybrid Approach (Recommended for Active Development)
**Goal:** Balance between cleanup and active development needs.

**Actions:**
1. **Immediate Cleanup:**
   - Move test files to `tests/`
   - Move scripts to `scripts/`
   - Move examples to `examples/`

2. **Documentation Consolidation:**
   - Create `docs/status/` and move all status reports
   - Create `docs/guides/` for quick references
   - Keep only essential docs in root (README, CHANGELOG, CONTRIBUTING, SECURITY)

3. **Active Development:**
   - Keep `QUICK_START.md` in root (or create symlink) if frequently accessed
   - Document the new structure in README

**Result:** Clean structure with easy access to frequently used docs.

## Recommended Structure After Cleanup

```
TappsCodingAgents/
├── README.md                    # Main documentation
├── LICENSE                      # License
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # Contribution guidelines
├── SECURITY.md                  # Security policy
├── pyproject.toml               # Project configuration
├── setup.py                     # Build configuration
├── requirements.txt             # Dependencies
├── pytest.ini                   # Test configuration
├── MANIFEST.in                  # Package manifest
├── .gitignore                   # Git exclusions
│
├── tapps_agents/                # Source code
├── tests/                       # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                        # Documentation
│   ├── status/                  # Status/progress reports
│   ├── guides/                  # Quick reference guides
│   ├── releases/                # Release notes
│   ├── implementation/          # Implementation docs
│   └── ...                      # Other existing docs
│
├── scripts/                     # Utility scripts
│   ├── analyze_and_fix.py
│   ├── analyze_project.py
│   ├── execute_improvements.py
│   └── *.ps1                    # PowerShell scripts
│
├── examples/                     # Examples
│   ├── experts/
│   └── example_bug.py
│
├── workflows/                    # YAML workflows
├── requirements/                # Specifications
├── templates/                   # Templates
│
└── [build artifacts - gitignored]
    ├── build/
    ├── dist/
    ├── htmlcov/
    └── *.egg-info/
```

## Implementation Steps

### Step 1: Create Target Directories
```bash
mkdir -p docs/status docs/guides docs/releases docs/implementation
```

### Step 2: Move Files (Choose your option)
Use git mv to preserve history:
```bash
# Test files
git mv test_*.py tests/

# Scripts
git mv analyze_*.py scripts/
git mv execute_improvements.py scripts/
git mv *.ps1 scripts/

# Examples
git mv example_bug.py examples/

# Documentation (batch move)
git mv *STATUS*.md docs/status/ 2>/dev/null || true
git mv *REVIEW*.md docs/status/ 2>/dev/null || true
git mv *SUMMARY*.md docs/status/ 2>/dev/null || true
# ... etc
```

### Step 3: Update References
- Update `README.md` to reflect new structure
- Update any hardcoded paths in scripts
- Update documentation links
- Check `pytest.ini` if test paths changed

### Step 4: Update .gitignore
Ensure build artifacts and temporary directories are properly ignored:
- Add `.coverage.*` pattern for coverage artifacts
- Ensure `test-results.xml` is ignored
- Add patterns for temporary documentation files

### Step 5: Update .cursorignore
Update `.cursorignore` to prevent Cursor from indexing misplaced files:
- Add patterns for test files, scripts, and temporary docs in root
- This prevents Cursor AI from suggesting or referencing these files

## Risk Assessment

### Low Risk
- Moving test files (pytest.ini already points to `tests/`)
- Moving scripts (if not imported elsewhere)
- Moving examples

### Medium Risk
- Moving documentation (need to update links)
- Moving status reports (if referenced in other docs)

### High Risk
- Moving `implementation/` directory (if referenced in code/docs)
- Removing `agents/` directory (if still in use)

## Recommendations

1. **Start with Option 1 (Minimal Cleanup)** - Quick win, low risk
2. **Gradually move to Option 4 (Hybrid)** - Best balance
3. **Use git mv** - Preserves file history
4. **Update README.md** - Document new structure
5. **Test after moves** - Ensure pytest and scripts still work
6. **Create redirects** - If files are linked externally, consider symlinks or redirect docs

## Preventive Measures: Keeping Root Clean Going Forward

To prevent the root directory from getting messy again, implement the following measures:

### 1. Enhanced .gitignore Rules

Add to `.gitignore` to prevent common artifacts from being committed:

```gitignore
# Test artifacts
test-results.xml
*.test-results.xml
.pytest_cache/
.coverage
.coverage.*
coverage.xml
htmlcov/

# Temporary documentation
*-report.md
*-summary.md
*-analysis.md
debug-*.md
temp-*.md

# Build and distribution
build/
dist/
*.egg-info/
.eggs/

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Project-specific temporary files
fixed-code/
MagicMock/
reports/
```

### 2. Pre-commit Hook: Root Directory Validation

Create `.git/hooks/pre-commit` (or use pre-commit framework) to validate root structure:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for test files in root
if git diff --cached --name-only --diff-filter=A | grep -q "^test_.*\.py$"; then
    echo "❌ ERROR: Test files should be in tests/ directory, not root"
    echo "   Move test files to tests/ before committing"
    exit 1
fi

# Check for new markdown files in root (except allowed ones)
ALLOWED_MD_FILES="README.md CHANGELOG.md CONTRIBUTING.md SECURITY.md"
for file in $(git diff --cached --name-only --diff-filter=A | grep "\.md$"); do
    basename_file=$(basename "$file")
    if [[ "$file" == "$basename_file" ]] && [[ ! "$ALLOWED_MD_FILES" =~ "$basename_file" ]]; then
        echo "⚠️  WARNING: New markdown file in root: $file"
        echo "   Consider moving to docs/ directory"
        echo "   Allowed root markdown files: $ALLOWED_MD_FILES"
        # Uncomment to make this an error:
        # exit 1
    fi
done

# Check for Python scripts in root (except setup.py)
for file in $(git diff --cached --name-only --diff-filter=A | grep "\.py$"); do
    basename_file=$(basename "$file")
    if [[ "$file" == "$basename_file" ]] && [[ "$basename_file" != "setup.py" ]]; then
        echo "⚠️  WARNING: New Python script in root: $file"
        echo "   Consider moving to scripts/ directory"
        # Uncomment to make this an error:
        # exit 1
    fi
done

exit 0
```

**Alternative: Use pre-commit Framework**

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: check-root-structure
        name: Check root directory structure
        entry: bash scripts/validate_root_structure.sh
        language: system
        pass_filenames: false
        always_run: true
```

### 3. Structure Validation Script

Create `scripts/validate_root_structure.py`:

```python
#!/usr/bin/env python3
"""
Validate that root directory follows project structure standards.
Run this in CI/CD or as a pre-commit hook.
"""

import sys
from pathlib import Path

# Allowed files in root
ALLOWED_ROOT_FILES = {
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "pyproject.toml",
    "setup.py",
    "requirements.txt",
    "pytest.ini",
    "MANIFEST.in",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".github",  # Directory
}

# Patterns that should NOT be in root
FORBIDDEN_PATTERNS = [
    "test_*.py",  # Test files
    "*-report.md",  # Report files
    "*-summary.md",  # Summary files
    "*-analysis.md",  # Analysis files
    "debug-*.md",  # Debug files
]


def validate_root_structure(project_root: Path) -> tuple[bool, list[str]]:
    """Validate root directory structure."""
    errors = []
    warnings = []
    
    root_files = {f.name for f in project_root.iterdir() if f.is_file()}
    root_dirs = {f.name for f in project_root.iterdir() if f.is_dir()}
    
    # Check for test files
    test_files = [f for f in root_files if f.startswith("test_") and f.endswith(".py")]
    if test_files:
        errors.append(f"Test files in root (move to tests/): {', '.join(test_files)}")
    
    # Check for forbidden markdown patterns
    for pattern in FORBIDDEN_PATTERNS:
        matching = [f for f in root_files if pattern.replace("*", "") in f]
        if matching:
            warnings.append(f"Files matching '{pattern}' in root: {', '.join(matching)}")
    
    # Check for Python scripts (except setup.py)
    python_scripts = [f for f in root_files if f.endswith(".py") and f != "setup.py"]
    if python_scripts:
        warnings.append(f"Python scripts in root (consider moving to scripts/): {', '.join(python_scripts)}")
    
    # Check for PowerShell scripts
    ps_scripts = [f for f in root_files if f.endswith(".ps1")]
    if ps_scripts:
        warnings.append(f"PowerShell scripts in root (consider moving to scripts/): {', '.join(ps_scripts)}")
    
    return len(errors) == 0, errors + warnings


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    is_valid, messages = validate_root_structure(project_root)
    
    if messages:
        for msg in messages:
            if "ERROR" in msg or "error" in msg.lower():
                print(f"❌ {msg}", file=sys.stderr)
            else:
                print(f"⚠️  {msg}", file=sys.stderr)
    
    sys.exit(0 if is_valid else 1)
```

### 4. CI/CD Validation

Add to GitHub Actions workflow (`.github/workflows/ci.yml`):

```yaml
- name: Validate root directory structure
  run: |
    python scripts/validate_root_structure.py
  continue-on-error: false
```

### 5. Documentation Standards

Add to `CONTRIBUTING.md`:

```markdown
## Project Structure Guidelines

### Root Directory
The root directory should only contain:
- Essential configuration files (pyproject.toml, setup.py, etc.)
- Core documentation (README.md, CHANGELOG.md, CONTRIBUTING.md, SECURITY.md)
- License file (LICENSE)

### Where to Put New Files

- **Test files**: Always in `tests/` directory
  - Unit tests: `tests/unit/`
  - Integration tests: `tests/integration/`
  - E2E tests: `tests/e2e/`

- **Documentation**: In `docs/` directory
  - Status reports: `docs/status/`
  - Guides: `docs/guides/`
  - Release notes: `docs/releases/`
  - Implementation docs: `docs/implementation/`

- **Scripts**: In `scripts/` directory
  - Python scripts: `scripts/`
  - PowerShell scripts: `scripts/` (or `scripts/powershell/`)

- **Examples**: In `examples/` directory

### Before Committing
Run the structure validation:
```bash
python scripts/validate_root_structure.py
```
```

### 6. Automated Cleanup Script

Create `scripts/cleanup_root.py` for periodic maintenance:

```python
#!/usr/bin/env python3
"""
Automated root directory cleanup script.
Moves misplaced files to appropriate directories.
"""

import shutil
from pathlib import Path

# File categorization rules
FILE_RULES = {
    "test_*.py": "tests/",
    "*-report.md": "docs/status/",
    "*-summary.md": "docs/status/",
    "*-analysis.md": "docs/status/",
    "RELEASE_NOTES_*.md": "docs/releases/",
    "QUICK_*.md": "docs/guides/",
    "*.ps1": "scripts/",
}

def cleanup_root(project_root: Path, dry_run: bool = True):
    """Clean up root directory."""
    # Implementation here
    pass
```

### 7. Developer Onboarding

Update `README.md` with structure guidelines:

```markdown
## Project Structure

This project follows Python project structure standards. Key directories:

- `tapps_agents/` - Source code
- `tests/` - Test suite
- `docs/` - Documentation
- `scripts/` - Utility scripts
- `examples/` - Example code

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed structure guidelines.
```

### 8. Enhanced .cursorignore File

Update `.cursorignore` to prevent Cursor from indexing or suggesting files in root that shouldn't be there:

```gitignore
# Prevent Cursor from indexing test files in root
/test_*.py

# Prevent Cursor from indexing temporary documentation in root
/*-report.md
/*-summary.md
/*-analysis.md
/debug-*.md
/temp-*.md

# Prevent Cursor from indexing scripts in root (they should be in scripts/)
/analyze_*.py
/execute_*.py
/*.ps1

# Prevent Cursor from indexing example files in root
/example_*.py
```

This helps prevent Cursor AI from suggesting or referencing misplaced files during development.

### 9. Regular Maintenance Checklist

Add to project maintenance routine:

- [ ] Run `scripts/validate_root_structure.py` monthly
- [ ] Review root directory quarterly
- [ ] Archive old status reports to `docs/archive/`
- [ ] Update `.gitignore` as new artifact types appear
- [ ] Update `.cursorignore` to exclude new patterns
- [ ] Review and update structure validation rules
- [ ] Check for new coverage files (`.coverage.*`) and ensure they're gitignored

## Implementation Priority

1. **Immediate (High Priority)**
   - Update `.gitignore` with new patterns (especially `.coverage.*`)
   - Update `.cursorignore` with root file exclusions
   - Create `scripts/validate_root_structure.py`
   - Add validation to CI/CD

2. **Short-term (Medium Priority)**
   - Add pre-commit hook
   - Update `CONTRIBUTING.md` with guidelines
   - Update `README.md` with structure info
   - Move files according to chosen cleanup option

3. **Long-term (Low Priority)**
   - Create automated cleanup script
   - Set up periodic maintenance reminders
   - Document in developer onboarding
   - Archive old documentation files

## Additional Considerations

### Files Not Yet Categorized

**Coverage Artifacts:**
- `.coverage.*` files (multiple files with process IDs) - Should be gitignored, not moved

**Existing .cursorignore:**
- Already exists in root - Should be updated with new patterns to prevent Cursor from indexing misplaced files

**ROOT_CLEANUP_OPTIONS.md:**
- This cleanup plan file itself should be moved to `docs/` after cleanup is complete
- Consider renaming to `docs/ROOT_CLEANUP_PLAN.md` or `docs/maintenance/ROOT_CLEANUP.md`

### Verification Checklist

Before finalizing cleanup:
- [ ] Check that pytest.ini doesn't reference root test files
- [ ] Verify no imports reference root test files
- [ ] Check that scripts don't have hardcoded paths to root files
- [ ] Ensure CI/CD workflows don't reference root test files
- [ ] Verify documentation links are updated
- [ ] Test that all moved scripts still work from new location
- [ ] Run full test suite after moves
- [ ] Update any external documentation that references moved files

## Next Steps

1. Review this document and choose an option
2. Create a backup branch: `git checkout -b cleanup/root-reorganization`
3. Execute the chosen option
4. **Implement preventive measures** (update .gitignore, update .cursorignore, create validation script)
5. Test the project (run tests, check scripts)
6. Update documentation references
7. Move `ROOT_CLEANUP_OPTIONS.md` to `docs/` (or archive it)
8. Commit changes with clear message
9. Create PR for review

