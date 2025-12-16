"""
Tests for Model Abstraction Layer (MAL).

Tests provider initialization, fallback strategies, error handling,
and response parsing. Uses mocks to avoid actual LLM calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
    """Tests for Ollama provider."""

    @pytest.mark.asyncio
    async def test_ollama_generate_success(self):
        """Test successful Ollama generation."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="test-model",
            default_provider="ollama",
        )
        mal = MAL(config=config)
        
        # Mock the entire HTTP response - need to mock httpx.AsyncClient context manager
        mock_response_data = {
            "model": "test-model",
            "response": "Test response",
            "done": True,
        }
        
        # Create a proper mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()  # Don't raise on 200
        mock_response.text = '{"error":"model \'test-model\' not found"}'
        
        # Mock the async context manager and post method
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await mal._ollama_generate("test prompt", "test-model")
            assert result == "Test response"
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_ollama_generate_error(self):
        """Test Ollama generation with error."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="test-model",
            default_provider="ollama",
        )
        mal = MAL(config=config)
        
        with patch.object(mal.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("Connection error")
            
            with pytest.raises(Exception):
                await mal._ollama_generate("test prompt", "test-model")


class TestMALFallback:
    """Tests for fallback strategies."""

    @pytest.mark.asyncio
    async def test_fallback_ollama_to_anthropic(self):
        """Test fallback from Ollama to Anthropic."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="test-model",
            default_provider="ollama",
            enable_fallback=True,
            anthropic_api_key="test-key",
        )
        mal = MAL(config=config)
        
        # Mock Ollama failure
        with patch.object(mal, "_ollama_generate", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.side_effect = Exception("Ollama failed")
            
            # Mock Anthropic success
            with patch.object(mal, "_anthropic_generate", new_callable=AsyncMock) as mock_anthropic:
                mock_anthropic.return_value = "Anthropic response"
                
                result = await mal.generate("test prompt", provider="ollama", enable_fallback=True)
                assert result == "Anthropic response"
                mock_ollama.assert_called_once()
                mock_anthropic.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_disabled(self):
        """Test that fallback doesn't occur when disabled."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="test-model",
            default_provider="ollama",
            enable_fallback=False,
        )
        mal = MAL(config=config)
        
        with patch.object(mal, "_ollama_generate", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.side_effect = Exception("Ollama failed")
            
            with pytest.raises(Exception):
                await mal.generate("test prompt", provider="ollama", enable_fallback=False)

    @pytest.mark.asyncio
    async def test_fallback_all_providers_fail(self):
        """Test fallback when all providers fail."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="test-model",
            default_provider="ollama",
            enable_fallback=True,
            anthropic_api_key="test-key",
        )
        mal = MAL(config=config)
        
        with patch.object(mal, "_ollama_generate", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.side_effect = Exception("Ollama failed")
            
            with patch.object(mal, "_anthropic_generate", new_callable=AsyncMock) as mock_anthropic:
                mock_anthropic.side_effect = Exception("Anthropic failed")
                
                with pytest.raises(Exception):
                    await mal.generate("test prompt", provider="ollama", enable_fallback=True)


class TestMALGenerate:
    """Tests for main generate method."""

    @pytest.mark.asyncio
    async def test_generate_with_defaults(self):
        """Test generate with default model and provider."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="default-model",
            default_provider="ollama",
        )
        mal = MAL(config=config)
        
        with patch.object(mal, "_ollama_generate", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = "Response"
            
            result = await mal.generate("test prompt")
            assert result == "Response"
            mock_ollama.assert_called_once_with("test prompt", "default-model")

    @pytest.mark.asyncio
    async def test_generate_with_custom_model(self):
        """Test generate with custom model."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="default-model",
            default_provider="ollama",
        )
        mal = MAL(config=config)
        
        with patch.object(mal, "_ollama_generate", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = "Response"
            
            result = await mal.generate("test prompt", model="custom-model")
            assert result == "Response"
            mock_ollama.assert_called_once_with("test prompt", "custom-model")

    @pytest.mark.asyncio
    async def test_generate_with_custom_provider(self):
        """Test generate with custom provider."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="test-model",
            default_provider="ollama",
            anthropic_api_key="test-key",
        )
        mal = MAL(config=config)
        
        with patch.object(mal, "_anthropic_generate", new_callable=AsyncMock) as mock_anthropic:
            mock_anthropic.return_value = "Anthropic response"
            
            result = await mal.generate("test prompt", provider="anthropic")
            assert result == "Anthropic response"
            mock_anthropic.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_invalid_provider(self):
        """Test generate with invalid provider."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="test-model",
            default_provider="ollama",
            enable_fallback=False,
        )
        mal = MAL(config=config)
        
        with pytest.raises((ValueError, ConnectionError), match="Unsupported provider|All providers failed"):
            await mal.generate("test prompt", provider="invalid-provider", enable_fallback=False)

    @pytest.mark.asyncio
    async def test_generate_enable_fallback_override(self):
        """Test generate with enable_fallback override."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="test-model",
            default_provider="ollama",
            enable_fallback=False,
        )
        mal = MAL(config=config)
        
        with patch.object(mal, "_ollama_generate", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = "Response"
            
            # Override fallback to True
            result = await mal.generate("test prompt", enable_fallback=True)
            assert result == "Response"


class TestMALClose:
    """Tests for MAL cleanup."""

    @pytest.mark.asyncio
    async def test_close(self):
        """Test MAL close method."""
        mal = MAL()
        
        with patch.object(mal.client, "aclose", new_callable=AsyncMock) as mock_close:
            await mal.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_manual(self):
        """Test MAL manual close."""
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_model="test-model",
            default_provider="ollama",
        )
        
        mal = MAL(config=config)
        await mal.close()
        # Should not raise
        assert True

