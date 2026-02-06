# Asyncio Parallel Execution Patterns for TappsCodingAgents

## Overview

This knowledge file covers asyncio-based concurrency patterns used in TappsCodingAgents for parallel story execution, wave-based scheduling, and bounded concurrency control.

## Key Patterns

### Wavefront (Wave-Based) Parallel Execution

Stories with no mutual dependencies form a "wave" and execute in parallel. The next wave starts when its dependencies complete.

```python
import asyncio
from collections import defaultdict

async def execute_waves(stories: list[Story], max_parallel: int = 3):
    """Execute stories in dependency-ordered waves."""
    waves = compute_waves(stories)  # topological sort into layers
    for wave in waves:
        semaphore = asyncio.Semaphore(max_parallel)
        tasks = [execute_with_semaphore(semaphore, story) for story in wave]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Check results, fail fast if critical story fails
```

### Bounded Concurrency with Semaphore

```python
async def execute_with_semaphore(sem: asyncio.Semaphore, story: Story):
    async with sem:
        return await execute_story(story)
```

### Python 3.11+ TaskGroup (Recommended)

```python
async def execute_wave_taskgroup(stories: list[Story], max_parallel: int = 3):
    """Modern Python 3.11+ pattern using TaskGroup."""
    sem = asyncio.Semaphore(max_parallel)
    async with asyncio.TaskGroup() as tg:
        for story in stories:
            tg.create_task(execute_with_semaphore(sem, story))
    # All tasks complete or first exception propagates
```

**Benefits over `asyncio.gather()`:**
- Structured concurrency — tasks have clear lifetime
- Better exception handling — first exception cancels siblings
- Avoids the `return_exceptions=True` footgun (silently swallowed errors)

### Timeouts (Python 3.11+)

```python
async def execute_with_timeout(story: Story, timeout_secs: float = 300):
    """Use asyncio.timeout() instead of wait_for()."""
    async with asyncio.timeout(timeout_secs):
        return await execute_story(story)
```

### Topological Sort for Dependency Resolution

```python
def topological_sort(stories: list[Story]) -> list[list[Story]]:
    """Return stories grouped into waves (layers) by dependency order."""
    in_degree = {s.id: 0 for s in stories}
    for s in stories:
        for dep in s.dependencies:
            in_degree[s.id] += 1

    waves = []
    ready = [s for s in stories if in_degree[s.id] == 0]
    while ready:
        waves.append(ready)
        next_ready = []
        for completed in ready:
            for s in stories:
                if completed.id in s.dependencies:
                    in_degree[s.id] -= 1
                    if in_degree[s.id] == 0:
                        next_ready.append(s)
        ready = next_ready
    return waves
```

### Error Handling in Parallel Execution

- Prefer `TaskGroup` over `gather(return_exceptions=True)` for proper error propagation
- Implement circuit breaker: if N consecutive stories fail, pause the epic
- File conflict detection: check that parallel stories don't modify the same files

### File Conflict Detection

```python
def detect_file_conflicts(wave: list[Story]) -> list[tuple[Story, Story, set[str]]]:
    """Detect stories in the same wave that modify overlapping files."""
    conflicts = []
    for i, s1 in enumerate(wave):
        for s2 in wave[i+1:]:
            overlap = set(s1.files_affected) & set(s2.files_affected)
            if overlap:
                conflicts.append((s1, s2, overlap))
    return conflicts
```

## Best Practices

1. **Default to sequential** — parallel execution is opt-in (`max_parallel_stories: 3`)
2. **Bounded concurrency** — always use a semaphore to prevent resource exhaustion
3. **Fail fast on critical stories** — if a foundational story fails, cancel dependent waves
4. **State isolation** — each parallel story should have its own working state
5. **Progress tracking** — update epic state after each story completes (atomic writes)
6. **Cross-platform** — use `asyncio.run()` for top-level; avoid Unix-specific APIs
7. **Prefer TaskGroup** — use `asyncio.TaskGroup()` (Python 3.11+) over `asyncio.gather()`
8. **Use `asyncio.timeout()`** — prefer over `asyncio.wait_for()` for clearer scoping
9. **Avoid blocking I/O in async** — use `aiofiles` or `asyncio.to_thread()` for file operations

## Configuration

```yaml
epic:
  max_parallel_stories: 3
  parallel_strategy: "sequential"  # sequential | asyncio | agent-teams
  fail_fast: true
  conflict_detection: true
```

## Related

- Phase 3: Parallel Story Execution (EPIC-AND-WORKFLOW-ENHANCEMENT-DESIGN-PLAN.md)
- Phase 7.2: Agent Teams for parallel execution (Claude Code CLI)
- `tapps_agents/workflow/parallel_executor.py`
- `tapps_agents/core/multi_agent_orchestrator.py`
