# API Documentation Patterns

## Overview

API documentation provides clear, comprehensive information about how to use an API. Good API documentation enables developers to integrate quickly and correctly.

## Documentation Components

### Essential Sections

1. **Overview**: What the API does
2. **Authentication**: How to authenticate
3. **Endpoints**: Available endpoints
4. **Request/Response**: Data formats
5. **Examples**: Working examples
6. **Error Handling**: Error responses
7. **Rate Limiting**: Usage limits
8. **SDKs/Code Samples**: Client libraries

## API Documentation Standards

### Endpoint Documentation

**Required Information:**
- HTTP method (GET, POST, PUT, DELETE)
- Endpoint URL
- Description
- Authentication requirements
- Parameters (query, path, body)
- Request body schema
- Response schema
- Status codes
- Error responses
- Example requests/responses

### Example Format

```markdown
## Get User by ID

**GET** `/api/v1/users/{id}`

Returns user information by ID.

### Authentication
Requires Bearer token in Authorization header.

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | integer | Yes | User ID |

### Response
**200 OK**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**404 Not Found**
```json
{
  "error": "User not found",
  "code": "USER_NOT_FOUND"
}
```

### Example Request
```bash
curl -X GET \
  https://api.example.com/v1/users/1 \
  -H 'Authorization: Bearer YOUR_TOKEN'
```
```

## OpenAPI/Swagger

### OpenAPI Specification

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
  description: API for managing users

paths:
  /users/{id}:
    get:
      summary: Get user by ID
      operationId: getUserById
      tags:
        - Users
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
```

## Documentation Best Practices

### Clarity
- Use clear, concise language
- Avoid jargon when possible
- Define technical terms
- Use examples liberally

### Completeness
- Document all endpoints
- Include all parameters
- Show all response codes
- Provide error examples

### Accuracy
- Keep docs synchronized with code
- Test all examples
- Verify response schemas
- Update when API changes

### Usability
- Organize logically
- Use consistent format
- Provide quick start guide
- Include common use cases

## Interactive Documentation

### Swagger UI
- Interactive API explorer
- Try-it-out functionality
- Schema validation
- Authentication support

### Redoc
- Clean, readable documentation
- Code examples
- Search functionality
- Customizable styling

### Postman Collections
- Import/export capabilities
- Example requests
- Environment variables
- Automated testing

## Code Examples

### Multiple Languages
- Provide examples in multiple languages
- Use popular client libraries
- Show common use cases
- Include error handling

### Example Quality
```python
# Good: Complete example with error handling
import requests

url = "https://api.example.com/v1/users/1"
headers = {"Authorization": "Bearer YOUR_TOKEN"}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    user = response.json()
    print(f"User: {user['name']}")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("User not found")
    else:
        print(f"Error: {e}")
```

```python
# Bad: Incomplete example
requests.get("https://api.example.com/v1/users/1")
```

## API Versioning Documentation

### Version Indicators
- URL versioning: `/api/v1/`, `/api/v2/`
- Header versioning: `Accept: application/vnd.api.v1+json`
- Query parameter: `?version=1`

### Version Documentation
- Document version differences
- Migration guides
- Deprecation notices
- Sunset dates

## Best Practices Summary

1. **Use Standards**: OpenAPI/Swagger
2. **Be Consistent**: Same format throughout
3. **Provide Examples**: Multiple languages
4. **Keep Updated**: Sync with code
5. **Test Examples**: Verify they work
6. **Organize Well**: Logical structure
7. **Make Interactive**: Try-it-out features
