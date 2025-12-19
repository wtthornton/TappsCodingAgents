"""
Task State Management for Checkpointing

Defines task states and state management for checkpoint/resume functionality.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskState(Enum):
    """Task execution states."""

    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    CHECKPOINTED = "checkpointed"
    COMPLETED = "completed"
    FAILED = "failed"
    RESUMED = "resumed"
    RETRY = "retry"


@dataclass
class StateTransition:
    """Record of a state transition."""

    from_state: TaskState
    to_state: TaskState
    timestamp: datetime
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskStateManager:
    """Manages task state transitions and validation."""

    # Valid state transitions
    VALID_TRANSITIONS = {
        TaskState.INITIALIZED: {TaskState.RUNNING},
        TaskState.RUNNING: {
            TaskState.CHECKPOINTED,
            TaskState.PAUSED,
            TaskState.COMPLETED,
            TaskState.FAILED,
        },
        TaskState.CHECKPOINTED: {TaskState.RUNNING, TaskState.PAUSED},
        TaskState.PAUSED: {TaskState.RESUMED, TaskState.RUNNING},
        TaskState.RESUMED: {TaskState.RUNNING},
        TaskState.FAILED: {TaskState.RETRY, TaskState.RUNNING},
        TaskState.RETRY: {TaskState.RUNNING},
        TaskState.COMPLETED: set(),  # Terminal state
    }

    def __init__(self, task_id: str, initial_state: TaskState = TaskState.INITIALIZED):
        """
        Initialize state manager.

        Args:
            task_id: Unique task identifier
            initial_state: Initial state (default: INITIALIZED)
        """
        self.task_id = task_id
        self.current_state = initial_state
        self.transitions: list[StateTransition] = []
        self._record_transition(initial_state, "Initial state")

    def transition(
        self,
        new_state: TaskState,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Transition to a new state.

        Args:
            new_state: Target state
            reason: Optional reason for transition
            metadata: Optional metadata

        Returns:
            True if transition is valid and successful, False otherwise

        Raises:
            ValueError: If transition is invalid
        """
        if not self.can_transition(new_state):
            raise ValueError(
                f"Invalid state transition from {self.current_state.value} to {new_state.value} "
                f"for task {self.task_id}"
            )

        old_state = self.current_state
        self.current_state = new_state
        self._record_transition(new_state, reason, metadata)

        logger.info(
            f"[{self.task_id}] State transition: {old_state.value} -> {new_state.value} "
            f"({reason or 'no reason'})"
        )

        return True

    def can_transition(self, new_state: TaskState) -> bool:
        """
        Check if transition to new state is valid.

        Args:
            new_state: Target state

        Returns:
            True if transition is valid
        """
        valid_targets = self.VALID_TRANSITIONS.get(self.current_state, set())
        return new_state in valid_targets

    def _record_transition(
        self,
        state: TaskState,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Record a state transition."""
        transition = StateTransition(
            from_state=self.current_state if self.transitions else state,
            to_state=state,
            timestamp=datetime.now(UTC),
            reason=reason,
            metadata=metadata or {},
        )
        self.transitions.append(transition)

    def get_state_history(self) -> list[StateTransition]:
        """
        Get state transition history.

        Returns:
            List of state transitions
        """
        return self.transitions.copy()

    def is_terminal(self) -> bool:
        """
        Check if current state is terminal (cannot transition further).

        Returns:
            True if in terminal state
        """
        return self.current_state == TaskState.COMPLETED

    def can_resume(self) -> bool:
        """
        Check if task can be resumed from current state.

        Returns:
            True if task can be resumed
        """
        return self.current_state in {
            TaskState.PAUSED,
            TaskState.CHECKPOINTED,
            TaskState.FAILED,
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Convert state manager to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "task_id": self.task_id,
            "current_state": self.current_state.value,
            "transitions": [
                {
                    "from_state": t.from_state.value,
                    "to_state": t.to_state.value,
                    "timestamp": t.timestamp.isoformat(),
                    "reason": t.reason,
                    "metadata": t.metadata,
                }
                for t in self.transitions
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskStateManager:
        """
        Create state manager from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            TaskStateManager instance
        """
        task_id = data["task_id"]
        transitions_data = data.get("transitions", [])

        if transitions_data:
            initial_state = TaskState(transitions_data[0]["to_state"])
            manager = cls(task_id, initial_state)

            # Restore all transitions
            for t_data in transitions_data[1:]:
                manager.current_state = TaskState(t_data["to_state"])
                transition = StateTransition(
                    from_state=TaskState(t_data["from_state"]),
                    to_state=TaskState(t_data["to_state"]),
                    timestamp=datetime.fromisoformat(t_data["timestamp"]),
                    reason=t_data.get("reason"),
                    metadata=t_data.get("metadata", {}),
                )
                manager.transitions.append(transition)
        else:
            manager = cls(task_id)

        return manager
