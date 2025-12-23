"""
Debugger agent command handlers
"""
import asyncio

from ...agents.debugger.agent import DebuggerAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_debugger_command(args: object) -> None:
    """Handle debugger agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("debugger")
        feedback.output_result(help_text)
        return
    
    # Only activate for commands that need it
    debugger = DebuggerAgent()
    try:
        asyncio.run(debugger.activate())
        if command == "debug":
            result = asyncio.run(
                debugger.run(
                    "debug",
                    error_message=args.error_message,
                    file=getattr(args, "file", None),
                    line=getattr(args, "line", None),
                    stack_trace=getattr(args, "stack_trace", None),
                )
            )
        elif command == "analyze-error":
            result = asyncio.run(
                debugger.run(
                    "analyze-error",
                    error_message=args.error_message,
                    stack_trace=getattr(args, "stack_trace", None),
                    code_context=getattr(args, "code_context", None),
                )
            )
        elif command == "trace":
            result = asyncio.run(
                debugger.run(
                    "trace",
                    file=args.file,
                    function=getattr(args, "function", None),
                    line=getattr(args, "line", None),
                )
            )
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("debugger")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        feedback.output_result(result, message="Debugging completed successfully")
    finally:
        safe_close_agent_sync(debugger)

