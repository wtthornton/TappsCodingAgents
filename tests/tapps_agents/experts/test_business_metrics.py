"""
Tests for business_metrics.py
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.experts.business_metrics import (
    AdoptionMetrics,
    BusinessMetricsCollector,
    BusinessMetricsData,
    CodeQualityImprovement,
    EffectivenessMetrics,
    MetricsStorage,
    OperationalMetrics,
    QualityMetrics,
    ROIMetrics,
    get_business_metrics_collector,
)


class TestAdoptionMetrics:
    """Tests for AdoptionMetrics dataclass."""

    def test_adoption_metrics_defaults(self):
        """Test AdoptionMetrics with default values."""
        metrics = AdoptionMetrics()
        assert metrics.total_consultations == 0
        assert metrics.consultations_per_workflow == 0.0
        assert metrics.expert_usage_by_id == {}
        assert metrics.domain_usage == {}
        assert metrics.agent_usage == {}


class TestBusinessMetricsData:
    """Tests for BusinessMetricsData."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = BusinessMetricsData(
            timestamp=datetime.now(),
            adoption_metrics=AdoptionMetrics(),
            effectiveness_metrics=EffectivenessMetrics(),
            quality_metrics=QualityMetrics(),
            roi_metrics=ROIMetrics(),
            operational_metrics=OperationalMetrics(),
        )
        data = metrics.to_dict()
        assert isinstance(data, dict)
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)  # ISO format

    def test_from_dict(self):
        """Test creation from dictionary."""
        timestamp = datetime.now()
        data = {
            "timestamp": timestamp.isoformat(),
            "adoption_metrics": {
                "total_consultations": 10,
                "consultations_per_workflow": 1.0,
                "consultations_per_day": 5.0,
                "expert_usage_by_id": {},
                "domain_usage": {},
                "agent_usage": {},
                "workflow_usage_percentage": 50.0,
            },
            "effectiveness_metrics": {
                "code_quality_improvements": [],
                "avg_quality_improvement": 0.0,
                "bug_prevention_rate": 0.1,
                "avg_time_savings_minutes": 15.0,
                "total_bugs_prevented": 0,
            },
            "quality_metrics": {
                "avg_confidence": 0.8,
                "confidence_trend": [],
                "avg_agreement_level": 0.75,
                "rag_quality_score": 0.9,
                "cache_hit_rate": 0.85,
                "avg_latency_ms": 100.0,
            },
            "roi_metrics": {
                "total_consultations": 10,
                "estimated_time_saved_hours": 2.5,
                "estimated_cost_per_consultation": 0.01,
                "estimated_value_per_consultation": 0.25,
                "total_cost": 0.1,
                "total_value": 2.5,
                "roi_percentage": 2400.0,
                "roi_per_consultation": 0.24,
            },
            "operational_metrics": {
                "cache_hit_rate": 0.85,
                "context7_hit_rate": 0.9,
                "local_kb_hit_rate": 0.8,
                "avg_latency_ms": 100.0,
                "error_rate": 0.0,
                "knowledge_base_size": 100,
            },
        }
        metrics = BusinessMetricsData.from_dict(data)
        assert isinstance(metrics, BusinessMetricsData)
        assert metrics.adoption_metrics.total_consultations == 10


class TestMetricsStorage:
    """Tests for MetricsStorage."""

    def test_init(self, tmp_path):
        """Test MetricsStorage initialization."""
        storage = MetricsStorage(storage_path=tmp_path)
        assert storage.storage_path == tmp_path
        assert storage.current_metrics_file.exists() is False  # Created on first save

    def test_save_and_load_metrics(self, tmp_path):
        """Test saving and loading metrics."""
        storage = MetricsStorage(storage_path=tmp_path)
        metrics = BusinessMetricsData(
            timestamp=datetime.now(),
            adoption_metrics=AdoptionMetrics(total_consultations=5),
            effectiveness_metrics=EffectivenessMetrics(),
            quality_metrics=QualityMetrics(),
            roi_metrics=ROIMetrics(),
            operational_metrics=OperationalMetrics(),
        )

        storage.save_metrics(metrics)
        assert storage.current_metrics_file.exists()

        loaded = storage.load_current_metrics()
        assert loaded is not None
        assert loaded.adoption_metrics.total_consultations == 5

    def test_load_historical_metrics(self, tmp_path):
        """Test loading historical metrics with date range."""
        storage = MetricsStorage(storage_path=tmp_path)

        # Create metrics for different dates
        now = datetime.now()
        metrics1 = BusinessMetricsData(
            timestamp=now - timedelta(days=10),
            adoption_metrics=AdoptionMetrics(total_consultations=5),
            effectiveness_metrics=EffectivenessMetrics(),
            quality_metrics=QualityMetrics(),
            roi_metrics=ROIMetrics(),
            operational_metrics=OperationalMetrics(),
        )
        metrics2 = BusinessMetricsData(
            timestamp=now - timedelta(days=5),
            adoption_metrics=AdoptionMetrics(total_consultations=10),
            effectiveness_metrics=EffectivenessMetrics(),
            quality_metrics=QualityMetrics(),
            roi_metrics=ROIMetrics(),
            operational_metrics=OperationalMetrics(),
        )

        storage.save_metrics(metrics1)
        storage.save_metrics(metrics2)

        # Load with date range
        start_date = now - timedelta(days=7)
        end_date = now
        historical = storage.load_historical_metrics(start_date, end_date)

        # Should only get metrics2 (within range)
        assert len(historical) >= 1
        assert historical[-1].adoption_metrics.total_consultations == 10

    def test_save_correlation(self, tmp_path):
        """Test saving code quality correlation."""
        storage = MetricsStorage(storage_path=tmp_path)
        storage.save_correlation("consult-1", 70.0, 85.0)

        assert storage.correlations_file.exists()
        correlations = storage._load_correlations()
        assert "consult-1" in correlations
        assert correlations["consult-1"]["before_score"] == 70.0
        assert correlations["consult-1"]["after_score"] == 85.0


