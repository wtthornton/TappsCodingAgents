# Full SDLC Workflow Execution Architecture

**Complete documentation of how the Full SDLC workflow executes with parallel tasks and background agents**

---

## Executive Summary

The **Full SDLC Pipeline** workflow (`full-sdlc`) uses **both parallel execution and background agents** to maximize efficiency:

- ✅ **Parallel Execution**: Up to 5 steps execute simultaneously after `implementation` completes
- ✅ **Background Agents**: Steps execute via Background Agents in Cursor mode when auto-execution is enabled
- ✅ **Combined**: Multiple Background Agents run in parallel, executing independent workflow steps concurrently

---

## Execution Flow

### High-Level Call Tree

```
WorkflowExecutor.execute()
  |
  +--[ROUTE] is_cursor_mode() -> True
  |
  +--[ROUTE] _route_to_cursor_executor()
     |
     +-- CursorWorkflowExecutor.__init__()
     |  |
     |  +-- ParallelStepExecutor(max_parallel=8)  [PARALLEL EXECUTOR]
     |  +-- BackgroundAgentAutoExecutor()         [BACKGROUND AGENTS]
     |  +-- SkillInvoker()                         [SKILL INVOCATION]
     |
     +-- CursorWorkflowExecutor.run()
        |
        +--[LOOP] while workflow.status == 'running':
           |
           +-- _find_ready_steps()
           |  |
           |  +-- parallel_executor.find_ready_steps()
           |     |
           |     +--[FOUND] 5 ready steps after 'implementation':
           |        |
           |        +-- review (requires: ['src/'])
           |        +-- testing (requires: ['src/'])
           |        +-- security (requires: ['src/'])
           |        +-- documentation (requires: ['src/'])
           |        +-- complete (requires: [])
           |
           +--[PARALLEL] parallel_executor.execute_parallel()
              |
              +-- asyncio.Semaphore(8)  [MAX 8 CONCURRENT]
              |
              +--[CREATE TASKS] for each ready step:
              |
              +--[TASK 1] execute_with_retries(review)
              |  |
              |  +-- async with semaphore:
              |  |
              |  +-- _execute_step_for_parallel(review)
              |     |
              |     +-- worktree_manager.create_worktree()
              |     |
              |     +--[IF] use_auto_execution:
              |        |
              |        +-- BackgroundAgentAutoExecutor.execute_command()
              |           |
              |           +-- Creates .cursor-skill-command.txt
              |           |
              |           +--[BACKGROUND AGENT] Picks up command file
              |           |
              |           +--[POLL] Waits for completion artifacts
              |
              +--[TASK 2-4] Same structure for testing, security, documentation [PARALLEL]
              |
              +--[WAIT] asyncio.gather(*tasks)  [ALL RUN IN PARALLEL]
                 |
                 +-- Returns when ALL tasks complete
           |
           +-- _process_parallel_results()
           |
           +-- Updates state with all results
```

---

## Parallel Execution Details

### When Parallel Execution Occurs

After the `implementation` step completes (creates `src/`), **5 steps are ready to execute in parallel**:

1. **review** - Requires: `['src/']`
2. **testing** - Requires: `['src/']`
3. **security** - Requires: `['src/']`
4. **documentation** - Requires: `['src/']`
5. **complete** - Requires: `[]`

All these steps only depend on `src/` and don't depend on each other, so they can run simultaneously.

### Code Implementation

**Entry Point:**
- `tapps_agents/workflow/executor.py:358` - `WorkflowExecutor.execute()`

**Routing:**
- `tapps_agents/workflow/executor.py:377` - Routes to `CursorWorkflowExecutor` if in Cursor mode

**Parallel Execution:**
- `tapps_agents/workflow/cursor_executor.py:82` - `ParallelStepExecutor(max_parallel=8)`
- `tapps_agents/workflow/cursor_executor.py:422` - `parallel_executor.execute_parallel()`
- `tapps_agents/workflow/parallel_executor.py:173` - `execute_parallel()` method
- `tapps_agents/workflow/parallel_executor.py:197` - `asyncio.Semaphore(8)`
- `tapps_agents/workflow/parallel_executor.py:323-324` - **ACTUAL PARALLEL EXECUTION**:
  ```python
  tasks = [execute_with_retries(step) for step in steps]
  task_results = await asyncio.gather(*tasks, return_exceptions=True)
  ```

