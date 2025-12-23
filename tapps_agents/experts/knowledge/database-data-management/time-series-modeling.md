# Time-Series Data Modeling

## Overview

Time-series data modeling requires different patterns than traditional relational databases. This guide covers time-series data architecture, schema design, and optimization strategies for HomeIQ and similar IoT/home automation systems.

## Time-Series Data Characteristics

### Key Properties

1. **Temporal Ordering:** Data points are ordered by time
2. **High Write Throughput:** Many writes, fewer reads
3. **Append-Only:** Data is typically inserted, rarely updated
4. **Time-Based Queries:** Most queries filter by time range
5. **Downsampling:** Older data is often aggregated

### Data Lifecycle

```
Raw Data (1-minute intervals)
  ↓ [7 days]
Downsampled Data (1-hour averages)
  ↓ [90 days]
Aggregated Data (1-day averages)
  ↓ [Indefinite]
Archived Data (1-week averages)
```

## Schema Design Patterns

### Pattern 1: Single Measurement, Multiple Sensors

**Use Case:** Multiple sensors of the same type

```flux
measurement: "temperature"
tags:
  - device_id: "sensor_001"
  - location: "kitchen"
  - unit: "fahrenheit"
fields:
  - value: 72.5
  - battery: 85
```

**Pros:**
- Simple queries across all sensors
- Easy aggregation
- Consistent schema

**Cons:**
- Can't store sensor-specific metadata easily

### Pattern 2: Separate Measurements per Sensor Type

**Use Case:** Different sensor types with different fields

```flux
measurement: "temperature"
tags: device_id, location
fields: value, unit

measurement: "humidity"
tags: device_id, location
fields: value, unit

measurement: "motion"
tags: device_id, location
fields: detected, confidence
```

**Pros:**
- Type-specific fields
- Clear separation
- Optimized for each type

**Cons:**
- Harder to query across types
- More complex queries

### Pattern 3: Hierarchical Tags

**Use Case:** Multi-level organization (home → room → device)

```flux
measurement: "sensors"
tags:
  - home_id: "home_001"
  - floor: "first"
  - room: "kitchen"
  - device_id: "sensor_001"
  - sensor_type: "temperature"
fields:
  - value: 72.5
```

**Pros:**
- Flexible querying at any level
- Easy aggregation by level

**Cons:**
- Higher tag cardinality
- More complex queries

## Data Modeling Best Practices

### 1. Tag vs Field Decision

**Use Tags For:**
- Frequently filtered values
- Low cardinality (< 100,000 unique values)
- Metadata that doesn't change often
- Values used in GROUP BY

**Use Fields For:**
- Actual measurements
- High cardinality values
- Values that change frequently
- Values used in aggregations (sum, mean, etc.)

**Example:**
```flux
// GOOD: device_id as tag (low cardinality, frequently filtered)
tags: device_id="sensor_001"
fields: temperature=72.5, humidity=45.2

// BAD: temperature as tag (high cardinality)
tags: temperature="72.5"
fields: device_id="sensor_001"
```

### 2. Cardinality Management

**Problem:** High tag cardinality slows queries

**Solution:** Limit unique tag combinations
```flux
// BAD: High cardinality (unique per write)
tags: timestamp="2026-01-15T10:30:00.123456Z"

// GOOD: Low cardinality (reusable values)
tags: device_id="sensor_001", location="kitchen"
```

**Cardinality Limits:**
- **Low:** < 1,000 unique values (ideal)
- **Medium:** 1,000 - 10,000 (acceptable)
- **High:** 10,000 - 100,000 (monitor performance)
- **Very High:** > 100,000 (avoid if possible)

### 3. Field Type Selection

**Numeric Fields:**
- Use for measurements (temperature, power, etc.)
- Supports aggregations (mean, sum, etc.)

**String Fields:**
- Use for status, state, messages
- Limited aggregation support

**Boolean Fields:**
- Use for binary states (on/off, detected/not detected)

**Example:**
```flux
fields:
  - temperature: 72.5        // float (numeric)
  - status: "online"          // string
  - motion_detected: true     // boolean
```

## Retention and Downsampling Strategies

### Strategy 1: Tiered Retention

**Raw Data (High Resolution):**
- Retention: 7 days
- Resolution: 1 minute
- Use: Real-time monitoring, debugging

**Downsampled Data (Medium Resolution):**
- Retention: 90 days
- Resolution: 1 hour
- Use: Trend analysis, daily reports

**Aggregated Data (Low Resolution):**
- Retention: 1 year
- Resolution: 1 day
- Use: Historical analysis, compliance

**Archived Data (Very Low Resolution):**
- Retention: Indefinite
- Resolution: 1 week
- Use: Long-term trends, research

### Strategy 2: Continuous Queries

**Automated Downsampling:**
```flux
// Downsample 1-minute data to 1-hour averages
option task = {name: "downsample_hourly", every: 1h}

from(bucket: "homeiq_raw")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "sensors")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> to(bucket: "homeiq_hourly", org: "homeiq")
```

### Strategy 3: Data Lifecycle Policies

**Automated Deletion:**
```flux
// Delete data older than retention period
from(bucket: "homeiq_raw")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_time"] < now() - duration(v: 7d))
  |> delete()
```

## Query Optimization Patterns

