# Issue 10: Simple Mode Full Workflow Infinite Loop - Fix Plan

## Problem Summary

**Issue**: Simple Mode full workflow (`simple-mode full`) hangs indefinitely, showing spinner for 1+ hour without executing any workflow steps.

**Command**: 
```bash
python -m tapps_agents.cli simple-mode full --prompt "http://localhost:3001/synergies page: Network Graph button does not display anything..."
```

**Observed Behavior**:
- Spinner starts: `\ Starting Simple Full Lifecycle Workflow... (45m 0s)`
- No workflow steps execute (no requirements gathering, no planning, no implementation)
- No error messages or exceptions
- Process must be manually cancelled (Ctrl+C)

**Version**: 3.2.2

## Root Cause Analysis

### Investigation Findings

1. **Workflow Execution Flow**:
   - `handle_simple_mode_full()` → `WorkflowExecutor.execute()` → `_route_to_cursor_executor()` → `CursorWorkflowExecutor.run()`

2. **Potential Hang Points**:

   **A. Workflow Initialization Issue** (`cursor_executor.py:619-650`):
   - `_initialize_run()` calls `await self.start()` if state doesn't exist
   - If state initialization fails silently, workflow never progresses
   - First step might not be marked as "ready" if dependencies aren't properly initialized

   **B. No Ready Steps Loop** (`cursor_executor.py:580-585`):
   - `_find_ready_steps()` returns empty list if dependencies not met
   - `_handle_no_ready_steps()` might not properly detect completion vs. blocking
   - Infinite loop if workflow thinks it's not complete but no steps are ready

   **C. Manual Mode Waiting** (`cursor_executor.py:1323-1359`):
   - If auto-execution is disabled, workflow waits for Background Agents
   - Polling loop waits up to 1 hour (`max_wait_time = 3600`)
   - If Background Agents never execute, workflow hangs indefinitely
   - **This is likely the primary issue** - workflow is waiting for manual Background Agent execution

   **D. Missing Progress Feedback**:
   - Spinner shows but no actual progress updates
   - No indication of which step is being executed
   - No timeout warnings

3. **Related Issues Pattern**:
   - Issue 3: Planner Agent returns instruction object instead of executing
   - Issue 4: Tester Agent returns instruction object instead of creating test file
   - Issue 8: Improver Agent returns instruction object instead of improving code
   - **Pattern**: Agents/workflows have execution problems in Cursor mode

## Fix Plan

### Phase 1: Immediate Fixes (Critical)

#### 1.1 Add Timeout Mechanism
**File**: `tapps_agents/workflow/cursor_executor.py`

**Changes**:
- Add overall workflow timeout (configurable, default: 2 hours)
- Add per-step timeout (configurable, default: 30 minutes)
- Raise `TimeoutError` with clear message if timeout exceeded
- Save workflow state with timeout error before raising

**Implementation**:
```python
async def run(self, workflow, target_file, max_steps=100) -> WorkflowState:
    """Run workflow with timeout protection."""
    from ...core.config import load_config
    config = load_config()
    workflow_timeout = config.workflow.get('workflow_timeout_seconds', 7200)  # 2 hours
    
    try:
        return await asyncio.wait_for(
            self._run_workflow(workflow, target_file, max_steps),
            timeout=workflow_timeout
        )
    except asyncio.TimeoutError:
        self.state.status = "failed"
        self.state.error = f"Workflow timeout after {workflow_timeout}s"
        self.save_state()
        raise TimeoutError(f"Workflow execution exceeded {workflow_timeout}s timeout")
```

#### 1.2 Fix Workflow Initialization
**File**: `tapps_agents/workflow/cursor_executor.py`

**Changes**:
- Ensure first step is always marked as "ready" if it has no dependencies
- Add validation that workflow has at least one step
- Add check that state is properly initialized before entering execution loop

