# Context7 API Key Management Guide

**TappsCodingAgents + Context7 Integration**

This guide covers managing API keys for Context7 integration, including storage options, encryption, and security best practices.

---

## Overview

Context7 API keys are used to fetch library documentation from the Context7 API. This guide covers:

- ✅ Environment variable storage (recommended)
- ✅ Encrypted file storage (optional)
- ✅ Security best practices
- ✅ Key rotation procedures
- ✅ Troubleshooting

---

## Storage Options

### Option 1: Environment Variables (Recommended)

**Best for**: Development, CI/CD, production

Store API key in environment variable:

```bash
# Linux/macOS
export CONTEXT7_API_KEY="your-api-key-here"

# Windows PowerShell
$env:CONTEXT7_API_KEY="your-api-key-here"

# Windows CMD
set CONTEXT7_API_KEY=your-api-key-here
```

**Advantages:**
- ✅ Simple and secure
- ✅ Works with CI/CD systems
- ✅ No files to manage
- ✅ Platform-independent

**Verification:**
```bash
# Check if key is set
echo $CONTEXT7_API_KEY  # Linux/macOS
echo $env:CONTEXT7_API_KEY  # Windows PowerShell
```

### Option 2: Encrypted File Storage

**Best for**: Local development, enhanced security

Store API key in encrypted file:

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
- Master key automatically generated in `.tapps-agents/.master-key`

**File Locations:**
- Encrypted keys: `.tapps-agents/api-keys.encrypted`
- Master key: `.tapps-agents/.master-key` (restricted permissions)

**Advantages:**
- ✅ Encrypted at rest
- ✅ No environment variable needed
- ✅ Multiple keys can be stored

**Disadvantages:**
- ❌ Requires cryptography package
- ❌ Files must be secured (permissions)
- ❌ Not suitable for CI/CD

---

## Security Best Practices

### 1. Never Commit API Keys

**Add to `.gitignore`:**
```
.tapps-agents/api-keys.encrypted
.tapps-agents/.master-key
.env
```

**Verify:**
```bash
git check-ignore .tapps-agents/api-keys.encrypted
```

### 2. File Permissions

**Set restrictive permissions:**
```bash
# Linux/macOS
chmod 600 .tapps-agents/api-keys.encrypted
chmod 600 .tapps-agents/.master-key

# Windows: Use file properties to restrict access
```

**Verify:**
```bash
ls -l .tapps-agents/api-keys.encrypted
# Should show: -rw------- (600)
```

### 3. Key Rotation

**Rotate API keys periodically:**

```python
from tapps_agents.context7.security import APIKeyManager

key_manager = APIKeyManager()

# Update API key
key_manager.store_api_key("context7", "new-api-key-here", encrypt=True)

# Or update environment variable
# export CONTEXT7_API_KEY="new-api-key-here"
```

**Rotation Schedule:**
- Development: Every 90 days
- Production: Every 60 days
- If compromised: Immediately

### 4. Separate Keys for Environments

**Use different keys for different environments:**

```bash
# Development
export CONTEXT7_API_KEY_DEV="dev-key-here"

# Production
export CONTEXT7_API_KEY_PROD="prod-key-here"
```

---

## CLI Commands

### Store API Key

```bash
# Using encrypted storage
python -m tapps_agents.cli context7 store-key --key-name context7 --encrypt

# Using environment variable (manual)
export CONTEXT7_API_KEY="your-key"
```

### List Stored Keys

```bash
python -m tapps_agents.cli context7 list-keys
```

### Delete API Key

```bash
python -m tapps_agents.cli context7 delete-key --key-name context7
```

### Test API Key

```bash
python -m tapps_agents.cli context7 test-key
```

---

## Configuration

### Environment Variable Priority

TappsCodingAgents checks for API keys in this order:

1. Environment variable: `CONTEXT7_API_KEY`
2. Encrypted storage: `.tapps-agents/api-keys.encrypted`
3. Configuration file: `.tapps-agents/config.yaml` (not recommended)

