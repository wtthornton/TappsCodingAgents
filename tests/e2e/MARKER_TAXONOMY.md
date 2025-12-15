# E2E Marker Taxonomy and Execution Matrix

This document describes the marker taxonomy for E2E tests and the execution matrix for different CI/CD stages.

## Marker Taxonomy

### E2E Test Type Markers

These markers categorize E2E tests by their purpose:

- **`e2e_smoke`**: Fast, deterministic smoke tests (no external services)
  - No network calls (no real LLM, no real Context7)
  - Use mocked services
  - Run in under 30 seconds total
  - Suitable for PR gating

- **`e2e_workflow`**: Workflow execution E2E tests
  - Test workflow step execution
  - Test state transitions
  - Test artifact generation
  - Can use mocked or real services

- **`e2e_scenario`**: User journey scenario tests
  - Test complete user journeys from start to finish
  - Simulate real-world usage patterns
  - Typically use real services

- **`e2e_cli`**: CLI command E2E tests
  - Test CLI commands work correctly end-to-end
  - Test argument parsing
  - Test command execution and output

- **`e2e_slow`**: E2E tests that take longer than expected
  - Can combine with other markers (e.g., `e2e_workflow and e2e_slow`)
  - Used to identify tests that may need optimization

### Service Requirement Markers

These markers indicate whether tests require real external services:

- **`requires_llm`**: Tests that require any LLM service (Ollama, Anthropic, or OpenAI)
  - Tests are skipped if no LLM service is available
  - Can combine with E2E markers (e.g., `e2e_workflow and requires_llm`)

- **`requires_context7`**: Tests that require Context7 API key
  - Tests are skipped if Context7 API key is not available
  - Can combine with E2E markers (e.g., `e2e_workflow and requires_context7`)

### Default Behavior

**E2E tests default to mocked mode** unless explicitly marked with `requires_llm` or `requires_context7`.

## Marker Combinations

### Common Combinations

```python
# Smoke test with mocked services (default)
@pytest.mark.e2e_smoke
def test_something():
    pass

# Workflow test with mocked services (default)
@pytest.mark.e2e_workflow
def test_workflow():
    pass

# Workflow test with real LLM
@pytest.mark.e2e_workflow
@pytest.mark.requires_llm
def test_workflow_real():
    pass

# Scenario test with real services
@pytest.mark.e2e_scenario
@pytest.mark.requires_llm
@pytest.mark.requires_context7
def test_scenario_real():
    pass

# Slow workflow test
@pytest.mark.e2e_workflow
@pytest.mark.e2e_slow
def test_slow_workflow():
    pass
```

## Execution Matrix

### PR/CI Default

**Command:** `pytest -m "unit or e2e_smoke"`

**What runs:**
- All unit tests
- All smoke E2E tests (mocked, no external services)

**Characteristics:**
- Fast execution (< 1 minute typically)
- No external service dependencies
- Deterministic results
- Suitable for PR gating

**When:** Runs on every PR and commit

### Main Branch

**Command:** `pytest -m "unit or integration or e2e_workflow"`

**What runs:**
- All unit tests
- All integration tests
- All workflow E2E tests (mocked by default)

**Characteristics:**
- Moderate execution time (< 5 minutes typically)
- Uses mocked services (no external dependencies)
- Validates workflow execution

**When:** Runs on main branch commits

### Nightly/Scheduled

**Command:** `pytest -m "e2e_scenario or (e2e_workflow and requires_llm)"`

**What runs:**
- All scenario E2E tests
- Workflow E2E tests that require real LLM services

**Characteristics:**
- Longer execution time (10+ minutes)
- Uses real services (requires credentials)
- Validates complete user journeys
- Tests skipped if services unavailable (don't fail)

**When:** Runs on schedule (e.g., nightly)

## Local Execution

### Run Smoke Tests

```bash
# Fast, no services required
pytest tests/e2e/smoke/ -m e2e_smoke
```

### Run Workflow Tests (Mocked)

```bash
# Uses mocked services
pytest tests/e2e/workflows/ -m e2e_workflow
```

### Run Workflow Tests (Real Services)

```bash
# Requires LLM service
pytest tests/e2e/workflows/ -m "e2e_workflow and requires_llm"

# Requires Context7
pytest tests/e2e/workflows/ -m "e2e_workflow and requires_context7"
```

### Run Scenario Tests

```bash
# Mocked (if available)
pytest tests/e2e/scenarios/ -m e2e_scenario

# Real services
pytest tests/e2e/scenarios/ -m "e2e_scenario and requires_llm"
```

### Run CLI Tests

```bash
pytest tests/e2e/cli/ -m e2e_cli
```

### Run All E2E Tests

```bash
# All E2E tests (mocked by default)
pytest tests/e2e/ -m "e2e_smoke or e2e_workflow or e2e_scenario or e2e_cli"
```

### Run with Real Services

```bash
# Set environment variables first
export ANTHROPIC_API_KEY=your_key
export CONTEXT7_API_KEY=your_key

# Run tests that require services
pytest tests/e2e/ -m "requires_llm or requires_context7"
```

## Default pytest Behavior

The default `pytest` execution remains unchanged:

```bash
# Default: unit tests only
pytest

# Explicit: unit tests only
pytest -m unit

# All tests (including E2E)
pytest -m ""
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on:
  pull_request:
  push:
    branches: [main]

jobs:
  pr-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -e ".[dev]"
      - run: pytest -m "unit or e2e_smoke"

  main-branch:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -e ".[dev]"
      - run: pytest -m "unit or integration or e2e_workflow"

  nightly:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -e ".[dev]"
      - run: |
          pytest -m "e2e_scenario or (e2e_workflow and requires_llm)" || true
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          CONTEXT7_API_KEY: ${{ secrets.CONTEXT7_API_KEY }}
        continue-on-error: true
```

### Credential Handling

- **PR checks**: No credentials needed (smoke tests use mocks)
- **Main branch**: No credentials needed (workflow tests use mocks)
- **Nightly**: Credentials provided via secrets, but tests skip (don't fail) if unavailable

## Best Practices

1. **Use appropriate markers**: Mark tests with the correct E2E type marker
2. **Default to mocked**: Don't mark tests with `requires_llm` or `requires_context7` unless necessary
3. **Combine markers correctly**: Use `and` for service requirements, `or` for test types
4. **Keep smoke tests fast**: Smoke tests should run in under 30 seconds total
5. **Document service requirements**: Clearly document which tests require real services

## Troubleshooting

### Tests Skipped Unexpectedly

Check if tests are marked with `requires_llm` or `requires_context7` and services are unavailable.

### Tests Running Too Slowly

Mark slow tests with `e2e_slow` and consider optimization.

### Marker Not Recognized

Ensure markers are registered in `pytest.ini` and run with `--strict-markers` to catch unregistered markers.
