# Background Agents - Troubleshooting Guide

## Overview

This guide provides solutions to common issues when using Background Agents in TappsCodingAgents. It includes diagnostic commands, error explanations, and step-by-step solutions.

**Related Documentation:**
- [Background Agents Evaluation](../docs/BACKGROUND_AGENTS_EVALUATION.md) - Complete evaluation and analysis
- [Use Case Guide](../docs/BACKGROUND_AGENTS_USE_CASE_GUIDE.md) - When to use Background Agents
- [Migration Guide](../docs/BACKGROUND_AGENTS_MIGRATION_GUIDE.md) - Step-by-step migration instructions

---

## Quick Diagnostic Commands

### Check Status
```bash
# Overall status
tapps-agents status

# Detailed status
tapps-agents status --detailed

# Worktrees only
tapps-agents status --worktrees-only

# JSON format for automation
tapps-agents status --format json
```

### Check API Health
```python
from tapps_agents.workflow.background_agent_api import BackgroundAgentAPI

api = BackgroundAgentAPI()
health = api.health_check()
print(health)
```

### Check Configuration
```bash
# Validate configuration
python -m tapps_agents.cli cursor verify

# Check configuration file
cat .cursor/background-agents.yaml
```

---

## Common Issues

### Issue 1: Background Agent Not Triggering

**Symptoms:**
- Task doesn't start
- No progress files created
- No worktree created

**Diagnosis:**
```bash
# Check API health
python -c "from tapps_agents.workflow.background_agent_api import BackgroundAgentAPI; api = BackgroundAgentAPI(); print(api.health_check())"

# Check configuration
tapps-agents cursor verify

# Check status
tapps-agents status
```

**Solutions:**

1. **Check API Availability (Phase 2):**
   ```python
   from tapps_agents.workflow.background_agent_api import BackgroundAgentAPI
   
   api = BackgroundAgentAPI()
   health = api.health_check()
   
   if not health["available"]:
       # API unavailable - use direct execution fallback
       print(f"API unavailable: {health['message']}")
       # Direct execution fallback automatically used
   ```

2. **Check Configuration:**
   ```bash
   # Verify configuration exists
   ls -la .cursor/background-agents.yaml
   
   # Validate configuration
   python -m tapps_agents.cli cursor verify
   ```

3. **Check Cursor Version:**
   - Ensure Background Agents support is enabled
   - Update Cursor to latest version
   - Check Cursor settings for Background Agents

4. **Use Direct Execution Fallback (Phase 2):**
   - Direct execution fallback automatically used when API unavailable
   - No configuration needed
   - Works transparently

---

### Issue 2: API Unavailable Error

**Symptoms:**
- Error: "API unavailable" or "Connection refused"
- Tasks fail to start
- Health check returns unavailable

**Diagnosis:**
```python
from tapps_agents.workflow.background_agent_api import BackgroundAgentAPI

api = BackgroundAgentAPI()
health = api.health_check()

print(f"Available: {health['available']}")
print(f"Status: {health['status']}")
print(f"Message: {health['message']}")
if 'details' in health:
    print(f"Details: {health['details']}")
```

**Solutions:**

1. **Check Cursor Background Agents:**
   - Ensure Cursor Background Agents are enabled
   - Check Cursor settings
   - Restart Cursor if needed

2. **Use Direct Execution Fallback (Phase 2):**
   ```python
   # Direct execution fallback automatically used
   # No action needed - system handles fallback
   ```

3. **Check Network/Firewall:**
   - Ensure no firewall blocking localhost connections
   - Check if Cursor API endpoint is accessible

4. **Clear Error Messages (Phase 2):**
   - Health check provides clear error messages
   - Check `health['message']` for specific issue

---

### Issue 3: Worktree Conflicts

**Symptoms:**
- Error: "Worktree already exists"
- Git conflicts
- Multiple worktrees for same agent

**Diagnosis:**
```bash
# Check worktrees
tapps-agents status --worktrees-only

# List git worktrees
git worktree list
```

**Solutions:**

1. **Auto-Cleanup (Phase 1):**
   ```bash
   # Old worktrees automatically cleaned up
   # Check status
   tapps-agents status --worktrees-only
   ```

2. **Manual Cleanup:**
   ```bash
   # Remove specific worktree
   git worktree remove <path> --force
   
   # Remove all old worktrees
   tapps-agents status --worktrees-only
   # Then manually remove if needed
   ```

3. **Configuration:**
   ```yaml
   # .tapps-agents/config.yaml
   workflow:
     auto_cleanup_enabled: true
     worktree_retention_days: 7
   ```

4. **Use Temp Directories (Phase 3):**
   - Temp directories used when git not needed
   - Reduces worktree conflicts
   - Automatic detection

