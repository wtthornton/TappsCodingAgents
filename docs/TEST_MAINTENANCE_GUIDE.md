# Test Maintenance Guide

## Overview

This guide provides best practices for maintaining and optimizing the test suite to ensure high code coverage, fast execution, and reliable results.

## Test Organization

### Test Structure

```
tests/
├── unit/              # Fast, isolated unit tests (default)
├── integration/      # Integration tests with dependencies
└── e2e/              # End-to-end tests (full system)
```

### Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, with dependencies)
- `@pytest.mark.e2e` - End-to-end tests (slowest, full system)
- `@pytest.mark.slow` - Tests taking >5 seconds

### Running Tests by Type

```bash
# Unit tests only (default, fastest)
pytest tests/ -m unit

# Integration tests
pytest tests/ -m integration

# E2E tests
pytest tests/ -m e2e

# All tests
pytest tests/ -m ""
```

## Coverage Maintenance

### Coverage Requirements

- **Minimum**: 75% line coverage (enforced in CI)
- **Target**: 80%+ line coverage
- **Critical Modules**: 80%+ (agents, core, security)

### Adding Tests for New Code

1. **Write tests first** (TDD approach):
   ```bash
   # Create test file
   tests/unit/module/test_new_feature.py
   ```

2. **Run with coverage**:
   ```bash
   pytest tests/unit/module/test_new_feature.py --cov=tapps_agents.module --cov-report=term
   ```

3. **Verify coverage**:
   ```bash
   python scripts/coverage_tracker.py
   ```

4. **Ensure CI passes**:
   ```bash
   pytest tests/ -m unit --cov=tapps_agents --cov-fail-under=75
   ```

### Fixing Coverage Gaps

1. **Identify gaps**:
   ```bash
   # Generate HTML report
   pytest tests/ -m unit --cov=tapps_agents --cov-report=html
   # Open htmlcov/index.html
   ```

2. **Add tests** for uncovered lines/branches

3. **Verify improvement**:
   ```bash
   pytest tests/ -m unit --cov=tapps_agents --cov-report=term
   ```

## Test Performance

### Parallel Execution

Use `pytest-xdist` for parallel test execution (5-10x faster):

```bash
# Auto-detect CPU cores
pytest tests/ -m unit -n auto

# Specific number of workers
pytest tests/ -m unit -n 4
```

### Performance Optimization

1. **Use fixtures** for shared setup:
   ```python
   @pytest.fixture
   def sample_data():
       return {"key": "value"}
   ```

2. **Mock external dependencies**:
   ```python
   @patch("module.external_api")
   def test_function(mock_api):
       mock_api.return_value = "result"
   ```

3. **Avoid slow operations** in unit tests:
   - File I/O → Use `tempfile` or mocks
   - Network calls → Use mocks
   - Database → Use in-memory or mocks

4. **Mark slow tests**:
   ```python
   @pytest.mark.slow
   def test_slow_operation():
       # Test that takes >5 seconds
   ```

### Test Execution Time

- **Unit tests**: <1 second each (target)
- **Integration tests**: <5 seconds each
- **E2E tests**: <30 seconds each

## Test Quality

### Best Practices

1. **Test one thing per test**:
   ```python
   # Good
   def test_add_user():
       assert add_user("John") == "user_123"

   def test_add_user_duplicate():
       with pytest.raises(ValueError):
           add_user("John")
   ```

2. **Use descriptive test names**:
   ```python
   # Good
   def test_add_user_raises_error_when_duplicate():
       pass

   # Bad
   def test_add():
       pass
   ```

3. **Test edge cases**:
   - Empty inputs
   - None/null values
   - Boundary conditions
   - Error paths

4. **Use fixtures for common setup**:
   ```python
   @pytest.fixture
   def user_data():
       return {"name": "John", "email": "john@example.com"}
   ```

### Test Assertions

1. **Use specific assertions**:
   ```python
   # Good
   assert result.status_code == 200
   assert "success" in result.json()

   # Bad
   assert result  # Too vague
   ```

2. **Test error conditions**:
   ```python
   with pytest.raises(ValueError, match="Invalid input"):
       process_data(None)
   ```

3. **Verify side effects**:
   ```python
   # Test that function modifies state correctly
   assert cache.get("key") == "value"
   ```

## Maintenance Tasks

### Regular Maintenance

1. **Weekly**: Review coverage reports
2. **Monthly**: Review slow tests and optimize
3. **Quarterly**: Review test organization and refactor

### When Adding Features

1. **Add tests** for new functionality
2. **Update existing tests** if behavior changes
3. **Verify coverage** meets threshold
4. **Run full test suite** before committing

### When Refactoring

1. **Run tests** before refactoring
2. **Keep tests passing** during refactoring
3. **Update tests** if API changes
4. **Maintain or improve** coverage

## Troubleshooting

### Tests Failing Intermittently

1. **Check for race conditions**:
   - Use proper locking/mocking
   - Avoid shared state

2. **Check for timing issues**:
   - Use `pytest-timeout` for long-running tests
   - Mock time-dependent operations

3. **Check for resource leaks**:
   - Close file handles
   - Clean up temporary files

### Slow Test Suite

1. **Identify slow tests**:
   ```bash
   pytest tests/ --durations=10
   ```

2. **Optimize slow tests**:
   - Use mocks instead of real operations
   - Parallelize where possible
   - Cache expensive operations

3. **Consider test organization**:
   - Move slow tests to integration/e2e
   - Keep unit tests fast

### Coverage Not Updating

1. **Check source paths** in `pytest.ini` and `pyproject.toml`
2. **Verify test discovery**:
   ```bash
   pytest tests/ --collect-only
   ```
3. **Check coverage configuration**:
   ```bash
   coverage report --show-missing
   ```

## Resources

- **Pytest Docs**: https://docs.pytest.org/
- **Coverage.py Docs**: https://coverage.readthedocs.io/
- **Test Performance Guide**: [docs/TEST_PERFORMANCE_GUIDE.md](TEST_PERFORMANCE_GUIDE.md)
- **Coverage Monitoring**: [docs/COVERAGE_MONITORING.md](COVERAGE_MONITORING.md)

