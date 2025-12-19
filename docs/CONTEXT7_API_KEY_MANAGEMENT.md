# Context7 API Key Management Guide

**TappsCodingAgents + Context7 Integration**

This guide covers managing API keys for Context7 integration, including storage options, encryption, and security best practices.

---

## Overview

Context7 API keys are used to fetch library documentation from the Context7 API. This guide covers:

- ✅ **Automatic API key loading** - No need to manually pass keys to agents
- ✅ **Where to find your API key** (environment variable or encrypted storage)
- ✅ Environment variable storage (recommended)
- ✅ Encrypted file storage (automatic fallback)
- ✅ Security best practices
- ✅ Key rotation procedures
- ✅ Direct API usage (HTTP fallback)
- ✅ Troubleshooting

## Quick Start: Automatic API Key Loading

**✨ NEW: The framework automatically loads your API key when needed!**

**The framework automatically checks for your API key in this order:**

1. **Environment Variable** (`CONTEXT7_API_KEY`) - Checked first
2. **Encrypted Storage** (`.tapps-agents/api-keys.encrypted`) - **Automatically loaded if environment variable not set**

**Key Benefits:**
- ✅ **No manual key passing required** - Agents automatically have access to the API key
- ✅ **Automatic fallback** - If not in environment, loads from encrypted storage automatically
- ✅ **Seamless integration** - Works transparently with all agents (Architect, Designer, Implementer, Tester, etc.)

**To quickly check where your key is:**

**Option 1: Use the check script (recommended):**
```bash
python docs/scripts/check_context7_key.py
```

**Option 2: Quick one-liner:**
```bash
# Windows PowerShell
python -c "import os; from tapps_agents.context7.security import APIKeyManager; env_key = os.getenv('CONTEXT7_API_KEY'); mgr = APIKeyManager(); enc_key = mgr.load_api_key('context7'); print('Environment:', 'SET' if env_key else 'NOT SET'); print('Encrypted:', 'FOUND' if enc_key else 'NOT FOUND'); print('Available:', 'YES' if (env_key or enc_key) else 'NO')"

# Linux/macOS
python -c "import os; from tapps_agents.context7.security import APIKeyManager; env_key = os.getenv('CONTEXT7_API_KEY'); mgr = APIKeyManager(); enc_key = mgr.load_api_key('context7'); print('Environment:', 'SET' if env_key else 'NOT SET'); print('Encrypted:', 'FOUND' if enc_key else 'NOT FOUND'); print('Available:', 'YES' if (env_key or enc_key) else 'NO')"
```

**Note:** If you have a key stored in encrypted storage, **you don't need to manually load it** - the framework will automatically load it when agents initialize. However, if you want to manually load it to the environment:

```bash
# Windows PowerShell
$env:CONTEXT7_API_KEY = (python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')")

# Linux/macOS  
export CONTEXT7_API_KEY=$(python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')")
```

---

## How Context7 API Works

### Two Access Methods

TappsCodingAgents supports two ways to access Context7:

1. **MCP Gateway (Preferred)** - When running from Cursor
   - Uses Cursor's MCP Context7 server
   - No API key needed (handled by Cursor)
   - Automatic fallback to HTTP if MCP unavailable

2. **Direct HTTP API (Fallback)** - When MCP Gateway unavailable
   - Automatically loads `CONTEXT7_API_KEY` from environment or encrypted storage
   - Makes direct HTTP requests to Context7 API
   - Used automatically when MCP Gateway is not available
   - **No manual key passing required** - Framework handles it automatically

### Context7 API Endpoints

The framework uses the following Context7 API endpoints:

#### 1. Search API (Library Resolution)

**Endpoint**: `GET https://context7.com/api/v2/search`

**Purpose**: Search for libraries and resolve library names to Context7 IDs

**Example Request**:
```bash
curl -X GET "https://context7.com/api/v2/search?query=next.js" \
  -H "Authorization: Bearer CONTEXT7_API_KEY"
```

**Parameters**:
- `query` (required): Search term for finding libraries (e.g., "next.js", "react", "fastapi")

