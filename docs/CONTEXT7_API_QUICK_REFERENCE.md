# Context7 API Quick Reference

**TappsCodingAgents + Context7 Integration**

Quick reference for calling Context7 API directly with API key authentication.

---

## Base URL

```
https://context7.com/api/v2
```

## Authentication

All API requests require authentication via Bearer token:

```bash
Authorization: Bearer CONTEXT7_API_KEY
```

### Finding Your API Key

**✨ NEW: Automatic API Key Loading!**

The framework automatically checks for your API key in this order:

1. **Environment Variable** (`CONTEXT7_API_KEY`) - Highest priority
2. **Encrypted Storage** (`.tapps-agents/api-keys.encrypted`) - **Automatically loaded if environment variable not set**

**Key Benefits:**
- ✅ **No manual key passing** - Agents automatically have access
- ✅ **Automatic fallback** - Loads from encrypted storage when needed
- ✅ **Seamless integration** - Works with all agents transparently

**Quick Check:**
```python
import os
from tapps_agents.context7.security import APIKeyManager

# Check environment variable
env_key = os.getenv("CONTEXT7_API_KEY")
print(f"Environment: {'SET' if env_key else 'NOT SET'}")

# Check encrypted storage
mgr = APIKeyManager()
enc_key = mgr.load_api_key("context7")
print(f"Encrypted: {'FOUND' if enc_key else 'NOT FOUND'}")

# Use whichever is available
api_key = env_key or enc_key
print(f"API Key Available: {'YES' if api_key else 'NO'}")
```

**Set the API key as an environment variable:**

```bash
# Linux/macOS
export CONTEXT7_API_KEY="your-api-key-here"

# Windows PowerShell
$env:CONTEXT7_API_KEY="your-api-key-here"
```

**Note:** If you store the key in encrypted storage, **you don't need to manually load it** - the framework automatically loads it when agents initialize. However, if you want to manually load it:

```bash
# Windows PowerShell
$env:CONTEXT7_API_KEY = (python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')")

# Linux/macOS
export CONTEXT7_API_KEY=$(python -c "from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')")
```

See [API Key Management Guide](CONTEXT7_API_KEY_MANAGEMENT.md) for complete details on key storage and retrieval.

---

## API Endpoints

### 1. Search Libraries

**Endpoint**: `GET /search`

**Purpose**: Search for libraries and resolve library names to Context7 IDs

**Example**:
```bash
curl -X GET "https://context7.com/api/v2/search?query=next.js" \
  -H "Authorization: Bearer $CONTEXT7_API_KEY"
```

**Parameters**:
- `query` (required): Search term (e.g., "next.js", "react", "fastapi")

**Response**: Array of library objects with `id`, `title`, `description`, `benchmarkScore`, etc.

---

### 2. Get Documentation (Code Mode)

**Endpoint**: `GET /docs/code/{library_id}`

**Purpose**: Fetch code examples and API references

**Example**:
```bash
curl -X GET "https://context7.com/api/v2/docs/code/vercel/next.js?type=json&topic=ssr&page=1" \
  -H "Authorization: Bearer $CONTEXT7_API_KEY"
```

**Parameters**:
- `library_id` (path): Context7 library ID (e.g., "vercel/next.js")
- `type` (query): `json` (default) or `txt`
- `topic` (query, optional): Specific topic (e.g., "ssr", "routing", "hooks")
- `page` (query, optional): Page number (1-10, default: 1)
- `limit` (query, optional): Results per page

**Response**: JSON object with `snippets` array containing code examples

---

### 3. Get Documentation (Info Mode)

**Endpoint**: `GET /docs/info/{library_id}`

**Purpose**: Fetch conceptual guides and narrative documentation

**Example**:
```bash
curl -X GET "https://context7.com/api/v2/docs/info/vercel/next.js?type=json&topic=ssr&page=1" \
  -H "Authorization: Bearer $CONTEXT7_API_KEY"
```

**Parameters**: Same as code mode

**Response**: JSON object with `snippets` array containing documentation content

---

## Python Examples

### Search for a Library

```python
import httpx
import os

api_key = os.getenv("CONTEXT7_API_KEY")
base_url = "https://context7.com/api/v2"

with httpx.Client(timeout=10.0) as client:
    response = client.get(
        f"{base_url}/search",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        params={"query": "fastapi"},
    )
    
    if response.status_code == 200:
        results = response.json()
        for result in results:
            print(f"Found: {result['id']} - {result['title']}")
            print(f"  Score: {result.get('benchmarkScore', 'N/A')}")
    else:
        print(f"Error: {response.status_code}")
```

### Get Code Documentation