---

### Issue 4: Progress Not Updating

**Symptoms:**
- Progress files not created
- Status shows "unknown"
- No progress updates

**Diagnosis:**
```bash
# Check unified state
tapps-agents status --detailed

# Check legacy progress files
ls -la .tapps-agents/reports/progress-*.json

# Check unified state files
ls -la .tapps-agents/state/*.json
```

**Solutions:**

1. **Check Permissions:**
   ```bash
   # Ensure write permissions
   chmod -R u+w .tapps-agents/
   
   # Check directory exists
   mkdir -p .tapps-agents/state
   mkdir -p .tapps-agents/reports
   ```

2. **Use Unified State (Phase 3):**
   - New tasks use unified state automatically
   - Single file instead of multiple
   - Better synchronization

3. **Check Status Command:**
   ```bash
   # Unified status shows both legacy and unified state
   tapps-agents status --detailed
   ```

4. **Check Logs:**
   - Review Cursor's Background Agents logs
   - Check for errors in progress reporting

---

### Issue 5: Task Duration Detection Not Working

**Symptoms:**
- Short tasks still use Background Agents
- Long tasks use direct execution
- Incorrect routing

**Diagnosis:**
```bash
# Check configuration
cat .tapps-agents/config.yaml | grep duration_threshold

# Check task duration estimation
python -c "from tapps_agents.core.task_duration import TaskDurationEstimator; est = TaskDurationEstimator(); print(est.estimate_duration('reviewer', 'review', ['src/app.py']))"
```

**Solutions:**

1. **Check Configuration:**
   ```yaml
   # .tapps-agents/config.yaml
   workflow:
     duration_threshold_seconds: 30.0  # Default: 30 seconds
   ```

2. **Verify Task Duration Estimation:**
   - Task duration detection (Phase 1) estimates based on:
     - Command type
     - File count/size
     - Historical execution times

3. **Manual Override:**
   ```python
   from tapps_agents.core.fallback_strategy import FallbackStrategy
   
   strategy = FallbackStrategy(force_background=True)  # Force Background Agents
   # or
   strategy = FallbackStrategy()  # Auto-detect
   ```

---

### Issue 6: Direct Execution Fallback Not Working

**Symptoms:**
- Tasks fail when API unavailable
- No fallback to direct execution
- Error messages unclear

**Diagnosis:**
```python
from tapps_agents.workflow.background_agent_api import BackgroundAgentAPI

api = BackgroundAgentAPI()
health = api.health_check()

if not health["available"]:
    # Should automatically use direct execution fallback
    print("Direct execution fallback should be used")
```

**Solutions:**

1. **Check Phase 2 Implementation:**
   - Direct execution fallback (Phase 2) automatically used
   - No configuration needed
   - Works transparently

2. **Verify Fallback Logic:**
   ```python
   from tapps_agents.workflow.skill_invoker import SkillInvoker
   
   invoker = SkillInvoker(use_api=True)
   # Automatically falls back to direct execution if API unavailable
   ```

3. **Check Error Messages:**
   - Phase 2 provides clear error messages
   - Health check shows specific issues

---

### Issue 7: Configuration Validation Errors

**Symptoms:**
- Configuration validation fails
- Warnings about missing fields
- YAML syntax errors

**Diagnosis:**
```bash
# Validate configuration
python -m tapps_agents.cli cursor verify

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('.cursor/background-agents.yaml'))"
```

**Solutions:**

1. **Check YAML Syntax:**
   ```bash
   # Validate YAML
   python -c "import yaml; yaml.safe_load(open('.cursor/background-agents.yaml'))"
   ```

2. **Check Required Fields:**
   - Phase 2 configuration validation provides clear errors
   - Check validation output for specific issues

3. **Update Configuration (Phase 2):**
   ```yaml
   # Remove deprecated watch_paths (Phase 2)
   agents:
     - name: "Quality Analyzer"
       type: "background"
       commands:
         - "python -m tapps_agents.cli reviewer analyze-project"
       # watch_paths no longer needed (direct execution fallback)
   ```

---

### Issue 8: State Synchronization Issues

**Symptoms:**
- Multiple state files out of sync
- Progress and results don't match
- State files missing

**Diagnosis:**
```bash
# Check unified state
tapps-agents status --detailed

# Check legacy files
ls -la .tapps-agents/reports/
ls -la .tapps-agents/workflow-state/
```

**Solutions:**

1. **Use Unified State (Phase 3):**
   - New tasks use unified state automatically
   - Single file instead of multiple
   - Better synchronization

2. **Check Status Command:**
   ```bash
   # Unified status shows both legacy and unified state
   tapps-agents status --detailed
   ```

