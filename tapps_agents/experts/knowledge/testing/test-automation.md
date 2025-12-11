# Test Automation Patterns

## Overview

Test automation improves efficiency, reliability, and speed of testing. This guide covers automation strategies, tools, and best practices.

## Automation Strategy

### What to Automate

**Good Candidates:**
- Repetitive tests
- Regression tests
- Smoke tests
- Integration tests
- Performance tests

**Not Ideal:**
- Exploratory testing
- Usability testing
- One-time tests
- Frequently changing tests

### Automation Pyramid

**Test Distribution:**
- **Unit Tests**: Many, fast, automated
- **Integration Tests**: Some, moderate speed
- **E2E Tests**: Few, slow, critical paths

## CI/CD Integration

### Continuous Testing

**Automated Execution:**
- Run on every commit
- Fast feedback
- Prevent regressions
- Automated deployment gates

**Example (GitHub Actions):**
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest tests/
```

### Test Stages

**Pipeline Stages:**
1. **Unit Tests**: Fast, run first
2. **Integration Tests**: Moderate speed
3. **E2E Tests**: Slow, run on schedule
4. **Performance Tests**: Periodic

## Test Frameworks

### Python: pytest

**Features:**
- Simple syntax
- Fixtures
- Parametrization
- Plugins

**Example:**
```python
import pytest

@pytest.fixture
def user():
    return User(email="test@example.com")

def test_user_login(user):
    assert login(user.email, "password") is True
```

### JavaScript: Jest

**Features:**
- Built-in test runner
- Mocking
- Coverage
- Snapshot testing

**Example:**
```javascript
test('calculates total', () => {
  expect(calculateTotal([1, 2, 3])).toBe(6);
});
```

### Java: JUnit

**Features:**
- Annotations
- Assertions
- Test runners
- Extensions

## Test Data Management

### Test Fixtures

**Reusable Data:**
```python
@pytest.fixture
def sample_users():
    return [
        User(email="user1@example.com"),
        User(email="user2@example.com"),
    ]
```

### Test Factories

**Generate Test Data:**
```python
class UserFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "active": True,
        }
        defaults.update(kwargs)
        return User(**defaults)
```

### Test Databases

**Isolated Test Data:**
- Use separate test database
- Reset between tests
- Seed with test data
- Clean up after tests

## Parallel Execution

### Run Tests in Parallel

**Speed Up Execution:**
```bash
# pytest-xdist
pytest -n auto

# Run specific test classes in parallel
pytest tests/ -n 4
```

### Test Isolation

**Independent Tests:**
- No shared state
- Can run in any order
- Parallel-safe
- Easy to debug

## Test Reporting

### Test Results

**Report Formats:**
- JUnit XML
- HTML reports
- Console output
- CI/CD integration

**Example:**
```bash
pytest --junitxml=results.xml --html=report.html
```

### Test Metrics

**Track:**
- Test execution time
- Pass/fail rates
- Coverage metrics
- Flaky test detection

## Page Object Model

### UI Test Organization

**Encapsulate Page Logic:**
```python
class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.username = driver.find_element(By.ID, "username")
        self.password = driver.find_element(By.ID, "password")
    
    def login(self, username, password):
        self.username.send_keys(username)
        self.password.send_keys(password)
        self.driver.find_element(By.ID, "submit").click()
```

## API Testing

### REST API Testing

**Test APIs:**
```python
def test_get_user():
    response = requests.get("/api/users/1")
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
```

### GraphQL Testing

**Test GraphQL:**
```python
def test_user_query():
    query = """
    query {
        user(id: 1) {
            email
            name
        }
    }
    """
    response = client.execute(query)
    assert response["data"]["user"]["email"] == "user@example.com"
```

## Best Practices

1. **Start Small**: Automate critical tests first
2. **Maintain Tests**: Update with code changes
3. **Keep Tests Fast**: Optimize execution time
4. **Isolate Tests**: No dependencies between tests
5. **Use Page Objects**: Organize UI tests
6. **Parallel Execution**: Speed up test runs
7. **Report Results**: Clear test reporting
8. **Monitor Flakiness**: Track unstable tests

## Common Mistakes

### Over-Automation

**Problem:**
- Automating everything
- Maintaining too many tests
- Slow test execution

**Solution:**
- Automate strategically
- Focus on value
- Regular maintenance

### Brittle Tests

**Problem:**
- Tests break on UI changes
- Hard to maintain
- High maintenance cost

**Solution:**
- Use stable selectors
- Page Object Model
- Abstract implementation details

## References

- [Test Automation Best Practices](https://www.selenium.dev/documentation/test_practices/)
- [CI/CD Testing](https://www.atlassian.com/continuous-delivery/software-testing)

