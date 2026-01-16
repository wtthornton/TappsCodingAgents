# CLI Path Handling Fix - Implementation Plan

**Date:** 2026-01-20  
**Status:** 📋 Planning Complete - Ready for Implementation  
**Priority:** P0 - Critical (Blocks workflow execution on Windows)

## Executive Summary

This plan addresses critical CLI path handling issues identified in the feedback document (`TAPPS_AGENTS_IMPLEMENTATION_PLAN_FEEDBACK.md`). The primary issue is that Windows absolute paths (e.g., `c:/cursor/TappsCodingAgents`) are not being properly normalized to relative paths before CLI command execution, causing workflow failures.

## Problem Analysis

### Root Cause

**Error Message:**
```
Error: Command failed to spawn: path should be a `path.relative()`d string, but got "c:/cursor/TappsCodingAgents"
```

**Where It Occurs:**
- Simple Mode CLI commands (`tapps-agents simple-mode build ...`)
- Planner CLI commands (`tapps-agents planner plan ...`)
- Any CLI command that accepts file paths as parameters

**Why It Fails:**
1. Windows absolute paths are passed directly to CLI commands
2. Some path validation expects relative paths
3. Path normalization doesn't handle Windows absolute paths correctly
4. Error messages don't provide diagnostic information

### Impact

- **High:** Blocks primary workflow execution on Windows
- **High:** Prevents Simple Mode and Planner agent usage via CLI
- **Medium:** Forces manual fallback approaches
- **Low:** Poor user experience with unclear error messages

## Implementation Plan

### Phase 1: Fix CLI Path Handling (Priority 1.1 - Critical)

#### 1.1: Create Path Normalization Utility

**File:** `tapps_agents/core/path_normalizer.py` (new)

**Purpose:** Centralized path normalization for Windows/Linux/macOS compatibility

**Functions:**
- `normalize_path(path: str | Path, project_root: Path) -> str` - Normalize to relative path
- `ensure_relative_path(path: str | Path, project_root: Path) -> str` - Ensure path is relative
- `normalize_for_cli(path: str | Path, project_root: Path) -> str` - CLI-safe path format

**Implementation:**
```python
def normalize_path(path: str | Path, project_root: Path) -> str:
    """Normalize path to relative format for CLI commands."""
    path_obj = Path(path) if isinstance(path, str) else path
    project_root_obj = Path(project_root).resolve()
    
    # Resolve absolute paths
    if path_obj.is_absolute():
        try:
            # Try to make relative to project root
            rel_path = path_obj.resolve().relative_to(project_root_obj)
            return str(rel_path)
        except ValueError:
            # Path is outside project root - return as-is but warn
            logger.warning(f"Path {path_obj} is outside project root {project_root_obj}")
            return str(path_obj)
    
    # Already relative
    return str(path_obj)
```

#### 1.2: Update CLI Command Handlers

**Files to Modify:**
- `tapps_agents/cli/commands/simple_mode.py`
- `tapps_agents/cli/commands/planner.py`
- `tapps_agents/cli/commands/top_level.py` (workflow commands)

**Changes:**
- Import `normalize_path` from `path_normalizer`
- Normalize all file paths before passing to workflow executor
- Normalize `project_root` if it's an absolute Windows path

**Example:**
```python
from ...core.path_normalizer import normalize_path

def handle_simple_mode_build(args: object) -> None:
    # ... existing code ...
    
    # Normalize project root if absolute Windows path
    project_root = Path.cwd()
    if project_root.is_absolute() and sys.platform == "win32":
        # Ensure we use a relative representation for CLI
        project_root = Path(".").resolve()
    
    # Normalize any file paths
    target_file = getattr(args, "file", None)
    if target_file:
        target_file = normalize_path(target_file, project_root)
```

#### 1.3: Update Workflow Executor Path Handling

**File:** `tapps_agents/workflow/cursor_executor.py`

**Line 1666:** Fix path conversion to handle Windows absolute paths

**Current Code:**
```python
if target_path:
    params["target_file"] = str(target_path.relative_to(self.project_root))
```

**Fixed Code:**
```python
if target_path:
    try:
        # Try relative path first
        rel_path = target_path.resolve().relative_to(self.project_root.resolve())
        params["target_file"] = str(rel_path)
    except ValueError:
        # Path is outside project root or absolute Windows path issue
        # Normalize using path normalizer
        from ...core.path_normalizer import normalize_path
        params["target_file"] = normalize_path(target_path, self.project_root)
```

### Phase 2: Improve Error Messages (Priority 1.2 - Critical)

#### 2.1: Enhanced Error Messages in CLI

**File:** `tapps_agents/cli/feedback.py` (enhance existing)

**Add Diagnostic Information:**
- Show received path format
- Show expected format
- Show project root for context
- Suggest workarounds

**Example Error Message:**
```
Error: Path validation failed
  Received: c:/cursor/TappsCodingAgents (absolute Windows path)
  Expected: Relative path from project root
  Project root: c:/cursor/TappsCodingAgents
  
  Suggestion: Paths should be relative to project root. Use:
    - Relative paths: "src/file.py" instead of "c:/cursor/TappsCodingAgents/src/file.py"
    - Or run command from project root directory
```

#### 2.2: Path Validation with Clear Errors

**File:** `tapps_agents/core/path_validator.py` (enhance existing)

