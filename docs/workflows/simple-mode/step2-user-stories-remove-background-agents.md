# Step 2: User Stories - Remove Background Agents

## User Stories

### Story 1: Remove Background Agent Implementation Modules
**As a** framework maintainer  
**I want** to remove all Background Agent implementation modules  
**So that** the codebase no longer contains Background Agent code

**Acceptance Criteria:**
- [ ] All Background Agent implementation files deleted
- [ ] No Background Agent classes remain in codebase
- [ ] Background Agent API client removed

**Story Points:** 3  
**Priority:** High

**Files:**
- `tapps_agents/workflow/background_agent_api.py`
- `tapps_agents/workflow/background_agent_config.py`
- `tapps_agents/workflow/background_agent_generator.py`
- `tapps_agents/workflow/background_auto_executor.py`
- `tapps_agents/workflow/background_context_agent.py`
- `tapps_agents/workflow/background_docs_agent.py`
- `tapps_agents/workflow/background_ops_agent.py`
- `tapps_agents/workflow/background_quality_agent.py`
- `tapps_agents/workflow/background_testing_agent.py`
- `tapps_agents/core/background_wrapper.py`

---

### Story 2: Update Workflow Executor to Remove Background Agent Routing
**As a** framework user  
**I want** workflows to use direct execution or Cursor Skills only  
**So that** Background Agents are no longer referenced in workflow execution

**Acceptance Criteria:**
- [ ] WorkflowExecutor no longer imports Background Agent modules
- [ ] Background Agent cleanup code removed from executor
- [ ] CursorWorkflowExecutor uses direct execution/Skills only
- [ ] No Background Agent routing logic remains

**Story Points:** 5  
**Priority:** High

**Files:**
- `tapps_agents/workflow/executor.py`
- `tapps_agents/workflow/cursor_executor.py`

---

### Story 3: Update Skill Invoker to Remove Background Agent API
**As a** framework user  
**I want** Skill invocations to use direct execution only  
**So that** Background Agent API is no longer used

**Acceptance Criteria:**
- [ ] SkillInvoker no longer imports Background Agent API
- [ ] Background Agent API calls removed
- [ ] Direct execution used for all skill invocations
- [ ] Background Agent-specific agent classes removed

**Story Points:** 3  
**Priority:** High

**Files:**
- `tapps_agents/workflow/skill_invoker.py`

---

### Story 4: Update CLI Commands to Remove Background Agent References
**As a** framework user  
**I want** CLI commands to not reference Background Agents  
**So that** Background Agents are completely removed from user-facing features

**Acceptance Criteria:**
- [ ] `status` command no longer shows Background Agent status
- [ ] `top_level` commands no longer reference Background Agents
- [ ] `simple_mode` commands no longer warn about Background Agents
- [ ] All Background Agent CLI options/flags removed

**Story Points:** 3  
**Priority:** Medium

**Files:**
- `tapps_agents/cli/commands/status.py`
- `tapps_agents/cli/commands/top_level.py`
- `tapps_agents/cli/commands/simple_mode.py`

---

### Story 5: Update Init Project to Remove Background Agent Configuration
**As a** framework user  
**I want** project initialization to not create Background Agent configs  
**So that** Background Agents are not set up during init

**Acceptance Criteria:**
- [ ] Init no longer creates Background Agent configurations
- [ ] Background Agent config generation code removed
- [ ] Existing background-agents.yaml remains but is empty (for reference)

**Story Points:** 2  
**Priority:** Medium

**Files:**
- `tapps_agents/core/init_project.py`

---

### Story 6: Update Health Checker to Remove Background Agent Validation
**As a** framework maintainer  
**I want** health checks to not validate Background Agent configuration  
**So that** Background Agents are not checked in health checks

**Acceptance Criteria:**
- [ ] Health checker no longer validates Background Agent config
- [ ] Background Agent config validator imports removed
- [ ] Health check passes without Background Agents

**Story Points:** 2  
**Priority:** Low

**Files:**
- `tapps_agents/workflow/health_checker.py`

---

### Story 7: Update Module Imports and Exports
**As a** framework maintainer  
**I want** module __init__ files to not export Background Agent classes  
**So that** Background Agents are not accessible from package imports

**Acceptance Criteria:**
- [ ] `workflow/__init__.py` no longer exports Background Agent classes
- [ ] All Background Agent imports removed from __init__ files
- [ ] Package imports work correctly

**Story Points:** 2  
**Priority:** Medium

**Files:**
- `tapps_agents/workflow/__init__.py`

---

### Story 8: Remove Background Agent Tests
**As a** framework maintainer  
**I want** Background Agent tests removed  
**So that** test suite no longer includes Background Agent tests

**Acceptance Criteria:**
- [ ] All Background Agent test files deleted
- [ ] Tests that depend on Background Agents updated or removed
- [ ] Test suite runs successfully

**Story Points:** 3  
**Priority:** High

**Files:**
- `tests/unit/workflow/test_background_agent_generator.py`
- `tests/unit/workflow/test_background_auto_executor.py`
- `tests/integration/workflow/test_background_agents.py`
- Update any tests that import Background Agent modules

---

### Story 9: Update Documentation
**As a** framework user  
**I want** documentation updated to reflect Background Agents removal  
**So that** users understand Background Agents are no longer available

**Acceptance Criteria:**
- [ ] Background Agent guides updated or removed
- [ ] README updated to remove Background Agent references
- [ ] Architecture docs updated
- [ ] Command reference updated
- [ ] Migration guide created if needed

**Story Points:** 5  
**Priority:** Medium

**Files:**
- `docs/BACKGROUND_AGENTS_GUIDE.md`
- `docs/BACKGROUND_AGENTS_MIGRATION_GUIDE.md`
- `docs/BACKGROUND_AGENTS_TROUBLESHOOTING.md`
- `docs/BACKGROUND_AGENTS_USE_CASE_GUIDE.md`
- `README.md`
- `.cursor/rules/quick-reference.mdc`
- `.cursor/rules/command-reference.mdc`
- `docs/ARCHITECTURE.md`

---

### Story 10: Update Fallback Strategy if Needed
**As a** framework maintainer  
**I want** fallback strategy to not reference Background Agents  
**So that** fallback logic works without Background Agents

**Acceptance Criteria:**
- [ ] FallbackStrategy checked for Background Agent references
- [ ] Background Agent routing removed if present
- [ ] Fallback works correctly

**Story Points:** 2  
**Priority:** Low

**Files:**
- `tapps_agents/core/fallback_strategy.py`

---

## Story Dependencies

```
Story 1 (Remove Modules)
  ↓
Story 2 (Update Executor) ──┐
Story 3 (Update Skill Invoker) ──┤
Story 4 (Update CLI) ──┤
Story 5 (Update Init) ──┤
Story 6 (Update Health) ──┤
Story 7 (Update Imports) ──┤
Story 10 (Update Fallback) ──┤
  ↓
Story 8 (Remove Tests)
  ↓
Story 9 (Update Docs)
```

## Total Story Points: 30

## Execution Order

1. Story 1: Remove Background Agent Implementation Modules (foundation)
2. Stories 2-7, 10: Update dependent code (can be parallel)
3. Story 8: Remove/update tests
4. Story 9: Update documentation (final)
