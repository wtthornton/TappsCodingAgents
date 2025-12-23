# RESTful API Design

## Overview

REST (Representational State Transfer) is an architectural style for designing networked applications. RESTful APIs use HTTP methods to perform operations on resources, providing a stateless, scalable approach to web services.

## REST Principles

### 1. Resource-Based URLs

**Resources are nouns, not verbs:**
```http
# Good: Resource-based
GET    /api/users
GET    /api/users/123
POST   /api/users
PUT    /api/users/123
DELETE /api/users/123

# Bad: Action-based
GET    /api/getUsers
POST   /api/createUser
POST   /api/updateUser/123
POST   /api/deleteUser/123
```

**Resource Naming:**
- Use plural nouns for collections
- Use lowercase with hyphens
- Be consistent across API
- Avoid deep nesting (> 2 levels)

### 2. HTTP Methods

**Semantic Usage:**
- **GET:** Retrieve resource(s) - idempotent, safe
- **POST:** Create resource - not idempotent
- **PUT:** Replace resource - idempotent
- **PATCH:** Partial update - idempotent
- **DELETE:** Remove resource - idempotent

**Example:**
```http
GET    /api/users          # List users
GET    /api/users/123      # Get user 123
POST   /api/users          # Create user
PUT    /api/users/123      # Replace user 123
PATCH  /api/users/123      # Update user 123
DELETE /api/users/123      # Delete user 123
```

### 3. Stateless Communication

**Each request must contain all information:**
- No server-side session storage
- Authentication in every request
- Client maintains state
- Server processes independently

### 4. Uniform Interface

**Standard HTTP:**
- Status codes for responses
- Standard headers
- Consistent data formats
- Clear resource identification

## URL Design Best Practices

### Resource Hierarchy

**Good Hierarchy:**
```http
/api/users
/api/users/123
/api/users/123/posts
/api/users/123/posts/456
/api/users/123/posts/456/comments
```

**Avoid Deep Nesting:**
```http
# Bad: Too deep
/api/users/123/posts/456/comments/789/reactions/10

# Better: Flatten when possible
/api/comments/789/reactions/10
```

### Query Parameters

**Use for filtering, sorting, pagination:**
```http
GET /api/users?role=admin&status=active
GET /api/users?sort=name&order=asc
GET /api/users?page=1&limit=20
GET /api/users?search=john&filter=active
```

### Common Patterns

**Pagination:**
```http
GET /api/users?page=1&limit=20
GET /api/users?offset=0&limit=20
GET /api/users?cursor=abc123
```

**Filtering:**
```http
GET /api/users?status=active
GET /api/users?role=admin&department=engineering
GET /api/users?created_after=2026-01-01
```

**Sorting:**
```http
GET /api/users?sort=name
GET /api/users?sort=-created_at  # Descending
GET /api/users?sort=name,created_at
```

## HTTP Status Codes

### Success Codes (2xx)

**200 OK:**
- Successful GET, PUT, PATCH
- Request succeeded

**201 Created:**
- Successful POST creating resource
- Include Location header

**204 No Content:**
- Successful DELETE
- No response body needed

### Client Error Codes (4xx)

**400 Bad Request:**
- Malformed request
- Invalid parameters
- Validation errors

**401 Unauthorized:**
- Missing or invalid authentication
- Not authenticated

**403 Forbidden:**
- Authenticated but not authorized
- Permission denied

**404 Not Found:**
- Resource doesn't exist
- Invalid URL

**409 Conflict:**
- Resource conflict
- Duplicate creation

**422 Unprocessable Entity:**
- Valid syntax but semantic errors
- Business rule violations

### Server Error Codes (5xx)

**500 Internal Server Error:**
- Unexpected server error
- Generic server failure

**502 Bad Gateway:**
- Upstream server error
- Gateway/proxy issue

**503 Service Unavailable:**
- Service temporarily down
- Overloaded

**504 Gateway Timeout:**
- Upstream timeout
- Gateway timeout

## Request and Response Format

### Content Types

**Standard Types:**
```http
Content-Type: application/json
Accept: application/json
```

**Versioning:**
```http
Accept: application/vnd.api+json;version=1
Content-Type: application/vnd.api+json;version=1
```

### Request Body

**POST Example:**
```json
POST /api/users
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "role": "user"
}
```

**PATCH Example:**
```json
PATCH /api/users/123
Content-Type: application/json

{
  "name": "Jane Doe"
}
```

### Response Body

**Success Response:**
```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "user",
  "created_at": "2026-01-15T10:30:00Z"
}
```

**List Response:**
```json
{
  "data": [
    {"id": 1, "name": "User 1"},
    {"id": 2, "name": "User 2"}
  ],
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 20
  }
}
```

**Error Response:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

## API Versioning

### URL Versioning

