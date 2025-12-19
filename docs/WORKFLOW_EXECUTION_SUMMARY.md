# Workflow Execution Summary

**Quick reference for workflow execution features**

---

## Parallel Execution

✅ **All workflows support automatic parallel execution**

- Independent steps execute simultaneously (up to 8 concurrent by default)
- Dependency-based execution - steps wait for dependencies before running
- No configuration needed - automatic detection and execution

**Example: Full SDLC Workflow**
- After `implementation` completes, 5 steps run in parallel:
  - `review`, `testing`, `security`, `documentation`, `complete`
- All only require `src/` and don't depend on each other

**See:** [Workflow Parallel Execution](WORKFLOW_PARALLEL_EXECUTION.md)

---

## Background Agents

✅ **Workflows use Background Agents in Cursor mode**

- Steps execute via Background Agents when auto-execution is enabled
- Non-blocking execution - workflow doesn't wait for Background Agents
- Multiple Background Agents can run in parallel
- Isolated execution in separate worktrees

**Configuration:**
- Enable in `.tapps-agents/config.yaml`: `workflow.auto_execution_enabled: true`
- Background Agents configured in `.cursor/background-agents.yaml`

**See:** 
- [Background Agents Guide](BACKGROUND_AGENTS_GUIDE.md)
- [Background Agent Auto-Execution](BACKGROUND_AGENTS_AUTO_EXECUTION_GUIDE.md)

---

## Full SDLC Workflow

✅ **Combines parallel execution + Background Agents**

The Full SDLC workflow demonstrates both features working together:

1. **Parallel Execution**: 5 steps execute simultaneously after implementation
2. **Background Agents**: Each step executes via Background Agents in Cursor mode
3. **Isolation**: Each step runs in its own worktree
4. **Performance**: Up to 50% faster than sequential execution

**See:** [Full SDLC Execution Architecture](FULL_SDLC_EXECUTION_ARCHITECTURE.md) - Complete documentation with call tree and code references

---

## Quick Links

- [Workflow Parallel Execution](WORKFLOW_PARALLEL_EXECUTION.md) - General parallel execution guide
- [Full SDLC Execution Architecture](FULL_SDLC_EXECUTION_ARCHITECTURE.md) - Complete Full SDLC execution documentation
- [Background Agents Guide](BACKGROUND_AGENTS_GUIDE.md) - Background Agents setup
- [Background Agent Auto-Execution](BACKGROUND_AGENTS_AUTO_EXECUTION_GUIDE.md) - Auto-execution details
- [Cursor Background Agents Research](CURSOR_BACKGROUND_AGENTS_RESEARCH.md) - Research findings

