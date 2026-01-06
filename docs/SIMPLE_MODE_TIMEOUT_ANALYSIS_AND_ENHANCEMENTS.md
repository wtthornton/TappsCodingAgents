# Simple Mode Workflow Timeout Analysis & Critical Enhancements

**Date**: January 6, 2026  
**Status**: Analysis Complete, Immediate Fixes Applied

## Executive Summary

Simple Mode `*build` and `*full` workflows are timing out due to **cascading cache lock timeouts** in the Context7 knowledge base system. Each library lookup waits up to 30 seconds for a file lock, and with 5+ libraries being detected, workflows block for **150+ seconds** before execution begins.

**Immediate Fix Applied**: Reduced lock timeout from 30s to 5s (3s for cache store).

## Root Cause Analysis

### 1. Cache Lock Timeout Cascade (Primary Issue)

**Evidence from terminal output:**
```
Failed to acquire lock after 30.0s timeout
Context7 lookup error for library 'httpx' (topic: None): Failed to acquire cache lock
Context7 lookup error for library 'jinja2' (topic: None): Failed to acquire cache lock
Context7 lookup error for library 'mypy' (topic: None): Failed to acquire cache lock
Context7 lookup error for library 'packaging' (topic: None): Failed to acquire cache lock
Context7 lookup error for library 'pip-audit' (topic: None): Failed to acquire cache lock
```

**Impact**: 5 libraries × 30s timeout = **150+ seconds of blocking**

**Root Location**: `tapps_agents/context7/cache_locking.py`
- Uses file-based locking with `O_CREAT | O_EXCL | O_WRONLY` on Windows
- 30-second timeout before giving up on lock acquisition
- No graceful degradation when locks fail

### 2. Sequential Library Detection

The `BuildOrchestrator` fetches Context7 docs for each detected library sequentially:

```python
# tapps_agents/simple_mode/orchestrators/build_orchestrator.py:253-257
context7_docs = await context7_helper.get_documentation_for_libraries(
    libraries=filtered_libraries,
    topic=None,
    use_fuzzy_match=True,
)
```

Even with `asyncio.gather`, each library hits the same lock file for its category.

### 3. Windows File Locking Issues

The Windows locking implementation has issues:
- Stale lock detection waits full timeout (30s) before attempting cleanup
- Lock files from crashed processes persist indefinitely
- No exponential backoff or jitter on retry

### 4. Cursor Response Timeout

Cursor AI has a response timeout (~60-90 seconds). Long-running workflows:
- Start executing but time out before completion
- Don't provide progressive feedback
- Can't be resumed after timeout

## Immediate Fixes Applied

### 1. Reduced Lock Timeout (30s → 5s)

**File**: `tapps_agents/context7/cache_locking.py`
```python
# Before
def __init__(self, lock_file: Path, timeout: float = 30.0):

# After
def __init__(self, lock_file: Path, timeout: float = 5.0):
```

### 2. Reduced Cache Store Timeout (30s → 3s)

**File**: `tapps_agents/context7/kb_cache.py`
```python
# Before
with cache_lock(lock_file, timeout=30.0):

# After
with cache_lock(lock_file, timeout=3.0):  # Short timeout - fail fast
```

### 3. Cleaned Stale Lock Files

```powershell
Remove-Item -Recurse -Force .tapps-agents\kb\context7-cache\.locks
New-Item -ItemType Directory -Force -Path .tapps-agents\kb\context7-cache\.locks
```

## Critical Enhancements for 2025

### Priority 1: Non-Blocking Cache Architecture (Critical)

**Problem**: Synchronous file locking blocks workflow execution.

**2025 Pattern**: Lock-Free Caching with Optimistic Concurrency Control (OCC)

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                    AsyncCacheManager                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │  In-Memory      │───▶│  Background     │───▶ Disk        │
│  │  Cache (LRU)    │    │  Write Queue    │    Persistence  │
│  └─────────────────┘    └─────────────────┘                 │
│         │                                                    │
│         ▼                                                    │
│  Instant reads (no locking)                                  │
│  Writes queued for background flush                          │
│  Atomic file rename for disk persistence                     │
└─────────────────────────────────────────────────────────────┘
```

**Key Benefits**:
- Zero blocking on reads (in-memory first)
- Background disk writes (fire-and-forget)
- No file locking needed (atomic rename pattern)

**Effort**: Medium (1-2 days)

### Priority 2: Cursor-Native Streaming Responses

**Problem**: Cursor has response timeout; long workflows fail silently.

**2025 Pattern**: Progressive Streaming with Checkpoint Responses

**Architecture**:
```
User Request ──▶ Simple Mode
                     │
                     ▼
              ┌──────────────────┐
              │ Stream Response  │
              │ "✅ Starting..." │◄──── Immediate (0ms)
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Execute Step 1   │
              │ Stream Progress  │◄──── Per-step (5s)
              │ Save Checkpoint  │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Execute Step 2   │
              │ (or timeout)     │
              │ Stream Status    │◄──── With timeout handling
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Final Summary    │
              │ Resume Command   │◄──── If interrupted
              └──────────────────┘
