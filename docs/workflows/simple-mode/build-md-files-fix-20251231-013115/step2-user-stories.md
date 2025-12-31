# Step 2: User Stories with Acceptance Criteria

**Workflow ID:** build-md-files-fix-20251231-013115  
**Date:** December 31, 2025  
**Step:** 2/7 - User Story Creation

---

## User Stories

### Story 1: Documentation Reader Utility

**As a** Simple Mode build workflow  
**I want** to read previous step documentation from .md files  
**So that** I can pass comprehensive context to subsequent agents

**Priority:** Critical  
**Story Points:** 5  
**Estimate:** 4-6 hours

**Acceptance Criteria:**
- [ ] Create `tapps_agents/simple_mode/documentation_reader.py`
- [ ] Implement `WorkflowDocumentationReader` class
- [ ] Method `read_step_documentation(workflow_id, step_number, step_name)` reads markdown content
- [ ] Method `read_step_state(workflow_id, step_number)` parses YAML frontmatter and returns state dict
- [ ] Handles missing files with clear error messages
- [ ] Supports both step names ("enhanced-prompt") and step numbers (1)
- [ ] Uses pathlib for cross-platform compatibility
- [ ] Explicit UTF-8 encoding for file reads
- [ ] Unit tests cover all methods
- [ ] Integration tests verify file reading works

**Technical Notes:**
- Use `WorkflowDocumentationManager.get_step_file_path()` pattern
- Parse YAML frontmatter using PyYAML
- Return empty dict if YAML frontmatter missing (backward compatible)

---

### Story 2: Context Enrichment for Implementer

**As a** Simple Mode build workflow  
**I want** the implementer agent to receive all previous step outputs  
**So that** implementation follows architecture, design, and user stories

**Priority:** Critical  
**Story Points:** 8  
**Estimate:** 6-8 hours

**Acceptance Criteria:**
- [ ] Modify `BuildOrchestrator.execute()` to read previous step documentation before Step 5
- [ ] Read step1-enhanced-prompt.md, step2-user-stories.md, step3-architecture.md, step4-design.md
- [ ] Pass all previous step outputs to implementer via `args` dictionary:
  - `specification`: enhanced prompt (from step1)
  - `user_stories`: user stories content (from step2)
  - `architecture`: architecture design (from step3)
  - `api_design`: API design (from step4)
- [ ] Maintain backward compatibility: if files don't exist, use in-memory `enhanced_prompt`
- [ ] Log when reading from files vs using in-memory data
- [ ] Handle errors gracefully (missing files, parse errors)
- [ ] Unit tests verify context enrichment logic
- [ ] Integration tests verify implementer receives all context

**Technical Notes:**
- Use `WorkflowDocumentationReader` to read files
- Only read files if `doc_manager` is initialized (organized documentation enabled)
- Pass context even if some files are missing (partial context is better than none)

---

### Story 3: State Serialization to .md Files

**As a** Simple Mode build workflow  
**I want** to save machine-readable state in .md files  
**So that** workflows can be resumed after crashes

**Priority:** Critical  
**Story Points:** 5  
**Estimate:** 4-6 hours

**Acceptance Criteria:**
- [ ] Extend `WorkflowDocumentationManager` with `save_step_state()` method
- [ ] Save state as YAML frontmatter + markdown content
- [ ] State includes: step_number, step_name, timestamp, agent_output, artifacts, success_status
- [ ] Files remain human-readable (markdown content preserved)
- [ ] YAML frontmatter is machine-readable
- [ ] Backward compatible: existing .md files without frontmatter still work
- [ ] Use PyYAML for YAML serialization
- [ ] Handle YAML serialization errors gracefully
- [ ] Unit tests verify state serialization/deserialization
- [ ] Integration tests verify state round-trip

**Technical Notes:**
- YAML frontmatter format: `---\n{yaml}\n---\n\n{markdown}`
- State dict should be JSON-serializable (for compatibility)
- Preserve existing markdown content when adding frontmatter

---

### Story 4: Workflow Resume Capability

**As a** developer using Simple Mode  
**I want** to resume interrupted workflows from the last completed step  
**So that** I don't lose progress and can continue without restarting

**Priority:** Critical  
**Story Points:** 8  
**Estimate:** 6-8 hours

