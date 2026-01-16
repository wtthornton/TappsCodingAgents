---
title: Test Stack Documentation
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [testing, quality, ci-cd]
---

# Test Stack

This document provides a comprehensive overview of the testing strategy, infrastructure, and quality gates for TappsCodingAgents.

## Overview

TappsCodingAgents uses a comprehensive testing strategy with multiple test types organized in a testing pyramid:

- **Unit Tests** (Foundation): Fast, isolated tests (1200+ tests)
- **Integration Tests** (Middle): Component interaction tests with real services
- **End-to-End Tests** (Top): Complete system validation tests

## Test Types

### Unit Tests

**Location:** `tests/unit/`

**Characteristics:**
- Fast execution (milliseconds per test)
- Isolated (no external dependencies)
- No network calls
- No file system dependencies (use mocks/fixtures)
- 1200+ tests

**Marker:** `@pytest.mark.unit`

**Run:**
```bash
pytest -m unit
pytest tests/unit/
```

**Coverage Target:** 80-90% for unit tests

### Integration Tests

**Location:** `tests/integration/`

**Characteristics:**
- Test component interactions
- May require external services (LLM, Context7)
- Use real API calls (when credentials available)
- Slower than unit tests
- Skip gracefully if services unavailable

**Marker:** `@pytest.mark.integration`

**Run:**
```bash
pytest -m integration
pytest tests/integration/
```

**Coverage Target:** 60-70% for integration tests

### End-to-End Tests

**Location:** `tests/e2e/`

**Characteristics:**
- Complete system validation
- Full user journey tests
- Slowest execution
- Organized by category:
  - **Smoke Tests** (`e2e_smoke`): Fast, deterministic (< 30 seconds, no external services)
  - **Workflow Tests** (`e2e_workflow`): Workflow execution validation
  - **Scenario Tests** (`e2e_scenario`): Complete user journeys
  - **CLI Tests** (`e2e_cli`): CLI command validation

**Markers:**
- `@pytest.mark.e2e_smoke`
- `@pytest.mark.e2e_workflow`
- `@pytest.mark.e2e_scenario`
- `@pytest.mark.e2e_cli`

**Run:**
```bash
# Smoke tests (fast, no external services)
pytest tests/e2e/smoke/ -m e2e_smoke

# Workflow tests
pytest tests/e2e/workflows/ -m e2e_workflow

# Scenario tests
pytest tests/e2e/scenarios/ -m e2e_scenario

# CLI tests
pytest tests/e2e/cli/ -m e2e_cli

# All E2E tests
pytest tests/e2e/ -m "e2e_smoke or e2e_workflow or e2e_scenario or e2e_cli"
```

**Documentation:** See [E2E Test Suite Documentation](../tests/e2e/README.md) for complete details.

**Coverage Target:** Cover critical paths

### Contract Tests

**Status:** Not currently implemented

**Future:** API contract testing for service integrations

### Performance Tests

**Status:** Not currently implemented

**Future:** Performance benchmarking and load testing

## Test Infrastructure

### Test Framework

- **Framework:** pytest
- **Configuration:** `pytest.ini` at project root
- **Async Support:** pytest-asyncio (auto mode)
- **Parallel Execution:** pytest-xdist (`pytest -n auto`)

### Test Configuration

**Default Behavior:**
- Only unit tests run by default (`-m unit`)
- Coverage disabled by default (use `--cov` to enable)
- Timeout: 30 seconds per test (configurable)
- Output: Verbose with colored output (pytest-sugar)

**Markers:**
- `unit`: Unit tests (fast, isolated)
- `integration`: Integration tests (slower, with dependencies)
- `e2e`: End-to-end tests (slowest, full system)
- `slow`: Tests that take longer than 5 seconds
- `requires_context7`: Tests requiring Context7 API key
- `requires_llm`: Tests requiring LLM service
- `e2e_smoke`, `e2e_workflow`, `e2e_scenario`, `e2e_cli`: E2E test categories

### Test Fixtures

**Shared Fixtures:** `tests/conftest.py`
- `mock_mal`: Mocked LLM
- `temp_project_dir`: Temporary project directory

**E2E Fixtures:** `tests/e2e/conftest.py`
- `e2e_project`: Isolated test project
- `e2e_correlation_id`: Unique test correlation ID

### Mock/Stub Strategies

**Unit Tests:**
- Use `unittest.mock` for external dependencies
- Mock LLM calls (MAL - Mock AI Language)
- Mock file system operations
- Mock network calls

**Integration Tests:**
- Use real services when credentials available
- Graceful degradation when services unavailable
- Test doubles for expensive operations

**E2E Tests:**
- Use project templates (minimal, small, medium)
- Isolated test environments
- No external services for smoke tests

## CI Integration

### Continuous Integration

Tests are integrated into CI/CD pipeline:

**Default Test Run:**
- Unit tests only (fast feedback)
- Runs on every commit

**Full Test Suite:**
- All test types
- Runs on PRs and main branch
- Includes coverage reporting

**E2E Tests:**
- Smoke tests run on every commit
- Full E2E suite runs on PRs
- Scenario tests run on main branch merges

### Test Execution in CI

