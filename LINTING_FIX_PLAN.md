# Plan: Fix Linting Issues Using Tapps-Agents

**Current Status:** Linting Score: 5.0/10  
**Target:** 7.0+/10 (Expected improvement: +2-3 points)  
**Priority:** High (10% weight in overall score)

---

## Overview

This plan uses tapps-agents to systematically identify and fix linting issues across the project. The approach combines automated tools (Ruff) with tapps-agents workflows and agents for comprehensive linting fixes.

## Project-Specific Considerations

### Ruff Configuration
- **Ruff is configured** in `pyproject.toml` with specific rules:
  - Selected rules: `["E", "F", "I", "UP", "B"]` (errors, pyflakes, isort, pyupgrade, bugbear)
  - Line length: 88 (matches Black)
  - Target Python: 3.13
  - Excludes: `.git`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.venv`, `build`, `dist`, `htmlcov`, `MagicMock`, `tapps_agents.egg-info`, `reports`

### How Ruff is Used in This Project
- **Reviewer Agent** uses `python -m ruff` internally (via `sys.executable`)
- **Scoring System** checks for Ruff availability using `shutil.which("ruff")`
- **Linting Score** is calculated based on Ruff diagnostics (0-10 scale)

### Command Syntax
- **Windows:** Use `python -m ruff` (Ruff may not be in PATH)
- **Linux/Mac:** Can use `ruff` directly if in PATH, or `python -m ruff` for consistency
- **Reviewer Agent:** The `lint` command works on **individual files only**, not directories

### Project Structure
- Main package: `tapps_agents/`
- Tests: `tests/`
- Reports directory: `reports/` (excluded from Ruff checks)

---

## Phase 1: Assessment & Discovery

### Step 1.1: Identify All Linting Issues

**Note:** The reviewer agent's `lint` command works on individual files. For project-wide analysis, use `analyze-project` or Ruff directly.

**Command (using Ruff directly - recommended for project-wide):**
```powershell
# Windows PowerShell - Run Ruff check and save issues
python -m ruff check . --output-format json | Out-File -FilePath reports/ruff_issues.json -Encoding utf8

# Also get a human-readable summary
python -m ruff check . | Out-File -FilePath reports/ruff_issues.txt -Encoding utf8
```

**Alternative (using reviewer analyze-project):**
```powershell
# Get comprehensive project analysis (includes linting scores)
python -m tapps_agents.cli reviewer analyze-project --format json | Out-File -FilePath reports/project_analysis.json -Encoding utf8
```

**Note:** On Windows, use `python -m ruff` instead of `ruff` directly, as Ruff may not be in PATH.

**Expected Output:**
- List of all linting violations
- File-by-file breakdown
- Issue counts by severity (error, warning, fatal)
- Auto-fixable vs manual fixes

### Step 1.2: Analyze Linting Score Breakdown

**Command:**
```bash
# Get detailed scoring that includes linting
python -m tapps_agents.cli reviewer analyze-project --format json > reports/project_analysis.json
```

**What to Review:**
- Current linting score: 5.0/10
- Files with most linting issues
- Types of violations (imports, style, complexity, etc.)
- Priority files (high-impact modules)

---

## Phase 2: Automated Fixes (Ruff Auto-Fix)

### Step 2.1: Apply Auto-Fixable Issues

**Command (Windows PowerShell):**
```powershell
# Ruff can automatically fix many issues
python -m ruff check . --fix

# Verify fixes were applied
python -m ruff check . --output-format json | Out-File -FilePath reports/ruff_after_autofix.json -Encoding utf8
```

**Command (Linux/Mac):**
```bash
# Ruff can automatically fix many issues
ruff check . --fix

