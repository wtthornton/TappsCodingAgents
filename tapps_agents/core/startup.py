"""
Startup routines for TappsCodingAgents.

Handles automatic documentation refresh and other startup tasks.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

from ..context7.commands import Context7Commands
from ..core.config import ProjectConfig, load_config


async def refresh_stale_documentation(
    config: ProjectConfig | None = None,
    background: bool = True,
    max_refresh: int = 10,
) -> dict[str, Any]:
    """
    Refresh stale documentation entries on startup.

    Args:
        config: Optional ProjectConfig (loads if not provided)
        background: If True, runs in background without blocking
        max_refresh: Maximum number of entries to refresh synchronously

    Returns:
        Dictionary with refresh results
    """
    if config is None:
        config = load_config()

    # Check if Context7 is enabled
    if not config.context7 or not config.context7.enabled:
        return {"success": False, "message": "Context7 is not enabled", "refreshed": 0}

    try:
        # Initialize Context7 commands
        project_root = Path.cwd()
        context7_commands = Context7Commands(project_root=project_root, config=config)

        # Check for stale entries and queue them (refresh with no args queues all stale)
        queue_result = await context7_commands.cmd_refresh()

        if not queue_result.get("success"):
            return {
                "success": False,
                "message": f"Failed to queue stale entries: {queue_result.get('error', 'Unknown error')}",
                "refreshed": 0,
            }

        entries_queued = queue_result.get("entries_queued", 0)

        if entries_queued == 0:
            return {
                "success": True,
                "message": "No stale entries found",
                "refreshed": 0,
                "queued": 0,
            }

        # Process refresh queue
        if background:
            # Run in background - don't block startup
            asyncio.create_task(
                _process_refresh_queue_background(context7_commands, max_refresh)
            )
            return {
                "success": True,
                "message": f"Queued {entries_queued} entries for background refresh",
                "queued": entries_queued,
                "background": True,
            }
        else:
            # Process synchronously (limited)
            refreshed = await _process_refresh_queue_sync(
                context7_commands, max_refresh
            )
            return {
                "success": True,
                "message": f"Refreshed {refreshed} entries on startup",
                "refreshed": refreshed,
                "queued": entries_queued,
                "background": False,
            }

    except Exception as e:
        # Don't fail startup if refresh fails
        return {
            "success": False,
            "message": f"Startup refresh failed: {str(e)}",
            "refreshed": 0,
            "error": str(e),
        }


async def _process_refresh_queue_background(
    context7_commands: Context7Commands, max_refresh: int = 10
):
    """Process refresh queue in background."""
    try:
        # Process a limited number of entries in background
        result = await context7_commands.cmd_refresh_process(max_items=max_refresh)
        if result.get("success"):
            refreshed = result.get("items_processed", 0)
            if refreshed > 0:
                print(
                    f"[Startup] Refreshed {refreshed} documentation entries in background",
                    file=sys.stderr,
                )
    except Exception:
        # Silently fail in background
        pass


async def _process_refresh_queue_sync(
    context7_commands: Context7Commands, max_refresh: int = 10
) -> int:
    """Process refresh queue synchronously (limited)."""
    try:
        result = await context7_commands.cmd_refresh_process(max_items=max_refresh)
        if result.get("success"):
            return result.get("items_processed", 0)
        return 0
    except Exception:
        return 0


async def startup_routines(
    config: ProjectConfig | None = None,
    refresh_docs: bool = True,
    background_refresh: bool = True,
) -> dict[str, Any]:
    """
    Run all startup routines.

    Args:
        config: Optional ProjectConfig (loads if not provided)
        refresh_docs: Whether to refresh stale documentation
        background_refresh: Whether to refresh in background

    Returns:
        Dictionary with startup results
    """
    routines: dict[str, Any] = {}
    results: dict[str, Any] = {"success": True, "routines": routines}

    if refresh_docs:
        refresh_result = await refresh_stale_documentation(
            config=config, background=background_refresh
        )
        routines["documentation_refresh"] = refresh_result

    return results
