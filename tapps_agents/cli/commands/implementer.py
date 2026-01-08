"""
Implementer agent command handlers
"""
import asyncio

from ...agents.implementer.agent import ImplementerAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from .common import check_result_error, format_json_output


async def implement_command(
    specification: str,
    file_path: str,
    context: str | None = None,
    language: str = "python",
    output_format: str = "json",
):
    """Generate and write code to file (with review)"""
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    from ...core.network_errors import NetworkRequiredError
    from ..base import handle_network_error
    from ..feedback import suggest_simple_mode
    
    # Suggest using @simple-mode for better outcomes
    suggest_simple_mode("implement", description=specification[:50], file_path=file_path)
    
    feedback = get_feedback()
    feedback.format_type = output_format
    
    # Check network requirement - implement requires network
    requirement = CommandClassifier.get_network_requirement("implementer", "implement")
    if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
        try:
            raise NetworkRequiredError(
                operation_name="implementer implement",
                message="Network is required for this command"
            )
        except NetworkRequiredError as e:
            handle_network_error(e, format_type=output_format)
            return
    
    spec_preview = specification[:50] + "..." if len(specification) > 50 else specification
    feedback.start_operation("Code Implementation", f"Implementing: {spec_preview} in {file_path}")
    feedback.running("Analyzing specification...", step=1, total_steps=4)
    
    implementer = ImplementerAgent()
    try:
        await implementer.activate(offline_mode=False)
        feedback.running("Generating code structure...", step=2, total_steps=4)
        result = await implementer.run(
            "implement",
            specification=specification,
            file_path=file_path,
            context=context,
            language=language,
        )
        feedback.running("Reviewing code quality...", step=3, total_steps=4)
        feedback.running("Preparing implementation...", step=4, total_steps=4)

        check_result_error(result)
        feedback.clear_progress()

        # Note: Implementer returns instructions for Cursor Skills execution
        # The actual code generation happens via Cursor Skills, not directly in CLI
        summary = {}
        if isinstance(result, dict):
            if "file" in result:
                summary["target_file"] = result["file"]
            if "file_existed" in result:
                summary["file_existed"] = result["file_existed"]
            if "instruction" in result:
                summary["instruction_prepared"] = True
            
            # Merge summary into result
            if summary:
                result = {**result, "summary": summary}
        
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
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    from ...core.network_errors import NetworkRequiredError
    from ..base import handle_network_error
    
    feedback = get_feedback()
    feedback.format_type = output_format
    
    # Check network requirement - generate-code requires network
    requirement = CommandClassifier.get_network_requirement("implementer", "generate-code")
    if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
        try:
            raise NetworkRequiredError(
                operation_name="implementer generate-code",
                message="Network is required for this command"
            )
        except NetworkRequiredError as e:
            handle_network_error(e, format_type=output_format)
            return
    
    spec_preview = specification[:50] + "..." if len(specification) > 50 else specification
    target_desc = f" for {file_path}" if file_path else ""
    feedback.start_operation("Code Generation", f"Generating code{target_desc}: {spec_preview}")
    feedback.running("Analyzing specification...", step=1, total_steps=3)
    
    implementer = ImplementerAgent()
    try:
        await implementer.activate(offline_mode=False)
        feedback.running("Generating code...", step=2, total_steps=3)
        result = await implementer.run(
            "generate-code",
            specification=specification,
            file_path=file_path,
            context=context,
            language=language,
        )
        feedback.running("Preparing code output...", step=3, total_steps=3)

        check_result_error(result)
        feedback.clear_progress()

        summary = {}
        if isinstance(result, dict):
            if "file" in result:
                summary["target_file"] = result["file"]
            if "instruction" in result:
                summary["instruction_prepared"] = True
            
            # Merge summary into result
            if summary:
                result = {**result, "summary": summary}

        if output_format == "json":
            feedback.output_result(result, message="Code generation instruction prepared")
            # Add note about instruction-based execution
            if "instruction" in result:
                feedback.warning(
                    "⚠️  Note: This command returns an instruction object.\n"
                    "   To see actual generated code, use @implementer in Cursor IDE."
                )
        else:
            feedback.success("Code generation instruction prepared")
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
    from ..feedback import get_feedback, suggest_simple_mode
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    from ...core.network_errors import NetworkRequiredError
    from ..base import handle_network_error
    
    # Suggest using @simple-mode for better outcomes
    suggest_simple_mode("refactor", description=instruction[:50], file_path=file_path)
    
    feedback = get_feedback()
    feedback.format_type = output_format
    
    # Check network requirement - refactor requires network
    requirement = CommandClassifier.get_network_requirement("implementer", "refactor")
    if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
        try:
            raise NetworkRequiredError(
                operation_name="implementer refactor",
                message="Network is required for this command"
            )
        except NetworkRequiredError as e:
            handle_network_error(e, format_type=output_format)
            return
    inst_preview = instruction[:50] + "..." if len(instruction) > 50 else instruction
    feedback.start_operation("Code Refactoring", f"Refactoring {file_path}: {inst_preview}")
    feedback.running("Analyzing source file...", step=1, total_steps=3)
    
    implementer = ImplementerAgent()
    try:
        await implementer.activate(offline_mode=False)
        feedback.running("Applying refactoring...", step=2, total_steps=3)
        result = await implementer.run(
            "refactor", file_path=file_path, instruction=instruction
        )
        feedback.running("Preparing refactored code...", step=3, total_steps=3)

        check_result_error(result)
        feedback.clear_progress()

        summary = {}
        if isinstance(result, dict):
            if "file" in result:
                summary["source_file"] = result["file"]
            if "instruction" in result:
                summary["instruction_prepared"] = True
            
            # Merge summary into result
            if summary:
                result = {**result, "summary": summary}

        # Use output handler utility for consistent output
        if output_file or output_format != "json":
            write_output(result, output_file=output_file, format_type=output_format, default_format="json")
        else:
            feedback.output_result(result, message="Refactoring instruction prepared")
            
        # Note: Actual file writing with refactored code would happen here
        # Currently, refactor returns instructions, not actual refactored code
        # File writing would need actual code generation to be implemented
    finally:
        await implementer.close()


def handle_implementer_command(args: object) -> None:
    """Handle implementer agent commands"""
    command = normalize_command(getattr(args, "command", None))
    feedback = get_feedback()
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("implementer")
        feedback.output_result(help_text)
        return
    
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
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("implementer")
            feedback.output_result(help_text)
    finally:
        from ..utils.agent_lifecycle import safe_close_agent_sync
        safe_close_agent_sync(implementer)

