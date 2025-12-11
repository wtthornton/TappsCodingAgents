# Performance Anti-Patterns

## Overview

Anti-patterns are common mistakes that lead to poor performance. This guide identifies common performance anti-patterns and how to avoid them.

## Code Anti-Patterns

### Premature Optimization

**Problem:**
- Optimizing before profiling
- Optimizing non-critical paths
- Complex code for minimal gain

**Solution:**
- Profile first
- Optimize hot paths
- Measure impact
- Keep code simple

### N+1 Query Problem

**Problem:**
```python
# Bad: N+1 queries
users = User.objects.all()
for user in users:
    posts = Post.objects.filter(user=user)  # N queries
```

**Solution:**
```python
# Good: Single query with JOIN
users = User.objects.prefetch_related('posts').all()
```

### String Concatenation in Loops

**Problem:**
```python
# Bad: O(n²) - creates new string each time
result = ""
for item in items:
    result += item
```

**Solution:**
```python
# Good: O(n) - efficient join
result = "".join(items)
```

### Unnecessary Object Creation

**Problem:**
- Creating objects in loops
- Not reusing objects
- Creating temporary objects

**Solution:**
- Reuse objects
- Use object pools
- Minimize allocations

## Database Anti-Patterns

### SELECT * Queries

**Problem:**
- Fetching unnecessary columns
- Increased memory usage
- Slower queries
- Network overhead

**Solution:**
- Select only needed columns
- Use projections
- Optimize data transfer

### Missing Indexes

**Problem:**
- Slow queries
- Full table scans
- Poor join performance

**Solution:**
- Add indexes on frequently queried columns
- Index foreign keys
- Monitor query performance

### Large Result Sets

**Problem:**
- Loading all records
- Memory exhaustion
- Slow queries

**Solution:**
- Use pagination
- Limit result sets
- Stream large datasets

## Caching Anti-Patterns

### Cache Stampede

**Problem:**
- Multiple requests miss cache simultaneously
- All query database
- Database overload

**Solution:**
- Use locks
- Stale-while-revalidate
- Pre-warm cache

### Cache Invalidation Issues

**Problem:**
- Stale data
- Inconsistent cache
- Wrong invalidation strategy

**Solution:**
- Proper invalidation
- Version-based cache
- Event-driven invalidation

### Over-Caching

**Problem:**
- Caching everything
- Memory waste
- Cache pollution

**Solution:**
- Cache selectively
- Monitor cache hit rate
- Use appropriate TTL

## Concurrency Anti-Patterns

### Race Conditions

**Problem:**
- Shared mutable state
- Non-atomic operations
- Data corruption

**Solution:**
- Use locks
- Immutable data
- Thread-safe collections

### Deadlocks

**Problem:**
- Circular dependencies
- Multiple locks
- Lock ordering issues

**Solution:**
- Consistent lock ordering
- Timeout on locks
- Avoid nested locks

### Thread Pool Exhaustion

**Problem:**
- Too many threads
- Blocking operations
- Resource exhaustion

**Solution:**
- Limit thread count
- Use async I/O
- Monitor thread pool

## I/O Anti-Patterns

### Synchronous I/O

**Problem:**
- Blocking operations
- Poor resource utilization
- Low throughput

**Solution:**
- Use async I/O
- Non-blocking operations
- Concurrent I/O

### Small I/O Operations

**Problem:**
- Many small reads/writes
- High overhead
- Poor performance

**Solution:**
- Batch operations
- Buffer data
- Larger I/O operations

### Not Closing Resources

**Problem:**
- Resource leaks
- File handle exhaustion
- Connection pool exhaustion

**Solution:**
- Always close resources
- Use context managers
- Proper cleanup

## Memory Anti-Patterns

### Memory Leaks

**Problem:**
- Unclosed resources
- Event listeners not removed
- Circular references

**Solution:**
- Proper cleanup
- Weak references
- Monitor memory usage

### Excessive Memory Allocation

**Problem:**
- Allocating in hot paths
- Large temporary objects
- Memory churn

**Solution:**
- Reuse objects
- Object pools
- Minimize allocations

## Architecture Anti-Patterns

### Monolithic Design

**Problem:**
- Hard to scale
- Single point of failure
- Difficult to optimize

**Solution:**
- Microservices
- Modular design
- Horizontal scaling

### Tight Coupling

**Problem:**
- Hard to optimize
- Difficult to scale
- Poor performance isolation

**Solution:**
- Loose coupling
- Service boundaries
- Independent scaling

## Best Practices to Avoid Anti-Patterns

1. **Profile First**: Always measure before optimizing
2. **Use Patterns**: Follow established patterns
3. **Monitor**: Track performance metrics
4. **Test**: Include performance tests
5. **Review**: Code reviews for performance
6. **Document**: Document performance decisions
7. **Refactor**: Continuously improve performance

## References

- [Performance Anti-Patterns](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/)

