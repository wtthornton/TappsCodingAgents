# CLI Development Guide

This guide explains how to develop and extend CLI commands in TappsCodingAgents using the standardized patterns established in Epic 22.

## Table of Contents

1. [Overview](#overview)
2. [Feedback System](#feedback-system)
3. [Standardized Utilities](#standardized-utilities)
4. [Patterns for Adding Commands](#patterns-for-adding-commands)
5. [Error Handling](#error-handling)
6. [Exit Codes](#exit-codes)
7. [Startup Routines](#startup-routines)
8. [Best Practices](#best-practices)
9. [Examples](#examples)

## Overview

The CLI uses standardized patterns to ensure:
- **Consistent behavior** across entrypoints (`tapps-agents` vs `python -m tapps_agents.cli`)
- **Proper async handling** without nested event loop issues
- **Standardized error output** for automation and CI/CD
- **Centralized agent lifecycle management** (activate/run/close)

All utilities are in `tapps_agents/cli/base.py`.

## Feedback System

The CLI uses a centralized feedback system to provide consistent, user-friendly output across all commands. This system supports multiple verbosity levels and both text and JSON output formats.

### Verbosity Levels

The feedback system supports three verbosity levels:

- **QUIET** (`--quiet` / `-q`): Only errors and final results are shown. Ideal for scripts and automation.
- **NORMAL** (default): Standard feedback with progress indicators for long operations.
- **VERBOSE** (`--verbose` / `-v`): Detailed debugging information including all steps and internal state.

### Using the Feedback System

#### Basic Usage

```python
from tapps_agents.cli.feedback import get_feedback

def handle_my_command(args):
    feedback = get_feedback()
    feedback.format_type = getattr(args, "format", "json")
    
    # Start operation timing
    feedback.start_operation("My Operation")
    
    # Show informational message
    feedback.info("Processing files...")
    
    # Show progress
    feedback.progress("Processing file 3 of 10...", percentage=30)
    
    # Clear progress line
    feedback.clear_progress()
    
    # Show success
    feedback.success("Operation completed", summary={"files_processed": 10})
    
    # Output final result
    feedback.output_result({"result": "data"}, message="Done")
```

#### Message Types

**Info Messages**: Use for normal operational messages
```python
feedback.info("Loading configuration...")
feedback.info("Found 5 files to process", details={"file_count": 5})
```

**Success Messages**: Use to confirm successful completion
```python
feedback.success("Review completed", 
                 data={"score": 85}, 
                 summary={"files_processed": 1})
```

**Warning Messages**: Use for non-fatal issues
```python
feedback.warning("Some dependencies are outdated", 
                 remediation="Run 'pip install --upgrade package'")
```

**Error Messages**: Use for failures (exits automatically)
```python
feedback.error("File not found: example.py",
               error_code="file_not_found",
               context={"file_path": "example.py"},
               remediation="Check that the file exists",
               exit_code=1)
```

**Progress Messages**: Use for long-running operations
```python
# Simple progress
feedback.progress("Processing... (step 3 of 10)")

# Progress with bar
feedback.progress("Processing...", percentage=75, show_progress_bar=True)
```

#### Progress Tracking

For multi-step operations, use `ProgressTracker`:

```python
from tapps_agents.cli.feedback import ProgressTracker, get_feedback

feedback = get_feedback()
tracker = ProgressTracker(total_steps=10, operation_name="Processing", feedback_manager=feedback)

for i in range(10):
    # Do work...
    tracker.update(step=i+1, message=f"Processing item {i+1}")

tracker.complete("All items processed")
```

#### Output Formats

The feedback system supports both text and JSON output:

**Text Mode** (default for interactive use):
- Human-readable messages
- Progress indicators
- Clear success/error formatting

**JSON Mode** (for automation):
- Structured output with standard envelope
- All information in parseable format
- Metadata including timestamps and duration

#### Standard JSON Envelope

All JSON output follows this structure:

```json
{
  "success": true,
  "message": "Human-readable summary",
  "data": {
    // Command-specific data
  },
  "metadata": {
    "timestamp": "2024-01-01T12:00:00Z",
    "duration_ms": 1234,
    "command": "review",
    "version": "2.0.6"
  },
  "warnings": [
    // Array of warning messages (if any)
  ],
  "error": {
    // Error details (only if success: false)
    "code": "error_code",
    "message": "Error message",
    "context": {},
    "remediation": "How to fix"
  }
}
```

#### Stream Separation

- **stdout**: Final results and data (for JSON parsing)
- **stderr**: Progress updates, info messages, warnings, errors

This separation ensures that JSON output can be parsed cleanly while progress information is still visible.

### Best Practices

1. **Always provide feedback**: Never have silent operations. At minimum, show start and completion.

2. **Use appropriate verbosity**: 
   - Info messages only in normal/verbose mode
   - Progress for operations > 5 seconds
   - Detailed info only in verbose mode

3. **Time operations**: Use `start_operation()` to track duration, which is included in JSON metadata.

4. **Provide context**: Include file paths, counts, and other relevant details in messages.

5. **Be actionable**: Error messages should suggest fixes, success messages should indicate next steps.

6. **Respect format type**: Check `feedback.format_type` and output accordingly.

## Standardized Utilities

### Exit Codes

Standard exit codes are defined as constants:

```python
from tapps_agents.cli.base import (
    EXIT_SUCCESS,        # 0 - Command succeeded
    EXIT_GENERAL_ERROR,  # 1 - General error
    EXIT_USAGE_ERROR,    # 2 - Invalid arguments/usage
    EXIT_CONFIG_ERROR,   # 3 - Configuration error
)
```

**Usage**: Always use these constants instead of magic numbers.

### Output Formatting

#### `format_output(data, format_type="json")`

Formats and prints output based on format type (JSON or text).

```python
from tapps_agents.cli.base import format_output

# JSON output (default)
format_output({"result": "success"}, format_type="json")

# Text output
format_output("Operation completed", format_type="text")
```

#### `format_error_output(error, error_type, exit_code, format_type, details)`

Formats and outputs error messages with consistent structure. **Always exits** with the specified exit code.

```python
from tapps_agents.cli.base import format_error_output, EXIT_GENERAL_ERROR

# Simple error
format_error_output(
    "File not found: example.py",
    error_type="file_not_found",
    exit_code=EXIT_GENERAL_ERROR,
    format_type="json"
)

# Error with details
format_error_output(
    "Validation failed",
    error_type="validation_error",
    exit_code=EXIT_USAGE_ERROR,
    format_type="text",
    details={"field": "email", "reason": "Invalid format"}
)
```

**JSON Error Format**:
```json
{
  "success": false,
  "error": "Error message",
  "error_type": "error_type",
  "details": { ... }
}
```

### Agent Lifecycle Management

#### `run_with_agent_lifecycle(agent, command_func, *args, **kwargs)`

Runs a command function with automatic agent lifecycle management:
1. Activates agent (loads configs, initializes)
2. Runs command function
3. Closes agent (cleanup)

**This is the standard pattern for agent commands.**

```python
from tapps_agents.cli.base import run_with_agent_lifecycle
from tapps_agents.agents.reviewer.agent import ReviewerAgent

async def my_command():
    reviewer = ReviewerAgent()
    
    async def _run_review():
        return await reviewer.run("review", file="example.py")
    
    result = await run_with_agent_lifecycle(reviewer, _run_review)
    return result
```

#### `run_agent_command(agent, command, format_type, exit_on_error, **kwargs)`

High-level convenience function that combines:
- Agent lifecycle management
- Command execution
- Error handling
- Output formatting

```python
from tapps_agents.cli.base import run_agent_command
from tapps_agents.agents.reviewer.agent import ReviewerAgent

async def my_command():
    reviewer = ReviewerAgent()
    
    # Automatically handles activate/close, error handling, and output
    result = await run_agent_command(
        reviewer,
        "score",
        format_type="json",
        exit_on_error=True,
        file="example.py"
    )
    # If exit_on_error=True and error occurs, function exits
    # Otherwise, returns result dict (may contain "error" key)
    return result
```

### Async Command Execution

#### `run_async_command(coro)`

Runs an async coroutine using `asyncio.run()` with proper event loop management.

**Use this instead of calling `asyncio.run()` directly.**

```python
from tapps_agents.cli.base import run_async_command

# In a synchronous handler function
def handle_command(args):
    run_async_command(my_async_function(args.file))
```

**Important**: This function will raise `RuntimeError` if called from within an existing event loop. Use `await` instead in async contexts.

## Patterns for Adding Commands

### Pattern 1: Simple Async Command Function

For commands that are called directly (not through handlers):

```python
from tapps_agents.cli.base import (
    run_with_agent_lifecycle,
    handle_agent_error,
    format_output,
)
from tapps_agents.agents.reviewer.agent import ReviewerAgent
from pathlib import Path

async def my_command(file_path: str, output_format: str = "json"):
    """My command description."""
    # Validate inputs
    path = Path(file_path)
    if not path.exists():
        from tapps_agents.cli.base import format_error_output, EXIT_GENERAL_ERROR
        format_error_output(
            f"File not found: {file_path}",
            error_type="file_not_found",
            exit_code=EXIT_GENERAL_ERROR,
            format_type=output_format,
        )
    
    # Create agent
    reviewer = ReviewerAgent()
    
    # Define command function
    async def _run_command():
        return await reviewer.run("review", file=file_path)
    
    # Run with lifecycle management
    result = await run_with_agent_lifecycle(reviewer, _run_command)
    
    # Handle errors
    handle_agent_error(result, format_type=output_format)
    
    # Format output
    format_output(result, format_type=output_format)
```

### Pattern 2: Handler Function (Synchronous)

For commands called from argparse handlers:

```python
from tapps_agents.cli.base import (
    run_async_command,
    run_with_agent_lifecycle,
    handle_agent_error,
    format_output,
)
from tapps_agents.agents.reviewer.agent import ReviewerAgent

def _handle_my_command(args):
    """Handle my command from argparse."""
    output_format = getattr(args, "format", "json")
    
    reviewer = ReviewerAgent()
    
    async def _run_command():
        return await reviewer.run("review", file=args.file)
    
    # Use run_async_command to bridge sync/async boundary
    result = run_async_command(
        run_with_agent_lifecycle(reviewer, _run_command)
    )
    
    # Handle errors
    handle_agent_error(result, format_type=output_format)
    
    # Format output
    format_output(result, format_type=output_format)
```

### Pattern 3: Using High-Level Helper

Simplest pattern using `run_agent_command`:

```python
from tapps_agents.cli.base import run_async_command, run_agent_command
from tapps_agents.agents.reviewer.agent import ReviewerAgent

def _handle_my_command(args):
    """Handle my command - simplified pattern."""
    output_format = getattr(args, "format", "json")
    
    reviewer = ReviewerAgent()
    
    # One-liner: handles lifecycle, errors, and output
    run_async_command(
        run_agent_command(
            reviewer,
            "score",
            format_type=output_format,
            exit_on_error=True,
            file=args.file
        )
    )
    # Function exits here if error occurred
```

## Error Handling

### Standard Error Handling Flow

1. **Validate inputs early** - Check file existence, required arguments, etc.
2. **Use `format_error_output()` for validation errors** - Provides structured error output
3. **Use `handle_agent_error()` for agent errors** - Handles errors from agent.run() results
4. **Always use standardized exit codes** - Use constants, not magic numbers

### Error Types

Common error types:
- `file_not_found` - File or path doesn't exist
- `validation_error` - Input validation failed
- `config_error` - Configuration issue
- `runtime_error` - Runtime execution error
- `error` - Generic error (default)

### Example: Comprehensive Error Handling

```python
from tapps_agents.cli.base import (
    format_error_output,
    handle_agent_error,
    EXIT_GENERAL_ERROR,
    EXIT_USAGE_ERROR,
)

async def my_command(file_path: str, output_format: str = "json"):
    # Input validation
    path = Path(file_path)
    if not path.exists():
        format_error_output(
            f"File not found: {file_path}",
            error_type="file_not_found",
            exit_code=EXIT_GENERAL_ERROR,
            format_type=output_format,
        )
    
    if not path.suffix == ".py":
        format_error_output(
            f"Invalid file type: {file_path}",
            error_type="validation_error",
            exit_code=EXIT_USAGE_ERROR,
            format_type=output_format,
            details={"expected": ".py", "got": path.suffix}
        )
    
    # Agent execution (errors handled by handle_agent_error)
    reviewer = ReviewerAgent()
    async def _run():
        return await reviewer.run("review", file=file_path)
    
    result = await run_with_agent_lifecycle(reviewer, _run)
    handle_agent_error(result, format_type=output_format)
    
    # Success
    format_output(result, format_type=output_format)
```

## Exit Codes

### When to Use Each Exit Code

- **EXIT_SUCCESS (0)**: Command completed successfully
- **EXIT_GENERAL_ERROR (1)**: General error (file not found, runtime error, etc.)
- **EXIT_USAGE_ERROR (2)**: Invalid arguments, missing required parameters, invalid format
- **EXIT_CONFIG_ERROR (3)**: Configuration file issues, missing config, invalid config

### Exit Code Best Practices

1. **Always exit with appropriate code** - Don't just use `sys.exit(1)` everywhere
2. **Use constants** - Import from `tapps_agents.cli.base`
3. **Document exit codes** - In command help text if non-standard
4. **Test exit codes** - Ensure CI/CD scripts can rely on them

## Startup Routines

### What Are Startup Routines?

Startup routines run automatically when the CLI starts, regardless of entrypoint:
- Documentation refresh (Context7)
- Configuration validation
- Cache initialization

### When Do They Run?

Startup routines run:
- At the beginning of `main()` function
- For both `tapps-agents` and `python -m tapps_agents.cli`
- In the background (non-blocking)
- Non-fatally (failures don't prevent CLI execution)

### How to Disable (if needed)

Startup routines can be disabled by modifying `_run_startup_routines()` in `tapps_agents/cli.py`, but this is generally not recommended.

### Adding New Startup Routines

To add new startup routines, modify `tapps_agents/core/startup.py`:

```python
async def startup_routines(
    config: ProjectConfig | None = None,
    refresh_docs: bool = True,
    background_refresh: bool = True,
) -> dict[str, Any]:
    """Run all startup routines."""
    routines: dict[str, Any] = {}
    results: dict[str, Any] = {"success": True, "routines": routines}
    
    if refresh_docs:
        # Existing documentation refresh
        ...
    
    # Add your new routine here
    if some_condition:
        my_routine_result = await my_startup_routine(config)
        routines["my_routine"] = my_routine_result
    
    return results
```

## Best Practices

### 1. Always Use Standardized Utilities

✅ **DO**:
```python
from tapps_agents.cli.base import run_with_agent_lifecycle, handle_agent_error
```

❌ **DON'T**:
```python
await agent.activate()
result = await agent.run(...)
await agent.close()
```

### 2. Handle Errors Consistently

✅ **DO**:
```python
handle_agent_error(result, format_type=output_format)
```

❌ **DON'T**:
```python
if "error" in result:
    print(f"Error: {result['error']}", file=sys.stderr)
    sys.exit(1)
```

### 3. Use Proper Exit Codes

✅ **DO**:
```python
from tapps_agents.cli.base import EXIT_USAGE_ERROR
format_error_output(..., exit_code=EXIT_USAGE_ERROR)
```

❌ **DON'T**:
```python
sys.exit(1)  # Always 1, no context
```

### 4. Validate Inputs Early

✅ **DO**:
```python
if not path.exists():
    format_error_output("File not found", ...)
```

❌ **DON'T**:
```python
# Let agent handle missing file - less clear error
result = await agent.run("review", file=missing_file)
```

### 5. Use run_async_command for Sync/Async Boundary

✅ **DO**:
```python
def handler(args):
    run_async_command(my_async_function())
```

❌ **DON'T**:
```python
def handler(args):
    asyncio.run(my_async_function())  # Can cause nested loop issues
```

## Examples

### Complete Example: Adding a New Command

```python
# In tapps_agents/cli.py

from tapps_agents.cli.base import (
    run_async_command,
    run_with_agent_lifecycle,
    handle_agent_error,
    format_output,
    format_error_output,
    EXIT_GENERAL_ERROR,
)
from tapps_agents.agents.reviewer.agent import ReviewerAgent
from pathlib import Path

# 1. Define async command function
async def analyze_command(
    file_path: str,
    analysis_type: str = "full",
    output_format: str = "json"
):
    """Analyze a code file."""
    # Validate inputs
    path = Path(file_path)
    if not path.exists():
        format_error_output(
            f"File not found: {file_path}",
            error_type="file_not_found",
            exit_code=EXIT_GENERAL_ERROR,
            format_type=output_format,
        )
    
    # Create agent
    reviewer = ReviewerAgent()
    
    # Define command execution
    async def _run_analysis():
        return await reviewer.run(
            "analyze",
            file=file_path,
            analysis_type=analysis_type
        )
    
    # Run with lifecycle management
    result = await run_with_agent_lifecycle(reviewer, _run_analysis)
    
    # Handle errors
    handle_agent_error(result, format_type=output_format)
    
    # Format output
    format_output(result, format_type=output_format)

# 2. Define handler function
def _handle_analyze_command(args):
    """Handle analyze command from argparse."""
    run_async_command(
        analyze_command(
            args.file,
            getattr(args, "type", "full"),
            getattr(args, "format", "json")
        )
    )

# 3. Add to argparse in main()
def main():
    # ... existing code ...
    
    analyze_parser = reviewer_subparsers.add_parser(
        "analyze", aliases=["*analyze"], help="Analyze a code file"
    )
    analyze_parser.add_argument("file", help="Path to code file")
    analyze_parser.add_argument(
        "--type", choices=["full", "quick"], default="full",
        help="Analysis type"
    )
    analyze_parser.add_argument(
        "--format", choices=["json", "text"], default="json",
        help="Output format"
    )
    
    # ... in command routing ...
    elif args.agent == "reviewer":
        if args.command == "analyze":
            _handle_analyze_command(args)
```

## Migration Guide

### Migrating Existing Commands

To migrate an existing command to use standardized patterns:

1. **Replace direct asyncio.run() calls**:
   ```python
   # Old
   asyncio.run(reviewer.activate())
   result = asyncio.run(reviewer.run("score", file=args.file))
   asyncio.run(reviewer.close())
   
   # New
   async def _run():
       return await reviewer.run("score", file=args.file)
   result = run_async_command(run_with_agent_lifecycle(reviewer, _run))
   ```

2. **Replace manual error handling**:
   ```python
   # Old
   if "error" in result:
       print(f"Error: {result['error']}", file=sys.stderr)
       sys.exit(1)
   
   # New
   handle_agent_error(result, format_type=output_format)
   ```

3. **Replace manual output formatting**:
   ```python
   # Old
   if output_format == "json":
       print(json.dumps(result, indent=2))
   else:
       print(result)
   
   # New
   format_output(result, format_type=output_format)
   ```

## Testing

When adding new commands, ensure:

1. **Exit codes are tested** - Verify correct exit codes for success/failure
2. **Error output is tested** - Check JSON and text error formats
3. **Entrypoint parity is tested** - Both entrypoints behave identically
4. **Agent lifecycle is tested** - Verify activate/close are called

See `tests/e2e/cli/test_cli_entrypoint_parity.py` for examples.

## Summary

- ✅ Use standardized utilities from `tapps_agents/cli/base.py`
- ✅ Always use `run_with_agent_lifecycle()` for agent commands
- ✅ Use `run_async_command()` to bridge sync/async boundaries
- ✅ Use `handle_agent_error()` and `format_error_output()` for errors
- ✅ Use standardized exit codes (constants, not magic numbers)
- ✅ Validate inputs early with clear error messages
- ✅ Test exit codes and error output formats

For questions or issues, see the main [Developer Guide](DEVELOPER_GUIDE.md) or open an issue.

