# Observability Guide

Complete guide to workflow observability features including execution graphs, metrics correlation, and OpenTelemetry export.

## Overview

TappsCodingAgents provides comprehensive observability for workflow execution through:

- **Execution Graphs**: Visual representation of workflow execution flow
- **Observability Dashboard**: Correlates metrics, traces, and logs
- **OpenTelemetry Export**: Integration with external observability tools

## Execution Graphs

Execution graphs visualize workflow execution as a directed graph showing:
- **Nodes**: Workflow steps with status, duration, and agent information
- **Edges**: Step dependencies and gate transitions
- **Visualization**: DOT, Mermaid, and HTML formats

### Generating Execution Graphs

**CLI Command:**
```bash
tapps-agents observability graph <workflow_id> [--format dot|mermaid|html|summary] [--output <path>]
```

**Examples:**
```bash
# Generate DOT graph (default)
tapps-agents observability graph workflow-123

# Generate Mermaid diagram
tapps-agents observability graph workflow-123 --format mermaid

# Generate HTML view
tapps-agents observability graph workflow-123 --format html

# Generate text summary
tapps-agents observability graph workflow-123 --format summary
```

**Python API:**
```python
from tapps_agents.workflow.event_log import WorkflowEventLog
from tapps_agents.workflow.execution_graph import ExecutionGraphGenerator

event_log = WorkflowEventLog(events_dir=Path(".tapps-agents/workflow-state/events"))
generator = ExecutionGraphGenerator(event_log=event_log)
graph = generator.generate_graph("workflow-123")

# Export to DOT
generator.save_dot(graph, Path("workflow-123.dot"))

# Export to Mermaid
generator.save_mermaid(graph, Path("workflow-123.mmd"))
```

### Automatic Graph Generation

Execution graphs are automatically generated when workflows complete. Graphs are saved to:
- `.tapps-agents/observability/graphs/{workflow_id}.dot` - DOT format
- `.tapps-agents/observability/graphs/{workflow_id}.mmd` - Mermaid format
- `.tapps-agents/observability/graphs/{workflow_id}.html` - HTML view
- `.tapps-agents/observability/graphs/{workflow_id}_summary.txt` - Text summary

## Observability Dashboard

> **Note:** This is the **workflow observability** dashboard (`tapps-agents observability dashboard`) which focuses on individual workflow execution traces, metrics correlation, and OpenTelemetry export. For the **project-wide performance** dashboard with agent, expert, cache, quality, and learning metrics, use `tapps-agents dashboard` (see [Performance Insight Dashboard](../tapps_agents/dashboard/)).

The observability dashboard correlates:
- **Metrics**: Execution duration, retry counts, success rates
- **Traces**: Step-by-step execution flow with timing
- **Logs**: Event log entries with correlation IDs

### Using the Dashboard

**CLI Command:**
```bash
tapps-agents observability dashboard [--workflow-id <id>] [--format json|text|html] [--output <path>]
```

**Examples:**
```bash
# Single workflow dashboard
tapps-agents observability dashboard --workflow-id workflow-123

# Overview of all workflows
tapps-agents observability dashboard

# JSON output for automation
tapps-agents observability dashboard --workflow-id workflow-123 --format json

# HTML dashboard
tapps-agents observability dashboard --workflow-id workflow-123 --format html
```

**Python API:**
```python
from tapps_agents.workflow.observability_dashboard import ObservabilityDashboard
from tapps_agents.workflow.event_log import WorkflowEventLog
from tapps_agents.workflow.execution_metrics import ExecutionMetricsCollector

event_log = WorkflowEventLog(events_dir=Path(".tapps-agents/workflow-state/events"))
metrics_collector = ExecutionMetricsCollector(metrics_dir=Path(".tapps-agents/metrics"))

dashboard = ObservabilityDashboard(
    project_root=Path.cwd(),
    event_log=event_log,
    metrics_collector=metrics_collector,
)

# Generate dashboard
dashboard_data = dashboard.generate_dashboard(workflow_id="workflow-123")
```

### Dashboard Features

**Single Workflow Dashboard:**
- Execution trace with step details
- Execution graph (DOT/Mermaid)
- Metrics aggregation (duration, retries, failures)
- Bottleneck identification
- Event correlation

**Overview Dashboard:**
- Summary statistics (total workflows, completed, failed)
- Workflow list with step counts
- System-wide metrics

## OpenTelemetry Export

Export workflow execution traces to OpenTelemetry format for integration with:
- **Jaeger**: Distributed tracing
- **Zipkin**: Request tracing
- **Datadog APM**: Application performance monitoring
- **New Relic**: Performance monitoring
- **Any OpenTelemetry-compatible tool**

### Exporting Traces

**CLI Command:**
```bash
tapps-agents observability otel <workflow_id> [--output <path>]
```

**Example:**
```bash
tapps-agents observability otel workflow-123
# Saves to: .tapps-agents/observability/otel/workflow-123_trace.json
```

**Python API:**
```python
from tapps_agents.workflow.observability_dashboard import ObservabilityDashboard

dashboard = ObservabilityDashboard(...)
otel_trace = dashboard.export_otel_trace("workflow-123")

# Save to file
import json
Path("trace.json").write_text(json.dumps(otel_trace, indent=2))
```

### OpenTelemetry Format

The exported trace follows OpenTelemetry Protocol (OTLP) format:

