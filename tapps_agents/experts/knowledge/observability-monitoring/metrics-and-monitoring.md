# Metrics and Monitoring

## Overview

Metrics provide quantitative measurements of system behavior over time. Unlike logs and traces which capture discrete events, metrics aggregate data points to show trends, patterns, and system health.

## Types of Metrics

### 1. Counter

**Purpose:** Count occurrences of events (monotonically increasing)

**Use Cases:**
- Request count
- Error count
- Total bytes processed
- Items created

**Example:**
```python
from prometheus_client import Counter

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_requests_total.labels(method='GET', endpoint='/api/users', status='200').inc()
```

**Characteristics:**
- Always increments
- Resets on process restart
- Good for rate calculations

### 2. Gauge

**Purpose:** Measure a value that can go up or down

**Use Cases:**
- Current memory usage
- Active connections
- Queue size
- Temperature

**Example:**
```python
from prometheus_client import Gauge

active_connections = Gauge(
    'active_connections',
    'Number of active connections',
    ['service']
)

active_connections.labels(service='api').set(42)
active_connections.labels(service='api').inc()  # Increase by 1
active_connections.labels(service='api').dec()  # Decrease by 1
```

**Characteristics:**
- Can increase or decrease
- Represents current state
- Not suitable for aggregation over time (use counter + rate)

### 3. Histogram

**Purpose:** Measure distribution of values in buckets

**Use Cases:**
- Request duration
- Response sizes
- Processing times
- Latency percentiles

**Example:**
```python
from prometheus_client import Histogram

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

with request_duration.labels(method='GET', endpoint='/api/users').time():
    # Process request
    pass
```

**Characteristics:**
- Pre-defined buckets
- Provides quantiles (p50, p95, p99)
- Fixed number of data points

### 4. Summary

**Purpose:** Similar to histogram, but calculates quantiles on the client side

**Use Cases:**
- When you need exact quantiles
- When bucket boundaries are not known in advance

**Example:**
```python
from prometheus_client import Summary

request_size = Summary(
    'http_request_size_bytes',
    'HTTP request size',
    ['method']
)

request_size.labels(method='POST').observe(1024)
```

**Characteristics:**
- Computes quantiles on client
- More expensive than histogram
- Use when exact quantiles needed

## Metric Naming Conventions

### Prometheus Naming Best Practices

**Format:** `{namespace}_{name}_{unit}_{suffix}`

**Components:**
- `namespace`: Service or application name (e.g., `http`, `db`, `cache`)
- `name`: Descriptive metric name
- `unit`: Unit of measurement (e.g., `seconds`, `bytes`, `total`)
- `suffix`: Type indicator (e.g., `total`, `count`, `sum`)

**Examples:**
```python
# Good naming
http_requests_total
http_request_duration_seconds
cache_hits_total
cache_miss_rate
db_connection_pool_size
memory_usage_bytes

# Bad naming
requests  # Too generic
req_time  # Abbreviated, unclear unit
cache     # Not descriptive
```

**Rules:**
- Use lowercase
- Separate words with underscores
- Use base units (seconds, bytes, not milliseconds, KB)
- End counters with `_total`
- End summaries/histograms with `_seconds` or `_bytes`

## Golden Signals

### 1. Latency

**Definition:** Time taken to serve a request

**Key Metrics:**
- Request duration (p50, p95, p99)
- Response time distribution
- Time to first byte (TTFB)

**Monitoring:**
```python
request_latency = Histogram(
    'http_request_duration_seconds',
    'Request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# Alert on: p99 latency > 1 second
```

### 2. Traffic

**Definition:** Demand placed on the system

**Key Metrics:**
- Requests per second (RPS)
- Concurrent connections
- Message throughput

**Monitoring:**
```python
request_rate = Counter(
    'http_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

# Alert on: Sudden drop in traffic (>50% decrease)
# Alert on: Traffic spike (>200% increase)
```

### 3. Errors

**Definition:** Rate of requests that fail

**Key Metrics:**
- Error rate (4xx, 5xx)
- Error count
- Exception rate

**Monitoring:**
```python
error_rate = Counter(
    'http_errors_total',
    'Total errors',
    ['status_code', 'error_type']
)

# Alert on: Error rate > 1%
# Alert on: 5xx errors > 0.1%
```

### 4. Saturation

**Definition:** How "full" the system is

**Key Metrics:**
- CPU utilization
- Memory usage
- Queue depth
- Disk I/O utilization

**Monitoring:**
```python
cpu_usage = Gauge('cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('memory_usage_bytes', 'Memory usage')
queue_depth = Gauge('queue_depth', 'Queue depth', ['queue_name'])

# Alert on: CPU > 80%
# Alert on: Memory > 90%
# Alert on: Queue depth > 1000
```

## Instrumentation Patterns

### 1. HTTP Server Metrics

