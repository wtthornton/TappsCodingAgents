# Phase 5: Context7 Integration - Implementation Plan

**Status:** 🚧 In Progress  
**Started:** December 2025  
**Estimated Duration:** 6-9 weeks (3 phases)

## Overview

Context7 integration provides real-time, version-specific library documentation with intelligent caching, reducing API calls by 87%+ and ensuring agents always have access to current best practices.

### Key Benefits
- **87%+ API Call Reduction** - KB-first caching minimizes external API usage
- **<0.15s Response Time** - Cached content responds in milliseconds
- **Version-Specific Docs** - Always current, eliminates outdated references
- **Reduced Hallucinations** - Accurate API references from official sources
- **Cost Efficiency** - Fewer API calls = lower costs

---

## Phase 1: Core Integration (2-3 weeks)

### Deliverables

#### 1.1 KB Cache Structure (`tapps_agents/context7/`)
- `kb_cache.py` - Main KB cache manager class
- `cache_structure.py` - Cache directory structure management
- `metadata.py` - Metadata file management (meta.yaml, index.yaml)

**Files to Create:**
- `tapps_agents/context7/__init__.py`
- `tapps_agents/context7/kb_cache.py`
- `tapps_agents/context7/cache_structure.py`
- `tapps_agents/context7/metadata.py`

#### 1.2 MCP Context7 Tool Integration (`tapps_agents/mcp/servers/`)
- `context7.py` - MCP server for Context7 tools
- Integration with existing MCP Gateway

**Files to Create:**
- `tapps_agents/mcp/servers/context7.py`

**Tools to Implement:**
- `mcp_Context7_resolve-library-id` - Resolve library name to Context7 ID
- `mcp_Context7_get-library-docs` - Fetch library documentation

#### 1.3 KB-First Lookup Workflow (`tapps_agents/context7/`)
- `lookup.py` - KB-first lookup logic
- Cache hit/miss handling
- Context7 API fallback

**Files to Create:**
- `tapps_agents/context7/lookup.py`

#### 1.4 Configuration Schema Updates
- Add Context7 config to `tapps_agents/core/config.py`
- Support for KB cache settings

**Files to Modify:**
- `tapps_agents/core/config.py`

### Success Criteria
- ✅ KB cache structure created and managed
- ✅ MCP Context7 tools integrated via MCP Gateway
- ✅ KB-first lookup workflow functional
- ✅ Basic caching working (store/retrieve)
- ✅ Metadata files (meta.yaml, index.yaml) updated on cache operations

### Tests
- Unit tests for KB cache operations
- Unit tests for MCP Context7 tools
- Integration tests for KB-first lookup workflow

---

## Phase 2: Intelligence Layer (2-3 weeks)

### Deliverables

#### 2.1 Fuzzy Matching (`tapps_agents/context7/`)
- `fuzzy_matcher.py` - Fuzzy matching with 0.7 confidence threshold
- Topic similarity matching
- Cross-reference lookup preparation

**Files to Create:**
- `tapps_agents/context7/fuzzy_matcher.py`

#### 2.2 Auto-Refresh System (`tapps_agents/context7/`)
- `refresh_queue.py` - Staleness detection and refresh queue
- `staleness_policies.py` - Library-specific staleness policies
- Queue management (file-based)

**Files to Create:**
- `tapps_agents/context7/refresh_queue.py`
- `tapps_agents/context7/staleness_policies.py`

#### 2.3 Performance Analytics (`tapps_agents/context7/`)
- `analytics.py` - Metrics tracking and reporting
- Hit rate calculation
- Cache statistics

**Files to Create:**
- `tapps_agents/context7/analytics.py`

#### 2.4 Commands (`tapps_agents/context7/commands.py`)
- `*context7-kb-status` - Show KB statistics
- `*context7-kb-refresh` - Refresh stale entries
- `*context7-kb-search` - Search local KB
- `*context7-kb-process-queue` - Process refresh queue

**Files to Create:**
- `tapps_agents/context7/commands.py`

### Success Criteria
- ✅ Fuzzy matching with 0.7 threshold functional
- ✅ Staleness detection working (30/14/7 day policies)
- ✅ Refresh queue functional (file-based)
- ✅ Analytics dashboard complete
- ✅ Hit rate >70% in tests
- ✅ All Context7 commands working

### Tests
- Unit tests for fuzzy matching
- Unit tests for staleness detection
- Unit tests for refresh queue
- Unit tests for analytics
- Integration tests for commands

---

## Phase 3: Advanced Features (2-3 weeks)

### Deliverables

#### 3.1 Cross-References System (`tapps_agents/context7/`)
- `cross_references.py` - Topic-based cross-referencing
- Cross-reference index management

**Files to Create:**
- `tapps_agents/context7/cross_references.py`