class TestBusinessMetricsCollector:
    """Tests for BusinessMetricsCollector."""

    @pytest.fixture
    def mock_expert_engine(self):
        """Create mock ExpertEngine."""
        engine = MagicMock()
        engine_metrics = MagicMock()
        engine_metrics.expert_consultations = 10
        engine_metrics.cache_hit_rate = 0.85
        engine_metrics.context7_hit_rate = 0.9
        engine_metrics.local_kb_hit_rate = 0.8
        engine_metrics.retrieval_quality_scores = [0.9, 0.85, 0.95]
        engine.get_metrics.return_value = engine_metrics
        return engine

    @pytest.fixture
    def mock_confidence_tracker(self):
        """Create mock ConfidenceMetricsTracker."""
        tracker = MagicMock()
        # Create mock metrics
        metric1 = MagicMock()
        metric1.confidence = 0.8
        metric1.agreement_level = 0.75
        metric1.domain = "security"
        metric1.agent_id = "architect"
        metric1.primary_expert = "expert-security"
        metric1.timestamp = datetime.now()

        metric2 = MagicMock()
        metric2.confidence = 0.85
        metric2.agreement_level = 0.8
        metric2.domain = "performance"
        metric2.agent_id = "implementer"
        metric2.primary_expert = "expert-performance"
        metric2.timestamp = datetime.now()

        tracker.get_metrics.return_value = [metric1, metric2]
        return tracker

    @pytest.mark.asyncio
    async def test_collect_metrics(self, tmp_path, mock_expert_engine, mock_confidence_tracker):
        """Test collecting metrics."""
        collector = BusinessMetricsCollector(
            expert_engine=mock_expert_engine,
            confidence_tracker=mock_confidence_tracker,
            storage_path=tmp_path,
        )

        metrics = await collector.collect_metrics()

        assert isinstance(metrics, BusinessMetricsData)
        assert metrics.adoption_metrics.total_consultations >= 2
        assert metrics.quality_metrics.avg_confidence > 0

    def test_aggregate_adoption_metrics(self, mock_confidence_tracker):
        """Test aggregating adoption metrics."""
        collector = BusinessMetricsCollector(confidence_tracker=mock_confidence_tracker)

        adoption = collector.aggregate_adoption_metrics()

        assert adoption.total_consultations >= 2
        assert "expert-security" in adoption.expert_usage_by_id
        assert "security" in adoption.domain_usage
        assert "architect" in adoption.agent_usage

    def test_calculate_roi_metrics(self):
        """Test calculating ROI metrics."""
        collector = BusinessMetricsCollector(
            time_savings_per_consultation_minutes=15.0,
            cost_per_consultation=0.01,
        )

        roi = collector.calculate_roi_metrics(total_consultations=10)

        assert roi.total_consultations == 10
        assert roi.total_cost == 0.1  # 10 * 0.01
        assert roi.total_value > 0
        assert roi.roi_percentage > 0

    def test_record_code_quality_correlation(self, tmp_path):
        """Test recording code quality correlation."""
        collector = BusinessMetricsCollector(storage_path=tmp_path)

        collector.record_code_quality_correlation(
            consultation_id="consult-1",
            before_score=70.0,
            after_score=85.0,
            expert_id="expert-security",
            domain="security",
        )

        # Check correlation was saved
        correlations = collector.storage._load_correlations()
        assert "consult-1" in correlations

        # Check improvement was added to metrics
        current = collector.storage.load_current_metrics()
        if current:
            improvements = current.effectiveness_metrics.code_quality_improvements
            assert len(improvements) > 0
            assert improvements[-1].consultation_id == "consult-1"


class TestFactoryFunction:
    """Tests for factory function."""

    def test_get_business_metrics_collector(self):
        """Test get_business_metrics_collector factory function."""
        collector = get_business_metrics_collector()
        assert isinstance(collector, BusinessMetricsCollector)
