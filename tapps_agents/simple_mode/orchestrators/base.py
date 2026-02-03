"""
Base orchestrator interface for Simple Mode.

Integrates optional hook system: UserPromptSubmit before workflow,
PostToolUse after implementer tool use, WorkflowComplete after workflow ends.
Hooks are opt-in (no behavior change when hooks disabled).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tapps_agents.core.config import ProjectConfig

if TYPE_CHECKING:
    from ..intent_parser import Intent

logger = logging.getLogger(__name__)


def _get_hook_manager(project_root: Path) -> Any:
    """
    Load HookManager for project if hooks are configured.

    Returns None when hooks.yaml is missing or has no enabled hooks (opt-in).
    """
    try:
        from tapps_agents.hooks.config import load_hooks_config
        from tapps_agents.hooks.manager import HookManager

        config = load_hooks_config(project_root=project_root)
        has_any = any(
            any(h.enabled for h in hooks)
            for hooks in config.hooks.values()
        )
        if not has_any:
            return None
        return HookManager(project_root=project_root)
    except Exception as e:  # pylint: disable=broad-except
        logger.debug("Hooks not loaded (opt-in): %s", e)
        return None


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
        self._hook_manager = None  # Lazy-loaded when needed

    def _get_hook_manager(self) -> Any:
        """Return HookManager if hooks are enabled for this project; else None."""
        if self._hook_manager is None:
            self._hook_manager = _get_hook_manager(self.project_root)
        return self._hook_manager

    def _trigger_user_prompt_submit(
        self,
        prompt: str,
        workflow_type: str | None = None,
    ) -> None:
        """
        Fire UserPromptSubmit hook before workflow execution.

        No-op when hooks disabled or no hooks configured for this event.
        """
        mgr = self._get_hook_manager()
        if not mgr:
            return
        try:
            from tapps_agents.hooks.events import UserPromptSubmitEvent

            payload = UserPromptSubmitEvent(
                prompt=prompt,
                project_root=str(self.project_root),
                workflow_type=workflow_type,
            )
            mgr.trigger("UserPromptSubmit", payload)
        except Exception as e:  # pylint: disable=broad-except
            logger.debug("UserPromptSubmit hook error (non-fatal): %s", e)

    def _trigger_post_tool_use(
        self,
        tool_name: str,
        file_path: str | None,
        file_paths: list[str] | None = None,
        workflow_id: str | None = None,
    ) -> None:
        """
        Fire PostToolUse hook after implementer Write/Edit.

        No-op when hooks disabled or no matching hooks.
        """
        mgr = self._get_hook_manager()
        if not mgr:
            return
        try:
            from tapps_agents.hooks.events import PostToolUseEvent

            payload = PostToolUseEvent(
                file_path=file_path,
                file_paths=file_paths or ([file_path] if file_path else []),
                tool_name=tool_name,
                project_root=str(self.project_root),
                workflow_id=workflow_id,
            )
            mgr.trigger(
                "PostToolUse",
                payload,
                tool_name=tool_name,
                file_path=file_path,
            )
        except Exception as e:  # pylint: disable=broad-except
            logger.debug("PostToolUse hook error (non-fatal): %s", e)

    def _trigger_workflow_complete(
        self,
        workflow_type: str,
        workflow_id: str,
        status: str,
        beads_issue_id: str | None = None,
    ) -> None:
        """
        Fire WorkflowComplete hook after workflow ends.

        status: 'completed', 'failed', or 'cancelled'.
        No-op when hooks disabled.
        """
        mgr = self._get_hook_manager()
        if not mgr:
            return
        try:
            from tapps_agents.hooks.events import WorkflowCompleteEvent

            payload = WorkflowCompleteEvent(
                workflow_type=workflow_type,
                workflow_id=workflow_id,
                status=status,
                project_root=str(self.project_root),
                beads_issue_id=beads_issue_id,
            )
            mgr.trigger("WorkflowComplete", payload)
        except Exception as e:  # pylint: disable=broad-except
            logger.debug("WorkflowComplete hook error (non-fatal): %s", e)

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

