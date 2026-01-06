# Step 4: Component Design Specifications - Build Workflow Improvements

**Workflow ID**: build-workflow-improvements-20250116  
**Date**: January 16, 2025

---

## Component Specifications

### 1. DeliverableChecklist Component

#### File: `tapps_agents/simple_mode/orchestrators/deliverable_checklist.py`

#### Class Definition

```python
"""Deliverable checklist for tracking workflow deliverables."""

from pathlib import Path
from typing import Any


class DeliverableChecklist:
    """Track all deliverables for a workflow execution."""
    
    def __init__(self, requirements: dict[str, Any] | None = None):
        """Initialize checklist with requirements context.
        
        Args:
            requirements: Optional requirements dict for context
        """
        self.requirements = requirements or {}
        self.checklist = {
            "core_code": [],
            "related_files": [],
            "documentation": [],
            "tests": [],
            "templates": [],
            "examples": [],
        }
    
    def add_deliverable(
        self,
        category: str,
        item: str,
        path: Path,
        status: str = "pending",
        metadata: dict[str, Any] | None = None
    ) -> None:
        """Add a deliverable to the checklist.
        
        Args:
            category: One of: core_code, related_files, documentation, tests, templates, examples
            item: Human-readable description of the deliverable
            path: File path to the deliverable
            status: Status of deliverable (pending, complete, failed, skipped)
            metadata: Optional metadata (e.g., requirement_id, step_number)
        """
    
    def discover_related_files(self, core_files: list[Path], project_root: Path) -> list[Path]:
        """Discover all related files that might need updates.
        
        Args:
            core_files: List of core files that were implemented
            project_root: Project root directory for searching
            
        Returns:
            List of discovered related file paths
        """
    
    def _find_templates(self, core_file: Path, project_root: Path) -> list[Path]:
        """Find template files related to core file.
        
        Searches in:
        - tapps_agents/resources/claude/skills/*/SKILL.md (for skill templates)
        - templates/ directory (for workflow templates)
        """
    
    def _find_documentation(self, core_file: Path, project_root: Path) -> list[Path]:
        """Find documentation files that reference the feature.
        
        Searches in:
        - docs/ directory
        - README files
        - API documentation
        """
    
    def _find_examples(self, core_file: Path, project_root: Path) -> list[Path]:
        """Find example files demonstrating the feature.
        
        Searches in:
        - examples/ directory
        - demo/ directory
        """
    
    def verify_completeness(self) -> dict[str, Any]:
        """Verify all checklist items are complete.
        
        Returns:
            Dictionary with:
            - complete: bool - Whether all items are complete
            - gaps: list[dict] - List of incomplete items with details
            - summary: dict - Summary by category
        """
    
    def mark_complete(self, category: str, item: str | None = None, path: Path | None = None) -> None:
        """Mark a deliverable as complete.
        
        Args:
            category: Category of deliverable
            item: Item description (optional, matches any if None)
            path: File path (optional, matches any if None)
        """
    
    def to_dict(self) -> dict[str, Any]:
        """Convert checklist to dictionary for serialization."""
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeliverableChecklist":
        """Create checklist from dictionary (for checkpoint restoration)."""
```

#### Method Specifications

**`add_deliverable()`**:
- Validates category is one of the allowed values
- Validates path exists (if file)
- Adds item to checklist with status
- Supports metadata for requirement linking

**`discover_related_files()`**:
- Calls `_find_templates()`, `_find_documentation()`, `_find_examples()` for each core file
- Deduplicates results
- Returns list of discovered paths

**`_find_templates()`**:
- Pattern: If core file is in `tapps_agents/core/skills/`, search for templates in `tapps_agents/resources/claude/skills/`
- Pattern: If core file is workflow-related, search `templates/` directory
- Returns list of template file paths

**`_find_documentation()`**:
- Search `docs/` for files mentioning core file name or feature
- Check README files for references
- Returns list of documentation file paths

**`_find_examples()`**:
- Search `examples/` and `demo/` directories
- Match by filename patterns or content
- Returns list of example file paths

**`verify_completeness()`**:
- Checks all items have status="complete"
- Returns gaps with category, item, path, status
- Provides summary by category

---

### 2. RequirementsTracer Component

#### File: `tapps_agents/simple_mode/orchestrators/requirements_tracer.py`

#### Class Definition

