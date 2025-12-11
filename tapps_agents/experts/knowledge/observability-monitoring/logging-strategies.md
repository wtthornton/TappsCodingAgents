# Logging Strategies

## Overview

Logging provides a chronological record of events and activities in a system. Effective logging strategies are essential for debugging, auditing, compliance, and understanding system behavior.

## Logging Levels

### Standard Levels (RFC 5424)

**DEBUG:**
- Detailed diagnostic information
- Typically only enabled during development
- Use for: Variable values, execution flow, detailed state

**INFO:**
- General informational messages
- Confirms normal operation
- Use for: Service start/stop, configuration loaded, milestones

**WARN:**
- Warning messages for potentially harmful situations
- System continues operating normally
- Use for: Deprecated API usage, slow operations, retry attempts

**ERROR:**
- Error events that may allow application to continue
- Indicates failure in application component
- Use for: Failed operations, exceptions caught and handled

**FATAL/CRITICAL:**
- Very severe error events
- Application may abort
- Use for: Critical failures, system unavailability

### Level Selection Guidelines

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG: Development and troubleshooting
logger.debug("Processing user %s with options %s", user_id, options)

# INFO: Normal operations
logger.info("User %s logged in successfully", user_id)

# WARN: Unexpected but handled situations
logger.warning("Failed to send email to %s, will retry", email)

# ERROR: Errors that are caught and handled
logger.error("Failed to process order %s: %s", order_id, error, exc_info=True)

# CRITICAL: System-threatening errors
logger.critical("Database connection pool exhausted", exc_info=True)
```

## Structured Logging

### Why Structured Logging?

**Benefits:**
- Machine-readable (JSON format)
- Easy to query and filter
- Supports aggregation and analysis
- Better for distributed systems

**Example:**
```python
import json
import logging

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
    
    def info(self, message, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def error(self, message, **kwargs):
        self.logger.error(message, extra=kwargs)

# Usage
logger = StructuredLogger(__name__)
logger.info("Order processed", 
    order_id="12345",
    user_id="67890",
    amount=99.99,
    currency="USD",
    status="completed"
)
```

### JSON Log Format

**Standard Fields:**
```json
{
  "timestamp": "2026-01-15T10:30:45.123Z",
  "level": "INFO",
  "service": "order-service",
  "message": "Order processed",
  "order_id": "12345",
  "user_id": "67890",
  "duration_ms": 245,
  "trace_id": "abc123",
  "span_id": "def456"
}
```

## Context and Correlation

### Request Correlation

**Add correlation IDs to all logs:**
```python
import logging
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id')

class CorrelationFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get(None)
        record.trace_id = get_trace_id()  # From OpenTelemetry
        return True

logger.addFilter(CorrelationFilter())
```

### Contextual Logging

**Use context managers for operation scoping:**
```python
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def log_operation(operation_name, **context):
    start_time = time.time()
    logger.info(f"Starting {operation_name}", extra=context)
    try:
        yield
        duration = time.time() - start_time
        logger.info(f"Completed {operation_name}", 
                   extra={**context, "duration_ms": duration * 1000})
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed {operation_name}", 
                    extra={**context, "duration_ms": duration * 1000},
                    exc_info=True)
        raise

# Usage
with log_operation("process_order", order_id="12345", user_id="67890"):
    # Process order
    pass
```

## Log Aggregation and Storage

### Centralized Logging

**Why Centralize:**
- Distributed systems span multiple services
- Containers/instances are ephemeral
- Need unified view across system
- Enable search and correlation

**Architecture:**
```
Services → Log Shippers → Log Aggregator → Storage → Search/Analysis
```

### Log Shippers

**Fluentd:**
- Open-source log collector
- Plugin ecosystem
- JSON transformation

**Fluent Bit:**
- Lightweight log processor
- Good for containers
- Lower resource usage

**Filebeat:**
- Elastic's log shipper
- Lightweight
- Integrates with Elasticsearch

**Vector:**
- High-performance observability pipeline
- Rust-based
- Transformations and routing

### Storage Solutions

**Elasticsearch + Logstash + Kibana (ELK):**
- Full-text search
- Powerful querying
- Visual dashboards

**Loki:**
- Log aggregation system (Grafana Labs)
- Label-based indexing
- Prometheus-compatible queries

**Cloud Logging:**
- AWS CloudWatch Logs
- Google Cloud Logging
- Azure Monitor Logs

## Log Retention and Rotation

### Retention Policies

**Development:**
- 7-14 days retention
- Debug logs enabled

**Production:**
- 30-90 days for application logs
- 1+ year for audit logs
- Compliance requirements may vary

### Log Rotation

**Size-based Rotation:**
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'app.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
```

