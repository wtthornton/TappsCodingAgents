"""
Reviewer agent command handlers
"""
import asyncio
import sys
from pathlib import Path

from ...agents.reviewer.agent import ReviewerAgent
from ..base import normalize_command
from ..feedback import get_feedback, ProgressTracker
from .common import check_result_error, format_json_output


async def review_command(
    file_path: str, model: str | None = None, output_format: str = "json"
):
    """Review a code file (supports both *review and review commands)"""
    feedback = get_feedback()
    feedback.format_type = output_format
    path = Path(file_path)

    if not path.exists():
        feedback.error(
            f"File not found: {file_path}",
            error_code="file_not_found",
            context={"file_path": str(file_path), "working_directory": str(Path.cwd())},
            remediation="Check that the file exists and the path is correct",
            exit_code=1,
        )

    feedback.start_operation("Review")
    feedback.info(f"Reviewing {file_path}...")
    
    reviewer = ReviewerAgent()
    try:
        # Activate agent (load configs, etc.)
        if feedback.verbosity.value == "verbose":
            feedback.info("Initializing ReviewerAgent...")
        await reviewer.activate()

        # Execute review command
        if feedback.verbosity.value == "verbose":
            feedback.info(f"Loading model: {model or 'qwen2.5-coder:7b'}")
            feedback.info("Running code analysis...")
        
        result = await reviewer.run(
            "review", file=file_path, model=model or "qwen2.5-coder:7b"
        )

        check_result_error(result)
        
        feedback.clear_progress()

        if output_format == "json":
            # Use feedback system for JSON output
            summary = None
            if "scoring" in result:
                scores = result["scoring"]
                summary = {
                    "complexity": f"{scores['complexity_score']:.1f}/10",
                    "security": f"{scores['security_score']:.1f}/10",
                    "maintainability": f"{scores['maintainability_score']:.1f}/10",
                    "overall": f"{scores['overall_score']:.1f}/100",
                    "passed": result.get("passed", False),
                }
            feedback.output_result(result, message="Review completed successfully", warnings=None)
        else:
            # Text format
            feedback.success("Review completed")
            if "scoring" in result:
                scores = result["scoring"]
                print(f"\nScore: {scores['overall_score']:.1f}/100")
                print(f"  Complexity: {scores['complexity_score']:.1f}/10")
                print(f"  Security: {scores['security_score']:.1f}/10")
                print(f"  Maintainability: {scores['maintainability_score']:.1f}/10")
                print(f"  Status: {'Passed' if result.get('passed', False) else 'Failed'}")

            if "feedback" in result and "summary" in result["feedback"]:
                print(f"\nFeedback:\n{result['feedback']['summary']}")
    finally:
        await reviewer.close()


async def score_command(file_path: str, output_format: str = "json"):
    """Score a code file (supports both *score and score commands)"""
    feedback = get_feedback()
    feedback.format_type = output_format
    path = Path(file_path)

    if not path.exists():
        feedback.error(
            f"File not found: {file_path}",
            error_code="file_not_found",
            context={"file_path": str(file_path), "working_directory": str(Path.cwd())},
            remediation="Check that the file exists and the path is correct",
            exit_code=1,
        )

    feedback.start_operation("Score")
    feedback.info(f"Scoring {file_path}...")
    
    reviewer = ReviewerAgent()
    try:
        await reviewer.activate()
        result = await reviewer.run("score", file=file_path)

        check_result_error(result)
        
        feedback.clear_progress()

        if output_format == "json":
            summary = None
            if "scoring" in result:
                scores = result["scoring"]
                summary = {
                    "complexity": f"{scores['complexity_score']:.1f}/10",
                    "security": f"{scores['security_score']:.1f}/10",
                    "maintainability": f"{scores['maintainability_score']:.1f}/10",
                    "overall": f"{scores['overall_score']:.1f}/100",
                }
            feedback.output_result(result, message="Scoring completed", warnings=None)
        else:
            feedback.success("Scoring completed")
            if "scoring" in result:
                scores = result["scoring"]
                print(f"\nScores for: {result['file']}")
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
    feedback = get_feedback()
    feedback.output_result(result["content"])
    await reviewer.close()


def handle_reviewer_command(args: object) -> None:
    """Handle reviewer agent commands"""
    from ..feedback import get_feedback
    
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    reviewer = ReviewerAgent()
    
    try:
        if command == "review":
            asyncio.run(
                review_command(args.file, getattr(args, "model", None), output_format)
            )
        elif command == "score":
            asyncio.run(score_command(args.file, output_format))
        elif command == "lint":
            feedback.start_operation("Lint")
            feedback.info(f"Linting {args.file}...")
            asyncio.run(reviewer.activate())
            result = asyncio.run(reviewer.run("lint", file=args.file))
            check_result_error(result)
            feedback.clear_progress()
            if output_format == "json":
                feedback.output_result(result, message="Linting completed")
            else:
                feedback.success("Linting completed")
                if "issues" in result:
                    print(f"\nLinting issues for {args.file}:")
                    for issue in result["issues"]:
                        print(
                            f"  {issue.get('code', '')}: {issue.get('message', '')} (line {issue.get('line', '?')})"
                        )
        elif command == "type-check":
            feedback.start_operation("Type Check")
            feedback.info(f"Type checking {args.file}...")
            asyncio.run(reviewer.activate())
            result = asyncio.run(reviewer.run("type-check", file=args.file))
            check_result_error(result)
            feedback.clear_progress()
            if output_format == "json":
                feedback.output_result(result, message="Type checking completed")
            else:
                feedback.success("Type checking completed")
                if "errors" in result:
                    print(f"\nType checking errors for {args.file}:")
                    for error in result["errors"]:
                        print(
                            f"  {error.get('message', '')} (line {error.get('line', '?')})"
                        )
        elif command == "report":
            feedback.start_operation("Report")
            feedback.info("Generating report...")
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
            feedback.clear_progress()
            feedback.output_result(result, message="Report generated successfully")
        elif command == "duplication":
            feedback.start_operation("Duplication Check")
            feedback.info(f"Checking for code duplication in {args.target}...")
            asyncio.run(reviewer.activate())
            result = asyncio.run(reviewer.run("duplication", file=args.target))
            check_result_error(result)
            feedback.clear_progress()
            if output_format == "json":
                feedback.output_result(result, message="Duplication check completed")
            else:
                feedback.success("Duplication check completed")
                if "duplicates" in result:
                    print(f"\nCode duplication detected in {args.target}:")
                    print(f"  Total duplicates: {len(result.get('duplicates', []))}")
        elif command == "analyze-project":
            feedback.start_operation("Project Analysis")
            feedback.info("Analyzing project...")
            asyncio.run(reviewer.activate())
            result = asyncio.run(
                reviewer.run(
                    "analyze-project",
                    project_root=getattr(args, "project_root", None),
                    include_comparison=not getattr(args, "no_comparison", False),
                )
            )
            check_result_error(result)
            feedback.clear_progress()
            feedback.output_result(result, message="Project analysis completed")
        elif command == "analyze-services":
            feedback.start_operation("Service Analysis")
            feedback.info("Analyzing services...")
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
            feedback.clear_progress()
            feedback.output_result(result, message="Service analysis completed")
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

