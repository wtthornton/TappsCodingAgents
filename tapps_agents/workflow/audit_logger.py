"""
Audit Logger for Background Agent Auto-Execution.

Provides comprehensive audit logging for troubleshooting and compliance.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logger for execution events."""

    def __init__(self, audit_dir: Path | None = None, project_root: Path | None = None):
        """
        Initialize audit logger.

        Args:
            audit_dir: Directory to store audit logs (defaults to .tapps-agents/audit)
            project_root: Project root directory (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.audit_dir = audit_dir or (self.project_root / ".tapps-agents" / "audit")
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Set up file handler with rotation
        self.log_file = self.audit_dir / "execution_audit.log"
        self.handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        self.handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        # Create audit logger
        self.audit_logger = logging.getLogger("tapps_agents.audit")
        self.audit_logger.addHandler(self.handler)
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.propagate = False

    def log_event(
        self,
        event_type: str,
        workflow_id: str | None = None,
        step_id: str | None = None,
        command: str | None = None,
        status: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event (e.g., "command_detected", "execution_started")
            workflow_id: Workflow identifier
            step_id: Step identifier
            command: Command being executed
            status: Event status
            details: Additional event details
        """
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "workflow_id": workflow_id,
            "step_id": step_id,
            "command": command,
            "status": status,
            "details": details or {},
        }

        # Log as JSON for structured logging
        self.audit_logger.info(json.dumps(event))

    def log_command_detected(
        self,
        workflow_id: str,
        step_id: str,
        command: str,
        command_file: Path,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log command file detection."""
        details = {"command_file": str(command_file)}
        if metadata:
            details["metadata"] = metadata
        self.log_event(
            event_type="command_detected",
            workflow_id=workflow_id,
            step_id=step_id,
            command=command,
            details=details,
        )

    def log_execution_started(
        self,
        workflow_id: str,
        step_id: str,
        command: str,
    ) -> None:
        """Log execution start."""
        self.log_event(
            event_type="execution_started",
            workflow_id=workflow_id,
            step_id=step_id,
            command=command,
            status="started",
        )

    def log_execution_completed(
        self,
        workflow_id: str,
        step_id: str,
        command: str,
        duration_ms: float,
    ) -> None:
        """Log execution completion."""
        self.log_event(
            event_type="execution_completed",
            workflow_id=workflow_id,
            step_id=step_id,
            command=command,
            status="completed",
            details={"duration_ms": duration_ms},
        )

    def log_execution_failed(
        self,
        workflow_id: str,
        step_id: str,
        command: str,
        error: str,
        duration_ms: float | None = None,
    ) -> None:
        """Log execution failure."""
        self.log_event(
            event_type="execution_failed",
            workflow_id=workflow_id,
            step_id=step_id,
            command=command,
            status="failed",
            details={"error": error, "duration_ms": duration_ms},
        )

    def log_status_updated(
        self,
        workflow_id: str,
        step_id: str,
        old_status: str,
        new_status: str,
    ) -> None:
        """Log status transition."""
        self.log_event(
            event_type="status_updated",
            workflow_id=workflow_id,
            step_id=step_id,
            status=new_status,
            details={"old_status": old_status, "new_status": new_status},
        )

    def log_decision(
        self,
        workflow_id: str,
        step_id: str,
        skill_name: str,
        command: str,
        input_summary: str,
        rationale: str | None,
        outcome: str,
    ) -> None:
        """
        Log a decision (e.g. quality gate, implementer write) for explainability.

        Args:
            workflow_id: Workflow identifier
            step_id: Step identifier
            skill_name: Skill or agent name
            command: Command or action
            input_summary: Brief summary of inputs
            rationale: Optional rationale for the decision
            outcome: Outcome (e.g. "pass", "fail", "approved")
        """
        self.log_event(
            event_type="decision",
            workflow_id=workflow_id,
            step_id=step_id,
            command=command,
            status=outcome,
            details={
                "skill_name": skill_name,
                "input_summary": input_summary,
                "rationale": rationale,
            },
        )

    def query_events(
        self,
        workflow_id: str | None = None,
        step_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Query audit events.

        Args:
            workflow_id: Filter by workflow ID
            step_id: Filter by step ID
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        events: list[dict[str, Any]] = []

        try:
            # Read from log file (most recent first)
            if self.log_file.exists():
                with open(self.log_file, encoding="utf-8") as f:
                    lines = f.readlines()

                # Parse JSON from each line
                for line in reversed(lines):
                    if len(events) >= limit:
                        break

                    try:
                        # Extract JSON from log line (format: timestamp | level | json)
                        parts = line.split(" | ", 2)
                        if len(parts) >= 3:
                            json_str = parts[2].strip()
                            event = json.loads(json_str)

                            # Apply filters
                            if workflow_id and event.get("workflow_id") != workflow_id:
                                continue
                            if step_id and event.get("step_id") != step_id:
                                continue
                            if event_type and event.get("event_type") != event_type:
                                continue

                            events.append(event)
                    except Exception:
                        continue

        except Exception as e:
            logger.error(f"Failed to query audit events: {e}")

        return events[:limit]

