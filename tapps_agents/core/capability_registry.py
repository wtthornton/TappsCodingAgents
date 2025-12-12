"""
Agent Capability Registry

Tracks agent capabilities and their performance metrics for self-improvement.
"""

import gzip
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .hardware_profiler import HardwareProfile, HardwareProfiler

logger = logging.getLogger(__name__)


class LearningIntensity(Enum):
    """Learning intensity levels based on hardware."""

    LOW = "low"  # Minimal learning, essential patterns only
    MEDIUM = "medium"  # Balanced learning
    HIGH = "high"  # Aggressive learning


@dataclass
class RefinementRecord:
    """Record of a capability refinement."""

    timestamp: datetime
    improvement_type: str  # "prompt_optimization", "pattern_learning", "feedback_loop"
    before_metric: dict[str, Any]  # Snapshot of metrics before
    after_metric: dict[str, Any]  # Snapshot of metrics after
    improvement_percent: float
    learned_patterns: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RefinementRecord:
        """Create from dictionary."""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class CapabilityMetric:
    """Tracks performance metrics for a capability."""

    capability_id: str
    agent_id: str
    success_rate: float  # 0.0 to 1.0
    average_duration: float  # seconds
    quality_score: float  # 0.0 to 1.0 (from code scoring system)
    usage_count: int
    last_improved: datetime | None = None
    refinement_history: list[RefinementRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        if self.last_improved:
            data["last_improved"] = self.last_improved.isoformat()
        else:
            data["last_improved"] = None
        data["refinement_history"] = [r.to_dict() for r in self.refinement_history]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityMetric:
        """Create from dictionary."""
        data = data.copy()
        if data.get("last_improved"):
            data["last_improved"] = datetime.fromisoformat(data["last_improved"])
        else:
            data["last_improved"] = None
        data["refinement_history"] = [
            RefinementRecord.from_dict(r) for r in data.get("refinement_history", [])
        ]
        return cls(**data)

    def update_metrics(
        self, success: bool, duration: float, quality_score: float | None = None
    ):
        """
        Update metrics with new task result.

        Args:
            success: Whether task succeeded
            duration: Task duration in seconds
            quality_score: Optional quality score (0.0 to 1.0)
        """
        # Update success rate (exponential moving average)
        alpha = 0.1  # Smoothing factor
        self.success_rate = (
            alpha * (1.0 if success else 0.0) + (1 - alpha) * self.success_rate
        )

        # Update average duration (exponential moving average)
        self.average_duration = alpha * duration + (1 - alpha) * self.average_duration

        # Update quality score if provided
        if quality_score is not None:
            self.quality_score = (
                alpha * quality_score + (1 - alpha) * self.quality_score
            )

        # Increment usage count
        self.usage_count += 1

    def record_refinement(
        self,
        improvement_type: str,
        improvement_percent: float,
        learned_patterns: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Record a refinement to the capability.

        Args:
            improvement_type: Type of improvement
            improvement_percent: Percentage improvement
            learned_patterns: Optional learned patterns
            metadata: Optional metadata
        """
        before_metric = {
            "success_rate": self.success_rate,
            "average_duration": self.average_duration,
            "quality_score": self.quality_score,
            "usage_count": self.usage_count,
        }

        # Create refinement record
        refinement = RefinementRecord(
            timestamp=datetime.utcnow(),
            improvement_type=improvement_type,
            before_metric=before_metric,
            after_metric=before_metric.copy(),  # Will be updated after refinement
            improvement_percent=improvement_percent,
            learned_patterns=learned_patterns or [],
            metadata=metadata or {},
        )

        self.refinement_history.append(refinement)
        self.last_improved = datetime.utcnow()

        logger.info(
            f"Recorded refinement for {self.capability_id}: "
            f"{improvement_type} ({improvement_percent:.1f}% improvement)"
        )


class CapabilityRegistry:
    """
    Central registry for agent capabilities and their performance metrics.

    Follows Hexagonal Architecture pattern (Ports and Adapters).
    """

    def __init__(
        self,
        storage_dir: Path | None = None,
        hardware_profile: HardwareProfile | None = None,
    ):
        """
        Initialize capability registry.

        Args:
            storage_dir: Directory for metric storage (default: .tapps-agents/capabilities)
            hardware_profile: Hardware profile (auto-detected if None)
        """
        if storage_dir is None:
            storage_dir = Path(".tapps-agents/capabilities")

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Detect hardware profile if not provided
        if hardware_profile is None:
            profiler = HardwareProfiler()
            hardware_profile = profiler.detect_profile()

        self.hardware_profile = hardware_profile
        self.compression_enabled = hardware_profile == HardwareProfile.NUC
        self.metrics_file = self.storage_dir / "capabilities.json"
        if self.compression_enabled:
            self.metrics_file = self.storage_dir / "capabilities.json.gz"

        # In-memory registry
        self.metrics: dict[str, CapabilityMetric] = {}
        self._load_metrics()

    def _load_metrics(self):
        """Load metrics from storage."""
        if not self.metrics_file.exists():
            return

        try:
            if self.compression_enabled:
                with gzip.open(self.metrics_file, "rt", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                with open(self.metrics_file, encoding="utf-8") as f:
                    data = json.load(f)

            for metric_data in data.get("metrics", []):
                metric = CapabilityMetric.from_dict(metric_data)
                self.metrics[metric.capability_id] = metric

            logger.info(f"Loaded {len(self.metrics)} capability metrics")
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")

    def _save_metrics(self):
        """Save metrics to storage."""
        try:
            data = {
                "version": "1.0",
                "hardware_profile": self.hardware_profile.value,
                "metrics": [m.to_dict() for m in self.metrics.values()],
            }

            json_str = json.dumps(data, indent=2, default=str)

            if self.compression_enabled:
                with gzip.open(self.metrics_file, "wt", encoding="utf-8") as f:
                    f.write(json_str)
            else:
                with open(self.metrics_file, "w", encoding="utf-8") as f:
                    f.write(json_str)

            logger.debug(f"Saved {len(self.metrics)} capability metrics")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def register_capability(
        self, capability_id: str, agent_id: str, initial_quality: float = 0.5
    ) -> CapabilityMetric:
        """
        Register a new capability.

        Args:
            capability_id: Unique capability identifier
            agent_id: Agent identifier
            initial_quality: Initial quality score

        Returns:
            CapabilityMetric instance
        """
        if capability_id not in self.metrics:
            self.metrics[capability_id] = CapabilityMetric(
                capability_id=capability_id,
                agent_id=agent_id,
                success_rate=0.5,  # Initial neutral value
                average_duration=0.0,
                quality_score=initial_quality,
                usage_count=0,
            )
            self._save_metrics()
            logger.info(f"Registered capability: {capability_id} for agent {agent_id}")

        return self.metrics[capability_id]

    def get_capability(self, capability_id: str) -> CapabilityMetric | None:
        """
        Get capability metric.

        Args:
            capability_id: Capability identifier

        Returns:
            CapabilityMetric if found, None otherwise
        """
        return self.metrics.get(capability_id)

    def get_agent_capabilities(self, agent_id: str) -> list[CapabilityMetric]:
        """
        Get all capabilities for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of capability metrics
        """
        return [m for m in self.metrics.values() if m.agent_id == agent_id]

    def update_capability_metrics(
        self,
        capability_id: str,
        success: bool,
        duration: float,
        quality_score: float | None = None,
    ):
        """
        Update capability metrics after task execution.

        Args:
            capability_id: Capability identifier
            success: Whether task succeeded
            duration: Task duration in seconds
            quality_score: Optional quality score
        """
        if capability_id not in self.metrics:
            logger.warning(
                f"Capability {capability_id} not registered, creating default"
            )
            self.register_capability(
                capability_id, "unknown", initial_quality=quality_score or 0.5
            )

        metric = self.metrics[capability_id]
        metric.update_metrics(success, duration, quality_score)
        self._save_metrics()

    def record_refinement(
        self,
        capability_id: str,
        improvement_type: str,
        improvement_percent: float,
        learned_patterns: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Record a capability refinement.

        Args:
            capability_id: Capability identifier
            improvement_type: Type of improvement
            improvement_percent: Percentage improvement
            learned_patterns: Optional learned patterns
            metadata: Optional metadata
        """
        if capability_id not in self.metrics:
            logger.warning(f"Capability {capability_id} not found for refinement")
            return

        metric = self.metrics[capability_id]
        metric.record_refinement(
            improvement_type=improvement_type,
            improvement_percent=improvement_percent,
            learned_patterns=learned_patterns,
            metadata=metadata,
        )
        self._save_metrics()

    def get_learning_intensity(self) -> LearningIntensity:
        """
        Get learning intensity based on hardware profile.

        Returns:
            LearningIntensity level
        """
        if self.hardware_profile == HardwareProfile.NUC:
            return LearningIntensity.LOW
        elif self.hardware_profile == HardwareProfile.DEVELOPMENT:
            return LearningIntensity.MEDIUM
        else:
            return LearningIntensity.HIGH

    def get_top_capabilities(
        self,
        agent_id: str | None = None,
        limit: int = 10,
        sort_by: str = "quality_score",
    ) -> list[CapabilityMetric]:
        """
        Get top capabilities by metric.

        Args:
            agent_id: Optional agent filter
            limit: Maximum results
            sort_by: Sort field ("quality_score", "success_rate", "usage_count")

        Returns:
            List of top capability metrics
        """
        candidates = list(self.metrics.values())

        if agent_id:
            candidates = [m for m in candidates if m.agent_id == agent_id]

        # Sort by specified field
        if sort_by == "quality_score":
            candidates.sort(key=lambda m: m.quality_score, reverse=True)
        elif sort_by == "success_rate":
            candidates.sort(key=lambda m: m.success_rate, reverse=True)
        elif sort_by == "usage_count":
            candidates.sort(key=lambda m: m.usage_count, reverse=True)
        else:
            candidates.sort(key=lambda m: m.quality_score, reverse=True)

        return candidates[:limit]

    def get_improvement_candidates(
        self, min_usage: int = 10, max_quality: float = 0.7
    ) -> list[CapabilityMetric]:
        """
        Get capabilities that could benefit from improvement.

        Args:
            min_usage: Minimum usage count to consider
            max_quality: Maximum quality score (capabilities below this are candidates)

        Returns:
            List of capability metrics needing improvement
        """
        candidates = [
            m
            for m in self.metrics.values()
            if m.usage_count >= min_usage and m.quality_score < max_quality
        ]

        # Sort by quality (lowest first)
        candidates.sort(key=lambda m: m.quality_score)

        return candidates
