# BUG-003B Implementation Plan: Workflow Error Handling & Recovery

**Date:** 2026-02-04
**Target Version:** 3.5.41
**Estimated Effort:** 2-3 hours
**Priority:** P2 (Medium)

---

## 📋 Overview

Fix workflow error handling so that:
1. Failed steps are marked as FAILED (❌), not completed (✅)
2. Workflow halts when required steps fail
3. Dependent steps are skipped when dependencies fail
4. Task status updates correctly (todo → in-progress → done/blocked)
5. Clear error messages in workflow output

---

## 🎯 Acceptance Criteria

**Must Have:**
- [ ] Failed steps marked with ❌ status, not ✅
- [ ] Workflow halts immediately when required step fails
- [ ] Dependent steps skipped with clear reason
- [ ] Task status reflects actual workflow state
- [ ] Error messages include stack traces and actionable info

**Should Have:**
- [ ] Optional steps can fail without halting workflow
- [ ] Retry/loopback logic works correctly after fixes
- [ ] Workflow markers include failure information
- [ ] Recovery suggestions in error output

**Nice to Have:**
- [ ] Automatic recovery attempts for transient failures
- [ ] Workflow resume capability
- [ ] Detailed failure analytics

---

## 🔍 Root Causes (From BUG-003-workflow-error-handling-recovery.md)

### Cause 1: Exception Handling Swallows Errors

**Current Code Pattern:**
```python
def execute_step(step):
    try:
        result = run_agent(step)
        return {"status": "completed"}  # Always returns completed!
    except Exception as e:
        logger.error(f"Step failed: {e}")
        return {"status": "completed"}  # ← WRONG!
```

### Cause 2: No Dependency Validation

Steps execute without checking if dependencies succeeded:
```python
def execute_workflow(steps):
    for step in steps:
        execute_step(step)  # No check of previous step status!
```

### Cause 3: Step Restart Logic

Loopback/retry logic triggers incorrectly, causing completed steps to re-run.

---

## 🛠️ Implementation Tasks

### Task 1: Create StepResult Type (30 min)

**File:** `tapps_agents/workflow/models.py`

**Add:**
```python
@dataclass
class StepResult:
    """Result of step execution with proper error handling."""
    step_id: str
    status: Literal["completed", "failed", "skipped"]
    success: bool
    duration: float
    started_at: datetime
    completed_at: datetime
    error: str | None = None
    error_traceback: str | None = None
    artifacts: list[str] = field(default_factory=list)
    skip_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_id": self.step_id,
            "status": self.status,
            "success": self.success,
            "duration": self.duration,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "error": self.error,
            "error_traceback": self.error_traceback,
            "artifacts": self.artifacts,
            "skip_reason": self.skip_reason,
        }
```

**Test:**
- [ ] StepResult creation for completed steps
- [ ] StepResult creation for failed steps
- [ ] StepResult creation for skipped steps
- [ ] to_dict() serialization

---

### Task 2: Update _execute_step to Return StepResult (45 min)

**File:** `tapps_agents/workflow/cursor_executor.py`

**Modify:** `_execute_step()` and `_execute_step_for_parallel()`

**Changes:**
```python
async def _execute_step(
    self, step: WorkflowStep, target_path: Path | None
) -> StepResult:
    """Execute step with proper error handling."""
    started_at = datetime.now()

    try:
        # Execute step (existing logic)
        artifacts = await self._execute_step_internal(step, target_path)

        return StepResult(
            step_id=step.id,
            status="completed",
            success=True,
            duration=(datetime.now() - started_at).total_seconds(),
            started_at=started_at,
            completed_at=datetime.now(),
            artifacts=artifacts or [],
        )

    except Exception as e:
        logger.error(
            f"Step {step.id} failed: {e}",
            exc_info=True,
            extra={"step_id": step.id, "agent": step.agent}
        )

        return StepResult(
            step_id=step.id,
            status="failed",
            success=False,
            duration=(datetime.now() - started_at).total_seconds(),
            started_at=started_at,
            completed_at=datetime.now(),
            error=str(e),
            error_traceback=traceback.format_exc(),
        )
```

**Test:**
- [ ] Successful step execution returns success=True
- [ ] Failed step execution returns success=False
- [ ] Error message and traceback captured
- [ ] Duration calculated correctly

---

### Task 3: Add Dependency Validation (30 min)

**File:** `tapps_agents/workflow/cursor_executor.py`

