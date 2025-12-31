# Background Agents - Migration Guide

## Overview

This guide provides step-by-step instructions for migrating from the current Background Agents implementation to the simplified approach introduced in Phases 1-3. The migration reduces complexity while maintaining functionality.

**Related Documentation:**
- [Background Agents Evaluation](../docs/BACKGROUND_AGENTS_EVALUATION.md) - Complete evaluation and analysis
- [Use Case Guide](../docs/BACKGROUND_AGENTS_USE_CASE_GUIDE.md) - When to use Background Agents
- [Troubleshooting Guide](../docs/BACKGROUND_AGENTS_TROUBLESHOOTING.md) - Common issues and solutions

---

## Migration Overview

### What Changed

**Phase 1 Improvements:**
- ✅ Task duration detection (auto-route short tasks to direct execution)
- ✅ Unified status command (`tapps-agents status`)
- ✅ Auto-cleanup system for worktrees

**Phase 2 Improvements:**
- ✅ Better API detection with health checks
- ✅ Direct execution fallback (replaces file-based triggers)
- ✅ Configuration validation enhancements

**Phase 3 Improvements:**
- ✅ Unified state management (single file instead of multiple)
- ✅ Temp directory option (reduces git dependency)
- ✅ Enhanced status command with unified state support

### Migration Benefits

- **Reduced Complexity:** 80% of tasks use direct execution automatically
- **Better Reliability:** Direct execution fallback eliminates file-based triggers
- **Simplified Monitoring:** Single status command replaces multiple scripts
- **Automatic Cleanup:** No manual worktree cleanup needed
- **Clearer Errors:** Better API detection and error messages

---

## Pre-Migration Checklist

Before starting migration, complete these steps:

- [ ] **Backup Configuration:** Copy `.cursor/background-agents.yaml`
- [ ] **Review Current Usage:** Identify which tasks use Background Agents
- [ ] **Check Dependencies:** Ensure all Phase 1-3 improvements are installed
- [ ] **Test Environment:** Test migration in development environment first
- [ ] **Document Current State:** Note any custom configurations

---

## Step-by-Step Migration

### Step 1: Assess Current Usage

**Analyze which tasks currently use Background Agents:**

```bash
# Check current Background Agent usage
tapps-agents status --detailed

# Review configuration
cat .cursor/background-agents.yaml

# Check for old worktrees
tapps-agents status --worktrees-only
```

**Identify tasks that could use direct execution:**
- Tasks < 30 seconds → Should use direct execution
- LLM-driven tasks → Should use direct Cursor chat
- Simple operations → Should use direct execution

---

### Step 2: Update Configuration

**Before (Complex - Phase 0):**
```yaml
agents:
  - name: "Quality Analyzer"
    type: "background"
    commands:
      - "python -m tapps_agents.cli reviewer analyze-project"
    watch_paths:
      - "**/.cursor-skill-command.txt"
    worktree: "quality-analysis"
```

**After (Simplified - Phase 1-3):**
```yaml
agents:
  - name: "Quality Analyzer"
    type: "background"
    commands:
      - "python -m tapps_agents.cli reviewer analyze-project"
    # No watch_paths needed (direct execution fallback - Phase 2)
    # No worktree needed for short tasks (task duration detection - Phase 1)
    min_duration_seconds: 30  # Only use for tasks > 30s
```

**Key Changes:**
1. **Remove `watch_paths`:** Direct execution fallback (Phase 2) eliminates need for file-based triggers
2. **Add `min_duration_seconds`:** Task duration detection (Phase 1) routes short tasks automatically
3. **Simplify worktree config:** Temp directories (Phase 3) used when git not needed

---

### Step 3: Update Code to Use Direct Execution

**Before (Always uses Background Agents):**
```python
# Always uses background agents
executor = CursorWorkflowExecutor(auto_execution_enabled=True)
executor.start()
```

