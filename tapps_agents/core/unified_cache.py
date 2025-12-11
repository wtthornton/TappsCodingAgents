"""
Unified Cache - Single interface for all caching systems.
"""

from typing import Optional, Any, Dict
from pathlib import Path
from dataclasses import dataclass

from .cache_router import (
    CacheRouter, CacheType, CacheRequest, CacheResponse
)
from .context_manager import ContextManager, ContextTier
from .hardware_profiler import HardwareProfiler, HardwareProfile
from ..context7.kb_cache import KBCache
from ..context7.cache_structure import CacheStructure
from ..context7.metadata import MetadataManager
from ..experts.simple_rag import SimpleKnowledgeBase


@dataclass
class UnifiedCacheStats:
    """Unified cache statistics."""
    hardware_profile: str
    cache_stats: Dict[str, Any]
    resource_usage: Dict[str, Any]
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
        cache_root: Optional[Path] = None,
        context_manager: Optional[ContextManager] = None,
        kb_cache: Optional[KBCache] = None,
        knowledge_base: Optional[SimpleKnowledgeBase] = None,
        hardware_profile: Optional[HardwareProfile] = None
    ):
        """
        Initialize unified cache.
        
        Args:
            cache_root: Root directory for caches (defaults to .tapps-agents/kb)
            context_manager: Optional ContextManager instance
            kb_cache: Optional KBCache instance
            knowledge_base: Optional SimpleKnowledgeBase instance
            hardware_profile: Optional hardware profile (auto-detects if not provided)
        """
        self.hardware_profiler = HardwareProfiler()
        
        # Auto-detect hardware profile if not provided
        if hardware_profile:
            self.hardware_profile = hardware_profile
        else:
            self.hardware_profile = self.hardware_profiler.detect_profile()
        
        # Initialize context manager if not provided
        if context_manager is None:
            optimization_profile = self.hardware_profiler.get_optimization_profile(self.hardware_profile)
            context_manager = ContextManager(
                cache_size=optimization_profile.max_in_memory_entries
            )
        
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
            optimization_profile=self.hardware_profiler.get_optimization_profile(self.hardware_profile)
        )
        
        # Statistics tracking
        self._stats = {
            "hits": 0,
            "misses": 0
        }
    
    def get(
        self,
        cache_type: CacheType,
        key: str,
        namespace: Optional[str] = None,
        tier: Optional[ContextTier] = None,
        library: Optional[str] = None,
        topic: Optional[str] = None,
        domain: Optional[str] = None,
        query: Optional[str] = None,
        include_related: bool = False,
        **kwargs: Any
    ) -> Optional[CacheResponse]:
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
            **kwargs
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
        namespace: Optional[str] = None,
        tier: Optional[ContextTier] = None,
        library: Optional[str] = None,
        topic: Optional[str] = None,
        ttl: Optional[int] = None,
        **kwargs: Any
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
            **kwargs
        )
        
        return self.router.route_put(request, value)
    
    def invalidate(
        self,
        cache_type: CacheType,
        key: str,
        namespace: Optional[str] = None,
        tier: Optional[ContextTier] = None,
        library: Optional[str] = None,
        topic: Optional[str] = None
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
            topic=topic
        )
        
        return self.router.route_invalidate(request)
    
    def get_stats(self) -> UnifiedCacheStats:
        """
        Get unified cache statistics.
        
        Returns:
            UnifiedCacheStats instance
        """
        cache_stats = self.router.get_all_stats()
        resource_usage = self.hardware_profiler.get_current_resource_usage()
        
        return UnifiedCacheStats(
            hardware_profile=self.hardware_profile.value,
            cache_stats=cache_stats,
            resource_usage=resource_usage,
            total_hits=self._stats["hits"],
            total_misses=self._stats["misses"]
        )
    
    def get_hardware_profile(self) -> HardwareProfile:
        """Get detected hardware profile."""
        return self.hardware_profile
    
    def get_optimization_profile(self) -> Dict[str, Any]:
        """Get current optimization profile settings."""
        profile = self.hardware_profiler.get_optimization_profile(self.hardware_profile)
        return {
            "profile": profile.profile.value,
            "tiered_context": {
                "tier1_ttl": profile.tier1_ttl,
                "tier2_ttl": profile.tier2_ttl,
                "tier3_ttl": profile.tier3_ttl,
                "max_in_memory_entries": profile.max_in_memory_entries,
                "hybrid_mode": profile.hybrid_mode,
                "compression_enabled": profile.compression_enabled
            },
            "context7_kb": {
                "max_cache_size_mb": profile.max_cache_size_mb,
                "pre_populate": profile.pre_populate,
                "auto_refresh": profile.auto_refresh
            },
            "rag_knowledge": {
                "index_on_startup": profile.index_on_startup,
                "max_knowledge_files": profile.max_knowledge_files
            },
            "adaptive": {
                "enabled": profile.enable_adaptive,
                "resource_check_interval": profile.resource_check_interval,
                "emergency_cleanup_threshold": profile.emergency_cleanup_threshold
            }
        }


# Convenience function to create a default UnifiedCache instance
def create_unified_cache(
    cache_root: Optional[Path] = None,
    hardware_profile: Optional[HardwareProfile] = None
) -> UnifiedCache:
    """
    Create a default UnifiedCache instance with auto-detection.
    
    Args:
        cache_root: Optional root directory for caches
        hardware_profile: Optional hardware profile (auto-detects if not provided)
    
    Returns:
        UnifiedCache instance
    """
    return UnifiedCache(
        cache_root=cache_root,
        hardware_profile=hardware_profile
    )

