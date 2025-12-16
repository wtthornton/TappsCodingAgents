# Test Performance Optimization Guide

## Overview

The test suite has been optimized for faster execution while maintaining comprehensive coverage. This guide explains the optimizations and how to use them effectively.

**Recent Improvements (January 2025)**:
- ✅ **pytest-xdist added** to `requirements.txt` for parallel execution (5-10x speedup)
- ✅ **Slow test fixed** - Analytics test optimized to avoid excessive file I/O
- ✅ **Timeout increased** - From 10s to 30s to prevent false timeouts
- ✅ **Parallel execution recommended** - Now the default way to run tests

**Quick Start**: Run tests in parallel: `pytest tests/ -m unit -n auto`

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

### 3. Parallel Execution (Recommended)

**Impact**: 5-10x faster on multi-core systems

`pytest-xdist` is now included in `requirements.txt` for parallel test execution. This is the **recommended way** to run tests for optimal performance.

**Recommended** (parallel execution):
```bash
pytest tests/ -m unit -n auto  # Auto-detect CPU cores (recommended)
pytest tests/ -m unit -n 4     # Use 4 workers (adjust based on CPU)
```

**Sequential** (for debugging):
```bash
pytest tests/ -m unit  # No -n flag = sequential
```

## Performance Comparison

| Configuration | Time | Use Case |
|--------------|------|----------|
| **Optimized (parallel, default)** | ~1-2 min | Daily development, quick checks |
| **Sequential (no parallel)** | ~5-10 min | Debugging (when parallel causes issues) |
| With coverage (parallel) | ~2-3 min | Pre-commit, CI/CD |
| All tests (unit + integration, parallel) | ~2-4 min | Full validation |
| All tests + coverage (parallel) | ~3-5 min | Release preparation |

**Note**: Times are for 1200+ unit tests. Parallel execution provides 5-10x speedup on multi-core systems.

## Usage Examples

### Daily Development (Fast - Recommended)
```bash
# Quick test run - unit tests only, parallel execution, no coverage (FASTEST)
pytest tests/ -m unit -n auto

# Run specific test file
pytest tests/unit/test_config.py -n auto

# Run specific test
pytest tests/unit/test_config.py::TestLoadConfig::test_load_config_from_file

# Sequential (for debugging only)
pytest tests/ -m unit  # No -n flag
```

### Pre-Commit Checks
```bash
# Unit tests with coverage (parallel)
pytest tests/ -m unit -n auto --cov=tapps_agents --cov-report=term --cov-fail-under=55
```

### Full Test Suite
```bash
# All tests (unit + integration, parallel)
pytest tests/ -m "" -n auto

# All tests with coverage (parallel)
pytest tests/ -m "" -n auto --cov=tapps_agents --cov-report=html --cov-report=xml
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

1. **Use parallel execution**: Always use `-n auto` for fastest results
2. **Check if coverage is enabled**: Remove `--cov` flags for faster runs
3. **Verify you're running unit tests only**: Check `-m unit` is in effect
4. **Install pytest-xdist**: Should be in `requirements.txt`, but verify: `pip install pytest-xdist`
5. **Check for slow tests**: Run with `--durations=10` to see slowest tests
6. **Verify timeout settings**: Tests now have 30s timeout (increased from 10s)

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

1. **Daily development**: Use parallel execution: `pytest tests/ -m unit -n auto` (fastest)
2. **Before committing**: Run with coverage: `pytest tests/ -m unit -n auto --cov`
3. **Before release**: Run full suite: `pytest tests/ -m "" -n auto --cov`
4. **CI/CD**: Always use parallel execution: `pytest tests/ -m unit -n auto --cov`
5. **Debugging**: Use sequential mode: `pytest tests/ -m unit` (no `-n` flag)

## Additional Tips

- Use `pytest --collect-only` to see what tests would run without executing them
- Use `pytest --durations=10` to identify slow tests
- Use `pytest -k "test_name"` to run tests matching a pattern
- Use `pytest --lf` (last failed) to rerun only failed tests
- Use `pytest --ff` (failed first) to run failed tests first, then others

