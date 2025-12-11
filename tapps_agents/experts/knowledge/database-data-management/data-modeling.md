# Data Modeling

## Overview

Data modeling designs the structure of data to meet application requirements. This guide covers entity relationships, data patterns, modeling techniques, and best practices.

## Modeling Process

### Conceptual Model

**High-Level View:**
- Entities and relationships
- Business concepts
- Domain understanding
- ER diagrams

**Example:**
```
User ----< Order
User ----< Post
Post ----< Comment
```

### Logical Model

**Detailed Structure:**
- Attributes
- Data types
- Relationships
- Constraints
- Normalization

### Physical Model

**Implementation:**
- Tables and columns
- Indexes
- Partitioning
- Storage considerations

## Entity Relationships

### One-to-One

**Single Association:**
- User → UserProfile
- Employee → EmployeeDetails

**Implementation:**
- Separate tables with FK
- Same table (if always present)

### One-to-Many

**Parent-Child:**
- User → Orders
- Customer → Invoices
- Category → Products

**Implementation:**
- FK in child table

### Many-to-Many

**Junction Table:**
- Users ↔ Roles
- Products ↔ Categories
- Students ↔ Courses

**Implementation:**
- Junction table with FKs

## Data Patterns

### Master-Detail

**Header-Detail:**
```
Order (master)
  OrderItems (detail)
```

**Characteristics:**
- Detail depends on master
- Deletion cascades
- Transactions span both

### Lookup Tables

**Reference Data:**
- Status codes
- Categories
- Countries
- Currency codes

**Benefits:**
- Centralized maintenance
- Data consistency
- Validation

### Audit Trail

**Track Changes:**
```sql
CREATE TABLE audit_log (
    id INT PRIMARY KEY,
    table_name VARCHAR(100),
    record_id INT,
    action VARCHAR(10),  -- INSERT, UPDATE, DELETE
    old_values JSON,
    new_values JSON,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP
);
```

### Soft Delete

**Mark as Deleted:**
```sql
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;

-- Soft delete
UPDATE users SET deleted_at = NOW() WHERE id = ?;

-- Query active
SELECT * FROM users WHERE deleted_at IS NULL;
```

## Modeling Techniques

### Star Schema

**Data Warehouse:**
- Fact table (transactions)
- Dimension tables (descriptors)
- Denormalized structure

**Example:**
```
Fact: Sales
Dimensions: Product, Customer, Time, Store
```

### Snowflake Schema

**Normalized Dimensions:**
- Dimensions normalized
- More joins
- Less redundancy

### Event Sourcing

**Store Events:**
```
Events: UserCreated, OrderPlaced, PaymentReceived
State: Reconstructed from events
```

## Best Practices

1. **Start with Requirements:** Understand use case
2. **Use Appropriate Model:** Conceptual → Logical → Physical
3. **Normalize First:** Then denormalize if needed
4. **Document Relationships:** Clear ER diagrams
5. **Plan for Growth:** Scalability considerations
6. **Consider Access Patterns:** Query optimization
7. **Handle History:** Audit trails, versioning
8. **Validate Early:** Constraints and checks
9. **Review Regularly:** Refactor as needed
10. **Communicate:** Team alignment

