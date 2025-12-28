# Background Agents Monitoring and Output Guide

This guide explains how to monitor Background Agent execution, where to find terminal output, and what happens when errors occur.

## How to Know When Background Agents Are Running

### 1. Terminal Output (Primary Method)

**All Background Agent output goes to `stderr`**, so it remains visible even when output is redirected. You'll see clear execution indicators:

#### Task Start Indicator
```
============================================================
[BACKGROUND AGENT TASK] Starting
Agent ID: quality-analyzer
Task ID: quality-analysis-2025-01-XX
Command: reviewer analyze-project
============================================================
```

#### Setup Phase
```
[BACKGROUND AGENT] Setting up environment...
[BACKGROUND AGENT] Setup complete
```

#### Command Execution
```
============================================================
[BACKGROUND AGENT] Starting: reviewer analyze-project
============================================================
[BACKGROUND AGENT] Running reviewer analyze-project...
```

#### Success Completion
```
============================================================
[BACKGROUND AGENT] Completed: reviewer analyze-project
Result saved to: .tapps-agents/reports/quality-analysis-reviewer-analyze-project.json
============================================================

============================================================
[BACKGROUND AGENT TASK] Completed Successfully
Task ID: quality-analysis-2025-01-XX
============================================================
```

### 2. Progress Files (JSON Format)

Progress is tracked in real-time JSON files:
- **Location**: `.tapps-agents/reports/progress-{task-id}.json`
- **Updated**: Continuously during execution
- **Format**: JSON with status, timestamps, and step information

**Example Progress File:**
```json
{
  "task_id": "quality-analysis-2025-01-16",
  "start_time": "2025-01-16T10:00:00Z",
  "current_time": "2025-01-16T10:05:00Z",
  "elapsed_seconds": 300,
  "status": "in_progress",
  "steps": [
    {
      "step": "setup",
      "status": "completed",
      "timestamp": "2025-01-16T10:00:05Z",
      "elapsed_seconds": 5
    },
    {
      "step": "command_start",
      "status": "in_progress",
      "message": "Running reviewer analyze-project",
      "timestamp": "2025-01-16T10:00:10Z",
      "elapsed_seconds": 10
    }
  ]
}
```

**Status Values:**
- `in_progress`: Task is currently running
- `completed`: Task finished successfully
- `failed`: Task encountered an error
- `setup`: Initial setup phase
- `command_start`: Command execution started
- `command_complete`: Command finished
- `cleanup`: Cleanup phase

### 3. Cursor UI - Background Agents Panel

If Background Agents are working correctly:
- Look for **"Background Agents"** panel in Cursor sidebar
- Active agents show execution status
- Progress indicators may be visible (depends on Cursor version)

### 4. Result Files

When agents complete successfully, results are saved to:
- **Location**: `.tapps-agents/reports/{task-id}-{agent}-{command}.json`
- **Format**: JSON with command results

**Example Result File Path:**
```
.tapps-agents/reports/quality-analysis-2025-01-16-reviewer-analyze-project.json
```

### 5. Worktree Activity

During execution, git worktrees are created:
- **Location**: `.tapps-agents/worktrees/{agent-id}/`
- **Evidence**: Directory exists while agent is running
- **Cleanup**: Automatically removed when task completes

Check for active worktrees:
```bash
git worktree list
```

## Where Terminal Output Appears

### In Cursor IDE

**Important**: Background Agents output goes to **`stderr`**, which typically appears in:

1. **Cursor's Terminal Panel**
   - Open terminal in Cursor (View → Terminal or `Ctrl+`` `)
   - Look for output with `[BACKGROUND AGENT]` prefixes

2. **Cursor's Background Agents Logs**
   - Cursor menu → Help → Toggle Developer Tools
   - Check Console for Background Agent messages
   - Look for output in Background Agents panel logs

3. **System Terminal** (if running commands directly)
   - If you run `python -m tapps_agents.cli` commands directly
   - Output appears in the terminal where command was executed

### Output Format Details

All execution indicators use this format:
```python
print(message, file=sys.stderr, flush=True)
```

This ensures:
- ✅ Output is **always visible** (not buffered)
- ✅ Output appears even when stdout is redirected
- ✅ Messages are **clearly marked** with `[BACKGROUND AGENT]` prefix

## What Happens When Background Agents Error Out

### Error Display Format

When errors occur, you'll see clear error indicators:

#### Setup Failure
```
============================================================
[BACKGROUND AGENT TASK] Setup Failed
Error: [error message here]
============================================================
```

#### Command Failure
```
============================================================
[BACKGROUND AGENT] Failed: reviewer analyze-project
Error: [error message here]
============================================================
```

#### Task Failure
```
============================================================
[BACKGROUND AGENT TASK] Failed
Task ID: quality-analysis-2025-01-16
Error: [error message here]
============================================================
```

### Error Information Sources

When errors occur, check these locations:

#### 1. Terminal Output (stderr)
- Error messages are printed to stderr with clear formatting
- Look for `[BACKGROUND AGENT TASK] Failed` or `[BACKGROUND AGENT] Failed`
- Error messages include exception details

#### 2. Progress Files
Progress files update to show failure:
```json
{
  "task_id": "quality-analysis-2025-01-16",
  "status": "failed",
  "error": "Error message here",
  "steps": [
    {
      "step": "command_failed",
      "status": "failed",
      "message": "Command failed: [error]"
    }
  ]
}
```

