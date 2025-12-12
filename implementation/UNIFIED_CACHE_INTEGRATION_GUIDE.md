# Unified Cache Integration Guide

> **Status Note (2025-12-11):** This file is a historical snapshot.  
> **Canonical status:** See `implementation/IMPLEMENTATION_STATUS.md`.

## Overview

The unified cache has been integrated into the agent framework with full backward compatibility. All existing code continues to work unchanged, while agents can optionally use the unified cache for enhanced functionality.

## Backward Compatibility

✅ **All existing code works unchanged:**
- `BaseAgent.get_context()` - continues to use `ContextManager`
- `BaseAgent.get_context_text()` - continues to use `ContextManager`
- Direct `ContextManager` usage in agents (e.g., `EnhancerAgent`) - unchanged
- `Context7AgentHelper` and `KBCache` usage - unchanged

## Using Unified Cache (Optional Enhancement)

### Basic Usage

```python
from tapps_agents.core import BaseAgent, CacheType, ContextTier

class MyAgent(BaseAgent):
    async def run(self, command: str, **kwargs):
        # Get unified cache instance (lazy initialization)
        cache = self.get_unified_cache()
        
        # Use unified cache for tiered context
        response = cache.get(
            CacheType.TIERED_CONTEXT,
            key="path/to/file.py",
            tier=ContextTier.TIER1
        )
        
        if response and response.cached:
            print(f"Cached context found: {response.data}")
        
        # Use unified cache for Context7 KB
        kb_response = cache.get(
            CacheType.CONTEXT7_KB,
            key="library-topic",
            library="python",
            topic="async-programming"
        )
        
        # Use unified cache for RAG knowledge
        rag_response = cache.get(
            CacheType.RAG_KNOWLEDGE,
            key="query",
            query="How to implement caching?"
        )
        
        return {"success": True}
```

### Hardware-Aware Caching

The unified cache automatically detects hardware and optimizes settings:

```python
cache = self.get_unified_cache()

# Check detected hardware profile
profile = cache.get_hardware_profile()
print(f"Hardware: {profile.value}")  # nuc, development, workstation, server

# Get optimization profile
opt_profile = cache.get_optimization_profile()
print(f"Max in-memory entries: {opt_profile.max_in_memory_entries}")
print(f"Cache TTL: {opt_profile.cache_ttl_seconds}s")
```

### Cache Statistics

```python
cache = self.get_unified_cache()

# Get unified statistics
stats = cache.get_stats()
print(f"Hardware Profile: {stats.hardware_profile}")
print(f"Total Hits: {stats.total_hits}")
print(f"Total Misses: {stats.total_misses}")
print(f"Cache Stats: {stats.cache_stats}")
```

### Storing in Cache

```python
cache = self.get_unified_cache()

# Store tiered context
response = cache.put(
    CacheType.TIERED_CONTEXT,
    key="path/to/file.py",
    value={"context": "..."},
    tier=ContextTier.TIER1
)

# Store Context7 KB entry
response = cache.put(
    CacheType.CONTEXT7_KB,
    key="library-topic",
    value="Content here...",
    library="python",
    topic="async-programming"
)
```

### Cache Invalidation

```python
cache = self.get_unified_cache()

# Invalidate specific entry
cache.invalidate(
    CacheType.TIERED_CONTEXT,
    key="path/to/file.py",
    tier=ContextTier.TIER1
)

# Invalidate all tiered context
cache.invalidate_all(CacheType.TIERED_CONTEXT)
```

## Migration Path

### Option 1: Keep Existing Code (Recommended)
- No changes needed
- Existing `ContextManager` usage continues to work
- Unified cache is available when needed

### Option 2: Gradual Migration
- Start using `get_unified_cache()` for new features
- Keep existing `get_context()` calls unchanged
- Migrate incrementally as needed

### Option 3: Full Migration
- Replace `self.context_manager` with `self.get_unified_cache()`
- Update all `get_context()` calls to use unified cache API
- Test thoroughly

## Benefits of Unified Cache

1. **Hardware Optimization**: Automatically adapts to NUC/Development/Workstation/Server
2. **Unified Interface**: Single API for all cache types
3. **Better Statistics**: Unified metrics across all caches
4. **Future-Proof**: Ready for Phase 2 (storage consolidation) and Phase 3 (analytics)

## Example: Enhanced Agent

```python
from tapps_agents.core import BaseAgent, CacheType, ContextTier

class EnhancedAgent(BaseAgent):
    async def run(self, command: str, **kwargs):
        cache = self.get_unified_cache()
        
        # Check hardware profile
        if cache.get_hardware_profile().value == "nuc":
            # Use conservative caching for NUC
            max_results = 5
        else:
            # Use aggressive caching for workstation
            max_results = 20
        
        # Get context with hardware-aware settings
        response = cache.get(
            CacheType.TIERED_CONTEXT,
            key=kwargs.get("file", ""),
            tier=ContextTier.TIER1
        )
        
        return {"context": response.data if response else None}
```

## Configuration

The unified cache uses automatic hardware detection by default. To override:

```python
from tapps_agents.core import UnifiedCache, HardwareProfile

cache = UnifiedCache(
    hardware_profile=HardwareProfile.WORKSTATION  # Force workstation profile
)
```

## Next Steps

- **Phase 2**: Storage consolidation (unified storage backend)
- **Phase 3**: Configuration & Analytics (dashboard, adaptive tuning)

See `implementation/UNIFIED_CACHE_ARCHITECTURE_PLAN.md` for details.

