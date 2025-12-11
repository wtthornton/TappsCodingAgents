# Observability Best Practices

## Overview

Observability is the ability to understand a system's internal state from its external outputs. The three pillars of observability are logs, metrics, and traces, which together provide comprehensive visibility into system behavior.

## Three Pillars of Observability

### 1. Logs

**Purpose:** Discrete events with timestamps

**Use For:**
- Debugging specific requests
- Audit trails
- Error investigation
- User activity tracking

**Characteristics:**
- High cardinality
- Rich context
- Event-oriented
- Text or structured

### 2. Metrics

**Purpose:** Aggregated measurements over time

**Use For:**
- System health monitoring
- Performance trends
- Capacity planning
- Alerting

**Characteristics:**
- Low cardinality
- Aggregated data
- Time-series
- Numerical

### 3. Traces

**Purpose:** Request flow through distributed systems

**Use For:**
- Understanding request paths
- Identifying bottlenecks
- Debugging distributed issues
- Service dependency mapping

**Characteristics:**
- Request-oriented
- Cross-service
- Hierarchical
- Correlation IDs

## Correlation Across Pillars

### Unified Observability

**Link logs, metrics, and traces:**
```python
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

def process_request(request_id: str):
    span = tracer.start_span("process_request")
    span.set_attribute("request.id", request_id)
    
    # Log includes trace context
    logger.info("Processing request",
        extra={
            "request_id": request_id,
            "trace_id": format_trace_id(span.get_span_context().trace_id),
            "span_id": format_span_id(span.get_span_context().span_id)
        }
    )
    
    # Metrics include trace context for correlation
    request_counter.inc({
        "request_id": request_id,
        "trace_id": format_trace_id(span.get_span_context().trace_id)
    })
    
    try:
        result = do_work()
        span.set_status(trace.Status(trace.StatusCode.OK))
        return result
    except Exception as e:
        logger.error("Request failed", exc_info=True,
            extra={
                "request_id": request_id,
                "trace_id": format_trace_id(span.get_span_context().trace_id),
                "error": str(e)
            }
        )
        span.record_exception(e)
        span.set_status(trace.Status(trace.StatusCode.ERROR))
        raise
```

### Correlation IDs

**Propagate across services:**
```python
# Extract correlation ID from request
def extract_correlation_id(request):
    return (
        request.headers.get('X-Request-ID') or
        request.headers.get('X-Correlation-ID') or
        generate_request_id()
    )

# Include in all observability data
correlation_id = extract_correlation_id(request)
logger.info("Processing", extra={"correlation_id": correlation_id})
span.set_attribute("correlation.id", correlation_id)
metrics.labels(correlation_id=correlation_id).inc()
```

## Instrumentation Strategy

### What to Instrument

**Application Level:**
- Request handling
- Business logic operations
- External service calls
- Database operations
- Cache operations

**Infrastructure Level:**
- CPU, memory, disk
- Network I/O
- Container metrics
- Service mesh metrics

**Business Level:**
- User actions
- Transactions
- Conversions
- Revenue events

### Instrumentation Depth

**High-Value Operations:**
- User-facing operations
- Critical business logic
- External dependencies
- Expensive computations

**Lower Priority:**
- Internal helper functions
- Low-frequency operations
- Non-critical paths

### Automatic vs Manual Instrumentation

**Use Automatic For:**
- Common frameworks (HTTP, gRPC, databases)
- Standard libraries
- Quick wins
- Consistency

**Use Manual For:**
- Business-specific logic
- Custom protocols
- Critical paths needing detail
- Framework gaps

## Structured Data

### Structured Logs

**Benefits:**
- Machine-readable
- Queryable
- Aggregatable
- Consistent format

**Format:**
```json
{
  "timestamp": "2026-01-15T10:30:45.123Z",
  "level": "INFO",
  "service": "order-service",
  "message": "Order processed",
  "request_id": "abc123",
  "trace_id": "def456",
  "user_id": "user789",
  "order_id": "order123",
  "duration_ms": 245
}
```

### Semantic Conventions

**Use Standards:**
- OpenTelemetry semantic conventions
- Consistent attribute names
- Standard units
- Common labels

**Example:**
```python
# Follow OpenTelemetry conventions
span.set_attribute("http.method", "GET")
span.set_attribute("http.url", "/api/users")
span.set_attribute("http.status_code", 200)
span.set_attribute("db.system", "postgresql")
span.set_attribute("db.name", "users")
span.set_attribute("db.operation", "SELECT")
```

## Sampling Strategies

### When to Sample

**Always Record:**
- Errors and exceptions
- Critical business events
- Security events
- SLO violations

**Sample:**
- High-volume normal operations
- Debug-level logs
- Verbose traces
- Low-value metrics

### Sampling Approaches

**Head-Based Sampling:**
- Decide at trace start
- Consistent per trace
- Good for debugging
- Simple implementation

**Tail-Based Sampling:**
- Decide after trace completes
- Prioritize errors/slow traces
- Better cost optimization
- More complex