**After (Auto-detects and routes appropriately):**
```python
# Auto-detects task duration and routes appropriately
executor = CursorWorkflowExecutor(
    auto_execution_enabled=True,
    use_background_agents_only_for_long_tasks=True,  # Phase 1
    min_task_duration_seconds=30  # Phase 1
)
executor.start()
```

**Benefits:**
- Short tasks automatically use direct execution
- Long tasks automatically use Background Agents
- No manual routing needed

---

### Step 4: Update Monitoring

**Before (Multiple scripts):**
```bash
# Multiple scripts needed
python scripts/monitor_background_agents.py
python scripts/monitor_status.py
python check_background_agents.py
```

**After (Unified command - Phase 1):**
```bash
# Single unified command
tapps-agents status

# Detailed status
tapps-agents status --detailed

# Worktrees only
tapps-agents status --worktrees-only

# JSON format for automation
tapps-agents status --format json
```

**Benefits:**
- Single command for all status information
- Shows unified state (Phase 3)
- Supports both legacy and new state files

---

### Step 5: Clean Up Old Worktrees

**Before (Manual cleanup):**
```bash
# Manual cleanup required
git worktree list
git worktree remove <path>
```

**After (Automatic cleanup - Phase 1):**
```bash
# Auto-cleanup system handles old worktrees
# Check status
tapps-agents status --worktrees-only

# Old worktrees are automatically cleaned up
# Manual cleanup only if needed
```

**Configuration:**
```yaml
# .tapps-agents/config.yaml
workflow:
  worktree_retention_days: 7  # Auto-cleanup after 7 days
  auto_cleanup_enabled: true
```

---

### Step 6: Update State Management

**Before (Multiple files - Phase 0):**
```
.tapps-agents/
├── reports/
│   ├── progress-{task_id}.json
│   └── result-{task_id}.json
└── workflow-state/
    └── {workflow_id}.json
```

**After (Unified state - Phase 3):**
```
.tapps-agents/
├── state/
│   └── {task_id}.json  # Unified state (progress + results + workflow)
└── reports/  # Legacy files (still supported)
    └── ...
```

**Migration:**
- New tasks automatically use unified state
- Legacy files still supported for backward compatibility
- Status command shows both legacy and unified state

---

### Step 7: Update Error Handling

**Before (Unclear errors):**
```python
# API unavailable - unclear error
api = BackgroundAgentAPI()
api.trigger_task(...)  # Fails silently or with unclear error
```

**After (Better error handling - Phase 2):**
```python
# Health check before use
api = BackgroundAgentAPI()
health = api.health_check()

if health["available"]:
    # Use Background Agents
    api.trigger_task(...)
else:
    # Clear error message
    print(f"API unavailable: {health['message']}")
    # Direct execution fallback automatically used
```

**Benefits:**
- Clear error messages
- Health check before use
- Automatic fallback to direct execution

---

## Configuration Migration Examples

### Example 1: Quality Analyzer

**Before:**
```yaml
agents:
  - name: "Quality Analyzer"
    type: "background"
    commands:
      - "python -m tapps_agents.cli reviewer analyze-project"
    watch_paths:
      - "**/.cursor-skill-command.txt"
    worktree: "quality-analysis"
```

**After:**
```yaml
agents:
  - name: "Quality Analyzer"
    type: "background"
    commands:
      - "python -m tapps_agents.cli reviewer analyze-project"
    # watch_paths removed (direct execution fallback)
    # worktree removed (auto-detected when needed)
    min_duration_seconds: 30
```

---

### Example 2: Security Scanner

**Before:**
```yaml
agents:
  - name: "Security Scanner"
    type: "background"
    commands:
      - "python -m tapps_agents.cli ops security-scan --target {target}"
    watch_paths:
      - "**/.cursor-skill-command.txt"
    worktree: "security-scan"
```

**After:**
```yaml
agents:
  - name: "Security Scanner"
    type: "background"
    commands:
      - "python -m tapps_agents.cli ops security-scan --target {target}"
    min_duration_seconds: 30
    # Temp directory used when git not needed (Phase 3)
```

---

### Example 3: Test Runner

