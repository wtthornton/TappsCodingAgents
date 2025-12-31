# Step 4: API Design and Component Specifications

**Workflow ID:** build-md-files-fix-20251231-013115  
**Date:** December 31, 2025  
**Step:** 4/7 - API Design and Component Specifications

---

## API Specifications

### 1. WorkflowDocumentationReader API

**Module:** `tapps_agents.simple_mode.documentation_reader`

**Class:** `WorkflowDocumentationReader`

#### Constructor

```python
def __init__(
    self,
    base_dir: Path,
    workflow_id: str,
) -> None
```

**Parameters:**
- `base_dir` (Path): Base directory for documentation (e.g., `docs/workflows/simple-mode/`)
- `workflow_id` (str): Workflow identifier

**Raises:**
- `ValueError`: If workflow_id is empty or contains invalid characters

---

#### read_step_documentation

```python
def read_step_documentation(
    self,
    step_number: int,
    step_name: str | None = None,
) -> str
```

**Purpose:** Read markdown content from step documentation file

**Parameters:**
- `step_number` (int): Step number (1-based)
- `step_name` (str | None): Optional step name (e.g., "enhanced-prompt")

**Returns:**
- `str`: Markdown content of the file

**Raises:**
- `FileNotFoundError`: If file doesn't exist (can be caught and handled)
- `UnicodeDecodeError`: If file encoding is invalid

**Example:**
```python
reader = WorkflowDocumentationReader(base_dir, workflow_id)
content = reader.read_step_documentation(1, "enhanced-prompt")
```

---

#### read_step_state

```python
def read_step_state(
    self,
    step_number: int,
    step_name: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Read and parse YAML frontmatter state from step file

**Parameters:**
- `step_number` (int): Step number (1-based)
- `step_name` (str | None): Optional step name

**Returns:**
- `dict[str, Any]`: Parsed state dictionary, or empty dict if no frontmatter

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `yaml.YAMLError`: If YAML frontmatter is malformed (handled gracefully, returns empty dict)

**Example:**
```python
state = reader.read_step_state(1, "enhanced-prompt")
# Returns: {"step_number": 1, "timestamp": "...", "agent_output": {...}}
```

**State Structure:**
```python
{
    "step_number": int,
    "step_name": str,
    "timestamp": str,  # ISO format
    "agent_output": dict[str, Any],
    "artifacts": list[str],
    "success_status": bool,
    "error": str | None,
}
```

---

#### validate_step_documentation

```python
def validate_step_documentation(
    self,
    step_number: int,
    step_name: str,
    required_sections: list[str],
) -> dict[str, bool]
```

**Purpose:** Validate step documentation has required sections

**Parameters:**
- `step_number` (int): Step number (1-based)
- `step_name` (str): Step name
- `required_sections` (list[str]): List of required section names

**Returns:**
- `dict[str, bool]`: Dictionary mapping section names to presence flags

**Example:**
```python
validation = reader.validate_step_documentation(
    1, "enhanced-prompt", ["Requirements Analysis", "Architecture Guidance"]
)
# Returns: {"Requirements Analysis": True, "Architecture Guidance": True}
```

---

#### get_step_file_path

```python
def get_step_file_path(
    self,
    step_number: int,
    step_name: str | None = None,
) -> Path
```

**Purpose:** Get file path for step documentation

**Parameters:**
- `step_number` (int): Step number (1-based)
- `step_name` (str | None): Optional step name

**Returns:**
- `Path`: Path to step documentation file

---

### 2. WorkflowDocumentationManager API Extensions

**Module:** `tapps_agents.simple_mode.documentation_manager`

**Class:** `WorkflowDocumentationManager` (extend existing)

#### save_step_state

```python
def save_step_state(
    self,
    step_number: int,
    state: dict[str, Any],
    content: str,
    step_name: str | None = None,
) -> Path
```

**Purpose:** Save workflow state with YAML frontmatter and markdown content

**Parameters:**
- `step_number` (int): Step number (1-based)
- `state` (dict[str, Any]): State dictionary to serialize
- `content` (str): Markdown content
- `step_name` (str | None): Optional step name

**Returns:**
- `Path`: Path to saved file

**Raises:**
- `DocumentationError`: If save fails

**File Format:**
```yaml
---
step_number: 1
step_name: enhanced-prompt
timestamp: "2025-12-31T01:31:15"
agent_output:
  enhanced_prompt: "..."
  success: true
