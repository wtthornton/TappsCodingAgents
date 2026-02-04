"""
Analyst agent command handlers
"""
import asyncio

from ...agents.analyst.agent import AnalystAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error


def handle_analyst_command(args: object) -> None:
    """Handle analyst agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("analyst")
        feedback.output_result(help_text)
        return
    
    # Check network requirement
    from ...core.network_errors import NetworkRequiredError
    from ..base import handle_network_error
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    
    requirement = CommandClassifier.get_network_requirement("analyst", command)
    offline_mode = False
    
    if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
        try:
            raise NetworkRequiredError(
                operation_name=f"analyst {command}",
                message="Network is required for this command"
            )
        except NetworkRequiredError as e:
            handle_network_error(e, format_type=output_format)
            return
    elif requirement == CommandNetworkRequirement.OFFLINE:
        offline_mode = True
    
    # Only activate for commands that need it
    analyst = AnalystAgent()
    try:
        asyncio.run(analyst.activate(offline_mode=offline_mode))
        if command == "gather-requirements":
            desc_preview = args.description[:50] + "..." if len(args.description) > 50 else args.description
            feedback.start_operation("Gather Requirements", f"Gathering requirements: {desc_preview}")
            feedback.running("Analyzing description...", step=1, total_steps=4)
            result = asyncio.run(
                analyst.run(
                    "gather-requirements",
                    description=args.description,
                    context=getattr(args, "context", ""),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
            feedback.running("Extracting requirements...", step=2, total_steps=4)
            feedback.running("Organizing requirements...", step=3, total_steps=4)
            feedback.running("Saving requirements document...", step=4, total_steps=4)
            feedback.clear_progress()
        elif command == "stakeholder-analysis":
            desc_preview = args.description[:50] + "..." if len(args.description) > 50 else args.description
            feedback.start_operation("Stakeholder Analysis", f"Analyzing stakeholders: {desc_preview}")
            feedback.running("Identifying stakeholders...", step=1, total_steps=3)
            result = asyncio.run(
                analyst.run(
                    "analyze-stakeholders",
                    description=args.description,
                    stakeholders=getattr(args, "stakeholders", []),
                )
            )
            feedback.running("Analyzing stakeholder needs...", step=2, total_steps=3)
            feedback.running("Generating analysis report...", step=3, total_steps=3)
            feedback.clear_progress()
        elif command == "tech-research":
            req_preview = args.requirement[:50] + "..." if len(args.requirement) > 50 else args.requirement
            feedback.start_operation("Technology Research", f"Researching: {req_preview}")
            feedback.running("Analyzing requirement...", step=1, total_steps=3)
            result = asyncio.run(
                analyst.run(
                    "research-technology",
                    requirement=args.requirement,
                    context=getattr(args, "context", ""),
                    criteria=getattr(args, "criteria", []),
                )
            )
            feedback.running("Researching technology options...", step=2, total_steps=3)
            feedback.running("Evaluating options...", step=3, total_steps=3)
            feedback.clear_progress()
        elif command == "estimate-effort":
            feat_preview = args.feature_description[:50] + "..." if len(args.feature_description) > 50 else args.feature_description
            feedback.start_operation("Effort Estimation", f"Estimating effort: {feat_preview}")
            feedback.running("Analyzing feature...", step=1, total_steps=3)
            result = asyncio.run(
                analyst.run(
                    "estimate-effort",
                    feature_description=args.feature_description,
                    context=getattr(args, "context", ""),
                )
            )
            feedback.running("Calculating complexity...", step=2, total_steps=3)
            feedback.running("Generating estimate...", step=3, total_steps=3)
            feedback.clear_progress()
        elif command == "assess-risk":
            feat_preview = args.feature_description[:50] + "..." if len(args.feature_description) > 50 else args.feature_description
            feedback.start_operation("Risk Assessment", f"Assessing risks: {feat_preview}")
            feedback.running("Analyzing feature...", step=1, total_steps=3)
            result = asyncio.run(
                analyst.run(
                    "assess-risk",
                    feature_description=args.feature_description,
                    context=getattr(args, "context", ""),
                )
            )
            feedback.running("Identifying risks...", step=2, total_steps=3)
            feedback.running("Evaluating risk levels...", step=3, total_steps=3)
            feedback.clear_progress()
        elif command == "competitive-analysis":
            prod_preview = args.product_description[:50] + "..." if len(args.product_description) > 50 else args.product_description
            feedback.start_operation("Competitive Analysis", f"Analyzing: {prod_preview}")
            feedback.running("Identifying competitors...", step=1, total_steps=3)
            result = asyncio.run(
                analyst.run(
                    "competitive-analysis",
                    product_description=args.product_description,
                    competitors=getattr(args, "competitors", []),
                )
            )
            feedback.running("Analyzing competitive landscape...", step=2, total_steps=3)
            feedback.running("Generating analysis report...", step=3, total_steps=3)
            feedback.clear_progress()
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("analyst")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        
        # Build summary based on command type
        summary = {}
        if isinstance(result, dict):
            if "output_file" in result:
                summary["output_file"] = result["output_file"]
            if command == "gather-requirements" and "requirements" in result:
                reqs = result["requirements"]
                if isinstance(reqs, list):
                    summary["requirements_count"] = len(reqs)
                elif isinstance(reqs, dict):
                    summary["requirements_count"] = len(reqs)
            if command == "stakeholder-analysis" and "stakeholders" in result:
                summary["stakeholders_count"] = len(result["stakeholders"]) if isinstance(result["stakeholders"], list) else 0
            if command == "estimate-effort" and "estimate" in result:
                summary["estimated_effort"] = result["estimate"]
            if command == "assess-risk" and "risks" in result:
                risks = result["risks"]
                summary["risks_count"] = len(risks) if isinstance(risks, list) else 0
            
            # Merge summary into result
            if summary:
                result = {**result, "summary": summary}
        
        feedback.output_result(result, message="Analysis completed successfully")
    finally:
        safe_close_agent_sync(analyst)

