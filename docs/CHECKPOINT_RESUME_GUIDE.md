# Checkpoint and Resume Guide

**Version:** 2.0.2  
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

## Hardware-Aware Checkpointing

The system automatically adjusts checkpoint frequency based on hardware profile:

| Hardware Profile | Checkpoint Interval | Compression |
|-----------------|---------------------|-------------|
| NUC | 30 seconds | Enabled |
| Development | 60 seconds | Disabled |
| Workstation | 120 seconds | Disabled |
| Server | 60 seconds | Disabled |

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

## See Also

- [Task State Management](../tapps_agents/core/task_state.py)
- [Checkpoint Manager](../tapps_agents/core/checkpoint_manager.py)
- [Resume Handler](../tapps_agents/core/resume_handler.py)
- [Hardware Profiling](../tapps_agents/core/hardware_profiler.py)