# Verify fixes were applied
ruff check . --output-format json > reports/ruff_after_autofix.json
```

**Note:** The project uses `python -m ruff` to ensure Ruff runs from the correct environment.

**What Gets Fixed Automatically:**
- Import sorting and organization
- Unused imports removal
- Simple style violations (whitespace, quotes, etc.)
- Basic formatting issues

**Note:** Review changes in git before committing to ensure no unintended modifications.

### Step 2.2: Verify Auto-Fixes

**Command:**
```bash
# Re-score to see improvement
python -m tapps_agents.cli reviewer analyze-project --format json
```

**Expected Result:**
- Linting score should improve (target: 6.0-7.0/10)
- Reduced issue count in reports

---

## Phase 3: Manual Fixes Using Tapps-Agents

### Step 3.1: Identify Files Needing Manual Fixes

**Process:**
1. Review `reports/ruff_issues.json` for remaining issues
2. Prioritize files by:
   - High-impact modules (CLI, core agents, workflow)
   - Number of remaining issues
   - Severity of issues

**Priority Files (likely candidates):**
- `tapps_agents/cli.py` (main CLI interface)
- `tapps_agents/core/*.py` (core functionality)
- `tapps_agents/agents/*/agent.py` (agent implementations)

### Step 3.2: Use Reviewer Agent to Analyze Individual Files

**For each priority file:**

```powershell
# Get detailed linting analysis for a specific file
python -m tapps_agents.cli reviewer lint tapps_agents/cli.py --format json
```

**Note:** The reviewer agent's `lint` command works on individual files only. It uses `python -m ruff` internally, which matches the project's setup.

**Review the output:**
- Specific violations
- Line numbers
- Issue descriptions
- Severity levels

### Step 3.3: Use Improver Agent to Fix Issues

**Option A: Use Quality Workflow (Recommended)**

The quality workflow automatically:
1. Reviews code (identifies issues)
2. Improves code (fixes issues)
3. Re-reviews (validates fixes)
4. Tests (ensures nothing broke)

**Command:**
```bash
# Run quality improvement workflow on specific file
python -m tapps_agents.cli workflow quality
```

**Note:** The workflow will prompt for target file or can work on the entire project.

**Option B: Use Improver Agent Directly**

```bash
# Improve quality of a specific file
python -m tapps_agents.cli improver improve-quality tapps_agents/cli.py
```

**What the Improver Agent Does:**
- Follows PEP 8 style guide
- Fixes code structure issues
- Improves naming conventions
- Adds appropriate type hints
- Reduces complexity

**Option C: Use Maintenance Workflow**

For broader refactoring that includes linting fixes:

```bash
# Run maintenance workflow
python -m tapps_agents.cli workflow fix
```

**What it does:**
1. Debugger analyzes issues
2. Improver refactors (includes linting fixes)
3. Reviewer validates
4. Tester ensures tests pass
5. Documenter updates docs

---

## Phase 4: Batch Processing Multiple Files

### Step 4.1: Create Custom Script for Batch Fixes

**Create:** `fix_linting_batch.py`

```python
"""
Batch fix linting issues using tapps-agents
"""
import asyncio
import json
from pathlib import Path
from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tapps_agents.agents.improver.agent import ImproverAgent

async def fix_file_linting(file_path: Path):
    """Fix linting issues for a single file."""
    reviewer = ReviewerAgent()
    improver = ImproverAgent()
    
    await reviewer.activate()
    await improver.activate()
    
    # Get linting issues
    lint_result = await reviewer.run("lint", file=str(file_path))
    
    if lint_result.get("issue_count", 0) > 0:
        print(f"Fixing {file_path}: {lint_result['issue_count']} issues")
        
        # Improve code quality (includes linting fixes)
        improve_result = await improver.run(
            "improve-quality",
            file_path=str(file_path)
        )
        
        # Re-check linting
        recheck = await reviewer.run("lint", file=str(file_path))
        print(f"After fix: {recheck.get('issue_count', 0)} issues")
        
        return improve_result
    else:
        print(f"{file_path}: No issues")
        return None

async def main():
    # Get list of Python files with linting issues
    # (from ruff_issues.json or analyze-project output)
    
    # Example: Fix all files in tapps_agents/
    project_root = Path("tapps_agents")
    python_files = list(project_root.rglob("*.py"))
    
    for file_path in python_files:
        try:
            await fix_file_linting(file_path)
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Usage:**
```bash
python fix_linting_batch.py
```

### Step 4.2: Use Reviewer Report for Comprehensive Analysis

**Command (Windows PowerShell):**
```powershell
# Generate comprehensive quality report (includes linting)
python -m tapps_agents.cli reviewer report . json markdown html --output-dir reports/quality
```

**Command (Linux/Mac):**
```bash
# Generate comprehensive quality report (includes linting)
python -m tapps_agents.cli reviewer report . json markdown html --output-dir reports/quality
```

**Output:**
- `reports/quality/report.json` - Machine-readable
- `reports/quality/report.md` - Human-readable markdown
- `reports/quality/report.html` - Visual dashboard

**Use the report to:**
- Identify files with most issues
- Track progress
- Prioritize fixes

---

## Phase 5: Verification & Validation

### Step 5.1: Re-run Project Analysis

**Command:**
```bash
# Get updated scores
python -m tapps_agents.cli reviewer analyze-project --format json
```

**Check:**
- Linting score improved (target: 7.0+/10)
- Overall score improved
- No regressions in other metrics

### Step 5.2: Run Tests to Ensure Nothing Broke

**Command:**
```bash
# Run test suite
pytest tests/

# Or specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Step 5.3: Final Linting Check

**Command (Windows PowerShell):**
```powershell
# Final comprehensive check
python -m ruff check . --output-format json | Out-File -FilePath reports/ruff_final.json -Encoding utf8

