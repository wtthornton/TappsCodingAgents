"""
File-based event bus for agent coordination.

Provides event-driven communication between workflow components using
file-based event storage for persistence and real-time monitoring.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .events import EventType, WorkflowEvent

logger = logging.getLogger(__name__)


class FileBasedEventBus:
    """
    File-based event bus for agent coordination.

    Stores events in .tapps-agents/events/ for persistence
    and real-time monitoring. Supports event subscription for
    in-process event handling.
    """

    def __init__(self, project_root: Path):
        """
        Initialize file-based event bus.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root)
        self.events_dir = self.project_root / ".tapps-agents" / "events"
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.subscribers: dict[EventType, list[Callable[[WorkflowEvent], Any]]] = {}

    async def publish(self, event: WorkflowEvent) -> None:
        """
        Publish event to file system and notify subscribers.

        Args:
            event: Workflow event to publish
        """
        # Store event in file for persistence
        event_filename = (
            f"{event.workflow_id}-{event.timestamp.timestamp():.6f}-{event.event_type.value}.json"
        )
        event_file = self.events_dir / event_filename

        try:
            event_file.write_text(
                json.dumps(event.to_dict(), indent=2), encoding="utf-8"
            )
        except (OSError, json.JSONEncodeError) as e:
            logger.warning(
                f"Failed to write event to file {event_file}: {e}",
                exc_info=True,
            )

        # Notify in-process subscribers (copy list to avoid mutation during iteration)
        handlers = list(self.subscribers.get(event.event_type, []))
        for handler in handlers:
            try:
                if isinstance(handler, Callable):
                    # Check if handler is async
                    import inspect

                    if inspect.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler for {event.event_type.value}: {e}",
                    exc_info=True,
                )

    def subscribe(
        self, event_type: EventType, handler: Callable[[WorkflowEvent], Any]
    ) -> None:
        """
        Subscribe to specific event types.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle events
                Can be sync or async function
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def unsubscribe(
        self, event_type: EventType, handler: Callable[[WorkflowEvent], Any]
    ) -> None:
        """
        Unsubscribe from event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(handler)
            except ValueError:
                # Handler not in list, ignore
                pass

    def get_events(
        self,
        workflow_id: str | None = None,
        event_type: EventType | None = None,
        limit: int | None = None,
    ) -> list[WorkflowEvent]:
        """
        Get events from file system.

        Args:
            workflow_id: Filter by workflow ID
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of workflow events
        """
        events: list[WorkflowEvent] = []

        if not self.events_dir.exists():
            return events

        # Get all event files, sorted by timestamp (filename contains timestamp)
        event_files = sorted(self.events_dir.glob("*.json"), reverse=True)

        for event_file in event_files:
            try:
                event_data = json.loads(event_file.read_text(encoding="utf-8"))

                # Filter by workflow_id if specified
                if workflow_id and event_data.get("workflow_id") != workflow_id:
                    continue

                # Filter by event_type if specified
                if event_type and event_data.get("event_type") != event_type.value:
                    continue

                event = WorkflowEvent.from_dict(event_data)
                events.append(event)

                # Apply limit if specified
                if limit and len(events) >= limit:
                    break

            except (json.JSONDecodeError, KeyError, OSError) as e:
                logger.debug(f"Failed to read event file {event_file}: {e}")
                continue

        return events

    def get_latest_event(
        self,
        workflow_id: str,
        event_type: EventType | None = None,
    ) -> WorkflowEvent | None:
        """
        Get the latest event for a workflow.

        Args:
            workflow_id: Workflow ID
            event_type: Optional event type filter

        Returns:
            Latest workflow event or None
        """
        events = self.get_events(workflow_id=workflow_id, event_type=event_type, limit=1)
        return events[0] if events else None