### Configuration File (Not Recommended)

```yaml
# .tapps-agents/config.yaml
context7:
  api_key: "your-api-key-here"  # NOT RECOMMENDED - use env vars instead
```

**⚠️ Warning**: Storing API keys in configuration files is not recommended. Use environment variables or encrypted storage instead.

---

## Troubleshooting

### Problem: API Key Not Found

**Symptoms:**
- Error: "Context7 API key not found"
- Cache misses increase

**Solutions:**

1. **Check Environment Variable:**
   ```bash
   echo $CONTEXT7_API_KEY  # Linux/macOS
   echo $env:CONTEXT7_API_KEY  # Windows PowerShell
   ```

2. **Check Encrypted Storage:**
   ```python
   from tapps_agents.context7.security import APIKeyManager
   key_manager = APIKeyManager()
   key = key_manager.load_api_key("context7")
   print(f"Key found: {key is not None}")
   ```

3. **Set Environment Variable:**
   ```bash
   export CONTEXT7_API_KEY="your-key-here"
   ```

### Problem: Encryption Not Available

**Symptoms:**
- Error: "cryptography package not installed"
- Encryption fails

**Solution:**
```bash
pip install cryptography
```

### Problem: Invalid API Key

**Symptoms:**
- API calls fail
- Authentication errors

**Solutions:**

1. **Verify Key Format:**
   - Check key length and format
   - Ensure no extra spaces or quotes

2. **Test Key:**
   ```bash
   python -m tapps_agents.cli context7 test-key
   ```

3. **Regenerate Key:**
   - Get new key from Context7 dashboard
   - Update storage or environment variable

### Problem: Permission Denied

**Symptoms:**
- Cannot read encrypted keys file
- File permission errors

**Solution:**
```bash
# Fix permissions
chmod 600 .tapps-agents/api-keys.encrypted
chmod 600 .tapps-agents/.master-key

# Verify
ls -l .tapps-agents/api-keys.encrypted
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Test
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set API Key
        env:
          CONTEXT7_API_KEY: ${{ secrets.CONTEXT7_API_KEY }}
        run: |
          export CONTEXT7_API_KEY="$CONTEXT7_API_KEY"
          python -m pytest
```

### GitLab CI

```yaml
test:
  script:
    - export CONTEXT7_API_KEY="${CONTEXT7_API_KEY}"
    - python -m pytest
  variables:
    CONTEXT7_API_KEY: $CONTEXT7_API_KEY
```

### Azure DevOps

```yaml
variables:
  - name: CONTEXT7_API_KEY
    value: $(CONTEXT7_API_KEY)
    secret: true

steps:
  - script: |
      export CONTEXT7_API_KEY="$(CONTEXT7_API_KEY)"
      python -m pytest
```

---

## Examples

### Example 1: Development Setup

```bash
# Set environment variable
export CONTEXT7_API_KEY="dev-key-here"

# Verify
python -m tapps_agents.cli context7 test-key
```

### Example 2: Production Setup

```bash
# Use encrypted storage
python -m tapps_agents.cli context7 store-key --key-name context7 --encrypt

# Or use environment variable (recommended)
export CONTEXT7_API_KEY="prod-key-here"
```

### Example 3: Key Rotation

```python
from tapps_agents.context7.security import APIKeyManager

# Initialize
key_manager = APIKeyManager()

# Store new key
key_manager.store_api_key("context7", "new-key-here", encrypt=True)

# Verify
key = key_manager.load_api_key("context7")
assert key == "new-key-here"
```

---

## See Also

- [Security & Privacy Guide](CONTEXT7_SECURITY_PRIVACY.md)
- [Cache Optimization Guide](CONTEXT7_CACHE_OPTIMIZATION.md)
- [CURSOR_AI_INTEGRATION_PLAN_2025.md](CURSOR_AI_INTEGRATION_PLAN_2025.md)

