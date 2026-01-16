"""
Context7 Backup Client - HTTP fallback for Context7 API calls.

This module provides a backup mechanism for Context7 API calls when MCP Gateway
is not available. It implements the same pattern used in successful integration tests.

Pattern:
1. Prefer MCP Gateway (Cursor's MCP server) - no API key needed
2. Fallback to direct HTTP calls if MCP not available - requires CONTEXT7_API_KEY
"""

import logging
import os
import time
import urllib.parse
from typing import Any, Callable

import httpx

from ..core.debug_logger import write_debug_log
from ..mcp.gateway import MCPGateway

logger = logging.getLogger(__name__)

_CONTEXT7_QUOTA_EXCEEDED: bool = False
_CONTEXT7_QUOTA_MESSAGE: str | None = None


def is_context7_quota_exceeded() -> bool:
    """Return True if a Context7 quota-exceeded response was observed in this process."""
    return _CONTEXT7_QUOTA_EXCEEDED


def get_context7_quota_message() -> str | None:
    """Return the last Context7 quota-exceeded message observed in this process."""
    return _CONTEXT7_QUOTA_MESSAGE


def _mark_context7_quota_exceeded(message: str) -> None:
    """Mark Context7 quota as exceeded (best-effort) to suppress repeated HTTP calls and log spam."""
    global _CONTEXT7_QUOTA_EXCEEDED, _CONTEXT7_QUOTA_MESSAGE
    _CONTEXT7_QUOTA_MESSAGE = message
    if _CONTEXT7_QUOTA_EXCEEDED:
        return
    _CONTEXT7_QUOTA_EXCEEDED = True
    logger.warning(
        "Context7 API quota exceeded. Further Context7 HTTP fallback calls will be skipped for this run."
    )


def _ensure_context7_api_key() -> str | None:
    """
    Ensure Context7 API key is available in environment.
    
    Checks environment variable first, then loads from encrypted storage if needed.
    Automatically sets the environment variable if loaded from storage.
    
    Returns:
        API key string if available, None otherwise
    """
    # #region agent log
    from ..core.debug_logger import write_debug_log
    write_debug_log(
        {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "A",
            "message": "_ensure_context7_api_key called",
            "data": {"env_key_exists": os.getenv("CONTEXT7_API_KEY") is not None},
        },
        location="backup_client.py:_ensure_context7_api_key:entry",
    )
    # #endregion
    
    # First check environment variable
    api_key = os.getenv("CONTEXT7_API_KEY")
    # #region agent log
    write_debug_log(
        {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "A",
            "message": "Checked environment variable",
            "data": {"api_key_from_env": api_key is not None, "key_length": len(api_key) if api_key else 0},
        },
        location="backup_client.py:_ensure_context7_api_key:env_check",
    )
    # #endregion
    if api_key:
        return api_key
    
    # Try loading from encrypted storage
    try:
        from .security import APIKeyManager
        
        key_manager = APIKeyManager()
        api_key = key_manager.load_api_key("context7")
        # #region agent log
        write_debug_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "message": "Loaded from encrypted storage",
                "data": {"api_key_loaded": api_key is not None, "key_length": len(api_key) if api_key else 0},
            },
            location="backup_client.py:_ensure_context7_api_key:storage_load",
        )
        # #endregion
        
        if api_key:
            # Set in environment for future use
            os.environ["CONTEXT7_API_KEY"] = api_key
            logger.debug("Loaded Context7 API key from encrypted storage")
            # #region agent log
            write_debug_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "message": "API key set in environment",
                    "data": {"env_set_success": True},
                },
                location="backup_client.py:_ensure_context7_api_key:env_set",
            )
            # #endregion
            return api_key
    except Exception as e:
        logger.debug(f"Could not load API key from encrypted storage: {e}")
        # #region agent log
        write_debug_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "message": "Failed to load from storage",
                "data": {"error": str(e)},
            },
            location="backup_client.py:_ensure_context7_api_key:error",
        )
        # #endregion
    
    # #region agent log
    write_debug_log(
        {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "A",
            "message": "Returning None - no API key available",
            "data": {},
        },
        location="backup_client.py:_ensure_context7_api_key:return_none",
    )
    # #endregion
    return None


