# Mocking and Test Doubles

## Overview

Mocking allows you to isolate units under test by replacing dependencies with test doubles. This guide covers mocking techniques, patterns, and best practices.

## Test Doubles

### Types of Test Doubles

**Dummy:**
- Placeholder object
- Never actually used
- Satisfies parameter requirements

**Fake:**
- Working implementation
- Simplified version
- In-memory database example

**Stub:**
- Returns predefined data
- No behavior verification
- Simple responses

**Mock:**
- Verifies interactions
- Records method calls
- Behavior verification

**Spy:**
- Real object wrapper
- Records interactions
- Verifies calls

## Mocking in Python

### unittest.mock

**Basic Mocking:**
```python
from unittest.mock import Mock, MagicMock

# Create mock
mock_service = Mock()
mock_service.get_data.return_value = {"key": "value"}

# Use mock
result = process_data(mock_service)
assert result == {"key": "value"}
```

### Patch Decorator

**Replace Dependencies:**
```python
from unittest.mock import patch

@patch('module.external_service')
def test_function(mock_service):
    mock_service.get_data.return_value = "test"
    result = my_function()
    assert result == "test"
```

### Context Manager

**Temporary Patching:**
```python
with patch('module.external_service') as mock_service:
    mock_service.get_data.return_value = "test"
    result = my_function()
```

## Mocking Patterns

### Mock External Services

**Isolate Units:**
```python
@patch('requests.get')
def test_fetch_data(mock_get):
    mock_get.return_value.json.return_value = {"data": "test"}
    result = fetch_data("http://api.example.com")
    assert result == {"data": "test"}
    mock_get.assert_called_once_with("http://api.example.com")
```

### Mock Database

**Test Without Database:**
```python
@patch('database.query')
def test_get_user(mock_query):
    mock_query.return_value = User(id=1, email="test@example.com")
    user = get_user(1)
    assert user.email == "test@example.com"
```

### Mock Time

**Control Time:**
```python
from unittest.mock import patch
from datetime import datetime

@patch('datetime.datetime')
def test_time_based_function(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 1, 1)
    result = time_based_function()
    assert result == "2025-01-01"
```

## Verification

### Assert Calls

**Verify Interactions:**
```python
mock_service = Mock()
process_data(mock_service)

# Verify called
mock_service.get_data.assert_called_once()

# Verify with arguments
mock_service.get_data.assert_called_with("arg1", "arg2")

# Verify call count
assert mock_service.get_data.call_count == 1
```

### Call Arguments

**Check Arguments:**
```python
mock_service.process.assert_called_with(
    user_id=1,
    data={"key": "value"}
)
```

## Stubbing

### Return Values

**Predefined Responses:**
```python
mock_service = Mock()
mock_service.get_user.return_value = User(id=1, email="test@example.com")

user = mock_service.get_user(1)
assert user.email == "test@example.com"
```

### Side Effects

**Dynamic Responses:**
```python
mock_service = Mock()
mock_service.get_data.side_effect = [
    "first",
    "second",
    ValueError("Error")
]

assert mock_service.get_data() == "first"
assert mock_service.get_data() == "second"
with pytest.raises(ValueError):
    mock_service.get_data()
```

## Spies

### Real Object Wrapper

**Wrap Real Objects:**
```python
from unittest.mock import MagicMock

real_service = RealService()
spy = MagicMock(wraps=real_service)

# Calls real method but records calls
result = spy.get_data(1)
spy.get_data.assert_called_once_with(1)
```

## Best Practices

1. **Mock External Dependencies**: Isolate units
2. **Verify Interactions**: Check method calls
3. **Use Appropriate Doubles**: Choose right type
4. **Keep Mocks Simple**: Don't over-complicate
5. **Test Behavior**: Focus on outcomes
6. **Avoid Over-Mocking**: Use real objects when possible
7. **Clear Mock Setup**: Explicit mock configuration
8. **Verify Assertions**: Check mock interactions

## Common Mistakes

### Over-Mocking

**Problem:**
- Mocking everything
- Tests don't reflect reality
- Hard to maintain

**Solution:**
- Mock external dependencies only
- Use real objects when possible
- Balance isolation and realism

### Testing Implementation

**Problem:**
- Testing how, not what
- Brittle tests
- Break on refactoring

**Solution:**
- Test behavior
- Verify outcomes
- Don't test internals

## Mocking Libraries

### Python

**unittest.mock:**
- Built-in
- Comprehensive
- Standard library

**pytest-mock:**
- pytest integration
- Fixture-based
- Easy to use

### JavaScript

**Jest:**
- Built-in mocking
- Auto-mocking
- Snapshot testing

**Sinon:**
- Standalone
- Comprehensive
- Flexible

## References

- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Mocking Best Practices](https://martinfowler.com/articles/mocksArentStubs.html)

