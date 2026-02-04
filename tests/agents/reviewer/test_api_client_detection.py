"""
Tests for API client pattern detection in ReviewerAgent.

Tests the _detect_api_client_pattern method to ensure it correctly identifies
API client code patterns including OAuth2, HTTP clients, REST endpoints, etc.
"""

import pytest

from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tapps_agents.core.config import load_config

pytestmark = pytest.mark.unit


@pytest.fixture
def reviewer():
    """Create ReviewerAgent instance for testing."""
    config = load_config()
    return ReviewerAgent(config=config)


class TestAPIClientDetection:
    """Test API client pattern detection."""

    @pytest.mark.asyncio
    async def test_detect_requests_library(self, reviewer):
        """Test detection of requests library usage with API structure."""
        code = """
import requests

class APIClient:
    base_url = "https://api.example.com"

    def get_user(self, user_id):
        response = requests.get(f"{self.base_url}/api/users/{user_id}")
        return response.json()
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_httpx_library(self, reviewer):
        """Test detection of httpx library usage with API structure."""
        code = """
import httpx

class APIClient:
    def __init__(self):
        self.base_url = "https://api.example.com"

    async def get_user(self, user_id):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/users/{user_id}")
            return response.json()
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_oauth2_patterns(self, reviewer):
        """Test detection of OAuth2 authentication patterns."""
        code = """
class OAuth2Client:
    def __init__(self, client_id, client_secret, token_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = None

    def get_access_token(self):
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        response = requests.post(self.token_url, data=data)
        self.access_token = response.json()['access_token']
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_bearer_auth(self, reviewer):
        """Test detection of Bearer token authentication."""
        code = """
import requests

def api_call(endpoint):
    headers = {
        'Authorization': f'Bearer {get_token()}',
        'Content-Type': 'application/json'
    }
    response = requests.get(f"https://api.example.com/{endpoint}", headers=headers)
    return response.json()
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_api_key_auth(self, reviewer):
        """Test detection of API key authentication."""
        code = """
import httpx

class APIClient:
    def __init__(self, api_key):
        self.api_key = api_key

    def _headers(self):
        return {
            'X-API-Key': self.api_key,
            'Accept': 'application/json'
        }

    def get(self, endpoint):
        return httpx.get(f"{self.base_url}/{endpoint}", headers=self._headers())
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_rest_endpoints(self, reviewer):
        """Test detection of REST API endpoint patterns."""
        code = """
class UserAPIClient:
    base_url = "https://api.example.com"

    def get_users(self):
        return requests.get(f"{self.base_url}/api/users")

    def post_user(self, data):
        return requests.post(f"{self.base_url}/api/users", json=data)

    def put_user(self, user_id, data):
        return requests.put(f"{self.base_url}/api/users/{user_id}", json=data)

    def delete_user(self, user_id):
        return requests.delete(f"{self.base_url}/api/users/{user_id}")
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_fastapi_patterns(self, reviewer):
        """Test detection of FastAPI endpoint patterns."""
        code = """
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/api/users")
async def get_users():
    return {"users": []}

@app.post("/api/users")
async def create_user(user: dict):
    return {"status": "created"}
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_jwt_patterns(self, reviewer):
        """Test detection of JWT token patterns."""
        code = """
import jwt
import requests

class JWTClient:
    def __init__(self, secret):
        self.secret = secret

    def generate_token(self, payload):
        return jwt.encode(payload, self.secret, algorithm='HS256')

    def api_call(self, endpoint, payload):
        token = self.generate_token(payload)
        headers = {'Authorization': f'Bearer {token}'}
        return requests.get(endpoint, headers=headers)
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_graphql_patterns(self, reviewer):
        """Test detection of GraphQL API patterns."""
        code = """
import requests

class GraphQLClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def query(self, query_string):
        response = requests.post(
            self.endpoint,
            json={'query': query_string},
            headers={'Content-Type': 'application/json'}
        )
        return response.json()
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_refresh_token_patterns(self, reviewer):
        """Test detection of token refresh patterns."""
        code = """
