# FastAPI Testing Patterns

## Overview

This guide covers testing patterns for FastAPI applications, including unit tests, integration tests, and API testing.

## Testing Patterns

### Pattern 1: Basic Test Client

```python
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "HomeIQ API"}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

### Pattern 2: Async Test Client

```python
import pytest
from httpx import AsyncClient
from app import app

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/sensors/device_001")
        assert response.status_code == 200
```

### Pattern 3: Dependency Override

```python
from fastapi import Depends
from fastapi.testclient import TestClient
from app import app, get_db

# Override dependency
def override_get_db():
    # Return test database
    return TestSessionLocal()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_with_mock_db():
    response = client.get("/users")
    assert response.status_code == 200
```

### Pattern 4: Fixtures

```python
import pytest
from fastapi.testclient import TestClient
from app import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "name": "Test User"
    }

def test_create_user(client, test_user):
    response = client.post("/users", json=test_user)
    assert response.status_code == 201
    assert response.json()["email"] == test_user["email"]
```

## Integration Testing

### Pattern 1: Database Testing

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app import app

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_user(db):
    response = client.post("/users", json={"email": "test@example.com"})
    assert response.status_code == 201
```

### Pattern 2: External Service Mocking

```python
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

@patch('app.influxdb_client')
def test_sensor_endpoint(mock_influxdb):
    # Mock InfluxDB client
    mock_influxdb.write = AsyncMock(return_value=True)
    
    response = client.post(
        "/sensors/data",
        json={
            "device_id": "sensor_001",
            "value": 72.5,
            "unit": "fahrenheit"
        }
    )
    
    assert response.status_code == 200
    mock_influxdb.write.assert_called_once()
```

## API Testing

### Pattern 1: End-to-End Testing

```python
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_sensor_data_flow():
    # Create sensor reading
    response = client.post(
        "/sensors/data",
        json={
            "device_id": "sensor_001",
            "value": 72.5,
            "unit": "fahrenheit"
        }
    )
    assert response.status_code == 200
    
    # Retrieve sensor data
    response = client.get("/sensors/sensor_001")
    assert response.status_code == 200
    assert len(response.json()["readings"]) > 0
```

### Pattern 2: Authentication Testing

```python
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_authenticated_endpoint():
    # Login
    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password"}
    )
    token = response.json()["access_token"]
    
    # Use token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
```

## Best Practices

### 1. Use Test Fixtures

```python
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_data():
    return {
        "device_id": "test_device",
        "value": 72.5
    }
```

### 2. Mock External Dependencies

```python
@patch('app.external_service')
def test_with_mock(mock_service):
    mock_service.call.return_value = {"result": "success"}
    # Test code
```

### 3. Clean Up Test Data

```python
@pytest.fixture
def clean_db():
    # Setup
    yield
    # Cleanup
    db.query(User).delete()
    db.commit()
```

### 4. Test Error Cases

```python
def test_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404

def test_validation_error():
    response = client.post("/users", json={"invalid": "data"})
    assert response.status_code == 422
```

## References

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest Documentation](https://docs.pytest.org/)
- [TestClient API](https://www.starlette.io/testclient/)

