# Long-Duration Operations Guide

**Version:** 1.0.0  
**Date:** December 2025  
**Status:** ✅ Complete

---

## Overview

The Long-Duration Operations system enables agents to handle tasks that run for 30+ hours with automatic durability guarantees, failure recovery, and progress tracking. This system provides:

- **Durability Guarantees**: Configurable checkpoint intervals (2-10 minutes)
- **Automatic Checkpointing**: Background thread creates checkpoints at regular intervals
- **Failure Recovery**: Automatic recovery from crashes, timeouts, and resource exhaustion
- **Progress Tracking**: Real-time progress monitoring with velocity calculation
- **Artifact Backup**: Automatic backup of generated artifacts for HIGH durability
- **Hardware-Aware**: Adapts checkpoint frequency based on hardware profile

---

## Architecture

### Components

1. **LongDurationManager** - Orchestrates long-duration operations
2. **DurabilityGuarantee** - Manages checkpoint intervals and artifact backup
3. **FailureRecovery** - Handles failure detection and recovery
4. **ProgressTracker** - Tracks progress and calculates velocity

### Integration Points

- **SessionManager**: Manages agent sessions
- **CheckpointManager**: Creates and stores checkpoints
- **ResourceAwareExecutor**: Monitors resources and applies optimizations
- **HardwareProfiler**: Detects hardware profile for adaptive behavior

---

## Durability Levels

The system supports three durability levels with different checkpoint intervals:

| Durability Level | Checkpoint Interval | Artifact Backup | Use Case |
|-----------------|---------------------|-----------------|----------|
| **BASIC** | 10 minutes | No | Low-risk tasks, development |
| **STANDARD** | 5 minutes | No | Production tasks, moderate risk |
| **HIGH** | 2 minutes | Yes | Critical tasks, high-value work |

### Hardware-Aware Intervals

The system automatically adjusts intervals based on hardware:

- **NUC**: Intervals are 50% longer (more conservative)
- **Workstation/Server**: Uses configured intervals
- **Development**: Uses configured intervals

---

## Usage

### Basic Long-Duration Task

```python
from tapps_agents.core import (
    LongDurationManager,
    SessionManager,
    CheckpointManager,
    DurabilityLevel
)

# Initialize components
session_manager = SessionManager()
checkpoint_manager = CheckpointManager()
long_duration_manager = LongDurationManager(
    session_manager=session_manager,
    checkpoint_manager=checkpoint_manager
)

# Start a long-duration task
task_id = long_duration_manager.start_long_duration_task(
    task_id="my-long-task",
    agent_id="architect",
    command="design_system",
    durability_level=DurabilityLevel.STANDARD,
    initial_context={"project": "my-project"}
)

# Update progress during execution
long_duration_manager.update_progress(
    task_id=task_id,
    progress=0.25,  # 25% complete
    current_step="Designing architecture",
    steps_completed=1,
    total_steps=4
)

# Continue with more progress updates...
long_duration_manager.update_progress(
    task_id=task_id,
    progress=0.5,
    current_step="Implementing core components",
    steps_completed=2,
    total_steps=4
)

# Complete the task
long_duration_manager.complete_task(
    task_id=task_id,
    final_context={"result": "system_designed.md"}
)
```

### Using Context Manager

```python
from tapps_agents.core import LongDurationManager, DurabilityLevel

with LongDurationManager(
    session_manager=session_manager,
    checkpoint_manager=checkpoint_manager
) as manager:
    # Start task
    task_id = manager.start_long_duration_task(
        task_id="my-task",
        agent_id="architect",
        command="design",
        durability_level=DurabilityLevel.HIGH
    )
    
    # Do work...
    for i in range(100):
        # Update progress
        manager.update_progress(
            task_id=task_id,
            progress=i / 100.0,
            current_step=f"Processing item {i}"
        )
        
        # Do actual work...
        process_item(i)
    
    # Complete task
    manager.complete_task(task_id=task_id)
# Context manager automatically stops checkpoint thread
```