**Implementation**:
```python
async def _initialize_run(self, workflow, target_file) -> Path | None:
    """Initialize workflow execution with validation."""
    # ... existing code ...
    
    # Validate workflow has steps
    if not self.workflow.steps:
        raise ValueError("Workflow has no steps to execute")
    
    # Ensure state is properly initialized
    if not self.state:
        await self.start(workflow=self.workflow)
    
    # Validate first step can be executed (no dependencies)
    first_step = self.workflow.steps[0]
    if not first_step.requires:  # No dependencies
        # First step should always be ready
        if self.logger:
            self.logger.info(f"First step {first_step.id} has no dependencies - ready to execute")
    
    return target_path
```

#### 1.3 Improve No Ready Steps Handling
**File**: `tapps_agents/workflow/cursor_executor.py`

**Changes**:
- Better detection of workflow completion vs. blocking
- Add diagnostic logging when no steps are ready
- Check for circular dependencies or missing artifacts
- Provide actionable error messages

**Implementation**:
```python
def _handle_no_ready_steps(self, completed_step_ids: set[str]) -> bool:
    """Handle case when no steps are ready with better diagnostics."""
    if len(completed_step_ids) >= len(self.workflow.steps):
        # Workflow is complete
        self.state.status = "completed"
        self.state.current_step = None
        self.save_state()
        return True
    else:
        # Workflow is blocked - provide diagnostics
        available_artifacts = set(self.state.artifacts.keys())
        pending_steps = [
            s for s in self.workflow.steps 
            if s.id not in completed_step_ids
        ]
        
        # Check what's blocking
        blocking_info = []
        for step in pending_steps:
            missing = [req for req in (step.requires or []) if req not in available_artifacts]
            if missing:
                blocking_info.append(f"Step {step.id} ({step.agent}/{step.action}): missing {missing}")
        
        error_msg = (
            f"Workflow blocked: no ready steps and workflow not complete. "
            f"Completed: {len(completed_step_ids)}/{len(self.workflow.steps)}. "
            f"Blocking issues: {blocking_info if blocking_info else 'Unknown'}"
        )
        
        self.state.status = "failed"
        self.state.error = error_msg
        self.save_state()
        
        # Log detailed diagnostics
        if self.logger:
            self.logger.error(
                "Workflow blocked - no ready steps",
                extra={
                    "completed_steps": list(completed_step_ids),
                    "pending_steps": [s.id for s in pending_steps],
                    "available_artifacts": list(available_artifacts),
                    "blocking_info": blocking_info,
                }
            )
        
        return True
```

#### 1.4 Add Progress Reporting
**File**: `tapps_agents/cli/commands/simple_mode.py`

**Changes**:
- Stop spinner before executing workflow (spinner blocks async execution)
- Add progress callbacks to workflow executor
- Report which step is currently executing
- Show elapsed time and estimated remaining time

**Implementation**:
```python
def handle_simple_mode_full(args: object) -> None:
    """Handle simple-mode full command with progress reporting."""
    feedback = get_feedback()
    
    # Load workflow
    loader = PresetLoader()
    workflow = loader.load_preset("simple-full")
    # ... validation ...
    
    # Stop spinner before async execution (spinner blocks async)
    feedback.clear_progress()
    
    print(f"\n{'='*60}")
    print(f"Starting: {workflow.name}")
    # ... existing print statements ...
    
    # Execute workflow
    executor = WorkflowExecutor(auto_detect=False, auto_mode=auto_mode)
    if user_prompt:
        executor.user_prompt = user_prompt
    
    # Add progress callback
    def on_step_start(step_id: str, agent: str, action: str):
        print(f"\n[STEP] Executing: {step_id} ({agent}/{action})")
        sys.stdout.flush()
    
    def on_step_complete(step_id: str, duration: float):
        print(f"[OK] Step {step_id} completed in {duration:.1f}s")
        sys.stdout.flush()
    
    executor.on_step_start = on_step_start
    executor.on_step_complete = on_step_complete
    
    try:
        import asyncio
        state = asyncio.run(executor.execute(workflow=workflow, target_file=target_file))
        # ... handle completion ...
    except TimeoutError as e:
        feedback.error(
            "Workflow timeout",
            error_code="workflow_timeout",
            context={"error": str(e)},
            remediation="Increase timeout in config or check for blocking operations",
            exit_code=1,
        )
    except Exception as e:
        # ... existing error handling ...
```

