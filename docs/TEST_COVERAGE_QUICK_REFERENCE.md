# Test Coverage Quick Reference

## Quick Commands

### Run Tests with Coverage

```bash
# Recommended: Use the test runner script
python scripts/run_tests_with_coverage.py

# Direct pytest command
pytest tests/ -m unit -n auto --cov=tapps_agents --cov-report=term
```

### Common Use Cases

| Use Case | Command |
|----------|---------|
| **Fast test run** (no coverage) | `pytest tests/ -m unit -n auto` |
| **With coverage** | `pytest tests/ -m unit -n auto --cov=tapps_agents --cov-report=term` |
| **HTML report** | `pytest tests/ --cov=tapps_agents --cov-report=html` |
| **All formats** | `pytest tests/ --cov=tapps_agents --cov-report=term --cov-report=html --cov-report=json` |
| **Specific file** | `pytest tests/unit/test_config.py --cov=tapps_agents` |
| **Fail if < 75%** | `pytest tests/ --cov=tapps_agents --cov-fail-under=75` |

### Test Runner Script

```bash
# Unit tests (default)
python scripts/run_tests_with_coverage.py

# All tests with HTML report
python scripts/run_tests_with_coverage.py --all --html

# Specific file
python scripts/run_tests_with_coverage.py --file tests/unit/test_config.py

# No coverage (faster)
python scripts/run_tests_with_coverage.py --no-coverage
```

## Coverage Reports

### View HTML Report

```bash
# Windows
start htmlcov/index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

### Coverage Files

- `htmlcov/index.html` - Interactive HTML report
- `coverage.json` - JSON data for programmatic use
- Terminal output - Real-time coverage summary

## Terminal Feedback Features

- ✅ **Colored output** - Green passes, red failures
- 📊 **Progress indicators** - Visual progress during execution
- ⏱️ **Duration display** - Shows slowest tests
- 🎯 **Clear formatting** - Better test name display

## Performance

- **Parallel**: ~1-2 minutes (1200+ tests)
- **With coverage**: ~2-3 minutes
- **Sequential**: ~5-10 minutes (not recommended)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tests slow | Use `-n auto` for parallel execution |
| No colors | Install `pytest-sugar`: `pip install pytest-sugar` |
| Coverage missing | Check `--cov=tapps_agents` matches package name |
| Parallel issues | Use `--no-parallel` for debugging |

## See Also

- Full guide: `docs/TEST_COVERAGE_AND_TERMINAL_FEEDBACK.md`
- Test performance: `docs/TEST_PERFORMANCE_GUIDE.md`
- Test maintenance: `docs/TEST_MAINTENANCE_GUIDE.md`