**Add Helper Function:**
```python
def _can_execute_step(
    self,
    step: WorkflowStep,
    completed_steps: dict[str, StepResult]
) -> tuple[bool, str]:
    """
    Check if step can execute based on dependencies.

    Args:
        step: Step to check
        completed_steps: Results of previously executed steps

    Returns:
        (can_execute, skip_reason)
    """
    for dep in step.requires or []:
        if dep not in completed_steps:
            return False, f"Dependency '{dep}' not executed"

        dep_result = completed_steps[dep]
        if not dep_result.success:
            return False, f"Dependency '{dep}' failed: {dep_result.error}"

    return True, ""
```

**Test:**
- [ ] Step executes when all dependencies succeeded
- [ ] Step skipped when dependency not executed
- [ ] Step skipped when dependency failed
- [ ] Clear skip reason provided

---

### Task 4: Update execute() Method (45 min)

**File:** `tapps_agents/workflow/cursor_executor.py`

**Modify:** Main workflow execution loop in `execute()`

**Changes:**
```python
async def execute(
    self,
    workflow: Workflow,
    target_file: str | None = None,
) -> WorkflowState:
    """Execute workflow with proper error handling."""
    # ... existing setup ...

    completed_steps: dict[str, StepResult] = {}

    for step in workflow.steps:
        # Validate dependencies
        can_execute, skip_reason = self._can_execute_step(step, completed_steps)

        if not can_execute:
            # Skip step due to dependency failure
            result = StepResult(
                step_id=step.id,
                status="skipped",
                success=False,
                duration=0,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                skip_reason=skip_reason,
            )
            completed_steps[step.id] = result

            safe_print(f"\n⏭️  Skipping step '{step.id}': {skip_reason}\n")
            continue

        # Execute step
        result = await self._execute_step(step, target_path)
        completed_steps[step.id] = result

        # Check if step is required
        is_required = step.get("required", True)

        # Halt on failure if step is required
        if not result.success and is_required:
            safe_print(
                f"\n❌ Workflow halted: Required step '{step.id}' failed\n"
                f"Error: {result.error}\n"
            )

            # Update task status to blocked
            self.state.status = "blocked"
            self.state.error = result.error
            break

    # Update final workflow state
    all_success = all(r.success for r in completed_steps.values())
    self.state.status = "completed" if all_success else "blocked"

    return self.state
```

**Test:**
- [ ] Workflow halts on required step failure
- [ ] Workflow continues on optional step failure
- [ ] All dependent steps skipped after failure
- [ ] Final status reflects actual outcome

---

### Task 5: Update Task Status (20 min)

**File:** `tapps_agents/cli/commands/task.py`

**Modify:** `run()` function to update task status

**Changes:**
```python
def run(task_id: str, auto: bool = False, preset: str | None = None) -> int:
    """Run workflow for task."""
    # Load task spec
    spec = load_task_spec(task_id)

    # Update status to in-progress
    spec.task.status = "in-progress"
    save_task_spec(spec, task_id)

    try:
        # Execute workflow
        final_state = run_async_command(
            executor.execute(workflow=workflow, target_file=target_file)
        )

        # Update task status based on result
        if final_state.status == "completed":
            spec.task.status = "done"
        elif final_state.status == "blocked":
            spec.task.status = "blocked"
        else:
            spec.task.status = "todo"  # Retry

        save_task_spec(spec, task_id)

        return 0 if final_state.status == "completed" else 1

    except Exception as e:
        # Update status to blocked on exception
        spec.task.status = "blocked"
        save_task_spec(spec, task_id)
        raise
```

**Test:**
- [ ] Status changes: todo → in-progress
- [ ] Status changes: in-progress → done (success)
- [ ] Status changes: in-progress → blocked (failure)
- [ ] Status persisted to YAML file

---

### Task 6: Update Workflow Markers (20 min)

**File:** `tapps_agents/workflow/marker_writer.py`

**Modify:** `write_done_marker()` to include failure info

**Add:** `write_failed_marker()`

**Changes:**
```python
def write_failed_marker(
    self,
    workflow_id: str,
    step_id: str,
    agent: str,
    action: str,
    error: str,
    error_traceback: str,
    duration_seconds: float,
    started_at: datetime,
    failed_at: datetime,
) -> Path:
    """Write FAILED.json marker for failed step."""
    marker_dir = self._get_step_marker_dir(workflow_id, step_id)
    marker_dir.mkdir(parents=True, exist_ok=True)

    marker_path = marker_dir / "FAILED.json"
    marker_data = {
        "workflow_id": workflow_id,
        "step_id": step_id,
        "agent": agent,
        "action": action,
        "status": "failed",
        "error": error,
        "error_traceback": error_traceback,
        "duration_seconds": duration_seconds,
        "started_at": started_at.isoformat(),
        "failed_at": failed_at.isoformat(),
    }

    marker_path.write_text(json.dumps(marker_data, indent=2), encoding='utf-8')
    return marker_path
```

