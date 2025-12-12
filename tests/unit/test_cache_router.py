"""
Unit tests for CacheRouter routing logic.

Tests routing to appropriate adapters for all three cache types.
"""

from unittest.mock import Mock

import pytest

from tapps_agents.context7.kb_cache import KBCache
from tapps_agents.core.cache_router import (
    CacheRequest,
    CacheRouter,
    CacheType,
    Context7KBAdapter,
    RAGKnowledgeAdapter,
    TieredContextAdapter,
)
from tapps_agents.core.context_manager import ContextManager, ContextTier
from tapps_agents.core.hardware_profiler import (
    CacheOptimizationProfile,
    HardwareProfile,
)
from tapps_agents.experts.simple_rag import SimpleKnowledgeBase


@pytest.mark.unit
class TestCacheRouterRouting:
    """Test CacheRouter routing logic."""

    @pytest.fixture
    def optimization_profile(self):
        """Create optimization profile."""
        return CacheOptimizationProfile(
            profile=HardwareProfile.DEVELOPMENT,
            tier1_ttl=300,
            tier2_ttl=120,
            tier3_ttl=60,
            max_in_memory_entries=100,
            hybrid_mode=True,
            compression_enabled=False,
            max_cache_size_mb=200,
            pre_populate=True,
            auto_refresh=True,
            index_on_startup=True,
            max_knowledge_files=500,
            enable_adaptive=True,
            resource_check_interval=60,
            emergency_cleanup_threshold=0.80,
        )

    @pytest.fixture
    def mock_context_manager(self):
        """Create mock context manager."""
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
        manager.clear_cache.return_value = None
        return manager

    @pytest.fixture
    def mock_kb_cache(self):
        """Create mock KB cache."""
        cache = Mock(spec=KBCache)
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
        cache.metadata_manager.load_cache_index.return_value = Mock(
            libraries={"test-lib": {"topics": {"test-topic": {}}}}
        )
        return cache

    @pytest.fixture
    def mock_knowledge_base(self):
        """Create mock knowledge base."""
        kb = Mock(spec=SimpleKnowledgeBase)
        kb.search.return_value = [{"chunk": "test", "score": 0.8}]
        kb.get_context.return_value = "test context"
        kb.get_sources.return_value = ["source1.md"]
        kb.list_all_files.return_value = ["file1.md"]
        kb.domain = "test-domain"
        return kb

    @pytest.fixture
    def router(
        self,
        optimization_profile,
        mock_context_manager,
        mock_kb_cache,
        mock_knowledge_base,
    ):
        """Create CacheRouter with all adapters."""
        return CacheRouter(
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            optimization_profile=optimization_profile,
        )

    def test_route_get_tiered_context(self, router, mock_context_manager):
        """Test routing get request to tiered context adapter."""
        request = CacheRequest(
            cache_type=CacheType.TIERED_CONTEXT, key="test.py", tier=ContextTier.TIER1
        )

        response = router.route_get(request)

        assert response is not None
        assert response.cache_type == CacheType.TIERED_CONTEXT
        assert response.cached is True
        mock_context_manager.get_context.assert_called_once()

    def test_route_get_context7_kb(self, router, mock_kb_cache):
        """Test routing get request to Context7 KB adapter."""
        request = CacheRequest(
            cache_type=CacheType.CONTEXT7_KB,
            key="test",
            library="test-lib",
            topic="test-topic",
        )

        response = router.route_get(request)

        assert response is not None
        assert response.cache_type == CacheType.CONTEXT7_KB
        assert response.cached is True
        mock_kb_cache.get.assert_called_once_with("test-lib", "test-topic")

    def test_route_get_rag_knowledge(self, router, mock_knowledge_base):
        """Test routing get request to RAG knowledge adapter."""
        request = CacheRequest(
            cache_type=CacheType.RAG_KNOWLEDGE, key="test", query="test query"
        )

        response = router.route_get(request)

        assert response is not None
        assert response.cache_type == CacheType.RAG_KNOWLEDGE
        assert response.cached is True
        mock_knowledge_base.search.assert_called_once()

    def test_route_get_no_adapter(self, optimization_profile):
        """Test routing get request when adapter not available."""
        router = CacheRouter(optimization_profile=optimization_profile)

        request = CacheRequest(
            cache_type=CacheType.TIERED_CONTEXT, key="test.py", tier=ContextTier.TIER1
        )

        response = router.route_get(request)

        assert response is None

    def test_route_put_tiered_context(self, router, mock_context_manager):
        """Test routing put request to tiered context adapter."""
        request = CacheRequest(
            cache_type=CacheType.TIERED_CONTEXT, key="test.py", tier=ContextTier.TIER1
        )

        response = router.route_put(request, {"content": "new"})

        assert response is not None
        assert response.cache_type == CacheType.TIERED_CONTEXT
        mock_context_manager.get_context.assert_called()

    def test_route_put_context7_kb(self, router, mock_kb_cache):
        """Test routing put request to Context7 KB adapter."""
        request = CacheRequest(
            cache_type=CacheType.CONTEXT7_KB,
            key="test",
            library="test-lib",
            topic="test-topic",
        )

        response = router.route_put(request, "new content")

        assert response is not None
        assert response.cache_type == CacheType.CONTEXT7_KB
        mock_kb_cache.store.assert_called_once()

    def test_route_put_no_adapter(self, optimization_profile):
        """Test routing put request when adapter not available."""
        router = CacheRouter(optimization_profile=optimization_profile)

        request = CacheRequest(cache_type=CacheType.TIERED_CONTEXT, key="test.py")

        response = router.route_put(request, "value")

        assert response is not None
        assert response.cached is False
        assert response.data == "value"

    def test_route_invalidate_tiered_context(self, router, mock_context_manager):
        """Test routing invalidate request to tiered context adapter."""
        request = CacheRequest(
            cache_type=CacheType.TIERED_CONTEXT, key="test.py", tier=ContextTier.TIER1
        )

        result = router.route_invalidate(request)

        assert result is True
        mock_context_manager.clear_cache.assert_called_once()

    def test_route_invalidate_context7_kb(self, router, mock_kb_cache):
        """Test routing invalidate request to Context7 KB adapter."""
        request = CacheRequest(
            cache_type=CacheType.CONTEXT7_KB,
            key="test",
            library="test-lib",
            topic="test-topic",
        )

        result = router.route_invalidate(request)

        assert result is True
        mock_kb_cache.delete.assert_called_once()

    def test_route_invalidate_no_adapter(self, optimization_profile):
        """Test routing invalidate request when adapter not available."""
        router = CacheRouter(optimization_profile=optimization_profile)

        request = CacheRequest(cache_type=CacheType.TIERED_CONTEXT, key="test.py")

        result = router.route_invalidate(request)

        assert result is False

    def test_get_all_stats(self, router):
        """Test getting statistics from all adapters."""
        stats = router.get_all_stats()

        assert "hardware_profile" in stats
        assert "caches" in stats
        assert CacheType.TIERED_CONTEXT.value in stats["caches"]
        assert CacheType.CONTEXT7_KB.value in stats["caches"]
        assert CacheType.RAG_KNOWLEDGE.value in stats["caches"]

    def test_get_adapter(self, router):
        """Test getting adapter for cache type."""
        adapter = router.get_adapter(CacheType.TIERED_CONTEXT)
        assert adapter is not None
        assert isinstance(adapter, TieredContextAdapter)

        adapter = router.get_adapter(CacheType.CONTEXT7_KB)
        assert adapter is not None
        assert isinstance(adapter, Context7KBAdapter)

        adapter = router.get_adapter(CacheType.RAG_KNOWLEDGE)
        assert adapter is not None
        assert isinstance(adapter, RAGKnowledgeAdapter)

        # Non-existent cache type
        adapter = router.get_adapter(CacheType.TIERED_CONTEXT)  # Should work
        assert adapter is not None


