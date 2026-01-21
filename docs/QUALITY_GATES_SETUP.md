# Quality Gates Setup Guide

This guide explains how to set up quality gates for continuous integration and development workflows.

## Current Configuration

Quality gates are configured in `.tapps-agents/config.yaml`:

```yaml
quality_gates:
  enabled: true
  test_coverage:
    enabled: true
    threshold: 0.8
    critical_services_threshold: 0.8
    warning_threshold: 0.6
```

## Using Quality Gates in CI/CD

### GitHub Actions Example

```yaml
name: Quality Checks

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov
      
      - name: Run quality checks
        run: |
          # Code review with fail-under threshold
          python -m tapps_agents.cli reviewer review tapps_agents \
            --fail-under 75 \
            --format json \
            --output quality-report.json
      
      - name: Run tests with coverage
        run: |
          pytest tests/ --cov=tapps_agents \
            --cov-report=json \
            --cov-report=term \
            --cov-fail-under=80
      
      - name: Check quality report
        if: failure()
        run: |
          echo "Quality checks failed. Review quality-report.json"
          exit 1
```

### Pre-commit Hook Example

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: quality-check
        name: Quality Check
        entry: python -m tapps_agents.cli reviewer review
        language: system
        args: ['--fail-under', '70', '--pattern', '**/*.py']
        pass_filenames: false
        always_run: true
      
      - id: lint-check
        name: Lint Check
        entry: ruff check
        language: system
        args: ['--fix']
        types: [python]
      
      - id: type-check
        name: Type Check
        entry: mypy
        language: system
        args: ['tapps_agents']
        types: [python]
```

Install pre-commit:
```bash
pip install pre-commit
pre-commit install
```

## Command-Line Usage

### Review with Quality Gate

```bash
# Fail if overall score < 75
tapps-agents reviewer review src/ --fail-under 75

# Fail if security score < 8.5
tapps-agents reviewer review src/ --fail-under 85 --security-threshold 8.5
```

### Test Coverage Gate

```bash
# Fail if coverage < 80%
pytest tests/ --cov=tapps_agents --cov-fail-under=80
```

## Quality Thresholds

Current thresholds (from config):

- **Overall Quality:** 70.0 (minimum)
- **Test Coverage:** 80.0 (80%)
- **Security:** 8.5 (from quality gates)
- **Maintainability:** 7.0 (threshold)
- **Complexity:** < 5.0 (maximum)

## Monitoring Quality Over Time

### Generate Quality Report

```bash
# Generate comprehensive report
tapps-agents reviewer report . all --output-dir reports/quality

# Analyze project-wide
tapps-agents reviewer analyze-project --format json > quality-metrics.json
```

### Track Metrics

Use the usage/analytics dashboard (via health usage):
```bash
tapps-agents health usage dashboard
tapps-agents health usage trends --days 30
```

## Best Practices

1. **Set Realistic Thresholds:** Start with current baseline, gradually increase
2. **Fail Fast:** Use `--fail-under` in CI/CD to catch issues early
3. **Monitor Trends:** Track quality metrics over time
4. **Fix Regressions:** Address quality regressions immediately
5. **Document Exceptions:** Document why certain thresholds can't be met

## Troubleshooting

### Quality Gate Failing

1. Check specific metric scores:
   ```bash
   tapps-agents reviewer score <file> --format json
   ```

2. Identify issues:
   ```bash
   tapps-agents reviewer review <file> --format text
   ```

3. Fix issues incrementally:
   - Start with critical issues (security, complexity)
   - Then address maintainability and type checking
   - Finally improve linting and documentation

### Coverage Too Low

1. Identify uncovered code:
   ```bash
   pytest --cov=tapps_agents --cov-report=term-missing
   ```

2. Prioritize critical paths:
   - Public APIs
   - Error handling
   - Core functionality

3. Add targeted tests for uncovered code

## Related Documentation

- See `QUALITY_AND_COVERAGE_REPORT.md` for current quality metrics
- See `QUALITY_IMPROVEMENTS_COMPLETED.md` for improvement progress
- See `.cursor/rules/command-reference.mdc` for command reference
