# Performance Patterns Quick Reference (2025)

**Quick reference for implementing performance optimizations in TappsCodingAgents**

---

## 1. Result Caching Pattern

**Use Case**: Cache command results (score, review, lint) to avoid re-execution

**Implementation**:
```python
# Cache key: file_path + content_hash + command + version
cache_key = f"{file_path}:{content_hash}:{command}:{version}"

# Check cache
if cached := cache.get(cache_key):
    return cached

# Execute and cache
result = await execute_command(file_path)
cache.set(cache_key, result, ttl=3600)
return result
```

**Files to Modify**:
- `tapps_agents/agents/reviewer/cache.py` (new)
- `tapps_agents/cli/commands/reviewer.py` (integrate cache)

**Expected Impact**: 90%+ speedup for unchanged files

---

## 2. Streaming Progress Pattern

**Use Case**: Show incremental progress during batch operations

**Implementation**:
```python
async def process_with_progress(files: list[Path], callback):
    total = len(files)
    completed = 0
    
    async def process_file(file: Path):
        nonlocal completed
        result = await process(file)
        completed += 1
        
        # Stream progress
        callback(ProgressUpdate(
            current=completed,
            total=total,
            percentage=(completed / total) * 100,
            current_file=str(file)
        ))
        
        return result
    
    # Process in parallel
    return await asyncio.gather(*[process_file(f) for f in files])
```

**Files to Modify**:
- `tapps_agents/cli/commands/reviewer.py` (add streaming)
- `tapps_agents/workflow/progress_manager.py` (enhance)

**Expected Impact**: Better UX, prevents timeouts

---

## 3. Background Processing Pattern

**Use Case**: Execute commands/workflows without blocking

**Implementation**:
```python
class BackgroundExecutor:
    def __init__(self):
        self.task_queue = asyncio.Queue()
        self.results_store = ResultStore()
    
    async def submit(self, command: str, args: dict) -> str:
        task_id = str(uuid.uuid4())
        await self.task_queue.put(Task(task_id, command, args))
        return task_id
    
    async def get_result(self, task_id: str) -> Result | None:
        return await self.results_store.get(task_id)
    
    async def _worker_loop(self):
        while True:
            task = await self.task_queue.get()
            result = await execute(task)
            await self.results_store.save(task.id, result)
```

**Files to Modify**:
- `tapps_agents/cli/background_executor.py` (new)
- `tapps_agents/workflow/background_executor.py` (new)

**Expected Impact**: Non-blocking execution

---

## 4. Async File I/O Pattern

**Use Case**: Replace blocking file operations with async

**Note**: TappsCodingAgents requires Python 3.13+ (supports native async file I/O), but `aiofiles` provides a more convenient API.

**Implementation**:
```python
import aiofiles
from pathlib import Path

async def read_file(file_path: Path) -> str:
    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        return await f.read()

async def write_file(file_path: Path, content: str) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(content)
```

**Alternative (Python 3.13+ native)**:
```python
# Python 3.13+ native async file I/O
async with open(file_path, "r", encoding="utf-8") as f:
    content = await f.read()
```

**Files to Modify**:
- `tapps_agents/core/async_file_ops.py` (new)
- Replace all `Path.read_text()` with `AsyncFileOps.read_file()`

**Expected Impact**: Better concurrency

---

## 5. Smart Cache Invalidation Pattern

**Use Case**: Automatically invalidate cache on file changes

**Implementation**:
```python
class SmartCache:
    async def get_cached_result(self, file_path: Path, command: str) -> Result | None:
        # Check if file changed
        current_hash = await self._file_hash(file_path)
        cached_hash = await self.metadata.get_hash(file_path, command)
        
        if current_hash != cached_hash:
            return None  # Cache invalid
        
        # Return cached result
        return await self._load_cache(file_path, command)
    
    async def save_result(self, file_path: Path, command: str, result: Result):
        file_hash = await self._file_hash(file_path)
        await self._save_cache(file_path, command, result)
        await self.metadata.save_hash(file_path, command, file_hash)
```

**Files to Modify**:
- `tapps_agents/agents/reviewer/cache.py` (add invalidation)
- `tapps_agents/workflow/caching.py` (add invalidation)

**Expected Impact**: Automatic cache management

---

## Implementation Checklist

### Phase 1: Quick Wins (Week 1-2)
- [ ] Implement `ReviewerResultCache`
- [ ] Integrate cache into `score_command`
- [ ] Integrate cache into `review_command`
- [ ] Add streaming progress to batch commands
- [ ] Replace synchronous file I/O with async

### Phase 2: Workflow Optimizations (Week 3-4)
- [ ] Implement `WorkflowStepCache`
- [ ] Integrate cache into workflow executor
- [ ] Enhance progress manager with streaming
- [ ] Add incremental step updates

### Phase 3: Advanced Features (Week 5-6)
- [ ] Implement `BackgroundCommandExecutor`
- [ ] Implement `BackgroundWorkflowExecutor`
- [ ] Add CLI commands for background execution
- [ ] Add status monitoring commands

---

## Performance Targets

| Metric | Target | Current | Improvement |
|--------|--------|---------|-------------|
| Cached command response | <10ms | N/A | New |
| Uncached command response | Same | Baseline | No regression |
| Batch progress updates | Every 100ms | N/A | New |
| Cache hit rate | >80% | 0% | New |
| Memory overhead | <50MB | N/A | New |

---

## Testing Checklist

- [ ] Unit tests for cache hit/miss logic
- [ ] Unit tests for cache invalidation
- [ ] Integration tests for cached commands
- [ ] Integration tests for streaming progress
- [ ] Performance benchmarks (cached vs uncached)
- [ ] Memory usage tests

---

## Related Documentation

- **Full Analysis**: `docs/PERFORMANCE_OPTIMIZATION_RECOMMENDATIONS_2025.md`
- **Architecture**: `docs/HOW_IT_WORKS.md`
- **Workflow State**: `tapps_agents/workflow/durable_state.py`
