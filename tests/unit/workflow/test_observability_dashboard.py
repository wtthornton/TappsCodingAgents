"""
Tests for observability dashboard.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.workflow.event_log import WorkflowEventLog
from tapps_agents.workflow.execution_metrics import (
    ExecutionMetricsCollector,
)
from tapps_agents.workflow.observability_dashboard import ObservabilityDashboard


@pytest.fixture
def event_log(tmp_path: Path) -> WorkflowEventLog:
    """Create a test event log."""
    events_dir = tmp_path / "events"
    return WorkflowEventLog(events_dir=events_dir)


@pytest.fixture
def metrics_collector(tmp_path: Path) -> ExecutionMetricsCollector:
    """Create a test metrics collector."""
    metrics_dir = tmp_path / "metrics"
    return ExecutionMetricsCollector(metrics_dir=metrics_dir)


@pytest.fixture
def dashboard(tmp_path: Path, event_log, metrics_collector) -> ObservabilityDashboard:
    """Create a test dashboard."""
    return ObservabilityDashboard(
        project_root=tmp_path,
        event_log=event_log,
        metrics_collector=metrics_collector,
    )


def test_dashboard_initialization(dashboard):
    """Test dashboard initialization."""
    assert dashboard.project_root is not None
    assert dashboard.event_log is not None
    assert dashboard.metrics_collector is not None


def test_generate_workflow_dashboard(dashboard):
    """Test generating dashboard for a single workflow."""
    workflow_id = "test-workflow-123"
    
    # Mock trace
    trace = {
        "workflow_id": workflow_id,
        "started_at": "2026-01-20T10:00:00Z",
        "ended_at": "2026-01-20T10:05:00Z",
        "steps": [
            {
                "step_id": "step1",
                "agent": "planner",
                "action": "plan",
                "status": "completed",
                "duration_ms": 60000,
            },
        ],
    }
    
    with patch.object(dashboard.event_log, "get_execution_trace", return_value=trace):
        with patch.object(dashboard.event_log, "read_events", return_value=[]):
            with patch.object(dashboard.graph_generator, "generate_graph") as mock_graph:
                mock_graph.return_value.nodes = []
                mock_graph.return_value.edges = []
                mock_graph.return_value.to_dot.return_value = "digraph {}"
                mock_graph.return_value.to_mermaid.return_value = "graph LR"
                
                result = dashboard.generate_dashboard(workflow_id=workflow_id)
                
                assert result["workflow_id"] == workflow_id
                assert "trace" in result
                assert "graph" in result


def test_generate_overview_dashboard(dashboard, tmp_path):
    """Test generating overview dashboard."""
    # Create mock event files
    events_dir = tmp_path / ".tapps-agents" / "workflow-state" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    (events_dir / "workflow1.events.jsonl").write_text("{}")
    (events_dir / "workflow2.events.jsonl").write_text("{}")
    
    dashboard.event_log.events_dir = events_dir
    
    with patch.object(dashboard.event_log, "get_execution_trace") as mock_trace:
        mock_trace.return_value = {
            "workflow_id": "workflow1",
            "steps": [],
        }
        
        result = dashboard.generate_dashboard(workflow_id=None)
        
        assert "workflows" in result
        assert "summary" in result


def test_export_otel_trace(dashboard):
    """Test OpenTelemetry export."""
    workflow_id = "test-workflow-123"
    
    trace = {
        "workflow_id": workflow_id,
        "steps": [
            {
                "step_id": "step1",
                "agent": "planner",
                "action": "plan",
                "started_at": "2026-01-20T10:00:00Z",
                "ended_at": "2026-01-20T10:01:00Z",
                "duration_ms": 60000,
                "status": "completed",
            },
        ],
    }
    
    with patch.object(dashboard.event_log, "get_execution_trace", return_value=trace):
        otel_trace = dashboard.export_otel_trace(workflow_id)
        
        assert "resourceSpans" in otel_trace
        assert len(otel_trace["resourceSpans"]) > 0
        spans = otel_trace["resourceSpans"][0]["scopeSpans"][0]["spans"]
        assert len(spans) == 1
        assert spans[0]["name"] == "planner.plan"


def test_save_dashboard(dashboard, tmp_path):
    """Test saving dashboard to file."""
    dashboard_data = {
        "workflow_id": "test",
        "generated_at": datetime.now(UTC).isoformat() + "Z",
    }
    
    output_path = tmp_path / "dashboard.json"
    dashboard.save_dashboard(dashboard_data, output_path)
    
    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["workflow_id"] == "test"


def test_dashboard_missing_event_log(tmp_path):
    """Test dashboard when event_log is None."""
    from tapps_agents.workflow.execution_metrics import ExecutionMetricsCollector
    
    metrics_collector = ExecutionMetricsCollector(metrics_dir=tmp_path / "metrics")
    dashboard = ObservabilityDashboard(
        project_root=tmp_path,
        event_log=None,
        metrics_collector=metrics_collector,
    )
    
    # Should handle gracefully
    result = dashboard.generate_dashboard(workflow_id="test")
    assert "workflow_id" in result
    assert "trace_error" in result or "trace" not in result


def test_dashboard_missing_metrics_collector(tmp_path):
    """Test dashboard when metrics_collector is None."""
    from tapps_agents.workflow.event_log import WorkflowEventLog
    
    event_log = WorkflowEventLog(events_dir=tmp_path / "events")
    dashboard = ObservabilityDashboard(
        project_root=tmp_path,
        event_log=event_log,
        metrics_collector=None,
    )
    
    # Should handle gracefully
    result = dashboard.generate_dashboard(workflow_id="test")
    assert "workflow_id" in result
    assert "metrics_error" in result or "metrics" not in result


def test_dashboard_empty_workflow(dashboard):
    """Test dashboard with workflow that has no steps."""
    empty_trace = {
        "workflow_id": "test",
        "steps": [],
    }
    
    with patch.object(dashboard.event_log, "get_execution_trace", return_value=empty_trace):
        with patch.object(dashboard.event_log, "read_events", return_value=[]):
            result = dashboard.generate_dashboard(workflow_id="test")
            
            # Should handle empty workflow gracefully
            assert "trace" in result
            assert result["trace"]["steps"] == []


def test_dashboard_missing_trace(dashboard):
    """Test dashboard when trace data is missing."""
    with patch.object(dashboard.event_log, "get_execution_trace", side_effect=FileNotFoundError()):
        result = dashboard.generate_dashboard(workflow_id="test")
        
        # Should have error but not crash
        assert "trace_error" in result or "error" in result


def test_dashboard_corrupt_metrics(dashboard):
    """Test dashboard with corrupt metrics data."""
    # Mock metrics collector to return invalid data
    with patch.object(dashboard.metrics_collector, "get_metrics", side_effect=Exception("Corrupt data")):
        result = dashboard.generate_dashboard(workflow_id="test")
        
        # Should handle gracefully
        assert "metrics_error" in result or "metrics" not in result


def test_export_otel_missing_trace(dashboard):
    """Test OpenTelemetry export when trace is missing."""
    with patch.object(dashboard.event_log, "get_execution_trace", side_effect=FileNotFoundError()):
        from tapps_agents.core.exceptions import WorkflowNotFoundError
        
        with pytest.raises(WorkflowNotFoundError):
            dashboard.export_otel_trace("test")


def test_export_otel_invalid_timestamps(dashboard):
    """Test OpenTelemetry export with invalid timestamp formats."""
    trace = {
        "workflow_id": "test",
        "steps": [
            {
                "step_id": "step1",
                "agent": "planner",
                "action": "plan",
                "started_at": "invalid-timestamp",
                "ended_at": "invalid-timestamp",
            },
        ],
    }
    
    with patch.object(dashboard.event_log, "get_execution_trace", return_value=trace):
        # Should handle invalid timestamps gracefully
        otel_trace = dashboard.export_otel_trace("test")
        assert "resourceSpans" in otel_trace


def test_generate_overview_no_workflows(dashboard, tmp_path):
    """Test overview dashboard when no workflows exist."""
    # Create empty events directory
    events_dir = tmp_path / ".tapps-agents" / "workflow-state" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    
    dashboard.event_log.events_dir = events_dir
    
    result = dashboard.generate_dashboard(workflow_id=None)
    
    assert "workflows" in result
    assert result["workflows"] == []
    assert "summary" in result


def test_generate_dashboard_invalid_workflow_id(dashboard):
    """Test dashboard generation with invalid workflow_id."""
    with pytest.raises(ValueError, match="workflow_id must be a non-empty string"):
        dashboard.generate_dashboard(workflow_id="")
    
    with pytest.raises(ValueError, match="workflow_id must be a non-empty string"):
        dashboard.generate_dashboard(workflow_id=None)  # type: ignore
