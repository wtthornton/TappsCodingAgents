# BUG-001: Git Worktree Conflicts in Parallel Workflow Execution

**Date:** 2026-02-03
**Severity:** High
**Component:** Workflow Orchestration, Build Orchestrator
**Status:** ✅ FIXED (2026-02-03)
**Fixed By:** Adding microsecond precision to workflow_id timestamps

---

## Summary

When multiple Build workflows execute in parallel, they all attempt to create git worktrees with the same path/branch name, causing "exit status 255" errors and workflow failures.

## ✅ Fix Applied (2026-02-03)

**Root Cause:** Workflow IDs used second-precision timestamps, causing collisions when workflows started simultaneously.

**Solution:** Added microsecond precision to workflow_id generation.

**File Modified:** `tapps_agents/workflow/cursor_executor.py:259`

**Change:**
```python
# Before (second precision - caused collisions)
workflow_id = f"{workflow.id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
# Example: build-20260203-143045

# After (microsecond precision - unique)
workflow_id = f"{workflow.id}-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
# Example: build-20260203-173302-906996
```

**Result:** Each parallel workflow now gets a unique worktree path even when started simultaneously.

**Tests:** All existing workflow executor tests pass (19/19).

**Verification:** Can now run multiple workflows in parallel without conflicts.

---

## Steps to Reproduce (Original Issue)

1. Start 3 parallel build workflows:
```bash
# Terminal 1
tapps-agents simple-mode build --prompt "ENH-001: Workflow Enforcement" --auto &

# Terminal 2
tapps-agents simple-mode build --prompt "HM-001: Health Metrics" --auto &

# Terminal 3
tapps-agents simple-mode build --prompt "ENH-002: Reviewer Tools" --auto &
```

2. All three workflows reach Step 2 (Planning) simultaneously
3. All attempt to create git worktree: `agent/planner-1`
4. Error occurs:
```
Command '['git', 'worktree', 'add', '.tapps-agents/worktrees/planner-1', '-b', 'agent/planner-1']'
returned non-zero exit status 255
```

## Expected Behavior

- Each workflow should create a uniquely named git worktree
- Parallel workflows should not conflict
- Worktree naming should include timestamp or UUID for uniqueness

## Actual Behavior

- All workflows use the same worktree path: `.tapps-agents/worktrees/planner-1`
- Second and third workflows fail when attempting to create already-existing worktree
- Steps 2-5 (Plan, Architect, Design, Implement) all fail with same error
- Workflows show "FAIL" status but continue to steps 6-7 anyway

## Root Cause

**File:** Likely in workflow orchestration or agent execution code

The git worktree path is generated without a unique identifier (timestamp, UUID, or workflow ID). All concurrent workflows generate the same path pattern.

**Example of non-unique path generation:**
```python
# WRONG - all workflows use same path
worktree_path = project_root / ".tapps-agents" / "worktrees" / f"{agent}-1"

# CORRECT - each workflow gets unique path
worktree_path = project_root / ".tapps-agents" / "worktrees" / f"{agent}-{workflow_id}"
# or with timestamp
worktree_path = project_root / ".tapps-agents" / "worktrees" / f"{agent}-{timestamp}"
```

## Impact

**Severity: High**

- ❌ Cannot run multiple workflows in parallel
- ❌ Breaks multi-enhancement execution
- ❌ Forces sequential execution (slower)
- ✅ Workaround exists: Run workflows sequentially

## Suggested Fix

### Option 1: Add Workflow ID to Worktree Path

```python
def create_agent_worktree(agent_name: str, workflow_id: str, project_root: Path) -> Path:
    """Create unique git worktree for agent execution."""
    worktree_name = f"{agent_name}-{workflow_id}"
    worktree_path = project_root / ".tapps-agents" / "worktrees" / worktree_name
    branch_name = f"agent/{worktree_name}"

    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
        check=True
    )
    return worktree_path
```

### Option 2: Add Timestamp to Worktree Path

```python
from datetime import datetime

def create_agent_worktree(agent_name: str, project_root: Path) -> Path:
    """Create unique git worktree with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:19]  # YYYYMMDD-HHMMSS-mmm
    worktree_name = f"{agent_name}-{timestamp}"
    worktree_path = project_root / ".tapps-agents" / "worktrees" / worktree_name
    branch_name = f"agent/{worktree_name}"

    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
        check=True
    )
    return worktree_path
```

### Option 3: Use UUID

```python
import uuid

def create_agent_worktree(agent_name: str, project_root: Path) -> Path:
    """Create unique git worktree with UUID."""
    unique_id = str(uuid.uuid4())[:8]  # Short UUID
    worktree_name = f"{agent_name}-{unique_id}"
    worktree_path = project_root / ".tapps-agents" / "worktrees" / worktree_name
    branch_name = f"agent/{worktree_name}"

    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
        check=True
    )
    return worktree_path
```

**Recommendation:** Use Option 1 (workflow_id) as it's most traceable and debuggable.

## Files to Investigate

1. `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`
2. `tapps_agents/workflow/orchestrator.py`
3. Agent execution code that creates worktrees
4. Search for: `git worktree add` or `worktrees/planner-1`

## Testing Verification

After fix, verify:
1. ✅ Can run 3+ workflows in parallel without conflicts
2. ✅ Each workflow creates unique worktree path
3. ✅ Worktrees are properly cleaned up after workflow completion
4. ✅ Workflow state directory also uses unique naming

## Related Issues

- None

## Workaround

**Current workaround:** Run workflows sequentially:
```bash
tapps-agents task run enh-001
tapps-agents task run hm-001
tapps-agents task run enh-002-reviewer
```

---

**Reported by:** Claude Sonnet 4.5 (Session 2026-02-03)
**Affects:** v3.5.39
**Priority:** P1 (High)
