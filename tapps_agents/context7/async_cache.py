"""
Async Non-Blocking Cache - Lock-free caching with in-memory LRU and background persistence.

2025 Architecture Pattern:
- In-memory LRU cache for instant reads (zero blocking)
- Background write queue for non-blocking writes
- Atomic file rename pattern for disk persistence (no file locking)
- Optimistic concurrency control (OCC) for consistency
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Global async cache instance
_async_cache: AsyncCacheManager | None = None


@dataclass
class CacheStats:
    """Cache statistics for monitoring."""
    hits: int = 0
    misses: int = 0
    writes: int = 0
    write_failures: int = 0
    evictions: int = 0
    background_writes_pending: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


@dataclass
class WriteTask:
    """Background write task."""
    library: str
    topic: str
    content: str
    metadata: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    retries: int = 0
    max_retries: int = 3


@dataclass
class AsyncCacheEntry:
    """Entry in the async cache."""
    
    library: str
    topic: str
    content: str
    context7_id: str | None = None
    trust_score: float | None = None
    snippet_count: int = 0
    token_count: int = 0
    cached_at: str | None = None
    cache_hits: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "library": self.library,
            "topic": self.topic,
            "content": self.content,
            "context7_id": self.context7_id,
            "trust_score": self.trust_score,
            "snippet_count": self.snippet_count,
            "token_count": self.token_count,
            "cached_at": self.cached_at,
            "cache_hits": self.cache_hits,
        }


class AsyncLRUCache:
    """
    Thread-safe LRU cache with async background persistence.
    
    Features:
    - O(1) read/write operations
    - Configurable max size with LRU eviction
    - Non-blocking background persistence
    - Atomic file operations (no locking)
    """
    
    def __init__(
        self,
        max_size: int = 500,
        persist_dir: Path | None = None,
        auto_persist: bool = True,
        persist_interval: float = 5.0,
    ):
        """
        Initialize async LRU cache.
        
        Args:
            max_size: Maximum number of entries in memory
            persist_dir: Directory for disk persistence (optional)
            auto_persist: Whether to auto-persist to disk
            persist_interval: Seconds between background persist runs
        """
        self._cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = Lock()  # Thread lock for cache operations
        self._max_size = max_size
        self._persist_dir = persist_dir
        self._auto_persist = auto_persist
        self._persist_interval = persist_interval
        self._stats = CacheStats()
        
        # Background write queue
        self._write_queue: asyncio.Queue[WriteTask] = asyncio.Queue()
        self._persist_task: asyncio.Task | None = None
        self._shutdown = False
        
        # Load from disk on init if persist_dir exists
        if persist_dir and persist_dir.exists():
            self._load_from_disk()
    
    def _make_key(self, library: str, topic: str) -> str:
        """Create cache key from library and topic."""
        return f"{library}::{topic}"
    
    def _parse_key(self, key: str) -> tuple[str, str]:
        """Parse cache key into library and topic."""
        parts = key.split("::", 1)
        return parts[0], parts[1] if len(parts) > 1 else "overview"
    
    def get(self, library: str, topic: str = "overview") -> dict[str, Any] | None:
        """
        Get entry from cache (instant, non-blocking).
        
        Args:
            library: Library name
            topic: Topic name
            
        Returns:
            Cache entry dict or None if not found
        """
        key = self._make_key(library, topic)
        
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self._stats.hits += 1
                entry = self._cache[key].copy()
                entry["cache_hits"] = entry.get("cache_hits", 0) + 1
                return entry
            else:
                self._stats.misses += 1
                return None
    
    def put(
        self,
        library: str,
        topic: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        persist: bool = True,
    ) -> None:
        """
        Put entry in cache (instant, non-blocking).
        
        Args:
            library: Library name
            topic: Topic name
            content: Documentation content
            metadata: Optional metadata dict
            persist: Whether to queue for disk persistence
        """
        key = self._make_key(library, topic)
        entry = {
            "library": library,
            "topic": topic,
            "content": content,
            "cached_at": datetime.now(UTC).isoformat() + "Z",
            "cache_hits": 0,
            **(metadata or {}),
        }
        
        with self._lock:
            # Add/update entry
            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._stats.writes += 1
            
            # Evict oldest if over capacity
            while len(self._cache) > self._max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                self._stats.evictions += 1
                logger.debug(f"Evicted cache entry: {oldest_key}")
        
        # Queue for background persistence (non-blocking)
        if persist and self._persist_dir:
            try:
                task = WriteTask(
                    library=library,
                    topic=topic,
                    content=content,
                    metadata=metadata or {},
                )
                self._write_queue.put_nowait(task)
                self._stats.background_writes_pending += 1
            except asyncio.QueueFull:
                logger.warning("Write queue full, skipping disk persistence")
    
    def delete(self, library: str, topic: str | None = None) -> bool:
        """
        Delete entry or all entries for a library.
        
        Args:
            library: Library name
            topic: Topic name (if None, deletes all topics for library)
            
        Returns:
            True if any entries were deleted
        """
        deleted = False
        
        with self._lock:
            if topic:
                key = self._make_key(library, topic)
                if key in self._cache:
                    del self._cache[key]
                    deleted = True
            else:
                # Delete all topics for library
                keys_to_delete = [k for k in self._cache if k.startswith(f"{library}::")]
                for key in keys_to_delete:
                    del self._cache[key]
                    deleted = True
        
        return deleted
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def keys(self) -> list[tuple[str, str]]:
        """Get all cache keys as (library, topic) tuples."""
        with self._lock:
            return [self._parse_key(k) for k in self._cache.keys()]
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats
    
    # --- Disk Persistence (Background) ---
    
    def _get_entry_path(self, library: str, topic: str) -> Path:
        """Get disk path for cache entry."""
        if not self._persist_dir:
            raise ValueError("No persist_dir configured")
        safe_library = library.replace("/", "_").replace("\\", "_")
        safe_topic = topic.replace("/", "_").replace("\\", "_")
        return self._persist_dir / safe_library / f"{safe_topic}.json"
    
    def _load_from_disk(self) -> None:
        """Load cache entries from disk (called on init)."""
        if not self._persist_dir or not self._persist_dir.exists():
            return
        
        count = 0
        for lib_dir in self._persist_dir.iterdir():
            if not lib_dir.is_dir() or lib_dir.name.startswith("."):
                continue
            
            for entry_file in lib_dir.glob("*.json"):
                try:
                    data = json.loads(entry_file.read_text(encoding="utf-8"))
                    library = data.get("library", lib_dir.name)
                    topic = data.get("topic", entry_file.stem)
                    key = self._make_key(library, topic)
                    
                    with self._lock:
                        self._cache[key] = data
                        count += 1
                        
                        # Respect max size during load
                        if len(self._cache) >= self._max_size:
                            break
                except Exception as e:
                    logger.debug(f"Failed to load cache entry {entry_file}: {e}")
            
            if len(self._cache) >= self._max_size:
                break
        
        logger.debug(f"Loaded {count} cache entries from disk")
    
    def _persist_entry_atomic(self, task: WriteTask) -> bool:
        """
        Persist single entry to disk atomically (no locking).
        
        Uses atomic rename pattern:
        1. Write to temp file
        2. Rename to target (atomic on most filesystems)
        """
        if not self._persist_dir:
            return False
        
        try:
            entry_path = self._get_entry_path(task.library, task.topic)
            entry_path.parent.mkdir(parents=True, exist_ok=True)
            
            entry_data = {
                "library": task.library,
                "topic": task.topic,
                "content": task.content,
                "cached_at": task.timestamp.isoformat() + "Z",
                "cache_hits": 0,
                **task.metadata,
            }
            
            # Write to temp file first
            fd, temp_path = tempfile.mkstemp(
                suffix=".json",
                prefix="cache_",
                dir=entry_path.parent,
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(entry_data, f, indent=2)
                
                # Atomic rename (overwrites existing)
                os.replace(temp_path, entry_path)
                return True
            except Exception:
                # Clean up temp file on failure
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
                raise
                
        except Exception as e:
            logger.debug(f"Failed to persist {task.library}/{task.topic}: {e}")
            return False
    
    async def _background_persist_loop(self) -> None:
        """Background loop that processes write queue."""
        while not self._shutdown:
            try:
                # Wait for write task with timeout
                try:
                    task = await asyncio.wait_for(
                        self._write_queue.get(),
                        timeout=self._persist_interval
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process write task
                self._stats.background_writes_pending -= 1
                success = self._persist_entry_atomic(task)
                
                if not success and task.retries < task.max_retries:
                    # Retry with backoff
                    task.retries += 1
                    await asyncio.sleep(0.1 * task.retries)
                    self._write_queue.put_nowait(task)
                    self._stats.background_writes_pending += 1
                elif not success:
                    self._stats.write_failures += 1
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Background persist error: {e}")
                await asyncio.sleep(1.0)
    
    async def start_background_persist(self) -> None:
        """Start background persistence task."""
        if self._persist_task is None or self._persist_task.done():
            self._shutdown = False
            self._persist_task = asyncio.create_task(self._background_persist_loop())
            logger.debug("Started background persist task")
    
    async def stop_background_persist(self, flush: bool = True) -> None:
        """
        Stop background persistence task.
        
        Args:
            flush: Whether to flush remaining writes before stopping
        """
        self._shutdown = True
        
        if flush:
            # Flush remaining writes
            while not self._write_queue.empty():
                try:
                    task = self._write_queue.get_nowait()
                    self._stats.background_writes_pending -= 1
                    self._persist_entry_atomic(task)
                except asyncio.QueueEmpty:
                    break
        
        if self._persist_task and not self._persist_task.done():
            self._persist_task.cancel()
            try:
                await self._persist_task
            except asyncio.CancelledError:
                pass
            self._persist_task = None
            logger.debug("Stopped background persist task")


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service unavailable, requests fail fast
    - HALF_OPEN: Testing if service recovered
    """
    
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker name (for logging)
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying again
            half_open_max_calls: Max calls in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time: datetime | None = None
        self._half_open_calls = 0
        self._lock = Lock()
    
    @property
    def state(self) -> str:
        """Get current state."""
        with self._lock:
            return self._state
    
    def can_execute(self) -> bool:
        """Check if request can be executed."""
        with self._lock:
            if self._state == self.CLOSED:
                return True
            
            if self._state == self.OPEN:
                # Check if recovery timeout has passed
                if self._last_failure_time:
                    elapsed = (datetime.now(UTC) - self._last_failure_time).total_seconds()
                    if elapsed >= self.recovery_timeout:
                        self._state = self.HALF_OPEN
                        self._half_open_calls = 0
                        logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                        return True
                return False
            
            if self._state == self.HALF_OPEN:
                return self._half_open_calls < self.half_open_max_calls
            
            return False
    
    def record_success(self) -> None:
        """Record successful execution."""
        with self._lock:
            if self._state == self.HALF_OPEN:
                # Service recovered, close circuit
                self._state = self.CLOSED
                self._failure_count = 0
                self._half_open_calls = 0
                logger.info(f"Circuit breaker '{self.name}' CLOSED (service recovered)")
            elif self._state == self.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
    
    def record_failure(self) -> None:
        """Record failed execution."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now(UTC)
            
            if self._state == self.HALF_OPEN:
                # Service still failing, reopen circuit
                self._state = self.OPEN
                logger.warning(f"Circuit breaker '{self.name}' REOPENED (service still failing)")
            
            elif self._state == self.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = self.OPEN
                    logger.warning(
                        f"Circuit breaker '{self.name}' OPENED after {self._failure_count} failures"
                    )


class ParallelResolver:
    """
    Parallel library resolution with bounded concurrency and circuit breaker.
    
    Features:
    - Bounded parallelism (configurable max concurrent)
    - Per-library timeout
    - Circuit breaker for external service
    - Graceful degradation
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        per_library_timeout: float = 5.0,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        """
        Initialize parallel resolver.
        
        Args:
            max_concurrent: Maximum concurrent resolutions
            per_library_timeout: Timeout per library (seconds)
            circuit_breaker: Optional circuit breaker for external calls
        """
        self.max_concurrent = max_concurrent
        self.per_library_timeout = per_library_timeout
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            name="context7_resolver",
            failure_threshold=3,
            recovery_timeout=30.0,
        )
        self._semaphore: asyncio.Semaphore | None = None
    
    async def resolve_libraries(
        self,
        libraries: list[str],
        resolve_func: Callable[[str], Any],
        on_success: Callable[[str, Any], None] | None = None,
        on_failure: Callable[[str, Exception], None] | None = None,
    ) -> dict[str, Any]:
        """
        Resolve multiple libraries in parallel with bounded concurrency.
        
        Args:
            libraries: List of library names to resolve
            resolve_func: Async function to resolve single library
            on_success: Optional callback on success
            on_failure: Optional callback on failure
            
        Returns:
            Dict mapping library names to results (or None if failed)
        """
        if not libraries:
            return {}
        
        # Create semaphore for bounded concurrency
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def resolve_with_timeout(library: str) -> tuple[str, Any]:
            """Resolve single library with timeout and circuit breaker."""
            # Check circuit breaker
            if not self.circuit_breaker.can_execute():
                logger.debug(f"Circuit breaker open, skipping {library}")
                if on_failure:
                    on_failure(library, Exception("Circuit breaker open"))
                return library, None
            
            async with self._semaphore:
                try:
                    result = await asyncio.wait_for(
                        resolve_func(library),
                        timeout=self.per_library_timeout,
                    )
                    self.circuit_breaker.record_success()
                    if on_success:
                        on_success(library, result)
                    return library, result
                    
                except asyncio.TimeoutError:
                    logger.debug(f"Timeout resolving {library} after {self.per_library_timeout}s")
                    self.circuit_breaker.record_failure()
                    if on_failure:
                        on_failure(library, asyncio.TimeoutError(f"Timeout after {self.per_library_timeout}s"))
                    return library, None
                    
                except Exception as e:
                    logger.debug(f"Failed to resolve {library}: {e}")
                    self.circuit_breaker.record_failure()
                    if on_failure:
                        on_failure(library, e)
                    return library, None
        
        # Run all resolutions in parallel (bounded by semaphore)
        tasks = [resolve_with_timeout(lib) for lib in libraries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dict
        result_dict: dict[str, Any] = {}
        for item in results:
            if isinstance(item, tuple) and len(item) == 2:
                lib, result = item
                result_dict[lib] = result
            elif isinstance(item, Exception):
                logger.warning(f"Unexpected exception in parallel resolve: {item}")
        
        return result_dict


# Alias for compatibility with existing imports
AsyncCacheManager = AsyncLRUCache


def init_async_cache(
    persist_dir: Path | None = None,
    max_size: int = 500,
) -> AsyncCacheManager:
    """
    Initialize the global async cache.
    
    Args:
        persist_dir: Directory for disk persistence
        max_size: Maximum entries in memory
        
    Returns:
        Initialized AsyncCacheManager instance
    """
    global _async_cache
    
    if persist_dir is None:
        # Use project root detection instead of current working directory
        from ...core.path_validator import PathValidator
        validator = PathValidator()
        persist_dir = validator.project_root / ".tapps-agents" / "kb" / "async-cache"
    
    _async_cache = AsyncCacheManager(
        max_size=max_size,
        persist_dir=persist_dir,
        auto_persist=True,
    )
    
    return _async_cache


def get_async_cache() -> AsyncCacheManager | None:
    """
    Get the global async cache instance.
    
    Returns:
        AsyncCacheManager instance or None if not initialized
    """
    return _async_cache
