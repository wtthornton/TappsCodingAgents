# Workflow State File Operations

**Version:** 1.0  
**Date:** December 2025  
**Status:** ✅ Complete

---

## Overview

This document describes the file operations used for workflow state persistence, focusing on atomic writes and safe reads to prevent corruption and race conditions.

---

## Atomic File Writing

### Problem

When state files are written directly, there's a window where the file exists but is incomplete. If another process (like `StatusFileMonitor`) tries to read the file during this window, it will see incomplete JSON and raise parsing errors:

```
Failed to parse state file .../full-sdlc-20251213-150718.json: Expecting value: line 26 column 9 (char 724)
```

### Solution: Temp-Then-Rename Pattern

All state file writes use atomic file operations:

1. **Write to Temp File**: Data is written to a temporary file (`.tmp` extension)
2. **Complete Write**: JSON is fully written and flushed
3. **Atomic Rename**: File is renamed atomically (single filesystem operation)
4. **Cleanup**: Temp file is removed on errors

This ensures files are only visible when fully written.

### Implementation

**Module:** `tapps_agents/workflow/file_utils.py`

```python
from tapps_agents.workflow.file_utils import atomic_write_json
from pathlib import Path

# Write state file atomically
atomic_write_json(
    path=Path(".tapps-agents/workflow-state/my-workflow.json"),
    data={"workflow_id": "my-workflow", "status": "running"},
    indent=2
)
```

**Features:**
- Supports compression (gzip)
- Automatic directory creation
- Error handling with temp file cleanup
- Thread-safe on most filesystems

---

## Safe File Reading

### Problem

Even with atomic writes, files may be:
- Still being written (race condition)
- Corrupted from previous errors
- Too small (incomplete)
- Recently modified (still in transition)

### Solution: Validation and Retry Logic

The `safe_load_json()` function provides:

1. **File Age Check**: Files must be at least 2 seconds old
2. **Size Validation**: Files below minimum size are considered incomplete
3. **JSON Validation**: Attempts to parse JSON before loading
4. **Retry Logic**: Automatic retries with exponential backoff
5. **Graceful Failure**: Returns None instead of raising errors

### Implementation

```python
from tapps_agents.workflow.file_utils import safe_load_json
from pathlib import Path

# Safely load state file
data = safe_load_json(
    path=Path(".tapps-agents/workflow-state/my-workflow.json"),
    retries=3,
    backoff=0.5,
    min_age_seconds=2.0,
    min_size=100
)

if data is None:
    print("File is incomplete, corrupted, or too new")
else:
    print(f"Loaded workflow: {data['workflow_id']}")
```

**Parameters:**
- `retries`: Number of retry attempts (default: 3)
- `backoff`: Backoff multiplier between retries (default: 0.5)
- `min_age_seconds`: Minimum file age before reading (default: 2.0)
- `min_size`: Minimum file size in bytes (default: 100)

---

## File Validation Utilities

### `is_valid_json_file(path, min_size=100) -> bool`

Check if a file contains valid JSON and meets minimum size.

```python
from tapps_agents.workflow.file_utils import is_valid_json_file

if is_valid_json_file(Path("state.json")):
    print("File is valid JSON")
```

### `is_file_stable(path, min_age_seconds=2.0) -> bool`

Check if a file has been stable (not modified recently).

```python
from tapps_agents.workflow.file_utils import is_file_stable

if is_file_stable(Path("state.json"), min_age_seconds=2.0):
    print("File is stable and safe to read")
```

---

## Usage in State Managers

### AdvancedStateManager

All state file writes in `AdvancedStateManager` use atomic writing:

```python
# In state_manager.py
from .file_utils import atomic_write_json

def _write_state_file(self, path: Path, data: dict[str, Any], compress: bool):
    """Write state file with optional compression using atomic write."""
    atomic_write_json(path, data, compress=compress, indent=2)
```

### StatusFileMonitor

All state file reads in `StatusFileMonitor` use safe loading:

```python
# In status_monitor.py
from .file_utils import safe_load_json, is_file_stable

def _load_state(self, state_file: Path) -> dict[str, Any] | None:
    # Skip files that are too new
    if not is_file_stable(state_file, min_age_seconds=2.0):
        return None
    
    # Use safe loading with retry logic
    return safe_load_json(state_file, retries=2, min_age_seconds=2.0)
```

---

## Performance Considerations

### Write Performance

- **Atomic writes are slightly slower** than direct writes (extra rename operation)
- **Overhead is minimal** (~1-2ms per write)
- **Benefits outweigh cost**: Prevents corruption and errors

### Read Performance

- **File age checks** prevent unnecessary read attempts
- **Retry logic** only activates when needed
- **Validation** happens before parsing (fast size check first)

### Best Practices

1. **Use atomic writes** for all state file operations
2. **Use safe loading** when reading files that may be in transition
3. **Set appropriate min_age_seconds** based on write frequency
4. **Monitor file sizes** to detect issues early

---

## Error Handling

### Write Errors

If atomic write fails:
- Temp file is automatically cleaned up
- Original file (if exists) is preserved
- Error is raised to caller

### Read Errors

If safe load fails:
- Returns None (doesn't raise exception)
- Logs debug message (not error, to reduce noise)
- Caller can handle None gracefully

### Corrupted Files

Corrupted files are:
- Detected during validation
- Skipped automatically
- Logged at debug level
- Don't cause workflow failures

---

## Migration Notes

### Before v2.0.8

- Direct file writes (race conditions possible)
- No file validation
- Parse errors on incomplete files
- No retry logic

### After v2.0.8

- Atomic file writes (no race conditions)
- File validation before reading
- Graceful handling of incomplete files
- Automatic retry with backoff

**Backward Compatibility:**
- Old corrupted files are automatically skipped
- New files are written atomically
- No breaking changes to API

---

## References

- [State Persistence Developer Guide](STATE_PERSISTENCE_DEVELOPER_GUIDE.md) - Complete state persistence documentation
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- `tapps_agents/workflow/file_utils.py` - Implementation source code

