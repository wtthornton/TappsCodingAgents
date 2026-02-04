"""
Tests for RAG Performance Metrics.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from tapps_agents.experts.rag_metrics import (
    RAGMetricsTracker,
    RAGPerformanceMetrics,
    RAGQueryMetrics,
    RAGQueryTimer,
    get_rag_metrics_tracker,
)

pytestmark = pytest.mark.unit


class TestRAGQueryMetrics:
    """Test RAG query metrics."""

    def test_query_metrics_creation(self):
        """Test creating query metrics."""
        metrics = RAGQueryMetrics(
            query="test query",
            expert_id="expert-1",
            domain="security",
            timestamp=datetime.now(),
            latency_ms=100.5,
            num_results=5,
            max_similarity=0.85,
            avg_similarity=0.75,
            backend_type="vector",
            cache_hit=False,
        )

        assert metrics.query == "test query"
        assert metrics.expert_id == "expert-1"
        assert metrics.latency_ms == 100.5
        assert metrics.num_results == 5
        assert metrics.max_similarity == 0.85


class TestRAGPerformanceMetrics:
    """Test RAG performance metrics aggregation."""

    def test_initial_state(self):
        """Test initial metrics state."""
        metrics = RAGPerformanceMetrics()

        assert metrics.total_queries == 0
        assert metrics.avg_latency_ms == 0.0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0

    def test_update_metrics(self):
        """Test updating metrics with query."""
        metrics = RAGPerformanceMetrics()

        query_metrics = RAGQueryMetrics(
            query="test",
            expert_id="expert-1",
            domain="security",
            timestamp=datetime.now(),
            latency_ms=100.0,
            num_results=5,
            max_similarity=0.8,
            avg_similarity=0.7,
            backend_type="vector",
            cache_hit=True,
        )

        metrics.update(query_metrics)

        assert metrics.total_queries == 1
        assert metrics.avg_latency_ms == 100.0
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 0
        assert metrics.queries_by_expert["expert-1"] == 1
        assert metrics.backend_usage["vector"] == 1

    def test_similarity_distribution(self):
        """Test similarity distribution tracking."""
        metrics = RAGPerformanceMetrics()

        # High similarity
        metrics.update(
            RAGQueryMetrics(
                query="test",
                expert_id="expert-1",
                domain="security",
                timestamp=datetime.now(),
                latency_ms=100.0,
                num_results=5,
                max_similarity=0.9,
                avg_similarity=0.85,
                backend_type="vector",
            )
        )

        # Medium similarity
        metrics.update(
            RAGQueryMetrics(
                query="test",
                expert_id="expert-2",
                domain="performance",
                timestamp=datetime.now(),
                latency_ms=100.0,
                num_results=5,
                max_similarity=0.7,
                avg_similarity=0.65,
                backend_type="vector",
            )
        )

        # Low similarity
        metrics.update(
            RAGQueryMetrics(
                query="test",
                expert_id="expert-3",
                domain="testing",
                timestamp=datetime.now(),
                latency_ms=100.0,
                num_results=5,
                max_similarity=0.5,
                avg_similarity=0.45,
                backend_type="simple",
            )
        )

        assert metrics.similarity_distribution["high"] == 1
        assert metrics.similarity_distribution["medium"] == 1
        assert metrics.similarity_distribution["low"] == 1

    def test_average_calculation(self):
        """Test running average calculations."""
        metrics = RAGPerformanceMetrics()

        # Add multiple queries with different results
        for i in range(5):
            metrics.update(
                RAGQueryMetrics(
                    query=f"test {i}",
                    expert_id="expert-1",
                    domain="security",
                    timestamp=datetime.now(),
                    latency_ms=100.0 + i * 10,
                    num_results=5 + i,
                    max_similarity=0.8 + i * 0.02,
                    avg_similarity=0.7 + i * 0.02,
                    backend_type="vector",
                )
            )

        assert metrics.total_queries == 5
        assert metrics.avg_latency_ms == 120.0  # (100+110+120+130+140)/5
        assert metrics.avg_results > 5.0
        assert metrics.avg_similarity > 0.7


class TestRAGMetricsTracker:
    """Test RAG metrics tracker."""

    @pytest.fixture
    def temp_metrics_file(self):
        """Create temporary metrics file."""
        temp_dir = Path(tempfile.mkdtemp())
        metrics_file = temp_dir / "rag_metrics.json"

        yield metrics_file

        import shutil

        shutil.rmtree(temp_dir)

    def test_tracker_creation(self, temp_metrics_file):
        """Test creating metrics tracker."""
        tracker = RAGMetricsTracker(temp_metrics_file)

        assert tracker.metrics_file == temp_metrics_file
        assert tracker.performance_metrics.total_queries == 0

    def test_record_query(self, temp_metrics_file):
        """Test recording a query."""
        tracker = RAGMetricsTracker(temp_metrics_file)

        tracker.record_query(
            query="test query",
            expert_id="expert-1",
            domain="security",
            num_results=5,
            max_similarity=0.8,
            avg_similarity=0.7,
            backend_type="vector",
            cache_hit=False,
            latency_ms=100.0,
        )

        assert tracker.performance_metrics.total_queries == 1
        assert tracker.performance_metrics.avg_latency_ms == 100.0
        assert len(tracker.query_history) == 1

    def test_get_metrics(self, temp_metrics_file):
        """Test getting metrics summary."""
        tracker = RAGMetricsTracker(temp_metrics_file)

        tracker.record_query(
            query="test",
            expert_id="expert-1",
            domain="security",
            num_results=5,
            max_similarity=0.8,
            avg_similarity=0.7,
            backend_type="vector",
            cache_hit=True,
            latency_ms=100.0,
        )

        metrics = tracker.get_metrics()

        assert metrics["total_queries"] == 1
        assert metrics["avg_latency_ms"] == 100.0
        assert metrics["cache_hit_rate"] == 1.0
        assert "backend_usage" in metrics
        assert "similarity_distribution" in metrics

    def test_get_recent_queries(self, temp_metrics_file):
        """Test getting recent queries."""
        tracker = RAGMetricsTracker(temp_metrics_file)

        # Add multiple queries
        for i in range(5):
            tracker.record_query(
                query=f"query {i}",
                expert_id="expert-1",
                domain="security",
                num_results=5,
                max_similarity=0.8,
                avg_similarity=0.7,
                backend_type="vector",
                latency_ms=100.0,
            )

        recent = tracker.get_recent_queries(limit=3)

        assert len(recent) == 3
        # Recent queries are in reverse chronological order (most recent last in list)
        # Query 4 should be in the list (last added)
        query_texts = [q["query"] for q in recent]
        assert "query 4" in query_texts  # Most recent should be included
        assert all("timestamp" in q for q in recent)

    def test_reset_metrics(self, temp_metrics_file):
        """Test resetting metrics."""
        tracker = RAGMetricsTracker(temp_metrics_file)

        tracker.record_query(
            query="test",
            expert_id="expert-1",
            domain="security",
            num_results=5,
            max_similarity=0.8,
            avg_similarity=0.7,
            backend_type="vector",
            latency_ms=100.0,
        )

        tracker.reset()

        assert tracker.performance_metrics.total_queries == 0
        assert len(tracker.query_history) == 0

    def test_global_tracker(self, temp_metrics_file):
        """Test global tracker instance."""
        # Reset global tracker
        import tapps_agents.experts.rag_metrics
        tapps_agents.experts.rag_metrics._global_tracker = None

        tracker1 = get_rag_metrics_tracker(metrics_file=temp_metrics_file)
        tracker2 = get_rag_metrics_tracker(metrics_file=temp_metrics_file)

        # Should return same instance when same file
        assert tracker1 is tracker2


class TestRAGQueryTimer:
    """Test RAG query timer context manager."""

    @pytest.fixture
    def temp_metrics_file(self):
        """Create temporary metrics file."""
        temp_dir = Path(tempfile.mkdtemp())
        metrics_file = temp_dir / "rag_metrics.json"

        yield metrics_file

        import shutil

        shutil.rmtree(temp_dir)

    def test_timer_context_manager(self, temp_metrics_file):
        """Test timer as context manager."""
        import time

        tracker = RAGMetricsTracker(temp_metrics_file)

        with RAGQueryTimer(tracker) as timer:
            timer.set_params(
                query="test",
                expert_id="expert-1",
                domain="security",
                num_results=5,
                max_similarity=0.8,
                avg_similarity=0.7,
                backend_type="vector",
            )
            time.sleep(0.1)  # Simulate query time

        # Metrics should be recorded
        assert tracker.performance_metrics.total_queries == 1
        assert tracker.performance_metrics.avg_latency_ms > 0

    def test_timer_without_params(self, temp_metrics_file):
        """Test timer without setting params (should not record)."""
        tracker = RAGMetricsTracker(temp_metrics_file)

        with RAGQueryTimer(tracker):
            pass  # No params set

        # Should not record query without params
        assert tracker.performance_metrics.total_queries == 0
