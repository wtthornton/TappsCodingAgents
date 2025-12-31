# Step 4: Component API Design and Specifications

**Workflow ID:** feedback-priority1-20251231-004422  
**Date:** January 16, 2025  
**Step:** 4/7 - Component Design

---

## API Specifications

### 1. Fast Mode API

#### CLI Command Interface

**File:** `tapps_agents/cli/commands/simple_mode.py`

**New Command:**
```python
def handle_simple_mode_build(args: object) -> None:
    """
    Handle simple-mode build command with optional fast mode.
    
    Args:
        args: Parsed arguments with:
            - prompt: str (required) - Feature description
            - file: Path | None (optional) - Target file
            - fast: bool (optional) - Enable fast mode
            - auto: bool (optional) - Auto-execution mode
    """
```

**CLI Parser Addition:**
```python
build_parser = subparsers.add_parser("build", help="Build new features")
build_parser.add_argument(
    "--prompt", "-p",
    type=str,
    required=True,
    help="Feature description"
)
build_parser.add_argument(
    "--file", "-f",
    type=Path,
    help="Target file path"
)
build_parser.add_argument(
    "--fast",
    action="store_true",
    help="Skip documentation steps (50-70% faster)"
)
build_parser.add_argument(
    "--auto",
    action="store_true",
    help="Auto-execute workflow"
)
```

**Cursor Skill Interface:**
```python
# In .claude/skills/simple-mode/SKILL.md
# Add to commands:
*build [--fast] "{description}" [--file <path>]
```

---

#### BuildOrchestrator API

**File:** `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`

**Modified Method:**
```python
async def execute(
    self,
    intent: Intent,
    parameters: dict[str, Any] | None = None,
    fast_mode: bool = False,  # NEW PARAMETER
) -> dict[str, Any]:
    """
    Execute build workflow with optional fast mode.
    
    Args:
        intent: Parsed user intent
        parameters: Additional parameters from user input
        fast_mode: If True, skip steps 1-4 (enhance, plan, architect, design)
    
    Returns:
        Dictionary with execution results including:
        - type: "build"
        - success: bool
        - fast_mode: bool
        - steps_executed: list[str]
        - results: dict[str, Any]
    """
```

**Implementation Logic:**
```python
if fast_mode:
    # Skip steps 1-4
    # Jump directly to implementation
    agent_tasks = [
        {
            "agent_id": "implementer-1",
            "agent": "implementer",
            "command": "implement",
            "args": {"specification": original_description},  # Use original, not enhanced
        },
    ]
else:
    # Full workflow: enhance → plan → architect → design → implement
    # ... existing logic ...
```

---

### 2. State Persistence API

#### StepCheckpointManager API

**File:** `tapps_agents/workflow/step_checkpoint.py` (new)

**Class Definition:**
```python
class StepCheckpointManager:
    """Manages step-level checkpoints for workflow state persistence."""
    
    def __init__(
        self,
        state_dir: Path,
        workflow_id: str,
        compression: bool = False,
    ):
        """
        Initialize checkpoint manager.
        
        Args:
            state_dir: Base directory for state storage
            workflow_id: Workflow identifier
            compression: Enable compression for checkpoint files
        """
    
    def save_checkpoint(
        self,
        step_id: str,
        step_number: int,
        step_output: dict[str, Any],
        artifacts: dict[str, Artifact],
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """
        Save checkpoint after step completion.
        
        Args:
            step_id: Step identifier (e.g., "step1", "enhance")
            step_number: Step number (1-based)
            step_output: Step execution output
            artifacts: Step artifacts
            metadata: Optional metadata
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            CheckpointError: If checkpoint save fails
        """
    
    def load_checkpoint(
        self,
        step_id: str | None = None,
        step_number: int | None = None,
    ) -> StepCheckpoint:
        """
        Load checkpoint for step.
        
        Args:
            step_id: Step identifier (if None, load latest)
            step_number: Step number (if None, load latest)
        
        Returns:
            StepCheckpoint object
        
        Raises:
            CheckpointNotFoundError: If checkpoint not found
            CheckpointValidationError: If checkpoint is invalid
        """
    
    def get_latest_checkpoint(self) -> StepCheckpoint | None:
        """
        Get latest checkpoint for workflow.
        
        Returns:
            Latest StepCheckpoint or None if no checkpoints exist
        """
    
    def list_checkpoints(self) -> list[StepCheckpoint]:
        """
        List all checkpoints for workflow.
        
        Returns:
            List of StepCheckpoint objects, sorted by step_number
        """
    
    def cleanup_old_checkpoints(
        self,
        retention_days: int = 30,
    ) -> int:
        """
        Clean up checkpoints older than retention period.
        
        Args:
            retention_days: Days to retain checkpoints
        
        Returns:
            Number of checkpoints deleted
        """
```

