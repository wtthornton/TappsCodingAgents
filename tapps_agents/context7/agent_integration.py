"""
Context7 Agent Integration - Helper functions for agents to use Context7 KB.
"""

import logging
from pathlib import Path
from typing import Any

from ..core.config import ProjectConfig
from ..mcp.gateway import MCPGateway
from .analytics import Analytics
from .cache_structure import CacheStructure
from .credential_validation import validate_context7_credentials
from .doc_manager import Context7DocManager
from .fuzzy_matcher import FuzzyMatcher
from .kb_cache import KBCache
from .library_detector import LibraryDetector
from .lookup import KBLookup
from .metadata import MetadataManager

logger = logging.getLogger(__name__)


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

        # #region agent log
        from ..core.debug_logger import write_debug_log
        # Extract values before JSON serialization to handle MagicMock objects in tests
        config_exists = config is not None
        context7_config_exists = False
        context7_enabled = False
        if config and hasattr(config, 'context7'):
            try:
                context7_config = config.context7
                context7_config_exists = context7_config is not None
                if context7_config_exists and hasattr(context7_config, 'enabled'):
                    context7_enabled = bool(context7_config.enabled)
            except (AttributeError, TypeError):
                pass
        
        write_debug_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "C",
                "message": "Context7AgentHelper __init__ called",
                "data": {
                    "config_exists": config_exists,
                    "context7_config_exists": context7_config_exists,
                    "context7_enabled": context7_enabled
                },
            },
            project_root=project_root,
            location="context7/agent_integration.py:__init__:entry",
        )
        # #endregion
        
        # Check if Context7 is enabled
        context7_config = config.context7
        if not context7_config or not context7_config.enabled:
            self.enabled = False
            # #region agent log
            write_debug_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "message": "Context7 disabled in config",
                    "data": {"context7_config": context7_config is not None, "enabled": context7_config.enabled if context7_config else False},
                },
                project_root=project_root,
                location="context7/agent_integration.py:__init__:disabled",
            )
            # #endregion
            return

        # Ensure API key is available (loads from encrypted storage if needed)
        # This ensures agents don't need to manually pass the API key
        try:
            from .backup_client import _ensure_context7_api_key
            api_key_result = _ensure_context7_api_key()
            # #region agent log
            write_debug_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "message": "API key ensured",
                    "data": {"api_key_available": api_key_result is not None, "key_length": len(api_key_result) if api_key_result else 0},
                },
                project_root=project_root,
                location="context7/agent_integration.py:__init__:api_key_ensured",
            )
            # #endregion
        except Exception as e:
            logger.debug(f"Could not ensure Context7 API key availability: {e}")
            # #region agent log
            write_debug_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "message": "API key ensure failed",
                    "data": {"error": str(e)},
                },
                project_root=project_root,
                location="context7/agent_integration.py:__init__:api_key_error",
            )
            # #endregion

        # Validate credentials (non-blocking, only warn if Context7 is actually needed)
        # Context7 is optional - only warn if it's explicitly required for the operation
        try:
            cred_result = validate_context7_credentials(mcp_gateway=mcp_gateway)
            # Only log as debug if MCP is available (Context7 works via MCP)
            # Only warn if both MCP and API key are unavailable
            if not cred_result.valid:
                if mcp_gateway:
                    # MCP is available, so Context7 should work via MCP
                    # Only log as debug to avoid noise
                    logger.debug(
                        f"Context7 API key not configured, but MCP gateway is available. "
                        f"Context7 will work via MCP: {cred_result.error}"
                    )
                else:
                    # No MCP and no API key - warn only if Context7 is actually needed
                    # For now, we'll still warn but at debug level to reduce noise
                    logger.debug(
                        f"Context7 credentials not configured: {cred_result.error}. "
                        f"Context7 features will be limited. {cred_result.actionable_message}"
                    )
        except Exception as e:
            logger.debug(f"Context7 credential validation error: {e}", exc_info=True)

        # Wrap initialization in try-except to prevent Context7 failures from breaking agents
        try:
            self.enabled = True
            self.config = context7_config
            self.project_root = project_root
            # #region agent log
            write_debug_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "message": "Context7AgentHelper enabled=True",
                    "data": {"enabled": True},
                },
                project_root=project_root,
                location="context7/agent_integration.py:__init__:enabled",
            )
            # #endregion

            # Initialize cache structure
            # Defensive: if knowledge_base.location is not a string (e.g. MagicMock in tests),
            # use default to avoid creating directories with mock reprs (e.g. "MagicMock/").
            kb = getattr(context7_config, "knowledge_base", None)
            loc = getattr(kb, "location", None) if kb is not None else None
            if not isinstance(loc, str):
                loc = ".tapps-agents/kb/context7-cache"
            cache_root = project_root / loc
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

            # Initialize library detector for Option 3 quality uplift
            self.library_detector = LibraryDetector(project_root=project_root)
            
            # Initialize documentation manager for auto-save and offline access (Phase 7.1)
            self.doc_manager = Context7DocManager(
                cache_root=self.cache_structure.cache_root,
                project_root=project_root,
            )
            
            # #region agent log
            write_debug_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "message": "Library detector initialized",
                    "data": {"library_detector_created": self.library_detector is not None},
                },
                project_root=project_root,
                location="context7/agent_integration.py:__init__:library_detector_init",
            )
            # #endregion
        except Exception as e:
            # If Context7 initialization fails, disable it gracefully
            # This prevents Context7 failures from breaking agent initialization
            logger.warning(
                f"Context7 initialization failed, disabling Context7 features: {e}. "
                f"Agents will continue to work without Context7."
            )
            self.enabled = False
            # Set minimal attributes to prevent AttributeError
            self.config = context7_config
            self.project_root = project_root
            self.cache_structure = None
            self.metadata_manager = None
            self.kb_cache = None
            self.fuzzy_matcher = None
            self.analytics = None
            self.mcp_gateway = mcp_gateway
            self.kb_lookup = None
            self.library_detector = None
            self.doc_manager = None  # Phase 7.1: Doc manager disabled on init failure
            # #region agent log
            write_debug_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "message": "Context7 initialization failed, disabled",
                    "data": {"error": str(e), "enabled": False},
                },
                project_root=project_root,
                location="context7/agent_integration.py:__init__:init_failed",
            )
            # #endregion

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
        # #region agent log
        from ..core.debug_logger import write_debug_log
        write_debug_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "E",
                "message": "get_documentation called",
                "data": {"library": library, "topic": topic, "enabled": self.enabled},
            },
            project_root=self.project_root if hasattr(self, 'project_root') else None,
            location="context7/agent_integration.py:get_documentation:entry",
        )
        # #endregion
        if not self.enabled or self.kb_lookup is None:
            return None

        try:
            # #region agent log
            write_debug_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "E",
                    "message": "About to call kb_lookup.lookup",
                    "data": {"library": library, "topic": topic},
                },
                project_root=self.project_root if hasattr(self, 'project_root') else None,
                location="context7/agent_integration.py:get_documentation:before_lookup",
            )
            # #endregion
            
            # Check if we have saved documentation first (offline access)
            if hasattr(self, 'doc_manager') and self.doc_manager:
                saved_doc = self.doc_manager.get_saved_documentation(library, topic)
                if saved_doc:
                    logger.debug(f"Using saved documentation for {library} ({topic})")
                    return saved_doc
            
            result = await self.kb_lookup.lookup(
                library=library, topic=topic, use_fuzzy_match=use_fuzzy_match
            )
            
            # Auto-save documentation if available
            if result and result.success and hasattr(self, 'doc_manager') and self.doc_manager:
                try:
                    doc_result = {
                        "content": result.content,
                        "library": result.library,
                        "topic": result.topic,
                        "source": result.source,
                    }
                    self.doc_manager.save_documentation(
                        library=library,
                        topic=topic,
                        documentation=doc_result,
                        source=result.source,
                    )
                except Exception as e:
                    logger.debug(f"Failed to auto-save documentation: {e}")
            
            # #region agent log
            write_debug_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "E",
                    "message": "kb_lookup.lookup returned",
                    "data": {"library": library, "success": result.success if hasattr(result, 'success') else None},
                },
                project_root=self.project_root if hasattr(self, 'project_root') else None,
                location="context7/agent_integration.py:get_documentation:after_lookup",
            )
            # #endregion

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
            elif result.error:
                # Log Context7 unavailability but continue (use debug for common cases)
                # Only log at info level if it's a known library or network error
                error_lower = result.error.lower()
                if "network" in error_lower or "connection" in error_lower:
                    logger.warning(
                        f"Context7 network error for library '{library}' "
                        f"(topic: {topic}): {result.error}. Continuing without Context7 documentation."
                    )
                elif "quota" in error_lower:
                    # Avoid log spam: once quota is exceeded, subsequent calls are expected to fail.
                    try:
                        from .backup_client import is_context7_quota_exceeded
                        already_exceeded = is_context7_quota_exceeded()
                    except Exception:
                        already_exceeded = False

                    log_fn = logger.debug if already_exceeded else logger.warning
                    log_fn(
                        f"Context7 quota exceeded for library '{library}' "
                        f"(topic: {topic}): {result.error}. Continuing without Context7 documentation."
                    )
                else:
                    # Common case: library not found - use debug level
                    logger.debug(
                        f"Context7 lookup unavailable for library '{library}' "
                        f"(topic: {topic}): {result.error}. Continuing without Context7 documentation."
                    )
        except (RuntimeError, OSError, PermissionError) as e:
            # Cache lock or file operation failed - log but don't fail the agent
            # These are non-critical errors that shouldn't break agent functionality
            error_msg = str(e)
            if "cache lock" in error_msg.lower() or "lock" in error_msg.lower():
                # Cache lock failures are expected in high-concurrency scenarios
                logger.debug(
                    f"Context7 cache lock unavailable for library '{library}' (topic: {topic}): {e}. "
                    f"Continuing without Context7 documentation."
                )
            else:
                logger.warning(
                    f"Context7 lookup error for library '{library}' (topic: {topic}): {e}. "
                    f"Continuing without Context7 documentation.",
                    exc_info=True
                )
        except Exception as e:
            # Other unexpected errors - log but don't fail the agent
            logger.warning(
                f"Context7 lookup error for library '{library}' (topic: {topic}): {e}. "
                f"Continuing without Context7 documentation.",
                exc_info=True
            )

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
            else:
                # Log Context7 unavailability but continue
                error_msg = result.get("error", "Unknown error")
                logger.info(
                    f"Context7 search unavailable for query '{query}': {error_msg}. "
                    f"Continuing without Context7 library search."
                )
        except Exception as e:
            logger.warning(
                f"Context7 search error for query '{query}': {e}. "
                f"Continuing without Context7 library search.",
                exc_info=True
            )

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
        if not self.enabled or self.kb_cache is None:
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
        if not self.enabled or self.analytics is None:
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

    def is_well_known_library(self, lib_name: str) -> bool:
        """
        Check if a library name is a well-known library (likely to be useful for Context7).
        
        This helps filter out local directory names vs. actual libraries that Context7
        might have documentation for.
        
        Args:
            lib_name: Library name to check
            
        Returns:
            True if it's a well-known library that Context7 likely has docs for
        """
        well_known = {
            # Python
            "fastapi", "django", "flask", "pydantic", "sqlalchemy", "pytest",
            "requests", "httpx", "aiohttp", "click", "typer", "numpy", "pandas",
            "openai", "anthropic", "yaml", "pyyaml", "marshmallow", "celery",
            # JavaScript/TypeScript
            "react", "vue", "angular", "express", "nextjs", "nuxt", "svelte",
            "typescript", "jest", "vitest", "playwright", "cypress", "selenium",
            "axios", "lodash", "moment", "dayjs", "webpack", "vite",
            # Node.js
            "node", "npm", "yarn", "pnpm",
            # Testing
            "puppeteer", "mocha",
            # Config/Infra (valid libraries in Context7)
            "config", "dotenv", "env",
        }
        return lib_name.lower() in well_known
    
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

    def detect_libraries(
        self,
        code: str | None = None,
        prompt: str | None = None,
        error_message: str | None = None,
        language: str = "python",
    ) -> list[str]:
        """
        Detect libraries from code, prompt, error messages, or project files.
        
        Option 3 (C1) Enhancement: Enhanced library detection for prompt analysis.
        Enhancement 5: Added error message detection.

        Args:
            code: Optional code content to analyze
            prompt: Optional prompt text to analyze
            error_message: Optional error message or stack trace to analyze
            language: Programming language ("python", "typescript", "javascript")

        Returns:
            List of detected library names
        """
        if not self.enabled:
            return []

        return self.library_detector.detect_all(
            code=code, prompt=prompt, error_message=error_message, language=language
        )

    async def get_documentation_for_libraries(
        self,
        libraries: list[str],
        topic: str | None = None,
        use_fuzzy_match: bool = True,
        max_concurrency: int = 5,
        per_library_timeout: float = 5.0,
    ) -> dict[str, dict[str, Any] | None]:
        """
        Get documentation for multiple libraries in parallel with circuit breaker.
        
        2025 Architecture: Bounded parallelism + circuit breaker for resilience.
        - Max 5 concurrent requests (prevents resource exhaustion)
        - 5s timeout per library (prevents cascading delays)
        - Circuit breaker opens after 3 failures (fast-fails subsequent requests)
        - Early quota detection prevents unnecessary API calls

        Args:
            libraries: List of library names
            topic: Optional topic name (e.g., "hooks", "routing")
            use_fuzzy_match: Whether to use fuzzy matching
            max_concurrency: Maximum concurrent library lookups (default: 5)
            per_library_timeout: Timeout per library in seconds (default: 5.0)

        Returns:
            Dictionary mapping library names to their documentation (or None if not found)
        """
        if not self.enabled:
            return {lib: None for lib in libraries}

        # Plan 3.2: apply max_chunks_per_step to limit Context7 injection
        max_chunks = 50
        try:
            cb = getattr(self.config, "context_budget", None)
            if cb is not None:
                max_chunks = max(1, getattr(cb, "max_chunks_per_step", 50) or 50)
        except Exception:  # pylint: disable=broad-except
            pass
        libraries = list(libraries)[:max_chunks]

        # CRITICAL FIX: Check quota BEFORE starting parallel execution
        # This prevents making multiple API calls when quota is already exceeded
        try:
            from .backup_client import (
                get_context7_quota_message,
                is_context7_quota_exceeded,
            )
            if is_context7_quota_exceeded():
                quota_msg = get_context7_quota_message() or "Monthly quota exceeded"
                logger.warning(
                    f"Context7 API quota exceeded ({quota_msg}). "
                    f"Skipping documentation lookup for {len(libraries)} libraries. "
                    f"Consider upgrading your Context7 plan or waiting for quota reset."
                )
                # Return empty results for all libraries without making API calls
                return {lib: None for lib in libraries}
        except Exception as e:
            # If quota check fails, log but continue (graceful degradation)
            logger.debug(f"Error checking Context7 quota status: {e}. Continuing with lookups.")

        import asyncio

        from .circuit_breaker import get_parallel_executor

        # Get parallel executor with circuit breaker
        executor = get_parallel_executor(max_concurrency=max_concurrency)

        # Define the lookup function for each library
        async def lookup_library(lib: str) -> tuple[str, dict[str, Any] | None]:
            # Check quota again before each individual lookup (defense in depth)
            try:
                from .backup_client import is_context7_quota_exceeded
                if is_context7_quota_exceeded():
                    return (lib, None)  # Fast-fail without API call
            except Exception:
                pass  # Continue if quota check fails
            
            try:
                result = await asyncio.wait_for(
                    self.get_documentation(
                        library=lib, topic=topic, use_fuzzy_match=use_fuzzy_match
                    ),
                    timeout=per_library_timeout,
                )
                return (lib, result)
            except TimeoutError:
                logger.debug(f"Context7 lookup timeout for {lib} ({per_library_timeout}s)")
                return (lib, None)
            except Exception as e:
                logger.debug(f"Context7 lookup error for {lib}: {e}")
                return (lib, None)

        # Execute all lookups in parallel with circuit breaker
        results = await executor.execute_all(
            items=libraries,
            func=lookup_library,
            fallback=None,
        )

        # Map results to libraries
        library_docs = {}
        for result in results:
            if result is None:
                continue
            if isinstance(result, tuple) and len(result) == 2:
                lib, doc = result
                library_docs[lib] = doc
            else:
                logger.debug(f"Unexpected result format: {result}")

        # Ensure all libraries are in the result (even if lookup failed)
        for lib in libraries:
            if lib not in library_docs:
                library_docs[lib] = None

        # Log circuit breaker status if any failures
        cb_stats = executor.stats.get("circuit_breaker", {}).get("stats", {})
        if cb_stats.get("failed_requests", 0) > 0:
            logger.debug(
                f"Context7 parallel lookup completed. "
                f"Success: {cb_stats.get('successful_requests', 0)}, "
                f"Failed: {cb_stats.get('failed_requests', 0)}, "
                f"Rejected: {cb_stats.get('rejected_requests', 0)}"
            )

        return library_docs

    async def resolve_library_ids(self, libraries: list[str]) -> dict[str, str | None]:
        """
        Resolve library names to Context7-compatible library IDs.
        
        Option 3 Enhancement: Batch library ID resolution.

        Args:
            libraries: List of library names

        Returns:
            Dictionary mapping library names to Context7 library IDs (or None if not found)
        """
        if not self.enabled or not self.mcp_gateway:
            return {lib: None for lib in libraries}

        import asyncio

        async def resolve_one(lib: str) -> tuple[str, str | None]:
            try:
                from .backup_client import call_context7_resolve_with_fallback

                result = await call_context7_resolve_with_fallback(lib, self.mcp_gateway)
                if result.get("success"):
                    matches = result.get("result", {}).get("matches", [])
                    if matches:
                        # Return the first match's library ID
                        return (lib, matches[0].get("library_id"))
            except Exception as e:
                logger.debug(f"Error resolving library ID for {lib}: {e}")
            return (lib, None)

        # Resolve all libraries in parallel
        tasks = [resolve_one(lib) for lib in libraries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results
        library_ids = {}
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Error in library resolution: {result}")
            else:
                lib, lib_id = result
                library_ids[lib] = lib_id

        return library_ids

    def detect_topics(self, code: str, library: str) -> list[str]:
        """
        Detect relevant Context7 topics from code context.
        
        Enhancement 7: Automatic topic detection from code patterns.
        
        Examples:
        - FastAPI code with @router.get() → ["routing", "path-parameters"]
        - React code with useState() → ["hooks", "state-management"]
        - pytest code with @pytest.fixture → ["fixtures", "testing"]
        
        Args:
            code: Code content to analyze
            library: Library name (e.g., "fastapi", "react", "pytest")
            
        Returns:
            List of detected topic names
        """
        if not self.enabled:
            return []
        
        topics = []
        code_lower = code.lower()
        
        # Library-specific topic mappings
        topic_mappings = {
            "fastapi": {
                "routing": ["@router.get", "@router.post", "@router.put", "@router.delete", "apirouter", "route"],
                "path-parameters": ["/{", "{id}", "path parameter", "pathparam"],
                "query-parameters": ["query(", "query parameter", "queryparam"],
                "dependencies": ["depends(", "dependency injection", "inject"],
                "middleware": ["middleware", "@app.middleware", "starlette.middleware"],
                "authentication": ["oauth2", "jwt", "security", "httponly", "authorization"],
                "validation": ["pydantic", "basemodel", "validator", "field"],
            },
            "react": {
                "hooks": ["usestate", "useeffect", "usecallback", "usememo", "useref"],
                "state-management": ["usestate", "usereducer", "context", "redux", "zustand"],
                "routing": ["router", "route", "link", "usenavigate", "browserrouter"],
                "components": ["component", "jsx", "props", "children"],
                "lifecycle": ["useeffect", "componentdidmount", "componentwillunmount"],
            },
            "pytest": {
                "fixtures": ["@pytest.fixture", "fixture", "conftest"],
                "parametrization": ["@pytest.mark.parametrize", "parametrize"],
                "mocking": ["mock", "patch", "magicmock", "mock.patch"],
                "async": ["pytest.mark.asyncio", "async def", "await"],
            },
            "django": {
                "models": ["models.model", "models.charfield", "models.foreignkey"],
                "views": ["view", "class view", "function view", "generic view"],
                "urls": ["urlpatterns", "path(", "re_path("],
                "admin": ["admin.site.register", "admin.modeladmin"],
                "orm": ["objects.filter", "objects.get", "queryset"],
            },
            "flask": {
                "routing": ["@app.route", "@blueprint.route", "route("],
                "templates": ["render_template", "jinja2", "template"],
                "request": ["request.form", "request.json", "request.args"],
            },
            "sqlalchemy": {
                "orm": ["session", "query(", "relationship", "backref"],
                "models": ["declarative_base", "column", "relationship"],
                "migrations": ["alembic", "migration", "upgrade", "downgrade"],
            },
        }
        
        if library.lower() in topic_mappings:
            for topic, keywords in topic_mappings[library.lower()].items():
                if any(keyword.lower() in code_lower for keyword in keywords):
                    topics.append(topic)
        
        return topics


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