```python
from prometheus_client import Counter, Histogram, Gauge
from flask import Flask, request

app = Flask(__name__)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'http_active_requests',
    'Currently active requests'
)

@app.before_request
def before_request():
    active_requests.inc()
    request._start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request._start_time
    active_requests.dec()
    
    http_request_duration.labels(
        method=request.method,
        endpoint=request.endpoint
    ).observe(duration)
    
    http_requests_total.labels(
        method=request.method,
        endpoint=request.endpoint,
        status=response.status_code
    ).inc()
    
    return response
```

### 2. Database Metrics

```python
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type', 'table']
)

db_connections = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_query_errors = Counter(
    'db_query_errors_total',
    'Database query errors',
    ['error_type']
)

def execute_query(query: str, query_type: str, table: str):
    with db_query_duration.labels(query_type=query_type, table=table).time():
        try:
            db_connections.inc()
            result = db.execute(query)
            return result
        except Exception as e:
            db_query_errors.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            db_connections.dec()
```

### 3. Business Metrics

```python
orders_created = Counter(
    'orders_created_total',
    'Total orders created',
    ['product_type', 'payment_method']
)

order_value = Histogram(
    'order_value_dollars',
    'Order value distribution',
    ['product_type'],
    buckets=[10, 50, 100, 500, 1000, 5000]
)

def create_order(product_type: str, payment_method: str, value: float):
    orders_created.labels(
        product_type=product_type,
        payment_method=payment_method
    ).inc()
    
    order_value.labels(product_type=product_type).observe(value)
```

## Monitoring Best Practices

### 1. Cardinality Management

**Problem:** Too many unique label combinations create too many time series

**Bad Example:**
```python
# Creates unique series for every user ID - BAD!
user_requests_total.labels(user_id=user_id).inc()
```

**Good Example:**
```python
# Use bounded label sets
user_requests_total.labels(user_tier='premium').inc()
```

**Guidelines:**
- Use bounded label values (status codes, not user IDs)
- Limit label cardinality (< 100 unique combinations)
- Use logs/traces for high-cardinality data

### 2. Aggregation Strategy

**Levels of Aggregation:**
- **Per-service:** Overall service health
- **Per-endpoint:** API endpoint performance
- **Per-instance:** Individual instance health

**Example:**
```python
# Service-level
service_requests_total = Counter('service_requests_total', ...)

# Endpoint-level
endpoint_requests_total = Counter(
    'endpoint_requests_total',
    ...,
    ['endpoint']
)
```

### 3. Retention and Storage

**Time Series Database Considerations:**
- Retention periods (15 days, 30 days, 1 year)
- Downsampling for long-term storage
- Compression strategies

**Example Retention:**
- Raw metrics: 15 days
- 5-minute aggregates: 30 days
- 1-hour aggregates: 1 year

### 4. Alerting Thresholds

**SLO-Based Alerting:**
- Alert when SLO is at risk
- Use burn rate for error budgets
- Alert on symptoms, not causes

**Example:**
```yaml
# Alert if error rate threatens SLO
- alert: HighErrorRate
  expr: |
    rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.01
  for: 5m
  annotations:
    summary: "Error rate above 1% for 5 minutes"
```

## Tools and Platforms

### Open Source

**Prometheus:**
- Time series database
- Pull-based metric collection
- Powerful query language (PromQL)
- Service discovery integration

**StatsD:**
- Simple metrics aggregation daemon
- Push-based (UDP)
- Language-agnostic
- Aggregates before storage

**Grafana:**
- Visualization and alerting platform
- Supports multiple data sources
- Rich dashboard ecosystem

### Commercial

**Datadog:**
- Infrastructure and application monitoring
- Custom metrics support
- AI-powered anomaly detection

**New Relic:**
- Full-stack observability
- Custom metrics
- Intelligent alerting

**CloudWatch (AWS):**
- Native AWS integration
- Custom metrics
- CloudWatch Alarms

## Metric Collection Patterns

### 1. Push vs Pull

**Pull Model (Prometheus):**
- Scraper polls endpoints
- Better for centralization
- Supports service discovery

**Push Model (StatsD, CloudWatch):**
- Services push metrics
- Simpler for ephemeral services
- Good for serverless

### 2. Export Strategies

**Direct Export:**
```python
# Export metrics directly
from prometheus_client import start_http_server
start_http_server(8000)  # Exposes /metrics endpoint
```

**Push Gateway:**
```python
# Push to gateway (for short-lived jobs)
from prometheus_client import CollectorRegistry, push_to_gateway

registry = CollectorRegistry()
# ... register metrics ...
push_to_gateway('pushgateway:9091', job='batch-job', registry=registry)
```

## Best Practices Summary

1. **Follow naming conventions** (namespace_name_unit_suffix)
2. **Use appropriate metric types** (counter, gauge, histogram, summary)
3. **Monitor golden signals** (latency, traffic, errors, saturation)
4. **Manage cardinality** (avoid high-cardinality labels)
5. **Instrument at the right granularity** (service, endpoint, operation)
6. **Set appropriate retention** periods
7. **Create actionable alerts** based on SLOs
8. **Use aggregation** for long-term trends
9. **Combine with logs and traces** for complete picture
10. **Document metrics** with clear descriptions and units

