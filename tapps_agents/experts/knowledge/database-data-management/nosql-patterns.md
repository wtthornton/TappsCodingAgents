# NoSQL Patterns

## Overview

NoSQL databases provide flexible data models for specific use cases. This guide covers document, key-value, column-family, and graph databases, their patterns, and when to use them.

## Database Types

### Document Databases

**Structure:**
- JSON/BSON documents
- Embedded data
- Flexible schema

**Examples:** MongoDB, CouchDB, DynamoDB

**Use Cases:**
- Content management
- User profiles
- Catalog data
- Semi-structured data

**Pattern:**
```json
{
  "_id": "user123",
  "name": "John Doe",
  "email": "john@example.com",
  "address": {
    "street": "123 Main St",
    "city": "San Francisco"
  },
  "orders": [
    {"orderId": "o1", "total": 99.99},
    {"orderId": "o2", "total": 149.99}
  ]
}
```

### Key-Value Stores

**Structure:**
- Simple key-value pairs
- Fast lookups
- Minimal querying

**Examples:** Redis, Memcached, DynamoDB

**Use Cases:**
- Caching
- Session storage
- Real-time data
- Configuration

**Pattern:**
```
key: "user:123"
value: {"name": "John", "email": "john@example.com"}

key: "session:abc123"
value: {"userId": "123", "expires": "2026-01-16"}
```

### Column-Family Stores

**Structure:**
- Column families (tables)
- Rows with flexible columns
- Wide tables

**Examples:** Cassandra, HBase, Bigtable

**Use Cases:**
- Time-series data
- Event logging
- Analytics
- High write throughput

**Pattern:**
```
Row Key: user123
  Column Family: profile
    name: "John"
    email: "john@example.com"
  Column Family: activity
    login:20260115: "2026-01-15T10:00:00Z"
    login:20260116: "2026-01-16T09:00:00Z"
```

### Graph Databases

**Structure:**
- Nodes (entities)
- Edges (relationships)
- Properties on both

**Examples:** Neo4j, Amazon Neptune, ArangoDB

**Use Cases:**
- Social networks
- Recommendation engines
- Fraud detection
- Knowledge graphs

**Pattern:**
```
(User:John) -[:FRIENDS_WITH]-> (User:Jane)
(User:John) -[:LIKES]-> (Product:123)
(Product:123) -[:CATEGORY]-> (Category:Electronics)
```

## Design Patterns

### Document Embedding vs References

**Embed (One-to-Few):**
```json
{
  "user": "john",
  "addresses": [
    {"type": "home", "street": "123 Main"},
    {"type": "work", "street": "456 Oak"}
  ]
}
```

**Reference (One-to-Many):**
```json
// User document
{"_id": "user123", "name": "John"}

// Separate orders collection
{"_id": "order1", "userId": "user123", "total": 99.99}
```

### Denormalization

**Duplicate Data for Performance:**
```json
// Order document includes user info
{
  "_id": "order123",
  "userId": "user123",
  "userName": "John Doe",  // Denormalized
  "userEmail": "john@example.com",  // Denormalized
  "items": [...]
}
```

### Sharding

**Partition Data:**
- Shard by user ID
- Shard by region
- Distribute across nodes
- Horizontal scaling

## Query Patterns

### Document Queries

**MongoDB Example:**
```javascript
// Find users by city
db.users.find({ "address.city": "San Francisco" })

// Aggregate query
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $group: { _id: "$userId", total: { $sum: "$total" } } }
])
```

### Graph Queries

**Neo4j Cypher Example:**
```cypher
// Find friends of friends
MATCH (user:User {id: "123"})-[:FRIENDS_WITH]->(friend)-[:FRIENDS_WITH]->(friendOfFriend)
RETURN friendOfFriend
```

## When to Use NoSQL

### Use NoSQL When:

- **Flexible Schema:** Schema changes frequently
- **Horizontal Scaling:** Need to scale out
- **High Write Throughput:** Many writes
- **Semi-structured Data:** JSON-like data
- **Specific Use Cases:** Graph, time-series, etc.

### Use SQL When:

- **Complex Queries:** JOINs, aggregations
- **ACID Requirements:** Strong consistency
- **Structured Data:** Relational data
- **Mature Ecosystem:** Established tools
- **Reporting:** BI and analytics

## Best Practices

1. **Choose Right Type:** Match use case
2. **Design for Access Patterns:** Query patterns first
3. **Denormalize Strategically:** For performance
4. **Plan for Sharding:** From the start
5. **Index Appropriately:** Different indexing models
6. **Handle Consistency:** Eventual vs strong
7. **Monitor Performance:** Different metrics
8. **Backup and Recovery:** Plan DR
9. **Security:** Access control and encryption
10. **Hybrid Approach:** SQL + NoSQL when needed

