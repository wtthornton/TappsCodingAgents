# Database Performance Optimization

## Overview

Database performance is critical for application scalability. This guide covers query optimization, indexing, connection management, and database tuning.

## Query Optimization

### Efficient Queries

**Best Practices:**
- Select only needed columns
- Use appropriate JOINs
- Avoid SELECT *
- Use LIMIT for pagination
- Filter early

**Example:**
```sql
-- Bad: Selects all columns
SELECT * FROM users WHERE active = true;

-- Good: Select only needed columns
SELECT id, name, email FROM users WHERE active = true LIMIT 100;
```

### Avoid N+1 Queries

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

### Use Indexes

**Effective Indexing:**
- Index frequently queried columns
- Index foreign keys
- Index columns in WHERE clauses
- Index columns in JOINs
- Use composite indexes for multi-column queries

**Example:**
```sql
-- Create index on frequently queried column
CREATE INDEX idx_user_email ON users(email);

-- Composite index for multi-column queries
CREATE INDEX idx_user_status_created ON users(status, created_at);
```

## Indexing Strategies

### Index Types

**B-Tree Indexes:**
- Default index type
- Good for equality and range queries
- Most common

**Hash Indexes:**
- Fast equality lookups
- Not for range queries
- Memory-based

**Bitmap Indexes:**
- Good for low-cardinality columns
- Space efficient
- Fast for AND/OR operations

### Index Selection

**When to Index:**
- Frequently queried columns
- Foreign keys
- Columns in WHERE clauses
- Columns in JOINs
- Columns in ORDER BY

**When Not to Index:**
- Rarely queried columns
- Frequently updated columns
- Very small tables
- Low-cardinality columns (unless bitmap)

## Connection Management

### Connection Pooling

**Reuse Connections:**
- Reduce connection overhead
- Limit connection count
- Better resource utilization

**Pool Configuration:**
```python
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://user:pass@localhost/db',
    pool_size=10,           # Minimum connections
    max_overflow=20,        # Maximum connections
    pool_timeout=30,        # Wait time
    pool_recycle=3600       # Recycle after 1 hour
)
```

### Connection Lifecycle

**Proper Management:**
- Acquire from pool
- Use connection
- Return to pool
- Handle errors

## Query Execution Plans

### EXPLAIN

**Analyze Queries:**
```sql
EXPLAIN ANALYZE
SELECT * FROM users WHERE email = 'user@example.com';
```

**Key Metrics:**
- Execution time
- Rows scanned
- Index usage
- Join algorithms

### Optimizing Execution Plans

**Improve Plans:**
- Add missing indexes
- Rewrite queries
- Update statistics
- Analyze tables

## Database Tuning

### Configuration Tuning

**Key Parameters:**
- Memory settings
- Connection limits
- Query cache size
- Buffer pool size
- Log settings

### Monitoring

**Key Metrics:**
- Query execution time
- Connection pool usage
- Cache hit rate
- Lock wait time
- I/O wait time

## Partitioning

### Table Partitioning

**Benefits:**
- Faster queries (smaller partitions)
- Easier maintenance
- Better performance

**Partition Types:**
- Range partitioning
- Hash partitioning
- List partitioning

**Example:**
```sql
-- Partition by date
CREATE TABLE orders (
    id INT,
    order_date DATE,
    ...
) PARTITION BY RANGE (order_date);
```

## Denormalization

### When to Denormalize

**Trade-offs:**
- Faster reads
- Slower writes
- Data redundancy
- Consistency challenges

**Use Cases:**
- Read-heavy workloads
- Reporting queries
- Performance critical paths

## Best Practices

1. **Index Strategically**: Index frequently queried columns
2. **Optimize Queries**: Write efficient queries
3. **Use Connection Pools**: Reuse connections
4. **Monitor Performance**: Track query times
5. **Partition Large Tables**: Improve query performance
6. **Update Statistics**: Keep statistics current
7. **Test Queries**: Profile before deploying
8. **Document Decisions**: Record optimization choices

## Common Issues

### Slow Queries

**Causes:**
- Missing indexes
- Inefficient queries
- Large result sets
- Lock contention

**Solutions:**
- Add indexes
- Optimize queries
- Use pagination
- Reduce lock time

### Connection Exhaustion

**Causes:**
- Too many connections
- Not returning connections
- Connection leaks

**Solutions:**
- Use connection pools
- Always close connections
- Monitor connection usage
- Set appropriate limits

## References

- [Database Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [MySQL Performance Tuning](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)

