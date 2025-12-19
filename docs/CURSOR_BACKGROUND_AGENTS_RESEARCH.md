# Cursor Background Agents Research

## Executive Summary

**Answer: Background Agents run asynchronously and do NOT block. You can run other tasks in parallel without waiting for them to return.**

---

## Key Findings

### 1. Asynchronous & Non-Blocking Execution

**Background Agents are designed to run asynchronously** - they execute tasks in isolated environments without blocking your workflow or other operations.

**Evidence:**
- From Cursor documentation: "Background Agents run tasks asynchronously in isolated environments, allowing multiple agents to operate concurrently without waiting for each other to complete"
- The project's `BackgroundAgentAPI.trigger_agent()` method returns immediately with a `job_id` - it does not wait for completion
- A separate `wait_for_completion()` method exists if you explicitly need to wait (opt-in behavior)

### 2. Parallel Execution Support

**Multiple Background Agents can run simultaneously** up to a configured limit.

**Project Configuration:**
```yaml
global:
  max_parallel_agents: 4  # Up to 4 agents can run concurrently
  timeout_seconds: 3600   # 1 hour timeout per agent
```

**Implementation Details:**
- The project uses `asyncio.Semaphore` to limit concurrent executions
- Each agent gets its own isolated worktree to prevent file conflicts
- Parallel execution is handled via `asyncio.gather()` in the orchestrator

### 3. Isolation Mechanism

**Each Background Agent runs in its own isolated environment:**

- **Git Worktrees**: Each agent gets a separate worktree (e.g., `.tapps-agents/worktrees/{agent-id}/`)
- **Isolated Branches**: Agents work on separate branches (`agent/{agent-id}`)
- **No File Conflicts**: Isolation prevents concurrent agents from interfering with each other
- **Shared Context**: Only the Git repository state is shared (via merges)

### 4. Execution Model

**Fire-and-Forget Pattern:**

```python
# Trigger agent (returns immediately)
result = api.trigger_agent(agent_id, command)
job_id = result["job_id"]  # Get job ID for tracking

# Continue with other work - agent runs in background
# ... do other tasks ...

# Optionally wait for completion (if needed)
if need_results:
    final_result = api.wait_for_completion(job_id, timeout=3600)
```

**Key Points:**
- `trigger_agent()` returns immediately (non-blocking)
- You get a `job_id` for tracking/monitoring
- `wait_for_completion()` is optional - only use if you need results before proceeding
- Progress can be monitored via progress files without blocking

### 5. Progress Monitoring (Non-Blocking)

**You can monitor progress without blocking:**

- **Progress Files**: `.tapps-agents/reports/progress-{task-id}.json`
- **Cursor UI**: Background Agents panel shows real-time progress
- **Status API**: `get_agent_status(job_id)` for programmatic checking
- **Polling**: Check status periodically without blocking execution

### 6. Result Delivery

**Results are delivered asynchronously:**

- **File Delivery**: Results saved to `.tapps-agents/reports/` (default)
- **PR Delivery**: Optional PR creation (explicit opt-in)
- **Web App**: Optional web interface for results
- **No Blocking**: Results available when ready, no need to wait

---

## Project-Specific Implementation

### Current Configuration

The project has **4 Background Agents** configured:

1. **Quality Analyzer** - Quality analysis, linting, type-checking
2. **Test Runner** - Test execution and coverage
3. **Security Auditor** - Security scanning and dependency auditing
4. **PR Mode** - Verification and PR creation (opt-in)

### Parallel Execution Example

From `tapps_agents/core/multi_agent_orchestrator.py`:

```python
async def execute_parallel(
    self, agent_tasks: list[dict[str, Any]], task_id: str | None = None
) -> dict[str, Any]:
    # Create worktrees for each agent
    worktree_paths = {}
    for task in agent_tasks:
        worktree_path = self.worktree_manager.create_worktree(...)
        worktree_paths[agent_id] = worktree_path
    
    # Execute agents in parallel with semaphore limit
    semaphore = asyncio.Semaphore(self.max_parallel)
    
    async def execute_agent_task(task):
        async with semaphore:
            # Execute agent task (non-blocking)
            return await self.execute_task(task)
    
    # Run all tasks in parallel
    results = await asyncio.gather(*[
        execute_agent_task(task) for task in agent_tasks
    ])
```

