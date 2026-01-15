"""
Centralized debug logger utility for tapps-agents.

Provides consistent debug logging with:
- Project root detection (not current working directory)
- Non-blocking error handling
- Automatic directory creation
- Structured JSON logging

This utility fixes the path resolution issue where debug logs were written
to subdirectories instead of project root, causing failures when running
from subdirectories.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .path_validator import PathValidator

logger = logging.getLogger(__name__)


def write_debug_log(
    message: dict[str, Any],
    project_root: Path | None = None,
    location: str | None = None,
) -> bool:
    """
    Write debug log entry with project root detection and non-blocking error handling.
    
    This function ensures debug logs are always written to the project root's
    `.cursor/debug.log` file, regardless of the current working directory.
    
    Args:
        message: Dictionary containing log entry data
        project_root: Optional project root (auto-detected if None)
        location: Optional location identifier (e.g., "reviewer/agent.py:733")
    
    Returns:
        True if log was written successfully, False otherwise (non-blocking)
    
    Example:
        >>> write_debug_log({
        ...     "sessionId": "session-123",
        ...     "message": "Operation started",
        ...     "data": {"file": "src/main.py"}
        ... }, location="reviewer/agent.py:733")
    """
    try:
        # Use PathValidator to detect project root (not current working directory)
        validator = PathValidator(project_root)
        log_path = validator.project_root / ".cursor" / "debug.log"
        
        # Create .cursor directory if it doesn't exist
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare log entry with timestamp and location
        log_entry = {
            **message,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "iso_timestamp": datetime.now().isoformat(),
        }
        
        if location:
            log_entry["location"] = location
        
        # Write log entry (append mode)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        return True
        
    except (OSError, IOError) as e:
        # Silently ignore - debug logs are non-critical
        # Only log to Python logger at debug level (not stderr)
        logger.debug(f"Debug log write failed (non-critical): {e}")
        return False
    except Exception as e:
        # Catch any other unexpected errors
        logger.debug(f"Unexpected error in debug log write: {e}")
        return False


def get_debug_log_path(project_root: Path | None = None) -> Path:
    """
    Get the debug log path for the project root.
    
    Args:
        project_root: Optional project root (auto-detected if None)
    
    Returns:
        Path to debug.log file in project root's .cursor directory
    
    Example:
        >>> log_path = get_debug_log_path()
        >>> print(f"Debug logs at: {log_path}")
    """
    validator = PathValidator(project_root)
    return validator.project_root / ".cursor" / "debug.log"


def ensure_debug_log_directory(project_root: Path | None = None) -> bool:
    """
    Ensure the .cursor directory exists for debug logs.
    
    Args:
        project_root: Optional project root (auto-detected if None)
    
    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        validator = PathValidator(project_root)
        cursor_dir = validator.project_root / ".cursor"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, IOError) as e:
        logger.debug(f"Failed to create .cursor directory: {e}")
        return False
