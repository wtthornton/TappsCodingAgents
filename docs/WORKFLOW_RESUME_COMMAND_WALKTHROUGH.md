# Workflow Resume Command - Code Walkthrough

## Overview

The workflow resume command (`tapps-agents workflow resume`) allows users to resume interrupted, paused, or failed workflows from their last saved checkpoint. This document provides a comprehensive walkthrough of the implementation, including the fix for the critical bug where `executor.run()` was called instead of `executor.execute()`.

## Architecture

### Components

1. **CLI Parser** (`tapps_agents/cli/parsers/top_level.py`)
   - Defines command-line arguments
   - Handles `--workflow-id`, `--validate`, `--no-validate`, `--max-steps`

2. **Command Handler** (`tapps_agents/cli/commands/top_level.py`)
   - `handle_workflow_resume_command()` - Main handler function
   - Orchestrates state loading and workflow execution

3. **Workflow Executor** (`tapps_agents/workflow/executor.py`)
   - `WorkflowExecutor` class - Core execution engine
   - `execute()` - Async method that runs workflow steps
   - `load_last_state()` - Loads persisted workflow state
   - `resume_workflow()` - Resumes paused workflows

4. **State Manager** (`tapps_agents/workflow/state_manager.py`)
   - `AdvancedStateManager` - Manages workflow state persistence
   - Handles validation, migration, and recovery

## Critical Bug Fix

### The Problem

**Location:** `tapps_agents/cli/commands/top_level.py:2421`

**Original Code:**
```python
result = asyncio.run(executor.run())
```

**Issue:** `WorkflowExecutor` does not have a `run()` method. This caused an `AttributeError` when attempting to resume workflows.

**Root Cause:** The method name was incorrect. The correct method is `execute()`, which is an async method that takes optional parameters.

### The Fix

**Fixed Code:**
```python
final_state = run_async_command(executor.execute(
    workflow=None,  # Already loaded
    target_file=target_file,
    max_steps=max_steps,
))
```

**Key Changes:**
1. Changed `executor.run()` to `executor.execute()`
2. Used `run_async_command()` helper instead of `asyncio.run()` directly (best practice for event loop management)
3. Passed correct parameters: `workflow=None` (already loaded), `target_file` (from state), `max_steps` (from args)
4. Fixed return value handling: `execute()` returns `WorkflowState`, not a result object
5. Updated status checking: Use `final_state.status` instead of `result.status`

## Code Flow

### 1. Command Entry Point

```python
def handle_workflow_resume_command(args: object) -> None:
    """Handle 'workflow resume' command (Epic 12)"""
```

**Parameters:**
- `args.workflow_id` - Optional specific workflow ID
- `args.validate` - Whether to validate state (default: True)
- `args.max_steps` - Maximum steps to execute (default: 50)

### 2. State Loading

**Two Paths:**

#### Path A: Specific Workflow ID
```python
if workflow_id:
    state_dir = Path.cwd() / ".tapps-agents" / "workflow-state"
    manager = AdvancedStateManager(state_dir)
    state, metadata = manager.load_state(workflow_id=workflow_id, validate=validate)
    executor.state = state
    # Load workflow from metadata
    if metadata.workflow_path:
        parser = WorkflowParser()
        executor.workflow = parser.parse_file(Path(metadata.workflow_path))
```

#### Path B: Last State (Default)
```python
else:
    executor.state = executor.load_last_state(validate=validate)
    # Load workflow from state variables
    workflow_path = executor.state.variables.get("_workflow_path")
    if workflow_path:
        parser = WorkflowParser()
        executor.workflow = parser.parse_file(Path(workflow_path))
```

### 3. State Validation

**Status Checks:**

```python
# Already completed - exit early
if executor.state.status == "completed":
    print("Status: Already completed")
    return

# Previously failed - reset to running
if executor.state.status == "failed":
    print("Warning: Workflow previously failed. Resuming from failure point.")
    executor.state.status = "running"

# Paused - resume
if executor.state.status == "paused":
    executor.resume_workflow()
```

