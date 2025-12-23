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

        # Note: Implementer returns instructions for Cursor Skills execution
        # The actual code generation happens via Cursor Skills, not directly in CLI
        if output_format == "json":
            feedback.output_result(result, message="Code implementation instruction prepared successfully")
            # Add prominent note about Cursor Skills execution
            if "instruction" in result:
                feedback.warning(
                    "⚠️  IMPORTANT: This command returns an instruction object, not actual code.\n"
                    "   The file will NOT be created by this CLI command.\n"
                    "   To actually generate and write code, use one of these methods:\n"
                    "   1. Use the skill_command in Cursor IDE: @implementer *implement ...\n"
                    "   2. Copy the skill_command from the result and run it in Cursor chat\n"
                    "   3. Use Simple Mode: @simple-mode *build \"your description\""
                )
        else:
            feedback.success("Code implementation instruction prepared successfully")
            print(f"\n{'='*60}")
            print("⚠️  IMPORTANT: This command returns an instruction, not actual code.")
            print("   The file will NOT be created by this CLI command.")
            print(f"{'='*60}")
            print(f"\nInstruction prepared for: {result.get('file', 'N/A')}")
            if "skill_command" in result:
                print(f"\n📋 To execute in Cursor IDE, use:")
                print(f"   {result['skill_command']}")
                print(f"\n   Or use Simple Mode:")
                print(f"   @simple-mode *build \"{specification[:50]}...\"")
            if result.get("file_existed"):
                print(f"\nFile existed: {result['file_existed']}")
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
            # Add note about instruction-based execution
            if "instruction" in result:
                feedback = get_feedback()
                feedback.warning(
                    "⚠️  Note: This command returns an instruction object.\n"
                    "   To see actual generated code, use @implementer in Cursor IDE."
                )
        else:
            print("⚠️  Note: This command returns an instruction object, not actual code.")
            print("   To see generated code, use @implementer in Cursor IDE.")
            if "skill_command" in result:
                print(f"\n   Execute in Cursor: {result['skill_command']}")
            print("\nInstruction Details:")
            print("-" * 40)
            if "instruction" in result:
                print(f"Specification: {result['instruction'].get('specification', 'N/A')[:100]}...")
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

