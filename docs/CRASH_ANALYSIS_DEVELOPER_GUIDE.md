# Crash Analysis Fixes - Developer Guide

**Date:** January 16, 2026  
**Purpose:** Guide for developers on using the new utilities and patterns

## Quick Reference

### Using Centralized Debug Logger

**Before (❌ Wrong):**
```python
from pathlib import Path
log_path = Path.cwd() / ".cursor" / "debug.log"
try:
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({...}) + "\n")
except Exception as e:
    print(f"DEBUG LOG WRITE FAILED: {e}", file=sys.stderr)
```

**After (✅ Correct):**
```python
from ...core.debug_logger import write_debug_log

write_debug_log(
    {
        "sessionId": "session-123",
        "message": "Operation started",
        "data": {"file": "src/main.py"},
    },
    project_root=self._project_root,  # Optional, auto-detected if None
    location="agent.py:function:entry",  # Optional, for traceability
)
```

**Benefits:**
- ✅ Always uses project root (not current working directory)
- ✅ Non-blocking (never fails operations)
- ✅ Automatic directory creation
- ✅ Structured JSON logging

### Using PathValidator for Project Root

**Before (❌ Wrong):**
```python
project_root = project_root or Path.cwd()
output_dir = project_root / ".tapps-agents" / "artifacts"
```

**After (✅ Correct):**
```python
from ...core.path_validator import PathValidator

validator = PathValidator(project_root)  # Auto-detects if None
output_dir = validator.project_root / ".tapps-agents" / "artifacts"
```

**Benefits:**
- ✅ Consistent project root detection
- ✅ Works from any subdirectory
- ✅ Uses `.tapps-agents/` marker for detection

### Using Retry Logic for LLM Operations

**Before (❌ No Retry):**
```python
async def generate_feedback(self, code: str, ...):
    # LLM call that may fail on connection errors
    result = await llm_call(...)
    return result
```

**After (✅ With Retry):**
```python
from ...core.retry_handler import retry_on_connection_error

@retry_on_connection_error(max_retries=3, backoff_factor=2.0)
async def generate_feedback(self, code: str, ...):
    # LLM call with automatic retry on connection errors
    result = await llm_call(...)
    return result
```

**Benefits:**
- ✅ Automatic retry on connection failures
- ✅ Exponential backoff (prevents overwhelming server)
- ✅ Configurable retry attempts and delays
- ✅ Works for both async and sync functions

### Adding Progress Indicators

**Pattern for Long Operations:**
```python
import asyncio
from ..feedback import get_feedback

feedback = get_feedback()
start_time = asyncio.get_event_loop().time()
last_update = start_time
PROGRESS_INTERVAL = 5.0  # Update every 5 seconds

for i, item in enumerate(items):
    # Process item
    await process_item(item)
    
    # Update progress for operations >10 seconds
    current_time = asyncio.get_event_loop().time()
    elapsed = current_time - start_time
    
    if elapsed > 10.0 and (current_time - last_update) >= PROGRESS_INTERVAL:
        percent = ((i + 1) / len(items) * 100) if items else 0
        feedback.info(
            f"Processing: {i + 1}/{len(items)} ({percent:.1f}%) - {elapsed:.1f}s elapsed"
        )
        last_update = current_time
```

**Benefits:**
- ✅ User feedback during long operations
- ✅ Reduces timeout risk (user knows operation is progressing)
- ✅ Better user experience

---

## Migration Checklist

When updating code to use new patterns:

- [ ] Replace `Path.cwd()` with `PathValidator` for project-specific paths
- [ ] Replace inline debug log writes with `write_debug_log()`
- [ ] Add `@retry_on_connection_error` to LLM operations
- [ ] Add progress indicators for operations >10 seconds
- [ ] Test from project root ✅
- [ ] Test from subdirectory ✅
- [ ] Verify no linter errors ✅

---

## Common Patterns

### Pattern 1: Agent Initialization

```python
from ...core.path_validator import PathValidator

class MyAgent(BaseAgent):
    def __init__(self, project_root: Path | None = None):
        validator = PathValidator(project_root)
        self.project_root = validator.project_root
        # ... rest of initialization
```

### Pattern 2: File Operations

```python
from ...core.path_validator import PathValidator

validator = PathValidator()
output_path = validator.project_root / ".tapps-agents" / "output" / "file.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
```

### Pattern 3: Debug Logging

```python
from ...core.debug_logger import write_debug_log

write_debug_log(
    {"message": "Operation started", "data": {...}},
    project_root=self._project_root,
    location="agent.py:method:entry",
)
```

### Pattern 4: LLM Operations with Retry

```python
from ...core.retry_handler import retry_on_connection_error

@retry_on_connection_error(max_retries=3)
async def call_llm(self, prompt: str) -> str:
    # LLM operation
    return await llm.generate(prompt)
```

---

## Testing Patterns

### Test Path Resolution

```python
def test_path_resolution_from_subdirectory():
    """Test that paths resolve correctly from subdirectories."""
    # Change to subdirectory
    original_cwd = Path.cwd()
    subdir = original_cwd / "services" / "service1"
    subdir.mkdir(parents=True, exist_ok=True)
    
    try:
        import os
        os.chdir(subdir)
        
        # Test operation
        validator = PathValidator()
        assert validator.project_root == original_cwd  # Should detect project root
        
        # Test debug log
        write_debug_log({"test": "message"})
        log_path = get_debug_log_path()
        assert log_path.parent.parent == original_cwd  # Should be in project root
        
    finally:
        os.chdir(original_cwd)
```

---

## Best Practices

1. **Always use PathValidator** for project-specific paths
2. **Use write_debug_log()** instead of inline log writes
3. **Add retry logic** to all LLM operations
4. **Add progress indicators** for operations >10 seconds
5. **Test from subdirectories** to verify path resolution
6. **Use non-blocking error handling** for debug logs

---

## Related Documentation

- `CODEBASE_WIDE_CRASH_ANALYSIS_RECOMMENDATIONS.md` - Full recommendations
- `CRASH_ANALYSIS_IMPLEMENTATION_PLAN.md` - Implementation tracking
- `CRASH_ANALYSIS_IMPLEMENTATION_SUMMARY.md` - Progress summary
