"""
Tester agent command handlers
"""
import asyncio

from ...agents.tester.agent import TesterAgent
from ..base import normalize_command
from .common import check_result_error, format_json_output


def handle_tester_command(args: object) -> None:
    """Handle tester agent commands"""
    command = normalize_command(getattr(args, "command", None))
    tester = TesterAgent()
    asyncio.run(tester.activate())
    try:
        if command == "test":
            result = asyncio.run(
                tester.run(
                    "test",
                    file=args.file,
                    test_file=getattr(args, "test_file", None),
                    integration=getattr(args, "integration", False),
                )
            )
        elif command == "generate-tests":
            result = asyncio.run(
                tester.run(
                    "generate-tests",
                    file=args.file,
                    test_file=getattr(args, "test_file", None),
                    integration=getattr(args, "integration", False),
                )
            )
        elif command == "run-tests":
            result = asyncio.run(
                tester.run(
                    "run-tests",
                    test_path=getattr(args, "test_path", None),
                    coverage=not getattr(args, "no_coverage", False),
                )
            )
        elif command == "help" or command is None:
            result = asyncio.run(tester.run("help"))
            print(result["content"])
            return
        else:
            result = asyncio.run(tester.run("help"))
            print(result["content"])
            return

        check_result_error(result)
        format_json_output(result)
    finally:
        asyncio.run(tester.close())

