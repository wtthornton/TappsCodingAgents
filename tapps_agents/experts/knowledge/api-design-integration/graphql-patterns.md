# GraphQL Patterns

## Overview

GraphQL is a query language for APIs that allows clients to request exactly the data they need. Unlike REST, GraphQL provides a single endpoint and gives clients control over the shape and size of responses.

## Core Concepts

### Schema Definition

**Type System:**
```graphql
type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]!
  createdAt: DateTime!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  comments: [Comment!]!
}

type Query {
  user(id: ID!): User
  users: [User!]!
  post(id: ID!): Post
}
```

### Queries

**Basic Query:**
```graphql
query {
  user(id: "123") {
    name
    email
  }
}
```

**Nested Query:**
```graphql
query {
  user(id: "123") {
    name
    posts {
      title
      comments {
        content
        author {
          name
        }
      }
    }
  }
}
```

**Query with Arguments:**
```graphql
query {
  users(limit: 10, offset: 0, filter: { role: ADMIN }) {
    id
    name
    email
  }
}
```

### Mutations

**Create Mutation:**
```graphql
mutation {
  createUser(input: {
    name: "John Doe"
    email: "john@example.com"
  }) {
    id
    name
    email
  }
}
```

**Update Mutation:**
```graphql
mutation {
  updateUser(id: "123", input: {
    name: "Jane Doe"
  }) {
    id
    name
  }
}
```

**Delete Mutation:**
```graphql
mutation {
  deleteUser(id: "123") {
    success
    message
  }
}
```

## Schema Design Best Practices

### Naming Conventions

**Types:** PascalCase
```graphql
type UserProfile { ... }
type OrderItem { ... }
```

**Fields:** camelCase
```graphql
type User {
  firstName: String!
  lastName: String!
  createdAt: DateTime!
}
```

**Queries/Mutations:** camelCase
```graphql
type Query {
  getUserById: User
  listUsers: [User!]!
}
```

### Field Types

**Scalar Types:**
- `ID`: Unique identifier
- `String`: Text
- `Int`: 32-bit integer
- `Float`: Floating point
- `Boolean`: true/false

**Object Types:**
- Custom types (User, Post)

**Lists:**
- `[String]`: Nullable list, nullable items
- `[String!]`: Nullable list, non-null items
- `[String!]!`: Non-null list, non-null items

**Non-Null:**
- `String!`: Required field
- Use `!` judiciously

### Relationships

**One-to-Many:**
```graphql
type User {
  posts: [Post!]!
}

type Post {
  author: User!
}
```

**Many-to-Many:**
```graphql
type User {
  followers: [User!]!
  following: [User!]!
}

type Post {
  tags: [Tag!]!
}

type Tag {
  posts: [Post!]!
}
```

## Resolver Patterns

### Basic Resolver

**Node.js Example:**
```javascript
const resolvers = {
  Query: {
    user: async (parent, args, context) => {
      return await context.db.user.findById(args.id);
    },
    users: async (parent, args, context) => {
      return await context.db.user.findAll(args);
    }
  },
  User: {
    posts: async (parent, args, context) => {
      return await context.db.post.findByUserId(parent.id);
    }
  }
};
```

**Python Example:**
```python
from ariadne import QueryType

query = QueryType()

@query.field("user")
async def resolve_user(_, info, id):
    db = info.context["db"]
    return await db.user.get_by_id(id)

@query.field("users")
async def resolve_users(_, info, **kwargs):
    db = info.context["db"]
    return await db.user.list(**kwargs)
```

### Field-Level Resolvers

**Resolve Fields on Demand:**
```python
from ariadne import ObjectType

user = ObjectType("User")

@user.field("fullName")
def resolve_full_name(parent, info):
    return f"{parent.first_name} {parent.last_name}"

@user.field("postCount")
async def resolve_post_count(parent, info):
    db = info.context["db"]
    return await db.post.count_by_user_id(parent.id)
```

## N+1 Problem

### Problem

**N+1 Queries:**
```graphql
query {
  users {
    name
    posts {
      title
      comments {
        content
      }
    }
  }
}
```

This could result in:
- 1 query for users
- N queries for posts (one per user)
- M queries for comments (one per post)

### Solution: DataLoader

**Batch Loading:**
```javascript
const DataLoader = require('dataloader');

const userLoader = new DataLoader(async (ids) => {
  const users = await db.user.findByIds(ids);
  return ids.map(id => users.find(u => u.id === id));
});

const resolvers = {
  Post: {
    author: async (parent) => {
      return userLoader.load(parent.authorId);
    }
  }
};
```

