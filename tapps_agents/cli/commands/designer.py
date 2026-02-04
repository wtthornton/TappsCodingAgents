"""
Designer agent command handlers
"""
import asyncio

from ...agents.designer.agent import DesignerAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error


def handle_designer_command(args: object) -> None:
    """Handle designer agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("designer")
        feedback.output_result(help_text)
        return
    
    # Check network requirement
    from ...core.network_errors import NetworkRequiredError
    from ..base import handle_network_error
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    
    requirement = CommandClassifier.get_network_requirement("designer", command)
    offline_mode = False
    
    if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
        try:
            raise NetworkRequiredError(
                operation_name=f"designer {command}",
                message="Network is required for this command"
            )
        except NetworkRequiredError as e:
            handle_network_error(e, format_type=output_format)
            return
    elif requirement == CommandNetworkRequirement.OFFLINE:
        offline_mode = True
    
    # Only activate for commands that need it
    designer = DesignerAgent()
    try:
        asyncio.run(designer.activate(offline_mode=offline_mode))
        if command in ("design-api", "api-design"):
            # Support both command names: design-api (internal) and api-design (CLI alias)
            result = asyncio.run(
                designer.run(
                    "design-api",
                    requirements=args.requirements,
                    api_type=getattr(args, "api_type", "REST"),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command in ("design-data-model", "data-model-design"):
            # Support both command names: design-data-model (internal) and data-model-design (CLI alias)
            result = asyncio.run(
                designer.run(
                    "design-data-model",
                    requirements=args.requirements,
                    data_source=getattr(args, "data_source", ""),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command in ("design-ui", "ui-ux-design"):
            # Support both command names: design-ui (internal) and ui-ux-design (CLI alias)
            result = asyncio.run(
                designer.run(
                    "design-ui",
                    feature_description=args.feature_description,
                    user_stories=getattr(args, "user_stories", []),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command in ("create-wireframe", "wireframes"):
            # Support both command names: create-wireframe (internal) and wireframes (CLI alias)
            result = asyncio.run(
                designer.run(
                    "create-wireframe",
                    screen_description=args.screen_description,
                    wireframe_type=getattr(args, "wireframe_type", "page"),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command in ("define-design-system", "design-system"):
            # Support both command names: define-design-system (internal) and design-system (CLI alias)
            result = asyncio.run(
                designer.run(
                    "define-design-system",
                    project_description=args.project_description,
                    brand_guidelines=getattr(args, "brand_guidelines", ""),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("designer")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        feedback.output_result(result, message="Design completed successfully")
    finally:
        safe_close_agent_sync(designer)

