"""
Real integration tests for MAL (Model Abstraction Layer).

These tests use ACTUAL LLM calls and require:
- Ollama running locally (http://localhost:11434)
- OR Anthropic API key in environment
- OR OpenAI API key in environment

Tests are marked with @pytest.mark.requires_llm and will be skipped
if no LLM service is available.
"""

import os

import pytest

from tapps_agents.core.config import MALConfig
from tapps_agents.core.mal import MAL


def check_ollama_available():
    """Check if Ollama is available."""
    import httpx
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def check_anthropic_available():
    """Check if Anthropic API key is available."""
    return os.getenv("ANTHROPIC_API_KEY") is not None


def check_openai_available():
    """Check if OpenAI API key is available."""
    return os.getenv("OPENAI_API_KEY") is not None


def has_any_llm():
    """Check if any LLM service is available."""
    return check_ollama_available() or check_anthropic_available() or check_openai_available()


pytestmark = pytest.mark.integration


@pytest.mark.requires_llm
@pytest.mark.asyncio
class TestMALRealOllama:
    """Real integration tests for MAL with Ollama - optimized for speed."""

    @pytest.fixture
    def ollama_config(self):
        """Create MAL config for Ollama."""
        if not check_ollama_available():
            pytest.skip("Ollama not available")
        return MALConfig(
            ollama_url="http://localhost:11434",
            default_model="qwen2.5-coder:7b",
            default_provider="ollama",
            enable_fallback=False,
            read_timeout=20.0,  # Reasonable timeout
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)  # Allow reasonable time for LLM response
    async def test_ollama_generate_real(self, ollama_config):
        """Test real Ollama generation - minimal test."""
        mal = MAL(config=ollama_config)
        try:
            # Absolute minimal prompt
            result = await mal.generate("OK")
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            await mal.close()

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)  # Should fail faster with invalid model
    async def test_ollama_error_handling_invalid_model(self, ollama_config):
        """Test Ollama error handling - fast failure test."""
        mal = MAL(config=ollama_config)
        try:
            with pytest.raises((ConnectionError, ValueError)):
                await mal.generate("OK", model="nonexistent-model-12345")
        finally:
            await mal.close()


@pytest.mark.requires_llm
@pytest.mark.asyncio
class TestMALRealAnthropic:
    """Real integration tests for MAL with Anthropic - optimized for speed."""

    @pytest.fixture
    def anthropic_config(self):
        """Create MAL config for Anthropic."""
        if not check_anthropic_available():
            pytest.skip("Anthropic API key not available")
        return MALConfig(
            default_provider="anthropic",
            default_model="claude-3-haiku-20240307",  # Fastest model
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            enable_fallback=False,
            read_timeout=20.0,
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_anthropic_generate_real(self, anthropic_config):
        """Test real Anthropic generation - minimal test."""
        mal = MAL(config=anthropic_config)
        try:
            result = await mal.generate("OK")
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            await mal.close()


@pytest.mark.requires_llm
@pytest.mark.asyncio
class TestMALRealFallback:
    """Real integration tests for MAL fallback - optimized for speed."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(35)  # Fallback takes longer
    async def test_fallback_ollama_to_anthropic(self):
        """Test fallback from Ollama to Anthropic - minimal."""
        if not (check_ollama_available() and check_anthropic_available()):
            pytest.skip("Both Ollama and Anthropic required")
        
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_provider="ollama",
            default_model="nonexistent-model-12345",
            enable_fallback=True,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            read_timeout=20.0,
        )
        
        mal = MAL(config=config)
        try:
            result = await mal.generate("OK")
            assert isinstance(result, str)
        finally:
            await mal.close()

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)  # Should fail fast
    async def test_fallback_disabled_raises_error(self):
        """Test fallback disabled - fast failure test."""
        if not check_ollama_available():
            pytest.skip("Ollama required")
        
        config = MALConfig(
            ollama_url="http://localhost:11434",
            default_provider="ollama",
            default_model="nonexistent-model-12345",
            enable_fallback=False,
            read_timeout=5.0,  # Fast timeout
        )
        
        mal = MAL(config=config)
        try:
            with pytest.raises((ConnectionError, ValueError)):
                await mal.generate("OK")
        finally:
            await mal.close()


@pytest.mark.requires_llm
@pytest.mark.asyncio
class TestMALRealPerformance:
    """Real integration tests for MAL performance - optimized."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_response_time_acceptable(self):
        """Test LLM response time - minimal test."""
        if not has_any_llm():
            pytest.skip("No LLM service available")
        
        if check_ollama_available():
            config = MALConfig(
                ollama_url="http://localhost:11434",
                default_provider="ollama",
                default_model="qwen2.5-coder:7b",
                read_timeout=20.0,
            )
        elif check_anthropic_available():
            config = MALConfig(
                default_provider="anthropic",
                default_model="claude-3-haiku-20240307",
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                read_timeout=20.0,
            )
        else:
            pytest.skip("No LLM service available")
        
        import time
        mal = MAL(config=config)
        try:
            start = time.time()
            result = await mal.generate("OK")
            elapsed = time.time() - start
            
            assert isinstance(result, str)
            assert elapsed < 20.0, f"Too slow: {elapsed:.2f}s"
        finally:
            await mal.close()

