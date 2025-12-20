# Epic 7: Task Manifest Generation System

**Status**: ✅ Complete  
**Completed**: January 2025

## Epic Goal

Generate human-readable task checklists from workflow YAML and execution state, enabling TODO-driven execution and providing clear visibility into workflow progress. This epic implements the "TODOs as Projection" approach, creating task manifests that are always consistent with workflow truth and actual execution state.

## Epic Description

### Existing System Context

- **Current relevant functionality**:
  - Workflow YAML defines steps with `id`, `agent`, `action`, `requires`, `creates`, `gate`, etc.
  - `WorkflowExecutor` tracks state in `.tapps-agents/workflow-state/{workflow_id}/state.json`
  - `ProgressUpdateManager` provides real-time updates via Cursor chat
  - Workflow state includes step status, artifacts, dependencies
  - No systematic way to generate a "task checklist" from workflow YAML
- **Technology stack**: Python 3.13+, YAML parsing, workflow engine, state management, markdown generation
- **Integration points**:
  - `tapps_agents/workflow/executor.py` (WorkflowExecutor - state management)
  - `tapps_agents/workflow/state.py` (WorkflowState - state persistence)
  - `tapps_agents/workflow/parser.py` (WorkflowParser - YAML parsing)
  - `.tapps-agents/workflow-state/{workflow_id}/` (state storage)
  - `docs/YAML_WORKFLOW_ARCHITECTURE_DESIGN.md` (architecture reference)

### Enhancement Details

- **What's being added/changed**:
  - `TaskManifestGenerator` class that creates markdown task checklists from YAML + state
  - Automatic manifest generation on workflow events (start, step completion, state load/resume)
  - Artifact tracking (expected vs. actual artifacts, missing artifacts blocking steps)
  - Status indicators (✅ Completed, ⏳ In progress, ⏸️ Blocked, ❌ Failed, ⏭️ Skipped)
  - Optional sync to visible location (e.g., `workflow-tasks.md` in project root)
  - Task manifest format with step details, dependencies, artifacts, commands
- **How it integrates**:
  - `TaskManifestGenerator` reads workflow YAML and current state
  - Generates manifest on workflow start, step completion, state load/resume
  - Manifest stored in `.tapps-agents/workflow-state/{workflow_id}/task-manifest.md`
  - Optional: Sync to project root for visibility
  - Agents and humans can read/parse manifest for progress tracking
- **Success criteria**:
  - Task manifests are always in sync with workflow state
  - Manifests are human-readable and agent-parseable
  - Artifact tracking accurately reflects expected vs. actual state
  - Status indicators correctly represent step states
  - Manifest generation is automatic and reliable

## Stories

1. **Story 7.1: TaskManifestGenerator Core Implementation**
   - Create `TaskManifestGenerator` class in `tapps_agents/workflow/manifest.py`
   - Implement manifest generation from workflow YAML + WorkflowState + execution plan JSON
   - Use normalized execution plan JSON (from Epic 6) as input for consistent structure
   - Design markdown format for task checklist
   - Add basic step listing with status indicators
   - Acceptance criteria: Generator creates valid markdown manifests; format is consistent and readable; uses execution plan JSON

2. **Story 7.2: Workflow Event Integration**
   - Integrate manifest generation on workflow start
   - Integrate manifest generation on step completion
   - Integrate manifest generation on state load/resume
   - Add manifest update hooks to `WorkflowExecutor`
   - Acceptance criteria: Manifest updates automatically on all workflow events; no manual refresh needed

3. **Story 7.3: Artifact Tracking System**
   - Extract expected artifacts from step `creates` fields
   - Track actual artifacts from workflow state
   - Identify missing artifacts that block steps
   - Display artifact status in manifest (✅ Created, ⏳ Expected, ❌ Missing)
   - Acceptance criteria: Artifact tracking accurately reflects expected vs. actual state; blocking artifacts clearly identified

