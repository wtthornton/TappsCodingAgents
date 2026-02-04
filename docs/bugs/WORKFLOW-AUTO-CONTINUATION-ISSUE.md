# Workflow Auto-Continuation Issue Analysis

**Date:** 2026-02-03
**Severity:** HIGH
**Component:** Workflow Orchestration, Task Execution
**Status:** ✅ **FIXED** (2026-02-03)

---

## ✅ Fix Applied (2026-02-03)

**Root Cause:** The `find_ready_steps()` method in `parallel_executor.py` only checked artifact dependencies (`requires` field) but ignored the workflow's sequential `next:` chain. This allowed the "complete" step to execute immediately after "enhance" because it had no artifact dependencies.

**Solution:** Modified `find_ready_steps()` to respect the workflow's `next:` chain for sequential step progression.

**File Modified:** `tapps_agents/workflow/parallel_executor.py:120-192`

**Changes:**
1. Build set of `next_step_ids` from completed steps' `next:` fields
2. Only mark steps as ready if they're in the `next_step_ids` set (sequential progression)
3. Maintain artifact dependency checking for each step
4. Handle first step case (when no completed steps yet)

**Verification Results (HM-001 Test):**
```
✅ Step 1: enhance → Completed
✅ Step 2: planning → Completed
✅ Step 3: implementation → Attempted (blocked by separate BUG-002)
```

**Before Fix:**
```
✅ enhance → ❌ complete (WRONG! Skipped 4 steps)
```

**Fix Confirmed:** Workflows now follow the sequential `next:` chain correctly. No more premature jumps to "complete" step.

**See:** `docs/bugs/WORKFLOW-AUTO-CONTINUATION-FIX-SUMMARY.md` for complete fix details.

---

## Problem Summary

When running workflows via `tapps-agents task run`, workflows **stop prematurely** after completing only 1-2 steps instead of continuing through all defined steps, **even though `auto_mode=True` is set**.

---

## Observed Behavior

### What Should Happen
```
tapps-agents task run hm-001
↓
Workflow: rapid-dev (6 steps defined)
↓
Step 1: enhance → ✅ Complete
Step 2: planning → ✅ Complete
Step 3: implementation → ✅ Complete
Step 4: review → ✅ Complete
Step 5: testing → ✅ Complete
Step 6: complete → ✅ Complete
↓
Task status: done
```

### What Actually Happens
```
tapps-agents task run hm-001
↓
Workflow: rapid-dev (6 steps defined)
↓
Step 1: enhance → ✅ Complete
Step 1: complete → ✅ Complete (WRONG STEP!)
↓
Workflow ends (PREMATURE!)
Task status: in-progress (NOT UPDATED!)
```

---

## Evidence

### Workflow Execution Log
```
## 🚀 Workflow Started

**Step 1 of 6** (`enhance`) (0.0% complete)
[EXEC] Executing enhancer/enhance-prompt...
[OK] Step 'enhance' completed (16.6s)

**Step 1 of 6** (`complete`) (0.0% complete)  ← WRONG!
**Status:** ✅ Completed
**Agent:** orchestrator
**Action:** finalize

[Workflow ends - only 1 step executed out of 6!]
```

### Expected Workflow Steps (rapid-dev.yaml)
```yaml
steps:
  - id: enhance → planning
  - id: planning → implementation
  - id: implementation → review
  - id: review → testing
  - id: testing → complete
  - id: complete (final)
```

### Actual Execution
```
✅ enhance (completed)
❌ planning (SKIPPED!)
❌ implementation (SKIPPED!)
❌ review (SKIPPED!)
❌ testing (SKIPPED!)
✅ complete (jumped directly!)
```

---

## Root Cause Analysis

### Code Investigation

**File:** `tapps_agents/cli/commands/task.py:200`

```python
executor = WorkflowExecutor(auto_detect=False, auto_mode=True)
```

`auto_mode=True` IS set! So why does it stop?

### Hypothesis

The workflow executor is **jumping directly to the `complete` step** after the first step, instead of following the `next:` chain defined in the workflow YAML.

**Possible causes:**
1. **Step progression logic broken** - Not reading `next:` field from workflow steps
2. **Auto-mode not fully implemented** - May only execute one step then stop
3. **Workflow state corruption** - Incorrect step tracking
4. **Gate/condition evaluation issue** - May be triggering early exit

---

## Why This Appears "Normal"

This behavior appears "normal" from a workflow execution perspective because:

1. **Workflows are designed for step-by-step execution** - Original design assumed human review between steps
2. **Interactive by default** - Wait for user confirmation before proceeding
3. **Safety mechanism** - Prevents runaway execution making unwanted changes

However, **for task-based execution via Beads, this is BROKEN behavior** because:
- Tasks should execute fully automatically
- `auto_mode=True` is explicitly set
- User expects complete workflow execution, not partial

---

## Impact

### High Impact Issues

❌ **Beads task execution doesn't work** - Tasks never complete fully
❌ **Manual intervention required** - Have to manually continue each step
❌ **Framework promise broken** - "Automatic task management" isn't automatic
❌ **Workflow state inconsistent** - Task shows "in-progress" forever

