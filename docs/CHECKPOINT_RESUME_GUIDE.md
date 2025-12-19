# Checkpoint and Resume Guide

**Version:** 2.0.6  
**Date:** January 2026  
**Status:** ✅ Complete

---

## Overview

The Checkpoint and Resume system enables tasks to be saved and resumed, critical for long-duration operations. This system provides:

- **Automatic Checkpointing**: Hardware-aware checkpoint frequency
- **State Persistence**: Complete task state saved to disk
- **Resume Capability**: Seamless task resumption from checkpoints
- **Integrity Validation**: Checksum verification for checkpoint data
- **Artifact Tracking**: Validates generated files exist before resuming

---

## Architecture

### Components

1. **TaskStateManager** - Manages task state transitions
2. **CheckpointManager** - Creates and manages checkpoints
3. **CheckpointStorage** - Handles checkpoint persistence
4. **ResumeHandler** - Handles task resumption

### State Machine

```
INITIALIZED → RUNNING → [CHECKPOINT] → RUNNING → COMPLETED
                ↓
            PAUSED → RESUMED → RUNNING
                ↓
            FAILED → RETRY → RUNNING
```

---

## Configuration Management

The state persistence system supports comprehensive configuration through `.tapps-agents/config.yaml`:

### Configuration Schema

```yaml
workflow:
  state_persistence:
    enabled: true
    storage_location: ".tapps-agents/workflow-state"
    format: "json"  # json or json_gzip
    compression: false
    checkpoint:
      enabled: true
      mode: "every_step"  # every_step, every_n_steps, on_gates, time_based, manual
      interval: 1  # For every_n_steps (step count) or time_based (seconds)
    cleanup:
      enabled: true
      retention_days: 30  # Delete states older than N days (null = no limit)
      max_size_mb: 1000  # Maximum total state size in MB (null = no limit)
      cleanup_schedule: "daily"  # daily, weekly, monthly, on_startup, manual
      keep_latest: 10  # Always keep the N most recent states
```

### Checkpoint Frequency Modes

- **`every_step`**: Checkpoint after every step completion (default)
- **`every_n_steps`**: Checkpoint every N steps (configure `interval`)
- **`on_gates`**: Checkpoint only at gate evaluation steps (reviewer steps)
- **`time_based`**: Checkpoint every N seconds (configure `interval`)
- **`manual`**: Only checkpoint when explicitly requested

### Cleanup Policies

- **Retention Policy**: Automatically delete states older than specified days
- **Size Limit Policy**: Delete oldest states when total size exceeds limit
- **Keep Latest**: Always preserve the N most recent states regardless of policies
- **Cleanup Schedule**: Automatic cleanup on startup, daily, weekly, or monthly

### Runtime Configuration Reload

Configuration can be reloaded at runtime without restarting workflows:

```python
from tapps_agents.workflow.state_persistence_config import StatePersistenceConfigManager

config_manager = StatePersistenceConfigManager()
success = config_manager.reload_configuration()
```

## Hardware-Aware Checkpointing

The system automatically adjusts checkpoint frequency based on hardware profile (legacy behavior, now configurable):

| Hardware Profile | Checkpoint Interval | Compression |
|-----------------|---------------------|-------------|
| NUC | 30 seconds | Enabled |
| Development | 60 seconds | Disabled |
| Workstation | 120 seconds | Disabled |
| Server | 60 seconds | Disabled |

**Note**: Configuration-based checkpointing (above) takes precedence over hardware-aware defaults.

### Configuration Examples

#### Example 1: Checkpoint Every 5 Steps

```yaml
workflow:
  state_persistence:
    checkpoint:
      mode: "every_n_steps"
      interval: 5
```

#### Example 2: Time-Based Checkpointing (Every 5 Minutes)

```yaml
workflow:
  state_persistence:
    checkpoint:
      mode: "time_based"
      interval: 300  # 5 minutes in seconds
```

#### Example 3: Cleanup Policy with Retention

