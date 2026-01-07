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
        # Initialize staleness policy manager and refresh queue (lazy-loaded)
        self._staleness_policy_manager = None
        self._refresh_queue = None

    async def _process_refresh_queue_async(self, max_items: int = 1) -> None:
        """
        Process refresh queue in background (non-blocking).

        Args:
            max_items: Maximum number of items to process
        """
        try:
            from .refresh_queue import RefreshQueue
            from .staleness_policies import StalenessPolicyManager
            
            if self._refresh_queue is None:
                if self._staleness_policy_manager is None:
                    self._staleness_policy_manager = StalenessPolicyManager()
                self._refresh_queue = RefreshQueue(
                    self.kb_cache.cache_structure.refresh_queue_file,
                    self._staleness_policy_manager
                )
            
            # Get highest priority tasks (limit to max_items)
            tasks_processed = 0
            while tasks_processed < max_items:
                task = self._refresh_queue.get_next_task(max_priority=10)
                if not task:
                    break
                
                # Process task via lookup (which will fetch and cache)
                try:
                    result = await self.lookup(
                        library=task.library, topic=task.topic, use_fuzzy_match=False
                    )
                    if result.success:
                        # Mark task as completed (removes from queue)
                        self._refresh_queue.mark_task_completed(
                            task.library, task.topic, error=None
                        )
                        tasks_processed += 1
                    else:
                        # Mark task as failed (keeps in queue for retry)
                        self._refresh_queue.mark_task_completed(
                            task.library, task.topic, error=result.error or "Refresh failed"
                        )
                        tasks_processed += 1  # Count as processed even if failed
                except Exception as e:
                    logger.warning(f"Failed to refresh {task.library}/{task.topic}: {e}")
                    # Mark task as failed
                    self._refresh_queue.mark_task_completed(
                        task.library, task.topic, error=str(e)
                    )
                    tasks_processed += 1
        except Exception as e:
            logger.warning(f"Background refresh processing failed: {e}")

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
        # #region agent log
        import json
        from datetime import datetime
        from pathlib import Path
        log_path = Path.cwd() / ".cursor" / "debug.log"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "E",
                    "location": "context7/lookup.py:lookup:entry",
                    "message": "KBLookup.lookup called",
                    "data": {"library": library, "topic": topic},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except: pass
        # #endregion
        start_time = datetime.now(UTC)

        # Default topic if not provided
        if topic is None:
            topic = "overview"

        # Step 1: Check KB cache (exact match)
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "E",
                    "location": "context7/lookup.py:lookup:before_cache_check",
                    "message": "About to check KB cache",
                    "data": {"library": library, "topic": topic},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except: pass
        # #endregion
        cached_entry = self.kb_cache.get(library, topic)
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "E",
                    "location": "context7/lookup.py:lookup:after_cache_check",
                    "message": "Cache check completed",
                    "data": {"library": library, "cached": cached_entry is not None},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except: pass
        # #endregion
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
            
            # Check if entry is stale
            if cached_entry.cached_at:
                from .staleness_policies import StalenessPolicyManager
                if self._staleness_policy_manager is None:
                    self._staleness_policy_manager = StalenessPolicyManager()
                
                is_stale = self._staleness_policy_manager.is_entry_stale(
                    library, cached_entry.cached_at
                )
                
                if is_stale:
                    # Queue refresh for background processing (non-blocking)
                    from .refresh_queue import RefreshQueue
                    if self._refresh_queue is None:
                        self._refresh_queue = RefreshQueue(
                            self.kb_cache.cache_structure.refresh_queue_file,
                            self._staleness_policy_manager
                        )
                    
                    self._refresh_queue.add_task(
                        library, topic, priority=7, reason="staleness"
                    )
                    
                    # Process refresh queue in background (non-blocking, limit to 1 item)
                    # Try to process in background if event loop is available
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                        # Event loop is running, create task for background processing
                        asyncio.create_task(
                            self._process_refresh_queue_async(max_items=1)
                        )
                    except RuntimeError:
                        # No running event loop - queue will be processed on next lookup
                        # or via manual refresh command
                        logger.debug("No running event loop, refresh queued for later processing")
                    
                    # Return stale entry immediately (non-blocking)
                    return LookupResult(
                        success=True,
                        content=cached_entry.content,
                        source="cache_stale",  # Indicate stale source
                        library=library,
                        topic=topic,
                        context7_id=cached_entry.context7_id,
                        cached_entry=cached_entry,
                        response_time_ms=response_time,
                    )
            
            # Entry is fresh - return it
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

        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "E",
                    "location": "context7/lookup.py:lookup:before_resolve",
                    "message": "About to resolve library ID",
                    "data": {"library": library, "topic": topic, "has_mcp_gateway": self.mcp_gateway is not None},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except: pass
        # #endregion
        
        # CRITICAL FIX: Check quota BEFORE making API calls
        # This prevents unnecessary API calls when quota is already exceeded
        try:
            from .backup_client import is_context7_quota_exceeded, get_context7_quota_message
            if is_context7_quota_exceeded():
                quota_msg = get_context7_quota_message() or "Monthly quota exceeded"
                response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
                logger.debug(
                    f"Context7 API quota exceeded for '{library}' (topic: {topic}): {quota_msg}. "
                    f"Skipping API call. Consider upgrading your Context7 plan or waiting for quota reset."
                )
                return LookupResult(
                    success=False,
                    source="api",
                    library=library,
                    topic=topic,
                    error=f"Context7 API quota exceeded: {quota_msg}. Consider upgrading your plan or waiting for quota reset.",
                    response_time_ms=response_time,
                )
        except Exception:
            pass  # If quota check fails, continue (graceful degradation)
        
        try:
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "E",
                        "location": "context7/lookup.py:lookup:before_await_resolve",
                        "message": "About to await call_context7_resolve_with_fallback",
                        "data": {"library": library},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + "\n")
            except: pass
            # #endregion
            resolve_result = await call_context7_resolve_with_fallback(
                library, self.mcp_gateway
            )
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "E",
                        "location": "context7/lookup.py:lookup:after_resolve",
                        "message": "call_context7_resolve_with_fallback returned",
                        "data": {"library": library, "success": resolve_result.get("success") if isinstance(resolve_result, dict) else None},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + "\n")
            except: pass
            # #endregion
            if resolve_result.get("success"):
                matches = resolve_result.get("result", {}).get("matches", [])
                if matches and len(matches) > 0:
                    # Extract context7_id from first match
                    first_match = matches[0]
                    if isinstance(first_match, dict):
                        context7_id = first_match.get("id")
                        # Also try library_id as fallback
                        if not context7_id:
                            context7_id = first_match.get("library_id")
                    else:
                        context7_id = str(first_match)
                    
                    # Validate that we actually got an ID
                    if not context7_id:
                        logger.warning(
                            f"Context7 library resolution succeeded for '{library}' (topic: {topic}) "
                            f"but no ID found in match result: {first_match}. "
                            f"Cannot fetch documentation without library ID."
                        )
                else:
                    logger.warning(
                        f"Context7 library resolution succeeded for '{library}' (topic: {topic}) "
                        f"but no matches returned. Cannot fetch documentation without library ID."
                    )
            elif "quota exceeded" in resolve_result.get("error", "").lower():
                # R3: Quota exceeded - clear error message with actionable guidance
                error_msg = resolve_result.get("error", "Context7 API quota exceeded")
                # Avoid log spam: once quota is exceeded, subsequent calls are expected to fail.
                try:
                    from .backup_client import is_context7_quota_exceeded
                    already_exceeded = is_context7_quota_exceeded()
                except Exception:
                    already_exceeded = False

                if already_exceeded:
                    logger.debug(
                        f"Context7 API quota exceeded for '{library}' (topic: {topic}): {error_msg}. "
                        f"Continuing without Context7 documentation."
                    )
                else:
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
                try:
                    cached_entry = self.kb_cache.store(
                        library=library,
                        topic=topic,
                        content=content,
                        context7_id=context7_id,
                    )
                except (RuntimeError, OSError, PermissionError) as e:
                    # Cache lock or file write failed - log but continue
                    # The content is still available, just not cached
                    logger.debug(
                        f"Failed to cache Context7 docs for {library}/{topic}: {e}. "
                        f"Content retrieved but not cached."
                    )
                    cached_entry = None

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
        
        # Provide more specific error message based on why we failed
        if context7_id is None:
            error_msg = (
                f"Could not resolve library ID for '{library}'. "
                f"This is required to fetch documentation from Context7 API. "
                f"Library resolution may have failed or returned no matches."
            )
            # Use debug level for library not found (common, expected case)
            # Only warn if it's a known popular library that should exist in Context7
            # Valid libraries not in Context7 (like 'openai', 'yaml') will log at debug level to reduce noise
            known_libraries = {
                "react", "vue", "angular", "fastapi", "django", "flask", 
                "pytest", "playwright", "typescript", "javascript", "node",
                "express", "nextjs", "svelte", "tailwind", "bootstrap"
            }
            if library.lower() in known_libraries:
                logger.info(
                    f"Context7 lookup failed for library '{library}' (topic: {topic}): {error_msg}. "
                    f"Continuing without Context7 documentation."
                )
            else:
                logger.debug(
                    f"Context7 lookup failed for library '{library}' (topic: {topic}): {error_msg}. "
                    f"Library may not be in Context7 database. Continuing without Context7 documentation."
                )
        else:
            error_msg = (
                f"Failed to fetch documentation from Context7 API for '{library}' (ID: {context7_id}). "
                f"API call may have failed or returned no content."
            )
            logger.warning(
                f"Context7 lookup failed for library '{library}' (topic: {topic}): {error_msg}. "
                f"Continuing without Context7 documentation."
            )
        
        return LookupResult(
            success=False,
            source="cache" if context7_id is None else "api",
            library=library,
            topic=topic,
            error=error_msg,
            response_time_ms=response_time,
        )
