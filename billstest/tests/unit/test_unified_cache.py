"""
Unit tests for UnifiedCache interface.

Tests the unified cache API (get, put, invalidate, get_stats) across all cache types.
"""

from unittest.mock import Mock, patch

import pytest

from tapps_agents.context7.kb_cache import KBCache
from tapps_agents.core.cache_router import CacheType
from tapps_agents.core.context_manager import ContextManager, ContextTier
from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.unified_cache import UnifiedCache, UnifiedCacheStats
from tapps_agents.experts.simple_rag import SimpleKnowledgeBase


@pytest.mark.unit
class TestUnifiedCacheInterface:
    """Test UnifiedCache interface methods."""

    @pytest.fixture
    def tmp_cache_root(self, tmp_path):
        """Create temporary cache root directory."""
        cache_root = tmp_path / ".tapps-agents" / "kb"
        cache_root.mkdir(parents=True, exist_ok=True)
        return cache_root

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
    def mock_kb_cache(self, tmp_cache_root):
        """Create mock KB cache."""
        cache = Mock(spec=KBCache)
        cache.get.return_value = Mock(
            content="test KB content",
            context7_id="test-id",
            trust_score=0.9,
            token_count=200,
            cache_hits=5,
        )
        cache.store.return_value = Mock(content="stored content", token_count=150)
        cache.delete.return_value = True
        cache.metadata_manager = Mock()
        cache.metadata_manager.load_cache_index.return_value = Mock(
            libraries={"test-lib": {"topics": {"test-topic": {}}}}
        )
        return cache

    @pytest.fixture
    def mock_knowledge_base(self, tmp_cache_root):
        """Create mock knowledge base."""
        kb = Mock(spec=SimpleKnowledgeBase)
        kb.search.return_value = [{"chunk": "test chunk", "score": 0.8}]
        kb.get_context.return_value = "test context from knowledge base"
        kb.get_sources.return_value = ["source1.md", "source2.md"]
        kb.list_all_files.return_value = ["file1.md", "file2.md"]
        kb.domain = "test-domain"
        return kb

    @pytest.fixture
    def unified_cache(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Create UnifiedCache instance with mocks."""
        return UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.DEVELOPMENT,
        )

    def test_get_tiered_context(self, unified_cache, mock_context_manager):
        """Test getting tiered context from cache."""
        response = unified_cache.get(
            cache_type=CacheType.TIERED_CONTEXT, key="test.py", tier=ContextTier.TIER1
        )

        assert response is not None
        assert response.cached is True
        assert response.cache_type == CacheType.TIERED_CONTEXT
        assert "content" in response.data
        mock_context_manager.get_context.assert_called_once()

    def test_get_context7_kb(self, unified_cache, mock_kb_cache):
        """Test getting Context7 KB entry from cache."""
        response = unified_cache.get(
            cache_type=CacheType.CONTEXT7_KB,
            key="test",
            library="test-lib",
            topic="test-topic",
        )

        assert response is not None
        assert response.cached is True
        assert response.cache_type == CacheType.CONTEXT7_KB
        assert response.data == "test KB content"
        assert response.metadata["library"] == "test-lib"
        mock_kb_cache.get.assert_called_once_with("test-lib", "test-topic")

    def test_get_rag_knowledge(self, unified_cache, mock_knowledge_base):
        """Test getting RAG knowledge from cache."""
        response = unified_cache.get(
            cache_type=CacheType.RAG_KNOWLEDGE,
            key="test",
            query="test query",
            domain="test-domain",
        )

        assert response is not None
        assert response.cached is True
        assert response.cache_type == CacheType.RAG_KNOWLEDGE
        assert response.data == "test context from knowledge base"
        mock_knowledge_base.search.assert_called_once()

    def test_get_miss(self, unified_cache, mock_context_manager):
        """Test cache miss returns None."""
        mock_context_manager.get_context.return_value = None

        response = unified_cache.get(
            cache_type=CacheType.TIERED_CONTEXT,
            key="nonexistent.py",
            tier=ContextTier.TIER1,
        )

        assert response is None
        assert unified_cache._stats["misses"] == 1

    def test_put_tiered_context(self, unified_cache, mock_context_manager):
        """Test storing tiered context in cache."""
        response = unified_cache.put(
            cache_type=CacheType.TIERED_CONTEXT,
            key="test.py",
            value={"content": "new context"},
            tier=ContextTier.TIER1,
        )

        assert response is not None
        assert response.cache_type == CacheType.TIERED_CONTEXT
        mock_context_manager.get_context.assert_called()

    def test_put_context7_kb(self, unified_cache, mock_kb_cache):
        """Test storing Context7 KB entry in cache."""
        response = unified_cache.put(
            cache_type=CacheType.CONTEXT7_KB,
            key="test",
            value="new KB content",
            library="test-lib",
            topic="test-topic",
        )

        assert response is not None
        assert response.cache_type == CacheType.CONTEXT7_KB
        mock_kb_cache.store.assert_called_once()

    def test_invalidate_tiered_context(self, unified_cache, mock_context_manager):
        """Test invalidating tiered context cache."""
        result = unified_cache.invalidate(
            cache_type=CacheType.TIERED_CONTEXT, key="test.py", tier=ContextTier.TIER1
        )

        assert result is True
        mock_context_manager.clear_cache.assert_called_once()

    def test_invalidate_context7_kb(self, unified_cache, mock_kb_cache):
        """Test invalidating Context7 KB cache."""
        result = unified_cache.invalidate(
            cache_type=CacheType.CONTEXT7_KB,
            key="test",
            library="test-lib",
            topic="test-topic",
        )

        assert result is True
        mock_kb_cache.delete.assert_called_once()

    def test_get_stats(self, unified_cache):
        """Test getting unified cache statistics."""
        stats = unified_cache.get_stats()

        assert isinstance(stats, UnifiedCacheStats)
        assert stats.hardware_profile == "development"
        assert "caches" in stats.cache_stats or "hardware_profile" in stats.cache_stats
        assert stats.total_hits >= 0
        assert stats.total_misses >= 0

    def test_get_hardware_profile(self, unified_cache):
        """Test getting hardware profile."""
        profile = unified_cache.get_hardware_profile()

        assert profile == HardwareProfile.DEVELOPMENT

    def test_get_optimization_profile(self, unified_cache):
        """Test getting optimization profile settings."""
        profile = unified_cache.get_optimization_profile()

        assert "profile" in profile
        assert "tiered_context" in profile
        assert "context7_kb" in profile
        assert "rag_knowledge" in profile
        assert "adaptive" in profile
        assert profile["tiered_context"]["max_in_memory_entries"] == 100

    def test_hit_miss_statistics(self, unified_cache, mock_context_manager):
        """Test that hit/miss statistics are tracked correctly."""
        # Initial state
        assert unified_cache._stats["hits"] == 0
        assert unified_cache._stats["misses"] == 0

        # Cache hit
        mock_context_manager.get_context.return_value = {
            "content": "test",
            "cached": True,
        }
        unified_cache.get(
            cache_type=CacheType.TIERED_CONTEXT, key="test.py", tier=ContextTier.TIER1
        )
        assert unified_cache._stats["hits"] == 1
        assert unified_cache._stats["misses"] == 0

        # Cache miss
        mock_context_manager.get_context.return_value = None
        unified_cache.get(
            cache_type=CacheType.TIERED_CONTEXT, key="miss.py", tier=ContextTier.TIER1
        )
        assert unified_cache._stats["hits"] == 1
        assert unified_cache._stats["misses"] == 1

    def test_auto_hardware_detection(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test automatic hardware profile detection."""
        with patch(
            "tapps_agents.core.unified_cache.HardwareProfiler"
        ) as mock_profiler_class:
            mock_profiler = Mock()
            mock_profiler.detect_profile.return_value = HardwareProfile.WORKSTATION
            mock_profiler.get_optimization_profile.return_value = Mock(
                max_in_memory_entries=200, profile=HardwareProfile.WORKSTATION
            )
            mock_profiler.get_current_resource_usage.return_value = {
                "cpu": 50.0,
                "memory": 60.0,
            }
            mock_profiler_class.return_value = mock_profiler

            cache = UnifiedCache(
                cache_root=tmp_cache_root,
                context_manager=mock_context_manager,
                kb_cache=mock_kb_cache,
                knowledge_base=mock_knowledge_base,
            )

            assert cache.hardware_profile == HardwareProfile.WORKSTATION
            mock_profiler.detect_profile.assert_called_once()
