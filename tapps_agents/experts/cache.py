"""Expert consultation caching system.

Caches expert responses to avoid redundant queries within workflows,
reducing token usage and improving response time.

@ai-prime-directive: Cache must:
- Provide 40-60% hit rate after warmup
- Respect TTL (24 hours default)
- Be thread-safe
- Track hit/miss statistics
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CachedExpertResponse:
    """Cached expert consultation response.

    Attributes:
        query_hash: Hash of query + domain
        domain: Domain name
        query: Original query text
        response: Expert response data
        experts_consulted: List of experts used
        timestamp: Cache creation time
        ttl_hours: Time to live in hours
    """
    query_hash: str
    domain: str
    query: str
    response: Any
    experts_consulted: list[str]
    timestamp: datetime
    ttl_hours: int = 24

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        expiry = self.timestamp + timedelta(hours=self.ttl_hours)
        return datetime.now() > expiry

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "query_hash": self.query_hash,
            "domain": self.domain,
            "query": self.query,
            "response": self.response,
            "experts_consulted": self.experts_consulted,
            "timestamp": self.timestamp.isoformat(),
            "ttl_hours": self.ttl_hours
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CachedExpertResponse":
        """Create from dict."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class ExpertCache:
    """Cache for expert consultations."""

    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl_hours: int = 24,
        enable_disk_cache: bool = True
    ):
        """Initialize expert cache.

        Args:
            cache_dir: Directory for disk cache
            ttl_hours: Time to live for cache entries
            enable_disk_cache: Enable persistent disk cache
        """
        if cache_dir is None:
            cache_dir = Path(".tapps-agents/cache/experts")

        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        self.enable_disk_cache = enable_disk_cache
        self._memory_cache: dict[str, CachedExpertResponse] = {}

        if self.enable_disk_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {"hits": 0, "misses": 0, "expirations": 0}

    def get(
        self,
        query: str,
        domain: str
    ) -> CachedExpertResponse | None:
        """Get cached response for query.

        Args:
            query: Expert query
            domain: Domain name

        Returns:
            Cached response or None if not found/expired
        """
        query_hash = self._hash_query(query, domain)

        # Check memory cache first
        if query_hash in self._memory_cache:
            cached = self._memory_cache[query_hash]
            if not cached.is_expired:
                self.stats["hits"] += 1
                logger.debug(f"Cache hit: {domain}")
                return cached
            else:
                self.stats["expirations"] += 1
                del self._memory_cache[query_hash]

        # Check disk cache
        if self.enable_disk_cache:
            cache_file = self.cache_dir / f"{query_hash}.json"
            if cache_file.exists():
                try:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    cached = CachedExpertResponse.from_dict(data)

                    if not cached.is_expired:
                        self._memory_cache[query_hash] = cached
                        self.stats["hits"] += 1
                        logger.debug(f"Disk cache hit: {domain}")
                        return cached
                    else:
                        self.stats["expirations"] += 1
                        cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to load cache: {e}")

        self.stats["misses"] += 1
        logger.debug(f"Cache miss: {domain}")
        return None

    def put(
        self,
        query: str,
        domain: str,
        response: Any,
        experts_consulted: list[str]
    ) -> CachedExpertResponse:
        """Cache expert response.

        Args:
            query: Expert query
            domain: Domain name
            response: Expert response
            experts_consulted: List of experts consulted

        Returns:
            Cached response object
        """
        query_hash = self._hash_query(query, domain)

        cached = CachedExpertResponse(
            query_hash=query_hash,
            domain=domain,
            query=query,
            response=response,
            experts_consulted=experts_consulted,
            timestamp=datetime.now(),
            ttl_hours=self.ttl_hours
        )

        # Save to memory cache
        self._memory_cache[query_hash] = cached

        # Save to disk cache
        if self.enable_disk_cache:
            try:
                cache_file = self.cache_dir / f"{query_hash}.json"
                cache_file.write_text(
                    json.dumps(cached.to_dict(), indent=2),
                    encoding="utf-8"
                )
            except Exception as e:
                logger.warning(f"Failed to save cache to disk: {e}")

        logger.debug(f"Cached response for: {domain}")
        return cached

    def _hash_query(self, query: str, domain: str) -> str:
        """Generate hash for query + domain."""
        content = f"{domain}:{query}".lower().strip()
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_queries = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            (self.stats["hits"] / total_queries * 100)
            if total_queries > 0 else 0
        )

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "expirations": self.stats["expirations"],
            "total_queries": total_queries,
            "hit_rate_percentage": hit_rate,
            "memory_cache_size": len(self._memory_cache),
            "disk_cache_size": (
                len(list(self.cache_dir.glob("*.json")))
                if self.enable_disk_cache else 0
            )
        }

    def clear_expired(self) -> int:
        """Clear expired cache entries.

        Returns:
            Number of entries cleared
        """
        cleared = 0

        # Clear memory cache
        expired_keys = [
            k for k, v in self._memory_cache.items()
            if v.is_expired
        ]
        for key in expired_keys:
            del self._memory_cache[key]
            cleared += 1

        # Clear disk cache
        if self.enable_disk_cache:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    cached = CachedExpertResponse.from_dict(data)
                    if cached.is_expired:
                        cache_file.unlink()
                        cleared += 1
                except Exception as e:
                    logger.warning(f"Failed to check cache expiry: {e}")

        if cleared > 0:
            logger.info(f"Cleared {cleared} expired cache entries")

        return cleared

    def clear_all(self) -> None:
        """Clear all cache entries."""
        self._memory_cache.clear()

        if self.enable_disk_cache:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

        self.stats = {"hits": 0, "misses": 0, "expirations": 0}
        logger.info("All cache entries cleared")
