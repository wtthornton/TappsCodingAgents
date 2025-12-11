# Coverage Analysis Techniques

## Overview

Code coverage measures how much of your code is executed by tests. This guide covers coverage metrics, analysis techniques, and best practices.

## Coverage Metrics

### Line Coverage

**Lines Executed:**
- Percentage of lines executed
- Most common metric
- Easy to understand
- Doesn't guarantee quality

**Example:**
```python
def calculate_total(items):
    total = 0           # Line 1: Covered
    for item in items:  # Line 2: Covered
        total += item   # Line 3: Covered
    return total        # Line 4: Covered
# 100% line coverage
```

### Branch Coverage

**Branches Executed:**
- Percentage of branches executed
- Tests if/else paths
- More thorough than line coverage
- Better quality indicator

**Example:**
```python
def process_user(user):
    if user.active:        # Branch 1: Need both True and False
        return "active"
    else:                   # Branch 2: Need both paths
        return "inactive"
```

### Function Coverage

**Functions Called:**
- Percentage of functions called
- Ensures functions are tested
- Less detailed
- Good high-level metric

### Statement Coverage

**Statements Executed:**
- Similar to line coverage
- Counts executable statements
- Excludes comments/blank lines
- More accurate than line coverage

## Coverage Tools

### Python: coverage.py

**Usage:**
```bash
# Run with coverage
coverage run -m pytest tests/

# Generate report
coverage report

# HTML report
coverage html
```

**Configuration (.coveragerc):**
```ini
[run]
source = src
omit = */tests/*,*/migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
```

### JavaScript: Istanbul/NYC

**Usage:**
```bash
# Run with coverage
nyc npm test

# Generate report
nyc report
```

### Java: JaCoCo

**Maven Configuration:**
```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <executions>
        <execution>
            <goals>
                <goal>prepare-agent</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

## Coverage Goals

### Target Coverage

**Recommended Levels:**
- **Unit Tests**: 80-90% coverage
- **Critical Code**: 100% coverage
- **Integration Tests**: 60-70% coverage
- **E2E Tests**: Cover critical paths

### Coverage by Code Type

**Different Targets:**
- **Business Logic**: 90%+
- **Utilities**: 80%+
- **Infrastructure**: 70%+
- **Legacy Code**: Increase gradually

## Coverage Analysis

### Identifying Gaps

**Analyze Coverage Reports:**
- Find untested code
- Identify missing test cases
- Prioritize critical paths
- Track coverage trends

### Coverage Reports

**HTML Reports:**
- Visual representation
- Line-by-line coverage
- Easy to navigate
- Identify gaps quickly

**Text Reports:**
- Command-line output
- Quick overview
- CI/CD integration
- Automated analysis

## Improving Coverage

### Add Missing Tests

**Fill Coverage Gaps:**
- Test uncovered lines
- Test edge cases
- Test error paths
- Test boundary conditions

### Test Edge Cases

**Coverage Gaps Often:**
- Error handling
- Edge cases
- Boundary conditions
- Rare code paths

**Example:**
```python
def divide(a, b):
    if b == 0:  # Often untested
        raise ValueError("Cannot divide by zero")
    return a / b

# Need test for b == 0
def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
```

## Coverage Exclusions

### When to Exclude

**Legitimate Exclusions:**
- Generated code
- Third-party code
- Test code
- Debug code
- Unreachable code

**Example:**
```python
# pragma: no cover
def debug_function():
    # Debug code that shouldn't be tested
    pass

def __repr__(self):  # Often excluded
    return f"User({self.id})"
```

## Coverage in CI/CD

### Continuous Coverage

**Automated Tracking:**
- Run coverage on every commit
- Track coverage trends
- Fail builds on coverage drop
- Report to team

**Example (GitHub Actions):**
```yaml
- name: Run tests with coverage
  run: |
    coverage run -m pytest
    coverage report
    coverage xml

- name: Upload coverage
  uses: codecov/codecov-action@v2
```

## Coverage Best Practices

1. **Set Realistic Goals**: 80-90% for unit tests
2. **Focus on Quality**: Coverage doesn't guarantee quality
3. **Test Critical Paths**: 100% for critical code
4. **Track Trends**: Monitor coverage over time
5. **Exclude Appropriately**: Don't test untestable code
6. **Review Reports**: Regularly review coverage
7. **Improve Gradually**: Increase coverage incrementally
8. **Use Tools**: Leverage coverage tools

## Common Mistakes

### Coverage Obsession

**Problem:**
- 100% coverage goal everywhere
- Testing untestable code
- Meaningless tests

**Solution:**
- Set realistic goals
- Focus on meaningful tests
- Exclude appropriately

### Ignoring Coverage

**Problem:**
- No coverage tracking
- Unknown test gaps
- Low confidence

**Solution:**
- Track coverage
- Set minimum thresholds
- Review regularly

## Coverage Metrics

### Key Metrics

**Track:**
- Overall coverage percentage
- Coverage by module
- Coverage trends
- Coverage gaps

### Coverage Reports

**Types:**
- Line coverage
- Branch coverage
- Function coverage
- Statement coverage

## References

- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Code Coverage Best Practices](https://www.atlassian.com/continuous-delivery/software-testing/code-coverage)