### 4. Execution

**Target File Resolution:**
```python
target_file = executor.state.variables.get("target_file")
if target_file:
    target_path = Path(target_file)
    if target_path.is_absolute():
        try:
            target_file = str(target_path.relative_to(Path.cwd()))
        except ValueError:
            target_file = str(target_path)
```

**Workflow Execution:**
```python
# Use run_async_command helper for proper event loop management
# This avoids nested event loop issues and follows codebase best practices
final_state = run_async_command(executor.execute(
    workflow=None,  # Already loaded
    target_file=target_file,
    max_steps=max_steps,
))
```

### 5. Result Handling

**Success Cases:**
```python
if final_state.status == "completed":
    print("Workflow completed successfully!")
    print(f"Total steps completed: {len(final_state.completed_steps)}")
```

**Failure Cases:**
```python
elif final_state.status == "failed":
    print("Workflow failed")
    print(f"Error: {final_state.error or 'Unknown error'}")
    sys.exit(1)
```

**Incomplete Cases:**
```python
else:
    print(f"Workflow status: {final_state.status}")
    print(f"Current step: {final_state.current_step or 'N/A'}")
    print("\nWorkflow can be resumed again with: tapps-agents workflow resume")
```

## Error Handling

### Exception Types

1. **FileNotFoundError**
   - No workflow state found
   - Missing workflow file
   - Handled with clear error messages

2. **ValueError**
   - Invalid workflow state
   - Missing required data
   - Handled with validation messages

3. **Generic Exception**
   - Unexpected errors during execution
   - Full traceback printed for debugging

### Error Messages

All errors are printed to `stderr` with descriptive messages:
```python
print(f"Error: No workflow state found to resume", file=sys.stderr)
if workflow_id:
    print(f"  Workflow ID: {workflow_id}", file=sys.stderr)
print(f"  Details: {e}", file=sys.stderr)
sys.exit(1)
```

## State Management

### State Persistence

Workflow state is persisted in:
```
.tapps-agents/workflow-state/workflow-{workflow_id}.json
```

### State Structure

```json
{
  "workflow_id": "workflow-name-20250116-143022",
  "started_at": "2025-01-16T14:30:22",
  "current_step": "step2",
  "completed_steps": ["step1"],
  "skipped_steps": [],
  "artifacts": {...},
  "variables": {
    "_workflow_path": "workflows/presets/full-sdlc.yaml",
    "target_file": "src/main.py",
    "user_prompt": "..."
  },
  "status": "running",
  "error": null,
  "step_executions": [...]
}
```

### State Loading

**Advanced State Manager (if enabled):**
- Validates state integrity
- Migrates state format if needed
- Recovers from corruption

**Basic Loading (fallback):**
- Reads JSON directly
- Minimal validation
- Faster but less robust

## Workflow Execution

### Execute Method Signature

```python
async def execute(
    self,
    workflow: Workflow | None = None,
    target_file: str | None = None,
    max_steps: int = 50,
) -> WorkflowState:
```

**Parameters:**
- `workflow` - Workflow definition (None if already loaded)
- `target_file` - Target file for brownfield workflows
- `max_steps` - Maximum steps to execute (safety limit)

**Returns:**
- `WorkflowState` - Final workflow state after execution

### Execution Flow

1. **Initialize Execution**
   - Ensure workflow is loaded
   - Ensure state exists
   - Set target file

2. **Step Execution Loop**
   - Find ready steps (dependencies met)
   - Execute steps in parallel (if possible)
   - Process results
   - Update state
   - Save checkpoint

3. **Completion**
   - Mark workflow as completed/failed
   - Generate timeline
   - Cleanup background agents

## Testing

### Test Coverage

Comprehensive tests in `tests/unit/test_workflow_resume_command.py`:

