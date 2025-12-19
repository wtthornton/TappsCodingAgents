# Quick Start: Use Cursor as LLM with Communication

## Problem Solved

**Before**: Workflows run in headless mode using MAL (separate LLM) with no communication back to Cursor.

**After**: Workflows use Cursor's LLM and maintain communication via state monitoring.

---

## Immediate Solution (3 Steps)

### Step 1: Run Workflow in Cursor Mode

```powershell
# Set Cursor mode
$env:TAPPS_AGENTS_MODE="cursor"

# Run with --cursor-mode flag
python -m tapps_agents.cli create "Create a simple html page that says Hello world" --cursor-mode
```

**What this does**:
- ✅ Uses Cursor's LLM instead of MAL
- ✅ Uses Cursor Skills for agent execution
- ✅ Saves state files for monitoring
- ✅ Works with Background Agents

### Step 2: Monitor Progress (In Another Terminal)

While the workflow runs, open another terminal and monitor progress:

```powershell
# Monitor the latest workflow
python scripts/monitor_workflow_progress.py --latest

# Or monitor a specific workflow
python scripts/monitor_workflow_progress.py <workflow_id>
```

**What you'll see**:
```
Monitoring workflow state: full-sdlc-20250113-123456.json
Press Ctrl+C to stop monitoring

[12:34:56]
Workflow: full-sdlc-20250113-123456
Status: RUNNING
Progress: 3/10 steps (30.0%)
Current Step: architect/design_system
Artifacts Created: 5
Last Step: planner/create_stories (completed)
------------------------------------------------------------
```

### Step 3: Check State File Directly (Optional)

You can also check the state file directly:

```powershell
# View latest state
cat .tapps-agents/workflow-state/last.json

# View specific workflow state
cat .tapps-agents/workflow-state/<workflow_id>-*.json
```

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Terminal 1: Workflow Execution                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ python -m tapps_agents.cli create "..."            │  │
│  │   → CursorWorkflowExecutor                         │  │
│  │   → Uses Cursor Skills (@analyst, @planner, etc.) │  │
│  │   → Saves state to .tapps-agents/workflow-state/   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          │ State File Updates
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Terminal 2: Progress Monitor                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │ python scripts/monitor_workflow_progress.py        │  │
│  │   → Reads state file every 2 seconds              │  │
│  │   → Reports progress to user                      │  │
│  │   → Shows current step, artifacts, status          │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Communication Flow

1. **Workflow starts** → Creates state file
2. **Each step executes** → Updates state file
3. **Monitor reads state** → Reports to user
4. **User sees progress** → Real-time updates

---

## Key Differences: Headless vs Cursor Mode

| Feature | Headless Mode | Cursor Mode |
|---------|--------------|-------------|
| **LLM** | MAL (separate) | Cursor's LLM ✅ |
| **Execution** | Fully automated | Uses Cursor Skills ✅ |
| **Communication** | Terminal only | State files + Monitor ✅ |
| **Progress** | Limited | Real-time updates ✅ |
| **Context** | Isolated | Cursor context ✅ |

---

## Advanced Usage

### Option 1: Interactive Mode (Future)

When implemented, you can run with interactive mode:

```powershell
python -m tapps_agents.cli create "..." --cursor-mode --interactive
```

This will:
- Execute one step at a time
- Report completion after each step
- Wait for user acknowledgment (optional)
- Proceed to next step

### Option 2: Background Agent Integration

Ensure Background Agents are configured:

```yaml
# .cursor/background-agents.yaml
agents:
  - name: Workflow Executor
    triggers:
      - file: .cursor-skill-command.txt
    actions:
      - execute_skill
```

### Option 3: Custom Monitoring

Create your own monitoring script:

```python
from pathlib import Path
import json

state_file = Path(".tapps-agents/workflow-state/last.json")
with open(state_file) as f:
    data = json.load(f)
    state_file = Path(data["state_file"])
    
with open(state_file) as f:
    state = json.load(f)
    print(f"Progress: {len(state['completed_steps'])}/{total}")
```

---

## Troubleshooting

### Issue: "No workflow state files found"

**Solution**: Make sure you've run a workflow first:
```powershell
python -m tapps_agents.cli create "..." --cursor-mode
```

### Issue: Monitor shows old workflow

**Solution**: Use `--latest` flag or specify workflow ID:
```powershell
python scripts/monitor_workflow_progress.py --latest
```

### Issue: Workflow not using Cursor mode

**Solution**: Explicitly set environment variable:
```powershell
$env:TAPPS_AGENTS_MODE="cursor"
python -m tapps_agents.cli create "..." --cursor-mode
```

### Issue: No progress updates

**Solution**: Check that state files are being created:
```powershell
ls .tapps-agents/workflow-state/
```

---

## Summary

**To use Cursor as LLM with communication:**

1. ✅ Run with `--cursor-mode` flag
2. ✅ Monitor progress with `monitor_workflow_progress.py`
3. ✅ Check state files for detailed information

**Benefits:**
- ✅ Uses Cursor's LLM (not MAL)
- ✅ Real-time progress updates
- ✅ Maintains communication during execution
- ✅ Works with Cursor Skills and Background Agents

---

## Next Steps

1. **Try it now**: Run a workflow with `--cursor-mode` and monitor it
2. **Read the plan**: See `CURSOR_LLM_COMMUNICATION_PLAN.md` for detailed architecture
3. **Provide feedback**: Let us know what works and what needs improvement

