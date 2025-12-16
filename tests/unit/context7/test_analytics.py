"""
Unit tests for Context7 analytics.
"""

import tempfile
from pathlib import Path

import pytest

from tapps_agents.context7.analytics import Analytics, CacheMetrics, LibraryMetrics
from tapps_agents.context7.cache_structure import CacheStructure
from tapps_agents.context7.metadata import LibraryMetadata, MetadataManager

pytestmark = pytest.mark.unit


class TestCacheMetrics:
    def test_cache_metrics_creation(self):
        metrics = CacheMetrics(total_entries=10, total_libraries=5, hit_rate=85.5)
        assert metrics.total_entries == 10
        assert metrics.total_libraries == 5
        assert metrics.hit_rate == 85.5

    def test_cache_metrics_to_dict(self):
        metrics = CacheMetrics(
            total_entries=10, total_libraries=5, cache_hits=100, cache_misses=20
        )
        metrics_dict = metrics.to_dict()
        assert metrics_dict["total_entries"] == 10
        assert metrics_dict["total_libraries"] == 5
        assert metrics_dict["cache_hits"] == 100
        assert metrics_dict["cache_misses"] == 20


class TestLibraryMetrics:
    def test_library_metrics_creation(self):
        metrics = LibraryMetrics(library="react", topics=5, cache_hits=50)
        assert metrics.library == "react"
        assert metrics.topics == 5
        assert metrics.cache_hits == 50

    def test_library_metrics_to_dict(self):
        metrics = LibraryMetrics(
            library="react", topics=5, cache_hits=50, total_tokens=1000
        )
        metrics_dict = metrics.to_dict()
        assert metrics_dict["library"] == "react"
        assert metrics_dict["topics"] == 5
        assert metrics_dict["cache_hits"] == 50
        assert metrics_dict["total_tokens"] == 1000


