"""
Agent Result Cache - Generic caching for agent command results.

2025 Performance Pattern: Result caching for agent commands.
Provides 90%+ speedup for unchanged files by caching results based on file content hash.

This module provides a generic cache that can be used by any agent that performs
file-based analysis operations. The cache invalidates when:
- File content changes (content-based hash)
- Agent version changes
- TTL expires (configurable)

References:
- docs/PERFORMANCE_OPTIMIZATION_RECOMMENDATIONS_2025.md
- docs/PERFORMANCE_PATTERNS_QUICK_REFERENCE.md
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AgentResultCache:
    """
    Generic cache for agent command results based on file content hash.
    
    Features:
    - Content-based cache keys (invalidates on file changes)
    - Version-aware caching (invalidates on agent version changes)
    - TTL-based expiration (configurable)
    - Atomic file operations (thread-safe)
    - Multi-file support (for commands that analyze multiple files)
    
    Cache Key Format: {agent}:{command}:{file_hash}:{version}
    
    Example:
        cache = AgentResultCache("tester")
        
        # Check cache before execution
        cached = await cache.get_cached_result(file_path, "generate-tests", version="1.0")
        if cached:
            return cached
        
        # Execute and cache
        result = await tester.run("generate-tests", file=str(file_path))
        await cache.save_result(file_path, "generate-tests", "1.0", result)
    """
    
    # Default cache version (increment to invalidate all caches)
    CACHE_VERSION = "1.0.0"
    
    def __init__(
        self,
        agent_name: str,
        cache_dir: Path | None = None,
        ttl_seconds: int = 3600,
        enabled: bool = True,
    ):
        """
        Initialize the agent result cache.
        
        Args:
            agent_name: Name of the agent (e.g., "tester", "documenter")
            cache_dir: Directory for cache files (default: .tapps-agents/cache/{agent_name})
            ttl_seconds: Time-to-live for cache entries in seconds (default: 3600)
            enabled: Whether caching is enabled (default: True)
        """
        self.agent_name = agent_name
        
        if cache_dir is None:
            cache_dir = Path.cwd() / ".tapps-agents" / "cache" / agent_name
        
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.enabled = enabled
        
        # Metadata file tracks cache entries and their file hashes
        self.metadata_file = self.cache_dir / "metadata.json"
        self._metadata: dict[str, dict[str, Any]] | None = None
        
        # Statistics
        self._hits = 0
        self._misses = 0
        
        # Create cache directory
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def metadata(self) -> dict[str, dict[str, Any]]:
        """Load and return cache metadata."""
        if self._metadata is None:
            self._metadata = self._load_metadata()
        return self._metadata
    
    def _load_metadata(self) -> dict[str, dict[str, Any]]:
        """Load cache metadata from file."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            content = self.metadata_file.read_text(encoding="utf-8")
            return json.loads(content)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load cache metadata: {e}")
            return {}
    
    def _save_metadata(self) -> None:
        """Save cache metadata to file (atomic write)."""
        try:
            content = json.dumps(self.metadata, indent=2)
            temp_file = self.metadata_file.with_suffix(".tmp")
            temp_file.write_text(content, encoding="utf-8")
            temp_file.replace(self.metadata_file)
        except OSError as e:
            logger.warning(f"Failed to save cache metadata: {e}")
    
    def _file_hash(self, file_path: Path) -> str:
        """
        Compute file content hash.
        
        Uses SHA-256 truncated to 16 characters for reasonable uniqueness
        while keeping cache keys manageable.
        """
        try:
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()[:16]
        except OSError as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            return ""
    
    def _multi_file_hash(self, file_paths: list[Path]) -> str:
        """
        Compute combined hash for multiple files.
        
        Useful for commands that analyze multiple files together.
        """
        hasher = hashlib.sha256()
        for file_path in sorted(file_paths):  # Sort for consistency
            try:
                content = file_path.read_bytes()
                hasher.update(content)
            except OSError as e:
                logger.warning(f"Failed to hash file {file_path}: {e}")
        return hasher.hexdigest()[:16]
    
    def _make_cache_key(
        self,
        file_path: Path | list[Path],
        command: str,
        version: str,
    ) -> str:
        """
        Create cache key from file path(s), command, and version.
        
        Format: {agent}:{command}:{file_hash}:{version}
        """
        if isinstance(file_path, list):
            file_hash = self._multi_file_hash(file_path)
            ",".join(sorted(str(p.resolve()) for p in file_path))
        else:
            file_hash = self._file_hash(file_path)
            str(file_path.resolve()).replace("\\", "/")
        
        return f"{self.agent_name}:{command}:{file_hash}:{version}"
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path for a cache key."""
        # Use hash of cache key for filename (to handle long paths)
        key_hash = hashlib.sha256(cache_key.encode()).hexdigest()[:32]
        return self.cache_dir / f"{key_hash}.json"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cache entry is valid (not expired, file unchanged).
        """
        if cache_key not in self.metadata:
            return False
        
        entry = self.metadata[cache_key]
        
        # Check TTL
        cached_at = entry.get("cached_at", "")
        if cached_at:
            try:
                cached_time = datetime.fromisoformat(cached_at.replace("Z", "+00:00"))
                age_seconds = (datetime.now(UTC) - cached_time).total_seconds()
                if age_seconds > self.ttl_seconds:
                    logger.debug(f"Cache expired for {cache_key} (age: {age_seconds:.0f}s)")
                    return False
            except ValueError:
                pass
        
        # Check file hash (content-based invalidation)
        file_path = entry.get("file_path", "")
        if file_path:
            path = Path(file_path)
            if path.exists():
                current_hash = self._file_hash(path)
                cached_hash = entry.get("file_hash", "")
                if current_hash != cached_hash:
                    logger.debug(f"Cache invalidated for {cache_key} (file changed)")
                    return False
        
        return True
    
    async def get_cached_result(
        self,
        file_path: Path | list[Path],
        command: str,
        version: str = CACHE_VERSION,
    ) -> dict[str, Any] | None:
        """
        Get cached result if file unchanged and cache valid.
        
        Args:
            file_path: Path to the file(s) being analyzed
            command: Command name (e.g., "generate-tests", "document")
            version: Command version for cache invalidation
            
        Returns:
            Cached result dict or None if cache miss
        """
        if not self.enabled:
            return None
        
        # Validate file(s) exist
        paths = file_path if isinstance(file_path, list) else [file_path]
        for p in paths:
            if not p.exists():
                return None
        
        cache_key = self._make_cache_key(file_path, command, version)
        
        # Check if cache is valid
        if not self._is_cache_valid(cache_key):
            self._misses += 1
            return None
        
        # Load cached result
        cache_file = self._get_cache_file(cache_key)
        if not cache_file.exists():
            self._misses += 1
            return None
        
        try:
            content = cache_file.read_text(encoding="utf-8")
            result = json.loads(content)
            self._hits += 1
            logger.debug(f"Cache hit for {self.agent_name} {command}")
            return result
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load cache for {self.agent_name} {command}: {e}")
            self._misses += 1
            return None
    
    async def save_result(
        self,
        file_path: Path | list[Path],
        command: str,
        version: str,
        result: dict[str, Any],
    ) -> None:
        """
        Save result to cache.
        
        Args:
            file_path: Path to the file(s) being analyzed
            command: Command name
            version: Command version for cache invalidation
            result: Result to cache
        """
        if not self.enabled:
            return
        
        # Validate file(s) exist
        paths = file_path if isinstance(file_path, list) else [file_path]
        for p in paths:
            if not p.exists():
                return
        
        cache_key = self._make_cache_key(file_path, command, version)
        cache_file = self._get_cache_file(cache_key)
        
        # Compute file hash(es)
        if isinstance(file_path, list):
            file_hash = self._multi_file_hash(file_path)
            normalized_path = ",".join(sorted(str(p.resolve()) for p in file_path))
        else:
            file_hash = self._file_hash(file_path)
            normalized_path = str(file_path.resolve())
        
        # Save result file (atomic write)
        try:
            content = json.dumps(result, indent=2, default=str)
            temp_file = cache_file.with_suffix(".tmp")
            temp_file.write_text(content, encoding="utf-8")
            temp_file.replace(cache_file)
        except OSError as e:
            logger.warning(f"Failed to save cache result: {e}")
            return
        
        # Update metadata
        self.metadata[cache_key] = {
            "agent": self.agent_name,
            "file_path": normalized_path,
            "file_hash": file_hash,
            "command": command,
            "version": version,
            "cached_at": datetime.now(UTC).isoformat() + "Z",
        }
        self._save_metadata()
    
    def invalidate_file(self, file_path: Path) -> int:
        """
        Invalidate all cache entries for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of entries invalidated
        """
        normalized_path = str(file_path.resolve())
        invalidated = 0
        
        keys_to_remove = []
        for cache_key, entry in self.metadata.items():
            if entry.get("file_path") == normalized_path:
                keys_to_remove.append(cache_key)
                # Remove cache file
                cache_file = self._get_cache_file(cache_key)
                if cache_file.exists():
                    try:
                        cache_file.unlink()
                    except OSError:
                        pass
                invalidated += 1
        
        for key in keys_to_remove:
            del self.metadata[key]
        
        if invalidated > 0:
            self._save_metadata()
        
        return invalidated
    
    def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        count = len(self.metadata)
        
        # Remove all cache files
        for cache_key in self.metadata:
            cache_file = self._get_cache_file(cache_key)
            if cache_file.exists():
                try:
                    cache_file.unlink()
                except OSError:
                    pass
        
        self._metadata = {}
        self._save_metadata()
        self._hits = 0
        self._misses = 0
        
        return count
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "agent": self.agent_name,
            "enabled": self.enabled,
            "ttl_seconds": self.ttl_seconds,
            "entries": len(self.metadata),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
        }
    
    def prune_expired(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries pruned
        """
        pruned = 0
        keys_to_remove = []
        
        now = datetime.now(UTC)
        for cache_key, entry in self.metadata.items():
            cached_at = entry.get("cached_at", "")
            if cached_at:
                try:
                    cached_time = datetime.fromisoformat(cached_at.replace("Z", "+00:00"))
                    age_seconds = (now - cached_time).total_seconds()
                    if age_seconds > self.ttl_seconds:
                        keys_to_remove.append(cache_key)
                        # Remove cache file
                        cache_file = self._get_cache_file(cache_key)
                        if cache_file.exists():
                            try:
                                cache_file.unlink()
                            except OSError:
                                pass
                        pruned += 1
                except ValueError:
                    pass
        
        for key in keys_to_remove:
            del self.metadata[key]
        
        if pruned > 0:
            self._save_metadata()
        
        return pruned


# Global cache instances for each agent
_agent_caches: dict[str, AgentResultCache] = {}


def get_agent_cache(agent_name: str) -> AgentResultCache:
    """
    Get or create a cache instance for an agent.
    
    Args:
        agent_name: Name of the agent (e.g., "tester", "documenter")
        
    Returns:
        AgentResultCache instance for the agent
    """
    if agent_name not in _agent_caches:
        _agent_caches[agent_name] = AgentResultCache(agent_name)
    return _agent_caches[agent_name]


def reset_agent_cache(agent_name: str) -> None:
    """
    Reset the cache instance for an agent.
    
    Args:
        agent_name: Name of the agent
    """
    if agent_name in _agent_caches:
        del _agent_caches[agent_name]