### Configuration

- **Max Parallel Steps**: 8 (configurable via `ParallelStepExecutor`)
- **Per-Step Timeout**: 3600 seconds (1 hour)
- **Bounded Concurrency**: Uses `asyncio.Semaphore` to limit concurrent execution

---

## Background Agent Integration

### How Background Agents Are Used

In **Cursor mode**, the Full SDLC workflow uses Background Agents for step execution:

1. **Auto-Execution Check**: `tapps_agents/workflow/cursor_executor.py:841` - Checks if auto-execution is enabled
2. **Command Execution**: `tapps_agents/workflow/cursor_executor.py:870` - Calls `auto_executor.execute_command()`
3. **Background Agent**: `tapps_agents/workflow/background_auto_executor.py` - `BackgroundAgentAutoExecutor` class

### Execution Flow

For each parallel step:

1. **Worktree Creation**: Each step gets its own isolated worktree
2. **Command File Creation**: Creates `.cursor-skill-command.txt` with the skill command
3. **Background Agent Pickup**: Background Agent watches for command files and picks them up
4. **Execution**: Background Agent executes the command in the worktree
5. **Polling**: Executor polls for completion artifacts
6. **Completion**: When artifacts are detected, step is marked complete

### Multiple Background Agents in Parallel

When multiple steps are ready:
- Each step creates its own command file in its own worktree
- Multiple Background Agents can pick up different command files simultaneously
- All Background Agents execute in parallel (up to `max_parallel_agents` limit)
- Executor waits for all steps to complete via `asyncio.gather()`

---

## Step Dependencies

### Full SDLC Workflow Steps

```yaml
requirements    → requires: []
planning        → requires: ['requirements.md']
design          → requires: ['requirements.md', 'stories/']
api_design      → requires: ['architecture.md']
implementation  → requires: ['architecture.md', 'api-specs/', 'stories/']
                ↓ creates: ['src/']
review          → requires: ['src/']          [PARALLEL]
testing         → requires: ['src/']          [PARALLEL]
security        → requires: ['src/']          [PARALLEL]
documentation   → requires: ['src/']          [PARALLEL]
complete        → requires: []                [PARALLEL]
```

### Parallel Execution Opportunities

**After `implementation` completes:**
- 5 steps become ready simultaneously
- All execute in parallel (up to 8 concurrent limit)
- Each uses its own worktree for isolation
- Each can use Background Agents for execution

---

## Function Signatures

### Key Functions

```python
WorkflowExecutor.execute(
    self, 
    workflow: Workflow | None = None, 
    target_file: str | None = None, 
    max_steps: int = 50
) -> WorkflowState

CursorWorkflowExecutor.run(
    self, 
    workflow: Workflow | None = None, 
    target_file: str | None = None, 
    max_steps: int = 100
) -> WorkflowState

ParallelStepExecutor.execute_parallel(
    self, 
    steps: list[WorkflowStep], 
    execute_fn: Callable[[WorkflowStep], Any], 
    *, 
    state: WorkflowState, 
    timeout_seconds: float | None = None
) -> list[StepExecutionResult]

BackgroundAgentAutoExecutor.execute_command(
    self,
    command: str,
    worktree_path: Path,
    workflow_id: str,
    step_id: str,
    expected_artifacts: list[str] | None = None,
) -> dict[str, Any]
```

---

## Configuration

### Enabling Parallel Execution

Parallel execution is **automatic** - no configuration needed. The executor:
- Analyzes step dependencies
- Finds ready steps
- Executes them in parallel automatically

### Enabling Background Agents

**In Cursor mode**, Background Agents are used when:
1. `TAPPS_AGENTS_MODE=cursor` (or auto-detected)
2. Auto-execution is enabled in workflow or config
3. Background Agents are configured in `.cursor/background-agents.yaml`

**Configuration Example:**
```yaml
# .tapps-agents/config.yaml
workflow:
  auto_execution_enabled: true
  polling_interval: 5.0
  timeout_seconds: 3600
```

