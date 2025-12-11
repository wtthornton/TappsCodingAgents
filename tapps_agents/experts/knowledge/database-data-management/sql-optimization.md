# SQL Query Optimization

## Overview

SQL optimization improves query performance through proper indexing, query structure, and execution planning. This guide covers indexing strategies, query patterns, and optimization techniques from a design perspective.

## Indexing Strategies

### When to Index

**Index These Columns:**
- Primary keys (automatic)
- Foreign keys
- Frequently filtered (WHERE)
- Frequently sorted (ORDER BY)
- JOIN columns

### Index Types

**B-Tree (Default):**
- Balanced tree structure
- Good for range queries
- Most common type

**Hash:**
- Fast equality lookups
- Not for range queries
- Memory-based

**Composite Indexes:**
```sql
-- Multi-column index
CREATE INDEX idx_user_status_created 
ON users(status, created_at);

-- Can use for:
-- WHERE status = ? AND created_at > ?
-- WHERE status = ?
-- Not: WHERE created_at > ? (unless status also filtered)
```

**Covering Indexes:**
```sql
-- Index includes all needed columns
CREATE INDEX idx_user_lookup 
ON users(id, name, email);

-- Query uses index only (no table access)
SELECT id, name, email FROM users WHERE id = ?;
```

### Index Guidelines

**Don't Over-Index:**
- Indexes slow writes
- Use indexes selectively
- Monitor index usage
- Remove unused indexes

## Query Optimization

### SELECT Only Needed Columns

```sql
-- Bad: Fetch all columns
SELECT * FROM users WHERE active = true;

-- Good: Only needed columns
SELECT id, name, email FROM users WHERE active = true;
```

### Use WHERE Efficiently

**Sargable Queries:**
```sql
-- Bad: Function on column prevents index use
SELECT * FROM users WHERE YEAR(created_at) = 2026;

-- Good: Index can be used
SELECT * FROM users WHERE created_at >= '2026-01-01' 
  AND created_at < '2027-01-01';
```

### JOIN Optimization

**Efficient JOINs:**
```sql
-- Ensure JOIN columns are indexed
-- Use appropriate JOIN type
-- Filter early

SELECT u.name, o.total
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'  -- Filter before JOIN
  AND o.created_at > '2026-01-01';
```

### Avoid N+1 Queries

**Use JOINs:**
```sql
-- Bad: Multiple queries
-- 1 query for users
-- N queries for orders

-- Good: Single query with JOIN
SELECT u.*, o.*
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.active = true;
```

### Use EXISTS for Existence Checks

```sql
-- Good: EXISTS stops at first match
SELECT * FROM users u
WHERE EXISTS (
  SELECT 1 FROM orders o 
  WHERE o.user_id = u.id
);

-- Less efficient: COUNT
SELECT * FROM users u
WHERE (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) > 0;
```

### Limit Result Sets

```sql
-- Use LIMIT for pagination
SELECT * FROM users
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;

-- Use TOP (SQL Server)
SELECT TOP 20 * FROM users;
```

## EXPLAIN and Query Plans

### Understanding Query Plans

**Read Execution Plan:**
- Sequential scans vs index scans
- Join methods (nested loop, hash, merge)
- Filter application order
- Estimated vs actual rows

**PostgreSQL:**
```sql
EXPLAIN ANALYZE
SELECT * FROM users WHERE email = 'user@example.com';
```

**MySQL:**
```sql
EXPLAIN
SELECT * FROM users WHERE email = 'user@example.com';
```

## Best Practices

1. **Index strategically:** Not every column
2. **Analyze query plans:** Use EXPLAIN
3. **Filter early:** Reduce result sets
4. **Use appropriate JOINs:** INNER, LEFT, etc.
5. **Avoid SELECT *:** Only needed columns
6. **Use LIMIT:** For pagination
7. **Batch operations:** Multiple rows at once
8. **Monitor slow queries:** Identify bottlenecks
9. **Update statistics:** For query optimizer
10. **Review regularly:** As data grows