### Phase 2: Enhanced Diagnostics

#### 2.1 Add Diagnostic Logging
**File**: `tapps_agents/workflow/cursor_executor.py`

**Changes**:
- Log when entering execution loop
- Log when finding ready steps (or lack thereof)
- Log step execution start/completion
- Log timeout warnings (at 50%, 75%, 90% of timeout)

**Implementation**:
```python
async def run(self, workflow, target_file, max_steps=100) -> WorkflowState:
    """Run workflow with enhanced diagnostics."""
    start_time = datetime.now()
    
    if self.logger:
        self.logger.info(
            "Starting workflow execution",
            extra={
                "workflow_id": self.state.workflow_id if self.state else None,
                "workflow_name": workflow.name if workflow else None,
                "max_steps": max_steps,
                "total_steps": len(workflow.steps) if workflow else 0,
            }
        )
    
    # ... existing execution loop with logging ...
    
    # Log progress every 10 steps
    if steps_executed % 10 == 0 and self.logger:
        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(
            f"Workflow progress: {steps_executed} steps executed in {elapsed:.1f}s",
            extra={
                "steps_executed": steps_executed,
                "completed_steps": len(completed_step_ids),
                "total_steps": len(self.workflow.steps),
                "elapsed_seconds": elapsed,
            }
        )
```

#### 2.2 Add Health Check Endpoint
**File**: `tapps_agents/workflow/cursor_executor.py`

**Changes**:
- Add method to check workflow health
- Detect if workflow is stuck (no progress for X minutes)
- Return diagnostic information

**Implementation**:
```python
def get_workflow_health(self) -> dict[str, Any]:
    """Get workflow health diagnostics."""
    if not self.state:
        return {"status": "not_started", "message": "Workflow not started"}
    
    elapsed = (datetime.now() - self.state.started_at).total_seconds() if self.state.started_at else 0
    completed = len(self.state.completed_steps)
    total = len(self.workflow.steps) if self.workflow else 0
    
    # Check if stuck (no progress in last 5 minutes)
    last_step_time = max(
        (se.completed_at for se in self.state.step_executions if se.completed_at),
        default=self.state.started_at
    )
    time_since_last_step = (
        (datetime.now() - last_step_time).total_seconds() 
        if last_step_time else elapsed
    )
    is_stuck = time_since_last_step > 300  # 5 minutes
    
    return {
        "status": self.state.status,
        "elapsed_seconds": elapsed,
        "completed_steps": completed,
        "total_steps": total,
        "progress_percent": (completed / total * 100) if total > 0 else 0,
        "time_since_last_step": time_since_last_step,
        "is_stuck": is_stuck,
        "current_step": self.state.current_step,
        "error": self.state.error,
    }
```

### Phase 3: Auto-Execution Improvements

#### 3.1 Force Auto-Execution for Simple Mode Full
**File**: `tapps_agents/cli/commands/simple_mode.py`

**Changes**:
- Force `auto_mode=True` for Simple Mode full workflow (unless explicitly disabled)
- Warn user if auto-execution is disabled
- Provide clear instructions on enabling auto-execution

**Implementation**:
```python
def handle_simple_mode_full(args: object) -> None:
    """Handle simple-mode full command."""
    # ... existing code ...
    
    auto_mode = getattr(args, "auto", False)
    
    # Force auto-execution for Simple Mode full (unless explicitly disabled)
    from ...core.config import load_config
    config = load_config()
    if not auto_mode and not config.workflow.auto_execution_enabled:
        from ...core.unicode_safe import safe_print
        safe_print("\n[WARNING] Auto-execution is disabled. Simple Mode full workflow requires auto-execution.", flush=True)
        safe_print("[TIP] Enable auto-execution:", flush=True)
        safe_print("  1. Add --auto flag: simple-mode full --prompt '...' --auto", flush=True)
        safe_print("  2. Or enable in config: workflow.auto_execution_enabled: true", flush=True)
        safe_print("  3. Or set TAPPS_AGENTS_MODE=headless for direct execution\n", flush=True)
        
        # Ask user if they want to continue (in interactive mode)
        if sys.stdin.isatty():
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response != 'y':
                feedback.error(
                    "Auto-execution required",
                    error_code="auto_execution_required",
                    remediation="Use --auto flag or enable auto-execution in config",
                    exit_code=1,
                )
                return
    
    # Execute with auto_mode
    executor = WorkflowExecutor(auto_detect=False, auto_mode=auto_mode or config.workflow.auto_execution_enabled)
    # ... rest of execution ...
```