```python
"""Requirements traceability for linking requirements to deliverables."""

from pathlib import Path
from typing import Any


class RequirementsTracer:
    """Trace requirements to deliverables."""
    
    def __init__(self, requirements: dict[str, Any] | None = None):
        """Initialize tracer with requirements.
        
        Args:
            requirements: Requirements dict with requirement IDs as keys
        """
        self.requirements = requirements or {}
        self.trace: dict[str, dict[str, list[Path]]] = {}
    
    def add_trace(
        self,
        requirement_id: str,
        deliverable_type: str,
        path: Path
    ) -> None:
        """Link a requirement to a deliverable.
        
        Args:
            requirement_id: Requirement ID (e.g., "R1-VERIFY-001")
            deliverable_type: One of: code, tests, docs, templates
            path: Path to the deliverable file
        """
    
    def verify_requirement(self, requirement_id: str) -> dict[str, Any]:
        """Verify a requirement is fully implemented.
        
        Args:
            requirement_id: Requirement ID to verify
            
        Returns:
            Dictionary with:
            - complete: bool - Whether requirement is complete
            - gaps: list[str] - List of missing deliverable types
            - deliverables: dict - All deliverables linked to requirement
        """
    
    def verify_all_requirements(self) -> dict[str, Any]:
        """Verify all requirements are fully implemented.
        
        Returns:
            Dictionary with:
            - complete: bool - Whether all requirements are complete
            - requirements: dict - Status for each requirement
            - gaps: list[dict] - List of gaps with requirement_id and missing types
        """
    
    def get_traceability_report(self) -> dict[str, Any]:
        """Generate traceability matrix report.
        
        Returns:
            Dictionary with traceability matrix and statistics
        """
    
    def extract_requirement_ids(self, user_stories: list[dict[str, Any]]) -> list[str]:
        """Extract requirement IDs from user stories.
        
        Args:
            user_stories: List of user story dicts with "id" or "requirement_id" field
            
        Returns:
            List of requirement ID strings
        """
    
    def to_dict(self) -> dict[str, Any]:
        """Convert tracer to dictionary for serialization."""
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequirementsTracer":
        """Create tracer from dictionary (for checkpoint restoration)."""
```

#### Method Specifications

**`add_trace()`**:
- Creates trace entry if requirement_id doesn't exist
- Validates deliverable_type is one of: code, tests, docs, templates
- Adds path to appropriate list
- Handles duplicate paths gracefully

**`verify_requirement()`**:
- Checks if requirement_id exists in trace
- Verifies at least one deliverable exists for each type (code, tests, docs)
- Returns gaps with missing deliverable types

**`verify_all_requirements()`**:
- Iterates through all requirements
- Calls `verify_requirement()` for each
- Aggregates results into summary

**`extract_requirement_ids()`**:
- Extracts IDs from user story format: `{"id": "R1-VERIFY-001", ...}`
- Supports alternative formats: `{"requirement_id": "R1-VERIFY-001", ...}`
- Returns list of requirement ID strings

---

### 3. BuildOrchestrator Enhancements

#### File: `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`

#### New/Modified Methods

**`_step_7_testing()` - Enhanced**:
```python
async def _step_7_testing(
    self,
    implemented_files: list[Path],
    requirements: dict[str, Any],
    checklist: DeliverableChecklist,
    tracer: RequirementsTracer,
    workflow_id: str,
    doc_manager: WorkflowDocumentationManager | None = None,
) -> dict[str, Any]:
    """Create comprehensive tests for implementation.
    
    Args:
        implemented_files: List of files that were implemented
        requirements: Requirements dict for test generation
        checklist: DeliverableChecklist instance
        tracer: RequirementsTracer instance
        workflow_id: Workflow ID for documentation
        doc_manager: Documentation manager for saving results
        
    Returns:
        Dictionary with:
        - test_files: list[Path] - Created test files
        - test_results: dict - Test execution results
        - coverage: dict - Coverage report
        - status: str - Complete or failed
    """
```

**`_step_8_verification()` - New**:
```python
async def _step_8_verification(
    self,
    workflow_id: str,
    requirements: dict[str, Any],
    checklist: DeliverableChecklist,
    tracer: RequirementsTracer,
    implemented_files: list[Path],
    doc_manager: WorkflowDocumentationManager | None = None,
) -> dict[str, Any]:
    """Verify all requirements are fully implemented.
    
    Args:
        workflow_id: Workflow ID
        requirements: Requirements dict
        checklist: DeliverableChecklist instance
        tracer: RequirementsTracer instance
        implemented_files: List of implemented files
        doc_manager: Documentation manager
        
    Returns:
        Dictionary with:
        - complete: bool - Whether verification passed
        - gaps: list[dict] - List of gaps found
        - verification_results: dict - Detailed results by category
        - loopback_step: int | None - Step to loop back to if gaps found
    """
```

**`_handle_verification_gaps()` - New**:
```python
async def _handle_verification_gaps(
    self,
    gaps: list[dict[str, Any]],
    current_step: int,
    checklist: DeliverableChecklist,
    tracer: RequirementsTracer,
    workflow_state: dict[str, Any],
    max_iterations: int = 3,
) -> dict[str, Any]:
    """Handle gaps found during verification.
    
    Args:
        gaps: List of gap dictionaries
        current_step: Current step number
        checklist: DeliverableChecklist instance
        tracer: RequirementsTracer instance
        workflow_state: Current workflow state
        max_iterations: Maximum loopback iterations (default: 3)
        
    Returns:
        Dictionary with loopback decision and results
    """
```

