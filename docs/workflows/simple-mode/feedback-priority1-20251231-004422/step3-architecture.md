# Step 3: System Architecture Design

**Workflow ID:** feedback-priority1-20251231-004422  
**Date:** January 16, 2025  
**Step:** 3/7 - Architecture Design

---

## Architecture Overview

This document describes the system architecture for implementing three Priority 1 framework improvements:
1. Fast Mode for Simple Mode *build workflow
2. Workflow State Persistence with Resume Capability
3. Documentation Organization by Workflow ID

---

## System Components

### 1. Fast Mode Architecture

#### Component: `BuildOrchestrator` Enhancement

**Location:** `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`

**Changes:**
- Add `fast_mode: bool` parameter to `execute()` method
- Conditional step execution based on `fast_mode` flag
- Skip steps 1-4 (enhance, plan, architect, design) when `fast_mode=True`
- Pass original prompt directly to implementer (no enhancement)

**Design Pattern:** Strategy Pattern
- Full mode: Execute all 7 steps with documentation
- Fast mode: Execute steps 5-7 (implement, review, test) only

**Flow Diagram:**
```
User Request (--fast flag)
    ↓
BuildOrchestrator.execute(fast_mode=True)
    ↓
Skip Steps 1-4 (enhance, plan, architect, design)
    ↓
Step 5: Implement (use original prompt)
    ↓
Step 6: Review (quality gates)
    ↓
Step 7: Test (validation)
    ↓
Return Results
```

**Configuration:**
- CLI flag: `--fast` or `-f`
- Config option: `simple_mode.fast_mode_default: bool = False`
- Environment variable: `TAPPS_AGENTS_FAST_MODE=true`

---

### 2. Workflow State Persistence Architecture

#### Component: `StepCheckpointManager`

**Location:** `tapps_agents/workflow/step_checkpoint.py` (new file)

**Responsibilities:**
- Save checkpoint after each workflow step
- Load checkpoint for resume capability
- Validate checkpoint integrity
- Manage checkpoint lifecycle (cleanup, retention)

**Design Pattern:** State Pattern + Observer Pattern
- State: Workflow execution state with step checkpoints
- Observer: Notify on checkpoint save/load events

**Data Model:**
```python
@dataclass
class StepCheckpoint:
    workflow_id: str
    step_id: str
    step_number: int
    completed_at: datetime
    step_output: dict[str, Any]
    artifacts: dict[str, Artifact]
    metadata: dict[str, Any]
    checksum: str
    version: str = "1.0"
```

**Storage Structure:**
```
.tapps-agents/workflow-state/
  ├── {workflow-id}/
  │   ├── checkpoints/
  │   │   ├── step1-checkpoint.json
  │   │   ├── step2-checkpoint.json
  │   │   └── ...
  │   ├── state.json (latest full state)
  │   └── metadata.json
  └── last.json (pointer to latest workflow)
```

**Integration Points:**
- Extend `AdvancedStateManager` with checkpoint methods
- Hook into `BuildOrchestrator` to save checkpoints after each step
- Create `ResumeOrchestrator` for resume logic

---

#### Component: `ResumeOrchestrator`

**Location:** `tapps_agents/simple_mode/orchestrators/resume_orchestrator.py` (new file)

**Responsibilities:**
- Load workflow state from checkpoint
- Validate state version and checksum
- Resume workflow from last completed step
- Handle state migration for version mismatches

**Flow Diagram:**
```
User: @simple-mode *resume {workflow-id}
    ↓
ResumeOrchestrator.load_checkpoint(workflow_id)
    ↓
Validate State (version, checksum)
    ↓
Load Last Completed Step
    ↓
Resume from Next Step
    ↓
Continue Normal Workflow Execution
```

**Error Handling:**
- Invalid workflow ID → Error message with available workflows
- State version mismatch → Attempt migration, fail if incompatible
- Corrupted checkpoint → Error with recovery suggestions
- Missing checkpoint → Error with step-by-step recovery

---

### 3. Documentation Organization Architecture

#### Component: `WorkflowDocumentationManager`

**Location:** `tapps_agents/simple_mode/documentation_manager.py` (new file)

**Responsibilities:**
- Generate workflow ID at workflow start
- Create workflow-specific documentation directory
- Manage documentation file paths
- Optional: Create `latest/` symlink

**Design Pattern:** Factory Pattern
- Factory: Generate workflow ID and create directory structure
- Manager: Manage documentation paths and organization

**Workflow ID Generation:**
```python
def generate_workflow_id(base_name: str = "build") -> str:
    """Generate workflow ID: {base_name}-{timestamp}"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{base_name}-{timestamp}"
```

**Directory Structure:**
```
docs/workflows/simple-mode/
  ├── {workflow-id-1}/
  │   ├── step1-enhanced-prompt.md
  │   ├── step2-user-stories.md
  │   ├── step3-architecture.md
  │   ├── step4-design.md
  │   ├── step5-implementation.md
  │   ├── step6-review.md
  │   └── step7-testing.md
  ├── {workflow-id-2}/
  │   └── ...
  └── latest/ -> symlink to most recent workflow
```

**Integration Points:**
- `BuildOrchestrator`: Generate workflow ID at start
- All orchestrators: Use workflow directory for documentation
- CLI commands: Support workflow ID in paths

---

## Component Interactions

### Fast Mode Flow

```
CLI/Command Parser
    ↓ (--fast flag)
BuildOrchestrator
    ↓ (fast_mode=True)
    ├─ Skip: EnhancerAgent
    ├─ Skip: PlannerAgent
    ├─ Skip: ArchitectAgent
    ├─ Skip: DesignerAgent
    ├─ Execute: ImplementerAgent
    ├─ Execute: ReviewerAgent
    └─ Execute: TesterAgent
```

