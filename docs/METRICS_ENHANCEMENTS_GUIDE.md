# Metrics Enhancements Guide

This guide documents the high-quality enhancements made to TappsCodingAgents metrics capture and reporting system.

## Overview

The enhanced metrics system provides:
- **Thread-safe operations** with proper locking
- **Data validation** before storage
- **Date range filtering** for queries
- **Batch operations** for efficient bulk recording
- **Performance optimizations** with write buffering
- **Metrics retention policies** for automatic cleanup
- **Enhanced error handling** with detailed logging
- **Advanced aggregation** with percentiles and time-series

## Enhanced Components

### 1. EnhancedExecutionMetricsCollector

Located in `tapps_agents/workflow/metrics_enhancements.py`

**Key Features:**
- Thread-safe with `threading.RLock()`
- Data validation before storage
- Write buffering (configurable buffer size)
- Date range filtering in queries
- Batch recording support
- Automatic metrics cleanup
- Enhanced statistics tracking

**Usage:**

```python
from tapps_agents.workflow.metrics_enhancements import EnhancedExecutionMetricsCollector
from datetime import datetime, timedelta
from pathlib import Path

# Initialize with enhanced features
collector = EnhancedExecutionMetricsCollector(
    project_root=Path("."),
    max_cache_size=1000,        # Larger cache
    write_buffer_size=10,       # Buffer 10 metrics before writing
    retention_days=90,          # Keep metrics for 90 days
    enable_validation=True,     # Validate before storing
)

# Record execution with metadata
metric = collector.record_execution(
    workflow_id="workflow-123",
    step_id="step-1",
    command="review",
    status="success",
    duration_ms=1234.5,
    retry_count=0,
    metadata={"agent": "reviewer", "file_count": 5},
)

# Query with date range
start_date = datetime.now(UTC) - timedelta(days=7)
end_date = datetime.now(UTC)
metrics = collector.get_metrics(
    workflow_id="workflow-123",
    start_date=start_date,
    end_date=end_date,
    limit=100,
    offset=0,  # Pagination support
)

# Batch recording
batch_metrics = [
    {
        "workflow_id": "wf-1",
        "step_id": "step-1",
        "command": "review",
        "status": "success",
        "duration_ms": 1000.0,
    },
    {
        "workflow_id": "wf-1",
        "step_id": "step-2",
        "command": "test",
        "status": "success",
        "duration_ms": 2000.0,
    },
]
recorded = collector.record_batch(batch_metrics)

# Get enhanced summary with date range
summary = collector.get_summary(
    start_date=start_date,
    end_date=end_date,
)
# Returns: {
#     "total_executions": 150,
#     "success_rate": 0.95,
#     "average_duration_ms": 1234.5,
#     "median_duration_ms": 1200.0,  # NEW
#     "min_duration_ms": 100.0,      # NEW
#     "max_duration_ms": 5000.0,     # NEW
#     "total_retries": 5,
#     "by_status": {...},
#     "date_range": {...},            # NEW
#     "stats": {...},                 # NEW
# }

# Cleanup old metrics
deleted_count = collector.cleanup_old_metrics(days_to_keep=30)

# Get collector statistics
stats = collector.get_stats()
# Returns: {
#     "total_recorded": 1000,
#     "total_failed": 5,
#     "validation_errors": 2,
#     "cache_hits": 500,
#     "cache_misses": 200,
#     "cache_size": 100,
#     "buffer_size": 3,
# }

# Manually flush buffer
collector.flush()
```

### 2. EnhancedAnalyticsCollector

Located in `tapps_agents/core/analytics_enhancements.py`

**Key Features:**
- Date range filtering
- Enhanced error handling
- Metadata support
- Improved performance

**Usage:**