@pytest.mark.unit
class TestCacheAdapters:
    """Test individual cache adapters."""

    @pytest.fixture
    def optimization_profile(self):
        """Create optimization profile."""
        return CacheOptimizationProfile(
            profile=HardwareProfile.DEVELOPMENT,
            tier1_ttl=300,
            tier2_ttl=120,
            tier3_ttl=60,
            max_in_memory_entries=100,
            hybrid_mode=True,
            compression_enabled=False,
            max_cache_size_mb=200,
            pre_populate=True,
            auto_refresh=True,
            index_on_startup=True,
            max_knowledge_files=500,
            enable_adaptive=True,
            resource_check_interval=60,
            emergency_cleanup_threshold=0.80,
        )

    def test_tiered_context_adapter_initialization(self, optimization_profile):
        """Test TieredContextAdapter initializes with optimization profile."""
        mock_context_manager = Mock(spec=ContextManager)
        mock_context_manager.caches = {
            ContextTier.TIER1: Mock(max_size=50),
            ContextTier.TIER2: Mock(max_size=50),
            ContextTier.TIER3: Mock(max_size=50),
        }

        adapter = TieredContextAdapter(mock_context_manager, optimization_profile)

        # Verify cache sizes updated
        assert adapter.context_manager.caches[ContextTier.TIER1].max_size == 100
        assert adapter.context_manager.caches[ContextTier.TIER2].max_size == 100
        assert adapter.context_manager.caches[ContextTier.TIER3].max_size == 100

    def test_context7_kb_adapter_stats(self, optimization_profile):
        """Test Context7KBAdapter statistics."""
        mock_kb_cache = Mock(spec=KBCache)
        mock_kb_cache.metadata_manager = Mock()
        mock_kb_cache.metadata_manager.load_cache_index.return_value = Mock(
            libraries={
                "lib1": {"topics": {"topic1": {}, "topic2": {}}},
                "lib2": {"topics": {"topic3": {}}},
            }
        )

        adapter = Context7KBAdapter(mock_kb_cache, optimization_profile)
        stats = adapter.get_stats()

        assert stats["total_libraries"] == 2
        assert stats["total_entries"] == 3

    def test_rag_knowledge_adapter_stats(self, optimization_profile):
        """Test RAGKnowledgeAdapter statistics."""
        mock_kb = Mock(spec=SimpleKnowledgeBase)
        mock_kb.list_all_files.return_value = ["file1.md", "file2.md", "file3.md"]
        mock_kb.domain = "test-domain"

        adapter = RAGKnowledgeAdapter(mock_kb, optimization_profile)
        stats = adapter.get_stats()

        assert stats["total_files"] == 3
        assert stats["domain"] == "test-domain"
