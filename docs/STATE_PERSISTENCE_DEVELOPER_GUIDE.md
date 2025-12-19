# State Persistence Developer Guide

**Version:** 1.1  
**Date:** January 2026  
**Last Updated:** December 2025  
**Status:** ✅ Complete

**Recent Updates:**
- Added atomic file writing to prevent corruption (v2.0.8+)
- Added safe JSON loading with retry logic
- Added file validation and stability checks

---

## Overview

This guide provides detailed technical documentation for developers working with the state persistence and resume system. It covers architecture, API reference, state format specifications, and implementation details.

---

## Architecture

### System Components

The state persistence system consists of several key components:

1. **AdvancedStateManager** (`tapps_agents/workflow/state_manager.py`)
   - Handles persistent state storage
   - Manages state versioning and migration
   - Provides state validation and recovery
   - Uses atomic file writing to prevent corruption

2. **File Utilities** (`tapps_agents/workflow/file_utils.py`)
   - Provides atomic file writing (temp-then-rename pattern)
   - Safe JSON loading with retry logic and validation
   - File stability checks to prevent reading incomplete files
   - Prevents race conditions during concurrent read/write operations

3. **WorkflowCheckpointManager** (`tapps_agents/workflow/checkpoint_manager.py`)
   - Determines when checkpoints should be created
   - Manages checkpoint frequency configuration
   - Tracks checkpoint metadata

4. **StatePersistenceConfigManager** (`tapps_agents/workflow/state_persistence_config.py`)
   - Manages configuration loading and validation
   - Handles configuration migration
   - Executes cleanup policies

5. **StateValidator** (`tapps_agents/workflow/state_manager.py`)
   - Validates state integrity
   - Calculates checksums
   - Detects corruption

6. **StateMigrator** (`tapps_agents/workflow/state_manager.py`)
   - Migrates state between versions
   - Handles backward compatibility

### State Storage Structure

```
.tapps-agents/
└── workflow-state/
    ├── {workflow_id}-{timestamp}.json      # Current state files
    ├── {workflow_id}-{timestamp}.json.gz   # Compressed state files
    ├── {workflow_id}.meta.json             # Metadata files
    ├── last.json                            # Pointer to latest state
    └── history/
        └── {workflow_id}-{timestamp}.json  # Historical checkpoints
```

---

## State Format Specification

### Current Version: 2.0

The state file is a JSON document with the following structure:

```json
{
  "version": "2.0",
  "workflow_id": "unique-workflow-id",
  "started_at": "2025-01-27T10:00:00",
  "current_step": "step-3",
  "completed_steps": ["step-0", "step-1", "step-2"],
  "skipped_steps": [],
  "artifacts": {
    "artifact-1": {
      "path": "output/file.txt",
      "type": "file",
      "created_at": "2025-01-27T10:05:00"
    }
  },
  "variables": {
    "key1": "value1",
    "key2": 42
  },
  "status": "running",
  "metadata": {
    "saved_at": "2025-01-27T10:10:00",
    "checksum": "sha256_hex_digest",
    "compression": false,
    "current_step": "step-3",
    "completed_steps_count": 3,
    "progress_percentage": 60.0,
    "trigger_step_id": "step-2"
  }
}
```

### Required Fields

- `version`: State format version (string)
- `workflow_id`: Unique workflow identifier (string)
- `started_at`: Workflow start timestamp (ISO 8601 string)
- `status`: Workflow status (string: "running", "completed", "failed", "paused")
- `metadata`: Metadata object with checksum and timestamps

### Optional Fields

- `current_step`: Current step identifier (string | null)
- `completed_steps`: List of completed step IDs (array)
- `skipped_steps`: List of skipped step IDs (array)
- `artifacts`: Dictionary of artifacts (object)
- `variables`: Dictionary of workflow variables (object)

### Version History

#### Version 1.0 (Legacy)

```json
{
  "version": "1.0",
  "workflow_id": "workflow-id",
  "started_at": "2025-01-27T10:00:00",
  "current_step": "step-1",
  "completed_steps": ["step-0"],
  "status": "running"
}
```

**Migration Notes:**
- Version 1.0 states are automatically migrated to 2.0
- Missing fields (`skipped_steps`, `artifacts`, `variables`) are initialized with defaults
- Migration occurs automatically on load

