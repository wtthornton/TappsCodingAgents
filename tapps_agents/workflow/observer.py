"""
Workflow Observer Pattern

Provides event-driven observer pattern for workflow execution monitoring.
Allows real-time subscription to workflow events without polling.
"""

import logging
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from .event_log import WorkflowEvent

logger = logging.getLogger(__name__)


@dataclass
class EventFilter:
    """Filter for selecting which events an observer should receive."""

    event_types: list[str] | None = None  # None = all types
    step_ids: list[str] | None = None  # None = all steps
    agents: list[str] | None = None  # None = all agents
    custom_filter: Callable[[WorkflowEvent], bool] | None = None  # Custom filter function

    def matches(self, event: WorkflowEvent) -> bool:
        """Check if event matches this filter."""
        if self.event_types and event.event_type not in self.event_types:
            return False
        if self.step_ids and event.step_id not in self.step_ids:
            return False
        if self.agents and event.agent not in self.agents:
            return False
        if self.custom_filter and not self.custom_filter(event):
            return False
        return True


class WorkflowObserver(ABC):
    """Abstract base class for workflow observers."""

    @abstractmethod
    def on_workflow_start(self, event: WorkflowEvent) -> None:
        """Called when workflow starts."""
        pass

    @abstractmethod
    def on_workflow_end(self, event: WorkflowEvent) -> None:
        """Called when workflow ends."""
        pass

    @abstractmethod
    def on_step_start(self, event: WorkflowEvent) -> None:
        """Called when a step starts."""
        pass

    @abstractmethod
    def on_step_complete(self, event: WorkflowEvent) -> None:
        """Called when a step completes successfully."""
        pass

    @abstractmethod
    def on_step_fail(self, event: WorkflowEvent) -> None:
        """Called when a step fails."""
        pass

    @abstractmethod
    def on_artifact_created(self, event: WorkflowEvent) -> None:
        """Called when an artifact is created."""
        pass

    def on_event(self, event: WorkflowEvent) -> None:
        """Generic event handler that routes to specific handlers."""
        try:
            if event.event_type == "workflow_start":
                self.on_workflow_start(event)
            elif event.event_type == "workflow_end":
                self.on_workflow_end(event)
            elif event.event_type == "step_start":
                self.on_step_start(event)
            elif event.event_type == "step_finish":
                self.on_step_complete(event)
            elif event.event_type == "step_fail":
                self.on_step_fail(event)
            elif event.event_type == "artifact_created":
                self.on_artifact_created(event)
            # Note: step_skip events don't have specific handlers by default
        except Exception as e:
            # Don't let observer exceptions break workflow execution
            logger.error(
                f"Observer {self.__class__.__name__} raised exception: {e}",
                exc_info=True,
                extra={"event_type": event.event_type, "workflow_id": event.workflow_id},
            )


class ObserverRegistry:
    """Thread-safe registry for managing workflow observers."""

    def __init__(self):
        """Initialize observer registry."""
        self._observers: list[tuple[WorkflowObserver, EventFilter | None]] = []
        self._lock = threading.Lock()

    def register(
        self, observer: WorkflowObserver, filter: EventFilter | None = None
    ) -> None:
        """
        Register an observer with optional filter.

        Args:
            observer: Observer instance to register
            filter: Optional filter to limit which events the observer receives
        """
        with self._lock:
            if (observer, filter) not in self._observers:
                self._observers.append((observer, filter))
                logger.debug(
                    f"Registered observer {observer.__class__.__name__} with filter {filter}"
                )

    def unregister(self, observer: WorkflowObserver) -> None:
        """
        Unregister an observer.

        Args:
            observer: Observer instance to unregister
        """
        with self._lock:
            self._observers = [
                (obs, filt) for obs, filt in self._observers if obs is not observer
            ]
            logger.debug(f"Unregistered observer {observer.__class__.__name__}")

    def notify(self, event: WorkflowEvent) -> None:
        """
        Notify all registered observers of an event.

        Args:
            event: Event to notify observers about
        """
        with self._lock:
            observers_to_notify = list(self._observers)

        for observer, event_filter in observers_to_notify:
            try:
                # Apply filter if present
                if event_filter is None or event_filter.matches(event):
                    observer.on_event(event)
            except Exception as e:
                # Don't let one observer's exception break others
                logger.error(
                    f"Observer {observer.__class__.__name__} raised exception: {e}",
                    exc_info=True,
                    extra={"event_type": event.event_type, "workflow_id": event.workflow_id},
                )

    def get_observers(self) -> list[WorkflowObserver]:
        """Get list of all registered observers."""
        with self._lock:
            return [obs for obs, _ in self._observers]

    def clear(self) -> None:
        """Clear all registered observers."""
        with self._lock:
            self._observers.clear()
            logger.debug("Cleared all observers")