```

**Key Benefits**:
- User sees immediate feedback
- Per-step timeout (30s) prevents cascade failures
- Workflow can resume after Cursor timeout

**Effort**: Medium (1-2 days)

### Priority 3: Parallel Library Resolution with Circuit Breaker

**Problem**: Sequential lookups multiply timeout penalties.

**2025 Pattern**: Bounded Parallelism + Circuit Breaker

**Architecture**:
```
Libraries: [httpx, fastapi, pytest, jinja2, pydantic]
                            │
                            ▼
              ┌─────────────────────────┐
              │   Circuit Breaker       │
              │   (3 failures = open)   │
              └───────────┬─────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
      ┌───────┐       ┌───────┐       ┌───────┐
      │ Slot 1│       │ Slot 2│       │ Slot 3│  ◄── Semaphore(5)
      │ httpx │       │fastapi│       │pytest │
      │  5s   │       │  5s   │       │  5s   │  ◄── 5s timeout each
      └───────┘       └───────┘       └───────┘
          │               │               │
          └───────────────┴───────────────┘
                          │
                          ▼
            5 libraries in ~5s (vs 150s sequential)
```

**Key Benefits**:
- 5-second per-library timeout (vs 30s)
- Bounded concurrency (5 parallel)
- Circuit breaker stops cascading failures

**Effort**: Low (0.5 day)

### Priority 4: Intelligent Cache Pre-warming

**Problem**: Cold cache causes API calls during workflow execution.

**2025 Pattern**: Predictive Pre-warming

**Architecture**:
```
tapps-agents init
       │
       ▼
┌──────────────────────────────────────┐
│  Detect Project Dependencies         │
│  (requirements.txt, pyproject.toml)  │
└─────────────────┬────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────┐
│  Prioritize by Usage Frequency       │
│  Top 20: fastapi, pytest, pydantic.. │
└─────────────────┬────────────────────┘
                  │
                  ▼ (background)
┌──────────────────────────────────────┐
│  Pre-warm Cache                      │
│  (async, non-blocking)               │
└──────────────────────────────────────┘
```

**Key Benefits**:
- Cache is warm when workflow starts
- No API calls during workflow execution
- Background pre-warming (non-blocking)

**Effort**: Low (0.5 day)

### Priority 5: Durable Workflow State Machine with Resume

**Problem**: Long workflows can't recover from interruption.

**2025 Pattern**: Event-Sourced Workflow with Checkpoints

**Architecture**:
```
Workflow Execution
       │
       ▼
┌──────────────────────────────────────┐
│  Event Store (append-only)           │
│  ┌────────────────────────────────┐  │
│  │ Event 1: workflow_started      │  │
│  │ Event 2: step_1_completed      │  │
│  │ Event 3: step_2_completed      │  │
│  │ Event 4: workflow_paused       │  │
│  └────────────────────────────────┘  │
└─────────────────┬────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────┐
│  Resume from Last Event              │
│  @simple-mode *resume {workflow_id}  │
└──────────────────────────────────────┘
```

**Key Benefits**:
- Complete audit trail
- Resume from any checkpoint
- Survives process crashes

**Effort**: Medium (1 day)

## Implementation Roadmap

| Priority | Enhancement | Impact | Effort | Status |
|----------|-------------|--------|--------|--------|
| **P0** | Reduce lock timeout (30s → 5s) | Critical | Done | ✅ Completed |
| **P1** | Non-blocking cache | Critical | 1-2 days | ✅ Completed |
| **P2** | Streaming responses | Critical | 1-2 days | ✅ Completed |
| **P3** | Parallel + circuit breaker | High | 0.5 day | ✅ Completed |
| **P4** | Cache pre-warming | Medium | 0.5 day | ✅ Completed |
| **P5** | Durable state machine | Medium | 1 day | ✅ Completed |

## Implemented Components

### P1: AsyncCacheManager (`tapps_agents/context7/async_cache.py`)
- **LRUCache**: Thread-safe in-memory cache with configurable size
- **BackgroundWriteQueue**: Async disk persistence with atomic rename
- Lock-free reads and writes
- Singleton pattern for process-wide caching

### P2: StreamingWorkflowExecutor (`tapps_agents/simple_mode/streaming.py`)
- **StreamEvent**: Typed events for workflow progress
- Per-step timeout (30s default) prevents cascade failures
- Automatic checkpoint on timeout
- Resume command generation (`@simple-mode *resume <id>`)

### P3: CircuitBreaker (`tapps_agents/context7/circuit_breaker.py`)
- **CircuitBreaker**: States (CLOSED, OPEN, HALF_OPEN)
- **ParallelExecutor**: Bounded concurrency with circuit breaker
- 3 failures to open, 2 successes to close
- 5s per-operation timeout

### P4: Predictive Pre-warming (`tapps_agents/context7/cache_warming.py`)
- **WELL_KNOWN_LIBRARIES**: Priority-based library detection
- `run_predictive_warming()`: Convenience function for `init`
- **WarmingResult**: Statistics on warming operations
- Detects project dependencies (requirements.txt, pyproject.toml, package.json)

### P5: DurableWorkflowState (`tapps_agents/workflow/durable_state.py`)
- **EventStore**: Append-only event log (JSONL format)
- **CheckpointStore**: Snapshot-based checkpoints
- **DurableWorkflowState**: Event-sourced state machine
- `resume_workflow()`: Restore from checkpoint or rebuild from events

## Testing the Immediate Fix

After applying the immediate fixes, test with:

```bash
# Clean start
cd C:\cursor\TappsCodingAgents