**Data Model:**
```python
@dataclass
class StepCheckpoint:
    """Step checkpoint data model."""
    
    workflow_id: str
    step_id: str
    step_number: int
    step_name: str
    completed_at: datetime
    step_output: dict[str, Any]
    artifacts: dict[str, Artifact]
    metadata: dict[str, Any]
    checksum: str
    version: str = "1.0"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary."""
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepCheckpoint":
        """Create checkpoint from dictionary."""
    
    def validate(self) -> bool:
        """Validate checkpoint integrity."""
        return self.checksum == self._calculate_checksum()
```

---

#### ResumeOrchestrator API

**File:** `tapps_agents/simple_mode/orchestrators/resume_orchestrator.py` (new)

**Class Definition:**
```python
class ResumeOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for resuming failed workflows."""
    
    async def execute(
        self,
        intent: Intent,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Resume workflow from checkpoint.
        
        Args:
            intent: Parsed user intent (should contain workflow_id)
            parameters: Additional parameters
        
        Returns:
            Dictionary with execution results
        
        Raises:
            WorkflowNotFoundError: If workflow_id not found
            CheckpointValidationError: If checkpoint is invalid
        """
    
    def list_available_workflows(self) -> list[dict[str, Any]]:
        """
        List available workflows that can be resumed.
        
        Returns:
            List of workflow metadata dictionaries with:
            - workflow_id: str
            - started_at: datetime
            - last_step: str
            - status: str
            - can_resume: bool
        """
    
    def load_workflow_state(
        self,
        workflow_id: str,
    ) -> tuple[WorkflowState, StepCheckpoint]:
        """
        Load workflow state and latest checkpoint.
        
        Args:
            workflow_id: Workflow identifier
        
        Returns:
            Tuple of (WorkflowState, latest StepCheckpoint)
        
        Raises:
            WorkflowNotFoundError: If workflow not found
            CheckpointValidationError: If checkpoint invalid
        """
```

---

#### CLI Resume Command

**File:** `tapps_agents/cli/commands/simple_mode.py`

**New Command:**
```python
def handle_simple_mode_resume(args: object) -> None:
    """
    Handle simple-mode resume command.
    
    Args:
        args: Parsed arguments with:
            - workflow_id: str (required) - Workflow to resume
            - validate: bool (optional) - Validate state before resume
    """
```

**CLI Parser Addition:**
```python
resume_parser = subparsers.add_parser("resume", help="Resume failed workflow")
resume_parser.add_argument(
    "workflow_id",
    type=str,
    help="Workflow ID to resume"
)
resume_parser.add_argument(
    "--validate",
    action="store_true",
    help="Validate state before resuming"
)
resume_parser.add_argument(
    "--list",
    action="store_true",
    help="List available workflows to resume"
)
```

**Cursor Skill Interface:**
```python
# In .claude/skills/simple-mode/SKILL.md
# Add to commands:
*resume {workflow-id} [--validate]
```

---

### 3. Documentation Organization API

#### WorkflowDocumentationManager API

**File:** `tapps_agents/simple_mode/documentation_manager.py` (new)

**Class Definition:**
```python
class WorkflowDocumentationManager:
    """Manages workflow-specific documentation organization."""
    
    def __init__(
        self,
        base_dir: Path,
        workflow_id: str,
        create_symlink: bool = False,
    ):
        """
        Initialize documentation manager.
        
        Args:
            base_dir: Base directory for documentation (e.g., docs/workflows/simple-mode/)
            workflow_id: Workflow identifier
            create_symlink: Create 'latest' symlink to this workflow
        """
    
    @staticmethod
    def generate_workflow_id(base_name: str = "build") -> str:
        """
        Generate unique workflow ID.
        
        Args:
            base_name: Base name for workflow ID
        
        Returns:
            Workflow ID in format: {base_name}-{timestamp}
        """
    
    def get_documentation_dir(self) -> Path:
        """
        Get workflow-specific documentation directory.
        
        Returns:
            Path to workflow documentation directory
        """
    
    def get_step_file_path(self, step_number: int, step_name: str | None = None) -> Path:
        """
        Get file path for step documentation.
        
        Args:
            step_number: Step number (1-based)
            step_name: Optional step name (e.g., "enhanced-prompt")
        
        Returns:
            Path to step documentation file
        """
    
    def create_directory(self) -> Path:
        """
        Create workflow documentation directory.
        
        Returns:
            Path to created directory
        
        Raises:
            DocumentationError: If directory creation fails
        """
    
    def save_step_documentation(
        self,
        step_number: int,
        content: str,
        step_name: str | None = None,
    ) -> Path:
        """
        Save step documentation to workflow directory.
        
        Args:
            step_number: Step number (1-based)
            content: Documentation content (markdown)
            step_name: Optional step name
        
        Returns:
            Path to saved file
        
        Raises:
            DocumentationError: If save fails
        """
    
    def create_latest_symlink(self) -> Path | None:
        """
        Create 'latest' symlink to this workflow.
        
        Returns:
            Path to symlink, or None if creation failed
        """
```