**Before:**
```yaml
agents:
  - name: "Test Runner"
    type: "background"
    commands:
      - "python -m tapps_agents.cli tester run-tests"
    watch_paths:
      - "**/.cursor-skill-command.txt"
    worktree: "test-runner"
```

**After:**
```yaml
agents:
  - name: "Test Runner"
    type: "background"
    commands:
      - "python -m tapps_agents.cli tester run-tests"
    min_duration_seconds: 30
    # Unified state management (Phase 3)
```

---

## Testing Migration

### Test 1: Task Duration Detection

**Verify short tasks use direct execution:**
```bash
# Should use direct execution (< 30s)
tapps-agents reviewer review src/app.py

# Should use Background Agents (> 30s)
tapps-agents reviewer review src/ --pattern "**/*.py"
```

### Test 2: Direct Execution Fallback

**Verify fallback when API unavailable:**
```python
from tapps_agents.workflow.background_agent_api import BackgroundAgentAPI

api = BackgroundAgentAPI()
health = api.health_check()

if not health["available"]:
    # Should automatically use direct execution fallback
    print("Using direct execution fallback")
```

### Test 3: Unified Status Command

**Verify status command works:**
```bash
# Should show unified state
tapps-agents status

# Should show both legacy and unified state
tapps-agents status --detailed
```

### Test 4: Auto-Cleanup

**Verify auto-cleanup works:**
```bash
# Create old worktree
# Wait for retention period
# Verify auto-cleanup
tapps-agents status --worktrees-only
```

---

## Rollback Plan

If migration causes issues, you can rollback:

### Step 1: Restore Configuration

```bash
# Restore backup
cp .cursor/background-agents.yaml.backup .cursor/background-agents.yaml
```

### Step 2: Revert Code Changes

```bash
# Revert to previous version
git checkout <previous-commit>
```

### Step 3: Clean Up

```bash
# Remove new state files if needed
rm -rf .tapps-agents/state/
```

---

## Post-Migration Checklist

After migration, verify:

- [ ] **Task Duration Detection:** Short tasks use direct execution
- [ ] **Direct Execution Fallback:** Works when API unavailable
- [ ] **Unified Status Command:** Shows correct status
- [ ] **Auto-Cleanup:** Old worktrees cleaned up automatically
- [ ] **Unified State:** New tasks use unified state
- [ ] **Error Handling:** Clear error messages
- [ ] **Configuration Validation:** Warnings about deprecated options

---

## Common Migration Issues

### Issue 1: watch_paths Still Required

**Problem:** Tasks fail because watch_paths not configured

**Solution:** Remove watch_paths - direct execution fallback (Phase 2) handles this automatically

### Issue 2: Old Worktrees Not Cleaned Up

**Problem:** Old worktrees accumulate

**Solution:** Enable auto-cleanup in config:
```yaml
workflow:
  auto_cleanup_enabled: true
  worktree_retention_days: 7
```

### Issue 3: Status Command Shows Legacy Files

**Problem:** Status command shows both legacy and unified state

**Solution:** This is expected - both are supported for backward compatibility. New tasks use unified state.

---

## Summary

**Migration Steps:**
1. ✅ Assess current usage
2. ✅ Update configuration (remove watch_paths, add min_duration_seconds)
3. ✅ Update code (use auto-detection)
4. ✅ Update monitoring (use unified status command)
5. ✅ Clean up old worktrees (auto-cleanup enabled)
6. ✅ Update state management (unified state)
7. ✅ Update error handling (health checks)

**Benefits:**
- Reduced complexity (80% tasks use direct execution)
- Better reliability (direct execution fallback)
- Simplified monitoring (unified status command)
- Automatic cleanup (no manual work)

**Related Documentation:**
- [Background Agents Evaluation](../docs/BACKGROUND_AGENTS_EVALUATION.md)
- [Use Case Guide](../docs/BACKGROUND_AGENTS_USE_CASE_GUIDE.md)
- [Troubleshooting Guide](../docs/BACKGROUND_AGENTS_TROUBLESHOOTING.md)

