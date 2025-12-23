"""
Documenter agent command handlers
"""
import asyncio

from ...agents.documenter.agent import DocumenterAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_documenter_command(args: object) -> None:
    """Handle documenter agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("documenter")
        feedback.output_result(help_text)
        return
    
    # Only activate for commands that need it
    documenter = DocumenterAgent()
    try:
        asyncio.run(documenter.activate())
        if command == "document":
            result = asyncio.run(
                documenter.run(
                    "document",
                    file=args.file,
                    output_format=getattr(args, "output_format", "markdown"),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command == "generate-docs":
            result = asyncio.run(
                documenter.run(
                    "generate-docs",
                    file=args.file,
                    output_format=getattr(args, "output_format", "markdown"),
                )
            )
        elif command == "update-readme":
            result = asyncio.run(
                documenter.run(
                    "update-readme",
                    project_root=getattr(args, "project_root", None),
                    context=getattr(args, "context", None),
                )
            )
        elif command == "update-docstrings":
            result = asyncio.run(
                documenter.run(
                    "update-docstrings",
                    file=args.file,
                    docstring_format=getattr(args, "docstring_format", None),
                    write_file=getattr(args, "write_file", False),
                )
            )
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("documenter")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        feedback.output_result(result, message="Documentation completed successfully")
    finally:
        safe_close_agent_sync(documenter)

