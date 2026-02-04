"""
Append-Only Workflow Event Log

Provides durable, append-only event logging for workflow execution.
Epic 5 / Story 5.4: Workflow State Management
"""

import json
import logging
import os
import threading
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WorkflowEvent:
    """A workflow execution event."""

    event_type: str  # workflow_start, workflow_end, step_start, step_finish, step_fail, step_skip
    workflow_id: str
    seq: int  # Monotonic sequence number
    timestamp: datetime
    step_id: str | None = None
    agent: str | None = None
    action: str | None = None
    status: str | None = None
    error: str | None = None
    artifacts: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    # Decision logging and trace fields (plan 1.1, 1.4)
    rationale: str | None = None
    input_summary: str | None = None
    criteria: dict[str, Any] | None = None
    skill_name: str | None = None
    model_profile: str | None = None
    artifact_paths: list[str] | None = None
    tool_call_summary: dict[str, Any] | None = None  # e.g. command, success, duration_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat() + "Z"
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowEvent":
        """Create event from dictionary."""
        data = data.copy()
        if isinstance(data.get("timestamp"), str):
            timestamp_str = data["timestamp"]
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1]
            data["timestamp"] = datetime.fromisoformat(timestamp_str)
        # Only pass known fields (backward compat with old event format)
        known = {
            "event_type", "workflow_id", "seq", "timestamp", "step_id", "agent",
            "action", "status", "error", "artifacts", "metadata",
            "rationale", "input_summary", "criteria", "skill_name", "model_profile",
            "artifact_paths", "tool_call_summary",
        }
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class EventFilter:
    """Filter for selecting which events a subscriber should receive."""

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


@dataclass
class Subscription:
    """Represents an event subscription."""

    callback: Callable[[WorkflowEvent], None]
    filter: EventFilter | None
    subscription_id: str


class EventStream:
    """Real-time event stream for consuming workflow events."""

    def __init__(self):
        """Initialize event stream."""
        self._subscribers: list[Subscription] = []
        self._lock = threading.Lock()
        self._event_buffer: dict[str, list[WorkflowEvent]] = {}  # workflow_id -> events
        self._buffer_limit = 1000  # Keep last 1000 events per workflow in memory

    def subscribe(
        self,
        callback: Callable[[WorkflowEvent], None],
        filter: EventFilter | None = None,
        subscription_id: str | None = None,
    ) -> Subscription:
        """
        Subscribe to events with optional filter.

        Args:
            callback: Function to call when matching events occur
            filter: Optional filter to limit which events trigger callback
            subscription_id: Optional ID for this subscription

        Returns:
            Subscription object that can be used to unsubscribe
        """
        if subscription_id is None:
            import uuid

            subscription_id = str(uuid.uuid4())

        subscription = Subscription(
            callback=callback, filter=filter, subscription_id=subscription_id
        )

        with self._lock:
            self._subscribers.append(subscription)

        logger.debug(f"Subscribed to event stream: {subscription_id}")
        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        """
        Unsubscribe from events.

        Args:
            subscription: Subscription to remove
        """
        with self._lock:
            self._subscribers = [
                s for s in self._subscribers if s.subscription_id != subscription.subscription_id
            ]
        logger.debug(f"Unsubscribed from event stream: {subscription.subscription_id}")

    def emit(self, event: WorkflowEvent) -> None:
        """
        Emit an event to all subscribers.

        Args:
            event: Event to emit
        """
        # Add to in-memory buffer
        with self._lock:
            if event.workflow_id not in self._event_buffer:
                self._event_buffer[event.workflow_id] = []
            self._event_buffer[event.workflow_id].append(event)

            # Limit buffer size
            if len(self._event_buffer[event.workflow_id]) > self._buffer_limit:
                self._event_buffer[event.workflow_id] = self._event_buffer[
                    event.workflow_id
                ][-self._buffer_limit :]

            # Get subscribers to notify (copy to avoid holding lock during callback)
            subscribers_to_notify = list(self._subscribers)

        # Notify subscribers (outside lock to avoid deadlocks)
        for subscription in subscribers_to_notify:
            try:
                if subscription.filter is None or subscription.filter.matches(event):
                    subscription.callback(event)
            except Exception as e:
                # Don't let one subscriber's exception break others
                logger.error(
                    f"Subscriber {subscription.subscription_id} raised exception: {e}",
                    exc_info=True,
                    extra={"event_type": event.event_type, "workflow_id": event.workflow_id},
                )

    def get_latest_events(self, workflow_id: str, limit: int = 100) -> list[WorkflowEvent]:
        """
        Get latest events for a workflow from in-memory buffer.

        Args:
            workflow_id: Workflow ID
            limit: Maximum number of events to return

        Returns:
            List of events, most recent first
        """
        with self._lock:
            events = self._event_buffer.get(workflow_id, [])
            return list(reversed(events[-limit:]))

    def clear_buffer(self, workflow_id: str | None = None) -> None:
        """
        Clear event buffer.

        Args:
            workflow_id: If provided, clear only this workflow's buffer. Otherwise clear all.
        """
        with self._lock:
            if workflow_id:
                self._event_buffer.pop(workflow_id, None)
            else:
                self._event_buffer.clear()


