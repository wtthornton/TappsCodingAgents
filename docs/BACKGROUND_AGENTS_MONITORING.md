# Background Agents Monitoring Guide

This guide explains how to monitor Background Agents in TappsCodingAgents.

## Quick Start

### Quick Status Check
```bash
python scripts/monitor_status.py
python scripts/monitor_status.py --detailed
```

### Real-Time Monitoring
```bash
python scripts/monitor_background_agents.py
python scripts/monitor_background_agents.py --interval 2
python scripts/monitor_background_agents.py --task-id <task-id>
```

### Full Status Check
```bash
python check_background_agents.py
```

## Monitoring Tools

### 1. Quick Status Monitor (`monitor_status.py`)

**Purpose:** Snapshot view of current background agent activity

**Usage:**
```bash
# Basic status
python scripts/monitor_status.py

# Detailed status with recent results
python scripts/monitor_status.py --detailed
```

**What it shows:**
- Runtime mode (Cursor Mode active/inactive)
- Active tasks (currently running)
- Active worktrees (evidence of agent activity)
- Recent results (if `--detailed` flag used)

**When to use:**
- Quick status check before starting work
- Verify agents are active
- Check if tasks completed

### 2. Real-Time Monitor (`monitor_background_agents.py`)

**Purpose:** Continuous real-time monitoring of background agent execution

**Usage:**
```bash
# Monitor all tasks (default)
python scripts/monitor_background_agents.py

# Custom polling interval (default: 2 seconds)
python scripts/monitor_background_agents.py --interval 3

# Monitor specific task
python scripts/monitor_background_agents.py --task-id <task-id>
```

**What it monitors:**
- Progress files (`.tapps-agents/reports/progress-*.json`)
- Result files (`.tapps-agents/reports/*.json`)
- Worktrees (`.tapps-agents/worktrees/`)
- Status changes (in_progress → completed/failed)

**Features:**
- Real-time updates when status changes
- Detects new tasks automatically
- Shows elapsed time and current step
- Heartbeat indicator when no activity
- Final summary on exit (Ctrl+C)

**When to use:**
- Monitoring long-running tasks
- Debugging agent execution issues
- Tracking workflow progress
- Watching for completion

### 3. Full Status Check (`check_background_agents.py`)

**Purpose:** Comprehensive configuration and status verification

**Usage:**
```bash
python check_background_agents.py
```

**What it checks:**
1. Runtime mode detection (Cursor Mode)
2. Background agents configuration (`.cursor/background-agents.yaml`)
3. Active worktrees (evidence of agent activity)
4. Workflow state files
5. Background Agent API availability

**When to use:**
- After setup/configuration changes
- Troubleshooting agent issues
- Verifying configuration
- CI/CD validation

## Understanding Monitor Output

### Status Indicators

- `[RUNNING]` - Task is in progress
- `[COMPLETE]` - Task completed successfully
- `[FAILED]` - Task failed
- `[OK]` - Success indicator
- `[FAIL]` - Failure indicator
- `[WORKTREE]` - Active worktree detected

### Progress File Structure

Progress files contain:
```json
{
  "task_id": "workflow-quality-20251229-015809",
  "status": "in_progress",
  "elapsed_seconds": 45.2,
  "steps": [
    {
      "step": "initial_review",
      "status": "completed",
      "message": "Review completed"
    }
  ]
}
```

### Result File Structure

Result files contain:
```json
{
  "success": true,
  "task_id": "workflow-quality-20251229-015809",
  "results": { ... }
}
```

## Monitoring Locations

### Directories to Watch

1. **Progress Files:** `.tapps-agents/reports/progress-*.json`
   - Real-time task progress
   - Status updates
   - Step-by-step execution

2. **Result Files:** `.tapps-agents/reports/*.json`
   - Completed task results
   - Success/failure status
   - Execution artifacts

