"""
Expert Performance Tracker

Tracks expert consultation effectiveness for adaptive learning.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..core.outcome_tracker import CodeOutcome, OutcomeTracker

logger = logging.getLogger(__name__)


@dataclass
class ExpertPerformance:
    """Performance metrics for an expert."""

    expert_id: str
    consultations: int = 0
    avg_confidence: float = 0.0
    first_pass_success_rate: float = 0.0
    code_quality_improvement: float = 0.0  # Delta in scores
    domain_coverage: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ExpertPerformanceTracker:
    """
    Tracks expert consultation effectiveness.
    
    Monitors which experts are consulted, their confidence levels,
    and the impact on code quality outcomes.
    """

    def __init__(
        self,
        project_root: Path | None = None,
        outcome_tracker: OutcomeTracker | None = None,
    ):
        """
        Initialize expert performance tracker.

        Args:
            project_root: Project root directory
            outcome_tracker: OutcomeTracker instance
        """
        self.project_root = project_root or Path.cwd()
        self.learning_dir = self.project_root / ".tapps-agents" / "learning"
        self.performance_file = self.learning_dir / "expert_performance.jsonl"
        self.outcome_tracker = outcome_tracker or OutcomeTracker()

        # Ensure learning directory exists
        self.learning_dir.mkdir(parents=True, exist_ok=True)

    def track_consultation(
        self,
        expert_id: str,
        domain: str,
        confidence: float,
        query: str | None = None,
    ) -> None:
        """
        Track expert consultation.

        Args:
            expert_id: Expert identifier
            domain: Domain consulted
            confidence: Confidence score (0.0-1.0)
            query: Optional query text
        """
        consultation_data = {
            "expert_id": expert_id,
            "domain": domain,
            "confidence": confidence,
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            with open(self.performance_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(consultation_data, default=str) + "\n")
        except Exception as e:
            logger.error(f"Error tracking consultation: {e}")

    def calculate_performance(
        self, expert_id: str, days: int = 30
    ) -> ExpertPerformance | None:
        """
        Calculate performance metrics for an expert.

        Args:
            expert_id: Expert identifier
            days: Number of days to analyze

        Returns:
            ExpertPerformance object or None if insufficient data
        """
        # Load consultations
        consultations = self._load_consultations(expert_id, days)

        if not consultations:
            return None

        # Load outcomes for this expert
        outcomes = self.outcome_tracker.load_outcomes()
        expert_outcomes = [
            o
            for o in outcomes
            if expert_id in o.expert_consultations
        ]

        # Calculate metrics
        avg_confidence = sum(c["confidence"] for c in consultations) / len(consultations)

        # Calculate first-pass success rate
        first_pass_successes = sum(
            1 for o in expert_outcomes if o.first_pass_success
        )
        first_pass_success_rate = (
            first_pass_successes / len(expert_outcomes)
            if expert_outcomes
            else 0.0
        )

        # Calculate code quality improvement
        quality_improvements = []
        for outcome in expert_outcomes:
            if outcome.initial_scores and outcome.final_scores:
                initial_overall = self._calculate_overall_score(
                    outcome.initial_scores
                )
                final_overall = self._calculate_overall_score(outcome.final_scores)
                improvement = final_overall - initial_overall
                quality_improvements.append(improvement)

        code_quality_improvement = (
            sum(quality_improvements) / len(quality_improvements)
            if quality_improvements
            else 0.0
        )

        # Get domain coverage
        domains = list(set(c["domain"] for c in consultations))

        # Identify weaknesses
        weaknesses = self._identify_weaknesses(
            avg_confidence, first_pass_success_rate, code_quality_improvement
        )

        return ExpertPerformance(
            expert_id=expert_id,
            consultations=len(consultations),
            avg_confidence=avg_confidence,
            first_pass_success_rate=first_pass_success_rate,
            code_quality_improvement=code_quality_improvement,
            domain_coverage=domains,
            weaknesses=weaknesses,
        )

    def get_all_performance(
        self, days: int = 30
    ) -> dict[str, ExpertPerformance]:
        """
        Get performance for all experts.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary mapping expert_id to ExpertPerformance
        """
        # Get all unique expert IDs from consultations
        expert_ids = self._get_all_expert_ids(days)

        performance: dict[str, ExpertPerformance] = {}
        for expert_id in expert_ids:
            perf = self.calculate_performance(expert_id, days)
            if perf:
                performance[expert_id] = perf

        return performance

    def _load_consultations(
        self, expert_id: str, days: int
    ) -> list[dict[str, Any]]:
        """Load consultations for an expert within time window."""
        if not self.performance_file.exists():
            return []

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        consultations = []

        try:
            with open(self.performance_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    if data.get("expert_id") != expert_id:
                        continue
                    timestamp = datetime.fromisoformat(data.get("timestamp", ""))
                    if timestamp >= cutoff_date:
                        consultations.append(data)
        except Exception as e:
            logger.error(f"Error loading consultations: {e}")

        return consultations

    def _get_all_expert_ids(self, days: int) -> set[str]:
        """Get all expert IDs from consultations."""
        if not self.performance_file.exists():
            return set()

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        expert_ids = set()

        try:
            with open(self.performance_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    timestamp = datetime.fromisoformat(data.get("timestamp", ""))
                    if timestamp >= cutoff_date:
                        expert_ids.add(data.get("expert_id"))
        except Exception:
            pass

        return expert_ids

    def _calculate_overall_score(self, scores: dict[str, float]) -> float:
        """Calculate overall quality score from individual scores."""
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
                score = scores[metric]
                if score <= 10.0:
                    score = score * 10.0
                total += score * weight

        return total

    def _identify_weaknesses(
        self,
        avg_confidence: float,
        first_pass_success_rate: float,
        code_quality_improvement: float,
    ) -> list[str]:
        """Identify expert weaknesses based on metrics."""
        weaknesses = []

        if avg_confidence < 0.6:
            weaknesses.append("Low average confidence in consultations")

        if first_pass_success_rate < 0.5:
            weaknesses.append("Low first-pass success rate")

        if code_quality_improvement < 0:
            weaknesses.append("Negative code quality improvement")

        if avg_confidence < 0.7 and first_pass_success_rate < 0.6:
            weaknesses.append("Knowledge base may need updates")

        return weaknesses