**Adaptive Sampling:**
- Adjust based on error rates
- Sample more errors
- Balance cost and visibility

**Example:**
```python
def should_sample_trace(trace_context):
    # Always sample errors
    if has_error(trace_context):
        return True
    
    # Sample slow traces
    if trace_duration > threshold:
        return True
    
    # Probabilistic sampling for normal traces
    return random.random() < sampling_rate
```

## Performance Considerations

### Overhead Management

**Minimize Impact:**
- Use async instrumentation
- Batch exports
- Sample appropriately
- Use efficient serialization

**Measure Overhead:**
```python
import time

overhead_start = time.time()
# Instrumentation code
overhead_end = time.time()
overhead_ms = (overhead_end - overhead_start) * 1000

if overhead_ms > 10:  # Alert if overhead > 10ms
    logger.warning("High instrumentation overhead", overhead_ms=overhead_ms)
```

### Async Operations

**Use Async Exporters:**
```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(endpoint="http://collector:4317")
processor = BatchSpanProcessor(exporter)
tracer_provider.add_span_processor(processor)
```

### Cardinality Management

**Control Label/Attribute Cardinality:**
```python
# Bad: High cardinality (unique per user)
metrics.labels(user_id=user_id).inc()

# Good: Bounded cardinality
metrics.labels(user_tier="premium").inc()

# High-cardinality data goes in logs/traces
logger.info("User action", user_id=user_id)
```

## Security and Privacy

### Sensitive Data

**Don't Log:**
- Passwords and tokens
- Credit card numbers
- PII (unless required)
- Full request/response bodies

**Redaction:**
```python
def redact_sensitive(message: str) -> str:
    # Redact credit cards
    message = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 
                    '[REDACTED]', message)
    # Redact emails
    message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    '[EMAIL_REDACTED]', message)
    return message
```

### Access Control

**Control Access:**
- Restrict log access
- Encrypt data in transit
- Encrypt data at rest
- Audit access to observability data

## Dashboard Design

### Effective Dashboards

**Principles:**
- Focus on user experience
- Show key metrics prominently
- Group related metrics
- Use appropriate visualizations
- Keep it simple

**Layout:**
1. **Top:** Golden signals (latency, traffic, errors, saturation)
2. **Middle:** Service-specific metrics
3. **Bottom:** Infrastructure metrics

**Visualization Types:**
- **Line graphs:** Trends over time
- **Gauges:** Current values
- **Tables:** Detailed breakdowns
- **Heatmaps:** Distribution patterns

### Dashboard Hierarchies

**Level 1: Service Overview**
- Overall health
- Key SLIs
- Error rates
- Traffic volume

**Level 2: Service Details**
- Per-endpoint metrics
- Dependency health
- Resource usage
- Error breakdown

**Level 3: Deep Dive**
- Individual request traces
- Detailed logs
- Profiling data
- Custom queries

## Best Practices Summary

### 1. Start Small

- Begin with critical paths
- Add instrumentation incrementally
- Focus on high-value areas
- Don't instrument everything at once

### 2. Use Standards

- OpenTelemetry for traces
- Prometheus for metrics
- Structured logging (JSON)
- Semantic conventions

### 3. Correlate Everything

- Include correlation IDs
- Link logs, metrics, traces
- Propagate context
- Use consistent identifiers

### 4. Sample Wisely

- Always record errors
- Sample normal operations
- Use adaptive sampling
- Balance cost and visibility

### 5. Manage Overhead

- Use async exporters
- Batch operations
- Measure impact
- Optimize hot paths

### 6. Control Cardinality

- Bounded label sets
- Avoid high-cardinality attributes
- Use logs for detailed data
- Aggregate metrics appropriately

### 7. Secure and Private

- Redact sensitive data
- Control access
- Encrypt data
- Audit access

### 8. Document and Educate

- Document instrumentation
- Share best practices
- Create runbooks
- Regular reviews

## Tools and Platforms

### Open Source Stack

**Collection:**
- Prometheus (metrics)
- Jaeger/Zipkin (traces)
- Fluentd/Fluent Bit (logs)

**Storage:**
- Prometheus (metrics)
- Elasticsearch (logs)
- Tempo (traces)

**Visualization:**
- Grafana (metrics and traces)
- Kibana (logs)
- Jaeger UI (traces)

### Commercial Platforms

**Full-Stack:**
- Datadog
- New Relic
- Dynatrace
- AppDynamics

**Specialized:**
- Honeycomb (traces)
- Splunk (logs)
- CloudWatch (AWS)
- Stackdriver (GCP)

## Summary

Effective observability requires:

1. **Three pillars:** Logs, metrics, and traces
2. **Correlation:** Link across all signals
3. **Standards:** Use semantic conventions
4. **Sampling:** Balance cost and visibility
5. **Performance:** Minimize overhead
6. **Security:** Protect sensitive data
7. **Documentation:** Share knowledge
8. **Iteration:** Continuous improvement

