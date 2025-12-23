"""
KB-First Lookup - Context7 documentation lookup with KB-first caching.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .fuzzy_matcher import FuzzyMatcher
from .kb_cache import CacheEntry, KBCache

if TYPE_CHECKING:
    from ..mcp.gateway import MCPGateway


logger = logging.getLogger(__name__)


@dataclass
class LookupResult:
    """Result from KB-first lookup."""

    success: bool
    content: str | None = None
    source: str = "cache"  # "cache", "api", "fuzzy_match"
    library: str | None = None
    topic: str | None = None
    context7_id: str | None = None
    cached_entry: CacheEntry | None = None
    error: str | None = None
    response_time_ms: float = 0.0
    fuzzy_score: float | None = None
    matched_topic: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "content": self.content,
            "source": self.source,
            "library": self.library,
            "topic": self.topic,
            "context7_id": self.context7_id,
            "error": self.error,
            "response_time_ms": self.response_time_ms,
            "fuzzy_score": self.fuzzy_score,
            "matched_topic": self.matched_topic,
        }


class KBLookup:
    """KB-first lookup workflow for Context7 documentation."""

    def __init__(
        self,
        kb_cache: KBCache,
        mcp_gateway: MCPGateway | None = None,
        resolve_library_func: Callable[[str], Any] | None = None,
        get_docs_func: Callable[[str, str | None], Any] | None = None,
        fuzzy_threshold: float = 0.7,
    ):
        """
        Initialize KB-first lookup.

        Args:
            kb_cache: KBCache instance
            mcp_gateway: Optional MCPGateway instance (used if provided)
            resolve_library_func: Optional function to resolve library name to Context7 ID (via MCP)
            get_docs_func: Optional function to get docs from Context7 API (via MCP)
            fuzzy_threshold: Fuzzy matching threshold (0.0-1.0)
        """
        self.kb_cache = kb_cache
        self.mcp_gateway = mcp_gateway
        self.resolve_library_func = resolve_library_func
        self.get_docs_func = get_docs_func
        self.fuzzy_matcher = FuzzyMatcher(threshold=fuzzy_threshold)

    async def lookup(
        self, library: str, topic: str | None = None, use_fuzzy_match: bool = False
    ) -> LookupResult:
        """
        Perform KB-first lookup for library documentation.

        Workflow:
        1. Check KB cache (exact match)
        2. If miss and fuzzy enabled: Try fuzzy matching (Phase 2)
        3. If still miss: Resolve library ID (if needed)
        4. If still miss: Fetch from Context7 API
        5. Store in cache

        Args:
            library: Library name
            topic: Optional topic name
            use_fuzzy_match: Whether to use fuzzy matching (Phase 2 feature)

        Returns:
            LookupResult with documentation content
        """
        start_time = datetime.now(UTC)

        # Default topic if not provided
        if topic is None:
            topic = "overview"

        # Step 1: Check KB cache (exact match)
        cached_entry = self.kb_cache.get(library, topic)
        if cached_entry:
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            # R4: Record cache hit with latency
            from .analytics import Analytics
            from .metadata import MetadataManager
            analytics = Analytics(
                self.kb_cache.cache_structure,
                MetadataManager(self.kb_cache.cache_structure)
            )
            analytics.record_cache_hit(response_time_ms=response_time)
            return LookupResult(
                success=True,
                content=cached_entry.content,
                source="cache",
                library=library,
                topic=topic,
                context7_id=cached_entry.context7_id,
                cached_entry=cached_entry,
                response_time_ms=response_time,
            )

        # Step 2: Fuzzy matching (Phase 2)
        if use_fuzzy_match:
            # Get available entries from cache index
            from .metadata import MetadataManager

            metadata_manager = MetadataManager(self.kb_cache.cache_structure)
            index = metadata_manager.load_cache_index()

            # Build list of available entries
            available_entries = []
            for lib_name, lib_data in index.libraries.items():
                topics = lib_data.get("topics", {})
                for topic_name in topics.keys():
                    available_entries.append((lib_name, topic_name))

            # Try fuzzy matching
            fuzzy_matches = self.fuzzy_matcher.find_matching_entry(
                library_query=library,
                topic_query=topic,
                available_entries=available_entries,
                max_results=1,
            )

            if fuzzy_matches:
                best_match = fuzzy_matches[0]
                # Try to get the matched entry from cache
                fuzzy_entry = self.kb_cache.get(best_match.library, best_match.topic)
                if fuzzy_entry:
                    response_time = (
                        datetime.now(UTC) - start_time
                    ).total_seconds() * 1000
                    # R4: Record fuzzy match with latency
                    from .analytics import Analytics
                    from .metadata import MetadataManager
                    analytics = Analytics(
                        self.kb_cache.cache_structure,
                        MetadataManager(self.kb_cache.cache_structure)
                    )
                    analytics.record_fuzzy_match()
                    analytics.record_cache_hit(response_time_ms=response_time)
                    return LookupResult(
                        success=True,
                        content=fuzzy_entry.content,
                        source="fuzzy_match",
                        library=best_match.library,
                        topic=best_match.topic,
                        context7_id=fuzzy_entry.context7_id,
                        cached_entry=fuzzy_entry,
                        response_time_ms=response_time,
                        fuzzy_score=best_match.score,
                        matched_topic=best_match.topic,
                    )

        # R4: Record cache miss before API call
        from .analytics import Analytics
        from .metadata import MetadataManager
        analytics = Analytics(
            self.kb_cache.cache_structure,
            MetadataManager(self.kb_cache.cache_structure)
        )
        analytics.record_cache_miss()

        # Step 3: Resolve library ID if needed
        context7_id = None

        # Use backup client with automatic fallback (MCP Gateway -> HTTP)
        from .backup_client import call_context7_resolve_with_fallback

        try:
            resolve_result = await call_context7_resolve_with_fallback(
                library, self.mcp_gateway
            )
            if resolve_result.get("success"):
                matches = resolve_result.get("result", {}).get("matches", [])
                if matches and len(matches) > 0:
                    context7_id = (
                        matches[0].get("id")
                        if isinstance(matches[0], dict)
                        else str(matches[0])
                    )
            elif "quota exceeded" in resolve_result.get("error", "").lower():
                # R3: Quota exceeded - clear error message with actionable guidance
                error_msg = resolve_result.get("error", "Context7 API quota exceeded")
                logger.warning(
                    f"Context7 API quota exceeded for library '{library}' (topic: {topic}): {error_msg}. "
                    f"Consider upgrading your Context7 plan or waiting for quota reset. "
                    f"Continuing without Context7 documentation."
                )
                response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
                return LookupResult(
                    success=False,
                    source="api",
                    library=library,
                    topic=topic,
                    error=f"Context7 API quota exceeded: {error_msg}. Consider upgrading your plan or waiting for quota reset.",
                    response_time_ms=response_time,
                )
            else:
                # R3: Context7 unavailable - distinguish between different error types
                error_msg = resolve_result.get("error", "Context7 not available")
                if "not configured" in error_msg.lower() or "not found" in error_msg.lower():
                    # Not configured - provide setup instructions
                    logger.info(
                        f"Context7 not configured for library '{library}' (topic: {topic}): {error_msg}. "
                        f"To enable Context7, set CONTEXT7_API_KEY or configure MCP server. "
                        f"Continuing without Context7 documentation."
                    )
                elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                    # Network error
                    logger.warning(
                        f"Context7 network error for library '{library}' (topic: {topic}): {error_msg}. "
                        f"Check your network connection. Continuing without Context7 documentation."
                    )
                else:
                    # Generic unavailable
                    logger.info(
                        f"Context7 not available for library '{library}' (topic: {topic}): {error_msg}. "
                        f"Continuing without Context7 documentation."
                    )
        except Exception as e:
            # Continue without context7_id if resolution fails
            logger.warning(
                f"Failed to resolve Context7 library id for '{library}' (topic: {topic}): {e}. "
                f"Continuing without Context7 documentation.",
                exc_info=True
            )

        # Step 4: Fetch from Context7 API
        if context7_id:
            content = None

            # Use backup client with automatic fallback (MCP Gateway -> HTTP)
            from .backup_client import call_context7_get_docs_with_fallback

            try:
                api_result = await call_context7_get_docs_with_fallback(
                    context7_id, topic, mode="code", page=1, mcp_gateway=self.mcp_gateway
                )
                # R4: Record API call
                analytics.record_api_call()
                if api_result.get("success"):
                    result_data = api_result.get("result", {})
                    content = (
                        result_data.get("content")
                        if isinstance(result_data, dict)
                        else result_data
                    )
                else:
                    # Context7 unavailable - log and continue
                    error_msg = api_result.get("error", "Context7 not available")
                    logger.info(
                        f"Context7 not available for library '{library}' (topic: {topic}): {error_msg}. "
                        f"Continuing without Context7 documentation."
                    )
                    content = None
            except Exception as e:
                # R4: Still record API call attempt
                analytics.record_api_call()
                logger.warning(
                    f"Failed to fetch Context7 docs for library '{library}' (topic: {topic}): {e}. "
                    f"Continuing without Context7 documentation.",
                    exc_info=True
                )
                content = None

            # Step 5: Store in cache if we got content
            if content:
                cached_entry = self.kb_cache.store(
                    library=library,
                    topic=topic,
                    content=content,
                    context7_id=context7_id,
                )

                response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
                # R4: Record latency for API call (already recorded API call above)
                if response_time > 0:
                    analytics.record_cache_hit(response_time_ms=response_time)  # Reuse method to record latency
                return LookupResult(
                    success=True,
                    content=content,
                    source="api",
                    library=library,
                    topic=topic,
                    context7_id=context7_id,
                    cached_entry=cached_entry,
                    response_time_ms=response_time,
                )

        # If we reach here, lookup failed
        response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        error_msg = "No documentation found in cache or API unavailable"
        logger.info(
            f"Context7 lookup failed for library '{library}' (topic: {topic}): {error_msg}. "
            f"Continuing without Context7 documentation."
        )
        return LookupResult(
            success=False,
            source="cache",
            library=library,
            topic=topic,
            error=error_msg,
            response_time_ms=response_time,
        )