**`_determine_loopback_step()` - New**:
```python
def _determine_loopback_step(
    self,
    gaps: list[dict[str, Any]]
) -> int:
    """Determine which step to loop back to based on gap types.
    
    Args:
        gaps: List of gap dictionaries
        
    Returns:
        Step number to loop back to (1-7)
    """
```

---

## Data Models

### DeliverableChecklist Data Structure

```python
{
    "requirements": {
        # Requirements context (optional)
    },
    "checklist": {
        "core_code": [
            {
                "item": "BuildOrchestrator enhancement",
                "path": "tapps_agents/simple_mode/orchestrators/build_orchestrator.py",
                "status": "complete",
                "metadata": {
                    "requirement_id": "R1-VERIFY-001",
                    "step_number": 8
                }
            }
        ],
        "related_files": [...],
        "documentation": [...],
        "tests": [...],
        "templates": [...],
        "examples": [...]
    }
}
```

### RequirementsTracer Data Structure

```python
{
    "requirements": {
        "R1-VERIFY-001": {
            "description": "Add Step 8 verification",
            ...
        },
        ...
    },
    "trace": {
        "R1-VERIFY-001": {
            "code": [
                Path("tapps_agents/simple_mode/orchestrators/build_orchestrator.py")
            ],
            "tests": [
                Path("tests/unit/simple_mode/test_verification.py")
            ],
            "docs": [
                Path("docs/workflows/simple-mode/.../step8-verification.md")
            ],
            "templates": []
        },
        ...
    }
}
```

---

## Integration Specifications

### BuildOrchestrator.execute() Integration

**Initialization** (after Step 1):
```python
# After Step 1: Extract requirements
enhanced_prompt_data = {...}  # From Step 1 result

# Initialize checklist and tracer
checklist = DeliverableChecklist(requirements=enhanced_prompt_data)
tracer = RequirementsTracer(requirements={})  # Will be populated in Step 2

# Store in workflow context
workflow_context = {
    "checklist": checklist,
    "tracer": tracer,
}
```

**Step 2 Integration** (after user stories):
```python
# Extract requirement IDs from user stories
user_stories = [...]  # From Step 2 result
requirement_ids = tracer.extract_requirement_ids(user_stories)

# Initialize tracer with requirement IDs
tracer = RequirementsTracer(requirements={
    req_id: story for req_id, story in zip(requirement_ids, user_stories)
})
```

**Step 5 Integration** (after implementation):
```python
# Track implemented files
for file_path in implemented_files:
    checklist.add_deliverable(
        category="core_code",
        item=f"Implementation: {file_path.name}",
        path=file_path,
        status="complete",
        metadata={"step_number": 5}
    )
    
    # Link to requirements (if applicable)
    for req_id in relevant_requirement_ids:
        tracer.add_trace(req_id, "code", file_path)
```

**Step 7 Integration** (enhanced test creation):
```python
# Generate and create test files
test_files = await self._generate_test_files(implemented_files, requirements)

# Track test files
for test_file in test_files:
    checklist.add_deliverable(
        category="tests",
        item=f"Test: {test_file.name}",
        path=test_file,
        status="complete",
        metadata={"step_number": 7}
    )
    
    # Link tests to requirements
    for req_id in relevant_requirement_ids:
        tracer.add_trace(req_id, "tests", test_file)
```

**Step 8 Integration** (verification):
```python
# Run verification
verification_result = await self._step_8_verification(
    workflow_id=workflow_id,
    requirements=requirements,
    checklist=checklist,
    tracer=tracer,
    implemented_files=implemented_files,
    doc_manager=doc_manager,
)

# Handle gaps if found
if not verification_result["complete"]:
    loopback_result = await self._handle_verification_gaps(
        gaps=verification_result["gaps"],
        current_step=8,
        checklist=checklist,
        tracer=tracer,
        workflow_state=workflow_context,
    )
```

---

## Error Handling Specifications

### DeliverableChecklist Errors
- **Invalid category**: Raise `ValueError` with allowed categories
- **File not found**: Log warning but continue (file may be created later)
- **Discovery failure**: Log error but return empty list

### RequirementsTracer Errors
- **Invalid requirement ID**: Log warning but continue
- **Invalid deliverable type**: Raise `ValueError` with allowed types
- **Missing requirement**: Return incomplete status in verification

### Verification Errors
- **Checklist verification failure**: Include in gap report
- **Tracer verification failure**: Include in gap report
- **File access error**: Log error but continue verification

### Loopback Errors
- **Max iterations reached**: Stop and report final status
- **Step execution failure**: Log error and stop loopback
- **Context restoration failure**: Log error and stop loopback

---

## Performance Specifications

### File Discovery
- **Timeout**: 30 seconds per discovery operation
- **Caching**: Cache discovered files per core file
- **Parallelization**: Discover files in parallel when possible

### Verification
- **Timeout**: 60 seconds for full verification
- **Parallelization**: Verify categories in parallel
- **Caching**: Cache verification results

### Checkpoint Persistence
- **Size limit**: 10MB per checkpoint
- **Compression**: Use JSON with path serialization
- **Cleanup**: Remove old checkpoints after workflow completion