3. **Worktrees:** `.tapps-agents/worktrees/`
   - Active agent worktrees
   - Command files (`.cursor-skill-command.txt`)
   - Progress indicators

4. **Workflow State:** `.tapps-agents/workflow-state/*.json`
   - Workflow execution state
   - Resume capability
   - State persistence

## Background Agents Configuration

Background agents are configured in `.cursor/background-agents.yaml`:

### Available Agents

1. **TappsCodingAgents Quality Analyzer**
   - Triggers: "Analyze project quality", "Generate quality report"
   - Commands: Quality analysis, lint, type-check, duplication detection

2. **TappsCodingAgents Test Runner**
   - Triggers: "Run tests", "Run the test suite"
   - Commands: Execute test suite

3. **TappsCodingAgents Security Auditor**
   - Triggers: "Run security scan", "Audit dependencies"
   - Commands: Security scanning, dependency auditing

4. **TappsCodingAgents Cursor Integration Verifier**
   - Triggers: "Verify Cursor setup", "Check Cursor integration"
   - Commands: Verify Cursor Skills, Rules, Background Agents

5. **TappsCodingAgents PR Mode (Verify + PR)**
   - Triggers: "Open a PR with these changes", "Create a PR"
   - Commands: Full verification + PR creation

## Troubleshooting

### No Activity Detected

1. **Check Cursor Mode:**
   ```bash
   python check_background_agents.py
   ```
   Ensure "Cursor Mode: ACTIVE"

2. **Verify Configuration:**
   ```bash
   # Check if config file exists
   cat .cursor/background-agents.yaml
   ```

3. **Check Worktrees:**
   ```bash
   ls -la .tapps-agents/worktrees/
   ```

### Tasks Stuck in "in_progress"

1. **Check for errors:**
   ```bash
   # Look for error messages in progress files
   python scripts/monitor_status.py --detailed
   ```

2. **Check worktree:**
   ```bash
   # Inspect worktree for command files
   ls -la .tapps-agents/worktrees/<worktree-name>/
   ```

3. **Restart monitoring:**
   ```bash
   # Stop and restart monitor
   python scripts/monitor_background_agents.py
   ```

### Monitor Not Showing Updates

1. **Check polling interval:**
   ```bash
   # Use shorter interval for faster updates
   python scripts/monitor_background_agents.py --interval 1
   ```

2. **Verify directories exist:**
   ```bash
   ls -la .tapps-agents/reports/
   ls -la .tapps-agents/worktrees/
   ```

3. **Check file permissions:**
   ```bash
   # Ensure monitor can read files
   ls -la .tapps-agents/reports/progress-*.json
   ```

## Best Practices

1. **Use Quick Status for Regular Checks:**
   ```bash
   python scripts/monitor_status.py
   ```

2. **Use Real-Time Monitor for Active Tasks:**
   ```bash
   python scripts/monitor_background_agents.py
   ```

3. **Use Full Check After Configuration Changes:**
   ```bash
   python check_background_agents.py
   ```

4. **Monitor Specific Tasks:**
   ```bash
   python scripts/monitor_background_agents.py --task-id <task-id>
   ```

5. **Check Detailed Status:**
   ```bash
   python scripts/monitor_status.py --detailed
   ```

## Integration with Workflows

Background agents are automatically triggered by:
- Natural language prompts in Cursor chat
- Workflow presets (via `tapps-agents workflow`)
- Simple Mode commands (via `@simple-mode`)

Monitor agents during workflow execution:
```bash
# In one terminal: Run workflow
tapps-agents workflow full --prompt "Build feature"

# In another terminal: Monitor progress
python scripts/monitor_background_agents.py
```

## Related Documentation

- **Background Agents Guide:** `docs/BACKGROUND_AGENTS_GUIDE.md`
- **Cursor Integration:** `docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md`
- **Workflow Presets:** `.cursor/rules/workflow-presets.mdc`
- **Configuration:** `.cursor/background-agents.yaml`

