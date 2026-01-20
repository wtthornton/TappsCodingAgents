# Context7 API Fixes

## Issue 1: API Authentication Header (Updated January 2026)

### Problem

The Context7 API authentication method was tested and verified. Testing showed:

```python
# Testing results:
# Authorization: Bearer {key} -> Quota Tier: "free" (AUTHENTICATED)
# X-API-Key: {key}            -> Quota Tier: "anonymous" (NOT authenticated)
```

### Correct Authentication

Context7 API uses **Bearer token authentication**:

```python
# CORRECT - Context7 API expects Authorization Bearer header
headers = {"Authorization": f"Bearer {api_key}"}
```

### Solution

Authentication header in `tapps_agents/context7/backup_client.py` uses:

```python
headers={
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
},
```

### Verification

After the fix:
- ✅ API calls return **HTTP 200** with library results
- ✅ Dashboard shows requests being counted (e.g., 2/500)
- ✅ "LAST USED" timestamp updates for the API key

---

## Issue 2: Quota Exceeded Handling

### Problem Summary

When Context7 API quota is actually exceeded, the framework was:
1. Making multiple API calls in parallel for each detected library
2. Not checking quota status before making API calls
3. Continuing to attempt API calls even after quota errors were detected
4. Potentially causing process crashes or connection exhaustion from repeated failures
5. Showing misleading progress indicators while API calls were failing

### Root Causes

1. **No Early Quota Check**: `get_documentation_for_libraries()` started parallel execution without checking quota status first
2. **No Circuit Breaker Integration**: Quota errors weren't detected by the circuit breaker, allowing continued attempts
3. **Late Quota Detection**: Quota was only detected after making HTTP requests, not before
4. **No Fail-Fast Logic**: Each library lookup attempted API calls even when quota was already known to be exceeded

## Solution Design

### 1. Early Quota Detection
- Added quota check in `get_documentation_for_libraries()` **before** starting parallel execution
- Returns empty results immediately if quota is exceeded, avoiding all API calls
- Added per-library quota check as defense-in-depth

### 2. Circuit Breaker Integration
- Enhanced circuit breaker to detect quota errors and open immediately (bypass threshold)
- Quota errors now immediately set circuit breaker to OPEN state
- Subsequent requests are rejected without making API calls

### 3. Pre-API Quota Check
- Added quota check in `lookup.py` before making any API calls
- Skips API calls entirely if quota is already exceeded
- Returns error result immediately without network requests

### 4. HTTP Response Handling
- Enhanced 429 (quota exceeded) response handling to:
  - Mark quota as exceeded globally
  - Open circuit breaker immediately
  - Provide clear error messages

## Implementation Details

### Files Modified

1. **`tapps_agents/context7/agent_integration.py`**
   - Added early quota check in `get_documentation_for_libraries()` before parallel execution
   - Added per-library quota check in `lookup_library()` function

2. **`tapps_agents/context7/circuit_breaker.py`**
   - Enhanced `call()` method to detect quota errors in exceptions
   - Opens circuit breaker immediately on quota errors (bypasses threshold)

3. **`tapps_agents/context7/lookup.py`**
   - Added quota check before making API calls in `lookup()` method
   - Returns error result immediately if quota is exceeded

4. **`tapps_agents/context7/backup_client.py`**
   - Enhanced 429 response handling to mark quota and open circuit breaker
   - Added `time` import for circuit breaker state management

### Code Changes

#### Early Quota Check (agent_integration.py)

```python
# CRITICAL FIX: Check quota BEFORE starting parallel execution
try:
    from .backup_client import is_context7_quota_exceeded, get_context7_quota_message
    if is_context7_quota_exceeded():
        quota_msg = get_context7_quota_message() or "Monthly quota exceeded"
        logger.warning(
            f"Context7 API quota exceeded ({quota_msg}). "
            f"Skipping documentation lookup for {len(libraries)} libraries."
        )
        return {lib: None for lib in libraries}  # Fast-fail without API calls
except Exception as e:
    logger.debug(f"Error checking Context7 quota status: {e}")
```

#### Circuit Breaker Quota Detection (circuit_breaker.py)

```python
# CRITICAL FIX: Detect quota errors and open circuit immediately
error_msg = str(e).lower()
is_quota_error = (
    "quota exceeded" in error_msg
    or "429" in error_msg
)

if is_quota_error:
    # Immediately open circuit on quota error - no need to wait for threshold
    if self._stats.state == CircuitState.CLOSED:
        self._stats.state = CircuitState.OPEN
        # Mark quota as exceeded globally
        try:
            from .backup_client import _mark_context7_quota_exceeded
            _mark_context7_quota_exceeded(quota_msg)
        except Exception:
            pass
```

