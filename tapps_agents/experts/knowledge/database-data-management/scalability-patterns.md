# Database Scalability Patterns

## Overview

Database scalability patterns handle growing data and traffic. This guide covers replication, sharding, partitioning, and caching strategies for scaling databases.

## Replication

### Master-Slave Replication

**Read Scaling:**
- Master handles writes
- Slaves handle reads
- Async replication
- Eventual consistency

**Use Cases:**
- Read-heavy workloads
- Reporting and analytics
- Geographic distribution

### Master-Master Replication

**Bi-Directional:**
- Both masters handle writes
- Sync or async
- Conflict resolution needed

**Use Cases:**
- Write distribution
- Geographic redundancy
- High availability

### Read Replicas

**Scale Reads:**
```sql
-- Write to master
INSERT INTO orders ... -- → Master

-- Read from replica
SELECT * FROM orders ... -- → Replica 1, 2, 3
```

**Benefits:**
- Distribute read load
- Reduce master load
- Better performance

## Sharding

### Horizontal Partitioning

**Split by Key:**
- Partition by user ID
- Partition by region
- Partition by date

**Sharding Strategies:**

**Range-Based:**
```
Shard 1: UserID 1-1000000
Shard 2: UserID 1000001-2000000
Shard 3: UserID 2000001-3000000
```

**Hash-Based:**
```python
shard_id = hash(user_id) % num_shards
```

**Directory-Based:**
```
Lookup table: user_id → shard_id
```

### Challenges

**Cross-Shard Queries:**
- More complex queries
- Aggregations across shards
- Distributed transactions

**Rebalancing:**
- Data movement
- Downtime considerations
- Consistency during move

## Partitioning

### Table Partitioning

**Range Partitioning:**
```sql
CREATE TABLE orders (
    id INT,
    created_at DATE,
    ...
) PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027)
);
```

**List Partitioning:**
```sql
CREATE TABLE users (
    id INT,
    region VARCHAR(50),
    ...
) PARTITION BY LIST (region) (
    PARTITION p_us VALUES IN ('US'),
    PARTITION p_eu VALUES IN ('EU', 'UK'),
    PARTITION p_asia VALUES IN ('ASIA')
);
```

**Hash Partitioning:**
```sql
CREATE TABLE orders (
    id INT,
    ...
) PARTITION BY HASH(id) PARTITIONS 4;
```

### Benefits

- Faster queries (pruning)
- Easier maintenance
- Parallel operations
- Archive old partitions

## Caching Strategies

### Application-Level Caching

**In-Memory Cache:**
- Redis
- Memcached
- Cache frequently accessed data

**Patterns:**
- Cache-aside
- Write-through
- Write-behind

### Database Query Cache

**Cache Query Results:**
- Cache SELECT results
- Invalidate on updates
- TTL-based expiration

### Materialized Views

**Pre-computed Results:**
```sql
CREATE MATERIALIZED VIEW user_stats AS
SELECT 
    user_id,
    COUNT(*) as order_count,
    SUM(total) as total_spent
FROM orders
GROUP BY user_id;

-- Refresh periodically
REFRESH MATERIALIZED VIEW user_stats;
```

## Best Practices

1. **Start Simple:** Replication before sharding
2. **Monitor Performance:** Track bottlenecks
3. **Plan for Growth:** Design for scale
4. **Choose Right Strategy:** Match use case
5. **Handle Failures:** Replication for HA
6. **Cache Strategically:** Reduce database load
7. **Partition Large Tables:** Improve performance
8. **Balance Load:** Distribute evenly
9. **Test Scaling:** Load testing
10. **Document Strategy:** Team alignment