**Acceptance Criteria:**
- [ ] Add `resume(workflow_id, from_step=None)` method to `BuildOrchestrator`
- [ ] Automatically detect last completed step if `from_step` is None
- [ ] Load state from all previous step .md files using `WorkflowDocumentationReader`
- [ ] Restore workflow state (enhanced_prompt, user_stories, architecture, api_design)
- [ ] Resume execution from next step after last completed step
- [ ] Handle partial state gracefully (some steps may be missing)
- [ ] Validate workflow state before resuming
- [ ] Log resume operation with details
- [ ] Unit tests for resume logic
- [ ] Integration tests verify resume works end-to-end
- [ ] Test resume from various step positions

**Technical Notes:**
- Use `_find_last_completed_step()` helper method
- Check for step .md files to determine completion
- Use `_execute_from_step()` to resume from specific step
- Restore all context needed for remaining steps

---

### Story 5: CLI Resume Command

**As a** developer using TappsCodingAgents CLI  
**I want** a command to resume interrupted workflows  
**So that** I can easily continue workflows from the command line

**Priority:** Critical  
**Story Points:** 3  
**Estimate:** 2-3 hours

**Acceptance Criteria:**
- [ ] Add `resume` subcommand to `tapps-agents simple-mode`
- [ ] Command: `tapps-agents simple-mode resume --workflow-id {workflow-id}`
- [ ] Command: `tapps-agents simple-mode resume --workflow-id {workflow-id} --from-step {step}`
- [ ] List available workflows if workflow-id not provided
- [ ] Validate workflow exists and has valid state
- [ ] Show workflow status before resuming
- [ ] Confirm before resuming (unless --yes flag)
- [ ] Display progress during resume
- [ ] Handle errors gracefully with clear messages
- [ ] Unit tests for CLI command
- [ ] Integration tests verify CLI resume works

**Technical Notes:**
- Add handler in `tapps_agents/cli/commands/simple_mode.py`
- Use existing CLI patterns for argument parsing
- Leverage `BuildOrchestrator.resume()` method

---

### Story 6: Documentation Validation

**As a** Simple Mode build workflow  
**I want** to validate step documentation has required sections  
**So that** documentation quality is ensured

**Priority:** High  
**Story Points:** 3  
**Estimate:** 2-3 hours

**Acceptance Criteria:**
- [ ] Add `validate_step_documentation(step_number, step_name, required_sections)` to `WorkflowDocumentationReader`
- [ ] Validate Step 1 has "Requirements Analysis" section
- [ ] Validate Step 2 has "User Stories" section
- [ ] Validate Step 3 has "Architecture" section
- [ ] Validate Step 4 has "API Design" section
- [ ] Return validation results dictionary with section presence flags
- [ ] Optionally fail workflow if critical sections missing (configurable)
- [ ] Log validation results
- [ ] Unit tests for validation logic
- [ ] Integration tests verify validation catches missing sections

**Technical Notes:**
- Check for section headers: `## {section}` or `### {section}`
- Make validation optional (don't break existing workflows)
- Add config option: `simple_mode.validate_documentation: bool = False`

---

### Story 7: Workflow Summarization

**As a** developer reviewing workflows  
**I want** a summary file with key workflow information  
**So that** I can quickly understand workflow status and decisions

**Priority:** Medium  
**Story Points:** 3  
**Estimate:** 2-3 hours

**Acceptance Criteria:**
- [ ] Add `create_workflow_summary(workflow_id)` method to `WorkflowDocumentationManager`
- [ ] Summary includes: workflow_id, steps_completed, key_decisions, artifacts_created
- [ ] Extract key information from all step files
- [ ] Save to `workflow-summary.md` in workflow directory
- [ ] Summary is human-readable markdown
- [ ] Include links to step files
- [ ] Generate summary after workflow completes
- [ ] Unit tests for summarization logic
- [ ] Integration tests verify summary is created

**Technical Notes:**
- Parse step files to extract key decisions
- List all artifacts created during workflow
- Format as readable markdown with sections

---

## Story Dependencies

```
Story 1 (Documentation Reader) → Story 2 (Context Enrichment)
Story 1 (Documentation Reader) → Story 3 (State Serialization)
Story 1 (Documentation Reader) → Story 4 (Resume Capability)
Story 3 (State Serialization) → Story 4 (Resume Capability)
Story 4 (Resume Capability) → Story 5 (CLI Resume)
Story 1 (Documentation Reader) → Story 6 (Validation)
Story 1 (Documentation Reader) → Story 7 (Summarization)
```

## Total Estimate

- **Total Story Points:** 35
- **Total Estimate:** 30-40 hours
- **Critical Stories:** 1, 2, 3, 4, 5 (29 story points, 24-31 hours)
- **High Priority:** 6 (3 story points, 2-3 hours)
- **Medium Priority:** 7 (3 story points, 2-3 hours)