```yaml
workflow:
  state_persistence:
    cleanup:
      enabled: true
      retention_days: 7  # Keep states for 7 days
      max_size_mb: 500  # Max 500 MB total
      keep_latest: 5  # Always keep 5 most recent
      cleanup_schedule: "daily"
```

#### Example 4: Manual Checkpointing Only

```yaml
workflow:
  state_persistence:
    checkpoint:
      mode: "manual"
      enabled: true
```

### Configuration Management CLI

The configuration manager provides utilities for managing state persistence:

```python
from tapps_agents.workflow.state_persistence_config import StatePersistenceConfigManager

# Initialize manager
config_manager = StatePersistenceConfigManager()

# Get configuration summary
summary = config_manager.get_config_summary()
print(summary)

# Execute cleanup manually
cleanup_result = config_manager.execute_cleanup()
print(f"Deleted {cleanup_result['deleted']} files, freed {cleanup_result['freed_mb']} MB")

# Reload configuration
success = config_manager.reload_configuration()
```

---

## Usage

### Basic Checkpointing

```python
from tapps_agents.core.checkpoint_manager import CheckpointManager
from tapps_agents.core.task_state import TaskState, TaskStateManager

# Initialize checkpoint manager
checkpoint_manager = CheckpointManager()

# Create state manager
state_manager = TaskStateManager("my-task")
state_manager.transition(TaskState.RUNNING)

# Create checkpoint
checkpoint = checkpoint_manager.create_checkpoint(
    task_id="my-task",
    agent_id="architect",
    command="design_system",
    state_manager=state_manager,
    progress=0.5,  # 50% complete
    context={"design_doc": "architecture.md"},
    artifacts=["architecture.md", "diagrams/"]
)
```

### Automatic Checkpointing

```python
import time
from tapps_agents.core.checkpoint_manager import CheckpointManager
from tapps_agents.core.task_state import TaskState, TaskStateManager

checkpoint_manager = CheckpointManager()
state_manager = TaskStateManager("long-task")
state_manager.transition(TaskState.RUNNING)

# Long-running task loop
for i in range(100):
    # Do work...
    
    # Check if checkpoint needed
    if checkpoint_manager.should_checkpoint("long-task"):
        checkpoint_manager.create_checkpoint(
            task_id="long-task",
            agent_id="implementer",
            command="implement_feature",
            state_manager=state_manager,
            progress=i / 100.0,
            context={"current_step": i}
        )
    
    time.sleep(1)
```

### Resuming from Checkpoint

```python
from tapps_agents.core.resume_handler import ResumeHandler
from tapps_agents.core.checkpoint_manager import CheckpointManager

# Initialize resume handler
checkpoint_manager = CheckpointManager()
resume_handler = ResumeHandler(checkpoint_manager=checkpoint_manager)

# Check if task can be resumed
can_resume, reason = resume_handler.can_resume("my-task")
if can_resume:
    # Prepare resume
    resume_data = resume_handler.prepare_resume("my-task")
    
    # Get restored context
    context = resume_data["context"]
    progress = resume_data["progress"]
    state_manager = resume_data["state_manager"]
    
    # Continue task execution with restored context
    print(f"Resuming from {progress:.1%} progress")
```

### Listing Resumable Tasks

```python
from tapps_agents.core.resume_handler import ResumeHandler

resume_handler = ResumeHandler()

# List all resumable tasks
resumable_tasks = resume_handler.list_resumable_tasks()

for task in resumable_tasks:
    print(f"Task: {task['task_id']}")
    print(f"  Agent: {task['agent_id']}")
    print(f"  Progress: {task['progress']:.1%}")
    print(f"  State: {task['state']}")
```

---

## Integration with Agents

### Adding Checkpointing to an Agent

