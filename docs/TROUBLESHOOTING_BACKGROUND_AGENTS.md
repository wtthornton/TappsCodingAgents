# Troubleshooting Background Agents

## Quick Diagnosis

Your Background Agents configuration is correct. Here's how to verify they're working:

### Current Status
- ✅ Configuration file exists: `.cursor/background-agents.yaml`
- ✅ 4 agents configured and enabled
- ✅ Cursor mode detected
- ⚠️ No active agent activity

## Common Issues and Solutions

### Issue 1: Background Agents Not Visible in Cursor UI

**Symptoms:**
- Can't see Background Agents in Cursor's UI
- Agents don't appear in Background Agents panel

**Solutions:**

1. **Restart Cursor IDE**
   - Cursor only detects `.cursor/background-agents.yaml` on startup
   - Close and reopen Cursor completely
   - After restart, agents should appear in the Background Agents panel

2. **Check Cursor Version**
   - Background Agents require Cursor 2.0+ with Background Agents feature enabled
   - Check Cursor settings to ensure Background Agents are enabled

3. **Verify File Location**
   - File must be at `.cursor/background-agents.yaml` (relative to workspace root)
   - Check the exact path: `C:\cursor\TappsCodingAgents\.cursor\background-agents.yaml`

### Issue 2: Agents Not Responding to Triggers

**Symptoms:**
- Agents visible but don't execute when you use trigger phrases
- No response in chat when using trigger phrases

**Solutions:**

1. **Use Exact Trigger Phrases**
   Your configured triggers are:
   - **Quality Analyzer**: "Analyze project quality", "Generate quality report", "Run lint and type check", "Check code quality"
   - **Test Runner**: "Run tests", "Run the test suite", "Check tests"
   - **Security Auditor**: "Run security scan", "Audit dependencies", "Security analysis"
   - **PR Mode**: "Open a PR with these changes", "Create a PR for this refactor", "Prepare a PR and run checks", "Make changes and open a PR"

   **Try this in Cursor chat:**
   ```
   Analyze project quality
   ```

2. **Check Agent Status**
   - Look for Background Agents panel in Cursor sidebar
   - Verify agents show as "available" or "ready"

3. **Check for Errors**
   - Look at Cursor's Background Agents logs
   - Check terminal output for error messages

### Issue 3: Auto-Execution Not Working (for Workflows)

**Symptoms:**
- Workflows create command files but agents don't execute them
- Agents don't watch for `.cursor-skill-command.txt` files

**Solution:**

Your current configuration uses **triggers only** (natural language). For auto-execution from workflows, you need `watch_paths`. Add this to your configuration:

```yaml
agents:
  - name: "TappsCodingAgents Workflow Executor"
    type: "background"
    description: "Automatically execute workflow commands from .cursor-skill-command.txt files"
    commands:
      - "python -m tapps_agents.cli cursor-invoke \"{command}\""
    watch_paths:
      - "**/.cursor-skill-command.txt"
      - ".tapps-agents/workflow-state/**/.cursor-skill-command.txt"
    enabled: true
    timeout_seconds: 3600
```

### Issue 4: Commands Fail to Execute

**Symptoms:**
- Agents trigger but commands fail
- Error messages in logs

**Solutions:**

1. **Check Python Path**
   - Ensure `python -m tapps_agents.cli` works in terminal
   - Test: `python -m tapps_agents.cli reviewer --help`

2. **Check Working Directory**
   - Agents use `${PROJECT_ROOT}` environment variable
   - Verify this resolves to your project root

3. **Check Dependencies**
   - Ensure all tapps-agents dependencies are installed
   - Run: `pip install -e .` or `pip install tapps-agents`

### Issue 5: Git Worktree Issues

**Symptoms:**
- Errors about worktrees
- Conflicts with existing branches

**Solutions:**

1. **Clean Up Worktrees**
   ```bash
   git worktree list
   git worktree remove .tapps-agents/worktrees/{agent-id}
   ```

2. **Check Git Repository**
   - Ensure you're in a git repository
   - Background Agents require git for worktree isolation

## Verification Steps

### Step 1: Verify Configuration
```bash
python check_background_agents.py
```

Expected output:
- [OK] Configuration file exists
- [OK] Found 4 configured agents
- All agents show ENABLED

### Step 2: Test Agent Trigger
In Cursor chat, try:
```
Analyze project quality
```

Expected behavior:
- Background Agent should trigger
- Should see execution indicators in terminal
- Should create reports in `.tapps-agents/reports/`

### Step 3: Check Background Agents Panel
1. Look for "Background Agents" in Cursor sidebar
2. Should see your 4 configured agents listed
3. Each agent should show status (available/ready)

### Step 4: Monitor Execution
Watch for these indicators:
```
============================================================
[BACKGROUND AGENT TASK] Starting
Agent ID: quality-analyzer
Task ID: quality-analysis-2025-01-XX
Command: reviewer analyze-project
============================================================
```

## Manual Test

To manually test if agents work, try:

1. **Open Cursor chat**
2. **Use exact trigger phrase**: "Analyze project quality"
3. **Check for execution**: Should see terminal output and progress
4. **Check results**: Look in `.tapps-agents/reports/` for output files

## Getting Help

If agents still don't work after trying these solutions:

1. **Check Cursor Logs**
   - Cursor menu → Help → Toggle Developer Tools
   - Look for errors related to Background Agents

2. **Verify Cursor Version**
   - Background Agents feature may not be available in your Cursor version
   - Check Cursor release notes for Background Agents support

3. **Check Configuration Syntax**
   ```bash
   python -m tapps_agents.cli background-agent-config validate
   ```

4. **Report Issues**
   - Include output from `check_background_agents.py`
   - Include Cursor version
   - Include any error messages from logs

## Expected Behavior Summary

When Background Agents are working correctly:

1. **Agents Visible**: All 4 agents appear in Cursor's Background Agents panel
2. **Triggers Work**: Using trigger phrases in chat executes agents
3. **Execution Visible**: Terminal shows execution indicators
4. **Results Created**: Reports appear in `.tapps-agents/reports/`
5. **Worktrees Created**: Worktrees appear in `.tapps-agents/worktrees/` during execution

If any of these don't happen, use the troubleshooting steps above.

