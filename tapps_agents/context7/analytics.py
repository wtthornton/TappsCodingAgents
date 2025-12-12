"""
Performance Analytics for Context7 KB cache.

Tracks metrics like hit rate, response times, cache size, and provides
reporting functionality.
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import yaml

from .cache_structure import CacheStructure
from .metadata import MetadataManager

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Metrics for the Context7 KB cache."""

    total_entries: int = 0
    total_libraries: int = 0
    total_topics: int = 0
    total_size_bytes: int = 0
    total_tokens: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    api_calls: int = 0
    fuzzy_matches: int = 0
    avg_response_time_ms: float = 0.0
    hit_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LibraryMetrics:
    """Metrics for a specific library."""

    library: str
    topics: int = 0
    cache_hits: int = 0
    total_tokens: int = 0
    size_bytes: int = 0
    last_accessed: str | None = None
    last_updated: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class Analytics:
    """Performance analytics for Context7 KB cache."""

    def __init__(
        self, cache_structure: CacheStructure, metadata_manager: MetadataManager
    ):
        """
        Initialize analytics.

        Args:
            cache_structure: CacheStructure instance
            metadata_manager: MetadataManager instance
        """
        self.cache_structure = cache_structure
        self.metadata_manager = metadata_manager
        self.metrics: dict[str, Any] = {}
        self._load_metrics()

    def _load_metrics(self):
        """Load metrics from file if it exists."""
        metrics_file = self.cache_structure.cache_root / ".metrics.yaml"
        if metrics_file.exists():
            try:
                with open(metrics_file, encoding="utf-8") as f:
                    self.metrics = yaml.safe_load(f) or {}
            except Exception:
                self.metrics = {}
        else:
            self.metrics = {
                "cache_hits": 0,
                "cache_misses": 0,
                "api_calls": 0,
                "fuzzy_matches": 0,
                "response_times": [],
            }

    def _save_metrics(self):
        """Save metrics to file."""
        metrics_file = self.cache_structure.cache_root / ".metrics.yaml"
        metrics_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(metrics_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    self.metrics, f, default_flow_style=False, sort_keys=False
                )
        except Exception:
            logger.debug("Failed to save Context7 metrics", exc_info=True)

    def record_cache_hit(self, response_time_ms: float = 0.0):
        """Record a cache hit."""
        self.metrics["cache_hits"] = self.metrics.get("cache_hits", 0) + 1
        if response_time_ms > 0:
            response_times = self.metrics.get("response_times", [])
            response_times.append(response_time_ms)
            # Keep only last 1000 response times
            if len(response_times) > 1000:
                response_times = response_times[-1000:]
            self.metrics["response_times"] = response_times
        self._save_metrics()

    def record_cache_miss(self):
        """Record a cache miss."""
        self.metrics["cache_misses"] = self.metrics.get("cache_misses", 0) + 1
        self._save_metrics()

    def record_api_call(self):
        """Record an API call to Context7."""
        self.metrics["api_calls"] = self.metrics.get("api_calls", 0) + 1
        self._save_metrics()

    def record_fuzzy_match(self):
        """Record a fuzzy match."""
        self.metrics["fuzzy_matches"] = self.metrics.get("fuzzy_matches", 0) + 1
        self._save_metrics()

    def get_cache_metrics(self) -> CacheMetrics:
        """
        Get overall cache metrics.

        Returns:
            CacheMetrics instance
        """
        index = self.metadata_manager.load_cache_index()

        # Calculate totals from index
        total_entries = index.total_entries
        total_libraries = len(index.libraries)
        total_topics = sum(
            len(lib_data.get("topics", {})) for lib_data in index.libraries.values()
        )

        # Calculate size and tokens (estimate from files)
        total_size_bytes = 0
        total_tokens = 0
        cache_hits = 0

        for library, _lib_data in index.libraries.items():
            metadata = self.metadata_manager.load_library_metadata(library)
            if metadata:
                cache_hits += metadata.cache_hits
                total_size_bytes += metadata.total_size_bytes
                total_tokens += metadata.total_tokens or 0

        # Get hit/miss counts
        cache_hits_count = self.metrics.get("cache_hits", 0)
        cache_misses_count = self.metrics.get("cache_misses", 0)
        api_calls_count = self.metrics.get("api_calls", 0)
        fuzzy_matches_count = self.metrics.get("fuzzy_matches", 0)

        # Calculate hit rate
        total_requests = cache_hits_count + cache_misses_count
        hit_rate = (
            (cache_hits_count / total_requests * 100) if total_requests > 0 else 0.0
        )

        # Calculate average response time
        response_times = self.metrics.get("response_times", [])
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0.0
        )

        return CacheMetrics(
            total_entries=total_entries,
            total_libraries=total_libraries,
            total_topics=total_topics,
            total_size_bytes=total_size_bytes,
            total_tokens=total_tokens,
            cache_hits=cache_hits_count,
            cache_misses=cache_misses_count,
            api_calls=api_calls_count,
            fuzzy_matches=fuzzy_matches_count,
            avg_response_time_ms=avg_response_time,
            hit_rate=hit_rate,
        )

    def get_library_metrics(self, library: str) -> LibraryMetrics | None:
        """
        Get metrics for a specific library.

        Args:
            library: Library name

        Returns:
            LibraryMetrics or None if library not found
        """
        metadata = self.metadata_manager.load_library_metadata(library)
        if not metadata:
            return None

        index = self.metadata_manager.load_cache_index()
        lib_data = index.libraries.get(library, {})
        topics = len(lib_data.get("topics", {}))

        return LibraryMetrics(
            library=library,
            topics=topics,
            cache_hits=metadata.cache_hits,
            total_tokens=metadata.total_tokens or 0,
            size_bytes=metadata.total_size_bytes,
            last_accessed=metadata.last_accessed,
            last_updated=metadata.last_updated,
        )

    def get_top_libraries(self, limit: int = 10) -> list[LibraryMetrics]:
        """
        Get top libraries by cache hits.

        Args:
            limit: Maximum number of libraries to return

        Returns:
            List of LibraryMetrics, sorted by cache hits (descending)
        """
        index = self.metadata_manager.load_cache_index()
        library_metrics_list = []

        for library in index.libraries.keys():
            metrics = self.get_library_metrics(library)
            if metrics:
                library_metrics_list.append(metrics)

        # Sort by cache hits (descending)
        library_metrics_list.sort(key=lambda m: m.cache_hits, reverse=True)
        return library_metrics_list[:limit]

    def get_status_report(self) -> dict[str, Any]:
        """
        Get comprehensive status report.

        Returns:
            Dictionary with status information
        """
        metrics = self.get_cache_metrics()

        return {
            "status": "healthy" if metrics.hit_rate > 70 else "needs_attention",
            "metrics": metrics.to_dict(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "top_libraries": [m.to_dict() for m in self.get_top_libraries(5)],
        }

    def reset_metrics(self):
        """Reset all metrics (keeps cache entries)."""
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "api_calls": 0,
            "fuzzy_matches": 0,
            "response_times": [],
        }
        self._save_metrics()
