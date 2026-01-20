---
title: Performance Guide
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [architecture, performance, optimization]
---

# Performance Guide

This document provides performance guidelines and optimization strategies for TappsCodingAgents.

## Performance Principles

### 1. Async-First Architecture

- Use async/await for I/O-bound operations
- Use `asyncio.TaskGroup` for structured concurrency (Python 3.11+)
- Avoid blocking operations in async code

### 2. Caching Strategy

- **Context7 Cache**: KB-first caching with async LRU cache
- **In-Memory Cache**: Thread-safe LRU cache for hot data
- **Cache Pre-warming**: Automatic dependency detection and cache population

### 3. Parallel Execution

- **Workflow Steps**: Up to 8 concurrent steps
- **Test Execution**: pytest-xdist for parallel test runs
- **TaskGroup**: Structured concurrency with automatic error handling

## 2025 Performance Enhancements

### Async LRU Cache

**Location**: `tapps_agents/context7/async_cache.py`

**Features:**
- Thread-safe in-memory cache with O(1) operations
- Background write queue for non-blocking disk persistence
- Atomic file rename pattern (no file locking needed)
- `CacheStats` for monitoring hit rates and performance

**Usage:**
```python
from tapps_agents.context7.async_cache import AsyncLRUCache

cache = AsyncLRUCache(maxsize=1000)
value = await cache.get(key)
await cache.set(key, value)
```

### Circuit Breaker

**Location**: `tapps_agents/context7/circuit_breaker.py`

**Features:**
- CLOSED → OPEN → HALF_OPEN state machine
- Bounded concurrency (default: 5) with fail-fast
- Global circuit breaker for Context7 operations
- Auto-recovery after configurable timeout (default: 30s)

**Usage:**
```python
from tapps_agents.context7.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, timeout=30)
result = await breaker.execute(operation)
```

### Cache Pre-warming

**Location**: `tapps_agents/context7/cache_prewarm.py`

**Features:**
- `DependencyDetector`: Detects from requirements.txt, pyproject.toml, package.json
- `CachePrewarmer`: Background pre-warming with priority ordering
- Integration with `tapps-agents init` for automatic population
- Expert library prioritization (fastapi, pytest, react, etc.)

### Lock Timeout Optimization

**Location**: `tapps_agents/context7/cache_locking.py`

**Improvements:**
- Reduced timeout from 30s → 5s (3s for cache store)
- Graceful degradation on lock failures
- **Result**: Eliminated 150+ second cache lock timeouts

## Performance Metrics

### Cache Performance

**Metrics Tracked:**
- Hit rate (target: >80%)
- Response time (target: <100ms for cache hits)
- Cache size and eviction rate
- Staleness analysis

**Monitoring:**
```python
from tapps_agents.context7.analytics import CacheStats

stats = CacheStats()
print(f"Hit rate: {stats.hit_rate:.2%}")
print(f"Avg response time: {stats.avg_response_time:.2f}ms")
```

### Workflow Performance

**Metrics Tracked:**
- Step execution time
- Parallel execution efficiency
- Total workflow duration
- Resource usage (CPU, memory)

**Optimization Targets:**
- Parallel steps: 5-10x speedup
- Cache hits: <100ms response time
- Workflow execution: <30s for typical workflows

## Optimization Strategies

### 1. Minimize External API Calls

- Use Context7 cache for library documentation
- Batch API calls when possible
- Use circuit breaker to prevent cascading failures

### 2. Parallel Execution

- Identify independent workflow steps
- Use dependency-based parallelism (automatic)
- Limit concurrency to avoid resource exhaustion

### 3. Lazy Loading

- Load experts and knowledge bases on demand
- Use lazy imports for optional dependencies
- Defer expensive operations until needed

### 4. Resource Management

- Use context managers for resource cleanup
- Close file handles and connections promptly
- Monitor memory usage and implement limits

## Performance Testing

### Benchmarking

**Test Performance:**
```bash
# Run tests with timing
pytest --durations=10

# Profile code execution
python -m cProfile -o profile.stats script.py
```

### Load Testing

- Test with realistic workloads
- Monitor resource usage under load
- Identify bottlenecks and optimize

## Best Practices

### 1. Async I/O

- Always use async for I/O operations
- Use `aiofiles` for async file operations
- Use `httpx` for async HTTP requests

### 2. Caching

- Cache expensive computations
- Use appropriate cache sizes
- Implement cache invalidation strategies

### 3. Database/Storage

- Use connection pooling
- Batch database operations
- Use indexes for frequent queries

### 4. Memory Management

- Avoid memory leaks (close resources)
- Use generators for large datasets
- Monitor memory usage

## Performance Checklist

Before deploying code:

- [ ] Async operations use `async/await` correctly
- [ ] External API calls are cached when appropriate
- [ ] Parallel execution is used for independent operations
- [ ] Resource cleanup is implemented (context managers)
- [ ] Memory usage is reasonable (no leaks)
- [ ] Performance tests pass
- [ ] Cache hit rates are acceptable (>80%)
- [ ] Response times meet targets (<100ms for cache hits)

## Related Documentation

- **Architecture Overview**: `docs/ARCHITECTURE.md`
- **Context7 Integration**: `docs/context7/CONTEXT7_CACHE_OPTIMIZATION.md`
- **Tech Stack**: `docs/architecture/tech-stack.md`

---

**Last Updated:** 2026-01-20  
**Maintained By:** TappsCodingAgents Team
