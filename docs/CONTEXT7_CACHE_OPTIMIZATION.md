# Context7 Cache Optimization Guide

**TappsCodingAgents + Context7 Integration**

This guide covers optimizing Context7 KB cache for maximum performance, including cache warming, hit rate optimization, and performance tuning.

> **Note**: As of December 2025, Context7 KB cache is now part of the **Unified Cache Architecture**. The unified cache provides a single interface for all caching systems (Tiered Context, Context7 KB, and RAG Knowledge) with automatic hardware detection and optimization. See [Unified Cache Architecture Plan](../implementation/UNIFIED_CACHE_ARCHITECTURE_PLAN.md) for details. This guide remains valid for direct Context7 KB cache usage, but consider using the unified cache for new implementations.

---

## Overview

Context7 KB cache optimization helps achieve:

- ✅ **95%+ Cache Hit Rate**: Minimize API calls
- ✅ **<30s Warm-up Time**: Fast cache initialization
- ✅ **<0.15s Response Time**: Sub-second lookup performance
- ✅ **Reduced Costs**: Fewer API calls = lower costs

---

## Cache Pre-Population

### Automatic Pre-Population

Pre-populate cache with project dependencies:

```bash
# Pre-populate from requirements.txt
python scripts/prepopulate_context7_cache.py

# Pre-populate with specific libraries
python scripts/prepopulate_context7_cache.py --libraries fastapi pytest sqlalchemy

# Pre-populate with topics
python scripts/prepopulate_context7_cache.py --topics
```

### Dependency-Based Warming

The pre-population script automatically:

1. **Parses requirements.txt** to extract dependencies
2. **Caches common libraries** (FastAPI, pytest, SQLAlchemy, etc.)
3. **Caches common topics** for each library
4. **Reports success rate** and cache statistics

**Example Output:**
```
🚀 Context7 KB Cache Pre-population
============================================================
📦 Parsing requirements.txt...
   Found 15 libraries in requirements.txt
📚 Total libraries to cache: 25
============================================================

🔍 Processing fastapi...
  📚 Caching fastapi (overview)... ✅
  📚 Caching fastapi (routing)... ✅
  📚 Caching fastapi (dependency-injection)... ✅

📊 Pre-population Summary
============================================================
✅ Successfully cached: 24 libraries
❌ Failed to cache: 1 libraries
📈 Success rate: 96.0%

📊 Cache Statistics:
   Total entries: 45
   Total libraries: 24
   Cache size: 12.5 MB
```

### Manual Cache Warming

```python
from tapps_agents.context7.commands import Context7Commands

commands = Context7Commands()

# Cache specific library
await commands.cmd_docs("fastapi")

# Cache library with topic
await commands.cmd_docs("fastapi", topic="routing")
```

---

## Hit Rate Optimization

### Target: 95%+ Hit Rate

**Strategies:**

1. **Pre-populate Common Libraries**
   ```bash
   python scripts/prepopulate_context7_cache.py
   ```

2. **Cache Aggressively**
   ```yaml
   # .tapps-agents/config.yaml
   context7:
     knowledge_base:
       cache_aggressively: true
       max_cache_size: "200MB"  # Larger cache
   ```

3. **Monitor Hit Rate**
   ```python
   from tapps_agents.context7.analytics import Analytics
   from tapps_agents.context7.cache_structure import CacheStructure
   from tapps_agents.context7.metadata import MetadataManager
   
   cache_structure = CacheStructure(cache_root)
   metadata_manager = MetadataManager(cache_structure)
   analytics = Analytics(cache_structure, metadata_manager)
   
   metrics = analytics.get_cache_metrics()
   print(f"Hit Rate: {metrics.hit_rate:.1f}%")
   ```

### Improving Hit Rate

**If hit rate < 95%:**

1. **Identify Miss Patterns**
   - Check analytics dashboard
   - Review cache misses
   - Identify frequently missed libraries

2. **Pre-populate Missing Libraries**
   ```bash
   # Add missing libraries to pre-population
   python scripts/prepopulate_context7_cache.py --libraries missing-lib-1 missing-lib-2
   ```

3. **Increase Cache Size**
   ```yaml
   context7:
     knowledge_base:
       max_cache_size: "500MB"  # Increase from default 100MB
   ```

