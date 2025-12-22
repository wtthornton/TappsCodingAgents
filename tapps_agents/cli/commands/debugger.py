"""
Debugger agent command handlers
"""
import asyncio

from ...agents.debugger.agent import DebuggerAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_debugger_command(args: object) -> None:
    """Handle debugger agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    debugger = DebuggerAgent()
    asyncio.run(debugger.activate())
    try:
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
        elif command == "help" or command is None:
            result = asyncio.run(debugger.run("help"))
            feedback.output_result(result["content"])
            return
        else:
            result = asyncio.run(debugger.run("help"))
            feedback.output_result(result["content"])
            return

        check_result_error(result)
        feedback.output_result(result, message="Debugging completed successfully")
    finally:
        safe_close_agent_sync(debugger)