**Add:**
- Better error messages for path validation failures
- Diagnostic information (received vs expected)
- Platform-specific guidance

### Phase 3: Add Fallback Workflows (Priority 2.1 - Important)

#### 3.1: Detect CLI Failures and Suggest Alternatives

**File:** `tapps_agents/simple_mode/error_handling.py` (enhance existing)

**Add Error Detection:**
- Detect path-related errors
- Suggest alternative execution methods
- Provide manual workflow templates

**Example:**
```python
def handle_path_error(error: Exception, context: dict) -> dict:
    """Handle path-related errors with suggestions."""
    error_msg = str(error)
    
    if "path.relative()" in error_msg or "relative path" in error_msg.lower():
        return {
            "error_type": "path_validation_error",
            "message": "Path validation failed - Windows absolute path detected",
            "suggestion": "Use relative paths or run from project root",
            "alternatives": [
                "Use Cursor Skills directly: @simple-mode *build 'description'",
                "Use relative paths: tapps-agents simple-mode build --file src/file.py",
                "Run from project root directory"
            ],
            "workaround": "Manual workflow creation is available as fallback"
        }
```

#### 3.2: Fallback Workflow Templates

**File:** `tapps_agents/simple_mode/fallback_templates.py` (new)

**Purpose:** Provide manual workflow templates when CLI fails

**Content:**
- Step-by-step manual workflow instructions
- Alternative execution methods
- Cursor Skills commands as alternatives

### Phase 4: Enhance Simple Mode Error Handling (Priority 2.2 - Important)

#### 4.1: Catch Path Errors Gracefully

**File:** `tapps_agents/simple_mode/error_handling.py`

**Add Error Handler:**
```python
ERROR_TEMPLATES = {
    # ... existing templates ...
    "path_validation_error": {
        "message": "Path validation failed",
        "suggestion": "Use relative paths or run from project root",
        "recovery": "normalize_path",
    },
    "windows_path_error": {
        "message": "Windows absolute path detected",
        "suggestion": "Convert to relative path or use Cursor Skills",
        "recovery": "suggest_cursor_skills",
    },
}
```

#### 4.2: Automatic Path Normalization

**File:** `tapps_agents/simple_mode/handler.py`

**Add:**
- Automatic path normalization before command execution
- Pre-flight path validation
- Clear error messages with suggestions

## Implementation Order

1. **Phase 1.1** - Create path normalizer utility (foundation)
2. **Phase 1.2** - Update CLI command handlers (fixes primary issue)
3. **Phase 1.3** - Update workflow executor (fixes workflow execution)
4. **Phase 2.1** - Enhanced error messages (improves UX)
5. **Phase 2.2** - Path validation improvements (completes error handling)
6. **Phase 3.1** - Fallback detection (resilience)
7. **Phase 3.2** - Fallback templates (completes fallback system)
8. **Phase 4.1** - Error handler updates (completes error handling)
9. **Phase 4.2** - Automatic normalization (proactive fix)

## Testing Strategy

### Unit Tests

**File:** `tests/unit/core/test_path_normalizer.py` (new)

**Test Cases:**
- Windows absolute path normalization
- Linux absolute path normalization
- Relative path handling
- Path outside project root
- Edge cases (empty paths, special characters)

### Integration Tests

**File:** `tests/integration/test_cli_path_handling.py` (new)

**Test Cases:**
- Simple Mode build with Windows absolute path
- Planner plan with Windows absolute path
- Workflow execution with various path formats
- Error message quality

### E2E Tests

**File:** `tests/e2e/test_windows_path_handling.py` (new)

**Test Cases:**
- Full workflow execution on Windows
- CLI command execution with absolute paths
- Error recovery and fallback suggestions

## Success Criteria

### Quantitative

- ✅ 100% of Windows absolute paths normalized correctly
- ✅ 0 CLI command failures due to path handling
- ✅ Error messages include diagnostic information
- ✅ Fallback suggestions provided for all path errors

### Qualitative

- ✅ Clear error messages with actionable guidance
- ✅ Automatic path normalization works transparently
- ✅ Fallback workflows available when needed
- ✅ Better user experience on Windows

## Risk Mitigation

### Risks

1. **Breaking existing functionality** - Mitigated by comprehensive testing
2. **Performance impact** - Path normalization is lightweight
3. **Incomplete fix** - Mitigated by comprehensive test coverage

### Rollback Plan

- All changes are additive (new utility functions)
- Existing code paths remain unchanged
- Can disable normalization via feature flag if needed

## Timeline

- **Phase 1:** 2-4 hours (critical fixes)
- **Phase 2:** 1-2 hours (error messages)
- **Phase 3:** 2-3 hours (fallback workflows)
- **Phase 4:** 1-2 hours (error handling)
- **Testing:** 2-3 hours
- **Total:** 8-14 hours

## Next Steps

1. ✅ Review and approve this plan
2. ⏳ Implement Phase 1 (path normalizer)
3. ⏳ Update CLI command handlers
4. ⏳ Update workflow executor
5. ⏳ Add enhanced error messages
6. ⏳ Implement fallback workflows
7. ⏳ Test on Windows
8. ⏳ Update documentation

---

**Document Status:** Ready for Implementation  
**Last Updated:** 2026-01-20  
**Next Review:** After Phase 1 completion
