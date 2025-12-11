# Secure Coding Practices

## General Principles

### Defense in Depth
Implement multiple layers of security controls. Never rely on a single security mechanism.

### Principle of Least Privilege
Grant only the minimum permissions necessary for a function to operate. Users, processes, and systems should operate with the least privilege required.

### Fail Securely
When a security control fails, the system should fail in a secure state (deny access rather than grant it).

### Secure by Default
Systems should be secure by default. Security should not require additional configuration.

### Separation of Duties
Critical operations should require multiple people or systems to complete.

## Input Validation

### Always Validate Input
- Validate all input at the boundary (where it enters the system)
- Use whitelist validation (allow only known good values) rather than blacklist
- Validate data type, length, format, and range
- Reject invalid input rather than sanitizing it

### Common Validation Rules
```python
# Good: Whitelist validation
ALLOWED_CHARS = set('abcdefghijklmnopqrstuvwxyz0123456789-')
if not all(c in ALLOWED_CHARS for c in username):
    raise ValidationError("Invalid characters")

# Bad: Blacklist validation
if '<' in username or '>' in username:
    username = username.replace('<', '').replace('>', '')
```

### Input Validation Checklist
- [ ] Validate data type (string, integer, etc.)
- [ ] Validate length (min/max)
- [ ] Validate format (regex, pattern matching)
- [ ] Validate range (numeric bounds)
- [ ] Validate business rules
- [ ] Validate against known malicious patterns

## Output Encoding

### Always Encode Output
- Encode data when outputting to prevent injection attacks
- Use context-appropriate encoding (HTML, URL, JavaScript, SQL)
- Never trust data from untrusted sources

### Encoding Contexts
- **HTML Context**: Use HTML entity encoding (`&lt;`, `&gt;`, `&amp;`)
- **JavaScript Context**: Use Unicode escaping (`\u003C`)
- **URL Context**: Use URL encoding (`%3C`)
- **SQL Context**: Use parameterized queries (not encoding)

## Authentication and Session Management

### Password Security
- Require strong passwords (length, complexity)
- Hash passwords using strong algorithms (bcrypt, Argon2, PBKDF2)
- Never store passwords in plain text
- Implement password history to prevent reuse
- Use secure password reset mechanisms

### Session Management
- Generate strong, random session IDs
- Use secure, HttpOnly cookies for session storage
- Set appropriate session timeout
- Invalidate sessions on logout
- Regenerate session ID after login
- Use HTTPS for all session-related traffic

### Multi-Factor Authentication
- Implement MFA for sensitive operations
- Use time-based one-time passwords (TOTP)
- Support hardware security keys (FIDO2/WebAuthn)

## Access Control

### Implement Proper Authorization
- Check authorization on every request
- Use role-based access control (RBAC) or attribute-based access control (ABAC)
- Enforce access control at the application level, not just UI
- Use deny-by-default policies

### Common Mistakes
- Relying on client-side checks only
- Using predictable resource identifiers
- Not checking ownership of resources
- Elevating privileges unnecessarily

## Cryptography

### Use Strong Cryptography
- Use well-vetted cryptographic libraries
- Use appropriate key sizes (AES-256, RSA-2048+)
- Never implement custom cryptography
- Use cryptographically secure random number generators
- Rotate keys regularly

### Key Management
- Store keys securely (HSM, key management services)
- Never hardcode keys in source code
- Use environment variables or secure key stores
- Implement key rotation procedures
- Separate encryption keys from data

## Error Handling

### Secure Error Messages
- Never expose sensitive information in error messages
- Don't reveal system internals (stack traces, file paths)
- Log detailed errors server-side
- Return generic messages to users
- Use consistent error handling across the application

### Error Handling Best Practices
```python
# Good: Generic error message
try:
    user = get_user(user_id)
except UserNotFound:
    logger.error(f"User lookup failed for ID: {user_id}")
    raise HTTPException(status_code=404, detail="User not found")

# Bad: Exposing internal details
try:
    user = get_user(user_id)
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # Exposes stack trace
```

## Logging and Monitoring

### Security Logging
- Log all authentication attempts (success and failure)
- Log all authorization failures
- Log all input validation failures
- Log all security-relevant events
- Include sufficient context (user, IP, timestamp, action)

### Log Protection
- Protect logs from tampering
- Use centralized logging
- Implement log rotation and retention policies
- Monitor logs for suspicious activity
- Alert on security events

## Dependency Management

### Secure Dependencies
- Keep all dependencies up to date
- Monitor for known vulnerabilities (npm audit, pip-audit, etc.)
- Use dependency pinning
- Remove unused dependencies
- Use only trusted sources for packages

### Dependency Scanning
- Automate vulnerability scanning in CI/CD
- Set up alerts for new vulnerabilities
- Review and update dependencies regularly
- Use tools like Snyk, Dependabot, or OWASP Dependency-Check

## Secure Configuration

### Configuration Security
- Use secure default configurations
- Remove or disable unnecessary features
- Use environment-specific configurations
- Never commit secrets to version control
- Use configuration management tools

### Secrets Management
- Never hardcode secrets
- Use secret management services (AWS Secrets Manager, HashiCorp Vault)
- Rotate secrets regularly
- Use different secrets for different environments
- Implement secret scanning in CI/CD

## API Security

### API Best Practices
- Use authentication for all API endpoints
- Implement rate limiting
- Validate all API input
- Use HTTPS for all API communication
- Implement proper CORS policies
- Version APIs appropriately
- Document security requirements

### API Authentication
- Use OAuth 2.0 or JWT for API authentication
- Implement token expiration and refresh
- Validate tokens on every request
- Use secure token storage

## References

- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