#### 3.2 Improve Auto-Execution Error Messages
**File**: `tapps_agents/workflow/cursor_executor.py`

**Changes**:
- Provide clearer error messages when auto-execution fails
- Suggest specific remediation steps
- Check Background Agents status before starting workflow

**Implementation**:
```python
async def _execute_step_for_parallel(self, step, target_path):
    """Execute step with improved error messages."""
    # ... existing code ...
    
    if use_auto_execution:
        # Check Background Agents are running before starting
        if not self._check_background_agents_running():
            error_msg = (
                f"Background Agents not running. Auto-execution requires Background Agents to be active. "
                f"Start them with: python -m tapps_agents.background_agents start"
            )
            raise RuntimeError(error_msg)
        
        # ... existing auto-execution code ...
    else:
        # Manual mode - provide clear instructions
        # ... existing manual mode code with improved messages ...
```

### Phase 4: Testing & Validation

#### 4.1 Add Unit Tests
**Files**: `tests/test_simple_mode_full.py`, `tests/test_cursor_executor_timeout.py`

**Test Cases**:
- Test workflow timeout mechanism
- Test no ready steps detection
- Test workflow initialization
- Test progress reporting
- Test auto-execution forcing

#### 4.2 Add Integration Tests
**File**: `tests/integration/test_simple_mode_full_workflow.py`

**Test Cases**:
- End-to-end Simple Mode full workflow execution
- Timeout handling
- Error recovery
- Progress reporting

#### 4.3 Manual Testing Checklist
- [ ] Run Simple Mode full workflow with `--auto` flag
- [ ] Run Simple Mode full workflow without `--auto` (should warn)
- [ ] Run Simple Mode full workflow with timeout (should fail gracefully)
- [ ] Run Simple Mode full workflow with blocking step (should detect and fail)
- [ ] Verify progress reporting shows step-by-step progress
- [ ] Verify timeout errors are clear and actionable

## Implementation Priority

1. **P0 (Critical - Fix Immediately)**:
   - Add timeout mechanism (1.1)
   - Fix workflow initialization (1.2)
   - Improve no ready steps handling (1.3)
   - Add progress reporting (1.4)

2. **P1 (High - Fix Soon)**:
   - Force auto-execution for Simple Mode full (3.1)
   - Improve auto-execution error messages (3.2)
   - Add diagnostic logging (2.1)

3. **P2 (Medium - Fix When Possible)**:
   - Add health check endpoint (2.2)
   - Add unit tests (4.1)
   - Add integration tests (4.2)

## Success Criteria

1. ✅ Simple Mode full workflow completes successfully or fails with clear error message
2. ✅ No infinite hangs - workflow times out after configured timeout
3. ✅ Progress is visible - user can see which step is executing
4. ✅ Clear error messages when workflow is blocked or fails
5. ✅ Auto-execution is enabled by default for Simple Mode full
6. ✅ Timeout errors are actionable with remediation steps

## Related Issues

- Issue 3: Planner Agent returns instruction object instead of executing
- Issue 4: Tester Agent returns instruction object instead of creating test file
- Issue 8: Improver Agent returns instruction object instead of improving code
- **Pattern**: All related to execution problems in Cursor mode - consider addressing root cause

## Notes

- The primary issue is likely **manual mode waiting** - workflow waits for Background Agents that never execute
- Solution: Force auto-execution for Simple Mode full workflow
- Alternative: Add timeout and better error messages for manual mode
- Consider adding a "dry-run" mode that validates workflow without executing

