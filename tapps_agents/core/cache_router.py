"""
Cache Router - Routes cache requests to appropriate cache adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from ..context7.kb_cache import KBCache
from .context_manager import ContextManager, ContextTier
from .hardware_profiler import CacheOptimizationProfile, HardwareProfiler

if TYPE_CHECKING:
    from ..experts.simple_rag import SimpleKnowledgeBase


class CacheType(Enum):
    """Cache type enumeration."""

    TIERED_CONTEXT = "tiered_context"
    CONTEXT7_KB = "context7_kb"
    RAG_KNOWLEDGE = "rag_knowledge"


@dataclass
class CacheRequest:
    """Cache request parameters."""

    cache_type: CacheType
    key: str
    namespace: str | None = None
    tier: ContextTier | None = None
    library: str | None = None
    topic: str | None = None
    domain: str | None = None
    query: str | None = None
    include_related: bool = False
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheResponse:
    """Cache response with metadata."""

    data: Any
    cached: bool
    cache_type: CacheType
    metadata: dict[str, Any] | None = None


class CacheAdapter(Protocol):
    """Protocol for cache adapters."""

    def get(self, request: CacheRequest) -> CacheResponse | None:
        """Get cached entry."""
        ...

    def put(self, request: CacheRequest, value: Any) -> CacheResponse:
        """Store entry in cache."""
        ...

    def invalidate(self, request: CacheRequest) -> bool:
        """Invalidate cached entry."""
        ...

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        ...


class TieredContextAdapter:
    """Adapter for Tiered Context Cache."""

    def __init__(
        self,
        context_manager: ContextManager,
        optimization_profile: CacheOptimizationProfile,
    ):
        self.context_manager = context_manager
        self.optimization_profile = optimization_profile

        # Update cache sizes based on optimization profile
        for tier in ContextTier:
            cache = self.context_manager.caches[tier]
            cache.max_size = self.optimization_profile.max_in_memory_entries

    def get(self, request: CacheRequest) -> CacheResponse | None:
        """Get tiered context from cache."""
        if not request.tier:
            return None

        file_path = Path(request.key)
        context = self.context_manager.get_context(
            file_path=file_path,
            tier=request.tier,
            include_related=request.include_related,
            use_cache=True,
        )

        if context:
            return CacheResponse(
                data=context,
                cached=context.get("cached", False),
                cache_type=CacheType.TIERED_CONTEXT,
                metadata={
                    "tier": request.tier.value,
                    "file": str(file_path),
                    "token_estimate": context.get("token_estimate", 0),
                },
            )
        return None

    def put(self, request: CacheRequest, value: Any) -> CacheResponse:
        """Store tiered context in cache."""
        # Tiered context cache is write-through via get_context
        # This is mainly for compatibility
        if request.tier:
            file_path = Path(request.key)
            context = self.context_manager.get_context(
                file_path=file_path,
                tier=request.tier,
                include_related=request.include_related,
                use_cache=True,
            )
            return CacheResponse(
                data=context, cached=False, cache_type=CacheType.TIERED_CONTEXT
            )
        return CacheResponse(
            data=value, cached=False, cache_type=CacheType.TIERED_CONTEXT
        )

    def invalidate(self, request: CacheRequest) -> bool:
        """Invalidate tiered context cache."""
        if request.tier:
            self.context_manager.clear_cache(tier=request.tier)
        else:
            self.context_manager.clear_cache()
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get tiered context cache statistics."""
        return self.context_manager.get_cache_stats()


class Context7KBAdapter:
    """Adapter for Context7 KB Cache."""

    def __init__(
        self, kb_cache: KBCache, optimization_profile: CacheOptimizationProfile
    ):
        self.kb_cache = kb_cache
        self.optimization_profile = optimization_profile

    def get(self, request: CacheRequest) -> CacheResponse | None:
        """Get Context7 KB entry from cache."""
        if not request.library or not request.topic:
            return None

        entry = self.kb_cache.get(request.library, request.topic)

        if entry:
            return CacheResponse(
                data=entry.content,
                cached=True,
                cache_type=CacheType.CONTEXT7_KB,
                metadata={
                    "library": request.library,
                    "topic": request.topic,
                    "context7_id": entry.context7_id,
                    "trust_score": entry.trust_score,
                    "token_count": entry.token_count,
                    "cache_hits": entry.cache_hits,
                },
            )
        return None

    def put(self, request: CacheRequest, value: Any) -> CacheResponse:
        """Store Context7 KB entry in cache."""
        if not request.library or not request.topic:
            return CacheResponse(
                data=value, cached=False, cache_type=CacheType.CONTEXT7_KB
            )

        entry = self.kb_cache.store(
            library=request.library,
            topic=request.topic,
            content=str(value),
            context7_id=request.kwargs.get("context7_id"),
            trust_score=request.kwargs.get("trust_score"),
            snippet_count=request.kwargs.get("snippet_count"),
        )

        return CacheResponse(
            data=entry.content,
            cached=False,
            cache_type=CacheType.CONTEXT7_KB,
            metadata={
                "library": request.library,
                "topic": request.topic,
                "token_count": entry.token_count,
            },
        )

    def invalidate(self, request: CacheRequest) -> bool:
        """Invalidate Context7 KB entry."""
        if not request.library:
            return False

        return self.kb_cache.delete(library=request.library, topic=request.topic)

    def get_stats(self) -> dict[str, Any]:
        """Get Context7 KB cache statistics."""
        # Get stats from metadata manager if available
        try:
            index = self.kb_cache.metadata_manager.load_cache_index()
            return {
                "total_libraries": len(index.libraries),
                "total_entries": sum(
                    len(lib.get("topics", {})) for lib in index.libraries.values()
                ),
            }
        except Exception:
            return {"status": "available"}


