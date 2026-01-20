---
title: Context7 Integration Patterns
version: 1.0.0
status: active
last_updated: 2026-01-20
tags: [context7, integration, patterns, best-practices]
---

# Context7 Integration Patterns

This document describes best practices and patterns for using Context7 in TappsCodingAgents.

## Overview

Context7 provides real-time library documentation through MCP (Model Context Protocol). TappsCodingAgents integrates Context7 via MCP Gateway for library documentation lookup.

## Integration Architecture

### MCP-Based Integration

**Key Principle**: TappsCodingAgents does **NOT** directly call the Context7 API. Instead, it uses MCP to delegate API calls to an external MCP Context7 server.

**Architecture:**
```
TappsCodingAgents
  └── MCP Gateway
      └── Context7MCPServer
          └── MCP Protocol
              └── External MCP Context7 Server
                  └── Context7 API
```

**Benefits:**
- No API keys required in framework code
- Uses developer's configured MCP server
- Consistent with Cursor-first architecture
- Graceful degradation when Context7 unavailable

## Library ID Resolution

### Resolution Pattern

**Step 1: Resolve Library Name to Context7 ID**

```python
# Use MCP tool to resolve library name
result = mcp_gateway.call_tool(
    "mcp_Context7_resolve-library-id",
    libraryName="fastapi"
)

# Response contains list of matching libraries
# {
#   "library": "fastapi",
#   "matches": [
#     {"id": "/tiangolo/fastapi", "name": "FastAPI", "score": 1.0}
#   ]
# }
```

**Step 2: Use Resolved ID for Documentation**

```python
# Use resolved ID to get documentation
docs = mcp_gateway.call_tool(
    "mcp_Context7_get-library-docs",
    context7CompatibleLibraryID="/tiangolo/fastapi",
    topic="routing",
    mode="code"
)
```

### Library ID Conventions

**Format**: `/owner/repo`

**Common Libraries:**
- `react` → `/facebook/react`
- `fastapi` → `/tiangolo/fastapi`
- `pytest` → `/pytest-dev/pytest`
- `next.js` → `/vercel/next.js`

**Resolution Strategy:**
1. Try exact match first
2. Use fuzzy matching for variations
3. Return best match with confidence score

## Cache Management

### KB-First Caching

**Strategy**: Check local knowledge base cache before external API calls

**Cache Location**: `.tapps-agents/kb/context7-cache/`

**Cache Structure:**
```
.tapps-agents/kb/context7-cache/
├── libraries/
│   ├── react/
│   │   ├── metadata.json
│   │   └── docs.json
│   └── fastapi/
│       ├── metadata.json
│       └── docs.json
└── index.json
```

### Cache Patterns

**Pattern 1: Cache Hit (Fast Path)**
```python
# 1. Check cache first
cached_docs = cache.get(library_id, topic)
if cached_docs and not cache.is_stale(cached_docs):
    return cached_docs  # Fast path - no API call

# 2. Cache miss - fetch from Context7
docs = fetch_from_context7(library_id, topic)

# 3. Store in cache
cache.set(library_id, topic, docs)
return docs
```

**Pattern 2: Cache Pre-warming**
```python
# Pre-warm cache during init
prewarmer = CachePrewarmer()
prewarmer.prewarm_dependencies(project_root)
```

**Pattern 3: Staleness Handling**
```python
if cache.is_stale(cached_docs, max_age_days=30):
    # Refresh in background
    refresh_queue.add(library_id, topic)
    # Return stale data immediately (don't block)
    return cached_docs
```

### 2025 Performance Enhancements

**Async LRU Cache** (`tapps_agents/context7/async_cache.py`):
- Thread-safe in-memory cache with O(1) operations
- Background write queue for non-blocking disk persistence
- Atomic file rename pattern (no file locking needed)

**Circuit Breaker** (`tapps_agents/context7/circuit_breaker.py`):
- CLOSED → OPEN → HALF_OPEN state machine
- Bounded concurrency (default: 5) with fail-fast
- Auto-recovery after configurable timeout (default: 30s)

**Cache Pre-warming** (`tapps_agents/context7/cache_prewarm.py`):
- Automatic dependency detection from requirements.txt, pyproject.toml
- Background pre-warming with priority ordering
- Expert library prioritization (fastapi, pytest, react, etc.)

