"""
Reviewer agent command handlers
"""
import asyncio
import sys
from pathlib import Path

from ...agents.reviewer.agent import ReviewerAgent
from ..base import normalize_command
from .common import check_result_error, format_json_output


async def review_command(
    file_path: str, model: str | None = None, output_format: str = "json"
):
    """Review a code file (supports both *review and review commands)"""
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    reviewer = ReviewerAgent()
    try:
        # Activate agent (load configs, etc.)
        await reviewer.activate()

        # Execute review command
        result = await reviewer.run(
            "review", file=file_path, model=model or "qwen2.5-coder:7b"
        )

        check_result_error(result)

        if output_format == "json":
            format_json_output(result)
        else:
            # Simple text format
            print(f"Review: {result['file']}")
            if "scoring" in result:
                scores = result["scoring"]
                print("\nScores:")
                print(f"  Complexity: {scores['complexity_score']:.1f}/10")
                print(f"  Security: {scores['security_score']:.1f}/10")
                print(f"  Maintainability: {scores['maintainability_score']:.1f}/10")
                print(f"  Overall: {scores['overall_score']:.1f}/100")
                print(f"\nPassed: {result.get('passed', False)}")

            if "feedback" in result and "summary" in result["feedback"]:
                print(f"\nFeedback:\n{result['feedback']['summary']}")
    finally:
        await reviewer.close()


async def score_command(file_path: str, output_format: str = "json"):
    """Score a code file (supports both *score and score commands)"""
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    reviewer = ReviewerAgent()
    try:
        await reviewer.activate()
        result = await reviewer.run("score", file=file_path)

        check_result_error(result)

        if output_format == "json":
            format_json_output(result)
        else:
            print(f"Scores for: {result['file']}")
            if "scoring" in result:
                scores = result["scoring"]
                print(f"  Complexity: {scores['complexity_score']:.1f}/10")
                print(f"  Security: {scores['security_score']:.1f}/10")
                print(f"  Maintainability: {scores['maintainability_score']:.1f}/10")
                print(f"  Overall: {scores['overall_score']:.1f}/100")
    finally:
        await reviewer.close()


async def help_command():
    """Show help (supports both *help and help commands)"""
    reviewer = ReviewerAgent()
    await reviewer.activate()
    result = await reviewer.run("help")
    print(result["content"])
    await reviewer.close()


def handle_reviewer_command(args: object) -> None:
    """Handle reviewer agent commands"""
    command = normalize_command(getattr(args, "command", None))
    reviewer = ReviewerAgent()
    
    try:
        if command == "review":
            asyncio.run(
                review_command(args.file, getattr(args, "model", None), getattr(args, "format", "json"))
            )
        elif command == "score":
            asyncio.run(score_command(args.file, getattr(args, "format", "json")))
        elif command == "lint":
            asyncio.run(reviewer.activate())
            result = asyncio.run(reviewer.run("lint", file=args.file))
            check_result_error(result)
            output_format = getattr(args, "format", "json")
            if output_format == "json":
                format_json_output(result)
            else:
                if "issues" in result:
                    print(f"Linting issues for {args.file}:")
                    for issue in result["issues"]:
                        print(
                            f"  {issue.get('code', '')}: {issue.get('message', '')} (line {issue.get('line', '?')})"
                        )
        elif command == "type-check":
            asyncio.run(reviewer.activate())
            result = asyncio.run(reviewer.run("type-check", file=args.file))
            check_result_error(result)
            output_format = getattr(args, "format", "json")
            if output_format == "json":
                format_json_output(result)
            else:
                if "errors" in result:
                    print(f"Type checking errors for {args.file}:")
                    for error in result["errors"]:
                        print(
                            f"  {error.get('message', '')} (line {error.get('line', '?')})"
                        )
        elif command == "report":
            asyncio.run(reviewer.activate())
            formats = getattr(args, "formats", ["all"])
            if "all" in formats:
                format_type = "all"
            else:
                format_type = ",".join(formats)
            result = asyncio.run(
                reviewer.run(
                    "report",
                    target=args.target,
                    format=format_type,
                    output_dir=getattr(args, "output_dir", None),
                )
            )
            check_result_error(result)
            format_json_output(result)
        elif command == "duplication":
            asyncio.run(reviewer.activate())
            result = asyncio.run(reviewer.run("duplication", file=args.target))
            check_result_error(result)
            output_format = getattr(args, "format", "json")
            if output_format == "json":
                format_json_output(result)
            else:
                if "duplicates" in result:
                    print(f"Code duplication detected in {args.target}:")
                    print(f"  Total duplicates: {len(result.get('duplicates', []))}")
        elif command == "analyze-project":
            asyncio.run(reviewer.activate())
            result = asyncio.run(
                reviewer.run(
                    "analyze-project",
                    project_root=getattr(args, "project_root", None),
                    include_comparison=not getattr(args, "no_comparison", False),
                )
            )
            check_result_error(result)
            output_format = getattr(args, "format", "json")
            if output_format == "json":
                format_json_output(result)
            else:
                print("Project analysis complete. See JSON output for details.")
        elif command == "analyze-services":
            asyncio.run(reviewer.activate())
            services = getattr(args, "services", None)
            result = asyncio.run(
                reviewer.run(
                    "analyze-services",
                    services=services if services else None,
                    project_root=getattr(args, "project_root", None),
                    include_comparison=not getattr(args, "no_comparison", False),
                )
            )
            check_result_error(result)
            output_format = getattr(args, "format", "json")
            if output_format == "json":
                format_json_output(result)
            else:
                print("Service analysis complete. See JSON output for details.")
        elif command == "help" or command is None:
            asyncio.run(help_command())
        else:
            asyncio.run(help_command())
    finally:
        if reviewer:
            try:
                asyncio.run(reviewer.close())
            except Exception:
                pass

