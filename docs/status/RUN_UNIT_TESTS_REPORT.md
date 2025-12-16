# Run All Unit Tests and Generate Report

## Quick Command (Recommended)

Run all unit tests in parallel with coverage report:

```bash
python -m pytest tests/ -m unit -n auto --cov=tapps_agents --cov-report=term --cov-report=html --cov-report=json --junitxml=reports/junit.xml
```

## Command Breakdown

- `tests/` - Test directory
- `-m unit` - Run only unit tests (fast, excludes integration/e2e)
- `-n auto` - Parallel execution using all CPU cores (5-10x faster)
- `--cov=tapps_agents` - Coverage for the main package
- `--cov-report=term` - Terminal coverage report
- `--cov-report=html` - HTML coverage report (opens in browser)
- `--cov-report=json` - JSON coverage report (for CI/CD)
- `--junitxml=reports/junit.xml` - JUnit XML report (for CI/CD)

## Output Files

After running, you'll get:

1. **Terminal output** - Test results and coverage summary
2. **HTML Coverage Report** - `htmlcov/index.html` (open in browser)
3. **JSON Coverage Report** - `coverage.json` (for programmatic use)
4. **JUnit XML Report** - `reports/junit.xml` (for CI/CD integration)

## View HTML Coverage Report

```bash
# Windows
start htmlcov/index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

## Alternative Commands

### Fast Run (No Coverage)
```bash
python -m pytest tests/ -m unit -n auto
```

### With Detailed Output
```bash
python -m pytest tests/ -m unit -n auto -v --cov=tapps_agents --cov-report=term --cov-report=html
```

### Sequential (Debugging Only)
```bash
python -m pytest tests/ -m unit --cov=tapps_agents --cov-report=term --cov-report=html
```

### Specific Test File
```bash
python -m pytest tests/unit/test_file.py -n auto --cov=tapps_agents --cov-report=term
```

## Expected Performance

- **Parallel execution**: ~1-2 minutes for 1200+ unit tests
- **With coverage**: ~2-3 minutes
- **Sequential**: ~5-10 minutes (not recommended)

## Troubleshooting

If `pytest-xdist` is not installed:
```bash
pip install pytest-xdist
```

If reports directory doesn't exist:
```bash
mkdir -p reports
```

## Full Report Command (All Formats)

```bash
python -m pytest tests/ -m unit -n auto \
  --cov=tapps_agents \
  --cov-report=term \
  --cov-report=html \
  --cov-report=json \
  --cov-report=xml \
  --junitxml=reports/junit.xml \
  --html=reports/report.html \
  --self-contained-html
```

*Note: Requires `pytest-html` for HTML report: `pip install pytest-html`*