**Time-based Rotation:**
```python
from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler(
    'app.log',
    when='midnight',
    interval=1,
    backupCount=30
)
```

## Security and Privacy

### Sensitive Data Handling

**Don't Log:**
- Passwords and tokens
- Credit card numbers
- Social security numbers
- Full request/response bodies (may contain PII)

**Redaction Patterns:**
```python
import re

def redact_sensitive_data(message: str) -> str:
    # Redact credit cards
    message = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 
                    '[REDACTED]', message)
    # Redact emails
    message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    '[EMAIL_REDACTED]', message)
    return message

logger.info(f"User login: {redact_sensitive_data(user_email)}")
```

### Audit Logging

**What to Audit:**
- Authentication and authorization events
- Data access and modifications
- Configuration changes
- Administrative actions

**Audit Log Requirements:**
- Immutable (append-only)
- Long retention (compliance)
- Tamper-evident
- Complete context

```python
def audit_log(action: str, user_id: str, resource: str, **details):
    logger.info("AUDIT",
        action=action,
        user_id=user_id,
        resource=resource,
        timestamp=datetime.utcnow().isoformat(),
        **details
    )

# Usage
audit_log("CREATE", user_id="admin", resource="user", target_user_id="12345")
audit_log("DELETE", user_id="admin", resource="order", order_id="67890")
```

## Performance Considerations

### Async Logging

**Use Async Handlers:**
```python
from logging.handlers import QueueHandler, QueueListener
import queue

log_queue = queue.Queue(-1)
queue_handler = QueueHandler(log_queue)
stream_handler = logging.StreamHandler()
listener = QueueListener(log_queue, stream_handler)
listener.start()

logger.addHandler(queue_handler)
```

### Sampling

**Sample debug logs in production:**
```python
import random

def sampled_debug(message, sample_rate=0.1):
    if random.random() < sample_rate:
        logger.debug(message)

# Use for high-volume debug logs
sampled_debug("Processing item", sample_rate=0.01)
```

### Conditional Logging

**Avoid expensive string formatting:**
```python
# Bad: Always formats string
logger.debug(f"Processing user {user_id} with complex data {expensive_operation()}")

# Good: Only formats if level enabled
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"Processing user {user_id} with complex data {expensive_operation()}")

# Better: Lazy formatting
logger.debug("Processing user %s with complex data %s", 
            user_id, expensive_operation())
```

## Best Practices

### 1. Meaningful Messages

```python
# Bad: Vague message
logger.error("Error occurred")

# Good: Specific with context
logger.error("Failed to process payment",
    order_id=order_id,
    payment_method=payment_method,
    error_code=error.code,
    exc_info=True
)
```

### 2. Consistent Format

- Use structured logging
- Include timestamps (UTC)
- Add correlation IDs
- Standard field names

### 3. Appropriate Levels

- DEBUG: Development only
- INFO: Normal operations
- WARN: Handled issues
- ERROR: Caught exceptions
- CRITICAL: System failures

### 4. Include Context

- Request IDs
- User IDs
- Resource IDs
- Operation names
- Duration metrics

### 5. Error Logging

```python
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed",
        operation="risky_operation",
        error_type=type(e).__name__,
        error_message=str(e),
        exc_info=True  # Include stack trace
    )
```

### 6. Don't Log Too Much

- Avoid logging in tight loops
- Don't log every iteration
- Use appropriate levels
- Sample when necessary

### 7. Don't Log Too Little

- Log entry/exit of important operations
- Log state changes
- Log external calls
- Log errors with context

## Tools and Libraries

### Python

**structlog:**
- Structured logging library
- Context propagation
- Multiple formatters

**python-json-logger:**
- JSON formatter for standard logging
- Simple integration

### JavaScript/Node.js

**pino:**
- Fast JSON logger
- Child loggers
- Levels

**winston:**
- Flexible logging library
- Multiple transports
- Formatting

### Java

**Logback:**
- Successor to Log4j
- Flexible configuration
- Multiple appenders

**Log4j2:**
- High performance
- Async logging
- Plugin architecture

## Summary

Effective logging requires:
1. **Structured format** for machine readability
2. **Appropriate levels** for different scenarios
3. **Context inclusion** (IDs, timestamps, correlation)
4. **Centralized aggregation** for distributed systems
5. **Security considerations** (redact sensitive data)
6. **Performance awareness** (async, sampling, conditional)
7. **Retention policies** based on requirements
8. **Consistent patterns** across services