def check_mcp_tools_available(gateway: MCPGateway | None = None) -> tuple[bool, str]:
    """
    Check if Context7 MCP tools are available via Cursor's MCP server or local gateway.
    
    R1: Improved detection to distinguish between Cursor MCP tools and local gateway.
    
    Returns:
        Tuple of (available: bool, source: str) where source is:
        - "cursor_mcp" if in Cursor mode (tools available via Cursor's MCP server)
        - "local_gateway" if tools registered in local MCPGateway
        - "none" if not available
    """
    # First, check if we're running in Cursor mode
    from ..core.runtime_mode import is_cursor_mode
    if is_cursor_mode():
        # In Cursor mode, MCP tools are available through Cursor's MCP server
        # Python code cannot directly call them, but AI assistant can
        logger.debug("Running in Cursor mode - Context7 MCP tools available via Cursor's MCP server")
        return True, "cursor_mcp"
    
    # If not in Cursor mode, check the custom gateway registry
    if gateway is None:
        try:
            gateway = MCPGateway()
        except Exception:
            return False, "none"
    
    try:
        # Check if Context7 MCP tools are registered in custom gateway
        tools = gateway.list_available_tools()
        tool_names = [tool.get("name", "") for tool in tools]
        
        has_tools = (
            "mcp_Context7_resolve-library-id" in tool_names
            and "mcp_Context7_get-library-docs" in tool_names
        )
        return has_tools, "local_gateway" if has_tools else "none"
    except Exception:
        return False, "none"


def check_context7_api_available() -> bool:
    """
    Check if Context7 API key is available (for fallback direct HTTP calls).
    
    Automatically loads from encrypted storage if not in environment.
    
    Returns True if API key is set, False otherwise.
    """
    api_key = _ensure_context7_api_key()
    return api_key is not None


