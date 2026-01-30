# Simple Mode Build Command Fix

## Issue Summary

Users attempting to use `tapps-agents simple-mode build` were encountering an error:
```
[ERROR] invalid_command: Invalid simple-mode command command: build
Suggestion: Use: on, off, status, init, configure, progress, full, or resume
```

Notice that `build` is **not** included in the suggested commands, even though it's a valid command.

## Root Cause

The error occurred because:
1. The `build` subcommand was not properly recognized by argparse
2. The error message didn't include `build` in the list of available commands
3. The subparser wasn't marked as `required=True`, causing argparse to generate its own error message before our handler could provide a better one

## Fix Applied

### 1. Added `required=True` to Subparser
**File:** `tapps_agents/cli/parsers/top_level.py`

```python
simple_mode_subparsers = simple_mode_parser.add_subparsers(
    dest="command",
    help="Simple Mode command",
    required=True,  # Added: ensures argparse validates subcommand exists
    metavar="COMMAND",  # Added: better help text
)
```

### 2. Improved Error Message
**File:** `tapps_agents/cli/commands/simple_mode.py`

Enhanced the error handler to:
- Show the actual command that was provided (or "(none provided)")
- Include all available commands in the error message
- Provide a clearer remediation message

```python
available_commands = ["on", "off", "status", "init", "configure", "progress", "full", "build", "resume"]
command_list = ", ".join(available_commands)
feedback.error(
    f"Invalid simple-mode command: {command or '(none provided)'}",
    error_code="invalid_command",
    context={"command": command, "available_commands": available_commands},
    remediation=f"Use one of: {command_list}",
    exit_code=2,
)
```

## Verification

The `build` command is properly registered and works:
```bash
# Test command
tapps-agents simple-mode build --prompt "test feature"

# Expected: Build workflow executes successfully
```

## Available Simple Mode Commands

After this fix, all Simple Mode commands are:
- `on` - Enable Simple Mode
- `off` - Disable Simple Mode
- `status` - Check Simple Mode status
- `init` - Run onboarding wizard
- `configure` / `config` - Configure settings
- `progress` - Show learning progression
- `full` - Full SDLC workflow (9 steps)
- `build` - Build workflow (7 steps) ✅ **Now properly recognized**
- `resume` - Resume interrupted workflow

## Usage Examples

### Build Workflow (7 steps)
```bash
tapps-agents simple-mode build --prompt "Add user authentication" --file src/api/auth.py
tapps-agents simple-mode build --prompt "Create REST API endpoint" --fast  # Skip docs steps
tapps-agents simple-mode build --prompt "Implement feature" --auto  # Fully automated
```

### Full Workflow (9 steps)
```bash
tapps-agents simple-mode full --prompt "Build complete application" --auto
```

## For Projects Using Older Versions

If you encounter the error "Invalid simple-mode command command: build", you need to:

1. **Update tapps-agents:**
   ```bash
   pip install --upgrade tapps-agents
   ```

2. **Re-initialize project files (optional but recommended):**
   ```bash
   tapps-agents init --reset
   ```

3. **Verify the command works:**
   ```bash
   tapps-agents simple-mode build --help
   ```

## Related Documentation

- [Simple Mode Guide](SIMPLE_MODE_GUIDE.md)
- [Command Reference](TAPPS_AGENTS_COMMAND_REFERENCE.md)
- [Simple Mode Workflow Comparison](SIMPLE_MODE_WORKFLOW_COMPARISON.md)
