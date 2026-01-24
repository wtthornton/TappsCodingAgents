"""
Adaptive Scorer Integration

Integrates adaptive scoring into reviewer agent with outcome tracking.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from ...core.adaptive_scoring import AdaptiveScoringEngine
from ...core.config import ScoringWeightsConfig
from ...core.outcome_tracker import OutcomeTracker

logger = logging.getLogger(__name__)


class AdaptiveScorerWrapper:
    """
    Wrapper that provides adaptive weights to CodeScorer.
    
    Loads adaptive weights from outcome tracker and applies them
    to scoring operations.
    """

    def __init__(
        self,
        outcome_tracker: OutcomeTracker | None = None,
        adaptive_engine: AdaptiveScoringEngine | None = None,
        enabled: bool = True,
    ):
        """
        Initialize adaptive scorer wrapper.

        Args:
            outcome_tracker: OutcomeTracker instance
            adaptive_engine: AdaptiveScoringEngine instance
            enabled: Whether adaptive scoring is enabled
        """
        self.outcome_tracker = outcome_tracker or OutcomeTracker()
        self.adaptive_engine = adaptive_engine or AdaptiveScoringEngine(
            outcome_tracker=self.outcome_tracker
        )
        self.enabled = enabled
        self._cached_weights: dict[str, float] | None = None

    async def get_adaptive_weights(
        self, force_reload: bool = False
    ) -> dict[str, float] | None:
        """
        Get adaptive weights for scoring.

        Args:
            force_reload: Force recalculation of weights

        Returns:
            Dictionary of weights or None if adaptive scoring disabled
        """
        if not self.enabled:
            return None

        # Use cached weights if available and not forcing reload
        if not force_reload and self._cached_weights:
            return self._cached_weights

        try:
            # Get adjusted weights from adaptive engine
            adjusted_weights = await self.adaptive_engine.adjust_weights()

            # Convert to ScoringWeightsConfig format
            self._cached_weights = adjusted_weights
            return adjusted_weights
        except Exception as e:
            logger.warning(f"Error getting adaptive weights: {e}")
            return None

    def get_weights_config(
        self, default_weights: ScoringWeightsConfig | None = None
    ) -> ScoringWeightsConfig:
        """
        Get ScoringWeightsConfig with adaptive weights applied.

        Args:
            default_weights: Default weights if adaptive not available

        Returns:
            ScoringWeightsConfig with adaptive weights
        """
        # Try to get adaptive weights (synchronous, uses cached)
        adaptive_weights = self._cached_weights

        if adaptive_weights and self.enabled:
            # Create config from adaptive weights
            return ScoringWeightsConfig(
                complexity=adaptive_weights.get("complexity", 0.18),
                security=adaptive_weights.get("security", 0.27),
                maintainability=adaptive_weights.get("maintainability", 0.24),
                test_coverage=adaptive_weights.get("test_coverage", 0.13),
                performance=adaptive_weights.get("performance", 0.08),
                structure=adaptive_weights.get("structure", 0.05),
                devex=adaptive_weights.get("devex", 0.05),
            )

        # Fall back to default weights
        return default_weights or ScoringWeightsConfig()

    async def track_outcome(
        self,
        workflow_id: str,
        file_path: Path,
        scores: dict[str, float],
        expert_consultations: list[str] | None = None,
        agent_id: str | None = None,
        prompt_hash: str | None = None,
    ) -> None:
        """
        Track initial scores for outcome tracking.

        Args:
            workflow_id: Workflow identifier
            file_path: Path to code file
            scores: Quality scores
            expert_consultations: List of expert IDs
            agent_id: Agent that generated code
            prompt_hash: Hash of original prompt
        """
        if not self.enabled:
            return

        try:
            self.outcome_tracker.track_initial_scores(
                workflow_id=workflow_id,
                file_path=file_path,
                scores=scores,
                expert_consultations=expert_consultations,
                agent_id=agent_id,
                prompt_hash=prompt_hash,
            )
        except Exception as e:
            logger.warning(f"Error tracking outcome: {e}")

    def hash_prompt(self, prompt: str) -> str:
        """Generate hash for prompt."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]