class TokenManager:
    def __init__(self, token_url):
        self.token_url = token_url
        self.access_token = None
        self.refresh_token = None

    def _refresh(self):
        data = {'refresh_token': self.refresh_token}
        response = requests.post(self.token_url, json=data)
        tokens = response.json()
        self.access_token = tokens['access_token']
        self.refresh_token = tokens['refresh_token']
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_javascript_fetch(self, reviewer):
        """Test detection of JavaScript/TypeScript fetch patterns."""
        code = """
async function fetchUser(userId) {
    const response = await fetch(`https://api.example.com/users/${userId}`, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });
    return response.json();
}
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_axios_patterns(self, reviewer):
        """Test detection of axios library patterns."""
        code = """
import axios from 'axios';

const apiClient = axios.create({
    baseURL: 'https://api.example.com',
    headers: {
        'X-API-Key': process.env.API_KEY
    }
});

async function getUser(userId) {
    const response = await apiClient.get(`/users/${userId}`);
    return response.data;
}
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_no_detection_regular_code(self, reviewer):
        """Test that regular code is not detected as API client."""
        code = """
def calculate_sum(numbers):
    return sum(numbers)

def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
"""
        assert await reviewer._detect_api_client_pattern(code) is False

    @pytest.mark.asyncio
    async def test_no_detection_empty_code(self, reviewer):
        """Test that empty code is not detected as API client."""
        assert await reviewer._detect_api_client_pattern("") is False
        assert await reviewer._detect_api_client_pattern(None) is False

    @pytest.mark.asyncio
    async def test_detect_http_client_without_auth(self, reviewer):
        """Test that HTTP client without auth/structure is not detected."""
        code = """
import requests

# Just importing requests without using it for API client patterns
def download_file(url):
    response = requests.get(url)
    return response.content
"""
        # This should not be detected because it lacks API client structure
        # (no auth patterns, no class structure, no REST endpoints)
        assert await reviewer._detect_api_client_pattern(code) is False

    @pytest.mark.asyncio
    async def test_detect_external_api_integration(self, reviewer):
        """Test detection of external/third-party API integration."""
        code = """
import requests

class ExternalAPIClient:
    '''Client for third-party payment API integration.'''

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.external-service.com"

    def process_payment(self, amount):
        headers = {'X-API-Key': self.api_key}
        response = requests.post(
            f"{self.base_url}/api/payments",
            json={'amount': amount},
            headers=headers
        )
        return response.json()
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_aiohttp_patterns(self, reviewer):
        """Test detection of aiohttp library patterns with API structure."""
        code = """
import aiohttp

class APIClient:
    def __init__(self):
        self.api_url = "https://api.example.com"

    async def fetch_user(self, user_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.api_url}/users/{user_id}') as response:
                return await response.json()
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_authorization_code_grant(self, reviewer):
        """Test detection of OAuth2 authorization code grant flow."""
        code = """
class OAuth2AuthCodeClient:
    def exchange_code_for_token(self, authorization_code):
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri
        }
        response = requests.post(self.token_url, data=data)
        return response.json()
"""
        assert await reviewer._detect_api_client_pattern(code) is True

    @pytest.mark.asyncio
    async def test_detect_id_token_patterns(self, reviewer):
        """Test detection of OpenID Connect id_token patterns with HTTP calls."""
        code = """
import jwt
import requests
from jwt import PyJWKClient

class OIDCClient:
    def __init__(self, jwks_url):
        self.jwks_url = jwks_url

    def verify_id_token(self, id_token, client_id):
        jwks_client = PyJWKClient(self.jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)

        decoded = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=['RS256'],
            audience=client_id
        )
        return decoded

    def get_user_info(self, access_token):
        headers = {'Authorization': f'Bearer {access_token}'}
        return requests.get(f'{self.base_url}/userinfo', headers=headers)
"""
        assert await reviewer._detect_api_client_pattern(code) is True
