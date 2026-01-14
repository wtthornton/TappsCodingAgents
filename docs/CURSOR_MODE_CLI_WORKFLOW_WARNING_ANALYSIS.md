# Cursor Mode CLI Workflow Warning - Analysis & Recommendations

**Date:** 2026-01-16  
**Issue:** CLI workflow commands not recommended in Cursor mode

## Why This Happened

### Root Cause

When you run a CLI workflow command (e.g., `python -m tapps_agents.cli workflow fix --file ... --auto`) **in Cursor IDE**, the TappsCodingAgents framework:

1. **Detects Cursor Mode**: The framework automatically detects that you're running in Cursor IDE (via environment variables like `CURSOR_IDE`, `CURSOR_WORKSPACE_ROOT`, etc.)

2. **Prevents CLI Workflow Execution**: CLI workflow commands are **not recommended in Cursor mode** because:
   - They may fail due to dependency issues (Cursor's execution environment differs from standalone CLI)
   - They bypass Cursor's integrated skill orchestration and context management
   - They don't leverage Cursor Skills, which provide better integration and experience

3. **Provides Clear Guidance**: The framework now prevents execution and suggests using `@simple-mode` commands instead

### Why CLI Workflows Don't Work Well in Cursor

- **Different Execution Environment**: Cursor IDE has its own execution context that differs from a standalone terminal
- **Skill Integration**: Cursor Skills (`@simple-mode`, `@reviewer`, etc.) provide native integration with Cursor's chat interface
- **Context Management**: Cursor Skills have better access to workspace context and can coordinate more effectively
- **Dependency Issues**: CLI commands may not have access to all dependencies or may conflict with Cursor's runtime

## Recommendations to Fix TappsCodingAgents

### 1. ✅ Use `@simple-mode` Commands in Cursor (PRIMARY RECOMMENDATION)

**For the specific fix workflow you were trying**, use:

```cursor
@simple-mode *fix services/ai-automation-service-new/src/api/preference_router.py "Fix issue in preference router"
```

**For other common tasks:**

| Your CLI Command | Use This Instead in Cursor |
|-----------------|---------------------------|
| `tapps-agents workflow fix --file <file> --auto` | `@simple-mode *fix <file> "description"` |
| `tapps-agents workflow rapid --prompt "description"` | `@simple-mode *build "description"` |
| `tapps-agents workflow full --prompt "description"` | `@simple-mode *full "description"` |
| `tapps-agents reviewer review <file>` | `@reviewer *review <file>` |
| `tapps-agents tester test <file>` | `@tester *test <file>` |

### 2. ✅ Run `tapps-agents init` to Ensure Proper Setup

**If this happened on another project**, the project may not have been properly initialized:

```bash
# In the project directory
tapps-agents init
```

**What `init` does:**
- ✅ Installs Cursor Rules (`.cursor/rules/`)
- ✅ Installs Cursor Skills (`.claude/skills/`) - **Required for `@simple-mode`**
- ✅ Creates configuration (`.tapps-agents/config.yaml`)
- ✅ Sets up workflow presets
- ✅ Pre-populates Context7 cache (if configured)

**After `init`, verify Simple Mode is ready:**
```bash
tapps-agents simple-mode status
tapps-agents cursor verify
```

### 3. ✅ If You Must Use CLI (Not Recommended)

If you absolutely need CLI workflow execution in Cursor mode (not recommended), use the `--cli-mode` override:

```bash
python -m tapps_agents.cli workflow fix --file <file> --auto --cli-mode
```

**Why this is not recommended:**
- May fail due to dependency issues
- Doesn't leverage Cursor's native capabilities
- Poorer integration with workspace context
- Better to use `@simple-mode` commands instead

### 4. ✅ Use CLI Commands in Terminal/CI (Outside Cursor)

CLI workflow commands are **designed for**:
- ✅ Terminal/command line (outside Cursor IDE)
- ✅ CI/CD pipelines
- ✅ Shell scripts
- ✅ Automated workflows

**In these environments, CLI commands work perfectly:**
```bash
# In a regular terminal (not Cursor)
tapps-agents workflow rapid --prompt "Add feature" --auto
tapps-agents workflow fix --file src/bug.py --auto
```

## Implementation Details

### How Cursor Mode Detection Works

The framework detects Cursor mode via:

1. **Environment Variables** (checked by `detect_runtime_mode()`):
   - `CURSOR_IDE`
   - `CURSOR_SESSION_ID`
   - `CURSOR_WORKSPACE_ROOT`
   - `CURSOR_TRACE_ID`

2. **Explicit Override** (via `TAPPS_AGENTS_MODE`):
   - `TAPPS_AGENTS_MODE=cursor` → Cursor mode
   - `TAPPS_AGENTS_MODE=headless` → CLI mode

3. **Auto-Detection**: If Cursor environment variables are present, Cursor mode is automatically enabled

### Code Location

The prevention logic is in:
- **File**: `tapps_agents/cli/commands/top_level.py`
- **Function**: `handle_workflow_command()`
- **Lines**: ~961-987

**Reference**: `WORKFLOW_EXECUTION_ROOT_CAUSE_FIX_IMPLEMENTED.md`

## Summary

### What Happened
- You ran a CLI workflow command in Cursor IDE
- Framework detected Cursor mode and prevented execution
- Warning message provided guidance

### What to Do

1. **Use `@simple-mode` commands in Cursor** (primary recommendation)
   - `@simple-mode *fix <file> "description"` for bug fixes
   - `@simple-mode *build "description"` for new features
   - `@simple-mode *review <file>` for code reviews

2. **Run `tapps-agents init` on the project** (if not already done)
   - Ensures all Cursor integration components are installed
   - Required for `@simple-mode` to work

3. **Use CLI commands in terminal/CI** (outside Cursor)
   - CLI commands are designed for standalone environments
   - Work perfectly in terminals, CI/CD pipelines, scripts

### Quick Reference

| Environment | Recommended Command Type |
|------------|-------------------------|
| **Cursor IDE Chat** | `@simple-mode *command` |
| **Terminal (outside Cursor)** | `tapps-agents workflow <preset>` |
| **CI/CD Pipeline** | `tapps-agents workflow <preset> --auto` |

## Related Documentation

- `.cursor/rules/simple-mode.mdc` - Simple Mode usage guide
- `.cursor/rules/command-reference.mdc` - Complete command reference
- `WORKFLOW_EXECUTION_ROOT_CAUSE_FIX_IMPLEMENTED.md` - Implementation details
- `docs/TROUBLESHOOTING.md` - Troubleshooting guide