---

## API Reference

### AdvancedStateManager

#### `save_state(state: WorkflowState, workflow_path: Path | None = None) -> Path`

Save workflow state to persistent storage.

**Parameters:**
- `state`: WorkflowState object to save
- `workflow_path`: Optional path to workflow YAML file

**Returns:**
- Path to saved state file

**Example:**
```python
from tapps_agents.workflow.state_manager import AdvancedStateManager
from tapps_agents.workflow.models import WorkflowState

state_manager = AdvancedStateManager(storage_dir, compression=False)
workflow_state = WorkflowState(
    workflow_id="my-workflow",
    started_at=datetime.now(),
    status="running"
)
state_path = state_manager.save_state(workflow_state)
```

#### `load_state(workflow_id: str | None = None, state_file: Path | None = None, validate: bool = True) -> tuple[WorkflowState, StateMetadata]`

Load workflow state from persistent storage.

**Parameters:**
- `workflow_id`: Workflow ID to load (loads latest if None)
- `state_file`: Specific state file to load
- `validate`: Whether to validate state integrity

**Returns:**
- Tuple of (WorkflowState, StateMetadata)

**Example:**
```python
state, metadata = state_manager.load_state(workflow_id="my-workflow")
print(f"Loaded state version: {metadata.version}")
```

#### `list_states(workflow_id: str | None = None) -> list[dict[str, Any]]`

List all available states.

**Parameters:**
- `workflow_id`: Filter by workflow ID (optional)

**Returns:**
- List of state metadata dictionaries

### WorkflowCheckpointManager

#### `should_checkpoint(step: WorkflowStep, state: WorkflowState, is_gate_step: bool = False) -> bool`

Determine if a checkpoint should be created.

**Parameters:**
- `step`: Workflow step that just completed
- `state`: Current workflow state
- `is_gate_step`: Whether this is a gate evaluation step

**Returns:**
- True if checkpoint should be created

**Example:**
```python
from tapps_agents.workflow.checkpoint_manager import (
    CheckpointConfig,
    CheckpointFrequency,
    WorkflowCheckpointManager
)

config = CheckpointConfig(frequency=CheckpointFrequency.EVERY_STEP)
checkpoint_manager = WorkflowCheckpointManager(config=config)

if checkpoint_manager.should_checkpoint(step, workflow_state):
    state_manager.save_state(workflow_state)
    checkpoint_manager.record_checkpoint(step.id)
```

#### `record_checkpoint(step_id: str) -> None`

Record that a checkpoint was created.

**Parameters:**
- `step_id`: ID of step that triggered checkpoint

#### `get_checkpoint_metadata(state: WorkflowState, step: WorkflowStep | None = None) -> dict[str, Any]`

Get metadata to include in checkpoint.

**Returns:**
- Dictionary with checkpoint metadata

### StatePersistenceConfigManager

#### `get_storage_path() -> Path`

Get the storage path for workflow state.

**Returns:**
- Path to state storage directory

#### `validate_configuration() -> bool`

Validate current configuration.

**Returns:**
- True if configuration is valid

#### `reload_configuration() -> bool`

Reload configuration from file.

**Returns:**
- True if reload was successful

#### `execute_cleanup() -> dict[str, Any]`

Execute state cleanup based on configured policies.

**Returns:**
- Dictionary with cleanup results

**Example:**
```python
from tapps_agents.workflow.state_persistence_config import StatePersistenceConfigManager

config_manager = StatePersistenceConfigManager()
result = config_manager.execute_cleanup()
print(f"Deleted {result['deleted']} files, freed {result['freed_mb']} MB")
```

### StateValidator

#### `calculate_checksum(state_data: dict[str, Any]) -> str`

Calculate SHA256 checksum for state data.

**Parameters:**
- `state_data`: State data dictionary

**Returns:**
- SHA256 hex digest string

#### `validate_state(state_data: dict[str, Any], expected_checksum: str | None = None) -> tuple[bool, str | None]`

Validate state integrity.

**Parameters:**
- `state_data`: State data dictionary
- `expected_checksum`: Expected checksum (optional)

