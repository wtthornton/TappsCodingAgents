# Epic 1: Foundation & Orchestration Infrastructure

## Epic Goal

Establish the core infrastructure for the new 11-agent architecture, including git worktree management, orchestration agent, and file-based communication system. This foundation enables parallel agent execution and sets up the coordination layer required for all subsequent agent work.

## Epic Description

### Existing System Context

- **Current relevant functionality**: TappsCodingAgents has existing workflow agents and execution system
- **Technology stack**: Python 3.13+, Git, existing agent framework
- **Integration points**: 
  - Existing workflow executor (`tapps_agents/workflow/executor.py`)
  - Current agent implementations in `tapps_agents/agents/`
  - Existing state management (`tapps_agents/workflow/state_manager.py`)

### Enhancement Details

- **What's being added/changed**: 
  - Git worktree management system for agent isolation
  - Workflow Orchestration Agent implementation
  - File-based inbox/outbox messaging system (versioned, schema-validated, durable)
  - YAML workflow parser and dependency graph resolver
  - Basic worktree merge and conflict resolution

- **How it integrates**: 
  - New orchestration layer coordinates existing agents
  - Worktree system provides isolation without breaking existing workflows
  - File messaging integrates with existing state management
  - YAML workflows extend current workflow system

- **2025 standards / guardrails**:
  - **Structured concurrency**: orchestrator uses `asyncio.TaskGroup` for parallel agent execution, cancellation, and timeouts.
  - **Message contracts**: JSON messages are **versioned** and **validated** (e.g., schema/typed models) to prevent silent drift.
  - **Durability & safety**: atomic writes (write-then-rename), fsync on critical state, and idempotent handlers to tolerate retries.
  - **Failure isolation**: dead-letter/quarantine folder for unprocessable messages + replay tooling.
  - **Observability baseline**: correlation IDs across workflow/task/message; structured logs from day 1.

- **Success criteria**: 
  - Orchestrator can route tasks to 2-3 agents in parallel
  - Worktrees auto-created and cleaned up
  - Simple workflow completes end-to-end
  - No regression in existing agent functionality

## Stories

1. **Story 1.1: Git Worktree Management System**
   - Implement worktree creation, cleanup, and branch management
   - Create worktree manager class with isolation support
   - Add worktree lifecycle hooks

2. **Story 1.2: File-Based Messaging Infrastructure**
   - Implement inbox/outbox JSON message system with **message versioning**
   - Define and enforce message schemas (task assignment/status/completion), including required IDs and timestamps
   - Ensure reliability: atomic write/rename, idempotency keys, retries with backoff, and dead-letter/quarantine handling
   - Add message polling and status tracking (including timeout + stuck-task detection)

3. **Story 1.3: Workflow Orchestration Agent Core**
   - Implement task routing and dependency management
   - Create dependency graph builder
   - Add task execution coordination with cancellation/timeouts and bounded concurrency

4. **Story 1.4: YAML Workflow Parser**
   - Parse YAML workflow definitions
   - Validate workflow structure (schema + cross-reference validation)
   - Generate dependency graphs from YAML

5. **Story 1.5: Worktree Merge & Conflict Resolution**
   - Implement worktree branch merging
   - Add conflict detection
   - Create basic conflict resolution (manual for now)

6. **Story 1.6: Correlation IDs & Baseline Observability**
   - Add consistent IDs for workflow/task/agent/message across state + artifacts
   - Ensure orchestrator emits structured logs for lifecycle events (start/finish/fail/retry)
   - Add minimal counters/timers for task latency and retry rates (to support later dashboards)

## Compatibility Requirements

- [ ] Existing agent APIs remain unchanged during foundation phase
- [ ] Current workflow execution continues to work
- [ ] No breaking changes to existing state management
- [ ] Git operations don't interfere with main branch

## Risk Mitigation

- **Primary Risk**: Worktree operations could corrupt git repository
- **Mitigation**: 
  - Comprehensive testing of worktree operations
  - Safe cleanup procedures
  - Rollback mechanisms for failed worktrees
- **Rollback Plan**: 
  - Remove all worktrees: `git worktree prune`
  - Revert orchestration changes
  - Existing system continues unchanged

## Definition of Done

- [ ] All stories completed with acceptance criteria met
- [ ] Orchestrator successfully routes tasks to 2-3 agents
- [ ] Worktrees created and cleaned up automatically
- [ ] Simple YAML workflow executes end-to-end
- [ ] Existing agent functionality verified through testing
- [ ] Integration points working correctly
- [ ] Documentation updated appropriately
- [ ] No regression in existing features

## Integration Verification

- **IV1**: Existing workflows still execute successfully
- **IV2**: New orchestration layer doesn't break current agent calls
- **IV3**: Git repository remains in clean state after worktree operations
- **IV4**: Performance impact is minimal (<5% overhead)
