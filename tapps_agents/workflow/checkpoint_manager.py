"""
Workflow Checkpoint Manager

Epic 12: State Persistence and Resume
Manages automatic checkpointing at step boundaries with configurable frequency.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .models import WorkflowState, WorkflowStep

logger = logging.getLogger(__name__)


class CheckpointFrequency(Enum):
    """Checkpoint frequency options."""

    EVERY_STEP = "every_step"  # Checkpoint after every step
    EVERY_N_STEPS = "every_n_steps"  # Checkpoint every N steps
    ON_GATES = "on_gates"  # Checkpoint only on gate steps (reviewer steps)
    TIME_BASED = "time_based"  # Checkpoint based on time interval
    MANUAL = "manual"  # Only checkpoint when explicitly requested


@dataclass
class CheckpointConfig:
    """Configuration for checkpoint behavior."""

    frequency: CheckpointFrequency = CheckpointFrequency.EVERY_STEP
    interval: int = 1  # For EVERY_N_STEPS or TIME_BASED (seconds for time-based)
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckpointConfig:
        """Create from dictionary."""
        frequency_str = data.get("frequency", "every_step")
        try:
            frequency = CheckpointFrequency(frequency_str)
        except ValueError:
            frequency = CheckpointFrequency.EVERY_STEP

        return cls(
            frequency=frequency,
            interval=data.get("interval", 1),
            enabled=data.get("enabled", True),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "frequency": self.frequency.value,
            "interval": self.interval,
            "enabled": self.enabled,
        }


class WorkflowCheckpointManager:
    """
    Manages workflow checkpointing with configurable frequency.
    
    Determines when checkpoints should be created based on:
    - Step completion
    - Checkpoint frequency configuration
    - Gate evaluation (for on_gates mode)
    """

    def __init__(self, config: CheckpointConfig | None = None):
        """
        Initialize checkpoint manager.

        Args:
            config: Checkpoint configuration (defaults to every step)
        """
        self.config = config or CheckpointConfig()
        self.step_count = 0
        self.last_checkpoint_time: datetime | None = None
        self.last_checkpoint_step: str | None = None

    def should_checkpoint(
        self,
        step: WorkflowStep,
        state: WorkflowState,
        is_gate_step: bool = False,
    ) -> bool:
        """
        Determine if a checkpoint should be created.

        Args:
            step: Step that just completed
            state: Current workflow state
            is_gate_step: Whether this is a gate evaluation step (reviewer)

        Returns:
            True if checkpoint should be created
        """
        if not self.config.enabled:
            return False

        self.step_count += 1

        if self.config.frequency == CheckpointFrequency.MANUAL:
            return False

        if self.config.frequency == CheckpointFrequency.EVERY_STEP:
            return True

        if self.config.frequency == CheckpointFrequency.ON_GATES:
            return is_gate_step

        if self.config.frequency == CheckpointFrequency.EVERY_N_STEPS:
            return self.step_count % self.config.interval == 0

        if self.config.frequency == CheckpointFrequency.TIME_BASED:
            if self.last_checkpoint_time is None:
                return True
            elapsed = (datetime.now() - self.last_checkpoint_time).total_seconds()
            return elapsed >= self.config.interval

        return False

    def record_checkpoint(self, step_id: str) -> None:
        """Record that a checkpoint was created."""
        self.last_checkpoint_time = datetime.now()
        self.last_checkpoint_step = step_id

    def get_checkpoint_metadata(
        self, state: WorkflowState, step: WorkflowStep | None = None
    ) -> dict[str, Any]:
        """
        Get metadata to include in checkpoint.

        Args:
            state: Current workflow state
            step: Optional step that triggered checkpoint

        Returns:
            Metadata dictionary
        """
        # Calculate progress
        total_steps = len(state.completed_steps) + len(state.skipped_steps) + 1
        if state.current_step:
            # Estimate remaining steps
            completed = len(state.completed_steps)
            total_steps = max(total_steps, completed + 5)  # Estimate

        progress = (
            len(state.completed_steps) / total_steps * 100
            if total_steps > 0
            else 0.0
        )

        metadata = {
            "checkpoint_time": datetime.now().isoformat(),
            "step_count": self.step_count,
            "current_step": state.current_step,
            "completed_steps": len(state.completed_steps),
            "skipped_steps": len(state.skipped_steps),
            "progress_percentage": round(progress, 2),
            "workflow_status": state.status,
        }

        if step:
            metadata.update(
                {
                    "trigger_step_id": step.id,
                    "trigger_step_agent": step.agent,
                    "trigger_step_action": step.action,
                }
            )

        return metadata