**Returns:**
- Tuple of (is_valid, error_message)

### StateMigrator

#### `migrate_state(state_data: dict[str, Any], from_version: str, to_version: str) -> dict[str, Any]`

Migrate state between versions.

**Parameters:**
- `state_data`: State data to migrate
- `from_version`: Source version
- `to_version`: Target version

**Returns:**
- Migrated state data

### File Utilities

#### `atomic_write_json(path: Path, data: dict[str, Any], compress: bool = False, indent: int = 2, **kwargs) -> None`

Atomically write JSON data to a file using temp-then-rename pattern.

**Parameters:**
- `path`: Target file path
- `data`: Data to write as JSON
- `compress`: Whether to compress with gzip
- `indent`: JSON indentation level
- `**kwargs`: Additional arguments for json.dump()

**Example:**
```python
from tapps_agents.workflow.file_utils import atomic_write_json
from pathlib import Path

atomic_write_json(Path("state.json"), {"key": "value"}, indent=2)
```

#### `safe_load_json(path: Path, retries: int = 3, backoff: float = 0.5, min_age_seconds: float = 2.0, min_size: int = 100) -> dict[str, Any] | None`

Safely load JSON from a file with retry logic and validation.

**Parameters:**
- `path`: File path to load
- `retries`: Number of retry attempts (default: 3)
- `backoff`: Backoff multiplier between retries (default: 0.5)
- `min_age_seconds`: Minimum file age before reading (default: 2.0)
- `min_size`: Minimum file size in bytes (default: 100)

**Returns:**
- Parsed JSON data or None if loading fails

**Example:**
```python
from tapps_agents.workflow.file_utils import safe_load_json
from pathlib import Path

data = safe_load_json(Path("state.json"))
if data is None:
    print("Failed to load or file is incomplete")
```

#### `is_valid_json_file(path: Path, min_size: int = 100) -> bool`

Check if a file contains valid JSON and meets minimum size.

**Parameters:**
- `path`: File path to check
- `min_size`: Minimum file size in bytes (default: 100)

**Returns:**
- True if file is valid JSON and meets size requirement

#### `is_file_stable(path: Path, min_age_seconds: float = 2.0) -> bool`

Check if a file has been stable (not modified recently).

**Parameters:**
- `path`: File path to check
- `min_age_seconds`: Minimum age in seconds (default: 2.0)

**Returns:**
- True if file exists and hasn't been modified recently

---

## State Versioning and Migration

### Migration Process

1. **Version Detection**: State version is read from state file
2. **Migration Check**: If version < CURRENT_STATE_VERSION, migration is triggered
3. **Migration Execution**: StateMigrator applies necessary transformations
4. **Validation**: Migrated state is validated
5. **Save**: Migrated state is saved with new version

### Adding New Versions

To add a new state version:

1. Update `CURRENT_STATE_VERSION` in `state_manager.py`
2. Add migration method in `StateMigrator`:
   ```python
   @staticmethod
   def _migrate_2_0_to_3_0(state_data: dict[str, Any]) -> dict[str, Any]:
       # Migration logic
       migrated = state_data.copy()
       migrated["version"] = "3.0"
       # Add new fields, transform existing fields
       return migrated
   ```
3. Update migration map:
   ```python
   MIGRATION_MAP = {
       ("1.0", "2.0"): StateMigrator._migrate_1_0_to_2_0,
       ("2.0", "3.0"): StateMigrator._migrate_2_0_to_3_0,
   }
   ```
4. Update state format specification in this document
5. Add tests for migration

---

## Checkpoint Creation and Loading

### Checkpoint Creation Flow

1. **Step Completion**: Workflow step completes
2. **Checkpoint Decision**: `WorkflowCheckpointManager.should_checkpoint()` is called
3. **State Update**: Workflow state is updated with step results
4. **Metadata Generation**: Checkpoint metadata is generated
5. **State Save**: `AdvancedStateManager.save_state()` is called
   - Uses atomic file writing (writes to temp file, then renames)
   - Prevents partial file visibility during concurrent reads
6. **Checkpoint Record**: `record_checkpoint()` is called

### Checkpoint Loading Flow

