# InfluxDB Patterns

## Overview

InfluxDB is a time-series database optimized for high-write throughput and efficient querying of time-stamped data. This guide covers InfluxDB 2.x patterns, data modeling, and best practices for HomeIQ and similar IoT/home automation systems.

## Core Concepts

### Data Model

**Measurement:** Similar to a table in SQL, contains time-series data
**Tags:** Indexed metadata (e.g., device_id, location, sensor_type)
**Fields:** Actual values (e.g., temperature, humidity, power)
**Timestamp:** Automatically indexed, precision matters

**Best Practice:**
- Use tags for frequently queried metadata (device_id, location)
- Use fields for actual measurements (temperature, voltage)
- Keep tag cardinality low (< 100,000 unique tag values)
- Use field keys for high-cardinality data

### Example Data Point

```
measurement: home_sensors
tags: device_id=sensor_001, location=kitchen, sensor_type=temperature
fields: value=72.5, unit=fahrenheit
timestamp: 2026-01-15T10:30:00Z
```

## Data Modeling Patterns

### Pattern 1: Device Sensor Data

**Use Case:** Home automation sensors (temperature, humidity, motion)

```flux
// Schema
measurement: "sensors"
tags:
  - device_id: "sensor_001"
  - location: "kitchen"
  - sensor_type: "temperature"
fields:
  - value: 72.5
  - unit: "fahrenheit"
  - battery_level: 85
```

**Query Pattern:**
```flux
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "sensors")
  |> filter(fn: (r) => r["location"] == "kitchen")
  |> filter(fn: (r) => r["sensor_type"] == "temperature")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
```

### Pattern 2: Energy Consumption

**Use Case:** Power monitoring, energy tracking

```flux
// Schema
measurement: "energy"
tags:
  - device_id: "smart_plug_001"
  - circuit: "kitchen_appliances"
  - device_type: "smart_plug"
fields:
  - power_watts: 1250.5
  - voltage: 120.2
  - current_amps: 10.4
  - cost_per_hour: 0.015
```

**Query Pattern:**
```flux
from(bucket: "homeiq")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "energy")
  |> filter(fn: (r) => r["circuit"] == "kitchen_appliances")
  |> integral(unit: 1h, column: "_value")
  |> map(fn: (r) => ({ r with total_kwh: r._value / 1000.0 }))
```

### Pattern 3: Event Logging

**Use Case:** Device events, state changes, alerts

```flux
// Schema
measurement: "events"
tags:
  - device_id: "door_sensor_001"
  - event_type: "door_opened"
  - severity: "info"
fields:
  - message: "Door opened at 10:30 AM"
  - duration_seconds: 0
```

## Flux Query Patterns

### Basic Query Structure

```flux
from(bucket: "homeiq")
  |> range(start: -1h)                    // Time range
  |> filter(fn: (r) => r["_measurement"] == "sensors")  // Filter measurement
  |> filter(fn: (r) => r["location"] == "kitchen")       // Filter tags
  |> aggregateWindow(every: 5m, fn: mean)               // Aggregation
  |> yield(name: "mean")                                  // Output
```

### Common Aggregations

**Mean (Average):**
```flux
|> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
```

**Sum:**
```flux
|> aggregateWindow(every: 1h, fn: sum, createEmpty: false)
```

**Min/Max:**
```flux
|> aggregateWindow(every: 1h, fn: min, createEmpty: false)
|> aggregateWindow(every: 1h, fn: max, createEmpty: false)
```

**Percentiles:**
```flux
|> quantile(q: 0.95, method: "exact_mean")
```

### Downsampling Pattern

**Use Case:** Reduce data retention while preserving trends

```flux
// Downsample 1-minute data to 1-hour averages
from(bucket: "homeiq")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "sensors")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> to(bucket: "homeiq_downsampled", org: "homeiq")
```

## Connection Patterns

### Python Client (influxdb-client)

**Basic Connection:**
```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

client = InfluxDBClient(
    url="http://localhost:8086",
    token="your-token",
    org="homeiq"
)

write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()
```

**Connection Pooling:**
```python
from influxdb_client import InfluxDBClient

# Reuse client instance (thread-safe)
client = InfluxDBClient(
    url="http://localhost:8086",
    token="your-token",
    org="homeiq",
    timeout=30_000  # 30 seconds
)

# Use context manager for automatic cleanup
with client.write_api() as write_api:
    point = Point("sensors").tag("device_id", "sensor_001").field("value", 72.5)
    write_api.write(bucket="homeiq", record=point)
```

**Async Pattern:**
```python
from influxdb_client_3 import InfluxDBClient3
import asyncio

async def write_data():
    client = InfluxDBClient3(
        host="localhost:8086",
        token="your-token",
        database="homeiq"
    )
    
    # Async write
    await client.write(
        record=[{"measurement": "sensors", "device_id": "sensor_001", "value": 72.5}],
        database="homeiq"
    )
```

### Retry Logic

```python
from influxdb_client import InfluxDBClient
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def write_with_retry(write_api, point):
    try:
        write_api.write(bucket="homeiq", record=point)
    except Exception as e:
        logger.error(f"Write failed: {e}")
        raise
```

## Performance Optimization

### Tag Cardinality

