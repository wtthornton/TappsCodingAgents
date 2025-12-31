# Step 1: Enhanced Prompt - Fix Simple Mode Build Workflow MD Files

**Workflow ID:** build-md-files-fix-20251231-013115  
**Date:** December 31, 2025  
**Step:** 1/7 - Prompt Enhancement with Requirements Analysis

---

## Original Prompt

Implement all critical recommendations from `docs/SIMPLE_MODE_BUILD_WORKFLOW_MD_FILES_ANALYSIS.md`:

1. **CRITICAL: Enable Agents to Read Previous Step Documentation** - Add WorkflowDocumentationReader utility and modify build orchestrator to pass previous step outputs to implementer
2. **CRITICAL: Add Workflow Resume Capability** - Add state serialization to .md files and resume method to build orchestrator
3. **HIGH: Add Documentation Validation** - Validate step documentation has required sections
4. **MEDIUM: Add Documentation Summarization** - Create workflow summary file

---

## Enhanced Prompt with Requirements Analysis

### 1. Intent Analysis

**Primary Intent:** Fix critical gaps in Simple Mode build workflow where generated .md files are not leveraged by subsequent workflow steps, enabling workflow resilience, state recovery, and agent context enrichment.

**Scope:**
- Framework-level enhancements to Simple Mode build workflow
- New utility: WorkflowDocumentationReader
- Build orchestrator modifications
- CLI command additions
- Documentation validation system
- Workflow summarization

**Workflow Type:** Framework enhancement (modifying existing TappsCodingAgents framework)

**Domain:** Software development tooling, workflow orchestration, developer experience, state management

---

### 2. Requirements Analysis

#### Functional Requirements

**FR1: Documentation Reader Utility**
- **Description:** Create `WorkflowDocumentationReader` class to read step documentation from .md files
- **Acceptance Criteria:**
  - Class located in `tapps_agents/simple_mode/documentation_reader.py`
  - Method: `read_step_documentation(workflow_id, step_number, step_name)` returns markdown content
  - Method: `read_step_state(workflow_id, step_number)` returns parsed YAML frontmatter state
  - Handles missing files gracefully with clear error messages
  - Supports both step names and step numbers
- **Priority:** Critical
- **Impact:** Enables agents to read previous step outputs

