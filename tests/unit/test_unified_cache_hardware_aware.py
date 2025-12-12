"""
Hardware-aware routing tests for UnifiedCache.

Tests that cache behavior adapts correctly to different hardware profiles (NUC, Development, Workstation).
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
class TestHardwareAwareRouting:
    """Test hardware-aware cache routing and optimization."""

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
            ContextTier.TIER1: Mock(max_size=50),
            ContextTier.TIER2: Mock(max_size=50),
            ContextTier.TIER3: Mock(max_size=50),
        }
        manager.get_cache_stats.return_value = {"hits": 10, "misses": 5}
        return manager

    @pytest.fixture
    def mock_kb_cache(self):
        """Create mock KB cache."""
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
        """Create mock knowledge base."""
        kb = Mock()
        kb.search.return_value = [{"chunk": "test", "score": 0.8}]
        kb.get_context.return_value = "test context"
        kb.get_sources.return_value = []
        kb.list_all_files.return_value = []
        kb.domain = "test"
        return kb

    def test_nuc_profile_optimization(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test NUC profile uses conservative cache settings."""
        cache = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.NUC,
        )

        profile = cache.get_optimization_profile()

        assert profile["profile"] == "nuc"
        assert profile["tiered_context"]["max_in_memory_entries"] == 50
        assert profile["tiered_context"]["compression_enabled"] is True
        assert profile["tiered_context"]["hybrid_mode"] is False
        assert profile["context7_kb"]["max_cache_size_mb"] == 100

        # Verify cache sizes were updated
        assert mock_context_manager.caches[ContextTier.TIER1].max_size == 50

    def test_development_profile_optimization(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test Development profile uses balanced cache settings."""
        cache = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.DEVELOPMENT,
        )

        profile = cache.get_optimization_profile()

        assert profile["profile"] == "development"
        assert profile["tiered_context"]["max_in_memory_entries"] == 100
        assert profile["tiered_context"]["compression_enabled"] is False
        assert profile["tiered_context"]["hybrid_mode"] is True
        assert profile["context7_kb"]["max_cache_size_mb"] == 200

        # Verify cache sizes were updated
        assert mock_context_manager.caches[ContextTier.TIER1].max_size == 100

    def test_workstation_profile_optimization(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test Workstation profile uses aggressive cache settings."""
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

        # Verify cache sizes were updated
        assert mock_context_manager.caches[ContextTier.TIER1].max_size == 200

    def test_server_profile_optimization(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test Server profile uses custom cache settings."""
        cache = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.SERVER,
        )

        profile = cache.get_optimization_profile()

        assert profile["profile"] == "server"
        assert profile["tiered_context"]["max_in_memory_entries"] == 150
        assert profile["context7_kb"]["max_cache_size_mb"] == 300

    def test_hardware_profile_detection(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test automatic hardware profile detection."""
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

    def test_ttl_settings_by_profile(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test TTL settings differ by hardware profile."""
        # NUC profile
        cache_nuc = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.NUC,
        )
        profile_nuc = cache_nuc.get_optimization_profile()

        # Workstation profile
        cache_ws = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.WORKSTATION,
        )
        profile_ws = cache_ws.get_optimization_profile()

        # NUC should have shorter TTLs (more aggressive cleanup)
        assert (
            profile_nuc["tiered_context"]["tier1_ttl"]
            < profile_ws["tiered_context"]["tier1_ttl"]
        )
        assert (
            profile_nuc["tiered_context"]["tier2_ttl"]
            < profile_ws["tiered_context"]["tier2_ttl"]
        )
        assert (
            profile_nuc["tiered_context"]["tier3_ttl"]
            < profile_ws["tiered_context"]["tier3_ttl"]
        )

    def test_adaptive_settings_by_profile(
        self, tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base
    ):
        """Test adaptive settings differ by hardware profile."""
        # NUC profile
        cache_nuc = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.NUC,
        )
        profile_nuc = cache_nuc.get_optimization_profile()

        # Workstation profile
        cache_ws = UnifiedCache(
            cache_root=tmp_cache_root,
            context_manager=mock_context_manager,
            kb_cache=mock_kb_cache,
            knowledge_base=mock_knowledge_base,
            hardware_profile=HardwareProfile.WORKSTATION,
        )
        profile_ws = cache_ws.get_optimization_profile()

        # NUC should have more frequent resource checks and lower cleanup threshold
        assert (
            profile_nuc["adaptive"]["resource_check_interval"]
            < profile_ws["adaptive"]["resource_check_interval"]
        )
        assert (
            profile_nuc["adaptive"]["emergency_cleanup_threshold"]
            < profile_ws["adaptive"]["emergency_cleanup_threshold"]
        )
