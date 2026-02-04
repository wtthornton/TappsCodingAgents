"""
Tests for API client pattern detection in ImplementerAgent.

Tests the _detect_api_client_pattern method to ensure it correctly identifies
API client specifications for OAuth2, HTTP clients, REST APIs, etc.
"""

import pytest

from tapps_agents.agents.implementer.agent import ImplementerAgent
from tapps_agents.core.config import load_config

pytestmark = pytest.mark.unit


@pytest.fixture
def implementer():
    """Create ImplementerAgent instance for testing."""
    config = load_config()
    return ImplementerAgent(config=config)


class TestAPIClientDetection:
    """Test API client pattern detection in specifications."""

    # ========================================================================
    # Test API Client Keywords
    # ========================================================================

    @pytest.mark.asyncio
    async def test_detect_api_client_keyword(self, implementer):
        """Test detection of 'API client' keyword."""
        spec = "Create an API client for user management with OAuth2"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_http_client_keyword(self, implementer):
        """Test detection of 'HTTP client' keyword."""
        spec = "Build an HTTP client for external service with authentication"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_rest_client_keyword(self, implementer):
        """Test detection of 'REST client' keyword."""
        spec = "Implement a REST client with token-based auth"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_oauth2_keyword(self, implementer):
        """Test detection of 'OAuth2' keyword."""
        spec = "Create OAuth2 authentication client with refresh tokens"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_oauth_keyword(self, implementer):
        """Test detection of 'OAuth' keyword."""
        spec = "Build OAuth authentication flow with bearer tokens"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_graphql_client(self, implementer):
        """Test detection of GraphQL client patterns."""
        spec = "Create a GraphQL client for querying user data with authentication"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_websocket_client(self, implementer):
        """Test detection of WebSocket client patterns."""
        spec = "Implement WebSocket client for real-time updates with auth"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_mqtt_client(self, implementer):
        """Test detection of MQTT client patterns."""
        spec = "Create MQTT client for IoT device communication with credentials"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_grpc_client(self, implementer):
        """Test detection of gRPC client patterns."""
        spec = "Build gRPC client with service authentication"
        assert await implementer._detect_api_client_pattern(spec) is True

    # ========================================================================
    # Test Authentication Keywords
    # ========================================================================

    @pytest.mark.asyncio
    async def test_detect_bearer_token(self, implementer):
        """Test detection of bearer token authentication."""
        spec = "Create API client using bearer token authentication"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_jwt_keyword(self, implementer):
        """Test detection of JWT patterns."""
        spec = "Implement REST API client with JWT authentication"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_id_token(self, implementer):
        """Test detection of OpenID Connect id_token patterns."""
        spec = "Create OAuth2 client with id_token validation for API calls"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_grant_type(self, implementer):
        """Test detection of OAuth2 grant_type patterns."""
        spec = "Implement API client using client_credentials grant_type"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_authorization_code(self, implementer):
        """Test detection of OAuth2 authorization code flow."""
        spec = "Build OAuth2 client with authorization_code flow and tokens"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_client_credentials(self, implementer):
        """Test detection of client credentials flow."""
        spec = "Create API client using client_credentials flow with API key"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_token_management(self, implementer):
        """Test detection of token management patterns."""
        spec = "Implement API client with token management and refresh logic"
        assert await implementer._detect_api_client_pattern(spec) is True

    # ========================================================================
    # Test Structure Keywords
    # ========================================================================

    @pytest.mark.asyncio
    async def test_detect_rest_endpoint(self, implementer):
        """Test detection of REST endpoint patterns."""
        spec = "Create API client for REST endpoint /users with authentication"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_http_request(self, implementer):
        """Test detection of HTTP request patterns."""
        spec = "Build REST API making HTTP requests with bearer tokens"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_fastapi_pattern(self, implementer):
        """Test detection of FastAPI REST API implementation."""
        spec = "Implement REST API using FastAPI with api_key authentication"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_django_rest(self, implementer):
        """Test detection of Django REST framework."""
        spec = "Create Django REST API with token authentication"
        assert await implementer._detect_api_client_pattern(spec) is True

    @pytest.mark.asyncio
    async def test_detect_api_router(self, implementer):
        """Test detection of REST API router patterns."""
        spec = "Build REST API router with authentication and endpoints"
        assert await implementer._detect_api_client_pattern(spec) is True

    # ========================================================================
    # Test With Context
    # ========================================================================

    @pytest.mark.asyncio
    async def test_detection_with_context(self, implementer):
        """Test detection using both specification and context."""
        spec = "Implement API client for user management"
        context = """
class APIClient:
    def __init__(self, api_key):
        self.api_key = api_key
    def get_users(self):
        return requests.get(url, headers={'Authorization': f'Bearer {token}'})
"""
        assert await implementer._detect_api_client_pattern(spec, context) is True

    @pytest.mark.asyncio
    async def test_detection_weak_spec_strong_context(self, implementer):
        """Test detection with weak spec but strong context."""
        spec = "Add new functionality"
        context = "OAuth2 client with refresh token management and API integration"
        assert await implementer._detect_api_client_pattern(spec, context) is True

    # ========================================================================
    # Test Negative Cases
    # ========================================================================

    @pytest.mark.asyncio
    async def test_no_detection_regular_function(self, implementer):
        """Test that regular function spec is not detected."""
        spec = "Create a function to calculate factorial"
        assert await implementer._detect_api_client_pattern(spec) is False

    @pytest.mark.asyncio
    async def test_no_detection_data_processing(self, implementer):
        """Test that data processing spec is not detected."""
        spec = "Implement data processing pipeline with filtering and transformation"
        assert await implementer._detect_api_client_pattern(spec) is False

    @pytest.mark.asyncio
    async def test_no_detection_ui_component(self, implementer):
        """Test that UI component spec is not detected."""
        spec = "Create React component for user profile display"
        assert await implementer._detect_api_client_pattern(spec) is False

    @pytest.mark.asyncio
    async def test_no_detection_database_function(self, implementer):
        """Test that database function spec is not detected."""
        spec = "Implement database query function for user records"
        assert await implementer._detect_api_client_pattern(spec) is False

    @pytest.mark.asyncio
    async def test_no_detection_empty_spec(self, implementer):
        """Test that empty spec is not detected."""
        assert await implementer._detect_api_client_pattern("") is False
        assert await implementer._detect_api_client_pattern(None) is False

    # ========================================================================
    # Test Case Insensitivity
    # ========================================================================

    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self, implementer):
        """Test that detection is case-insensitive."""
        specs = [
            "Create API CLIENT with OAUTH2 authentication",
            "Create Api Client with OAuth2 Authentication",
            "create api client with oauth2 authentication",
        ]
        for spec in specs:
            assert await implementer._detect_api_client_pattern(spec) is True

    # ========================================================================
    # Test Real User Specifications
    # ========================================================================

    @pytest.mark.parametrize("spec,should_detect", [
        ("Create OAuth2 authentication client for external API", True),
        ("Build REST API client with JWT tokens", True),
        ("Implement API wrapper for third-party service with bearer auth", True),
        ("Create REST API using FastAPI with API key authentication", True),
        ("Build GraphQL client for data fetching with credentials", True),
        ("Implement WebSocket client with token-based auth", True),
        ("Create function to process CSV data", False),
        ("Build React component for dashboard", False),
        ("Implement database migration script", False),
    ])
    @pytest.mark.asyncio
    async def test_real_user_specifications(self, implementer, spec, should_detect):
        """Test real user specifications."""
        result = await implementer._detect_api_client_pattern(spec)
        assert result == should_detect