**Response Format**:
```json
[
  {
    "id": "/vercel/next.js",
    "title": "Next.js",
    "description": "Next.js enables you to create full-stack web...",
    "benchmarkScore": 91.1,
    "trustScore": 10,
    "stars": 131745,
    "versions": ["v14.3.0-canary.87", "v13.5.11", "v15.1.8"]
  },
  {
    "id": "/websites/nextjs",
    "title": "Next.js",
    "description": "Next.js is a React framework for building full-stack web...",
    "benchmarkScore": 86.3
  }
]
```

#### 2. Documentation API (Code Mode)

**Endpoint**: `GET https://context7.com/api/v2/docs/code/{library_id}`

**Purpose**: Fetch code examples and API references for a library

**Example Request**:
```bash
curl -X GET "https://context7.com/api/v2/docs/code/vercel/next.js?type=json&topic=ssr&page=1" \
  -H "Authorization: Bearer CONTEXT7_API_KEY"
```

**Parameters**:
- `library_id` (path): Context7 library ID (e.g., "vercel/next.js", format: `org/project`)
- `type` (query): Response format - `json` (default) or `txt`
- `topic` (query, optional): Focus documentation on a specific topic (e.g., "ssr", "routing", "hooks")
- `page` (query, optional): Page number for pagination (1-10, default: 1)
- `limit` (query, optional): Number of results per page

**Response Format**:
```json
{
  "snippets": [
    {
      "codeTitle": "Dynamically Load Client-Side Only Component",
      "codeDescription": "Explains how to prevent server-side rendering...",
      "codeLanguage": "jsx",
      "codeTokens": 130,
      "codeId": "https://github.com/vercel/next.js/blob/canary/docs/...",
      "pageTitle": "How to lazy load Client Components",
      "codeList": [
        {
          "language": "jsx",
          "code": "'use client'\n\nimport dynamic from 'next/dynamic'\n\n..."
        }
      ]
    }
  ],
  "totalTokens": 1764,
  "pagination": {
    "page": 1,
    "limit": 10,
    "totalPages": 10,
    "hasNext": true,
    "hasPrev": false
  }
}
```

#### 3. Documentation API (Info Mode)

**Endpoint**: `GET https://context7.com/api/v2/docs/info/{library_id}`

**Purpose**: Fetch conceptual guides and narrative documentation

**Example Request**:
```bash
curl -X GET "https://context7.com/api/v2/docs/info/vercel/next.js?type=json&topic=ssr&page=1" \
  -H "Authorization: Bearer CONTEXT7_API_KEY"
```

**Parameters**: Same as code mode

**Response Format**:
```json
{
  "snippets": [
    {
      "pageId": "https://github.com/vercel/next.js/blob/canary/docs/...",
      "breadcrumb": "Examples > With no SSR",
      "content": "To dynamically load a component on the client side...",
      "contentTokens": 42
    }
  ],
  "totalTokens": 856,
  "pagination": { ... }
}
```

### Automatic Fallback Mechanism

The framework automatically uses the best available method and **automatically loads the API key when needed**:

```python
# 1. Try MCP Gateway first (no API key needed)
if mcp_gateway_available:
    result = await mcp_gateway.call_tool("mcp_Context7_resolve-library-id", ...)
    
# 2. Fallback to HTTP API if MCP unavailable
#    API key is automatically loaded from environment or encrypted storage
elif api_key_available:  # Automatically checked and loaded
    result = await http_client.search(query="library-name")
    
# 3. Error if neither available
else:
    return {"error": "Context7 not available: MCP Gateway and API key both unavailable"}
```

### Automatic API Key Loading for Agents

**✨ All agents automatically have access to the Context7 API key - no manual passing required!**

When agents initialize with Context7 support, the framework:

1. **Automatically checks** for `CONTEXT7_API_KEY` in environment
2. **Automatically loads** from encrypted storage if not in environment
3. **Sets environment variable** for future use (if loaded from storage)
4. **Makes key available** to all Context7 operations

**Example - Agent Usage (No API Key Passing Needed):**

