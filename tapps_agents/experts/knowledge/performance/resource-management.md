# Resource Management Strategies

## Overview

Effective resource management is critical for application performance and stability. This guide covers memory management, connection pooling, thread management, and resource lifecycle patterns.

## Memory Management

### Memory Allocation

**Efficient Allocation:**
- Pre-allocate when size is known
- Use object pools for frequent allocations
- Minimize allocations in hot paths
- Reuse objects when possible

**Example:**
```python
# Bad: Allocate in loop
def process_items(items):
    results = []
    for item in items:
        result = {}  # New allocation each iteration
        result['processed'] = process(item)
        results.append(result)
    return results

# Good: Pre-allocate or reuse
def process_items(items):
    results = [None] * len(items)  # Pre-allocate
    for i, item in enumerate(items):
        results[i] = {'processed': process(item)}
    return results
```

### Garbage Collection

**GC Optimization:**
- Minimize object creation
- Reduce object lifetime
- Use weak references when appropriate
- Tune GC parameters if needed

### Memory Leaks

**Prevent Leaks:**
- Close resources properly
- Remove event listeners
- Clear caches periodically
- Use weak references for observers

**Common Leak Patterns:**
- Unclosed file handles
- Event listeners not removed
- Circular references
- Caches without expiration

## Connection Management

### Connection Pooling

**Reuse Connections:**
- Database connections
- HTTP connections
- Network sockets
- Reduce connection overhead

**Pool Configuration:**
- Minimum pool size
- Maximum pool size
- Connection timeout
- Idle timeout
- Health checks

**Example:**
```python
from sqlalchemy import create_engine

# Configure connection pool
engine = create_engine(
    'postgresql://user:pass@localhost/db',
    pool_size=10,           # Minimum connections
    max_overflow=20,        # Maximum connections
    pool_timeout=30,        # Wait time for connection
    pool_recycle=3600      # Recycle connections after 1 hour
)
```

### Connection Lifecycle

**Proper Lifecycle:**
1. Acquire from pool
2. Use connection
3. Return to pool
4. Handle errors gracefully

**Best Practices:**
- Always use context managers
- Handle connection errors
- Set appropriate timeouts
- Monitor connection usage

## Thread Management

### Thread Pools

**Manage Threads:**
- Reuse threads
- Limit thread count
- Queue tasks
- Handle thread lifecycle

**Thread Pool Sizing:**
- CPU-bound: Number of cores
- I/O-bound: Higher count (2-4x cores)
- Consider blocking factor
- Monitor thread utilization

**Example:**
```python
from concurrent.futures import ThreadPoolExecutor
import os

# Size based on workload
cpu_count = os.cpu_count()
io_bound_pool = ThreadPoolExecutor(max_workers=cpu_count * 2)
cpu_bound_pool = ThreadPoolExecutor(max_workers=cpu_count)
```

### Thread Safety

**Concurrent Access:**
- Use locks for shared state
- Prefer immutable data
- Use thread-safe collections
- Avoid shared mutable state

## File Handle Management

### Resource Cleanup

**Proper Cleanup:**
- Always close file handles
- Use context managers
- Handle exceptions
- Ensure cleanup in finally blocks

**Example:**
```python
# Bad: File not closed on exception
file = open('data.txt', 'r')
data = file.read()
file.close()  # Not reached if exception occurs

# Good: Context manager
with open('data.txt', 'r') as file:
    data = file.read()
# File automatically closed
```

### File Handle Limits

**System Limits:**
- Monitor open file handles
- Set appropriate limits
- Handle "too many open files" errors
- Use connection pooling for files

## Cache Management

### Cache Size Limits

**Memory Bounded:**
- Set maximum cache size
- Use LRU eviction
- Monitor memory usage
- Prevent memory exhaustion

**Example:**
```python
from functools import lru_cache
from cachetools import LRUCache

# LRU cache with size limit
cache = LRUCache(maxsize=1000)

# Or use functools.lru_cache
@lru_cache(maxsize=1000)
def expensive_function(arg):
    return compute(arg)
```

### Cache Eviction

**Eviction Strategies:**
- **LRU**: Least Recently Used
- **LFU**: Least Frequently Used
- **TTL**: Time To Live
- **Size-based**: Evict when size limit reached

## Resource Monitoring

### Metrics to Track

**Key Metrics:**
- Memory usage (heap, stack, cache)
- Connection pool usage
- Thread pool usage
- File handle count
- CPU utilization
- I/O wait time

### Monitoring Tools

**Common Tools:**
- Application Performance Monitoring (APM)
- System monitoring (Prometheus, Grafana)
- Profilers
- Resource usage dashboards

## Resource Limits

### Setting Limits

**Configure Limits:**
- Memory limits
- CPU limits
- Connection limits
- Thread limits
- File handle limits

**Container Limits:**
```yaml
# Docker resource limits
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "250m"
```

### Handling Limits

**Graceful Degradation:**
- Monitor resource usage
- Throttle requests when near limit
- Return appropriate errors
- Log resource exhaustion

## Best Practices

1. **Use Context Managers**: Always use `with` statements
2. **Monitor Resources**: Track resource usage
3. **Set Limits**: Configure appropriate limits
4. **Pool Resources**: Reuse connections, threads, etc.
5. **Clean Up**: Always release resources
6. **Handle Errors**: Clean up even on errors
7. **Test Limits**: Test behavior at resource limits
8. **Document Limits**: Document resource requirements

## Patterns

### Resource Pool Pattern

**Reusable Resources:**
- Create pool of resources
- Acquire from pool
- Use resource
- Return to pool

### Lazy Initialization

**Initialize on Demand:**
- Defer resource creation
- Create when first needed
- Reduce startup overhead
- Lower initial resource usage

### Resource Locator

**Centralized Access:**
- Single point for resource access
- Consistent configuration
- Easier monitoring
- Simplified management

## References

- [Effective Resource Management](https://docs.oracle.com/javase/tutorial/essential/exceptions/resource.html)
- [Connection Pooling Best Practices](https://www.baeldung.com/java-connection-pooling-best-practices)