1. **State Discovery**: Locate state file (by workflow_id or state_file)
2. **File Stability Check**: Verify file hasn't been modified recently (prevents reading incomplete files)
3. **File Validation**: Check file size and JSON validity before parsing
4. **File Loading**: Load JSON from file (with decompression if needed, with retry logic)
5. **Version Check**: Check state version
6. **Migration**: Migrate if needed
7. **Validation**: Validate state integrity
8. **State Reconstruction**: Create WorkflowState object
9. **Metadata Extraction**: Extract StateMetadata

---

## Error Handling and Recovery

### Corruption Detection

The system detects corruption through:

1. **JSON Parsing Errors**: Invalid JSON syntax
2. **Checksum Mismatch**: Calculated checksum doesn't match stored checksum
3. **Missing Required Fields**: Required fields are absent
4. **Invalid Field Types**: Fields have incorrect types
5. **Incomplete Files**: Files that are too small or fail JSON validation
6. **File Stability**: Files modified too recently are considered potentially incomplete

### Atomic File Writing

All state file writes use atomic file operations to prevent corruption:

- **Temp-then-Rename Pattern**: Files are written to temporary files first (`.tmp` extension)
- **Atomic Rename**: Once write is complete, file is renamed atomically
- **No Partial Visibility**: Readers never see incomplete files
- **Automatic Cleanup**: Temp files are cleaned up on errors

This prevents "Failed to parse state file" errors that occurred when files were read during writes.

### Recovery Mechanisms

1. **History Recovery**: Attempt to load from history directory
2. **Default Values**: Missing fields are initialized with defaults
3. **Validation Errors**: Clear error messages guide recovery

### Error Types

- `StateValidationError`: State validation failed
- `StateMigrationError`: State migration failed
- `StateCorruptionError`: State file is corrupted
- `StateNotFoundError`: State file not found

---

## Performance Considerations

### Storage Optimization

- **Compression**: Enable compression for large states
- **Cleanup Policies**: Configure retention and size limits
- **Selective Persistence**: Use checkpoint frequency to reduce writes

### Loading Performance

- **Lazy Loading**: Load state only when needed
- **Caching**: Cache loaded states in memory
- **Parallel Loading**: Load multiple states in parallel when possible

### Checkpoint Frequency

- **Every Step**: Maximum safety, higher I/O
- **Every N Steps**: Balanced safety and performance
- **On Gates**: Minimal checkpoints, faster execution
- **Time-Based**: Regular checkpoints regardless of step count

---

## Testing

### Unit Tests

Test individual components in isolation:

```python
def test_state_save_and_load():
    state_manager = AdvancedStateManager(temp_dir)
    state = create_test_state()
    saved_path = state_manager.save_state(state)
    loaded_state, metadata = state_manager.load_state(state_file=saved_path)
    assert loaded_state.workflow_id == state.workflow_id
```

### Integration Tests

Test component interactions:

```python
def test_checkpoint_creation_during_execution():
    state_manager = AdvancedStateManager(storage_dir)
    checkpoint_manager = WorkflowCheckpointManager()
    # Test checkpoint creation during workflow execution
```

### End-to-End Tests

Test complete workflows:

```python
def test_workflow_resume_after_interruption():
    # Execute workflow, interrupt, resume
    # Verify state persistence and recovery
```

---

## Contribution Guidelines

### Adding New Features

1. **Design**: Document architecture changes
2. **Implementation**: Follow existing patterns
3. **Tests**: Add comprehensive tests
4. **Documentation**: Update this guide
5. **Migration**: Handle state versioning if needed

### Code Style

- Follow existing code patterns
- Use type hints
- Add docstrings
- Write tests for new functionality

### State Format Changes

- Always increment version
- Provide migration path
- Maintain backward compatibility
- Update format specification

---

## References

- [Checkpoint & Resume Guide](CHECKPOINT_RESUME_GUIDE.md) - User-facing documentation
- [Workflow State File Operations](WORKFLOW_STATE_FILE_OPERATIONS.md) - Atomic file operations guide
- [Epic 12: State Persistence and Resume](../implementation/EPIC_12_State_Persistence_and_Resume.md) - Epic definition
- [Story 12.7: Testing and Documentation](../stories/12.7.testing-documentation.md) - Story definition