**FR2: Build Orchestrator Context Enrichment**
- **Description:** Modify build orchestrator to read and pass previous step documentation to implementer
- **Acceptance Criteria:**
  - Before Step 5 (implementation), read step1-enhanced-prompt.md, step2-user-stories.md, step3-architecture.md, step4-design.md
  - Pass all previous step outputs to implementer agent via `args` dictionary
  - Implementer receives: `specification`, `user_stories`, `architecture`, `api_design`
  - Maintain backward compatibility (if files don't exist, use in-memory data)
- **Priority:** Critical
- **Impact:** Implementer receives full context from all previous steps

**FR3: State Serialization to .md Files**
- **Description:** Add YAML frontmatter to .md files containing machine-readable state
- **Acceptance Criteria:**
  - Extend `WorkflowDocumentationManager.save_step_state()` method
  - Save state as YAML frontmatter + markdown content
  - State includes: step_number, step_name, timestamp, agent_output, artifacts, success status
  - Files remain human-readable (markdown) with machine-readable metadata (YAML)
- **Priority:** Critical
- **Impact:** Enables workflow resume capability

**FR4: Workflow Resume Capability**
- **Description:** Add resume method to build orchestrator that can restore workflow state from .md files
- **Acceptance Criteria:**
  - Method: `resume(workflow_id, from_step=None)` in BuildOrchestrator
  - Automatically detects last completed step if `from_step` is None
  - Loads state from all previous step .md files
  - Resumes execution from next step
  - Handles partial state gracefully
- **Priority:** Critical
- **Impact:** Workflow can resume after crashes, saves time and API costs

**FR5: CLI Resume Command**
- **Description:** Add CLI command to resume interrupted workflows
- **Acceptance Criteria:**
  - Command: `tapps-agents simple-mode resume --workflow-id {workflow-id}`
  - Command: `tapps-agents simple-mode resume --workflow-id {workflow-id} --from-step {step}`
  - Lists available workflows if workflow-id not provided
  - Validates workflow state before resuming
- **Priority:** Critical
- **Impact:** User-friendly way to resume workflows

**FR6: Documentation Validation**
- **Description:** Validate step documentation has required sections
- **Acceptance Criteria:**
  - Method: `validate_step_documentation(step_number, step_name, required_sections)` in WorkflowDocumentationReader
  - Step 1 must have "Requirements Analysis"
  - Step 2 must have "User Stories"
  - Step 3 must have "Architecture"
  - Step 4 must have "API Design"
  - Returns validation results dictionary
  - Optionally fails workflow if critical sections missing
- **Priority:** High
- **Impact:** Ensures documentation quality

**FR7: Workflow Summarization**
- **Description:** Create workflow summary file with key information
- **Acceptance Criteria:**
  - Method: `create_workflow_summary(workflow_id)` in WorkflowDocumentationManager
  - Summary includes: workflow_id, steps_completed, key_decisions, artifacts_created
  - Saved to `workflow-summary.md` in workflow directory
  - Extracts key information from all step files
- **Priority:** Medium
- **Impact:** Quick overview of workflow, better navigation

#### Non-Functional Requirements

**NFR1: Backward Compatibility**
- All changes must maintain backward compatibility
- Existing workflows continue to work without modification
- New features are opt-in via configuration

**NFR2: Performance**
- Reading .md files should be fast (< 100ms per file)
- State serialization should not significantly slow down workflow execution
- Resume capability should be faster than restarting workflow

**NFR3: Error Handling**
- Graceful handling of missing files
- Clear error messages for invalid state
- Validation errors are informative

**NFR4: Windows Compatibility**
- All file operations must work on Windows
- Path handling uses pathlib for cross-platform compatibility
- Encoding explicitly set to UTF-8

---

### 3. Architecture Guidance

**Design Patterns:**
- **Reader Pattern:** WorkflowDocumentationReader follows reader pattern for file access
- **State Pattern:** Workflow state serialization/deserialization
- **Strategy Pattern:** Different validation strategies for different step types

**Component Design:**
1. **WorkflowDocumentationReader** (`tapps_agents/simple_mode/documentation_reader.py`)
   - Reads step documentation files
   - Parses YAML frontmatter
   - Validates documentation structure

2. **WorkflowDocumentationManager** (extend existing)
   - Add `save_step_state()` method
   - Add `create_workflow_summary()` method

3. **BuildOrchestrator** (modify existing)
   - Add context enrichment before Step 5
   - Add `resume()` method
   - Add `_find_last_completed_step()` helper

4. **CLI Commands** (`tapps_agents/cli/commands/simple_mode.py`)
   - Add `resume` command handler

**Data Flow:**
```
Step 1-4: Agents execute → Create .md files with state
Step 5: BuildOrchestrator reads .md files → Passes to implementer
Step 6-7: Continue workflow
Resume: Read all .md files → Restore state → Continue from last step
```

---

### 4. Codebase Context

**Related Files:**
- `tapps_agents/simple_mode/orchestrators/build_orchestrator.py` - Main orchestrator to modify
- `tapps_agents/simple_mode/documentation_manager.py` - Extend with state serialization
- `tapps_agents/simple_mode/cli/commands/simple_mode.py` - Add resume command
- `tapps_agents/core/config.py` - May need config options for validation

**Existing Patterns:**
- Documentation manager already creates organized directories
- Checkpoint manager exists for state persistence (can leverage)
- Multi-agent orchestrator pattern for agent execution

**Integration Points:**
- Build orchestrator calls documentation manager
- CLI commands invoke orchestrator methods
- Agents receive context via args dictionary

---

### 5. Quality Standards

**Security:**
- Validate file paths to prevent directory traversal
- Sanitize workflow IDs to prevent injection
- Validate YAML content before parsing

**Testing:**
- Unit tests for WorkflowDocumentationReader
- Integration tests for resume capability
- Tests for validation logic
- Tests for backward compatibility

**Performance:**
- File reads should be cached if same file read multiple times
- State serialization should be efficient
- Resume should be faster than full restart

**Documentation:**
- Docstrings for all new methods
- Update Simple Mode guide with resume capability
- Add examples to CLI help

---

### 6. Implementation Strategy

**Task Breakdown:**
1. Create `documentation_reader.py` with WorkflowDocumentationReader class
2. Extend `documentation_manager.py` with state serialization methods
3. Modify `build_orchestrator.py` to read and pass previous step outputs
4. Add resume method to build orchestrator
5. Add CLI resume command
6. Add validation methods
7. Add summarization method
8. Write tests for all new functionality
9. Update documentation

**Dependencies:**
- PyYAML for YAML frontmatter parsing
- pathlib for cross-platform paths
- Existing documentation manager

**Implementation Order:**
1. Documentation reader (foundation)
2. State serialization (enables resume)
3. Context enrichment (immediate value)
4. Resume capability (builds on state serialization)
5. Validation and summarization (quality improvements)

---

### 7. Synthesis

**Final Enhanced Prompt:**

Implement a comprehensive fix for Simple Mode build workflow that enables agents to leverage generated .md files. Create WorkflowDocumentationReader utility to read step documentation, extend WorkflowDocumentationManager with state serialization, modify BuildOrchestrator to pass previous step outputs to implementer and add resume capability, add CLI resume command, implement documentation validation, and add workflow summarization. All changes must maintain backward compatibility, work on Windows, include comprehensive tests, and follow existing code patterns.

**Key Success Criteria:**
- ✅ Implementer receives user stories, architecture, and API design from previous steps
- ✅ Workflow can resume from last completed step using .md files
- ✅ Documentation is validated for required sections
- ✅ Workflow summary provides quick overview
- ✅ All existing functionality continues to work
- ✅ Comprehensive test coverage
