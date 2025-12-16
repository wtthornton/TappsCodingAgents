"""
Tests for Model Abstraction Layer (MAL).

Tests provider initialization, fallback strategies, error handling,
and response parsing. Uses httpx.MockTransport to test real HTTP behavior
without requiring actual network calls.
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient, MockTransport, Request, Response

pytestmark = pytest.mark.unit

from tapps_agents.core.config import MALConfig
from tapps_agents.core.mal import MAL


@pytest.fixture(autouse=True)
def _force_headless_mode_for_mal_tests(monkeypatch):
    """
    MAL unit tests must run in headless mode.

    When running pytest under Cursor, Cursor may inject CURSOR_* environment markers,
    which would otherwise cause runtime auto-detection to treat the process as Cursor mode
    and (correctly) disable MAL. These tests are specifically validating MAL behavior,
    so we force headless mode here.
    """
    monkeypatch.setenv("TAPPS_AGENTS_MODE", "headless")


@pytest.fixture
def ollama_success_transport():
    """MockTransport fixture for successful Ollama non-streaming responses."""
    def handler(request: Request) -> Response:
        if request.url.path == "/api/generate":
            # Non-streaming response
            response_data = {
                "model": "test-model",
                "response": "Test response",
                "done": True,
            }
            return Response(200, json=response_data)
        return Response(404, text="Not found")
    
    return MockTransport(handler)


@pytest.fixture
def ollama_streaming_transport():
    """MockTransport fixture for successful Ollama streaming responses."""
    def handler(request: Request) -> Response:
        if request.url.path == "/api/generate":
            # Streaming response - return ndjson format
            # Note: httpx streaming uses client.stream() which expects newline-delimited JSON
            chunks = [
                b'{"response":"Test","done":false}\n',
                b'{"response":" response","done":false}\n',
                b'{"response":"","done":true}\n',
            ]
            content = b"".join(chunks)
            return Response(
                200, 
                content=content, 
                headers={"Content-Type": "application/x-ndjson"}
            )
        return Response(404, text="Not found")
    
    return MockTransport(handler)


@pytest.fixture
def ollama_error_4xx_transport():
    """MockTransport fixture for 4xx error responses."""
    def handler(request: Request) -> Response:
        error_data = {"error": "model 'test-model' not found"}
        return Response(404, json=error_data)
    
    return MockTransport(handler)


@pytest.fixture
def ollama_error_5xx_transport():
    """MockTransport fixture for 5xx error responses."""
    def handler(request: Request) -> Response:
        return Response(500, text="Internal Server Error")
    
    return MockTransport(handler)


@pytest.fixture
def ollama_timeout_transport():
    """MockTransport fixture that simulates timeout - handled at httpx level."""
    # MockTransport doesn't support async handlers, so we'll handle timeout differently
    # in the test by using a very short timeout in the config
    def handler(request: Request) -> Response:
        # Return a response - timeout will be handled by httpx when transport is slow
        # In practice, we use a very short timeout in config and let httpx handle it
        return Response(200, json={"response": "This should timeout"})
    
    return MockTransport(handler)


@pytest.fixture
def ollama_connection_error_transport():
    """MockTransport fixture that simulates connection errors."""
    def handler(request: Request) -> Response:
        raise ConnectionError("Connection refused")
    
    return MockTransport(handler)


@pytest.fixture
def anthropic_success_transport():
    """MockTransport fixture for successful Anthropic responses."""
    def handler(request: Request) -> Response:
        if "/messages" in request.url.path:
            response_data = {
                "content": [{"type": "text", "text": "Anthropic response"}],
                "model": "claude-3-sonnet-20240229",
            }
            return Response(200, json=response_data)
        return Response(404, text="Not found")
    
    return MockTransport(handler)


@pytest.fixture
def anthropic_error_transport():
    """MockTransport fixture for Anthropic error responses."""
    def handler(request: Request) -> Response:
        error_data = {"error": {"type": "invalid_request_error", "message": "Invalid API key"}}
        return Response(401, json=error_data)
    
    return MockTransport(handler)


class TestMALInitialization:
    """Tests for MAL initialization."""

    def test_mal_init_with_config(self):
        """Test MAL initialization with config."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="test-model",
            default_provider="ollama",
        )
        mal = MAL(config=config)
        assert mal.config == config
        assert mal.ollama_url == "http://localhost:11434"
        assert mal.timeout_config is not None

    def test_mal_init_with_ollama_url_override(self):
        """Test MAL initialization with ollama_url override."""
        config = MALConfig(ollama_url="http://default:11434")
        mal = MAL(config=config, ollama_url="http://override:11434")
        assert mal.ollama_url == "http://override:11434"

    def test_mal_init_default_config(self):
        """Test MAL initialization with default config."""
        mal = MAL()
        assert mal.config is not None
        assert isinstance(mal.config, MALConfig)
        assert mal.client is not None

    def test_mal_timeout_config(self):
        """Test MAL timeout configuration."""
        config = MALConfig(
            connect_timeout=5.0,
            read_timeout=30.0,
            write_timeout=10.0,
            pool_timeout=5.0,
        )
        mal = MAL(config=config)
        assert mal.timeout_config.connect == 5.0
        assert mal.timeout_config.read == 30.0
        assert mal.timeout_config.write == 10.0
        assert mal.timeout_config.pool == 5.0