4. **Enable Auto-Refresh**
   ```yaml
   context7:
     refresh:
       enabled: true
       auto_queue: true
       auto_process_on_startup: true
   ```

---

## Performance Tuning

### Response Time Optimization

**Target: <0.15s response time**

**Strategies:**

1. **Use Local Cache First**
   - KB-first lookup (cache before API)
   - Fuzzy matching for library name variations

2. **Optimize Cache Structure**
   ```yaml
   context7:
     knowledge_base:
       sharding: true  # Library-based sharding
       indexing: true   # Fast index lookups
   ```

3. **Monitor Response Times**
   ```python
   metrics = analytics.get_cache_metrics()
   print(f"Avg Response Time: {metrics.avg_response_time_ms:.2f} ms")
   ```

### Cache Size Management

**Default: 100MB**

**Tuning:**

```yaml
# .tapps-agents/config.yaml
context7:
  knowledge_base:
    max_cache_size: "200MB"  # Increase for larger projects
    cleanup_interval: 86400   # 24 hours
```

**Size Recommendations:**
- Small projects: 100MB
- Medium projects: 200MB
- Large projects: 500MB
- Enterprise: 1GB+

### Cleanup Strategies

**Automatic Cleanup:**

```yaml
context7:
  knowledge_base:
    cleanup_interval: 86400  # 24 hours
```

**Manual Cleanup:**

```python
from tapps_agents.context7.commands import Context7Commands

commands = Context7Commands()

# Cleanup old entries
result = commands.cmd_cleanup(max_age_days=30)
```

**Cleanup Strategies:**
- **LRU Eviction**: Remove least recently used entries
- **Size-based**: Maintain cache under maximum size
- **Age-based**: Remove entries older than threshold
- **Unused entry**: Remove entries not accessed recently

---

## Cache Warming Strategies

### Strategy 1: Startup Warming

Warm cache on application startup:

```python
from tapps_agents.context7.commands import Context7Commands

async def warm_cache_on_startup():
    commands = Context7Commands()
    
    # Common libraries
    common_libs = ["fastapi", "pytest", "sqlalchemy", "pydantic"]
    
    for lib in common_libs:
        await commands.cmd_docs(lib)
```

### Strategy 2: Dependency-Based Warming

Warm cache based on project dependencies:

```bash
# Automatic from requirements.txt
python scripts/prepopulate_context7_cache.py --requirements requirements.txt
```

### Strategy 3: Predictive Warming

Warm cache based on usage patterns:

```python
from tapps_agents.context7.analytics_dashboard import AnalyticsDashboard

dashboard = AnalyticsDashboard(analytics, cache_structure, metadata_manager)

# Get top libraries
top_libs = analytics.get_top_libraries(10)

# Pre-warm top libraries
for lib_metrics in top_libs:
    await commands.cmd_docs(lib_metrics.library)
```

---

## Monitoring & Analytics

### Analytics Dashboard

View cache performance:

```python
from tapps_agents.context7.analytics_dashboard import AnalyticsDashboard

dashboard = AnalyticsDashboard(analytics, cache_structure, metadata_manager)

# Get dashboard metrics
metrics = dashboard.get_dashboard_metrics()

# Export to JSON
dashboard.export_dashboard_json()

# Generate report
report = dashboard.generate_dashboard_report()
print(report)
```

### Key Metrics

**Monitor these metrics:**

1. **Hit Rate**: Target 95%+
2. **Response Time**: Target <150ms
3. **Cache Size**: Monitor growth
4. **API Calls**: Minimize external calls
5. **Top Libraries**: Identify frequently used libraries

### Observability

This repo does not currently expose a dedicated `tapps-agents context7 ...` CLI command set.

Use these instead:

- **Cache inspection**: check `.tapps-agents/kb/context7-cache/` (size, hot libraries, staleness).
- **Pre-population**: `python scripts/prepopulate_context7_cache.py`
- **System analytics**: `python -m tapps_agents.cli analytics dashboard`

---

## Best Practices

### 1. Pre-populate on Setup

```bash
# Run after project setup
python scripts/prepopulate_context7_cache.py
```

### 2. Monitor Hit Rate