```python
from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.core.checkpoint_manager import CheckpointManager
from tapps_agents.core.task_state import TaskState, TaskStateManager

class MyAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checkpoint_manager = CheckpointManager()
        self.state_manager = None
        self.current_task_id = None
    
    async def run(self, command: str, **kwargs):
        task_id = kwargs.get("task_id", f"task-{uuid.uuid4()}")
        self.current_task_id = task_id
        
        # Initialize state
        self.state_manager = TaskStateManager(task_id)
        self.state_manager.transition(TaskState.RUNNING)
        
        try:
            # Check for existing checkpoint
            checkpoint = self.checkpoint_manager.load_checkpoint(task_id)
            if checkpoint:
                # Resume from checkpoint
                resume_handler = ResumeHandler(
                    checkpoint_manager=self.checkpoint_manager
                )
                resume_data = resume_handler.prepare_resume(task_id)
                context = resume_data["context"]
                progress = resume_data["progress"]
                
                # Restore context
                self.context.update(context)
            
            # Execute task with checkpointing
            result = await self._execute_with_checkpointing(command, **kwargs)
            
            # Mark complete
            self.state_manager.transition(TaskState.COMPLETED, "Task completed")
            return result
            
        except Exception as e:
            self.state_manager.transition(TaskState.FAILED, str(e))
            raise
    
    async def _execute_with_checkpointing(self, command: str, **kwargs):
        """Execute with automatic checkpointing."""
        # Your task execution logic here
        # Periodically check if checkpoint needed
        if self.checkpoint_manager.should_checkpoint(self.current_task_id):
            self.checkpoint_manager.create_checkpoint(
                task_id=self.current_task_id,
                agent_id=self.agent_id,
                command=command,
                state_manager=self.state_manager,
                progress=self._calculate_progress(),
                context=self.context.copy(),
                artifacts=self._get_artifacts()
            )
```

---

## Checkpoint Data Structure

### TaskCheckpoint

```python
@dataclass
class TaskCheckpoint:
    task_id: str                    # Unique task identifier
    agent_id: str                   # Agent that created checkpoint
    command: str                   # Command being executed
    state: str                     # TaskState value
    progress: float                # Progress (0.0 to 1.0)
    checkpoint_time: datetime       # When checkpoint was created
    context: Dict[str, Any]        # Agent context
    artifacts: List[str]           # Generated file paths
    metadata: Dict[str, Any]       # Additional metadata
    checksum: Optional[str]       # Integrity checksum
```

---

## Best Practices

### 1. Checkpoint Frequency

- **Long Tasks**: Checkpoint every 30-60 seconds
- **Short Tasks**: Checkpoint at major milestones
- **Critical Operations**: Checkpoint before risky operations

### 2. Context Management

- Store only essential context data
- Avoid storing large objects in context
- Use file paths for large data, not in-memory objects

### 3. Artifact Tracking

- Track all generated files in `artifacts` list
- Use relative paths for portability
- Validate artifacts exist before resuming

### 4. Error Handling

- Always validate checkpoint integrity before resuming
- Handle missing artifacts gracefully
- Provide clear error messages for resume failures

---

## CLI Commands (Future)

Future CLI commands for checkpoint management:

```bash
# List all checkpoints
tapps checkpoint list

# Show checkpoint details
tapps checkpoint show <task-id>

# Resume from checkpoint
tapps checkpoint resume <task-id>

# Delete checkpoint
tapps checkpoint delete <task-id>
```

---

## Examples

### Example 1: Long-Running Implementation Task

```python
from tapps_agents.core.checkpoint_manager import CheckpointManager
from tapps_agents.core.task_state import TaskState, TaskStateManager

checkpoint_manager = CheckpointManager()
state_manager = TaskStateManager("implement-feature-123")
state_manager.transition(TaskState.RUNNING)

files_to_implement = ["file1.py", "file2.py", "file3.py"]
implemented_files = []

for i, file in enumerate(files_to_implement):
    # Implement file...
    implemented_files.append(file)
    
    # Checkpoint after each file
    checkpoint_manager.create_checkpoint(
        task_id="implement-feature-123",
        agent_id="implementer",
        command="implement_files",
        state_manager=state_manager,
        progress=(i + 1) / len(files_to_implement),
        context={"implemented_files": implemented_files},
        artifacts=implemented_files
    )
```

