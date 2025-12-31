# Step 1: Enhanced Prompt - Priority 1 Framework Improvements

**Workflow ID:** feedback-priority1-20251231-004422  
**Date:** January 16, 2025  
**Step:** 1/7 - Prompt Enhancement with Requirements Analysis

---

## Original Prompt

Implement the Priority 1 high-impact improvements identified in the TappsCodingAgents feedback session:

1. **Fast Mode for Simple Mode *build** - Add `--fast` flag to skip documentation steps (50-70% faster execution)
2. **Workflow State Persistence** - Save workflow progress after each step to enable resume capability
3. **Documentation Organization** - Organize documentation by workflow ID instead of flat file structure

---

## Enhanced Prompt with Requirements Analysis

### 1. Intent Analysis

**Primary Intent:** Improve TappsCodingAgents framework efficiency and user experience by addressing the top 3 friction points identified in user feedback.

**Scope:**
- Framework-level enhancements to Simple Mode build workflow
- Workflow state management system
- Documentation artifact organization system

**Workflow Type:** Framework enhancement (modifying existing TappsCodingAgents framework)

**Domain:** Software development tooling, workflow orchestration, developer experience

---

### 2. Requirements Analysis

#### Functional Requirements

**FR1: Fast Mode for Simple Mode *build**
- **Description:** Add a `--fast` flag to Simple Mode *build workflow that skips documentation generation steps
- **Acceptance Criteria:**
  - CLI command: `@simple-mode *build --fast "description"` or `tapps-agents simple-mode build --fast --prompt "description"`
  - Skip steps 1-4 (enhance, plan, architect, design) when `--fast` is enabled
  - Jump directly to implementation (step 5)
  - Still execute review (step 6) and testing (step 7)
  - Optional: Generate minimal documentation at end if needed
  - Maintain backward compatibility (default behavior unchanged)
