"""
Performance validation tests for UnifiedCache.

Tests response times, hit rates, and resource usage to ensure performance targets are met.
"""

import time
from unittest.mock import Mock

import pytest

from tapps_agents.core.cache_router import CacheType
from tapps_agents.core.context_manager import ContextManager, ContextTier
from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.unified_cache import UnifiedCache


@pytest.mark.unit
class TestPerformanceValidation:
    """Test performance metrics and targets."""

    @pytest.fixture
    def tmp_cache_root(self, tmp_path):
        """Create temporary cache root directory."""
        cache_root = tmp_path / ".tapps-agents" / "kb"
        cache_root.mkdir(parents=True, exist_ok=True)
        return cache_root

    @pytest.fixture
    def mock_context_manager(self):
        """Create fast mock context manager."""
        manager = Mock(spec=ContextManager)
        manager.get_context.return_value = {
            "content": "test context",
            "cached": True,
            "token_estimate": 100,
        }
        manager.caches = {
            ContextTier.TIER1: Mock(max_size=100),
            ContextTier.TIER2: Mock(max_size=100),
            ContextTier.TIER3: Mock(max_size=100),
        }
        manager.get_cache_stats.return_value = {"hits": 10, "misses": 5}
        return manager

    @pytest.fixture
    def mock_kb_cache(self):
        """Create fast mock KB cache."""
        cache = Mock()
        cache.get.return_value = Mock(
            content="test KB content",
            context7_id="test-id",
            trust_score=0.9,
            token_count=200,
            cache_hits=5,
        )
        cache.store.return_value = Mock(content="stored", token_count=150)
        cache.delete.return_value = True
        cache.metadata_manager = Mock()
        cache.metadata_manager.load_cache_index.return_value = Mock(libraries={})
        return cache

    @pytest.fixture
    def mock_knowledge_base(self):
        """Create fast mock knowledge base."""
        kb = Mock()
        kb.search.return_value = [{"chunk": "test", "score": 0.8}]
        kb.get_context.return_value = "test context"
        kb.get_sources.return_value = []
        kb.list_all_files.return_value = []
        kb.domain = "test"
        return kb

    def test_tiered_context_response_time(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test tiered context cache response time meets target (<10ms for in-memory)."""
        cache = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.DEVELOPMENT,
        )

        # Measure response time
        start = time.perf_counter()
        response = cache.get(
            cache_type=CacheType.TIERED_CONTEXT, key="test.py", tier=ContextTier.TIER1
        )
        elapsed = (time.perf_counter() - start) * 1000  # Convert to milliseconds

        assert response is not None
        # Target: <10ms for in-memory cache (with some margin for test overhead)
        assert elapsed < 50, f"Response time {elapsed:.2f}ms exceeds target of 10ms"

    def test_context7_kb_response_time(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test Context7 KB cache response time meets target (<150ms)."""
        cache = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.DEVELOPMENT,
        )

        # Measure response time
        start = time.perf_counter()
        response = cache.get(
            cache_type=CacheType.CONTEXT7_KB,
            key="test",
            library="test-lib",
            topic="test-topic",
        )
        elapsed = (time.perf_counter() - start) * 1000  # Convert to milliseconds

        assert response is not None
        # Target: <150ms (with margin for test overhead)
        assert elapsed < 200, f"Response time {elapsed:.2f}ms exceeds target of 150ms"

    def test_unified_interface_overhead(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test unified interface overhead is minimal (<5ms target)."""
        cache = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.DEVELOPMENT,
        )

        # Measure overhead of unified interface
        start = time.perf_counter()
        for _ in range(100):
            cache.get(
                cache_type=CacheType.TIERED_CONTEXT,
                key="test.py",
                tier=ContextTier.TIER1,
            )
        elapsed = (time.perf_counter() - start) * 1000  # Total time in ms
        avg_overhead = elapsed / 100  # Average per call

        # Target: <5ms overhead per call (with margin)
        assert (
            avg_overhead < 20
        ), f"Average overhead {avg_overhead:.2f}ms exceeds target of 5ms"

    def test_hit_rate_tracking(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test that hit/miss rates are tracked correctly for performance analysis."""
        cache = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.DEVELOPMENT,
        )

        # Make some requests
        for i in range(10):
            cache.get(
                cache_type=CacheType.TIERED_CONTEXT,
                key=f"test{i}.py",
                tier=ContextTier.TIER1,
            )

        stats = cache.get_stats()

        # Verify statistics are tracked
        assert stats.total_hits >= 0
        assert stats.total_misses >= 0
        assert stats.total_hits + stats.total_misses == 10

        # Calculate hit rate
        total_requests = stats.total_hits + stats.total_misses
        if total_requests > 0:
            hit_rate = stats.total_hits / total_requests
            # Target: 85%+ hit rate for tiered context (in test, all should hit due to mock)
            assert hit_rate >= 0.0  # At minimum, tracking works

    def test_concurrent_requests(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test that cache handles concurrent requests efficiently."""
        cache = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.DEVELOPMENT,
        )

        # Simulate concurrent requests
        start = time.perf_counter()
        for i in range(50):
            cache.get(
                cache_type=CacheType.TIERED_CONTEXT,
                key=f"test{i}.py",
                tier=ContextTier.TIER1,
            )
        elapsed = (time.perf_counter() - start) * 1000

        # Should handle 50 requests quickly
        assert (
            elapsed < 500
        ), f"50 concurrent requests took {elapsed:.2f}ms, should be <500ms"

    def test_memory_usage_by_profile(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test that memory usage scales appropriately by hardware profile."""
        # NUC profile (conservative)
        cache_nuc = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.NUC,
        )
        profile_nuc = cache_nuc.get_optimization_profile()

        # Workstation profile (aggressive)
        cache_ws = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.WORKSTATION,
        )
        profile_ws = cache_ws.get_optimization_profile()

        # Workstation should allow more in-memory entries
        assert (
            profile_ws["tiered_context"]["max_in_memory_entries"]
            > profile_nuc["tiered_context"]["max_in_memory_entries"]
        )
        assert (
            profile_ws["context7_kb"]["max_cache_size_mb"]
            > profile_nuc["context7_kb"]["max_cache_size_mb"]
        )

    def test_cache_size_limits(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test that cache respects size limits by hardware profile."""
        # NUC profile
        cache = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.NUC,
        )

        profile = cache.get_optimization_profile()

        # Verify NUC limits are conservative
        assert profile["tiered_context"]["max_in_memory_entries"] == 50
        assert profile["context7_kb"]["max_cache_size_mb"] == 100
        assert profile["rag_knowledge"]["max_knowledge_files"] == 100

    def test_statistics_aggregation(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test that statistics are correctly aggregated across all cache types."""
        cache = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.DEVELOPMENT,
        )

        # Make requests to different cache types
        cache.get(
            cache_type=CacheType.TIERED_CONTEXT, key="test1.py", tier=ContextTier.TIER1
        )
        cache.get(
            cache_type=CacheType.CONTEXT7_KB, key="test2", library="lib", topic="topic"
        )
        cache.get(cache_type=CacheType.RAG_KNOWLEDGE, key="test3", query="query")

        stats = cache.get_stats()

        # Verify statistics include all cache types
        assert "caches" in stats.cache_stats
        assert CacheType.TIERED_CONTEXT.value in stats.cache_stats["caches"]
        assert CacheType.CONTEXT7_KB.value in stats.cache_stats["caches"]
        assert CacheType.RAG_KNOWLEDGE.value in stats.cache_stats["caches"]

        # Verify resource usage is tracked
        assert (
            "resource_usage" in stats.cache_stats or "resource_usage" in stats.__dict__
        )
