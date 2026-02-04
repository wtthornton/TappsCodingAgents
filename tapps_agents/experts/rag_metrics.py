"""
RAG Performance Metrics

Tracks RAG system performance including hit rates, latency, and query patterns.
"""

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class RAGQueryMetrics:
    """Metrics for a single RAG query."""

    query: str
    expert_id: str
    domain: str
    timestamp: datetime
    latency_ms: float
    num_results: int
    max_similarity: float
    avg_similarity: float
    backend_type: str  # 'vector' or 'simple'
    cache_hit: bool = False


@dataclass
class RAGPerformanceMetrics:
    """Aggregated RAG performance metrics."""

    total_queries: int = 0
    total_latency_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    queries_by_expert: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    queries_by_domain: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    avg_latency_ms: float = 0.0
    avg_results: float = 0.0
    avg_similarity: float = 0.0
    backend_usage: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    similarity_distribution: dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )  # 'high' (>0.8), 'medium' (0.6-0.8), 'low' (<0.6)

    def update(self, query_metrics: RAGQueryMetrics) -> None:
        """Update metrics with a new query."""
        self.total_queries += 1
        self.total_latency_ms += query_metrics.latency_ms
        self.avg_latency_ms = self.total_latency_ms / self.total_queries

        if query_metrics.cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        self.queries_by_expert[query_metrics.expert_id] += 1
        self.queries_by_domain[query_metrics.domain] += 1
        self.backend_usage[query_metrics.backend_type] += 1

        # Update similarity distribution
        if query_metrics.max_similarity >= 0.8:
            self.similarity_distribution["high"] += 1
        elif query_metrics.max_similarity >= 0.6:
            self.similarity_distribution["medium"] += 1
        else:
            self.similarity_distribution["low"] += 1

        # Update averages
        if self.total_queries > 0:
            # Running average for results
            self.avg_results = (
                (self.avg_results * (self.total_queries - 1) + query_metrics.num_results)
                / self.total_queries
            )
            # Running average for similarity
            self.avg_similarity = (
                (self.avg_similarity * (self.total_queries - 1) + query_metrics.max_similarity)
                / self.total_queries
            )


class RAGMetricsTracker:
    """Tracks RAG performance metrics."""

    def __init__(self, metrics_file: Path | None = None):
        """
        Initialize metrics tracker.

        Args:
            metrics_file: Optional path to persist metrics (JSON)
        """
        self.metrics_file = metrics_file
        self.performance_metrics = RAGPerformanceMetrics()
        self.query_history: list[RAGQueryMetrics] = []
        self.max_history = 1000  # Keep last 1000 queries

    def record_query(
        self,
        query: str,
        expert_id: str,
        domain: str,
        num_results: int,
        max_similarity: float,
        avg_similarity: float,
        backend_type: str,
        cache_hit: bool = False,
        latency_ms: float | None = None,
    ) -> None:
        """
        Record a RAG query.

        Args:
            query: Search query
            expert_id: Expert ID
            domain: Domain name
            num_results: Number of results returned
            max_similarity: Maximum similarity score
            avg_similarity: Average similarity score
            backend_type: 'vector' or 'simple'
            cache_hit: Whether this was a cache hit
            latency_ms: Query latency in milliseconds (if None, will be calculated)
        """
        if latency_ms is None:
            latency_ms = 0.0  # Will be set by context manager

        query_metrics = RAGQueryMetrics(
            query=query,
            expert_id=expert_id,
            domain=domain,
            timestamp=datetime.now(),
            latency_ms=latency_ms,
            num_results=num_results,
            max_similarity=max_similarity,
            avg_similarity=avg_similarity,
            backend_type=backend_type,
            cache_hit=cache_hit,
        )

        self.query_history.append(query_metrics)
        if len(self.query_history) > self.max_history:
            self.query_history.pop(0)

        self.performance_metrics.update(query_metrics)

        # Persist if file provided
        if self.metrics_file:
            self._persist_metrics()

    def get_metrics(self) -> dict[str, Any]:
        """
        Get current performance metrics.

        Returns:
            Dictionary with metrics
        """
        cache_hit_rate = (
            self.performance_metrics.cache_hits
            / (self.performance_metrics.cache_hits + self.performance_metrics.cache_misses)
            if (self.performance_metrics.cache_hits + self.performance_metrics.cache_misses) > 0
            else 0.0
        )

        return {
            "total_queries": self.performance_metrics.total_queries,
            "avg_latency_ms": round(self.performance_metrics.avg_latency_ms, 2),
            "cache_hit_rate": round(cache_hit_rate, 3),
            "avg_results": round(self.performance_metrics.avg_results, 2),
            "avg_similarity": round(self.performance_metrics.avg_similarity, 3),
            "backend_usage": dict(self.performance_metrics.backend_usage),
            "similarity_distribution": dict(self.performance_metrics.similarity_distribution),
            "queries_by_expert": dict(self.performance_metrics.queries_by_expert),
            "queries_by_domain": dict(self.performance_metrics.queries_by_domain),
        }

    def get_recent_queries(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent query history.

        Args:
            limit: Number of recent queries to return

        Returns:
            List of recent queries as dictionaries
        """
        recent = self.query_history[-limit:]
        return [
            {
                "query": q.query,
                "expert_id": q.expert_id,
                "domain": q.domain,
                "timestamp": q.timestamp.isoformat(),
                "latency_ms": round(q.latency_ms, 2),
                "num_results": q.num_results,
                "max_similarity": round(q.max_similarity, 3),
                "backend_type": q.backend_type,
                "cache_hit": q.cache_hit,
            }
            for q in recent
        ]

    def _persist_metrics(self) -> None:
        """Persist metrics to file."""
        if not self.metrics_file:
            return

        try:
            data = {
                "metrics": self.get_metrics(),
                "recent_queries": self.get_recent_queries(100),
                "last_updated": datetime.now().isoformat(),
            }

            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            self.metrics_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            # Silently fail if persistence fails (non-critical)
            pass

    def reset(self) -> None:
        """Reset all metrics."""
        self.performance_metrics = RAGPerformanceMetrics()
        self.query_history = []


# Global metrics tracker instance
_global_tracker: RAGMetricsTracker | None = None


def get_rag_metrics_tracker(metrics_file: Path | None = None) -> RAGMetricsTracker:
    """
    Get or create global RAG metrics tracker.

    Args:
        metrics_file: Optional path to persist metrics

    Returns:
        RAGMetricsTracker instance
    """
    global _global_tracker

    if _global_tracker is None:
        if metrics_file is None:
            # Default location
            project_root = Path.cwd()
            metrics_file = project_root / ".tapps-agents" / "rag_metrics.json"

        _global_tracker = RAGMetricsTracker(metrics_file=metrics_file)

    return _global_tracker


class RAGQueryTimer:
    """Context manager for timing RAG queries."""

    def __init__(self, tracker: RAGMetricsTracker):
        """
        Initialize timer.

        Args:
            tracker: Metrics tracker to record to
        """
        self.tracker = tracker
        self.start_time: float | None = None
        self.query_params: dict[str, Any] = {}

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record metrics."""
        if self.start_time is None:
            return

        latency_ms = (time.time() - self.start_time) * 1000

        # Record query if params provided
        if self.query_params:
            self.tracker.record_query(
                latency_ms=latency_ms,
                **self.query_params,
            )

    def set_params(self, **kwargs: Any) -> None:
        """Set query parameters for recording."""
        self.query_params.update(kwargs)