def create_fallback_http_client() -> tuple[Callable[[str], dict[str, Any]], Callable[[str, str | None, str | None, int | None], Any] | None]:
    """
    Create fallback HTTP client functions for direct API calls.
    
    Only used if MCP Gateway tools are not available.
    Requires CONTEXT7_API_KEY environment variable.
    
    Returns:
        Tuple of (resolve_library_client, get_docs_client) or (None, None) if API key not available
    """
    # #region agent log
    from ..core.debug_logger import write_debug_log
    write_debug_log(
        {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "B",
            "message": "create_fallback_http_client called",
            "data": {"api_key_at_creation": os.getenv("CONTEXT7_API_KEY") is not None},
        },
        location="backup_client.py:create_fallback_http_client:entry",
    )
    # #endregion
    api_key = _ensure_context7_api_key()
    # #region agent log
    write_debug_log(
        {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "B",
            "message": "API key check after _ensure_context7_api_key",
            "data": {"api_key_available": api_key is not None, "key_length": len(api_key) if api_key else 0, "env_key_after": os.getenv("CONTEXT7_API_KEY") is not None},
        },
        location="backup_client.py:create_fallback_http_client:api_key_check",
    )
    # #endregion
    if not api_key:
        # #region agent log
        write_debug_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "message": "RETURNING None, None (no API key)",
                "data": {},
            },
            location="backup_client.py:67",
        )
        # #endregion
        return None, None
    
    # Context7 API base URL - using correct API endpoint from documentation
    BASE_URL = os.getenv("CONTEXT7_API_URL", "https://context7.com/api/v2")
    
    def resolve_library_client(
        library_name: str,
        offline_mode: bool = False
    ) -> dict[str, Any]:
        """
        Fallback HTTP client for library resolution.
        Only used if MCP Gateway is not available.
        
        Uses Context7 Search API: GET /api/v2/search?query={library_name}
        
        Args:
            library_name: Name of library to resolve
            offline_mode: If True, return cached result or empty matches without network call
        """
        # Check offline mode
        from ..core.offline_mode import OfflineMode
        
        if offline_mode or OfflineMode.is_offline():
            return {
                "success": False,
                "error": "Offline mode",
                "result": {"matches": []}
            }

        # Fast-fail if quota already exceeded (avoid repeated HTTP calls / log spam)
        if is_context7_quota_exceeded():
            msg = get_context7_quota_message() or "Monthly quota exceeded"
            return {
                "success": False,
                "error": f"Context7 API quota exceeded: {msg}",
                "result": {"matches": []},
            }
        # #region agent log
        from ..core.debug_logger import write_debug_log
        write_debug_log(
            {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "F",
                "message": "BEFORE API call",
                "data": {"library": library_name, "api_key_set": api_key is not None},
            },
            location="backup_client.py:resolve_library_client",
        )
        # #endregion
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{BASE_URL}/search",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    params={"query": library_name},
                )
                # #region agent log
                write_debug_log(
                    {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "F",
                        "message": "AFTER API call",
                        "data": {"status_code": response.status_code, "library": library_name},
                    },
                    location="backup_client.py:resolve_library_client",
                )
                # #endregion
                
                if response.status_code == 200:
                    data = response.json()
                    # Format search results to match MCP tool response format
                    # Search API returns array of results, convert to matches format
                    results = data if isinstance(data, list) else data.get("results", [])
                    matches = []
                    for result in results:
                        matches.append({
                            "id": result.get("id"),
                            "title": result.get("title"),
                            "description": result.get("description"),
                            "benchmarkScore": result.get("benchmarkScore"),
                        })
                    # #region agent log
                    write_debug_log(
                        {
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "F",
                            "message": "API SUCCESS",
                            "data": {"library": library_name, "matches_count": len(matches)},
                        },
                        location="backup_client.py:resolve_library_client",
                    )
                    # #endregion
                    return {
                        "success": True,
                        "result": {
                            "matches": matches,
                        },
                    }
                elif response.status_code == 429:
                    # CRITICAL FIX: Quota exceeded - mark immediately and open circuit breaker
                    try:
                        error_data = response.json()
                        quota_message = error_data.get("message", "Daily quota exceeded")
                    except Exception:
                        quota_message = "Daily quota exceeded"
                    
                    # Mark quota as exceeded globally (this prevents future API calls)
                    _mark_context7_quota_exceeded(quota_message)
                    
                    # CRITICAL FIX: Open circuit breaker immediately on quota error
                    # This prevents subsequent parallel calls from attempting API requests
                    try:
                        from .circuit_breaker import get_context7_circuit_breaker, CircuitState
                        circuit_breaker = get_context7_circuit_breaker()
                        # Force open circuit breaker immediately (bypass threshold)
                        if hasattr(circuit_breaker, '_stats'):
                            circuit_breaker._stats.state = CircuitState.OPEN
                            circuit_breaker._stats.last_failure_time = time.time()
                            circuit_breaker._stats.last_state_change = time.time()
                            logger.warning(
                                f"Context7 circuit breaker opened immediately due to quota error (429). "
                                f"Subsequent requests will be rejected without API calls."
                            )
                    except Exception as cb_error:
                        logger.debug(f"Could not open circuit breaker on quota error: {cb_error}")
                    
                    # #region agent log
                    write_debug_log(
                        {
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "F",
                            "message": "API QUOTA EXCEEDED",
                            "data": {"status_code": 429, "library": library_name, "message": quota_message},
                        },
                        location="backup_client.py:resolve_library_client",
                    )
                    # #endregion
                    return {
                        "success": False,
                        "error": f"Context7 API quota exceeded: {quota_message}",
                        "result": {
                            "matches": [],
                        },
                    }
                else:
                    # #region agent log
                    write_debug_log(
                        {
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "F",
                            "message": "API ERROR",
                            "data": {"status_code": response.status_code, "library": library_name, "response_text": response.text[:200]},
                        },
                        location="backup_client.py:resolve_library_client",
                    )
                    # #endregion
                    return {
                        "success": False,
                        "error": f"API returned status {response.status_code}",
                        "result": {
                            "matches": [],
                        },
                    }
        except httpx.ConnectError as e:
            # #region agent log
            write_debug_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "F",
                    "message": "CONNECTION ERROR",
                    "data": {"library": library_name, "error": str(e)},
                },
                location="backup_client.py:resolve_library_client",
            )
            # #endregion
            
            # Record connection failure for offline mode detection
            from ..core.offline_mode import OfflineMode
            OfflineMode.record_connection_failure()
            
            # Return error with context (don't raise exception to allow graceful fallback)
            import uuid
            request_id = str(uuid.uuid4())
            return {
                "success": False,
                "error": "Context7 API endpoint not reachable",
                "error_details": {
                    "operation": "Context7 library lookup",
                    "request_id": request_id,
                    "library": library_name,
                    "original_error": str(e),
                },
                "result": {
                    "matches": [],
                },
            }
        except Exception as e:
            # #region agent log
            write_debug_log(
                {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "F",
                    "message": "EXCEPTION",
                    "data": {"library": library_name, "error": str(e)},
                },
                location="backup_client.py:resolve_library_client",
            )
            # #endregion
            return {
                "success": False,
                "error": str(e),
                "result": {
                    "matches": [],
                },
            }
    
    def get_docs_client(
        context7_id: str, topic: str | None = None, mode: str = "code", page: int = 1
    ) -> dict[str, Any]:
        """
        Fallback HTTP client for documentation fetch.
        Only used if MCP Gateway is not available.
        
        Uses Context7 Docs API: GET /api/v2/docs/{mode}/{library_id}?type=json&topic={topic}&page={page}
        - mode: "code" or "info"
        - type: "json" (for structured response) or "txt"
        """
        # Fast-fail if quota already exceeded (avoid repeated HTTP calls / log spam)
        if is_context7_quota_exceeded():
            msg = get_context7_quota_message() or "Monthly quota exceeded"
            return {"success": False, "error": f"Context7 API quota exceeded: {msg}", "result": {}}

        try:
            with httpx.Client(timeout=30.0) as client:
                # Remove leading slash from context7_id if present (API expects format like "vercel/next.js")
                library_id = context7_id.lstrip("/")
                
                # Build endpoint: /api/v2/docs/{mode}/{library_id}
                endpoint = f"{BASE_URL}/docs/{mode}/{library_id}"
                
                # Build query parameters
                params = {"type": "json", "page": page}
                if topic:
                    params["topic"] = topic
                
                response = client.get(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    params=params,
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # Format to match MCP tool response format
                        # Context7 API returns snippets array, extract content
                        if isinstance(data, dict):
                            snippets = data.get("snippets", [])
                            # Combine snippets into markdown content
                            content_parts = []
                            for snippet in snippets:
                                if isinstance(snippet, dict):
                                    # For code mode: extract code snippets
                                    if mode == "code":
                                        code_list = snippet.get("codeList", [])
                                        for code_item in code_list:
                                            code = code_item.get("code", "")
                                            title = snippet.get("codeTitle", "")
                                            if title:
                                                content_parts.append(f"## {title}\n")
                                            if code:
                                                content_parts.append(f"```{code_item.get('language', '')}\n{code}\n```\n")
                                    # For info mode: extract content
                                    elif mode == "info":
                                        content = snippet.get("content", "")
                                        breadcrumb = snippet.get("breadcrumb", "")
                                        if breadcrumb:
                                            content_parts.append(f"## {breadcrumb}\n")
                                        if content:
                                            content_parts.append(f"{content}\n")
                            
                            content = "\n".join(content_parts) if content_parts else response.text
                            
                            return {
                                "success": True,
                                "result": {
                                    "content": content,
                                },
                            }
                        # Fallback: return as string
                        return {
                            "success": True,
                            "result": {
                                "content": response.text,
                            },
                        }
                    except Exception:
                        return {
                            "success": True,
                            "result": {
                                "content": response.text,
                            },
                        }
                elif response.status_code == 429:
                    # CRITICAL FIX: Quota exceeded - mark immediately and open circuit breaker
                    try:
                        error_data = response.json()
                        quota_message = error_data.get("message", "Daily quota exceeded")
                    except Exception:
                        quota_message = "Daily quota exceeded"
                    
                    # Mark quota as exceeded globally (this prevents future API calls)
                    _mark_context7_quota_exceeded(quota_message)
                    
                    # CRITICAL FIX: Open circuit breaker immediately on quota error
                    # This prevents subsequent parallel calls from attempting API requests
                    try:
                        from .circuit_breaker import get_context7_circuit_breaker, CircuitState
                        circuit_breaker = get_context7_circuit_breaker()
                        # Force open circuit breaker immediately (bypass threshold)
                        if hasattr(circuit_breaker, '_stats'):
                            circuit_breaker._stats.state = CircuitState.OPEN
                            circuit_breaker._stats.last_failure_time = time.time()
                            circuit_breaker._stats.last_state_change = time.time()
                            logger.warning(
                                f"Context7 circuit breaker opened immediately due to quota error (429). "
                                f"Subsequent requests will be rejected without API calls."
                            )
                    except Exception as cb_error:
                        logger.debug(f"Could not open circuit breaker on quota error: {cb_error}")
                    
                    return {
                        "success": False,
                        "error": f"Context7 API quota exceeded: {quota_message}",
                        "result": {},
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API returned status {response.status_code}",
                        "result": {},
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": {},
            }
    
    return resolve_library_client, get_docs_client


def get_context7_client_with_fallback(
    mcp_gateway: MCPGateway | None = None,
) -> tuple[MCPGateway | None, bool, str, Callable[[str], dict[str, Any]] | None, Callable[[str, str | None, str | None, int | None], dict[str, Any]] | None]:
    """
    Get Context7 client with automatic fallback.
    
    R1: Improved to distinguish between Cursor MCP tools and local gateway.
    
    Pattern:
    1. Prefer MCP Gateway (Cursor's MCP server) - no API key needed
    2. Fallback to direct HTTP calls if MCP not available - requires CONTEXT7_API_KEY
    
    Args:
        mcp_gateway: Optional MCPGateway instance (creates new if None)
    
    Returns:
        Tuple of (gateway, use_mcp, mcp_source, resolve_client, get_docs_client):
        - gateway: MCPGateway instance (may be None in Cursor mode)
        - use_mcp: True if MCP tools are available, False if using fallback
        - mcp_source: "cursor_mcp", "local_gateway", or "none"
        - resolve_client: HTTP client function (only if use_mcp=False)
        - get_docs_client: HTTP client function (only if use_mcp=False)
    """
    if mcp_gateway is None:
        try:
            mcp_gateway = MCPGateway()
        except Exception:
            mcp_gateway = None
    
    # Check if MCP tools are available (R1: improved detection)
    mcp_available, mcp_source = check_mcp_tools_available(mcp_gateway)
    
    # CRITICAL FIX: Python code cannot call Cursor's MCP tools directly
    # Even though MCP tools are "available" in Cursor mode, Python code must use HTTP fallback
    # Only the AI assistant (via Cursor chat) can use MCP tools directly
    from ..core.runtime_mode import is_cursor_mode
    # #region agent log
    from ..core.debug_logger import write_debug_log
    write_debug_log(
        {
            "sessionId": "debug-session",
            "runId": "run2",
            "hypothesisId": "F",
            "message": "Before MCP fix check",
            "data": {"mcp_available": mcp_available, "mcp_source": mcp_source, "is_cursor_mode": is_cursor_mode()},
        },
        location="backup_client.py:get_context7_client_with_fallback:before_fix",
    )
    # #endregion
    if mcp_available and mcp_source == "cursor_mcp":
        # In Cursor mode, MCP tools are available to AI assistant but NOT to Python code
        # Force HTTP fallback for Python code execution
        logger.debug(
            "Context7 MCP tools available in Cursor but Python code cannot call them. "
            "Using HTTP fallback with API key."
        )
        # #region agent log
        write_debug_log(
            {
                "sessionId": "debug-session",
                "runId": "run2",
                "hypothesisId": "F",
                "message": "FIX APPLIED: Forcing HTTP fallback for Cursor MCP",
                "data": {"mcp_available_before": True, "mcp_available_after": False},
            },
            location="backup_client.py:get_context7_client_with_fallback:fix_applied",
        )
        # #endregion
        mcp_available = False  # Force HTTP fallback
    
    if mcp_available:
        # Use MCP - no API key needed!
        # This path is only for local gateway (not Cursor MCP)
        return mcp_gateway, True, mcp_source, None, None
    
    # Fallback to direct HTTP - requires API key
    api_available = check_context7_api_available()
    # #region agent log
    write_debug_log(
        {
            "sessionId": "debug-session",
            "runId": "run2",
            "hypothesisId": "F",
            "message": "Using HTTP fallback path",
            "data": {"mcp_available": mcp_available, "api_available": api_available},
        },
        location="backup_client.py:get_context7_client_with_fallback:http_fallback",
    )
    # #endregion
    if not api_available:
        # R2/R3: Neither MCP nor API key available - provide clear error message
        from ..core.runtime_mode import is_cursor_mode
        if is_cursor_mode():
            # In Cursor mode, MCP tools should be available but Python can't call them directly
            logger.debug(
                "Context7 MCP tools available in Cursor but cannot be called from Python. "
                "AI assistant should use MCP tools directly."
            )
        else:
            # R3: Clear error message for headless mode
            logger.warning(
                "Context7 not available: MCP tools not found and CONTEXT7_API_KEY not set. "
                "To enable Context7:\n"
                "  1. Set CONTEXT7_API_KEY environment variable, OR\n"
                "  2. Configure Context7 MCP server\n"
                "Continuing without Context7 functionality."
            )
        return mcp_gateway, False, "none", None, None
    
    resolve_client, get_docs_client = create_fallback_http_client()
    # #region agent log
    write_debug_log(
        {
            "sessionId": "debug-session",
            "runId": "run2",
            "hypothesisId": "F",
            "message": "Returning HTTP fallback clients",
            "data": {"use_mcp": False, "resolve_client_created": resolve_client is not None, "get_docs_client_created": get_docs_client is not None},
        },
        location="backup_client.py:get_context7_client_with_fallback:return_http",
    )
    # #endregion
    return mcp_gateway, False, "none", resolve_client, get_docs_client


async def call_context7_resolve_with_fallback(
    library_name: str,
    mcp_gateway: MCPGateway | None = None,
) -> dict[str, Any]:
    """
    Call Context7 resolve-library-id with automatic fallback.
    
    R1: Improved to handle Cursor MCP tools vs local gateway distinction.
    
    Args:
        library_name: Library name to resolve
        mcp_gateway: Optional MCPGateway instance
    
    Returns:
        Dictionary with resolve result (matches MCP tool response format)
    """
    gateway, use_mcp, mcp_source, resolve_client, _ = get_context7_client_with_fallback(mcp_gateway)
    # #region agent log
    from ..core.debug_logger import write_debug_log
    write_debug_log(
        {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "D",
            "message": "call_context7_resolve_with_fallback got clients",
            "data": {"use_mcp": use_mcp, "resolve_client": resolve_client is not None, "library": library_name},
        },
        location="backup_client.py:call_context7_resolve_with_fallback",
    )
    # #endregion
    if use_mcp:
        # R1: Handle Cursor MCP vs local gateway differently
        if mcp_source == "cursor_mcp":
            # In Cursor mode, Python code cannot directly call MCP tools
            # AI assistant should use MCP tools: mcp_Context7_resolve-library-id
            if resolve_client:
                # Allow HTTP fallback for CLI commands in Cursor mode
                logger.debug(
                    f"Context7 MCP tools available in Cursor for library '{library_name}', "
                    f"but using HTTP fallback for Python code path. "
                    f"AI assistant should use MCP tools directly for better performance."
                )
                return resolve_client(library_name)
            else:
                # No HTTP fallback - indicate MCP tools should be used
                logger.info(
                    f"Context7 MCP tools available in Cursor but cannot be called from Python. "
                    f"AI assistant should use MCP tools: mcp_Context7_resolve-library-id with libraryName='{library_name}'."
                )
                return {
                    "success": False,
                    "error": "Context7 MCP tools available in Cursor but require AI assistant to call them. "
                             "Use MCP tools directly: mcp_Context7_resolve-library-id",
                    "result": {"matches": []},
                }
        elif mcp_source == "local_gateway" and gateway:
            # Local gateway has tools registered - try to call them
            try:
                result = await gateway.call_tool(
                    "mcp_Context7_resolve-library-id",
                    libraryName=library_name,
                )
                return result
            except (ValueError, KeyError) as e:
                # Tool not found - fall back to HTTP if available
                logger.debug(
                    f"Context7 MCP tool not found in local gateway for library '{library_name}': {e}. "
                    f"Falling back to HTTP client if available."
                )
                if resolve_client:
                    return resolve_client(library_name)
                return {
                    "success": False,
                    "error": f"Context7 MCP tool not found: {e}",
                    "result": {"matches": []},
                }
            except Exception as e:
                # Other errors - try fallback
                logger.debug(
                    f"Context7 MCP Gateway call failed for library '{library_name}': {e}. Trying fallback.",
                    exc_info=True
                )
                if resolve_client:
                    return resolve_client(library_name)
                return {
                    "success": False,
                    "error": f"MCP Gateway call failed: {e}",
                    "result": {"matches": []},
                }
    elif resolve_client:
        # Fallback: Use direct HTTP client
        return resolve_client(library_name)
    else:
        logger.info(
            f"Context7 not available for library '{library_name}': MCP tools not found and CONTEXT7_API_KEY not set. "
            f"Continuing without Context7 documentation."
        )
        return {
            "success": False,
            "error": "Context7 not available: MCP tools not found and CONTEXT7_API_KEY not set",
            "result": {"matches": []},
        }


async def call_context7_get_docs_with_fallback(
    context7_id: str,
    topic: str | None = None,
    mode: str = "code",
    page: int = 1,
    mcp_gateway: MCPGateway | None = None,
) -> dict[str, Any]:
    """
    Call Context7 get-library-docs with automatic fallback.
    
    R1: Improved to handle Cursor MCP tools vs local gateway distinction.
    
    Args:
        context7_id: Context7-compatible library ID
        topic: Optional topic name
        mode: "code" or "info" (default: "code")
        page: Page number (default: 1)
        mcp_gateway: Optional MCPGateway instance
    
    Returns:
        Dictionary with docs result (matches MCP tool response format)
    """
    gateway, use_mcp, mcp_source, _, get_docs_client = get_context7_client_with_fallback(mcp_gateway)
    
    if use_mcp:
        # R1: Handle Cursor MCP vs local gateway differently
        if mcp_source == "cursor_mcp":
            # In Cursor mode, Python code cannot directly call MCP tools
            # AI assistant should use MCP tools: mcp_Context7_get-library-docs
            if get_docs_client:
                # Allow HTTP fallback for CLI commands in Cursor mode
                logger.debug(
                    f"Context7 MCP tools available in Cursor for library '{context7_id}' (topic: {topic}), "
                    f"but using HTTP fallback for Python code path. "
                    f"AI assistant should use MCP tools directly for better performance."
                )
                return get_docs_client(context7_id, topic, mode, page)
            else:
                # No HTTP fallback - indicate MCP tools should be used
                logger.info(
                    f"Context7 MCP tools available in Cursor but cannot be called from Python. "
                    f"AI assistant should use MCP tools: mcp_Context7_get-library-docs with "
                    f"context7CompatibleLibraryID='{context7_id}', topic='{topic}', mode='{mode}', page={page}."
                )
                return {
                    "success": False,
                    "error": "Context7 MCP tools available in Cursor but require AI assistant to call them. "
                             "Use MCP tools directly: mcp_Context7_get-library-docs",
                    "result": {},
                }
        elif mcp_source == "local_gateway" and gateway:
            # Local gateway has tools registered - try to call them
            try:
                result = await gateway.call_tool(
                    "mcp_Context7_get-library-docs",
                    context7CompatibleLibraryID=context7_id,
                    topic=topic,
                    mode=mode,
                    page=page,
                )
                return result
            except (ValueError, KeyError) as e:
                # Tool not found - fall back to HTTP if available
                logger.debug(
                    f"Context7 MCP tool not found in local gateway for library '{context7_id}' (topic: {topic}): {e}. "
                    f"Falling back to HTTP client if available."
                )
                if get_docs_client:
                    return get_docs_client(context7_id, topic, mode, page)
                return {
                    "success": False,
                    "error": f"Context7 MCP tool not found: {e}",
                    "result": {},
                }
            except Exception as e:
                # Other errors - try fallback
                logger.debug(
                    f"Context7 MCP Gateway call failed for library '{context7_id}' (topic: {topic}): {e}. Trying fallback.",
                    exc_info=True
                )
                if get_docs_client:
                    return get_docs_client(context7_id, topic, mode, page)
                return {
                    "success": False,
                    "error": f"MCP Gateway call failed: {e}",
                    "result": {},
                }
    elif get_docs_client:
        # Fallback: Use direct HTTP client
        return get_docs_client(context7_id, topic, mode, page)
    else:
        logger.info(
            f"Context7 not available for library '{context7_id}' (topic: {topic}): "
            f"MCP tools not found and CONTEXT7_API_KEY not set. Continuing without Context7 documentation."
        )
        return {
            "success": False,
            "error": "Context7 not available: MCP tools not found and CONTEXT7_API_KEY not set",
            "result": {},
        }