class WorkflowEventLog:
    """Manages append-only event log for workflow execution."""

    def __init__(self, events_dir: Path, enable_streaming: bool = True):
        """
        Initialize event log.

        Args:
            events_dir: Directory to store event log files
            enable_streaming: Whether to enable in-memory event streaming
        """
        self.events_dir = Path(events_dir)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self._sequence_counter: dict[str, int] = {}
        self._stream: EventStream | None = EventStream() if enable_streaming else None

    def _get_event_file(self, workflow_id: str) -> Path:
        """Get event log file path for a workflow."""
        return self.events_dir / f"{workflow_id}.events.jsonl"

    def _get_next_sequence(self, workflow_id: str) -> int:
        """Get next sequence number for a workflow."""
        if workflow_id not in self._sequence_counter:
            # Try to read last sequence from file
            event_file = self._get_event_file(workflow_id)
            if event_file.exists():
                try:
                    last_seq = 0
                    with open(event_file, encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                event_data = json.loads(line)
                                last_seq = max(last_seq, event_data.get("seq", 0))
                    self._sequence_counter[workflow_id] = last_seq
                except Exception as e:
                    logger.warning(
                        f"Failed to read sequence from {event_file}: {e}",
                        exc_info=True,
                    )
                    self._sequence_counter[workflow_id] = 0
            else:
                self._sequence_counter[workflow_id] = 0

        self._sequence_counter[workflow_id] += 1
        return self._sequence_counter[workflow_id]

    def emit_event(
        self,
        event_type: str,
        workflow_id: str,
        step_id: str | None = None,
        agent: str | None = None,
        action: str | None = None,
        status: str | None = None,
        error: str | None = None,
        artifacts: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        *,
        rationale: str | None = None,
        input_summary: str | None = None,
        criteria: dict[str, Any] | None = None,
        skill_name: str | None = None,
        model_profile: str | None = None,
        artifact_paths: list[str] | None = None,
        tool_call_summary: dict[str, Any] | None = None,
    ) -> WorkflowEvent:
        """
        Emit a workflow event (append-only write).

        Args:
            event_type: Type of event (workflow_start, workflow_end, step_start, step_finish, step_fail, step_skip)
            workflow_id: Workflow ID
            step_id: Step ID (if applicable)
            agent: Agent name (if applicable)
            action: Action name (if applicable)
            status: Status (if applicable)
            error: Error message (if applicable)
            artifacts: Artifact summaries (if applicable)
            metadata: Additional metadata
            rationale: Optional decision rationale (decision logging)
            input_summary: Optional input summary (decision logging)
            criteria: Optional criteria dict (decision logging)
            skill_name: Optional skill name (trace)
            model_profile: Optional model profile (trace)
            artifact_paths: Optional list of artifact paths produced (trace)
            tool_call_summary: Optional dict with command, success, duration_ms (trace)

        Returns:
            Created WorkflowEvent
        """
        seq = self._get_next_sequence(workflow_id)
        event = WorkflowEvent(
            event_type=event_type,
            workflow_id=workflow_id,
            seq=seq,
            timestamp=datetime.now(UTC),
            step_id=step_id,
            agent=agent,
            action=action,
            status=status,
            error=error,
            artifacts=artifacts,
            metadata=metadata,
            rationale=rationale,
            input_summary=input_summary,
            criteria=criteria,
            skill_name=skill_name,
            model_profile=model_profile,
            artifact_paths=artifact_paths,
            tool_call_summary=tool_call_summary,
        )

        # Append to event log file (best-effort, non-blocking)
        try:
            event_file = self._get_event_file(workflow_id)
            with open(event_file, "a", encoding="utf-8") as f:
                # Use atomic write: write to temp file, then rename
                # For append-only, we'll use a simpler approach with file locking
                # In practice, JSONL append is atomic on most filesystems
                json_line = json.dumps(event.to_dict(), ensure_ascii=False)
                f.write(json_line + "\n")
                f.flush()
                os.fsync(f.fileno())  # Ensure durability
        except Exception as e:
            # Log error but don't fail workflow execution
            logger.error(
                f"Failed to write event to log: {e}",
                exc_info=True,
                extra={
                    "workflow_id": workflow_id,
                    "event_type": event_type,
                    "step_id": step_id,
                },
            )

        # Emit to stream subscribers (real-time notification)
        if self._stream:
            self._stream.emit(event)

        return event

    def read_events(
        self, workflow_id: str, limit: int | None = None
    ) -> list[WorkflowEvent]:
        """
        Read events for a workflow.

        Args:
            workflow_id: Workflow ID
            limit: Maximum number of events to read (None = all)

        Returns:
            List of events, ordered by sequence number
        """
        event_file = self._get_event_file(workflow_id)
        if not event_file.exists():
            return []

        events: list[WorkflowEvent] = []
        try:
            with open(event_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            event_data = json.loads(line)
                            event = WorkflowEvent.from_dict(event_data)
                            events.append(event)
                        except Exception as e:
                            logger.warning(
                                f"Failed to parse event line: {e}",
                                extra={"workflow_id": workflow_id, "line": line[:100]},
                            )
                            continue

            # Sort by sequence number (should already be sorted, but ensure it)
            events.sort(key=lambda e: e.seq)

            if limit:
                events = events[-limit:]  # Get most recent events

        except Exception as e:
            logger.error(
                f"Failed to read events from {event_file}: {e}",
                exc_info=True,
                extra={"workflow_id": workflow_id},
            )

        return events

    def get_execution_history(
        self, workflow_id: str
    ) -> dict[str, Any]:
        """
        Generate human-readable execution history from event log.

        Args:
            workflow_id: Workflow ID

        Returns:
            Dictionary with execution history summary
        """
        events = self.read_events(workflow_id)
        if not events:
            return {
                "workflow_id": workflow_id,
                "events": [],
                "summary": "No events found",
            }

        workflow_start = next(
            (e for e in events if e.event_type == "workflow_start"), None
        )
        workflow_end = next(
            (e for e in events if e.event_type == "workflow_end"), None
        )

        step_events = [
            e
            for e in events
            if e.event_type in ("step_start", "step_finish", "step_fail", "step_skip")
        ]

        # Group step events by step_id
        step_history: dict[str, list[WorkflowEvent]] = {}
        for event in step_events:
            if event.step_id:
                if event.step_id not in step_history:
                    step_history[event.step_id] = []
                step_history[event.step_id].append(event)

        # Calculate duration if both start and end exist
        duration_seconds: float | None = None
        if workflow_start and workflow_end:
            duration_seconds = (
                workflow_end.timestamp - workflow_start.timestamp
            ).total_seconds()

        return {
            "workflow_id": workflow_id,
            "started_at": workflow_start.timestamp.isoformat() + "Z"
            if workflow_start
            else None,
            "ended_at": workflow_end.timestamp.isoformat() + "Z" if workflow_end else None,
            "duration_seconds": duration_seconds,
            "status": workflow_end.status if workflow_end else "running",
            "total_events": len(events),
            "step_count": len(step_history),
            "steps": {
                step_id: [
                    {
                        "event_type": e.event_type,
                        "timestamp": e.timestamp.isoformat() + "Z",
                        "status": e.status,
                        "error": e.error,
                    }
                    for e in sorted(events, key=lambda e: e.seq)
                ]
                for step_id, events in step_history.items()
            },
            "events": [
                {
                    "seq": e.seq,
                    "event_type": e.event_type,
                    "timestamp": e.timestamp.isoformat() + "Z",
                    "step_id": e.step_id,
                    "agent": e.agent,
                    "action": e.action,
                    "status": e.status,
                    "error": e.error,
                }
                for e in events
            ],
        }

    def get_execution_trace(self, workflow_id: str) -> dict[str, Any]:
        """
        Derive a structured execution trace from events for metrics/AgentOps.

        Args:
            workflow_id: Workflow ID

        Returns:
            Dict with workflow_id, started_at, ended_at, steps (list of
            step_id, agent, skill_name, action, started_at, ended_at,
            duration_ms, status, tool_calls, artifact_paths, error).
        """
        events = self.read_events(workflow_id)
        if not events:
            return {"workflow_id": workflow_id, "steps": []}

        workflow_start = next((e for e in events if e.event_type == "workflow_start"), None)
        workflow_end = next((e for e in events if e.event_type == "workflow_end"), None)
        step_evts = [
            e for e in events
            if e.event_type in ("step_start", "step_finish", "step_fail", "step_skip")
        ]

        # Build steps: group by step_id, pair start with finish/fail/skip
        steps_d: dict[str, dict[str, Any]] = {}
        for e in step_evts:
            if not e.step_id:
                continue
            if e.step_id not in steps_d:
                steps_d[e.step_id] = {
                    "step_id": e.step_id,
                    "agent": e.agent,
                    "skill_name": e.skill_name,
                    "action": e.action,
                    "started_at": None,
                    "ended_at": None,
                    "duration_ms": None,
                    "status": e.status or "unknown",
                    "tool_call_summary": e.tool_call_summary,
                    "artifact_paths": e.artifact_paths or [],
                    "error": e.error,
                }
            s = steps_d[e.step_id]
            if e.event_type == "step_start":
                s["started_at"] = e.timestamp.isoformat() + "Z"
            else:
                s["ended_at"] = e.timestamp.isoformat() + "Z"
                s["status"] = e.status or s["status"]
                s["tool_call_summary"] = e.tool_call_summary or s["tool_call_summary"]
                s["artifact_paths"] = e.artifact_paths or s["artifact_paths"]
                s["error"] = e.error or s["error"]

        for s in steps_d.values():
            if s["started_at"] and s["ended_at"]:
                try:
                    start = datetime.fromisoformat(s["started_at"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(s["ended_at"].replace("Z", "+00:00"))
                    s["duration_ms"] = (end - start).total_seconds() * 1000
                except Exception:
                    pass

        return {
            "workflow_id": workflow_id,
            "started_at": workflow_start.timestamp.isoformat() + "Z" if workflow_start else None,
            "ended_at": workflow_end.timestamp.isoformat() + "Z" if workflow_end else None,
            "steps": list(steps_d.values()),
        }

    def subscribe(
        self,
        callback: Callable[[WorkflowEvent], None],
        filter: EventFilter | None = None,
        subscription_id: str | None = None,
    ) -> Subscription | None:
        """
        Subscribe to real-time workflow events.

        Args:
            callback: Function to call when matching events occur
            filter: Optional filter to limit which events trigger callback
            subscription_id: Optional ID for this subscription

        Returns:
            Subscription object that can be used to unsubscribe, or None if streaming disabled
        """
        if not self._stream:
            logger.warning("Event streaming is disabled")
            return None
        return self._stream.subscribe(callback, filter, subscription_id)

    def get_latest_events(self, workflow_id: str, limit: int = 100) -> list[WorkflowEvent]:
        """
        Get latest events for a workflow from in-memory buffer.

        Args:
            workflow_id: Workflow ID
            limit: Maximum number of events to return

        Returns:
            List of events, most recent first
        """
        if not self._stream:
            # Fallback to reading from file
            return list(reversed(self.read_events(workflow_id, limit=limit)))
        return self._stream.get_latest_events(workflow_id, limit)

    def generate_execution_graph(self, workflow_id: str) -> "ExecutionGraph":
        """
        Generate execution graph from event log.

        Args:
            workflow_id: Workflow ID

        Returns:
            ExecutionGraph instance
        """
        from .execution_graph import ExecutionGraphGenerator

        generator = ExecutionGraphGenerator(event_log=self)
        return generator.generate_graph(workflow_id)
