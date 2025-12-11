# API Security Patterns

## Overview

API security protects APIs from unauthorized access, data breaches, and attacks. It involves authentication, authorization, encryption, input validation, and threat protection.

## Authentication Patterns

### 1. API Keys

**Simple but Limited:**
```python
API_KEY_HEADER = 'X-API-Key'

def authenticate_api_key(request):
    api_key = request.headers.get(API_KEY_HEADER)
    if not api_key:
        return None
    
    key_record = db.get_api_key(api_key)
    if not key_record or not key_record.is_active:
        return None
    
    return key_record.user
```

**Best Practices:**
- Store hashed keys
- Rotate regularly
- Scope permissions
- Rate limit per key

### 2. OAuth 2.0

**Authorization Code Flow:**
```
Client → Authorization Server → User Consent → Authorization Code
Client → Exchange Code → Access Token
Client → API (with Access Token)
```

**Implementation:**
```python
from authlib.integrations.flask_client import OAuth

oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/login')
def login():
    return oauth.google.authorize_redirect(redirect_uri=url_for('callback', _external=True))

@app.route('/callback')
def callback():
    token = oauth.google.authorize_access_token()
    user_info = token['userinfo']
    return user_info
```

### 3. JWT (JSON Web Tokens)

**Token Structure:**
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user123",
    "exp": 1642233600,
    "iat": 1642147200,
    "roles": ["user", "admin"]
  },
  "signature": "..."
}
```

**Generate Token:**
```python
import jwt
from datetime import datetime, timedelta

def generate_token(user):
    payload = {
        'sub': user.id,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'roles': user.roles
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
```

**Validate Token:**
```python
def validate_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token
```

### 4. mTLS (Mutual TLS)

**Both client and server authenticate:**
```python
import ssl

# Server
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain('server.crt', 'server.key')
context.load_verify_locations('ca.crt')
context.verify_mode = ssl.CERT_REQUIRED

# Client
context = ssl.create_default_context()
context.load_cert_chain('client.crt', 'client.key')
context.load_verify_locations('ca.crt')
```

## Authorization Patterns

### 1. Role-Based Access Control (RBAC)

**Roles and Permissions:**
```python
ROLES = {
    'admin': ['read', 'write', 'delete', 'manage_users'],
    'user': ['read', 'write'],
    'guest': ['read']
}

def check_permission(user, permission):
    user_roles = user.roles
    for role in user_roles:
        if permission in ROLES.get(role, []):
            return True
    return False

@app.route('/api/users/<user_id>')
@require_permission('read')
def get_user(user_id):
    return get_user_by_id(user_id)
```

### 2. Attribute-Based Access Control (ABAC)

**Fine-grained permissions:**
```python
def can_access_resource(user, resource, action):
    # Check attributes
    if action == 'read' and resource.owner_id == user.id:
        return True
    if action == 'delete' and user.role == 'admin':
        return True
    if resource.is_public and action == 'read':
        return True
    return False
```

## Input Validation

### Schema Validation

**Validate request data:**
```python
from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    age = fields.Int(validate=validate.Range(min=0, max=150))

@app.route('/api/users', methods=['POST'])
def create_user():
    schema = UserSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    user = create_user(data)
    return jsonify(user), 201
```

### SQL Injection Prevention

**Use parameterized queries:**
```python
# Bad: SQL injection risk
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good: Parameterized
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

### XSS Prevention

**Sanitize output:**
```python
from markupsafe import escape

@app.route('/api/users/<user_id>')
def get_user(user_id):
    user = get_user_by_id(user_id)
    # Escape user input in response
    return jsonify({
        'name': escape(user.name),
        'bio': escape(user.bio)
    })
```

## Encryption

### HTTPS/TLS

**Always use HTTPS:**
```python
# Force HTTPS redirect
@app.before_request
def force_https():
    if request.headers.get('X-Forwarded-Proto') == 'http':
        return redirect(request.url.replace('http://', 'https://'), code=301)
```

### Data Encryption at Rest

**Encrypt sensitive data:**
```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

def encrypt_field(value):
    return cipher.encrypt(value.encode()).decode()

def decrypt_field(encrypted_value):
    return cipher.decrypt(encrypted_value.encode()).decode()
```

## Security Headers

### Common Security Headers

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

## Rate Limiting

**Protect from abuse:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/users')
@limiter.limit("10 per minute")
def get_users():
    return jsonify(users=[...])
```

## Best Practices

1. **Use HTTPS:** Always encrypt in transit
2. **Authenticate all requests:** No anonymous access
3. **Authorize properly:** Check permissions
4. **Validate input:** Sanitize all inputs
5. **Use parameterized queries:** Prevent SQL injection
6. **Set security headers:** X-Frame-Options, CSP, etc.
7. **Rate limit:** Prevent abuse
8. **Log security events:** Audit authentication/authorization
9. **Rotate secrets:** Regularly rotate keys and tokens
10. **Keep dependencies updated:** Patch vulnerabilities

