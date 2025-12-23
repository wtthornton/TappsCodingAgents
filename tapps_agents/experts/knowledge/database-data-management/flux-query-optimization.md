# Flux Query Optimization

## Overview

Flux is InfluxDB's functional data scripting language. This guide covers query optimization patterns, performance best practices, and common pitfalls for HomeIQ and similar time-series applications.

## Query Performance Fundamentals

### Execution Order Matters

Flux queries execute left-to-right. Early filtering reduces data processed in later operations.

**Good Pattern:**
```flux
from(bucket: "homeiq")
  |> range(start: -1h)                    // 1. Limit time range (fast)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")  // 2. Filter tags (indexed)
  |> filter(fn: (r) => r["_value"] > 70.0)              // 3. Filter fields (slower)
  |> aggregateWindow(every: 5m, fn: mean)               // 4. Aggregate (on less data)
```

**Bad Pattern:**
```flux
from(bucket: "homeiq")
  |> filter(fn: (r) => r["_value"] > 70.0)              // 1. Filter fields (full scan!)
  |> range(start: -1h)                    // 2. Time range (too late)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")  // 3. Filter tags
  |> aggregateWindow(every: 5m, fn: mean)
```

## Optimization Patterns

### Pattern 1: Time Range First

**Always specify time range immediately after `from()`:**

```flux
// GOOD: Time range limits data scanned
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")

// BAD: No time range (scans all data)
from(bucket: "homeiq")
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
```

**Time Range Best Practices:**
- Use specific ranges: `-1h`, `-24h`, `-7d`
- Avoid very broad ranges: `-365d` (unless necessary)
- Use relative times: `start: -1h` (more efficient than absolute)

### Pattern 2: Tag Filtering Before Field Filtering

**Tags are indexed, fields are not:**

```flux
// GOOD: Tags first (uses index)
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")  // Tag (indexed)
  |> filter(fn: (r) => r["location"] == "kitchen")      // Tag (indexed)
  |> filter(fn: (r) => r["_value"] > 70.0)              // Field (not indexed)

// BAD: Fields first (full scan)
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_value"] > 70.0)              // Field (full scan!)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")  // Tag
```

### Pattern 3: Filter Early, Aggregate Late

**Reduce data volume before expensive operations:**

```flux
// GOOD: Filter before aggregation
from(bucket: "homeiq")
  |> range(start: -24h)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")  // Filter first
  |> aggregateWindow(every: 1h, fn: mean)               // Aggregate less data

// BAD: Aggregate before filtering
from(bucket: "homeiq")
  |> range(start: -24h)
  |> aggregateWindow(every: 1h, fn: mean)               // Aggregate all data
  |> filter(fn: (r) => r["device_id"] == "sensor_001")  // Filter aggregated data
```

### Pattern 4: Use Appropriate Aggregation Windows

**Match window size to query purpose:**

```flux
// Real-time monitoring: Small windows
|> aggregateWindow(every: 1m, fn: mean, createEmpty: false)

// Daily reports: Medium windows
|> aggregateWindow(every: 1h, fn: mean, createEmpty: false)

// Historical analysis: Large windows
|> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
```

**Window Size Guidelines:**
- **1m-5m:** Real-time dashboards, alerts
- **1h:** Daily reports, trend analysis
- **1d:** Historical analysis, long-term trends
- **1w:** Archive data, compliance

### Pattern 5: Limit Result Sets

**Use `limit()` to cap results:**

```flux
// GOOD: Limit results
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
  |> limit(n: 100)  // Limit to 100 points

// BAD: Return all results (potentially millions)
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
  // No limit
```

## Common Query Patterns

### Pattern 1: Latest Value per Device

```flux
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "sensors")
  |> group(columns: ["device_id"])
  |> last()
```

**Optimization:** Use specific time range, group by device_id

### Pattern 2: Time-Series Aggregation

```flux
from(bucket: "homeiq")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "sensors")
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
```

**Optimization:** Filter before aggregation, use appropriate window

### Pattern 3: Difference Calculation

```flux
from(bucket: "homeiq")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "energy")
  |> filter(fn: (r) => r["device_id"] == "smart_plug_001")
  |> difference()
```

**Optimization:** Filter first, then calculate difference

### Pattern 4: Percentile Calculation