artifacts: []
success_status: true
---
# Step 1: Enhanced Prompt
[markdown content]
```

---

#### create_workflow_summary

```python
def create_workflow_summary(self) -> Path
```

**Purpose:** Create workflow summary file with key information

**Returns:**
- `Path`: Path to summary file

**Summary Content:**
- Workflow ID
- Steps completed
- Key decisions extracted from step files
- Artifacts created
- Links to step files

---

### 3. BuildOrchestrator API Extensions

**Module:** `tapps_agents.simple_mode.orchestrators.build_orchestrator`

**Class:** `BuildOrchestrator` (modify existing)

#### resume

```python
async def resume(
    self,
    workflow_id: str,
    from_step: int | None = None,
) -> dict[str, Any]
```

**Purpose:** Resume workflow from last completed step

**Parameters:**
- `workflow_id` (str): Workflow identifier
- `from_step` (int | None): Step to resume from (None = auto-detect)

**Returns:**
- `dict[str, Any]`: Execution results

**Raises:**
- `ValueError`: If workflow_id is invalid
- `FileNotFoundError`: If workflow directory doesn't exist

**Example:**
```python
orchestrator = BuildOrchestrator(project_root, config)
result = await orchestrator.resume("build-20251231-013115")
```

---

#### _enrich_implementer_context

```python
def _enrich_implementer_context(
    self,
    workflow_id: str,
    doc_manager: WorkflowDocumentationManager | None,
) -> dict[str, str]
```

**Purpose:** Read previous step documentation and return context dictionary

**Parameters:**
- `workflow_id` (str): Workflow identifier
- `doc_manager` (WorkflowDocumentationManager | None): Documentation manager instance

**Returns:**
- `dict[str, str]`: Context dictionary with keys: `specification`, `user_stories`, `architecture`, `api_design`

**Returns empty dict if doc_manager is None or files don't exist (backward compatible)**

---

#### _find_last_completed_step

```python
def _find_last_completed_step(
    self,
    workflow_id: str,
) -> int
```

**Purpose:** Find last completed step by checking for step .md files

**Parameters:**
- `workflow_id` (str): Workflow identifier

**Returns:**
- `int`: Last completed step number (0 if no steps completed)

---

#### _execute_from_step

```python
async def _execute_from_step(
    self,
    from_step: int,
    state: dict[str, Any],
) -> dict[str, Any]
```

**Purpose:** Execute workflow from specific step with restored state

**Parameters:**
- `from_step` (int): Step to start from (1-based)
- `state` (dict[str, Any]): Restored workflow state

**Returns:**
- `dict[str, Any]`: Execution results

---

### 4. CLI Command API

**Module:** `tapps_agents.cli.commands.simple_mode`

#### handle_simple_mode_resume

```python
def handle_simple_mode_resume(args: object) -> None
```

**Purpose:** Handle `tapps-agents simple-mode resume` command

**CLI Arguments:**
- `--workflow-id` (str, required): Workflow identifier
- `--from-step` (int, optional): Step to resume from
- `--yes` (flag, optional): Skip confirmation prompt

**Behavior:**
1. Validate workflow exists
2. Show workflow status
3. Confirm resume (unless --yes)
4. Execute resume
5. Display results

**Example:**
```bash
tapps-agents simple-mode resume --workflow-id build-20251231-013115
tapps-agents simple-mode resume --workflow-id build-20251231-013115 --from-step 5 --yes
```

---

## Data Models

### StepState

```python
@dataclass
class StepState:
    step_number: int
    step_name: str
    timestamp: str  # ISO format
    agent_output: dict[str, Any]
    artifacts: list[str]
    success_status: bool
    error: str | None = None
```

### WorkflowContext

```python
@dataclass
class WorkflowContext:
    enhanced_prompt: str
    user_stories: str
    architecture: str
    api_design: str
