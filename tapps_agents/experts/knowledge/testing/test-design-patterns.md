# Test Design Patterns

## Overview

Test design patterns provide reusable solutions to common testing problems. This guide covers essential patterns for writing maintainable and effective tests.

## Arrange-Act-Assert (AAA)

### Pattern Structure

**Three Phases:**
1. **Arrange**: Set up test data and conditions
2. **Act**: Execute the code under test
3. **Assert**: Verify the results

**Example:**
```python
def test_calculate_total():
    # Arrange
    items = [10, 20, 30]
    
    # Act
    result = calculate_total(items)
    
    # Assert
    assert result == 60
```

## Test Fixtures

### Setup and Teardown

**Reusable Test Data:**
```python
@pytest.fixture
def user():
    # Setup
    user = User(email="test@example.com")
    yield user
    # Teardown
    user.delete()

def test_user_operations(user):
    assert user.email == "test@example.com"
```

### Factory Pattern

**Create Test Objects:**
```python
class UserFactory:
    @staticmethod
    def create(email=None, active=True):
        return User(
            email=email or f"user{random.randint(1000, 9999)}@example.com",
            active=active
        )

def test_user_creation():
    user = UserFactory.create(active=False)
    assert user.active is False
```

## Mock Objects

### Mock External Dependencies

**Isolate Units:**
```python
from unittest.mock import Mock, patch

def test_send_email():
    # Mock email service
    email_service = Mock()
    email_service.send.return_value = True
    
    # Test with mock
    result = send_notification(email_service, "user@example.com")
    
    assert result is True
    email_service.send.assert_called_once_with("user@example.com")
```

### Stub Pattern

**Provide Test Data:**
```python
def test_calculate_price():
    # Stub discount service
    discount_service = Mock()
    discount_service.get_discount.return_value = 0.1  # 10% discount
    
    price = calculate_price(100, discount_service)
    assert price == 90
```

## Test Doubles

### Types of Test Doubles

**Dummy:**
- Placeholder object
- Never used
- Satisfies parameter requirements

**Fake:**
- Working implementation
- Simplified version
- In-memory database

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

## Page Object Pattern

### UI Test Organization

**Encapsulate Page Logic:**
```python
class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.username_field = driver.find_element(By.ID, "username")
        self.password_field = driver.find_element(By.ID, "password")
        self.login_button = driver.find_element(By.ID, "login")
    
    def login(self, username, password):
        self.username_field.send_keys(username)
        self.password_field.send_keys(password)
        self.login_button.click()

def test_login():
    page = LoginPage(driver)
    page.login("user", "pass")
    assert driver.current_url == "/dashboard"
```

## Data Builder Pattern

### Flexible Test Data

**Build Complex Objects:**
```python
class UserBuilder:
    def __init__(self):
        self.email = "default@example.com"
        self.active = True
        self.role = "user"
    
    def with_email(self, email):
        self.email = email
        return self
    
    def with_role(self, role):
        self.role = role
        return self
    
    def build(self):
        return User(email=self.email, active=self.active, role=self.role)

def test_admin_user():
    user = UserBuilder().with_role("admin").build()
    assert user.role == "admin"
```

## Parameterized Tests

### Test Multiple Scenarios

**Run Same Test with Different Data:**
```python
@pytest.mark.parametrize("input,expected", [
    ([1, 2, 3], 6),
    ([10, 20], 30),
    ([], 0),
    ([5], 5),
])
def test_calculate_total(input, expected):
    assert calculate_total(input) == expected
```

## Test Hooks

### Setup and Teardown

**Manage Test Lifecycle:**
```python
@pytest.fixture(scope="module")
def database():
    # Setup
    db = create_test_database()
    yield db
    # Teardown
    db.cleanup()

def test_query(database):
    result = database.query("SELECT * FROM users")
    assert len(result) > 0
```

## Test Categories

### Organize Tests

**Tag Tests:**
```python
@pytest.mark.unit
def test_calculate_total():
    pass

@pytest.mark.integration
def test_api_integration():
    pass

@pytest.mark.slow
def test_large_dataset():
    pass
```

## Best Practices

1. **Use AAA Pattern**: Clear test structure
2. **Isolate Tests**: No shared state
3. **Use Fixtures**: Reusable test data
4. **Mock External Dependencies**: Isolate units
5. **Parameterize Tests**: Test multiple scenarios
6. **Keep Tests Simple**: One concept per test
7. **Use Descriptive Names**: Clear test purpose
8. **Maintain Tests**: Update with code changes

## Common Patterns

### Given-When-Then

**BDD Style:**
```python
def test_user_registration():
    # Given a new user
    user_data = {"email": "new@example.com", "password": "pass123"}
    
    # When they register
    user = register_user(user_data)
    
    # Then they should be created
    assert user.email == "new@example.com"
    assert user.is_active is True
```

### Test Helpers

**Reusable Test Functions:**
```python
def create_test_user(email=None, active=True):
    return User(
        email=email or "test@example.com",
        active=active
    )

def test_user_operations():
    user = create_test_user(active=False)
    assert user.active is False
```

## References

- [Test Design Patterns](https://xunitpatterns.com/)
- [Testing Patterns](https://www.oreilly.com/library/view/test-driven-development/0596006892/)

