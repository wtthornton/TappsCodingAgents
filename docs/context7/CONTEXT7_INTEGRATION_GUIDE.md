# Context7 Integration Guide for TappsCodingAgents

## Overview

TappsCodingAgents integrates with Context7 MCP server to provide up-to-date library documentation lookup capabilities. This integration enables agents to automatically fetch current documentation for libraries, frameworks, and tools during code generation, review, and implementation.

## Architecture

### Context7 Flow in TappsCodingAgents

```
┌─────────────────────────────────────────────────────────────┐
│                    TappsCodingAgents                         │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Agent (Reviewer, Implementer, etc.)                 │   │
│  │  - Detects library usage                              │   │
│  │  - Requests documentation                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                      │
│                        ▼                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Context7AgentHelper                                  │   │
│  │  - KB-first lookup strategy                           │   │
│  │  - Cache management                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                      │
│                        ▼                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  KBLookup                                             │   │
│  │  1. Check KB cache first                              │   │
│  │  2. Fuzzy match if cache miss                         │   │
│  │  3. Query Context7 MCP if needed                      │   │
│  │  4. Cache result for future use                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                      │
│                        ▼                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MCPGateway                                           │   │
│  │  - resolve-library-id                                │   │
│  │  - get-library-docs                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                      │
│                        ▼                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Context7 MCP Server                                  │   │
│  │  - Library documentation                              │   │
│  │  - Code examples                                      │   │
│  │  - API references                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### KB-First Caching Strategy

TappsCodingAgents uses a **KB-first caching strategy** to minimize API calls and improve performance:

1. **Cache Check**: First checks local KB cache (`.tapps-agents/kb/context7-cache/`)
2. **Fuzzy Matching**: If exact match not found, attempts fuzzy topic matching
3. **MCP Query**: Only queries Context7 MCP if cache miss
4. **Cache Update**: Stores result in cache for future use

**Benefits**:
- ✅ 90%+ token savings on repeated queries
- ✅ Sub-second response times for cached queries
- ✅ Offline capability for cached libraries
- ✅ Automatic cache refresh based on staleness policies

## Configuration

### Enable Context7 Integration

Context7 is enabled by default. Configuration is in `.tapps-agents/config.yaml`:

```yaml
context7:
  enabled: true
  knowledge_base:
    location: ".tapps-agents/kb/context7-cache"
    auto_refresh: true
  mcp:
    server_name: "Context7"
    enabled: true
```

### MCP Server Setup

Context7 integration requires the Context7 MCP server to be configured in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "Context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"]
    }
  }
}
```

## Usage Examples

### CLI Usage

#### Basic Library Documentation Lookup

```bash
# Look up FastAPI documentation
python -m tapps_agents.cli reviewer docs fastapi

# Look up specific topic
python -m tapps_agents.cli reviewer docs fastapi routing

# Look up with code mode (includes code examples)
python -m tapps_agents.cli reviewer docs fastapi routing --mode code
```

#### In Cursor Chat

```cursor
# Basic lookup
@reviewer *docs fastapi

# Topic-specific query
@reviewer *docs fastapi routing

# Implementer agent also supports Context7
@implementer *docs pytest fixtures
```

### Python API Usage

#### Using Context7AgentHelper

```python
from pathlib import Path
from tapps_agents.core.config import ProjectConfig
from tapps_agents.context7.agent_integration import Context7AgentHelper

# Initialize helper
config = ProjectConfig.load()
helper = Context7AgentHelper(config=config, project_root=Path.cwd())

# Look up library documentation
result = await helper.lookup_docs(
    library="fastapi",
    topic="routing"
)

if result.success:
    print(f"Documentation: {result.content}")
    print(f"Source: {result.source}")  # "cache" or "api"
    print(f"Response time: {result.response_time_ms}ms")
else:
    print(f"Error: {result.error}")
```

#### Using KBLookup Directly

```python
from tapps_agents.context7.lookup import KBLookup
from tapps_agents.context7.kb_cache import KBCache
from tapps_agents.context7.metadata import MetadataManager
from tapps_agents.context7.cache_structure import CacheStructure

# Initialize components
cache_root = Path(".tapps-agents/kb/context7-cache")
cache_structure = CacheStructure(cache_root)
cache_structure.initialize()

metadata_manager = MetadataManager(cache_structure)
kb_cache = KBCache(cache_structure.cache_root, metadata_manager)

# Create lookup instance
lookup = KBLookup(
    kb_cache=kb_cache,
    mcp_gateway=mcp_gateway,  # Optional MCPGateway instance
    fuzzy_threshold=0.7
)

# Perform lookup
result = await lookup.lookup(
    library="pytest",
    topic="fixtures"
)

if result.success:
    print(f"Found: {result.content[:200]}...")
    print(f"Matched topic: {result.matched_topic}")
    print(f"Fuzzy score: {result.fuzzy_score}")
```

