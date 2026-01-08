# How External Projects Can Get Detailed Metrics on TappsCodingAgents Performance

This guide explains how another project can programmatically access detailed metrics about how well TappsCodingAgents is performing.

## Table of Contents

1. [Overview](#overview)
2. [Metrics Storage Locations](#metrics-storage-locations)
3. [Access Methods](#access-methods)
   - [Method 1: Programmatic Access via Python API](#method-1-programmatic-access-via-python-api)
   - [Method 2: Direct File Access](#method-2-direct-file-access-jsonjsonl)
   - [Method 3: Analytics Exporter](#method-3-analytics-exporter)
   - [Method 4: CLI Output](#method-4-cli-output-json-format)
4. [Metrics Summary](#metrics-summary)
5. [Advanced Features](#advanced-features)
   - [Historical Tracking](#historical-tracking)
   - [Real-time Monitoring](#real-time-monitoring)
   - [Alerting and Thresholds](#alerting-and-thresholds)
   - [Comparative Analysis](#comparative-analysis)
   - [Export to External Systems](#export-to-external-systems)
6. [Example: Comprehensive Metrics Report](#example-comprehensive-metrics-report)
7. [Integration Examples](#integration-examples)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Related Documentation](#related-documentation)

## Overview

TappsCodingAgents collects multiple types of metrics across different layers:

1. **Execution Metrics** - Individual workflow step executions
2. **Agent Performance Metrics** - Per-agent success rates, durations, usage
3. **Workflow Metrics** - Workflow-level execution statistics
4. **Code Quality Scores** - 5-metric code quality scoring (complexity, security, maintainability, test coverage, performance)
5. **System Metrics** - Overall system health and resource usage
6. **Performance Metrics** - Multi-agent orchestration performance (parallelism, throughput, efficiency)
7. **Capability Metrics** - Agent capability performance (success rates, quality scores, usage patterns)
8. **Learning Metrics** - Agent learning system metrics (pattern extraction, refinement history)
9. **Context7 Cache Metrics** - KB cache performance (hit rates, response times, library usage)
10. **Quality Artifacts** - Versioned quality analysis artifacts with tool results
11. **Code Artifacts** - Versioned code generation artifacts with change tracking

## Metrics Storage Locations

All metrics are stored in the project's `.tapps-agents/` directory:

- **Execution Metrics**: `.tapps-agents/metrics/executions_YYYY-MM-DD.jsonl` (JSONL format, one metric per line)
- **Analytics Data**: `.tapps-agents/analytics/` (history files, metrics.json)
- **Performance Metrics**: `.tapps-agents/performance-{task_id}.json` (per-task performance data)
- **Review Results**: Review outputs include scoring data in JSON format
- **Capability Metrics**: `.tapps-agents/capabilities/capabilities.json` (capability registry)
- **Learning Data**: `.tapps-agents/learning/` (patterns, refinements, task memory)
- **Context7 Cache**: `.tapps-agents/kb/context7-cache/` (cache structure, analytics)
- **Quality Artifacts**: `.tapps-agents/artifacts/quality/` (versioned quality artifacts)
- **Code Artifacts**: `.tapps-agents/artifacts/code/` (versioned code artifacts)

## Access Methods

### Method 1: Programmatic Access via Python API

The recommended way for external projects to access metrics is through the Python API:

#### 1.1 Execution Metrics Collector

Access individual workflow step execution metrics:

```python
from pathlib import Path
from tapps_agents.workflow.execution_metrics import ExecutionMetricsCollector

# Initialize collector
collector = ExecutionMetricsCollector(
    metrics_dir=Path(".tapps-agents/metrics"),
    project_root=Path(".")
)

# Get metrics summary
summary = collector.get_summary()
# Returns: {
#     "total_executions": 150,
#     "success_rate": 0.95,
#     "average_duration_ms": 1234.5,
#     "total_retries": 5,
#     "by_status": {"success": 142, "failed": 8, "timeout": 0, "cancelled": 0}
# }

# Get filtered metrics
metrics = collector.get_metrics(
    workflow_id="workflow-123",  # Optional filter
    step_id="step-1",            # Optional filter
    status="success",            # Optional filter
    limit=100
)
# Returns list of ExecutionMetric objects with:
# - execution_id, workflow_id, step_id, command
# - status, duration_ms, retry_count
# - started_at, completed_at, error_message
```

#### 1.2 Analytics Dashboard API

Access comprehensive analytics including agent performance, workflow metrics, and trends:

```python
from pathlib import Path
from tapps_agents.core.analytics_dashboard import AnalyticsDashboard

# Initialize dashboard
dashboard = AnalyticsDashboard(analytics_dir=Path(".tapps-agents/analytics"))

# Get comprehensive dashboard data (all metrics)
data = dashboard.get_dashboard_data()
# Returns: {
#     "system": {...},      # SystemMetrics
#     "agents": [...],      # List of AgentPerformanceMetrics
#     "workflows": [...],   # List of WorkflowMetrics
#     "trends": {
#         "agent_duration": [...],
#         "workflow_duration": [...],
#         "agent_success_rate": [...],
#         "workflow_success_rate": [...]
#     },
#     "timestamp": "2025-01-16T12:00:00"
# }

# Get agent performance metrics
agent_metrics = dashboard.get_agent_performance(agent_id="reviewer")
# Returns list of dicts with:
# - agent_id, agent_name
# - total_executions, successful_executions, failed_executions
# - average_duration, min_duration, max_duration, total_duration
# - last_execution, success_rate

# Get workflow performance metrics
workflow_metrics = dashboard.get_workflow_performance(workflow_id="workflow-123")
# Returns list of dicts with:
# - workflow_id, workflow_name
# - total_executions, successful_executions, failed_executions
# - average_duration, average_steps
# - last_execution, success_rate

# Get system status
system_metrics = dashboard.get_system_status()
# Returns dict with:
# - timestamp, total_agents, active_workflows
# - completed_workflows_today, failed_workflows_today
# - average_workflow_duration
# - cpu_usage, memory_usage, disk_usage (if available)
```

#### 1.3 Analytics Accessor (Recommended for Cursor Integration)

For Cursor integration with caching support:

```python
from pathlib import Path
from tapps_agents.workflow.analytics_accessor import CursorAnalyticsAccessor

# Initialize accessor (includes caching)
accessor = CursorAnalyticsAccessor(
    analytics_dir=Path(".tapps-agents/analytics"),
    cache_ttl_seconds=60,  # Cache for 60 seconds
    enable_cache=True
)

# Get system metrics (cached)
system_metrics = accessor.get_system_metrics(use_cache=True)

# Get agent metrics with time filtering
agent_metrics = accessor.get_agent_metrics(
    agent_id="reviewer",  # Optional filter
    days=30,              # Last 30 days
    use_cache=True
)

# Get workflow metrics
workflow_metrics = accessor.get_workflow_metrics(
    workflow_id="workflow-123",  # Optional filter
    days=7,                      # Last 7 days
    use_cache=True
)

# Get trend data
trends = accessor.get_trends(
    metric_type="agent_duration",  # or "workflow_duration", "agent_success_rate", etc.
    days=30,
    use_cache=True
)

# Get comprehensive dashboard data
dashboard_data = accessor.get_dashboard_data(use_cache=True)

# Aggregate metrics
aggregated = accessor.aggregate_metrics(
    metrics=agent_metrics,
    aggregation_type="summary"  # or "totals", "averages"
)
# Returns summary statistics: count, totals, averages, min, max, success_rate
```

#### 1.4 Code Quality Scores from Reviewer Agent

Access code quality scores from reviewer agent outputs:

```python
from pathlib import Path
from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tapps_agents.core.config import load_config

# Initialize reviewer agent
config = load_config(Path(".tapps-agents/config.yaml"))
reviewer = ReviewerAgent(config=config)

# Run review and get scores
result = await reviewer.review_file(
    file_path=Path("src/main.py"),
    include_scoring=True,  # Essential for getting scores
    include_llm_feedback=False  # Optional
)

# Extract scoring data
scoring = result.get("scoring", {})
scores = scoring.get("scores", {})

# Access individual metrics (0-10 scale, except overall_score is 0-100)
overall_score = scores.get("overall_score", 0.0)  # 0-100
complexity_score = scores.get("complexity_score", 0.0)  # 0-10
security_score = scores.get("security_score", 0.0)  # 0-10
maintainability_score = scores.get("maintainability_score", 0.0)  # 0-10
test_coverage_score = scores.get("test_coverage_score", 0.0)  # 0-10
performance_score = scores.get("performance_score", 0.0)  # 0-10

# Quality gate evaluation
from tapps_agents.quality.quality_gates import QualityGate, QualityThresholds

gate = QualityGate()
gate_result = gate.evaluate_from_review_result(result)
# Returns QualityGateResult with:
# - passed, overall_passed, security_passed
# - maintainability_passed, complexity_passed
# - test_coverage_passed, performance_passed
# - failures, warnings
# - scores dict, thresholds
```

#### 1.5 Capability Metrics (Agent Learning System)

Access agent capability performance metrics:

```python
from pathlib import Path
from tapps_agents.core.capability_registry import CapabilityRegistry
from tapps_agents.core.config import load_config

# Initialize capability registry
config = load_config(Path(".tapps-agents/config.yaml"))
registry = CapabilityRegistry(config=config)

# Get capability metrics
capability_id = "code_generation"
capability = registry.get_capability(capability_id)

if capability:
    metrics = {
        "capability_id": capability.capability_id,
        "agent_id": capability.agent_id,
        "success_rate": capability.success_rate,  # 0.0 to 1.0
        "average_duration": capability.average_duration,  # seconds
        "quality_score": capability.quality_score,  # 0.0 to 1.0
        "usage_count": capability.usage_count,
        "last_improved": capability.last_improved.isoformat() if capability.last_improved else None,
        "refinement_history": [r.to_dict() for r in capability.refinement_history],
    }

# Get all capabilities
all_capabilities = registry.metrics
for cap_id, metric in all_capabilities.items():
    print(f"{cap_id}: {metric.success_rate:.2%} success, {metric.quality_score:.2f} quality")
```

#### 1.6 Learning Dashboard Metrics

Access learning system metrics:

```python
from pathlib import Path
from tapps_agents.core.learning_dashboard import LearningDashboard
from tapps_agents.core.capability_registry import CapabilityRegistry
from tapps_agents.core.config import load_config

# Initialize learning dashboard
config = load_config(Path(".tapps-agents/config.yaml"))
registry = CapabilityRegistry(config=config)
dashboard = LearningDashboard(capability_registry=registry)

# Get capability metrics
capability_metrics = dashboard.get_capability_metrics(capability_id="code_generation")
# Returns: {
#     "capability_id": "code_generation",
#     "found": True,
#     "usage_count": 42,
#     "success_rate": 0.85,
#     "quality_score": 0.92,
#     "average_duration": 1.23,
#     "last_used": "2025-01-16T12:00:00"
# }

# Get learning trends
trends = dashboard.get_learning_trends(days=30, capability_id="code_generation")
# Returns trend data with success_rate, quality_score over time

# Get security metrics
security_metrics = dashboard.get_security_metrics()
# Returns security-related learning metrics
```

#### 1.7 Context7 Cache Metrics

Access Context7 KB cache performance metrics:

```python
from pathlib import Path
from tapps_agents.context7.analytics_dashboard import AnalyticsDashboard
from tapps_agents.context7.analytics import Analytics
from tapps_agents.context7.cache_structure import CacheStructure
from tapps_agents.context7.metadata import MetadataManager

# Initialize Context7 analytics
cache_root = Path(".tapps-agents/kb/context7-cache")
analytics = Analytics(cache_root=cache_root)
cache_structure = CacheStructure(cache_root=cache_root)
metadata = MetadataManager(cache_root=cache_root)

dashboard = AnalyticsDashboard(
    analytics=analytics,
    cache_structure=cache_structure,
    metadata_manager=metadata
)

# Get dashboard metrics
metrics = dashboard.get_dashboard_metrics()
# Returns DashboardMetrics with:
# - overall_metrics: total_entries, cache_hits, cache_misses, hit_rate, api_calls, avg_response_time_ms
# - skill_usage: per-skill usage statistics
# - top_libraries: most accessed libraries
# - cache_health: cache health indicators
# - performance_trends: historical performance data

# Export dashboard JSON
dashboard_file = dashboard.export_dashboard_json()
# Saves to .tapps-agents/kb/context7-cache/dashboard/dashboard-{timestamp}.json

# Generate text report
report = dashboard.generate_dashboard_report()
print(report)
```

### Method 2: Direct File Access (JSON/JSONL)

For simple scripts or non-Python integrations, metrics can be read directly from files:

#### 2.1 Execution Metrics (JSONL)

```python
import json
from pathlib import Path

# Read execution metrics
metrics_file = Path(".tapps-agents/metrics/executions_2025-01-16.jsonl")
metrics = []
with open(metrics_file, "r", encoding="utf-8") as f:
    for line in f:
        metric = json.loads(line.strip())
        metrics.append(metric)
        # Each metric contains:
        # - execution_id, workflow_id, step_id, command
        # - status, duration_ms, retry_count
        # - started_at, completed_at, error_message
```

#### 2.2 Analytics History (JSONL)

```python
import json
from pathlib import Path
from datetime import datetime, timedelta

# Read agent execution history
date = datetime.now().strftime("%Y-%m-%d")
history_file = Path(f".tapps-agents/analytics/history/agents-{date}.jsonl")

agent_executions = []
with open(history_file, "r", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line.strip())
        agent_executions.append(record)
        # Each record contains:
        # - agent_id, agent_name
        # - duration, success
        # - timestamp

# Read workflow execution history
workflow_file = Path(f".tapps-agents/analytics/history/workflows-{date}.jsonl")
workflow_executions = []
with open(workflow_file, "r", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line.strip())
        workflow_executions.append(record)
        # Each record contains:
        # - workflow_id, workflow_name
        # - duration, steps, success
        # - timestamp
```

#### 2.3 Performance Metrics (JSON)

```python
import json
from pathlib import Path

# Read performance metrics
metrics_file = Path(".tapps-agents/performance-task-123.json")
with open(metrics_file, "r", encoding="utf-8") as f:
    metrics = json.load(f)
    # Contains:
    # - task_id, start_time, end_time, total_duration
    # - agents: {agent_id: {duration, success, error, ...}}
    # - parallelism: {max_parallel, average_parallel, total_agents}
    # - throughput: {agents_per_second, total_agents}
    # - efficiency: {sequential_time_estimate, parallel_time_actual, speedup}
```

### Method 3: Analytics Exporter

Export analytics data to JSON, Markdown, or Text formats:

```python
from pathlib import Path
from tapps_agents.workflow.analytics_alerts import AnalyticsExporter

# Initialize exporter
exporter = AnalyticsExporter()

# Export as JSON
json_file = exporter.export_json(
    output_file=Path(".tapps-agents/analytics_export.json"),
    include_trends=True
)

# Export as Markdown report
md_file = exporter.export_markdown(
    output_file=Path(".tapps-agents/analytics_report.md")
)

# Export as plain text
txt_file = exporter.export_text(
    output_file=Path(".tapps-agents/analytics_report.txt")
)
```

Or use the integration function:

```python
from pathlib import Path
from tapps_agents.workflow.analytics_integration import export_analytics

# Export analytics in various formats
export_analytics(format="json", project_root=Path("."))
export_analytics(format="markdown", project_root=Path("."))
export_analytics(format="text", project_root=Path("."))
```

### Method 4: CLI Output (JSON Format)

For quick access via command line, use JSON output format:

```bash
# Get review results with scores (JSON)
tapps-agents reviewer review src/main.py --format json

# Output includes:
# {
#   "file": "src/main.py",
#   "scoring": {
#     "scores": {
#       "overall_score": 85.5,
#       "complexity_score": 8.2,
#       "security_score": 9.0,
#       "maintainability_score": 7.8,
#       "test_coverage_score": 8.5,
#       "performance_score": 8.0
#     },
#     "detailed": {...}
#   },
#   "feedback": {...},
#   "quality_gate": {...}
# }

# Get batch review results
tapps-agents reviewer review --pattern "**/*.py" --format json --output reviews.json
```

## Metrics Summary

### Execution Metrics
- **Location**: `.tapps-agents/metrics/executions_*.jsonl`
- **Format**: JSONL (one JSON object per line)
- **Content**: Individual workflow step executions
- **Fields**: execution_id, workflow_id, step_id, command, status, duration_ms, retry_count, timestamps, error_message

### Agent Performance Metrics
- **Location**: `.tapps-agents/analytics/history/agents-*.jsonl` (raw), AnalyticsDashboard API (aggregated)
- **Content**: Per-agent execution statistics
- **Metrics**: total_executions, successful_executions, failed_executions, average_duration, success_rate, last_execution

### Workflow Performance Metrics
- **Location**: `.tapps-agents/analytics/history/workflows-*.jsonl` (raw), AnalyticsDashboard API (aggregated)
- **Content**: Per-workflow execution statistics
- **Metrics**: total_executions, successful_executions, failed_executions, average_duration, average_steps, success_rate

### Code Quality Scores
- **Location**: Reviewer agent output (JSON)
- **Metrics**: 5-metric scoring system
  - **Overall Score** (0-100): Weighted composite of all metrics
  - **Complexity Score** (0-10): Cyclomatic complexity (lower is better, inverted to 0-10 scale)
  - **Security Score** (0-10): Vulnerability detection (Bandit + heuristics)
  - **Maintainability Score** (0-10): Maintainability Index (Radon MI)
  - **Test Coverage Score** (0-10): Coverage percentage + heuristic analysis
  - **Performance Score** (0-10): Static analysis (function size, nesting depth, patterns)

### System Metrics
- **Location**: AnalyticsDashboard API
- **Content**: System-wide health metrics
- **Metrics**: total_agents, active_workflows, completed_workflows_today, failed_workflows_today, average_workflow_duration, cpu_usage, memory_usage, disk_usage

### Performance Metrics (Multi-Agent)
- **Location**: `.tapps-agents/performance-*.json`
- **Content**: Multi-agent orchestration performance
- **Metrics**: parallelism (max_parallel, average_parallel, total_agents), throughput (agents_per_second), efficiency (speedup ratio)

### Capability Metrics
- **Location**: `.tapps-agents/capabilities/capabilities.json`
- **Content**: Agent capability performance tracking
- **Metrics**: success_rate, average_duration, quality_score, usage_count, refinement_history

### Learning Metrics
- **Location**: `.tapps-agents/learning/` (various files)
- **Content**: Agent learning system metrics
- **Metrics**: pattern extraction, refinement history, task memory, learning trends

### Context7 Cache Metrics
- **Location**: `.tapps-agents/kb/context7-cache/dashboard/`
- **Content**: KB cache performance analytics
- **Metrics**: cache_hits, cache_misses, hit_rate, api_calls, avg_response_time_ms, skill_usage, top_libraries

### Quality Artifacts
- **Location**: `.tapps-agents/artifacts/quality/`
- **Content**: Versioned quality analysis artifacts
- **Metrics**: tool results, aggregated scores, total_issues, overall_score

### Code Artifacts
- **Location**: `.tapps-agents/artifacts/code/`
- **Content**: Versioned code generation artifacts
- **Metrics**: files_modified, lines_added/removed, functions_added, review_scores

## Advanced Features

### Historical Tracking

Track metrics over time for trend analysis:

```python
from pathlib import Path
from datetime import datetime, timedelta
from tapps_agents.workflow.analytics_accessor import CursorAnalyticsAccessor
import json

def track_code_quality_history(file_path: Path, days: int = 30):
    """Track code quality scores over time."""
    scores_history = []
    
    # Read historical review results (if stored)
    artifacts_dir = Path(".tapps-agents/artifacts/quality")
    for artifact_file in sorted(artifacts_dir.glob("*.json")):
        with open(artifact_file, "r", encoding="utf-8") as f:
            artifact = json.load(f)
            if artifact.get("file") == str(file_path):
                scores_history.append({
                    "timestamp": artifact.get("timestamp"),
                    "overall_score": artifact.get("overall_score"),
                    "scores": artifact.get("scores", {})
                })
    
    return scores_history

def track_agent_performance_trends(agent_id: str, days: int = 30):
    """Track agent performance trends over time."""
    accessor = CursorAnalyticsAccessor()
    
    # Get trend data
    trends = accessor.get_trends(
        metric_type="agent_duration",
        days=days
    )
    
    # Filter by agent if needed
    agent_metrics = accessor.get_agent_metrics(
        agent_id=agent_id,
        days=days
    )
    
    return {
        "trends": trends,
        "current_metrics": agent_metrics[0] if agent_metrics else None
    }
```

### Real-time Monitoring

Monitor metrics in real-time:

```python
from pathlib import Path
import time
from tapps_agents.workflow.execution_metrics import ExecutionMetricsCollector

def monitor_executions(project_root: Path, interval_seconds: int = 5):
    """Monitor execution metrics in real-time."""
    collector = ExecutionMetricsCollector(project_root=project_root)
    
    last_count = 0
    while True:
        summary = collector.get_summary()
        current_count = summary["total_executions"]
        
        if current_count > last_count:
            new_executions = current_count - last_count
            print(f"[{datetime.now()}] {new_executions} new executions")
            print(f"  Success rate: {summary['success_rate']:.2%}")
            print(f"  Avg duration: {summary['average_duration_ms']:.1f}ms")
            last_count = current_count
        
        time.sleep(interval_seconds)
```

### Alerting and Thresholds

Set up alerts based on metric thresholds:

```python
from pathlib import Path
from tapps_agents.workflow.analytics_accessor import CursorAnalyticsAccessor
from tapps_agents.workflow.analytics_alerts import AnalyticsAlertManager

def setup_quality_alerts(project_root: Path):
    """Set up alerts for quality metrics."""
    accessor = CursorAnalyticsAccessor(
        analytics_dir=project_root / ".tapps-agents/analytics"
    )
    alert_manager = AnalyticsAlertManager(accessor=accessor)
    
    # Define alert rules
    alert_manager.add_alert(
        name="low_success_rate",
        condition=lambda metrics: metrics.get("success_rate", 1.0) < 0.90,
        severity="warning",
        message="Agent success rate below 90%"
    )
    
    alert_manager.add_alert(
        name="high_failure_rate",
        condition=lambda metrics: metrics.get("failed_executions", 0) > 10,
        severity="critical",
        message="High number of failed executions detected"
    )
    
    # Check alerts
    alerts = alert_manager.check_alerts()
    for alert in alerts:
        print(f"[{alert.severity.upper()}] {alert.message}")
        print(f"  Triggered at: {alert.timestamp}")
```

### Comparative Analysis

Compare metrics across time periods or workflows:

```python
from pathlib import Path
from datetime import datetime, timedelta
from tapps_agents.workflow.analytics_accessor import CursorAnalyticsAccessor

def compare_periods(project_root: Path, days_before: int = 7, days_after: int = 7):
    """Compare metrics between two time periods."""
    accessor = CursorAnalyticsAccessor(
        analytics_dir=project_root / ".tapps-agents/analytics"
    )
    
    # Get metrics for both periods
    before_metrics = accessor.get_agent_metrics(days=days_before)
    after_metrics = accessor.get_agent_metrics(days=days_after)
    
    # Aggregate for comparison
    before_agg = accessor.aggregate_metrics(before_metrics, "summary")
    after_agg = accessor.aggregate_metrics(after_metrics, "summary")
    
    # Calculate changes
    success_rate_change = after_agg["success_rate"] - before_agg["success_rate"]
    avg_duration_change = after_agg["average_duration"] - before_agg["average_duration"]
    
    return {
        "before": before_agg,
        "after": after_agg,
        "changes": {
            "success_rate": success_rate_change,
            "average_duration": avg_duration_change,
        }
    }

def compare_workflows(workflow_id_1: str, workflow_id_2: str):
    """Compare two workflows."""
    accessor = CursorAnalyticsAccessor()
    
    wf1_metrics = accessor.get_workflow_metrics(workflow_id=workflow_id_1)
    wf2_metrics = accessor.get_workflow_metrics(workflow_id=workflow_id_2)
    
    if wf1_metrics and wf2_metrics:
        wf1 = wf1_metrics[0]
        wf2 = wf2_metrics[0]
        
        return {
            "workflow_1": {
                "success_rate": wf1["success_rate"],
                "avg_duration": wf1["average_duration"],
                "total_executions": wf1["total_executions"]
            },
            "workflow_2": {
                "success_rate": wf2["success_rate"],
                "avg_duration": wf2["average_duration"],
                "total_executions": wf2["total_executions"]
            },
            "comparison": {
                "success_rate_diff": wf1["success_rate"] - wf2["success_rate"],
                "duration_diff": wf1["average_duration"] - wf2["average_duration"]
            }
        }
```

### Export to External Systems

Export metrics to external monitoring systems:

```python
from pathlib import Path
import json
import requests  # For HTTP APIs
from tapps_agents.workflow.analytics_accessor import CursorAnalyticsAccessor

def export_to_prometheus(project_root: Path, prometheus_url: str):
    """Export metrics to Prometheus-compatible format."""
    accessor = CursorAnalyticsAccessor(
        analytics_dir=project_root / ".tapps-agents/analytics"
    )
    
    metrics = accessor.get_dashboard_data()
    
    # Convert to Prometheus format
    prometheus_metrics = []
    
    # Agent metrics
    for agent in metrics.get("agents", []):
        prometheus_metrics.append(
            f'tapps_agent_success_rate{{agent="{agent["agent_id"]}"}} '
            f'{agent["success_rate"]}'
        )
        prometheus_metrics.append(
            f'tapps_agent_duration_seconds{{agent="{agent["agent_id"]}"}} '
            f'{agent["average_duration"]}'
        )
    
    # Push to Prometheus
    response = requests.post(
        f"{prometheus_url}/metrics",
        data="\n".join(prometheus_metrics)
    )
    return response.status_code == 200

def export_to_datadog(project_root: Path, api_key: str):
    """Export metrics to Datadog."""
    accessor = CursorAnalyticsAccessor(
        analytics_dir=project_root / ".tapps-agents/analytics"
    )
    
    metrics = accessor.get_dashboard_data()
    
    # Format for Datadog API
    datadog_metrics = []
    for agent in metrics.get("agents", []):
        datadog_metrics.append({
            "metric": "tapps.agent.success_rate",
            "points": [[int(time.time()), agent["success_rate"]]],
            "tags": [f"agent:{agent['agent_id']}"]
        })
    
    # Send to Datadog
    response = requests.post(
        "https://api.datadoghq.com/api/v1/series",
        headers={"DD-API-KEY": api_key},
        json={"series": datadog_metrics}
    )
    return response.status_code == 202
```

## Example: Comprehensive Metrics Report

Here's a complete example of how to generate a comprehensive metrics report:

```python
from pathlib import Path
from datetime import datetime
from tapps_agents.workflow.analytics_accessor import CursorAnalyticsAccessor
from tapps_agents.workflow.execution_metrics import ExecutionMetricsCollector

def generate_metrics_report(project_root: Path, output_file: Path):
    """Generate comprehensive metrics report."""
    
    # Initialize collectors
    analytics = CursorAnalyticsAccessor(analytics_dir=project_root / ".tapps-agents/analytics")
    executions = ExecutionMetricsCollector(project_root=project_root)
    
    # Collect all metrics
    report = {
        "generated_at": datetime.now().isoformat(),
        "system": analytics.get_system_metrics(),
        "agents": analytics.get_agent_metrics(days=30),
        "workflows": analytics.get_workflow_metrics(days=30),
        "executions": executions.get_summary(),
        "trends": {
            "agent_duration": analytics.get_trends("agent_duration", days=30),
            "workflow_duration": analytics.get_trends("workflow_duration", days=30),
            "agent_success_rate": analytics.get_trends("agent_success_rate", days=30),
            "workflow_success_rate": analytics.get_trends("workflow_success_rate", days=30),
        }
    }
    
    # Aggregate agent metrics
    agent_aggregate = analytics.aggregate_metrics(
        report["agents"],
        aggregation_type="summary"
    )
    report["agent_summary"] = agent_aggregate
    
    # Aggregate workflow metrics
    workflow_aggregate = analytics.aggregate_metrics(
        report["workflows"],
        aggregation_type="summary"
    )
    report["workflow_summary"] = workflow_aggregate
    
    # Write report
    import json
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    
    return report

# Usage
project_root = Path(".")
output_file = Path(".tapps-agents/metrics_report.json")
report = generate_metrics_report(project_root, output_file)
```

## Integration Examples

### Example 1: CI/CD Quality Gate

```python
from pathlib import Path
from tapps_agents.workflow.execution_metrics import ExecutionMetricsCollector

def check_ci_quality_gate(project_root: Path, min_success_rate: float = 0.90):
    """Check if metrics meet CI quality gate."""
    collector = ExecutionMetricsCollector(project_root=project_root)
    summary = collector.get_summary()
    
    success_rate = summary["success_rate"]
    if success_rate < min_success_rate:
        raise ValueError(
            f"Quality gate failed: success rate {success_rate:.2%} "
            f"below threshold {min_success_rate:.2%}"
        )
    
    return True
```

### Example 2: Dashboard Integration

```python
from pathlib import Path
from tapps_agents.core.analytics_dashboard import AnalyticsDashboard

def get_dashboard_data(project_root: Path):
    """Get data for external dashboard."""
    dashboard = AnalyticsDashboard(
        analytics_dir=project_root / ".tapps-agents/analytics"
    )
    return dashboard.get_dashboard_data()
```

### Example 3: Code Quality Tracking

```python
from pathlib import Path
from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tapps_agents.core.config import load_config

async def track_code_quality(file_path: Path, project_root: Path):
    """Track code quality scores over time."""
    config = load_config(project_root / ".tapps-agents/config.yaml")
    reviewer = ReviewerAgent(config=config)
    
    result = await reviewer.review_file(
        file_path=file_path,
        include_scoring=True
    )
    
    scores = result.get("scoring", {}).get("scores", {})
    return {
        "file": str(file_path),
        "timestamp": datetime.now().isoformat(),
        "overall_score": scores.get("overall_score", 0.0),
        "complexity": scores.get("complexity_score", 0.0),
        "security": scores.get("security_score", 0.0),
        "maintainability": scores.get("maintainability_score", 0.0),
        "test_coverage": scores.get("test_coverage_score", 0.0),
        "performance": scores.get("performance_score", 0.0),
    }
```

## Best Practices

1. **Use Analytics Accessor**: For Cursor integration or frequent queries, use `CursorAnalyticsAccessor` for built-in caching
2. **Filter by Time Range**: Use `days` parameter to limit data to recent metrics
3. **Aggregate Large Datasets**: Use `aggregate_metrics()` for summary statistics
4. **Handle Missing Data**: Always check if metrics files/directories exist before accessing
5. **Cache Results**: Use accessor caching or implement your own caching for frequently accessed metrics
6. **Export Periodically**: Generate periodic reports for historical tracking
7. **Monitor Trends**: Use trend data to identify performance degradation
8. **Batch Queries**: When querying multiple metrics, use `get_dashboard_data()` instead of individual calls
9. **Error Handling**: Wrap metric access in try-except blocks to handle missing or corrupted data gracefully
10. **Performance**: For large datasets, use pagination (limit parameter) and process in batches
11. **Time Zones**: Be aware that timestamps are in UTC; convert to local time if needed for display
12. **Data Retention**: Consider archiving old metrics files to prevent disk space issues

## Troubleshooting

### Common Issues

#### Issue: Metrics files not found

**Symptoms**: `FileNotFoundError` when accessing metrics files

**Solutions**:
```python
from pathlib import Path

# Check if metrics directory exists
metrics_dir = Path(".tapps-agents/metrics")
if not metrics_dir.exists():
    print("Metrics directory not found. Run workflows to generate metrics.")
    # Create directory if needed
    metrics_dir.mkdir(parents=True, exist_ok=True)
```

#### Issue: Empty or missing metrics

**Symptoms**: Metrics return empty lists or zero values

**Solutions**:
- Ensure workflows have been executed (metrics are generated during workflow execution)
- Check that metrics collection is enabled in config
- Verify file permissions allow writing to `.tapps-agents/` directory

#### Issue: Stale cache data

**Symptoms**: Metrics appear outdated

**Solutions**:
```python
# Invalidate cache
accessor = CursorAnalyticsAccessor()
accessor.invalidate_cache()  # Invalidate all cache
accessor.invalidate_cache("agents")  # Invalidate specific query type
```

#### Issue: Performance issues with large datasets

**Symptoms**: Slow queries or memory issues

**Solutions**:
```python
# Use pagination
metrics = collector.get_metrics(limit=100)  # Process in batches

# Filter early
metrics = collector.get_metrics(
    workflow_id="specific-workflow",  # Filter before loading
    status="success",
    limit=50
)

# Use aggregation instead of loading all data
summary = collector.get_summary()  # Pre-aggregated
```

#### Issue: Encoding errors on Windows

**Symptoms**: `UnicodeDecodeError` when reading JSON files

**Solutions**:
```python
# Always specify UTF-8 encoding
with open(metrics_file, "r", encoding="utf-8") as f:
    data = json.load(f)
```

### Debugging Tips

1. **Enable Logging**: Set logging level to DEBUG to see metric collection details
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Verify Metrics Collection**: Check that metrics are being written
   ```python
   metrics_dir = Path(".tapps-agents/metrics")
   files = list(metrics_dir.glob("*.jsonl"))
   print(f"Found {len(files)} metrics files")
   ```

3. **Validate JSON Structure**: Ensure JSON files are valid
   ```python
   import json
   try:
       with open(metrics_file, "r", encoding="utf-8") as f:
           for line in f:
               json.loads(line)  # Validate each line
   except json.JSONDecodeError as e:
       print(f"Invalid JSON at line: {e}")
   ```

4. **Check File Permissions**: Ensure read/write access
   ```python
   metrics_dir = Path(".tapps-agents/metrics")
   print(f"Readable: {metrics_dir.is_dir() and os.access(metrics_dir, os.R_OK)}")
   print(f"Writable: {metrics_dir.is_dir() and os.access(metrics_dir, os.W_OK)}")
   ```

## Related Documentation

- **Code Scoring System**: See `tapps_agents/agents/reviewer/scoring.py` for scoring algorithm details
- **Quality Gates**: See `tapps_agents/quality/quality_gates.py` for quality gate evaluation
- **Analytics Dashboard**: See `tapps_agents/core/analytics_dashboard.py` for full API documentation
- **Execution Metrics**: See `tapps_agents/workflow/execution_metrics.py` for execution tracking
- **Performance Monitoring**: See `tapps_agents/core/performance_monitor.py` for multi-agent performance
- **Capability Registry**: See `tapps_agents/core/capability_registry.py` for capability metrics
- **Learning Dashboard**: See `tapps_agents/core/learning_dashboard.py` for learning metrics
- **Context7 Analytics**: See `tapps_agents/context7/analytics_dashboard.py` for KB cache metrics
- **Analytics Exporter**: See `tapps_agents/workflow/analytics_alerts.py` for export functionality
- **Quality Artifacts**: See `tapps_agents/workflow/quality_artifact.py` for artifact structure
- **Code Artifacts**: See `tapps_agents/workflow/code_artifact.py` for code artifact structure

## Quick Reference

### Most Common Use Cases

**Get overall system health:**
```python
from tapps_agents.core.analytics_dashboard import AnalyticsDashboard
dashboard = AnalyticsDashboard()
system = dashboard.get_system_status()
```

**Get agent performance:**
```python
from tapps_agents.workflow.analytics_accessor import CursorAnalyticsAccessor
accessor = CursorAnalyticsAccessor()
agents = accessor.get_agent_metrics(days=7)
```

**Get code quality scores:**
```python
from tapps_agents.agents.reviewer.agent import ReviewerAgent
reviewer = ReviewerAgent(config=config)
result = await reviewer.review_file(file_path, include_scoring=True)
scores = result["scoring"]["scores"]
```

**Export metrics:**
```python
from tapps_agents.workflow.analytics_alerts import AnalyticsExporter
exporter = AnalyticsExporter()
exporter.export_json(output_file=Path("metrics.json"))
```

### Metric Scales Reference

- **Overall Score**: 0-100 (higher is better)
- **Individual Scores** (complexity, security, etc.): 0-10 (higher is better)
- **Success Rate**: 0.0-1.0 (1.0 = 100%)
- **Duration**: Seconds (lower is better for execution time)
- **Quality Score** (capabilities): 0.0-1.0 (higher is better)
- **Hit Rate** (cache): 0.0-1.0 (1.0 = 100% cache hits)

### File Format Reference

- **JSONL**: One JSON object per line (for streaming/append operations)
- **JSON**: Standard JSON format (for complete data structures)
- **Timestamps**: ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
- **Encoding**: UTF-8 (always specify explicitly on Windows)