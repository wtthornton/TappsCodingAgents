# Simple Mode Troubleshooting Guide

**Date**: 2025-01-16  
**Status**: Updated for Phase 2 Features

---

## Common Issues

### 1. Command Validation Errors

#### Issue: `--prompt argument is required`

**Error Message**:
```
Validation Error
============================================================

Errors:
  • --prompt argument is required

Suggestions:
  • Provide --prompt with feature description

Examples:
  $ tapps-agents simple-mode build --prompt "Add user authentication"
```

**Solution**: Always provide `--prompt` argument:

```bash
# ✅ Correct
tapps-agents simple-mode build --prompt "Add user authentication"

# ❌ Incorrect
tapps-agents simple-mode build
```

#### Issue: `--prompt cannot be empty`

**Error Message**:
```
Errors:
  • --prompt cannot be empty
```

**Solution**: Provide a non-empty description:

```bash
# ✅ Correct
tapps-agents simple-mode build --prompt "Add login endpoint"

# ❌ Incorrect
tapps-agents simple-mode build --prompt ""
```

#### Issue: `--file must be a string`

**Error Message**:
```
Errors:
  • --file must be a string, got NoneType
```

**Solution**: Provide file path as string or omit:

```bash
# ✅ Correct
tapps-agents simple-mode build --prompt "..." --file src/api/auth.py

# ✅ Also correct (omit --file)
tapps-agents simple-mode build --prompt "..."

# ❌ Incorrect
tapps-agents simple-mode build --prompt "..." --file None
```

---

### 2. Status Reporter Issues

#### Issue: No progress indicators during execution

**Symptoms**: Workflow runs but no `[X/Y] Step name...` output.

**Possible Causes**:
1. Callbacks not passed to orchestrator
2. StatusReporter not initialized
3. Output redirected/suppressed

**Solution**: Ensure StatusReporter callbacks are integrated:

```python
# ✅ Correct - Callbacks passed
from tapps_agents.cli.utils.status_reporter import StatusReporter

reporter = StatusReporter(total_steps=7)

def on_step_start(step_num: int, step_name: str):
    reporter.start_step(step_num, step_name)

orchestrator.execute(..., on_step_start=on_step_start)
```

**Check**: Verify `simple_mode.py` has StatusReporter integration (should be automatic).

#### Issue: Step numbers incorrect in output

**Symptoms**: Steps show wrong numbers (e.g., `[5/7]` for step 1).

**Cause**: Fast mode changes step numbering.

**Solution**: This is expected in fast mode. Steps 1-4 are skipped, so step 5 (implementation) becomes step 1.

**Note**: In fast mode, only 4 steps execute (steps 5-7 from complete mode).

---

### 3. Error Recovery Issues

#### Issue: Errors cause immediate failure without recovery

**Symptoms**: Workflow fails immediately on error, no retry/skip options.

**Possible Causes**:
1. ErrorRecoveryHandler not integrated
2. Error type not recognized
3. Critical step failure (cannot recover)

**Solution**: Ensure ErrorRecoveryHandler is integrated:

```python
from tapps_agents.cli.utils.error_recovery import ErrorRecoveryHandler

handler = ErrorRecoveryHandler(interactive=False)

def on_step_error(step_num: int, step_name: str, error: Exception):
    action = handler.handle_step_error(
        step_num=step_num,
        step_name=step_name,
        error=error,
        retry_callback=lambda: retry_step(step_num),
    )
```

**Note**: Critical steps (implementation, planning) will fail immediately. Only non-critical steps (review, test, document) can be skipped.

#### Issue: Recovery strategy not working as expected

**Symptoms**: Wrong recovery action taken (e.g., retry when should skip).

**Cause**: Error type detection may be incorrect.

**Solution**: Check error type and adjust strategy:

```python
# Check error type
error_type = type(error).__name__
error_str = str(error).lower()

# Adjust strategy based on error
if "timeout" in error_str:
    # Will retry
elif "validation" in error_str and step_name.lower() in ["review", "test"]:
    # Will skip (non-critical)
else:
    # Will fail (critical)
```

---

### 4. Workflow Preview Issues

#### Issue: No workflow preview shown

**Symptoms**: Workflow starts immediately without preview.

**Cause**: Auto mode enabled (`--auto` flag).

**Solution**: Remove `--auto` flag:

```bash
# ✅ Shows preview
tapps-agents simple-mode build --prompt "Add feature"

# ❌ No preview
tapps-agents simple-mode build --prompt "Add feature" --auto
```

**Note**: Preview only shows in interactive mode (non-auto).

#### Issue: Preview shows wrong step count

**Symptoms**: Preview shows 7 steps but fast mode enabled.

**Cause**: Fast mode changes step count.

**Solution**: This is expected. Fast mode shows 4 steps (steps 5-7 from complete mode).

