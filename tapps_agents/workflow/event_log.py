"""
Append-Only Workflow Event Log

Provides durable, append-only event logging for workflow execution.
Epic 5 / Story 5.4: Workflow State Management
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
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
        return cls(**data)


class WorkflowEventLog:
    """Manages append-only event log for workflow execution."""

    def __init__(self, events_dir: Path):
        """
        Initialize event log.

        Args:
            events_dir: Directory to store event log files
        """
        self.events_dir = Path(events_dir)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self._sequence_counter: dict[str, int] = {}

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
                    with open(event_file, "r", encoding="utf-8") as f:
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

        Returns:
            Created WorkflowEvent
        """
        seq = self._get_next_sequence(workflow_id)
        event = WorkflowEvent(
            event_type=event_type,
            workflow_id=workflow_id,
            seq=seq,
            timestamp=datetime.utcnow(),
            step_id=step_id,
            agent=agent,
            action=action,
            status=status,
            error=error,
            artifacts=artifacts,
            metadata=metadata,
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
            with open(event_file, "r", encoding="utf-8") as f:
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
