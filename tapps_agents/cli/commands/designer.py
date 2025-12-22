"""
Designer agent command handlers
"""
import asyncio

from ...agents.designer.agent import DesignerAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_designer_command(args: object) -> None:
    """Handle designer agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    designer = DesignerAgent()
    asyncio.run(designer.activate())
    try:
        if command == "design-api":
            result = asyncio.run(
                designer.run(
                    "design-api",
                    requirements=args.requirements,
                    api_type=getattr(args, "api_type", "REST"),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command == "design-data-model":
            result = asyncio.run(
                designer.run(
                    "design-data-model",
                    requirements=args.requirements,
                    data_source=getattr(args, "data_source", ""),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command == "design-ui":
            result = asyncio.run(
                designer.run(
                    "design-ui",
                    feature_description=args.feature_description,
                    user_stories=getattr(args, "user_stories", []),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command == "create-wireframe":
            result = asyncio.run(
                designer.run(
                    "create-wireframe",
                    screen_description=args.screen_description,
                    wireframe_type=getattr(args, "wireframe_type", "page"),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command == "define-design-system":
            result = asyncio.run(
                designer.run(
                    "define-design-system",
                    project_description=args.project_description,
                    brand_guidelines=getattr(args, "brand_guidelines", ""),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command == "help" or command is None:
            result = asyncio.run(designer.run("help"))
            feedback.output_result(result["content"])
            return
        else:
            result = asyncio.run(designer.run("help"))
            feedback.output_result(result["content"])
            return

        check_result_error(result)
        feedback.output_result(result, message="Design completed successfully")
    finally:
        safe_close_agent_sync(designer)