### Workflow Blockers

| Workflow | Steps Defined | Steps Executed | % Complete |
|----------|--------------|----------------|------------|
| rapid-dev | 6 | 1 | 17% |
| full-sdlc | 9 | 1 | 11% |
| fix | 4 | 1 | 25% |

**Result:** No workflow completes automatically!

---

## Solution Required

### Immediate Fix Needed

**Fix the step progression logic** in WorkflowExecutor to:

1. **Read `next:` field** from workflow step definition
2. **Auto-progress to next step** when `auto_mode=True`
3. **Continue until `complete` step** or error
4. **Update task status** to `done` when workflow completes

### Implementation Approach

**File to modify:** `tapps_agents/workflow/executor.py` or `tapps_agents/workflow/cursor_executor.py`

**Key changes:**

```python
async def execute(self, workflow, target_file=None):
    current_step_id = workflow.steps[0].id

    while current_step_id and current_step_id != 'complete':
        # Execute current step
        step = self._get_step(current_step_id)
        result = await self._execute_step(step)

        if not result.success:
            # Handle failure
            break

        # Auto-progress to next step when auto_mode=True
        if self.auto_mode and step.next:
            current_step_id = step.next  # ← KEY FIX
        else:
            # Interactive mode: wait for user
            break

    # Execute complete step
    complete_step = self._get_step('complete')
    await self._execute_step(complete_step)
```

### Alternative: Workflow Resume Automation

If fixing step progression is complex, add **automatic workflow resumption**:

```python
# In task.py:_handle_run()
while not workflow_complete:
    state = run_workflow(task_id)

    if state.status == 'completed':
        break
    elif state.status == 'paused':
        # Auto-resume
        resume_workflow(state.workflow_id)
    else:
        # Error
        break
```

---

## Testing Requirements

### Test Case 1: Full Workflow Execution
```bash
tapps-agents task run test-task-001

# Expected:
# ✅ All steps execute automatically
# ✅ Task status updated to "done"
# ✅ No manual intervention required
```

### Test Case 2: Parallel Workflows
```bash
tapps-agents task run task-001 &
tapps-agents task run task-002 &
tapps-agents task run task-003 &

# Expected:
# ✅ All workflows complete independently
# ✅ No conflicts (BUG-001 already fixed)
# ✅ All tasks marked "done"
```

### Test Case 3: Workflow Failure Handling
```bash
tapps-agents task run failing-task

# Expected:
# ✅ Workflow stops at failing step
# ✅ Task status: "todo" or "blocked"
# ✅ Error clearly reported
```

---

## Workarounds (Temporary)

### Option 1: Manual Step Execution
```bash
# Run each step manually
tapps-agents workflow rapid --prompt "..." --step enhance
tapps-agents workflow rapid --prompt "..." --step planning
tapps-agents workflow rapid --prompt "..." --step implementation
# ...etc
```

### Option 2: Direct Agent Invocation
```bash
# Bypass workflows entirely
@enhancer *enhance "prompt"
@planner *plan "prompt"
@implementer *implement "description" file.py
@reviewer *review file.py
@tester *test file.py
```

### Option 3: Workflow Resume Loop (Manual)
```bash
# Keep resuming until complete
while true; do
    tapps-agents workflow resume --workflow-id <id>
    if [ $? -eq 0 ]; then break; fi
done
```

---

## Related Issues

- **BUG-001:** Git worktree conflicts (FIXED) - Was blocking parallel execution
- **BUG-002:** CLI quotation parsing (OPEN) - Causes implementation steps to fail
- **BUG-003:** Workflow error handling (OPEN) - Silent failures mask issues

---

## Recommended Priority

**PRIORITY: P0 (CRITICAL)**

**Why P0:**
- Blocks entire Beads task management system
- Affects all workflows (rapid, full, fix, quality, etc.)
- Breaks core framework promise of automation
- No acceptable workaround (manual is not scalable)

**Dependencies:**
- BUG-001: FIXED ✅ (parallel execution now possible)
- BUG-002: Can fix in parallel (separate issue)
- BUG-003: Can fix in parallel (separate issue)

**Estimated Effort:** 4-8 hours
- Investigate workflow executor step progression logic
- Implement auto-progression when auto_mode=True
- Add tests for full workflow execution
- Verify with all workflow presets

---

## Next Steps

1. **Investigate WorkflowExecutor code** - Find where step progression breaks
2. **Implement fix** - Enable auto-progression through workflow steps
3. **Test with HM-001** - Verify full workflow completion
4. **Test parallel execution** - Ensure BUG-001 fix still works
5. **Update documentation** - Document auto-mode behavior

---

**Reported By:** Claude Sonnet 4.5 (Session 2026-02-03)
**Affects:** All workflow presets (rapid-dev, full-sdlc, fix, quality, etc.)
**Framework Version:** v3.5.39+
**Blocks:** Beads task management, automated workflows, HM-001/ENH-002 execution
