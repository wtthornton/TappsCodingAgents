"""
Learning Integration for Agents

Provides learning capabilities for agents to improve over time.
"""

import logging
from typing import Any

from .agent_learning import AgentLearner, CodePattern
from .capability_registry import CapabilityRegistry
from .hardware_profiler import HardwareProfiler

logger = logging.getLogger(__name__)


class LearningAwareMixin:
    """Mixin to add learning capabilities to agents."""

    def __init__(self, *args, **kwargs):
        """Initialize learning-aware mixin."""
        super().__init__(*args, **kwargs)

        # Initialize learning system
        hardware_profile = kwargs.get("hardware_profile")
        if hardware_profile is None:
            profiler = HardwareProfiler()
            hardware_profile = profiler.detect_profile()

        # Get expert_registry from agent if available (from ExpertSupportMixin),
        # or create a default one
        expert_registry = kwargs.get("expert_registry")
        if expert_registry is None and hasattr(self, "expert_registry"):
            expert_registry = self.expert_registry

        # If still None, create a default ExpertRegistry with built-in experts
        if expert_registry is None:
            try:
                from ..experts.expert_registry import ExpertRegistry

                expert_registry = ExpertRegistry(domain_config=None, load_builtin=True)
                logger.info("Created default ExpertRegistry for LearningAwareMixin")
            except Exception as e:
                logger.error(f"Failed to create ExpertRegistry: {e}")
                raise ValueError(
                    "expert_registry is required for AgentLearner. "
                    "Either provide it in kwargs or ensure the agent has ExpertSupportMixin initialized."
                ) from e

        self.capability_registry = CapabilityRegistry(hardware_profile=hardware_profile)
        self.agent_learner = AgentLearner(
            capability_registry=self.capability_registry,
            expert_registry=expert_registry,
            hardware_profile=hardware_profile,
        )
        self.learning_enabled = True

    def enable_learning(self, enabled: bool = True):
        """
        Enable or disable learning.

        Args:
            enabled: Whether to enable learning
        """
        self.learning_enabled = enabled

    def register_capability(self, capability_id: str, initial_quality: float = 0.5):
        """
        Register a capability for this agent.

        Args:
            capability_id: Capability identifier
            initial_quality: Initial quality score
        """
        if not self.learning_enabled:
            return

        self.capability_registry.register_capability(
            capability_id=capability_id,
            agent_id=self.agent_id,
            initial_quality=initial_quality,
        )

    async def learn_from_task(
        self,
        capability_id: str,
        task_id: str,
        code: str | None = None,
        quality_scores: dict[str, float] | None = None,
        success: bool = True,
        duration: float = 0.0,
    ) -> dict[str, Any]:
        """
        Learn from a completed task.

        Args:
            capability_id: Capability identifier
            task_id: Task identifier
            code: Optional source code
            quality_scores: Optional code scoring results
            success: Whether task succeeded
            duration: Task duration

        Returns:
            Learning results
        """
        if not self.learning_enabled:
            return {}

        return await self.agent_learner.learn_from_task(
            capability_id=capability_id,
            task_id=task_id,
            code=code,
            quality_scores=quality_scores,
            success=success,
            duration=duration,
        )

    def get_learned_patterns(
        self, context: str, pattern_type: str | None = None, limit: int = 5
    ) -> list[CodePattern]:
        """
        Get learned patterns for a context.

        Args:
            context: Context string
            pattern_type: Optional pattern type filter
            limit: Maximum results

        Returns:
            List of relevant patterns
        """
        if not self.learning_enabled:
            return []

        return self.agent_learner.get_learned_patterns(
            context=context, pattern_type=pattern_type, limit=limit
        )

    def optimize_prompt(self, base_prompt: str, context: str | None = None) -> str:
        """
        Get optimized prompt.

        Args:
            base_prompt: Base prompt
            context: Optional context

        Returns:
            Optimized prompt
        """
        if not self.learning_enabled:
            return base_prompt

        return self.agent_learner.optimize_prompt(base_prompt, context)

    def get_capability_metrics(self, capability_id: str) -> dict[str, Any] | None:
        """
        Get capability metrics.

        Args:
            capability_id: Capability identifier

        Returns:
            Capability metrics if found, None otherwise
        """
        if not self.learning_enabled:
            return None

        metric = self.capability_registry.get_capability(capability_id)
        if not metric:
            return None

        return {
            "capability_id": metric.capability_id,
            "agent_id": metric.agent_id,
            "success_rate": metric.success_rate,
            "average_duration": metric.average_duration,
            "quality_score": metric.quality_score,
            "usage_count": metric.usage_count,
            "last_improved": (
                metric.last_improved.isoformat() if metric.last_improved else None
            ),
            "refinement_count": len(metric.refinement_history),
        }

    def should_refine_capability(self, capability_id: str) -> bool:
        """
        Check if a capability should be refined.

        Args:
            capability_id: Capability identifier

        Returns:
            True if refinement is recommended
        """
        if not self.learning_enabled:
            return False

        return self.agent_learner.should_refine_capability(capability_id)

    def get_improvement_candidates(self, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get capabilities that could benefit from improvement.

        Args:
            limit: Maximum results

        Returns:
            List of capability metrics needing improvement
        """
        if not self.learning_enabled:
            return []

        candidates = self.capability_registry.get_improvement_candidates()

        return [
            {
                "capability_id": m.capability_id,
                "quality_score": m.quality_score,
                "usage_count": m.usage_count,
                "success_rate": m.success_rate,
            }
            for m in candidates[:limit]
        ]