**Python DataLoader:**
```python
from promise import Promise
from promise.dataloader import DataLoader

class UserLoader(DataLoader):
    def batch_load_fn(self, keys):
        return Promise.resolve(
            db.user.find_by_ids(keys)
        )

user_loader = UserLoader()

def resolve_author(parent, info):
    return user_loader.load(parent.author_id)
```

## Pagination Patterns

### Offset-Based Pagination

**Schema:**
```graphql
type Query {
  users(offset: Int, limit: Int): UserConnection!
}

type UserConnection {
  nodes: [User!]!
  totalCount: Int!
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
}
```

**Resolver:**
```python
@query.field("users")
async def resolve_users(_, info, offset=0, limit=10):
    db = info.context["db"]
    users, total = await db.user.list_paginated(offset, limit)
    
    return {
        "nodes": users,
        "totalCount": total,
        "hasNextPage": offset + limit < total,
        "hasPreviousPage": offset > 0
    }
```

### Cursor-Based Pagination

**Schema:**
```graphql
type Query {
  users(first: Int, after: String): UserConnection!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

**Query:**
```graphql
query {
  users(first: 10, after: "cursor123") {
    edges {
      node {
        id
        name
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Error Handling

### GraphQL Errors

**Format:**
```json
{
  "errors": [
    {
      "message": "User not found",
      "extensions": {
        "code": "NOT_FOUND",
        "field": "user",
        "argument": "id"
      },
      "path": ["user"]
    }
  ],
  "data": null
}
```

**Custom Error Classes:**
```python
class GraphQLError(Exception):
    def __init__(self, message, code, extensions=None):
        self.message = message
        self.code = code
        self.extensions = extensions or {}
```

### Partial Success

**Return Data and Errors:**
```json
{
  "data": {
    "user": null,
    "posts": [...]
  },
  "errors": [
    {
      "message": "User not found",
      "path": ["user"]
    }
  ]
}
```

## Authentication and Authorization

### Context-Based Auth

**Add to Context:**
```python
from ariadne import make_executable_schema

def create_context(request):
    token = request.headers.get("Authorization")
    user = authenticate_token(token) if token else None
    
    return {
        "request": request,
        "user": user,
        "db": get_database()
    }

schema = make_executable_schema(type_defs, resolvers)
result = schema.execute_sync(
    query,
    context_value=create_context(request)
)
```

### Field-Level Authorization

**Check Permissions:**
```python
@user.field("email")
def resolve_email(parent, info):
    # Only allow user to see their own email
    current_user = info.context["user"]
    if current_user and current_user.id == parent.id:
        return parent.email
    raise PermissionError("Not authorized")
```

## Subscriptions

### Real-Time Updates

**Schema:**
```graphql
type Subscription {
  postCreated: Post!
  userUpdated(userId: ID!): User!
}
```

**Implementation:**
```python
from ariadne import SubscriptionType

subscription = SubscriptionType()

@subscription.source("postCreated")
async def post_created_generator(obj, info):
    async for post in db.post.watch_created():
        yield post

@subscription.field("postCreated")
def post_created_resolver(post, info):
    return post
```

## Performance Optimization

### Query Complexity Analysis

**Limit Query Depth:**
```python
def check_query_complexity(query_ast, max_depth=5):
    depth = calculate_depth(query_ast)
    if depth > max_depth:
        raise GraphQLError("Query too deep")
```

### Caching Strategies

**Field-Level Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def resolve_user_stats(parent, info):
    return db.user.calculate_stats(parent.id)
```

**Response Caching:**
- Cache full query results
- Invalidate on mutations
- Use ETags for HTTP caching

## Best Practices

1. **Design schema first:** Start with schema design
2. **Use appropriate types:** Non-null judiciously
3. **Implement DataLoader:** Prevent N+1 queries
4. **Add pagination:** For list fields
5. **Handle errors consistently:** Use error extensions
6. **Secure properly:** Authentication and authorization
7. **Monitor performance:** Track query complexity
8. **Document with descriptions:** Add schema descriptions
9. **Version carefully:** Use schema evolution
10. **Test thoroughly:** Test queries and mutations

## Common Anti-Patterns

### Avoid

**Too Deep Nesting:**
```graphql
query {
  user {
    posts {
      comments {
        author {
          posts {
            comments { ... }
          }
        }
      }
    }
  }
}
```

**Fetching Everything:**
```graphql
query {
  users {
    # Don't fetch all fields if not needed
    id name email posts comments followers ...
  }
}
```

**Missing Pagination:**
```graphql
type Query {
  users: [User!]!  # Could return millions
}
```

