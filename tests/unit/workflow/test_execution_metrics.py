"""
Unit tests for execution metrics collection.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from tapps_agents.workflow.execution_metrics import (
    ExecutionMetric,
    ExecutionMetricsCollector,
)


def test_execution_metric_to_dict():
    """Test ExecutionMetric serialization."""
    metric = ExecutionMetric(
        execution_id="test-id",
        workflow_id="test-workflow",
        step_id="test-step",
        command="test-command",
        status="success",
        duration_ms=1000.0,
        retry_count=0,
        started_at="2025-01-27T00:00:00",
        completed_at="2025-01-27T00:00:01",
    )
    data = metric.to_dict()
    assert data["execution_id"] == "test-id"
    assert data["status"] == "success"
    assert data["duration_ms"] == 1000.0


def test_execution_metric_from_dict():
    """Test ExecutionMetric deserialization."""
    data = {
        "execution_id": "test-id",
        "workflow_id": "test-workflow",
        "step_id": "test-step",
        "command": "test-command",
        "status": "failed",
        "duration_ms": 500.0,
        "retry_count": 2,
        "started_at": "2025-01-27T00:00:00",
        "completed_at": None,
        "error_message": "Test error",
    }
    metric = ExecutionMetric.from_dict(data)
    assert metric.execution_id == "test-id"
    assert metric.status == "failed"
    assert metric.retry_count == 2
    assert metric.error_message == "Test error"


def test_metrics_collector_record_execution(tmp_path: Path):
    """Test recording execution metrics."""
    collector = ExecutionMetricsCollector(metrics_dir=tmp_path / "metrics")
    metric = collector.record_execution(
        workflow_id="test-workflow",
        step_id="test-step",
        command="test-command",
        status="success",
        duration_ms=1000.0,
    )

    assert metric.workflow_id == "test-workflow"
    assert metric.status == "success"
    assert metric.duration_ms == 1000.0

    # Check file was created
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    metrics_file = tmp_path / "metrics" / f"executions_{date_str}.jsonl"
    assert metrics_file.exists()


def test_metrics_collector_get_metrics(tmp_path: Path):
    """Test retrieving metrics."""
    collector = ExecutionMetricsCollector(metrics_dir=tmp_path / "metrics")

    # Record multiple metrics
    collector.record_execution(
        workflow_id="workflow-1",
        step_id="step-1",
        command="cmd-1",
        status="success",
        duration_ms=100.0,
    )
    collector.record_execution(
        workflow_id="workflow-1",
        step_id="step-2",
        command="cmd-2",
        status="failed",
        duration_ms=200.0,
    )
    collector.record_execution(
        workflow_id="workflow-2",
        step_id="step-1",
        command="cmd-1",
        status="success",
        duration_ms=150.0,
    )

    # Get all metrics
    all_metrics = collector.get_metrics(limit=10)
    assert len(all_metrics) == 3

    # Filter by workflow
    workflow_metrics = collector.get_metrics(workflow_id="workflow-1", limit=10)
    assert len(workflow_metrics) == 2
    assert all(m.workflow_id == "workflow-1" for m in workflow_metrics)

    # Filter by status
    success_metrics = collector.get_metrics(status="success", limit=10)
    assert len(success_metrics) == 2
    assert all(m.status == "success" for m in success_metrics)


def test_metrics_collector_get_summary(tmp_path: Path):
    """Test metrics summary."""
    collector = ExecutionMetricsCollector(metrics_dir=tmp_path / "metrics")

    # Record metrics
    collector.record_execution(
        workflow_id="w1",
        step_id="s1",
        command="c1",
        status="success",
        duration_ms=100.0,
        retry_count=0,
    )
    collector.record_execution(
        workflow_id="w1",
        step_id="s2",
        command="c2",
        status="success",
        duration_ms=200.0,
        retry_count=1,
    )
    collector.record_execution(
        workflow_id="w2",
        step_id="s1",
        command="c1",
        status="failed",
        duration_ms=150.0,
        retry_count=0,
    )

    summary = collector.get_summary()
    assert summary["total_executions"] == 3
    assert summary["success_rate"] == pytest.approx(2 / 3, rel=0.1)
    assert summary["average_duration_ms"] == pytest.approx(150.0, rel=0.1)
    assert summary["total_retries"] == 1
    assert summary["by_status"]["success"] == 2
    assert summary["by_status"]["failed"] == 1


def test_metrics_collector_empty_summary(tmp_path: Path):
    """Test summary with no metrics."""
    collector = ExecutionMetricsCollector(metrics_dir=tmp_path / "metrics")
    summary = collector.get_summary()
    assert summary["total_executions"] == 0
    assert summary["success_rate"] == 0.0
    assert summary["average_duration_ms"] == 0.0