# Test planner (was timing out)
python -m tapps_agents.cli planner plan "Test plan creation"

# Test simple-mode build (should be faster now)
python -m tapps_agents.cli simple-mode build --prompt "Create a hello world function"
```

## Related Files

### Core Implementation
- `tapps_agents/context7/async_cache.py` - **NEW** Lock-free async cache
- `tapps_agents/context7/circuit_breaker.py` - **NEW** Circuit breaker + parallel executor
- `tapps_agents/context7/cache_warming.py` - **ENHANCED** Predictive pre-warming
- `tapps_agents/simple_mode/streaming.py` - **NEW** Streaming workflow executor
- `tapps_agents/workflow/durable_state.py` - **NEW** Event-sourced state machine

### Existing (Modified)
- `tapps_agents/context7/cache_locking.py` - Reduced timeout (30s → 5s)
- `tapps_agents/context7/kb_cache.py` - Graceful lock failure handling
- `tapps_agents/context7/agent_integration.py` - Circuit breaker integration
- `tapps_agents/simple_mode/orchestrators/build_orchestrator.py` - Build workflow

### Cursor Integration
- `.claude/skills/simple-mode/SKILL.md` - Cursor skill definition
- `tapps_agents/workflow/executor.py` - Workflow execution engine

## Usage Examples

### Using Async Cache (Non-blocking)
```python
from tapps_agents.context7 import init_async_cache, get_async_cache

# Initialize (typically in app startup)
cache = await init_async_cache()

# Store (instant in-memory, async disk write)
await cache.store("fastapi", "routing", content="...")

# Get (instant from memory)
entry = await cache.get("fastapi", "routing")
```

### Using Circuit Breaker
```python
from tapps_agents.context7 import get_parallel_executor

executor = get_parallel_executor(max_concurrency=5)

# Execute multiple lookups with circuit breaker
results = await executor.execute_all(
    items=["fastapi", "pytest", "pydantic"],
    func=lookup_library,
    fallback=None,
)
```

### Using Streaming Responses
```python
from tapps_agents.simple_mode import create_streaming_response

markdown = await create_streaming_response(
    workflow_id="build-123",
    steps=[
        {"id": "enhance", "name": "Enhance Prompt"},
        {"id": "plan", "name": "Create Plan"},
        {"id": "implement", "name": "Implement"},
    ],
    step_executor=execute_step,
    step_timeout=30.0,
)
```

### Using Durable State Machine
```python
from tapps_agents.workflow import get_durable_state, resume_workflow

# Start workflow
state = get_durable_state()
workflow_id = await state.start_workflow(intent="build")

# Track steps
await state.start_step("enhance", "Enhance Prompt")
await state.complete_step("enhance", {"result": "..."})

# Resume after interruption
resume_info = await resume_workflow(workflow_id)
```

### Predictive Pre-warming
```python
from tapps_agents.context7 import run_predictive_warming

# Run during init (non-blocking)
result = await run_predictive_warming(
    project_root=Path.cwd(),
    max_libraries=20,
    max_concurrency=5,
)
print(f"Warmed {result.warmed} libraries in {result.duration_ms}ms")
```

## References

- [2025 Async Python Patterns](https://docs.python.org/3.13/library/asyncio.html)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Optimistic Concurrency Control](https://en.wikipedia.org/wiki/Optimistic_concurrency_control)