### Example 2: Resuming After Interruption

```python
from tapps_agents.core.resume_handler import ResumeHandler

resume_handler = ResumeHandler()

# Check if task can be resumed
can_resume, reason = resume_handler.can_resume("implement-feature-123")

if can_resume:
    # Prepare resume
    resume_data = resume_handler.prepare_resume("implement-feature-123")
    
    # Get context
    context = resume_data["context"]
    implemented_files = context.get("implemented_files", [])
    
    # Continue from where we left off
    remaining_files = [f for f in files_to_implement if f not in implemented_files]
    # Implement remaining files...
else:
    print(f"Cannot resume: {reason}")
```

---

## Troubleshooting

### Checkpoint Not Found

**Problem**: `can_resume()` returns `False` with "No checkpoint found"

**Solution**: 
- Verify task_id matches the checkpoint
- Check checkpoint storage directory (default: `.tapps-agents/checkpoints`)
- List checkpoints: `checkpoint_manager.list_checkpoints()`

### Integrity Check Failed

**Problem**: Checkpoint validation fails

**Solution**:
- Checkpoint may be corrupted
- Delete and recreate checkpoint
- Verify disk space and permissions

### Missing Artifacts

**Problem**: Cannot resume due to missing artifacts

**Solution**:
- Verify artifact paths are correct
- Check if files were moved or deleted
- Use absolute paths or ensure project_root is set correctly

### Workflow State Not Persisting

**Problem**: Workflow state is not being saved

**Solution**:
- Verify state persistence is enabled in configuration:
  ```yaml
  workflow:
    state_persistence:
      enabled: true
  ```
- Check storage location is writable: `.tapps-agents/workflow-state/`
- Review logs for save errors
- Ensure checkpoint manager is configured correctly

### Cannot Resume Workflow

**Problem**: Workflow cannot be resumed from saved state

**Solution**:
- Verify state file exists: Check `.tapps-agents/workflow-state/` directory
- Load state manually to check for errors:
  ```python
  from tapps_agents.workflow.state_manager import AdvancedStateManager
  state_manager = AdvancedStateManager(storage_dir)
  state, metadata = state_manager.load_state(workflow_id="your-workflow-id")
  ```
- Check state version compatibility
- Verify workflow YAML file still exists and is valid

### State File Corruption

**Problem**: State file is corrupted and cannot be loaded

**Solution**:
- Check for backup in `history/` subdirectory
- System automatically attempts recovery from history
- If recovery fails, check logs for specific error
- Consider starting workflow from beginning if state is unrecoverable

### Checkpoint Frequency Not Working

**Problem**: Checkpoints are not being created at expected frequency

**Solution**:
- Verify checkpoint configuration:
  ```yaml
  workflow:
    state_persistence:
      checkpoint:
        enabled: true
        mode: "every_step"  # or your desired mode
  ```
- Check if checkpoint manager is initialized with correct config
- Review workflow executor logs for checkpoint decisions
- Ensure `should_checkpoint()` is being called after each step

### State Cleanup Not Running

**Problem**: Old state files are not being cleaned up

**Solution**:
- Verify cleanup is enabled:
  ```yaml
  workflow:
    state_persistence:
      cleanup:
        enabled: true
        cleanup_schedule: "daily"  # or "on_startup", "weekly", etc.
  ```
- Manually trigger cleanup:
  ```python
  from tapps_agents.workflow.state_persistence_config import StatePersistenceConfigManager
  config_manager = StatePersistenceConfigManager()
  result = config_manager.execute_cleanup()
  ```
- Check cleanup policies (retention_days, max_size_mb, keep_latest)

### State Version Migration Issues

**Problem**: Errors during state version migration

**Solution**:
- Check state file version in metadata
- Verify migration logic supports your state version
- Review migration logs for specific errors
- If migration fails, manually update state file format or start fresh

---

## Performance Considerations

### Storage

- Checkpoints are stored as JSON files
- NUC devices use gzip compression
- Typical checkpoint size: 1-10 KB

### Overhead