---

## Performance Benefits

### Sequential vs Parallel Execution

**Sequential Execution** (if parallel was disabled):
- Total time: `review_time + testing_time + security_time + documentation_time`
- Example: `300s + 600s + 120s + 180s = 1200s` (20 minutes)

**Parallel Execution** (current):
- Total time: `max(review_time, testing_time, security_time, documentation_time)`
- Example: `max(300s, 600s, 120s, 180s) = 600s` (10 minutes)
- **50% faster** in this example

### Background Agent Benefits

- **Non-blocking**: Workflow doesn't wait for Background Agents to return
- **Isolated**: Each step runs in its own worktree
- **Scalable**: Multiple Background Agents can run simultaneously
- **Resilient**: Background Agents can retry on failure

---

## Monitoring and Debugging

### Execution State

Workflow state is tracked in:
- `.tapps-agents/workflow-state/{workflow_id}/state.json`
- Step executions with timestamps
- Parallel execution results

### Logging

Key log points:
- `tapps_agents/workflow/cursor_executor.py` - Workflow execution logs
- `tapps_agents/workflow/parallel_executor.py` - Parallel execution logs
- `tapps_agents/workflow/background_auto_executor.py` - Background Agent logs

### Progress Tracking

- Progress files: `.tapps-agents/reports/progress-{task-id}.json`
- Step execution timestamps in state
- Parallel execution metrics

---

## Best Practices

### 1. Dependency Design

**Good**: Steps that can run in parallel have minimal dependencies
```yaml
- id: review
  requires: [src/]  # Can run in parallel with...
  
- id: testing
  requires: [src/]  # ...this step
```

**Avoid**: Unnecessary dependencies that force sequential execution
```yaml
- id: testing
  requires: [src/, review-report.md]  # Unnecessary dependency
```

### 2. Worktree Management

- Each parallel step gets its own worktree
- Worktrees are cleaned up after completion
- Manual cleanup: `git worktree remove .tapps-agents/worktrees/{worktree-name}`

### 3. Background Agent Configuration

- Configure Background Agents in `.cursor/background-agents.yaml`
- Set appropriate `max_parallel_agents` limit
- Monitor Background Agent execution via Cursor UI

---

## Troubleshooting

### Parallel Execution Not Working

1. **Check dependencies**: Steps must have no dependencies on each other
2. **Check max_parallel**: Ensure limit is high enough
3. **Check logs**: Review parallel executor logs

### Background Agents Not Executing

1. **Check runtime mode**: Must be in Cursor mode (`TAPPS_AGENTS_MODE=cursor`)
2. **Check auto-execution**: Must be enabled in config
3. **Check Background Agents**: Must be configured in `.cursor/background-agents.yaml`
4. **Check command files**: Look for `.cursor-skill-command.txt` files in worktrees

### Performance Issues

1. **Check parallel limit**: Increase `max_parallel` if needed
2. **Check Background Agent limit**: Increase `max_parallel_agents` in config
3. **Check worktree disk space**: Each worktree uses disk space
4. **Check timeout settings**: Ensure timeouts are appropriate

---

## Related Documentation

- [Workflow Parallel Execution](WORKFLOW_PARALLEL_EXECUTION.md) - General parallel execution guide
- [Background Agents Guide](BACKGROUND_AGENTS_GUIDE.md) - Background Agents setup and usage
- [Background Agent Auto-Execution](BACKGROUND_AGENTS_AUTO_EXECUTION_GUIDE.md) - Auto-execution details
- [Cursor Background Agents Research](CURSOR_BACKGROUND_AGENTS_RESEARCH.md) - Research findings
- [Parallel Execution Optimization 2025](PARALLEL_EXECUTION_OPTIMIZATION_2025.md) - Optimization recommendations and best practices

---

## Summary

The Full SDLC workflow demonstrates the power of combining:
- **Parallel Execution**: Automatic detection and execution of independent steps
- **Background Agents**: Asynchronous, non-blocking step execution
- **Isolation**: Each step runs in its own worktree
- **Scalability**: Up to 8 steps can run concurrently

This architecture enables efficient, scalable workflow execution while maintaining isolation and reliability.