```flux
from(bucket: "homeiq")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "sensors")
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
  |> quantile(q: 0.95, method: "exact_mean")
```

**Optimization:** Use `exact_mean` for better performance than `exact_selector`

### Pattern 5: Integral (Cumulative Sum)

```flux
from(bucket: "homeiq")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "energy")
  |> filter(fn: (r) => r["device_id"] == "smart_plug_001")
  |> integral(unit: 1h)
```

**Optimization:** Filter first, specify appropriate unit

## Anti-Patterns to Avoid

### Anti-Pattern 1: Querying Without Time Range

```flux
// BAD: No time range (scans all data)
from(bucket: "homeiq")
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
```

**Fix:**
```flux
// GOOD: Always specify time range
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
```

### Anti-Pattern 2: Filtering Fields Before Tags

```flux
// BAD: Field filter first (full scan)
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_value"] > 70.0)              // Field (not indexed)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")  // Tag (indexed)
```

**Fix:**
```flux
// GOOD: Tag filter first (uses index)
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")  // Tag (indexed)
  |> filter(fn: (r) => r["_value"] > 70.0)              // Field
```

### Anti-Pattern 3: Aggregating Before Filtering

```flux
// BAD: Aggregate all data first
from(bucket: "homeiq")
  |> range(start: -24h)
  |> aggregateWindow(every: 1h, fn: mean)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
```

**Fix:**
```flux
// GOOD: Filter before aggregating
from(bucket: "homeiq")
  |> range(start: -24h)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")
  |> aggregateWindow(every: 1h, fn: mean)
```

### Anti-Pattern 4: Using `map()` for Simple Transformations

```flux
// BAD: map() for simple arithmetic
|> map(fn: (r) => ({ r with kwh: r._value / 1000.0 }))
```

**Fix:**
```flux
// GOOD: Use built-in functions when possible
|> map(fn: (r) => ({ r with kwh: r._value / 1000.0 }))
// Or use integral() for cumulative calculations
```

### Anti-Pattern 5: Not Using `createEmpty: false`

```flux
// BAD: Creates empty windows
|> aggregateWindow(every: 1h, fn: mean)
```

**Fix:**
```flux
// GOOD: Skip empty windows
|> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
```

## Performance Monitoring

### Query Execution Time

**Monitor query performance:**
```flux
// Add timing to queries
option task = {name: "monitor_query_performance", every: 1h}

from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "sensors")
  |> aggregateWindow(every: 5m, fn: mean)
  |> yield(name: "mean")
```

### Query Optimization Checklist

- [ ] Time range specified immediately after `from()`
- [ ] Tag filters before field filters
- [ ] Filters before aggregations
- [ ] Appropriate aggregation window size
- [ ] `createEmpty: false` for aggregations
- [ ] `limit()` used when appropriate
- [ ] No unnecessary `map()` operations
- [ ] Grouping used appropriately

## HomeIQ-Specific Optimizations

### Optimization 1: Device-Specific Queries

```flux
// Optimized: Filter by device_id early
from(bucket: "homeiq")
  |> range(start: -1h)
  |> filter(fn: (r) => r["device_id"] == "sensor_001")  // Tag filter first
  |> filter(fn: (r) => r["_measurement"] == "sensors")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
```

### Optimization 2: Location-Based Queries

```flux
// Optimized: Filter by location (tag) early
from(bucket: "homeiq")
  |> range(start: -24h)
  |> filter(fn: (r) => r["location"] == "kitchen")      // Tag filter first
  |> filter(fn: (r) => r["_measurement"] == "sensors")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
```

### Optimization 3: Energy Consumption Queries

```flux
// Optimized: Filter before integral calculation
from(bucket: "homeiq")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "energy")
  |> filter(fn: (r) => r["circuit"] == "kitchen_appliances")  // Tag filter
  |> integral(unit: 1h)
  |> map(fn: (r) => ({ r with kwh: r._value / 1000.0 }))
```

## References

- [Flux Query Optimization](https://docs.influxdata.com/flux/v0.x/optimize-queries/)
- [Flux Performance Best Practices](https://docs.influxdata.com/influxdb/v2.7/query-data/flux/optimize-queries/)
- [Flux Language Guide](https://docs.influxdata.com/flux/v0.x/)

