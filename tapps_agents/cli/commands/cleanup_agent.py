"""
Cleanup Agent command handlers
"""
import asyncio

from ...agents.cleanup.agent import CleanupAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error


def handle_cleanup_agent_command(args: object) -> None:
    """Handle cleanup-agent commands."""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format

    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("cleanup-agent")
        feedback.output_result(help_text)
        return

    # Cleanup agent runs offline (no network needed for file operations)
    offline_mode = True

    # Create and activate agent
    cleanup = CleanupAgent()
    try:
        asyncio.run(cleanup.activate(offline_mode=offline_mode))

        if command == "analyze":
            result = asyncio.run(
                cleanup.run(
                    "analyze",
                    path=getattr(args, "path", None),
                    pattern=getattr(args, "pattern", "*.md"),
                    output=getattr(args, "output", None),
                )
            )
        elif command == "plan":
            result = asyncio.run(
                cleanup.run(
                    "plan",
                    analysis_file=getattr(args, "analysis_file", None),
                    path=getattr(args, "path", None),
                    pattern=getattr(args, "pattern", "*.md"),
                    output=getattr(args, "output", None),
                )
            )
        elif command == "execute":
            # Handle dry-run flag (--no-dry-run disables dry-run)
            dry_run = not getattr(args, "no_dry_run", False)
            backup = not getattr(args, "no_backup", False)

            result = asyncio.run(
                cleanup.run(
                    "execute",
                    plan_file=getattr(args, "plan_file", None),
                    path=getattr(args, "path", None),
                    pattern=getattr(args, "pattern", "*.md"),
                    dry_run=dry_run,
                    backup=backup,
                )
            )
        elif command == "run":
            # Handle dry-run flag (--no-dry-run disables dry-run)
            dry_run = not getattr(args, "no_dry_run", False)
            backup = not getattr(args, "no_backup", False)

            result = asyncio.run(
                cleanup.run(
                    "run",
                    path=getattr(args, "path", None),
                    pattern=getattr(args, "pattern", "*.md"),
                    dry_run=dry_run,
                    backup=backup,
                )
            )
        else:
            # Invalid command - show help
            help_text = get_static_help("cleanup-agent")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        feedback.output_result(result, message="Cleanup operation completed successfully")
    finally:
        safe_close_agent_sync(cleanup)
