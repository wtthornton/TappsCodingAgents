# Workflow Parallel Execution Research

## Executive Summary

**Answer: YES - All prebuilt workflows support parallel execution automatically. Steps that have no dependencies on each other will run in parallel (up to 8 concurrent steps by default).**

---

## Key Findings

### 1. Automatic Parallel Execution

**All workflows automatically execute independent steps in parallel** - you don't need to configure anything special.

**How It Works:**
- The workflow executor analyzes step dependencies (`requires` field)
- Steps with no dependencies or whose dependencies are met are considered "ready"
- All "ready" steps execute simultaneously (up to `max_parallel` limit)
- Steps wait for their dependencies before executing

**Evidence from Code:**
```python
# From tapps_agents/workflow/cursor_executor.py
# Find steps ready to execute (dependencies met)
ready_steps = self._find_ready_steps(
    completed_step_ids, running_step_ids
)

# Execute ready steps in parallel
results = await self.parallel_executor.execute_parallel(
    steps=ready_steps,
    execute_fn=execute_step_wrapper,
    state=self.state,
)
```

### 2. Default Parallel Limits

**Default Configuration:**
- **Max Parallel Steps**: 8 (configurable via `ParallelStepExecutor`)
- **Per-Step Timeout**: 3600 seconds (1 hour)
- **Bounded Concurrency**: Uses `asyncio.Semaphore` to limit concurrent execution

**From `tapps_agents/workflow/parallel_executor.py`:**
```python
def __init__(
    self,
    max_parallel: int = 8,  # Default: 8 concurrent steps
    default_timeout_seconds: float | None = 3600.0,
    ...
):
```

### 3. Dependency-Based Execution

**Steps execute in parallel when:**
- They have no `requires` dependencies
- All their `requires` dependencies are already completed
- They don't depend on each other

**Example from `full-sdlc.yaml`:**
```yaml
# These steps run sequentially (each depends on previous)
- id: requirements
  requires: []  # Can start immediately
  
- id: planning
  requires: [requirements.md]  # Waits for requirements
  
- id: design
  requires: [requirements.md, stories/]  # Waits for both

# But if multiple steps only require the same completed step:
- id: security
  requires: [src/]  # Can run in parallel with...
  
- id: documentation
  requires: [src/]  # ...this step (both only need src/)
```

### 4. Explicitly Parallel Workflows

**Two workflows are explicitly designed for parallel execution:**

#### A. `multi-agent-review-and-test.yaml`
- **Purpose**: Review multiple services and generate tests in parallel
- **Max Parallel**: 8 agents
- **Structure**: Uses `parallel_tasks` section with independent tasks

```yaml
parallel_execution: true
settings:
  max_parallel_agents: 8

parallel_tasks:
  - agent_id: auth-reviewer
    agent: reviewer
    command: review
    target: services/auth/
    # No depends_on = runs immediately
    
  - agent_id: api-reviewer
    agent: reviewer
    command: review
    target: services/api/
    # No depends_on = runs in parallel with auth-reviewer
    
  - agent_id: payment-reviewer
    agent: reviewer
    command: review
    target: services/payment/
    # All three reviewers run simultaneously
```

#### B. `multi-agent-refactor.yaml`
- **Purpose**: Refactor multiple components concurrently
- **Max Parallel**: 6 agents
- **Structure**: Parallel refactoring with dependent reviews

```yaml
parallel_execution: true
settings:
  max_parallel_agents: 6

parallel_tasks:
  # These three refactors run in parallel
  - agent_id: auth-refactor
    agent: improver
    command: refactor
    target: services/auth/
    
  - agent_id: api-refactor
    agent: improver
    command: refactor
    target: services/api/
    
  - agent_id: payment-refactor
    agent: improver
    command: refactor
    target: services/payment/
  
  # These reviews wait for their respective refactors
  - agent_id: auth-review
    agent: reviewer
    depends_on: [auth-refactor]  # Waits for auth-refactor
    
  - agent_id: api-review
    agent: reviewer
    depends_on: [api-refactor]  # Waits for api-refactor
```

### 5. Sequential Workflows (Still Support Parallel)

**Even "sequential" workflows can run steps in parallel when dependencies allow:**

#### Example: `full-sdlc.yaml`
Most steps are sequential, but some can run in parallel:

```yaml
# Sequential chain:
requirements → planning → design → api_design → implementation

# After implementation, these can run in parallel:
- id: review
  requires: [src/]  # Can start when src/ exists
  
- id: testing
  requires: [src/]  # Can start when src/ exists (parallel with review)
  
- id: security
  requires: [src/]  # Can start when src/ exists (parallel with both)
  
- id: documentation
  requires: [src/]  # Can start when src/ exists (parallel with all)
```

**All four steps (review, testing, security, documentation) can run simultaneously** because they all only require `src/` and don't depend on each other.

### 6. Other Prebuilt Workflows

#### `rapid-dev.yaml`
- Mostly sequential (planning → implementation → review → testing)
- `enhance` step is optional and can run independently

#### `quality.yaml`
- Sequential: initial_review → improve → re_review → testing → security
- Each step depends on the previous one's output

#### `maintenance.yaml`
- Some steps can run in parallel if they have no dependencies

#### `quick-fix.yaml`
- Sequential workflow for quick fixes

---

## Parallel Execution Details