### Pattern 1: Time Range Filtering

**Always specify time range first:**
```flux
// GOOD: Time range first
from(bucket: "homeiq")
  |> range(start: -1h)  // Limits data scanned
  |> filter(fn: (r) => r["device_id"] == "sensor_001")

// BAD: Filter before time range
from(bucket: "homeiq")
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
  |> range(start: -1h)  // Scans all data first
```

### Pattern 2: Tag Filtering Before Field Filtering

**Filter tags before fields:**
```flux
// GOOD: Tags first (indexed)
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")  // Tag (indexed)
  |> filter(fn: (r) => r["_value"] > 70.0)              // Field (not indexed)

// BAD: Fields first
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_value"] > 70.0)              // Field (full scan)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")  // Tag
```

### Pattern 3: Aggregation Window Size

**Match window size to query needs:**
```flux
// Real-time monitoring: 1-minute windows
|> aggregateWindow(every: 1m, fn: mean)

// Daily reports: 1-hour windows
|> aggregateWindow(every: 1h, fn: mean)

// Historical analysis: 1-day windows
|> aggregateWindow(every: 1d, fn: mean)
```

## HomeIQ-Specific Patterns

### Pattern 1: Home Assistant State Tracking

**Schema:**
```flux
measurement: "home_assistant_states"
tags:
  - entity_id: "sensor.kitchen_temperature"
  - domain: "sensor"
  - device_id: "sensor_001"
  - location: "kitchen"
fields:
  - state: "72.5"
  - attributes: '{"unit_of_measurement": "°F", "friendly_name": "Kitchen Temperature"}'
```

**Query Pattern:**
```flux
// Get latest state for all entities
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "home_assistant_states")
  |> group(columns: ["entity_id"])
  |> last()
```

### Pattern 2: Energy Consumption Tracking

**Schema:**
```flux
measurement: "energy_consumption"
tags:
  - device_id: "smart_plug_001"
  - circuit: "kitchen_appliances"
  - device_type: "smart_plug"
fields:
  - power_watts: 1250.5
  - voltage: 120.2
  - current_amps: 10.4
  - energy_kwh: 0.125
```

**Query Pattern:**
```flux
// Calculate daily energy consumption
from(bucket: "homeiq")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "energy_consumption")
  |> filter(fn: (r) => r["circuit"] == "kitchen_appliances")
  |> integral(unit: 1h, column: "_value")
  |> map(fn: (r) => ({ r with total_kwh: r._value / 1000.0 }))
```

### Pattern 3: Device Health Monitoring

**Schema:**
```flux
measurement: "device_health"
tags:
  - device_id: "sensor_001"
  - device_type: "temperature_sensor"
  - location: "kitchen"
fields:
  - battery_level: 85
  - signal_strength: -65
  - last_seen: 1633024800
  - status: "online"
```

**Query Pattern:**
```flux
// Find devices with low battery
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "device_health")
  |> filter(fn: (r) => r["battery_level"] < 20)
  |> group(columns: ["device_id"])
  |> last()
```

## Common Anti-Patterns

### 1. Storing Non-Time-Series Data

**Anti-Pattern:**
```flux
// BAD: User profiles in time-series DB
measurement: "users"
tags: user_id="user_001"
fields: name="John", email="john@example.com"
```

**Solution:** Use SQLite or PostgreSQL for metadata

### 2. High Tag Cardinality

**Anti-Pattern:**
```flux
// BAD: Unique timestamp as tag
tags: timestamp="2026-01-15T10:30:00.123456Z"
```

**Solution:** Timestamp is automatic, don't duplicate

### 3. Storing Computed Values

**Anti-Pattern:**
```flux
// BAD: Storing computed daily total
fields: daily_total_kwh=12.5
```

**Solution:** Compute on-the-fly or use downsampling

### 4. Over-Normalization

**Anti-Pattern:**
```flux
// BAD: Too many separate measurements
measurement: "temperature_kitchen_sensor_001"
measurement: "temperature_kitchen_sensor_002"
```

**Solution:** Use tags for differentiation
```flux
// GOOD: Single measurement with tags
measurement: "temperature"
tags: location="kitchen", device_id="sensor_001"
```

## Performance Considerations

### Write Performance

**Batch Writes:**
- Write multiple points in single request
- Optimal batch size: 5,000-10,000 points
- Use async writes for high throughput

**Connection Pooling:**
- Reuse client instances
- Use connection pooling
- Implement retry logic

### Read Performance

**Index Usage:**
- Tags are indexed automatically
- Fields are not indexed
- Filter by tags first, then fields

**Query Optimization:**
- Use specific time ranges
- Filter early in query pipeline
- Use appropriate aggregation windows
- Limit result sets

### Storage Optimization

**Data Compression:**
- InfluxDB compresses data automatically
- Use appropriate field types
- Avoid storing redundant data

**Retention Policies:**
- Delete old data automatically
- Use downsampling to reduce storage
- Archive old data to cheaper storage

## References

- [InfluxDB Data Modeling](https://docs.influxdata.com/influxdb/v2.7/write-data/best-practices/)
- [Time-Series Database Design](https://www.influxdata.com/time-series-database/)
- [Flux Query Optimization](https://docs.influxdata.com/flux/v0.x/optimize-queries/)

