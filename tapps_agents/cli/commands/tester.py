"""
Tester agent command handlers
"""
import asyncio

from ...agents.tester.agent import TesterAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_tester_command(args: object) -> None:
    """Handle tester agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("tester")
        feedback.output_result(help_text)
        return
    
    # Only activate for commands that need it
    tester = TesterAgent()
    try:
        asyncio.run(tester.activate())
        if command == "test":
            feedback.start_operation("Test Generation", f"Generating tests for {args.file}...")
            feedback.running("Analyzing source file...", step=1, total_steps=3)
            result = asyncio.run(
                tester.run(
                    "test",
                    file=args.file,
                    test_file=getattr(args, "test_file", None),
                    integration=getattr(args, "integration", False),
                    focus=getattr(args, "focus", None),
                )
            )
            check_result_error(result)
            feedback.running("Generating test code...", step=2, total_steps=3)
            feedback.running("Preparing test file...", step=3, total_steps=3)
            feedback.clear_progress()
            
            # Note: Tester returns instructions for Cursor Skills execution
            # Check if test file was actually created
            test_file_path = result.get("test_file")
            summary = {}
            if test_file_path:
                from pathlib import Path
                test_path = Path(test_file_path)
                if test_path.exists() and test_path.stat().st_size > 0:
                    summary["test_file"] = test_file_path
                    summary["file_created"] = True
                    feedback.output_result(result, message="Tests generated and file created successfully", summary=summary)
                else:
                    summary["test_file"] = test_file_path
                    summary["file_created"] = False
                    feedback.output_result(result, message="Test generation instruction prepared", summary=summary)
                    feedback.info(
                        f"Note: Test file not yet created at {test_file_path}. "
                        "This command returns an instruction for Cursor Skills execution. "
                        "To execute, use the skill_command in Cursor or use @tester in Cursor chat."
                    )
            else:
                feedback.output_result(result, message="Test generation instruction prepared", summary=summary)
                feedback.info(
                    "Note: This command returns an instruction for Cursor Skills execution. "
                    "To execute, use the skill_command in Cursor or use @tester in Cursor chat."
                )
        elif command == "generate-tests":
            feedback.start_operation("Generate Tests", f"Generating tests for {args.file}...")
            feedback.running("Analyzing source file...", step=1, total_steps=3)
            result = asyncio.run(
                tester.run(
                    "generate-tests",
                    file=args.file,
                    test_file=getattr(args, "test_file", None),
                    integration=getattr(args, "integration", False),
                )
            )
            check_result_error(result)
            feedback.running("Generating test code...", step=2, total_steps=3)
            feedback.running("Preparing test file...", step=3, total_steps=3)
            feedback.clear_progress()
            
            summary = {}
            test_file_path = result.get("test_file")
            if test_file_path:
                summary["test_file"] = test_file_path
            feedback.output_result(result, message="Tests generated successfully", summary=summary)
        elif command == "run-tests":
            test_path = getattr(args, "test_path", None)
            operation_desc = f"Running test suite{f' in {test_path}' if test_path else ''}..."
            feedback.start_operation("Run Tests", operation_desc)
            feedback.running("Discovering test files...", step=1, total_steps=3)
            result = asyncio.run(
                tester.run(
                    "run-tests",
                    test_path=test_path,
                    coverage=not getattr(args, "no_coverage", False),
                )
            )
            check_result_error(result)
            feedback.running("Executing tests...", step=2, total_steps=3)
            feedback.running("Collecting results...", step=3, total_steps=3)
            feedback.clear_progress()
            
            summary = {}
            if isinstance(result, dict):
                if "tests_run" in result:
                    summary["tests_run"] = result["tests_run"]
                if "tests_passed" in result:
                    summary["tests_passed"] = result["tests_passed"]
                if "tests_failed" in result:
                    summary["tests_failed"] = result["tests_failed"]
                if "coverage" in result:
                    summary["coverage"] = result["coverage"]
            feedback.output_result(result, message="Test suite completed", summary=summary)
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("tester")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        format_json_output(result)
    finally:
        safe_close_agent_sync(tester)

