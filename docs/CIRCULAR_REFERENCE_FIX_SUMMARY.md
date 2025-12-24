# Circular Reference Fix Summary

## Problem

The enhancer agent (and potentially other areas) was failing with "Circular reference detected" errors when trying to serialize complex data structures containing circular references to JSON.

## Solution

### 1. Created Shared Utility Module

**File**: `tapps_agents/core/json_utils.py` (NEW)

Provides two functions:
- `safe_json_dumps()` - Drop-in replacement for `json.dumps()` with circular reference handling
- `safe_json_dump()` - Drop-in replacement for `json.dump()` with circular reference handling

**Features**:
- Detects circular references and replaces them with `"<circular reference>"`
- Handles datetime, Path, and other common types
- Only tracks mutable objects (dicts, lists, custom objects) for efficiency
- Graceful error handling with fallback to error strings

### 2. Fixed Enhancer Agent

**File**: `tapps_agents/agents/enhancer/agent.py`

- Added `_safe_json_dumps()` method (uses the same logic, could be refactored to use shared utility)
- Updated all `json.dumps()` calls to use `_safe_json_dumps()`:
  - `_save_session()` - Session persistence
  - Output file serialization in `_enhance_full()` and `_enhance_quick()`
  - `_stage_architecture()` - Requirements serialization
  - `_build_synthesis_prompt()` - Stage data serialization
  - `_stage_synthesis()` - Stages parameter serialization

## Areas That May Need Similar Fixes

### High Priority (Complex Data Structures)

1. **CLI Feedback Output** (`tapps_agents/cli/feedback.py:609`)
   - `output_result()` uses `json.dumps()` directly on result data
   - Result data from agents may contain circular references
   - **Recommendation**: Use `safe_json_dumps()` from `json_utils`

2. **CLI Enhancer Command** (`tapps_agents/cli/commands/enhancer.py:101`)
   - Uses `json.dumps()` on enhanced prompt result
   - **Recommendation**: Use `safe_json_dumps()` from `json_utils`

3. **Workflow Executors** (`tapps_agents/workflow/executor.py`, `cursor_executor.py`)
   - `_make_json_serializable()` functions don't handle circular references
   - They check `json.dumps(obj)` which will fail on circular references
   - **Recommendation**: Update to use `safe_json_dumps()` or enhance `_make_json_serializable()` with circular reference detection

4. **Storage Manager** (`tapps_agents/core/storage_manager.py`)
   - Uses `json.dump()` for feedback, prompts, and evaluation data
   - **Recommendation**: Use `safe_json_dump()` from `json_utils`

5. **Workflow File Utils** (`tapps_agents/workflow/file_utils.py`)
   - `atomic_write_json()` uses `json.dump()` directly
   - **Recommendation**: Use `safe_json_dump()` from `json_utils`

### Medium Priority (Agent Results)

6. **Architect Agent** (`tapps_agents/agents/architect/agent.py:309`)
   - Uses `json.dumps()` for architecture output
   - **Recommendation**: Use `safe_json_dumps()` from `json_utils`

7. **Designer Agent** (`tapps_agents/agents/designer/agent.py:553`)
   - Uses `json.dumps()` for design system output
   - **Recommendation**: Use `safe_json_dumps()` from `json_utils`

### Low Priority (Simple Data Structures)

The following areas are less likely to have circular references but could benefit from the safe utility:

- Configuration file writes (simple dicts)
- Debug logging (simple dicts)
- Metadata writes (simple structures)

## Migration Path

### Option 1: Direct Replacement (Recommended)

Replace `json.dumps()` with `safe_json_dumps()`:

```python
# Before
import json
output = json.dumps(data, indent=2)

# After
from tapps_agents.core.json_utils import safe_json_dumps
output = safe_json_dumps(data, indent=2)
```

Replace `json.dump()` with `safe_json_dump()`:

```python
# Before
import json
with open('file.json', 'w') as f:
    json.dump(data, f, indent=2)

# After
from tapps_agents.core.json_utils import safe_json_dump
with open('file.json', 'w') as f:
    safe_json_dump(data, f, indent=2)
```

### Option 2: Refactor Enhancer Agent

The enhancer agent currently has its own `_safe_json_dumps()` method. This could be refactored to use the shared utility:

```python
# In enhancer agent
from ...core.json_utils import safe_json_dumps

# Replace
self._safe_json_dumps(session, indent=2)
# With
safe_json_dumps(session, indent=2)
```

## Testing

To test if circular references are handled correctly:

```python
# Test circular reference
data = {}
data['self'] = data  # Creates circular reference

# Should not raise error
from tapps_agents.core.json_utils import safe_json_dumps
result = safe_json_dumps(data)
assert '"self": "<circular reference>"' in result
```

## Benefits

1. **Prevents Crashes**: Circular references no longer cause serialization errors
2. **Better Debugging**: Circular references are replaced with clear placeholders
3. **Consistent Handling**: All JSON serialization uses the same safe approach
4. **Backward Compatible**: Drop-in replacements for `json.dumps()` and `json.dump()`

