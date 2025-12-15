# Epic 5: YAML Workflow Orchestration Engine

## Epic Goal

Implement comprehensive YAML-based workflow orchestration engine with dependency resolution, parallel task execution, and workflow state management. This epic enables complex multi-stage workflows with proper dependency handling.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Existing workflow system (`tapps_agents/workflow/`)
- **Technology stack**: YAML parsing, workflow executor, state manager
- **Integration points**: 
  - Workflow executor (`tapps_agents/workflow/executor.py`)
  - State manager (`tapps_agents/workflow/state_manager.py`)
  - Existing workflow definitions

### Enhancement Details

- **What's being added/changed**: 
  - YAML workflow parser and validator
  - Dependency graph resolver
  - Parallel task execution engine (structured concurrency, retries, cancellation)
  - Workflow state persistence (resumable, auditable)
  - Progress monitoring and reporting (events + metrics)

- **How it integrates**: 
  - Extends existing workflow executor
  - YAML workflows complement current workflow system
  - State management enhanced for workflow tracking
  - Orchestrator coordinates workflow execution

- **2025 standards / guardrails**:
  - **Schema-first workflows**: validate YAML against a versioned schema + cross-reference validation.
  - **Determinism**: stable topological ordering for “ready” tasks to keep runs reproducible.
  - **Resumability**: append-only event log for workflow execution to support resume/debug/audit.
  - **Safety**: timeouts, cancellation propagation, bounded concurrency, and idempotent step execution.

- **Success criteria**: 
  - Complex workflows execute correctly
  - Dependencies respected
  - State persists across runs
  - 3-5 standard workflows created

## Stories

1. ✅ **Story 5.1: YAML Workflow Parser & Validator** (Completed 2025-12-14)
   - ✅ Implement YAML schema validation (`schema_validator.py` with versioned schemas)
   - ✅ Parse workflow definitions (enhanced `parser.py` with schema validation)
   - ✅ Validate dependency references (cross-reference validation for `next`, `optional_steps`, `gate.on_pass`, `gate.on_fail`)
   - **Status**: Schema-first validation operational with versioned schema support (v1.0, v2.0)

2. ✅ **Story 5.2: Dependency Graph Resolver** (Completed 2025-12-14)
   - ✅ Build dependency graphs from YAML (`dependency_resolver.py` with `DependencyGraph`)
   - ✅ Resolve task execution order (topological sort via `resolve_execution_order()`)
   - ✅ Detect circular dependencies (`detect_cycles()` method)
   - **Status**: Dependency resolution operational with cycle detection and stable topological ordering

3. ✅ **Story 5.3: Parallel Task Execution Engine** (Completed 2025-12-14)
   - ✅ Execute independent tasks in parallel (existing `ParallelStepExecutor` enhanced)
   - ✅ Manage task concurrency (max 8, configurable via `max_parallel`)
   - ✅ Handle task failures and retries (exponential backoff via `RetryConfig`, configurable per-step via metadata)
   - ✅ Implement cancellation + per-step timeouts with structured concurrency (existing timeout support enhanced with retries)
   - **Status**: Parallel execution with retries and exponential backoff operational

4. ✅ **Story 5.4: Workflow State Management** (Completed 2025-12-14)
   - ✅ Persist workflow state across runs (existing `AdvancedStateManager` leveraged)
   - ✅ Track task completion status (existing state tracking enhanced)
   - ✅ Enable workflow resumption (existing resume functionality maintained)
   - ✅ Add an append-only workflow event log (`event_log.py` with `WorkflowEventLog` for start/finish/fail/skip events)
   - **Status**: Append-only event log integrated into executor with durable JSONL storage

5. ✅ **Story 5.5: Standard Workflow Templates** (Completed 2025-12-14)
   - ✅ Create feature-implementation workflow (`workflows/presets/feature-implementation.yaml`)
   - ✅ Create full-sdlc workflow (existing `workflows/presets/full-sdlc.yaml` verified)
   - ✅ Create quick-fix workflow (existing `workflows/presets/quick-fix.yaml` verified)
   - ✅ Add workflow progress monitoring (`progress_monitor.py` with `WorkflowProgressMonitor` and `get_progress()` method in executor)
   - **Status**: All standard workflow templates created and progress monitoring operational

## Compatibility Requirements

- [x] Existing workflow definitions remain functional
- [x] YAML workflows optional (current system works)
- [x] No breaking changes to workflow executor
- [x] State management backward compatible

## Risk Mitigation

- **Primary Risk**: Complex workflows fail or deadlock
- **Mitigation**: 
  - Comprehensive dependency validation
  - Timeout mechanisms for tasks
  - Deadlock detection
  - Workflow rollback capabilities
- **Rollback Plan**: 
  - Disable YAML workflow engine
  - Use existing workflow system
  - No impact on current workflows

## Definition of Done

- [x] YAML workflow parser operational (with schema validation)
- [x] Dependency resolution works correctly (topological sort + cycle detection)
- [x] Parallel execution respects dependencies (bounded concurrency with retries)
- [x] Workflow state persists correctly (enhanced with event log)
- [x] 3-5 standard workflows created and tested (feature-implementation, full-sdlc, quick-fix)
- [x] Complex workflows execute successfully (dependency resolution + parallel execution)
- [x] Documentation updated (new modules exported in `__init__.py`)
- [x] No regression in existing features (backward compatible)

## Integration Verification

- **IV1**: YAML workflows execute successfully
- **IV2**: Dependencies resolved correctly
- **IV3**: Parallel execution works as expected
- **IV4**: Workflow state management functional
