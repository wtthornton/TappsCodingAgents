# Epic 10: Workflow Auto-Progression

## Epic Goal

Automatically advance workflows to the next step when the current step completes, eliminating the need for manual intervention between workflow steps. This creates a fully automated workflow execution experience.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Workflow executor manages workflow state and steps. Steps execute sequentially, but progression may require manual confirmation or intervention. Completion detection exists but may not automatically trigger next step
- **Technology stack**: Python 3.13+, workflow executor, state management, step execution system
- **Integration points**: 
  - `tapps_agents/workflow/executor.py` - Workflow execution
  - `tapps_agents/workflow/workflow_state.py` - State management
  - Step execution system
  - Completion detection (from Epic 7)

### Enhancement Details

- **What's being added/changed**: 
  - Implement automatic step progression when step completes
  - Create completion detection integration with step execution
  - Add automatic next step triggering
  - Implement gate evaluation and automatic progression
  - Create error handling for failed steps (skip, retry, abort)
  - Add progression logging and visibility
  - Implement parallel step support (multiple steps simultaneously)

- **How it integrates**: 
  - Completion detection triggers next step automatically
  - Gate evaluation determines if workflow can proceed
  - Step executor automatically starts next step
  - Works with existing workflow state management
  - Integrates with Background Agent execution

- **Success criteria**: 
  - Workflows progress automatically without manual intervention
  - Next step starts when current step completes
  - Gates are evaluated automatically
  - Failed steps handled appropriately
  - Parallel steps execute simultaneously

## Stories

1. **Story 10.1: Automatic Step Progression Foundation**
   - Implement step completion detection integration
   - Create automatic next step trigger mechanism
   - Add step progression state tracking
   - Implement progression logging
   - Acceptance criteria: Completion detected, next step triggered, state tracked, logging works

2. **Story 10.2: Gate Evaluation and Progression**
   - Implement automatic gate evaluation after step completion
   - Create gate pass/fail determination logic
   - Add automatic progression on gate pass
   - Implement gate failure handling (retry, skip, abort)
   - Acceptance criteria: Gates evaluated automatically, pass/fail determined, progression on pass, failure handled

3. **Story 10.3: Error Handling and Recovery**
   - Implement failed step detection
   - Create error recovery strategies (retry, skip, abort)
   - Add retry logic with exponential backoff
   - Implement workflow abort on critical failures
   - Acceptance criteria: Failures detected, recovery strategies work, retries execute, abort works

4. **Story 10.4: Parallel Step Execution**
   - Implement parallel step detection (steps that can run simultaneously)
   - Create parallel execution coordinator
   - Add dependency resolution (which steps can run in parallel)
   - Implement parallel completion detection
   - Acceptance criteria: Parallel steps detected, execution coordinated, dependencies resolved, completion detected

5. **Story 10.5: Progression Visibility and Control**
   - Add progression visibility (which step is next, why)
   - Create progression control (pause, resume, skip step)
   - Implement progression history (what steps executed)
   - Add progression notifications
   - Acceptance criteria: Visibility provided, control works, history tracked, notifications sent

## Compatibility Requirements

- [ ] Existing manual progression continues to work
- [ ] Auto-progression is optional (can be disabled)
- [ ] No breaking changes to workflow execution
- [ ] Works with existing step execution system
- [ ] Backward compatible with current workflows

## Risk Mitigation

- **Primary Risk**: Auto-progression may skip important steps
  - **Mitigation**: Gate evaluation, confirmation for critical steps, progression logging, user can pause
- **Primary Risk**: Failed steps may cause workflow to hang
  - **Mitigation**: Timeout mechanisms, error detection, retry logic, abort capability
- **Primary Risk**: Parallel steps may conflict
  - **Mitigation**: Worktree isolation, dependency resolution, conflict detection
- **Rollback Plan**: 
  - Disable auto-progression via configuration
  - Fall back to manual step progression
  - Remove auto-progression without breaking workflows

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Workflows progress automatically between steps
- [ ] Gates evaluated automatically
- [ ] Error handling and recovery implemented
- [ ] Parallel steps execute correctly
- [ ] Progression visibility and control available
- [ ] Comprehensive test coverage
- [ ] Documentation complete (configuration, troubleshooting)
- [ ] No regression in workflow execution
- [ ] Manual progression still works

## Implementation Status

**Last Updated:** 2025-01-27

**Overall Status:** ✅ Completed

**Story Status:**
- Story 10.1 (Progression Foundation): ✅ Completed
- Story 10.2 (Gate Evaluation): ✅ Completed
- Story 10.3 (Error Handling): ✅ Completed
- Story 10.4 (Parallel Execution): ✅ Completed (already supported via ParallelStepExecutor)
- Story 10.5 (Visibility): ✅ Completed

## Implementation Summary

### Files Created:
- `tapps_agents/workflow/auto_progression.py` - Auto-progression manager with gate evaluation, error handling, and progression tracking

### Files Modified:
- `tapps_agents/workflow/cursor_executor.py` - Integrated auto-progression for Cursor mode
- `tapps_agents/workflow/executor.py` - Integrated auto-progression for headless mode

### Key Features Implemented:

1. **Automatic Step Progression Foundation** (Story 10.1):
   - `AutoProgressionManager` class manages automatic progression
   - Step completion detection integrated with existing completion system
   - Automatic next step triggering
   - Progression state tracking and logging

2. **Gate Evaluation and Progression** (Story 10.2):
   - Automatic gate evaluation after step completion
   - Gate pass/fail determination with quality thresholds
   - Automatic progression on gate pass (routes to `on_pass` step)
   - Gate failure handling (routes to `on_fail` step or retries)

3. **Error Handling and Recovery** (Story 10.3):
   - Failed step detection
   - Error recovery strategies: retry, skip, abort
   - Retry logic with exponential backoff
   - Workflow abort on critical failures
   - Configurable retry behavior via step metadata

4. **Parallel Step Execution** (Story 10.4):
   - Already supported via `ParallelStepExecutor`
   - Enhanced to work seamlessly with auto-progression
   - Dependency resolution and parallel completion detection

5. **Progression Visibility and Control** (Story 10.5):
   - `get_progression_status()` - Current step, next step, progress metrics
   - `get_progression_history()` - History of progression decisions
   - `pause_workflow()` - Pause workflow execution
   - `resume_workflow()` - Resume paused workflow
   - `skip_step()` - Skip a specific step

### Configuration:

Auto-progression can be controlled via environment variable:
- `TAPPS_AGENTS_AUTO_PROGRESSION=true` (default) - Enable auto-progression
- `TAPPS_AGENTS_AUTO_PROGRESSION=false` - Disable auto-progression (fallback to manual)

### Usage:

Auto-progression is enabled by default. Workflows will automatically:
- Progress to next step when current step completes
- Evaluate gates and route based on results
- Retry failed steps (up to 3 attempts with exponential backoff)
- Skip steps on failure if configured
- Abort workflow on critical failures

### Backward Compatibility:

- Existing workflows continue to work
- Auto-progression is optional (can be disabled)
- No breaking changes to workflow execution
- Works with existing step execution system
- Backward compatible with current workflows

