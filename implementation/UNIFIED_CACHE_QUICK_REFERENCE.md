# Unified Cache Architecture - Quick Reference

**Version:** 1.0  
**Date:** December 2025  
**See Full Plan:** [UNIFIED_CACHE_ARCHITECTURE_PLAN.md](UNIFIED_CACHE_ARCHITECTURE_PLAN.md)

> **Status Note (2025-12-11):** This file is a historical snapshot.  
> **Canonical status:** See `implementation/IMPLEMENTATION_STATUS.md`.

---

## Problem Statement

**Current State:** Three separate caching systems cause confusion:
1. Tiered Context Cache (in-memory LRU)
2. Context7 KB Cache (file-based)
3. RAG Knowledge Base (file-based)

**Issues:**
- Multiple APIs and configurations
- No unified visibility
- Code duplication
- User confusion
- Manual optimization required for different hardware (NUC vs Development)
- No automatic adaptation to available resources

---

## Solution

**Unified Cache Architecture with Auto-Optimization** with:
- Single interface for all agents
- **Automatic hardware detection** (NUC, Development, Workstation)
- **Auto-optimization** for detected hardware profile
- **Adaptive configuration** based on available resources
- Namespace-based storage (all use Context7 structure)
- Unified configuration
- Unified analytics dashboard with hardware metrics

---

## Architecture

```
Unified Cache Interface
         ↓
Hardware Detection & Auto-Optimization
         ↓
Cache Router (dispatches with adaptive routing)
         ↓
┌────────┬────────┬────────┐
│Tiered  │Context7│ RAG    │
│Context │KB Cache│Knowledge│
│(Adaptive)│(Adaptive)│(Adaptive)│
└────────┴────────┴────────┘
         ↓
  Unified Storage Backend
         ↓
  Resource Monitor (CPU, Memory, Disk)
```

---

## Implementation Phases

### Phase 1: Unified Interface + Hardware Detection ✅ COMPLETE
- [x] Create `UnifiedCache` class ✅
- [x] **Hardware detection and profiling** ✅
- [x] **Auto-optimization system** ✅
- [x] **Adaptive cache configuration** ✅
- [x] Implement cache router ✅
- [x] Update agent integrations (backward compatible) ✅

**Key Files:**
- `tapps_agents/core/unified_cache.py` ✅
- `tapps_agents/core/cache_router.py` ✅
- `tapps_agents/core/hardware_profiler.py` ✅
- `tapps_agents/core/unified_cache_config.py` ✅

**Status:** ✅ **COMPLETE** - Ready for use
- `tapps_agents/core/hardware_profiler.py` ✅
- `tapps_agents/core/unified_cache_config.py` ✅

### Phase 2: Storage Consolidation + Adaptive Strategies (4-5 weeks)
- Migrate tiered context to file-based storage
- **Hardware-aware storage policies**
- **Adaptive storage strategies** (NUC vs Development vs Workstation)
- **Compression support** for disk optimization
- Create unified storage backend
- Migration tools and scripts

**Key Files:**
- `tapps_agents/core/tiered_context_storage.py`
- `tapps_agents/core/unified_storage.py`
- `scripts/migrate_*.py`

### Phase 3: Configuration & Analytics + Hardware Integration (4 weeks)
- Unified configuration system
- **Hardware auto-detection in config**
- **Runtime adaptive configuration**
- Analytics dashboard with hardware metrics
- CLI commands with hardware profile support

**Key Files:**
- `tapps_agents/core/unified_cache_config.py`
- `tapps_agents/core/unified_cache_analytics.py`
- `tapps_agents/cli/unified_cache.py`

---

## Storage Structure

```
.tapps-agents/kb/unified-cache/
├── tiered-context/      # Tiered context cache
│   ├── tier1/
│   ├── tier2/
│   └── tier3/
├── context7-kb/         # Context7 KB cache (moved)
│   └── libraries/
└── rag-knowledge/       # RAG knowledge base (moved)
    └── {domain}/
```

---

## Configuration (Unified + Auto-Optimized)

