# Distributed Tracing Best Practices

## Overview

Distributed tracing provides visibility into requests as they flow through microservices, helping identify bottlenecks, errors, and performance issues across complex distributed systems.

## Key Concepts

### OpenTelemetry Standard

OpenTelemetry is the open standard for observability, providing:
- Unified instrumentation APIs across languages
- Vendor-neutral instrumentation
- Automatic and manual instrumentation support
- Standard trace context propagation (W3C Trace Context)

### Trace Components

**Trace:**
- Complete request lifecycle from entry point to completion
- Contains multiple spans representing operations
- Identified by a unique trace ID

**Span:**
- Individual operation within a trace
- Represents work done by a single service
- Contains start time, duration, status, attributes, and events

**Span Context:**
- Trace ID and Span ID
- Propagated across service boundaries
- Maintains causality relationships

**Baggage:**
- Custom key-value pairs propagated across spans
- Use sparingly (affects performance)
- Useful for cross-cutting concerns

## Instrumentation Strategies

### 1. Auto-instrumentation

**When to Use:**
- Common frameworks (HTTP, gRPC, database drivers)
- Standard libraries already supported
- Quick setup with minimal code changes

**Example:**
```python
# OpenTelemetry auto-instrumentation
from opentelemetry.instrumentation.requests import RequestsInstrumentor
RequestsInstrumentor().instrument()
```

**Benefits:**
- Zero code changes
- Consistent instrumentation
- Framework best practices

### 2. Manual Instrumentation

**When to Use:**
- Custom business logic
- Critical paths requiring detailed visibility
- Framework not supported by auto-instrumentation

**Example:**
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("order.type", "premium")
        
        try:
            # Business logic
            result = validate_order(order_id)
            span.add_event("order.validated", {"status": "success"})
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            raise
```

### 3. Sampling Strategies

**Always-On Sampling:**
- 100% of traces recorded
- Use for: Low-traffic services, critical paths

**Probabilistic Sampling:**
- Sample percentage of traces
- Use for: High-traffic services, cost optimization

**Rate Limiting Sampling:**
- Sample N traces per second
- Use for: Protecting backend systems

**Dynamic Sampling:**
- Adjust sampling rate based on error rates
- Use for: Balancing cost and visibility

## Span Naming Conventions

### Best Practices

**Use hierarchical, descriptive names:**
```python
# Good: Clear, hierarchical naming
span.set_name("user_service.get_user_profile")
span.set_name("payment_service.process_payment")
span.set_name("order_service.calculate_total")

# Bad: Generic or unclear names
span.set_name("function_call")
span.set_name("operation")
span.set_name("do_work")
```

**Naming Patterns:**
- `{service}.{operation}` - Most common pattern
- `{service}.{resource}.{action}` - For REST APIs
- `{component}.{method}` - For library code

## Context Propagation

### W3C Trace Context Standard

**Headers to Propagate:**
- `traceparent` - Trace ID, Span ID, trace flags
- `tracestate` - Vendor-specific trace data

**HTTP Example:**
```python
from opentelemetry.propagate import inject, extract

# Client side: Inject context into headers
headers = {}
inject(headers)
response = requests.get(url, headers=headers)

# Server side: Extract context from headers
context = extract(request.headers)
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("handle_request", context=context):
    # Process request
    pass
