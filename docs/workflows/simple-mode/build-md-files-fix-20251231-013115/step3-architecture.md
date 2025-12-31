# Step 3: System Architecture Design

**Workflow ID:** build-md-files-fix-20251231-013115  
**Date:** December 31, 2025  
**Step:** 3/7 - System Architecture Design

---

## Architecture Overview

This enhancement adds documentation reading, state management, and resume capability to the Simple Mode build workflow. The architecture follows existing patterns while introducing new components for file-based state persistence.

---

## Component Architecture

### 1. WorkflowDocumentationReader

**Purpose:** Read step documentation and state from .md files

**Location:** `tapps_agents/simple_mode/documentation_reader.py`

**Responsibilities:**
- Read markdown content from step files
- Parse YAML frontmatter to extract state
- Validate documentation structure
- Handle missing files gracefully

**Interface:**
```python
class WorkflowDocumentationReader:
    def __init__(self, base_dir: Path, workflow_id: str)
    def read_step_documentation(step_number: int, step_name: str | None = None) -> str
    def read_step_state(step_number: int, step_name: str | None = None) -> dict[str, Any]
    def validate_step_documentation(step_number: int, step_name: str, required_sections: list[str]) -> dict[str, bool]
    def get_step_file_path(step_number: int, step_name: str | None = None) -> Path
```

**Dependencies:**
- `WorkflowDocumentationManager` (for path generation pattern)
- PyYAML (for frontmatter parsing)
- pathlib (for file operations)

**Design Patterns:**
- **Reader Pattern:** Encapsulates file reading logic
- **Strategy Pattern:** Different validation strategies per step type

---

### 2. WorkflowDocumentationManager (Extended)

**Purpose:** Manage workflow documentation and state serialization

**Location:** `tapps_agents/simple_mode/documentation_manager.py` (extend existing)

**New Responsibilities:**
- Serialize workflow state to YAML frontmatter
- Create workflow summary files
- Manage state persistence

**New Interface:**
```python
class WorkflowDocumentationManager:
    # Existing methods...
    
    def save_step_state(
        self,
        step_number: int,
        state: dict[str, Any],
        content: str,
        step_name: str | None = None,
    ) -> Path
    
    def create_workflow_summary(self) -> Path
    def _extract_key_decisions(self) -> list[str]
    def _list_artifacts(self) -> list[str]
    def _get_completed_steps(self) -> list[int]
```

**State Format:**
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

### 3. BuildOrchestrator (Modified)

**Purpose:** Coordinate build workflow with context enrichment and resume capability

**Location:** `tapps_agents/simple_mode/orchestrators/build_orchestrator.py` (modify existing)

**New Responsibilities:**
- Read previous step documentation before Step 5
- Pass comprehensive context to implementer
- Resume workflows from last completed step
- Detect last completed step

**New Interface:**
```python
class BuildOrchestrator:
    # Existing methods...
    
    async def resume(
        self,
        workflow_id: str,
        from_step: int | None = None,
    ) -> dict[str, Any]
    
    def _enrich_implementer_context(
        self,
        workflow_id: str,
        doc_manager: WorkflowDocumentationManager | None,
    ) -> dict[str, str]
    
    def _find_last_completed_step(
        self,
        workflow_id: str,
    ) -> int
    
    async def _execute_from_step(
        self,
        from_step: int,
        state: dict[str, Any],
    ) -> dict[str, Any]
```

**Context Enrichment Flow:**
```
Before Step 5 (Implementation):
1. Check if doc_manager exists (organized documentation enabled)
2. If yes, create WorkflowDocumentationReader
3. Read step1-enhanced-prompt.md → enhanced_prompt
4. Read step2-user-stories.md → user_stories
5. Read step3-architecture.md → architecture
6. Read step4-design.md → api_design
7. Pass all to implementer via args dictionary
8. If files missing, fallback to in-memory enhanced_prompt (backward compatible)
```

**Resume Flow:**
```
1. Validate workflow_id exists
2. Find last completed step (check for step .md files)
3. Load state from all previous step files
4. Restore context (enhanced_prompt, user_stories, architecture, api_design)
5. Execute from next step with restored state
6. Continue workflow normally
```

---

### 4. CLI Command Handler

**Purpose:** Provide CLI interface for resume capability

**Location:** `tapps_agents/cli/commands/simple_mode.py` (extend existing)

**New Interface:**
```python
def handle_simple_mode_resume(args: object) -> None:
    """Handle simple-mode resume command."""
    workflow_id = args.workflow_id
    from_step = args.from_step
    
    # Validate workflow exists
    # Show workflow status
    # Confirm resume (unless --yes)
    # Execute resume
```

**CLI Command:**
```bash
tapps-agents simple-mode resume --workflow-id {workflow-id} [--from-step {step}] [--yes]
```

---

## Data Flow

### Normal Workflow Execution (Enhanced)

```
Step 1: Enhancer
  ↓ Creates step1-enhanced-prompt.md (with state)
Step 2: Planner
  ↓ Creates step2-user-stories.md (with state)
Step 3: Architect
  ↓ Creates step3-architecture.md (with state)
Step 4: Designer
  ↓ Creates step4-design.md (with state)
Step 5: BuildOrchestrator reads all previous steps
  ↓ Passes: enhanced_prompt, user_stories, architecture, api_design
  ↓ Implementer receives full context
Step 6: Reviewer
  ↓ Creates step6-review.md (with state)
Step 7: Tester
  ↓ Creates step7-testing.md (with state)
  ↓ Creates workflow-summary.md
```

