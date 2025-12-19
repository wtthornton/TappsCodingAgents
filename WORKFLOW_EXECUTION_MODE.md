# Workflow Execution Mode Guide

## Problem: "Manual Mode" and No Terminal Output

When running workflows, you may see:
- "Waiting for {agent}/{action} to complete (manual mode)..."
- No output in terminal
- Workflow appears to hang

## Root Cause

The framework detects **Cursor mode** automatically and uses `CursorWorkflowExecutor`, which:
1. Uses Background Agents (file-based coordination)
2. Requires `auto_execution_enabled: true` in config to run automatically
3. Defaults to **manual mode** (creates command files, waits for execution)
4. Output goes to log files, not terminal

## Solutions

### Solution 1: Force Headless Mode (Recommended for CLI)

Force headless mode to use the regular `WorkflowExecutor` which:
- Shows output in terminal
- Runs fully automated
- Doesn't require Background Agents

**In your script:**
```python
import os
os.environ["TAPPS_AGENTS_MODE"] = "headless"
```

**Or via command line:**
```powershell
$env:TAPPS_AGENTS_MODE="headless"
python run_amazon_workflow.py
```

### Solution 2: Enable Auto-Execution (For Cursor Mode)

If you want to use Cursor mode with Background Agents:

1. **Edit `.tapps-agents/config.yaml`:**
```yaml
workflow:
  auto_execution_enabled: true
  polling_interval: 5.0
  timeout_seconds: 3600
```

2. **Or set in workflow metadata** (`workflows/presets/full-sdlc.yaml`):
```yaml
metadata:
  auto_execution: true
```

### Solution 3: Check Runtime Mode

To see which mode is active:

```python
from tapps_agents.core.runtime_mode import detect_runtime_mode
print(f"Runtime mode: {detect_runtime_mode()}")
```

## Mode Detection

The framework detects Cursor mode if:
- `TAPPS_AGENTS_MODE=cursor` or `background` is set
- OR any of these environment variables exist:
  - `CURSOR`
  - `CURSOR_IDE`
  - `CURSOR_SESSION_ID`
  - `CURSOR_WORKSPACE_ROOT`
  - `CURSOR_TRACE_ID`

## When to Use Each Mode

### Headless Mode (CLI/CI)
- ✅ Running from command line
- ✅ Want terminal output
- ✅ Fully automated execution
- ✅ No Background Agents needed

### Cursor Mode (Inside Cursor IDE)
- ✅ Running from Cursor Skills/Background Agents
- ✅ Want to use Cursor's LLM
- ✅ Need Background Agent coordination
- ⚠️ Requires auto-execution enabled for automation

## Quick Fix for Your Script

The `run_amazon_workflow.py` script now includes:
```python
os.environ["TAPPS_AGENTS_MODE"] = "headless"
```

This ensures:
- ✅ Terminal output visible
- ✅ Fully automated execution
- ✅ No manual mode waiting

## Troubleshooting

### Issue: Still seeing "manual mode"
**Check:** Is `TAPPS_AGENTS_MODE` set correctly?
```powershell
echo $env:TAPPS_AGENTS_MODE
```

### Issue: No terminal output
**Check:** Are you in headless mode?
```python
from tapps_agents.core.runtime_mode import is_cursor_mode
print(f"Is Cursor mode: {is_cursor_mode()}")
```

### Issue: Workflow hangs
**Check:** If in Cursor mode, is auto-execution enabled?
```yaml
# .tapps-agents/config.yaml
workflow:
  auto_execution_enabled: true
```

## Summary

For **CLI execution with terminal output**, always use:
```python
os.environ["TAPPS_AGENTS_MODE"] = "headless"
```

This bypasses Cursor mode and uses the direct executor that shows output and runs automatically.