3. **Migrate Legacy State:**
   - Legacy files still supported
   - New tasks use unified state
   - Gradual migration

---

### Issue 9: Temp Directory Issues

**Symptoms:**
- Temp directories not created
- Git dependency still required
- Isolation not working

**Diagnosis:**
```python
from tapps_agents.core.temp_directory import TempDirectoryManager

manager = TempDirectoryManager()
temp_dir = manager.create_temp_directory("test-task")
print(f"Temp directory: {temp_dir}")
```

**Solutions:**

1. **Check Temp Directory Manager (Phase 3):**
   - Temp directories used when git not needed
   - Automatic detection
   - No configuration needed

2. **Verify Git Detection:**
   ```python
   from tapps_agents.core.temp_directory import needs_git_operations
   
   # Check if git operations needed
   needs_git = needs_git_operations(task_description)
   if not needs_git:
       # Use temp directory
   ```

3. **Check Permissions:**
   ```bash
   # Ensure temp directory permissions
   ls -la /tmp/tapps-agent-*
   ```

---

### Issue 10: Monitoring Scripts Not Working

**Symptoms:**
- Old monitoring scripts fail
- Status command not working
- Multiple scripts needed

**Solutions:**

1. **Use Unified Status Command (Phase 1):**
   ```bash
   # Single unified command
   tapps-agents status
   tapps-agents status --detailed
   tapps-agents status --worktrees-only
   ```

2. **Replace Old Scripts:**
   - `monitor_background_agents.py` → `tapps-agents status`
   - `monitor_status.py` → `tapps-agents status --detailed`
   - `check_background_agents.py` → `tapps-agents status --worktrees-only`

3. **Check Status Command:**
   ```bash
   # Verify status command works
   tapps-agents status --format json
   ```

---

## Error Message Reference

### API Unavailable
```
Error: API unavailable - Cursor Background Agents API is not available
Status: unavailable
Message: Cursor Background Agents API endpoint not accessible
```

**Solution:** Use direct execution fallback (Phase 2) - automatically handled

---

### Worktree Already Exists
```
Error: Worktree already exists: agent/{agent_id}
```

**Solution:** Auto-cleanup (Phase 1) or manual cleanup

---

### Configuration Validation Failed
```
Error: Configuration validation failed
Field 'watch_paths' is deprecated (Phase 2 - use direct execution fallback)
```

**Solution:** Remove `watch_paths` from configuration (Phase 2)

---

### Task Duration Detection Failed
```
Warning: Could not estimate task duration, using default threshold
```

**Solution:** Check task duration estimation logic (Phase 1)

---

## Diagnostic Checklist

When troubleshooting, check:

- [ ] **API Health:** `api.health_check()`
- [ ] **Configuration:** `tapps-agents cursor verify`
- [ ] **Status:** `tapps-agents status --detailed`
- [ ] **Worktrees:** `tapps-agents status --worktrees-only`
- [ ] **Permissions:** Check `.tapps-agents/` directory permissions
- [ ] **Logs:** Review Cursor's Background Agents logs
- [ ] **Phase Implementation:** Verify Phases 1-3 are installed

---

## Getting Help

If issues persist:

1. **Check Documentation:**
   - [Background Agents Evaluation](../docs/BACKGROUND_AGENTS_EVALUATION.md)
   - [Use Case Guide](../docs/BACKGROUND_AGENTS_USE_CASE_GUIDE.md)
   - [Migration Guide](../docs/BACKGROUND_AGENTS_MIGRATION_GUIDE.md)

2. **Run Diagnostics:**
   ```bash
   # Full diagnostic
   tapps-agents status --detailed
   tapps-agents cursor verify
   ```

3. **Check Logs:**
   - Cursor Background Agents logs
   - Python error logs
   - System logs

4. **Report Issues:**
   - Include diagnostic output
   - Include configuration (sanitized)
   - Include error messages

---

## Summary

**Common Solutions:**
1. **API Unavailable:** Use direct execution fallback (Phase 2)
2. **Worktree Conflicts:** Auto-cleanup (Phase 1) or manual cleanup
3. **Progress Not Updating:** Use unified state (Phase 3)
4. **Configuration Errors:** Remove deprecated options (Phase 2)
5. **Monitoring Issues:** Use unified status command (Phase 1)

**Related Documentation:**
- [Background Agents Evaluation](../docs/BACKGROUND_AGENTS_EVALUATION.md)
- [Use Case Guide](../docs/BACKGROUND_AGENTS_USE_CASE_GUIDE.md)
- [Migration Guide](../docs/BACKGROUND_AGENTS_MIGRATION_GUIDE.md)