- **Priority:** High (addresses #1 friction point)
- **Impact:** 50-70% faster execution for iterative development

**FR2: Workflow State Persistence**
- **Description:** Save workflow progress after each step to enable resume capability
- **Acceptance Criteria:**
  - Save state to `.tapps-agents/workflow-state/{workflow-id}/` after each step
  - Include: step outputs, artifacts, completion status, metadata
  - Add `@simple-mode *resume {workflow-id}` command
  - Auto-detect and offer resume on failure detection
  - Support resuming from any completed step
  - State format: JSON with versioning and checksums
- **Priority:** High (addresses error recovery friction)
- **Impact:** Eliminates wasted time and LLM calls on failures

**FR3: Documentation Organization by Workflow ID**
- **Description:** Organize documentation artifacts by workflow ID instead of flat structure
- **Acceptance Criteria:**
  - New structure: `docs/workflows/simple-mode/{workflow-id}/step1.md`
  - Generate unique workflow ID for each workflow execution
  - Create workflow-specific directory on workflow start
  - Save all step documentation to workflow directory
  - Optional: Create `latest/` symlink to most recent workflow
  - Maintain backward compatibility (migrate existing docs if needed)
- **Priority:** High (addresses documentation clutter)
- **Impact:** Better organization, no naming conflicts, easier cleanup

#### Non-Functional Requirements

**NFR1: Performance**
- Fast mode should reduce execution time by 50-70%
- State persistence should add <100ms overhead per step
- Documentation organization should not impact workflow execution time

**NFR2: Backward Compatibility**
- All changes must maintain backward compatibility
- Existing workflows must continue to work
- Default behavior unchanged (fast mode is opt-in)

**NFR3: Reliability**
- State persistence must be atomic (no partial writes)
- Resume capability must handle state version mismatches
- Documentation organization must handle concurrent workflows

**NFR4: Maintainability**
- Code must follow existing framework patterns
- Configuration must use Pydantic models
- Tests must cover all new functionality

---

### 3. Architecture Guidance

**Design Patterns:**
- **Strategy Pattern:** Fast mode vs full mode workflow execution
- **State Pattern:** Workflow state management with persistence
- **Factory Pattern:** Workflow ID generation and directory creation
- **Observer Pattern:** State change notifications for resume capability

**Technology Recommendations:**
- Use existing `AdvancedStateManager` for state persistence (already exists in `tapps_agents/workflow/state_manager.py`)
- Use existing workflow ID generation logic (timestamp-based format)
- Use `pathlib.Path` for cross-platform directory operations
- Use atomic file writes for state persistence

**Integration Points:**
- `tapps_agents/simple_mode/orchestrators/build_orchestrator.py` - Add fast mode logic
- `tapps_agents/workflow/state_manager.py` - Extend for step-level checkpoints
- `tapps_agents/simple_mode/` - Add resume command handler
- `tapps_agents/cli/commands/simple_mode.py` - Add CLI flags

---

### 4. Codebase Context

**Related Files:**
- `tapps_agents/simple_mode/orchestrators/build_orchestrator.py` - Build workflow orchestrator
- `tapps_agents/workflow/state_manager.py` - Existing state management
- `tapps_agents/workflow/executor.py` - Workflow execution engine
- `tapps_agents/cli/commands/simple_mode.py` - CLI command handlers
- `tapps_agents/core/config.py` - Configuration models
- `docs/workflows/simple-mode/` - Current documentation location

**Existing Patterns:**
- Workflow IDs: `{workflow-id}-{timestamp}` format (see `WorkflowExecutor.start()`)
- State persistence: `AdvancedStateManager` with JSON serialization
- CLI flags: Use `argparse` with subcommands
- Configuration: Pydantic models in `ProjectConfig`

---

### 5. Quality Standards

**Security:**
- Validate workflow IDs to prevent path traversal attacks
- Sanitize file paths in documentation organization
- Use atomic writes for state files (prevent corruption)

**Testing:**
- Unit tests for fast mode logic
- Integration tests for state persistence and resume
- Tests for documentation organization
- Test concurrent workflow execution
- Test backward compatibility

**Performance:**
- Fast mode must skip unnecessary steps efficiently
- State persistence overhead must be minimal
- Documentation organization must not block workflow execution

**Documentation:**
- Update CLI help text for new flags
- Document fast mode behavior in user guide
- Document resume capability workflow
- Document new documentation structure

---

### 6. Implementation Strategy

**Task Breakdown:**

1. **Fast Mode Implementation**
   - Add `--fast` flag to CLI parser
   - Modify `BuildOrchestrator` to skip steps 1-4 when fast mode enabled
   - Update workflow execution logic
   - Add configuration option for fast mode defaults

2. **State Persistence Enhancement**
   - Extend `AdvancedStateManager` for step-level checkpoints
   - Add checkpoint saving after each step
   - Implement resume command handler
   - Add auto-resume detection on failures

3. **Documentation Organization**
   - Generate workflow ID at workflow start
   - Create workflow-specific directory
   - Update documentation save paths
   - Add migration logic for existing docs (optional)

**Dependencies:**
- Fast mode: Independent, can be implemented first
- State persistence: Requires workflow ID generation (already exists)
- Documentation organization: Requires workflow ID (already exists)

**Implementation Order:**
1. Documentation organization (simplest, enables better testing)
2. Fast mode (high impact, straightforward)
3. State persistence (most complex, builds on workflow ID)

---

### 7. Synthesis: Comprehensive Specification

**Complete Feature Specification:**

Implement three Priority 1 framework improvements to address user feedback friction points:

1. **Fast Mode (`--fast` flag):** Skip documentation steps (1-4) in Simple Mode *build workflow, jumping directly to implementation while maintaining quality gates (review + testing). Reduces execution time by 50-70% for iterative development.

2. **Workflow State Persistence:** Save workflow progress after each step to `.tapps-agents/workflow-state/{workflow-id}/`, enabling resume capability via `@simple-mode *resume {workflow-id}` command. Includes step outputs, artifacts, completion status, and metadata with versioning and checksums.

3. **Documentation Organization:** Organize documentation artifacts by workflow ID in `docs/workflows/simple-mode/{workflow-id}/step1.md` structure instead of flat files. Prevents naming conflicts, enables easy cleanup, and improves traceability.

**Technical Approach:**
- Use existing `AdvancedStateManager` for state persistence
- Extend `BuildOrchestrator` with fast mode conditional logic
- Generate workflow IDs using existing timestamp-based format
- Use atomic file operations for reliability
- Maintain full backward compatibility

**Success Criteria:**
- Fast mode reduces workflow time by 50-70%
- Resume capability works for any completed step
- Documentation organized by workflow ID
- All existing functionality preserved
- Comprehensive test coverage (>80%)
- Quality score ≥75/100

---

## Next Steps

Proceed to Step 2: Create user stories with acceptance criteria based on this enhanced specification.
