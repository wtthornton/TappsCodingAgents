"""
Reviewer agent command handlers
"""
import asyncio
import sys
from pathlib import Path
from typing import Any

from ...agents.reviewer.agent import ReviewerAgent
from ..base import normalize_command
from ..feedback import get_feedback, ProgressTracker
from .common import check_result_error, format_json_output
from ..formatters import format_json, format_markdown, format_html


async def review_command(
    file_path: str | None = None,
    files: list[str] | None = None,
    pattern: str | None = None,
    output_format: str = "json",
    max_workers: int = 4,
):
    """
    Review code file(s) (supports both *review and review commands).
    
    Supports single file (backward compatible) or batch processing.
    """
    feedback = get_feedback()
    feedback.format_type = output_format
    
    # Handle backward compatibility: single file argument
    if file_path and not files and not pattern:
        files = [file_path]
    
    # Resolve file list
    try:
        resolved_files = _resolve_file_list(files, pattern)
    except ValueError as e:
        feedback.error(
            str(e),
            error_code="no_files_found",
            context={"files": files, "pattern": pattern},
            remediation="Specify files as arguments or use --pattern with a glob pattern",
            exit_code=1,
        )
        return
    
    # Validate files exist
    missing_files = [f for f in resolved_files if not f.exists()]
    if missing_files:
        feedback.error(
            f"Files not found: {', '.join(str(f) for f in missing_files)}",
            error_code="file_not_found",
            context={"missing_files": [str(f) for f in missing_files]},
            remediation="Check that the files exist and paths are correct",
            exit_code=1,
        )
        return

    feedback.start_operation("Review")
    if len(resolved_files) == 1:
        feedback.info(f"Reviewing {resolved_files[0]}...")
    else:
        feedback.info(f"Reviewing {len(resolved_files)} files (max {max_workers} concurrent)...")
    
    reviewer = ReviewerAgent()
    try:
        # Activate agent (load configs, etc.)
        if feedback.verbosity.value == "verbose":
            feedback.info("Initializing ReviewerAgent...")
        await reviewer.activate()

        # Single file - use existing flow for backward compatibility
        if len(resolved_files) == 1:
            # Execute review command
            if feedback.verbosity.value == "verbose":
                feedback.info("Running code analysis...")
            
            result = await reviewer.run("review", file=str(resolved_files[0]))
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
        else:
            # Batch processing
            result = await _process_file_batch(reviewer, resolved_files, "review", max_workers)
            feedback.clear_progress()
            
            if output_format == "json":
                feedback.output_result(result, message=f"Review completed: {result['successful']}/{result['total']} files successful")
            else:
                feedback.success(f"Review completed: {result['successful']}/{result['total']} files successful")
                print(f"\nBatch Review Results:")
                print(f"  Total files: {result['total']}")
                print(f"  Successful: {result['successful']}")
                print(f"  Failed: {result['failed']}")
                
                if result['errors']:
                    print(f"\nErrors:")
                    for error in result['errors']:
                        print(f"  {error.get('file', 'unknown')}: {error.get('error', 'unknown error')}")
                
                print(f"\nReviews:")
                for file_result in result['files']:
                    if "scoring" in file_result:
                        scores = file_result["scoring"]
                        print(f"  {file_result['file']}:")
                        print(f"    Score: {scores['overall_score']:.1f}/100")
                        print(f"    Status: {'Passed' if file_result.get('passed', False) else 'Failed'}")
    finally:
        await reviewer.close()


def _resolve_file_list(files: list[str] | None, pattern: str | None) -> list[Path]:
    """
    Resolve file list from files and/or pattern.
    
    Args:
        files: List of file paths (can be None or empty)
        pattern: Glob pattern (can be None)
        
    Returns:
        List of resolved Path objects
        
    Raises:
        ValueError: If no files found
    """
    resolved_files: list[Path] = []
    
    # Handle glob pattern
    if pattern:
        cwd = Path.cwd()
        matched_files = list(cwd.glob(pattern))
        resolved_files.extend(matched_files)
    
    # Handle explicit file list
    if files:
        for file_path in files:
            path = Path(file_path)
            if not path.is_absolute():
                path = Path.cwd() / path
            if path.exists():
                resolved_files.append(path)
            else:
                # Try relative to cwd
                cwd_path = Path.cwd() / file_path
                if cwd_path.exists():
                    resolved_files.append(cwd_path)
                else:
                    # Keep it anyway - let the agent handle the error
                    resolved_files.append(path)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in resolved_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)
    
    if not unique_files:
        raise ValueError("No files found. Specify files or use --pattern to match files.")
    
    return unique_files


