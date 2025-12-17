# Test Suite

This directory contains the comprehensive test suite for TappsCodingAgents.

## Test Organization

```
tests/
├── unit/          # Unit tests (fast, isolated, no external dependencies)
├── integration/   # Integration tests (with real services, slower)
└── e2e/           # End-to-end tests (full system validation)
```

## Quick Start

### Run All Tests

```bash
# Run all tests (default: unit tests only)
pytest

# Run all tests including E2E
pytest -m ""

# Run with coverage
pytest --cov=tapps_agents --cov-report=term
```

### Run Specific Test Types

```bash
# Unit tests only (fast, default)
pytest -m unit

# Integration tests
pytest -m integration

# E2E tests (see tests/e2e/README.md for details)
pytest tests/e2e/ -m "e2e_smoke or e2e_workflow or e2e_scenario or e2e_cli"
```

## Test Types

### Unit Tests (`unit/`)

Fast, isolated tests that validate individual components without external dependencies.

**Characteristics:**
- No network calls
- No file system dependencies (use mocks/fixtures)
- Run in milliseconds
- 1200+ tests

**Run:**
```bash
pytest tests/unit/ -m unit
```

### Integration Tests (`integration/`)

Tests that validate component interactions with real services (LLM, Context7, etc.).

**Characteristics:**
- May require external services
- Use real API calls (when credentials available)
- Slower than unit tests
- Skip gracefully if services unavailable

**Run:**
```bash
pytest tests/integration/ -m integration
```

### End-to-End Tests (`e2e/`)

**Comprehensive E2E test suite validating complete system workflows.**

**📖 See [E2E Test Suite Documentation](e2e/README.md) for complete details.**

**Quick Reference:**

```bash
# Smoke tests (fast, no external services)
pytest tests/e2e/smoke/ -m e2e_smoke

# Workflow tests
pytest tests/e2e/workflows/ -m e2e_workflow

# Scenario tests (complete user journeys)
pytest tests/e2e/scenarios/ -m e2e_scenario

# CLI tests
pytest tests/e2e/cli/ -m e2e_cli

# All E2E tests
pytest tests/e2e/ -m "e2e_smoke or e2e_workflow or e2e_scenario or e2e_cli"
```

**E2E Test Categories:**
- **Smoke Tests**: Fast, deterministic tests (< 30 seconds, no external services)
- **Workflow Tests**: Validate workflow execution end-to-end
- **Scenario Tests**: Complete user journey validation (feature implementation, bug fixes, refactoring)
- **CLI Tests**: CLI command validation and error handling
- **Agent Tests**: Agent-specific behavior validation

**For detailed E2E documentation, see:**
- **[E2E Test Suite README](e2e/README.md)** - Complete E2E test documentation
- **[E2E Marker Taxonomy](e2e/MARKER_TAXONOMY.md)** - Test markers and execution matrix
- **[E2E CI/CD Execution](e2e/CI_CD_EXECUTION.md)** - CI/CD integration guide

## Test Configuration

### Pytest Configuration

Test configuration is in `pytest.ini` at the project root:

- **Default markers**: `unit` (only unit tests run by default)
- **Markers**: `unit`, `integration`, `e2e`, `e2e_smoke`, `e2e_workflow`, `e2e_scenario`, `e2e_cli`
- **Timeout**: 30 seconds default (configurable per test)
- **Async mode**: Auto (pytest-asyncio)

### Running Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

## Test Performance

See [Test Performance Guide](../docs/TEST_PERFORMANCE_GUIDE.md) for optimization tips.

**Performance Tips:**
- Use `-m unit` for fast feedback during development
- Use `-n auto` for parallel execution (5-10x faster)
- E2E smoke tests run in < 30 seconds total
- Use `--tb=short` for concise output

## Test Coverage

```bash
# Generate coverage report
pytest --cov=tapps_agents --cov-report=term

# Generate HTML coverage report
pytest --cov=tapps_agents --cov-report=html
# Open htmlcov/index.html in browser
```

## Common Test Patterns

### Using Fixtures

```python
# Use shared fixtures from tests/conftest.py
def test_something(mock_mal, temp_project_dir):
    # mock_mal: Mocked LLM
    # temp_project_dir: Temporary project directory
    pass
```

### E2E Test Patterns

```python
# Use E2E fixtures from tests/e2e/conftest.py
@pytest.mark.e2e_smoke
@pytest.mark.template_type("minimal")
def test_something(e2e_project, e2e_correlation_id):
    # e2e_project: Isolated test project
    # e2e_correlation_id: Unique test correlation ID
    pass
```

## Troubleshooting

### Tests Not Running

- Check pytest configuration: `pytest --collect-only`
- Verify markers: `pytest -m unit --collect-only`
- Check Python path: Ensure project root is in PYTHONPATH

### E2E Tests Failing

- See [E2E README](e2e/README.md) troubleshooting section
- Check artifact capture: Artifacts are automatically captured on failure
- Verify fixtures: Ensure all required fixtures are available

### Import Errors

- Ensure project is installed: `pip install -e .`
- Check Python path: `pythonpath = .` in pytest.ini

## Contributing Tests

When adding new tests:

1. **Unit tests**: Add to `tests/unit/` with `@pytest.mark.unit`
2. **Integration tests**: Add to `tests/integration/` with `@pytest.mark.integration`
3. **E2E tests**: Add to `tests/e2e/` with appropriate marker (`e2e_smoke`, `e2e_workflow`, etc.)
4. **Follow existing patterns**: Use fixtures, markers, and structure from existing tests

For E2E tests, see [E2E README](e2e/README.md) for conventions and best practices.

