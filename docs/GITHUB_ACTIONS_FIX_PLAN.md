# GitHub Actions Fix Plan

## Overview

This document outlines the plan to fix all failing GitHub Actions workflows for the TappsCodingAgents project.

## Current Workflow Status

### Workflows Configured

1. **CI Workflow** (`.github/workflows/ci.yml`)
   - `dependency-check`: Validates dependency consistency
   - `lint`: Ruff linting and format checking
   - `type-check`: Mypy type checking
   - `test`: Pytest with coverage (75% threshold)

2. **E2E Workflow** (`.github/workflows/e2e.yml`)
   - `pr-checks`: Fast tests for PRs (`unit or e2e_smoke`)
   - `main-branch`: Full test suite for main branch (`unit or integration or e2e_workflow`)
   - `nightly`: Scenario tests with real services (`e2e_scenario or (e2e_workflow and requires_llm) or (e2e_cli and requires_llm)`)

3. **Release Workflow** (`.github/workflows/release.yml`)
   - `validate`: Pre-release validation
   - `build`: Package building
   - `github-release`: GitHub release creation
   - `pypi-publish`: PyPI publishing

## Identified Issues

### 1. Missing `requires_llm` Marker in pytest.ini

**Issue**: The `requires_llm` marker is registered in `tests/conftest.py` but not in `pytest.ini`. With `--strict-markers` enabled, this will cause failures.

**Fix**: Add `requires_llm` marker to `pytest.ini`.

**Location**: `pytest.ini` line 50 (after `requires_context7`)

### 2. Python 3.13 Availability

**Issue**: Python 3.13 may not be stable or available in GitHub Actions yet. This could cause setup failures.

**Fix Options**:
- Option A: Use Python 3.12 (stable, widely available)
- Option B: Keep 3.13 but add fallback to 3.12
- Option C: Verify 3.13 is available and use it

**Recommendation**: Use Python 3.12 for stability, or verify 3.13 availability.

### 3. Test Coverage Threshold

**Issue**: Coverage may be below 75% threshold, causing test job to fail.

**Fix Options**:
- Option A: Lower threshold temporarily (e.g., 70%)
- Option B: Increase test coverage
- Option C: Make coverage failure non-blocking for now

**Recommendation**: Check current coverage first, then decide.

### 4. Type Checking Scope

**Issue**: Mypy is only checking `tapps_agents/core`, `tapps_agents/workflow`, and `tapps_agents/context7`. Other modules may have type errors.

**Fix**: Either expand scope or ensure all checked modules pass.

### 5. Dependency Validation Script

**Issue**: Script may fail if `tomli` is not installed or if there are dependency mismatches.

**Fix**: Ensure script handles errors gracefully and provides clear messages.

### 6. E2E Test Markers

**Issue**: E2E tests may not be properly marked, causing marker expression failures.

**Fix**: Verify all E2E tests have appropriate markers.

## Fix Plan

### Phase 1: Configuration Fixes (High Priority)

1. **Add missing `requires_llm` marker to pytest.ini**
   ```ini
   requires_llm: Tests that require LLM service (Ollama, Anthropic, or OpenAI)
   ```

2. **Verify Python version compatibility**
   - Check if Python 3.13 is available in GitHub Actions
   - If not, switch to 3.12 or add version matrix

3. **Review and fix pytest marker configuration**
   - Ensure all markers used in workflows are registered
   - Verify `--strict-markers` doesn't cause issues

### Phase 2: Test Fixes (Medium Priority)

4. **Fix test coverage issues**
   - Run coverage locally: `pytest --cov=tapps_agents --cov-report=term-missing`
   - Identify uncovered code paths
   - Either add tests or adjust threshold

5. **Fix type checking errors**
   - Run mypy locally: `mypy tapps_agents/core tapps_agents/workflow tapps_agents/context7`
   - Fix type errors or add type ignores with justification

6. **Fix linting errors**
   - Run ruff: `ruff check .`
   - Fix or ignore errors as appropriate

### Phase 3: Workflow Improvements (Low Priority)

7. **Improve error messages**
   - Add better error handling in scripts
   - Provide actionable failure messages

