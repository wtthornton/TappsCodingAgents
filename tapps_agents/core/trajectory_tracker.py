"""
Thought-Action-Result Trajectory Tracker

Tracks agent decision-making for better failure diagnosis.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Trajectory:
    """Represents a thought-action-result trajectory."""

    thought: str
    action: str
    result: str
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False


class TrajectoryTracker:
    """Tracks agent trajectories for analysis."""

    def __init__(self):
        """Initialize trajectory tracker."""
        self.trajectories: list[Trajectory] = []

    def record(self, thought: str, action: str, result: str, success: bool = False) -> None:
        """Record a trajectory."""
        self.trajectories.append(
            Trajectory(thought=thought, action=action, result=result, success=success)
        )

    def analyze_patterns(self) -> dict[str, Any]:
        """Analyze trajectories for success patterns."""
        successful = [t for t in self.trajectories if t.success]
        failed = [t for t in self.trajectories if not t.success]

        return {
            "total": len(self.trajectories),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.trajectories) if self.trajectories else 0.0,
        }

