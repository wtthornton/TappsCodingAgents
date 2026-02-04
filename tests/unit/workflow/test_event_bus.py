"""
Unit tests for File-Based Event Bus.

Tests the Phase 2 enhancement: event-driven internal communication.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from tapps_agents.workflow.event_bus import FileBasedEventBus
from tapps_agents.workflow.events import EventType, WorkflowEvent

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_event_bus_publish_creates_file(tmp_path: Path):
    """Test that publishing an event creates a file."""
    event_bus = FileBasedEventBus(project_root=tmp_path)
    
    event = WorkflowEvent(
        event_type=EventType.STEP_STARTED,
        workflow_id="test-workflow-123",
        step_id="requirements",
        data={"agent": "analyst", "action": "gather-requirements"},
        timestamp=None,
    )
    event.timestamp = __import__("datetime").datetime.now()
    
    await event_bus.publish(event)
    
    # Check that event file was created
    events_dir = tmp_path / ".tapps-agents" / "events"
    assert events_dir.exists()
    
    event_files = list(events_dir.glob("*.json"))
    assert len(event_files) == 1
    
    # Verify event content
    event_data = json.loads(event_files[0].read_text(encoding="utf-8"))
    assert event_data["event_type"] == "step_started"
    assert event_data["workflow_id"] == "test-workflow-123"
    assert event_data["step_id"] == "requirements"


@pytest.mark.asyncio
async def test_event_bus_subscribe_and_notify(tmp_path: Path):
    """Test event subscription and notification."""
    event_bus = FileBasedEventBus(project_root=tmp_path)
    
    # Create mock handler
    handler = AsyncMock()
    event_bus.subscribe(EventType.STEP_STARTED, handler)
    
    event = WorkflowEvent(
        event_type=EventType.STEP_STARTED,
        workflow_id="test-workflow-123",
        step_id="requirements",
        data={"agent": "analyst"},
        timestamp=__import__("datetime").datetime.now(),
    )
    
    await event_bus.publish(event)
    
    # Verify handler was called
    handler.assert_called_once()
    assert handler.call_args[0][0] == event


@pytest.mark.asyncio
async def test_event_bus_get_events(tmp_path: Path):
    """Test retrieving events from file system."""
    event_bus = FileBasedEventBus(project_root=tmp_path)
    
    # Publish multiple events
    for i in range(3):
        event = WorkflowEvent(
            event_type=EventType.STEP_STARTED,
            workflow_id="test-workflow-123",
            step_id=f"step-{i}",
            data={"step_number": i},
            timestamp=__import__("datetime").datetime.now(),
        )
        await event_bus.publish(event)
        # Small delay to ensure different timestamps
        await __import__("asyncio").sleep(0.01)
    
    # Get events
    events = event_bus.get_events(workflow_id="test-workflow-123")
    
    assert len(events) == 3
    assert all(e.workflow_id == "test-workflow-123" for e in events)
    assert all(e.event_type == EventType.STEP_STARTED for e in events)


@pytest.mark.asyncio
async def test_event_bus_filter_by_type(tmp_path: Path):
    """Test filtering events by type."""
    event_bus = FileBasedEventBus(project_root=tmp_path)
    
    # Publish different event types
    await event_bus.publish(
        WorkflowEvent(
            event_type=EventType.STEP_STARTED,
            workflow_id="test-workflow-123",
            step_id="step-1",
            data={},
            timestamp=__import__("datetime").datetime.now(),
        )
    )
    await event_bus.publish(
        WorkflowEvent(
            event_type=EventType.STEP_COMPLETED,
            workflow_id="test-workflow-123",
            step_id="step-1",
            data={},
            timestamp=__import__("datetime").datetime.now(),
        )
    )
    
    # Get only STEP_STARTED events
    events = event_bus.get_events(
        workflow_id="test-workflow-123",
        event_type=EventType.STEP_STARTED,
    )
    
    assert len(events) == 1
    assert events[0].event_type == EventType.STEP_STARTED


@pytest.mark.asyncio
async def test_event_bus_get_latest_event(tmp_path: Path):
    """Test getting the latest event for a workflow."""
    event_bus = FileBasedEventBus(project_root=tmp_path)
    
    # Publish multiple events
    for i in range(3):
        event = WorkflowEvent(
            event_type=EventType.STEP_STARTED,
            workflow_id="test-workflow-123",
            step_id=f"step-{i}",
            data={"step_number": i},
            timestamp=__import__("datetime").datetime.now(),
        )
        await event_bus.publish(event)
        await __import__("asyncio").sleep(0.01)
    
    # Get latest event
    latest = event_bus.get_latest_event("test-workflow-123")
    
    assert latest is not None
    assert latest.step_id == "step-2"  # Last one published


@pytest.mark.asyncio
async def test_event_bus_unsubscribe(tmp_path: Path):
    """Test unsubscribing from events."""
    event_bus = FileBasedEventBus(project_root=tmp_path)
    
    handler = AsyncMock()
    event_bus.subscribe(EventType.STEP_STARTED, handler)
    
    # Publish event - handler should be called
    event = WorkflowEvent(
        event_type=EventType.STEP_STARTED,
        workflow_id="test-workflow-123",
        step_id="step-1",
        data={},
        timestamp=__import__("datetime").datetime.now(),
    )
    await event_bus.publish(event)
    handler.assert_called_once()
    
    # Unsubscribe
    event_bus.unsubscribe(EventType.STEP_STARTED, handler)
    handler.reset_mock()
    
    # Publish again - handler should not be called
    await event_bus.publish(event)
    handler.assert_not_called()


@pytest.mark.asyncio
async def test_event_bus_handles_handler_errors(tmp_path: Path):
    """Test that handler errors don't break event publishing."""
    event_bus = FileBasedEventBus(project_root=tmp_path)
    
    # Create handler that raises exception
    def failing_handler(event: WorkflowEvent):
        raise ValueError("Handler error")
    
    event_bus.subscribe(EventType.STEP_STARTED, failing_handler)
    
    event = WorkflowEvent(
        event_type=EventType.STEP_STARTED,
        workflow_id="test-workflow-123",
        step_id="step-1",
        data={},
        timestamp=__import__("datetime").datetime.now(),
    )
    
    # Should not raise exception
    await event_bus.publish(event)
    
    # Event file should still be created
    events_dir = tmp_path / ".tapps-agents" / "events"
    event_files = list(events_dir.glob("*.json"))
    assert len(event_files) == 1

