"""
Unit tests for audit logging.
"""

from __future__ import annotations

from pathlib import Path

from tapps_agents.workflow.audit_logger import AuditLogger


def test_audit_logger_initialization(tmp_path: Path):
    """Test AuditLogger initialization."""
    logger = AuditLogger(audit_dir=tmp_path / "audit")
    assert logger.audit_dir.exists()
    assert logger.log_file.exists()


def test_audit_logger_log_event(tmp_path: Path):
    """Test logging an event."""
    logger = AuditLogger(audit_dir=tmp_path / "audit")
    logger.log_event(
        event_type="test_event",
        workflow_id="test-workflow",
        step_id="test-step",
        command="test-command",
        status="started",
    )

    # Check log file was written
    assert logger.log_file.exists()
    content = logger.log_file.read_text()
    assert "test_event" in content
    assert "test-workflow" in content


def test_audit_logger_log_command_detected(tmp_path: Path):
    """Test logging command detection."""
    logger = AuditLogger(audit_dir=tmp_path / "audit")
    logger.log_command_detected(
        workflow_id="w1",
        step_id="s1",
        command="cmd1",
        command_file=Path("test.txt"),
    )

    content = logger.log_file.read_text()
    assert "command_detected" in content
    assert "w1" in content


def test_audit_logger_log_execution_started(tmp_path: Path):
    """Test logging execution start."""
    logger = AuditLogger(audit_dir=tmp_path / "audit")
    logger.log_execution_started(
        workflow_id="w1",
        step_id="s1",
        command="cmd1",
    )

    content = logger.log_file.read_text()
    assert "execution_started" in content


def test_audit_logger_log_execution_completed(tmp_path: Path):
    """Test logging execution completion."""
    logger = AuditLogger(audit_dir=tmp_path / "audit")
    logger.log_execution_completed(
        workflow_id="w1",
        step_id="s1",
        command="cmd1",
        duration_ms=1000.0,
    )

    content = logger.log_file.read_text()
    assert "execution_completed" in content
    assert "1000.0" in content


def test_audit_logger_log_execution_failed(tmp_path: Path):
    """Test logging execution failure."""
    logger = AuditLogger(audit_dir=tmp_path / "audit")
    logger.log_execution_failed(
        workflow_id="w1",
        step_id="s1",
        command="cmd1",
        error="Test error",
        duration_ms=500.0,
    )

    content = logger.log_file.read_text()
    assert "execution_failed" in content
    assert "Test error" in content


def test_audit_logger_query_events(tmp_path: Path):
    """Test querying audit events."""
    logger = AuditLogger(audit_dir=tmp_path / "audit")

    # Log some events
    logger.log_execution_started(workflow_id="w1", step_id="s1", command="c1")
    logger.log_execution_started(workflow_id="w2", step_id="s1", command="c1")
    logger.log_execution_completed(workflow_id="w1", step_id="s1", command="c1", duration_ms=100.0)

    # Query all events
    events = logger.query_events(limit=10)
    assert len(events) >= 3

    # Filter by workflow
    w1_events = logger.query_events(workflow_id="w1", limit=10)
    assert len(w1_events) >= 2
    assert all(e["workflow_id"] == "w1" for e in w1_events)

    # Filter by event type
    started_events = logger.query_events(event_type="execution_started", limit=10)
    assert len(started_events) >= 2
    assert all(e["event_type"] == "execution_started" for e in started_events)

