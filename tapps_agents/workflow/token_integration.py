"""Token monitoring integration for workflow execution.

This module provides integration helpers for adding token monitoring
to workflow execution without modifying core workflow code.

Usage:
    from tapps_agents.workflow.token_integration import TokenAwareWorkflow

    workflow = TokenAwareWorkflow(executor, token_budget=200000)
    result = await workflow.execute_with_monitoring(workflow_def)
"""

import logging
from pathlib import Path
from typing import Any

from tapps_agents.core.token_monitor import (
    TokenBudget,
    TokenMonitor,
)
from tapps_agents.workflow.checkpoint import CheckpointManager

logger = logging.getLogger(__name__)


class TokenAwareWorkflow:
    """Wrapper for workflow executor with token monitoring.

    This class wraps the standard WorkflowExecutor and adds:
    - Token budget monitoring
    - Automatic checkpoint at 90% threshold
    - Warning messages at 50%, 75%, 90%

    Example:
        >>> from tapps_agents.workflow.executor import WorkflowExecutor
        >>> from tapps_agents.workflow.token_integration import TokenAwareWorkflow
        >>>
        >>> executor = WorkflowExecutor()
        >>> monitored = TokenAwareWorkflow(executor, token_budget=200000)
        >>> result = await monitored.execute_with_monitoring(workflow)
    """

    def __init__(
        self,
        executor: Any,  # WorkflowExecutor
        token_budget: int = 200000,
        enable_auto_checkpoint: bool = True,
        checkpoint_dir: Path | None = None
    ):
        """Initialize token-aware workflow wrapper.

        Args:
            executor: WorkflowExecutor instance to wrap
            token_budget: Total token budget
            enable_auto_checkpoint: Enable automatic checkpointing at 90%
            checkpoint_dir: Directory for checkpoints
        """
        self.executor = executor
        self.token_monitor = TokenMonitor(
            TokenBudget(total=token_budget),
            enable_warnings=True,
            checkpoint_threshold=90.0
        )
        self.enable_auto_checkpoint = enable_auto_checkpoint
        self.checkpoint_manager = CheckpointManager(checkpoint_dir) if enable_auto_checkpoint else None

    async def execute_with_monitoring(
        self,
        workflow: Any,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Execute workflow with token monitoring.

        Args:
            workflow: Workflow definition
            **kwargs: Additional arguments for executor

        Returns:
            Workflow execution result with token stats
        """
        # Execute workflow (delegating to real executor)
        result = await self.executor.execute(workflow, **kwargs)

        # Estimate tokens consumed (rough estimate based on output)
        # In production, this should use actual API token counts
        tokens_consumed = self._estimate_tokens(result)

        # Update token monitor
        monitor_result = self.token_monitor.update(tokens_consumed)

        # Show warnings if threshold crossed
        if monitor_result.message:
            print(monitor_result.message)
            logger.warning(f"Token threshold crossed: {monitor_result.threshold}")

        # Auto-checkpoint if needed
        if self.enable_auto_checkpoint and monitor_result.should_checkpoint:
            self._create_checkpoint(workflow, result)

        # Add token stats to result
        result["token_stats"] = {
            "consumed": monitor_result.consumed,
            "remaining": monitor_result.remaining,
            "percentage": monitor_result.percentage,
            "threshold": monitor_result.threshold
        }

        return result

    def _estimate_tokens(self, result: dict[str, Any]) -> int:
        """Estimate tokens consumed from workflow result.

        This is a rough estimate. In production, use actual API token counts.

        Args:
            result: Workflow execution result

        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token per 4 characters
        # This should be replaced with actual API token counts
        total_chars = 0

        if "artifacts" in result:
            for artifact in result["artifacts"].values():
                if isinstance(artifact, dict) and "content" in artifact:
                    total_chars += len(str(artifact["content"]))

        if "output" in result:
            total_chars += len(str(result["output"]))

        # Convert chars to tokens (rough estimate)
        return total_chars // 4

    def _create_checkpoint(self, workflow: Any, result: dict[str, Any]) -> None:
        """Create checkpoint at token threshold.

        Args:
            workflow: Workflow definition
            result: Current workflow result
        """
        if not self.checkpoint_manager:
            return

        try:
            workflow_state = {
                "workflow_id": getattr(workflow, "id", "unknown"),
                "workflow_type": getattr(workflow, "type", "unknown"),
                "completed_steps": result.get("completed_steps", []),
                "current_step": result.get("current_step", ""),
                "pending_steps": result.get("pending_steps", []),
                "context": result.get("context", {}),
                "results": result.get("artifacts", {}),
                "tokens_consumed": self.token_monitor.budget.consumed,
                "tokens_remaining": self.token_monitor.budget.remaining,
                "time_elapsed": result.get("elapsed_time", 0.0)
            }

            checkpoint = self.checkpoint_manager.create_checkpoint(
                workflow_state,
                reason="token_threshold"
            )

            print(f"\n🔖 Auto-checkpoint created: {checkpoint.checkpoint_id}")
            print(f"   Resume with: tapps-agents resume {checkpoint.checkpoint_id}\n")

        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}", exc_info=True)

    def get_token_status(self) -> str:
        """Get current token status.

        Returns:
            Formatted status string
        """
        return self.token_monitor.format_status(verbose=True)

    def get_stats(self) -> dict[str, Any]:
        """Get token monitoring statistics.

        Returns:
            Statistics dictionary
        """
        return self.token_monitor.get_stats()


def create_monitored_workflow(
    executor: Any,
    token_budget: int = 200000,
    enable_auto_checkpoint: bool = True
) -> TokenAwareWorkflow:
    """Convenience function to create token-monitored workflow.

    Args:
        executor: WorkflowExecutor instance
        token_budget: Total token budget
        enable_auto_checkpoint: Enable auto-checkpoint

    Returns:
        TokenAwareWorkflow instance

    Example:
        >>> executor = WorkflowExecutor()
        >>> workflow = create_monitored_workflow(executor)
        >>> result = await workflow.execute_with_monitoring(workflow_def)
    """
    return TokenAwareWorkflow(
        executor,
        token_budget=token_budget,
        enable_auto_checkpoint=enable_auto_checkpoint
    )
