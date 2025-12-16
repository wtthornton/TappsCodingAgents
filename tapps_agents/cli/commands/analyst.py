"""
Analyst agent command handlers
"""
import asyncio

from ...agents.analyst.agent import AnalystAgent
from ..base import normalize_command
from .common import check_result_error, format_json_output


def handle_analyst_command(args: object) -> None:
    """Handle analyst agent commands"""
    command = normalize_command(getattr(args, "command", None))
    analyst = AnalystAgent()
    asyncio.run(analyst.activate())
    try:
        if command == "gather-requirements":
            result = asyncio.run(
                analyst.run(
                    "gather-requirements",
                    description=args.description,
                    context=getattr(args, "context", ""),
                    output_file=getattr(args, "output_file", None),
                )
            )
        elif command == "stakeholder-analysis":
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
            print(result["content"])
            return
        else:
            result = asyncio.run(analyst.run("help"))
            print(result["content"])
            return

        check_result_error(result)
        format_json_output(result)
    finally:
        asyncio.run(analyst.close())