```

### Cross-Service Propagation

**Best Practices:**
- Always propagate trace context across service boundaries
- Include correlation IDs for business context
- Use middleware/plugins for automatic propagation

## Span Attributes

### Recommended Attributes

**Service Identity:**
```python
span.set_attribute("service.name", "user-service")
span.set_attribute("service.version", "1.2.3")
span.set_attribute("service.namespace", "production")
```

**Operation Context:**
```python
span.set_attribute("http.method", "GET")
span.set_attribute("http.url", "/api/users/123")
span.set_attribute("http.status_code", 200)
span.set_attribute("db.system", "postgresql")
span.set_attribute("db.name", "users")
span.set_attribute("db.operation", "SELECT")
```

**Business Context:**
```python
span.set_attribute("user.id", user_id)
span.set_attribute("order.id", order_id)
span.set_attribute("payment.amount", amount)
```

**Error Context:**
```python
span.set_attribute("error", True)
span.set_attribute("error.type", "ValidationError")
span.set_attribute("error.message", error_message)
```

### Attribute Best Practices

- Use semantic conventions (OpenTelemetry specs)
- Avoid high-cardinality values (don't include full request bodies)
- Include enough context to debug issues
- Standardize attribute names across services

## Common Patterns

### 1. Async Operations

```python
async def async_operation():
    tracer = trace.get_tracer(__name__)
    span = tracer.start_span("async_operation")
    
    try:
        ctx = trace.set_span_in_context(span)
        result = await some_async_call(ctx)
        span.set_status(trace.Status(trace.StatusCode.OK))
        return result
    except Exception as e:
        span.record_exception(e)
        span.set_status(trace.Status(trace.StatusCode.ERROR))
        raise
    finally:
        span.end()
```

### 2. Database Operations

```python
def execute_query(query: str):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("db.query") as span:
        span.set_attribute("db.statement", query)
        span.set_attribute("db.system", "postgresql")
        
        start_time = time.time()
        result = db.execute(query)
        duration = time.time() - start_time
        
        span.set_attribute("db.duration_ms", duration * 1000)
        span.set_attribute("db.rows_returned", len(result))
        return result
```

### 3. External API Calls

```python
def call_external_api(url: str):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("http.request") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.url", url)
        
        headers = {}
        inject(headers)  # Propagate trace context
        
        try:
            response = requests.get(url, headers=headers)
            span.set_attribute("http.status_code", response.status_code)
            span.set_status(trace.Status(trace.StatusCode.OK))
            return response
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            raise
```

## Error Handling

### Recording Exceptions

```python
try:
    risky_operation()
except Exception as e:
    span.record_exception(e, escaped=True)  # escaped=True for exceptions that bubble up
    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
    raise
```

### Status Codes

- `UNSET` - Default status, operation not explicitly set
- `OK` - Operation completed successfully
- `ERROR` - Operation completed with error

## Performance Considerations

### Sampling

- Use probabilistic sampling for high-traffic services
- Increase sampling for error traces
- Implement adaptive sampling based on load

### Overhead Management

- Minimize span attributes (avoid large payloads)
- Use async exporters where possible
- Batch span exports
- Use appropriate sampling rates

### Cost Optimization

- Sample traces, not log every request
- Filter out noisy spans (health checks, metrics endpoints)
- Use sampling based on error rates (sample more errors)

## Tools and Platforms

### Open Source

**Jaeger:**
- Distributed tracing platform
- UI for trace visualization
- Supports multiple storage backends

**Zipkin:**
- Distributed tracing system
- HTTP-based collection
- Simple deployment

**Tempo:**
- Grafana's tracing backend
- Object storage backend
- High scalability

### Commercial

**Datadog APM:**
- Full observability platform
- Automatic instrumentation
- AI-powered insights

**New Relic:**
- Application performance monitoring
- Distributed tracing
- Error tracking

**Honeycomb:**
- High-cardinality data analysis
- Event-based architecture
- Powerful query interface

## Integration Patterns

### Service Mesh Integration

- Automatic trace propagation in service meshes (Istio, Linkerd)
- Configurable sampling at mesh level
- Cross-service visibility without code changes

### Framework Integration

- Express.js middleware for Node.js
- Spring Boot auto-configuration for Java
- Django middleware for Python
- Rails instrumentation for Ruby

## Best Practices Summary

1. **Always propagate context** across service boundaries
2. **Use semantic conventions** for attribute names
3. **Sample appropriately** to balance cost and visibility
4. **Include business context** (user IDs, order IDs) in spans
5. **Record exceptions** with full stack traces
6. **Use hierarchical span names** following naming conventions
7. **Minimize attribute cardinality** to reduce storage costs
8. **Combine with metrics and logs** for complete observability

