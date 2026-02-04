# BUG-003: Workflow Error Handling and Recovery Issues

**Date:** 2026-02-03
**Severity:** Medium
**Component:** Workflow Orchestration
**Status:** Open

---

## Summary

Workflow orchestration has multiple error handling issues: steps are marked as "completed" when they fail, failed steps don't halt the workflow, and step execution order becomes corrupted after failures.

## Steps to Reproduce

1. Run a workflow that encounters errors:
```bash
tapps-agents task run enh-001
```

2. Step 3 (Implementation) fails with quotation parsing error
3. Observe behavior:
   - Step marked as "✅ Completed" despite error
   - Workflow continues to steps 6-7 (Review, Test)
   - Then attempts to re-run steps 1-2 (Enhance, Planning)
   - Those steps then fail
   - Step 6 (Complete) also fails

## Expected Behavior

When a step fails:
1. **Mark step as FAILED** (❌), not completed (✅)
2. **Halt workflow execution** (or trigger configured recovery)
3. **Do not proceed** to dependent steps
4. **Report failure** clearly to user
5. **Update task status** to reflect failure

## Actual Behavior

When a step fails:
1. ❌ Step is marked as "✅ Completed" (incorrect)
2. ❌ Workflow continues to next steps (incorrect)
3. ❌ Dependent steps execute with missing inputs (incorrect)
4. ❌ Workflow then re-attempts earlier completed steps (incorrect)
5. ❌ Those re-attempted steps fail (cascading failure)
6. ❌ Final status unclear (confusing to user)

## Detailed Issue Breakdown

### Issue 3.1: Silent Failures

**Problem:** Errors are caught but not properly propagated.

**Evidence:**
```
Direct execution failed: No closing quotation
... [full traceback] ...
ValueError: No closing quotation

[OK] Step 'implementation' completed (4.2s)  ← WRONG!
```

The step should be marked as FAILED, not OK.

### Issue 3.2: Continuing After Failure

**Problem:** Workflow proceeds to dependent steps despite upstream failure.

**Evidence:**
```
Step 3 (implementation) - FAILED (but marked OK)
Step 4 (review) - Proceeds anyway (has nothing to review!)
Step 5 (testing) - Proceeds anyway (has no code to test!)
```

**Expected:** Workflow should halt after Step 3 failure.

### Issue 3.3: Corrupted Step Order

**Problem:** After failures, workflow re-attempts earlier completed steps.

**Evidence:**
```
Step 1 (enhance) - ✅ Completed successfully (17s)
Step 2 (planning) - ✅ Completed successfully (17s)
Step 3 (implementation) - ❌ Failed (but marked OK)
... later ...
Step 1 (enhance) - ❌ Failed (why re-running?)
Step 2 (planning) - ❌ Failed (why re-running?)
Step 6 (complete) - ❌ Failed
```

The workflow re-attempted Steps 1-2 which already completed successfully. This suggests corrupted workflow state or incorrect step dependency resolution.

### Issue 3.4: Unclear Final Status

**Problem:** Task status remains "todo" despite workflow execution.

**Evidence:**
```bash
$ tapps-agents task show enh-001
status: todo  ← Should be "failed" or "in-progress"
```

The task wasn't updated to reflect workflow execution or failure.

## Root Causes

### Cause 1: Exception Handling Swallows Errors

Likely code pattern:
```python
def execute_step(step):
    try:
        result = run_agent(step)
        return {"status": "completed"}  # Always returns completed!
    except Exception as e:
        logger.error(f"Step failed: {e}")
        return {"status": "completed"}  # ← WRONG! Should be "failed"
```

**Fix:** Propagate errors correctly:
```python
def execute_step(step):
    try:
        result = run_agent(step)
        return {"status": "completed", "success": True}
    except Exception as e:
        logger.error(f"Step failed: {e}")
        return {"status": "failed", "success": False, "error": str(e)}
```

### Cause 2: No Dependency Validation

Steps execute without checking if dependencies succeeded:
```python
def execute_workflow(steps):
    for step in steps:
        execute_step(step)  # No check of previous step status!
```

