"""
Unified Cache - Single interface for all caching systems.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..context7.cache_structure import CacheStructure
from ..context7.kb_cache import KBCache
from ..context7.metadata import MetadataManager
from .adaptive_cache_config import AdaptiveCacheConfig
from .cache_router import CacheRequest, CacheResponse, CacheRouter, CacheType
from .context_manager import ContextManager, ContextTier
from .hardware_profiler import HardwareProfile, HardwareProfiler

if TYPE_CHECKING:
    from ..experts.simple_rag import SimpleKnowledgeBase

logger = logging.getLogger(__name__)


@dataclass
class UnifiedCacheStats:
    """Unified cache statistics."""

    hardware_profile: str
    cache_stats: dict[str, Any]
    resource_usage: dict[str, Any]
    total_hits: int = 0
    total_misses: int = 0


class UnifiedCache:
    """
    Unified cache interface for all caching systems.

    Provides a single API for:
    - Tiered Context Cache
    - Context7 KB Cache
    - RAG Knowledge Base
    """

    def __init__(
        self,
        cache_root: Path | None = None,
        context_manager: ContextManager | None = None,
        kb_cache: KBCache | None = None,
        knowledge_base: SimpleKnowledgeBase | None = None,
        hardware_profile: HardwareProfile | None = None,
        adaptive_config: AdaptiveCacheConfig | None = None,
        enable_adaptive: bool = True,
    ):
        """
        Initialize unified cache.

        Args:
            cache_root: Root directory for caches (defaults to .tapps-agents/kb)
            context_manager: Optional ContextManager instance
            kb_cache: Optional KBCache instance
            knowledge_base: Optional SimpleKnowledgeBase instance
            hardware_profile: Optional hardware profile (auto-detects if not provided)
            adaptive_config: Optional AdaptiveCacheConfig instance (creates default if enable_adaptive=True)
            enable_adaptive: Whether to enable adaptive configuration (default: True)
        """
        self.hardware_profiler = HardwareProfiler()
        self.adaptive_config: AdaptiveCacheConfig | None = None
        base_profile = None

        # Auto-detect hardware profile if not provided
        if hardware_profile:
            self.hardware_profile = hardware_profile
        else:
            self.hardware_profile = self.hardware_profiler.detect_profile()
        base_profile = self.hardware_profiler.get_optimization_profile(
            self.hardware_profile
        )

        # Initialize adaptive configuration if enabled
        if enable_adaptive:
            if adaptive_config is None:
                adaptive_config = AdaptiveCacheConfig(
                    hardware_profiler=self.hardware_profiler,
                    hardware_profile=self.hardware_profile,
                    check_interval=base_profile.resource_check_interval,
                )
            self.adaptive_config = adaptive_config
        else:
            self.adaptive_config = None

        # Determine cache sizing based on adaptive or base profile
        if self.adaptive_config:
            settings = self.adaptive_config.get_current_settings()
            cache_size = settings.max_in_memory_entries
        else:
            cache_size = base_profile.max_in_memory_entries

        # Initialize context manager if not provided
        if context_manager is None:
            context_manager = ContextManager(cache_size=cache_size)
        else:
            # If a context manager is provided (often mocked in tests), apply sizing to its tier caches if present.
            try:
                caches = getattr(context_manager, "caches", None)
                if isinstance(caches, dict):
                    for tier_cache in caches.values():
                        if hasattr(tier_cache, "max_size"):
                            tier_cache.max_size = cache_size
            except Exception:
                # Best-effort only; never fail initialization because a mock doesn't behave like a real ContextManager.
                logger.debug("Failed to apply cache sizing to provided context_manager")

        # Initialize KB cache if not provided
        if kb_cache is None:
            if cache_root is None:
                cache_root = Path(".tapps-agents/kb/context7-cache")
            else:
                cache_root = Path(cache_root) / "context7-cache"

            cache_structure = CacheStructure(cache_root)
            metadata_manager = MetadataManager(cache_structure)
            kb_cache = KBCache(cache_root, metadata_manager)

        # Initialize cache router
        self.router = CacheRouter(
            context_manager=context_manager,
            kb_cache=kb_cache,
            knowledge_base=knowledge_base,
            optimization_profile=base_profile,
        )

        # Statistics tracking
        self._stats = {"hits": 0, "misses": 0}

    def get(
        self,
        cache_type: CacheType,
        key: str,
        namespace: str | None = None,
        tier: ContextTier | None = None,
        library: str | None = None,
        topic: str | None = None,
        domain: str | None = None,
        query: str | None = None,
        include_related: bool = False,
        **kwargs: Any,
    ) -> CacheResponse | None:
        """
        Get cached entry.

        Args:
            cache_type: Type of cache (TIERED_CONTEXT, CONTEXT7_KB, RAG_KNOWLEDGE)
            key: Cache key (file path for tiered context, etc.)
            namespace: Optional namespace (for future use)
            tier: Context tier (for TIERED_CONTEXT)
            library: Library name (for CONTEXT7_KB)
            topic: Topic name (for CONTEXT7_KB)
            domain: Domain name (for RAG_KNOWLEDGE)
            query: Search query (for RAG_KNOWLEDGE)
            include_related: Include related files (for TIERED_CONTEXT)
            **kwargs: Additional cache-specific parameters

        Returns:
            CacheResponse if found, None otherwise
        """
        request = CacheRequest(
            cache_type=cache_type,
            key=key,
            namespace=namespace,
            tier=tier,
            library=library,
            topic=topic,
            domain=domain,
            query=query,
            include_related=include_related,
            **kwargs,
        )

        response = self.router.route_get(request)

        if response:
            self._stats["hits"] += 1
        else:
            self._stats["misses"] += 1

        return response

    def put(
        self,
        cache_type: CacheType,
        key: str,
        value: Any,
        namespace: str | None = None,
        tier: ContextTier | None = None,
        library: str | None = None,
        topic: str | None = None,
        ttl: int | None = None,
        **kwargs: Any,
    ) -> CacheResponse:
        """
        Store entry in cache.

        Args:
            cache_type: Type of cache
            key: Cache key
            value: Value to cache
            namespace: Optional namespace
            tier: Context tier (for TIERED_CONTEXT)
            library: Library name (for CONTEXT7_KB)
            topic: Topic name (for CONTEXT7_KB)
            ttl: Time-to-live in seconds (for future use)
            **kwargs: Additional cache-specific parameters

        Returns:
            CacheResponse with stored data
        """
        request = CacheRequest(
            cache_type=cache_type,
            key=key,
            namespace=namespace,
            tier=tier,
            library=library,
            topic=topic,
            **kwargs,
        )

        return self.router.route_put(request, value)

    def invalidate(
        self,
        cache_type: CacheType,
        key: str,
        namespace: str | None = None,
        tier: ContextTier | None = None,
        library: str | None = None,
        topic: str | None = None,
    ) -> bool:
        """
        Invalidate cached entry.

        Args:
            cache_type: Type of cache
            key: Cache key
            namespace: Optional namespace
            tier: Context tier (for TIERED_CONTEXT)
            library: Library name (for CONTEXT7_KB)
            topic: Topic name (for CONTEXT7_KB)

        Returns:
            True if invalidated successfully
        """
        request = CacheRequest(
            cache_type=cache_type,
            key=key,
            namespace=namespace,
            tier=tier,
            library=library,
            topic=topic,
        )

        return self.router.route_invalidate(request)

    def get_stats(self) -> UnifiedCacheStats:
        """
        Get unified cache statistics.

        Returns:
            UnifiedCacheStats instance
        """
        # Check and adjust adaptive configuration if enabled
        if self.adaptive_config:
            self.adaptive_config.check_and_adjust()

        cache_stats = self.router.get_all_stats()
        resource_usage = self.hardware_profiler.get_current_resource_usage()

        return UnifiedCacheStats(
            hardware_profile=self.hardware_profile.value,
            cache_stats=cache_stats,
            resource_usage=resource_usage,
            total_hits=self._stats["hits"],
            total_misses=self._stats["misses"],
        )

    def get_hardware_profile(self) -> HardwareProfile:
        """Get detected hardware profile."""
        return self.hardware_profile

    def get_optimization_profile(self) -> dict[str, Any]:
        """Get current optimization profile settings."""
        # Use adaptive settings if available, otherwise use base profile
        if self.adaptive_config:
            settings = self.adaptive_config.get_current_settings()
            return {
                "profile": self.hardware_profile.value,
                "adaptive_enabled": True,
                "tiered_context": {
                    "tier1_ttl": settings.tier1_ttl,
                    "tier2_ttl": settings.tier2_ttl,
                    "tier3_ttl": settings.tier3_ttl,
                    "max_in_memory_entries": settings.max_in_memory_entries,
                    "hybrid_mode": settings.hybrid_mode,
                    "compression_enabled": settings.compression_enabled,
                },
                "context7_kb": {
                    "max_cache_size_mb": settings.max_cache_size_mb,
                    "pre_populate": settings.pre_populate,
                    "auto_refresh": settings.auto_refresh,
                },
                "rag_knowledge": {
                    "index_on_startup": settings.index_on_startup,
                    "max_knowledge_files": settings.max_knowledge_files,
                },
                "adaptive": {
                    "enabled": True,
                    "resource_check_interval": settings.resource_check_interval,
                    "emergency_cleanup_threshold": settings.emergency_cleanup_threshold,
                },
                "adaptive_behavior": {
                    "background_indexing_enabled": settings.background_indexing_enabled,
                    "cache_warming_enabled": settings.cache_warming_enabled,
                    "emergency_cleanup_active": settings.emergency_cleanup_active,
                },
            }
        else:
            profile = self.hardware_profiler.get_optimization_profile(
                self.hardware_profile
            )
            return {
                "profile": profile.profile.value,
                "adaptive_enabled": False,
                "tiered_context": {
                    "tier1_ttl": profile.tier1_ttl,
                    "tier2_ttl": profile.tier2_ttl,
                    "tier3_ttl": profile.tier3_ttl,
                    "max_in_memory_entries": profile.max_in_memory_entries,
                    "hybrid_mode": profile.hybrid_mode,
                    "compression_enabled": profile.compression_enabled,
                },
                "context7_kb": {
                    "max_cache_size_mb": profile.max_cache_size_mb,
                    "pre_populate": profile.pre_populate,
                    "auto_refresh": profile.auto_refresh,
                },
                "rag_knowledge": {
                    "index_on_startup": profile.index_on_startup,
                    "max_knowledge_files": profile.max_knowledge_files,
                },
                "adaptive": {
                    "enabled": profile.enable_adaptive,
                    "resource_check_interval": profile.resource_check_interval,
                    "emergency_cleanup_threshold": profile.emergency_cleanup_threshold,
                },
            }

    def get_adaptive_status(self) -> dict[str, Any] | None:
        """
        Get adaptive configuration status.

        Returns:
            Dictionary with adaptive status or None if adaptive config is disabled
        """
        if self.adaptive_config:
            return self.adaptive_config.get_status()
        return None


# Convenience function to create a default UnifiedCache instance
def create_unified_cache(
    cache_root: Path | None = None,
    hardware_profile: HardwareProfile | None = None,
) -> UnifiedCache:
    """
    Create a default UnifiedCache instance with auto-detection.

    Args:
        cache_root: Optional root directory for caches
        hardware_profile: Optional hardware profile (auto-detects if not provided)

    Returns:
        UnifiedCache instance
    """
    return UnifiedCache(cache_root=cache_root, hardware_profile=hardware_profile)
