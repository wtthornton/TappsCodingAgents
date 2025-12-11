# ACID vs CAP Theorem

## Overview

ACID and CAP are fundamental concepts for understanding database guarantees. ACID focuses on transaction reliability, while CAP describes trade-offs in distributed systems.

## ACID Properties

### Atomicity

**All or Nothing:**
- Transaction completes entirely or not at all
- No partial updates
- Rollback on failure

**Example:**
```sql
BEGIN;
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
-- Both succeed or both fail
```

### Consistency

**Valid State Transitions:**
- Database remains in valid state
- Constraints always satisfied
- Referential integrity maintained

### Isolation

**Concurrent Transactions:**
- Transactions don't interfere
- Isolation levels: Read Uncommitted, Read Committed, Repeatable Read, Serializable

**Isolation Levels:**
- **Read Uncommitted:** Lowest isolation, dirty reads possible
- **Read Committed:** No dirty reads, non-repeatable reads possible
- **Repeatable Read:** No non-repeatable reads, phantom reads possible
- **Serializable:** Highest isolation, no anomalies

### Durability

**Permanent Changes:**
- Committed transactions persist
- Survives system crashes
- Written to persistent storage

**Implementation:**
- Write-ahead logging (WAL)
- Transaction logs
- Replication

## CAP Theorem

**Can Only Guarantee Two of Three:**

### Consistency

**All Nodes See Same Data:**
- All replicas have same data
- Strong consistency
- Synchronous replication

### Availability

**System Remains Operational:**
- Every request gets response
- No downtime
- No errors (non-failure responses)

### Partition Tolerance

**Network Partitions Handled:**
- System continues despite network failures
- Nodes can't communicate
- Required for distributed systems

## CAP Trade-offs

### CP (Consistency + Partition Tolerance)

**Sacrifice Availability:**
- Strong consistency
- Blocks during partitions
- Examples: MongoDB (with strong consistency), HBase

### AP (Availability + Partition Tolerance)

**Sacrifice Consistency:**
- Always available
- Eventual consistency
- Examples: DynamoDB, Cassandra, CouchDB

### CA (Consistency + Availability)

**Sacrifice Partition Tolerance:**
- Single-node systems
- Not truly distributed
- Examples: Traditional SQL databases (single instance)

## Real-World Implications

### SQL Databases

**Typically ACID + CP:**
- Strong consistency
- ACID transactions
- May block during partitions
- Examples: PostgreSQL, MySQL, Oracle

### NoSQL Databases

**Various Choices:**
- **DynamoDB:** AP (configurable consistency)
- **Cassandra:** AP (tunable consistency)
- **MongoDB:** CP (with strong consistency)
- **Redis:** CP (single-node) or AP (cluster mode)

### Eventual Consistency

**Accept Temporary Inconsistency:**
- Replicas sync eventually
- Acceptable for many use cases
- Conflict resolution needed

## Choosing the Right Model

### Use ACID When:

- Financial transactions
- Critical data integrity
- Strong consistency required
- Traditional SQL databases

### Use Eventual Consistency When:

- High availability critical
- Can tolerate temporary inconsistency
- High write throughput
- Global distribution

### Use Partition Tolerance When:

- Distributed system
- Multiple data centers
- Network failures possible
- Scalability needed

## Best Practices

1. **Understand Requirements:** Consistency vs availability needs
2. **Choose Appropriate Database:** Match CAP trade-offs
3. **Design for Failure:** Assume partitions will occur
4. **Handle Conflicts:** Eventual consistency strategies
5. **Monitor Consistency:** Track replication lag
6. **Document Decisions:** Why chosen model
7. **Test Partition Scenarios:** How system behaves
8. **Balance Trade-offs:** Match business needs
9. **Consider Hybrid:** Different models for different data
10. **Review Regularly:** As requirements change

