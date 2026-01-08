"""
File utilities for atomic writing and safe reading of JSON files.

Provides utilities to prevent race conditions when reading/writing state files.
"""

import json
import gzip
import time
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


def atomic_write_json(
    path: Path,
    data: dict[str, Any],
    compress: bool = False,
    indent: int = 2,
    **kwargs,
) -> None:
    """
    Atomically write JSON data to a file using temp-then-rename pattern.
    
    This ensures the file is only visible when fully written, preventing
    race conditions where readers see incomplete files.
    
    Args:
        path: Target file path
        data: Data to write as JSON
        compress: Whether to compress with gzip
        indent: JSON indentation level
        **kwargs: Additional arguments for json.dump()
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temp file first
    temp_path = path.with_suffix(path.suffix + ".tmp")
    
    try:
        if compress:
            with gzip.open(temp_path, "wt", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, **kwargs)
        else:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, **kwargs)
        
        # Atomic rename (works on most filesystems)
        temp_path.replace(path)
    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        raise


def is_valid_json_file(path: Path, min_size: int = 100) -> bool:
    """
    Check if a file contains valid JSON and meets minimum size.
    
    Args:
        path: File path to check
        min_size: Minimum file size in bytes (default: 100)
    
    Returns:
        True if file is valid JSON and meets size requirement
    """
    if not path.exists():
        return False
    
    # Check file size
    try:
        if path.stat().st_size < min_size:
            return False
    except OSError:
        return False
    
    # Try to parse JSON
    try:
        if path.suffix == ".gz" or path.name.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8") as f:
                json.load(f)
        else:
            with open(path, encoding="utf-8") as f:
                json.load(f)
        return True
    except (json.JSONDecodeError, OSError, ValueError):
        return False


def is_file_stable(path: Path, min_age_seconds: float = 2.0) -> bool:
    """
    Check if a file has been stable (not modified recently).
    
    This helps avoid reading files that are still being written.
    
    Args:
        path: File path to check
        min_age_seconds: Minimum age in seconds (default: 2.0)
    
    Returns:
        True if file exists and hasn't been modified recently
    """
    if not path.exists():
        return False
    
    try:
        mtime = path.stat().st_mtime
        age = time.time() - mtime
        return age >= min_age_seconds
    except OSError:
        return False


def safe_load_json(
    path: Path,
    retries: int = 3,
    backoff: float = 0.5,
    min_age_seconds: float = 2.0,
    min_size: int = 100,
) -> dict[str, Any] | None:
    """
    Safely load JSON from a file with retry logic and validation.
    
    Args:
        path: File path to load
        retries: Number of retry attempts (default: 3)
        backoff: Backoff multiplier between retries (default: 0.5)
        min_age_seconds: Minimum file age before reading (default: 2.0)
        min_size: Minimum file size in bytes (default: 100)
    
    Returns:
        Parsed JSON data or None if loading fails
    """
    if not path.exists():
        return None
    
    # Check file size first
    try:
        if path.stat().st_size < min_size:
            logger.debug(f"File {path} too small, likely incomplete")
            return None
    except OSError:
        return None
    
    # Try loading with retries
    for attempt in range(retries):
        # Wait for file to be stable (except on first attempt if file is already old)
        if attempt > 0 or not is_file_stable(path, min_age_seconds):
            wait_time = backoff * (2 ** attempt)
            if attempt > 0:
                time.sleep(wait_time)
            elif not is_file_stable(path, min_age_seconds):
                # First attempt but file is too new, wait a bit
                time.sleep(min_age_seconds)
        
        # Validate JSON before attempting to load
        if not is_valid_json_file(path, min_size):
            if attempt < retries - 1:
                continue  # Retry
            logger.debug(f"File {path} is not valid JSON after {attempt + 1} attempts")
            return None
        
        # Try to load
        try:
            if path.suffix == ".gz" or path.name.endswith(".gz"):
                with gzip.open(path, "rt", encoding="utf-8") as f:
                    return json.load(f)
            else:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError, ValueError) as e:
            if attempt < retries - 1:
                logger.debug(f"Failed to load {path} (attempt {attempt + 1}/{retries}): {e}")
                continue  # Retry
            logger.debug(f"Failed to load {path} after {retries} attempts: {e}")
            return None
    
    return None