## Best Practices

### 1. Always Specify Topics

**Good:**
```python
docs = get_library_docs("fastapi", topic="routing")
```

**Avoid:**
```python
docs = get_library_docs("fastapi")  # Returns entire library docs
```

**Why**: Topics limit scope and reduce token usage

### 2. Use KB-First Strategy

**Always check cache first:**
```python
# Check cache before API call
cached = kb_cache.get(library_id, topic)
if cached:
    return cached

# Only call API if cache miss
return fetch_from_context7(library_id, topic)
```

### 3. Handle Errors Gracefully

**Pattern:**
```python
try:
    docs = get_library_docs(library_id, topic)
except Context7UnavailableError:
    # Fallback to local knowledge or cached docs
    return get_cached_docs(library_id, topic) or get_local_knowledge(topic)
except LibraryNotFoundError:
    # Suggest similar libraries or return empty
    return suggest_similar_libraries(library_id)
```

### 4. Optimize Token Usage

**Strategies:**
- Use specific topics to limit scope
- Cache results to avoid repeated calls
- Use pagination for large documentation sets
- Set appropriate token limits per agent

**Agent-Specific Limits:**
- Architect: 4000 tokens (architecture, design-patterns, scalability)
- Implementer: 3000 tokens (hooks, routing, authentication, testing)
- Tester: 2500 tokens (testing, security, performance)

## Performance Optimization

### Cache Hit Rate Targets

**Target**: >80% cache hit rate

**Monitoring:**
```python
from tapps_agents.context7.analytics import CacheStats

stats = CacheStats()
print(f"Hit rate: {stats.hit_rate:.2%}")
print(f"Avg response time: {stats.avg_response_time:.2f}ms")
```

### Response Time Targets

**Cache Hits**: <100ms  
**Cache Misses**: <2s (including API call)

### Optimization Tips

1. **Pre-warm Cache**: Run `tapps-agents init` to pre-populate cache
2. **Use Specific Topics**: Narrow scope reduces response time
3. **Enable Circuit Breaker**: Prevents cascading failures
4. **Monitor Cache Stats**: Track hit rates and adjust strategy

## Error Handling Patterns

### Common Errors

**Library Not Found:**
```python
try:
    docs = get_library_docs("nonexistent-library")
except LibraryNotFoundError as e:
    # Suggest similar libraries
    suggestions = suggest_similar_libraries("nonexistent-library")
    logger.warning(f"Library not found. Suggestions: {suggestions}")
```

**Context7 Unavailable:**
```python
try:
    docs = get_library_docs(library_id, topic)
except Context7UnavailableError:
    # Fallback to cached docs or local knowledge
    cached = get_cached_docs(library_id, topic)
    if cached:
        return cached
    return get_local_knowledge(topic)
```

**Token Limit Exceeded:**
```python
try:
    docs = get_library_docs(library_id, topic, token_limit=3000)
except TokenLimitExceededError:
    # Suggest smaller topic scope
    return suggest_narrower_topic(topic)
```

## Integration Examples

### Agent Integration

**Reviewer Agent:**
```python
# Get library docs for code review
docs = mcp_gateway.call_tool(
    "mcp_Context7_get-library-docs",
    context7CompatibleLibraryID="/tiangolo/fastapi",
    topic="routing",
    mode="code"
)

# Use docs in review feedback
review_feedback = f"According to FastAPI docs: {docs['summary']}"
```

**Implementer Agent:**
```python
# Get library docs for code generation
docs = mcp_gateway.call_tool(
    "mcp_Context7_get-library-docs",
    context7CompatibleLibraryID="/facebook/react",
    topic="hooks",
    mode="code"
)

# Use docs in code generation
code = generate_code_with_docs(docs)
```

## Related Documentation

- **MCP Standards**: `docs/MCP_STANDARDS.md`
- **Context7 Cache Optimization**: `docs/context7/CONTEXT7_CACHE_OPTIMIZATION.md` (if exists)
- **Architecture Overview**: `docs/ARCHITECTURE.md`
- **Performance Guide**: `docs/architecture/performance-guide.md`

---

**Last Updated**: 2026-01-20  
**Maintained By**: TappsCodingAgents Team
