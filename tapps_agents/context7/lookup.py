"""
KB-First Lookup - Context7 documentation lookup with KB-first caching.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .fuzzy_matcher import FuzzyMatcher
from .kb_cache import CacheEntry, KBCache

if TYPE_CHECKING:
    from ..mcp.gateway import MCPGateway


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
        start_time = datetime.utcnow()

        # Default topic if not provided
        if topic is None:
            topic = "overview"

        # Step 1: Check KB cache (exact match)
        cached_entry = self.kb_cache.get(library, topic)
        if cached_entry:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
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
                        datetime.utcnow() - start_time
                    ).total_seconds() * 1000
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

        # Step 3: Resolve library ID if needed
        context7_id = None

        # Try MCP Gateway first
        if self.mcp_gateway:
            try:
                resolve_result = self.mcp_gateway.call_tool(
                    "mcp_Context7_resolve-library-id", libraryName=library
                )
                if resolve_result.get("success"):
                    matches = resolve_result.get("result", {}).get("matches", [])
                    if matches and len(matches) > 0:
                        context7_id = (
                            matches[0].get("id")
                            if isinstance(matches[0], dict)
                            else str(matches[0])
                        )
            except Exception:
                # Continue without context7_id if resolution fails
                pass

        # Fallback to provided function
        if not context7_id and self.resolve_library_func:
            try:
                resolve_result = self.resolve_library_func(library)
                if isinstance(resolve_result, dict):
                    matches = resolve_result.get("matches", [])
                    if matches and len(matches) > 0:
                        context7_id = (
                            matches[0].get("id")
                            if isinstance(matches[0], dict)
                            else str(matches[0])
                        )
                elif isinstance(resolve_result, list) and len(resolve_result) > 0:
                    context7_id = (
                        resolve_result[0].get("id")
                        if isinstance(resolve_result[0], dict)
                        else str(resolve_result[0])
                    )
            except Exception:
                # Continue without context7_id if resolution fails
                pass

        # Step 4: Fetch from Context7 API
        if context7_id:
            content = None

            # Try MCP Gateway first
            if self.mcp_gateway:
                try:
                    api_result = self.mcp_gateway.call_tool(
                        "mcp_Context7_get-library-docs",
                        context7CompatibleLibraryID=context7_id,
                        topic=topic,
                    )
                    if api_result.get("success"):
                        result_data = api_result.get("result", {})
                        content = (
                            result_data.get("content")
                            if isinstance(result_data, dict)
                            else result_data
                        )
                except Exception:
                    # Fall through to provided function
                    pass

            # Fallback to provided function
            if not content and self.get_docs_func:
                try:
                    api_result = self.get_docs_func(context7_id, topic)
                    if isinstance(api_result, dict):
                        content = api_result.get("content") or api_result.get("result")
                    elif isinstance(api_result, str):
                        content = api_result
                except Exception as e:
                    response_time = (
                        datetime.utcnow() - start_time
                    ).total_seconds() * 1000
                    return LookupResult(
                        success=False,
                        source="api",
                        library=library,
                        topic=topic,
                        error=str(e),
                        response_time_ms=response_time,
                    )

            # Step 5: Store in cache if we got content
            if content:
                cached_entry = self.kb_cache.store(
                    library=library,
                    topic=topic,
                    content=content,
                    context7_id=context7_id,
                )

                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
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
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return LookupResult(
            success=False,
            source="cache",
            library=library,
            topic=topic,
            error="No documentation found in cache or API unavailable",
            response_time_ms=response_time,
        )
