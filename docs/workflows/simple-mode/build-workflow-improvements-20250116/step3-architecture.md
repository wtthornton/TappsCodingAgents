# Step 3: Architecture Design - Build Workflow Improvements

**Workflow ID**: build-workflow-improvements-20250116  
**Date**: January 16, 2025

---

## System Architecture Overview

The build workflow improvements add comprehensive verification, deliverable tracking, requirements traceability, and loopback mechanisms to ensure complete deliverables on first pass.

### High-Level Architecture

```
BuildOrchestrator
├── Step 1-7: Existing workflow steps
├── DeliverableChecklist (NEW)
│   ├── Track deliverables by category
│   ├── Discover related files
│   └── Verify completeness
├── RequirementsTracer (NEW)
│   ├── Link requirements to deliverables
│   ├── Verify requirement completeness
│   └── Generate traceability reports
├── Enhanced Step 7 (MODIFIED)
│   ├── Create test files (not just validate)
│   ├── Generate test cases
│   └── Run tests and report coverage
└── Step 8: Verification (NEW)
    ├── Load requirements
    ├── Check deliverables
    ├── Generate gap report
    └── Loopback mechanism
```

---

## Component Architecture

### 1. DeliverableChecklist Component

**Purpose**: Track all deliverables systematically throughout workflow execution.

**Location**: `tapps_agents/simple_mode/orchestrators/deliverable_checklist.py`

**Class Structure**:
```python
class DeliverableChecklist:
    """Track all deliverables for a workflow."""
    
    def __init__(self, requirements: dict[str, Any])
    def add_deliverable(self, category: str, item: str, path: Path)
    def discover_related_files(self, core_files: list[Path]) -> list[Path]
    def verify_completeness(self) -> dict[str, Any]
    def _find_templates(self, core_file: Path) -> list[Path]
    def _find_documentation(self, core_file: Path) -> list[Path]
    def _find_examples(self, core_file: Path) -> list[Path]
```

**Data Structure**:
```python
{
    "core_code": [{"item": "BuildOrchestrator", "path": Path(...), "status": "complete"}],
    "related_files": [...],
    "documentation": [...],
    "tests": [...],
    "templates": [...],
    "examples": [...]
}
```

**Integration Points**:
- **Step 5 (Implement)**: Add implemented files to `core_code`
- **Step 7 (Test)**: Add test files to `tests`
- **Step 8 (Verify)**: Use checklist to verify completeness

---

### 2. RequirementsTracer Component

**Purpose**: Link requirements to deliverables and verify completeness.

**Location**: `tapps_agents/simple_mode/orchestrators/requirements_tracer.py`

**Class Structure**:
```python
class RequirementsTracer:
    """Trace requirements to deliverables."""
    
    def __init__(self, requirements: dict[str, Any])
    def add_trace(self, requirement_id: str, deliverable_type: str, path: Path)
    def verify_requirement(self, requirement_id: str) -> dict[str, Any]
    def get_traceability_report(self) -> dict[str, Any]
```

**Data Structure**:
```python
{
    "R1-VERIFY-001": {
        "code": [Path(...)],
        "tests": [Path(...)],
        "docs": [Path(...)],
        "templates": []
    },
    ...
}
```

**Integration Points**:
- **Step 2 (Planner)**: Extract requirement IDs from user stories
- **Step 5 (Implement)**: Link code files to requirements
- **Step 7 (Test)**: Link test files to requirements
- **Step 8 (Verify)**: Verify each requirement is complete

---

### 3. Enhanced Step 7: Test Creation

**Purpose**: Create comprehensive tests as part of workflow, not deferred work.

**Location**: `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`

**Method Signature**:
```python
async def _step_7_testing(
    self,
    implemented_files: list[Path],
    requirements: dict[str, Any],
    checklist: DeliverableChecklist,
    tracer: RequirementsTracer,
) -> dict[str, Any]:
    """Create comprehensive tests for implementation."""
```

**Workflow**:
1. Identify new functionality from implemented_files
2. Generate test file paths
3. Create test cases based on requirements
4. Write test files
5. Run tests via pytest
6. Report coverage for new code
7. Track test files in checklist
8. Link tests to requirements in tracer

**Output**:
- Test files created
- Test execution results
- Coverage report
- Test files added to checklist

---

### 4. Step 8: Comprehensive Verification

**Purpose**: Verify all deliverables against requirements and identify gaps.

**Location**: `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`

**Method Signature**:
```python
async def _step_8_verification(
    self,
    workflow_id: str,
    requirements: dict[str, Any],
    checklist: DeliverableChecklist,
    tracer: RequirementsTracer,
    implemented_files: list[Path],
) -> dict[str, Any]:
    """Verify all requirements are fully implemented."""
```

**Workflow**:
1. Load requirements from Step 1/2 documentation
2. Verify core implementation exists
3. Discover and verify related files
4. Verify documentation completeness
5. Verify test coverage
6. Verify templates/examples updated
7. Generate gap report
8. Determine loopback step if gaps found

**Output**:
- Verification results by category
- Gap report with actionable items
- Loopback decision (if needed)
- Verification report saved to `step8-verification.md`