### Agent Integration Examples

#### Reviewer Agent Automatic Context7 Usage

The Reviewer agent automatically uses Context7 when reviewing code that uses libraries:

```python
# When reviewing code like this:
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

# Reviewer agent automatically:
# 1. Detects FastAPI usage
# 2. Looks up FastAPI best practices via Context7
# 3. Includes documentation in review feedback
```

#### Implementer Agent Context7 Integration

The Implementer agent uses Context7 to ensure code follows current library patterns:

```python
# User request: "Create a FastAPI endpoint for user authentication"

# Implementer agent:
# 1. Detects FastAPI requirement
# 2. Queries Context7 for FastAPI authentication patterns
# 3. Generates code using current FastAPI best practices
# 4. Includes proper imports and patterns from Context7 docs
```

#### Error Message Library Detection

The Debugger agent can detect libraries from error messages:

```python
# Error: "ImportError: No module named 'pydantic'"

# Debugger agent:
# 1. Detects "pydantic" in error message
# 2. Queries Context7 for Pydantic installation/usage
# 3. Provides solution with current Pydantic patterns
```

## Cache Management

### Cache Structure

Context7 cache is stored in `.tapps-agents/kb/context7-cache/`:

```
.tapps-agents/kb/context7-cache/
├── libraries/
│   ├── fastapi/
│   │   ├── general.json
│   │   ├── routing.json
│   │   └── metadata.json
│   └── pytest/
│       ├── fixtures.json
│       └── metadata.json
├── metadata.json
└── refresh_queue.json
```

### Cache Operations

#### Pre-populate Cache

```bash
# Pre-populate cache with common libraries
python -m tapps_agents.cli context7 prepopulate

# Pre-populate specific libraries
python -m tapps_agents.cli context7 prepopulate --libraries fastapi pytest pydantic
```

#### Check Cache Status

```bash
# Check cache health
python -m tapps_agents.cli health check context7-cache

# View cache analytics
python -m tapps_agents.cli context7 analytics
```

#### Refresh Stale Cache

```bash
# Refresh stale entries
python -m tapps_agents.cli context7 refresh

# Refresh specific library
python -m tapps_agents.cli context7 refresh --library fastapi
```

## Best Practices

### When to Use Context7

✅ **Use Context7 for**:
- Library API documentation
- Framework-specific patterns
- Current best practices
- Version-specific features
- Code examples and snippets

❌ **Don't use Context7 for**:
- Project-specific business logic
- Custom domain knowledge
- Internal APIs
- Proprietary libraries

### Performance Optimization

1. **Pre-populate Common Libraries**: Cache frequently used libraries during setup
2. **Use Topic-Specific Queries**: Narrow queries to specific topics for faster results
3. **Monitor Cache Hit Rate**: Aim for >80% cache hit rate
4. **Refresh Strategically**: Only refresh when libraries update

### Error Handling

```python
try:
    result = await helper.lookup_docs(library="fastapi", topic="routing")
    if not result.success:
        # Fallback to local documentation or skip
        logger.warning(f"Context7 lookup failed: {result.error}")
        # Continue without Context7 enhancement
except Exception as e:
    logger.error(f"Context7 error: {e}")
    # Graceful degradation - continue without Context7
```

## Troubleshooting

### Common Issues

#### Issue: "Context7 not available"

**Solution**: Check MCP server configuration in `.cursor/mcp.json`

```bash
# Verify MCP server is running
python -m tapps_agents.cli doctor
```

#### Issue: "Cache miss rate too high"

**Solution**: Pre-populate cache with common libraries

```bash
python -m tapps_agents.cli context7 prepopulate
```

#### Issue: "Slow response times"

**Solution**: Check cache health and refresh stale entries

```bash
python -m tapps_agents.cli context7 refresh
python -m tapps_agents.cli health check context7-cache
```

### Debug Mode

Enable debug logging for Context7:

```yaml
# .tapps-agents/config.yaml
logging:
  level: DEBUG
  context7: true
```

## Related Documentation

- [Context7 MCP Server Documentation](https://context7.com)
- [MCP Gateway Integration](../tapps_agents/mcp/gateway.py)
- [KB Cache System](../tapps_agents/context7/kb_cache.py)
- [Lookup Implementation](../tapps_agents/context7/lookup.py)