```python
from tapps_agents.agents.architect import ArchitectAgent
from tapps_agents.core.config import load_config

# Initialize agent - API key is automatically loaded!
config = load_config()
agent = ArchitectAgent(config=config)

# Context7 helper is automatically initialized with API key access
# No need to pass API key manually!
await agent.activate()

# Use Context7 - API key is already available
if agent.context7:
    docs = await agent.context7.get_documentation("react", topic="hooks")
```

**Supported Agents:**
- ✅ Architect Agent
- ✅ Designer Agent
- ✅ Implementer Agent
- ✅ Tester Agent
- ✅ Analyst Agent

All of these agents automatically have Context7 API key access when initialized.

### Python Example: Direct API Usage

If you need to call Context7 API directly (bypassing the framework):

**Note:** The framework automatically loads the API key from encrypted storage if not in environment. For direct API usage, you can use the same helper:

```python
import httpx
import os

# Option 1: Use automatic loading (recommended)
from tapps_agents.context7.backup_client import _ensure_context7_api_key
api_key = _ensure_context7_api_key()

# Option 2: Manual check (fallback)
if not api_key:
    api_key = os.getenv("CONTEXT7_API_KEY")

base_url = "https://context7.com/api/v2"

# Search for a library
with httpx.Client(timeout=10.0) as client:
    response = client.get(
        f"{base_url}/search",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        params={"query": "fastapi"},
    )
    results = response.json()
    print(f"Found {len(results)} libraries")

# Get documentation
library_id = "tiangolo/fastapi"  # From search results
with httpx.Client(timeout=30.0) as client:
    response = client.get(
        f"{base_url}/docs/code/{library_id}",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        params={"type": "json", "topic": "routing", "page": 1},
    )
    docs = response.json()
    print(f"Retrieved {len(docs.get('snippets', []))} code snippets")
```

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

**✨ Automatic Loading:** Keys stored in encrypted storage are **automatically loaded** when agents initialize - no manual steps required!

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

## Managing API Keys

This repo does not currently expose a dedicated `tapps-agents context7 ...` CLI command set.

Recommended options:

- **Environment variables (recommended)**:

```bash
export CONTEXT7_API_KEY="your-key"
```

- **Encrypted local storage (advanced)** via the Python API:

```python
from pathlib import Path
from tapps_agents.context7.security import APIKeyManager

mgr = APIKeyManager(config_dir=Path(".tapps-agents"))
mgr.store_api_key("context7", "your-key", encrypt=True)
```

> Note: Cursor-first policy means Skills/Background Agents use Cursor’s configured model; key storage here only affects Context7 API access (if used).

---

## Configuration

### Environment Variable Priority

Recommended lookup order:

1. Environment variable: `CONTEXT7_API_KEY`
2. Encrypted storage file under `.tapps-agents/` (managed by `APIKeyManager`)

This repo does **not** recommend (or currently support) putting Context7 API keys into `.tapps-agents/config.yaml`.

**⚠️ Warning**: Storing API keys in configuration files is not recommended. Use environment variables or encrypted storage instead.

---

## Finding Your API Key

The framework checks for the API key in the following order:

1. **Environment Variable** (`CONTEXT7_API_KEY`) - Highest priority
2. **Encrypted Storage** (`.tapps-agents/api-keys.encrypted`) - Automatic fallback

### Quick Check: Where is My Key?

Run this command to check all locations:

```python
import os
from pathlib import Path
from tapps_agents.context7.security import APIKeyManager

print("=" * 60)
print("Context7 API Key Location Check")
print("=" * 60)

# Check 1: Environment Variable
env_key = os.getenv("CONTEXT7_API_KEY")
print(f"1. Environment Variable: {'✅ SET' if env_key else '❌ NOT SET'}")
if env_key:
    print(f"   Key length: {len(env_key)}")
    print(f"   Key prefix: {env_key[:20]}...")

# Check 2: Encrypted Storage
try:
    mgr = APIKeyManager()
    encrypted_key = mgr.load_api_key("context7")
    print(f"\n2. Encrypted Storage: {'✅ FOUND' if encrypted_key else '❌ NOT FOUND'}")
    if encrypted_key:
        print(f"   Key length: {len(encrypted_key)}")
        print(f"   Key prefix: {encrypted_key[:20]}...")
        print(f"   File location: {Path('.tapps-agents/api-keys.encrypted').absolute()}")
except Exception as e:
    print(f"\n2. Encrypted Storage: ❌ ERROR - {e}")

# Check 3: File Exists
encrypted_file = Path(".tapps-agents/api-keys.encrypted")
print(f"\n3. Encrypted File Exists: {'✅ YES' if encrypted_file.exists() else '❌ NO'}")
if encrypted_file.exists():
    print(f"   File size: {encrypted_file.stat().st_size} bytes")
    print(f"   File path: {encrypted_file.absolute()}")

# Summary
final_key = env_key or encrypted_key
print(f"\n{'=' * 60}")
print(f"Final Status: {'✅ API KEY AVAILABLE' if final_key else '❌ NO API KEY FOUND'}")
if final_key:
    print(f"Source: {'Environment Variable' if env_key else 'Encrypted Storage'}")
print("=" * 60)
```