```python
import httpx
import os

api_key = os.getenv("CONTEXT7_API_KEY")
base_url = "https://context7.com/api/v2"
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
    
    if response.status_code == 200:
        docs = response.json()
        snippets = docs.get("snippets", [])
        print(f"Retrieved {len(snippets)} code snippets")
        
        for snippet in snippets:
            print(f"\n## {snippet.get('codeTitle', 'Untitled')}")
            code_list = snippet.get("codeList", [])
            for code_item in code_list:
                print(f"```{code_item.get('language', '')}")
                print(code_item.get("code", ""))
                print("```")
    else:
        print(f"Error: {response.status_code}")
```

### Get Info Documentation

```python
import httpx
import os

api_key = os.getenv("CONTEXT7_API_KEY")
base_url = "https://context7.com/api/v2"
library_id = "tiangolo/fastapi"

with httpx.Client(timeout=30.0) as client:
    response = client.get(
        f"{base_url}/docs/info/{library_id}",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        params={"type": "json", "topic": "authentication", "page": 1},
    )
    
    if response.status_code == 200:
        docs = response.json()
        snippets = docs.get("snippets", [])
        
        for snippet in snippets:
            breadcrumb = snippet.get("breadcrumb", "")
            content = snippet.get("content", "")
            print(f"\n## {breadcrumb}")
            print(content)
```

---

## Using with TappsCodingAgents

### Automatic Fallback

The framework automatically uses the best available method:

1. **MCP Gateway** (preferred) - When running from Cursor
   - No API key needed
   - Uses Cursor's MCP Context7 server

2. **HTTP API** (fallback) - When MCP unavailable
   - Requires `CONTEXT7_API_KEY` environment variable
   - Automatically used by the framework

### Framework Usage

```python
from tapps_agents.context7.backup_client import (
    call_context7_resolve_with_fallback,
    call_context7_get_docs_with_fallback,
)

# Search for library (automatic fallback)
result = await call_context7_resolve_with_fallback("fastapi", mcp_gateway=None)
if result.get("success"):
    matches = result["result"]["matches"]
    library_id = matches[0]["id"] if matches else None

# Get documentation (automatic fallback)
if library_id:
    docs = await call_context7_get_docs_with_fallback(
        library_id, topic="routing", mode="code", page=1, mcp_gateway=None
    )
    if docs.get("success"):
        content = docs["result"]["content"]
        print(content)
```

---

## Response Formats

### Search Response

```json
[
  {
    "id": "/vercel/next.js",
    "title": "Next.js",
    "description": "Next.js enables you to create full-stack web...",
    "branch": "canary",
    "lastUpdateDate": "2025-11-17T22:20:15.784Z",
    "state": "finalized",
    "totalTokens": 824953,
    "totalSnippets": 3336,
    "stars": 131745,
    "trustScore": 10,
    "benchmarkScore": 91.1,
    "versions": ["v14.3.0-canary.87", "v13.5.11", "v15.1.8"]
  }
]
```

### Code Docs Response

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

### Info Docs Response

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

---

## Error Handling

### Common Status Codes

- **200**: Success
- **401**: Unauthorized - Invalid or missing API key
- **403**: Forbidden - API key lacks permissions
- **404**: Not found - Library or endpoint not found
- **429**: Rate limit exceeded
- **500**: Server error

### Error Response Format

```json
{
  "error": "Error message here",
  "status": 401
}
```

### Python Error Handling

```python
import httpx

try:
    response = client.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        # Process data
    elif response.status_code == 401:
        print("Authentication failed - check API key")
    elif response.status_code == 403:
        print("Forbidden - API key lacks permissions")
    elif response.status_code == 404:
        print("Library not found")
    elif response.status_code == 429:
        print("Rate limit exceeded - wait before retrying")
    else:
        print(f"Error: {response.status_code} - {response.text}")
        
except httpx.ConnectError:
    print("Cannot connect to Context7 API")
except httpx.TimeoutException:
    print("Request timed out")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Rate Limits

- Check response headers for rate limit information
- Implement exponential backoff for retries
- Cache responses to minimize API calls

---

## See Also

- [API Key Management Guide](CONTEXT7_API_KEY_MANAGEMENT.md) - Complete guide for managing API keys
- [Cache Optimization Guide](CONTEXT7_CACHE_OPTIMIZATION.md) - Optimizing cache performance
- [Security & Privacy Guide](CONTEXT7_SECURITY_PRIVACY.md) - Security best practices

---

## Official Context7 Documentation

For the most up-to-date API documentation, visit:
- Context7 Dashboard: https://context7.com/dashboard
- API Documentation: Available in the Context7 dashboard

