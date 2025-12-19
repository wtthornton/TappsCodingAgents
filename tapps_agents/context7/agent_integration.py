"""
Context7 Agent Integration - Helper functions for agents to use Context7 KB.
"""

from pathlib import Path
from typing import Any

from ..core.config import ProjectConfig
from ..mcp.gateway import MCPGateway
from .analytics import Analytics
from .cache_structure import CacheStructure
from .credential_validation import validate_context7_credentials
from .fuzzy_matcher import FuzzyMatcher
from .kb_cache import KBCache
from .lookup import KBLookup
from .metadata import MetadataManager


class Context7AgentHelper:
    """
    Helper class for agents to easily access Context7 KB.
    Provides simplified interface for common operations.
    """

    def __init__(
        self,
        config: ProjectConfig,
        mcp_gateway: MCPGateway | None = None,
        project_root: Path | None = None,
    ):
        """
        Initialize Context7 helper for an agent.

        Args:
            config: ProjectConfig instance
            mcp_gateway: Optional MCPGateway instance
            project_root: Optional project root path
        """
        if project_root is None:
            project_root = Path.cwd()

        # Check if Context7 is enabled
        context7_config = config.context7
        if not context7_config or not context7_config.enabled:
            self.enabled = False
            return

        # Validate credentials (non-blocking, logs warnings if invalid)
        try:
            cred_result = validate_context7_credentials(mcp_gateway=mcp_gateway)
            if not cred_result.valid:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Context7 credentials validation failed: {cred_result.error}\n"
                    f"{cred_result.actionable_message}"
                )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Context7 credential validation error: {e}", exc_info=True)

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

        # Initialize KB lookup with MCP Gateway
        self.mcp_gateway = mcp_gateway
        self.kb_lookup = KBLookup(
            kb_cache=self.kb_cache, mcp_gateway=mcp_gateway, fuzzy_threshold=0.7
        )

    async def get_documentation(
        self, library: str, topic: str | None = None, use_fuzzy_match: bool = True
    ) -> dict[str, Any] | None:
        """
        Get documentation for a library/topic.

        Args:
            library: Library name (e.g., "react", "fastapi")
            topic: Optional topic name (e.g., "hooks", "routing")
            use_fuzzy_match: Whether to use fuzzy matching if exact match not found

        Returns:
            Dictionary with documentation content, or None if not found
        """
        if not self.enabled:
            return None

        try:
            result = await self.kb_lookup.lookup(
                library=library, topic=topic, use_fuzzy_match=use_fuzzy_match
            )

            if result.success:
                return {
                    "content": result.content,
                    "library": result.library,
                    "topic": result.topic,
                    "source": result.source,  # "cache", "api", "fuzzy_match"
                    "fuzzy_score": result.fuzzy_score,
                    "matched_topic": result.matched_topic,
                    "response_time_ms": result.response_time_ms,
                }
        except Exception as e:
            # Log error but don't fail the agent
            print(f"Context7 lookup error: {e}")

        return None

    async def search_libraries(
        self, query: str, limit: int = 5
    ) -> list[dict[str, str]]:
        """
        Search for libraries matching a query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of dictionaries with library information
        """
        if not self.enabled or not self.mcp_gateway:
            return []

        try:
            # Use backup client with automatic fallback (MCP Gateway -> HTTP)
            from .backup_client import call_context7_resolve_with_fallback
            
            result = await call_context7_resolve_with_fallback(query, self.mcp_gateway)

            if result.get("success"):
                matches = result.get("result", {}).get("matches", [])
                return matches[:limit]
        except Exception as e:
            print(f"Context7 search error: {e}")

        return []

    def is_library_cached(self, library: str, topic: str | None = None) -> bool:
        """
        Check if a library/topic is cached.

        Args:
            library: Library name
            topic: Optional topic name

        Returns:
            True if cached, False otherwise
        """
        if not self.enabled:
            return False

        if topic is None:
            topic = "overview"

        return self.kb_cache.exists(library, topic)

    def get_cache_statistics(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            metrics = self.analytics.get_cache_metrics()
            return {
                "enabled": True,
                "total_entries": metrics.total_entries,
                "total_libraries": metrics.total_libraries,
                "cache_hits": metrics.cache_hits,
                "cache_misses": metrics.cache_misses,
                "hit_rate": metrics.hit_rate,
                "avg_response_time_ms": metrics.avg_response_time_ms,
            }
        except Exception:
            return {"enabled": True, "error": "Failed to get statistics"}

    def should_use_context7(self, user_message: str) -> bool:
        """
        Heuristic check if Context7 should be used based on user message.

        Args:
            user_message: User's message/query

        Returns:
            True if Context7 might be helpful
        """
        if not self.enabled:
            return False

        message_lower = user_message.lower()

        # Common library/framework mentions
        library_keywords = [
            "library",
            "framework",
            "package",
            "npm",
            "pip",
            "import",
            "react",
            "vue",
            "angular",
            "fastapi",
            "django",
            "flask",
            "pytest",
            "jest",
            "vitest",
            "typescript",
            "javascript",
            "documentation",
            "docs",
            "api",
            "sdk",
        ]

        return any(keyword in message_lower for keyword in library_keywords)


def get_context7_helper(
    agent_instance,
    config: ProjectConfig | None = None,
    project_root: Path | None = None,
) -> Context7AgentHelper | None:
    """
    Get Context7 helper for an agent instance.

    Args:
        agent_instance: Agent instance (must have config and mcp_gateway attributes)
        config: Optional ProjectConfig (uses agent's config if not provided)
        project_root: Optional project root path

    Returns:
        Context7AgentHelper instance or None if Context7 is disabled
    """
    if config is None:
        config = agent_instance.config

    if config is None:
        return None

    mcp_gateway = getattr(agent_instance, "mcp_gateway", None)

    helper = Context7AgentHelper(
        config=config, mcp_gateway=mcp_gateway, project_root=project_root
    )

    if not helper.enabled:
        return None

    return helper
