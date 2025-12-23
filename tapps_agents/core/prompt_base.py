"""
Base classes for prompt optimization in Tier 1 Enhancement.

Provides abstract base classes for prompt optimizers and A/B testing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .evaluation_models import PromptVersion


@dataclass
class PromptVariation:
    """Represents a prompt variation for A/B testing."""

    id: str
    prompt_text: str
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Set default created_at if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class PromptOutcome:
    """Outcome metrics for a prompt variation."""

    variation_id: str
    usage_count: int
    success_count: int
    failure_count: int
    average_score: float | None = None
    metadata: dict[str, Any] | None = None

    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.usage_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "variation_id": self.variation_id,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "average_score": self.average_score,
            "success_rate": self.success_rate(),
            "metadata": self.metadata or {},
        }


class PromptVersionManager:
    """Manages version tracking for prompts."""

    def __init__(self, storage_path: str | None = None):
        """
        Initialize version manager.
        
        Args:
            storage_path: Optional path for storing version history
        """
        self.storage_path = storage_path
        self.versions: dict[str, list[PromptVersion]] = {}

    def add_version(self, prompt_type: str, version: PromptVersion) -> None:
        """Add a new prompt version."""
        if prompt_type not in self.versions:
            self.versions[prompt_type] = []
        self.versions[prompt_type].append(version)

    def get_latest_version(self, prompt_type: str) -> PromptVersion | None:
        """Get the latest version for a prompt type."""
        if prompt_type not in self.versions or not self.versions[prompt_type]:
            return None
        return max(
            self.versions[prompt_type], key=lambda v: v.created_at, default=None
        )

    def get_version_history(self, prompt_type: str) -> list[PromptVersion]:
        """Get version history for a prompt type."""
        return self.versions.get(prompt_type, [])

    def get_version_by_id(self, prompt_type: str, version_id: str) -> PromptVersion | None:
        """Get a specific version by ID."""
        for version in self.versions.get(prompt_type, []):
            if version.id == version_id:
                return version
        return None


class BasePromptOptimizer(ABC):
    """
    Abstract base class for prompt optimizers.
    
    Prompt optimizers refine prompts based on feedback and outcomes.
    """

    @abstractmethod
    def optimize(
        self, current_prompt: str, outcomes: list[PromptOutcome]
    ) -> str:
        """
        Optimize a prompt based on outcomes.
        
        Args:
            current_prompt: Current prompt text
            outcomes: List of outcomes from prompt variations
            
        Returns:
            Optimized prompt text
        """
        pass

    @abstractmethod
    def generate_variations(self, base_prompt: str, count: int = 3) -> list[PromptVariation]:
        """
        Generate variations of a prompt for A/B testing.
        
        Args:
            base_prompt: Base prompt to vary
            count: Number of variations to generate
            
        Returns:
            List of prompt variations
        """
        pass


class PromptABTester:
    """
    A/B testing framework for prompt variations.
    
    Tests multiple prompt variations and tracks outcomes.
    """

    def __init__(self):
        """Initialize A/B tester."""
        self.variations: dict[str, PromptVariation] = {}
        self.outcomes: dict[str, PromptOutcome] = {}

    def register_variation(self, variation: PromptVariation) -> None:
        """Register a prompt variation for testing."""
        self.variations[variation.id] = variation
        if variation.id not in self.outcomes:
            self.outcomes[variation.id] = PromptOutcome(
                variation_id=variation.id,
                usage_count=0,
                success_count=0,
                failure_count=0,
            )

    def record_outcome(
        self, variation_id: str, success: bool, score: float | None = None
    ) -> None:
        """
        Record an outcome for a prompt variation.
        
        Args:
            variation_id: ID of the variation
            success: Whether the outcome was successful
            score: Optional quality score
        """
        if variation_id not in self.outcomes:
            self.outcomes[variation_id] = PromptOutcome(
                variation_id=variation_id,
                usage_count=0,
                success_count=0,
                failure_count=0,
            )

        outcome = self.outcomes[variation_id]
        outcome.usage_count += 1
        if success:
            outcome.success_count += 1
        else:
            outcome.failure_count += 1

        # Update average score
        if score is not None:
            if outcome.average_score is None:
                outcome.average_score = score
            else:
                # Running average
                outcome.average_score = (
                    outcome.average_score * (outcome.usage_count - 1) + score
                ) / outcome.usage_count

    def get_best_variation(self) -> PromptVariation | None:
        """Get the variation with the best outcomes."""
        if not self.outcomes:
            return None

        best_id = max(
            self.outcomes.keys(),
            key=lambda vid: (
                self.outcomes[vid].success_rate(),
                self.outcomes[vid].average_score or 0.0,
            ),
        )
        return self.variations.get(best_id)

    def get_statistics(self) -> dict[str, Any]:
        """Get A/B test statistics."""
        return {
            "variations": len(self.variations),
            "outcomes": {
                vid: outcome.to_dict()
                for vid, outcome in self.outcomes.items()
            },
            "best_variation": (
                self.get_best_variation().id if self.get_best_variation() else None
            ),
        }