### Failure Recovery

```python
from tapps_agents.core import LongDurationManager

# Simulate a failure
try:
    # Long-running task...
    long_duration_manager.update_progress(
        task_id=task_id,
        progress=0.3,
        current_step="Step 3"
    )
    
    # Simulate crash
    raise Exception("Unexpected error")
    
except Exception as e:
    # Record failure
    long_duration_manager.handle_failure(
        task_id=task_id,
        failure_type="crash",
        error_message=str(e),
        stack_trace=traceback.format_exc()
    )

# Recover from checkpoint
recovered_checkpoint = long_duration_manager.recover_from_failure(task_id)
if recovered_checkpoint:
    print(f"Recovered from checkpoint at {recovered_checkpoint.progress * 100}%")
    print(f"Last step: {recovered_checkpoint.context.get('current_step')}")
    
    # Resume from checkpoint
    # ... continue from recovered state
```

### Progress Tracking

```python
# Get progress snapshot
snapshot = long_duration_manager.get_progress_snapshot(task_id)
print(f"Progress: {snapshot.progress * 100}%")
print(f"Current Step: {snapshot.current_step}")
print(f"Steps Completed: {snapshot.steps_completed}/{snapshot.total_steps}")
print(f"Elapsed Time: {snapshot.elapsed_time}")
print(f"Estimated Remaining: {snapshot.estimated_remaining}")

# Get progress history
history = long_duration_manager.get_progress_history(task_id)
for entry in history:
    print(f"{entry.timestamp}: {entry.progress * 100}% - {entry.current_step}")

# Calculate velocity
velocity = long_duration_manager.calculate_progress_velocity(task_id)
print(f"Progress Velocity: {velocity.progress_per_hour}% per hour")
print(f"Estimated Completion: {velocity.estimated_completion_time}")
```

### Multiple Concurrent Tasks

```python
# Start multiple long-duration tasks
task1 = long_duration_manager.start_long_duration_task(
    task_id="task-1",
    agent_id="architect",
    command="design",
    durability_level=DurabilityLevel.STANDARD
)

task2 = long_duration_manager.start_long_duration_task(
    task_id="task-2",
    agent_id="reviewer",
    command="review",
    durability_level=DurabilityLevel.BASIC
)

# Update progress for each task
long_duration_manager.update_progress(
    task_id=task1,
    progress=0.5,
    current_step="Task 1 - Step 2"
)

long_duration_manager.update_progress(
    task_id=task2,
    progress=0.3,
    current_step="Task 2 - Step 1"
)

# List all active tasks
active_tasks = long_duration_manager.list_active_tasks()
for task_id in active_tasks:
    snapshot = long_duration_manager.get_progress_snapshot(task_id)
    print(f"{task_id}: {snapshot.progress * 100}%")
```

---

## Integration with Agents

### Architect Agent Example

```python
from tapps_agents.agents.architect.agent import ArchitectAgent
from tapps_agents.core import LongDurationManager, DurabilityLevel

class LongDurationArchitectAgent(ArchitectAgent):
    """Architect agent with long-duration support."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.long_duration_manager = LongDurationManager(
            session_manager=self.session_manager,
            checkpoint_manager=self.checkpoint_manager
        )
    
    async def design_system_long(self, project_path: str):
        """Design system with long-duration support."""
        task_id = self.long_duration_manager.start_long_duration_task(
            task_id=f"design-{project_path}",
            agent_id=self.agent_id,
            command="design_system",
            durability_level=DurabilityLevel.HIGH,
            initial_context={"project_path": project_path}
        )
        
        try:
            # Phase 1: Analysis
            self.long_duration_manager.update_progress(
                task_id=task_id,
                progress=0.1,
                current_step="Analyzing project structure",
                steps_completed=1,
                total_steps=10
            )
            analysis = await self.analyze_project(project_path)
            
            # Phase 2: Design
            self.long_duration_manager.update_progress(
                task_id=task_id,
                progress=0.3,
                current_step="Designing architecture",
                steps_completed=3,
                total_steps=10
            )
            design = await self.create_design(analysis)
            
            # Continue with more phases...
            
            # Complete
            self.long_duration_manager.complete_task(
                task_id=task_id,
                final_context={"design": design}
            )
            
        except Exception as e:
            self.long_duration_manager.handle_failure(
                task_id=task_id,
                failure_type="error",
                error_message=str(e)
            )
            raise
```