**Anti-Pattern:** High cardinality tags
```flux
// BAD: High cardinality (unique per timestamp)
tags: timestamp="2026-01-15T10:30:00Z"
```

**Best Practice:** Low cardinality tags
```flux
// GOOD: Low cardinality (reusable values)
tags: device_id="sensor_001", location="kitchen"
```

### Batch Writes

**Best Practice:** Batch multiple points
```python
points = [
    Point("sensors").tag("device_id", "sensor_001").field("value", 72.5),
    Point("sensors").tag("device_id", "sensor_002").field("value", 68.2),
    Point("sensors").tag("device_id", "sensor_003").field("value", 70.1),
]
write_api.write(bucket="homeiq", record=points)
```

### Query Optimization

**Use Specific Time Ranges:**
```flux
// GOOD: Specific range
|> range(start: -1h)

// BAD: Too broad
|> range(start: -365d)
```

**Filter Early:**
```flux
// GOOD: Filter before aggregation
|> filter(fn: (r) => r["location"] == "kitchen")
|> aggregateWindow(every: 1h, fn: mean)

// BAD: Aggregate before filtering
|> aggregateWindow(every: 1h, fn: mean)
|> filter(fn: (r) => r["location"] == "kitchen")
```

## Retention Policies

### Short-Term Data (Raw)

- **Retention:** 7-30 days
- **Bucket:** `homeiq_raw`
- **Use Case:** Real-time monitoring, debugging

### Medium-Term Data (Downsampled)

- **Retention:** 90-365 days
- **Bucket:** `homeiq_downsampled`
- **Downsample:** 1-minute → 1-hour averages
- **Use Case:** Trend analysis, reporting

### Long-Term Data (Aggregated)

- **Retention:** Indefinite
- **Bucket:** `homeiq_archive`
- **Downsample:** 1-hour → 1-day averages
- **Use Case:** Historical analysis, compliance

## Common Anti-Patterns

### 1. Storing Non-Time-Series Data

**Anti-Pattern:**
```flux
// BAD: User profiles don't belong in InfluxDB
measurement: "users"
tags: user_id="user_001"
fields: name="John Doe", email="john@example.com"
```

**Solution:** Use SQLite or PostgreSQL for metadata

### 2. High Tag Cardinality

**Anti-Pattern:**
```flux
// BAD: Unique timestamp as tag
tags: timestamp="2026-01-15T10:30:00.123456Z"
```

**Solution:** Timestamp is automatic, use for filtering

### 3. Writing Individual Points

**Anti-Pattern:**
```python
# BAD: One write per point
for point in points:
    write_api.write(bucket="homeiq", record=point)
```

**Solution:** Batch writes
```python
# GOOD: Batch write
write_api.write(bucket="homeiq", record=points)
```

### 4. Querying Without Time Range

**Anti-Pattern:**
```flux
// BAD: No time range (scans all data)
from(bucket: "homeiq")
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
```

**Solution:** Always specify time range
```flux
// GOOD: Specific time range
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
```

## HomeIQ-Specific Patterns

### Home Assistant Integration

**Pattern:** WebSocket events → InfluxDB
```python
# WebSocket event handler
async def handle_state_change(event):
    point = Point("home_assistant")
        .tag("entity_id", event.data["entity_id"])
        .tag("domain", event.data["domain"])
        .field("state", event.data["new_state"]["state"])
        .field("attributes", json.dumps(event.data["new_state"]["attributes"]))
        .time(event.time_fired)
    
    write_api.write(bucket="homeiq", record=point)
```

### Energy Monitoring

**Pattern:** Power data aggregation
```flux
// Calculate daily energy consumption
from(bucket: "homeiq")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "energy"))
  |> integral(unit: 1h)
  |> map(fn: (r) => ({ r with kwh: r._value / 1000.0 }))
  |> sum()
```

### Device Health Monitoring

**Pattern:** Track device connectivity
```flux
// Find devices that haven't reported in 1 hour
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "device_heartbeat")
  |> group(columns: ["device_id"])
  |> last()
  |> filter(fn: (r) => r["_time"] < now() - duration(v: 1h))
```

## Testing Patterns

### Mock InfluxDB Client

```python
from unittest.mock import Mock, MagicMock

class MockInfluxDBClient:
    def __init__(self):
        self.write_api = Mock()
        self.query_api = Mock()
    
    def write(self, bucket, record):
        # Validate point structure
        assert hasattr(record, 'tags')
        assert hasattr(record, 'fields')
        self.write_api.write(bucket=bucket, record=record)
```

### Integration Testing

```python
import pytest
from influxdb_client import InfluxDBClient

@pytest.fixture
def influxdb_client():
    client = InfluxDBClient(
        url=os.getenv("INFLUXDB_URL", "http://localhost:8086"),
        token=os.getenv("INFLUXDB_TOKEN"),
        org="test"
    )
    yield client
    # Cleanup test data
    client.close()
```

## References

- [InfluxDB Documentation](https://docs.influxdata.com/influxdb/v2.7/)
- [Flux Language Guide](https://docs.influxdata.com/flux/v0.x/)
- [InfluxDB Python Client](https://github.com/influxdata/influxdb-client-python)
- [Time-Series Data Modeling](https://docs.influxdata.com/influxdb/v2.7/write-data/best-practices/)

