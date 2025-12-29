# Reviewer Agent Batch Processing Crash Analysis

## Problem Statement

The reviewer agent crashes when processing large batches of files, even with batching enabled. Connection errors occur during batch processing, causing the entire operation to fail.

## Root Cause Analysis

### Current Implementation Issues

1. **No Retry Logic**: The batch processing in `_process_file_batch()` catches exceptions but doesn't retry on connection errors
2. **Connection Pool Exhaustion**: Even with batching (10 files per batch, max 2 concurrent), connection errors can accumulate
3. **No Error Classification**: All exceptions are treated the same - no distinction between retryable (connection errors) and non-retryable (file not found) errors
4. **No Circuit Breaker**: If too many failures occur, the system continues trying, potentially making the situation worse
5. **No Exponential Backoff**: Fixed delays (0.2s between files, 1.0s between batches) don't help with transient connection issues

### Error Flow

```
Batch Processing
  ↓
Process File 1 → Connection Error → Caught → Marked as failed
Process File 2 → Connection Error → Caught → Marked as failed
...
Process File N → Connection Error → Process crashes (too many failures)
```

### Connection Error Sources

1. **LLM Feedback Generation**: When `include_llm_feedback=True`, the reviewer generates `GenericInstruction` objects that may trigger Cursor Skills API calls
2. **Context7 API Calls**: If Context7 is used for library documentation lookup
3. **Background Agent API**: If using Background Agent API for skill execution

## Solution Design

### 1. Retry Logic with Exponential Backoff

Add retry logic specifically for connection errors:

```python
async def process_single_file_with_retry(
    file_path: Path,
    command: str,
    reviewer: ReviewerAgent,
    max_retries: int = 3,
) -> tuple[Path, dict[str, Any]]:
    """Process file with retry logic for connection errors."""
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            result = await reviewer.run(command, file=str(file_path))
            if not isinstance(result, dict):
                return (file_path, {
                    "error": f"Unexpected result type: {type(result).__name__}",
                    "file": str(file_path)
                })
            return (file_path, result)
        except (ConnectionError, TimeoutError, OSError) as e:
            last_error = e
            if attempt < max_retries:
                backoff = min(2 ** attempt, 10.0)  # Exponential backoff, max 10s
                await asyncio.sleep(backoff)
                continue
        except Exception as e:
            # Non-retryable errors - return immediately
            return (file_path, {"error": str(e), "file": str(file_path)})
    
    # All retries exhausted
    return (file_path, {
        "error": f"Connection error after {max_retries} attempts: {str(last_error)}",
        "file": str(file_path),
        "retryable": True
    })
```

### 2. Circuit Breaker Pattern

Stop processing if too many failures occur:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        self.is_open = False
    
    def record_failure(self):
        """Record failure and check if circuit should open."""
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            self.last_failure_time = time.time()
    
    def should_allow(self) -> bool:
        """Check if operation should be allowed."""
        if not self.is_open:
            return True
        
        # Check if reset timeout has passed
        if self.last_failure_time:
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.reset_timeout:
                self.is_open = False
                self.failure_count = 0
                return True
        
        return False
```

### 3. Error Classification

Distinguish between retryable and non-retryable errors:

```python
def is_retryable_error(error: Exception) -> bool:
    """Check if error is retryable (connection-related)."""
    retryable_types = (
        ConnectionError,
        TimeoutError,
        OSError,
        requests.exceptions.RequestException,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    )
    
    error_str = str(error).lower()
    retryable_keywords = [
        "connection",
        "timeout",
        "network",
        "unreachable",
        "refused",
        "reset",
    ]
    
    return (
        isinstance(error, retryable_types) or
        any(keyword in error_str for keyword in retryable_keywords)
    )
