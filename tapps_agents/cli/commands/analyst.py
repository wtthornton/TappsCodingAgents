"""
Analyst agent command handlers
"""
import asyncio

from ...agents.analyst.agent import AnalystAgent
from ..base import normalize_command
from ..feedback import get_feedback
from .common import check_result_error, format_json_output


def handle_analyst_command(args: object) -> None:
    """Handle analyst agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    analyst = AnalystAgent()
    asyncio.run(analyst.activate())
    try:
        if command == "gather-requirements":
            feedback.start_operation("Gather Requirements")
            feedback.info("Gathering requirements...")
            result = asyncio.run(
                analyst.run(
                    "gather-requirements",
                    description=args.description,
                    context=getattr(args, "context", ""),
                    output_file=getattr(args, "output_file", None),
                )
            )
            feedback.clear_progress()
        elif command == "stakeholder-analysis":
            feedback.start_operation("Stakeholder Analysis")
            feedback.info("Analyzing stakeholders...")
            result = asyncio.run(
                analyst.run(
                    "analyze-stakeholders",
                    description=args.description,
                    stakeholders=getattr(args, "stakeholders", []),
                )
            )
        elif command == "tech-research":
            result = asyncio.run(
                analyst.run(
                    "research-technology",
                    requirement=args.requirement,
                    context=getattr(args, "context", ""),
                    criteria=getattr(args, "criteria", []),
                )
            )
        elif command == "estimate-effort":
            result = asyncio.run(
                analyst.run(
                    "estimate-effort",
                    feature_description=args.feature_description,
                    context=getattr(args, "context", ""),
                )
            )
        elif command == "assess-risk":
            result = asyncio.run(
                analyst.run(
                    "assess-risk",
                    feature_description=args.feature_description,
                    context=getattr(args, "context", ""),
                )
            )
        elif command == "competitive-analysis":
            result = asyncio.run(
                analyst.run(
                    "competitive-analysis",
                    product_description=args.product_description,
                    competitors=getattr(args, "competitors", []),
                )
            )
        elif command == "help" or command is None:
            result = asyncio.run(analyst.run("help"))
            feedback.output_result(result["content"])
            return
        else:
            result = asyncio.run(analyst.run("help"))
            feedback.output_result(result["content"])
            return

        check_result_error(result)
        feedback.output_result(result, message="Analysis completed successfully")
    finally:
        asyncio.run(analyst.close())

