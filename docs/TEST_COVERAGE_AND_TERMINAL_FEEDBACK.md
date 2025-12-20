# Test Coverage and Terminal Feedback Guide

This guide explains how to implement and use unit test code coverage with live terminal feedback in the TappsCodingAgents project.

## Overview

The project includes:
- **Code Coverage**: Automated coverage tracking with pytest-cov
- **Terminal Feedback**: Real-time progress indicators and colored output
- **Multiple Report Formats**: Terminal, HTML, and JSON reports
- **Parallel Execution**: Fast test runs with pytest-xdist
- **Enhanced Visual Output**: Colored output and progress bars with pytest-sugar

## Quick Start

### Basic Usage

Run unit tests with coverage and live terminal feedback:

```bash
# Using the test runner script (recommended)
python scripts/run_tests_with_coverage.py

# Or using pytest directly
pytest tests/ -m unit -n auto --cov=tapps_agents --cov-report=term
```

### Test Runner Script

The `scripts/run_tests_with_coverage.py` script provides a convenient interface:

```bash
# Run unit tests with coverage (default)
python scripts/run_tests_with_coverage.py

# Run all tests with HTML report
python scripts/run_tests_with_coverage.py --all --html

# Run specific test file
python scripts/run_tests_with_coverage.py --file tests/unit/test_config.py

# Run without coverage (faster)
python scripts/run_tests_with_coverage.py --no-coverage

# Run sequentially (for debugging)
python scripts/run_tests_with_coverage.py --no-parallel
```

## Features

### 1. Code Coverage

#### Coverage Configuration

Coverage is configured in `pytest.ini`:

```ini
[coverage:run]
source = tapps_agents
omit =
    */tests/*
    */__pycache__/*
    */site-packages/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
fail_under = 75
```

#### Coverage Reports

**Terminal Report** (default):
```bash
pytest tests/ --cov=tapps_agents --cov-report=term
```

**HTML Report** (interactive):
```bash
pytest tests/ --cov=tapps_agents --cov-report=html
# Open htmlcov/index.html in browser
```

**JSON Report** (for CI/CD):
```bash
pytest tests/ --cov=tapps_agents --cov-report=json
# Generates coverage.json
```

**Multiple Formats**:
```bash
pytest tests/ --cov=tapps_agents --cov-report=term --cov-report=html --cov-report=json
```

#### Coverage Thresholds

Fail if coverage is below a threshold:

```bash
pytest tests/ --cov=tapps_agents --cov-fail-under=75
```

The default threshold is 75% (configured in `pytest.ini`).

### 2. Terminal Feedback

#### Enhanced Visual Output

The project uses **pytest-sugar** for enhanced terminal output:

- ✅ **Colored output**: Green for passes, red for failures
- 📊 **Progress indicators**: Visual progress during test execution
- 🎯 **Clear test names**: Better formatting of test names and results
- ⏱️ **Duration display**: Shows slowest tests at the end

#### Real-Time Progress

When running tests, you'll see:

```
tests/unit/test_config.py::TestConfig::test_load_config ✓
tests/unit/test_agent.py::TestAgent::test_execute ✓
tests/unit/test_workflow.py::TestWorkflow::test_run ...
```

#### Verbosity Levels

**Verbose** (default):
```bash
pytest tests/ -v
```

**Quiet**:
```bash
pytest tests/ -q
```

**Extra verbose**:
```bash
pytest tests/ -vv
```

### 3. Parallel Execution

Run tests in parallel for faster execution:

```bash
# Auto-detect CPU cores (recommended)
pytest tests/ -n auto

# Use specific number of workers
pytest tests/ -n 4
```

**Performance**:
- Sequential: ~5-10 minutes for 1200+ tests
- Parallel: ~1-2 minutes (5-10x faster)

### 4. Test Selection

#### By Marker

```bash
# Unit tests only (default)
pytest tests/ -m unit

# Integration tests
pytest tests/ -m integration

# E2E tests
pytest tests/ -m e2e

# All tests
pytest tests/ -m ""
```

#### By File

```bash
# Specific test file
pytest tests/unit/test_config.py

# Specific test class
pytest tests/unit/test_config.py::TestConfig

# Specific test function
pytest tests/unit/test_config.py::TestConfig::test_load_config
```

## Configuration

### pytest.ini

The main pytest configuration includes:

```ini
addopts =
    -v                          # Verbose output
    --strict-markers           # Strict marker validation
    --strict-config            # Strict config validation
    --tb=short                 # Short traceback format
    --asyncio-mode=auto        # Auto async mode
    -m unit                    # Run unit tests by default
    --timeout=30               # Test timeout
    --timeout-method=thread    # Timeout method
    --color=yes                # Colored output
    --durations=10             # Show 10 slowest tests
```

### Coverage Settings

Coverage settings in `pytest.ini`:

```ini
[coverage:run]
source = tapps_agents
omit = */tests/*, */__pycache__/*, */site-packages/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
fail_under = 75

[coverage:html]
directory = htmlcov
```

## Usage Examples

### Daily Development