8. **Add workflow status badges**
   - Update README with workflow status badges

9. **Optimize workflow performance**
   - Cache dependencies
   - Parallelize jobs where possible

## Implementation Steps

### Step 1: Fix pytest.ini

Add `requires_llm` marker to `pytest.ini`:

```ini
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, with dependencies)
    e2e: End-to-end tests (slowest, full system)
    slow: Tests that take longer than 5 seconds
    requires_context7: Tests that require Context7 API key and make real API calls
    requires_llm: Tests that require LLM service (Ollama, Anthropic, or OpenAI)
    e2e_smoke: Fast, deterministic smoke E2E tests (no external services)
    e2e_workflow: Workflow execution E2E tests
    e2e_scenario: User journey scenario E2E tests
    e2e_cli: CLI command E2E tests
    e2e_slow: E2E tests that take longer than expected (can combine with other markers)
    template_type: Project template type for E2E tests (minimal, small, medium)
    behavioral_mock: Tests using behavioral mocks instead of real agents
    monitoring_config: Custom monitoring configuration for workflow tests (accepts max_seconds_without_activity, max_seconds_without_progress, max_seconds_total, check_interval_seconds, log_progress)
```

### Step 2: Verify Python Version

Check GitHub Actions Python version availability:

```yaml
# Test with both versions
strategy:
  matrix:
    python-version: ["3.12", "3.13"]
```

Or use stable version:

```yaml
python-version: "3.12"
```

### Step 3: Test Locally

Before committing, test all workflows locally:

```bash
# Linting
ruff check .
ruff format --check .

# Type checking
mypy tapps_agents/core tapps_agents/workflow tapps_agents/context7

# Tests
pytest tests/ --cov=tapps_agents --cov-report=term-missing --cov-fail-under=75

# Dependency validation
python scripts/validate_dependencies.py

# E2E markers
pytest -m "unit or e2e_smoke" -v
pytest -m "unit or integration or e2e_workflow" -v
```

### Step 4: Fix Issues Found

Address any issues found during local testing:
- Fix type errors
- Fix linting errors
- Add missing tests for coverage
- Fix marker registration issues

### Step 5: Update Workflows

Make any necessary workflow adjustments:
- Python version
- Test commands
- Error handling
- Artifact retention

## Testing Strategy

### Local Testing

1. **Run all checks locally**:
   ```bash
   # Full CI simulation
   ruff check .
   ruff format --check .
   mypy tapps_agents/core tapps_agents/workflow tapps_agents/context7
   pytest tests/ --cov=tapps_agents --cov-fail-under=75
   python scripts/validate_dependencies.py
   ```

2. **Test marker expressions**:
   ```bash
   pytest -m "unit or e2e_smoke" -v
   pytest -m "unit or integration or e2e_workflow" -v
   pytest -m "e2e_scenario or (e2e_workflow and requires_llm) or (e2e_cli and requires_llm)" -v
   ```

### GitHub Actions Testing

1. **Create test branch** with fixes
2. **Push to trigger workflows**
3. **Monitor workflow runs**
4. **Fix any remaining issues**
5. **Merge to main**

## Success Criteria

- [ ] All CI workflow jobs pass
- [ ] All E2E workflow jobs pass (or skip gracefully)
- [ ] Release workflow validates correctly
- [ ] No pytest marker warnings
- [ ] Coverage meets threshold
- [ ] Type checking passes
- [ ] Linting passes

## Rollback Plan

If fixes cause new issues:

1. Revert pytest.ini changes
2. Revert Python version changes
3. Temporarily disable strict markers
4. Lower coverage threshold if needed

## Timeline

- **Phase 1** (Configuration): 1-2 hours
- **Phase 2** (Test Fixes): 2-4 hours (depending on issues found)
- **Phase 3** (Improvements): 1-2 hours

**Total Estimated Time**: 4-8 hours

## Notes

- Python 3.13 was released in October 2024, but GitHub Actions may not have stable support yet
- Coverage threshold of 75% is reasonable but may need adjustment based on current coverage
- Strict markers help catch marker typos but require all markers to be registered
- E2E tests with `requires_llm` should skip gracefully if no LLM is available