```yaml
# .tapps-agents/unified-cache-config.yaml
unified_cache:
  enabled: true
  storage_root: ".tapps-agents/kb/unified-cache"
  
  # Hardware auto-detection (automatic on first run)
  hardware:
    auto_detect: true
    profile: "auto"  # auto, nuc, development, workstation
    detected_profile: "development"  # Set automatically
    
  # Adaptive settings (adjusts based on resources)
  adaptive:
    enabled: true
    check_interval: 60
  
  tiered_context:
    enabled: true
    namespace: "tiered-context"
    # Auto-configured based on hardware profile:
    # NUC: file-only, Development: hybrid, Workstation: aggressive
    hybrid_mode: true  # Auto-configured
    
  context7_kb:
    enabled: true
    namespace: "context7-kb"
    max_cache_size: "200MB"  # Auto-adjusted (NUC: 100MB, Dev: 200MB, Work: 500MB)
    
  rag_knowledge:
    enabled: true
    namespace: "rag-knowledge"
```

---

## API Usage

```python
from tapps_agents.core.unified_cache import UnifiedCache, CacheType

cache = UnifiedCache()

# Get tiered context
response = await cache.get(
    CacheType.TIERED_CONTEXT,
    key="file_path",
    tier=ContextTier.TIER1
)

# Get Context7 docs
response = await cache.get(
    CacheType.CONTEXT7_KB,
    library="fastapi",
    topic="routing"
)

# Get RAG knowledge
response = await cache.get(
    CacheType.RAG_KNOWLEDGE,
    domain="ai-frameworks",
    query="agent orchestration"
)
```

---

## CLI Commands

```bash
# Status (shows hardware profile)
python -m tapps_agents.cli unified-cache status

# Hardware profile detection
python -m tapps_agents.cli unified-cache hardware-profile

# Auto-optimize for detected hardware
python -m tapps_agents.cli unified-cache optimize --auto-detect

# Optimize for specific profile
python -m tapps_agents.cli unified-cache optimize --profile nuc

# Analytics (with hardware metrics)
python -m tapps_agents.cli unified-cache analytics

# View resource usage
python -m tapps_agents.cli unified-cache resources

# Clear cache
python -m tapps_agents.cli unified-cache clear --namespace tiered-context

# Stats (with hardware context)
python -m tapps_agents.cli unified-cache stats
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Token Savings | 90%+ (maintained) |
| Context7 Hit Rate | 95%+ (maintained) |
| Configuration Files | 3 → 1 |
| Code Duplication | -50% |
| User Confusion | Zero |

---

## Timeline

- **Phase 1:** Weeks 1-5 (Unified Interface + Hardware Detection)
- **Phase 2:** Weeks 6-10 (Storage Consolidation + Adaptive Strategies)
- **Phase 3:** Weeks 11-14 (Config & Analytics + Hardware Integration)

**Total Duration:** 12-14 weeks

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Performance degradation | Hybrid mode, benchmarks, rollback |
| Data loss | Backups, validation, rollback |
| Breaking changes | Backward-compatible wrappers |
| Increased complexity | Good abstraction, documentation |

---

## Key Benefits

✅ **Single interface** - One API for all caches  
✅ **Auto-optimization** - Automatically optimizes for hardware (NUC, Dev, Workstation)  
✅ **Zero-config setup** - Works out of the box, no manual tuning needed  
✅ **Adaptive behavior** - Adjusts cache settings based on available resources  
✅ **Unified config** - One configuration file (auto-configured)  
✅ **Unified analytics** - One dashboard with hardware metrics  
✅ **Maintained performance** - 90%+ token savings, 95%+ hit rates (all profiles)  
✅ **Better maintainability** - Less code duplication  
✅ **Zero user confusion** - Clear, simple interface  
✅ **NUC optimized** - Automatically optimized for low-resource hardware  

---

**For full details, see:** [UNIFIED_CACHE_ARCHITECTURE_PLAN.md](UNIFIED_CACHE_ARCHITECTURE_PLAN.md)

