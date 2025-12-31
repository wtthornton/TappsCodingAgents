# Step 2: User Stories with Acceptance Criteria

**Workflow ID:** feedback-priority1-20251231-004422  
**Date:** January 16, 2025  
**Step:** 2/7 - User Story Creation

---

## User Stories

### Story 1: Fast Mode for Iterative Development

**As a** developer using TappsCodingAgents  
**I want** to use a `--fast` flag to skip documentation steps in Simple Mode *build workflow  
**So that** I can iterate quickly on code changes without waiting for full documentation generation

**Priority:** High  
**Story Points:** 5  
**Estimate:** 4-6 hours

**Acceptance Criteria:**
- [ ] CLI command supports `--fast` flag: `tapps-agents simple-mode build --fast --prompt "description"`
- [ ] Cursor Skill supports `--fast` flag: `@simple-mode *build --fast "description"`
- [ ] When `--fast` is enabled, steps 1-4 (enhance, plan, architect, design) are skipped
- [ ] Workflow jumps directly to step 5 (implementation)
- [ ] Steps 6 (review) and 7 (testing) still execute
- [ ] Quality gates are still enforced (review scoring, test execution)
- [ ] Default behavior unchanged (fast mode is opt-in)
- [ ] Configuration option available: `simple_mode.fast_mode_default: bool`
- [ ] Help text documents fast mode behavior
- [ ] Unit tests verify fast mode skips correct steps
- [ ] Integration tests verify fast mode workflow execution

**Technical Notes:**
- Modify `BuildOrchestrator.execute()` to check for fast mode flag
- Skip enhancer, planner, architect, designer agents when fast mode enabled
- Pass original prompt directly to implementer (no enhancement)
- Maintain all quality gates in review and testing steps

---

### Story 2: Workflow State Persistence and Resume

**As a** developer using TappsCodingAgents  
**I want** workflow progress to be saved after each step  
**So that** I can resume failed workflows without losing progress

**Priority:** High  
**Story Points:** 8  
**Estimate:** 8-12 hours

**Acceptance Criteria:**
- [ ] State is saved to `.tapps-agents/workflow-state/{workflow-id}/` after each step
- [ ] State includes: step outputs, artifacts, completion status, metadata, timestamp
- [ ] State format: JSON with versioning (`state_version: "1.0"`)
- [ ] State includes checksum for integrity validation
- [ ] CLI command: `tapps-agents simple-mode resume {workflow-id}`
- [ ] Cursor Skill: `@simple-mode *resume {workflow-id}`
- [ ] Resume command loads state and continues from last completed step
- [ ] Auto-detection: On workflow failure, offer resume option
- [ ] Resume validates state version and checksum before loading
- [ ] Resume handles state migration for version mismatches
- [ ] Resume command shows progress: "Resuming from step 3/7"
- [ ] State cleanup: Configurable retention (default: 30 days)
- [ ] Unit tests for state save/load operations
- [ ] Integration tests for resume capability
- [ ] Tests for state version migration

**Technical Notes:**
- Extend `AdvancedStateManager` with `save_step_checkpoint()` method
- Add checkpoint metadata to `WorkflowState` model
- Create `ResumeOrchestrator` class for resume logic
- Add resume command handler in `simple_mode.py`
- Use atomic file writes for state persistence
- Implement state validation and migration logic

---

### Story 3: Documentation Organization by Workflow ID

**As a** developer using TappsCodingAgents  
**I want** documentation artifacts organized by workflow ID  
**So that** I can easily find related documentation and avoid naming conflicts

**Priority:** High  
**Story Points:** 3  
**Estimate:** 2-4 hours

**Acceptance Criteria:**
- [ ] Documentation saved to `docs/workflows/simple-mode/{workflow-id}/step1.md`
- [ ] Workflow ID generated at workflow start (timestamp-based format)
- [ ] Workflow directory created automatically on workflow start
- [ ] All step documentation saved to workflow directory
- [ ] Optional: `latest/` symlink points to most recent workflow
- [ ] Backward compatibility: Existing flat structure still works (migration optional)
- [ ] Documentation paths updated in all workflow orchestrators
- [ ] Documentation cleanup: Can delete entire workflow directories
- [ ] Unit tests for directory creation and file paths
- [ ] Integration tests for documentation organization
- [ ] Tests verify no naming conflicts with concurrent workflows

**Technical Notes:**
- Generate workflow ID in `BuildOrchestrator.execute()` or workflow start
- Create directory: `docs/workflows/simple-mode/{workflow-id}/`
- Update all documentation save paths to use workflow directory
- Use `pathlib.Path` for cross-platform compatibility
- Optional: Add migration script for existing documentation

---

## Story Dependencies

```
Story 3 (Documentation Organization)
  ↓
Story 1 (Fast Mode)
  ↓
Story 2 (State Persistence)
```

**Rationale:**
- Story 3 is independent and simplest - implement first
- Story 1 depends on workflow ID (from Story 3) for documentation paths
- Story 2 depends on workflow ID and can leverage Story 3's directory structure

---

## Story Estimates Summary

| Story | Points | Estimate | Priority |
|-------|--------|-----------|----------|
| Story 1: Fast Mode | 5 | 4-6 hours | High |
| Story 2: State Persistence | 8 | 8-12 hours | High |
| Story 3: Documentation Organization | 3 | 2-4 hours | High |
| **Total** | **16** | **14-22 hours** | **High** |

---

## Implementation Plan

**Phase 1: Foundation (Story 3)**
- Generate workflow IDs
- Create workflow directories
- Update documentation paths
- Tests

**Phase 2: Fast Mode (Story 1)**
- Add `--fast` flag
- Modify orchestrator logic
- Skip steps 1-4
- Tests

**Phase 3: State Persistence (Story 2)**
- Extend state manager
- Add checkpoint saving
- Implement resume command
- Tests

---

## Definition of Done

All stories are considered complete when:
- [ ] All acceptance criteria met
- [ ] Code reviewed and approved
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Integration tests written and passing
- [ ] Documentation updated (CLI help, user guide)
- [ ] Backward compatibility verified
- [ ] Quality score ≥75/100

---

## Next Steps

Proceed to Step 3: Design system architecture for these three features.