async def _process_file_batch(
    reviewer: ReviewerAgent,
    files: list[Path],
    command: str,
    max_workers: int = 4,
) -> dict[str, Any]:
    """
    Process multiple files concurrently.
    
    Args:
        reviewer: ReviewerAgent instance
        files: List of file paths to process
        command: Command to run ('score', 'review', 'lint', 'type-check')
        max_workers: Maximum concurrent operations
        
    Returns:
        Dictionary with aggregated results
    """
    semaphore = asyncio.Semaphore(max_workers)
    
    async def process_single_file(file_path: Path) -> tuple[Path, dict[str, Any]]:
        """Process a single file with semaphore limiting."""
        async with semaphore:
            try:
                result = await reviewer.run(command, file=str(file_path))
                return (file_path, result)
            except Exception as e:
                return (file_path, {"error": str(e), "file": str(file_path)})
    
    # Process all files concurrently
    tasks = [process_single_file(f) for f in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Aggregate results
    aggregated: dict[str, Any] = {
        "files": [],
        "successful": 0,
        "failed": 0,
        "errors": [],
    }
    
    for result in results:
        if isinstance(result, Exception):
            aggregated["failed"] += 1
            aggregated["errors"].append({"error": str(result)})
            continue
            
        file_path, file_result = result
        
        if "error" in file_result:
            aggregated["failed"] += 1
            aggregated["errors"].append({
                "file": str(file_path),
                "error": file_result["error"]
            })
        else:
            aggregated["successful"] += 1
        
        file_entry: dict[str, Any] = {
            "file": str(file_path),
        }
        file_entry.update(file_result)
        aggregated["files"].append(file_entry)
    
    aggregated["total"] = len(files)
    return aggregated


async def score_command(
    file_path: str | None = None,
    files: list[str] | None = None,
    pattern: str | None = None,
    output_format: str = "json",
    max_workers: int = 4,
    output_file: str | None = None,
):
    """
    Score code file(s) (supports both *score and score commands).
    
    Supports single file (backward compatible) or batch processing.
    """
    feedback = get_feedback()
    feedback.format_type = output_format
    
    # Handle backward compatibility: single file argument
    if file_path and not files and not pattern:
        files = [file_path]
    
    # Resolve file list
    try:
        resolved_files = _resolve_file_list(files, pattern)
    except ValueError as e:
        feedback.error(
            str(e),
            error_code="no_files_found",
            context={"files": files, "pattern": pattern},
            remediation="Specify files as arguments or use --pattern with a glob pattern",
            exit_code=1,
        )
        return
    
    # Validate files exist
    missing_files = [f for f in resolved_files if not f.exists()]
    if missing_files:
        feedback.error(
            f"Files not found: {', '.join(str(f) for f in missing_files)}",
            error_code="file_not_found",
            context={"missing_files": [str(f) for f in missing_files]},
            remediation="Check that the files exist and paths are correct",
            exit_code=1,
        )
        return
    
    feedback.start_operation("Score")
    if len(resolved_files) == 1:
        feedback.info(f"Scoring {resolved_files[0]}...")
    else:
        feedback.info(f"Scoring {len(resolved_files)} files (max {max_workers} concurrent)...")
    
    reviewer = ReviewerAgent()
    try:
        await reviewer.activate()
        
        # Single file - use existing flow for backward compatibility
        if len(resolved_files) == 1:
            result = await reviewer.run("score", file=str(resolved_files[0]))
            check_result_error(result)
            feedback.clear_progress()
            
            # Determine output format from file extension if output_file is specified
            if output_file:
                output_path = Path(output_file)
                if output_path.suffix == ".html":
                    output_format = "html"
                elif output_path.suffix == ".md":
                    output_format = "markdown"
                elif output_path.suffix == ".json":
                    output_format = "json"
            
            # Format and output result
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
                output_content = format_json(result)
            elif output_format == "markdown":
                output_content = format_markdown(result)
            elif output_format == "html":
                output_content = format_html(result, title="Code Quality Scores")
            else:  # text
                output_content = None  # Use existing text output
            
            # Write to file or stdout
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(output_content, encoding="utf-8")
                feedback.success(f"Results written to {output_file}")
            else:
                if output_format == "json":
                    feedback.output_result(result, message="Scoring completed", warnings=None)
                elif output_format in ("markdown", "html"):
                    print(output_content)
                else:
                    feedback.success("Scoring completed")
                    if "scoring" in result:
                        scores = result["scoring"]
                        print(f"\nScores for: {result['file']}")
                        print(f"  Complexity: {scores['complexity_score']:.1f}/10")
                        print(f"  Security: {scores['security_score']:.1f}/10")
                        print(f"  Maintainability: {scores['maintainability_score']:.1f}/10")
                        print(f"  Overall: {scores['overall_score']:.1f}/100")
        else:
            # Batch processing
            result = await _process_file_batch(reviewer, resolved_files, "score", max_workers)
            feedback.clear_progress()
            
            # Determine output format from file extension if output_file is specified
            if output_file:
                output_path = Path(output_file)
                if output_path.suffix == ".html":
                    output_format = "html"
                elif output_path.suffix == ".md":
                    output_format = "markdown"
                elif output_path.suffix == ".json":
                    output_format = "json"
            
            # Format and output result
            if output_format == "json":
                output_content = format_json(result)
            elif output_format == "markdown":
                output_content = format_markdown(result['files'])
            elif output_format == "html":
                output_content = format_html(result['files'], title="Batch Code Quality Scores")
            else:  # text
                output_content = None  # Use existing text output
            
            # Write to file or stdout
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(output_content, encoding="utf-8")
                feedback.success(f"Results written to {output_file}")
            else:
                if output_format == "json":
                    feedback.output_result(result, message=f"Scoring completed: {result['successful']}/{result['total']} files successful")
                elif output_format in ("markdown", "html"):
                    print(output_content)
                else:
                    feedback.success(f"Scoring completed: {result['successful']}/{result['total']} files successful")
                    print(f"\nBatch Scoring Results:")
                    print(f"  Total files: {result['total']}")
                    print(f"  Successful: {result['successful']}")
                    print(f"  Failed: {result['failed']}")
                    
                    if result['errors']:
                        print(f"\nErrors:")
                        for error in result['errors']:
                            print(f"  {error.get('file', 'unknown')}: {error.get('error', 'unknown error')}")
                    
                    print(f"\nScores:")
                    for file_result in result['files']:
                        if "scoring" in file_result:
                            scores = file_result["scoring"]
                            print(f"  {file_result['file']}:")
                            print(f"    Complexity: {scores['complexity_score']:.1f}/10")
                            print(f"    Security: {scores['security_score']:.1f}/10")
                            print(f"    Maintainability: {scores['maintainability_score']:.1f}/10")
                            print(f"    Overall: {scores['overall_score']:.1f}/100")
    finally:
        await reviewer.close()


async def help_command():
    """Show help (supports both *help and help commands) - uses static help, no activation needed"""
    from ..help.static_help import get_static_help
    help_text = get_static_help("reviewer")
    feedback = get_feedback()
    feedback.output_result(help_text)


def handle_reviewer_command(args: object) -> None:
    """Handle reviewer agent commands"""
    from ..feedback import get_feedback
    from ..help.static_help import get_static_help
    
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("reviewer")
        feedback.output_result(help_text)
        return
    
    # Get batch operation parameters
    files = getattr(args, "files", None)
    pattern = getattr(args, "pattern", None)
    max_workers = getattr(args, "max_workers", 4)
    
    # Backward compatibility: support 'file' attribute for single file
    single_file = getattr(args, "file", None)
    if single_file and not files:
        files = [single_file]
    
    reviewer = ReviewerAgent()
    
    try:
        if command == "review":
            asyncio.run(
                review_command(
                    file_path=single_file,
                    files=files,
                    pattern=pattern,
                    output_format=output_format,
                    max_workers=max_workers,
                )
            )
        elif command == "score":
            output_file = getattr(args, "output", None)
            asyncio.run(
                score_command(
                    file_path=single_file,
                    files=files,
                    pattern=pattern,
                    output_format=output_format,
                    max_workers=max_workers,
                    output_file=output_file,
                )
            )
        elif command == "lint":
            output_file = getattr(args, "output", None)
            
            # Resolve file list
            try:
                resolved_files = _resolve_file_list(files, pattern)
            except ValueError as e:
                feedback.error(
                    str(e),
                    error_code="no_files_found",
                    context={"files": files, "pattern": pattern},
                    remediation="Specify files as arguments or use --pattern with a glob pattern",
                    exit_code=1,
                )
                return
            
            feedback.start_operation("Lint")
            if len(resolved_files) == 1:
                feedback.info(f"Linting {resolved_files[0]}...")
            else:
                feedback.info(f"Linting {len(resolved_files)} files (max {max_workers} concurrent)...")
            
            asyncio.run(reviewer.activate())
            
            # Determine output format from file extension if output_file is specified
            if output_file:
                output_path = Path(output_file)
                if output_path.suffix == ".html":
                    output_format = "html"
                elif output_path.suffix == ".md":
                    output_format = "markdown"
                elif output_path.suffix == ".json":
                    output_format = "json"
            
            if len(resolved_files) == 1:
                result = asyncio.run(reviewer.run("lint", file=str(resolved_files[0])))
                check_result_error(result)
                feedback.clear_progress()
                
                # Format and output result
                if output_format == "json":
                    output_content = format_json(result)
                elif output_format == "markdown":
                    output_content = format_markdown(result)
                elif output_format == "html":
                    output_content = format_html(result, title="Linting Results")
                else:  # text
                    output_content = None  # Use existing text output
                
                # Write to file or stdout
                if output_file:
                    output_path = Path(output_file)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(output_content, encoding="utf-8")
                    feedback.success(f"Results written to {output_file}")
                else:
                    if output_format == "json":
                        feedback.output_result(result, message="Linting completed")
                    else:
                        feedback.success("Linting completed")
                        if "issues" in result:
                            print(f"\nLinting issues for {resolved_files[0]}:")
                            for issue in result["issues"]:
                                print(
                                    f"  {issue.get('code', '')}: {issue.get('message', '')} (line {issue.get('line', '?')})"
                                )
            else:
                result = asyncio.run(_process_file_batch(reviewer, resolved_files, "lint", max_workers))
                feedback.clear_progress()
                
                # Format and output result
                if output_format == "json":
                    output_content = format_json(result)
                elif output_format == "markdown":
                    output_content = format_markdown(result['files'])
                elif output_format == "html":
                    output_content = format_html(result['files'], title="Batch Linting Results")
                else:  # text
                    output_content = None  # Use existing text output
                
                # Write to file or stdout
                if output_file:
                    output_path = Path(output_file)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(output_content, encoding="utf-8")
                    feedback.success(f"Results written to {output_file}")
                else:
                    if output_format == "json":
                        feedback.output_result(result, message=f"Linting completed: {result['successful']}/{result['total']} files successful")
                    else:
                        feedback.success(f"Linting completed: {result['successful']}/{result['total']} files successful")
                        print(f"\nBatch Linting Results:")
                        print(f"  Total files: {result['total']}")
                        print(f"  Successful: {result['successful']}")
                        print(f"  Failed: {result['failed']}")
                        
                        if result['errors']:
                            print(f"\nErrors:")
                            for error in result['errors']:
                                print(f"  {error.get('file', 'unknown')}: {error.get('error', 'unknown error')}")
                        
                        print(f"\nLinting Issues:")
                        for file_result in result['files']:
                            if "issues" in file_result:
                                print(f"  {file_result['file']}: {len(file_result['issues'])} issues")
                                for issue in file_result["issues"][:5]:  # Show first 5
                                    print(f"    {issue.get('code', '')}: {issue.get('message', '')} (line {issue.get('line', '?')})")
                                if len(file_result["issues"]) > 5:
                                    print(f"    ... and {len(file_result['issues']) - 5} more issues")
        elif command == "type-check":
            output_file = getattr(args, "output", None)
            
            # Resolve file list
            try:
                resolved_files = _resolve_file_list(files, pattern)
            except ValueError as e:
                feedback.error(
                    str(e),
                    error_code="no_files_found",
                    context={"files": files, "pattern": pattern},
                    remediation="Specify files as arguments or use --pattern with a glob pattern",
                    exit_code=1,
                )
                return
            
            feedback.start_operation("Type Check")
            if len(resolved_files) == 1:
                feedback.info(f"Type checking {resolved_files[0]}...")
            else:
                feedback.info(f"Type checking {len(resolved_files)} files (max {max_workers} concurrent)...")
            
            asyncio.run(reviewer.activate())
            
            # Determine output format from file extension if output_file is specified
            if output_file:
                output_path = Path(output_file)
                if output_path.suffix == ".html":
                    output_format = "html"
                elif output_path.suffix == ".md":
                    output_format = "markdown"
                elif output_path.suffix == ".json":
                    output_format = "json"
            
            if len(resolved_files) == 1:
                result = asyncio.run(reviewer.run("type-check", file=str(resolved_files[0])))
                check_result_error(result)
                feedback.clear_progress()
                
                # Format and output result
                if output_format == "json":
                    output_content = format_json(result)
                elif output_format == "markdown":
                    output_content = format_markdown(result)
                elif output_format == "html":
                    output_content = format_html(result, title="Type Check Results")
                else:  # text
                    output_content = None  # Use existing text output
                
                # Write to file or stdout
                if output_file:
                    output_path = Path(output_file)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(output_content, encoding="utf-8")
                    feedback.success(f"Results written to {output_file}")
                else:
                    if output_format == "json":
                        feedback.output_result(result, message="Type checking completed")
                    else:
                        feedback.success("Type checking completed")
                        if "errors" in result:
                            print(f"\nType checking errors for {resolved_files[0]}:")
                            for error in result["errors"]:
                                print(
                                    f"  {error.get('message', '')} (line {error.get('line', '?')})"
                                )
            else:
                result = asyncio.run(_process_file_batch(reviewer, resolved_files, "type-check", max_workers))
                feedback.clear_progress()
                
                # Format and output result
                if output_format == "json":
                    output_content = format_json(result)
                elif output_format == "markdown":
                    output_content = format_markdown(result['files'])
                elif output_format == "html":
                    output_content = format_html(result['files'], title="Batch Type Check Results")
                else:  # text
                    output_content = None  # Use existing text output
                
                # Write to file or stdout
                if output_file:
                    output_path = Path(output_file)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(output_content, encoding="utf-8")
                    feedback.success(f"Results written to {output_file}")
                else:
                    if output_format == "json":
                        feedback.output_result(result, message=f"Type checking completed: {result['successful']}/{result['total']} files successful")
                    else:
                        feedback.success(f"Type checking completed: {result['successful']}/{result['total']} files successful")
                        print(f"\nBatch Type Checking Results:")
                        print(f"  Total files: {result['total']}")
                        print(f"  Successful: {result['successful']}")
                        print(f"  Failed: {result['failed']}")
                        
                        if result['errors']:
                            print(f"\nErrors:")
                            for error in result['errors']:
                                print(f"  {error.get('file', 'unknown')}: {error.get('error', 'unknown error')}")
                    
                    print(f"\nType Checking Errors:")
                    for file_result in result['files']:
                        if "errors" in file_result:
                            print(f"  {file_result['file']}: {len(file_result['errors'])} errors")
                            for error in file_result["errors"][:5]:  # Show first 5
                                print(f"    {error.get('message', '')} (line {error.get('line', '?')})")
                            if len(file_result["errors"]) > 5:
                                print(f"    ... and {len(file_result['errors']) - 5} more errors")
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
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("reviewer")
            feedback.output_result(help_text)
    finally:
        from ..utils.agent_lifecycle import safe_close_agent_sync
        safe_close_agent_sync(reviewer)

