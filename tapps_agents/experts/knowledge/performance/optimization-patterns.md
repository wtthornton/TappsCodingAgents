# Performance Optimization Patterns

## Overview

Performance optimization is the process of improving system performance by reducing resource consumption, improving response times, and increasing throughput. This guide covers common optimization patterns and techniques.

## Code-Level Optimizations

### Algorithm Optimization

**Choose the Right Algorithm:**
- Use O(n log n) sorting instead of O(n²)
- Prefer hash maps (O(1)) over linear search (O(n))
- Use binary search (O(log n)) for sorted arrays
- Consider space-time tradeoffs

**Example:**
```python
# Bad: O(n²) - nested loops
def find_duplicates_slow(arr):
    duplicates = []
    for i in range(len(arr)):
        for j in range(i+1, len(arr)):
            if arr[i] == arr[j]:
                duplicates.append(arr[i])
    return duplicates

# Good: O(n) - hash set
def find_duplicates_fast(arr):
    seen = set()
    duplicates = []
    for item in arr:
        if item in seen:
            duplicates.append(item)
        else:
            seen.add(item)
    return duplicates
```

### Data Structure Selection

**Choose Appropriate Data Structures:**
- Use sets for membership testing
- Use dictionaries for key-value lookups
- Use lists for ordered, indexed access
- Use deques for queue operations
- Use heaps for priority queues

### Loop Optimization

**Minimize Loop Overhead:**
- Cache loop bounds
- Avoid function calls in loops
- Use list comprehensions when appropriate
- Minimize nested loops

**Example:**
```python
# Bad: Function call in loop
result = []
for i in range(len(data)):
    result.append(process(data[i]))

# Good: List comprehension
result = [process(item) for item in data]

# Better: Generator for large datasets
result = (process(item) for item in data)
```

### String Operations

**Efficient String Handling:**
- Use `join()` instead of concatenation
- Use f-strings or `.format()` instead of `%`
- Avoid repeated string operations
- Use string builders for many concatenations

**Example:**
```python
# Bad: O(n²) - creates new string each time
result = ""
for item in items:
    result += item

# Good: O(n) - efficient join
result = "".join(items)
```

## Database Optimizations

### Query Optimization

**Efficient Queries:**
- Use indexes on frequently queried columns
- Select only needed columns (avoid SELECT *)
- Use LIMIT for pagination
- Avoid N+1 queries
- Use JOINs instead of multiple queries
- Use prepared statements

**Example:**
```python
# Bad: N+1 queries
users = User.objects.all()
for user in users:
    posts = Post.objects.filter(user=user)  # N queries

# Good: Single query with JOIN
users = User.objects.prefetch_related('posts').all()
```

### Indexing Strategies

**Effective Indexing:**
- Index foreign keys
- Index columns used in WHERE clauses
- Index columns used in JOINs
- Use composite indexes for multi-column queries
- Monitor index usage and remove unused indexes

### Connection Pooling

**Manage Database Connections:**
- Use connection pools
- Reuse connections
- Set appropriate pool sizes
- Monitor connection usage

## Caching Strategies

### Cache-Aside Pattern

**Application-Managed Cache:**
1. Check cache for data
2. If miss, query database
3. Store result in cache
4. Return data

**Example:**
```python
def get_user(user_id):
    # Check cache
    user = cache.get(f"user:{user_id}")
    if user:
        return user
    
    # Query database
    user = db.query(User).filter(id=user_id).first()
    
    # Store in cache
    cache.set(f"user:{user_id}", user, ttl=3600)
    return user
```

### Write-Through Cache

**Synchronous Write:**
- Write to cache and database simultaneously
- Ensures consistency
- Higher write latency

### Write-Back Cache

**Asynchronous Write:**
- Write to cache immediately
- Write to database asynchronously
- Lower write latency
- Risk of data loss

### Cache Invalidation

**Strategies:**
- Time-based expiration (TTL)
- Event-based invalidation
- Version-based invalidation
- Manual invalidation

## Memory Optimization

### Object Pooling

**Reuse Objects:**
- Reduce garbage collection pressure
- Lower memory allocation overhead
- Useful for frequently created objects

### Lazy Loading

**Load on Demand:**
- Defer object creation until needed
- Reduce initial memory footprint
- Improve startup time

**Example:**
```python
class LazyLoader:
    def __init__(self, loader_func):
        self._loader = loader_func
        self._data = None
    
    @property
    def data(self):
        if self._data is None:
            self._data = self._loader()
        return self._data
```

### Memory Profiling

**Identify Memory Issues:**
- Use memory profilers
- Monitor memory usage
- Identify memory leaks
- Track object lifetimes

## I/O Optimizations

### Asynchronous I/O

**Non-Blocking Operations:**
- Use async/await for I/O operations
- Process multiple requests concurrently
- Improve throughput
- Reduce resource consumption

**Example:**
```python
# Bad: Synchronous I/O
def fetch_data(urls):
    results = []
    for url in urls:
        response = requests.get(url)  # Blocks
        results.append(response.json())
    return results

# Good: Asynchronous I/O
async def fetch_data(urls):
    tasks = [fetch_url(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
```

### Batch Processing

**Group Operations:**
- Batch database writes
- Batch API calls
- Reduce network overhead
- Improve throughput

### Compression

**Reduce Data Size:**
- Compress responses (gzip, brotli)
- Compress database storage
- Reduce network transfer time
- Trade CPU for bandwidth

## Concurrency Patterns

### Thread Pool

**Manage Threads:**
- Reuse threads
- Limit thread count
- Queue tasks
- Handle thread lifecycle

### Process Pool

**Parallel Processing:**
- Use multiple processes
- Bypass GIL (Python)
- True parallelism
- Higher memory overhead

### Async/Await

**Concurrent Execution:**
- Single-threaded concurrency
- Event loop based
- Efficient for I/O-bound tasks
- Lower overhead than threads

## Monitoring and Profiling

### Performance Metrics

**Key Metrics:**
- Response time (p50, p95, p99)
- Throughput (requests/second)
- Error rate
- Resource utilization (CPU, memory, I/O)

### Profiling Tools

**Common Tools:**
- cProfile (Python)
- JProfiler (Java)
- Chrome DevTools (JavaScript)
- Application Performance Monitoring (APM) tools

### Benchmarking

**Measure Performance:**
- Establish baseline
- Compare before/after
- Use realistic test data
- Run multiple iterations
- Account for variance

## Best Practices

1. **Measure First**: Profile before optimizing
2. **Optimize Hot Paths**: Focus on frequently executed code
3. **Avoid Premature Optimization**: Optimize when needed
4. **Test Performance**: Include performance tests
5. **Monitor Production**: Track performance metrics
6. **Document Tradeoffs**: Record optimization decisions

## References

- [High Performance Browser Networking](https://hpbn.co/)
- [System Design Primer](https://github.com/donnemartin/system-design-primer)
- [Performance Best Practices](https://web.dev/performance/)

