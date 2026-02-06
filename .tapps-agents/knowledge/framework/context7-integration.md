# Context7 Integration Guide

## Architecture

Context7 provides library documentation via MCP (Model Context Protocol). TappsCodingAgents integrates at 3 levels:

1. **External MCP Server** — `@anthropic/context7-mcp` fetches live documentation
2. **Python SDK Wrapper** — `context7/` package: `MCPGateway`, `KBCache`, `FuzzyMatcher`, `LibraryDetector`
3. **Agent Helper** — `Context7AgentHelper` provides high-level API for agents

## Components

| Component | File | Purpose |
|-----------|------|---------|
| `MCPGateway` | `context7/mcp_gateway.py` | MCP protocol client |
| `KBCache` | `context7/kb_cache.py` | Local JSON/markdown cache |
| `FuzzyMatcher` | `context7/fuzzy_matcher.py` | Library name resolution |
| `LibraryDetector` | `context7/library_detector.py` | Auto-detect project dependencies |
| `Context7AgentHelper` | `context7/agent_integration.py` | Agent-facing API |
| `TopicPrePopulator` | `context7/topic_prepopulator.py` | Async cache warming |

## Cache Structure

The canonical KB cache root is `.tapps-agents/kb/context7-cache` (see `context7/cache_structure.py`, `agent_integration.py`). Layout:

```
.tapps-agents/kb/context7-cache/
  libraries/<library>/<topic>.md    # Per-library, per-topic markdown
  index.yaml                        # Cache index
  .refresh-queue                     # Staleness refresh queue
```

Legacy or alternate paths (e.g. `.tapps-agents/context7-docs/`) may exist in config; the code uses `context7_config.knowledge_base.location` defaulting to `.tapps-agents/kb/context7-cache`.

## Known Issues (2026-02)

### 1. Fuzzy Match Misresolutions
6+ libraries resolve to wrong IDs. Example: `pyyaml` → wrong Context7 library.
**Fix:** Add verification step — check resolved library's language matches project.

### 2. No Cache TTL / Staleness Detection
Cache entries never expire. Stale documentation persists indefinitely.
**Fix:** Add `fetched_at` timestamp to `CacheEntry`; TTL of 7-30 days configurable.

### 3. Race Condition in Global Cache Init
Multiple concurrent `_ensure_cache()` calls can corrupt the singleton.
**Fix:** Use `asyncio.Lock()` for cache initialization.

### 4. Silent Write Failures
`KBCache.write()` catches all exceptions and logs debug — data loss is silent.
**Fix:** Return success/failure status; raise for critical writes.

### 5. No Cache Size Monitoring
Unbounded cache growth with no pruning.
**Fix:** Add LRU eviction policy; configurable max cache entries.

## Reviewer Agent: Context7 Cache and RAG Best Practices

The Reviewer uses Context7 for library-documentation retrieval (RAG): docs are retrieved and injected into review context. The following align with Context7’s official workflow and API guide.

### Required workflow order

1. **resolve-library-id** — Resolve library name to a Context7-compatible library ID (e.g. `/vercel/next.js`, `/supabase/supabase`). This step is mandatory before fetching docs.
2. **get-library-docs** — Fetch documentation using the resolved ID. Use the `topic` parameter to focus results (e.g. `best-practices`, `routing`, `hooks`).

Implementation: `context7/lookup.py` implements KB-first lookup: (1) check KB cache, (2) fuzzy match on cache, (3) resolve library ID via MCP/HTTP, (4) get-library-docs, (5) store in cache. The Reviewer’s `Context7ReviewEnhancer` calls `Context7AgentHelper.get_documentation(library, topic, use_fuzzy_match=True)`, which uses this flow.

### Best practices (from Context7 API guide)

- **Cache responses** — All fetched documentation is stored in `.tapps-agents/kb/context7-cache` to reduce redundant API calls.
- **Be specific with queries** — Use the `topic` parameter when calling get-library-docs (e.g. `best-practices`, `common-mistakes`, `usage`, `examples`) for better relevance.
- **Handle rate limits** — Quota and rate-limit handling are implemented in `context7/backup_client.py` and circuit breaker; avoid duplicate lookups in tight loops.
- **Use specific versions** — When a library version matters, use versioned library IDs (e.g. `/vercel/next.js/v15.1.0`) when supported by Context7.

### Reviewer-specific behavior

- **Context7ReviewEnhancer** (`agents/reviewer/context7_enhancer.py`) requests docs for multiple topics per library: `best-practices`, `common-mistakes`, `usage`, `examples`, then falls back to general docs. Results are cached in-memory per run and persisted via the shared KB cache.
- **CLI/Skill** — `@reviewer *docs <library> [topic]` and CLI equivalent use the same KB-first lookup; when running in Cursor, the AI can also call MCP tools `resolve-library-id` and `get-library-docs` directly for ad-hoc lookups.

## Recommendations

1. **Add resolution verification** — match resolved library language to project tech stack
2. **Implement cache TTL** — configurable staleness window (default 14 days)
3. **Add cache metrics** — hit rate, miss rate, stale rate for `health overview`
4. **Thread-safe initialization** — use `asyncio.Lock()` for `_ensure_cache()`
5. **Structured error codes** — replace string errors with enum-based error types
6. **Deduplicate MCP config** — single source of truth for MCP server settings
7. **Usage analytics** — track most-queried topics for pre-population optimization

## Configuration

```yaml
context7:
  enabled: true
  max_results: 5
  timeout: 30
  cache_dir: ".tapps-agents/context7-docs"
  cache_ttl_days: 14        # Recommended addition
  max_cache_entries: 500     # Recommended addition
  auto_fetch: true
```