---

#### BuildOrchestrator Integration

**File:** `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`

**Modified Initialization:**
```python
def __init__(
    self,
    project_root: Path | None = None,
    config: ProjectConfig | None = None,
):
    # ... existing initialization ...
    
    # Initialize documentation manager
    self.doc_manager: WorkflowDocumentationManager | None = None
```

**Modified Execute Method:**
```python
async def execute(
    self,
    intent: Intent,
    parameters: dict[str, Any] | None = None,
    fast_mode: bool = False,
) -> dict[str, Any]:
    # Generate workflow ID
    workflow_id = WorkflowDocumentationManager.generate_workflow_id("build")
    
    # Initialize documentation manager
    base_dir = self.project_root / "docs" / "workflows" / "simple-mode"
    self.doc_manager = WorkflowDocumentationManager(
        base_dir=base_dir,
        workflow_id=workflow_id,
        create_symlink=self.config.simple_mode.create_latest_symlink,
    )
    
    # Create documentation directory
    doc_dir = self.doc_manager.create_directory()
    
    # Save documentation using doc_manager.get_step_file_path()
    # ... rest of implementation ...
```

---

## Configuration API

### SimpleModeConfig Extension

**File:** `tapps_agents/core/config.py`

**New Configuration Class:**
```python
class SimpleModeConfig(BaseModel):
    """Simple Mode configuration."""
    
    enabled: bool = Field(
        default=True,
        description="Enable Simple Mode"
    )
    fast_mode_default: bool = Field(
        default=False,
        description="Default to fast mode for workflows"
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

**Integration in ProjectConfig:**
```python
class ProjectConfig(BaseModel):
    # ... existing fields ...
    
    simple_mode: SimpleModeConfig = Field(
        default_factory=SimpleModeConfig,
        description="Simple Mode configuration"
    )
```

---

## Error Handling API

### Custom Exceptions

**File:** `tapps_agents/workflow/exceptions.py` (extend existing)

**New Exceptions:**
```python
class CheckpointError(Exception):
    """Base exception for checkpoint operations."""
    pass

class CheckpointNotFoundError(CheckpointError):
    """Checkpoint not found."""
    pass

class CheckpointValidationError(CheckpointError):
    """Checkpoint validation failed."""
    pass

class WorkflowNotFoundError(Exception):
    """Workflow not found."""
    pass

class DocumentationError(Exception):
    """Documentation operation failed."""
    pass
```

---

## Integration Points

### BuildOrchestrator Integration

**Checkpoint Saving:**
```python
# After each step completion
if self.config.simple_mode.state_persistence_enabled:
    checkpoint_manager = StepCheckpointManager(
        state_dir=self.project_root / ".tapps-agents" / "workflow-state",
        workflow_id=workflow_id,
    )
    checkpoint_manager.save_checkpoint(
        step_id=step_id,
        step_number=step_number,
        step_output=step_result,
        artifacts=step_artifacts,
    )
```

**Documentation Saving:**
```python
# After each step completion
if self.doc_manager:
    doc_path = self.doc_manager.save_step_documentation(
        step_number=step_number,
        content=step_documentation,
        step_name=step_name,
    )
```

---

## API Usage Examples

### Fast Mode Usage

**CLI:**
```bash
tapps-agents simple-mode build --fast --prompt "Add feature X"
```

**Cursor:**
```
@simple-mode *build --fast "Add feature X"
```

**Python:**
```python
orchestrator = BuildOrchestrator(project_root=Path.cwd())
result = await orchestrator.execute(
    intent=intent,
    parameters={"description": "Add feature X"},
    fast_mode=True,
)
```

---

### Resume Usage

**CLI:**
```bash
# List available workflows
tapps-agents simple-mode resume --list

# Resume specific workflow
tapps-agents simple-mode resume feedback-priority1-20251231-004422
```

**Cursor:**
```
@simple-mode *resume feedback-priority1-20251231-004422
```

**Python:**
```python
orchestrator = ResumeOrchestrator(project_root=Path.cwd())
result = await orchestrator.execute(
    intent=intent,
    parameters={"workflow_id": "feedback-priority1-20251231-004422"},
)
```

---

### Documentation Organization Usage

**Automatic (no user action required):**
- Workflow ID generated automatically
- Directory created automatically
- Documentation saved automatically to workflow directory

**Manual (if needed):**
```python
doc_manager = WorkflowDocumentationManager(
    base_dir=Path("docs/workflows/simple-mode"),
    workflow_id="my-workflow-123",
)
doc_dir = doc_manager.create_directory()
doc_path = doc_manager.save_step_documentation(
    step_number=1,
    content="# Step 1 Documentation",
    step_name="enhanced-prompt",
)
```

---

## Next Steps

Proceed to Step 5: Implement code for Fast Mode, State Persistence, and Documentation Organization based on these API specifications.
