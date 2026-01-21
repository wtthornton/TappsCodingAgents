"""
UnifiedCache optimization profile tests.

Hardware taxonomy (NUC, development, server) removed; all profiles use
workstation-like settings. These tests assert the unified behavior.
"""

from unittest.mock import Mock, patch

import pytest

from tapps_agents.core.context_manager import ContextManager, ContextTier
from tapps_agents.core.hardware_profiler import (
    CacheOptimizationProfile,
    HardwareProfile,
)
from tapps_agents.core.unified_cache import UnifiedCache


@pytest.mark.unit
class TestUnifiedCacheOptimizationProfile:
    """Test cache optimization profile (workstation-like default)."""

    @pytest.fixture
    def tmp_cache_root(self, tmp_path):
        cache_root = tmp_path / ".tapps-agents" / "kb"
        cache_root.mkdir(parents=True, exist_ok=True)
        return cache_root

    @pytest.fixture
    def mock_context_manager(self):
        manager = Mock(spec=ContextManager)
        manager.get_context.return_value = {
            "content": "test context",
            "cached": True,
            "token_estimate": 100,
        }
        manager.caches = {
            ContextTier.TIER1: Mock(max_size=50),
            ContextTier.TIER2: Mock(max_size=50),
            ContextTier.TIER3: Mock(max_size=50),
        }
        manager.get_cache_stats.return_value = {"hits": 10, "misses": 5}
        return manager

    @pytest.fixture
    def mock_kb_cache(self):
        cache = Mock()
        cache.get.return_value = Mock(
            content="test",
            context7_id="id",
            trust_score=0.9,
            token_count=100,
            cache_hits=1,
        )
        cache.store.return_value = Mock(content="stored", token_count=100)
        cache.delete.return_value = True
        cache.metadata_manager = Mock()
        cache.metadata_manager.load_cache_index.return_value = Mock(libraries={})
        return cache

    @pytest.fixture
    def mock_knowledge_base(self):
        kb = Mock()
        kb.search.return_value = [{"chunk": "test", "score": 0.8}]
        kb.get_context.return_value = "test context"
        kb.get_sources.return_value = []
        kb.list_all_files.return_value = []
        kb.domain = "test"
        return kb

    def test_workstation_like_profile(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """All profiles use workstation-like cache settings."""
        cache = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.WORKSTATION,
        )
        profile = cache.get_optimization_profile()

        assert profile["profile"] == "workstation"
        assert profile["tiered_context"]["max_in_memory_entries"] == 200
        assert profile["tiered_context"]["compression_enabled"] is False
        assert profile["tiered_context"]["hybrid_mode"] is True
        assert profile["context7_kb"]["max_cache_size_mb"] == 500
        assert mock_context_manager.caches[ContextTier.TIER1].max_size == 200

    def test_hardware_profile_detection(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Detection returns WORKSTATION (taxonomy removed)."""
        with patch(
            "tapps_agents.core.unified_cache.HardwareProfiler"
        ) as mock_profiler_class:
            mock_profiler = Mock()
            mock_profiler.detect_profile.return_value = HardwareProfile.WORKSTATION
            mock_profiler.get_optimization_profile.return_value = (
                CacheOptimizationProfile(
                    profile=HardwareProfile.WORKSTATION,
                    tier1_ttl=600,
                    tier2_ttl=300,
                    tier3_ttl=120,
                    max_in_memory_entries=200,
                    hybrid_mode=True,
                    compression_enabled=False,
                    max_cache_size_mb=500,
                    pre_populate=True,
                    auto_refresh=True,
                    index_on_startup=True,
                    max_knowledge_files=1000,
                    enable_adaptive=True,
                    resource_check_interval=120,
                    emergency_cleanup_threshold=0.85,
                )
            )
            mock_profiler.get_current_resource_usage.return_value = {
                "cpu": 30.0,
                "memory": 50.0,
            }
            mock_profiler_class.return_value = mock_profiler

            cache = UnifiedCache(
                cache_root=tmp_cache_root,
                context_manager=mock_context_manager,
                kb_cache=mock_kb_cache,
                knowledge_base=mock_knowledge_base,
            )
            assert cache.get_hardware_profile() == HardwareProfile.WORKSTATION
            mock_profiler.detect_profile.assert_called_once()
