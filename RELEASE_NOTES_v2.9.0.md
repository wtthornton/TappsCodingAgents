# Release v2.9.0

## Bug Fixes

### Fixed Circular Reference Errors in Enhancer Agent

**Issue**: The enhancer agent was failing with "Circular reference detected" errors when trying to serialize complex data structures containing circular references to JSON.

**Solution**:
- Created shared JSON serialization utility (`tapps_agents/core/json_utils.py`) with circular reference handling
- Updated enhancer agent to use safe JSON serialization for all session and output data
- Circular references are now detected and replaced with `"<circular reference>"` placeholders instead of causing crashes

**Files Changed**:
- `tapps_agents/agents/enhancer/agent.py` - Added `_safe_json_dumps()` method and updated all `json.dumps()` calls
- `tapps_agents/core/json_utils.py` - New shared utility module for safe JSON serialization
- `docs/CIRCULAR_REFERENCE_FIX_SUMMARY.md` - Documentation of fix and areas that may need similar updates

**Impact**: Both `enhance` and `enhance-quick` commands now complete successfully even with complex nested data structures containing circular references.

## Improvements

- Enhanced error handling for JSON serialization across the framework
- Better debugging experience with clear circular reference placeholders in saved files

## Documentation

- Added comprehensive documentation identifying other areas that may need similar fixes
- Created migration guide for updating other code to use the safe JSON serialization utility