---

### 5. Loopback Mechanism

**Purpose**: Loop back to appropriate step when gaps found in verification.

**Location**: `tapps_agents/simple_mode/orchestrators/build_orchestrator.py`

**Method Signature**:
```python
async def _handle_verification_gaps(
    self,
    gaps: list[dict[str, Any]],
    current_step: int,
    checklist: DeliverableChecklist,
    tracer: RequirementsTracer,
) -> dict[str, Any]:
    """Handle gaps found during verification."""
```

**Loopback Decision Logic**:
- **Missing code**: Loop back to Step 5 (Implement)
- **Missing tests**: Loop back to Step 7 (Test)
- **Missing docs**: Loop back to Step 4 (Design) or Step 9 (Documenter)
- **Missing templates**: Loop back to Step 5 (Implement)
- **Incomplete requirements**: Loop back to Step 1 (Enhance) or Step 2 (Plan)

**Constraints**:
- Maximum 3 loopback iterations
- Preserve context via checkpoint system
- Track loopback count in workflow state

---

## Data Flow

### Workflow Execution Flow

```
Step 1: Enhance
  └── Requirements extracted → RequirementsTracer initialized

Step 2: Plan
  └── User stories with requirement IDs → RequirementsTracer.add_trace()

Step 3: Architect
  └── Architecture docs → DeliverableChecklist.add_deliverable("documentation")

Step 4: Design
  └── Design docs → DeliverableChecklist.add_deliverable("documentation")

Step 5: Implement
  ├── Code files created → DeliverableChecklist.add_deliverable("core_code")
  └── Code files → RequirementsTracer.add_trace("code")

Step 6: Review
  └── Review docs → DeliverableChecklist.add_deliverable("documentation")

Step 7: Test (ENHANCED)
  ├── Test files created → DeliverableChecklist.add_deliverable("tests")
  ├── Test files → RequirementsTracer.add_trace("tests")
  └── Coverage report → DeliverableChecklist.add_deliverable("documentation")

Step 8: Verify (NEW)
  ├── Load requirements → Verification checks
  ├── Check deliverables → Gap identification
  ├── Generate gap report → Documentation
  └── Loopback decision → Re-execute if needed
```

---

## Integration Points

### BuildOrchestrator Integration

**Initialization** (in `execute()` method):
```python
# Initialize checklist and tracer
checklist = DeliverableChecklist(requirements=enhanced_prompt_data)
tracer = RequirementsTracer(requirements=user_stories_data)

# Store in workflow state for persistence
workflow_state = {
    "checklist": checklist,
    "tracer": tracer,
}
```

**During Steps**:
- Step 5: `checklist.add_deliverable("core_code", item, file_path)`
- Step 7: `checklist.add_deliverable("tests", item, test_file_path)`
- Step 8: `checklist.verify_completeness()` and `tracer.verify_requirement(id)`

### Checkpoint Integration

**Persist Checklist and Tracer**:
```python
# Save to checkpoint
checkpoint_manager.save_checkpoint(
    step_id="verification",
    step_output={
        "checklist": checklist.to_dict(),
        "tracer": tracer.to_dict(),
    }
)
```

### Documentation Integration

**Step 8 Verification Report**:
- Saved via `WorkflowDocumentationManager.save_step_documentation()`
- Format: Markdown with gap report and traceability matrix
- Location: `docs/workflows/simple-mode/{workflow_id}/step8-verification.md`

---

## File Discovery Patterns

### Template Discovery
- Search for files matching core file patterns in `tapps_agents/resources/`
- Check skill templates if core file is skill-related
- Check workflow templates if core file is workflow-related

### Documentation Discovery
- Search for docs referencing new functionality
- Check README files for mentions
- Check API docs for new endpoints/classes

### Example Discovery
- Search for example files using new functionality
- Check `examples/` directory
- Check demo files

---

## Error Handling

### Verification Failures
- Log gaps but continue workflow
- Generate gap report with actionable items
- Trigger loopback if gaps found

### Loopback Failures
- Track loopback count
- Stop after max iterations (3)
- Report final status even if incomplete

### Checklist/Tracer Errors
- Log errors but continue workflow
- Use fallback verification if components fail

---

## Performance Considerations

### File Discovery
- Cache discovered files to avoid repeated searches
- Limit search depth for performance
- Use glob patterns for efficient matching

### Verification
- Run verification checks in parallel where possible
- Cache verification results
- Skip redundant checks

---

## Security Considerations

- Validate file paths to prevent path traversal
- Sanitize requirement IDs
- Verify file existence before tracking
- Validate checkpoint data on load

---

## Testing Strategy

### Unit Tests
- `DeliverableChecklist`: All methods, edge cases
- `RequirementsTracer`: All methods, traceability logic
- Verification logic: Gap identification, loopback decision

### Integration Tests
- Full workflow with verification
- Loopback scenarios
- Checklist persistence across steps
- Tracer integration with user stories

### End-to-End Tests
- Complete workflow execution with Step 8
- Loopback mechanism with gap resolution
- Verification report generation