### Resume Workflow Execution

```
User: tapps-agents simple-mode resume --workflow-id {id}
  ↓
BuildOrchestrator.resume()
  ↓
Find last completed step (check step .md files)
  ↓
Load state from all previous steps
  ↓
Restore context (enhanced_prompt, user_stories, architecture, api_design)
  ↓
Execute from next step with restored state
  ↓
Continue workflow normally
```

---

## State Management

### State Structure

```python
{
    "step_number": int,
    "step_name": str,
    "timestamp": str,  # ISO format
    "agent_output": dict[str, Any],  # Agent-specific output
    "artifacts": list[str],  # Artifact paths created
    "success_status": bool,
    "error": str | None,  # If failed
}
```

### State Persistence

- **Format:** YAML frontmatter + Markdown content
- **Location:** `docs/workflows/simple-mode/{workflow-id}/step{N}-{name}.md`
- **Persistence:** After each step completes
- **Recovery:** Read all previous step files to restore state

---

## Error Handling

### Missing Files
- **Scenario:** Step file doesn't exist
- **Handling:** Return empty string/dict, log warning, continue with fallback
- **Fallback:** Use in-memory data if available

### Invalid State
- **Scenario:** YAML frontmatter is malformed
- **Handling:** Log error, skip state restoration, continue with available data
- **Fallback:** Use markdown content only (backward compatible)

### Partial State
- **Scenario:** Some step files exist, others don't
- **Handling:** Use available state, log missing steps
- **Fallback:** Continue with partial context

---

## Performance Considerations

### File Reading
- **Caching:** Cache file reads within same workflow execution
- **Lazy Loading:** Only read files when needed
- **Batch Reading:** Read all step files in one operation when possible

### State Serialization
- **Efficiency:** Only serialize essential state (not full agent outputs)
- **Size Limits:** Truncate large outputs if needed
- **Compression:** Not needed for .md files (human-readable requirement)

---

## Security Considerations

### Path Validation
- **Directory Traversal:** Validate workflow_id doesn't contain `..` or `/`
- **Path Sanitization:** Use pathlib for safe path operations
- **File Existence:** Check file exists before reading

### YAML Parsing
- **Safe Loading:** Use `yaml.safe_load()` to prevent code execution
- **Size Limits:** Limit YAML frontmatter size
- **Error Handling:** Catch YAML parsing errors gracefully

---

## Testing Strategy

### Unit Tests
- `test_documentation_reader.py` - Test file reading, state parsing, validation
- `test_documentation_manager_state.py` - Test state serialization
- `test_build_orchestrator_resume.py` - Test resume logic
- `test_cli_resume.py` - Test CLI command

### Integration Tests
- Test full workflow with context enrichment
- Test resume from various step positions
- Test backward compatibility (workflows without state)
- Test error scenarios (missing files, invalid state)

---

## Migration Strategy

### Backward Compatibility
- Existing workflows without state continue to work
- New features are opt-in (require organized documentation enabled)
- Fallback to in-memory data if files don't exist

### Gradual Rollout
1. Deploy documentation reader (read-only, no breaking changes)
2. Deploy state serialization (adds frontmatter, preserves markdown)
3. Deploy context enrichment (enhances implementer, backward compatible)
4. Deploy resume capability (new feature, doesn't affect existing workflows)

---

## Configuration

### New Config Options

```yaml
simple_mode:
  documentation_organized: true  # Existing
  state_persistence_enabled: true  # New: Enable state serialization
  validate_documentation: false  # New: Enable validation (default: false)
  create_latest_symlink: false  # Existing
```

---

## Dependencies

### New Dependencies
- **PyYAML:** For YAML frontmatter parsing (may already be in requirements)

### Existing Dependencies
- pathlib (standard library)
- datetime (standard library)
- logging (standard library)

---

## Future Enhancements

### Potential Improvements
1. **State Compression:** Compress large state objects
2. **Incremental State:** Only save changed state
3. **State Versioning:** Version state format for migration
4. **Remote State:** Store state in database/cloud for distributed workflows
5. **State Diff:** Show what changed between workflow runs

---

## Architecture Diagrams

### Component Interaction

```
┌─────────────────────────┐
│  BuildOrchestrator      │
│  - execute()            │
│  - resume()             │
│  - _enrich_context()    │
└──────────┬──────────────┘
           │
           ├─────────────────┐
           │                 │
           ▼                 ▼
┌──────────────────────┐  ┌──────────────────────┐
│ WorkflowDocumentation│  │ WorkflowDocumentation│
│ Manager              │  │ Reader               │
│ - save_step_state()  │  │ - read_step_doc()    │
│ - create_summary()   │  │ - read_step_state()  │
└──────────────────────┘  │ - validate()         │
                          └──────────────────────┘
```

### Data Flow

```
Agent Execution
    ↓
Save State (YAML + Markdown)
    ↓
Step File Created
    ↓
Next Step: Read Previous Steps
    ↓
Enrich Context
    ↓
Pass to Next Agent
```

---

## Conclusion

This architecture enables Simple Mode build workflow to leverage generated .md files for context enrichment and resume capability while maintaining backward compatibility and following existing patterns.