### Command-Line Check

**Windows PowerShell:**
```powershell
# Check environment variable
if ($env:CONTEXT7_API_KEY) { 
    Write-Host "✅ Key in environment: $($env:CONTEXT7_API_KEY.Length) chars" 
} else { 
    Write-Host "❌ No key in environment" 
}

# Check encrypted storage
python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print('✅ Key in encrypted storage' if key else '❌ No key in encrypted storage')"
```

**Linux/macOS:**
```bash
# Check environment variable
if [ -n "$CONTEXT7_API_KEY" ]; then
    echo "✅ Key in environment: ${#CONTEXT7_API_KEY} chars"
else
    echo "❌ No key in environment"
fi

# Check encrypted storage
python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print('✅ Key in encrypted storage' if key else '❌ No key in encrypted storage')"
```

### Key Storage Locations

| Location | Path | Priority | Notes |
|----------|------|----------|-------|
| **Environment Variable** | `CONTEXT7_API_KEY` | 1 (Highest) | Session-based, not persistent |
| **Encrypted Storage** | `.tapps-agents/api-keys.encrypted` | 2 (Fallback) | Persistent, encrypted at rest |

**File Locations:**
- Encrypted keys: `.tapps-agents/api-keys.encrypted`
- Master key: `.tapps-agents/.master-key` (auto-generated, restricted permissions)

---

## Troubleshooting

### Problem: API Key Not Found

**Symptoms:**
- Error: "Context7 API key not found"
- Cache misses increase
- Error: "Context7 API unavailable: MCP Gateway not available and CONTEXT7_API_KEY not set"
- **Note**: If you see "quota exceeded" errors, your API key IS working - see "API Quota Exceeded" section below

**Solutions:**

1. **Check All Locations:**
   ```python
   # Run the quick check script above to see where your key is
   ```

2. **Check Environment Variable:**
   ```bash
   # Linux/macOS
   echo $CONTEXT7_API_KEY
   
   # Windows PowerShell
   echo $env:CONTEXT7_API_KEY
   ```

3. **Check Encrypted Storage:**
   ```python
   from tapps_agents.context7.security import APIKeyManager
   key_manager = APIKeyManager()
   key = key_manager.load_api_key("context7")
   if key:
       print(f"✅ Key found in encrypted storage (length: {len(key)})")
       print(f"   File: .tapps-agents/api-keys.encrypted")
   else:
       print("❌ No key in encrypted storage")
   ```

4. **Load Key from Encrypted Storage to Environment:**
   ```bash
   # Windows PowerShell
   $env:CONTEXT7_API_KEY = (python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')")
   
   # Linux/macOS
   export CONTEXT7_API_KEY=$(python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')")
   ```

5. **Set Environment Variable Manually:**
   ```bash
   # Windows PowerShell
   $env:CONTEXT7_API_KEY="your-key-here"
   
   # Linux/macOS
   export CONTEXT7_API_KEY="your-key-here"
   ```