**Fast test run** (no coverage):
```bash
pytest tests/ -m unit -n auto
```

**With coverage**:
```bash
pytest tests/ -m unit -n auto --cov=tapps_agents --cov-report=term
```

### Pre-Commit Checks

```bash
pytest tests/ -m unit -n auto --cov=tapps_agents --cov-report=term --cov-fail-under=75
```

### Full Test Suite

```bash
pytest tests/ -m "" -n auto --cov=tapps_agents --cov-report=html --cov-report=json
```

### CI/CD Pipeline

```bash
pytest tests/ -n auto --cov=tapps_agents --cov-report=xml --cov-report=term --junitxml=reports/junit.xml
```

## Viewing Coverage Reports

### HTML Report

After generating an HTML report:

```bash
# Windows
start htmlcov/index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

The HTML report provides:
- Overall coverage percentage
- Per-module coverage breakdown
- Line-by-line coverage highlighting
- Missing lines identification

### JSON Report

The JSON report (`coverage.json`) can be used programmatically:

```python
import json

with open("coverage.json") as f:
    data = json.load(f)
    print(f"Coverage: {data['totals']['percent_covered']}%")
```

### Terminal Report

The terminal report shows:
- Overall coverage percentage
- Per-module coverage
- Missing lines (if `show_missing=True`)
- Coverage by file

Example output:
```
---------- coverage: platform win32, python 3.13.0 -----------
Name                                    Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
tapps_agents/__init__.py                   5      0   100%
tapps_agents/core/__init__.py              3      0   100%
tapps_agents/core/config.py               45      2    96%   23-24
...
-------------------------------------------------------------------------
TOTAL                                    1234    156    87%
```

## Troubleshooting

### Tests Running Slowly

1. **Use parallel execution**: Always use `-n auto` for fastest results
2. **Disable coverage**: Remove `--cov` flags for faster runs
3. **Check for slow tests**: Run with `--durations=10` to see slowest tests
4. **Verify timeout settings**: Tests have 30s timeout

### Coverage Not Showing

1. **Check pytest-cov is installed**: `pip install pytest-cov`
2. **Verify source path**: Ensure `--cov=tapps_agents` matches your package name
3. **Check omit patterns**: Verify files aren't being excluded

### Terminal Output Not Colored

1. **Check pytest-sugar is installed**: `pip install pytest-sugar`
2. **Verify terminal supports colors**: Most modern terminals do
3. **Check pytest.ini**: Ensure `--color=yes` is in `addopts`

### Parallel Execution Issues

1. **Disable for debugging**: Use `--no-parallel` flag
2. **Check pytest-xdist**: Ensure `pytest-xdist` is installed
3. **Reduce workers**: Use `-n 2` instead of `-n auto` if issues occur

## Best Practices

1. **Daily Development**: Use parallel execution without coverage for speed
   ```bash
   pytest tests/ -m unit -n auto
   ```

2. **Before Committing**: Run with coverage to ensure no regressions
   ```bash
   pytest tests/ -m unit -n auto --cov=tapps_agents --cov-report=term
   ```

3. **Before Release**: Run full suite with all reports
   ```bash
   pytest tests/ -m "" -n auto --cov=tapps_agents --cov-report=html --cov-report=json
   ```

4. **CI/CD**: Always use parallel execution and generate XML reports
   ```bash
   pytest tests/ -n auto --cov=tapps_agents --cov-report=xml --junitxml=reports/junit.xml
   ```

5. **Debugging**: Use sequential mode for easier debugging
   ```bash
   pytest tests/ -m unit --no-parallel -vv
   ```

## Dependencies

Required packages (already in `pyproject.toml`):

- `pytest>=9.0.2` - Test framework
- `pytest-cov>=7.0.0` - Coverage plugin
- `pytest-xdist>=3.6.0` - Parallel execution
- `pytest-sugar>=1.0.0` - Enhanced terminal output
- `coverage>=7.13.0` - Coverage library

Install with:
```bash
pip install -e ".[dev]"
```

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [pytest-xdist Documentation](https://pytest-xdist.readthedocs.io/)
- [pytest-sugar Documentation](https://pytest-sugar.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## Script Reference

### run_tests_with_coverage.py

The test runner script provides a convenient interface:

**Options**:
- `--unit`: Run only unit tests (default)
- `--integration`: Run only integration tests
- `--e2e`: Run only E2E tests
- `--all`: Run all tests
- `--file PATH`: Run specific test file
- `--no-coverage`: Disable coverage (faster)
- `--html`: Generate HTML coverage report
- `--json`: Generate JSON coverage report
- `--fail-under PERCENT`: Fail if coverage below threshold
- `--no-parallel`: Run sequentially
- `--quiet`: Reduce verbosity
- `--test-path PATH`: Custom test directory

**Examples**:
```bash
# Quick unit test run
python scripts/run_tests_with_coverage.py

# Full suite with HTML report
python scripts/run_tests_with_coverage.py --all --html

# Specific file with coverage
python scripts/run_tests_with_coverage.py --file tests/unit/test_config.py

# Integration tests only
python scripts/run_tests_with_coverage.py --integration
```

