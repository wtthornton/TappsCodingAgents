# Best Practices for Batch Processing with Connection Error Handling

## Overview

This document outlines the best practices applied to fix the reviewer agent batch processing crashes, based on industry standards and research.

## Key Principles

### 1. Error Taxonomy

**Distinguish between retryable and non-retryable errors:**

- **Retryable (Transient)**: Network timeouts, connection errors, service unavailable
- **Non-retryable (Permanent)**: File not found, invalid input, syntax errors

**Implementation:**
```python
def is_retryable_error(error: Exception) -> bool:
    """Classify errors as retryable or non-retryable."""
    # Check error types and error messages
    # Only retry transient issues
```

### 2. Circuit Breaker Pattern

**Prevent cascading failures:**

- Monitor failure rate
- Open circuit when threshold exceeded
- Skip remaining operations when circuit is open
- Auto-reset after timeout

**Benefits:**
- Prevents system overload
- Gives failing services time to recover
- Provides clear feedback to users

**Implementation:**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60.0):
        # Opens after 5 failures
        # Resets after 60 seconds
```

### 3. Exponential Backoff

**Reduce load on failing services:**

- Start with short delay (2s)
- Double delay on each retry (2s, 4s, 8s)
- Cap maximum delay (10s)
- Only retry retryable errors

**Benefits:**
- Gives services time to recover
- Reduces unnecessary load
- Prevents retry storms

**Implementation:**
```python
backoff = min(2 ** attempt, 10.0)  # Exponential, capped at 10s
await asyncio.sleep(backoff)
```

### 4. Context Preservation

**Maintain state for debugging and recovery:**

- Include file path in error messages
- Track retry attempts
- Record circuit breaker state
- Preserve partial results

**Benefits:**
- Easier debugging
- Can resume from last successful state
- Better error reporting

### 5. Graceful Degradation

**Continue processing when possible:**

- Process files that succeed
- Skip files that fail after retries
- Return partial results
- Don't crash on individual failures

**Benefits:**
- Maximizes throughput
- Provides useful results even with failures
- Better user experience

## Implementation Details

### Retry Logic

```python
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0
MAX_RETRY_BACKOFF = 10.0

for attempt in range(1, MAX_RETRIES + 1):
    try:
        result = await operation()
        return result
    except Exception as e:
        if is_retryable_error(e) and attempt < MAX_RETRIES:
            backoff = min(RETRY_BACKOFF_BASE ** attempt, MAX_RETRY_BACKOFF)
            await asyncio.sleep(backoff)
            continue
        raise
```

### Circuit Breaker

```python
circuit_breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60.0)

if not circuit_breaker.should_allow():
    # Skip operation
    return error_result

try:
    result = await operation()
    circuit_breaker.record_success()
    return result
except Exception as e:
    if is_retryable_error(e):
        circuit_breaker.record_failure()
    raise
```

### Error Classification

```python
RETRYABLE_TYPES = (
    ConnectionError,
    TimeoutError,
    OSError,
    requests.exceptions.RequestException,
    aiohttp.ClientError,
)

RETRYABLE_KEYWORDS = [
    "connection",
    "timeout",
    "network",
    "unreachable",
    "refused",
    "reset",
]

NON_RETRYABLE_KEYWORDS = [
    "file not found",
    "permission denied",
    "invalid",
    "malformed",
]
```

## Configuration Recommendations

### Batch Processing Settings

```yaml
agents:
  reviewer:
    batch_processing:
      # Retry configuration
      max_retries: 3
      retry_backoff_base: 2.0
      max_retry_backoff: 10.0
      
      # Circuit breaker
      circuit_breaker:
        enabled: true
        failure_threshold: 5
        reset_timeout: 60.0
      
      # Batch configuration
      batch_size: 10
      max_concurrent: 2
      batch_delay: 1.0
      file_delay: 0.2
```

### Error Handling Settings

```yaml
error_handling:
  # Retryable error patterns
  retryable_keywords:
    - "connection"
    - "timeout"
    - "network"
    - "unreachable"
  
  # Non-retryable error patterns
  non_retryable_keywords:
    - "file not found"
    - "permission denied"
    - "invalid"
```

## Monitoring and Metrics

### Key Metrics to Track

1. **Retry Success Rate**: Percentage of retries that succeed
2. **Circuit Breaker Events**: How often circuit opens/closes
3. **Average Retry Attempts**: How many retries before success
4. **Error Distribution**: Retryable vs non-retryable errors
5. **Batch Completion Rate**: Percentage of files processed successfully

### Logging Recommendations

```python
# Log retry attempts
logger.info(f"Retrying {file} after connection error (attempt {attempt}/{max_retries})")

# Log circuit breaker events
logger.warning(f"Circuit breaker opened after {failure_count} failures")

# Log error classification
logger.debug(f"Error classified as {'retryable' if retryable else 'non-retryable'}")
```

## Testing Strategy

### Unit Tests

- Test retry logic with mock errors
- Test circuit breaker state transitions
- Test error classification
- Test exponential backoff calculation

### Integration Tests

- Test with actual connection errors
- Test with network throttling
- Test with service unavailability
- Test circuit breaker behavior

### Load Tests

- Test with 100+ files
- Test with high failure rate
- Test with intermittent failures
- Test recovery after circuit breaker reset

## References

1. [Exception Handling Frameworks for AI Agents](https://www.datagrid.com/blog/exception-handling-frameworks-ai-agents)
2. [Preventing AI Agent Failure](https://galileo.ai/blog/prevent-ai-agent-failure)
3. [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
4. [Exponential Backoff](https://en.wikipedia.org/wiki/Exponential_backoff)

## Related Documentation

- `docs/REVIEWER_BATCH_CRASH_ANALYSIS.md` - Root cause analysis
- `docs/REVIEWER_BATCH_CRASH_FIX.md` - Implementation details


