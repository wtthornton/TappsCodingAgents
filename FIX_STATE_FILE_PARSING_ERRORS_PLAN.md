# Plan: Fix "Failed to parse state file" Errors

## Problem Summary

JSON state files are being read while still being written, causing incomplete/corrupted JSON files that trigger parsing errors:
- `JSONDecodeError: Expecting value: line 26 column 9 (char 724)`
- Files end abruptly mid-write (e.g., `"compliance_requirements": [` with no closing)
- StatusFileMonitor tries to parse all `.json` files, including incomplete ones

## Root Causes

1. **No Atomic File Writing**: Files are written directly without temp-then-rename pattern
2. **Race Condition**: StatusFileMonitor reads files while they're being written
3. **No File Validation**: No checks for complete/incomplete JSON before parsing
4. **No File Age Check**: Recently modified files are read immediately

## Solution Strategy

### Phase 1: Atomic File Writing
- Implement temp-then-rename pattern for all state file writes
- Ensures files are only visible when fully written

### Phase 2: File Validation & Retry Logic
- Add JSON validation before parsing
- Implement retry with exponential backoff for incomplete files
- Add file age check (wait 2 seconds after modification before reading)

### Phase 3: Error Handling Improvements
- Better error messages distinguishing incomplete vs corrupted files
- Skip files that are too small (likely incomplete)
- Log warnings instead of errors for recoverable issues

## Implementation Plan

### 1. Create Atomic File Writing Utility

**File**: `tapps_agents/workflow/file_utils.py` (new)
- Function: `atomic_write_json(path, data, **kwargs)`
- Writes to temp file first, then renames atomically
- Handles compression if needed

### 2. Update State File Writers

**Files to update**:
- `tapps_agents/workflow/state_manager.py` - `_write_state_file()` method
- `tapps_agents/workflow/cursor_executor.py` - `save_state()` method
- `tapps_agents/workflow/executor.py` - `save_state()` method

**Changes**:
- Replace direct `json.dump()` with `atomic_write_json()`
- Apply to all JSON file writes (state files, metadata, last.json)

### 3. Update StatusFileMonitor

**File**: `tapps_agents/workflow/status_monitor.py`
- Update `_load_state()` method:
  - Add file age check (skip if modified < 2 seconds ago)
  - Add JSON validation (try parsing, catch errors gracefully)
  - Add retry logic with exponential backoff
  - Check file size (skip if suspiciously small)
- Update `_check_status_files()`:
  - Filter out recently modified files
  - Better error handling

### 4. Add File Validation Helper

**File**: `tapps_agents/workflow/file_utils.py`
- Function: `is_valid_json_file(path, min_size=100)`
- Function: `is_file_stable(path, min_age_seconds=2)`
- Function: `safe_load_json(path, retries=3, backoff=0.5)`

## Testing Strategy

1. **Unit Tests**: Test atomic writing, validation, retry logic
2. **Integration Tests**: Test with concurrent read/write scenarios
3. **Manual Test**: Run workflow and verify no parsing errors

## Files to Modify

1. ✅ `tapps_agents/workflow/file_utils.py` - NEW - Atomic writing utilities
2. ✅ `tapps_agents/workflow/state_manager.py` - Update `_write_state_file()`
3. ✅ `tapps_agents/workflow/cursor_executor.py` - Update `save_state()`
4. ✅ `tapps_agents/workflow/executor.py` - Update `save_state()`
5. ✅ `tapps_agents/workflow/status_monitor.py` - Update `_load_state()` and `_check_status_files()`

## Success Criteria

- ✅ No more "Failed to parse state file" errors in logs
- ✅ State files are written atomically
- ✅ StatusFileMonitor handles incomplete files gracefully
- ✅ All existing corrupted files are skipped without errors

