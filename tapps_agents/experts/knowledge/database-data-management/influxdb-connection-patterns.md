# InfluxDB Connection Patterns

## Overview

This guide covers InfluxDB connection management, pooling, retry logic, and error handling patterns for HomeIQ and similar production applications.

## Connection Management

### Basic Connection Pattern

**Python (influxdb-client):**
```python
from influxdb_client import InfluxDBClient

client = InfluxDBClient(
    url="http://localhost:8086",
    token="your-token",
    org="homeiq"
)

# Use client
write_api = client.write_api()
query_api = client.query_api()

# Cleanup
client.close()
```

**Best Practice:** Use context manager for automatic cleanup
```python
with InfluxDBClient(
    url="http://localhost:8086",
    token="your-token",
    org="homeiq"
) as client:
    write_api = client.write_api()
    # Use write_api
    # Automatically closed on exit
```

### Connection Pooling

**Reuse Client Instance:**
```python
class InfluxDBService:
    def __init__(self):
        self.client = InfluxDBClient(
            url=os.getenv("INFLUXDB_URL"),
            token=os.getenv("INFLUXDB_TOKEN"),
            org="homeiq",
            timeout=30_000  # 30 seconds
        )
        self.write_api = self.client.write_api()
        self.query_api = self.client.query_api()
    
    def close(self):
        self.client.close()
```

**Thread-Safe Pattern:**
```python
from threading import Lock

class ThreadSafeInfluxDBService:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.client = InfluxDBClient(
                        url=os.getenv("INFLUXDB_URL"),
                        token=os.getenv("INFLUXDB_TOKEN"),
                        org="homeiq"
                    )
        return cls._instance
    
    @property
    def write_api(self):
        return self.client.write_api()
    
    @property
    def query_api(self):
        return self.client.query_api()
```

## Retry Logic

### Basic Retry Pattern

**Using tenacity:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from influxdb_client.rest import ApiException

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ApiException, ConnectionError))
)
def write_with_retry(write_api, point):
    try:
        write_api.write(bucket="homeiq", record=point)
    except ApiException as e:
        logger.error(f"InfluxDB API error: {e}")
        raise
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        raise
```

### Advanced Retry Pattern

**With exponential backoff and jitter:**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ApiException, ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def write_with_advanced_retry(write_api, point):
    write_api.write(bucket="homeiq", record=point)
```

### Circuit Breaker Pattern

**Prevent cascading failures:**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def write_with_circuit_breaker(write_api, point):
    try:
        write_api.write(bucket="homeiq", record=point)
    except Exception as e:
        logger.error(f"Write failed: {e}")
        raise
```

## Error Handling

### Connection Error Handling

```python
from influxdb_client import InfluxDBClient
from influxdb_client.rest import ApiException
import logging

logger = logging.getLogger(__name__)

def create_influxdb_client():
    try:
        client = InfluxDBClient(
            url=os.getenv("INFLUXDB_URL"),
            token=os.getenv("INFLUXDB_TOKEN"),
            org="homeiq"
        )
        # Test connection
        client.ping()
        return client
    except ApiException as e:
        logger.error(f"Failed to connect to InfluxDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to InfluxDB: {e}")
        raise
```

### Write Error Handling

```python
def write_point_safe(write_api, point):
    try:
        write_api.write(bucket="homeiq", record=point)
    except ApiException as e:
        if e.status == 401:
            logger.error("Authentication failed - check token")
        elif e.status == 404:
            logger.error("Bucket or organization not found")
        elif e.status == 429:
            logger.warning("Rate limit exceeded - backing off")
            time.sleep(1)
        else:
            logger.error(f"InfluxDB API error: {e.status} - {e.reason}")
        raise
    except Exception as e:
        logger.error(f"Unexpected write error: {e}")
        raise
```

### Query Error Handling

```python
def query_safe(query_api, query):
    try:
        result = query_api.query(query)
        return result
    except ApiException as e:
        if e.status == 400:
            logger.error(f"Invalid Flux query: {e.reason}")
        elif e.status == 401:
            logger.error("Authentication failed - check token")
        else:
            logger.error(f"InfluxDB API error: {e.status} - {e.reason}")
        raise
    except Exception as e:
        logger.error(f"Unexpected query error: {e}")
        raise
```

## Async Patterns

### AsyncIO Pattern

```python
import asyncio
from influxdb_client_3 import InfluxDBClient3

