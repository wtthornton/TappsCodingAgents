# Plan: Leverage Cursor as LLM with Continuous Communication

## Problem Statement

When running workflows in **headless mode**, the framework:
- Uses MAL (Model Abstraction Layer) for LLM calls instead of Cursor's LLM
- Runs fully automated without communication back to Cursor
- Provides no real-time progress updates to the user
- Cannot leverage Cursor's context and capabilities

**User Requirement**: Use Cursor as the LLM and maintain continuous communication during workflow execution.

---

## Current Architecture Analysis

### Headless Mode (Current Behavior)
```
CLI Command → WorkflowExecutor → MAL (LLM) → Agents → Results
```
- ❌ No communication back to Cursor
- ❌ Uses separate LLM (MAL) instead of Cursor
- ❌ Terminal output only
- ✅ Fully automated

### Cursor Mode (Available but Underutilized)
```
CLI Command → CursorWorkflowExecutor → Cursor Skills → Background Agents → Results
```
- ✅ Uses Cursor's LLM
- ⚠️ File-based coordination (semi-manual)
- ⚠️ Requires Background Agents configuration
- ✅ Can maintain communication via state files

---

## Solution Plan

### Phase 1: Enable Cursor Mode with Communication

#### 1.1 Use `--cursor-mode` Flag
Instead of headless mode, explicitly use Cursor mode:

```bash
python -m tapps_agents.cli create "Create a simple html page that says Hello world" --cursor-mode
```

**Benefits**:
- Uses Cursor's LLM instead of MAL
- Leverages Cursor Skills
- Can communicate via state files

#### 1.2 Enable Auto-Execution
Ensure Background Agents are configured for auto-execution:

```yaml
# .tapps-agents/config.yaml
workflow:
  auto_execution_enabled: true
  polling_interval: 5.0
  timeout_seconds: 3600
```

#### 1.3 Set Environment Variable
```powershell
$env:TAPPS_AGENTS_MODE="cursor"
```

---

### Phase 2: Implement Communication Mechanisms

#### 2.1 Progress Updates via State Files
The framework already saves state to `.tapps-agents/workflows/state/{workflow_id}.json`

**Enhancement**: Create a progress monitor that reads state and reports to user:

```python
# Monitor workflow state and report progress
import json
from pathlib import Path

def monitor_workflow_progress(workflow_id: str):
    state_file = Path(f".tapps-agents/workflows/state/{workflow_id}.json")
    while True:
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
                print(f"Progress: {len(state['completed_steps'])}/{total_steps}")
                print(f"Current: {state['current_step']}")
                print(f"Status: {state['status']}")
        time.sleep(2)
```

#### 2.2 Real-time Communication via Cursor Chat
Instead of silent execution, periodically send updates to Cursor chat:

**Option A**: Use Cursor's MCP tools to send messages
**Option B**: Create status files that Cursor can read
**Option C**: Use Background Agents to post updates

#### 2.3 Step-by-Step Execution with Feedback
Modify workflow execution to:
1. Execute one step at a time
2. Report completion to Cursor
3. Wait for acknowledgment (optional)
4. Proceed to next step

---

### Phase 3: Hybrid Approach (Recommended)

#### 3.1 Interactive Mode
Create a new execution mode: **"Interactive Cursor Mode"**

```python
# New mode: interactive_cursor
# - Uses Cursor's LLM
# - Executes steps one at a time
# - Reports progress after each step
# - Allows user to review/approve before next step
```

#### 3.2 Communication Channels

**Channel 1: State File Monitoring**
- Framework writes state updates
- Cursor reads state file periodically
- User sees progress in Cursor UI

**Channel 2: Progress Reports**
- After each step, create a progress report file
- Cursor displays report in chat or sidebar
- User can review before next step

**Channel 3: Direct Chat Integration**
- Use Cursor's chat API (if available)
- Send step completion messages
- Receive user feedback

---

## Implementation Steps

### Step 1: Modify CLI Command
Update `handle_create_command()` to support interactive Cursor mode:

```python
# tapps_agents/cli/commands/top_level.py
def handle_create_command(args: object) -> None:
    cursor_mode = getattr(args, "cursor_mode", False)
    interactive = getattr(args, "interactive", False)
    
    if interactive:
        # Force Cursor mode for interactive
        os.environ["TAPPS_AGENTS_MODE"] = "cursor"
        # Enable step-by-step execution
        os.environ["TAPPS_AGENTS_INTERACTIVE"] = "true"
```

