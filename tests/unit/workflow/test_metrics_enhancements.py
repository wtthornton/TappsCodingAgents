"""
Unit tests for enhanced execution metrics collection.
"""

from __future__ import annotations

import pytest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tapps_agents.workflow.metrics_enhancements import (
    ExecutionMetric,
    EnhancedExecutionMetricsCollector,
    VALID_STATUSES,
)


@pytest.mark.unit
class TestExecutionMetric:
    """Tests for ExecutionMetric dataclass."""

    def test_valid_metric_creation(self):
        """Test creating a valid metric."""
        metric = ExecutionMetric(
            execution_id="test-id",
            workflow_id="test-workflow",
            step_id="test-step",
            command="test-command",
            status="success",
            duration_ms=1000.0,
            started_at="2025-01-27T00:00:00",
        )
        assert metric.execution_id == "test-id"
        assert metric.status == "success"

    def test_invalid_status_raises_error(self):
        """Test that invalid status raises ValueError."""
        with pytest.raises(ValueError, match="Invalid status"):
            ExecutionMetric(
                execution_id="test-id",
                workflow_id="test-workflow",
                step_id="test-step",
                command="test-command",
                status="invalid_status",
                duration_ms=1000.0,
                started_at="2025-01-27T00:00:00",
            )

    def test_negative_duration_raises_error(self):
        """Test that negative duration raises ValueError."""
        with pytest.raises(ValueError, match="Duration cannot be negative"):
            ExecutionMetric(
                execution_id="test-id",
                workflow_id="test-workflow",
                step_id="test-step",
                command="test-command",
                status="success",
                duration_ms=-100.0,
                started_at="2025-01-27T00:00:00",
            )

    def test_to_dict(self):
        """Test serialization to dictionary."""
        metric = ExecutionMetric(
            execution_id="test-id",
            workflow_id="test-workflow",
            step_id="test-step",
            command="test-command",
            status="success",
            duration_ms=1000.0,
            started_at="2025-01-27T00:00:00",
            metadata={"key": "value"},
        )
        data = metric.to_dict()
        assert data["execution_id"] == "test-id"
        assert data["metadata"] == {"key": "value"}

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "execution_id": "test-id",
            "workflow_id": "test-workflow",
            "step_id": "test-step",
            "command": "test-command",
            "status": "failed",
            "duration_ms": 500.0,
            "started_at": "2025-01-27T00:00:00",
            "retry_count": 2,
            "completed_at": None,
            "error_message": "Test error",
            "metadata": {},
        }
        metric = ExecutionMetric.from_dict(data)
        assert metric.execution_id == "test-id"
        assert metric.status == "failed"
        assert metric.error_message == "Test error"

    def test_validate_returns_errors(self):
        """Test validate method returns list of errors."""
        # Create metric with invalid data (bypass __post_init__ by setting directly)
        metric = ExecutionMetric.__new__(ExecutionMetric)
        metric.execution_id = "test-id"
        metric.workflow_id = "test-workflow"
        metric.step_id = "test-step"
        metric.command = "test-command"
        metric.status = "invalid"
        metric.duration_ms = -100.0
        metric.started_at = "invalid-timestamp"
        metric.retry_count = 0
        metric.completed_at = None
        metric.error_message = None
        metric.metadata = {}
        
        errors = metric.validate()
        assert len(errors) >= 2
        assert any("Invalid status" in e for e in errors)
        assert any("Negative duration" in e for e in errors)


