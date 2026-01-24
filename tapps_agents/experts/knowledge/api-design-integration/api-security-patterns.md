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

**Refresh-Token Flow:**

**Use Case:** Long-lived API access without user re-authentication

**Pattern:**
```
Client → Exchange refresh_token → Access Token
Client → API (with Access Token)
Client → Refresh before expiry → New Access Token
```

**Implementation:**
```python
import os
import time
from typing import Any

import requests


class OAuth2RefreshTokenClient:
    """
    OAuth2 client using refresh-token flow for long-lived API access.
    
    This pattern is used by many SaaS APIs (Zoho, Okta, Salesforce) that require
    long-term access without user re-authentication.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        token_url: str,
        api_base_url: str | None = None,
        timeout_s: int = 30,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.token_url = token_url
        self.api_base_url = api_base_url.rstrip("/") if api_base_url else None
        self.timeout_s = timeout_s
        
        self._access_token: str | None = None
        self._access_token_expiry_epoch: float = 0.0  # unix epoch seconds
    
    def _refresh_access_token(self) -> str:
        """
        Exchange refresh_token for access_token.
        
        Returns:
            The new access token string.
            
        Raises:
            RuntimeError: If the token response is missing access_token.
            requests.RequestException: If the token refresh request fails.
        """
        resp = requests.post(
            self.token_url,
            data={
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
            },
            timeout=self.timeout_s,
        )
        resp.raise_for_status()
        payload = resp.json()
        
        if "access_token" not in payload:
            raise RuntimeError("Token response missing access_token")
        
        access_token = payload["access_token"]
        
        # Some providers use expires_in_sec, others use expires_in (handle both)
        expires_in = payload.get("expires_in_sec", payload.get("expires_in", 3600))
        
        # Refresh proactively (e.g. 60 seconds before expiry) to avoid race conditions
        self._access_token_expiry_epoch = time.time() + int(expires_in) - 60
        self._access_token = access_token
        return access_token
    
    def _get_access_token(self) -> str:
        """
        Get valid access token, refreshing if necessary.
        
        Returns:
            Valid access token string.
        """
        if self._access_token and time.time() < self._access_token_expiry_epoch:
            return self._access_token
        return self._refresh_access_token()
    
    def _headers(self) -> dict[str, str]:
        """
        Get HTTP headers for authenticated requests.
        
        Returns:
            Dictionary with Authorization and Accept headers.
        """
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",  # Standard OAuth2 header
            "Accept": "application/json",
        }
    
    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Make authenticated GET request.
        
        Args:
            path: API endpoint path
            params: Optional query parameters
            
        Returns:
            JSON response as dictionary
        """
        if not self.api_base_url:
            raise ValueError("api_base_url not set")
        
        url = f"{self.api_base_url}/{path.lstrip('/')}"
        resp = requests.get(
            url,
            headers=self._headers(),
            params=params,
            timeout=self.timeout_s,
        )
        resp.raise_for_status()
        return resp.json()
```

**Best Practices:**
- **Refresh proactively:** Refresh tokens 60 seconds before expiry to avoid race conditions
- **Handle both expiry formats:** Some providers use `expires_in_sec`, others use `expires_in` (Zoho uses both)
- **Cache access tokens:** Store tokens until near expiry to reduce API calls
- **Secure storage:** Use environment variables or secret managers for refresh tokens (never hardcode)
- **Error handling:** Handle token refresh failures gracefully (retry, exponential backoff)
- **Multi-region support:** Some providers (e.g. Zoho) have different endpoints for EU/US regions

**Example Usage:**
```python
# Prefer environment variables for secrets
client = OAuth2RefreshTokenClient(
    client_id=os.environ["OAUTH_CLIENT_ID"],
    client_secret=os.environ["OAUTH_CLIENT_SECRET"],
    refresh_token=os.environ["OAUTH_REFRESH_TOKEN"],
    token_url="https://accounts.zoho.com/oauth/v2/token",
    api_base_url="https://www.site24x7.com/api",
)

# Token refresh happens automatically
status = client.get("/current_status")
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

### 5. Custom Authentication Headers

**Overview:** Some APIs use non-standard authentication headers instead of the standard `Authorization: Bearer <token>` format.

**Common Custom Headers:**
- `Authorization: Zoho-oauthtoken <token>` (Zoho/Site24x7)
- `Authorization: Bearer <token>` (standard OAuth2)
- `X-API-Key: <key>` (API key authentication)
- `Authorization: Token <token>` (GitHub-style)

**Implementation:**
```python
def _headers(self) -> dict[str, str]:
    """
    Get HTTP headers for authenticated requests.
    
    Supports custom auth header formats based on API requirements.
    """
    token = self._get_access_token()
    
    # Custom header format (e.g. Zoho/Site24x7)
    return {
        "Authorization": f"Zoho-oauthtoken {token}",  # Custom header format
        "Accept": "application/json",
    }

# Or standard OAuth2 format:
def _headers_standard(self) -> dict[str, str]:
    """Standard OAuth2 Bearer token format."""
    token = self._get_access_token()
    return {
        "Authorization": f"Bearer {token}",  # Standard OAuth2
        "Accept": "application/json",
    }
```

**Best Practices:**
- **Check API documentation:** Each API specifies its required header format
- **Support multiple formats:** Some clients need to support multiple APIs with different formats
- **Use configuration:** Make header format configurable rather than hardcoded
- **Document format:** Clearly document which header format your client uses

**Example: Multi-Format Support**
```python
class FlexibleOAuth2Client:
    """OAuth2 client that supports multiple auth header formats."""
    
    def __init__(self, auth_header_format: str = "Bearer"):
        """
        Args:
            auth_header_format: Header format - "Bearer", "Zoho-oauthtoken", "Token", etc.
        """
        self.auth_header_format = auth_header_format
    
    def _headers(self) -> dict[str, str]:
        token = self._get_access_token()
        return {
            "Authorization": f"{self.auth_header_format} {token}",
            "Accept": "application/json",
        }

# Usage:
zoho_client = FlexibleOAuth2Client(auth_header_format="Zoho-oauthtoken")
github_client = FlexibleOAuth2Client(auth_header_format="Token")
standard_client = FlexibleOAuth2Client(auth_header_format="Bearer")
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

