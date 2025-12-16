"""
Architect agent command handlers
"""
import asyncio

from ...agents.architect.agent import ArchitectAgent
from ..base import normalize_command
from .common import check_result_error, format_json_output


def handle_architect_command(args: object) -> None:
    """Handle architect agent commands"""
    command = normalize_command(getattr(args, "command", None))
    architect = ArchitectAgent()
    asyncio.run(architect.activate())
    try:
        if command == "design-system":
            result = asyncio.run(
                architect.run(
                    "design-system",
                    requirements=args.requirements,
                    context=getattr(args, "context", ""),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "architecture-diagram":
            result = asyncio.run(
                architect.run(
                    "create-diagram",
                    architecture_description=args.architecture_description,
                    diagram_type=getattr(args, "diagram_type", "component"),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "tech-selection":
            result = asyncio.run(
                architect.run(
                    "select-technology",
                    component_description=args.component_description,
                    requirements=getattr(args, "requirements", ""),
                    constraints=getattr(args, "constraints", []),
                )
            )
        elif command == "design-security":
            result = asyncio.run(
                architect.run(
                    "design-security",
                    system_description=args.system_description,
                    threat_model=getattr(args, "threat_model", ""),
                )
            )
        elif command == "define-boundaries":
            result = asyncio.run(
                architect.run(
                    "define-boundaries",
                    system_description=args.system_description,
                    context=getattr(args, "context", ""),
                )
            )
        elif command == "help" or command is None:
            result = asyncio.run(architect.run("help"))
            print(result["content"])
            return
        else:
            result = asyncio.run(architect.run("help"))
            print(result["content"])
            return

        check_result_error(result)
        format_json_output(result)
    finally:
        asyncio.run(architect.close())