# Should show minimal or no issues
python -m ruff check .
```

**Command (Linux/Mac):**
```bash
# Final comprehensive check
ruff check . --output-format json > reports/ruff_final.json

# Should show minimal or no issues
ruff check .
```

---

## Phase 6: Continuous Improvement

### Step 6.1: Set Up Pre-commit Hooks (Optional)

**Create:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

**Install:**
```bash
pip install pre-commit
pre-commit install
```

### Step 6.2: Integrate with CI/CD

Add linting checks to CI pipeline:
```yaml
# Example GitHub Actions
- name: Run Ruff
  run: ruff check .
```

---

## Recommended Execution Order

### Quick Path (Automated):
1. **Phase 2** - Run `python -m ruff check . --fix` (auto-fixes)
2. **Phase 3.3 Option A** - Run `workflow quality` on remaining files
3. **Phase 5** - Verify improvements

**Windows PowerShell:**
```powershell
python -m ruff check . --fix
python -m tapps_agents.cli workflow quality
python -m tapps_agents.cli reviewer analyze-project
```

### Comprehensive Path (Full Automation):
1. **Phase 1** - Assessment
2. **Phase 2** - Auto-fixes
3. **Phase 4** - Batch processing
4. **Phase 5** - Verification

### Manual Path (Selective):
1. **Phase 1** - Identify issues
2. **Phase 3.2** - Review specific files
3. **Phase 3.3 Option B** - Fix files individually
4. **Phase 5** - Verify

---

## Expected Outcomes

### Metrics Improvement:
- **Linting Score:** 5.0/10 → 7.0+/10 (+2-3 points)
- **Overall Score:** 74.97/100 → 77-78/100 (+2-3 points)
- **Issue Count:** Reduced by 60-80%

### Code Quality:
- ✅ All files follow PEP 8 style guide
- ✅ Consistent import organization
- ✅ Proper type hints where applicable
- ✅ Reduced code complexity
- ✅ Better maintainability

---

## Troubleshooting

### Issue: Ruff auto-fix breaks code
**Solution:** Review changes in git diff before committing. Revert if needed.

### Issue: `ruff` command not found
**Solution:** Use `python -m ruff` instead. The project is configured to use Ruff via Python module, which ensures it runs from the correct environment.

### Issue: Improver agent makes unwanted changes
**Solution:** Use git worktrees (workflow handles this automatically) or review changes carefully.

### Issue: Linting score doesn't improve
**Solution:** 
- Check if Ruff config is correct
- Verify all Python files are being checked
- Review scoring algorithm in `tapps_agents/agents/reviewer/scoring.py`

---

## Next Steps After Linting Fixes

Once linting is fixed:
1. **Type Checking** - Fix mypy issues (current: 5.0/10)
2. **Test Coverage** - Increase coverage (current: 3.61/10)
3. **Maintainability** - Further improvements (current: 6.02/10)

---

## Commands Quick Reference

### Windows PowerShell

```powershell
# Assessment
python -m tapps_agents.cli reviewer lint <file>
python -m tapps_agents.cli reviewer analyze-project
python -m ruff check . --output-format json | Out-File -FilePath reports/ruff_issues.json -Encoding utf8

# Auto-fixes
python -m ruff check . --fix

# Manual fixes (workflows)
python -m tapps_agents.cli workflow quality
python -m tapps_agents.cli workflow fix

# Manual fixes (agents)
python -m tapps_agents.cli improver improve-quality <file>
python -m tapps_agents.cli reviewer lint <file>

# Reports
python -m tapps_agents.cli reviewer report . json markdown html --output-dir reports/quality

# Verification
python -m tapps_agents.cli reviewer analyze-project
python -m ruff check .
pytest tests/
```

### Linux/Mac (Bash)

```bash
# Assessment
python -m tapps_agents.cli reviewer lint <file>
python -m tapps_agents.cli reviewer analyze-project
ruff check . --output-format json > reports/ruff_issues.json

# Auto-fixes
ruff check . --fix

# Manual fixes (workflows)
python -m tapps_agents.cli workflow quality
python -m tapps_agents.cli workflow fix

# Manual fixes (agents)
python -m tapps_agents.cli improver improve-quality <file>
python -m tapps_agents.cli reviewer lint <file>

# Reports
python -m tapps_agents.cli reviewer report . json markdown html --output-dir reports/quality

# Verification
python -m tapps_agents.cli reviewer analyze-project
ruff check .
pytest tests/
```

**Note:** This project uses `python -m ruff` to ensure Ruff runs from the correct Python environment. The reviewer agent also uses this approach internally.

---

**Created:** 2025-01-13  
**Status:** Ready for Execution  
**Estimated Time:** 2-4 hours (depending on number of issues)

