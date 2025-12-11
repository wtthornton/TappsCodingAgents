# NUC Setup Guide for TappsCodingAgents

**Optimizing TappsCodingAgents for NUC (Next Unit of Computing) Hardware**

This guide helps you configure and optimize TappsCodingAgents for NUC devices, which typically have limited CPU and memory resources.

---

## Overview

NUC devices are compact computers with limited resources. This guide provides:

- ✅ **NUC-optimized configuration** for minimal resource usage
- ✅ **Background Agent setup** to offload heavy tasks
- ✅ **Resource monitoring** to track system performance
- ✅ **Performance optimization** tips and best practices
- ✅ **Troubleshooting** common NUC issues

---

## Prerequisites

1. **NUC Hardware**
   - Intel NUC or similar compact PC
   - Minimum: 8GB RAM, 4-core CPU
   - Recommended: 16GB+ RAM, 6+ core CPU

2. **Software**
   - Python 3.12+
   - Cursor AI IDE
   - Git
   - Ollama (for local LLM)

3. **TappsCodingAgents**
   - Installed and configured (see [QUICK_START.md](../QUICK_START.md))

---

## Quick Start

### 1. Enable NUC Configuration

The NUC configuration file is automatically created at `.tapps-agents/nuc-config.yaml`. This file optimizes TappsCodingAgents for NUC hardware.

**Verify configuration exists:**
```bash
ls .tapps-agents/nuc-config.yaml
```

If it doesn't exist, it will be created automatically on first run.

### 2. Verify Configuration

```bash
# Check NUC config
cat .tapps-agents/nuc-config.yaml
```

**Key settings:**
- `use_background_agents: true` - Offload heavy tasks
- `cache_aggressively: true` - Maximize Context7 cache
- `parallel_tools: false` - Reduce CPU load
- `lightweight_skills: true` - Minimal resource usage

### 3. Pre-populate Context7 Cache

Pre-populate the cache to minimize API calls:

```bash
python scripts/prepopulate_context7_cache.py
```

This caches common libraries and reduces future API calls.

---

## Configuration Details

### NUC Configuration File

The NUC configuration file (`.tapps-agents/nuc-config.yaml`) includes:

**Optimization Settings:**
```yaml
optimization:
  use_background_agents: true      # Offload heavy tasks
  cache_aggressively: true         # Maximize Context7 cache
  parallel_tools: false            # Reduce CPU load
  lightweight_skills: true         # Minimal resource usage
```

**Resource Thresholds:**
```yaml
resource_thresholds:
  cpu_warning: 50.0      # Warn if CPU > 50%
  cpu_critical: 80.0     # Critical if CPU > 80%
  memory_warning: 70.0    # Warn if memory > 70%
  memory_critical: 85.0   # Critical if memory > 85%
```

**Context7 Cache:**
```yaml
context7:
  max_cache_size: "200MB"  # Larger cache for offline
  pre_populate: true       # Pre-load common libraries
  auto_refresh: false      # Manual refresh only
```

**Background Agents:**
```yaml
background_agents:
  enabled: true
  default_for:
    - "analyze-project"
    - "refactor-large"
    - "generate-tests"
```

---

## Resource Monitoring

### Enable Resource Monitoring

Resource monitoring tracks CPU, memory, and disk usage:

```python
from tapps_agents.core.resource_monitor import ResourceMonitor

# Create monitor with NUC thresholds
monitor = ResourceMonitor(
    cpu_threshold=50.0,
    memory_threshold=70.0,
    disk_threshold=85.0
)

# Get current metrics
metrics = monitor.get_current_metrics()
print(f"CPU: {metrics.cpu_percent:.1f}%")
print(f"Memory: {metrics.memory_percent:.1f}%")
```

### Monitor Resource Usage

```bash
# Check resource usage
python -m tapps_agents.cli nuc monitor

# View resource history
python -m tapps_agents.cli nuc metrics --export metrics.json
```

