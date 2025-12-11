# Testing Best Practices

## Overview

Following testing best practices ensures reliable, maintainable, and effective test suites. This guide covers essential practices for writing quality tests.

## Test Design

### Write Clear Tests

**AAA Pattern:**
```python
def test_calculate_total():
    # Arrange
    items = [10, 20, 30]
    
    # Act
    result = calculate_total(items)
    
    # Assert
    assert result == 60
```

### One Concept Per Test

**Focused Tests:**
```python
# Good: One concept
def test_user_activation():
    user = create_user()
    user.activate()
    assert user.is_active is True

# Bad: Multiple concepts
def test_user_operations():
    user = create_user()
    user.activate()
    user.add_role("admin")
    user.update_email("new@example.com")
    assert user.is_active is True
    assert "admin" in user.roles
    assert user.email == "new@example.com"
```

### Test Behavior, Not Implementation

**Focus on Outcomes:**
```python
# Good: Tests behavior
def test_user_login():
    user = create_user()
    result = login(user.email, "password")
    assert result is True

# Bad: Tests implementation
def test_user_login():
    user = create_user()
    login(user.email, "password")
    assert user.session_id is not None  # Implementation detail
```

## Test Organization

### Structure Tests

**Organize by Feature:**
```
tests/
├── unit/
│   ├── test_user.py
│   └── test_order.py
├── integration/
│   └── test_api.py
└── e2e/
    └── test_checkout.py
```

### Use Descriptive Names

**Clear Test Names:**
```python
# Good: Descriptive
def test_calculate_total_returns_sum_of_items():
    pass

def test_calculate_total_handles_empty_list():
    pass

# Bad: Unclear
def test_calculate():
    pass
```

## Test Data

### Use Fixtures

**Reusable Test Data:**
```python
@pytest.fixture
def user():
    return User(email="test@example.com", password="password")

def test_user_login(user):
    assert login(user.email, "password") is True
```

### Isolate Test Data

**Independent Tests:**
```python
def test_user_operations():
    # Each test creates its own data
    user = create_user()
    # Test operations
```

## Test Isolation

### No Shared State

**Independent Tests:**
```python
# Good: Isolated
def test_user_creation():
    user = create_user()
    assert user.id is not None

def test_user_deletion():
    user = create_user()
    user.delete()
    assert user.deleted is True

# Bad: Shared state
shared_user = None

def test_user_creation():
    global shared_user
    shared_user = create_user()

def test_user_deletion():
    shared_user.delete()  # Depends on previous test
```

## Mocking

### Mock External Dependencies

**Isolate Units:**
```python
@patch('external_service.get_data')
def test_process_data(mock_get):
    mock_get.return_value = {"key": "value"}
    result = process_data()
    assert result == {"key": "value"}
```

### Avoid Over-Mocking

**Balance:**
```python
# Good: Mock external service
@patch('api.external_api')
def test_fetch_data(mock_api):
    mock_api.get.return_value = {"data": "test"}
    result = fetch_data()
    assert result == {"data": "test"}

# Bad: Over-mocking
@patch('database.query')
@patch('cache.get')
@patch('logger.info')
def test_simple_function(mock_logger, mock_cache, mock_db):
    # Too many mocks
    pass
```

## Test Coverage

### Meaningful Coverage

**Focus on Value:**
- Test critical paths
- Test edge cases
- Test error handling
- Don't chase 100% coverage

### Coverage Goals

**Realistic Targets:**
- Unit tests: 80-90%
- Critical code: 100%
- Integration: 60-70%

## Performance

### Keep Tests Fast

**Optimize Execution:**
```python
# Fast: Mock database
@patch('database.query')
def test_user_operations(mock_query):
    mock_query.return_value = User()
    # Test operations

# Slow: Real database
def test_user_operations():
    user = User.objects.create(...)
    # Test operations
```

### Parallel Execution

**Speed Up Tests:**
```bash
pytest -n auto  # Run in parallel
```

## Error Handling

### Test Error Cases

**Cover Edge Cases:**
```python
def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)

def test_invalid_input():
    with pytest.raises(ValueError):
        process_data(None)
```

## Documentation

### Document Tests

**Clear Documentation:**
```python
def test_calculate_total_with_discount():
    """
    Test that calculate_total applies discount correctly.
    
    Given: Items totaling 100 with 10% discount
    When: calculate_total is called
    Then: Result should be 90
    """
    items = [50, 50]
    discount = 0.1
    result = calculate_total(items, discount)
    assert result == 90
```

## Best Practices Summary

1. **Write Clear Tests**: AAA pattern, descriptive names
2. **Test Behavior**: Focus on outcomes, not implementation
3. **Isolate Tests**: No shared state, independent tests
4. **Use Fixtures**: Reusable test data
5. **Mock Appropriately**: External dependencies only
6. **Keep Tests Fast**: Optimize execution time
7. **Test Edge Cases**: Error handling, boundary conditions
8. **Document Tests**: Clear test purpose
9. **Maintain Tests**: Update with code changes
10. **Review Tests**: Regular test reviews

## Common Mistakes

### Testing Implementation

**Problem:**
- Testing how, not what
- Brittle tests
- Break on refactoring

**Solution:**
- Test behavior
- Test public interface
- Focus on outcomes

### Shared State

**Problem:**
- Tests depend on each other
- Unpredictable results
- Hard to debug

**Solution:**
- Isolate tests
- No shared state
- Independent execution

### Over-Mocking

**Problem:**
- Too many mocks
- Tests don't reflect reality
- Hard to maintain

**Solution:**
- Mock external dependencies
- Use real objects when possible
- Balance isolation and realism

## References

- [Testing Best Practices](https://testing.googleblog.com/)
- [Test-Driven Development](https://www.agilealliance.org/glossary/tdd/)