**Fix:** Validate dependencies before execution:
```python
def execute_workflow(steps):
    state = {}
    for step in steps:
        # Check dependencies succeeded
        if not all(state.get(dep, {}).get("success") for dep in step.dependencies):
            state[step.id] = {"status": "skipped", "reason": "dependency_failed"}
            continue

        # Execute step
        state[step.id] = execute_step(step)

        # Halt on failure
        if not state[step.id].get("success"):
            logger.error(f"Workflow halted at step {step.id}")
            break

    return state
```

### Cause 3: Step Restart Logic

The workflow appears to have retry/loopback logic that's triggering incorrectly, causing completed steps to re-run.

**Needs investigation:** Gate condition logic, loopback triggers

## Impact

**Severity: Medium**

- ❌ Workflows fail silently without clear indication
- ❌ Wasted resources executing dependent steps after failures
- ❌ Confusing user experience (status says "OK" but nothing works)
- ❌ Task status not updated correctly
- ⚠️ Difficult to debug (logs say "completed" when it failed)

## Suggested Fixes

### Fix 1: Proper Error Propagation

```python
@dataclass
class StepResult:
    """Result of step execution."""
    step_id: str
    status: Literal["completed", "failed", "skipped"]
    success: bool
    duration: float
    error: str | None = None
    artifacts: list[str] = field(default_factory=list)

def execute_step(step: Step) -> StepResult:
    """Execute step with proper error handling."""
    start = time.time()
    try:
        artifacts = run_agent(step)
        return StepResult(
            step_id=step.id,
            status="completed",
            success=True,
            duration=time.time() - start,
            artifacts=artifacts
        )
    except Exception as e:
        logger.error(f"Step {step.id} failed: {e}", exc_info=True)
        return StepResult(
            step_id=step.id,
            status="failed",
            success=False,
            duration=time.time() - start,
            error=str(e)
        )
```

### Fix 2: Dependency Validation

```python
def can_execute_step(step: Step, state: dict[str, StepResult]) -> tuple[bool, str]:
    """Check if step can execute based on dependencies."""
    for dep in step.requires:
        if dep not in state:
            return False, f"Dependency {dep} not executed"
        if not state[dep].success:
            return False, f"Dependency {dep} failed"
    return True, ""

def execute_workflow(workflow: Workflow) -> WorkflowResult:
    """Execute workflow with proper error handling."""
    state: dict[str, StepResult] = {}

    for step in workflow.steps:
        # Validate dependencies
        can_run, reason = can_execute_step(step, state)
        if not can_run:
            state[step.id] = StepResult(
                step_id=step.id,
                status="skipped",
                success=False,
                duration=0,
                error=reason
            )
            continue

        # Execute step
        result = execute_step(step)
        state[step.id] = result

        # Halt on failure (unless step is optional)
        if not result.success and step.condition == "required":
            logger.error(f"Workflow halted: {step.id} failed")
            break

    return WorkflowResult(steps=state)
```

### Fix 3: Update Task Status

```python
def run_task_workflow(task_id: str) -> WorkflowResult:
    """Run workflow for task and update task status."""
    # Load task
    task = load_task_spec(task_id)

    # Update status to in-progress
    task.status = "in-progress"
    save_task_spec(task)

    # Execute workflow
    result = execute_workflow(task.workflow)

    # Update task status based on result
    if result.all_success():
        task.status = "done"
    elif result.any_failed():
        task.status = "blocked"  # or "todo" to retry

    save_task_spec(task)

    return result
```

## Files to Investigate

1. Workflow orchestrator code (step execution loop)
2. Error handling in agent execution
3. Step dependency resolution
4. Gate/loopback logic
5. Task status update code

## Testing Verification

After fix, verify:
1. ✅ Failed steps marked as FAILED (❌), not completed (✅)
2. ✅ Workflow halts when required step fails
3. ✅ Dependent steps skipped when dependency fails
4. ✅ Task status updated correctly (in-progress → done/blocked)
5. ✅ No re-execution of already-completed steps
6. ✅ Clear error messages in workflow output

## Related Issues

- BUG-002 (CLI quotation parsing) - causes this workflow failure
- Silent error handling throughout codebase

## Workaround

**Current workaround:** Monitor workflow output carefully and manually verify completion:
```bash
# Check if implementation actually succeeded
ls -la tapps_agents/workflow/

# Manually retry if needed
@implementer *implement "..." target_file.py
```

---

**Reported by:** Claude Sonnet 4.5 (Session 2026-02-03)
**Affects:** v3.5.39
**Priority:** P2 (Medium)
