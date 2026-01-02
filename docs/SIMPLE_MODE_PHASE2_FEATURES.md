# Simple Mode Phase 2 Features Documentation

**Date**: 2025-01-16  
**Status**: ✅ Complete  
**Phase**: Phase 2 - User Experience Improvements

---

## Overview

Phase 2 introduces significant user experience improvements to Simple Mode build workflow, including real-time status reporting, error recovery, and enhanced workflow visibility.

---

## Features

### 1. Real-Time Status Reporting

**StatusReporter** provides real-time progress indicators during workflow execution.

#### Usage

The StatusReporter is automatically integrated into Simple Mode build workflows. You'll see real-time progress like:

```
[1/7] Enhance prompt (requirements analysis)... [OK] (2.1s)
[2/7] Create user stories... [OK] (1.8s)
[3/7] Design architecture... [OK] (3.2s)
...
```

#### Features

- **Step Progress**: Shows current step number and total steps (`[X/Y]`)
- **Step Names**: Clear, descriptive step names
- **Status Icons**: 
  - `[OK]` - Step completed successfully
  - `[FAIL]` - Step failed
  - `[SKIP]` - Step skipped
- **Duration Tracking**: Shows execution time for each step
- **Execution Summary**: Comprehensive summary after workflow completion

#### Example Output

```
[1/7] Enhance prompt (requirements analysis)... [OK] (2.1s)
[2/7] Create user stories... [OK] (1.8s)
[3/7] Design architecture... [OK] (3.2s)
[4/7] Design API/data models... [OK] (2.9s)
[5/7] Implement code... [OK] (5.3s)
[6/7] Review code quality... [OK] (2.0s)
[7/7] Generate tests... [OK] (1.9s)

============================================================
Execution Summary
============================================================
Steps Executed: 7/7
Total Time: 19.2s

Step Details:
  [OK] Step 1: Enhance prompt (requirements analysis) (2.1s)
  [OK] Step 2: Create user stories (1.8s)
  [OK] Step 3: Design architecture (3.2s)
  [OK] Step 4: Design API/data models (2.9s)
  [OK] Step 5: Implement code (5.3s)
  [OK] Step 6: Review code quality (2.0s)
  [OK] Step 7: Generate tests (1.9s)
```

#### Programmatic Usage

```python
from tapps_agents.cli.utils.status_reporter import StatusReporter

# Initialize reporter
reporter = StatusReporter(total_steps=7)

# Track steps
reporter.start_step(1, "Enhance prompt")
# ... execute step ...
reporter.complete_step(1, "Enhance prompt", "success")

# Print summary
reporter.print_summary()
```

---

### 2. Error Recovery Handler

**ErrorRecoveryHandler** provides automatic error recovery strategies based on error type.

#### Automatic Recovery Strategies

The handler automatically determines recovery action based on error type:

| Error Type | Strategy | When Used |
|------------|----------|-----------|
| Timeout/Network | Retry | Connection issues, timeouts |
| Validation (non-critical) | Skip | Review/test/document steps |
| File Not Found (non-critical) | Continue | Document/test steps |
| Critical Errors | Fail | Implementation/planning steps |

#### Usage

```python
from tapps_agents.cli.utils.error_recovery import ErrorRecoveryHandler

handler = ErrorRecoveryHandler(interactive=False)

# Handle step error
action = handler.handle_step_error(
    step_num=1,
    step_name="test step",
    error=TimeoutError("Connection timeout"),
    retry_callback=lambda: retry_step(),
    skip_callback=lambda: skip_step(),
    continue_callback=lambda: continue_with_degraded(),
)

# Get recovery summary
summary = handler.get_recovery_summary()
print(f"Retries: {summary['retries']}")
print(f"Skips: {summary['skips']}")
```

#### Interactive Mode

Enable interactive mode for user-guided recovery:

```python
handler = ErrorRecoveryHandler(interactive=True)

# User will be prompted:
# Step Failed: test step
# Error: Connection timeout
# 
# Recovery Options:
#   1. Retry step
#   2. Skip step and continue
#   3. Continue with degraded functionality
#   4. Fail workflow
```

#### Recovery Summary

```python
summary = handler.get_recovery_summary()
# Returns:
# {
#     "total_recoveries": 3,
#     "retries": 1,
#     "skips": 1,
#     "continues": 0,
#     "failures": 1,
#     "actions": [...]
# }
```

---

### 3. Workflow Preview

Before execution, Simple Mode shows a preview of the workflow:

```
============================================================
Workflow Preview
============================================================
Feature: Add user authentication
Mode: Complete (7 steps)

Steps to Execute:
  1. Enhance prompt (requirements analysis)     ~2s
  2. Create user stories                        ~2s
  3. Design architecture                        ~3s
  4. Design API/data models                     ~3s
  5. Implement code                             ~5s
  6. Review code quality                        ~2s
  7. Generate tests                             ~2s

Estimated Total Time: ~19s
Configuration: automation.level=2, fast_mode=false

============================================================
```

**Note**: Preview only shows in non-auto mode (interactive execution).

---

### 4. Enhanced BuildOrchestrator Callbacks

BuildOrchestrator now supports callbacks for step tracking:

```python
from tapps_agents.simple_mode.orchestrators.build_orchestrator import BuildOrchestrator

def on_step_start(step_num: int, step_name: str):
    print(f"Starting step {step_num}: {step_name}")

def on_step_complete(step_num: int, step_name: str, status: str):
    print(f"Step {step_num} completed: {status}")

def on_step_error(step_num: int, step_name: str, error: Exception):
    print(f"Step {step_num} failed: {error}")

orchestrator = BuildOrchestrator(project_root=Path.cwd(), config=config)

result = await orchestrator.execute(
    intent=intent,
    parameters=parameters,
    fast_mode=False,
    on_step_start=on_step_start,
    on_step_complete=on_step_complete,
    on_step_error=on_step_error,
)
```

