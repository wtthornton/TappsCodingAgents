# Reviewer Agent Batch Processing Crash Fix

## Summary

Fixed crashes in reviewer agent batch processing by adding retry logic, circuit breaker pattern, and better error handling for connection errors.

## Changes Made

### 1. Retry Logic with Exponential Backoff

Added automatic retry for connection errors:
- **Max Retries**: 3 attempts per file
- **Exponential Backoff**: 2s, 4s, 8s (capped at 10s)
- **Retryable Errors**: ConnectionError, TimeoutError, OSError, and network-related errors

### 2. Circuit Breaker Pattern

Prevents cascading failures:
- **Failure Threshold**: Opens circuit after 5 consecutive failures
- **Reset Timeout**: 60 seconds before attempting to close circuit
- **Behavior**: Skips remaining files when circuit is open to prevent further failures

### 3. Error Classification

Distinguishes between retryable and non-retryable errors:
- **Retryable**: Connection errors, timeouts, network issues
- **Non-retryable**: File not found, invalid input, etc.
- **Smart Retry**: Only retries connection-related errors

### 4. Improved Logging

Better feedback during batch processing:
- Verbose mode shows retry attempts and backoff times
- Circuit breaker warnings when too many failures occur
- Clear error messages with retry information

## Code Changes

### New Classes and Functions

1. **`CircuitBreaker`**: Manages circuit breaker state
2. **`is_retryable_error()`**: Classifies errors as retryable or not
3. **Enhanced `_process_file_batch()`**: Includes retry logic and circuit breaker

### Key Improvements

```python
# Before: Simple exception catching
except Exception as e:
    return (file_path, {"error": str(e), "file": str(file_path)})

# After: Retry logic with exponential backoff
for attempt in range(1, MAX_RETRIES + 1):
    try:
        result = await reviewer.run(command, file=str(file_path))
        circuit_breaker.record_success()
        return (file_path, result)
    except Exception as e:
        if is_retryable_error(e) and attempt < MAX_RETRIES:
            backoff = min(2 ** attempt, 10.0)
            await asyncio.sleep(backoff)
            continue
        # Handle non-retryable or exhausted retries
```

## Configuration

Current settings (hardcoded, can be made configurable):

```python
BATCH_SIZE = 10              # Files per batch
MAX_CONCURRENT = 2           # Max concurrent operations
MAX_RETRIES = 3              # Retry attempts
RETRY_BACKOFF_BASE = 2.0     # Exponential backoff base
MAX_RETRY_BACKOFF = 10.0     # Max backoff time
CIRCUIT_BREAKER_THRESHOLD = 5  # Failures before opening circuit
CIRCUIT_BREAKER_RESET = 60.0   # Seconds before reset
```

## Usage

No changes required - the fix is automatic:

```bash
# Batch review with automatic retry and circuit breaker
tapps-agents reviewer review . --format json --output report.json

# Verbose mode shows retry attempts
tapps-agents reviewer review . --format json --verbose
```

## Expected Behavior

### Before Fix
- Connection error on file 1 → Marked as failed
- Connection error on file 2 → Marked as failed
- ... (continues until process crashes)

### After Fix
- Connection error on file 1 → Retry (2s delay) → Success
- Connection error on file 2 → Retry (2s delay) → Retry (4s delay) → Success
- 5 consecutive failures → Circuit breaker opens → Remaining files skipped with clear message

## Testing

To test the fix:

1. **Simulate Connection Errors**: Use network throttling or disconnect/reconnect
2. **Large Batch**: Process 100+ files to verify stability
3. **Monitor Logs**: Check for retry messages and circuit breaker warnings

## Related Files

- `tapps_agents/cli/commands/reviewer.py` - Batch processing implementation
- `docs/REVIEWER_BATCH_CRASH_ANALYSIS.md` - Root cause analysis

## Best Practices Applied

Based on industry best practices for AI agent batch processing:

1. **Error Taxonomy**: Clear distinction between retryable (transient) and non-retryable (permanent) errors
2. **Circuit Breakers**: Prevent cascading failures by halting operations when error threshold is exceeded
3. **Exponential Backoff**: Reduces load on failing services while giving them time to recover
4. **Context Preservation**: Error messages include file path and retry information for debugging
5. **Graceful Degradation**: Circuit breaker allows partial results instead of complete failure

## References

- [Exception Handling Frameworks for AI Agents](https://www.datagrid.com/blog/exception-handling-frameworks-ai-agents)
- [Preventing AI Agent Failure](https://galileo.ai/blog/prevent-ai-agent-failure)
- Industry best practices for async batch processing with connection error handling

## Future Improvements

1. **Configurable Settings**: Move hardcoded values to config.yaml
2. **Metrics**: Track retry success rates and circuit breaker events
3. **Adaptive Backoff**: Adjust backoff based on error patterns
4. **Partial Results**: Save progress periodically for large batches
5. **Context Snapshots**: Save state at batch boundaries for recovery
6. **Resource Monitoring**: Track CPU/memory usage during batch processing