**Path-based:**
```http
GET /api/v1/users
GET /api/v2/users
```

**Benefits:**
- Clear and explicit
- Easy to understand
- Supports multiple versions

### Header Versioning

**Accept Header:**
```http
GET /api/users
Accept: application/vnd.api+json;version=2
```

**Custom Header:**
```http
GET /api/users
API-Version: 2
```

### Query Parameter Versioning

```http
GET /api/users?version=2
```

**Not Recommended:**
- Less RESTful
- Easy to forget
- Harder to maintain

## Documentation

### OpenAPI/Swagger

**Define API contract:**
```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
```

**Generate Documentation:**
- Interactive docs (Swagger UI)
- Code generation
- Testing tools
- Mock servers

## Security Best Practices

### Authentication

**Bearer Token:**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**API Key:**
```http
X-API-Key: abc123def456
```

### HTTPS Only

- Always use HTTPS
- Never send credentials over HTTP
- Redirect HTTP to HTTPS

### Rate Limiting

**Headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642233600
```

### Input Validation

- Validate all inputs
- Sanitize user data
- Prevent injection attacks
- Use parameterized queries

## Pagination Patterns

### Offset-Based

```json
GET /api/users?page=1&limit=20

Response:
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### Cursor-Based

```json
GET /api/users?cursor=abc123&limit=20

Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "def456",
    "has_more": true
  }
}
```

**Benefits:**
- Consistent results
- Better for large datasets
- Avoids offset issues

## Error Handling

### Consistent Error Format

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User not found",
    "details": {
      "resource": "user",
      "id": "123"
    },
    "request_id": "req-abc123",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Codes

**Use consistent error codes:**
- `VALIDATION_ERROR`
- `RESOURCE_NOT_FOUND`
- `UNAUTHORIZED`
- `FORBIDDEN`
- `RATE_LIMIT_EXCEEDED`
- `INTERNAL_ERROR`

## FastAPI Examples

### Basic RESTful API with FastAPI

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List

app = FastAPI(title="User API", version="1.0.0")

class User(BaseModel):
    id: int
    name: str
    email: str

class UserCreate(BaseModel):
    name: str
    email: str

# GET /users - List users
@app.get("/users", response_model=List[User])
async def list_users():
    return [
        User(id=1, name="John", email="john@example.com"),
        User(id=2, name="Jane", email="jane@example.com")
    ]

# GET /users/{user_id} - Get user
@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    if user_id == 1:
        return User(id=1, name="John", email="john@example.com")
    raise HTTPException(status_code=404, detail="User not found")

# POST /users - Create user
@app.post("/users", response_model=User, status_code=201)
async def create_user(user: UserCreate):
    # Create user logic
    return User(id=3, name=user.name, email=user.email)

# PUT /users/{user_id} - Replace user
@app.put("/users/{user_id}", response_model=User)
async def replace_user(user_id: int, user: UserCreate):
    # Replace user logic
    return User(id=user_id, name=user.name, email=user.email)

# PATCH /users/{user_id} - Update user
@app.patch("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: UserCreate):
    # Partial update logic
    return User(id=user_id, name=user.name, email=user.email)

# DELETE /users/{user_id} - Delete user
@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int):
    # Delete user logic
    return None
```

### FastAPI with Query Parameters and Pagination

```python
from fastapi import Query
from typing import Optional

@app.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None
):
    """List users with pagination and search."""
    # Query logic with pagination
    users = await db.get_users(skip=skip, limit=limit, search=search)
    return {
        "items": users,
        "total": await db.count_users(search=search),
        "skip": skip,
        "limit": limit
    }
```

### FastAPI Error Handling

```python
from fastapi import HTTPException, status

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return user
```

### FastAPI with Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## Best Practices Summary

1. **Use RESTful principles:** Resources as nouns, HTTP methods correctly
2. **Follow HTTP semantics:** Correct status codes, idempotent operations
3. **Design clear URLs:** Resource-based, consistent, not too deep
4. **Version your API:** URL versioning recommended
5. **Document thoroughly:** OpenAPI/Swagger
6. **Handle errors consistently:** Standard error format
7. **Implement pagination:** For list endpoints
8. **Secure properly:** HTTPS, authentication, rate limiting
9. **Use appropriate status codes:** Follow HTTP standards
10. **Keep it stateless:** Each request independent

## Common Anti-Patterns

### Avoid These

**Action-Based URLs:**
```http
POST /api/getUser
POST /api/createUser
```

**Ignoring HTTP Methods:**
```http
POST /api/users/123/delete
```

**Inconsistent Naming:**
```http
GET /api/user
GET /api/users
GET /api/userList
```

**Returning 200 for Errors:**
```json
{
  "success": false,
  "error": "Not found"
}
```

**Too Much Nesting:**
```http
/api/v1/users/123/posts/456/comments/789/reactions/10
```

