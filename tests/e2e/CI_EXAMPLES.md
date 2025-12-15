# CI/CD Configuration Examples

This document provides example CI/CD configurations for running E2E tests in different environments.

## GitHub Actions

### Complete Workflow Example

```yaml
name: Tests

on:
  pull_request:
  push:
    branches: [main]
  schedule:
    # Run nightly tests at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  # PR checks: Fast tests only (unit + smoke E2E)
  pr-checks:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run unit and smoke tests
        run: |
          pytest -m "unit or e2e_smoke" --tb=short

  # Main branch: Unit + integration + workflow E2E (mocked)
  main-branch:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run unit, integration, and workflow tests
        run: |
          pytest -m "unit or integration or e2e_workflow" --tb=short

  # Nightly: Scenario tests + real services
  nightly:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run scenario and real service tests
        run: |
          pytest -m "e2e_scenario or (e2e_workflow and requires_llm)" --tb=short || true
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          CONTEXT7_API_KEY: ${{ secrets.CONTEXT7_API_KEY }}
        continue-on-error: true
```

### Simplified Workflow (Single Job)

```yaml
name: Tests

on: [pull_request, push]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        marker:
          - "unit or e2e_smoke"  # PR checks
          - "unit or integration or e2e_workflow"  # Main branch
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -e ".[dev]"
      - run: pytest -m "${{ matrix.marker }}"
```

## GitLab CI

### Complete Pipeline Example

```yaml
stages:
  - test

variables:
  PYTHON_VERSION: "3.9"

# PR checks: Fast tests only
pr-checks:
  stage: test
  only:
    - merge_requests
  script:
    - pip install -e ".[dev]"
    - pytest -m "unit or e2e_smoke" --tb=short

# Main branch: Unit + integration + workflow E2E
main-branch:
  stage: test
  only:
    - main
  script:
    - pip install -e ".[dev]"
    - pytest -m "unit or integration or e2e_workflow" --tb=short

# Nightly: Scenario tests + real services
nightly:
  stage: test
  only:
    - schedules
  script:
    - pip install -e ".[dev]"
    - pytest -m "e2e_scenario or (e2e_workflow and requires_llm)" --tb=short || true
  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
    CONTEXT7_API_KEY: $CONTEXT7_API_KEY
  allow_failure: true
```

## Generic YAML (Jenkins, CircleCI, etc.)

### PR Checks Job

```yaml
name: PR Checks
steps:
  - name: Install dependencies
    run: pip install -e ".[dev]"
  
  - name: Run unit and smoke tests
    run: pytest -m "unit or e2e_smoke" --tb=short
```

### Main Branch Job

```yaml
name: Main Branch Tests
steps:
  - name: Install dependencies
    run: pip install -e ".[dev]"
  
  - name: Run unit, integration, and workflow tests
    run: pytest -m "unit or integration or e2e_workflow" --tb=short
```

### Nightly Job

```yaml
name: Nightly Tests
steps:
  - name: Install dependencies
    run: pip install -e ".[dev]"
  
  - name: Run scenario and real service tests
    run: pytest -m "e2e_scenario or (e2e_workflow and requires_llm)" --tb=short || true
    env:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      CONTEXT7_API_KEY: ${CONTEXT7_API_KEY}
    continue_on_error: true
```

## Credential Handling

### Best Practices

1. **Store credentials as secrets**: Never hardcode API keys in CI configuration
2. **Skip, don't fail**: Tests that require services should skip (not fail) if credentials are unavailable
3. **Use conditional execution**: Only run real service tests when credentials are available

### GitHub Actions Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. Add secrets:
   - `ANTHROPIC_API_KEY`
   - `CONTEXT7_API_KEY`
3. Reference in workflow:
   ```yaml
   env:
     ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
     CONTEXT7_API_KEY: ${{ secrets.CONTEXT7_API_KEY }}
   ```

### GitLab CI Variables

1. Go to repository Settings → CI/CD → Variables
2. Add variables (mark as protected/masked if needed):
   - `ANTHROPIC_API_KEY`
   - `CONTEXT7_API_KEY`
3. Reference in pipeline:
   ```yaml
   variables:
     ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
     CONTEXT7_API_KEY: $CONTEXT7_API_KEY
   ```

## Test Execution Strategies

### Parallel Execution

Use `pytest-xdist` for parallel test execution:

```yaml
- name: Install dependencies
  run: pip install -e ".[dev]" pytest-xdist

- name: Run tests in parallel
  run: pytest -m "unit or e2e_smoke" -n auto
```

### Test Caching

Cache Python dependencies and test artifacts:

```yaml
- name: Cache pip packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}

- name: Cache pytest cache
  uses: actions/cache@v3
  with:
    path: .pytest_cache
    key: ${{ runner.os }}-pytest-${{ github.sha }}
```

### Artifact Collection

Collect test artifacts on failure:

```yaml
- name: Run tests
  run: pytest -m "unit or e2e_smoke" --tb=short
  continue-on-error: true

- name: Upload test artifacts
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: test-artifacts
    path: |
      .pytest_cache/
      tests/e2e/**/*.log
      tests/e2e/**/artifacts/
```

## Performance Optimization

### Test Timeouts

Add timeouts to prevent hanging tests:

```yaml
- name: Run tests with timeout
  run: pytest -m "unit or e2e_smoke" --timeout=300
```

### Selective Test Execution

Run only changed tests (if supported by CI):

```yaml
- name: Run changed tests only
  run: |
    # Example: Run tests for changed files
    pytest $(git diff --name-only HEAD~1 | grep test_ | xargs) || pytest -m "unit or e2e_smoke"
```

## Monitoring and Reporting

### Test Results

Publish test results:

```yaml
- name: Publish test results
  uses: EnricoMi/publish-unit-test-result-action@v2
  if: always()
  with:
    files: |
      test-results.xml
```

### Coverage Reports

Generate and upload coverage:

```yaml
- name: Run tests with coverage
  run: pytest -m "unit or e2e_smoke" --cov=tapps_agents --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Troubleshooting

### Tests Skipped in CI

- Check if credentials are set correctly
- Verify marker combinations are correct
- Check CI logs for skip reasons

### Tests Failing in CI but Passing Locally

- Check Python version compatibility
- Verify dependencies are installed correctly
- Check for environment-specific issues (paths, permissions)

### Slow CI Execution

- Use parallel execution (`pytest-xdist`)
- Cache dependencies and test artifacts
- Run only necessary tests (use markers effectively)