#### Pre-API Quota Check (lookup.py)

```python
# CRITICAL FIX: Check quota BEFORE making API calls
try:
    from .backup_client import is_context7_quota_exceeded, get_context7_quota_message
    if is_context7_quota_exceeded():
        quota_msg = get_context7_quota_message() or "Monthly quota exceeded"
        logger.debug(f"Context7 API quota exceeded. Skipping API call.")
        return LookupResult(success=False, error=f"Quota exceeded: {quota_msg}")
except Exception:
    pass  # Continue if quota check fails
```

#### HTTP Response Quota Handling (backup_client.py)

```python
elif response.status_code == 429:
    # Mark quota as exceeded globally
    _mark_context7_quota_exceeded(quota_message)
    
    # Open circuit breaker immediately
    try:
        from .circuit_breaker import get_context7_circuit_breaker, CircuitState
        circuit_breaker = get_context7_circuit_breaker()
        if hasattr(circuit_breaker, '_stats'):
            circuit_breaker._stats.state = CircuitState.OPEN
            circuit_breaker._stats.last_failure_time = time.time()
            circuit_breaker._stats.last_state_change = time.time()
    except Exception:
        pass  # Graceful degradation
```

## Benefits

1. **Zero Unnecessary API Calls**: When quota is exceeded, no API calls are made
2. **Fast Failure**: Quota detection happens immediately, before parallel execution
3. **Circuit Breaker Protection**: Quota errors immediately open circuit breaker
4. **Better Error Messages**: Clear user-facing messages about quota status
5. **Resource Efficiency**: Prevents connection exhaustion and process crashes
6. **Defense in Depth**: Multiple layers of quota checking for robustness

## Testing

To test the fix:

1. **Simulate Quota Exceeded**:
   ```python
   from tapps_agents.context7.backup_client import _mark_context7_quota_exceeded
   _mark_context7_quota_exceeded("Test quota exceeded")
   ```

2. **Try Multiple Library Lookups**:
   ```python
   helper = Context7AgentHelper(config, mcp_gateway)
   docs = await helper.get_documentation_for_libraries(
       libraries=["fastapi", "react", "pytest", "django", "flask"]
   )
   # Should return {lib: None for lib in libraries} without making API calls
   ```

3. **Verify No API Calls**:
   - Check logs for "Skipping documentation lookup" message
   - Verify no HTTP requests are made (network monitoring)
   - Circuit breaker should be OPEN state

## Migration Notes

- **Backward Compatible**: Existing code continues to work
- **No Configuration Changes**: Works automatically with existing quota detection
- **Graceful Degradation**: If quota check fails, code continues (log at debug level)

## Related Issues

- Fixes issue where multiple libraries × 2 calls each = many quota errors
- Prevents process crashes from connection exhaustion
- Eliminates misleading progress indicators during quota errors
- Reduces log spam from repeated quota errors

---

## Files Modified

| File | Change |
|------|--------|
| `tapps_agents/context7/backup_client.py` | Fixed auth header: `Bearer` → `X-API-Key` |
| `tapps_agents/context7/agent_integration.py` | Added early quota check before parallel execution |
| `tapps_agents/context7/circuit_breaker.py` | Enhanced quota error detection |
| `tapps_agents/context7/lookup.py` | Added pre-API quota check |

## Context7 API Reference

### Authentication

Context7 API uses Bearer token authentication:

```bash
curl -X GET "https://context7.com/api/v2/search?query=fastapi" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Endpoints

| Endpoint | Purpose | Parameters |
|----------|---------|------------|
| `/api/v2/search` | Search for libraries | `query` |
| `/api/v2/docs/{mode}/{library_id}` | Get documentation | `type`, `topic`, `page` |

### Rate Limits

- Free tier: 500 requests/month
- Each API key has its own quota counter
- Check `ratelimit-remaining` header for current quota

### Updating API Key

If your API key has exhausted quota, you can create a new key at https://context7.com/dashboard
and update it using:

```bash
# Option 1: Environment variable (temporary)
$env:CONTEXT7_API_KEY="your-new-api-key"

# Option 2: Store in encrypted storage (permanent)
python scripts/update_context7_key.py --key "your-new-api-key"
```