```

---

## Error Handling

### DocumentationError

```python
class DocumentationError(Exception):
    """Exception raised for documentation operation errors."""
    pass
```

**Raised by:**
- `WorkflowDocumentationManager.save_step_state()` - If save fails
- `WorkflowDocumentationManager.create_workflow_summary()` - If summary creation fails

---

### FileNotFoundError Handling

**Strategy:** Graceful degradation
- If step file doesn't exist, return empty string/dict
- Log warning
- Continue with available data (backward compatible)

**Example:**
```python
try:
    content = reader.read_step_documentation(1, "enhanced-prompt")
except FileNotFoundError:
    logger.warning(f"Step 1 file not found, using fallback")
    content = ""  # Fallback to in-memory data
```

---

### YAMLError Handling

**Strategy:** Graceful degradation
- If YAML frontmatter is malformed, return empty dict
- Log warning
- Continue with markdown content only (backward compatible)

**Example:**
```python
try:
    state = reader.read_step_state(1, "enhanced-prompt")
except yaml.YAMLError:
    logger.warning(f"Invalid YAML frontmatter in step 1, using empty state")
    state = {}  # Fallback to empty state
```

---

## Configuration

### Config Schema Extensions

```python
class SimpleModeConfig(BaseModel):
    # Existing fields...
    
    state_persistence_enabled: bool = True  # New
    validate_documentation: bool = False  # New
```

---

## Usage Examples

### Reading Step Documentation

```python
from pathlib import Path
from tapps_agents.simple_mode.documentation_reader import WorkflowDocumentationReader

base_dir = Path("docs/workflows/simple-mode")
reader = WorkflowDocumentationReader(base_dir, "build-20251231-013115")

# Read markdown content
content = reader.read_step_documentation(1, "enhanced-prompt")

# Read state
state = reader.read_step_state(1, "enhanced-prompt")

# Validate
validation = reader.validate_step_documentation(
    1, "enhanced-prompt", ["Requirements Analysis"]
)
```

### Saving Step State

```python
from tapps_agents.simple_mode.documentation_manager import WorkflowDocumentationManager

doc_manager = WorkflowDocumentationManager(
    base_dir=Path("docs/workflows/simple-mode"),
    workflow_id="build-20251231-013115",
)

state = {
    "step_number": 1,
    "step_name": "enhanced-prompt",
    "timestamp": "2025-12-31T01:31:15",
    "agent_output": {"enhanced_prompt": "..."},
    "artifacts": [],
    "success_status": True,
}

content = "# Step 1: Enhanced Prompt\n\n..."

path = doc_manager.save_step_state(1, state, content, "enhanced-prompt")
```

### Resuming Workflow

```python
from tapps_agents.simple_mode.orchestrators.build_orchestrator import BuildOrchestrator

orchestrator = BuildOrchestrator(project_root, config)

# Auto-detect last step
result = await orchestrator.resume("build-20251231-013115")

# Resume from specific step
result = await orchestrator.resume("build-20251231-013115", from_step=5)
```

---

## Testing API

### Mock Objects

```python
from unittest.mock import Mock, MagicMock

# Mock WorkflowDocumentationReader
mock_reader = Mock(spec=WorkflowDocumentationReader)
mock_reader.read_step_documentation.return_value = "# Step 1\n\nContent"
mock_reader.read_step_state.return_value = {"step_number": 1, "success": True}
```

---

## Performance Considerations

### File Reading
- Cache file reads within same workflow execution
- Use pathlib for efficient path operations
- Read files only when needed (lazy loading)

### State Serialization
- Only serialize essential state (not full agent outputs)
- Truncate large outputs if needed
- Use efficient YAML serialization

---

## Security Considerations

### Path Validation
- Validate workflow_id doesn't contain `..` or `/`
- Use pathlib for safe path operations
- Check file exists before reading

### YAML Parsing
- Use `yaml.safe_load()` to prevent code execution
- Limit YAML frontmatter size
- Catch YAML parsing errors gracefully

---

## Conclusion

These API specifications provide a complete interface for reading documentation, managing state, and resuming workflows while maintaining backward compatibility and following existing patterns.