```json
{
  "resourceSpans": [
    {
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "tapps-agents"}},
          {"key": "workflow.id", "value": {"stringValue": "workflow-123"}}
        ]
      },
      "scopeSpans": [
        {
          "spans": [
            {
              "traceId": "step1",
              "spanId": "step1",
              "name": "planner.plan",
              "startTimeUnixNano": 1705752000000000000,
              "endTimeUnixNano": 1705752060000000000,
              "attributes": [
                {"key": "step.id", "value": {"stringValue": "step1"}},
                {"key": "agent", "value": {"stringValue": "planner"}},
                {"key": "duration.ms", "value": {"doubleValue": 60000}}
              ],
              "status": {"code": 2}
            }
          ]
        }
      ]
    }
  ]
}
```

## Graph Visualization

### DOT Format (Graphviz)

DOT files can be rendered using Graphviz:

```bash
# Install Graphviz
# Windows: choco install graphviz
# macOS: brew install graphviz
# Linux: apt-get install graphviz

# Render to PNG
dot -Tpng workflow-123.dot -o workflow-123.png

# Render to SVG
dot -Tsvg workflow-123.dot -o workflow-123.svg
```

### Mermaid Format

Mermaid diagrams can be rendered:
- **GitHub/GitLab**: Renders automatically in markdown
- **Mermaid Live Editor**: https://mermaid.live
- **VS Code**: Mermaid extension
- **Documentation**: Embed in markdown files

### HTML View

HTML views include:
- Interactive Mermaid diagram
- Metadata display
- Step details on hover
- Responsive design

## Integration Examples

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Generate execution graph
  run: |
    tapps-agents observability graph ${{ github.run_id }} --format html
    # Upload as artifact
    # Display in PR comments
```

### Monitoring Integration

```python
# Export traces to monitoring system
from tapps_agents.workflow.observability_dashboard import ObservabilityDashboard

dashboard = ObservabilityDashboard(...)
otel_trace = dashboard.export_otel_trace(workflow_id)

# Send to OpenTelemetry collector
import requests
requests.post(
    "http://otel-collector:4318/v1/traces",
    json=otel_trace,
    headers={"Content-Type": "application/json"},
)
```

## Best Practices

1. **Regular Monitoring**: Review dashboards regularly to identify bottlenecks
2. **Graph Analysis**: Use execution graphs to optimize workflow dependencies
3. **Trace Export**: Export traces for long-term analysis and trend tracking
4. **Correlation**: Correlate metrics, traces, and logs for complete picture
5. **Automation**: Integrate observability into CI/CD pipelines

## Error Handling & Resilience

The observability system includes comprehensive error handling:

### Input Validation

All observability functions validate inputs:
- **Workflow ID**: Must be non-empty string
- **Event Log**: Must be valid `WorkflowEventLog` instance
- **Trace Structure**: Validated before processing

### Exception Types

Custom exceptions provide clear error messages:

```python
from tapps_agents.workflow.exceptions import (
    ObservabilityError,          # Base exception
    GraphGenerationError,        # Graph generation failures
    EmptyWorkflowError,          # Workflow has no steps
    InvalidTraceError,           # Invalid trace structure
    DashboardGenerationError,    # Dashboard generation failures
    OpenTelemetryExportError,    # OTel export failures
)
from tapps_agents.core.exceptions import WorkflowNotFoundError
```

### Graceful Degradation

The dashboard handles missing data gracefully:
- **Missing Event Log**: Returns partial dashboard with error messages
- **Missing Metrics**: Dashboard includes available data only
- **Corrupt Traces**: Errors logged, partial results returned
- **Missing Graph**: Graph generation errors included in dashboard

**Example:**
```python
dashboard = ObservabilityDashboard(...)
result = dashboard.generate_dashboard("workflow-123")

# Check for errors
if "trace_error" in result:
    print(f"Trace error: {result['trace_error']}")
if "graph_error" in result:
    print(f"Graph error: {result['graph_error']}")
if "metrics_error" in result:
    print(f"Metrics error: {result['metrics_error']}")

# Dashboard still contains available data
if "trace" in result:
    print(f"Workflow has {len(result['trace']['steps'])} steps")
```

### Parallel Execution Support

Execution graphs handle parallel workflow steps:
- **Dependency Edges**: Built from `step.requires` fields
- **Parallel Steps**: Multiple steps with same dependency shown correctly
- **Sequential Fallback**: Uses event order when dependencies unavailable

## Troubleshooting

**Graph generation fails:**
- Check that event log exists: `.tapps-agents/workflow-state/events/{workflow_id}.events.jsonl`
- Verify workflow completed successfully
- Check file permissions
- **Error**: `WorkflowNotFoundError` - Workflow ID doesn't exist
- **Error**: `EmptyWorkflowError` - Workflow has no steps
- **Error**: `InvalidTraceError` - Trace structure is invalid

**Dashboard shows no data:**
- Ensure workflow executed at least once
- Check metrics directory: `.tapps-agents/metrics/`
- Verify event log directory exists
- **Note**: Dashboard returns partial results with error messages if data unavailable

**OpenTelemetry export fails:**
- Ensure workflow has execution trace
- Check that steps have timing information
- Verify workflow completed (not in progress)
- **Error**: `OpenTelemetryExportError` - Export conversion failed

## Related Documentation

- [Workflow Execution Architecture](FULL_SDLC_EXECUTION_ARCHITECTURE.md)
- [Event Log System](workflow/event_log.py)
- [Execution Metrics](workflow/execution_metrics.py)
