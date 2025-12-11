# Context7 Security & Privacy Guide

**TappsCodingAgents + Context7 Integration**

This guide covers security best practices, privacy considerations, and compliance for Context7 KB integration.

---

## Overview

Context7 integration is designed with **privacy-first architecture**:

- ✅ **Queries Stay Local**: Only library/topic names sent to Context7 API
- ✅ **No Code Sent**: Your code never leaves your machine
- ✅ **Encrypted API Keys**: Optional encryption for stored API keys
- ✅ **SOC 2 Compliance**: Security audit and compliance verification
- ✅ **Audit Logging**: Track all KB operations

---

## Privacy Architecture

### Privacy-First Design

Context7 queries are designed to be privacy-preserving:

1. **Only Topics Sent**: When looking up documentation, only the library name and topic are sent to Context7 API
2. **No Code Content**: Your actual code, file contents, or project details are never transmitted
3. **Local Caching**: All documentation is cached locally, reducing API calls
4. **Offline Operation**: Once cached, documentation works offline without API calls

### Example Query Flow

```
1. Skill requests: "Get FastAPI routing documentation"
2. System checks local KB cache
3. If cache miss: Send only "fastapi" + "routing" to Context7 API
4. Receive documentation (public, version-specific)
5. Cache locally for future use
6. Return to Skill
```

**What is NOT sent:**
- ❌ Your code
- ❌ File contents
- ❌ Project structure
- ❌ Personal information
- ❌ Any sensitive data

---

## API Key Management

### Environment Variables (Recommended)

Store API keys in environment variables:

```bash
# Linux/macOS
export CONTEXT7_API_KEY="your-api-key-here"

# Windows PowerShell
$env:CONTEXT7_API_KEY="your-api-key-here"

# Windows CMD
set CONTEXT7_API_KEY=your-api-key-here
```

### Encrypted Storage (Optional)

For enhanced security, use encrypted storage:

```python
from tapps_agents.context7.security import APIKeyManager

# Initialize key manager
key_manager = APIKeyManager()

# Store encrypted API key
key_manager.store_api_key("context7", "your-api-key-here", encrypt=True)

# Retrieve API key
api_key = key_manager.load_api_key("context7")
```

**Requirements:**
- Install `cryptography` package: `pip install cryptography`
- Master key stored in `.tapps-agents/.master-key` (restricted permissions)

### Security Best Practices

1. **Never Commit API Keys**
   - Add `.tapps-agents/api-keys.encrypted` to `.gitignore`
   - Add `.tapps-agents/.master-key` to `.gitignore`
   - Use environment variables in CI/CD

2. **File Permissions**
   - API key files should have 600 permissions (owner read/write only)
   - Master key file should have 600 permissions

3. **Key Rotation**
   - Rotate API keys periodically
   - Update keys in environment variables or encrypted storage

4. **Access Control**
   - Limit who has access to API keys
   - Use separate keys for development/production

---

## Security Audit

### Running Security Audit

```python
from tapps_agents.context7.security import SecurityAuditor

# Initialize auditor
auditor = SecurityAuditor()

# Run audit
result = auditor.audit()

# Check results
if result.passed:
    print("✅ Security audit passed")
else:
    print("❌ Security issues found:")
    for issue in result.issues:
        print(f"  - {issue}")
    
    print("\n⚠️  Warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")
    
    print("\n💡 Recommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")
```

### Audit Checks

The security auditor checks:

1. **API Key Storage**
   - Encryption availability
   - Environment variable usage
   - File permissions

2. **Cache Security**
   - Directory permissions
   - Sensitive data detection

3. **Compliance**
   - SOC 2 compliance status
   - Data retention compliance
   - Audit logging enabled

### CLI Command

```bash
# Run security audit
python -m tapps_agents.cli context7 security-audit
```

---

## SOC 2 Compliance

### Compliance Features

TappsCodingAgents Context7 integration includes:

1. **Data Retention**
   - Configurable cache retention (default: 30 days)
   - Automatic cleanup of stale entries

2. **Audit Logging**
   - All KB operations logged
   - Access tracking
   - Performance metrics

3. **Access Control**
   - File permission enforcement
   - Encrypted API key storage
   - Environment variable support

4. **Privacy Protection**
   - No code sent to external APIs
   - Only library/topic names transmitted
   - Local caching for offline operation

### Compliance Verification

```python
from tapps_agents.context7.security import SecurityAuditor

auditor = SecurityAuditor()
compliance = auditor.verify_compliance()

print(f"SOC 2 Verified: {compliance.soc2_verified}")
print(f"Data Retention Compliant: {compliance.data_retention_compliant}")
print(f"Audit Logging Enabled: {compliance.audit_logging_enabled}")
print(f"API Keys Encrypted: {compliance.api_key_encrypted}")
print(f"Privacy Mode Enabled: {compliance.privacy_mode_enabled}")
```

---

## Configuration

### Security Configuration

```yaml
# .tapps-agents/security-config.yaml
context7:
  privacy_mode: true  # Queries stay local
  encrypted_keys: true  # Encrypt stored API keys
  api_key_storage: "env"  # Use environment variables
  compliance:
    soc2_verified: true
    data_retention_days: 30
    audit_logging: true
```

### Privacy Settings

```yaml
context7:
  knowledge_base:
    # Cache settings
    max_cache_size: "100MB"
    cleanup_interval: 86400  # 24 hours
    
    # Privacy settings
    local_only: true  # Never send code to external APIs
    cache_aggressively: true  # Maximize cache usage
```

---

## Data Retention

### Cache Retention Policy

- **Default**: 30 days
- **Configurable**: Set in `security-config.yaml`
- **Automatic Cleanup**: Stale entries removed automatically

### Manual Cleanup

```python
from tapps_agents.context7.commands import Context7Commands

commands = Context7Commands()
result = commands.cmd_cleanup(max_age_days=30)
```

---

## Audit Logging

### Logged Operations

- KB cache lookups
- API calls to Context7
- Cache hits/misses
- Performance metrics
- Security events

### Log Location

- Analytics: `.tapps-agents/kb/context7-cache/.metrics.yaml`
- Dashboard: `.tapps-agents/kb/context7-cache/dashboard/`

---

## Troubleshooting

### API Key Issues

**Problem**: API key not found

**Solution**:
1. Check environment variable: `echo $CONTEXT7_API_KEY`
2. Verify key format
3. Check file permissions if using encrypted storage

### Security Audit Failures

**Problem**: Security audit fails

**Solution**:
1. Review audit results for specific issues
2. Fix file permissions: `chmod 600 .tapps-agents/api-keys.encrypted`
3. Install cryptography: `pip install cryptography`
4. Review recommendations in audit output

### Privacy Concerns

**Problem**: Worried about data privacy

**Solution**:
1. Verify privacy mode is enabled
2. Review what data is sent (only library/topic names)
3. Use local cache to minimize API calls
4. Run security audit to verify compliance

---

## Best Practices

1. **Use Environment Variables** for API keys in production
2. **Enable Encryption** for stored API keys
3. **Run Security Audits** regularly
4. **Monitor Cache Usage** to minimize API calls
5. **Rotate API Keys** periodically
6. **Review Audit Logs** for suspicious activity
7. **Keep Dependencies Updated** for security patches

---

## See Also

- [API Key Management Guide](CONTEXT7_API_KEY_MANAGEMENT.md)
- [Cache Optimization Guide](CONTEXT7_CACHE_OPTIMIZATION.md)
- [CURSOR_AI_INTEGRATION_PLAN_2025.md](CURSOR_AI_INTEGRATION_PLAN_2025.md)

