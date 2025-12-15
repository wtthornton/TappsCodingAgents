# Test Performance Optimization Guide

## Overview

The test suite has been optimized for faster execution while maintaining comprehensive coverage. This guide explains the optimizations and how to use them effectively.

## Performance Optimizations

### 1. Coverage Disabled by Default

**Impact**: 2-5x faster test execution

Coverage tracking adds significant overhead to every test run. It's now **disabled by default** but can be enabled when needed.

**Before** (slow):
```bash
pytest tests/  # Coverage enabled, generates HTML/XML reports
```

**After** (fast):
```bash
pytest tests/  # No coverage, fast execution
pytest tests/ --cov=tapps_agents --cov-report=term  # Coverage when needed
```

### 2. Unit Tests Only by Default

**Impact**: 3-10x faster (skips slow integration tests)

By default, only fast unit tests run. Integration tests are excluded unless explicitly requested.

**Fast run** (default):
```bash
pytest tests/  # Only unit tests
```

**All tests**:
```bash
pytest tests/ -m ""  # Run all tests (unit + integration)
```

**Integration only**:
```bash
pytest tests/ -m integration
```

### 3. Parallel Execution (Optional)

**Impact**: 2-4x faster on multi-core systems

Install `pytest-xdist` for parallel test execution:

```bash
pip install pytest-xdist
pytest tests/ -n auto  # Auto-detect CPU cores
pytest tests/ -n 4     # Use 4 workers
```

## Performance Comparison

| Configuration | Time | Use Case |
|--------------|------|----------|
| **Optimized (default)** | ~10-30s | Daily development, quick checks |
| With coverage | ~60-120s | Pre-commit, CI/CD |
| All tests (unit + integration) | ~30-60s | Full validation |
| All tests + coverage | ~120-240s | Release preparation |

## Usage Examples

### Daily Development (Fast)
```bash
# Quick test run - unit tests only, no coverage
pytest tests/

# Run specific test file
pytest tests/unit/test_config.py

# Run specific test
pytest tests/unit/test_config.py::TestLoadConfig::test_load_config_from_file
```

### Pre-Commit Checks
```bash
# Unit tests with coverage
pytest tests/ -m unit --cov=tapps_agents --cov-report=term --cov-fail-under=55
```

### Full Test Suite
```bash
# All tests (unit + integration)
pytest tests/ -m ""

# All tests with coverage
pytest tests/ -m "" --cov=tapps_agents --cov-report=html --cov-report=xml
```

### CI/CD Pipeline
```bash
# Parallel execution with coverage
pytest tests/ -n auto --cov=tapps_agents --cov-report=xml --cov-report=term
```

## Test Markers

Tests are organized with markers for selective execution:

- `@pytest.mark.unit` - Fast, isolated unit tests (default)
- `@pytest.mark.integration` - Slower integration tests
- `@pytest.mark.e2e` - End-to-end tests (slowest)
- `@pytest.mark.slow` - Tests taking >5 seconds
- `@pytest.mark.requires_ollama` - Tests requiring Ollama server

## Troubleshooting

### Tests Still Slow?

1. **Check if coverage is enabled**: Remove `--cov` flags
2. **Verify you're running unit tests only**: Check `-m unit` is in effect
3. **Install pytest-xdist**: `pip install pytest-xdist` for parallel execution
4. **Check for slow tests**: Run with `--durations=10` to see slowest tests

### Need Coverage Reports?

```bash
# Terminal report only (fastest)
pytest tests/ --cov=tapps_agents --cov-report=term

# HTML report (for viewing)
pytest tests/ --cov=tapps_agents --cov-report=html
# Then open htmlcov/index.html

# XML report (for CI/CD)
pytest tests/ --cov=tapps_agents --cov-report=xml
```

## Configuration

The optimizations are configured in `pytest.ini`:

```ini
addopts =
    -v
    --strict-markers
    --strict-config
    --tb=short
    --asyncio-mode=auto
    -m unit  # Run only unit tests by default
```

To override defaults, use command-line flags:
- `-m ""` - Run all tests
- `--cov=tapps_agents` - Enable coverage
- `-n auto` - Enable parallel execution (requires pytest-xdist)

## Best Practices

1. **Daily development**: Use default (unit tests only, no coverage)
2. **Before committing**: Run with coverage: `pytest tests/ -m unit --cov`
3. **Before release**: Run full suite: `pytest tests/ -m "" --cov`
4. **CI/CD**: Use parallel execution: `pytest tests/ -n auto --cov`

## Additional Tips

- Use `pytest --collect-only` to see what tests would run without executing them
- Use `pytest --durations=10` to identify slow tests
- Use `pytest -k "test_name"` to run tests matching a pattern
- Use `pytest --lf` (last failed) to rerun only failed tests
- Use `pytest --ff` (failed first) to run failed tests first, then others

