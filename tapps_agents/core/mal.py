"""
Model Abstraction Layer (MAL) - Routes requests to appropriate LLM providers

Supports:
- Ollama (local) - with streaming support
- Anthropic Claude (cloud)
- OpenAI (cloud)
- Automatic fallback
"""

import json
import logging
import os
from collections.abc import Callable

import httpx

from .config import MALConfig
from .exceptions import MALDisabledInCursorModeError
from .runtime_mode import RuntimeMode, detect_runtime_mode

logger = logging.getLogger(__name__)


class MAL:
    """Model Abstraction Layer - Routes to local or cloud models"""

    def __init__(self, config: MALConfig | None = None, ollama_url: str | None = None):
        """
        Initialize MAL with configuration.

        Args:
            config: MALConfig instance (from ProjectConfig.mal)
            ollama_url: Optional Ollama URL (legacy support, overrides config)
        """
        if config is None:
            # Create default config
            from .config import MALConfig

            config = MALConfig()

        self.config = config
        self.ollama_url = ollama_url or config.ollama_url
        self.timeout = config.timeout

        # Create granular timeout configuration (2025 best practice)
        self.timeout_config = httpx.Timeout(
            connect=config.connect_timeout,
            read=config.read_timeout,
            write=config.write_timeout,
            pool=config.pool_timeout,
        )

        # Initialize HTTP client with granular timeouts
        self.client = httpx.AsyncClient(timeout=self.timeout_config)

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        provider: str | None = None,
        enable_fallback: bool | None = None,
        **kwargs,
    ) -> str:
        """
        Generate text using specified model provider with automatic fallback.

        Args:
            prompt: Input prompt
            model: Model name (defaults to config default_model)
            provider: Provider type ("ollama", "anthropic", "openai")
            enable_fallback: Override config fallback setting
            **kwargs: Additional model parameters

        Returns:
            Generated text response

        Raises:
            ConnectionError: If all providers fail
            ValueError: If provider is invalid
        """
        # Option A policy: when running under Cursor/Background Agents,
        # Cursor is the only LLM runtime. The framework must not call MAL.
        if detect_runtime_mode() == RuntimeMode.CURSOR:
            raise MALDisabledInCursorModeError(
                "MAL is disabled when running under Cursor/Background Agents. "
                "Run LLM-driven steps in Cursor (Skills/Chat/Background Agents) using the user's configured model, "
                "or run the CLI headlessly with TAPPS_AGENTS_MODE=headless to enable MAL (optional)."
            )

        model = model or self.config.default_model
        provider = provider or self.config.default_provider
        enable_fallback = (
            enable_fallback
            if enable_fallback is not None
            else self.config.enable_fallback
        )

        # Try primary provider
        try:
            if provider == "ollama":
                return await self._ollama_generate(prompt, model, **kwargs)
            elif provider == "anthropic":
                return await self._anthropic_generate(prompt, model, **kwargs)
            elif provider == "openai":
                return await self._openai_generate(prompt, model, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except Exception as e:
            # If fallback enabled and primary failed, try fallback providers
            if enable_fallback and provider == "ollama":
                # Try cloud fallback
                for fallback_provider in self.config.fallback_providers:
                    try:
                        if fallback_provider == "anthropic":
                            return await self._anthropic_generate(
                                prompt, model, **kwargs
                            )
                        elif fallback_provider == "openai":
                            return await self._openai_generate(prompt, model, **kwargs)
                    except Exception:
                        logger.debug(
                            "Fallback provider %s failed; trying next",
                            fallback_provider,
                            exc_info=True,
                        )
                        continue  # nosec B112 - intentional fallback loop

            # All providers failed
            raise ConnectionError(
                f"All providers failed. Last error from {provider}: {e}"
            ) from e

    async def _ollama_generate(self, prompt: str, model: str, **kwargs) -> str:
        """
        Generate using Ollama with automatic streaming detection.

        Args:
            prompt: Input prompt
            model: Model name
            **kwargs: Additional model parameters, including:
                - progress_callback: Optional callback for streaming progress
                - stream: Optional boolean to force streaming/non-streaming

        Returns:
            Generated text response
        """
        # Extract progress_callback from kwargs if provided
        progress_callback = kwargs.pop("progress_callback", None)

        # Determine if streaming should be used
        use_streaming = kwargs.get("stream", None)
        if use_streaming is None:
            # Auto-detect: use streaming for large prompts or if enabled in config
            use_streaming = (
                self.config.use_streaming
                and len(prompt) > self.config.streaming_threshold
            )

        if use_streaming:
            return await self._ollama_generate_streaming(
                prompt, model, progress_callback, **kwargs
            )
        else:
            return await self._ollama_generate_non_streaming(prompt, model, **kwargs)

    async def _ollama_generate_streaming(
        self,
        prompt: str,
        model: str,
        progress_callback: Callable[[str], None] | None = None,
        **kwargs,
    ) -> str:
        """
        Generate using Ollama with streaming (2025 best practice).

        Streams response tokens in real-time using newline-delimited JSON (ndjson).
        This prevents timeouts on large files and provides better UX.

        Args:
            prompt: Input prompt
            model: Model name
            progress_callback: Optional callback for streaming progress
            **kwargs: Additional model parameters

        Returns:
            Accumulated generated text response
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout_config) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": True,  # Enable streaming
                        **{
                            k: v
                            for k, v in kwargs.items()
                            if k not in ("timeout", "stream")
                        },
                    },
                ) as response:
                    response.raise_for_status()

                    accumulated_response = ""
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk = json.loads(line)
                                chunk_text = chunk.get("response", "")
                                accumulated_response += chunk_text

                                # Call progress callback if provided
                                if progress_callback and chunk_text:
                                    progress_callback(chunk_text)

                                # Check if generation is complete
                                if chunk.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                # Skip invalid JSON lines (shouldn't happen, but be defensive)
                                continue

                    return accumulated_response
        except httpx.RequestError as e:
            raise ConnectionError(
                f"Ollama request failed ({e.__class__.__name__}): {e}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise ConnectionError(
                f"Ollama API returned error status {e.response.status_code}: {e.response.text}"
            ) from e
        except Exception as e:
            raise ConnectionError(
                f"An unexpected error occurred during Ollama streaming: {e}"
            ) from e

    async def _ollama_generate_non_streaming(
        self, prompt: str, model: str, **kwargs
    ) -> str:
        """
        Generate using Ollama without streaming (for small prompts).

        Args:
            prompt: Input prompt
            model: Model name
            **kwargs: Additional model parameters

        Returns:
            Generated text response
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout_config) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        **{k: v for k, v in kwargs.items() if k != "timeout"},
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except httpx.RequestError as e:
            raise ConnectionError(
                f"Ollama request failed ({e.__class__.__name__}): {e}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise ConnectionError(
                f"Ollama API returned error status {e.response.status_code}: {e.response.text}"
            ) from e
        except Exception as e:
            raise ConnectionError(
                f"An unexpected error occurred during Ollama request: {e}"
            ) from e

    async def _anthropic_generate(self, prompt: str, model: str, **kwargs) -> str:
        """Generate using Anthropic Claude API"""
        api_key = (
            self.config.anthropic.api_key
            if self.config.anthropic
            else os.getenv("ANTHROPIC_API_KEY")
        )

        if not api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY env var or config.anthropic.api_key"
            )

        base_url = (
            self.config.anthropic.base_url
            if self.config.anthropic and self.config.anthropic.base_url
            else "https://api.anthropic.com/v1"
        )

        # Use granular timeout configuration (2025 best practice)
        timeout_config = self.timeout_config
        if self.config.anthropic and self.config.anthropic.timeout:
            # Override with provider-specific timeout if configured
            timeout_config = httpx.Timeout(
                connect=self.config.connect_timeout,
                read=self.config.anthropic.timeout,
                write=self.config.write_timeout,
                pool=self.config.pool_timeout,
            )

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        # Map model names (default to claude-3-sonnet if not specified)
        if (
            model.startswith("claude")
            or "sonnet" in model.lower()
            or "haiku" in model.lower()
        ):
            # Model name already in Anthropic format
            anthropic_model = model
        else:
            # Default to claude-3-sonnet-20240229
            anthropic_model = "claude-3-sonnet-20240229"

        payload = {
            "model": anthropic_model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": [{"role": "user", "content": prompt}],
        }

        async with httpx.AsyncClient(timeout=timeout_config) as client:
            response = await client.post(
                f"{base_url}/messages", headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Extract content from Anthropic response
            if "content" in data and len(data["content"]) > 0:
                return data["content"][0].get("text", "")
            return ""

    async def _openai_generate(self, prompt: str, model: str, **kwargs) -> str:
        """Generate using OpenAI API"""
        api_key = (
            self.config.openai.api_key
            if self.config.openai
            else os.getenv("OPENAI_API_KEY")
        )

        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY env var or config.openai.api_key"
            )

        base_url = (
            self.config.openai.base_url
            if self.config.openai and self.config.openai.base_url
            else "https://api.openai.com/v1"
        )

        # Use granular timeout configuration (2025 best practice)
        timeout_config = self.timeout_config
        if self.config.openai and self.config.openai.timeout:
            # Override with provider-specific timeout if configured
            timeout_config = httpx.Timeout(
                connect=self.config.connect_timeout,
                read=self.config.openai.timeout,
                write=self.config.write_timeout,
                pool=self.config.pool_timeout,
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Map model names (default to gpt-4 if not specified)
        if model.startswith("gpt") or model.startswith("o1"):
            # Model name already in OpenAI format
            openai_model = model
        else:
            # Default to gpt-4-turbo-preview
            openai_model = "gpt-4-turbo-preview"

        payload = {
            "model": openai_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
        }

        async with httpx.AsyncClient(timeout=timeout_config) as client:
            response = await client.post(
                f"{base_url}/chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Extract content from OpenAI response
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"].get("content", "")
            return ""

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