### Resource Alerts

The monitor automatically alerts when thresholds are exceeded:

```python
# Check for alerts
alerts = monitor.get_recent_alerts(count=10)
for alert in alerts:
    print(f"{alert.alert_type}: {alert.message}")
```

---

## Background Agent Fallback

### Automatic Fallback

The fallback strategy automatically routes heavy tasks to Background Agents:

```python
from tapps_agents.core.fallback_strategy import FallbackStrategy
from tapps_agents.core.resource_monitor import ResourceMonitor

# Create fallback strategy
monitor = ResourceMonitor()
strategy = FallbackStrategy(resource_monitor=monitor)

# Check if task should use background agent
decision = strategy.should_use_background_agent("analyze-project")
if decision.use_background:
    print(f"Using Background Agent: {decision.reason}")
    agent_name = strategy.get_background_agent_for_task("analyze-project")
    print(f"Agent: {agent_name}")
```

### Task Classification

Tasks are automatically classified:

- **Heavy Tasks**: Always use Background Agents
  - `analyze-project`
  - `refactor-large`
  - `generate-tests`
  - `full-review`

- **Medium Tasks**: Use Background Agents if resources are constrained
  - `review-file`
  - `refactor-file`
  - `generate-code`

- **Light Tasks**: Always run locally
  - `lint-file`
  - `type-check`
  - `format-code`

---

## Performance Optimization

### 1. Use Background Agents

Heavy tasks should use Background Agents:

```yaml
# .cursor/background-agents.yaml
agents:
  - name: "TappsCodingAgents Quality Analyzer"
    type: "background"
    commands:
      - "python -m tapps_agents.cli reviewer analyze-project"
```

### 2. Maximize Context7 Cache

Pre-populate cache and use aggressive caching:

```bash
# Pre-populate cache
python scripts/prepopulate_context7_cache.py

# Verify cache hit rate
python -m tapps_agents.cli context7 status
```

### 3. Disable Parallel Tools

Reduce CPU load by disabling parallel tool execution:

```yaml
optimization:
  parallel_tools: false
```

### 4. Use Lightweight Skills

Use lightweight Skills for quick tasks:

```yaml
optimization:
  lightweight_skills: true
```

### 5. Monitor Resource Usage

Regularly monitor resource usage:

```python
from tapps_agents.core.resource_monitor import ResourceMonitor

monitor = ResourceMonitor()
metrics = monitor.get_current_metrics()

if metrics.is_high_usage():
    print("⚠️  High resource usage - consider using Background Agents")
```

---

## Performance Benchmarks

### Run Benchmarks

Benchmark performance before and after optimization:

```python
from tapps_agents.core.performance_benchmark import PerformanceBenchmark
from tapps_agents.core.resource_monitor import ResourceMonitor

# Create benchmark
monitor = ResourceMonitor()
benchmark = PerformanceBenchmark(resource_monitor=monitor)

# Benchmark a task
def my_task():
    # Your task code
    pass

result = benchmark.benchmark_task("my-task", my_task)
print(f"Duration: {result.duration_seconds:.2f}s")
print(f"CPU: {result.cpu_avg:.1f}%")
print(f"Memory: {result.memory_avg:.1f}%")
```

### Compare Benchmarks

Compare baseline vs optimized:

```python
baseline = benchmark.benchmark_task("baseline", baseline_task)
optimized = benchmark.benchmark_task("optimized", optimized_task)

comparison = benchmark.compare_benchmarks(baseline, optimized)
print(f"Speedup: {comparison.speedup:.2f}x")
print(f"Improvement: {comparison.improvement_percent:.1f}%")
```

### Export Results

```python
# Export benchmark results
benchmark.export_results("benchmarks.json")

# Generate report
report = benchmark.generate_report()
print(report)
```

---

## Best Practices

### 1. Pre-populate Cache

Always pre-populate Context7 cache on setup:

```bash
python scripts/prepopulate_context7_cache.py
```

