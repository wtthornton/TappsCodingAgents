"""
Improver agent command handlers
"""
import asyncio

from ...agents.improver.agent import ImproverAgent
from ..base import normalize_command
from .common import check_result_error, format_json_output


def handle_improver_command(args: object) -> None:
    """Handle improver agent commands"""
    command = normalize_command(getattr(args, "command", None))
    improver = ImproverAgent()
    asyncio.run(improver.activate())

    try:
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
            result = asyncio.run(
                improver.run("improve-quality", file_path=args.file_path)
            )
        elif command == "help" or command is None:
            result = asyncio.run(improver.run("help"))
            print(result["content"] if isinstance(result, dict) else result)
            return
        else:
            result = asyncio.run(improver.run("help"))
            print(result["content"] if isinstance(result, dict) else result)
            return

        check_result_error(result)
        format_json_output(result)
    finally:
        asyncio.run(improver.close())

