"""
Workflow Auto-Progression System.

Epic 10: Workflow Auto-Progression
Implements automatic step progression, gate evaluation, error handling, and progression visibility.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..quality.quality_gates import QualityGate, QualityThresholds
from .models import StepExecution, WorkflowState, WorkflowStep

logger = logging.getLogger(__name__)


class ProgressionAction(Enum):
    """Action to take when a step completes."""

    CONTINUE = "continue"  # Proceed to next step
    SKIP = "skip"  # Skip to next step
    RETRY = "retry"  # Retry current step
    ABORT = "abort"  # Abort workflow
    PAUSE = "pause"  # Pause workflow for manual intervention


@dataclass
class ProgressionDecision:
    """Decision about how to progress after a step completes."""

    action: ProgressionAction
    next_step_id: str | None = None
    reason: str = ""
    gate_passed: bool | None = None
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressionHistory:
    """History of workflow progression decisions."""

    step_id: str
    timestamp: datetime
    action: ProgressionAction
    reason: str
    gate_result: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AutoProgressionManager:
    """
    Manages automatic workflow step progression.

    Features:
    - Automatic step progression on completion
    - Gate evaluation and routing
    - Error handling with retry/skip/abort
    - Progression history tracking
    - Visibility and control
    """

    def __init__(
        self,
        auto_progression_enabled: bool = True,
        auto_retry_enabled: bool = True,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0,
        max_retry_backoff: float = 60.0,
    ):
        """
        Initialize auto-progression manager.

        Args:
            auto_progression_enabled: Whether to enable automatic progression
            auto_retry_enabled: Whether to enable automatic retries
            max_retries: Maximum number of retry attempts
            retry_backoff_base: Base for exponential backoff
            max_retry_backoff: Maximum backoff delay in seconds
        """
        self.auto_progression_enabled = auto_progression_enabled
        self.auto_retry_enabled = auto_retry_enabled
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.max_retry_backoff = max_retry_backoff
        self.progression_history: list[ProgressionHistory] = []
        self.step_retry_counts: dict[str, int] = {}

    def should_auto_progress(self) -> bool:
        """Check if auto-progression is enabled."""
        return self.auto_progression_enabled

    def record_progression(
        self,
        step_id: str,
        action: ProgressionAction,
        reason: str,
        gate_result: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a progression decision in history.

        Args:
            step_id: Step ID that triggered the progression
            action: Action taken
            reason: Reason for the action
            gate_result: Gate evaluation result if applicable
            metadata: Additional metadata
        """
        history = ProgressionHistory(
            step_id=step_id,
            timestamp=datetime.now(),
            action=action,
            reason=reason,
            gate_result=gate_result,
            metadata=metadata or {},
        )
        self.progression_history.append(history)
        logger.info(
            f"Progression recorded: step={step_id}, action={action.value}, reason={reason}"
        )

    def get_progression_history(
        self, step_id: str | None = None
    ) -> list[ProgressionHistory]:
        """
        Get progression history, optionally filtered by step ID.

        Args:
            step_id: Optional step ID to filter by

        Returns:
            List of progression history entries
        """
        if step_id:
            return [h for h in self.progression_history if h.step_id == step_id]
        return self.progression_history.copy()

    def evaluate_gate(
        self,
        step: WorkflowStep,
        state: WorkflowState,
        review_result: dict[str, Any] | None = None,
    ) -> ProgressionDecision:
        """
        Evaluate a gate condition and determine progression.

        Args:
            step: Workflow step with gate configuration
            state: Current workflow state
            review_result: Review result from reviewer agent (if applicable)

        Returns:
            ProgressionDecision with gate evaluation result
        """
        if not step.gate:
            # No gate - proceed normally
            return ProgressionDecision(
                action=ProgressionAction.CONTINUE,
                reason="No gate configured",
            )

        gate = step.gate
        gate_result: dict[str, Any] = {}

        # Evaluate quality gate if reviewer step
        if step.agent == "reviewer" and review_result:
            # Extract scoring thresholds from step configuration
            scoring_config = step.metadata.get("scoring", {}) if step.metadata else {}
            thresholds_config = scoring_config.get("thresholds", {})  # scoring_config is always a dict

            # Create quality thresholds from step config or use defaults
            thresholds = QualityThresholds.from_dict(thresholds_config)

            # Extract scores from review result
            scores = review_result.get("scores", {})
            if not scores:
                scoring = review_result.get("scoring", {})
                if scoring:
                    scores = scoring.get("scores", {})

            # Evaluate quality gate
            quality_gate = QualityGate(thresholds=thresholds)
            gate_eval_result = quality_gate.evaluate_from_review_result(
                review_result, thresholds
            )

            passed = gate_eval_result.passed
            gate_result = {
                "passed": passed,
                "step": step.id,
                "scoring": scores,
                "gate_result": gate_eval_result.to_dict(),
            }

            # Store in state for reference
            state.variables["gate_last"] = gate_result

            # Determine next step based on gate result
            on_pass = gate.get("on_pass") or gate.get("on-pass")
            on_fail = gate.get("on_fail") or gate.get("on-fail")

            if passed:
                if on_pass:
                    return ProgressionDecision(
                        action=ProgressionAction.CONTINUE,
                        next_step_id=on_pass,
                        reason=f"Gate passed, routing to {on_pass}",
                        gate_passed=True,
                        metadata={"gate_result": gate_result},
                    )
                else:
                    return ProgressionDecision(
                        action=ProgressionAction.CONTINUE,
                        reason="Gate passed, continuing to next step",
                        gate_passed=True,
                        metadata={"gate_result": gate_result},
                    )
            else:
                if on_fail:
                    return ProgressionDecision(
                        action=ProgressionAction.CONTINUE,
                        next_step_id=on_fail,
                        reason=f"Gate failed, routing to {on_fail}",
                        gate_passed=False,
                        metadata={"gate_result": gate_result},
                    )
                else:
                    # Gate failed but no on_fail route - retry or abort?
                    retry_on_fail = gate.get("retry_on_fail", False)
                    if retry_on_fail and self.auto_retry_enabled:
                        return ProgressionDecision(
                            action=ProgressionAction.RETRY,
                            reason="Gate failed, retrying step",
                            gate_passed=False,
                            metadata={"gate_result": gate_result},
                        )
                    else:
                        return ProgressionDecision(
                            action=ProgressionAction.ABORT,
                            reason="Gate failed and no recovery path configured",
                            gate_passed=False,
                            metadata={"gate_result": gate_result},
                        )

        # For non-reviewer gates, evaluate condition if provided
        condition = gate.get("condition")
        if condition:
            # Simple condition evaluation (can be extended)
            # For now, check if condition references state variables
            try:
                # Evaluate condition as Python expression (safely)
                # This is a simplified version - in production, use a proper expression evaluator
                condition_result = self._evaluate_condition(condition, state)
                passed = bool(condition_result)

                gate_result = {
                    "passed": passed,
                    "step": step.id,
                    "condition": condition,
                }

                on_pass = gate.get("on_pass") or gate.get("on-pass")
                on_fail = gate.get("on_fail") or gate.get("on-fail")

                if passed:
                    next_step = on_pass if on_pass else None
                    return ProgressionDecision(
                        action=ProgressionAction.CONTINUE,
                        next_step_id=next_step,
                        reason=f"Gate condition passed: {condition}",
                        gate_passed=True,
                        metadata={"gate_result": gate_result},
                    )
                else:
                    next_step = on_fail if on_fail else None
                    return ProgressionDecision(
                        action=ProgressionAction.CONTINUE,
                        next_step_id=next_step,
                        reason=f"Gate condition failed: {condition}",
                        gate_passed=False,
                        metadata={"gate_result": gate_result},
                    )
            except Exception as e:
                logger.warning(f"Error evaluating gate condition: {e}")
                return ProgressionDecision(
                    action=ProgressionAction.CONTINUE,
                    reason=f"Gate evaluation error: {e}",
                    metadata={"error": str(e)},
                )

        # Default: continue
        return ProgressionDecision(
            action=ProgressionAction.CONTINUE,
            reason="Gate evaluated, no specific routing",
            metadata={"gate_result": gate_result},
        )

    def _evaluate_condition(self, condition: str, state: WorkflowState) -> Any:
        """
        Evaluate a condition expression against workflow state.

        This is a simplified evaluator. In production, use a proper expression evaluator
        like `simpleeval` or `asteval` for safety.

        Args:
            condition: Condition expression string
            state: Workflow state

        Returns:
            Evaluation result
        """
        # Simple variable substitution
        # Replace state.variables references
        for key, value in state.variables.items():
            condition = condition.replace(f"variables.{key}", str(value))
            condition = condition.replace(f"state.{key}", str(value))

        # Check for common patterns
        if "gate_last.passed" in condition:
            gate_last = state.variables.get("gate_last", {})
            passed = gate_last.get("passed", False)
            if "==" in condition and "true" in condition:
                return passed
            elif "==" in condition and "false" in condition:
                return not passed
            return passed

        # For now, return True as default (can be enhanced)
        return True

    def handle_step_completion(
        self,
        step: WorkflowStep,
        state: WorkflowState,
        step_execution: StepExecution,
        review_result: dict[str, Any] | None = None,
    ) -> ProgressionDecision:
        """
        Handle step completion and determine next action.

        Args:
            step: Completed workflow step
            state: Current workflow state
            step_execution: Step execution record
            review_result: Review result if this was a reviewer step

        Returns:
            ProgressionDecision with next action
        """
        # Check if step failed
        if step_execution.status == "failed":
            return self._handle_step_failure(step, state, step_execution)

        # Step completed successfully - evaluate gate if present
        if step.gate:
            decision = self.evaluate_gate(step, state, review_result)
            self.record_progression(
                step_id=step.id,
                action=decision.action,
                reason=decision.reason,
                gate_result=decision.metadata.get("gate_result"),
                metadata=decision.metadata,
            )
            return decision

        # No gate - continue to next step
        decision = ProgressionDecision(
            action=ProgressionAction.CONTINUE,
            reason="Step completed successfully",
        )
        self.record_progression(
            step_id=step.id,
            action=decision.action,
            reason=decision.reason,
        )
        return decision

    def _handle_step_failure(
        self,
        step: WorkflowStep,
        state: WorkflowState,
        step_execution: StepExecution,
    ) -> ProgressionDecision:
        """
        Handle step failure and determine recovery action.

        Args:
            step: Failed workflow step
            state: Current workflow state
            step_execution: Step execution record with error

        Returns:
            ProgressionDecision with recovery action
        """
        step_id = step.id
        retry_count = self.step_retry_counts.get(step_id, 0)

        # Check if we should retry
        if self.auto_retry_enabled and retry_count < self.max_retries:
            # Check step metadata for retry configuration
            retry_config = step.metadata.get("retry", {})
            if retry_config.get("enabled", True):
                self.step_retry_counts[step_id] = retry_count + 1
                backoff = min(
                    self.retry_backoff_base**retry_count,
                    self.max_retry_backoff,
                )

                decision = ProgressionDecision(
                    action=ProgressionAction.RETRY,
                    reason=f"Step failed, retrying (attempt {retry_count + 1}/{self.max_retries})",
                    retry_count=retry_count + 1,
                    metadata={
                        "error": step_execution.error,
                        "backoff_seconds": backoff,
                    },
                )
                self.record_progression(
                    step_id=step_id,
                    action=decision.action,
                    reason=decision.reason,
                    metadata=decision.metadata,
                )
                return decision

        # Check if step should be skipped on failure
        skip_on_fail = step.metadata.get("skip_on_fail", False)
        if skip_on_fail:
            decision = ProgressionDecision(
                action=ProgressionAction.SKIP,
                reason="Step failed but configured to skip on failure",
                metadata={"error": step_execution.error},
            )
            self.record_progression(
                step_id=step_id,
                action=decision.action,
                reason=decision.reason,
                metadata=decision.metadata,
            )
            return decision

        # Check if error is recoverable
        error_recoverable = step.metadata.get("error_recoverable", False)
        if error_recoverable:
            # Try to continue despite error
            decision = ProgressionDecision(
                action=ProgressionAction.CONTINUE,
                reason="Step failed but error is recoverable, continuing",
                metadata={"error": step_execution.error},
            )
            self.record_progression(
                step_id=step_id,
                action=decision.action,
                reason=decision.reason,
                metadata=decision.metadata,
            )
            return decision

        # Default: abort workflow
        decision = ProgressionDecision(
            action=ProgressionAction.ABORT,
            reason=f"Step failed after {retry_count} retries: {step_execution.error}",
            metadata={"error": step_execution.error, "retry_count": retry_count},
        )
        self.record_progression(
            step_id=step_id,
            action=decision.action,
            reason=decision.reason,
            metadata=decision.metadata,
        )
        return decision

    def get_next_step_id(
        self,
        step: WorkflowStep,
        decision: ProgressionDecision,
        workflow_steps: list[WorkflowStep],
    ) -> str | None:
        """
        Determine the next step ID based on progression decision.

        Args:
            step: Current step
            decision: Progression decision
            workflow_steps: All workflow steps

        Returns:
            Next step ID, or None if workflow should complete
        """
        if decision.action == ProgressionAction.ABORT:
            return None

        if decision.action == ProgressionAction.RETRY:
            return step.id  # Retry same step

        if decision.action == ProgressionAction.SKIP:
            # Skip to next step
            return step.next

        if decision.next_step_id:
            # Gate-based routing
            return decision.next_step_id

        # Default: use step.next
        return step.next

    def get_progression_status(
        self, state: WorkflowState, workflow_steps: list[WorkflowStep]
    ) -> dict[str, Any]:
        """
        Get current progression status and visibility information.

        Args:
            state: Current workflow state
            workflow_steps: All workflow steps

        Returns:
            Dictionary with progression status information
        """
        current_step = None
        if state.current_step:
            current_step = next(
                (s for s in workflow_steps if s.id == state.current_step), None
            )

        next_step = None
        if current_step and current_step.next:
            next_step = next(
                (s for s in workflow_steps if s.id == current_step.next), None
            )

        return {
            "auto_progression_enabled": self.auto_progression_enabled,
            "current_step": {
                "id": state.current_step,
                "agent": current_step.agent if current_step else None,
                "action": current_step.action if current_step else None,
            },
            "next_step": {
                "id": next_step.id if next_step else None,
                "agent": next_step.agent if next_step else None,
                "action": next_step.action if next_step else None,
            },
            "completed_steps": len(state.completed_steps),
            "total_steps": len(workflow_steps),
            "progression_history_count": len(self.progression_history),
            "status": state.status,
        }

