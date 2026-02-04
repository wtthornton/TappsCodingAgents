"""
Path normalization utilities for cross-platform compatibility.

Handles Windows absolute paths, relative path conversion, and CLI-safe path formatting.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = [
    "normalize_path",
    "ensure_relative_path",
    "normalize_for_cli",
    "normalize_project_root",
]


def normalize_path(path: str | Path, project_root: Path) -> str:
    """
    Normalize path to relative format for CLI commands.
    
    Converts absolute paths (especially Windows absolute paths) to relative paths
    based on the project root. Handles edge cases like paths outside project root.
    
    Args:
        path: Path to normalize (can be absolute or relative)
        project_root: Project root directory for relative path calculation
        
    Returns:
        Normalized relative path string, or absolute path string if outside project root
        
    Examples:
        >>> normalize_path("c:/cursor/TappsCodingAgents/src/file.py", Path("c:/cursor/TappsCodingAgents"))
        'src/file.py'
        
        >>> normalize_path("src/file.py", Path("c:/cursor/TappsCodingAgents"))
        'src/file.py'
        
        >>> normalize_path("c:/other/project/file.py", Path("c:/cursor/TappsCodingAgents"))
        'c:/other/project/file.py'  # Outside project root, return as-is
    """
    path_obj = Path(path) if isinstance(path, str) else path
    project_root_obj = Path(project_root).resolve()
    
    # Handle empty or None paths
    if not path_obj or str(path_obj).strip() == "":
        return ""
    
    # Resolve absolute paths
    if path_obj.is_absolute():
        try:
            # Resolve both paths to handle symlinks and relative components
            resolved_path = path_obj.resolve()
            resolved_root = project_root_obj.resolve()
            
            # Try to make relative to project root
            if resolved_path.is_relative_to(resolved_root):
                rel_path = resolved_path.relative_to(resolved_root)
                return str(rel_path)
            else:
                # Path is outside project root - return as-is but log warning
                logger.warning(
                    f"Path {resolved_path} is outside project root {resolved_root}. "
                    "Returning absolute path."
                )
                return str(resolved_path)
        except (ValueError, AttributeError) as e:
            # Python < 3.9 doesn't have is_relative_to, or other error
            try:
                rel_path = path_obj.resolve().relative_to(project_root_obj.resolve())
                return str(rel_path)
            except ValueError:
                # Path is outside project root
                logger.warning(
                    f"Path {path_obj} could not be made relative to {project_root_obj}: {e}"
                )
                return str(path_obj.resolve())
    
    # Already relative - return as-is
    return str(path_obj)


def ensure_relative_path(path: str | Path, project_root: Path) -> str:
    """
    Ensure path is relative to project root, raising error if outside.
    
    Args:
        path: Path to normalize
        project_root: Project root directory
        
    Returns:
        Relative path string
        
    Raises:
        ValueError: If path is outside project root
        
    Examples:
        >>> ensure_relative_path("src/file.py", Path("c:/cursor/TappsCodingAgents"))
        'src/file.py'
        
        >>> ensure_relative_path("c:/other/file.py", Path("c:/cursor/TappsCodingAgents"))
        ValueError: Path is outside project root
    """
    normalized = normalize_path(path, project_root)
    path_obj = Path(normalized)
    Path(project_root).resolve()
    
    # Check if still absolute (means it's outside project root)
    if path_obj.is_absolute():
        raise ValueError(
            f"Path {path} is outside project root {project_root}. "
            "Use relative paths or paths within the project directory."
        )
    
    return normalized


def normalize_for_cli(path: str | Path, project_root: Path) -> str:
    """
    Normalize path for CLI command execution (most permissive).
    
    Similar to normalize_path but handles more edge cases and provides
    CLI-safe formatting (forward slashes on Windows for compatibility).
    
    Args:
        path: Path to normalize
        project_root: Project root directory
        
    Returns:
        CLI-safe path string (uses forward slashes on all platforms)
        
    Examples:
        >>> normalize_for_cli("c:\\cursor\\TappsCodingAgents\\src\\file.py", Path("c:/cursor/TappsCodingAgents"))
        'src/file.py'
    """
    normalized = normalize_path(path, project_root)
    
    # Use forward slashes for CLI compatibility (works on Windows too)
    # This is especially important for subprocess calls
    return normalized.replace("\\", "/") if sys.platform == "win32" else normalized


def normalize_project_root(project_root: str | Path) -> Path:
    """
    Normalize project root path for consistent handling.
    
    Resolves absolute paths and ensures consistent format across platforms.
    
    Args:
        project_root: Project root path (can be absolute or relative)
        
    Returns:
        Resolved Path object
        
    Examples:
        >>> normalize_project_root("c:/cursor/TappsCodingAgents")
        Path('c:/cursor/TappsCodingAgents')
        
        >>> normalize_project_root(".")
        Path('/current/working/directory')
    """
    root_path = Path(project_root) if isinstance(project_root, str) else project_root
    
    # If relative, resolve to absolute
    if not root_path.is_absolute():
        root_path = root_path.resolve()
    
    return root_path
