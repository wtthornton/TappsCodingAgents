# BUG-002: CLI Command Quotation Parsing Error in Direct Execution Fallback

**Date:** 2026-02-03
**Severity:** Medium
**Component:** Workflow Direct Execution, CLI
**Status:** Open

---

## Summary

The direct execution fallback in workflow orchestration fails to parse CLI commands due to improper quotation handling, causing "No closing quotation" ValueError during command execution.

## Steps to Reproduce

1. Run a build workflow via task system:
```bash
tapps-agents task run enh-001
```

2. Workflow reaches Step 3 (Implementation)
3. Attempts to execute implementer via direct CLI command
4. Error occurs during command parsing:
```
ValueError: No closing quotation
  File "tapps_agents/workflow/direct_execution_fallback.py", line 159, in execute_command
    command_parts = shlex.split(cli_command, posix=not is_windows)
```

## Expected Behavior

- CLI commands should be properly quoted and escaped for shell execution
- `shlex.split()` should successfully parse the command
- Implementer agent should execute successfully

## Actual Behavior

- CLI command has unmatched quotation marks
- `shlex.split()` raises ValueError: "No closing quotation"
- Step is marked as "completed" despite error (incorrect error handling)
- Workflow continues but with incomplete implementation

## Error Details

**File:** `tapps_agents/workflow/direct_execution_fallback.py:159`

**Traceback:**
```python
Traceback (most recent call last):
  File "tapps_agents/cli/base.py", line 299, in run_async_command
    asyncio.get_running_loop()
RuntimeError: no running event loop

During handling of the above exception:
  File "tapps_agents/workflow/direct_execution_fallback.py", line 159, in execute_command
    command_parts = shlex.split(cli_command, posix=not is_windows)
  File "shlex.py", line 313, in split
    return list(lex)
  File "shlex.py", line 191, in read_token
    raise ValueError("No closing quotation")
ValueError: No closing quotation
```

## Root Cause

**Primary Issue:** CLI command string is not properly escaped/quoted before being passed to `shlex.split()`.

**Possible causes:**
1. Multi-line description or prompt contains unescaped quotes
2. File paths with spaces not properly quoted
3. Arguments with special characters not escaped
4. Windows-specific quoting issues (using `posix=not is_windows` may not be sufficient)

**Code Location:**
```python
# tapps_agents/workflow/direct_execution_fallback.py:159
def execute_command(cli_command: str) -> dict:
    try:
        # This line fails when cli_command has unmatched quotes
        command_parts = shlex.split(cli_command, posix=not is_windows)
        # ... rest of execution
```

## Impact

**Severity: Medium**

- ❌ Workflow fails silently (marked as complete despite error)
- ❌ Implementation step produces no code
- ❌ Subsequent steps (review, test) have nothing to work with
- ⚠️ Error is caught but not properly propagated
- ✅ Workaround exists: Use agents directly

## Suggested Fix

### Option 1: Better Quoting Before shlex.split()

```python
import shlex
import sys

def execute_command(cli_command: str) -> dict:
    """Execute CLI command with proper quotation handling."""
    try:
        # Validate command has balanced quotes before parsing
        if not _has_balanced_quotes(cli_command):
            raise ValueError(f"Unbalanced quotes in command: {cli_command[:100]}...")

        # Use platform-specific parsing
        is_windows = sys.platform == "win32"
        command_parts = shlex.split(cli_command, posix=not is_windows)

        # ... rest of execution

    except ValueError as e:
        logger.error(f"Command parsing failed: {e}")
        logger.debug(f"Problematic command: {cli_command}")
        raise  # Don't swallow the error!

def _has_balanced_quotes(s: str) -> bool:
    """Check if string has balanced quotes."""
    single_quotes = s.count("'") - s.count("\\'")
    double_quotes = s.count('"') - s.count('\\"')
    return single_quotes % 2 == 0 and double_quotes % 2 == 0
```

### Option 2: Escape Arguments Properly During Command Construction

```python
def build_cli_command(agent: str, action: str, args: dict) -> str:
    """Build CLI command with proper escaping."""
    parts = ["tapps-agents", agent, action]

    for key, value in args.items():
        if isinstance(value, str):
            # Properly escape quotes in value
            escaped_value = value.replace('"', '\\"')
            parts.append(f'--{key}="{escaped_value}"')
        else:
            parts.append(f'--{key}={value}')

    return " ".join(parts)
```

### Option 3: Use subprocess.run() with List Arguments

```python
def execute_command(agent: str, action: str, args: dict) -> dict:
    """Execute command using subprocess with list args (safer)."""
    import subprocess

    # Build command as list (avoids shell parsing issues)
    cmd = ["tapps-agents", agent, action]

    for key, value in args.items():
        cmd.extend([f"--{key}", str(value)])

    # Execute without shell (safer, no quote parsing needed)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False  # Don't raise on non-zero exit
    )

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }
```

**Recommendation:** Use Option 3 (subprocess with list args) - most robust and avoids shell parsing entirely.

## Secondary Issue: Silent Failure

The workflow marks the step as "completed" despite the error:

```
[OK] Step 'implementation' completed (4.2s)
```

**This is incorrect!** The error should:
1. Mark the step as FAILED
2. Halt the workflow (or trigger retry/loopback)
3. Not proceed to review/test steps

**Fix:** Improve error handling in workflow orchestrator to propagate failures correctly.

## Files to Investigate

1. `tapps_agents/workflow/direct_execution_fallback.py:159` (primary issue)
2. `tapps_agents/cli/base.py:299` (async event loop issue)
3. Workflow orchestrator error handling code
4. Command construction code (where CLI command string is built)

## Testing Verification

After fix, verify:
1. ✅ CLI commands with quotes in descriptions parse correctly
2. ✅ File paths with spaces work properly
3. ✅ Windows and Unix command parsing both work
4. ✅ Errors properly propagate (step marked as FAILED, not OK)
5. ✅ Workflow halts on parsing errors (doesn't continue)

## Related Issues

- Silent failure / error handling issue (should be separate bug report)
- Async event loop issue in CLI base.py

## Workaround

**Current workaround:** Use agents directly instead of via workflow:
```bash
@implementer *implement "description" target_file.py
```

Or use task system with manual agent invocation.

---

**Reported by:** Claude Sonnet 4.5 (Session 2026-02-03)
**Affects:** v3.5.39
**Priority:** P2 (Medium)