```python
from tapps_agents.core.analytics_enhancements import EnhancedAnalyticsCollector, DateRange
from datetime import datetime, timedelta

collector = EnhancedAnalyticsCollector()

# Record with metadata
collector.record_agent_execution(
    agent_id="reviewer",
    agent_name="Reviewer Agent",
    duration=1.5,
    success=True,
    metadata={"files_reviewed": 10, "score": 85.5},
)

# Query with date range
date_range = DateRange(
    start=datetime.now(UTC) - timedelta(days=7),
    end=datetime.now(UTC),
)
metrics = collector.get_agent_metrics(
    agent_id="reviewer",
    date_range=date_range,
)
```

### 3. MetricsAggregator

Located in `tapps_agents/core/analytics_enhancements.py`

**Key Features:**
- Multiple aggregation types (summary, percentiles, time-series)
- Grouped aggregation
- Percentile calculations (p25, p50, p75, p90, p95, p99)

**Usage:**

```python
from tapps_agents.core.analytics_enhancements import MetricsAggregator

metrics = [...]  # List of metric dictionaries

# Summary aggregation
summary = MetricsAggregator.aggregate(metrics, aggregation_type="summary")
# Returns: {
#     "count": 100,
#     "total_executions": 1000,
#     "success_rate": 0.95,
#     "average_duration": 1.5,
#     "median_duration": 1.4,      # NEW
#     "p25_duration": 1.0,         # NEW
#     "p75_duration": 2.0,         # NEW
#     "p95_duration": 3.0,         # NEW
#     ...
# }

# Percentile aggregation
percentiles = MetricsAggregator.aggregate(metrics, aggregation_type="percentiles")
# Returns: {
#     "duration_percentiles": {
#         "p50": 1.4,
#         "p75": 2.0,
#         "p90": 2.5,
#         "p95": 3.0,
#         "p99": 4.0,
#     },
#     "success_rate_percentiles": {...},
# }

# Time-series aggregation
time_series = MetricsAggregator.aggregate(metrics, aggregation_type="time_series")
# Returns: {
#     "time_series": [
#         {"date": "2025-01-16", "total_executions": 50, ...},
#         {"date": "2025-01-17", "total_executions": 60, ...},
#     ],
# }

# Grouped aggregation
grouped = MetricsAggregator.aggregate(
    metrics,
    aggregation_type="summary",
    group_by="agent_id",
)
# Returns: {
#     "groups": 5,
#     "grouped": {
#         "reviewer": {"count": 20, "total_executions": 200, ...},
#         "implementer": {"count": 15, "total_executions": 150, ...},
#     },
# }
```

### 4. MetricsCollectorAdapter

Located in `tapps_agents/workflow/metrics_integration.py`

**Purpose:** Provides backward-compatible interface while using enhanced features.

**Usage:**

```python
from tapps_agents.workflow.metrics_integration import MetricsCollectorAdapter

# Use enhanced collector with backward-compatible interface
adapter = MetricsCollectorAdapter(
    use_enhanced=True,
    project_root=Path("."),
    write_buffer_size=10,
    retention_days=90,
)

# Standard interface works
metric = adapter.record_execution(
    workflow_id="wf-1",
    step_id="step-1",
    command="review",
    status="success",
    duration_ms=1000.0,
)

# Enhanced features available
metrics = adapter.get_metrics(
    workflow_id="wf-1",
    start_date=datetime.now(UTC) - timedelta(days=7),
    end_date=datetime.now(UTC),
    limit=100,
    offset=0,
)

# Enhanced summary
summary = adapter.get_summary(
    start_date=datetime.now(UTC) - timedelta(days=30),
    end_date=datetime.now(UTC),
)

# Enhanced features
adapter.flush()  # Flush buffer
deleted = adapter.cleanup_old_metrics(days_to_keep=30)
stats = adapter.get_stats()
```

## Migration Guide

### Option 1: Gradual Migration (Recommended)

Use `MetricsCollectorAdapter` for backward compatibility:

```python
# Before
from tapps_agents.workflow.execution_metrics import ExecutionMetricsCollector
collector = ExecutionMetricsCollector()

# After (backward compatible)
from tapps_agents.workflow.metrics_integration import MetricsCollectorAdapter
collector = MetricsCollectorAdapter(use_enhanced=True)
# Existing code works without changes
```

