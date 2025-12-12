"""
Context Manager - Manages tiered context with caching.
"""

import hashlib
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any

from .ast_parser import ASTParser
from .tiered_context import ContextTier, TieredContextBuilder


class ContextCache:
    """LRU cache for context entries with TTL."""

    def __init__(self, max_size: int = 100):
        self.cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.max_size = max_size
        self.timestamps: dict[str, datetime] = {}

    def get(self, key: str, ttl: int) -> dict[str, Any] | None:
        """
        Get cached entry if it exists and hasn't expired.

        Args:
            key: Cache key
            ttl: Time-to-live in seconds

        Returns:
            Cached entry or None if expired/missing
        """
        if key not in self.cache:
            return None

        # Check TTL
        if key in self.timestamps:
            age = (datetime.now() - self.timestamps[key]).total_seconds()
            if age > ttl:
                # Expired - remove
                del self.cache[key]
                del self.timestamps[key]
                return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: dict[str, Any]):
        """Put entry in cache with current timestamp."""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            if oldest_key in self.timestamps:
                del self.timestamps[oldest_key]

        self.cache[key] = value
        self.timestamps[key] = datetime.now()
        self.cache.move_to_end(key)

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()

    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


class ContextManager:
    """Manages tiered context with caching."""

    def __init__(self, cache_size: int = 100):
        self.ast_parser = ASTParser()
        self.context_builder = TieredContextBuilder(self.ast_parser)
        self.caches: dict[ContextTier, ContextCache] = {
            tier: ContextCache(max_size=cache_size) for tier in ContextTier
        }

    def get_context(
        self,
        file_path: Path,
        tier: ContextTier,
        include_related: bool = False,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Get context for a file at the specified tier.

        Args:
            file_path: Path to the file
            tier: Context tier level
            include_related: Whether to include related files
            use_cache: Whether to use cache

        Returns:
            Dictionary with tiered context
        """
        # Generate cache key
        cache_key = self._generate_cache_key(file_path, tier, include_related)

        # Check cache
        if use_cache:
            config = self.context_builder.TIER_CONFIGS[tier]
            cached = self.caches[tier].get(cache_key, config.cache_ttl)
            if cached:
                cached["cached"] = True
                return cached

        # Build context
        context = self.context_builder.build_context(file_path, tier, include_related)

        # Cache result
        if use_cache:
            self.caches[tier].put(cache_key, context)
            context["cached"] = False

        return context

    def get_context_text(
        self, file_path: Path, tier: ContextTier, format: str = "text"
    ) -> str:
        """
        Get context as formatted text.

        Args:
            file_path: Path to the file
            tier: Context tier level
            format: Output format (text/markdown/json)

        Returns:
            Formatted context string
        """
        context = self.get_context(file_path, tier)

        if format == "json":
            import json

            return json.dumps(context, indent=2)
        elif format == "markdown":
            return self._format_as_markdown(context)
        else:  # text
            return self._format_as_text(context)

    def _generate_cache_key(
        self, file_path: Path, tier: ContextTier, include_related: bool
    ) -> str:
        """Generate cache key for file and tier."""
        # Include file path, tier, and file modification time for cache invalidation
        try:
            mtime = file_path.stat().st_mtime
        except (OSError, FileNotFoundError):
            mtime = 0

        key_data = f"{file_path}:{tier.value}:{include_related}:{mtime}"
        # Use a modern hash even for cache keys (not security-related).
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _format_as_text(self, context: dict[str, Any]) -> str:
        """Format context as plain text."""
        lines = [f"Context for {context['file']} (Tier {context['tier']})"]
        lines.append("=" * 60)

        content = context.get("content", {})

        if "structure" in content:
            lines.append("\nStructure:")
            struct = content["structure"]
            lines.append(f"  Functions: {', '.join(struct.get('functions', []))}")
            lines.append(f"  Classes: {', '.join(struct.get('classes', []))}")

        if "functions" in content:
            lines.append("\nFunctions:")
            for func in content["functions"]:
                lines.append(f"  {func['signature']}")
                if func.get("docstring"):
                    lines.append(f"    {func['docstring'][:100]}...")

        if "classes" in content:
            lines.append("\nClasses:")
            for cls in content["classes"]:
                lines.append(f"  class {cls['name']}({', '.join(cls['bases'])})")
                lines.append(f"    Methods: {', '.join(cls['methods'])}")

        lines.append(f"\nToken estimate: {context.get('token_estimate', 0)}")

        return "\n".join(lines)

    def _format_as_markdown(self, context: dict[str, Any]) -> str:
        """Format context as markdown."""
        lines = [f"# Context: {Path(context['file']).name}"]
        lines.append(f"\n**Tier:** {context['tier']}")
        lines.append(f"**File:** `{context['file']}`")
        lines.append(f"**Token Estimate:** {context.get('token_estimate', 0)}")
        lines.append("\n---\n")

        content = context.get("content", {})

        if "functions" in content:
            lines.append("## Functions\n")
            for func in content["functions"]:
                lines.append(f"### `{func['name']}`")
                lines.append(f"```python\n{func['signature']}\n```")
                if func.get("docstring"):
                    lines.append(f"\n{func['docstring']}\n")

        if "classes" in content:
            lines.append("## Classes\n")
            for cls in content["classes"]:
                lines.append(f"### `{cls['name']}`")
                if cls.get("bases"):
                    lines.append(f"**Bases:** {', '.join(cls['bases'])}")
                if cls.get("methods"):
                    lines.append(f"**Methods:** {', '.join(cls['methods'])}")
                lines.append("")

        return "\n".join(lines)

    def clear_cache(self, tier: ContextTier | None = None):
        """
        Clear cache for a specific tier or all tiers.

        Args:
            tier: Tier to clear, or None for all tiers
        """
        if tier:
            self.caches[tier].clear()
        else:
            for cache in self.caches.values():
                cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            tier.value: {"size": cache.size(), "max_size": cache.max_size}
            for tier, cache in self.caches.items()
        }
