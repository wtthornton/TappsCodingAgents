# Enhancer Agent Expert Information Integration - Examples

This document provides before/after examples showing how the enhanced Enhancer Agent now prominently features all expert information.

## Example 1: Domain-Specific Enhancement

### Input Prompt
```
Create a healthcare patient management system
```

### Before Enhancement (Basic Output)
```markdown
# Enhanced Prompt: Create a healthcare patient management system

## Requirements
### Functional Requirements
1. Patient registration
2. Medical records management
3. Appointment scheduling

## Architecture Guidance
Use REST API with database backend
```

### After Enhancement (With Expert Information) ✅
```markdown
# Enhanced Prompt: Create a healthcare patient management system

## Analysis
- **Intent**: feature
- **Scope**: large
- **Workflow Type**: greenfield
- **Detected Domains**: healthcare, patient-management, compliance
- **Detected Libraries**: FastAPI, PostgreSQL, Redis

## Requirements

### Functional Requirements
1. Patient registration with demographic information
2. Medical records management with versioning
3. Appointment scheduling with calendar integration
4. Prescription management
5. Billing and insurance integration

### Domain Context (from Industry Experts)

#### Healthcare Domain
**Confidence**: 94.2%
**Agreement**: 91.5%
**Primary Expert**: healthcare-compliance-expert
**Total Experts Consulted**: 4

**Weighted Consensus Answer**:
For healthcare patient management systems, critical requirements include:
- HIPAA compliance: All patient data must be encrypted at rest and in transit
- Audit logging: Complete audit trail of all PHI access (who, what, when)
- Access controls: Role-based access with minimum necessary principle
- Data retention: Follow state and federal retention requirements
- Breach notification: Automated breach detection and notification procedures
- Business Associate Agreements: Required for all third-party integrations

**Individual Expert Responses**:
1. **healthcare-compliance-expert** (confidence: 96.0%):
   HIPAA compliance is non-negotiable. Implement encryption, audit logging, and role-based access controls. All PHI access must be logged with timestamp, user, and action.
2. **healthcare-security-expert** (confidence: 93.0%):
   Use end-to-end encryption, implement MFA for all users, regular security audits, and penetration testing. Follow NIST cybersecurity framework.
3. **healthcare-data-expert** (confidence: 92.0%):
   Implement data minimization - only collect necessary PHI. Use pseudonymization where possible. Ensure data portability for patient requests.
4. **healthcare-integration-expert** (confidence: 91.0%):
   Use HL7 FHIR for interoperability. Implement proper API authentication. Ensure all integrations have BAAs in place.

### Library Best Practices (from Context7)

#### FastAPI
**Source**: Context7 KB Cache
**Best Practices Preview**:
```python
# Use dependency injection for role-based access
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def require_hipaa_compliance(
    token: str = Depends(security),
    user_role: str = Depends(get_user_role)
):
    # Verify user has access to PHI
    if not can_access_phi(user_role):
        raise HTTPException(403, "Access denied")
    # Log PHI access
    audit_log(user_id=token.user_id, action="PHI_ACCESS")
```

#### PostgreSQL
**Source**: Context7 KB Cache
**Best Practices Preview**:
- Use row-level security for PHI data
- Enable encryption at rest
- Implement database-level audit triggers
- Use prepared statements to prevent SQL injection

### API Compatibility Status
- ✅ **FastAPI**: Docs=true, Best Practices=true
- ✅ **PostgreSQL**: Docs=true, Best Practices=true
- ✅ **Redis**: Docs=true, Best Practices=true

## Architecture Guidance

### System Design
- **Architecture Pattern**: Microservices with API gateway
- **Database**: PostgreSQL with encryption at rest
- **Caching**: Redis for session management (no PHI in cache)
- **Message Queue**: RabbitMQ for async processing

### Library-Specific Architecture Patterns (from Context7)

#### FastAPI
**Recommended Patterns**:
- **Dependency Injection Pattern**: Use for authentication and authorization
- **Middleware Pattern**: Request logging and audit trail
- **Error Handling Pattern**: Structured error responses with logging

#### PostgreSQL
**Recommended Patterns**:
- **Row-Level Security**: Implement RLS policies for PHI access
- **Audit Trigger Pattern**: Database triggers for audit logging
- **Encryption Pattern**: Encrypt sensitive columns at database level

### Integration Examples (from Context7)

#### FastAPI + PostgreSQL
1. **HIPAA-Compliant API**: FastAPI endpoints with audit logging and encryption
2. **Row-Level Security Integration**: FastAPI dependencies that enforce RLS policies
3. **Audit Trail Pattern**: Automatic audit logging for all PHI access

## Quality Standards
- **Security Score**: ≥ 9.0 (critical for healthcare)
- **Compliance**: HIPAA, HITECH Act
- **Audit Logging**: Required for all PHI access
- **Encryption**: AES-256 for data at rest, TLS 1.3 for data in transit

## Implementation Strategy
Step 1: Set up HIPAA-compliant infrastructure (encryption, audit logging)
Step 2: Implement role-based access control with FastAPI dependencies
Step 3: Create patient data models with encryption
Step 4: Implement audit logging for all PHI access
Step 5: Add HL7 FHIR integration for interoperability
```

## Example 2: Library-Specific Enhancement

### Input Prompt
```
Add FastAPI authentication with JWT tokens
```