6. **Store Key in Encrypted Storage:**
   ```python
   from tapps_agents.context7.security import APIKeyManager
   key_manager = APIKeyManager()
   key_manager.store_api_key("context7", "your-key-here", encrypt=True)
   print("✅ Key stored in encrypted storage")
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

2. **Test Key with Direct API Call:**
   ```bash
   # Test search API
   curl -X GET "https://context7.com/api/v2/search?query=react" \
     -H "Authorization: Bearer $CONTEXT7_API_KEY"
   
   # Test docs API
   curl -X GET "https://context7.com/api/v2/docs/code/facebook/react?type=json&page=1" \
     -H "Authorization: Bearer $CONTEXT7_API_KEY"
   
   # Or use the cache pre-population script (it will fail fast if the key is invalid):
   python scripts/prepopulate_context7_cache.py --libraries fastapi
   ```

3. **Regenerate Key:**
   - Get new key from Context7 dashboard
   - Update storage or environment variable

### Problem: API Quota Exceeded

**Symptoms:**
- Error: "Context7 API quota exceeded: Daily quota exceeded"
- HTTP 429 status code in API responses
- Cache pre-population fails with quota error
- All API calls fail despite valid API key

**Root Cause:**
- Your Context7 API plan has a daily request limit
- The limit has been reached for the current day
- This is **not** an API key issue - the key is valid and working

**Solutions:**

1. **Check Quota Status:**
   ```bash
   # The error message will indicate quota exceeded
   # Example: "Context7 API quota exceeded: Daily quota exceeded. Upgrade your plan at context7.com/plans for more requests."
   ```

2. **Wait for Quota Reset:**
   - Daily quotas typically reset at midnight UTC
   - Wait until quota resets before retrying

3. **Upgrade Your Plan:**
   - Visit [context7.com/plans](https://context7.com/plans) to upgrade
   - Higher tier plans have larger quotas

4. **Optimize API Usage:**
   - Pre-populate cache in smaller batches
   - Use `--no-cache` flag during init to skip pre-population if quota is low
   - Rely on cache hits instead of API calls when possible

5. **Reduce Pre-population Scope:**
   ```bash
   # Instead of caching all libraries, cache only essential ones
   python scripts/prepopulate_context7_cache.py --libraries fastapi pytest pydantic
   ```

**Important Notes:**
- ✅ **API key loading is working correctly** - The quota error confirms your API key is valid
- ✅ **Automatic fallback works** - The framework correctly detects quota errors
- ⚠️ **Quota limits are per API key** - Each key has its own daily limit
- ⚠️ **Cache pre-population can use many requests** - 64+ libraries × multiple topics = many API calls

**Error Message Examples:**

**Before Fix (Misleading):**
```
Error: Context7 API unavailable: MCP Gateway not available and CONTEXT7_API_KEY not set.
```

**After Fix (Accurate):**
```
Error: Context7 API quota exceeded. Daily quota exceeded. Upgrade your plan at context7.com/plans for more requests.
Cache pre-population requires available API quota. Consider upgrading your plan or running pre-population later.
```

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

# Validate by performing a small fetch (fails fast if the key is invalid)
python scripts/prepopulate_context7_cache.py --libraries fastapi
```

### Example 2: Production Setup

```bash
# Use encrypted storage (Python API)
python -c "from tapps_agents.context7.security import APIKeyManager; APIKeyManager().store_api_key('context7','YOUR_KEY',encrypt=True)"

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

## Quick Reference: Key Location

**Always know where your key is:**

1. **Run the check script:**
   ```bash
   python docs/scripts/check_context7_key.py
   ```

2. **Key storage locations (checked in order):**
   - `CONTEXT7_API_KEY` environment variable (highest priority)
   - `.tapps-agents/api-keys.encrypted` (automatic fallback)

3. **Load key from encrypted storage:**
   ```bash
   # Windows PowerShell
   $env:CONTEXT7_API_KEY = (python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')")
   
   # Linux/macOS
   export CONTEXT7_API_KEY=$(python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')")
   ```

## See Also

- [Context7 API Quick Reference](CONTEXT7_API_QUICK_REFERENCE.md) - Quick reference for API endpoints and usage
- [Security & Privacy Guide](CONTEXT7_SECURITY_PRIVACY.md)
- [Cache Optimization Guide](CONTEXT7_CACHE_OPTIMIZATION.md)
- [CURSOR_AI_INTEGRATION_PLAN_2025.md](CURSOR_AI_INTEGRATION_PLAN_2025.md)

