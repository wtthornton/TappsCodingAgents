"""
Outcome Tracking System

Tracks code quality outcomes and correlates with scoring to enable adaptive learning.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CodeOutcome:
    """Tracks code quality outcome for adaptive learning."""

    workflow_id: str
    file_path: str
    initial_scores: dict[str, float]  # Scores from first review
    final_scores: dict[str, float]  # Scores after all iterations
    iterations: int  # Number of iterations needed
    expert_consultations: list[str] = field(default_factory=list)  # Expert IDs consulted
    time_to_correctness: float = 0.0  # Seconds to achieve quality threshold
    first_pass_success: bool = False  # Whether first pass met quality threshold
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_id: str | None = None  # Agent that generated the code
    prompt_hash: str | None = None  # Hash of original prompt for correlation


class OutcomeTracker:
    """
    Tracks code quality outcomes for adaptive learning.
    
    Stores outcomes in JSONL format for analysis by adaptive scoring engine.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize outcome tracker.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        self.learning_dir = self.project_root / ".tapps-agents" / "learning"
        self.outcomes_file = self.learning_dir / "outcomes.jsonl"

        # Ensure learning directory exists
        self.learning_dir.mkdir(parents=True, exist_ok=True)

    def track_initial_scores(
        self,
        workflow_id: str,
        file_path: str,
        scores: dict[str, float],
        expert_consultations: list[str] | None = None,
        agent_id: str | None = None,
        prompt_hash: str | None = None,
    ) -> CodeOutcome:
        """
        Track initial code scores from first review.

        Args:
            workflow_id: Unique workflow identifier
            file_path: Path to code file
            scores: Initial quality scores
            expert_consultations: List of expert IDs consulted
            agent_id: Agent that generated the code
            prompt_hash: Hash of original prompt

        Returns:
            CodeOutcome object for tracking
        """
        outcome = CodeOutcome(
            workflow_id=workflow_id,
            file_path=str(file_path),
            initial_scores=scores.copy(),
            final_scores={},  # Will be updated later
            iterations=1,
            expert_consultations=expert_consultations or [],
            agent_id=agent_id,
            prompt_hash=prompt_hash,
        )

        # Check if first pass succeeded (assuming threshold of 70)
        quality_threshold = 70.0
        overall_score = self._calculate_overall_score(scores)
        outcome.first_pass_success = overall_score >= quality_threshold

        return outcome

    def track_iteration(
        self,
        workflow_id: str,
        scores: dict[str, float],
        iteration_number: int,
    ) -> CodeOutcome | None:
        """
        Track iteration scores.

        Args:
            workflow_id: Workflow identifier
            scores: Scores from this iteration
            iteration_number: Iteration number (1-based)

        Returns:
            Updated CodeOutcome if found, None otherwise
        """
        outcome = self._load_outcome(workflow_id)
        if not outcome:
            logger.warning(f"Outcome not found for workflow {workflow_id}")
            return None

        outcome.iterations = iteration_number
        outcome.final_scores = scores.copy()

        return outcome

    def finalize_outcome(
        self,
        workflow_id: str,
        final_scores: dict[str, float],
        time_to_correctness: float | None = None,
    ) -> CodeOutcome | None:
        """
        Finalize outcome tracking.

        Args:
            workflow_id: Workflow identifier
            final_scores: Final quality scores
            time_to_correctness: Time in seconds to achieve quality

        Returns:
            Finalized CodeOutcome
        """
        outcome = self._load_outcome(workflow_id)
        if not outcome:
            logger.warning(f"Outcome not found for workflow {workflow_id}")
            return None

        outcome.final_scores = final_scores.copy()
        if time_to_correctness is not None:
            outcome.time_to_correctness = time_to_correctness

        # Save outcome
        self._save_outcome(outcome)

        return outcome

    def save_outcome(self, outcome: CodeOutcome) -> None:
        """
        Save outcome to JSONL file.

        Args:
            outcome: CodeOutcome to save
        """
        self._save_outcome(outcome)

    def load_outcomes(
        self, limit: int | None = None, workflow_id: str | None = None
    ) -> list[CodeOutcome]:
        """
        Load outcomes from storage.

        Args:
            limit: Maximum number of outcomes to load
            workflow_id: Filter by workflow ID

        Returns:
            List of CodeOutcome objects
        """
        if not self.outcomes_file.exists():
            return []

        outcomes = []
        try:
            with open(self.outcomes_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    if workflow_id and data.get("workflow_id") != workflow_id:
                        continue
                    outcomes.append(CodeOutcome(**data))
                    if limit and len(outcomes) >= limit:
                        break
        except Exception as e:
            logger.error(f"Error loading outcomes: {e}")

        return outcomes

    def get_outcome_statistics(self) -> dict[str, Any]:
        """
        Get statistics about tracked outcomes.

        Returns:
            Dictionary with statistics
        """
        outcomes = self.load_outcomes()

        if not outcomes:
            return {
                "total_outcomes": 0,
                "first_pass_success_rate": 0.0,
                "avg_iterations": 0.0,
                "avg_time_to_correctness": 0.0,
            }

        first_pass_successes = sum(1 for o in outcomes if o.first_pass_success)
        total_iterations = sum(o.iterations for o in outcomes)
        total_time = sum(o.time_to_correctness for o in outcomes if o.time_to_correctness > 0)
        outcomes_with_time = sum(1 for o in outcomes if o.time_to_correctness > 0)

        return {
            "total_outcomes": len(outcomes),
            "first_pass_success_rate": first_pass_successes / len(outcomes),
            "avg_iterations": total_iterations / len(outcomes),
            "avg_time_to_correctness": total_time / outcomes_with_time if outcomes_with_time > 0 else 0.0,
            "expert_usage": self._calculate_expert_usage(outcomes),
        }

    def _save_outcome(self, outcome: CodeOutcome) -> None:
        """Save outcome to JSONL file."""
        try:
            with open(self.outcomes_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(outcome), default=str) + "\n")
        except Exception as e:
            logger.error(f"Error saving outcome: {e}")

    def _load_outcome(self, workflow_id: str) -> CodeOutcome | None:
        """Load specific outcome by workflow ID."""
        outcomes = self.load_outcomes(workflow_id=workflow_id)
        return outcomes[0] if outcomes else None

    def _calculate_overall_score(self, scores: dict[str, float]) -> float:
        """Calculate overall quality score from individual scores."""
        # Use default weights if not provided
        weights = {
            "complexity_score": 0.18,
            "security_score": 0.27,
            "maintainability_score": 0.24,
            "test_coverage_score": 0.13,
            "performance_score": 0.08,
            "structure_score": 0.05,
            "devex_score": 0.05,
        }

        total = 0.0
        for metric, weight in weights.items():
            if metric in scores:
                # Convert 0-10 scores to 0-100 scale
                score = scores[metric]
                if score <= 10.0:  # Assume 0-10 scale
                    score = score * 10.0
                total += score * weight

        return total

    def _calculate_expert_usage(
        self, outcomes: list[CodeOutcome]
    ) -> dict[str, int]:
        """Calculate expert usage statistics."""
        expert_counts: dict[str, int] = {}
        for outcome in outcomes:
            for expert_id in outcome.expert_consultations:
                expert_counts[expert_id] = expert_counts.get(expert_id, 0) + 1
        return expert_counts
