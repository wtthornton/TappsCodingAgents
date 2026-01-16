---
title: Testing Strategy
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [architecture, testing, strategy]
---

# Testing Strategy

This document describes the testing strategy for TappsCodingAgents. For detailed test infrastructure documentation, see [Test Stack Documentation](../test-stack.md).

## Testing Pyramid

TappsCodingAgents follows a testing pyramid approach:

```
        /\
       /  \  E2E Tests (few, slow, critical paths)
      /----\
     /      \  Integration Tests (some, moderate speed)
    /--------\
   /          \  Unit Tests (many, fast, isolated)
  /------------\
```

### Unit Tests (Foundation)

**Location**: `tests/unit/`

**Characteristics:**
- Fast execution (milliseconds per test)
- Isolated (no external dependencies)
- No network calls
- No file system dependencies (use mocks/fixtures)
- 1200+ tests

**Coverage Target**: 80-90%

### Integration Tests (Middle)

**Location**: `tests/integration/`

**Characteristics:**
- Test component interactions
- May require external services (LLM, Context7)
- Use real API calls (when credentials available)
- Slower than unit tests
- Skip gracefully if services unavailable

**Coverage Target**: 60-70%

### End-to-End Tests (Top)

**Location**: `tests/e2e/`

**Characteristics:**
- Complete system validation
- Full user journey tests
- Slowest execution
- Organized by category:
  - **Smoke Tests**: Fast, deterministic (< 30 seconds, no external services)
  - **Workflow Tests**: Workflow execution validation
  - **Scenario Tests**: Complete user journeys
  - **CLI Tests**: CLI command validation

**Coverage Target**: Cover critical paths

## Test Organization

### Directory Structure

```
tests/
├── unit/          # Unit tests (fast, isolated)
├── integration/   # Integration tests (with real services)
└── e2e/           # End-to-end tests (full system)
    ├── smoke/      # Fast smoke tests
    ├── workflows/  # Workflow execution tests
    ├── scenarios/  # User journey tests
    └── cli/        # CLI command tests
```

### Test Naming

- **Files**: `test_*.py`
- **Functions**: `test_*`
- **Classes**: `Test*`
- **Descriptive names**: `test_calculate_total_returns_sum_of_items()`

## Test Execution

### Running Tests

```bash
# Unit tests only (fast, default)
pytest -m unit

# Integration tests
pytest -m integration

# E2E smoke tests
pytest tests/e2e/smoke/ -m e2e_smoke

# All tests
pytest -m ""

# With coverage
pytest --cov=tapps_agents --cov-report=term

# Parallel execution (5-10x faster)
pytest -n auto
```

### Test Markers

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.e2e_smoke`: E2E smoke tests
- `@pytest.mark.e2e_workflow`: E2E workflow tests
- `@pytest.mark.e2e_scenario`: E2E scenario tests
- `@pytest.mark.e2e_cli`: E2E CLI tests

## Coverage Requirements

### Overall Coverage

**Minimum Threshold**: 75% (enforced in `pytest.ini`)

**Target Coverage:**
- **Unit Tests**: 80-90% coverage
- **Integration Tests**: 60-70% coverage
- **Core Modules**: 70%+ coverage (quality gate)
- **Critical Paths**: 100% coverage

### Coverage Reporting

```bash
# Terminal report
pytest --cov=tapps_agents --cov-report=term

# HTML report
pytest --cov=tapps_agents --cov-report=html
# Open htmlcov/index.html in browser

# XML report (for CI)
pytest --cov=tapps_agents --cov-report=xml
```

## Quality Gates

**CI/CD Quality Gates:**
- **Overall Score**: ≥ 70 (fail if below)
- **Maintainability Score**: ≥ 7.0 (warn if below)
- **Test Coverage Score**: ≥ 7.0 (warn if below)
- **Coverage**: ≥ 75% (fail if below)

## Test Patterns

### Unit Test Pattern

```python
@pytest.mark.unit
def test_calculate_total(mock_mal, temp_project_dir):
    """Test calculation with fixtures."""
    result = calculate_total([10, 20, 30])
    assert result == 60
```

### Integration Test Pattern

```python
@pytest.mark.integration
@pytest.mark.requires_context7
def test_context7_lookup(real_context7_client):
    """Test Context7 integration with real client."""
    result = await real_context7_client.lookup("fastapi")
    assert result is not None
```

### E2E Test Pattern

```python
@pytest.mark.e2e_smoke
@pytest.mark.template_type("minimal")
def test_workflow_parsing(e2e_project, e2e_correlation_id):
    """Test workflow parsing with E2E fixtures."""
    result = run_workflow(e2e_project)
    assert result.success
```

## Mock/Stub Strategies

### Unit Tests

- Use `unittest.mock` for external dependencies
- Mock LLM calls (MAL - Mock AI Language)
- Mock file system operations
- Mock network calls

### Integration Tests

- Use real services when credentials available
- Graceful degradation when services unavailable
- Test doubles for expensive operations

### E2E Tests

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

## Performance Targets

- **Unit Tests**: Milliseconds per test
- **Integration Tests**: Seconds per test
- **E2E Smoke Tests**: < 30 seconds total
- **Full E2E Suite**: Minutes (acceptable for full validation)

## Related Documentation

- **Test Stack**: `docs/test-stack.md` (comprehensive test infrastructure documentation)
- **E2E Test Suite**: `tests/e2e/README.md`
- **Test Performance Guide**: `docs/TEST_PERFORMANCE_GUIDE.md`

---

**Last Updated:** 2026-01-20  
**Maintained By:** TappsCodingAgents Team
