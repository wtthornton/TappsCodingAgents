"""
Tester agent command handlers
"""
import asyncio

from ...agents.tester.agent import TesterAgent
from ..base import normalize_command
from ..feedback import get_feedback
from .common import check_result_error, format_json_output


def handle_tester_command(args: object) -> None:
    """Handle tester agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    tester = TesterAgent()
    asyncio.run(tester.activate())
    try:
        if command == "test":
            feedback.start_operation("Test")
            feedback.info(f"Running tests for {args.file}...")
            result = asyncio.run(
                tester.run(
                    "test",
                    file=args.file,
                    test_file=getattr(args, "test_file", None),
                    integration=getattr(args, "integration", False),
                )
            )
            check_result_error(result)
            feedback.clear_progress()
            feedback.output_result(result, message="Tests completed")
        elif command == "generate-tests":
            feedback.start_operation("Generate Tests")
            feedback.info(f"Generating tests for {args.file}...")
            result = asyncio.run(
                tester.run(
                    "generate-tests",
                    file=args.file,
                    test_file=getattr(args, "test_file", None),
                    integration=getattr(args, "integration", False),
                )
            )
            check_result_error(result)
            feedback.clear_progress()
            feedback.output_result(result, message="Tests generated successfully")
        elif command == "run-tests":
            feedback.start_operation("Run Tests")
            feedback.info("Running test suite...")
            result = asyncio.run(
                tester.run(
                    "run-tests",
                    test_path=getattr(args, "test_path", None),
                    coverage=not getattr(args, "no_coverage", False),
                )
            )
            check_result_error(result)
            feedback.clear_progress()
            feedback.output_result(result, message="Test suite completed")
        elif command == "help" or command is None:
            result = asyncio.run(tester.run("help"))
            feedback.output_result(result["content"])
            return
        else:
            result = asyncio.run(tester.run("help"))
            feedback.output_result(result["content"])
            return

        check_result_error(result)
        format_json_output(result)
    finally:
        asyncio.run(tester.close())

