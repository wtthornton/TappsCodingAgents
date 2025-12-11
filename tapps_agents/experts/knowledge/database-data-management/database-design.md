# Database Design

## Overview

Database design involves structuring data efficiently to support application requirements. This guide covers normalization, schema design, entity relationships, and data modeling principles.

## Normalization

### First Normal Form (1NF)

**Eliminate Repeating Groups:**
- Each column contains atomic values
- No repeating groups
- Unique row identifier

**Example:**
```sql
-- Before (Violates 1NF)
Orders (OrderID, Items)

-- After (1NF)
Orders (OrderID)
OrderItems (OrderID, ItemID, Quantity, Price)
```

### Second Normal Form (2NF)

**Eliminate Partial Dependencies:**
- Must be in 1NF
- All non-key attributes fully dependent on primary key

**Example:**
```sql
-- Violates 2NF (ProductName depends on ProductID, not OrderID)
OrderItems (OrderID, ProductID, ProductName, Quantity)

-- After (2NF)
OrderItems (OrderID, ProductID, Quantity)
Products (ProductID, ProductName)
```

### Third Normal Form (3NF)

**Eliminate Transitive Dependencies:**
- Must be in 2NF
- No non-key attribute depends on another non-key attribute

**Example:**
```sql
-- Violates 3NF (CustomerCity depends on CustomerID, not OrderID)
Orders (OrderID, CustomerID, CustomerCity)

-- After (3NF)
Orders (OrderID, CustomerID)
Customers (CustomerID, City)
```

### Denormalization

**When to Denormalize:**
- Read performance critical
- Complex joins expensive
- Data rarely changes
- Acceptable redundancy

**Trade-offs:**
- Faster reads
- Slower writes
- More storage
- Data consistency challenges

## Entity Relationships

### One-to-One

**Single Association:**
```sql
Users (UserID, ...)
UserProfiles (UserID, Bio, Avatar, ...)
-- UserID is both PK and FK
```

### One-to-Many

**Parent-Child Relationship:**
```sql
Users (UserID, ...)
Posts (PostID, UserID, ...)
-- UserID is FK in Posts
```

### Many-to-Many

**Junction Table:**
```sql
Users (UserID, ...)
Roles (RoleID, ...)
UserRoles (UserID, RoleID)
-- Junction table with composite PK
```

## Schema Design Principles

### Primary Keys

**Best Practices:**
- Unique identifier
- Never change
- Non-nullable
- Preferably sequential (for performance)

**Types:**
- Auto-increment integers
- UUIDs (for distributed systems)
- Natural keys (if stable)

### Foreign Keys

**Referential Integrity:**
```sql
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY,
    CustomerID INT,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);
```

### Indexes

**Performance Optimization:**
- Primary keys (automatic)
- Foreign keys
- Frequently queried columns
- JOIN columns

### Constraints

**Data Integrity:**
- NOT NULL
- UNIQUE
- CHECK
- DEFAULT

## Data Types

### Numeric

**Choose Appropriately:**
- INT vs BIGINT (size vs range)
- DECIMAL vs FLOAT (precision)
- Consider storage impact

### Strings

**VARCHAR vs CHAR:**
- VARCHAR: Variable length
- CHAR: Fixed length
- TEXT: Large text

### Dates and Times

**Types:**
- DATE: Date only
- TIME: Time only
- TIMESTAMP: Date and time
- TIMESTAMP WITH TIME ZONE: Timezone aware

### Booleans

**Use Native Types:**
- BOOLEAN (where supported)
- TINYINT(1) alternative
- Avoid strings ('true', 'false')

## Best Practices

1. **Normalize First:** Start normalized
2. **Denormalize Strategically:** For performance
3. **Use Appropriate Types:** Match domain needs
4. **Define Relationships:** Foreign keys
5. **Add Constraints:** Data integrity
6. **Index Thoughtfully:** Balance read/write
7. **Document Schema:** Clear naming
8. **Plan for Growth:** Scalability considerations
9. **Consider Partitioning:** For large tables
10. **Review Regularly:** Refactor as needed

