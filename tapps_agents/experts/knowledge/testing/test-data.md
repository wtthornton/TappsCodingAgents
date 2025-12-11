# Test Data Management

## Overview

Effective test data management ensures tests are reliable, maintainable, and isolated. This guide covers test data strategies, patterns, and best practices.

## Test Data Strategies

### Inline Test Data

**Simple Cases:**
```python
def test_calculate_total():
    items = [10, 20, 30]  # Inline data
    assert calculate_total(items) == 60
```

**Pros:**
- Simple
- Clear
- Self-contained

**Cons:**
- Not reusable
- Duplication
- Hard to maintain

### Test Fixtures

**Reusable Data:**
```python
@pytest.fixture
def sample_user():
    return User(
        email="test@example.com",
        password="password123",
        active=True
    )

def test_user_login(sample_user):
    assert login(sample_user.email, "password123") is True
```

### Test Factories

**Generate Test Data:**
```python
class UserFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "password": "password123",
            "active": True,
        }
        defaults.update(kwargs)
        return User(**defaults)

def test_user_operations():
    user = UserFactory.create(active=False)
    assert user.active is False
```

## Data Builders

### Builder Pattern

**Flexible Object Creation:**
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

## Test Databases

### Isolated Test Databases

**Separate Test Environment:**
```python
@pytest.fixture(scope="module")
def test_db():
    # Create test database
    db = create_test_database()
    yield db
    # Cleanup
    db.drop_all()

def test_user_creation(test_db):
    user = User(email="test@example.com")
    test_db.session.add(user)
    test_db.session.commit()
    assert user.id is not None
```

### Database Seeding

**Pre-populate Data:**
```python
@pytest.fixture
def seeded_db():
    db = create_test_database()
    # Seed with test data
    db.session.add(User(email="admin@example.com", role="admin"))
    db.session.add(User(email="user@example.com", role="user"))
    db.session.commit()
    return db
```

## Data Cleanup

### Teardown

**Clean Up After Tests:**
```python
@pytest.fixture
def user():
    user = User(email="test@example.com")
    yield user
    # Cleanup
    user.delete()

def test_user_operations(user):
    # Test uses user
    pass
    # User automatically deleted after test
```

### Transaction Rollback

**Isolate Tests:**
```python
@pytest.fixture
def db_session():
    session = create_session()
    transaction = session.begin()
    yield session
    transaction.rollback()
    session.close()
```

## Parameterized Tests

### Multiple Test Cases

**Test with Different Data:**
```python
@pytest.mark.parametrize("input,expected", [
    ([1, 2, 3], 6),
    ([10, 20], 30),
    ([], 0),
])
def test_calculate_total(input, expected):
    assert calculate_total(input) == expected
```

## External Data Files

### JSON/YAML Files

**Load Test Data:**
```python
import json

@pytest.fixture
def test_data():
    with open("tests/data/users.json") as f:
        return json.load(f)

def test_user_creation(test_data):
    for user_data in test_data:
        user = User(**user_data)
        assert user.email is not None
```

### CSV Files

**Tabular Test Data:**
```python
import csv

def load_test_data(filename):
    with open(filename) as f:
        reader = csv.DictReader(f)
        return list(reader)

def test_users_from_csv():
    users = load_test_data("tests/data/users.csv")
    for user_data in users:
        user = User(**user_data)
        assert user.email is not None
```

## Data Generation

### Faker Library

**Generate Realistic Data:**
```python
from faker import Faker

fake = Faker()

def test_user_creation():
    user = User(
        email=fake.email(),
        name=fake.name(),
        address=fake.address()
    )
    assert user.email is not None
```

## Best Practices

1. **Isolate Test Data**: Each test independent
2. **Use Factories**: Generate test data
3. **Clean Up**: Remove test data after tests
4. **Use Fixtures**: Reusable test data
5. **Parameterize**: Test multiple scenarios
6. **Realistic Data**: Use realistic test data
7. **Minimal Data**: Only data needed for test
8. **Document Data**: Clear test data purpose

## Common Mistakes

### Shared State

**Problem:**
- Tests share data
- Tests affect each other
- Unpredictable results

**Solution:**
- Isolate test data
- Clean up after tests
- Use fixtures properly

### Hard-Coded Data

**Problem:**
- Brittle tests
- Hard to maintain
- Not reusable

**Solution:**
- Use factories
- Parameterize tests
- External data files

## References

- [Test Data Management](https://www.oreilly.com/library/view/the-art-of-unit/9781449361211/)
- [Faker Library](https://faker.readthedocs.io/)

