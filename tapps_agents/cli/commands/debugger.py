"""
Debugger agent command handlers
"""
import asyncio

from ...agents.debugger.agent import DebuggerAgent
from ..base import normalize_command
from .common import check_result_error, format_json_output


def handle_debugger_command(args: object) -> None:
    """Handle debugger agent commands"""
    command = normalize_command(getattr(args, "command", None))
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
            print(result["content"])
            return
        else:
            result = asyncio.run(debugger.run("help"))
            print(result["content"])
            return

        check_result_error(result)
        format_json_output(result)
    finally:
        asyncio.run(debugger.close())