### State Persistence Flow

```
BuildOrchestrator
    ↓ (after each step)
StepCheckpointManager.save_checkpoint()
    ↓
AdvancedStateManager.save_state()
    ↓
Atomic Write to .tapps-agents/workflow-state/{workflow-id}/
```

### Resume Flow

```
User: @simple-mode *resume {workflow-id}
    ↓
ResumeOrchestrator.load_checkpoint()
    ↓
StepCheckpointManager.load_checkpoint()
    ↓
Validate State
    ↓
Resume from Last Completed Step
```

### Documentation Organization Flow

```
BuildOrchestrator.start()
    ↓
WorkflowDocumentationManager.generate_workflow_id()
    ↓
WorkflowDocumentationManager.create_directory()
    ↓
All Steps Save to {workflow-id}/ directory
```

---

## Data Flow

### Workflow State Data Model

```python
@dataclass
class WorkflowState:
    workflow_id: str
    started_at: datetime
    current_step: str | None
    completed_steps: list[str]
    skipped_steps: list[str]
    artifacts: dict[str, Artifact]
    variables: dict[str, Any]
    status: str  # running, paused, completed, failed
    error: str | None
    step_executions: list[StepExecution]
    checkpoints: list[StepCheckpoint]  # NEW
    fast_mode: bool  # NEW
    documentation_dir: Path  # NEW
```

### Checkpoint Data Model

```python
@dataclass
class StepCheckpoint:
    workflow_id: str
    step_id: str
    step_number: int
    step_name: str
    completed_at: datetime
    step_output: dict[str, Any]
    artifacts: dict[str, Artifact]
    metadata: dict[str, Any]
    checksum: str
    version: str
```

---

## Security Considerations

### Path Traversal Prevention

**Risk:** Malicious workflow IDs could cause path traversal attacks

**Mitigation:**
- Validate workflow IDs: Only alphanumeric, hyphens, underscores
- Sanitize paths: Use `pathlib.Path` for safe path operations
- Restrict directory creation: Only create in allowed directories

**Implementation:**
```python
def validate_workflow_id(workflow_id: str) -> bool:
    """Validate workflow ID format."""
    import re
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, workflow_id))
```

### State Integrity

**Risk:** Corrupted or tampered state files

**Mitigation:**
- Checksums: Calculate and verify checksums for all state files
- Atomic writes: Use atomic file operations to prevent corruption
- Version validation: Check state version before loading

---

## Performance Considerations

### Fast Mode Performance

**Optimization:**
- Skip 4 LLM calls (enhance, plan, architect, design)
- Estimated time savings: 50-70% (from 5-15 minutes to 2-5 minutes)
- No quality impact: Review and testing still executed

### State Persistence Performance

**Optimization:**
- Asynchronous checkpoint saving (non-blocking)
- Compression for large state files (optional)
- Batch checkpoint operations
- Estimated overhead: <100ms per step

### Documentation Organization Performance

**Optimization:**
- Directory creation: Single operation at workflow start
- File writes: No additional overhead (same as current)
- Symlink creation: Negligible overhead

---

## Error Handling

### Fast Mode Errors

- **Missing prompt:** Error with suggestion to provide description
- **Invalid flag combination:** Error explaining incompatible flags
- **Step failure:** Continue with error, log failure, complete remaining steps

### State Persistence Errors

- **Write failure:** Retry with exponential backoff (max 3 retries)
- **Corrupted state:** Error with recovery suggestions
- **Version mismatch:** Attempt migration, fail if incompatible
- **Missing checkpoint:** Error with available workflows list

### Documentation Organization Errors

- **Directory creation failure:** Error with permission suggestions
- **Path conflicts:** Generate unique workflow ID with retry
- **Symlink failure:** Warning (non-critical), continue without symlink

---

## Configuration

### New Configuration Options

```python
class SimpleModeConfig(BaseModel):
    fast_mode_default: bool = Field(
        default=False,
        description="Default to fast mode for Simple Mode workflows"
    )
    state_persistence_enabled: bool = Field(
        default=True,
        description="Enable workflow state persistence"
    )
    checkpoint_retention_days: int = Field(
        default=30,
        ge=1,
        description="Days to retain workflow checkpoints"
    )
    documentation_organized: bool = Field(
        default=True,
        description="Organize documentation by workflow ID"
    )
    create_latest_symlink: bool = Field(
        default=False,
        description="Create 'latest' symlink to most recent workflow"
    )
```

---

## Testing Strategy

### Unit Tests

- Fast mode: Verify step skipping logic
- State persistence: Test checkpoint save/load
- Documentation: Test directory creation and paths
- Resume: Test state validation and migration

### Integration Tests

- Fast mode workflow: End-to-end fast mode execution
- Resume workflow: Resume from various steps
- Documentation organization: Concurrent workflow execution
- Error recovery: Test failure scenarios and recovery

### Performance Tests

- Fast mode: Measure time savings
- State persistence: Measure overhead
- Documentation: Measure directory creation time

---

## Migration Strategy

### Backward Compatibility

- **Existing workflows:** Continue to work (no breaking changes)
- **Existing documentation:** Optional migration script
- **Existing state:** Automatic migration on load

### Rollout Plan

1. **Phase 1:** Documentation organization (low risk)
2. **Phase 2:** Fast mode (medium risk, opt-in)
3. **Phase 3:** State persistence (higher risk, requires testing)

---

## Next Steps

Proceed to Step 4: Design component APIs and specifications for implementation.