```yaml
# Example CI configuration
- name: Run Unit Tests
  run: pytest -m unit

- name: Run Integration Tests
  run: pytest -m integration

- name: Run E2E Smoke Tests
  run: pytest tests/e2e/smoke/ -m e2e_smoke

- name: Run Full Test Suite
  run: pytest -m ""
```

## Coverage Thresholds

### Overall Coverage

**Minimum Threshold:** 75% (enforced in `pytest.ini`)

**Target Coverage:**
- **Unit Tests:** 80-90% coverage
- **Integration Tests:** 60-70% coverage
- **Core Modules:** 70%+ coverage (quality gate)
- **Critical Paths:** 100% coverage

### Coverage Reporting

**Generate Coverage Report:**
```bash
# Terminal report
pytest --cov=tapps_agents --cov-report=term

# HTML report
pytest --cov=tapps_agents --cov-report=html
# Open htmlcov/index.html in browser

# XML report (for CI)
pytest --cov=tapps_agents --cov-report=xml
```

**Coverage Configuration:**
- Source: `tapps_agents`
- Omit: `*/tests/*`, `*/__pycache__/*`, `*/site-packages/*`, `*/cli.py`

### Quality Gates

**CI/CD Quality Gates:**
- **Overall Score:** ≥ 70 (fail if below)
- **Maintainability Score:** ≥ 7.0 (warn if below)
- **Test Coverage Score:** ≥ 7.0 (warn if below)
- **Complexity:** Block PRs with new F/D level violations

**Coverage Gate:**
- Fail if coverage < 75% (configurable in `pytest.ini`)

## Test Performance

### Performance Targets

- **Unit Tests:** Milliseconds per test
- **Integration Tests:** Seconds per test
- **E2E Smoke Tests:** < 30 seconds total
- **Full E2E Suite:** Minutes (acceptable for full validation)

### Performance Optimization

**Parallel Execution:**
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (5-10x faster)
pytest -n auto
```

**Fast Feedback:**
- Use `-m unit` for fast feedback during development
- Use `--tb=short` for concise output
- Use `-k <pattern>` to run specific tests

**Performance Tips:**
- Use unit tests for fast feedback
- Run integration/E2E tests before committing
- Use parallel execution for full test suite
- See [Test Performance Guide](TEST_PERFORMANCE_GUIDE.md) for optimization tips

## Test Organization

### Directory Structure

```
tests/
├── unit/          # Unit tests (fast, isolated)
├── integration/   # Integration tests (with real services)
└── e2e/           # End-to-end tests (full system)
    ├── smoke/      # Fast, deterministic smoke tests
    ├── workflows/  # Workflow execution tests
    ├── scenarios/  # User journey scenario tests
    ├── cli/        # CLI command tests
    └── fixtures/   # Shared E2E fixtures
```

### Test Naming Conventions

**File Naming:**
- `test_*.py` for test files
- Mirror source structure when possible

**Test Function Naming:**
- `test_*` for test functions
- Descriptive names: `test_calculate_total_returns_sum_of_items()`

**Test Class Naming:**
- `Test*` for test classes

## Contributing Tests

### Adding New Tests

1. **Unit Tests:** Add to `tests/unit/` with `@pytest.mark.unit`
2. **Integration Tests:** Add to `tests/integration/` with `@pytest.mark.integration`
3. **E2E Tests:** Add to `tests/e2e/` with appropriate marker

### Test Patterns

**Unit Test Pattern:**
```python
@pytest.mark.unit
def test_calculate_total(mock_mal, temp_project_dir):
    # Use fixtures for dependencies
    result = calculate_total([10, 20, 30])
    assert result == 60
```

**E2E Test Pattern:**
```python
@pytest.mark.e2e_smoke
@pytest.mark.template_type("minimal")
def test_workflow_parsing(e2e_project, e2e_correlation_id):
    # Use E2E fixtures
    result = run_workflow(e2e_project)
    assert result.success
```

### Best Practices

- **Isolation:** Each test should be independent
- **Fixtures:** Use shared fixtures for common setup
- **Markers:** Use appropriate markers for test categorization
- **Documentation:** Document complex test scenarios
- **Performance:** Keep unit tests fast (< 1 second each)

## Troubleshooting

### Common Issues

**Tests Not Running:**
- Check pytest configuration: `pytest --collect-only`
- Verify markers: `pytest -m unit --collect-only`
- Check Python path: Ensure project root is in PYTHONPATH

**E2E Tests Failing:**
- See [E2E README](../tests/e2e/README.md) troubleshooting section
- Check artifact capture: Artifacts automatically captured on failure
- Verify fixtures: Ensure all required fixtures available

**Import Errors:**
- Ensure project is installed: `pip install -e .`
- Check Python path: `pythonpath = .` in pytest.ini

**Coverage Issues:**
- Verify source paths in coverage configuration
- Check omit patterns match actual file locations
- Ensure tests are importing from installed package

## Related Documentation

- **[Test Suite Overview](../tests/README.md)** - Complete test suite documentation
- **[E2E Test Suite](../tests/e2e/README.md)** - End-to-end test documentation
- **[Test Performance Guide](TEST_PERFORMANCE_GUIDE.md)** - Performance optimization tips
- **[Quality Improvements](../docs/QUALITY_IMPROVEMENTS_EPIC_19.md)** - Quality improvement initiatives

---

**Last Updated:** 2026-01-20  
**Maintained By:** TappsCodingAgents Team
