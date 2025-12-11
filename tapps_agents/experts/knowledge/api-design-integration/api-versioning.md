# API Versioning Strategies

## Overview

API versioning is essential for managing changes to APIs while maintaining backward compatibility. Different versioning strategies have trade-offs in clarity, maintenance, and flexibility.

## Versioning Strategies

### 1. URL Path Versioning

**Format:** `/api/v{version}/resource`

**Example:**
```http
GET /api/v1/users
GET /api/v2/users
POST /api/v1/orders
```

**Pros:**
- Explicit and clear
- Easy to understand
- Supports multiple versions simultaneously
- RESTful and cacheable

**Cons:**
- Clutters URL space
- Requires route management
- Can confuse users about which version to use

**Implementation:**
```python
from flask import Flask

app = Flask(__name__)

@app.route('/api/v1/users')
def v1_users():
    return {"version": "v1", "users": [...]}

@app.route('/api/v2/users')
def v2_users():
    return {"version": "v2", "users": [...]}  # New format
```

### 2. Header Versioning

**Format:** Custom header or Accept header

**Example:**
```http
GET /api/users
API-Version: 2

GET /api/users
Accept: application/vnd.api+json;version=2
```

**Pros:**
- Clean URLs
- HTTP-compliant
- Content negotiation

**Cons:**
- Less discoverable
- Harder to test
- Clients must remember to set headers

**Implementation:**
```python
from flask import request

def get_api_version():
    # Check custom header
    version = request.headers.get('API-Version', '1')
    
    # Or check Accept header
    accept = request.headers.get('Accept', '')
    if 'version=' in accept:
        version = extract_version_from_accept(accept)
    
    return version

@app.route('/api/users')
def users():
    version = get_api_version()
    if version == '2':
        return new_format_users()
    return legacy_format_users()
```

### 3. Query Parameter Versioning

**Format:** `?version={version}` or `?v={version}`

**Example:**
```http
GET /api/users?version=2
GET /api/users?v=2
```

**Pros:**
- Simple to implement
- Easy to test
- Backward compatible

**Cons:**
- Less RESTful
- Easy to forget
- Not semantic
- Doesn't work well for POST/PUT

**Implementation:**
```python
@app.route('/api/users')
def users():
    version = request.args.get('version', '1')
    if version == '2':
        return new_format_users()
    return legacy_format_users()
```

### 4. Domain/Subdomain Versioning

**Format:** `v{version}.api.example.com`

**Example:**
```http
GET https://v1.api.example.com/users
GET https://v2.api.example.com/users
```

**Pros:**
- Clear separation
- Easy deployment per version
- Good for major versions

**Cons:**
- DNS management overhead
- SSL certificate complexity
- Less flexible

## Version Numbering

### Semantic Versioning

**Format:** `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes
- **MINOR:** New features, backward compatible
- **PATCH:** Bug fixes, backward compatible

**Example:**
```
v1.0.0 → v1.1.0 (new feature)
v1.1.0 → v1.1.1 (bug fix)
v1.1.1 → v2.0.0 (breaking change)
```

### API Versioning

**Common Approaches:**
- **Major only:** `v1`, `v2` (simpler)
- **Major.Minor:** `v1.0`, `v1.1` (more granular)
- **Date-based:** `2026-01-15` (YAML style)

## Breaking vs Non-Breaking Changes

### Breaking Changes (New Major Version)

**Require New Version:**
- Removing fields
- Changing field types
- Removing endpoints
- Changing required fields
- Changing authentication
- Changing URL structure

**Example:**
```json
// v1
{
  "id": 123,
  "name": "John"
}

// v2 - Breaking: Changed field name
{
  "id": 123,
  "fullName": "John"  // Was "name" in v1
}
```

### Non-Breaking Changes (Same Version)

**Safe to Make:**
- Adding new fields
- Adding new endpoints
- Making optional fields required (with migration)
- Adding query parameters
- Improving error messages

**Example:**
```json
// v1
{
  "id": 123,
  "name": "John"
}

// v1 (updated) - Non-breaking: Added field
{
  "id": 123,
  "name": "John",
  "email": "john@example.com"  // New field
}
```

## Implementation Patterns

### Version Detection

**Middleware:**
```python
from flask import request, g

