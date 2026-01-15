"""
Reviewer Result Cache - Cache reviewer command results based on file content hash.

2025 Performance Pattern: Result caching for reviewer commands (score, review, lint).
Provides 90%+ speedup for unchanged files by caching results based on file content hash.

References:
- docs/PERFORMANCE_OPTIMIZATION_RECOMMENDATIONS_2025.md
- docs/PERFORMANCE_PATTERNS_QUICK_REFERENCE.md
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ReviewerResultCache:
    """
    Cache reviewer command results based on file content hash.
    
    Features:
    - Content-based cache keys (invalidates on file changes)
    - Version-aware caching (invalidates on command version changes)
    - TTL-based expiration (configurable)
    - Atomic file operations (thread-safe)
    
    Cache Key Format: {file_path}:{content_hash}:{command}:{version}
    
    Example:
        cache = ReviewerResultCache()
        
        # Check cache before execution
        cached = await cache.get_cached_result(file_path, "score", version="1.0")
        if cached:
            return cached
        
        # Execute and cache
        result = await reviewer.run("score", file=str(file_path))
        await cache.save_result(file_path, "score", "1.0", result)
    """
    
    # Default cache version (increment to invalidate all caches)
    CACHE_VERSION = "1.0.0"
    
    # Default TTL in seconds (1 hour)
    DEFAULT_TTL = 3600
    
    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl_seconds: int = DEFAULT_TTL,
        enabled: bool = True,
    ):
        """
        Initialize the reviewer result cache.
        
        Args:
            cache_dir: Directory for cache files (default: .tapps-agents/cache/reviewer)
            ttl_seconds: Time-to-live for cache entries in seconds (default: 3600)
            enabled: Whether caching is enabled (default: True)
        """
        if cache_dir is None:
            # Use project root detection instead of current working directory
            from ...core.path_validator import PathValidator
            validator = PathValidator()
            cache_dir = validator.project_root / ".tapps-agents" / "cache" / "reviewer"
        
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
        if self._metadata is None:
            return
        
        try:
            # Atomic write: write to temp file, then rename
            temp_file = self.metadata_file.with_suffix(".tmp")
            temp_file.write_text(
                json.dumps(self._metadata, indent=2),
                encoding="utf-8"
            )
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
    
    def _make_cache_key(
        self,
        file_path: Path,
        command: str,
        version: str,
    ) -> str:
        """
        Create cache key from file path, content hash, command, and version.
        
        Format: {normalized_path}:{content_hash}:{command}:{version}
        """
        # Normalize path for consistent keys
        normalized_path = str(file_path.resolve()).replace("\\", "/")
        file_hash = self._file_hash(file_path)
        
        return f"{normalized_path}:{file_hash}:{command}:{version}"
    
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
        file_path = Path(entry.get("file_path", ""))
        if file_path.exists():
            current_hash = self._file_hash(file_path)
            cached_hash = entry.get("file_hash", "")
            if current_hash != cached_hash:
                logger.debug(f"Cache invalidated for {cache_key} (file changed)")
                return False
        
        return True
    
    async def get_cached_result(
        self,
        file_path: Path,
        command: str,
        version: str = CACHE_VERSION,
    ) -> dict[str, Any] | None:
        """
        Get cached result if file unchanged and cache valid.
        
        Args:
            file_path: Path to the file being analyzed
            command: Command name (e.g., "score", "review", "lint")
            version: Command version for cache invalidation
            
        Returns:
            Cached result dict or None if cache miss
        """
        if not self.enabled:
            return None
        
        if not file_path.exists():
            return None
        
        # Try current version first
        cache_key = self._make_cache_key(file_path, command, version)
        
        # Check if cache is valid
        if self._is_cache_valid(cache_key):
            cache_file = self._get_cache_file(cache_key)
            if cache_file.exists():
                try:
                    content = cache_file.read_text(encoding="utf-8")
                    result = json.loads(content)
                    self._hits += 1
                    logger.debug(f"Cache hit for {file_path} ({command})")
                    return result
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning(f"Failed to load cache for {file_path}: {e}")
        
        # Backward compatibility: Check for cache entries with package version
        # (old cache entries may have been saved with package version instead of cache version)
        try:
            from ... import __version__ as package_version
            if package_version != version:
                old_cache_key = self._make_cache_key(file_path, command, package_version)
                if self._is_cache_valid(old_cache_key):
                    cache_file = self._get_cache_file(old_cache_key)
                    if cache_file.exists():
                        try:
                            content = cache_file.read_text(encoding="utf-8")
                            result = json.loads(content)
                            # Migrate to new cache key format
                            await self.save_result(file_path, command, version, result)
                            # Remove old cache entry
                            if old_cache_key in self.metadata:
                                self.metadata.pop(old_cache_key, None)
                                try:
                                    cache_file.unlink(missing_ok=True)
                                except OSError:
                                    pass
                                self._save_metadata()
                            self._hits += 1
                            logger.debug(f"Cache hit for {file_path} ({command}) - migrated from package version")
                            return result
                        except (json.JSONDecodeError, OSError) as e:
                            logger.warning(f"Failed to load old cache for {file_path}: {e}")
        except ImportError:
            # Package version not available, skip backward compatibility check
            pass
        
        self._misses += 1
        return None
    
    async def save_result(
        self,
        file_path: Path,
        command: str,
        version: str,
        result: dict[str, Any],
    ) -> None:
        """
        Save result to cache.
        
        Args:
            file_path: Path to the file being analyzed
            command: Command name (e.g., "score", "review", "lint")
            version: Command version for cache invalidation
            result: Result to cache
        """
        if not self.enabled:
            return
        
        if not file_path.exists():
            return
        
        cache_key = self._make_cache_key(file_path, command, version)
        file_hash = self._file_hash(file_path)
        
        # Save result to cache file
        cache_file = self._get_cache_file(cache_key)
        try:
            cache_file.write_text(
                json.dumps(result, indent=2, default=str),
                encoding="utf-8"
            )
        except OSError as e:
            logger.warning(f"Failed to save cache for {file_path}: {e}")
            return
        
        # Update metadata
        self.metadata[cache_key] = {
            "file_path": str(file_path.resolve()),
            "file_hash": file_hash,
            "command": command,
            "version": version,
            "cached_at": datetime.now(UTC).isoformat() + "Z",
        }
        self._save_metadata()
        
        logger.debug(f"Cached result for {file_path} ({command})")
    
    def invalidate_file(self, file_path: Path) -> int:
        """
        Invalidate all cache entries for a file.
        
        Returns:
            Number of entries invalidated
        """
        if not self.enabled:
            return 0
        
        normalized_path = str(file_path.resolve()).replace("\\", "/")
        keys_to_remove = [
            key for key in self.metadata
            if key.startswith(normalized_path + ":")
        ]
        
        for key in keys_to_remove:
            self.metadata.pop(key, None)
            cache_file = self._get_cache_file(key)
            try:
                cache_file.unlink(missing_ok=True)
            except OSError:
                pass
        
        if keys_to_remove:
            self._save_metadata()
        
        return len(keys_to_remove)
    
    def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        if not self.enabled:
            return 0
        
        count = len(self.metadata)
        
        # Remove cache files
        for key in self.metadata:
            cache_file = self._get_cache_file(key)
            try:
                cache_file.unlink(missing_ok=True)
            except OSError:
                pass
        
        # Clear metadata
        self._metadata = {}
        self._save_metadata()
        
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
            "enabled": self.enabled,
            "cache_dir": str(self.cache_dir),
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
        if not self.enabled:
            return 0
        
        keys_to_remove = [
            key for key in self.metadata
            if not self._is_cache_valid(key)
        ]
        
        for key in keys_to_remove:
            self.metadata.pop(key, None)
            cache_file = self._get_cache_file(key)
            try:
                cache_file.unlink(missing_ok=True)
            except OSError:
                pass
        
        if keys_to_remove:
            self._save_metadata()
        
        return len(keys_to_remove)


# Global cache instance (lazy initialization)
_global_cache: ReviewerResultCache | None = None


def get_reviewer_cache() -> ReviewerResultCache:
    """
    Get the global reviewer cache instance.
    
    Returns:
        Global ReviewerResultCache instance
    """
    global _global_cache
    if _global_cache is None:
        # Check if caching is enabled via environment variable
        enabled = os.getenv("TAPPS_AGENTS_CACHE_ENABLED", "true").lower() == "true"
        _global_cache = ReviewerResultCache(enabled=enabled)
    return _global_cache


def reset_reviewer_cache() -> None:
    """Reset the global reviewer cache instance."""
    global _global_cache
    _global_cache = None