class TestMALOllamaProvider:
    """Tests for Ollama provider using real HTTP transport."""

    @pytest.mark.asyncio
    async def test_ollama_generate_success_non_streaming(self, ollama_success_transport):
        """Test successful Ollama generation with non-streaming response."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
            use_streaming=False,
        )
        mal = MAL(config=config)
        
        # Replace client transport with mock transport
        mal.client = AsyncClient(transport=ollama_success_transport, timeout=mal.timeout_config)
        
        result = await mal._ollama_generate("test prompt", "test-model", stream=False)
        assert result == "Test response"

    @pytest.mark.asyncio
    async def test_ollama_generate_success_streaming(self, ollama_streaming_transport):
        """Test successful Ollama generation with streaming response."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
            use_streaming=True,
        )
        mal = MAL(config=config)
        
        # Patch AsyncClient to use streaming transport
        original_async_client = AsyncClient
        def patched_client(*args, **kwargs):
            kwargs["transport"] = ollama_streaming_transport
            return original_async_client(*args, **kwargs)
        
        with patch("httpx.AsyncClient", side_effect=patched_client):
            result = await mal._ollama_generate("test prompt", "test-model", stream=True)
            assert result == "Test response"

    @pytest.mark.asyncio
    async def test_ollama_generate_error_4xx(self, ollama_error_4xx_transport):
        """Test Ollama generation with 4xx error response."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
        )
        mal = MAL(config=config)
        mal.client = AsyncClient(transport=ollama_error_4xx_transport, timeout=mal.timeout_config)
        
        with pytest.raises(ConnectionError, match="Ollama API returned error status"):
            await mal._ollama_generate("test prompt", "test-model")

    @pytest.mark.asyncio
    async def test_ollama_generate_error_5xx(self, ollama_error_5xx_transport):
        """Test Ollama generation with 5xx error response."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
        )
        mal = MAL(config=config)
        mal.client = AsyncClient(transport=ollama_error_5xx_transport, timeout=mal.timeout_config)
        
        with pytest.raises(ConnectionError, match="Ollama API returned error status"):
            await mal._ollama_generate("test prompt", "test-model")

    @pytest.mark.asyncio
    async def test_ollama_generate_connection_error(self, ollama_connection_error_transport):
        """Test Ollama generation with connection error."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
        )
        mal = MAL(config=config)
        mal.client = AsyncClient(transport=ollama_connection_error_transport, timeout=mal.timeout_config)
        
        with pytest.raises(ConnectionError, match="Ollama request failed"):
            await mal._ollama_generate("test prompt", "test-model")

    @pytest.mark.asyncio
    async def test_ollama_generate_timeout(self):
        """Test Ollama generation with timeout handling."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
            connect_timeout=0.1,  # Very short timeout
            read_timeout=0.1,
        )
        mal = MAL(config=config)
        
        # Use a transport that will exceed timeout
        async def slow_handler(request: Request) -> Response:
            import asyncio
            await asyncio.sleep(1.0)  # Sleep longer than timeout
            return Response(200, json={"response": "Should timeout"})
        
        transport = MockTransport(slow_handler)
        mal.client = AsyncClient(transport=transport, timeout=mal.timeout_config)
        
        # Validate timeout error message includes "Ollama request failed"
        with pytest.raises(ConnectionError, match="Ollama request failed"):
            await mal._ollama_generate("test prompt", "test-model")