---

## Command Usage

### Basic Build Command

```bash
tapps-agents simple-mode build --prompt "Add user authentication"
```

**Output**:
- Workflow preview (if not in auto mode)
- Real-time step progress
- Execution summary

### Fast Mode

```bash
tapps-agents simple-mode build --prompt "Add feature" --fast
```

**Output**:
- Skips steps 1-4 (enhance, plan, architect, design)
- Shows progress for steps 5-7 only
- Faster execution (~9s vs ~19s)

### Auto Mode

```bash
tapps-agents simple-mode build --prompt "Add feature" --auto
```

**Output**:
- No workflow preview
- Real-time progress still shown
- Execution summary at end

---

## Integration Examples

### Custom Status Tracking

```python
from tapps_agents.cli.utils.status_reporter import StatusReporter
from tapps_agents.simple_mode.orchestrators.build_orchestrator import BuildOrchestrator

reporter = StatusReporter(total_steps=7)

def on_step_start(step_num: int, step_name: str):
    reporter.start_step(step_num, step_name)
    # Custom logging
    logger.info(f"Step {step_num} started: {step_name}")

def on_step_complete(step_num: int, step_name: str, status: str):
    reporter.complete_step(step_num, step_name, status)
    # Custom metrics
    metrics.record_step(step_num, step_name, status)

orchestrator = BuildOrchestrator(...)
result = await orchestrator.execute(
    ...,
    on_step_start=on_step_start,
    on_step_complete=on_step_complete,
)
```

### Error Recovery Integration

```python
from tapps_agents.cli.utils.error_recovery import ErrorRecoveryHandler

handler = ErrorRecoveryHandler(interactive=False)

def on_step_error(step_num: int, step_name: str, error: Exception):
    action = handler.handle_step_error(
        step_num=step_num,
        step_name=step_name,
        error=error,
        retry_callback=lambda: retry_step(step_num),
        skip_callback=lambda: skip_step(step_num),
    )
    
    if action == "fail":
        raise error  # Re-raise if recovery failed

orchestrator.execute(..., on_step_error=on_step_error)
```

---

## Configuration

Phase 2 features work with default configuration. No additional configuration required.

**Optional**: Enable interactive error recovery:

```python
handler = ErrorRecoveryHandler(interactive=True)
```

---

## Troubleshooting

### Status Reporter Not Showing Progress

**Issue**: No progress indicators during execution.

**Solution**: Ensure StatusReporter callbacks are passed to BuildOrchestrator:

```python
# ✅ Correct
orchestrator.execute(..., on_step_start=on_step_start, ...)

# ❌ Incorrect
orchestrator.execute(...)  # No callbacks
```

### Error Recovery Not Working

**Issue**: Errors cause immediate failure without recovery.

**Solution**: Ensure ErrorRecoveryHandler is integrated with on_step_error callback:

```python
handler = ErrorRecoveryHandler()
orchestrator.execute(..., on_step_error=handler.handle_step_error)
```

### Workflow Preview Not Showing

**Issue**: No preview before execution.

**Solution**: Preview only shows in non-auto mode. Remove `--auto` flag:

```bash
# ✅ Shows preview
tapps-agents simple-mode build --prompt "..."

# ❌ No preview
tapps-agents simple-mode build --prompt "..." --auto
```

---

## Best Practices

1. **Always Use StatusReporter**: Provides valuable feedback during long workflows
2. **Handle Errors Gracefully**: Use ErrorRecoveryHandler for automatic recovery
3. **Monitor Recovery Actions**: Check recovery summary to understand workflow resilience
4. **Use Fast Mode Sparingly**: Complete mode provides better documentation and design
5. **Enable Interactive Mode**: For debugging or when recovery strategy is unclear

---

## Related Documentation

- [Simple Mode Guide](docs/SIMPLE_MODE_GUIDE.md)
- [Command Reference](docs/TAPPS_AGENTS_COMMAND_REFERENCE.md)
- [Phase 2 Implementation Status](docs/workflows/simple-mode/phase2-user-experience-20250116-000000/PHASE2_IMPLEMENTATION_STATUS.md)

---

## API Reference

### StatusReporter

```python
class StatusReporter:
    def __init__(self, total_steps: int = 0)
    def start_step(self, step_num: int, step_name: str) -> None
    def complete_step(self, step_num: int, step_name: str, status: str) -> None
    def print_summary(self) -> None
```

### ErrorRecoveryHandler

```python
class ErrorRecoveryHandler:
    def __init__(self, interactive: bool = False)
    def handle_step_error(
        self,
        step_num: int,
        step_name: str,
        error: Exception,
        retry_callback: Callable | None = None,
        skip_callback: Callable | None = None,
        continue_callback: Callable | None = None,
    ) -> str
    def get_recovery_summary(self) -> dict[str, Any]
```

### BuildOrchestrator.execute()

```python
async def execute(
    self,
    intent: Intent,
    parameters: dict[str, Any] | None = None,
    fast_mode: bool = False,
    on_step_start: Callable[[int, str], None] | None = None,
    on_step_complete: Callable[[int, str, str], None] | None = None,
    on_step_error: Callable[[int, str, Exception], None] | None = None,
) -> dict[str, Any]
```