**Test:**
- [ ] FAILED.json created for failed steps
- [ ] Contains error message and traceback
- [ ] DONE.json created for successful steps
- [ ] Markers readable by workflow resume logic

---

### Task 7: Fix Loopback Logic (30 min)

**File:** `tapps_agents/workflow/cursor_executor.py`

**Investigate:** Gate condition evaluation and loopback triggers

**Ensure:**
- Loopback only triggers when quality gate fails (not on errors)
- Loopback doesn't re-execute completed steps
- Loopback counter prevents infinite loops

**Test:**
- [ ] Loopback triggers on quality gate failure
- [ ] Loopback doesn't trigger on step errors
- [ ] Loopback limited to max iterations
- [ ] Completed steps not re-executed

---

### Task 8: Integration Tests (30 min)

**File:** `tests/integration/test_workflow_error_handling.py`

**Test Cases:**
```python
async def test_step_failure_halts_workflow():
    """Verify workflow halts when required step fails."""
    # Mock step that fails
    # Execute workflow
    # Assert workflow halted
    # Assert dependent steps skipped

async def test_optional_step_failure_continues():
    """Verify workflow continues when optional step fails."""
    # Mock optional step that fails
    # Execute workflow
    # Assert workflow continued
    # Assert next step executed

async def test_dependency_validation():
    """Verify steps skip when dependencies fail."""
    # Mock step 1 fails
    # Step 2 depends on step 1
    # Assert step 2 skipped
    # Assert skip reason is clear

async def test_task_status_updates():
    """Verify task status updates correctly."""
    # Execute workflow that fails
    # Assert task status changed to "blocked"
    # Execute workflow that succeeds
    # Assert task status changed to "done"
```

---

## 📊 Testing Strategy

### Unit Tests (1 hour)
- [ ] StepResult creation and serialization
- [ ] Dependency validation logic
- [ ] Error propagation
- [ ] Status calculation

### Integration Tests (1 hour)
- [ ] End-to-end workflow with failures
- [ ] Task status updates
- [ ] Workflow markers
- [ ] Error messages in output

### Manual Testing (30 min)
- [ ] Run `tapps-agents task run enh-001` with induced failure
- [ ] Verify workflow halts
- [ ] Verify clear error messages
- [ ] Verify task status updated

---

## 🚀 Rollout Plan

1. **Create feature branch:** `fix/bug-003b-error-handling`
2. **Implement tasks 1-7** (incremental commits)
3. **Run full test suite**
4. **Manual verification**
5. **PR to main** with detailed description
6. **Code review**
7. **Merge to main**
8. **Release v3.5.41**

---

## 📝 Documentation Updates

**Files to Update:**
- [ ] `docs/bugs/BUG-003-workflow-error-handling-recovery.md` - Mark as FIXED
- [ ] `docs/releases/RELEASE-3.5.41.md` - Create release notes
- [ ] `docs/ARCHITECTURE.md` - Document error handling strategy
- [ ] `README.md` - Update workflow error handling section

---

## ⏱️ Time Estimates

| Task | Estimate | Priority |
|------|----------|----------|
| StepResult type | 30 min | P0 |
| Update _execute_step | 45 min | P0 |
| Dependency validation | 30 min | P0 |
| Update execute() | 45 min | P0 |
| Task status updates | 20 min | P1 |
| Workflow markers | 20 min | P1 |
| Fix loopback logic | 30 min | P2 |
| Integration tests | 1 hour | P0 |
| Documentation | 30 min | P1 |

**Total Estimate:** 4-5 hours (including testing)

---

## 🎯 Success Metrics

**Before Fix:**
- ❌ Steps marked "✅ Completed" when failed
- ❌ Workflow continues after failures
- ❌ Task status doesn't update

**After Fix:**
- ✅ Failed steps clearly marked "❌ Failed"
- ✅ Workflow halts on required step failure
- ✅ Task status reflects actual state (in-progress/done/blocked)
- ✅ Clear error messages with actionable info

---

## 📌 Next Actions

1. Create feature branch
2. Start with Task 1 (StepResult type)
3. Work through tasks incrementally
4. Test after each task
5. Commit after each working task

**Ready to start?** Run:
```bash
git checkout -b fix/bug-003b-error-handling
```

---

**Created by:** Claude Sonnet 4.5
**Date:** 2026-02-04
**Target Release:** v3.5.41