### 2. Use Background Agents for Heavy Tasks

Configure Background Agents for heavy tasks:

```yaml
background_agents:
  default_for:
    - "analyze-project"
    - "refactor-large"
    - "generate-tests"
```

### 3. Monitor Resource Usage

Regularly check resource usage:

```bash
python -m tapps_agents.cli nuc monitor
```

### 4. Adjust Thresholds

Adjust resource thresholds based on your NUC:

```yaml
resource_thresholds:
  cpu_warning: 50.0      # Adjust based on your CPU
  memory_warning: 70.0    # Adjust based on your RAM
```

### 5. Use Lightweight Operations

Prefer lightweight operations:

- Use `*lint` instead of `*review` for quick checks
- Use `*type-check` instead of full analysis
- Use cached Context7 docs instead of API calls

---

## Troubleshooting

### Problem: High CPU Usage

**Symptoms:**
- CPU usage > 50%
- Cursor becomes unresponsive

**Solutions:**

1. **Use Background Agents:**
   ```yaml
   optimization:
     use_background_agents: true
   ```

2. **Disable Parallel Tools:**
   ```yaml
   optimization:
     parallel_tools: false
   ```

3. **Check Resource Usage:**
   ```python
   monitor = ResourceMonitor()
   metrics = monitor.get_current_metrics()
   print(f"CPU: {metrics.cpu_percent:.1f}%")
   ```

### Problem: High Memory Usage

**Symptoms:**
- Memory usage > 70%
- System becomes slow

**Solutions:**

1. **Reduce Cache Size:**
   ```yaml
   context7:
     max_cache_size: "100MB"  # Reduce from 200MB
   ```

2. **Use Background Agents:**
   ```yaml
   background_agents:
     enabled: true
   ```

3. **Close Unused Applications:**
   - Close browser tabs
   - Close unused IDE windows
   - Stop unused services

### Problem: Slow Performance

**Symptoms:**
- Tasks take longer than expected
- Cursor lags

**Solutions:**

1. **Pre-populate Cache:**
   ```bash
   python scripts/prepopulate_context7_cache.py
   ```

2. **Use Background Agents:**
   ```yaml
   background_agents:
     default_for:
       - "analyze-project"
       - "refactor-large"
   ```

3. **Check Resource Usage:**
   ```bash
   python -m tapps_agents.cli nuc monitor
   ```

### Problem: Background Agents Not Working

**Symptoms:**
- Background Agents not triggering
- Tasks still run locally

**Solutions:**

1. **Verify Configuration:**
   ```yaml
   background_agents:
     enabled: true
   ```

2. **Check Task Classification:**
   ```python
   strategy = FallbackStrategy()
   decision = strategy.should_use_background_agent("analyze-project")
   print(decision.use_background)
   ```

3. **Verify Background Agent Config:**
   ```bash
   cat .cursor/background-agents.yaml
   ```

---

## Success Criteria

After following this guide, you should achieve:

- ✅ **Cursor stays responsive** on NUC
- ✅ **Heavy tasks run in Background Agents**
- ✅ **90%+ Context7 cache hit rate**
- ✅ **CPU usage < 50%** during development

---

## Additional Resources

- [Background Agents Guide](BACKGROUND_AGENTS_GUIDE.md)
- [Context7 Cache Optimization](CONTEXT7_CACHE_OPTIMIZATION.md)
- [Hardware Recommendations](HARDWARE_RECOMMENDATIONS.md)
- [CURSOR_AI_INTEGRATION_PLAN_2025.md](CURSOR_AI_INTEGRATION_PLAN_2025.md)

---

## Support

If you encounter issues:

1. Check resource usage: `python -m tapps_agents.cli nuc monitor`
2. Review logs: `.tapps-agents/logs/`
3. Verify configuration: `.tapps-agents/nuc-config.yaml`
4. Check Background Agents: `.cursor/background-agents.yaml`

