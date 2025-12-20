"""
Base orchestrator interface for Simple Mode.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tapps_agents.core.config import ProjectConfig

if TYPE_CHECKING:
    from ..intent_parser import Intent


class SimpleModeOrchestrator(ABC):
    """Base class for Simple Mode orchestrators."""

    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
    ):
        """
        Initialize orchestrator.

        Args:
            project_root: Project root directory
            config: Optional project configuration
        """
        self.project_root = project_root or Path.cwd()
        self.config = config

    @abstractmethod
    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute the orchestrator's workflow.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with execution results
        """
        pass

    def get_agent_sequence(self) -> list[str]:
        """
        Get the sequence of agents this orchestrator coordinates.

        Returns:
            List of agent names in execution order
        """
        return []

