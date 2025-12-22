"""
Implementer agent command handlers
"""
import asyncio

from ...agents.implementer.agent import ImplementerAgent
from ..base import normalize_command
from ..feedback import get_feedback
from .common import check_result_error, format_json_output


async def implement_command(
    specification: str,
    file_path: str,
    context: str | None = None,
    language: str = "python",
    output_format: str = "json",
):
    """Generate and write code to file (with review)"""
    feedback = get_feedback()
    feedback.format_type = output_format
    feedback.start_operation("Implement")
    feedback.info(f"Implementing code in {file_path}...")
    
    implementer = ImplementerAgent()
    try:
        await implementer.activate()
        result = await implementer.run(
            "implement",
            specification=specification,
            file_path=file_path,
            context=context,
            language=language,
        )

        check_result_error(result)
        feedback.clear_progress()

        if output_format == "json":
            feedback.output_result(result, message="Code implemented successfully")
        else:
            feedback.success("Code implemented successfully")
            print(f"\nCode implemented: {result['file']}")
            print(f"Approved: {result['approved']}")
            if result.get("backup"):
                print(f"Backup created: {result['backup']}")
    finally:
        await implementer.close()


async def generate_code_command(
    specification: str,
    file_path: str | None = None,
    context: str | None = None,
    language: str = "python",
    output_format: str = "json",
):
    """Generate code from specification (no file write)"""
    implementer = ImplementerAgent()
    try:
        await implementer.activate()
        result = await implementer.run(
            "generate-code",
            specification=specification,
            file_path=file_path,
            context=context,
            language=language,
        )

        check_result_error(result)

        if output_format == "json":
            format_json_output(result)
        else:
            print("Generated Code:")
            print("-" * 40)
            print(result["code"])
    finally:
        await implementer.close()


async def refactor_command(
    file_path: str, instruction: str, output_format: str = "json", output_file: str | None = None
):
    """Refactor existing code file"""
    from ..utils.output_handler import write_output
    
    implementer = ImplementerAgent()
    try:
        await implementer.activate()
        result = await implementer.run(
            "refactor", file_path=file_path, instruction=instruction
        )

        check_result_error(result)

        # Use output handler utility for consistent output
        if output_file or output_format != "json":
            write_output(result, output_file=output_file, format_type=output_format, default_format="json")
        else:
            format_json_output(result)
            
        # Note: Actual file writing with refactored code would happen here
        # Currently, refactor returns instructions, not actual refactored code
        # File writing would need actual code generation to be implemented
    finally:
        await implementer.close()


def handle_implementer_command(args: object) -> None:
    """Handle implementer agent commands"""
    command = normalize_command(getattr(args, "command", None))
    implementer = ImplementerAgent()
    
    try:
        if command == "implement":
            asyncio.run(
                implement_command(
                    args.specification,
                    args.file_path,
                    context=getattr(args, "context", None),
                    language=getattr(args, "language", "python"),
                    output_format=getattr(args, "format", "json"),
                )
            )
        elif command == "generate-code":
            asyncio.run(
                generate_code_command(
                    args.specification,
                    file_path=getattr(args, "file", None),
                    context=getattr(args, "context", None),
                    language=getattr(args, "language", "python"),
                    output_format=getattr(args, "format", "json"),
                )
            )
        elif command == "refactor":
            asyncio.run(
                refactor_command(
                    args.file_path,
                    args.instruction,
                    output_format=getattr(args, "format", "json"),
                    output_file=getattr(args, "output", None),
                )
            )
        elif command == "help" or command is None:
            asyncio.run(implementer.activate())
            result = asyncio.run(implementer.run("help"))
            print(result["content"])
        else:
            asyncio.run(implementer.activate())
            result = asyncio.run(implementer.run("help"))
            print(result["content"])
    finally:
        from ..utils.agent_lifecycle import safe_close_agent_sync
        safe_close_agent_sync(implementer)

