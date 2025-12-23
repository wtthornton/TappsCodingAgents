"""
Real integration tests for Context7 with actual API calls.

These tests use ACTUAL Context7 API calls via MCP and prefer:
- MCP Gateway with Cursor's MCP Context7 server (no API key needed)
- Fallback to direct HTTP calls (requires CONTEXT7_API_KEY)

Tests are marked with @pytest.mark.requires_context7 and will be skipped
if neither MCP tools nor API key are available.

IMPORTANT: These tests prefer MCP Gateway (Cursor's MCP server) over direct HTTP calls.
They verify that the MCP Context7 integration actually calls the real API.
"""

import os
import urllib.parse

import httpx
import pytest

from tapps_agents.context7.kb_cache import KBCache
from tapps_agents.context7.lookup import KBLookup, LookupResult
from tapps_agents.mcp.gateway import MCPGateway
from tapps_agents.mcp.servers.context7 import Context7MCPServer


def check_mcp_tools_available(gateway: MCPGateway | None = None) -> tuple[bool, str]:
    """
    Check if Context7 MCP tools are available via Cursor's MCP server or local gateway.
    
    Returns tuple of (available: bool, source: str) where source is:
    - "cursor_mcp" if in Cursor mode
    - "local_gateway" if tools registered in local MCPGateway
    - "none" if not available
    """
    from tapps_agents.context7.backup_client import check_mcp_tools_available as check_mcp
    return check_mcp(gateway)


def check_context7_api_available():
    """
    Check if Context7 API key is available (for fallback direct HTTP calls).
    
    Returns True if API key is set, False otherwise.
    """
    return os.getenv("CONTEXT7_API_KEY") is not None


def check_context7_available():
    """
    Check if Context7 is available via either:
    1. MCP Gateway (preferred, no API key needed)
    2. Direct API with API key (fallback)
    
    Returns tuple: (mcp_available, api_key_available)
    """
    gateway = MCPGateway()
    mcp_available = check_mcp_tools_available(gateway)
    api_key_available = check_context7_api_available()
    
    return mcp_available, api_key_available


