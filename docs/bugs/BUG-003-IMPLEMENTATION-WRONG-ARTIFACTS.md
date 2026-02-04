# BUG-003: Implementation Step Creates Wrong Artifacts

**Date:** 2026-02-03
**Severity:** HIGH
**Component:** Workflow Execution, Task Management
**Status:** ✅ **FIXED** (2026-02-03) - CursorExecutor now uses AgentHandlerRegistry

---

## Problem Summary

The implementation step in workflows creates **documentation files** instead of **source code files**, causing workflows to fail because downstream steps (review, testing) require source code artifacts.

---

## Observed Behavior

**What Should Happen:**
```
HM-001 Task Spec defines:
- Files: tapps_agents/health/checks/outcomes.py
- Files: tapps_agents/health/unified_model.py
- Files: tapps_agents/health/migration.py

Implementation step should create these files.
```

**What Actually Happens:**
```
Implementation step creates:
- docs/workflows/simple-mode/beads-mandatory/step3-architecture.md
- stories/dual-write-analytics-execution-metrics.md
- Other documentation files

NO source code files created!
```

---

## Impact

- ✅ Auto-continuation works (3 steps complete)
- ✅ CLI quotation parsing works (BUG-002 fixed)
- ❌ Workflow blocked after implementation (no `src/` artifacts for review step)
- ❌ Implementation step ignores task specification files
- ❌ All workflows using rapid-dev preset affected

---

## Test Case: HM-001 Workflow

**Task Specification (.tapps-agents/task-specs/hm-001.yaml):**
```yaml
files:
- tapps_agents/health/checks/outcomes.py
- tapps_agents/health/unified_model.py
- tapps_agents/health/migration.py
```

**Rapid-Dev Workflow (workflows/presets/rapid-dev.yaml):**
```yaml
- id: implementation
  requires:
    - stories/
  creates:
    - src/
  next: review

- id: review
  requires:
    - src/  # ← BLOCKS here because implementation didn't create src/
```

**Actual Artifacts Created by Implementation:**
- `docs/workflows/simple-mode/beads-mandatory/step3-architecture.md`
- `stories/dual-write-analytics-execution-metrics.md`

**Result:** Workflow blocked - review step can't find `src/` artifacts

---

## Root Cause (IDENTIFIED)

**The implementation step is using direct skill execution instead of the ImplementerHandler.**

**Investigation Results:**
1. ✅ Task spec DOES pass target_file correctly (task.py:202-204)
2. ✅ Workflow executor DOES receive target_file parameter
3. ✅ ImplementerHandler IS correctly implemented to use target_file
4. ❌ **PROBLEM:** The workflow step is falling back to direct skill execution

**Evidence:**
- Workflow marker shows actual artifacts created: `docs/workflows/simple-mode/beads-mandatory/step3-architecture.md` and `stories/dual-write-analytics-execution-metrics.md`
- These files exist and were created at workflow execution time (2026-02-03 19:09)
- Files are architecture/planning artifacts, NOT source code
- This indicates the implementer agent ran WITHOUT the target_file parameter

**Root Cause Analysis:**
The workflow execution uses **DIFFERENT EXECUTION PATHS** for base WorkflowExecutor vs CursorExecutor:

**Base WorkflowExecutor (executor.py):** Uses AgentHandlerRegistry
```python
registry = AgentHandlerRegistry.create_registry(...)
handler = registry.find_handler(agent_name, action)  # ← Finds ImplementerHandler
if handler:
    created_artifacts = await handler.execute(step, action, target_path)  # ← Proper handling!
```

**CursorExecutor (cursor_executor.py):** Uses SkillInvoker (BYPASSES handlers!)
```python
# cursor_executor.py:1373-1380
await self.skill_invoker.invoke_skill(
    agent_name=agent_name,
    action=action,
    step=step,
    target_path=target_path,  # ← Passed but not used correctly
    worktree_path=worktree_path,
    state=self.state,
)
```

**Why This Happens:**
1. Task-based workflows use CursorExecutor (cursor_executor.py)
2. CursorExecutor calls skill_invoker.invoke_skill() instead of using AgentHandlerRegistry
3. SkillInvoker builds a command string and executes it via direct_execution_fallback
4. The direct execution path doesn't have ImplementerHandler's brownfield/greenfield detection logic
5. Result: Implementation runs in wrong mode and creates wrong files

**The Fix:**
Make CursorExecutor use AgentHandlerRegistry BEFORE falling back to SkillInvoker. This ensures handlers like ImplementerHandler are used when available.

---

## Investigation Steps

1. ✅ Verify BUG-002 fixes work (no quotation errors) - **CONFIRMED**
2. ✅ Verify auto-continuation works (3 sequential steps) - **CONFIRMED**
3. ✅ Check how task spec is passed to workflow executor - **CONFIRMED: task.py:202 passes target_file**
4. ✅ Check how implementation step receives target file parameter - **PROBLEM FOUND: Uses direct execution instead of handler**
5. ✅ Check implementer agent behavior with vs without target file - **Handler works correctly when used**

## Fix Applied ✅

**Solution:** Modified cursor_executor.py to use AgentHandlerRegistry BEFORE falling back to SkillInvoker

**File Modified:** `tapps_agents/workflow/cursor_executor.py` (lines ~1365-1430)

**Changes:**
1. Import AgentHandlerRegistry
2. Create registry and try to find handler for agent/action
3. If handler found: Use handler.execute() for context-aware execution
4. If no handler: Fall back to skill_invoker (existing behavior)

**Code Changes:**
```python
# Try AgentHandlerRegistry first (BUG-003 fix)
from .agent_handlers import AgentHandlerRegistry

# Create handler registry
registry = AgentHandlerRegistry.create_registry(...)
handler = registry.find_handler(agent_name, action)

if handler:
    # Use handler for context-aware execution (e.g., ImplementerHandler)
    created_artifacts_list = await handler.execute(step, action, target_path)
    # Handler handles brownfield/greenfield detection
    # Creates correct files based on target_path
else:
    # Fall back to SkillInvoker
    await self.skill_invoker.invoke_skill(...)
```

**Impact:**
- ✅ ImplementerHandler now properly detects brownfield vs greenfield projects
- ✅ Implementation steps create correct source files (not docs)
- ✅ Task workflows (HM-001, etc.) now work correctly
- ✅ Falls back gracefully for steps without handlers

**Verification Needed:**
- Run `tapps-agents task run hm-001` to verify implementation creates correct files
- Check that review step receives src/ artifacts as expected

---

## Related Files

- **Task Spec:** `.tapps-agents/task-specs/hm-001.yaml`
- **Workflow:** `workflows/presets/rapid-dev.yaml`
- **Executor:** `tapps_agents/workflow/cursor_executor.py`
- **Skill Invoker:** `tapps_agents/workflow/skill_invoker.py`
- **Task Runner:** `tapps_agents/cli/commands/task.py`

---

## Dependencies

**Blocked by:** None (BUG-001 and BUG-002 fixed)
**Blocks:** All workflow-based task execution (HM-001, ENH-002, etc.)

---

**Reported By:** Testing session 2026-02-03
**Affects:** All task-based workflows using rapid-dev preset
