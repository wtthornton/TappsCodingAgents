# Workflow Monitoring Pattern for E2E Tests

This document describes the reusable workflow monitoring pattern for e2e tests.

## Overview

The workflow monitoring system provides event-driven, real-time monitoring of workflow execution without polling. It uses the observer pattern to subscribe to workflow events and track progress, activity, and validation results.

## Key Components

### 1. WorkflowActivityMonitor

The main monitoring class that tracks workflow execution:

- **Event-driven**: Automatically receives workflow events via observer pattern
- **Progress tracking**: Monitors step completion, progress percentage
- **Hang detection**: Detects when workflow appears stuck
- **Activity snapshots**: Captures state at key points

### 2. Pytest Fixtures

Reusable fixtures for easy test setup:

- `workflow_monitor`: Automatically sets up monitoring for any test
- `workflow_monitoring_config`: Configurable monitoring settings
- `workflow_observers`: Register custom observers

### 3. Base Classes

- `BaseWorkflowObserver`: Base class for creating custom observers
- `SDLCPhaseValidator`: Validator for SDLC phase artifacts

## Usage Examples

### Basic Usage with Fixture

```python
@pytest.mark.e2e_workflow
async def test_my_workflow(workflow_runner, workflow_monitor):
    state, results = await workflow_runner.run_workflow(workflow_path)
    
    # Monitor automatically tracked all events
    assert workflow_monitor.get_activity_summary()["steps_completed"] > 0
```

### Custom Monitoring Configuration

```python
@pytest.mark.monitoring_config(
    max_seconds_without_activity=120,
    max_seconds_without_progress=240
)
@pytest.mark.e2e_workflow
async def test_with_custom_config(workflow_runner, workflow_monitor):
    state, results = await workflow_runner.run_workflow(workflow_path)
    # Uses custom hang detection settings
```

### Custom Observer

```python
from tests.e2e.fixtures.workflow_monitor import BaseWorkflowObserver
from tapps_agents.workflow.event_log import WorkflowEvent

class MyCustomObserver(BaseWorkflowObserver):
    def on_step_complete(self, event: WorkflowEvent) -> None:
        if event.step_id == "implementation":
            # Custom validation logic
            pass

@pytest.mark.e2e_workflow
async def test_with_custom_observer(workflow_runner, workflow_observers):
    custom_observer = MyCustomObserver()
    workflow_observers.append(custom_observer)
    
    state, results = await workflow_runner.run_workflow(workflow_path)
    
    # Access custom observer data
    assert len(custom_observer.get_observed_events()) > 0
```

### Multiple Observers

```python
from tests.e2e.fixtures.workflow_test_helpers import (
    create_error_collector_observer,
    create_artifact_tracker_observer,
)

@pytest.mark.e2e_workflow
async def test_with_multiple_observers(workflow_runner, workflow_observers):
    error_collector = create_error_collector_observer()
    artifact_tracker = create_artifact_tracker_observer(["requirements.md"])
    
    workflow_observers.extend([error_collector, artifact_tracker])
    
    state, results = await workflow_runner.run_workflow(workflow_path)
    
    # Assert on each observer
    assert len(error_collector.get_errors()) == 0
    assert artifact_tracker.has_artifact("requirements.md")
```

### SDLC Validation

```python
from tests.e2e.fixtures.sdlc_validators import SDLCPhaseValidator

@pytest.mark.e2e_workflow
async def test_with_sdlc_validation(workflow_runner, e2e_project):
    executor = workflow_runner.create_executor()
    executor.load_workflow(workflow_path)
    
    # Register SDLC validator
    sdlc_validator = SDLCPhaseValidator(e2e_project)
    executor.register_validator("requirements", sdlc_validator)
    executor.register_validator("implementation", sdlc_validator)
    
    state, results = await workflow_runner.run_workflow(workflow_path)
    
    # Check validation results
    validation_results = state.variables.get("validation_results", {})
    assert "requirements" in validation_results
```

### Waiting for Specific Step

```python
from tests.e2e.fixtures.workflow_test_helpers import WorkflowTestHelper

@pytest.mark.e2e_workflow
async def test_wait_for_step(workflow_runner):
    executor = workflow_runner.create_executor()
    executor.load_workflow(workflow_path)
    executor.start(workflow)
    
    # Wait for specific step to complete
    completed = await WorkflowTestHelper.wait_for_step(
        executor, "implementation", timeout=60.0
    )
    assert completed, "Implementation step should complete"
```

## Helper Functions

### WorkflowTestHelper

Static helper methods for common patterns:

- `setup_monitoring()`: Set up monitoring for an executor
- `register_custom_observer()`: Register a custom observer
- `wait_for_step()`: Wait for a step to complete
- `assert_workflow_progress()`: Assert minimum progress
- `get_step_events()`: Get events for a specific step
- `assert_step_completed()`: Assert a step completed

### Factory Functions

Common observer patterns:

- `create_step_tracker_observer()`: Track specific steps
- `create_artifact_tracker_observer()`: Track artifact creation
- `create_error_collector_observer()`: Collect all errors
- `create_progress_logger_observer()`: Log progress to logger

## Best Practices

1. **Use fixtures when possible**: The `workflow_monitor` fixture automatically handles setup and cleanup

2. **Custom observers for specific concerns**: Create focused observers for specific validation needs

3. **Combine multiple observers**: Use `workflow_observers` fixture to register multiple observers

4. **Configure monitoring per test**: Use `@pytest.mark.monitoring_config` for test-specific settings

5. **Validate SDLC phases**: Register validators for comprehensive SDLC validation

## Architecture

The monitoring system uses the observer pattern:

```
WorkflowExecutor
    ├── emit_event() → WorkflowEventLog
    │                       └── notify subscribers
    │
    ├── register_observer() → ObserverRegistry
    │                           └── observers[] (list of WorkflowObserver)
    │
    └── get_current_progress() → WorkflowProgressMonitor
                                    └── ProgressMetrics (real-time query)
```

Events flow:
1. Step starts → `emit_event("step_start")` → notify observers → monitor captures snapshot
2. Step completes → `emit_event("step_finish")` → notify observers → monitor updates progress
3. Artifact created → `emit_event("artifact_created")` → notify observers → monitor tracks files

## Migration from Polling

The old polling-based monitoring has been replaced with event-driven monitoring:

**Before (polling)**:
```python
# Polling loop (inefficient)
while executor.state.status == "running":
    monitor.capture_snapshot()
    await asyncio.sleep(5.0)
```

**After (event-driven)**:
```python
# Automatic via observer pattern (efficient)
monitor = WorkflowActivityMonitor(executor=executor)
# Events automatically trigger snapshot capture
```

## See Also

- `workflow_monitor.py`: Core monitoring implementation
- `workflow_test_helpers.py`: Helper utilities
- `sdlc_validators.py`: SDLC validation helpers
- `conftest.py`: Pytest fixtures

