"""
Confidence Metrics Tracking and Logging

Tracks confidence metrics for expert consultations to enable:
- Performance monitoring
- Quality analysis
- Confidence threshold tuning
- Expert effectiveness measurement
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ConfidenceMetric:
    """Single confidence metric record."""

    timestamp: datetime
    agent_id: str
    domain: str
    confidence: float
    threshold: float
    meets_threshold: bool
    agreement_level: float
    num_experts: int
    primary_expert: str
    query_preview: str  # First 100 chars of query
    expert_ids: list[str] = field(default_factory=list)
    selection_reason: str = "unknown"


class ConfidenceMetricsTracker:
    """
    Tracks confidence metrics for expert consultations.

    Provides:
    - In-memory metric storage
    - JSON file persistence
    - Query and analysis methods
    """

    def __init__(self, metrics_file: Path | None = None):
        """
        Initialize metrics tracker.

        Args:
            metrics_file: Optional path to JSON file for persistence
        """
        self.metrics: list[ConfidenceMetric] = []
        self.metrics_file = metrics_file or Path(
            ".tapps-agents/confidence_metrics.json"
        )
        self._load_metrics()

    def record(
        self,
        agent_id: str,
        domain: str,
        confidence: float,
        threshold: float,
        agreement_level: float,
        num_experts: int,
        primary_expert: str,
        query: str,
        expert_ids: list[str] | None = None,
        selection_reason: str = "unknown",
    ) -> None:
        """
        Record a confidence metric.

        Args:
            agent_id: Agent that made the consultation
            domain: Domain of the consultation
            confidence: Calculated confidence score
            threshold: Agent-specific threshold
            agreement_level: Agreement level between experts
            num_experts: Number of experts consulted
            primary_expert: Primary expert ID
            query: Consultation query
            expert_ids: Optional list of expert IDs consulted
            selection_reason: Why experts were selected (weight_matrix, domain_match_*, fallback_*)
        """
        metric = ConfidenceMetric(
            timestamp=datetime.now(),
            agent_id=agent_id,
            domain=domain,
            confidence=confidence,
            threshold=threshold,
            meets_threshold=confidence >= threshold,
            agreement_level=agreement_level,
            num_experts=num_experts,
            primary_expert=primary_expert,
            query_preview=query[:100],
            expert_ids=expert_ids or [],
            selection_reason=selection_reason,
        )

        self.metrics.append(metric)
        self._save_metrics()

    def get_metrics(
        self,
        agent_id: str | None = None,
        domain: str | None = None,
        min_confidence: float | None = None,
        max_confidence: float | None = None,
    ) -> list[ConfidenceMetric]:
        """
        Get metrics matching filters.

        Args:
            agent_id: Filter by agent ID
            domain: Filter by domain
            min_confidence: Minimum confidence
            max_confidence: Maximum confidence

        Returns:
            List of matching metrics
        """
        filtered = self.metrics

        if agent_id:
            filtered = [m for m in filtered if m.agent_id == agent_id]

        if domain:
            filtered = [m for m in filtered if m.domain == domain]

        if min_confidence is not None:
            filtered = [m for m in filtered if m.confidence >= min_confidence]

        if max_confidence is not None:
            filtered = [m for m in filtered if m.confidence <= max_confidence]

        return filtered

    def get_statistics(
        self, agent_id: str | None = None, domain: str | None = None
    ) -> dict[str, Any]:
        """
        Get statistics for metrics.

        Args:
            agent_id: Filter by agent ID
            domain: Filter by domain

        Returns:
            Dictionary with statistics
        """
        metrics = self.get_metrics(agent_id=agent_id, domain=domain)

        if not metrics:
            return {
                "count": 0,
                "avg_confidence": 0.0,
                "avg_agreement": 0.0,
                "threshold_meet_rate": 0.0,
            }

        confidences = [m.confidence for m in metrics]
        agreements = [m.agreement_level for m in metrics]
        meets_threshold = sum(1 for m in metrics if m.meets_threshold)

        return {
            "count": len(metrics),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "avg_agreement": sum(agreements) / len(agreements),
            "threshold_meet_rate": meets_threshold / len(metrics),
            "low_confidence_count": sum(1 for c in confidences if c < 0.5),
        }

    def _load_metrics(self) -> None:
        """Load metrics from file."""
        if not self.metrics_file.exists():
            return

        try:
            with open(self.metrics_file, encoding="utf-8") as f:
                data = json.load(f)

            self.metrics = [
                ConfidenceMetric(
                    timestamp=datetime.fromisoformat(m["timestamp"]),
                    agent_id=m["agent_id"],
                    domain=m["domain"],
                    confidence=m["confidence"],
                    threshold=m["threshold"],
                    meets_threshold=m["meets_threshold"],
                    agreement_level=m["agreement_level"],
                    num_experts=m["num_experts"],
                    primary_expert=m["primary_expert"],
                    query_preview=m["query_preview"],
                    expert_ids=m.get("expert_ids") or [],
                    selection_reason=m.get("selection_reason", "unknown"),
                )
                for m in data.get("metrics", [])
            ]
        except Exception:
            # If loading fails, start with empty metrics
            self.metrics = []

    def _save_metrics(self) -> None:
        """Save metrics to file."""
        try:
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "metrics": [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "agent_id": m.agent_id,
                        "domain": m.domain,
                        "confidence": m.confidence,
                        "threshold": m.threshold,
                        "meets_threshold": m.meets_threshold,
                        "agreement_level": m.agreement_level,
                        "num_experts": m.num_experts,
                        "primary_expert": m.primary_expert,
                        "query_preview": m.query_preview,
                        "expert_ids": m.expert_ids,
                        "selection_reason": m.selection_reason,
                    }
                    for m in self.metrics[-1000:]  # Keep last 1000 metrics
                ]
            }

            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            # Silently fail if saving fails
            return


# Global metrics tracker instance
_global_tracker: ConfidenceMetricsTracker | None = None


def get_tracker() -> ConfidenceMetricsTracker:
    """Get global confidence metrics tracker."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ConfidenceMetricsTracker()
    return _global_tracker
