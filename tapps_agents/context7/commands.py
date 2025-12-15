"""
Context7 Commands - CLI commands for Context7 KB management.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.config import ProjectConfig
from .analytics import Analytics
from .cache_structure import CacheStructure
from .cache_warming import CacheWarmer
from .cleanup import KBCleanup
from .credential_validation import validate_context7_credentials
from .cross_references import CrossReferenceManager
from .fuzzy_matcher import FuzzyMatcher
from .kb_cache import KBCache
from .lookup import KBLookup
from .metadata import MetadataManager
from .refresh_queue import RefreshQueue
from .staleness_policies import StalenessPolicyManager


def _parse_size_string(size_str: str) -> int:
    """
    Parse size string like "100MB" or "1GB" into bytes.

    Args:
        size_str: Size string (e.g., "100MB", "1GB", "500KB")

    Returns:
        Size in bytes
    """
    if not size_str:
        return 100 * 1024 * 1024  # Default 100MB

    # Match pattern like "100MB", "1.5GB", etc.
    match = re.match(r"^(\d+(?:\.\d+)?)\s*([KMGT]?B?)$", size_str.upper().strip())
    if not match:
        # If parsing fails, default to 100MB
        return 100 * 1024 * 1024

    value = float(match.group(1))
    unit = match.group(2) or "B"

    multipliers = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
        "TB": 1024 * 1024 * 1024 * 1024,
    }

    return int(value * multipliers.get(unit, 1))


class Context7Commands:
    """
    Context7 KB commands for CLI/agent interface.
    """

    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
    ):
        """
        Initialize Context7 commands.

        Args:
            project_root: Optional project root path (defaults to cwd)
            config: Optional ProjectConfig instance (loads if not provided)
        """
        if project_root is None:
            project_root = Path.cwd()

        if config is None:
            from ..core.config import load_config

            config = load_config()

        context7_config = config.context7
        if not context7_config or not context7_config.enabled:
            self.enabled = False
            return

        self.enabled = True
        self.config = context7_config
        self.project_root = project_root

        # Initialize cache structure
        cache_root = project_root / context7_config.knowledge_base.location
        self.cache_structure = CacheStructure(cache_root)
        self.cache_structure.initialize()

        # Initialize components
        self.metadata_manager = MetadataManager(self.cache_structure)
        self.kb_cache = KBCache(self.cache_structure.cache_root, self.metadata_manager)
        self.fuzzy_matcher = FuzzyMatcher(threshold=0.7)
        self.analytics = Analytics(self.cache_structure, self.metadata_manager)
        self.staleness_policy_manager = StalenessPolicyManager()
        self.refresh_queue = RefreshQueue(
            self.cache_structure.refresh_queue_file, self.staleness_policy_manager
        )
        # Parse max_cache_size string (e.g., "100MB") to bytes
        max_cache_size_bytes = _parse_size_string(
            context7_config.knowledge_base.max_cache_size
        )

        self.cleanup = KBCleanup(
            self.cache_structure,
            self.metadata_manager,
            self.staleness_policy_manager,
            self.analytics,
            max_cache_size_bytes=max_cache_size_bytes,
        )
        self.cross_refs = CrossReferenceManager(self.cache_structure)

        # KB lookup (will need MCP Gateway for API calls)
        self.kb_lookup = KBLookup(
            kb_cache=self.kb_cache,
            mcp_gateway=None,  # Set via set_mcp_gateway
            fuzzy_threshold=0.7,
        )

        # Cache warmer
        self.cache_warmer = CacheWarmer(
            kb_cache=self.kb_cache,
            kb_lookup=self.kb_lookup,
            cache_structure=self.cache_structure,
            metadata_manager=self.metadata_manager,
            project_root=self.project_root,
        )

    def set_mcp_gateway(self, mcp_gateway):
        """Set MCP Gateway for API calls."""
        self.kb_lookup.mcp_gateway = mcp_gateway
        self.cache_warmer.kb_lookup = self.kb_lookup

    async def cmd_docs(self, library: str, topic: str | None = None) -> dict[str, Any]:
        """
        Get KB-first documentation for a library/topic.

        Command: *context7-docs {library} [topic]

        Args:
            library: Library name
            topic: Optional topic name

        Returns:
            Dictionary with documentation result
        """
        if not self.enabled:
            return {"error": "Context7 is not enabled"}

        try:
            result = await self.kb_lookup.lookup(
                library=library, topic=topic, use_fuzzy_match=True
            )

            if result.success:
                return {
                    "success": True,
                    "library": result.library,
                    "topic": result.topic,
                    "content": result.content,
                    "source": result.source,
                    "fuzzy_score": result.fuzzy_score,
                    "matched_topic": result.matched_topic,
                    "response_time_ms": result.response_time_ms,
                }
            else:
                return {
                    "success": False,
                    "error": result.error or "Documentation not found",
                    "library": library,
                    "topic": topic,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cmd_resolve(self, library: str) -> dict[str, Any]:
        """
        Resolve library name to Context7 ID.

        Command: *context7-resolve {library}

        Args:
            library: Library name to resolve

        Returns:
            Dictionary with resolution result
        """
        if not self.enabled:
            return {"error": "Context7 is not enabled"}

        if not self.kb_lookup.mcp_gateway:
            return {"error": "MCP Gateway not available"}

        try:
            result = await self.kb_lookup.mcp_gateway.call_tool(
                "mcp_Context7_resolve-library-id", libraryName=library
            )

            if result.get("success"):
                matches = result.get("result", {}).get("matches", [])
                return {"success": True, "library": library, "matches": matches}
            else:
                return {
                    "success": False,
                    "error": "Failed to resolve library",
                    "library": library,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cmd_status(self) -> dict[str, Any]:
        """
        Get KB status and statistics.

        Command: *context7-kb-status

        Returns:
            Dictionary with status information
        """
        if not self.enabled:
            return {"error": "Context7 is not enabled"}

        try:
            metrics = self.analytics.get_cache_metrics()
            status_report = self.analytics.get_status_report()

            # Get cache size
            cache_size = self.cleanup.get_cache_size()

            return {
                "success": True,
                "status": status_report.get("status", "unknown"),
                "health_issues": status_report.get("health_issues", []),
                "cache_size_bytes": cache_size,
                "cache_size_mb": cache_size / (1024 * 1024),
                "metrics": {
                    "total_entries": metrics.total_entries,
                    "total_libraries": metrics.total_libraries,
                    "cache_hits": metrics.cache_hits,
                    "cache_misses": metrics.cache_misses,
                    "api_calls": metrics.api_calls,
                    "hit_rate": metrics.hit_rate,
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                },
                "top_libraries": status_report.get("top_libraries", []),
                "timestamp": status_report.get("timestamp"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cmd_health(self) -> dict[str, Any]:
        """
        Get detailed health check report.

        Command: *context7-kb-health

        Returns:
            Dictionary with health check information
        """
        if not self.enabled:
            return {"error": "Context7 is not enabled"}

        try:
            health_check = self.analytics.get_health_check()
            return {"success": True, **health_check}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cmd_search(self, query: str, limit: int = 10) -> dict[str, Any]:
        """
        Search cached documentation.

        Command: *context7-kb-search {query} [limit]

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            Dictionary with search results
        """
        if not self.enabled:
            return {"error": "Context7 is not enabled"}

        try:
            cache_index = self.metadata_manager.load_cache_index()
            results = []

            # Simple keyword search in library/topic names
            query_lower = query.lower()

            for library_name, library_data in cache_index.libraries.items():
                topics = library_data.get("topics", {})

                # Check library name
                if query_lower in library_name.lower():
                    for topic_name in topics.keys():
                        results.append(
                            {
                                "library": library_name,
                                "topic": topic_name,
                                "match_type": "library_name",
                            }
                        )

                # Check topic names
                for topic_name in topics.keys():
                    if query_lower in topic_name.lower():
                        results.append(
                            {
                                "library": library_name,
                                "topic": topic_name,
                                "match_type": "topic_name",
                            }
                        )

            # Use fuzzy matching for better results
            if len(results) < limit:
                fuzzy_results = self.fuzzy_matcher.find_best_match(
                    query, None, cache_index
                )
                if fuzzy_results:
                    for match in fuzzy_results[: limit - len(results)]:
                        if match not in results:
                            results.append(
                                {
                                    "library": match.library,
                                    "topic": match.topic,
                                    "match_type": "fuzzy",
                                    "score": match.score,
                                }
                            )

            return {
                "success": True,
                "query": query,
                "results": results[:limit],
                "count": len(results[:limit]),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cmd_refresh_process(self, max_items: int = 10) -> dict[str, Any]:
        """
        Process queued refresh tasks (best-effort).

        This is used by startup routines to refresh stale entries incrementally.
        If the MCP gateway is not available, we soft-fail with a clear error.
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Context7 is not enabled",
                "items_processed": 0,
            }

        if not self.kb_lookup.mcp_gateway:
            return {
                "success": False,
                "error": "MCP Gateway not available",
                "items_processed": 0,
            }

        processed = 0
        errors: list[str] = []

        while processed < max_items:
            task = self.refresh_queue.get_next_task()
            if task is None:
                break

            topic = task.topic or "overview"
            try:
                # Resolve library -> Context7 ID
                resolve = await self.kb_lookup.mcp_gateway.call_tool(
                    "mcp_Context7_resolve-library-id", libraryName=task.library
                )
                matches = (
                    resolve.get("result", {}).get("matches", [])
                    if resolve.get("success")
                    else []
                )
                context7_id = None
                if matches:
                    first = matches[0]
                    context7_id = (
                        first.get("id") if isinstance(first, dict) else str(first)
                    )

                if not context7_id:
                    raise RuntimeError("Could not resolve Context7 library ID")

                # Fetch docs
                docs = await self.kb_lookup.mcp_gateway.call_tool(
                    "mcp_Context7_get-library-docs",
                    context7CompatibleLibraryID=context7_id,
                    topic=topic,
                )
                if not docs.get("success"):
                    raise RuntimeError(docs.get("error") or "Failed to fetch docs")

                result_data = docs.get("result", {})
                content = (
                    result_data.get("content")
                    if isinstance(result_data, dict)
                    else (result_data if isinstance(result_data, str) else None)
                )
                if not content:
                    raise RuntimeError("No content returned from Context7 docs tool")

                # Store (refresh) content
                self.kb_cache.store(
                    library=task.library,
                    topic=topic,
                    content=content,
                    context7_id=context7_id,
                )

                self.refresh_queue.mark_task_completed(
                    task.library, task.topic, error=None
                )
                processed += 1

            except Exception as e:
                err = f"{task.library}/{topic}: {e}"
                errors.append(err)
                self.refresh_queue.mark_task_completed(
                    task.library, task.topic, error=str(e)
                )
                # Avoid infinite loop on a permanently failing head task.
                break

        return {
            "success": processed > 0 and not errors,
            "items_processed": processed,
            "errors": errors,
            "queue_remaining": self.refresh_queue.size(),
        }

    async def cmd_refresh(
        self, library: str | None = None, topic: str | None = None
    ) -> dict[str, Any]:
        """
        Refresh stale KB entries.

        Command: *context7-kb-refresh [library] [topic]

        Args:
            library: Optional library name (refreshes all if not provided)
            topic: Optional topic name

        Returns:
            Dictionary with refresh result
        """
        if not self.enabled:
            return {"error": "Context7 is not enabled"}

        try:
            if library:
                # Refresh specific library/topic
                if topic:
                    priority = 8  # High priority for manual refresh
                    self.refresh_queue.add_task(library, topic, priority=priority)
                    return {
                        "success": True,
                        "message": f"Queued refresh for {library}/{topic}",
                        "library": library,
                        "topic": topic,
                    }
                else:
                    # Refresh all topics for library
                    cache_index = self.metadata_manager.load_cache_index()
                    library_data = cache_index.libraries.get(library, {})
                    topics = library_data.get("topics", {})

                    queued = 0
                    for topic_name in topics.keys():
                        self.refresh_queue.add_task(library, topic_name, priority=7)
                        queued += 1

                    return {
                        "success": True,
                        "message": f"Queued refresh for {queued} topics in {library}",
                        "library": library,
                        "topics_queued": queued,
                    }
            else:
                # Refresh all stale entries
                cache_index = self.metadata_manager.load_cache_index()
                entries = []

                for lib_name, lib_data in cache_index.libraries.items():
                    topics = lib_data.get("topics", {})
                    for topic_name, topic_data in topics.items():
                        last_updated = topic_data.get("last_updated") or topic_data.get(
                            "cached_at"
                        )
                        if last_updated:
                            entries.append(
                                {
                                    "library": lib_name,
                                    "topic": topic_name,
                                    "last_updated": last_updated,
                                }
                            )

                queued = self.refresh_queue.queue_stale_entries(entries)

                return {
                    "success": True,
                    "message": f"Queued refresh for {queued} stale entries",
                    "entries_queued": queued,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cmd_cleanup(
        self,
        strategy: str = "all",
        target_size_mb: float | None = None,
        max_age_days: int | None = None,
    ) -> dict[str, Any]:
        """
        Clean up old/unused KB entries.

        Command: *context7-kb-cleanup [strategy] [options]

        Args:
            strategy: Cleanup strategy ("size", "age", "unused", "all")
            target_size_mb: Target size in MB (for size strategy)
            max_age_days: Maximum age in days (for age strategy)

        Returns:
            Dictionary with cleanup result
        """
        if not self.enabled:
            return {"error": "Context7 is not enabled"}

        try:
            if strategy == "size":
                target_bytes = (
                    int(target_size_mb * 1024 * 1024) if target_size_mb else None
                )
                result = self.cleanup.cleanup_by_size(target_size_bytes=target_bytes)
            elif strategy == "age":
                result = self.cleanup.cleanup_by_age(max_age_days=max_age_days)
            elif strategy == "unused":
                result = self.cleanup.cleanup_unused()
            else:  # "all"
                result = self.cleanup.cleanup_all(
                    target_size_bytes=(
                        int(target_size_mb * 1024 * 1024) if target_size_mb else None
                    ),
                    max_age_days=max_age_days,
                )

            return {"success": True, "strategy": strategy, "result": result.to_dict()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cmd_rebuild_index(self) -> dict[str, Any]:
        """
        Rebuild KB cache index.

        Command: *context7-kb-rebuild

        Returns:
            Dictionary with rebuild result
        """
        if not self.enabled:
            return {"error": "Context7 is not enabled"}

        try:
            # Rebuild index from filesystem
            cache_index = self.metadata_manager.load_cache_index()
            cache_index.libraries = {}
            cache_index.total_entries = 0

            # Scan filesystem
            for lib_dir in self.cache_structure.libraries_dir.iterdir():
                if lib_dir.is_dir():
                    library_name = lib_dir.name
                    topics = {}

                    for doc_file in lib_dir.glob("*.md"):
                        if doc_file.name != "index.md":  # Skip index files
                            topic = doc_file.stem
                            topics[topic] = {
                                "cached_at": datetime.utcnow().isoformat() + "Z"
                            }

                    if topics:
                        cache_index.libraries[library_name] = {"topics": topics}
                        cache_index.total_entries += len(topics)

            self.metadata_manager.save_cache_index(cache_index)

            return {
                "success": True,
                "message": "Index rebuilt successfully",
                "libraries": len(cache_index.libraries),
                "total_entries": cache_index.total_entries,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cmd_warm(
        self,
        auto_detect: bool = True,
        libraries: list[str] | None = None,
        priority: int = 5,
    ) -> dict[str, Any]:
        """
        Warm cache with project libraries and common topics.

        Command: *context7-kb-warm [--auto-detect] [libraries...]

        Args:
            auto_detect: Whether to auto-detect libraries from project (default: True)
            libraries: Optional list of library names
            priority: Priority for warming (1-10)

        Returns:
            Dictionary with warming result
        """
        if not self.enabled:
            return {"error": "Context7 is not enabled"}

        if not self.kb_lookup.mcp_gateway:
            return {"error": "MCP Gateway not available"}

        try:
            result = await self.cache_warmer.warm_cache(
                libraries=libraries,
                topics=None,  # Auto-detect topics
                priority=priority,
                auto_detect=auto_detect,
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cmd_populate(
        self,
        libraries: list[str] | None = None,
        topics: list[str] | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """
        Pre-populate cache with library documentation.

        Command: *context7-kb-populate [libraries...] [--topics topics...] [--force]

        Args:
            libraries: List of library names to populate (defaults to common libraries)
            topics: Optional list of topics to populate (defaults to ["overview"])
            force: Whether to force refresh even if already cached

        Returns:
            Dictionary with populate result
        """
        if not self.enabled:
            return {"error": "Context7 is not enabled"}

        if not self.kb_lookup.mcp_gateway:
            return {"error": "MCP Gateway not available"}

        # Default libraries if not provided
        if libraries is None:
            libraries = [
                "fastapi",
                "pytest",
                "react",
                "typescript",
                "python",
                "pydantic",
                "sqlalchemy",
                "playwright",
            ]

        # Default topics if not provided
        if topics is None:
            topics = ["overview"]

        populated = 0
        errors: list[str] = []

        for library in libraries:
            for topic in topics:
                # Check if already cached (unless force)
                if not force and self.kb_cache.exists(library, topic):
                    continue

                try:
                    # Resolve library -> Context7 ID
                    resolve = await self.kb_lookup.mcp_gateway.call_tool(
                        "mcp_Context7_resolve-library-id", libraryName=library
                    )
                    matches = (
                        resolve.get("result", {}).get("matches", [])
                        if resolve.get("success")
                        else []
                    )
                    context7_id = None
                    if matches:
                        first = matches[0]
                        context7_id = (
                            first.get("id") if isinstance(first, dict) else str(first)
                        )

                    if not context7_id:
                        errors.append(f"{library}/{topic}: Could not resolve library ID")
                        continue

                    # Fetch docs
                    docs = await self.kb_lookup.mcp_gateway.call_tool(
                        "mcp_Context7_get-library-docs",
                        context7CompatibleLibraryID=context7_id,
                        topic=topic,
                    )
                    if not docs.get("success"):
                        errors.append(
                            f"{library}/{topic}: {docs.get('error', 'Failed to fetch docs')}"
                        )
                        continue

                    result_data = docs.get("result", {})
                    content = (
                        result_data.get("content")
                        if isinstance(result_data, dict)
                        else (result_data if isinstance(result_data, str) else None)
                    )
                    if not content:
                        errors.append(f"{library}/{topic}: No content returned")
                        continue

                    # Store in cache
                    self.kb_cache.store(
                        library=library,
                        topic=topic,
                        content=content,
                        context7_id=context7_id,
                    )
                    populated += 1

                except Exception as e:
                    errors.append(f"{library}/{topic}: {str(e)}")

        return {
            "success": populated > 0,
            "populated": populated,
            "total_requested": len(libraries) * len(topics),
            "errors": errors,
        }

    def cmd_help(self) -> dict[str, Any]:
        """
        Show Context7 usage examples.

        Command: *context7-help

        Returns:
            Dictionary with help content
        """
        help_text = """
Context7 KB Commands

Documentation Commands:
  *context7-docs {library} [topic]
    Get KB-first documentation for a library/topic.
    Example: *context7-docs react hooks
    
  *context7-resolve {library}
    Resolve library name to Context7 ID.
    Example: *context7-resolve fastapi

Status & Search:
  *context7-kb-status
    Show KB cache statistics and performance metrics.
    
  *context7-kb-health
    Get detailed health check report with recommendations.
    
  *context7-kb-search {query} [limit]
    Search cached documentation.
    Example: *context7-kb-search authentication 5

Management Commands:
  *context7-kb-populate [libraries...] [--topics topics...] [--force]
    Pre-populate cache with library documentation.
    Example: *context7-kb-populate fastapi pytest react --topics overview hooks
  
  *context7-kb-warm [--auto-detect] [libraries...]
    Warm cache with project libraries and common topics.
    Example: *context7-kb-warm --auto-detect
  
  *context7-kb-refresh [library] [topic]
    Refresh stale KB entries.
    Examples:
      *context7-kb-refresh              # Refresh all stale entries
      *context7-kb-refresh react        # Refresh all topics in react
      *context7-kb-refresh react hooks  # Refresh specific topic
    
  *context7-kb-cleanup [strategy] [options]
    Clean up old/unused KB entries.
    Strategies: size, age, unused, all
    Example: *context7-kb-cleanup size target_size_mb=50
    
  *context7-kb-rebuild
    Rebuild KB cache index from filesystem.

For more information, see: docs/CONTEXT7_GUIDE.md
"""
        return {"success": True, "help": help_text.strip()}
