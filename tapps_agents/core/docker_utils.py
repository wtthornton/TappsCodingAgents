"""
Docker utility functions for safe command execution.

This module provides utilities for executing Docker commands safely,
especially on Windows/PowerShell where certain command formats can cause issues.

Issue 7: Docker ps Command - Agent Crash with Table Format
- Problem: `docker ps --format "table {{.Names}}\t{{.Status}}" | Select-Object -First 35` crashes
- Root Cause: Table format header breaks Select-Object parsing, tab characters not handled properly
- Solution: Use JSON format or simple format instead
"""

import json
import subprocess
from typing import Any


def run_docker_ps_json(limit: int | None = None) -> list[dict[str, Any]]:
    """
    Run `docker ps` using JSON format (most reliable for PowerShell).
    
    This is the recommended method for checking container status as it:
    - Works reliably on Windows/PowerShell
    - Provides structured data that's easy to parse
    - Avoids table format parsing issues
    
    Args:
        limit: Maximum number of containers to return (None = all)
    
    Returns:
        List of container dictionaries with keys: Names, Status, ID, Image, etc.
    
    Example:
        >>> containers = run_docker_ps_json(limit=35)
        >>> for container in containers:
        ...     print(f"{container['Names']}: {container['Status']}")
    """
    try:
        # Use JSON format - most reliable for PowerShell
        result = subprocess.run(  # nosec B603
            ["docker", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        
        if result.returncode != 0:
            # Docker not available or error
            return []
        
        # Parse JSON lines (one JSON object per line)
        containers = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                container = json.loads(line)
                containers.append(container)
            except json.JSONDecodeError:
                # Skip invalid JSON lines
                continue
        
        # Apply limit if specified
        if limit is not None:
            containers = containers[:limit]
        
        return containers
    
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Docker not installed or command failed
        return []


def run_docker_ps_simple(limit: int | None = None) -> list[dict[str, str]]:
    """
    Run `docker ps` using simple format (no table header).
    
    This method uses a simple format without table headers, which works
    better with PowerShell piping than table format.
    
    Args:
        limit: Maximum number of containers to return (None = all)
    
    Returns:
        List of dictionaries with 'Names' and 'Status' keys
    
    Example:
        >>> containers = run_docker_ps_simple(limit=35)
        >>> for container in containers:
        ...     print(f"{container['Names']}: {container['Status']}")
    """
    try:
        # Use simple format without table header
        # Note: Using backtick for tab in PowerShell, but we'll parse it ourselves
        result = subprocess.run(  # nosec B603
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        
        if result.returncode != 0:
            return []
        
        # Parse tab-separated output
        containers = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                containers.append({
                    "Names": parts[0].strip(),
                    "Status": parts[1].strip(),
                })
        
        # Apply limit if specified
        if limit is not None:
            containers = containers[:limit]
        
        return containers
    
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return []


def run_docker_ps_native(limit: int | None = None) -> str:
    """
    Run `docker ps` with native output (no formatting).
    
    This returns the raw Docker output, which can be useful for display
    but is harder to parse programmatically.
    
    Args:
        limit: Maximum number of lines to return (None = all)
    
    Returns:
        Raw Docker output as string
    
    Example:
        >>> output = run_docker_ps_native()
        >>> print(output)
    """
    try:
        result = subprocess.run(  # nosec B603
            ["docker", "ps"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        
        if result.returncode != 0:
            return ""
        
        output = result.stdout.strip()
        
        # Apply limit if specified (count lines)
        if limit is not None:
            lines = output.split("\n")
            output = "\n".join(lines[:limit])
        
        return output
    
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return ""


def get_container_status(container_name: str | None = None) -> dict[str, Any]:
    """
    Get status of a specific container or all containers.
    
    Args:
        container_name: Name of container to check (None = all containers)
    
    Returns:
        Dictionary with container status information
    
    Example:
        >>> status = get_container_status("my-container")
        >>> print(status['running'])
    """
    containers = run_docker_ps_json()
    
    if container_name is None:
        return {
            "total": len(containers),
            "containers": containers,
        }
    
    # Find specific container
    for container in containers:
        # Container names can have leading slash in Docker output
        names = container.get("Names", "").lstrip("/")
        if container_name in names or names == container_name:
            return {
                "found": True,
                "container": container,
                "running": container.get("State", "").lower() == "running",
            }
    
    return {
        "found": False,
        "container": None,
        "running": False,
    }


# Recommended usage examples for PowerShell scripts:
#
# ❌ AVOID (causes crashes):
#   docker ps --format "table {{.Names}}\t{{.Status}}" | Select-Object -First 35
#
# ✅ USE INSTEAD (Option 1 - JSON format, most reliable):
#   docker ps --format json | ConvertFrom-Json | Select-Object -First 35 | Format-Table Name, Status
#
# ✅ USE INSTEAD (Option 2 - Simple format):
#   docker ps --format "{{.Names}}\t{{.Status}}" | Select-Object -First 35
#
# ✅ USE INSTEAD (Option 3 - Native output):
#   docker ps | Select-Object -First 35
#
# ✅ USE INSTEAD (Option 4 - Python utility):
#   from tapps_agents.core.docker_utils import run_docker_ps_json
#   containers = run_docker_ps_json(limit=35)
#   for container in containers:
#       print(f"{container['Names']}: {container['Status']}")