### Triggering Agents

**Method 1: Natural Language (Cursor UI)**
```
"Analyze project quality"
"Run security scan"
"Run tests"
```

**Method 2: Programmatic (API)**
```python
api = BackgroundAgentAPI()
result = api.trigger_agent(
    agent_id="quality-analyzer",
    command="python -m tapps_agents.cli reviewer analyze-project"
)
# Returns immediately with job_id
```

**Method 3: File-Based (Watch Paths)**
- Agents can watch for command files (`.cursor-skill-command.txt`)
- Automatically execute when files are detected
- Useful for workflow automation

---

## Best Practices

### ✅ DO: Use Background Agents For

- Long-running tasks (analysis, testing, security scans)
- Independent tasks that don't need immediate results
- Tasks that can run in parallel
- Heavy operations that would block your workflow

### ❌ DON'T: Use Background Agents For

- Tasks that need immediate results
- Tasks with strict dependencies (unless properly sequenced)
- Quick operations (use regular skills instead)
- Tasks that require interactive input

### 🔄 Parallel Execution Guidelines

1. **Independent Tasks**: Agents can run in parallel if tasks are independent
2. **Dependencies**: If tasks depend on each other, structure them so shared work completes first
3. **Resource Limits**: Respect `max_parallel_agents` limit (default: 4)
4. **Worktree Cleanup**: Regularly clean up unused worktrees

### 📊 Monitoring Without Blocking

```python
# Trigger agent
job_id = api.trigger_agent(agent_id, command)["job_id"]

# Continue with other work
do_other_tasks()

# Check status periodically (non-blocking)
while True:
    status = api.get_agent_status(job_id)
    if status["status"] == "completed":
        results = api.get_agent_results(job_id)
        break
    time.sleep(5)  # Poll every 5 seconds
```

---

## Technical Details

### API Methods (Non-Blocking)

1. **`trigger_agent()`** - Starts agent, returns immediately with `job_id`
2. **`get_agent_status()`** - Check status without blocking
3. **`get_agent_results()`** - Get results when ready
4. **`wait_for_completion()`** - **Only blocking method** (opt-in)

### Worktree Isolation

- **Base Directory**: `.tapps-agents/worktrees/`
- **Per Agent**: `.tapps-agents/worktrees/{agent-id}/`
- **Branch Names**: `agent/{agent-id}`
- **Cleanup**: Automatic or manual via `git worktree remove`

### Context7 Cache Sharing

- **Location**: `.tapps-agents/kb/context7-cache`
- **Shared**: Between Sidebar Skills and Background Agents
- **Auto-Sync**: Cache synced on agent startup
- **Hit Rate**: 90%+ with pre-populated cache

---

## Summary

**Question: Does a Background Agent have to wait for it to return or can it run other things in parallel?**

**Answer: Background Agents are completely asynchronous and non-blocking. You can:**
- ✅ Trigger multiple agents simultaneously (up to `max_parallel_agents` limit)
- ✅ Continue working on other tasks immediately after triggering
- ✅ Monitor progress without blocking
- ✅ Get results when ready (asynchronously)
- ✅ Run other operations in parallel

**The only time you wait is if you explicitly call `wait_for_completion()` - and that's optional.**

---

## References

- [Cursor Background Agents Documentation](https://docs.cursor.com/en/background-agents)
- Project: `.cursor/background-agents.yaml`
- Project: `docs/BACKGROUND_AGENTS_GUIDE.md`
- Project: `tapps_agents/workflow/background_agent_api.py`
- Project: `tapps_agents/core/multi_agent_orchestrator.py`

