"""
Tests for Cloud MAL providers (Anthropic, OpenAI).
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.core.config import CloudProviderConfig, MALConfig
from tapps_agents.core.mal import MAL


class TestCloudMAL:
    """Test cloud provider integration."""

    @pytest.fixture
    def mal_config(self):
        """Create MAL config with cloud providers."""
        return MALConfig(
            anthropic=CloudProviderConfig(api_key="test-anthropic-key"),
            openai=CloudProviderConfig(api_key="test-openai-key"),
        )

    @pytest.fixture(autouse=True)
    def set_headless_mode(self):
        """Set TAPPS_AGENTS_MODE to headless for all tests in this class."""
        with patch.dict("os.environ", {"TAPPS_AGENTS_MODE": "headless"}):
            yield

    @pytest.mark.asyncio
    async def test_anthropic_generate_success(self, mal_config):
        """Test successful Anthropic API call."""
        mock_response = {"content": [{"text": "This is a test response from Claude"}]}

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.raise_for_status = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_post.return_value = mock_response_obj

            mal = MAL(config=mal_config)
            result = await mal._anthropic_generate(
                "Test prompt", "claude-3-sonnet-20240229"
            )

            assert result == "This is a test response from Claude"
            mock_post.assert_called_once()

            # Verify API key header
            call_args = mock_post.call_args
            assert call_args[1]["headers"]["x-api-key"] == "test-anthropic-key"

    @pytest.mark.asyncio
    async def test_anthropic_missing_api_key(self):
        """Test Anthropic with missing API key."""
        config = MALConfig(anthropic=None)

        # Remove env var if set
        import os

        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)

        try:
            mal = MAL(config=config)
            with pytest.raises(ValueError, match="Anthropic API key not found"):
                await mal._anthropic_generate("Test", "claude-3-sonnet")
        finally:
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key

    @pytest.mark.asyncio
    async def test_openai_generate_success(self, mal_config):
        """Test successful OpenAI API call."""
        mock_response = {
            "choices": [{"message": {"content": "This is a test response from GPT"}}]
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.raise_for_status = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_post.return_value = mock_response_obj

            mal = MAL(config=mal_config)
            result = await mal._openai_generate("Test prompt", "gpt-4")

            assert result == "This is a test response from GPT"
            mock_post.assert_called_once()

            # Verify API key header
            call_args = mock_post.call_args
            assert "Bearer test-openai-key" in call_args[1]["headers"]["Authorization"]

    @pytest.mark.asyncio
    async def test_openai_missing_api_key(self):
        """Test OpenAI with missing API key."""
        config = MALConfig(openai=None)

        # Remove env var if set
        import os

        old_key = os.environ.pop("OPENAI_API_KEY", None)

        try:
            mal = MAL(config=config)
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                await mal._openai_generate("Test", "gpt-4")
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key

    @pytest.mark.asyncio
    async def test_fallback_ollama_to_anthropic(self, mal_config):
        """Test fallback from Ollama to Anthropic when Ollama fails."""
        # Mock Ollama failure
        with patch.object(
            MAL, "_ollama_generate", side_effect=ConnectionError("Ollama unavailable")
        ):
            # Mock Anthropic success
            mock_response = {"content": [{"text": "Fallback response"}]}

            with patch("httpx.AsyncClient.post") as mock_post:
                mock_response_obj = MagicMock()
                mock_response_obj.raise_for_status = MagicMock()
                mock_response_obj.json.return_value = mock_response
                mock_post.return_value = mock_response_obj

                mal = MAL(config=mal_config)
                result = await mal.generate(
                    "Test prompt", provider="ollama", enable_fallback=True
                )

                assert result == "Fallback response"

    @pytest.mark.asyncio
    async def test_fallback_provider_order(self, mal_config):
        """Test fallback tries providers in configured order."""
        mal_config.fallback_providers = ["anthropic", "openai"]

        # Mock Ollama failure
        with patch.object(
            MAL, "_ollama_generate", side_effect=ConnectionError("Ollama unavailable")
        ):
            # Mock Anthropic failure
            with patch.object(
                MAL,
                "_anthropic_generate",
                side_effect=ConnectionError("Anthropic unavailable"),
            ):
                # Mock OpenAI success
                mock_response = {
                    "choices": [{"message": {"content": "OpenAI fallback"}}]
                }

                with patch("httpx.AsyncClient.post") as mock_post:
                    mock_response_obj = MagicMock()
                    mock_response_obj.raise_for_status = MagicMock()
                    mock_response_obj.json.return_value = mock_response
                    mock_post.return_value = mock_response_obj

                    mal = MAL(config=mal_config)
                    result = await mal.generate(
                        "Test prompt", provider="ollama", enable_fallback=True
                    )

                    assert result == "OpenAI fallback"

    @pytest.mark.asyncio
    async def test_no_fallback_when_disabled(self, mal_config):
        """Test that fallback doesn't occur when disabled."""
        with patch.object(
            MAL, "_ollama_generate", side_effect=ConnectionError("Ollama unavailable")
        ):
            mal = MAL(config=mal_config)

            with pytest.raises(ConnectionError, match="All providers failed"):
                await mal.generate(
                    "Test prompt", provider="ollama", enable_fallback=False
                )

    @pytest.mark.asyncio
    async def test_model_name_mapping_anthropic(self, mal_config):
        """Test model name mapping for Anthropic."""
        mock_response = {"content": [{"text": "Response"}]}

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.raise_for_status = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_post.return_value = mock_response_obj

            mal = MAL(config=mal_config)

            # Test with non-Anthropic model name (should default)
            await mal._anthropic_generate("Test", "qwen2.5-coder:7b")

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            # Should default to claude-3-sonnet-20240229
            assert payload["model"] == "claude-3-sonnet-20240229"

    @pytest.mark.asyncio
    async def test_model_name_mapping_openai(self, mal_config):
        """Test model name mapping for OpenAI."""
        mock_response = {"choices": [{"message": {"content": "Response"}}]}

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.raise_for_status = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_post.return_value = mock_response_obj

            mal = MAL(config=mal_config)

            # Test with non-OpenAI model name (should default)
            await mal._openai_generate("Test", "qwen2.5-coder:7b")

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            # Should default to gpt-4-turbo-preview
            assert payload["model"] == "gpt-4-turbo-preview"