### Before Enhancement (Basic Output)
```markdown
# Enhanced Prompt: Add FastAPI authentication with JWT tokens

## Requirements
1. Implement JWT authentication
2. Add login endpoint
3. Protect routes with authentication

## Architecture Guidance
Use FastAPI with JWT library
```

### After Enhancement (With Expert Information) ✅
```markdown
# Enhanced Prompt: Add FastAPI authentication with JWT tokens

## Analysis
- **Intent**: feature
- **Scope**: medium
- **Workflow Type**: brownfield
- **Detected Domains**: security, authentication
- **Detected Libraries**: FastAPI, JWT, python-jose, passlib

## Requirements

### Functional Requirements
1. User login with email/password
2. JWT token generation (access + refresh tokens)
3. Token validation middleware
4. Protected route decorator
5. Token refresh endpoint
6. Logout with token blacklisting

### Domain Context (from Industry Experts)

#### Security Domain
**Confidence**: 89.5%
**Agreement**: 85.2%
**Primary Expert**: authentication-expert
**Total Experts Consulted**: 3

**Weighted Consensus Answer**:
For JWT authentication in FastAPI:
- Use separate access (15 min) and refresh (7 days) tokens
- Implement token rotation for refresh tokens
- Use secure HTTP-only cookies for refresh tokens
- Implement rate limiting on login endpoints
- Add account lockout after failed attempts
- Use HS256 or RS256 algorithms (avoid none)

**Individual Expert Responses**:
1. **authentication-expert** (confidence: 92.0%):
   Implement token rotation, use secure cookies, add rate limiting. Use RS256 for better security.
2. **security-expert** (confidence: 90.0%):
   Short-lived access tokens, implement token blacklist for logout, use HTTPS only.
3. **api-security-expert** (confidence: 87.0%):
   Add CORS configuration, implement CSRF protection, validate token signature and expiration.

### Library Best Practices (from Context7)

#### FastAPI
**Source**: Context7 KB Cache
**Best Practices Preview**:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
```

#### JWT (python-jose)
**Source**: Context7 KB Cache
**Best Practices Preview**:
- Use `python-jose` library for JWT operations
- Set appropriate expiration times (15 min access, 7 days refresh)
- Include user ID, email, and roles in token payload
- Always validate token signature and expiration
- Use environment variables for secret keys

### API Compatibility Status
- ✅ **FastAPI**: Docs=true, Best Practices=true
- ✅ **JWT**: Docs=true, Best Practices=true
- ✅ **python-jose**: Docs=true, Best Practices=true
- ✅ **passlib**: Docs=true, Best Practices=true

## Architecture Guidance

### System Design
- **Authentication Flow**: JWT with access/refresh token pattern
- **Token Storage**: Access tokens in memory, refresh tokens in HTTP-only cookies
- **Token Validation**: FastAPI dependency injection
- **Rate Limiting**: Redis-based rate limiting on login endpoints

### Library-Specific Architecture Patterns (from Context7)

#### FastAPI
**Recommended Patterns**:
- **Dependency Injection Pattern**: Use `Depends()` for authentication
- **Security Scheme Pattern**: Use `HTTPBearer` for token extraction
- **Route Protection Pattern**: Apply authentication dependency to protected routes

#### JWT
**Recommended Patterns**:
- **Token Refresh Pattern**: Separate access and refresh tokens
- **Token Rotation Pattern**: Rotate refresh tokens on use
- **Blacklist Pattern**: Maintain token blacklist in Redis for logout

### Integration Examples (from Context7)

#### FastAPI + JWT
1. **JWT Authentication Dependency**: FastAPI dependency for token validation
2. **Token Refresh Endpoint**: Endpoint to refresh expired access tokens
3. **Protected Route Example**: Example of protecting routes with JWT authentication
4. **Token Blacklist Middleware**: Middleware to check token blacklist

## Quality Standards
- **Security Score**: ≥ 8.5
- **Token Security**: HS256 or RS256 algorithms
- **Rate Limiting**: 5 requests per minute on login
- **Token Expiration**: 15 minutes for access, 7 days for refresh

## Implementation Strategy
Step 1: Install dependencies (python-jose, passlib, python-multipart)
Step 2: Create JWT utility functions (generate, validate, decode)
Step 3: Implement FastAPI authentication dependency
Step 4: Create login endpoint with rate limiting
Step 5: Add token refresh endpoint
Step 6: Implement protected route examples
Step 7: Add token blacklist for logout
```

## Key Improvements Demonstrated

### 1. Expert Information Prominence
- **Before**: Basic expert mention
- **After**: Full expert consultation section with confidence metrics, all experts consulted, and individual responses

### 2. Library Best Practices Integration
- **Before**: Generic library mention
- **After**: Specific best practices from Context7 with code examples

### 3. Architecture Patterns
- **Before**: Generic architecture guidance
- **After**: Library-specific patterns and integration examples from Context7

### 4. Actionable Requirements
- **Before**: Generic requirements
- **After**: Expert insights converted into specific, actionable requirements

### 5. Full Transparency
- **Before**: Single expert answer
- **After**: All experts consulted, individual responses, confidence metrics, and agreement levels

## Usage

To use the enhanced enhancer with full expert information:

```bash
# In Cursor chat
@enhancer *enhance "Your prompt here"

# Or via CLI
tapps-agents enhancer enhance "Your prompt here" --format markdown
```

The enhanced output will automatically include:
- All expert consultations with full transparency
- Library best practices from Context7
- Architecture patterns and integration examples
- API compatibility status
- Actionable requirements based on expert insights
