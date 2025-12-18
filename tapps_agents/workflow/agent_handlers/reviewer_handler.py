"""
Reviewer Agent Handler

Handles execution of reviewer agent steps with quality gate evaluation.

Epic 20: Complexity Reduction - Story 20.1
"""

from pathlib import Path
from typing import Any

from ...quality.quality_gates import QualityGate, QualityThresholds
from ..models import WorkflowStep
from .base import AgentExecutionHandler


class ReviewerHandler(AgentExecutionHandler):
    """Handler for reviewer agent execution."""
    
    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports reviewer agent."""
        return agent_name == "reviewer" and action in {"review_code", "review", "score"}
    
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute reviewer step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Target file path
            
        Returns:
            List of created artifacts (empty for reviewer)
        """
        # Determine review target
        review_target = self._find_review_target(target_path)
        if not review_target or not review_target.exists():
            raise ValueError("Reviewer step requires a target file to review.")
        
        # Run reviewer agent
        review_result = await self.run_agent(
            "reviewer", "score", file=str(review_target)
        )
        self.state.variables["reviewer_result"] = review_result
        
        # Evaluate gate if configured
        gate = step.gate or {}
        if gate:
            self._evaluate_quality_gate(step, review_result, gate)
        
        return []
    
    def _find_review_target(self, target_path: Path | None) -> Path | None:
        """Find the target file to review."""
        fixed_file = self.state.variables.get("fixed_file")
        implementer_file = self.state.variables.get("target_file")
        
        if fixed_file:
            return Path(fixed_file)
        elif implementer_file:
            return Path(implementer_file)
        elif target_path:
            return target_path
        return None
    
    def _evaluate_quality_gate(
        self,
        step: WorkflowStep,
        review_result: dict[str, Any],
        gate: dict[str, Any],
    ) -> None:
        """Evaluate quality gate and update state."""
        # Extract scoring thresholds from step configuration
        scoring_config = step.metadata.get("scoring", {}) if step.metadata else {}
        thresholds_config = scoring_config.get("thresholds", {}) if scoring_config else {}
        
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
        gate_result = quality_gate.evaluate_from_review_result(review_result, thresholds)
        
        passed = gate_result.passed
        self.state.variables["gate_last"] = {
            "step": step.id,
            "passed": passed,
            "scoring": scores,
            "gate_result": gate_result.to_dict(),
        }
        
        on_pass = gate.get("on_pass") or gate.get("on-pass")
        on_fail = gate.get("on_fail") or gate.get("on-fail")
        
        # Mark review complete, but override next step based on gate decision
        if self.executor and hasattr(self.executor, "mark_step_complete"):
            self.executor.mark_step_complete(step_id=step.id, artifacts=None)
        
        if passed and on_pass:
            self.state.current_step = on_pass
        elif (not passed) and on_fail:
            self.state.current_step = on_fail
        
        if self.executor and hasattr(self.executor, "save_state"):
            self.executor.save_state()

