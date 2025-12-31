"""
Business Metrics Collection for Experts Feature

Collects and aggregates business metrics from technical metrics to demonstrate
the business value and ROI of expert consultations.

Phases:
- Phase 1: Aggregate existing technical metrics into business metrics
- Phase 2: Correlate expert consultations with code quality scores
- Phase 3: Calculate ROI and track user value
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .confidence_metrics import ConfidenceMetricsTracker, get_tracker
from .expert_engine import ExpertEngine, ExpertEngineMetrics

logger = logging.getLogger(__name__)


@dataclass
class AdoptionMetrics:
    """Adoption and usage metrics."""

    total_consultations: int = 0
    consultations_per_workflow: float = 0.0
    consultations_per_day: float = 0.0
    expert_usage_by_id: dict[str, int] = field(default_factory=dict)
    domain_usage: dict[str, int] = field(default_factory=dict)
    agent_usage: dict[str, int] = field(default_factory=dict)
    workflow_usage_percentage: float = 0.0


@dataclass
class CodeQualityImprovement:
    """Single code quality improvement record."""

    consultation_id: str
    timestamp: datetime
    before_score: float
    after_score: float
    improvement_percentage: float
    expert_id: str
    domain: str


@dataclass
class EffectivenessMetrics:
    """Effectiveness and impact metrics."""

    code_quality_improvements: list[CodeQualityImprovement] = field(
        default_factory=list
    )
    avg_quality_improvement: float = 0.0
    bug_prevention_rate: float = 0.0
    avg_time_savings_minutes: float = 15.0  # Default estimate
    total_bugs_prevented: int = 0


@dataclass
class QualityMetrics:
    """Quality and performance metrics."""

    avg_confidence: float = 0.0
    confidence_trend: list[float] = field(default_factory=list)
    avg_agreement_level: float = 0.0
    rag_quality_score: float = 0.0
    cache_hit_rate: float = 0.0
    avg_latency_ms: float = 0.0


@dataclass
class ROIMetrics:
    """ROI and business value metrics."""

    total_consultations: int = 0
    estimated_time_saved_hours: float = 0.0
    estimated_cost_per_consultation: float = 0.01  # Infrastructure cost
    estimated_value_per_consultation: float = 0.0  # Time saved value
    total_cost: float = 0.0
    total_value: float = 0.0
    roi_percentage: float = 0.0
    roi_per_consultation: float = 0.0


@dataclass
class OperationalMetrics:
    """System health and operational metrics."""

    cache_hit_rate: float = 0.0
    context7_hit_rate: float = 0.0
    local_kb_hit_rate: float = 0.0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    knowledge_base_size: int = 0


@dataclass
class BusinessMetricsData:
    """Complete business metrics snapshot."""

    timestamp: datetime
    adoption_metrics: AdoptionMetrics
    effectiveness_metrics: EffectivenessMetrics
    quality_metrics: QualityMetrics
    roi_metrics: ROIMetrics
    operational_metrics: OperationalMetrics

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime to ISO format string
        data["timestamp"] = self.timestamp.isoformat()
        # Convert CodeQualityImprovement datetimes
        for improvement in data["effectiveness_metrics"]["code_quality_improvements"]:
            if isinstance(improvement.get("timestamp"), datetime):
                improvement["timestamp"] = improvement["timestamp"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BusinessMetricsData:
        """Create from dictionary (from JSON)."""
        # Convert ISO format string back to datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Convert CodeQualityImprovement timestamps
        for improvement in data.get("effectiveness_metrics", {}).get(
            "code_quality_improvements", []
        ):
            if isinstance(improvement.get("timestamp"), str):
                improvement["timestamp"] = datetime.fromisoformat(
                    improvement["timestamp"]
                )

        return cls(**data)


class MetricsStorage:
    """File-based storage for business metrics."""

    def __init__(self, storage_path: Path | None = None):
        """
        Initialize metrics storage.

        Args:
            storage_path: Path to metrics directory (default: .tapps-agents/metrics)
        """
        if storage_path is None:
            storage_path = Path(".tapps-agents") / "metrics"
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.current_metrics_file = self.storage_path / "business_metrics.json"
        self.history_file = self.storage_path / "business_metrics_history.json"
        self.correlations_file = self.storage_path / "correlations.json"

    def save_metrics(self, metrics: BusinessMetricsData) -> None:
        """Save metrics to JSON file."""
        try:
            # Save current snapshot
            with open(self.current_metrics_file, "w", encoding="utf-8") as f:
                json.dump(metrics.to_dict(), f, indent=2)

            # Append to history
            history = self._load_history()
            history.append(metrics.to_dict())
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)

            logger.debug(f"Saved business metrics to {self.current_metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save business metrics: {e}", exc_info=True)

    def load_current_metrics(self) -> BusinessMetricsData | None:
        """Load current metrics snapshot."""
        if not self.current_metrics_file.exists():
            return None

        try:
            with open(self.current_metrics_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return BusinessMetricsData.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load current metrics: {e}", exc_info=True)
            return None

    def load_historical_metrics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[BusinessMetricsData]:
        """Load historical metrics for date range."""
        history = self._load_history()
        metrics_list = []

        for entry in history:
            try:
                metrics = BusinessMetricsData.from_dict(entry)
                timestamp = metrics.timestamp

                # Filter by date range
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue

                metrics_list.append(metrics)
            except Exception as e:
                logger.warning(f"Failed to parse historical metric entry: {e}")
                continue

        return metrics_list

    def save_correlation(
        self, consultation_id: str, before_score: float, after_score: float
    ) -> None:
        """Save code quality correlation data."""
        correlations = self._load_correlations()
        correlations[consultation_id] = {
            "timestamp": datetime.now().isoformat(),
            "before_score": before_score,
            "after_score": after_score,
            "improvement": after_score - before_score,
        }

        try:
            with open(self.correlations_file, "w", encoding="utf-8") as f:
                json.dump(correlations, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save correlation: {e}", exc_info=True)

    def _load_history(self) -> list[dict[str, Any]]:
        """Load history file."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _load_correlations(self) -> dict[str, Any]:
        """Load correlations file."""
        if not self.correlations_file.exists():
            return {}
        try:
            with open(self.correlations_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


class BusinessMetricsCollector:
    """Collects and aggregates business metrics from technical metrics."""

    def __init__(
        self,
        expert_engine: ExpertEngine | None = None,
        confidence_tracker: ConfidenceMetricsTracker | None = None,
        storage_path: Path | None = None,
        time_savings_per_consultation_minutes: float = 15.0,
        cost_per_consultation: float = 0.01,
    ):
        """
        Initialize business metrics collector.

        Args:
            expert_engine: ExpertEngine instance (optional)
            confidence_tracker: ConfidenceMetricsTracker instance (optional)
            storage_path: Path to metrics storage directory
            time_savings_per_consultation_minutes: Estimated time saved per consultation
            cost_per_consultation: Estimated infrastructure cost per consultation
        """
        self.expert_engine = expert_engine
        self.confidence_tracker = confidence_tracker or get_tracker()
        self.storage = MetricsStorage(storage_path)
        self.time_savings_per_consultation_minutes = time_savings_per_consultation_minutes
        self.cost_per_consultation = cost_per_consultation

    async def collect_metrics(self) -> BusinessMetricsData:
        """Collect current business metrics from all sources."""
        # Aggregate adoption metrics
        adoption = self.aggregate_adoption_metrics()

        # Calculate effectiveness metrics
        effectiveness = self.calculate_effectiveness_metrics()

        # Aggregate quality metrics
        quality = self.aggregate_quality_metrics()

        # Calculate ROI metrics
        roi = self.calculate_roi_metrics(adoption.total_consultations)

        # Aggregate operational metrics
        operational = self.aggregate_operational_metrics()

        metrics = BusinessMetricsData(
            timestamp=datetime.now(),
            adoption_metrics=adoption,
            effectiveness_metrics=effectiveness,
            quality_metrics=quality,
            roi_metrics=roi,
            operational_metrics=operational,
        )

        # Save metrics
        self.storage.save_metrics(metrics)

        return metrics

    def aggregate_adoption_metrics(self) -> AdoptionMetrics:
        """Aggregate adoption metrics (usage, frequency, popularity)."""
        adoption = AdoptionMetrics()

        # Get metrics from confidence tracker
        if self.confidence_tracker:
            metrics = self.confidence_tracker.get_metrics()
            adoption.total_consultations = len(metrics)

            # Count by expert, domain, agent
            for metric in metrics:
                # Expert usage (from primary_expert or domain)
                expert_id = getattr(metric, "primary_expert", None) or metric.domain
                adoption.expert_usage_by_id[expert_id] = (
                    adoption.expert_usage_by_id.get(expert_id, 0) + 1
                )

                # Domain usage
                adoption.domain_usage[metric.domain] = (
                    adoption.domain_usage.get(metric.domain, 0) + 1
                )

                # Agent usage
                adoption.agent_usage[metric.agent_id] = (
                    adoption.agent_usage.get(metric.agent_id, 0) + 1
                )

        # Get metrics from expert engine
        if self.expert_engine:
            engine_metrics = self.expert_engine.get_metrics()
            adoption.total_consultations = max(
                adoption.total_consultations, engine_metrics.expert_consultations
            )

        # Calculate per-day and per-workflow (estimates)
        if adoption.total_consultations > 0:
            # Estimate: assume 1 consultation per workflow on average
            adoption.consultations_per_workflow = 1.0
            # Estimate: assume 5 consultations per day on average
            adoption.consultations_per_day = min(
                adoption.total_consultations / 30.0, 5.0
            )
            # Estimate: 50% of workflows use experts
            adoption.workflow_usage_percentage = 50.0

        return adoption

    def calculate_effectiveness_metrics(self) -> EffectivenessMetrics:
        """Calculate effectiveness metrics (quality improvements, bug prevention)."""
        effectiveness = EffectivenessMetrics()

        # Load correlation data
        correlations = self.storage._load_correlations()

        # Process correlations into improvements
        for consultation_id, correlation_data in correlations.items():
            improvement = CodeQualityImprovement(
                consultation_id=consultation_id,
                timestamp=datetime.fromisoformat(correlation_data["timestamp"]),
                before_score=correlation_data["before_score"],
                after_score=correlation_data["after_score"],
                improvement_percentage=(
                    (correlation_data["after_score"] - correlation_data["before_score"])
                    / correlation_data["before_score"]
                    * 100
                    if correlation_data["before_score"] > 0
                    else 0.0
                ),
                expert_id="unknown",  # Not stored in correlation
                domain="unknown",  # Not stored in correlation
            )
            effectiveness.code_quality_improvements.append(improvement)

        # Calculate averages
        if effectiveness.code_quality_improvements:
            effectiveness.avg_quality_improvement = sum(
                imp.improvement_percentage
                for imp in effectiveness.code_quality_improvements
            ) / len(effectiveness.code_quality_improvements)

        # Set default time savings
        effectiveness.avg_time_savings_minutes = (
            self.time_savings_per_consultation_minutes
        )

        # Estimate bug prevention (10% of consultations prevent bugs)
        effectiveness.bug_prevention_rate = 0.1
        if self.confidence_tracker:
            metrics = self.confidence_tracker.get_metrics()
            effectiveness.total_bugs_prevented = int(len(metrics) * 0.1)

        return effectiveness

    def aggregate_quality_metrics(self) -> QualityMetrics:
        """Aggregate quality metrics (confidence, agreement, RAG quality)."""
        quality = QualityMetrics()

        if self.confidence_tracker:
            metrics = self.confidence_tracker.get_metrics()

            if metrics:
                # Calculate average confidence
                confidences = [m.confidence for m in metrics]
                quality.avg_confidence = sum(confidences) / len(confidences)

                # Get confidence trend (last 30 days)
                thirty_days_ago = datetime.now() - timedelta(days=30)
                recent_metrics = [
                    m
                    for m in metrics
                    if hasattr(m, "timestamp")
                    and m.timestamp >= thirty_days_ago
                ]
                if recent_metrics:
                    quality.confidence_trend = [
                        m.confidence for m in sorted(recent_metrics, key=lambda x: x.timestamp)
                    ][-30:]  # Last 30

                # Calculate average agreement level
                agreement_levels = [
                    m.agreement_level
                    for m in metrics
                    if hasattr(m, "agreement_level")
                ]
                if agreement_levels:
                    quality.avg_agreement_level = sum(agreement_levels) / len(
                        agreement_levels
                    )

        # Get operational metrics for RAG quality and cache hit rate
        if self.expert_engine:
            engine_metrics = self.expert_engine.get_metrics()
            quality.cache_hit_rate = engine_metrics.cache_hit_rate
            quality.rag_quality_score = (
                sum(engine_metrics.retrieval_quality_scores)
                / len(engine_metrics.retrieval_quality_scores)
                if engine_metrics.retrieval_quality_scores
                else 0.0
            )

        return quality

    def calculate_roi_metrics(self, total_consultations: int) -> ROIMetrics:
        """Calculate ROI metrics (time savings, costs, ROI)."""
        roi = ROIMetrics()

        roi.total_consultations = total_consultations
        roi.estimated_cost_per_consultation = self.cost_per_consultation
        roi.estimated_value_per_consultation = (
            self.time_savings_per_consultation_minutes / 60.0
        )  # Convert to hours

        # Calculate totals
        roi.total_cost = roi.total_consultations * roi.estimated_cost_per_consultation
        roi.total_value = (
            roi.total_consultations * roi.estimated_value_per_consultation
        )

        # Calculate ROI
        if roi.total_cost > 0:
            roi.roi_percentage = ((roi.total_value - roi.total_cost) / roi.total_cost) * 100
        else:
            roi.roi_percentage = 0.0

        roi.roi_per_consultation = (
            roi.estimated_value_per_consultation - roi.estimated_cost_per_consultation
        )

        roi.estimated_time_saved_hours = roi.total_value

        return roi

    def aggregate_operational_metrics(self) -> OperationalMetrics:
        """Aggregate operational metrics (system health)."""
        operational = OperationalMetrics()

        if self.expert_engine:
            engine_metrics = self.expert_engine.get_metrics()
            operational.cache_hit_rate = engine_metrics.cache_hit_rate
            operational.context7_hit_rate = engine_metrics.context7_hit_rate
            operational.local_kb_hit_rate = engine_metrics.local_kb_hit_rate

        return operational

    def record_code_quality_correlation(
        self,
        consultation_id: str,
        before_score: float,
        after_score: float,
        expert_id: str = "unknown",
        domain: str = "unknown",
    ) -> None:
        """
        Record code quality correlation (Phase 2).

        Args:
            consultation_id: Unique ID for the consultation
            before_score: Code quality score before expert consultation
            after_score: Code quality score after expert consultation
            expert_id: Expert that was consulted
            domain: Domain of the consultation
        """
        self.storage.save_correlation(consultation_id, before_score, after_score)

        # Also create improvement record
        improvement = CodeQualityImprovement(
            consultation_id=consultation_id,
            timestamp=datetime.now(),
            before_score=before_score,
            after_score=after_score,
            improvement_percentage=(
                (after_score - before_score) / before_score * 100
                if before_score > 0
                else 0.0
            ),
            expert_id=expert_id,
            domain=domain,
        )

        # Load current metrics and add improvement
        current = self.storage.load_current_metrics()
        if current:
            current.effectiveness_metrics.code_quality_improvements.append(
                improvement
            )
            self.storage.save_metrics(current)


def get_business_metrics_collector(
    expert_engine: ExpertEngine | None = None,
    storage_path: Path | None = None,
) -> BusinessMetricsCollector:
    """
    Factory function to get or create BusinessMetricsCollector.

    Args:
        expert_engine: Optional ExpertEngine instance
        storage_path: Optional storage path

    Returns:
        BusinessMetricsCollector instance
    """
    return BusinessMetricsCollector(
        expert_engine=expert_engine,
        confidence_tracker=get_tracker(),
        storage_path=storage_path,
    )