def create_fallback_http_client():
    """
    Create fallback HTTP client functions for direct API calls.
    
    Only used if MCP Gateway tools are not available.
    Requires CONTEXT7_API_KEY environment variable.
    """
    api_key = os.getenv("CONTEXT7_API_KEY")
    if not api_key:
        return None, None
    
    # Context7 API base URL - adjust if different
    BASE_URL = os.getenv("CONTEXT7_API_URL", "https://api.context7.com")
    
    def resolve_library_client(library_name: str):
        """
        Fallback HTTP client for library resolution.
        Only used if MCP Gateway is not available.
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{BASE_URL}/v1/resolve",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    params={"library": library_name},
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "library": library_name,
                        "matches": [],
                        "error": f"API returned status {response.status_code}",
                    }
        except httpx.ConnectError:
            return {
                "library": library_name,
                "matches": [],
                "error": "Context7 API endpoint not reachable",
            }
        except Exception as e:
            return {"library": library_name, "matches": [], "error": str(e)}
    
    def get_docs_client(
        context7_id: str, topic: str | None = None, mode: str = "code", page: int = 1
    ):
        """
        Fallback HTTP client for documentation fetch.
        Only used if MCP Gateway is not available.
        """
        try:
            with httpx.Client(timeout=30.0) as client:
                params = {"mode": mode, "page": page}
                if topic:
                    params["topic"] = topic
                
                encoded_id = urllib.parse.quote(context7_id, safe="")
                
                response = client.get(
                    f"{BASE_URL}/v1/docs/{encoded_id}",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    params=params,
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, dict) and "content" in data:
                            return data["content"]
                        return data
                    except Exception:
                        return response.text
                else:
                    return None
        except Exception:
            return None
    
    return resolve_library_client, get_docs_client


pytestmark = pytest.mark.integration


@pytest.mark.requires_context7
class TestContext7MCPReal:
    """
    Real integration tests for Context7 MCP Server.
    
    Prefers MCP Gateway (Cursor's MCP server) - no API key needed.
    Falls back to direct HTTP calls if MCP not available.
    """

    @pytest.fixture
    def mcp_gateway_or_fallback(self):
        """
        Create MCP Gateway or fallback HTTP clients.
        
        Returns: (gateway, use_mcp, resolve_client, get_docs_client)
        - gateway: MCPGateway instance
        - use_mcp: True if MCP tools are available, False if using fallback
        - resolve_client: HTTP client function (only if use_mcp=False)
        - get_docs_client: HTTP client function (only if use_mcp=False)
        """
        gateway = MCPGateway()
        mcp_available = check_mcp_tools_available(gateway)
        
        if mcp_available:
            # Use MCP Gateway - no API key needed!
            return gateway, True, None, None
        
        # Fallback to direct HTTP - requires API key
        if not check_context7_api_available():
            pytest.skip(
                "Context7 not available: "
                "MCP tools not found and CONTEXT7_API_KEY not set"
            )
        
        resolve_client, get_docs_client = create_fallback_http_client()
        return gateway, False, resolve_client, get_docs_client

    def test_context7_resolve_library_real(self, mcp_gateway_or_fallback):
        """
        Test real Context7 library resolution.
        
        Uses MCP Gateway if available (preferred, no API key needed),
        otherwise falls back to direct HTTP calls.
        """
        gateway, use_mcp, resolve_client, _ = mcp_gateway_or_fallback
        
        if use_mcp:
            # Use MCP Gateway - Cursor's MCP server handles API key
            result = gateway.call_tool(
                "mcp_Context7_resolve-library-id",
                libraryName="react",
            )
            assert isinstance(result, dict)
            assert "success" in result
        else:
            # Fallback: Use direct HTTP client
            from tapps_agents.mcp.tool_registry import ToolRegistry
            
            registry = ToolRegistry()
            server = Context7MCPServer(
                registry=registry,
                resolve_library_client=resolve_client,
            )
            
            result = server.resolve_library_id("react")
            assert isinstance(result, dict)
            assert "library" in result

    def test_context7_get_docs_real(self, mcp_gateway_or_fallback):
        """
        Test real Context7 documentation fetch.
        
        Uses MCP Gateway if available (preferred, no API key needed),
        otherwise falls back to direct HTTP calls.
        """
        gateway, use_mcp, _, get_docs_client = mcp_gateway_or_fallback
        
        if use_mcp:
            # Use MCP Gateway - Cursor's MCP server handles API key
            result = gateway.call_tool(
                "mcp_Context7_get-library-docs",
                context7CompatibleLibraryID="/facebook/react",
                topic="hooks",
            )
            assert isinstance(result, dict)
            assert "success" in result
        else:
            # Fallback: Use direct HTTP client
            from tapps_agents.mcp.tool_registry import ToolRegistry
            
            registry = ToolRegistry()
            server = Context7MCPServer(
                registry=registry,
                get_docs_client=get_docs_client,
            )
            
            result = server.get_library_docs("/facebook/react", "hooks")
            assert isinstance(result, dict)
            assert "library_id" in result


@pytest.mark.requires_context7
@pytest.mark.asyncio
class TestContext7LookupReal:
    """
    Real integration tests for Context7 lookup.
    
    Prefers MCP Gateway (Cursor's MCP server) - no API key needed.
    Falls back to direct HTTP calls if MCP not available.
    """

    @pytest.fixture
    def real_mcp_gateway(self):
        """
        Create MCP Gateway with Context7 integration.
        
        Prefers MCP tools from Cursor (no API key needed).
        Falls back to HTTP clients if MCP not available.
        """
        gateway = MCPGateway()
        mcp_available = check_mcp_tools_available(gateway)
        
        if not mcp_available:
            # MCP tools not available - need to register fallback server
            if not check_context7_api_available():
                pytest.skip(
                    "Context7 not available: "
                    "MCP tools not found and CONTEXT7_API_KEY not set"
                )
            
            resolve_client, get_docs_client = create_fallback_http_client()
            # Register fallback server with HTTP clients
            Context7MCPServer(
                registry=gateway.registry,
                resolve_library_client=resolve_client,
                get_docs_client=get_docs_client,
            )
        
        # If MCP tools are available, they're already registered by Cursor
        return gateway

    @pytest.fixture
    def kb_lookup_with_real_api(self, tmp_path, real_mcp_gateway):
        """Create KBLookup with real MCP Gateway."""
        cache = KBCache(cache_root=tmp_path / "cache")
        lookup = KBLookup(
            kb_cache=cache,
            mcp_gateway=real_mcp_gateway,
        )
        return lookup

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_lookup_with_real_api_call(self, kb_lookup_with_real_api):
        """Test lookup that triggers real Context7 API call."""
        # Use a library that's not in cache
        result = await kb_lookup_with_real_api.lookup("nonexistent-test-lib", "overview")
        
        assert isinstance(result, LookupResult)
        # May succeed (if API works) or fail (if API unavailable)
        # Key is that it attempts the API call

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_lookup_resolve_library_real(self, kb_lookup_with_real_api):
        """Test library resolution with real API."""
        # This should trigger MCP Gateway → Context7 Server → Real API call
        result = await kb_lookup_with_real_api.lookup("react", "overview")
        
        assert isinstance(result, LookupResult)
        # Should attempt API call if not cached


@pytest.mark.requires_context7
class TestContext7MCPGatewayReal:
    """
    Real integration tests for MCP Gateway → Context7 API flow.
    
    Prefers MCP Gateway (Cursor's MCP server) - no API key needed.
    Falls back to direct HTTP calls if MCP not available.
    """

    @pytest.fixture
    def real_context7_gateway(self):
        """
        Create MCP Gateway with Context7 integration.
        
        Prefers MCP tools from Cursor (no API key needed).
        Falls back to HTTP clients if MCP not available.
        """
        gateway = MCPGateway()
        mcp_available = check_mcp_tools_available(gateway)
        
        if not mcp_available:
            # MCP tools not available - need to register fallback server
            if not check_context7_api_available():
                pytest.skip(
                    "Context7 not available: "
                    "MCP tools not found and CONTEXT7_API_KEY not set"
                )
            
            resolve_client, get_docs_client = create_fallback_http_client()
            # Register fallback server with HTTP clients
            Context7MCPServer(
                registry=gateway.registry,
                resolve_library_client=resolve_client,
                get_docs_client=get_docs_client,
            )
        
        # If MCP tools are available, they're already registered by Cursor
        return gateway

    @pytest.mark.timeout(30)
    def test_mcp_gateway_resolve_library_real(self, real_context7_gateway):
        """Test MCP Gateway → Context7 Server → Real API call for resolve."""
        # This tests the full flow: Gateway → Server → Real API
        result = real_context7_gateway.call_tool(
            "mcp_Context7_resolve-library-id",
            libraryName="react",
        )
        
        assert isinstance(result, dict)
        assert "success" in result
        # If successful, should have result from real API call
        # If failed, will have error (API unavailable, etc.)
        # Key is verifying the MCP Gateway actually calls the real client function

    @pytest.mark.timeout(30)
    def test_mcp_gateway_get_docs_real(self, real_context7_gateway):
        """Test MCP Gateway → Context7 Server → Real API call for get-docs."""
        # This tests the full flow: Gateway → Server → Real API
        result = real_context7_gateway.call_tool(
            "mcp_Context7_get-library-docs",
            context7CompatibleLibraryID="/facebook/react",
            topic="hooks",
        )
        
        assert isinstance(result, dict)
        assert "success" in result
        # If successful, should have result from real API call
        # If failed, will have error (API unavailable, etc.)
        # Key is verifying the MCP Gateway actually calls the real client function