async def write_async(points):
    client = InfluxDBClient3(
        host=os.getenv("INFLUXDB_HOST", "localhost:8086"),
        token=os.getenv("INFLUXDB_TOKEN"),
        database="homeiq"
    )
    
    try:
        await client.write(record=points, database="homeiq")
    finally:
        await client.close()

# Usage
asyncio.run(write_async(points))
```

### Async Context Manager

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_influxdb_client():
    client = InfluxDBClient3(
        host=os.getenv("INFLUXDB_HOST"),
        token=os.getenv("INFLUXDB_TOKEN"),
        database="homeiq"
    )
    try:
        yield client
    finally:
        await client.close()

# Usage
async def write_data(points):
    async with async_influxdb_client() as client:
        await client.write(record=points, database="homeiq")
```

## Batch Writing Patterns

### Basic Batch Write

```python
def write_batch(write_api, points, batch_size=5000):
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        try:
            write_api.write(bucket="homeiq", record=batch)
        except Exception as e:
            logger.error(f"Batch write failed: {e}")
            # Optionally: retry or store failed batch
```

### Buffered Batch Write

```python
from collections import deque

class BufferedInfluxDBWriter:
    def __init__(self, write_api, batch_size=5000, flush_interval=60):
        self.write_api = write_api
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer = deque()
        self.last_flush = time.time()
    
    def add_point(self, point):
        self.buffer.append(point)
        
        # Flush if buffer is full
        if len(self.buffer) >= self.batch_size:
            self.flush()
        
        # Flush if interval elapsed
        if time.time() - self.last_flush >= self.flush_interval:
            self.flush()
    
    def flush(self):
        if not self.buffer:
            return
        
        points = list(self.buffer)
        self.buffer.clear()
        
        try:
            self.write_api.write(bucket="homeiq", record=points)
            self.last_flush = time.time()
        except Exception as e:
            logger.error(f"Flush failed: {e}")
            # Optionally: re-add points to buffer
```

## Health Checks

### Connection Health Check

```python
def check_influxdb_health(client):
    try:
        # Ping InfluxDB
        health = client.health()
        if health.status == "pass":
            return True
        return False
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
```

### Readiness Check

```python
def check_influxdb_ready(client):
    try:
        # Query a simple test
        query = 'from(bucket: "homeiq") |> range(start: -1m) |> limit(n: 1)'
        result = client.query_api().query(query)
        return True
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return False
```

## Configuration Patterns

### Environment-Based Configuration

```python
import os
from influxdb_client import InfluxDBClient

def create_client_from_env():
    return InfluxDBClient(
        url=os.getenv("INFLUXDB_URL", "http://localhost:8086"),
        token=os.getenv("INFLUXDB_TOKEN", ""),
        org=os.getenv("INFLUXDB_ORG", "homeiq"),
        timeout=int(os.getenv("INFLUXDB_TIMEOUT", "30000"))
    )
```

### Configuration File Pattern

```python
import yaml
from influxdb_client import InfluxDBClient

def load_influxdb_config(config_path="config.yaml"):
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    return InfluxDBClient(
        url=config["influxdb"]["url"],
        token=config["influxdb"]["token"],
        org=config["influxdb"]["org"],
        timeout=config["influxdb"].get("timeout", 30000)
    )
```

## Testing Patterns

### Mock InfluxDB Client

```python
from unittest.mock import Mock, MagicMock

class MockInfluxDBClient:
    def __init__(self):
        self.write_api = Mock()
        self.query_api = Mock()
        self.ping = Mock(return_value={"status": "pass"})
    
    def close(self):
        pass
```

### Integration Test Fixture

```python
import pytest
from influxdb_client import InfluxDBClient

@pytest.fixture
def influxdb_client():
    client = InfluxDBClient(
        url=os.getenv("INFLUXDB_URL", "http://localhost:8086"),
        token=os.getenv("INFLUXDB_TOKEN", "test-token"),
        org="test"
    )
    yield client
    # Cleanup test data
    client.close()
```

## References

- [InfluxDB Python Client](https://github.com/influxdata/influxdb-client-python)
- [InfluxDB Connection Management](https://docs.influxdata.com/influxdb/v2.7/api-guide/client-libraries/python/)
- [Error Handling Best Practices](https://docs.influxdata.com/influxdb/v2.7/write-data/best-practices/)