@pytest.mark.unit
class TestEnhancedExecutionMetricsCollector:
    """Tests for EnhancedExecutionMetricsCollector."""

    def test_record_execution(self, tmp_path: Path):
        """Test recording execution metrics."""
        collector = EnhancedExecutionMetricsCollector(
            metrics_dir=tmp_path / "metrics",
            write_buffer_size=1,  # Immediate write
        )
        metric = collector.record_execution(
            workflow_id="test-workflow",
            step_id="test-step",
            command="test-command",
            status="success",
            duration_ms=1000.0,
        )

        assert metric.workflow_id == "test-workflow"
        assert metric.status == "success"

    def test_record_execution_with_metadata(self, tmp_path: Path):
        """Test recording execution with metadata."""
        collector = EnhancedExecutionMetricsCollector(
            metrics_dir=tmp_path / "metrics",
            write_buffer_size=1,
        )
        metric = collector.record_execution(
            workflow_id="test-workflow",
            step_id="test-step",
            command="test-command",
            status="success",
            duration_ms=1000.0,
            metadata={"agent": "reviewer", "files": 5},
        )

        assert metric.metadata == {"agent": "reviewer", "files": 5}

    def test_validation_rejects_invalid_status(self, tmp_path: Path):
        """Test that invalid status is rejected."""
        collector = EnhancedExecutionMetricsCollector(
            metrics_dir=tmp_path / "metrics",
            enable_validation=True,
        )
        
        with pytest.raises(ValueError, match="Invalid status"):
            collector.record_execution(
                workflow_id="test-workflow",
                step_id="test-step",
                command="test-command",
                status="invalid_status",
                duration_ms=1000.0,
            )

    def test_batch_recording(self, tmp_path: Path):
        """Test batch recording of metrics."""
        collector = EnhancedExecutionMetricsCollector(
            metrics_dir=tmp_path / "metrics",
            write_buffer_size=10,
        )
        
        batch = [
            {
                "workflow_id": "wf-1",
                "step_id": "s1",
                "command": "cmd1",
                "status": "success",
                "duration_ms": 100.0,
            },
            {
                "workflow_id": "wf-1",
                "step_id": "s2",
                "command": "cmd2",
                "status": "failed",
                "duration_ms": 200.0,
            },
        ]
        
        recorded = collector.record_batch(batch)
        assert len(recorded) == 2

    def test_get_metrics_no_duplicates(self, tmp_path: Path):
        """Test that get_metrics returns no duplicates."""
        collector = EnhancedExecutionMetricsCollector(
            metrics_dir=tmp_path / "metrics",
            write_buffer_size=1,  # Immediate write
        )
        
        # Record metrics
        for i in range(3):
            collector.record_execution(
                workflow_id="test-workflow",
                step_id=f"step-{i}",
                command="test-command",
                status="success",
                duration_ms=100.0 * (i + 1),
            )
        
        # Flush to ensure written
        collector.flush()
        
        # Get metrics
        metrics = collector.get_metrics(workflow_id="test-workflow", limit=10)
        
        # Check no duplicates
        ids = [m.execution_id for m in metrics]
        assert len(ids) == len(set(ids))
        assert len(metrics) == 3

    def test_get_metrics_with_filters(self, tmp_path: Path):
        """Test filtering metrics."""
        collector = EnhancedExecutionMetricsCollector(
            metrics_dir=tmp_path / "metrics",
            write_buffer_size=1,
        )
        
        collector.record_execution(
            workflow_id="wf-1",
            step_id="s1",
            command="cmd",
            status="success",
            duration_ms=100.0,
        )
        collector.record_execution(
            workflow_id="wf-1",
            step_id="s2",
            command="cmd",
            status="failed",
            duration_ms=200.0,
        )
        collector.record_execution(
            workflow_id="wf-2",
            step_id="s1",
            command="cmd",
            status="success",
            duration_ms=150.0,
        )
        
        collector.flush()
        
        # Filter by workflow
        wf1_metrics = collector.get_metrics(workflow_id="wf-1", limit=10)
        assert len(wf1_metrics) == 2
        
        # Filter by status
        success_metrics = collector.get_metrics(status="success", limit=10)
        assert len(success_metrics) == 2

    def test_get_summary(self, tmp_path: Path):
        """Test summary statistics."""
        collector = EnhancedExecutionMetricsCollector(
            metrics_dir=tmp_path / "metrics",
            write_buffer_size=1,
        )
        
        collector.record_execution(
            workflow_id="w1",
            step_id="s1",
            command="c1",
            status="success",
            duration_ms=100.0,
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
        )
        
        collector.flush()
        
        summary = collector.get_summary()
        assert summary["total_executions"] == 3
        assert summary["success_rate"] == pytest.approx(2 / 3, rel=0.1)
        assert summary["total_retries"] == 1
        assert summary["by_status"]["success"] == 2
        assert summary["by_status"]["failed"] == 1

    def test_get_stats(self, tmp_path: Path):
        """Test collector statistics."""
        collector = EnhancedExecutionMetricsCollector(
            metrics_dir=tmp_path / "metrics",
            write_buffer_size=5,
        )
        
        collector.record_execution(
            workflow_id="w1",
            step_id="s1",
            command="c1",
            status="success",
            duration_ms=100.0,
        )
        
        stats = collector.get_stats()
        assert stats["total_recorded"] == 1
        assert stats["cache_size"] == 1

    def test_flush(self, tmp_path: Path):
        """Test manual flush."""
        collector = EnhancedExecutionMetricsCollector(
            metrics_dir=tmp_path / "metrics",
            write_buffer_size=100,  # Large buffer
        )
        
        collector.record_execution(
            workflow_id="w1",
            step_id="s1",
            command="c1",
            status="success",
            duration_ms=100.0,
        )
        
        # Buffer should have 1 item
        assert collector.get_stats()["buffer_size"] == 1
        
        # Flush
        collector.flush()
        
        # Buffer should be empty
        assert collector.get_stats()["buffer_size"] == 0

    def test_pagination(self, tmp_path: Path):
        """Test pagination with offset."""
        collector = EnhancedExecutionMetricsCollector(
            metrics_dir=tmp_path / "metrics",
            write_buffer_size=1,
        )
        
        for i in range(10):
            collector.record_execution(
                workflow_id="w1",
                step_id=f"s{i}",
                command="c1",
                status="success",
                duration_ms=100.0 * (i + 1),
            )
        
        collector.flush()
        
        # Get first 5
        first_page = collector.get_metrics(limit=5, offset=0)
        assert len(first_page) == 5
        
        # Get next 5
        second_page = collector.get_metrics(limit=5, offset=5)
        assert len(second_page) == 5
        
        # No overlap
        first_ids = {m.execution_id for m in first_page}
        second_ids = {m.execution_id for m in second_page}
        assert first_ids.isdisjoint(second_ids)