@app.before_request
def detect_version():
    # Check multiple sources
    version = (
        request.args.get('version') or
        request.headers.get('API-Version') or
        request.headers.get('X-API-Version') or
        extract_from_accept_header() or
        '1'  # Default
    )
    g.api_version = version
```

### Version Routing

**Route Decorator:**
```python
def version_route(rule, **options):
    def decorator(f):
        @app.route(f'/api/v1{rule}', endpoint=f'v1_{f.__name__}', **options)
        def v1_handler():
            return f(version='1')
        
        @app.route(f'/api/v2{rule}', endpoint=f'v2_{f.__name__}', **options)
        def v2_handler():
            return f(version='2')
        
        return f
    return decorator

@version_route('/users')
def users(version):
    if version == '2':
        return new_format()
    return legacy_format()
```

### Version-Specific Handlers

**Separate Modules:**
```python
# api/v1/handlers.py
def get_users_v1():
    return {"users": [...]}  # Old format

# api/v2/handlers.py
def get_users_v2():
    return {"data": [...]}  # New format

# api/routes.py
from api.v1 import handlers as v1_handlers
from api.v2 import handlers as v2_handlers

app.register_blueprint(v1_handlers.bp, url_prefix='/api/v1')
app.register_blueprint(v2_handlers.bp, url_prefix='/api/v2')
```

## Deprecation Strategy

### Deprecation Process

**Steps:**
1. Announce deprecation
2. Set deprecation date
3. Add deprecation headers
4. Provide migration guide
5. Monitor usage
6. Sunset after grace period

**Deprecation Headers:**
```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: <https://api.example.com/docs/v2>; rel="successor-version"
Warning: 299 - "API v1 is deprecated, migrate to v2"
```

**Implementation:**
```python
@app.route('/api/v1/users')
def users_v1():
    response = jsonify(legacy_users())
    response.headers['Deprecation'] = 'true'
    response.headers['Sunset'] = 'Sat, 01 Jan 2027 00:00:00 GMT'
    response.headers['Warning'] = '299 - "API v1 is deprecated"'
    return response
```

## Version Documentation

### Changelog

**Maintain Changelog:**
```markdown
# API Changelog

## v2.0.0 (2026-01-15)
### Breaking Changes
- Removed `name` field, use `fullName`
- Changed `GET /users` response format

### New Features
- Added pagination to all list endpoints
- Added filtering by `status`

## v1.2.0 (2025-12-01)
### New Features
- Added `email` field to User
- Added `GET /users/:id/posts` endpoint
```

### Migration Guides

**Provide Clear Migration:**
```markdown
# Migrating from v1 to v2

## Response Format Changes

### v1 Response
```json
{
  "users": [...]
}
```

### v2 Response
```json
{
  "data": [...],
  "meta": {...}
}
```

## Field Name Changes
- `name` → `fullName`
- `created` → `createdAt`
```

## Best Practices

1. **Choose one strategy:** Be consistent
2. **Version major changes only:** Minor changes within version
3. **Document changes:** Clear changelogs and migration guides
4. **Deprecate gracefully:** Give clients time to migrate
5. **Monitor usage:** Track version adoption
6. **Sunset old versions:** Remove after deprecation period
7. **Default to latest:** When version not specified
8. **Test thoroughly:** Ensure backward compatibility
9. **Communicate clearly:** Announce changes early
10. **Support multiple versions:** During transition periods

## Common Patterns

### Default Version

**Use Latest:**
```python
def get_version():
    version = extract_version() or get_latest_version()
    return version
```

### Version Aliases

**Support "latest":**
```http
GET /api/latest/users  # Maps to v2
```

### Version Negotiation

**Content Negotiation:**
```http
GET /api/users
Accept: application/vnd.api+json;version=2

HTTP/1.1 200 OK
Content-Type: application/vnd.api+json;version=2
```

## Summary

Effective API versioning requires:

1. **Choose appropriate strategy:** URL path recommended for REST
2. **Version breaking changes:** Major version increments
3. **Maintain backward compatibility:** During transition
4. **Deprecate gracefully:** With clear timelines
5. **Document thoroughly:** Changelogs and migration guides
6. **Monitor adoption:** Track version usage
7. **Sunset old versions:** After deprecation period
8. **Test compatibility:** Ensure no regressions