**Check**: Verify `--fast` flag is set correctly:

```bash
# Complete mode (7 steps)
tapps-agents simple-mode build --prompt "..."

# Fast mode (4 steps)
tapps-agents simple-mode build --prompt "..." --fast
```

---

### 5. BuildOrchestrator Callback Issues

#### Issue: Callbacks not being called

**Symptoms**: Custom callbacks not executed during workflow.

**Possible Causes**:
1. Callbacks not passed to `execute()`
2. Wrong callback signature
3. Step execution path doesn't trigger callbacks

**Solution**: Verify callback signatures:

```python
# ✅ Correct signatures
def on_step_start(step_num: int, step_name: str) -> None:
    ...

def on_step_complete(step_num: int, step_name: str, status: str) -> None:
    ...

def on_step_error(step_num: int, step_name: str, error: Exception) -> None:
    ...

# Pass to orchestrator
orchestrator.execute(
    ...,
    on_step_start=on_step_start,
    on_step_complete=on_step_complete,
    on_step_error=on_step_error,
)
```

**Check**: Ensure callbacks are passed to `execute()` method, not just defined.

---

### 6. Configuration Issues

#### Issue: Simple Mode not enabled

**Symptoms**: `simple-mode build` command not available or fails.

**Solution**: Enable Simple Mode:

```bash
tapps-agents simple-mode on
tapps-agents simple-mode status  # Verify enabled
```

**Check**: Verify config file exists:

```bash
# Check config
cat .tapps-agents/config.yaml | grep simple_mode
```

---

### 7. Performance Issues

#### Issue: Workflow execution slow

**Symptoms**: Workflow takes longer than expected.

**Possible Causes**:
1. Network issues (Context7, agent APIs)
2. Large codebase analysis
3. Multiple retries due to errors

**Solutions**:

1. **Use Fast Mode** (skip documentation steps):
   ```bash
   tapps-agents simple-mode build --prompt "..." --fast
   ```

2. **Check Network**: Verify Context7 API key and network connectivity

3. **Monitor Recovery Actions**: Check if errors causing retries:
   ```python
   summary = handler.get_recovery_summary()
   print(f"Retries: {summary['retries']}")
   ```

4. **Check Step Durations**: Review execution summary for slow steps

---

## Debugging Tips

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check StatusReporter State

```python
reporter = StatusReporter(total_steps=7)
# ... execute steps ...
print(f"Current step: {reporter.current_step}")
print(f"Step times: {reporter.step_times}")
print(f"Step status: {reporter.step_status}")
```

### Check Error Recovery Summary

```python
handler = ErrorRecoveryHandler()
# ... handle errors ...
summary = handler.get_recovery_summary()
print(summary)
```

### Verify Callback Integration

```python
# Add debug prints to callbacks
def on_step_start(step_num: int, step_name: str):
    print(f"DEBUG: Step {step_num} started: {step_name}")
    reporter.start_step(step_num, step_name)
```

---

## Getting Help

### Check Documentation

- [Simple Mode Guide](SIMPLE_MODE_GUIDE.md)
- [Phase 2 Features](SIMPLE_MODE_PHASE2_FEATURES.md)
- [Command Reference](TAPPS_AGENTS_COMMAND_REFERENCE.md)

### Verify Installation

```bash
tapps-agents doctor
```

### Check Status

```bash
tapps-agents simple-mode status
```

### Report Issues

Include:
- Error message (full output)
- Command used
- Configuration (if relevant)
- Steps to reproduce

---

## Common Error Patterns

### Pattern 1: Missing Required Argument

**Error**: `--prompt argument is required`

**Fix**: Always provide `--prompt`:

```bash
tapps-agents simple-mode build --prompt "Your feature description"
```

### Pattern 2: Validation Error

**Error**: `Validation error: ...`

**Fix**: Check error message for specific validation issue and fix input.

### Pattern 3: Network Timeout

**Error**: `TimeoutError: Connection timeout`

**Fix**: ErrorRecoveryHandler will automatically retry. If persists, check network/API key.

### Pattern 4: File Not Found

**Error**: `FileNotFoundError: ...`

**Fix**: 
- Non-critical steps (document/test): Will continue automatically
- Critical steps: Check file path or create file first

---

## Best Practices

1. **Always Provide --prompt**: Required for build command
2. **Use Fast Mode Sparingly**: Complete mode provides better documentation
3. **Monitor Recovery Actions**: Check recovery summary to understand resilience
4. **Enable Verbose Logging**: For debugging complex issues
5. **Verify Configuration**: Check Simple Mode is enabled before use

---

## Related Documentation

- [Simple Mode Guide](SIMPLE_MODE_GUIDE.md)
- [Phase 2 Features](SIMPLE_MODE_PHASE2_FEATURES.md)
- [Command Reference](TAPPS_AGENTS_COMMAND_REFERENCE.md)