### How Dependencies Work

**Step Dependency Resolution:**
1. Executor tracks completed steps and available artifacts
2. For each step, checks if all `requires` artifacts exist
3. Steps with all dependencies met are "ready"
4. All ready steps execute in parallel (up to limit)

**From `parallel_executor.py`:**
```python
def find_ready_steps(
    self,
    workflow_steps: list[WorkflowStep],
    completed_step_ids: set[str],
    running_step_ids: set[str],
    available_artifacts: set[str] | None = None,
) -> list[WorkflowStep]:
    """Find steps that are ready to execute (dependencies met)."""
    ready: list[WorkflowStep] = []
    artifacts = available_artifacts or set()

    for step in workflow_steps:
        # Skip if already completed or running
        if step.id in completed_step_ids or step.id in running_step_ids:
            continue

        # Check if all required artifacts exist
        if step.requires:
            all_met = all(req in artifacts for req in step.requires)
            if not all_met:
                continue  # Not ready yet

        ready.append(step)  # Ready to execute

    return ready
```

### Execution Flow

```
1. Workflow starts
2. Find all steps with no dependencies → Execute in parallel
3. As steps complete, check if any waiting steps are now ready
4. Execute newly ready steps in parallel
5. Repeat until all steps complete
```

### Isolation & Safety

**Each parallel step runs safely:**
- Uses `asyncio.Semaphore` for bounded concurrency
- Per-step timeouts prevent hanging
- Retry logic for failed steps
- State updates are thread-safe (async context)

---

## Summary by Workflow

| Workflow | Parallel Support | Max Parallel | Notes |
|----------|------------------|--------------|-------|
| `full-sdlc` | ✅ Automatic | 8 | **5 steps run in parallel** after implementation: review, testing, security, docs, complete. Uses Background Agents in Cursor mode. See [Full SDLC Execution Architecture](FULL_SDLC_EXECUTION_ARCHITECTURE.md) for details. |
| `rapid-dev` | ✅ Automatic | 8 | Mostly sequential, but independent steps can parallelize |
| `quality` | ✅ Automatic | 8 | Sequential by design (each step needs previous) |
| `maintenance` | ✅ Automatic | 8 | Some steps can run in parallel |
| `quick-fix` | ✅ Automatic | 8 | Sequential for quick fixes |
| `multi-agent-review-and-test` | ✅ Explicit | 8 | Designed for parallel execution |
| `multi-agent-refactor` | ✅ Explicit | 6 | Designed for parallel refactoring |

---

## Best Practices

### ✅ DO: Design for Parallel Execution

1. **Minimize Dependencies**: Steps with fewer dependencies can run earlier
2. **Independent Operations**: Structure workflows so independent tasks can run simultaneously
3. **Use Parallel Workflows**: For multi-service/multi-component work, use `multi-agent-*` workflows

### ❌ DON'T: Force Sequential Execution

1. **Unnecessary Dependencies**: Don't add `requires` if steps are truly independent
2. **Blocking Dependencies**: Avoid making everything depend on one step if possible

### 📊 Example: Optimizing for Parallel Execution

**Before (Sequential):**
```yaml
- id: review
  requires: [src/]
  
- id: testing
  requires: [src/, review-report.md]  # Unnecessary dependency
  
- id: security
  requires: [src/, review-report.md, tests/]  # Unnecessary dependencies
```

**After (Parallel):**
```yaml
- id: review
  requires: [src/]  # Can run immediately after src/
  
- id: testing
  requires: [src/]  # Can run in parallel with review
  
- id: security
  requires: [src/]  # Can run in parallel with both
```

---

## Technical Implementation

### Parallel Executor

**Location**: `tapps_agents/workflow/parallel_executor.py`

**Key Features:**
- Bounded parallelism (semaphore-based)
- Per-step timeouts
- Retry logic
- Deterministic state updates
- Cancellation support

### Workflow Executor

**Location**: `tapps_agents/workflow/cursor_executor.py`

**Key Features:**
- Dependency analysis
- Ready step detection
- Parallel execution orchestration
- State management
- Progress tracking

---

## Conclusion

**All prebuilt workflows support parallel execution automatically.** The executor:
- ✅ Analyzes step dependencies
- ✅ Executes independent steps simultaneously (up to 8 by default)
- ✅ Waits for dependencies before executing dependent steps
- ✅ Maximizes parallelism while respecting dependencies

**For maximum parallel execution**, use:
- `multi-agent-review-and-test.yaml` - Explicit parallel review and testing
- `multi-agent-refactor.yaml` - Explicit parallel refactoring

**For sequential workflows**, steps will still parallelize when dependencies allow (e.g., multiple steps that only need the same completed artifact).

---

## References

- `tapps_agents/workflow/parallel_executor.py` - Parallel execution engine
- `tapps_agents/workflow/cursor_executor.py` - Workflow executor with parallel support
- `workflows/multi-agent-review-and-test.yaml` - Explicit parallel workflow example
- `workflows/multi-agent-refactor.yaml` - Explicit parallel refactoring example
- `workflows/presets/full-sdlc.yaml` - Sequential workflow with parallel opportunities
- [Full SDLC Execution Architecture](FULL_SDLC_EXECUTION_ARCHITECTURE.md) - Complete documentation of Full SDLC parallel execution and Background Agent integration

