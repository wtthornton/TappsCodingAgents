# Unified Cache Architecture

**Version**: 1.0  
**Last Updated**: December 2025  
**Status**: ✅ Phase 1 Complete

## Overview

The Unified Cache Architecture provides a single interface for all caching systems in TappsCodingAgents, with automatic hardware detection and optimization. It consolidates three separate caching systems into one unified, hardware-aware solution.

## Key Features

✅ **Single Interface** - One API for all cache types  
✅ **Hardware Auto-Detection** - Automatically detects NUC, Development, Workstation, or Server  
✅ **Auto-Optimization** - Configures cache settings based on detected hardware  
✅ **Backward Compatible** - Existing cache systems continue to work unchanged  
✅ **Zero Configuration** - Works out of the box with sensible defaults  
✅ **Unified Statistics** - Single interface for all cache metrics  

## Cache Types

The unified cache supports three cache types:

1. **Tiered Context Cache** - Code context caching (in-memory LRU)
2. **Context7 KB Cache** - Library documentation caching (file-based)
3. **RAG Knowledge Base** - Domain knowledge caching (file-based)

## Hardware Profiles

The unified cache automatically detects hardware and optimizes settings:

| Profile | CPU Cores | RAM | Cache Strategy | In-Memory Size | File Cache Size |
|---------|-----------|-----|----------------|----------------|-----------------|
| **NUC** | ≤6 cores | ≤16GB | Conservative | 50 entries | 100MB |
| **Development** | ≤12 cores | ≤32GB | Balanced | 100 entries | 200MB |
| **Workstation** | >12 cores | >32GB | Aggressive | 200 entries | 500MB |
| **Server** | Variable | Variable | Custom | Configurable | Configurable |

## Quick Start

### Basic Usage

```python
from tapps_agents.core import UnifiedCache, create_unified_cache, CacheType, ContextTier

# Create unified cache (auto-detects hardware)
cache = create_unified_cache()

# Check hardware profile
profile = cache.get_hardware_profile()
print(f"Hardware: {profile.value}")  # nuc, development, workstation, server

# Get tiered context
response = cache.get(
    CacheType.TIERED_CONTEXT,
    key="path/to/file.py",
    tier=ContextTier.TIER1
)

# Get Context7 KB entry
response = cache.get(
    CacheType.CONTEXT7_KB,
    key="library-topic",
    library="fastapi",
    topic="routing"
)

# Get RAG knowledge
response = cache.get(
    CacheType.RAG_KNOWLEDGE,
    key="query-id",
    query="agent orchestration patterns"
)
```

### Using in Agents

```python
from tapps_agents.core import BaseAgent, CacheType, ContextTier

class MyAgent(BaseAgent):
    async def run(self, command: str, **kwargs):
        # Get unified cache (lazy initialization)
        cache = self.get_unified_cache()
        
        # Use unified cache
        response = cache.get(
            CacheType.TIERED_CONTEXT,
            key=kwargs.get("file", ""),
            tier=ContextTier.TIER1
        )
        
        if response and response.cached:
            print(f"Cached context found: {response.data}")
        
        return {"success": True}
```

## API Reference

### `UnifiedCache`

Main unified cache interface.

**Methods:**
- `get(cache_type, key, **kwargs)` - Retrieve cached entry
- `put(cache_type, key, value, **kwargs)` - Store entry in cache
- `invalidate(cache_type, key, **kwargs)` - Clear cache entry
- `invalidate_all(cache_type)` - Clear all entries for cache type
- `get_stats()` - Get unified statistics
- `get_hardware_profile()` - Get detected hardware profile
- `get_optimization_profile()` - Get optimization settings

### `BaseAgent.get_unified_cache()`

Optional unified cache access in agents (lazy initialization).

## Configuration

Configuration is optional. The unified cache works with sensible defaults and auto-detects hardware on first run.

For custom configuration, see [Configuration Guide](CONFIGURATION.md#unified-cache-configuration).

## Backward Compatibility

✅ **All existing code works unchanged:**
- `BaseAgent.get_context()` - continues to use `ContextManager`
- `BaseAgent.get_context_text()` - continues to use `ContextManager`
- Direct `ContextManager` usage - unchanged
- `Context7AgentHelper` and `KBCache` usage - unchanged
- `SimpleKnowledgeBase` usage - unchanged

## Documentation

- **[Architecture Plan](../implementation/UNIFIED_CACHE_ARCHITECTURE_PLAN.md)** - Complete architecture and implementation plan
- **[Integration Guide](../implementation/UNIFIED_CACHE_INTEGRATION_GUIDE.md)** - How to use unified cache in agents
- **[Quick Reference](../implementation/UNIFIED_CACHE_QUICK_REFERENCE.md)** - Quick reference guide
- **[Implementation Summary](../implementation/UNIFIED_CACHE_IMPLEMENTATION_SUMMARY.md)** - Implementation details
- **[Phase 1 Completion Report](../implementation/UNIFIED_CACHE_PHASE1_COMPLETE.md)** - Completion status

## Status

**Phase 1**: ✅ **COMPLETE** (December 2025)
- Hardware profiler
- Cache router
- Unified cache interface
- Configuration system
- Agent integration

**Phase 2**: Planned
- Storage consolidation
- Unified storage backend
- Compression support

**Phase 3**: Planned
- Analytics dashboard
- CLI commands
- Performance monitoring

## See Also

- [Context7 Cache Optimization](CONTEXT7_CACHE_OPTIMIZATION.md) - Context7-specific optimization
- [Architecture Overview](ARCHITECTURE.md) - System architecture
- [API Reference](API.md) - Complete API documentation