#### 3.2 KB Cleanup Automation (`tapps_agents/context7/`)
- `cleanup.py` - Automated cleanup of old/unused entries
- Size-based cleanup (max 100MB)
- LRU-based eviction

**Files to Create:**
- `tapps_agents/context7/cleanup.py`

#### 3.3 Agent Integration
- Integrate Context7 with Architect agent
- Integrate Context7 with Implementer agent
- Integrate Context7 with Tester agent
- Auto-triggers for library/framework mentions

**Files to Modify:**
- `tapps_agents/agents/architect/agent.py`
- `tapps_agents/agents/implementer/agent.py`
- `tapps_agents/agents/tester/agent.py`

#### 3.4 Additional Commands
- `*context7-docs {library} {topic}` - Get KB-first documentation
- `*context7-resolve {library}` - Resolve library to Context7 ID
- `*context7-kb-cleanup` - Clean up old entries
- `*context7-kb-rebuild` - Rebuild index
- `*context7-help` - Show usage examples

**Files to Modify:**
- `tapps_agents/context7/commands.py`

### Success Criteria
- ✅ Cross-references functional
- ✅ Automated cleanup working
- ✅ Agent integration complete
- ✅ All commands implemented
- ✅ Seamless integration with existing RAG

### Tests
- Unit tests for cross-references
- Unit tests for cleanup
- Integration tests for agent Context7 usage
- End-to-end tests for full workflow

---

## File Structure

```
tapps_agents/
├── context7/
│   ├── __init__.py
│   ├── kb_cache.py              # Main KB cache manager
│   ├── cache_structure.py       # Directory structure management
│   ├── metadata.py              # Metadata file management
│   ├── lookup.py                # KB-first lookup workflow
│   ├── fuzzy_matcher.py         # Fuzzy matching (Phase 2)
│   ├── refresh_queue.py         # Auto-refresh system (Phase 2)
│   ├── staleness_policies.py    # Staleness policies (Phase 2)
│   ├── analytics.py             # Performance analytics (Phase 2)
│   ├── cross_references.py      # Cross-references (Phase 3)
│   ├── cleanup.py               # KB cleanup (Phase 3)
│   └── commands.py              # Context7 commands
│
├── mcp/
│   └── servers/
│       └── context7.py          # MCP Context7 server
│
└── core/
    └── config.py                # Updated with Context7 config
```

## Cache Directory Structure

```
.tapps-agents/kb/context7-cache/
├── index.yaml                    # Master index
├── cross-references.yaml         # Topic cross-references (Phase 3)
├── .refresh-queue               # Refresh queue (Phase 2)
│
├── libraries/
│   ├── react/
│   │   ├── meta.yaml            # Library metadata
│   │   ├── hooks.md             # Cached docs
│   │   └── components.md
│   └── fastapi/
│       ├── meta.yaml
│       └── authentication.md
│
└── topics/                       # Topic cross-references (Phase 3)
    ├── hooks/
    │   └── index.yaml
    └── routing/
        └── index.yaml
```

---

## Testing Strategy

### Phase 1 Tests
- `tests/unit/context7/test_kb_cache.py`
- `tests/unit/context7/test_cache_structure.py`
- `tests/unit/context7/test_metadata.py`
- `tests/unit/context7/test_lookup.py`
- `tests/unit/mcp/test_context7_server.py`

### Phase 2 Tests
- `tests/unit/context7/test_fuzzy_matcher.py`
- `tests/unit/context7/test_refresh_queue.py`
- `tests/unit/context7/test_staleness_policies.py`
- `tests/unit/context7/test_analytics.py`
- `tests/unit/context7/test_commands.py`

### Phase 3 Tests
- `tests/unit/context7/test_cross_references.py`
- `tests/unit/context7/test_cleanup.py`
- `tests/integration/test_context7_agent_integration.py`

---

## Progress Tracking

### Phase 1: Core Integration
- [ ] KB cache structure
- [ ] MCP Context7 tools
- [ ] KB-first lookup
- [ ] Metadata tracking
- [ ] Configuration schema
- [ ] Phase 1 tests

### Phase 2: Intelligence Layer
- [ ] Fuzzy matching
- [ ] Auto-refresh system
- [ ] Performance analytics
- [ ] Commands implementation
- [ ] Phase 2 tests

### Phase 3: Advanced Features
- [ ] Cross-references
- [ ] KB cleanup
- [ ] Agent integration
- [ ] Additional commands
- [ ] Phase 3 tests

---

## Dependencies

- Existing MCP Gateway infrastructure
- Existing BaseAgent for agent integration
- Pydantic for configuration validation
- PyYAML for metadata file management
- MCP Context7 server (external dependency via MCP)

---

## Notes

- MCP Context7 tools require external MCP server setup (configured via Cursor/Claude Desktop)
- KB cache uses file-based storage (simple, no DB required)
- All operations are async where appropriate
- Configuration is optional (graceful degradation if not enabled)