1. **Success Cases**
   - Resume from last state
   - Resume with specific workflow ID
   - Resume paused workflow
   - Resume failed workflow
   - Resume with target file

2. **Edge Cases**
   - Already completed workflow
   - Missing state file
   - Missing workflow file
   - Validation disabled

3. **Error Cases**
   - Workflow fails during execution
   - Exception handling
   - Invalid state

### Running Tests

```bash
# Run all resume command tests
pytest tests/unit/test_workflow_resume_command.py -v

# Run specific test
pytest tests/unit/test_workflow_resume_command.py::TestWorkflowResumeCommand::test_resume_from_last_state_success -v
```

## CLI Usage

### Basic Usage

```bash
# Resume most recent workflow
tapps-agents workflow resume

# Resume specific workflow
tapps-agents workflow resume --workflow-id workflow-name-20250116-143022

# Resume with validation disabled
tapps-agents workflow resume --no-validate

# Resume with step limit
tapps-agents workflow resume --max-steps 10
```

### Command Options

- `--workflow-id <id>` - Specific workflow ID to resume
- `--validate` - Validate state integrity (default: True)
- `--no-validate` - Skip validation
- `--max-steps <n>` - Maximum steps to execute (default: 50)

## Related Components

### Workflow Executor

- **File:** `tapps_agents/workflow/executor.py`
- **Key Methods:**
  - `start()` - Initialize workflow
  - `execute()` - Run workflow steps
  - `load_last_state()` - Load persisted state
  - `save_state()` - Persist state
  - `resume_workflow()` - Resume paused workflow

### State Manager

- **File:** `tapps_agents/workflow/state_manager.py`
- **Key Methods:**
  - `load_state()` - Load state with validation
  - `save_state()` - Save state with metadata
  - `cleanup_old_states()` - Remove old states

### Workflow Parser

- **File:** `tapps_agents/workflow/parser.py`
- **Key Methods:**
  - `parse_file()` - Parse workflow YAML
  - Validates workflow schema

## Best Practices

1. **Always Validate State**
   - Use `--validate` (default) unless certain state is valid
   - Validation checks file existence, schema compatibility

2. **Use Specific Workflow ID**
   - Prevents resuming wrong workflow
   - Useful when multiple workflows exist

3. **Set Max Steps**
   - Prevents infinite loops
   - Useful for debugging
   - Default (50) is usually sufficient

4. **Handle Incomplete Workflows**
   - Check status after resume
   - Resume again if needed
   - Monitor progress

5. **Use run_async_command Helper**
   - Always use `run_async_command()` instead of `asyncio.run()` directly
   - Prevents nested event loop issues
   - Follows codebase best practices
   - Provides better error messages for event loop conflicts

## Troubleshooting

### Common Issues

1. **"No workflow state found"**
   - No workflow has been started
   - State directory was deleted
   - Wrong project directory

2. **"Could not load workflow state or workflow definition"**
   - Workflow file was moved/deleted
   - State references invalid path
   - Check `_workflow_path` in state

3. **"Workflow previously failed"**
   - Normal - workflow can be resumed
   - Previous error is shown
   - Status is reset to "running"

4. **"Max steps exceeded"**
   - Workflow is stuck in loop
   - Increase `--max-steps` or investigate

## Future Improvements

1. **Resume from Specific Step**
   - Allow resuming from any step, not just last checkpoint
   - Useful for debugging

2. **Resume with Modified State**
   - Allow editing state before resuming
   - Useful for recovery scenarios

3. **Resume Preview**
   - Show what will happen before resuming
   - List steps that will execute

4. **Better Error Recovery**
   - Automatic retry with backoff
   - Skip problematic steps
   - Partial completion handling

## Summary

The workflow resume command provides robust functionality for recovering from interruptions, failures, and pauses. The critical bug fix ensures that workflows can be properly resumed using the correct `execute()` method instead of the non-existent `run()` method. Comprehensive error handling, state validation, and testing ensure reliability and user experience.