### Option 2: Direct Migration

Replace imports and use enhanced features:

```python
# Before
from tapps_agents.workflow.execution_metrics import ExecutionMetricsCollector
collector = ExecutionMetricsCollector(project_root=Path("."))

# After
from tapps_agents.workflow.metrics_enhancements import EnhancedExecutionMetricsCollector
collector = EnhancedExecutionMetricsCollector(
    project_root=Path("."),
    write_buffer_size=10,
    retention_days=90,
    enable_validation=True,
)

# Now you can use enhanced features
metrics = collector.get_metrics(
    start_date=datetime.now(UTC) - timedelta(days=7),
    end_date=datetime.now(UTC),
)
```

## Performance Improvements

### Write Buffering

The enhanced collector buffers writes to reduce I/O operations:

```python
collector = EnhancedExecutionMetricsCollector(
    write_buffer_size=10,  # Buffer 10 metrics before writing
)

# Metrics are buffered and written in batches
for i in range(100):
    collector.record_execution(...)  # Buffered

collector.flush()  # Explicitly flush remaining buffer
```

### Caching

Larger cache size reduces file reads:

```python
collector = EnhancedExecutionMetricsCollector(
    max_cache_size=1000,  # Keep 1000 metrics in memory
)
```

## Validation

Metrics are validated before storage:

```python
collector = EnhancedExecutionMetricsCollector(
    enable_validation=True,  # Default: True
)

try:
    # This will raise ValueError if invalid
    collector.record_execution(
        workflow_id="wf-1",
        step_id="step-1",
        command="review",
        status="invalid_status",  # Invalid!
        duration_ms=-100,  # Invalid!
        duration_ms=-100,
    )
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Metrics Retention

Automatic cleanup of old metrics:

```python
collector = EnhancedExecutionMetricsCollector(
    retention_days=90,  # Keep metrics for 90 days
)

# Manual cleanup
deleted = collector.cleanup_old_metrics(days_to_keep=30)
print(f"Deleted {deleted} old metric files")
```

## Thread Safety

The enhanced collector is thread-safe:

```python
import threading

collector = EnhancedExecutionMetricsCollector()

def record_metrics():
    for i in range(100):
        collector.record_execution(
            workflow_id=f"wf-{i}",
            step_id="step-1",
            command="review",
            status="success",
            duration_ms=1000.0,
        )

# Multiple threads can safely record metrics
threads = [threading.Thread(target=record_metrics) for _ in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## Statistics Tracking

Track collector performance:

```python
stats = collector.get_stats()
print(f"Total recorded: {stats['total_recorded']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Cache misses: {stats['cache_misses']}")
print(f"Validation errors: {stats['validation_errors']}")
```

## Best Practices

1. **Use Enhanced Collector**: Enable enhanced features for new code
2. **Configure Buffer Size**: Set `write_buffer_size` based on your workload (10-50 is typical)
3. **Set Retention Policy**: Configure `retention_days` to prevent disk space issues
4. **Enable Validation**: Keep `enable_validation=True` for production
5. **Flush Before Exit**: Call `flush()` before application shutdown
6. **Monitor Statistics**: Regularly check `get_stats()` for performance insights
7. **Use Date Ranges**: Use date range filtering for better query performance
8. **Batch Operations**: Use `record_batch()` for bulk recording

## Backward Compatibility

The enhanced system is fully backward compatible:

- Existing code using `ExecutionMetricsCollector` continues to work
- Enhanced features are opt-in via `MetricsCollectorAdapter`
- Data format is compatible (same JSONL structure)
- No migration required for existing metrics files

## Related Documentation

- **Metrics Access Guide**: `docs/METRICS_ACCESS_GUIDE.md` - How to access metrics
- **Execution Metrics**: `tapps_agents/workflow/execution_metrics.py` - Standard collector
- **Analytics Dashboard**: `tapps_agents/core/analytics_dashboard.py` - Analytics system