- Checkpoint creation: <10ms
- Checkpoint loading: <5ms
- Resume preparation: <50ms

### Best Practices

- Don't checkpoint too frequently (< 10 seconds)
- Limit context size (< 100 KB)
- Clean up old checkpoints periodically

---

## State Inspection and Debugging

### Inspecting State Files

You can inspect workflow state files directly:

```python
from tapps_agents.workflow.state_manager import AdvancedStateManager
from pathlib import Path

state_manager = AdvancedStateManager(Path(".tapps-agents/workflow-state"))

# List all states
states = state_manager.list_states()
for state_info in states:
    print(f"Workflow: {state_info['workflow_id']}")
    print(f"Saved at: {state_info['saved_at']}")
    print(f"Version: {state_info['version']}")

# Load specific state
state, metadata = state_manager.load_state(workflow_id="your-workflow-id")
print(f"Current step: {state.current_step}")
print(f"Completed steps: {state.completed_steps}")
print(f"Status: {state.status}")
print(f"Variables: {state.variables}")
```

### Debugging State Issues

1. **Check State File Location**:
   ```python
   from tapps_agents.workflow.state_persistence_config import StatePersistenceConfigManager
   config_manager = StatePersistenceConfigManager()
   storage_path = config_manager.get_storage_path()
   print(f"State storage: {storage_path}")
   ```

2. **Validate State Integrity**:
   ```python
   from tapps_agents.workflow.state_manager import StateValidator
   
   # Load state data
   import json
   with open(state_file, 'r') as f:
       state_data = json.load(f)
   
   # Validate
   is_valid, error = StateValidator.validate_state(state_data)
   if not is_valid:
       print(f"State validation failed: {error}")
   ```

3. **Check Configuration**:
   ```python
   config_manager = StatePersistenceConfigManager()
   summary = config_manager.get_config_summary()
   print(json.dumps(summary, indent=2))
   ```

### Common State File Locations

- **Default**: `.tapps-agents/workflow-state/`
- **Configurable**: Set via `workflow.state_persistence.storage_location` in config.yaml
- **History**: `.tapps-agents/workflow-state/history/`
- **Metadata**: `.tapps-agents/workflow-state/{workflow_id}.meta.json`
- **Latest Pointer**: `.tapps-agents/workflow-state/last.json`

## Use Cases

### Use Case 1: Long-Running Workflow with Periodic Checkpoints

For workflows that take hours to complete:

```yaml
workflow:
  state_persistence:
    checkpoint:
      mode: "time_based"
      interval: 1800  # Checkpoint every 30 minutes
    cleanup:
      retention_days: 7  # Keep states for 7 days
```

### Use Case 2: Critical Workflow with Maximum Safety

For workflows where you can't afford to lose progress:

```yaml
workflow:
  state_persistence:
    checkpoint:
      mode: "every_step"  # Checkpoint after every step
    cleanup:
      keep_latest: 10  # Always keep 10 most recent states
```

### Use Case 3: High-Performance Workflow with Minimal Checkpoints

For workflows where performance is critical:

```yaml
workflow:
  state_persistence:
    checkpoint:
      mode: "on_gates"  # Only checkpoint at gate steps (reviewer)
    cleanup:
      max_size_mb: 100  # Limit total state storage to 100MB
```

### Use Case 4: Development Workflow with Manual Checkpoints

For development/testing where you want full control:

```yaml
workflow:
  state_persistence:
    checkpoint:
      mode: "manual"  # Only checkpoint when explicitly requested
    cleanup:
      cleanup_schedule: "manual"  # Manual cleanup only
```

## See Also

- [State Persistence Developer Guide](STATE_PERSISTENCE_DEVELOPER_GUIDE.md) - Technical documentation
- [Task State Management](../tapps_agents/core/task_state.py)
- [Checkpoint Manager](../tapps_agents/core/checkpoint_manager.py)
- [Resume Handler](../tapps_agents/core/resume_handler.py)
- [Hardware Profiling](../tapps_agents/core/hardware_profiler.py)

