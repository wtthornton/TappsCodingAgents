# Cursor IDE Integration Analysis

## Summary: **YES, but with important caveats**

The project **does work with Cursor IDE**, but the integration model is **file-based coordination** rather than direct programmatic API calls. Here's how it actually works:

---

## How Cursor Integration Actually Works

### 1. **Runtime Mode Detection**
- The framework detects Cursor mode via environment variables (`CURSOR_IDE`, `CURSOR_SESSION_ID`, etc.)
- Or explicitly via `TAPPS_AGENTS_MODE=cursor`
- When in Cursor mode, `WorkflowExecutor.execute()` automatically delegates to `CursorWorkflowExecutor`

### 2. **Execution Model: File-Based Coordination**

**The key insight:** Cursor IDE doesn't have a public programmatic API for Skills. Instead, the framework uses a **file-based coordination pattern**:

1. **Worktree Creation**: Each workflow step runs in an isolated Git worktree
2. **Command File Generation**: Creates `.cursor-skill-command.txt` files with Skill commands (e.g., `@analyst gather-requirements ...`)
3. **Instructions**: Creates `.cursor-skill-instructions.md` with execution instructions
4. **Background Agent Fallback**: Attempts to use Background Agent API (if available), but falls back to file-based execution
5. **Completion Detection**: Polls for expected artifacts to detect when Skills complete

### 3. **Two Execution Paths**

#### Path A: Background Agent API (Attempted, but likely unavailable)
- Tries to use `BackgroundAgentAPI` to programmatically trigger agents
- Uses `https://api.cursor.com/v0` (requires API key)
- **Issue**: This API likely doesn't exist or isn't public yet
- Falls back to file-based execution if API fails

#### Path B: File-Based Execution (Actual implementation)
- Creates command files in worktrees (`.cursor-skill-command.txt`)
- Creates instruction files (`.cursor-skill-instructions.md`)
- **Assumes**: Users manually execute commands in Cursor chat OR Background Agents read these files

---

## What Actually Works

✅ **Git Worktree Isolation**: Works perfectly - each step runs in its own worktree
✅ **Command Generation**: Creates proper Skill commands in correct format
✅ **State Management**: Workflow state persistence works correctly
✅ **Timeline Generation**: Will generate timeline when workflow completes
✅ **Artifact Tracking**: Detects and tracks artifacts created by Skills
✅ **Runtime Mode Detection**: Correctly detects Cursor vs headless mode
✅ **DONE/FAILED Markers**: Explicit completion/failure markers for each step (`.tapps-agents/workflows/markers/{workflow_id}/step-{step_id}/`)
✅ **Correlation IDs**: Consistent workflow_id/step_id propagation across logs, events, and coordination files
✅ **Secret Redaction**: Coordination files automatically redact API keys, tokens, and passwords before persistence

---

## What Doesn't Work (Yet)

❌ **Automatic Skill Execution**: No direct programmatic way to invoke Cursor Skills (by design - runs on top of Cursor)
❌ **Background Agent API**: The API at `https://api.cursor.com/v0` appears to be non-existent or private
⚠️ **Polling/Completion Detection**: Completion detection uses artifact polling and DONE/FAILED markers (improved reliability)
⚠️ **Real-time Progress**: Progress updates via state files and event bus (no streaming, but structured and observable)

---

## How Users Actually Execute This

### Current Reality:
1. User runs: `python -m tapps_agents.cli create "prompt"` (or workflow command)
2. Framework creates worktrees and command files (with correlation metadata and redacted secrets)
3. Framework writes DONE/FAILED markers for each step execution
4. **User must manually** (if auto-execution disabled):
   - Open each worktree directory
   - Copy the command from `.cursor-skill-command.txt` (secrets already redacted)
   - Paste into Cursor chat
   - Execute the Skill
   - Framework detects completion via artifacts or DONE markers
   - Framework automatically advances to next step

### Troubleshooting Stalled Steps:
1. **Check for failure marker**: `.tapps-agents/workflows/markers/{workflow_id}/step-{step_id}/FAILED.json`
   - Contains error message, expected/found artifacts, duration, error type
2. **Check for DONE marker**: `.tapps-agents/workflows/markers/{workflow_id}/step-{step_id}/DONE.json`
   - Confirms step completed successfully with artifact summary
3. **Check command file**: `.cursor-skill-command.txt` in worktree
   - Includes correlation metadata (workflow_id, step_id, expected artifacts)
   - Secrets are automatically redacted
4. **Check workflow state**: `.tapps-agents/workflow-state/{workflow_id}.json`
   - Contains full workflow execution state with correlation IDs

### Intended Future (with Background Agents):
1. Framework creates command files
2. Background Agents read these files automatically
3. Execute Skills autonomously
4. Framework detects completion via artifacts

---

## Code Evidence

### 1. Execution Delegation (✅ Works)
```python
# tapps_agents/workflow/executor.py:210
if is_cursor_mode():
    cursor_executor = CursorWorkflowExecutor(...)
    return await cursor_executor.run(...)
```

### 2. Skill Invocation (⚠️ Partial)
```python
# tapps_agents/workflow/skill_invoker.py:421
if self.use_api and self.background_agent_api:
    try:
        # Tries API first, but likely fails
        trigger_result = self.background_agent_api.trigger_agent(...)
    except Exception:
        # Falls back to file-based
        pass

# Creates command files (actual implementation)
command_file = create_skill_command_file(...)
```

### 3. Background Agent API (❌ Likely Non-Existent)
```python
# tapps_agents/workflow/background_agent_api.py:38
self.base_url = base_url or "https://api.cursor.com/v0"
# This API endpoint likely doesn't exist publicly
```

---

## Conclusion

**The architecture is sound and durable for Cursor-first execution.**

The framework:
- ✅ Correctly detects Cursor mode
- ✅ Creates proper Skill command files with correlation metadata and secret redaction
- ✅ Writes explicit DONE/FAILED markers for each step execution
- ✅ Manages workflow state correctly with correlation IDs throughout
- ✅ Provides structured completion detection (artifacts + markers)
- ✅ Will generate timelines when workflows complete
- ✅ Propagates correlation IDs (workflow_id:step_id) across logs, events, and files
- ⚠️ Requires manual Skill execution OR Background Agents that can read files (by design - no API dependency)
- ❌ Cannot automatically invoke Skills programmatically (by design - runs on top of Cursor)

**Troubleshooting**: When steps stall or fail, check marker files at:
`.tapps-agents/workflows/markers/{workflow_id}/step-{step_id}/DONE.json` or `FAILED.json`

**For the test to work:**
- The test should work IF Background Agents are configured to read the command files
- OR if the test framework simulates executing the commands
- OR if there's a way to manually trigger Skills (which is the current reality)

**Recommendation:** The test should acknowledge this design choice and verify:
1. ✅ Command files are created correctly with correlation metadata
2. ✅ DONE/FAILED markers are written for each step
3. ✅ Secrets are redacted from coordination files
4. ✅ Correlation IDs are present in all artifacts (logs, events, state)
5. ✅ Completion detection works with both artifacts and markers
6. Document that manual execution is required if Background Agents are not running (by design - runs on top of Cursor)