class TestMALFallback:
    """Tests for fallback strategies using real HTTP behavior."""

    @pytest.mark.asyncio
    async def test_fallback_ollama_to_anthropic(self):
        """Test fallback from Ollama to Anthropic with real HTTP behavior."""
        # Create a routing transport that fails Ollama but succeeds Anthropic
        def routing_handler(request: Request) -> Response:
            if "test-ollama" in str(request.url) or "11434" in str(request.url):
                # Ollama fails with 404
                error_data = {"error": "model 'test-model' not found"}
                return Response(404, json=error_data)
            elif "test-anthropic" in str(request.url) or "anthropic" in str(request.url):
                # Anthropic succeeds
                response_data = {
                    "content": [{"type": "text", "text": "Anthropic response"}],
                    "model": "claude-3-sonnet-20240229",
                }
                return Response(200, json=response_data)
            return Response(404, text="Not found")
        
        transport = MockTransport(routing_handler)
        
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
            enable_fallback=True,
            anthropic_api_key="test-key",
            anthropic_base_url="http://test-anthropic",
        )
        mal = MAL(config=config)
        
        # Patch AsyncClient creation to use our routing transport
        original_async_client = AsyncClient
        async def patched_client(*args, **kwargs):
            kwargs["transport"] = transport
            return original_async_client(*args, **kwargs)
        
        with patch("httpx.AsyncClient", side_effect=patched_client):
            result = await mal.generate("test prompt", provider="ollama", enable_fallback=True)
            assert result == "Anthropic response"

    @pytest.mark.asyncio
    async def test_fallback_disabled(self, ollama_error_4xx_transport):
        """Test that fallback doesn't occur when disabled."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
            enable_fallback=False,
        )
        mal = MAL(config=config)
        
        # Patch AsyncClient to use error transport
        original_async_client = AsyncClient
        async def patched_client(*args, **kwargs):
            kwargs["transport"] = ollama_error_4xx_transport
            return original_async_client(*args, **kwargs)
        
        with patch("httpx.AsyncClient", side_effect=patched_client):
            # Validate error message includes "Ollama API returned error status"
            with pytest.raises(ConnectionError, match="Ollama API returned error status"):
                await mal.generate("test prompt", provider="ollama", enable_fallback=False)

    @pytest.mark.asyncio
    async def test_fallback_all_providers_fail(self):
        """Test fallback when all providers fail with real HTTP behavior."""
        # Create a routing transport where all providers fail
        def all_fail_handler(request: Request) -> Response:
            if "test-ollama" in str(request.url) or "11434" in str(request.url):
                return Response(404, json={"error": "Ollama failed"})
            elif "test-anthropic" in str(request.url) or "anthropic" in str(request.url):
                return Response(401, json={"error": {"type": "invalid_request_error", "message": "Invalid API key"}})
            return Response(404, text="Not found")
        
        transport = MockTransport(all_fail_handler)
        
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
            enable_fallback=True,
            anthropic_api_key="test-key",
            anthropic_base_url="http://test-anthropic",
        )
        mal = MAL(config=config)
        
        original_async_client = AsyncClient
        async def patched_client(*args, **kwargs):
            kwargs["transport"] = transport
            return original_async_client(*args, **kwargs)
        
        with patch("httpx.AsyncClient", side_effect=patched_client):
            with pytest.raises(ConnectionError, match="All providers failed"):
                await mal.generate("test prompt", provider="ollama", enable_fallback=True)


class TestMALGenerate:
    """Tests for main generate method using real HTTP behavior."""

    @pytest.mark.asyncio
    async def test_generate_with_defaults(self, ollama_success_transport):
        """Test generate with default model and provider."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="default-model",
            default_provider="ollama",
            use_streaming=False,
        )
        mal = MAL(config=config)
        
        original_async_client = AsyncClient
        def patched_client(*args, **kwargs):
            kwargs["transport"] = ollama_success_transport
            return original_async_client(*args, **kwargs)
        
        with patch("httpx.AsyncClient", side_effect=patched_client):
            result = await mal.generate("test prompt")
            assert result == "Test response"

    @pytest.mark.asyncio
    async def test_generate_with_custom_model(self, ollama_success_transport):
        """Test generate with custom model."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="default-model",
            default_provider="ollama",
            use_streaming=False,
        )
        mal = MAL(config=config)
        
        original_async_client = AsyncClient
        def patched_client(*args, **kwargs):
            kwargs["transport"] = ollama_success_transport
            return original_async_client(*args, **kwargs)
        
        with patch("httpx.AsyncClient", side_effect=patched_client):
            result = await mal.generate("test prompt", model="custom-model")
            assert result == "Test response"

    @pytest.mark.asyncio
    async def test_generate_with_custom_provider(self, anthropic_success_transport):
        """Test generate with custom provider."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
            anthropic_api_key="test-key",
            anthropic_base_url="http://test-anthropic",
        )
        mal = MAL(config=config)
        
        original_async_client = AsyncClient
        def patched_client(*args, **kwargs):
            kwargs["transport"] = anthropic_success_transport
            return original_async_client(*args, **kwargs)
        
        with patch("httpx.AsyncClient", side_effect=patched_client):
            result = await mal.generate("test prompt", provider="anthropic")
            assert result == "Anthropic response"

    @pytest.mark.asyncio
    async def test_generate_invalid_provider(self):
        """Test generate with invalid provider."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
            enable_fallback=False,
        )
        mal = MAL(config=config)
        
        # Validate specific error: ValueError with "Unsupported provider" message
        with pytest.raises(ValueError, match="Unsupported provider"):
            await mal.generate("test prompt", provider="invalid-provider", enable_fallback=False)

    @pytest.mark.asyncio
    async def test_generate_enable_fallback_override(self, ollama_success_transport):
        """Test generate with enable_fallback override."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
            enable_fallback=False,
            use_streaming=False,
        )
        mal = MAL(config=config)
        
        original_async_client = AsyncClient
        def patched_client(*args, **kwargs):
            kwargs["transport"] = ollama_success_transport
            return original_async_client(*args, **kwargs)
        
        with patch("httpx.AsyncClient", side_effect=patched_client):
            # Override fallback to True
            result = await mal.generate("test prompt", enable_fallback=True)
            assert result == "Test response"


class TestMALClose:
    """Tests for MAL cleanup."""

    @pytest.mark.asyncio
    async def test_close(self):
        """Test MAL close method."""
        mal = MAL()
        await mal.close()
        # Should not raise
        assert True

    @pytest.mark.asyncio
    async def test_close_manual(self):
        """Test MAL manual close."""
        config = MALConfig(
            ollama_url="http://test-ollama:11434",
            default_model="test-model",
            default_provider="ollama",
        )
        
        mal = MAL(config=config)
        await mal.close()
        # Should not raise
        assert True