### Reviewer Agent Example

```python
from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tapps_agents.core import LongDurationManager, DurabilityLevel

class LongDurationReviewerAgent(ReviewerAgent):
    """Reviewer agent with long-duration support."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.long_duration_manager = LongDurationManager(
            session_manager=self.session_manager,
            checkpoint_manager=self.checkpoint_manager
        )
    
    async def review_large_codebase(self, codebase_path: str):
        """Review large codebase with progress tracking."""
        task_id = self.long_duration_manager.start_long_duration_task(
            task_id=f"review-{codebase_path}",
            agent_id=self.agent_id,
            command="review",
            durability_level=DurabilityLevel.STANDARD
        )
        
        files = list_files(codebase_path)
        total_files = len(files)
        
        for i, file_path in enumerate(files):
            # Update progress
            self.long_duration_manager.update_progress(
                task_id=task_id,
                progress=i / total_files,
                current_step=f"Reviewing {file_path}",
                steps_completed=i,
                total_steps=total_files
            )
            
            # Review file
            await self.review_file(file_path)
        
        # Complete
        self.long_duration_manager.complete_task(task_id=task_id)
```

---

## Best Practices

### 1. Choose Appropriate Durability Level

- **BASIC**: Use for development, testing, low-risk tasks
- **STANDARD**: Use for production tasks, moderate value
- **HIGH**: Use for critical tasks, high-value work, irreplaceable results

### 2. Update Progress Regularly

```python
# Good: Update progress at meaningful milestones
for phase in phases:
    result = process_phase(phase)
    manager.update_progress(
        task_id=task_id,
        progress=calculate_progress(phase),
        current_step=f"Completed {phase.name}"
    )

# Bad: Update progress too frequently (wastes resources)
for item in items:
    manager.update_progress(...)  # Too frequent!
    process_item(item)
```

### 3. Handle Failures Gracefully

```python
try:
    # Long-running work...
    pass
except Exception as e:
    # Always record failures
    manager.handle_failure(
        task_id=task_id,
        failure_type="error",
        error_message=str(e),
        stack_trace=traceback.format_exc()
    )
    
    # Attempt recovery
    checkpoint = manager.recover_from_failure(task_id)
    if checkpoint:
        # Resume from checkpoint
        resume_from_checkpoint(checkpoint)
    else:
        # No checkpoint available, start over
        raise
```

### 4. Use Context Manager for Cleanup

```python
# Good: Automatic cleanup
with LongDurationManager(...) as manager:
    # Work...
    pass

# Bad: Manual cleanup (easy to forget)
manager = LongDurationManager(...)
try:
    # Work...
    pass
finally:
    manager.stop_checkpoint_thread()  # Easy to forget!
```

### 5. Monitor Progress Velocity

```python
# Check if task is progressing too slowly
velocity = manager.calculate_progress_velocity(task_id)
if velocity.progress_per_hour < 1.0:  # Less than 1% per hour
    logger.warning(f"Task {task_id} is progressing slowly")
    # Consider pausing or optimizing
```

---

## Troubleshooting

### Checkpoint Not Created

**Problem**: Checkpoints are not being created automatically.

**Solutions**:
1. Ensure `start_long_duration_task()` was called
2. Check that enough time has passed since last checkpoint (based on durability level)
3. Verify checkpoint manager is properly initialized
4. Check logs for errors

### Recovery Fails

**Problem**: Cannot recover from failure.

**Solutions**:
1. Verify checkpoint exists: `checkpoint_manager.load_checkpoint(task_id)`
2. Check checkpoint integrity: `checkpoint.validate()`
3. Ensure artifacts exist if using HIGH durability
4. Check failure history: `manager.get_failure_history(task_id)`

