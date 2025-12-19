# TappsCodingAgents Usability Fix Plan

## Problem Statement

The framework is not working as designed when users run CLI commands. Key issues:

1. **CLI commands default to Cursor mode** - When running from Cursor IDE, CLI commands detect Cursor mode and switch to manual execution mode, requiring background agents
2. **Auto-execution not enabled by default** - Users must configure `auto_execution_enabled: true` to make Cursor mode work automatically
3. **Poor user experience** - Users must know about `TAPPS_AGENTS_MODE=headless` environment variable to make CLI commands work
4. **Unclear error messages** - When workflows hang in manual mode, users don't get clear guidance
5. **Command complexity** - The `create` command should "just work" without requiring environment variables

## Root Cause Analysis

### Issue 1: Runtime Mode Detection
**Location**: `tapps_agents/core/runtime_mode.py`

**Problem**: 
- When Cursor environment variables are present (CURSOR, CURSOR_IDE, etc.), the framework automatically detects Cursor mode
- This causes CLI commands to use `CursorWorkflowExecutor` which defaults to manual mode
- Users running `python -m tapps_agents.cli create "..."` from Cursor IDE get stuck in manual mode

**Current Behavior**:
```python
# detect_runtime_mode() checks for Cursor env vars first
if any(os.getenv(k) for k in cursor_markers):
    return RuntimeMode.CURSOR  # Forces Cursor mode
```

### Issue 2: Auto-Execution Default
**Location**: `tapps_agents/workflow/cursor_executor.py`

**Problem**:
- Auto-execution is disabled by default
- Requires explicit config: `workflow.auto_execution_enabled: true`
- Users don't know they need this configuration

**Current Behavior**:
```python
# Auto-execution only enabled if config says so
use_auto_execution = (
    self.auto_execution_enabled_workflow
    if self.auto_execution_enabled_workflow is not None
    else self.auto_execution_enabled  # Defaults to False
)
```

### Issue 3: CLI Command Doesn't Force Headless Mode
**Location**: `tapps_agents/cli/commands/top_level.py`

**Problem**:
- `handle_create_command()` doesn't force headless mode for CLI usage
- Relies on runtime detection which may choose Cursor mode
- No distinction between "CLI from terminal" vs "CLI from Cursor Skills"

**Current Behavior**:
```python
# No mode override - uses whatever runtime mode is detected
executor = WorkflowExecutor(auto_detect=False, auto_mode=True)
```

## Solution Plan

### Fix 1: Smart Runtime Mode Detection for CLI Commands

**Goal**: CLI commands should default to headless mode unless explicitly running from Cursor Skills

**Approach**:
1. Add `is_cli_invocation()` function to detect if running from CLI vs Cursor Skills
2. Modify `detect_runtime_mode()` to check CLI invocation first
3. Only use Cursor mode if:
   - Explicitly set via `TAPPS_AGENTS_MODE=cursor`
   - OR running from Cursor Skills (detected via different mechanism)

**Implementation**:
- Add detection for CLI invocation (check if `sys.argv[0]` contains `cli` or `tapps_agents`)
- Modify runtime mode detection to prioritize CLI headless mode
- Add `--cursor-mode` flag to CLI commands for explicit Cursor mode

**Files to Modify**:
- `tapps_agents/core/runtime_mode.py` - Add CLI detection
- `tapps_agents/cli/commands/top_level.py` - Add `--cursor-mode` flag

### Fix 2: Enable Auto-Execution by Default in Cursor Mode

**Goal**: When in Cursor mode, auto-execution should be enabled by default

**Approach**:
1. Change default `auto_execution_enabled` to `True` in config
2. Update `CursorWorkflowExecutor` to default to auto-execution
3. Add clear warning if auto-execution fails (background agents not running)

**Implementation**:
- Modify default config in `tapps_agents/core/config.py`
- Update `CursorWorkflowExecutor.__init__()` to default `auto_execution_enabled=True`
- Add fallback message if auto-execution fails

**Files to Modify**:
- `tapps_agents/core/config.py` - Change default
- `tapps_agents/workflow/cursor_executor.py` - Default to auto-execution
- `templates/default_config.yaml` - Update default config template

### Fix 3: Force Headless Mode in CLI Commands

**Goal**: CLI commands should explicitly force headless mode unless `--cursor-mode` is specified

**Approach**:
1. Modify `handle_create_command()` to set `TAPPS_AGENTS_MODE=headless` before creating executor
2. Add `--cursor-mode` flag for users who want Cursor mode
3. Add clear messaging about which mode is being used

**Implementation**:
```python
def handle_create_command(args: object) -> None:
    # Force headless mode for CLI unless --cursor-mode specified
    if not getattr(args, "cursor_mode", False):
        os.environ["TAPPS_AGENTS_MODE"] = "headless"
    
    # ... rest of function
```

**Files to Modify**:
- `tapps_agents/cli/commands/top_level.py` - Force headless mode
- `tapps_agents/cli/base.py` - Add `--cursor-mode` argument

### Fix 4: Better Error Messages and User Guidance