class TestAnalytics:
    @pytest.fixture
    def temp_cache_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cache_structure(self, temp_cache_root):
        cs = CacheStructure(temp_cache_root)
        cs.initialize()
        return cs

    @pytest.fixture
    def metadata_manager(self, cache_structure):
        return MetadataManager(cache_structure)

    @pytest.fixture
    def analytics(self, cache_structure, metadata_manager):
        return Analytics(cache_structure, metadata_manager)

    def test_initialization(self, cache_structure, metadata_manager):
        analytics = Analytics(cache_structure, metadata_manager)
        assert analytics.cache_structure == cache_structure
        assert analytics.metadata_manager == metadata_manager

    def test_record_cache_hit(self, analytics):
        initial_hits = analytics.metrics.get("cache_hits", 0)
        analytics.record_cache_hit(response_time_ms=10.5)
        assert analytics.metrics["cache_hits"] == initial_hits + 1

        # Check response time recorded
        response_times = analytics.metrics.get("response_times", [])
        assert 10.5 in response_times

    def test_record_cache_miss(self, analytics):
        initial_misses = analytics.metrics.get("cache_misses", 0)
        analytics.record_cache_miss()
        assert analytics.metrics["cache_misses"] == initial_misses + 1

    def test_record_api_call(self, analytics):
        initial_calls = analytics.metrics.get("api_calls", 0)
        analytics.record_api_call()
        assert analytics.metrics["api_calls"] == initial_calls + 1

    def test_record_fuzzy_match(self, analytics):
        initial_matches = analytics.metrics.get("fuzzy_matches", 0)
        analytics.record_fuzzy_match()
        assert analytics.metrics["fuzzy_matches"] == initial_matches + 1

    def test_get_cache_metrics_empty_cache(self, analytics):
        metrics = analytics.get_cache_metrics()
        assert metrics.total_entries == 0
        assert metrics.total_libraries == 0
        assert metrics.total_topics == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.hit_rate == 0.0

    def test_get_cache_metrics_with_data(
        self, analytics, metadata_manager, cache_structure
    ):
        # Add some metadata
        metadata = LibraryMetadata(
            library="react",
            topics=["hooks", "routing"],
            cache_hits=10,
            total_tokens=500,
            total_size_bytes=1000,
        )
        metadata_manager.save_library_metadata(metadata)
        metadata_manager.update_cache_index("react", "hooks")
        metadata_manager.update_cache_index("react", "routing")

        # Record some metrics
        analytics.record_cache_hit()
        analytics.record_cache_hit()
        analytics.record_cache_miss()
        analytics.record_api_call()

        metrics = analytics.get_cache_metrics()
        assert metrics.total_libraries == 1
        assert metrics.total_entries == 2
        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 1
        assert metrics.api_calls == 1
        assert metrics.hit_rate == (2 / 3 * 100)  # 2 hits / 3 total requests

    def test_get_library_metrics_nonexistent(self, analytics):
        metrics = analytics.get_library_metrics("nonexistent")
        assert metrics is None

    def test_get_library_metrics_existing(self, analytics, metadata_manager):
        metadata = LibraryMetadata(
            library="react",
            topics=["hooks", "routing"],
            cache_hits=15,
            total_tokens=500,
            total_size_bytes=1000,
            last_accessed="2024-01-01T00:00:00Z",
            last_updated="2024-01-01T00:00:00Z",
        )
        metadata_manager.save_library_metadata(metadata)
        metadata_manager.update_cache_index("react", "hooks")
        metadata_manager.update_cache_index("react", "routing")

        metrics = analytics.get_library_metrics("react")
        assert metrics is not None
        assert metrics.library == "react"
        assert metrics.topics == 2
        assert metrics.cache_hits == 15
        assert metrics.total_tokens == 500

    def test_get_top_libraries(self, analytics, metadata_manager):
        # Add multiple libraries with different hit counts
        for lib, hits in [("react", 20), ("vue", 10), ("angular", 5)]:
            metadata = LibraryMetadata(library=lib, cache_hits=hits)
            metadata_manager.save_library_metadata(metadata)
            metadata_manager.update_cache_index(lib, "overview")

        top_libs = analytics.get_top_libraries(limit=2)
        assert len(top_libs) == 2
        assert top_libs[0].library == "react"  # Highest hits
        assert top_libs[1].library == "vue"

    def test_get_top_libraries_empty(self, analytics):
        top_libs = analytics.get_top_libraries()
        assert len(top_libs) == 0

    def test_get_status_report_healthy(self, analytics, metadata_manager):
        # Record more hits than misses (good hit rate)
        for _ in range(10):
            analytics.record_cache_hit()
        for _ in range(2):
            analytics.record_cache_miss()

        report = analytics.get_status_report()
        assert report["status"] == "healthy"
        assert "metrics" in report
        assert "timestamp" in report
        assert "top_libraries" in report

    def test_get_status_report_needs_attention(self, analytics):
        # Record more misses than hits (poor hit rate)
        for _ in range(2):
            analytics.record_cache_hit()
        for _ in range(10):
            analytics.record_cache_miss()

        report = analytics.get_status_report()
        assert report["status"] == "needs_attention"

    def test_get_status_report_structure(self, analytics):
        report = analytics.get_status_report()
        assert "status" in report
        assert "metrics" in report
        assert "timestamp" in report
        assert "top_libraries" in report

        metrics = report["metrics"]
        assert "total_entries" in metrics
        assert "hit_rate" in metrics
        assert "cache_hits" in metrics

    def test_reset_metrics(self, analytics):
        # Record some metrics
        analytics.record_cache_hit()
        analytics.record_cache_miss()
        analytics.record_api_call()

        # Reset
        analytics.reset_metrics()

        assert analytics.metrics["cache_hits"] == 0
        assert analytics.metrics["cache_misses"] == 0
        assert analytics.metrics["api_calls"] == 0
        assert analytics.metrics["fuzzy_matches"] == 0
        assert len(analytics.metrics["response_times"]) == 0

    @pytest.mark.skip(reason="TODO: Fix file operation timeout - needs proper tmp_path usage")
    def test_response_times_limit(self, analytics):
        # Record many response times (should keep only last 1000)
        print("\n[TEST] Recording 1500 response times (testing limit enforcement)...")
        for i in range(1500):
            if i % 300 == 0:
                print(f"[TEST] Progress: {i}/1500 records...")
            analytics.record_cache_hit(response_time_ms=float(i))

        print("[TEST] Verifying response times limit...")
        response_times = analytics.metrics.get("response_times", [])
        assert len(response_times) == 1000
        # Should have the latest values (1000-1499)
        assert min(response_times) >= 500  # First 500 should be removed
        print("[TEST] Response times limit test passed OK")

    def test_average_response_time_calculation(self, analytics):
        analytics.record_cache_hit(response_time_ms=10.0)
        analytics.record_cache_hit(response_time_ms=20.0)
        analytics.record_cache_hit(response_time_ms=30.0)

        metrics = analytics.get_cache_metrics()
        assert metrics.avg_response_time_ms == 20.0

    def test_average_response_time_no_data(self, analytics):
        metrics = analytics.get_cache_metrics()
        assert metrics.avg_response_time_ms == 0.0

    def test_metrics_persistence(
        self, temp_cache_root, cache_structure, metadata_manager
    ):
        analytics1 = Analytics(cache_structure, metadata_manager)
        analytics1.record_cache_hit()
        analytics1.record_cache_miss()

        # Create new instance (should load from file)
        analytics2 = Analytics(cache_structure, metadata_manager)
        assert analytics2.metrics["cache_hits"] == 1
        assert analytics2.metrics["cache_misses"] == 1

    def test_hit_rate_calculation(self, analytics):
        # 80% hit rate
        for _ in range(8):
            analytics.record_cache_hit()
        for _ in range(2):
            analytics.record_cache_miss()

        metrics = analytics.get_cache_metrics()
        assert metrics.hit_rate == 80.0

    def test_hit_rate_no_requests(self, analytics):
        metrics = analytics.get_cache_metrics()
        assert metrics.hit_rate == 0.0  # No requests yet