#### 3. Result Files (Error Cases)
Even on failure, result files may be created with error information:
```json
{
  "success": false,
  "error": "Error message here",
  "task_id": "quality-analysis-2025-01-16"
}
```

#### 4. Cursor Logs
- Cursor menu → Help → Toggle Developer Tools
- Check Console for detailed error stack traces
- Look for error logs in Background Agents panel

#### 5. Python Exception Traces
If the error originates from Python code, full stack traces are logged:
- Check Cursor's developer console
- Check terminal output for Python tracebacks
- Framework logs may contain additional context

### Error Handling Behavior

#### Automatic Cleanup
Even when errors occur:
1. **Cleanup Always Runs**: Worktrees are removed (if created)
2. **Progress Files Updated**: Status set to "failed"
3. **Error Messages Saved**: Error information persists in progress/result files

#### Error Types

**Setup Errors:**
- Git worktree creation failures
- Directory permission issues
- Configuration problems

**Command Errors:**
- Agent command failures
- Dependency errors (missing packages)
- Python execution errors

**Execution Errors:**
- Timeout errors
- Resource exhaustion
- System errors

### Monitoring Error State

Check if an agent failed:

**1. Check Progress File:**
```bash
cat .tapps-agents/reports/progress-{task-id}.json
```

Look for:
- `"status": "failed"`
- `"error"` field with error message

**2. Check Result File:**
```bash
cat .tapps-agents/reports/{task-id}-{agent}-{command}.json
```

Look for:
- `"success": false`
- `"error"` field with error details

**3. Check Terminal Output:**
Look for error indicators in terminal:
- `[BACKGROUND AGENT TASK] Failed`
- `[BACKGROUND AGENT] Failed`

**4. Check Worktree Status:**
```bash
git worktree list
```

If worktree still exists after error, cleanup may have failed (unusual).

## Best Practices for Monitoring

### During Execution

1. **Watch Terminal Output**
   - Keep terminal panel open in Cursor
   - Look for execution indicators
   - Monitor for error messages

2. **Check Progress Files Periodically**
   ```bash
   # Watch progress file (Linux/Mac)
   watch -n 2 cat .tapps-agents/reports/progress-{task-id}.json
   
   # Or manually check
   cat .tapps-agents/reports/progress-{task-id}.json | jq .
   ```

3. **Monitor Worktrees**
   ```bash
   # List active worktrees
   git worktree list
   ```

### After Completion

1. **Check Result Files**
   ```bash
   ls -lh .tapps-agents/reports/{task-id}-*
   ```

2. **Verify Success**
   - Look for `[BACKGROUND AGENT TASK] Completed Successfully` in terminal
   - Check result file for `"success": true`
   - Verify worktree was cleaned up

3. **Review Errors** (if failed)
   - Read error message in terminal output
   - Check progress file for error details
   - Review Cursor logs for stack traces

## Troubleshooting: No Output Visible

If you don't see any output:

### 1. Check Terminal Panel
- Ensure terminal is open in Cursor
- Check if output is being filtered or hidden
- Try scrolling to see if output is above viewport

### 2. Check Cursor Logs
- Cursor menu → Help → Toggle Developer Tools
- Check Console for Background Agent messages
- Look for errors that might prevent output

### 3. Check Progress Files
```bash
ls -la .tapps-agents/reports/progress-*.json
```

If progress files exist but no terminal output:
- Agent may be running but output isn't visible
- Check progress file status to confirm execution

### 4. Verify Agent Triggered
- Confirm agent was actually triggered
- Check Background Agents panel in Cursor
- Look for worktree creation as evidence

### 5. Check Command Execution
Try running command directly to see if it works:
```bash
python -m tapps_agents.cli reviewer analyze-project --format json
```

If this works but Background Agent doesn't show output:
- Output may be going to Cursor's Background Agents logs
- Check Cursor's Background Agents panel for output

## Summary

| Indicator | Location | What It Means |
|-----------|----------|---------------|
| `[BACKGROUND AGENT TASK] Starting` | Terminal (stderr) | Agent task started |
| `[BACKGROUND AGENT] Running...` | Terminal (stderr) | Command executing |
| `[BACKGROUND AGENT TASK] Completed Successfully` | Terminal (stderr) | Task finished successfully |
| `[BACKGROUND AGENT TASK] Failed` | Terminal (stderr) | Task encountered error |
| Progress file `status: "in_progress"` | `.tapps-agents/reports/progress-*.json` | Task is running |
| Progress file `status: "failed"` | `.tapps-agents/reports/progress-*.json` | Task failed |
| Result file `"success": true` | `.tapps-agents/reports/*.json` | Command succeeded |
| Result file `"success": false` | `.tapps-agents/reports/*.json` | Command failed |
| Worktree exists | `.tapps-agents/worktrees/{agent-id}/` | Agent is or was running |

## Quick Reference

**Check if agent is running:**
```bash
# Check progress files
ls -la .tapps-agents/reports/progress-*.json

# Check worktrees
git worktree list

# Watch progress file
cat .tapps-agents/reports/progress-{task-id}.json | jq .
```

**Find errors:**
```bash
# Check progress file for errors
cat .tapps-agents/reports/progress-{task-id}.json | jq .error

# Check result file
cat .tapps-agents/reports/{task-id}-*.json | jq .success, .error
```

**Monitor output:**
- Watch terminal panel in Cursor (stderr output)
- Check Cursor's Background Agents panel
- Review progress files periodically
