"""
Model Abstraction Layer (MAL) - Routes requests to appropriate LLM providers
"""

import asyncio
from typing import Optional
import httpx


class MAL:
    """Model Abstraction Layer - Routes to local or cloud models"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate(
        self,
        prompt: str,
        model: str = "qwen2.5-coder:7b",
        provider: str = "ollama",
        **kwargs
    ) -> str:
        """
        Generate text using specified model provider.
        
        Args:
            prompt: Input prompt
            model: Model name (e.g., "qwen2.5-coder:7b")
            provider: Provider type ("ollama" or "cloud")
            **kwargs: Additional model parameters
            
        Returns:
            Generated text response
        """
        if provider == "ollama":
            return await self._ollama_generate(prompt, model, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def _ollama_generate(self, prompt: str, model: str, **kwargs) -> str:
        """Generate using Ollama"""
        try:
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
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