```

### 4. Improved Batch Processing

Enhanced batch processing with all improvements:

```python
async def _process_file_batch(
    reviewer: ReviewerAgent,
    files: list[Path],
    command: str,
    max_workers: int = 4,
) -> dict[str, Any]:
    """Process files with retry logic and circuit breaker."""
    from ..feedback import get_feedback
    feedback = get_feedback()
    
    BATCH_SIZE = 10
    MAX_CONCURRENT = max(1, min(max_workers, 2))
    BATCH_DELAY = 1.0
    FILE_DELAY = 0.2
    MAX_RETRIES = 3
    
    circuit_breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60.0)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    async def process_single_file(file_path: Path) -> tuple[Path, dict[str, Any]]:
        """Process file with retry and circuit breaker."""
        # Check circuit breaker
        if not circuit_breaker.should_allow():
            return (file_path, {
                "error": "Circuit breaker open - too many failures",
                "file": str(file_path),
                "circuit_breaker": True
            })
        
        async with semaphore:
            await asyncio.sleep(FILE_DELAY)
            
            # Retry logic
            last_error = None
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    result = await reviewer.run(command, file=str(file_path))
                    if not isinstance(result, dict):
                        return (file_path, {
                            "error": f"Unexpected result type: {type(result).__name__}",
                            "file": str(file_path)
                        })
                    
                    # Success - record in circuit breaker
                    circuit_breaker.record_success()
                    return (file_path, result)
                    
                except Exception as e:
                    last_error = e
                    
                    # Check if retryable
                    if is_retryable_error(e) and attempt < MAX_RETRIES:
                        backoff = min(2 ** attempt, 10.0)
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        # Non-retryable or max retries reached
                        if is_retryable_error(e):
                            circuit_breaker.record_failure()
                        return (file_path, {
                            "error": str(e),
                            "file": str(file_path),
                            "retryable": is_retryable_error(e),
                            "attempts": attempt
                        })
            
            # All retries exhausted
            circuit_breaker.record_failure()
            return (file_path, {
                "error": f"Failed after {MAX_RETRIES} attempts: {str(last_error)}",
                "file": str(file_path),
                "retryable": True,
                "attempts": MAX_RETRIES
            })
    
    # Process in batches
    all_results = []
    total_batches = (len(files) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_idx in range(total_batches):
        # Check circuit breaker before processing batch
        if not circuit_breaker.should_allow():
            feedback.warning(
                f"Circuit breaker open - skipping remaining {len(files) - batch_idx * BATCH_SIZE} files"
            )
            # Mark remaining files as failed
            for remaining_file in files[batch_idx * BATCH_SIZE:]:
                all_results.append((remaining_file, {
                    "error": "Circuit breaker open - skipped",
                    "file": str(remaining_file),
                    "circuit_breaker": True
                }))
            break
        
        start_idx = batch_idx * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(files))
        batch_files = files[start_idx:end_idx]
        
        if total_batches > 1:
            feedback.info(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_files)} files)...")
        
        batch_tasks = [process_single_file(f) for f in batch_files]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        all_results.extend(batch_results)
        
        if batch_idx < total_batches - 1:
            await asyncio.sleep(BATCH_DELAY)
    
    # Aggregate results (same as before)
    # ...
```

## Implementation Plan

1. **Phase 1**: Add retry logic with exponential backoff
2. **Phase 2**: Add error classification (retryable vs non-retryable)
3. **Phase 3**: Add circuit breaker pattern
4. **Phase 4**: Add configuration options for retry/circuit breaker settings
5. **Phase 5**: Add comprehensive logging for debugging

## Configuration Options

Add to `.tapps-agents/config.yaml`:

```yaml
agents:
  reviewer:
    batch_processing:
      max_retries: 3
      retry_backoff_base: 2.0
      max_retry_backoff: 10.0
      circuit_breaker:
        enabled: true
        failure_threshold: 5
        reset_timeout: 60.0
      batch_size: 10
      max_concurrent: 2
      batch_delay: 1.0
      file_delay: 0.2
```

## Testing Strategy

1. **Unit Tests**: Test retry logic, circuit breaker, error classification
2. **Integration Tests**: Test with mock connection errors
3. **E2E Tests**: Test with actual large batch operations
4. **Load Tests**: Test with 100+ files to verify stability

## Related Issues

- Connection errors during batch processing
- No retry logic for transient failures
- Process crashes when too many files fail
- No circuit breaker to prevent cascading failures

## References

- `tapps_agents/cli/commands/reviewer.py` - Batch processing implementation
- `tapps_agents/agents/reviewer/agent.py` - Reviewer agent implementation
- `tapps_agents/workflow/parallel_executor.py` - Parallel execution with retries (reference)


