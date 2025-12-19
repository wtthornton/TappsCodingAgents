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
import urllib.parse
from typing import Any, Callable

import httpx

from ..mcp.gateway import MCPGateway

logger = logging.getLogger(__name__)


def _ensure_context7_api_key() -> str | None:
    """
    Ensure Context7 API key is available in environment.
    
    Checks environment variable first, then loads from encrypted storage if needed.
    Automatically sets the environment variable if loaded from storage.
    
    Returns:
        API key string if available, None otherwise
    """
    # First check environment variable
    api_key = os.getenv("CONTEXT7_API_KEY")
    if api_key:
        return api_key
    
    # Try loading from encrypted storage
    try:
        from .security import APIKeyManager
        
        key_manager = APIKeyManager()
        api_key = key_manager.load_api_key("context7")
        
        if api_key:
            # Set in environment for future use
            os.environ["CONTEXT7_API_KEY"] = api_key
            logger.debug("Loaded Context7 API key from encrypted storage")
            return api_key
    except Exception as e:
        logger.debug(f"Could not load API key from encrypted storage: {e}")
    
    return None


def check_mcp_tools_available(gateway: MCPGateway | None = None) -> bool:
    """
    Check if Context7 MCP tools are available via Cursor's MCP server.
    
    When running in Cursor mode, MCP tools are available through Cursor's MCP interface.
    This function checks if we're in Cursor mode and assumes MCP tools are available.
    
    Returns True if MCP tools are available (no API key needed).
    """
    # First, check if we're running in Cursor mode
    from ..core.runtime_mode import is_cursor_mode
    if is_cursor_mode():
        # In Cursor mode, MCP tools should be available through Cursor's MCP server
        # We can't directly check Cursor's MCP registry from Python, but if we're
        # in Cursor mode, we should try to use MCP tools
        logger.debug("Running in Cursor mode - assuming Context7 MCP tools are available")
        return True
    
    # If not in Cursor mode, check the custom gateway registry
    if gateway is None:
        try:
            gateway = MCPGateway()
        except Exception:
            return False
    
    try:
        # Check if Context7 MCP tools are registered in custom gateway
        tools = gateway.list_available_tools()
        tool_names = [tool.get("name", "") for tool in tools]
        
        return (
            "mcp_Context7_resolve-library-id" in tool_names
            and "mcp_Context7_get-library-docs" in tool_names
        )
    except Exception:
        return False


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
    import json
    from datetime import datetime
    from pathlib import Path
    log_path = Path.cwd() / ".cursor" / "debug.log"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "backup_client.py:65",
                "message": "create_fallback_http_client called",
                "data": {"api_key_at_creation": os.getenv("CONTEXT7_API_KEY") is not None},
                "timestamp": int(datetime.now().timestamp() * 1000)
            }) + "\n")
    except: pass
    # #endregion
    api_key = _ensure_context7_api_key()
    # #region agent log
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "backup_client.py:66",
                "message": "api_key captured in closure",
                "data": {"api_key_captured": api_key is not None, "key_length": len(api_key) if api_key else 0},
                "timestamp": int(datetime.now().timestamp() * 1000)
            }) + "\n")
    except: pass
    # #endregion
    if not api_key:
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B",
                    "location": "backup_client.py:67",
                    "message": "RETURNING None, None (no API key)",
                    "data": {},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except: pass
        # #endregion
        return None, None
    
    # Context7 API base URL - using correct API endpoint from documentation
    BASE_URL = os.getenv("CONTEXT7_API_URL", "https://context7.com/api/v2")
    
    def resolve_library_client(library_name: str) -> dict[str, Any]:
        """
        Fallback HTTP client for library resolution.
        Only used if MCP Gateway is not available.
        
        Uses Context7 Search API: GET /api/v2/search?query={library_name}
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
                    "hypothesisId": "F",
                    "location": "backup_client.py:resolve_library_client",
                    "message": "BEFORE API call",
                    "data": {"library": library_name, "api_key_set": api_key is not None},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except: pass
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
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "F",
                            "location": "backup_client.py:resolve_library_client",
                            "message": "AFTER API call",
                            "data": {"status_code": response.status_code, "library": library_name},
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + "\n")
                except: pass
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
                    try:
                        with open(log_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "F",
                                "location": "backup_client.py:resolve_library_client",
                                "message": "API SUCCESS",
                                "data": {"library": library_name, "matches_count": len(matches)},
                                "timestamp": int(datetime.now().timestamp() * 1000)
                            }) + "\n")
                    except: pass
                    # #endregion
                    return {
                        "success": True,
                        "result": {
                            "matches": matches,
                        },
                    }
                elif response.status_code == 429:
                    # Quota exceeded - provide helpful error message
                    try:
                        error_data = response.json()
                        quota_message = error_data.get("message", "Daily quota exceeded")
                    except Exception:
                        quota_message = "Daily quota exceeded"
                    # #region agent log
                    try:
                        with open(log_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "F",
                                "location": "backup_client.py:resolve_library_client",
                                "message": "API QUOTA EXCEEDED",
                                "data": {"status_code": 429, "library": library_name, "message": quota_message},
                                "timestamp": int(datetime.now().timestamp() * 1000)
                            }) + "\n")
                    except: pass
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
                    try:
                        with open(log_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "F",
                                "location": "backup_client.py:resolve_library_client",
                                "message": "API ERROR",
                                "data": {"status_code": response.status_code, "library": library_name, "response_text": response.text[:200]},
                                "timestamp": int(datetime.now().timestamp() * 1000)
                            }) + "\n")
                    except: pass
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
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "F",
                        "location": "backup_client.py:resolve_library_client",
                        "message": "CONNECTION ERROR",
                        "data": {"library": library_name, "error": str(e)},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + "\n")
            except: pass
            # #endregion
            return {
                "success": False,
                "error": "Context7 API endpoint not reachable",
                "result": {
                    "matches": [],
                },
            }
        except Exception as e:
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "F",
                        "location": "backup_client.py:resolve_library_client",
                        "message": "EXCEPTION",
                        "data": {"library": library_name, "error": str(e)},
                        "timestamp": int(datetime.now().timestamp() * 1000)
                    }) + "\n")
            except: pass
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
) -> tuple[MCPGateway | None, bool, Callable[[str], dict[str, Any]] | None, Callable[[str, str | None, str | None, int | None], dict[str, Any]] | None]:
    """
    Get Context7 client with automatic fallback.
    
    Pattern:
    1. Prefer MCP Gateway (Cursor's MCP server) - no API key needed
    2. Fallback to direct HTTP calls if MCP not available - requires CONTEXT7_API_KEY
    
    Args:
        mcp_gateway: Optional MCPGateway instance (creates new if None)
    
    Returns:
        Tuple of (gateway, use_mcp, resolve_client, get_docs_client):
        - gateway: MCPGateway instance
        - use_mcp: True if MCP tools are available, False if using fallback
        - resolve_client: HTTP client function (only if use_mcp=False)
        - get_docs_client: HTTP client function (only if use_mcp=False)
    """
    if mcp_gateway is None:
        try:
            mcp_gateway = MCPGateway()
        except Exception:
            mcp_gateway = None
    
    # Check if MCP tools are available
    if mcp_gateway and check_mcp_tools_available(mcp_gateway):
        # Use MCP Gateway - no API key needed!
        return mcp_gateway, True, None, None
    
    # Fallback to direct HTTP - requires API key
    api_available = check_context7_api_available()
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
                "hypothesisId": "C",
                "location": "backup_client.py:268",
                "message": "get_context7_client_with_fallback check result",
                "data": {"api_available": api_available, "mcp_available": mcp_gateway is not None},
                "timestamp": int(datetime.now().timestamp() * 1000)
            }) + "\n")
    except: pass
    # #endregion
    if not api_available:
        # Neither MCP nor API key available
        logger.info(
            "Context7 not available: MCP tools not found and CONTEXT7_API_KEY not set. "
            "Continuing without Context7 functionality."
        )
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "location": "backup_client.py:270",
                    "message": "RETURNING None clients (API not available)",
                    "data": {},
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }) + "\n")
        except: pass
        # #endregion
        return mcp_gateway, False, None, None
    
    resolve_client, get_docs_client = create_fallback_http_client()
    # #region agent log
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "backup_client.py:272",
                "message": "clients created",
                "data": {"resolve_client": resolve_client is not None, "get_docs_client": get_docs_client is not None},
                "timestamp": int(datetime.now().timestamp() * 1000)
            }) + "\n")
    except: pass
    # #endregion
    return mcp_gateway, False, resolve_client, get_docs_client


async def call_context7_resolve_with_fallback(
    library_name: str,
    mcp_gateway: MCPGateway | None = None,
) -> dict[str, Any]:
    """
    Call Context7 resolve-library-id with automatic fallback.
    
    Args:
        library_name: Library name to resolve
        mcp_gateway: Optional MCPGateway instance
    
    Returns:
        Dictionary with resolve result (matches MCP tool response format)
    """
    gateway, use_mcp, resolve_client, _ = get_context7_client_with_fallback(mcp_gateway)
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
                "hypothesisId": "D",
                "location": "backup_client.py:290",
                "message": "call_context7_resolve_with_fallback got clients",
                "data": {"use_mcp": use_mcp, "resolve_client": resolve_client is not None, "library": library_name},
                "timestamp": int(datetime.now().timestamp() * 1000)
            }) + "\n")
    except: pass
    # #endregion
    if use_mcp and gateway:
        # Use MCP Gateway - Cursor's MCP server handles API key
        try:
            # In Cursor mode, the custom gateway may not have the tools registered
            # Try to call the tool, but if it fails, fall back to HTTP
            result = await gateway.call_tool(
                "mcp_Context7_resolve-library-id",
                libraryName=library_name,
            )
            return result
        except (ValueError, KeyError) as e:
            # Tool not found in custom gateway registry - this is expected in Cursor mode
            # The tools are in Cursor's MCP server, not the custom gateway
            # Fall back to HTTP client if available
            logger.debug(
                f"Context7 MCP tool not found in custom gateway for library '{library_name}'. "
                f"This is expected in Cursor mode where tools are in Cursor's MCP server. "
                f"Falling back to HTTP client if available."
            )
            if resolve_client:
                return resolve_client(library_name)
            # If no HTTP fallback, indicate MCP tools should be used by AI assistant
            logger.info(
                f"Context7 MCP tools are available in Cursor but cannot be called directly from Python. "
                f"AI assistant should use MCP tools: mcp_Context7_resolve-library-id with libraryName='{library_name}'. "
                f"Continuing without Context7 documentation in this Python process."
            )
            return {
                "success": False,
                "error": "Context7 MCP tools available in Cursor but require AI assistant to call them",
                "result": {"matches": []},
            }
        except Exception as e:
            # Other errors - try fallback
            logger.debug(f"Context7 MCP Gateway call failed for library '{library_name}': {e}. Trying fallback.", exc_info=True)
            if resolve_client:
                return resolve_client(library_name)
            logger.info(
                f"Context7 not available for library '{library_name}': MCP Gateway call failed and no fallback available. "
                f"Continuing without Context7 documentation."
            )
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
    
    Args:
        context7_id: Context7-compatible library ID
        topic: Optional topic name
        mode: "code" or "info" (default: "code")
        page: Page number (default: 1)
        mcp_gateway: Optional MCPGateway instance
    
    Returns:
        Dictionary with docs result (matches MCP tool response format)
    """
    gateway, use_mcp, _, get_docs_client = get_context7_client_with_fallback(mcp_gateway)
    
    if use_mcp and gateway:
        # Use MCP Gateway - Cursor's MCP server handles API key
        try:
            # In Cursor mode, the custom gateway may not have the tools registered
            # Try to call the tool, but if it fails, fall back to HTTP
            result = await gateway.call_tool(
                "mcp_Context7_get-library-docs",
                context7CompatibleLibraryID=context7_id,
                topic=topic,
                mode=mode,
                page=page,
            )
            return result
        except (ValueError, KeyError) as e:
            # Tool not found in custom gateway registry - this is expected in Cursor mode
            # The tools are in Cursor's MCP server, not the custom gateway
            # Fall back to HTTP client if available
            logger.debug(
                f"Context7 MCP tool not found in custom gateway for library '{context7_id}' (topic: {topic}). "
                f"This is expected in Cursor mode where tools are in Cursor's MCP server. "
                f"Falling back to HTTP client if available."
            )
            if get_docs_client:
                return get_docs_client(context7_id, topic, mode, page)
            # If no HTTP fallback, indicate MCP tools should be used by AI assistant
            logger.info(
                f"Context7 MCP tools are available in Cursor but cannot be called directly from Python. "
                f"AI assistant should use MCP tools: mcp_Context7_get-library-docs with "
                f"context7CompatibleLibraryID='{context7_id}', topic='{topic}', mode='{mode}', page={page}. "
                f"Continuing without Context7 documentation in this Python process."
            )
            return {
                "success": False,
                "error": "Context7 MCP tools available in Cursor but require AI assistant to call them",
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
            logger.info(
                f"Context7 not available for library '{context7_id}' (topic: {topic}): "
                f"MCP Gateway call failed and no fallback available. Continuing without Context7 documentation."
            )
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

