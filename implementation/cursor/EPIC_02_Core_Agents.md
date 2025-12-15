# Epic 2: Core Agent Implementation

## Epic Goal

Implement all 11 specialized agents (5 background cloud + 5 foreground + 1 orchestrator) with Cursor cloud integration, enabling parallel execution of up to 8 agents simultaneously. This epic transforms the existing agent system into the new architecture while maintaining backward compatibility.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Existing workflow agents (analyst, architect, implementer, reviewer, tester, etc.)
- **Technology stack**: Python agents, existing skill system, Cursor integration
- **Integration points**: 
  - Existing agent base classes (`tapps_agents/agents/`)
  - Current skill invoker (`tapps_agents/workflow/skill_invoker.py`)
  - Cursor executor (`tapps_agents/workflow/cursor_executor.py`)

### Enhancement Details

- **What's being added/changed**: 
  - 5 Background Cloud Agents (Quality, Testing, Docs, Ops, Context)
  - 5 Foreground Agents (Code, Design, Review, Planning, Enhancement)
  - Cursor cloud agent configuration
  - Agent communication via file messaging (versioned, schema-validated contracts)
  - Parallel execution coordination with structured concurrency and bounded resources

- **How it integrates**: 
  - New agents extend existing agent base classes
  - Background agents use Cursor cloud infrastructure
  - Foreground agents run in Cursor IDE
  - Orchestrator coordinates all agents

- **2025 standards / guardrails**:
  - **Agent I/O contracts**: agent inputs/outputs are **typed and validated**; each agent emits machine-readable artifacts (JSON) plus optional human-readable markdown.
  - **Deterministic aggregation**: orchestrator uses stable ordering and explicit merge rules when combining multiple agent results.
  - **Cancellation & timeouts**: each agent run is cancellable, time-bounded, and emits partial progress/state.
  - **Resource hygiene**: background agents declare limits (CPU/mem/time) and avoid unbounded workspace writes.
  - **Security baseline**: redact secrets/PII in logs and artifacts; do not persist raw prompts containing secrets.

- **Success criteria**: 
  - All 11 agents implemented and functional
  - 8 agents can run in parallel
  - Results properly aggregated
  - No merge conflicts in parallel execution

## Stories

1. **Story 2.1: Background Cloud Agents - Quality & Testing**
   - Implement Quality & Analysis Agent (Ruff, mypy, Bandit, Radon)
   - Implement Testing & Coverage Agent (pytest, coverage)
   - Configure Cursor cloud execution

2. **Story 2.2: Background Cloud Agents - Docs, Ops, Context**
   - Implement Documentation Agent (markdown, API docs)
   - Implement Operations & Deployment Agent (CI/CD, Docker)
   - Implement Context & Knowledge Agent (Context7 management)

3. **Story 2.3: Foreground Agents - Code & Design**
   - Implement Code Generation Agent (feature implementation)
   - Implement Design & Architecture Agent (system design, expert consultation)
   - Configure foreground execution in Cursor IDE

4. **Story 2.4: Foreground Agents - Review, Planning, Enhancement**
   - Implement Review & Improvement Agent (5-metric scoring)
   - Implement Planning & Analysis Agent (user stories, estimation)
   - Implement Enhancement & Prompt Agent (7-stage enhancement)

5. **Story 2.5: Parallel Execution & Result Aggregation**
   - Enable 8-agent parallel execution
   - Implement result aggregation from multiple agents
   - Add conflict detection and reporting

6. **Story 2.6: Agent Contract Tests & Backward Compatibility Harness**
   - Add contract tests to ensure agent inputs/outputs remain compatible with existing workflows
   - Validate that every agent run produces required artifacts (status, outputs, errors) in agreed schemas
   - Add golden-path workflow tests that exercise mixed old/new agents

## Compatibility Requirements

- [ ] Existing agent skills remain functional
- [ ] Current workflow definitions compatible
- [ ] Agent output formats backward compatible
- [ ] No breaking changes to agent interfaces

## Risk Mitigation

- **Primary Risk**: Parallel execution causes merge conflicts or data corruption
- **Mitigation**: 
  - Git worktree isolation prevents conflicts
  - Atomic file operations for state
  - Comprehensive testing of parallel scenarios
- **Rollback Plan**: 
  - Disable parallel execution flag
  - Fall back to sequential execution
  - Existing agents continue working

## Definition of Done

- [ ] All 11 agents implemented and tested
- [ ] Cursor cloud agents configured and working
- [ ] 8 agents successfully run in parallel
- [ ] Results aggregated correctly
- [ ] No merge conflicts in parallel execution
- [ ] Existing agent functionality verified
- [ ] Documentation updated
- [ ] No regression in existing features

## Integration Verification

- **IV1**: Existing workflows execute with new agents
- **IV2**: Agent skill system continues to work
- **IV3**: Cursor integration functional for both foreground and background
- **IV4**: Performance meets targets (parallel execution faster than sequential)
