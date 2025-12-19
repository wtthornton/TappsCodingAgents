# Context7 Debugging Guide

**TappsCodingAgents + Context7 Integration**

This guide covers debugging Context7 integration issues, including API key loading, quota management, and error diagnosis.

---

## Quick Diagnosis

### Step 1: Check API Key Status

**✨ Note:** The framework automatically loads the API key from encrypted storage if not in environment - no manual steps needed!

```bash
# Use the check script
python docs/scripts/check_context7_key.py
```

**Expected Output:**
```
[OK] API KEY AVAILABLE
   Source: Environment Variable (CONTEXT7_API_KEY) or Encrypted Storage
   (Automatically loaded if in encrypted storage)
```

### Step 2: Test API Connectivity

```bash
# Test with a single library
python -c "
import asyncio
from pathlib import Path
from tapps_agents.core.init_project import pre_populate_context7_cache

result = asyncio.run(pre_populate_context7_cache(Path('.'), libraries=['pytest']))
print('Success:', result.get('success'))
print('Error:', result.get('error'))
"
```

### Step 3: Interpret Error Messages

**If you see:**
- ✅ "quota exceeded" → API key is working, but quota limit reached
- ❌ "API key not set" → API key not found in environment or encrypted storage (check both locations)
- ❌ "MCP Gateway not available" → Running outside Cursor, API key will be automatically loaded from encrypted storage if available

---

## Common Issues and Solutions

### Issue 1: "Context7 API quota exceeded"

**Symptoms:**
- Error: "Context7 API quota exceeded: Daily quota exceeded"
- HTTP 429 status code
- All API calls fail despite valid API key

**Diagnosis:**
- ✅ **API key is working correctly** - Quota errors confirm the key is valid
- ❌ **Daily quota limit reached** - Your plan's daily limit has been exceeded

**Solutions:**
1. **Wait for quota reset** (typically midnight UTC)
2. **Upgrade your Context7 plan** at [context7.com/plans](https://context7.com/plans)
3. **Reduce pre-population scope:**
   ```bash
   # Cache only essential libraries
   python scripts/prepopulate_context7_cache.py --libraries fastapi pytest pydantic
   ```
4. **Skip pre-population during init:**
   ```bash
   python -m tapps_agents.cli init --no-cache
   ```

**Verification:**
```bash
# Check if quota is available
curl -X GET "https://context7.com/api/v2/search?query=test" \
  -H "Authorization: Bearer $CONTEXT7_API_KEY"
# If you get 429, quota is exceeded
# If you get 200, quota is available
```

### Issue 2: "Context7 API unavailable: MCP Gateway not available and CONTEXT7_API_KEY not set"

**Symptoms:**
- Error message indicates API key not found
- Cache pre-population fails

**Diagnosis:**
- **Note:** The framework automatically loads API keys from encrypted storage - this error usually means the key is not stored anywhere
- Check if API key exists in either environment variable or encrypted storage

**Solutions:**
1. **Check API key location:**
   ```bash
   python docs/scripts/check_context7_key.py
   ```

2. **If key is in encrypted storage:** The framework should automatically load it. If you still see this error, try manually loading (for debugging):
   ```bash
   # Windows PowerShell
   $env:CONTEXT7_API_KEY = (python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')")
   
   # Linux/macOS
   export CONTEXT7_API_KEY=$(python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')")
   ```

3. **If key doesn't exist:** Store it in encrypted storage:
   ```python
   from tapps_agents.context7.security import APIKeyManager
   key_manager = APIKeyManager()
   key_manager.store_api_key("context7", "your-api-key-here", encrypt=True)
   ```

4. **Verify API key is set:**
   ```bash
   # Windows PowerShell
   echo $env:CONTEXT7_API_KEY
   
   # Linux/macOS
   echo $CONTEXT7_API_KEY
   ```

### Issue 3: Cache Pre-population Fails

**Symptoms:**
- `tapps-agents init` shows cache pre-population failed
- Cache directory is empty

**Diagnosis Steps:**

1. **Check API key:**
   ```bash
   python docs/scripts/check_context7_key.py
   ```

2. **Check error message:**
   - If "quota exceeded" → See Issue 1
   - If "API key not set" → See Issue 2
   - If other error → Check API connectivity

3. **Test with single library:**
   ```bash
   python -c "
   import asyncio
   from pathlib import Path
   from tapps_agents.core.init_project import pre_populate_context7_cache
   
   result = asyncio.run(pre_populate_context7_cache(Path('.'), libraries=['pytest']))
   print('Success:', result.get('success'))
   print('Cached:', result.get('cached'))
   print('Failed:', result.get('failed'))
   print('Error:', result.get('error'))
   "
   ```

**Solutions:**
- If quota issue: Wait for reset or upgrade plan
- If API key issue: Load key from encrypted storage
- If connectivity issue: Check network/firewall settings

---

## Debugging Workflow

### Step-by-Step Debugging

1. **Verify API Key:**
   ```bash
   python docs/scripts/check_context7_key.py
   ```

2. **Test API Connectivity:**
   ```bash
   curl -X GET "https://context7.com/api/v2/search?query=test" \
     -H "Authorization: Bearer $CONTEXT7_API_KEY"
   ```

3. **Check Quota Status:**
   - If HTTP 429 → Quota exceeded
   - If HTTP 200 → Quota available
   - If HTTP 401 → Invalid API key

4. **Test Framework Integration:**
   ```bash
   python -m tapps_agents.cli init --no-cache  # Skip cache to test other components
   ```

5. **Test Cache Pre-population:**
   ```bash
   python scripts/prepopulate_context7_cache.py --libraries pytest
   ```

---

## Error Message Reference

### Accurate Error Messages (After Fixes)

| Error Message | Meaning | Solution |
|--------------|---------|----------|
| "Context7 API quota exceeded: Daily quota exceeded" | API key is valid, but daily quota limit reached | Wait for reset or upgrade plan |
| "Context7 API unavailable: MCP Gateway not available and CONTEXT7_API_KEY not set" | API key not found in environment or encrypted storage | Load key from encrypted storage or set environment variable |
| "Context7 API calls failed despite API key being available" | API key is set but calls are failing for other reasons | Check network connectivity, API status, or library names |

### Misleading Error Messages (Before Fixes)

**Old (Misleading):**
```
Error: Context7 API unavailable: MCP Gateway not available and CONTEXT7_API_KEY not set.
```

**New (Accurate):**
```
Error: Context7 API quota exceeded. Daily quota exceeded. Upgrade your plan at context7.com/plans for more requests.
```

---

## Verification Checklist

Use this checklist to verify Context7 integration:

- [ ] API key is available (environment variable or encrypted storage)
- [ ] API key is valid (test with curl or direct API call)
- [ ] Quota is available (check for HTTP 429 errors)
- [ ] MCP Gateway available (when running from Cursor)
- [ ] Network connectivity (can reach context7.com)
- [ ] Cache directory exists (`.tapps-agents/kb/context7-cache`)
- [ ] Error messages are accurate (not misleading)

---

## See Also

- [Context7 API Key Management Guide](CONTEXT7_API_KEY_MANAGEMENT.md) - Complete API key setup and troubleshooting
- [Context7 Cache Optimization Guide](CONTEXT7_CACHE_OPTIMIZATION.md) - Cache performance and optimization
- [Context7 API Quick Reference](CONTEXT7_API_QUICK_REFERENCE.md) - API endpoint reference