### Progress Not Updating

**Problem**: Progress snapshot shows old values.

**Solutions**:
1. Ensure `update_progress()` is being called
2. Verify task_id matches the one used in `start_long_duration_task()`
3. Check for exceptions in progress tracking
4. Verify session is active: `session_manager.get_session(session_id)`

### High Resource Usage

**Problem**: Long-duration operations consume too many resources.

**Solutions**:
1. Use BASIC durability level (less frequent checkpoints)
2. Reduce progress update frequency
3. Use ResourceAwareExecutor for automatic resource management
4. Monitor with ResourceMonitor and adjust thresholds

---

## Performance Considerations

### Checkpoint Overhead

- **BASIC**: ~0.1% overhead (10 min intervals)
- **STANDARD**: ~0.2% overhead (5 min intervals)
- **HIGH**: ~0.5% overhead (2 min intervals + artifact backup)

### Storage Requirements

- **Per Checkpoint**: ~10-50 KB (depends on context size)
- **Per Task (30 hours)**: 
  - BASIC: ~180 checkpoints = ~3-9 MB
  - STANDARD: ~360 checkpoints = ~6-18 MB
  - HIGH: ~900 checkpoints + artifacts = ~20-50 MB

### Memory Usage

- **LongDurationManager**: ~5-10 MB
- **Progress History**: ~1 MB per 1000 entries
- **Failure History**: ~100 KB per 100 failures

---

## API Reference

### LongDurationManager

```python
class LongDurationManager:
    def start_long_duration_task(
        self,
        task_id: str,
        agent_id: str,
        command: str,
        durability_level: DurabilityLevel = DurabilityLevel.STANDARD,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str
    
    def update_progress(
        self,
        task_id: str,
        progress: float,
        current_step: Optional[str] = None,
        steps_completed: Optional[int] = None,
        total_steps: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    )
    
    def complete_task(
        self,
        task_id: str,
        final_context: Optional[Dict[str, Any]] = None
    )
    
    def handle_failure(
        self,
        task_id: str,
        failure_type: str,
        error_message: str,
        stack_trace: Optional[str] = None
    )
    
    def recover_from_failure(
        self,
        task_id: str
    ) -> Optional[TaskCheckpoint]
    
    def get_progress_snapshot(
        self,
        task_id: str
    ) -> Optional[ProgressSnapshot]
    
    def get_progress_history(
        self,
        task_id: str,
        limit: Optional[int] = None
    ) -> List[ProgressSnapshot]
    
    def calculate_progress_velocity(
        self,
        task_id: str
    ) -> Optional[ProgressVelocity]
    
    def list_active_tasks(self) -> List[str]
```

### DurabilityLevel

```python
class DurabilityLevel(Enum):
    BASIC = "basic"      # 10 minute intervals
    STANDARD = "standard"  # 5 minute intervals
    HIGH = "high"        # 2 minute intervals + artifact backup
```

### ProgressSnapshot

```python
@dataclass
class ProgressSnapshot:
    timestamp: datetime
    progress: float  # 0.0 to 1.0
    current_step: Optional[str]
    steps_completed: Optional[int]
    total_steps: Optional[int]
    elapsed_time: timedelta
    estimated_remaining: Optional[timedelta]
```

---

## Examples

See `examples/long_duration_example.py` for a complete working example.

---

## Related Documentation

- [Checkpoint and Resume Guide](CHECKPOINT_RESUME_GUIDE.md) - Basic checkpointing
- [Session Management](ARCHITECTURE.md#session-management) - Session lifecycle
- [Resource-Aware Execution](ARCHITECTURE.md#resource-aware-execution) - Resource management
- [Hardware Recommendations](HARDWARE_RECOMMENDATIONS.md) - Hardware profiles

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [API Reference](#api-reference)
3. See examples in `examples/long_duration_example.py`
4. Check logs in `.tapps-agents/logs/`