class RAGKnowledgeAdapter:
    """Adapter for RAG Knowledge Base."""

    def __init__(
        self,
        knowledge_base: SimpleKnowledgeBase,
        optimization_profile: CacheOptimizationProfile,
    ):
        self.knowledge_base = knowledge_base
        self.optimization_profile = optimization_profile

    def get(self, request: CacheRequest) -> CacheResponse | None:
        """Get RAG knowledge from cache."""
        if not request.query:
            return None

        chunks = self.knowledge_base.search(
            query=request.query,
            max_results=request.kwargs.get("max_results", 5),
            context_lines=request.kwargs.get("context_lines", 10),
        )

        if chunks:
            # Return formatted context
            context = self.knowledge_base.get_context(
                query=request.query, max_length=request.kwargs.get("max_length", 2000)
            )

            return CacheResponse(
                data=context,
                cached=True,  # Knowledge base is always "cached" (file-based)
                cache_type=CacheType.RAG_KNOWLEDGE,
                metadata={
                    "query": request.query,
                    "chunks_found": len(chunks),
                    "sources": self.knowledge_base.get_sources(request.query),
                },
            )
        return None

    def put(self, request: CacheRequest, value: Any) -> CacheResponse:
        """RAG knowledge base is read-only (file-based)."""
        # Knowledge base is file-based and read-only from cache perspective
        return CacheResponse(
            data=value, cached=False, cache_type=CacheType.RAG_KNOWLEDGE
        )

    def invalidate(self, request: CacheRequest) -> bool:
        """RAG knowledge base doesn't support invalidation (file-based)."""
        # Could reload files, but typically not needed
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get RAG knowledge base statistics."""
        try:
            files = self.knowledge_base.list_all_files()
            return {"total_files": len(files), "domain": self.knowledge_base.domain}
        except Exception:
            return {"status": "available"}


class CacheRouter:
    """Routes cache requests to appropriate cache adapters."""

    def __init__(
        self,
        context_manager: ContextManager | None = None,
        kb_cache: KBCache | None = None,
        knowledge_base: SimpleKnowledgeBase | None = None,
        optimization_profile: CacheOptimizationProfile | None = None,
    ):
        self.hardware_profiler = HardwareProfiler()
        self.optimization_profile = (
            optimization_profile or self.hardware_profiler.get_optimization_profile()
        )

        # Initialize adapters
        self.adapters: dict[CacheType, CacheAdapter] = {}

        if context_manager:
            self.adapters[CacheType.TIERED_CONTEXT] = TieredContextAdapter(
                context_manager, self.optimization_profile
            )

        if kb_cache:
            self.adapters[CacheType.CONTEXT7_KB] = Context7KBAdapter(
                kb_cache, self.optimization_profile
            )

        if knowledge_base:
            self.adapters[CacheType.RAG_KNOWLEDGE] = RAGKnowledgeAdapter(
                knowledge_base, self.optimization_profile
            )

    def get_adapter(self, cache_type: CacheType) -> CacheAdapter | None:
        """Get adapter for cache type."""
        return self.adapters.get(cache_type)

    def route_get(self, request: CacheRequest) -> CacheResponse | None:
        """Route get request to appropriate adapter."""
        adapter = self.get_adapter(request.cache_type)
        if adapter:
            return adapter.get(request)
        return None

    def route_put(self, request: CacheRequest, value: Any) -> CacheResponse:
        """Route put request to appropriate adapter."""
        adapter = self.get_adapter(request.cache_type)
        if adapter:
            return adapter.put(request, value)

        # Fallback response if no adapter
        return CacheResponse(data=value, cached=False, cache_type=request.cache_type)

    def route_invalidate(self, request: CacheRequest) -> bool:
        """Route invalidate request to appropriate adapter."""
        adapter = self.get_adapter(request.cache_type)
        if adapter:
            return adapter.invalidate(request)
        return False

    def get_all_stats(self) -> dict[str, Any]:
        """Get statistics from all adapters."""
        caches: dict[str, Any] = {}
        stats: dict[str, Any] = {
            "hardware_profile": self.optimization_profile.profile.value,
            "caches": caches,
        }

        for cache_type, adapter in self.adapters.items():
            caches[cache_type.value] = adapter.get_stats()

        return stats
