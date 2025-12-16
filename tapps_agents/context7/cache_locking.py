"""
File Locking for Context7 KB cache operations.

Provides atomic write operations to prevent cache corruption under parallel agents.
"""

import logging
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

# Windows doesn't support fcntl, use alternative
WINDOWS = sys.platform == "win32"

if not WINDOWS:
    import fcntl
else:
    fcntl = None  # type: ignore


class CacheLock:
    """File-based lock for cache operations."""

    def __init__(self, lock_file: Path, timeout: float = 30.0):
        """
        Initialize cache lock.

        Args:
            lock_file: Path to lock file
            timeout: Maximum time to wait for lock (seconds)
        """
        self.lock_file = Path(lock_file)
        self.timeout = timeout
        self.lock_fd = None

    def acquire(self) -> bool:
        """
        Acquire lock.

        Returns:
            True if lock acquired, False otherwise
        """
        if not self.lock_file.parent.exists():
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                if WINDOWS:
                    # Windows file locking using msvcrt
                    try:
                        self.lock_fd = open(self.lock_file, "w")
                        # Try to lock the file (non-blocking)
                        # On Windows, we use a simple exclusive file creation approach
                        # since msvcrt.locking has limitations
                        # Create lock file atomically
                        if self.lock_file.exists():
                            # Check if lock is stale (older than timeout)
                            import os
                            lock_age = time.time() - os.path.getmtime(self.lock_file)
                            if lock_age > self.timeout:
                                # Stale lock, remove it
                                try:
                                    self.lock_file.unlink()
                                except Exception:
                                    pass
                            else:
                                self.lock_fd.close()
                                self.lock_fd = None
                                time.sleep(0.1)
                                continue
                        # Write PID to lock file for debugging
                        self.lock_fd.write(str(os.getpid()))
                        self.lock_fd.flush()
                        return True
                    except (OSError, PermissionError):
                        if self.lock_fd:
                            try:
                                self.lock_fd.close()
                            except Exception:
                                pass
                        self.lock_fd = None
                        time.sleep(0.1)
                        continue
                else:
                    # Unix file locking
                    if fcntl is None:
                        raise RuntimeError("fcntl not available on this platform")
                    self.lock_fd = open(self.lock_file, "w")
                    try:
                        fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        return True
                    except OSError:
                        self.lock_fd.close()
                        self.lock_fd = None
                        time.sleep(0.1)
                        continue
            except Exception as e:
                logger.debug(f"Failed to acquire lock: {e}", exc_info=True)
                if self.lock_fd:
                    try:
                        self.lock_fd.close()
                    except Exception:
                        pass
                    self.lock_fd = None
                time.sleep(0.1)

        logger.warning(f"Failed to acquire lock after {self.timeout}s timeout")
        return False

    def release(self):
        """Release lock."""
        if self.lock_fd:
            try:
                if not WINDOWS and fcntl is not None:
                    fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
            except Exception as e:
                logger.debug(f"Error releasing lock: {e}", exc_info=True)
            finally:
                self.lock_fd = None
                # Clean up lock file if it exists
                try:
                    if self.lock_file.exists():
                        self.lock_file.unlink()
                except Exception:
                    pass

    def __enter__(self):
        """Context manager entry."""
        if not self.acquire():
            raise RuntimeError(f"Failed to acquire lock: {self.lock_file}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


@contextmanager
def cache_lock(lock_file: Path, timeout: float = 30.0) -> Generator[CacheLock]:
    """
    Context manager for cache locking.

    Args:
        lock_file: Path to lock file
        timeout: Maximum time to wait for lock (seconds)

    Yields:
        CacheLock instance

    Example:
        with cache_lock(lock_file) as lock:
            # Perform atomic cache operations
            cache.store(...)
    """
    lock = CacheLock(lock_file, timeout=timeout)
    try:
        if not lock.acquire():
            raise RuntimeError(f"Failed to acquire cache lock: {lock_file}")
        yield lock
    finally:
        lock.release()


def get_cache_lock_file(cache_root: Path, library: str | None = None) -> Path:
    """
    Get lock file path for cache operations.

    Args:
        cache_root: Cache root directory
        library: Optional library name (for library-specific locks)

    Returns:
        Path to lock file
    """
    if library:
        return cache_root / ".locks" / f"{library}.lock"
    else:
        return cache_root / ".locks" / "global.lock"
