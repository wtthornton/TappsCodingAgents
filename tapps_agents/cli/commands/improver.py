"""
Improver agent command handlers
"""
import asyncio

from ...agents.improver.agent import ImproverAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_improver_command(args: object) -> None:
    """Handle improver agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("improver")
        feedback.output_result(help_text)
        return
    
    # Only activate for commands that need it
    improver = ImproverAgent()
    try:
        asyncio.run(improver.activate())
        if command == "refactor":
            result = asyncio.run(
                improver.run(
                    "refactor",
                    file_path=args.file_path,
                    instruction=getattr(args, "instruction", None),
                )
            )
        elif command == "optimize":
            result = asyncio.run(
                improver.run(
                    "optimize",
                    file_path=args.file_path,
                    optimization_type=getattr(args, "type", "performance"),
                )
            )
        elif command == "improve-quality":
            focus = getattr(args, "focus", None)
            result = asyncio.run(
                improver.run("improve-quality", file_path=args.file_path, focus=focus)
            )
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("improver")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        feedback.output_result(result, message="Improvement completed successfully")
    finally:
        safe_close_agent_sync(improver)

