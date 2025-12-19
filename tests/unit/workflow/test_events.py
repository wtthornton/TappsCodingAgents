"""
Unit tests for Workflow Events.

Tests event type definitions and serialization.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from tapps_agents.workflow.events import EventType, WorkflowEvent

pytestmark = pytest.mark.unit


def test_event_type_enum():
    """Test that EventType enum has expected values."""
    assert EventType.STEP_STARTED.value == "step_started"
    assert EventType.STEP_COMPLETED.value == "step_completed"
    assert EventType.WORKFLOW_STARTED.value == "workflow_started"
    assert EventType.WORKFLOW_COMPLETED.value == "workflow_completed"


def test_workflow_event_to_dict():
    """Test converting event to dictionary."""
    event = WorkflowEvent(
        event_type=EventType.STEP_STARTED,
        workflow_id="test-workflow-123",
        step_id="requirements",
        data={"agent": "analyst", "action": "gather-requirements"},
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        correlation_id="corr-123",
    )
    
    event_dict = event.to_dict()
    
    assert event_dict["event_type"] == "step_started"
    assert event_dict["workflow_id"] == "test-workflow-123"
    assert event_dict["step_id"] == "requirements"
    assert event_dict["data"]["agent"] == "analyst"
    assert event_dict["timestamp"] == "2025-01-01T12:00:00"
    assert event_dict["correlation_id"] == "corr-123"


def test_workflow_event_from_dict():
    """Test creating event from dictionary."""
    event_dict = {
        "event_type": "step_started",
        "workflow_id": "test-workflow-123",
        "step_id": "requirements",
        "data": {"agent": "analyst"},
        "timestamp": "2025-01-01T12:00:00",
        "correlation_id": "corr-123",
    }
    
    event = WorkflowEvent.from_dict(event_dict)
    
    assert event.event_type == EventType.STEP_STARTED
    assert event.workflow_id == "test-workflow-123"
    assert event.step_id == "requirements"
    assert event.data["agent"] == "analyst"
    assert event.timestamp == datetime(2025, 1, 1, 12, 0, 0)
    assert event.correlation_id == "corr-123"


def test_workflow_event_round_trip():
    """Test that event can be serialized and deserialized."""
    original = WorkflowEvent(
        event_type=EventType.STEP_COMPLETED,
        workflow_id="test-workflow-123",
        step_id="requirements",
        data={"agent": "analyst", "duration": 5.5},
        timestamp=datetime.now(),
        correlation_id="corr-123",
    )
    
    # Convert to dict and back
    event_dict = original.to_dict()
    restored = WorkflowEvent.from_dict(event_dict)
    
    assert restored.event_type == original.event_type
    assert restored.workflow_id == original.workflow_id
    assert restored.step_id == original.step_id
    assert restored.data == original.data
    assert restored.correlation_id == original.correlation_id
    # Timestamp may have slight precision differences, so check within 1 second
    assert abs((restored.timestamp - original.timestamp).total_seconds()) < 1

