# Context7 Integration Architecture

## How Context7 Integration Works (Without Direct API Key Usage)

### Overview

**Key Finding**: This codebase does **NOT** directly call the Context7 API. Instead, it uses **MCP (Model Context Protocol)** to delegate API calls to an external MCP Context7 server.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TappsCodingAgents                         │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Context7MCPServer (tapps_agents/mcp/servers/)       │   │
│  │  - Registers MCP tools                                │   │
│  │  - Delegates to client functions                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                      │
│                        │ calls                                │
│                        ▼                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  resolve_library_client()  (external function)       │   │
│  │  get_docs_client()         (external function)       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ MCP Protocol
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         External MCP Context7 Server                         │
│  (Configured via Cursor/Claude Desktop MCP settings)        │
│                                                               │
│  - Handles CONTEXT7_API_KEY authentication                   │
│  - Makes actual HTTP requests to Context7 API                │
│  - Returns documentation data                                │
└─────────────────────────────────────────────────────────────┘
```

### How It Works

#### 1. **MCP-Based Architecture**

The `Context7MCPServer` class (`tapps_agents/mcp/servers/context7.py`) is a **wrapper** that:
- Registers MCP tools (`mcp_Context7_resolve-library-id`, `mcp_Context7_get-library-docs`)
- Accepts **client functions** as parameters (`resolve_library_client`, `get_docs_client`)
- Delegates actual API calls to these external functions

```python
class Context7MCPServer:
    def __init__(
        self,
        registry: ToolRegistry | None = None,
        resolve_library_client: Callable[[str], Any] | None = None,  # External!
        get_docs_client: Callable[[str, str | None, ...], Any] | None = None,  # External!
    ):
        self.resolve_library_client = resolve_library_client
        self.get_docs_client = get_docs_client
```

#### 2. **No Direct API Calls**

When you look at the code:

```python
# In resolve_library_id():
if self.resolve_library_client:
    result = self.resolve_library_client(libraryName)  # Delegates to external function
else:
    return {"error": "Context7 MCP client not configured"}  # No client = no API call
```

**The codebase never makes HTTP requests to Context7 API directly.**

#### 3. **Where API Key Would Be Used**

The API key (`CONTEXT7_API_KEY`) would be used by:
- **External MCP Context7 Server** (configured in Cursor/Claude Desktop)
- The MCP server would read the environment variable and include it in HTTP requests
- This codebase never sees or uses the API key directly

#### 4. **KB-First Caching Strategy**

The integration uses a **KB-first** (Knowledge Base first) strategy:

```python
# In KBLookup.lookup():
# Step 1: Check KB cache (exact match) - NO API CALL
cached_entry = self.kb_cache.get(library, topic)
if cached_entry:
    return LookupResult(success=True, content=cached_entry.content, source="cache")

# Step 2: Fuzzy matching (if enabled) - NO API CALL
if use_fuzzy_match:
    # Try fuzzy match in cache
    ...

# Step 3: Resolve library ID - MAY CALL API (via MCP)
if self.mcp_gateway:
    resolve_result = self.mcp_gateway.call_tool("mcp_Context7_resolve-library-id", ...)

# Step 4: Fetch from Context7 API - MAY CALL API (via MCP)
if self.mcp_gateway:
    api_result = self.mcp_gateway.call_tool("mcp_Context7_get-library-docs", ...)
```

**Most operations work from cache without any API calls!**

### Why It Works Without API Key

#### 1. **Cache-First Design**
- Once documentation is cached, no API calls are needed
- The system can work entirely offline after initial population
- Cache is stored in `.tapps-agents/knowledge/` directory

#### 2. **Optional MCP Integration**
- If MCP Context7 server is not configured, tools return errors but don't crash
- The system gracefully degrades to cache-only mode
- No API key is required for cache operations

#### 3. **External MCP Server Handles Auth**
- The actual Context7 API authentication happens in the external MCP server
- This codebase just passes through the requests
- API key is read by the MCP server, not this codebase

### Code Evidence

#### Evidence 1: Client Functions Are Optional

```python
# tapps_agents/mcp/servers/context7.py:107-129
def resolve_library_id(self, libraryName: str) -> dict[str, Any]:
    if self.resolve_library_client:  # Only calls if client provided
        try:
            result = self.resolve_library_client(libraryName)
            ...
        except Exception as e:
            return {"error": str(e)}
    else:
        # No client = no API call, just return error
        return {
            "library": libraryName,
            "matches": [],
            "error": "Context7 MCP client not configured",
        }
```

#### Evidence 2: MCP Gateway Delegation

```python
# tapps_agents/context7/lookup.py:172-184
# Try MCP Gateway first
if self.mcp_gateway:
    try:
        resolve_result = self.mcp_gateway.call_tool(
            "mcp_Context7_resolve-library-id", libraryName=library
        )
        # MCP Gateway calls the registered tool handler
        # Which calls the external client function
        # Which makes the actual HTTP request
```

#### Evidence 3: No HTTP Client in Codebase

Searching the codebase shows:
- ✅ No `httpx` or `requests` calls to Context7 API
- ✅ No API key usage in HTTP headers
- ✅ Only MCP tool calls and cache operations

### API Key Documentation vs. Reality

#### What Documentation Says

The documentation (`docs/CONTEXT7_API_KEY_MANAGEMENT.md`) mentions:
- `CONTEXT7_API_KEY` environment variable
- API key storage and management
- How to set up API keys

#### What Actually Happens

1. **This codebase** checks for `CONTEXT7_API_KEY` in security audits but doesn't use it
2. **External MCP server** would read `CONTEXT7_API_KEY` and use it for authentication
3. **Cache operations** don't require API keys at all

### How to Actually Use Context7 API

To make actual Context7 API calls, you need:

1. **External MCP Context7 Server** configured (e.g., in Cursor MCP settings)
2. **API Key** set in environment: `export CONTEXT7_API_KEY="your-key"`
3. **MCP Gateway** initialized with the Context7 server
4. **Client functions** passed to `Context7MCPServer`

Example setup (pseudo-code, not in this codebase):

```python
# This would be in external MCP server configuration
def resolve_library_client(library_name: str):
    api_key = os.getenv("CONTEXT7_API_KEY")
    response = httpx.get(
        "https://api.context7.com/resolve",
        headers={"Authorization": f"Bearer {api_key}"},
        params={"library": library_name}
    )
    return response.json()

# Then pass to Context7MCPServer
server = Context7MCPServer(
    resolve_library_client=resolve_library_client,
    get_docs_client=get_docs_client
)
```

### Current State

**Without MCP Server Configured:**
- ✅ Cache operations work (read/write cached docs)
- ✅ KB-first lookup works (from cache)
- ✅ Fuzzy matching works (from cache)
- ❌ API calls fail with "Context7 MCP client not configured"
- ❌ No new documentation fetched from API

**With MCP Server Configured:**
- ✅ All cache operations work
- ✅ API calls work (via MCP server)
- ✅ New documentation can be fetched
- ✅ API key handled by external MCP server

### Conclusion

**You're calling Context7 without an API key because:**

1. **This codebase doesn't make direct API calls** - it delegates to MCP
2. **Most operations use cache** - no API calls needed
3. **API key would be used by external MCP server** - not this codebase
4. **System gracefully handles missing MCP server** - works cache-only

The `CONTEXT7_API_KEY` environment variable is documented but would only be used by an external MCP Context7 server implementation, not by this codebase directly.