**Goal**: When workflows hang or fail, provide clear guidance

**Approach**:
1. Add helpful error messages when manual mode is detected
2. Provide remediation steps in error output
3. Add progress indicators and status messages

**Implementation**:
- Add error messages in `CursorWorkflowExecutor` when manual mode is detected
- Include remediation steps (enable auto-execution, use headless mode, etc.)
- Add status messages showing which mode is active

**Files to Modify**:
- `tapps_agents/workflow/cursor_executor.py` - Add error messages
- `tapps_agents/cli/commands/top_level.py` - Add status messages

### Fix 5: Simplify Default Workflow Presets

**Goal**: Default workflow presets should enable auto-execution

**Approach**:
1. Update workflow presets to include `auto_execution: true` in metadata
2. Ensure all presets work out of the box

**Files to Modify**:
- `workflows/presets/*.yaml` - Add `auto_execution: true` to metadata

## Implementation Priority

### Phase 1: Critical Fixes (Immediate)
1. **Fix 3**: Force headless mode in CLI commands
   - Impact: High - Makes CLI commands work immediately
   - Effort: Low - Simple environment variable setting
   - Risk: Low - Only affects CLI commands

2. **Fix 2**: Enable auto-execution by default
   - Impact: High - Makes Cursor mode work automatically
   - Effort: Low - Change default values
   - Risk: Low - Can be overridden by config

### Phase 2: User Experience Improvements (Short-term)
3. **Fix 4**: Better error messages
   - Impact: Medium - Improves user experience
   - Effort: Medium - Add error handling and messages
   - Risk: Low - Only adds messages

4. **Fix 5**: Update workflow presets
   - Impact: Medium - Ensures presets work out of box
   - Effort: Low - Update YAML files
   - Risk: Low - Metadata only

### Phase 3: Advanced Improvements (Long-term)
5. **Fix 1**: Smart runtime mode detection
   - Impact: Medium - Better automatic detection
   - Effort: High - Requires careful testing
   - Risk: Medium - Could affect existing behavior

## Testing Plan

### Test Case 1: CLI Command from Terminal
**Scenario**: User runs `python -m tapps_agents.cli create "Hello world"` from terminal
**Expected**: 
- Runs in headless mode
- Shows terminal output
- Completes automatically
- No manual mode waiting

### Test Case 2: CLI Command from Cursor IDE
**Scenario**: User runs `python -m tapps_agents.cli create "Hello world"` from Cursor IDE terminal
**Expected**:
- Runs in headless mode (unless `--cursor-mode` specified)
- Shows terminal output
- Completes automatically

### Test Case 3: Cursor Mode with Auto-Execution
**Scenario**: User runs with `--cursor-mode` or `TAPPS_AGENTS_MODE=cursor`
**Expected**:
- Auto-execution enabled by default
- Uses Background Agents
- Completes automatically if agents running
- Clear error if agents not running

### Test Case 4: Manual Mode Fallback
**Scenario**: Auto-execution disabled or fails
**Expected**:
- Clear error message
- Remediation steps provided
- Option to switch to headless mode

## Success Criteria

1. ✅ CLI commands work out of the box without environment variables
2. ✅ Auto-execution enabled by default in Cursor mode
3. ✅ Clear error messages when things don't work
4. ✅ Users can easily switch between modes
5. ✅ Documentation updated with new behavior

## Documentation Updates

1. Update `WORKFLOW_EXECUTION_MODE.md` with new defaults
2. Update `README.md` with simplified usage
3. Update CLI help text with mode information
4. Add troubleshooting guide for common issues

## Migration Notes

**Breaking Changes**: None - All changes are backward compatible
- Existing configs still work
- `TAPPS_AGENTS_MODE` still respected
- `--cursor-mode` flag is optional

**Deprecations**: None

**New Features**:
- `--cursor-mode` flag for CLI commands
- Auto-execution enabled by default
- Better error messages

## Implementation Checklist

### Phase 1
- [ ] Modify `handle_create_command()` to force headless mode
- [ ] Add `--cursor-mode` flag to CLI
- [ ] Change default `auto_execution_enabled` to `True`
- [ ] Update `CursorWorkflowExecutor` to default to auto-execution
- [ ] Update default config template

### Phase 2
- [ ] Add error messages in `CursorWorkflowExecutor`
- [ ] Add status messages in CLI commands
- [ ] Update workflow presets with `auto_execution: true`

### Phase 3
- [ ] Add `is_cli_invocation()` function
- [ ] Modify `detect_runtime_mode()` for smart detection
- [ ] Add tests for runtime mode detection

### Documentation
- [ ] Update `WORKFLOW_EXECUTION_MODE.md`
- [ ] Update `README.md`
- [ ] Update CLI help text
- [ ] Add troubleshooting guide

## Estimated Timeline

- **Phase 1**: 2-4 hours (Critical fixes)
- **Phase 2**: 2-3 hours (UX improvements)
- **Phase 3**: 4-6 hours (Advanced improvements)
- **Testing**: 2-3 hours
- **Documentation**: 1-2 hours

**Total**: 11-18 hours