4. **Story 7.4: Status Indicators & Step Details**
   - Implement status indicators (✅ Completed, ⏳ In progress, ⏸️ Blocked, ❌ Failed, ⏭️ Skipped)
   - Add step details (agent, action, worktree, command)
   - Add dependency information (requires, creates)
   - Add step metadata (start time, completion time, duration)
   - Acceptance criteria: All step states correctly represented; step details are complete and accurate

5. **Story 7.5: Manifest Format Enhancement**
   - Add workflow metadata section (name, status, progress)
   - Add completed steps section with timestamps
   - Add current step section with details
   - Add upcoming steps section with dependencies
   - Add artifacts section with status
   - Acceptance criteria: Manifest format is comprehensive and user-friendly; all sections populated correctly

6. **Story 7.6: Optional Project Root Sync**
   - Add configuration option for syncing manifest to project root
   - Implement sync to `workflow-tasks.md` (or configurable location)
   - Add sync on workflow events (configurable)
   - Handle conflicts and file permissions
   - Acceptance criteria: Optional sync works correctly; conflicts handled gracefully; file permissions respected

7. **Story 7.7: Manifest Parsing & Agent Integration**
   - Create manifest parser for agents to read task status
   - Add helper methods for querying manifest (get current step, get blocked steps, etc.)
   - Integrate manifest reading into agent workflows
   - Add manifest validation (ensure manifest matches state)
   - Acceptance criteria: Agents can parse and query manifests; manifest validation catches inconsistencies

## Execution Notes

### Prerequisites
- Epic 6 complete (YAML schema enforcement ensures reliable parsing)
- Understanding of workflow state structure
- Access to workflow YAML files and state files

### Technical Decisions Required
- Manifest markdown format (structure, sections, indicators)
- Sync location and naming convention
- Manifest update frequency (real-time vs. on-demand)
- Manifest validation strategy

### Risk Mitigation
- **Primary Risk**: Manifest drift from actual state
- **Mitigation**: Automatic generation on all state changes, validation checks, single source of truth (state)
- **Rollback Plan**: Manifest is generated artifact; can regenerate from state at any time

## Definition of Done

- [x] `TaskManifestGenerator` class implemented and tested
- [x] Manifest generation integrated with all workflow events
- [x] Artifact tracking accurately reflects state
- [x] Status indicators correctly represent all step states
- [x] Manifest format is comprehensive and user-friendly
- [x] Optional project root sync works correctly
- [x] Agents can parse and query manifests
- [x] Manifest parser with validation implemented
- [ ] Documentation on manifest format and usage (optional enhancement)
- [ ] Test suite covers all manifest generation scenarios (optional enhancement)

## Implementation Summary

**Location**: `tapps_agents/workflow/manifest.py`

**Key Components**:
- `TaskManifestGenerator`: Generates markdown task manifests from workflow state
- `TaskManifestParser`: Parses and queries manifests for agent integration
- `generate_manifest()`: Convenience function for manifest generation
- `save_manifest()`: Saves manifest to workflow state directory
- `sync_manifest_to_project_root()`: Optional sync to project root

**Integration Points**:
- `WorkflowExecutor.start()`: Generates manifest on workflow start
- `WorkflowExecutor._handle_step_success()`: Generates manifest on step completion
- `WorkflowExecutor.load_last_state()`: Generates manifest on state load/resume
- `CursorWorkflowExecutor.start()`: Generates manifest on workflow start
- `CursorWorkflowExecutor.save_state()`: Generates manifest on state save

**Configuration**:
- `TAPPS_AGENTS_MANIFEST_SYNC`: Set to `"true"` to enable project root sync (default: `false`)

**Manifest Location**:
- Primary: `.tapps-agents/workflow-state/{workflow_id}/task-manifest.md`
- Optional sync: `{project_root}/workflow-tasks.md` (if sync enabled)