### Step 2: Create Progress Reporter
Create a new module for progress reporting:

```python
# tapps_agents/workflow/progress_reporter.py
class CursorProgressReporter:
    """Reports workflow progress to Cursor."""
    
    def report_step_start(self, step: WorkflowStep):
        # Create status file
        # Optionally send to Cursor chat
        
    def report_step_complete(self, step: WorkflowStep, artifacts: dict):
        # Update status file
        # Report completion to user
        
    def report_progress(self, completed: int, total: int):
        # Send progress update
```

### Step 3: Modify CursorWorkflowExecutor
Add communication hooks:

```python
# tapps_agents/workflow/cursor_executor.py
class CursorWorkflowExecutor:
    def __init__(self, ...):
        self.progress_reporter = CursorProgressReporter() if interactive else None
        
    async def _execute_step(self, step: WorkflowStep):
        if self.progress_reporter:
            self.progress_reporter.report_step_start(step)
        
        # Execute step...
        
        if self.progress_reporter:
            self.progress_reporter.report_step_complete(step, artifacts)
```

### Step 4: Create Status File Format
Standardize status file format for Cursor to read:

```json
{
  "workflow_id": "full-sdlc-20250113-123456",
  "status": "running",
  "current_step": "architect/design_system",
  "progress": {
    "completed": 3,
    "total": 10,
    "percentage": 30
  },
  "last_update": "2025-01-13T12:34:56Z",
  "recent_artifacts": [...]
}
```

---

## Recommended Approach: Immediate Solution

### Quick Fix: Use Cursor Mode with State Monitoring

1. **Run with Cursor mode**:
   ```powershell
   $env:TAPPS_AGENTS_MODE="cursor"
   python -m tapps_agents.cli create "Create a simple html page that says Hello world" --cursor-mode
   ```

2. **Monitor state file**:
   - Framework writes to `.tapps-agents/workflows/state/{workflow_id}.json`
   - User can periodically check this file
   - Or create a simple monitor script

3. **Enable Background Agents**:
   - Ensure `.cursor/background-agents.yaml` is configured
   - Background Agents will execute Skills automatically

### Better Solution: Interactive Mode Script

Create a wrapper script that:
1. Runs workflow in Cursor mode
2. Monitors state file
3. Reports progress to user
4. Allows step-by-step execution

```python
# scripts/run_interactive_workflow.py
import asyncio
from tapps_agents.cli.commands.top_level import handle_create_command
from tapps_agents.workflow.progress_reporter import CursorProgressReporter

async def run_interactive(prompt: str):
    # Set Cursor mode
    os.environ["TAPPS_AGENTS_MODE"] = "cursor"
    os.environ["TAPPS_AGENTS_INTERACTIVE"] = "true"
    
    # Start workflow
    # Monitor and report progress
    # Communicate with user
```

---

## Testing Plan

1. **Test Cursor Mode Detection**
   - Verify `TAPPS_AGENTS_MODE=cursor` is detected
   - Verify `CursorWorkflowExecutor` is used

2. **Test State File Updates**
   - Verify state file is created
   - Verify state updates after each step
   - Verify progress can be read from state file

3. **Test Communication**
   - Verify progress reports are generated
   - Verify user can see updates
   - Verify Background Agents execute Skills

---

## Next Steps

1. **Immediate**: Use `--cursor-mode` flag and monitor state file
2. **Short-term**: Create progress monitoring script
3. **Long-term**: Implement full interactive mode with chat integration

---

## Files to Modify

1. `tapps_agents/cli/commands/top_level.py` - Add `--interactive` flag
2. `tapps_agents/workflow/cursor_executor.py` - Add progress reporting
3. `tapps_agents/workflow/progress_reporter.py` - New file for reporting
4. `scripts/monitor_workflow.py` - New script for monitoring

---

## Summary

**Current Problem**: Headless mode uses MAL and has no communication.

**Solution**: Use Cursor mode with:
- State file monitoring
- Progress reporting
- Background Agents for execution
- Optional interactive mode for step-by-step execution

**Key Insight**: The framework already supports Cursor mode - we just need to:
1. Use it explicitly (`--cursor-mode`)
2. Monitor state files for progress
3. Optionally add interactive reporting

