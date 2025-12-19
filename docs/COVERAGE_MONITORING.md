# Coverage Monitoring Guide

## Overview

This project maintains a **75% minimum code coverage threshold** enforced in CI/CD. This document describes how to monitor, track, and maintain coverage.

## Coverage Thresholds

- **Minimum Threshold**: 75% line coverage
- **Target**: 80%+ line coverage
- **Enforcement**: CI builds fail if coverage < 75%

## Running Coverage Locally

### Quick Coverage Check

```bash
# Run tests with coverage
python -m pytest tests/ -m unit --cov=tapps_agents --cov-report=term --cov-report=html

# View HTML report
# Windows: start htmlcov/index.html
# macOS: open htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
```

### Generate Coverage Report

```bash
# Generate JSON report for tracking
python -m pytest tests/ -m unit --cov=tapps_agents --cov-report=json:coverage.json --cov-report=term

# Use coverage tracker script
python scripts/coverage_tracker.py --coverage-file coverage.json
```

### Coverage Tracker Script

The `scripts/coverage_tracker.py` script provides:

- **Overall metrics**: Lines, statements, branches, functions
- **Baseline comparison**: Check against 75% threshold
- **Per-module coverage**: Identify modules needing attention
- **JSON output**: For programmatic use

```bash
# Text report
python scripts/coverage_tracker.py

# JSON output
python scripts/coverage_tracker.py --json

# Custom baseline
python scripts/coverage_tracker.py --baseline 80.0

# Save to file
python scripts/coverage_tracker.py --output reports/coverage_report.txt
```

## CI/CD Coverage

### GitHub Actions

Coverage is automatically:
- Calculated during test runs
- Uploaded to Codecov
- Displayed in workflow summary
- Enforced via `--cov-fail-under=75`

### Coverage Reports

- **Codecov**: https://codecov.io/gh/wtthornton/TappsCodingAgents
- **CI Artifacts**: Coverage XML and HTML reports in workflow artifacts
- **Workflow Summary**: Coverage percentage in GitHub Actions summary

## Baseline Metrics

### Current Baseline (2025-01)

- **Overall Coverage**: Target 75%+ (enforced in CI)
- **Critical Modules**: 80%+ (agents, core, security)
- **Supporting Modules**: 70%+ (workflow, experts, context7)

### Module Coverage Targets

| Module | Target | Description |
|--------|--------|-------------|
| `tapps_agents.agents.*` | 80%+ | Core agent implementations - critical for framework functionality |
| `tapps_agents.core.*` | 80%+ | Core infrastructure - agent base, security, configuration |
| `tapps_agents.context7.security` | 80%+ | Security and compliance modules - critical for production |
| `tapps_agents.experts.*` | 70%+ | Expert system - supporting functionality |
| `tapps_agents.workflow.*` | 70%+ | Workflow system - supporting functionality |
| `tapps_agents.cli.*` | 70%+ | CLI interface - user-facing, less critical for core functionality |

*Note: Run `python scripts/coverage_tracker.py` to see current values.*

### Baseline Configuration

Baseline metrics are tracked in:
- **CI/CD**: Enforced via `--cov-fail-under=75` in GitHub Actions
- **Local**: Configured in `pyproject.toml` and `pytest.ini`
- **Tracking**: Use `scripts/coverage_tracker.py` for trend analysis

## Trend Analysis

### Tracking Coverage Over Time

1. **Generate coverage report**:
   ```bash
   python -m pytest tests/ -m unit --cov=tapps_agents --cov-report=json:coverage.json
   ```

2. **Extract metrics**:
   ```bash
   python scripts/coverage_tracker.py --json > reports/coverage_$(date +%Y%m%d).json
   ```

3. **Compare trends**: Review historical JSON files in `reports/`

### Codecov Trends

Codecov automatically tracks coverage trends:
- Visit https://codecov.io/gh/wtthornton/TappsCodingAgents
- View coverage graphs and trends
- Compare coverage across branches/PRs

## Per-Module Tracking

### Identifying Low Coverage Modules

```bash
# Generate report showing lowest coverage modules
python scripts/coverage_tracker.py | grep "⚠️"
```

### Improving Module Coverage

1. **Identify gaps**: Review HTML coverage report
2. **Add tests**: Focus on uncovered lines/branches
3. **Verify**: Re-run coverage to confirm improvement
4. **Commit**: Ensure CI passes with new coverage

## Coverage Exclusions

Some code is intentionally excluded from coverage:

- Test files (`tests/**`)
- CLI entry points (minimal, user-facing)
- Exception handlers (error paths)
- Type stubs and protocol definitions

See `pytest.ini` and `pyproject.toml` for full exclusion lists.

## Best Practices

### Maintaining Coverage

1. **Run coverage locally** before committing
2. **Fix coverage regressions** immediately
3. **Add tests** for new code paths
4. **Review coverage reports** in PRs

### Coverage Goals

- **New code**: 80%+ coverage required
- **Refactored code**: Maintain or improve coverage
- **Legacy code**: Gradually improve to 75%+

### When Coverage Drops

1. **Identify cause**: Review coverage diff in Codecov
2. **Add tests**: Cover new or modified code paths
3. **Verify fix**: Re-run coverage locally
4. **Document**: If exclusion is needed, document why

## Troubleshooting

### CI Coverage Failures

If CI fails due to coverage:

1. **Check local coverage**:
   ```bash
   python -m pytest tests/ -m unit --cov=tapps_agents --cov-fail-under=75
   ```

2. **Review coverage report**:
   ```bash
   python scripts/coverage_tracker.py
   ```

3. **Identify gaps**: Focus on modules with lowest coverage

4. **Add tests**: Cover missing lines/branches

5. **Re-run**: Verify coverage meets threshold

### Coverage Not Updating

- Ensure `--cov-report=json:coverage.json` is used
- Check that test files are being discovered
- Verify source paths are correct in `pytest.ini`

## Resources

- **Coverage.py Docs**: https://coverage.readthedocs.io/
- **Pytest-Cov Docs**: https://pytest-cov.readthedocs.io/
- **Codecov Docs**: https://docs.codecov.com/
- **Project Coverage**: https://codecov.io/gh/wtthornton/TappsCodingAgents

