"""
Model Abstraction Layer (MAL) - Routes requests to appropriate LLM providers

Supports:
- Ollama (local)
- Anthropic Claude (cloud)
- OpenAI (cloud)
- Automatic fallback
"""

import asyncio
from typing import Optional, Any
import httpx
import os

from .config import MALConfig


class MAL:
    """Model Abstraction Layer - Routes to local or cloud models"""
    
    def __init__(self, config: Optional[MALConfig] = None, ollama_url: Optional[str] = None):
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
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        enable_fallback: Optional[bool] = None,
        **kwargs
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
        model = model or self.config.default_model
        provider = provider or self.config.default_provider
        enable_fallback = enable_fallback if enable_fallback is not None else self.config.enable_fallback
        
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
                            return await self._anthropic_generate(prompt, model, **kwargs)
                        elif fallback_provider == "openai":
                            return await self._openai_generate(prompt, model, **kwargs)
                    except Exception as fallback_error:
                        continue  # Try next fallback
            
            # All providers failed
            raise ConnectionError(
                f"All providers failed. Last error from {provider}: {e}"
            ) from e
    
    async def _ollama_generate(self, prompt: str, model: str, **kwargs) -> str:
        """Generate using Ollama"""
        response = await self.client.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    
    async def _anthropic_generate(self, prompt: str, model: str, **kwargs) -> str:
        """Generate using Anthropic Claude API"""
        api_key = (
            self.config.anthropic.api_key if self.config.anthropic 
            else os.getenv("ANTHROPIC_API_KEY")
        )
        
        if not api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY env var or config.anthropic.api_key")
        
        base_url = (
            self.config.anthropic.base_url if self.config.anthropic and self.config.anthropic.base_url
            else "https://api.anthropic.com/v1"
        )
        
        timeout = (
            self.config.anthropic.timeout if self.config.anthropic
            else self.timeout
        )
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Map model names (default to claude-3-sonnet if not specified)
        if model.startswith("claude") or "sonnet" in model.lower() or "haiku" in model.lower():
            # Model name already in Anthropic format
            anthropic_model = model
        else:
            # Default to claude-3-sonnet-20240229
            anthropic_model = "claude-3-sonnet-20240229"
        
        payload = {
            "model": anthropic_model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{base_url}/messages",
                headers=headers,
                json=payload
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
            self.config.openai.api_key if self.config.openai
            else os.getenv("OPENAI_API_KEY")
        )
        
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY env var or config.openai.api_key")
        
        base_url = (
            self.config.openai.base_url if self.config.openai and self.config.openai.base_url
            else "https://api.openai.com/v1"
        )
        
        timeout = (
            self.config.openai.timeout if self.config.openai
            else self.timeout
        )
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
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
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
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