```python
# Check hit rate regularly
metrics = analytics.get_cache_metrics()
if metrics.hit_rate < 95:
    print("⚠️  Hit rate below target, consider pre-population")
```

### 3. Optimize Cache Size

```yaml
# Adjust based on project size
context7:
  knowledge_base:
    max_cache_size: "200MB"  # Increase for larger projects
```

### 4. Enable Auto-Refresh

```yaml
context7:
  refresh:
    enabled: true
    auto_queue: true
    auto_process_on_startup: true
```

### 5. Regular Cleanup

```python
# Run cleanup periodically
commands.cmd_cleanup(max_age_days=30)
```

---

## Troubleshooting

### Problem: Low Hit Rate

**Symptoms:**
- Hit rate < 95%
- Frequent API calls

**Solutions:**

1. **Pre-populate cache:**
   ```bash
   python scripts/prepopulate_context7_cache.py
   ```

2. **Increase cache size:**
   ```yaml
   context7:
     knowledge_base:
       max_cache_size: "500MB"
   ```

3. **Check missing libraries:**
   ```python
   # Review cache misses
   metrics = analytics.get_cache_metrics()
   print(f"Misses: {metrics.cache_misses}")
   ```

### Problem: Slow Response Time

**Symptoms:**
- Response time > 150ms
- Slow lookups

**Solutions:**

1. **Check cache structure:**
   ```yaml
   context7:
     knowledge_base:
       sharding: true
       indexing: true
   ```

2. **Optimize disk I/O:**
   - Use SSD storage
   - Reduce cache directory depth

3. **Monitor performance:**
   ```python
   metrics = analytics.get_cache_metrics()
   print(f"Response time: {metrics.avg_response_time_ms} ms")
   ```

### Problem: Cache Size Issues

**Symptoms:**
- Cache exceeds max size
- Cleanup not working

**Solutions:**

1. **Increase max size:**
   ```yaml
   context7:
     knowledge_base:
       max_cache_size: "500MB"
   ```

2. **Run manual cleanup:**
   ```python
   commands.cmd_cleanup(max_age_days=30)
   ```

3. **Check cleanup interval:**
   ```yaml
   context7:
     knowledge_base:
       cleanup_interval: 86400  # 24 hours
   ```

---

## Configuration Examples

### Small Project

```yaml
context7:
  knowledge_base:
    max_cache_size: "100MB"
    cleanup_interval: 172800  # 48 hours
```

### Medium Project

```yaml
context7:
  knowledge_base:
    max_cache_size: "200MB"
    cleanup_interval: 86400  # 24 hours
```

### Large Project

```yaml
context7:
  knowledge_base:
    max_cache_size: "500MB"
    cleanup_interval: 43200  # 12 hours
```

---

## Planned Enhancements

### Dynamic Expert & RAG Engine Integration

The Context7 KB cache will be enhanced as part of the planned **Dynamic Expert & RAG Engine**:

- **Automatic Dependency Detection**: When the engine detects a library/framework is used, automatically fetch overview, patterns, pitfalls, and security notes from Context7 KB
- **Knowledge Distillation**: Optionally distill Context7 docs into project KB as "how we use X here" notes
- **Metrics Integration**: Context7 KB metrics (hit rate, latency) will be tracked as part of the Expert Engine observability system
- **Cache Pre-population**: Automatic cache warming when new dependencies are detected during workflow execution

**Status**: Design phase - See [SDLC Improvements Analysis](../SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) and [Epic 2: Dynamic Expert & RAG Engine](prd/epic-2-dynamic-expert-rag-engine.md)

## See Also

- [Security & Privacy Guide](CONTEXT7_SECURITY_PRIVACY.md)
- [API Key Management Guide](CONTEXT7_API_KEY_MANAGEMENT.md)
- [CURSOR_AI_INTEGRATION_PLAN_2025.md](CURSOR_AI_INTEGRATION_PLAN_2025.md)
- [SDLC Improvements Analysis](../SDLC_ISSUES_AND_IMPROVEMENTS_ANALYSIS.md) - Comprehensive analysis of planned improvements
- [Unified Cache Architecture](UNIFIED_CACHE.md) - Single interface for all caching systems

