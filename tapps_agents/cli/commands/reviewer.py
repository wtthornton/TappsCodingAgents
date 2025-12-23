"""
Reviewer agent command handlers
"""
import asyncio
import sys
from pathlib import Path
from typing import Any

from ...agents.reviewer.agent import ReviewerAgent
from ..base import normalize_command, run_async_command
from ..feedback import get_feedback, ProgressTracker
from .common import check_result_error, format_json_output
from ..formatters import format_json, format_markdown, format_html


def _infer_output_format(output_format: str, output_file: str | None) -> str:
    """Infer output format from output file extension, otherwise keep explicit format."""
    if not output_file:
        return output_format

    suffix = Path(output_file).suffix.lower()
    if suffix == ".html":
        return "html"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".json":
        return "json"
    if suffix in {".txt", ".log"}:
        return "text"
    return output_format


def _write_output(output_file: str, content: str) -> None:
    """Write output content to a file (UTF-8), creating parent directories."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def _format_text_review_result(result: dict[str, Any]) -> str:
    """Create a human-readable review summary string."""
    lines: list[str] = []
    file_path = result.get("file", "unknown")
    lines.append(f"Results for: {file_path}")

    scoring = result.get("scoring") or {}
    if scoring:
        lines.append("")
        lines.append(f"Score: {scoring.get('overall_score', 0.0):.1f}/100")
        lines.append(f"  Complexity: {scoring.get('complexity_score', 0.0):.1f}/10")
        lines.append(f"  Security: {scoring.get('security_score', 0.0):.1f}/10")
        lines.append(f"  Maintainability: {scoring.get('maintainability_score', 0.0):.1f}/10")
        if "threshold" in result:
            lines.append(f"  Threshold: {result.get('threshold')}")
        if "passed" in result:
            lines.append(f"  Status: {'Passed' if result.get('passed') else 'Failed'}")

    feedback = result.get("feedback") or {}
    summary = feedback.get("summary")
    if summary:
        lines.append("")
        lines.append("Feedback:")
        lines.append(str(summary))

    # Surface quality gate signals if present
    if result.get("quality_gate_blocked"):
        lines.append("")
        lines.append("Quality Gate: BLOCKED")

    return "\n".join(lines) + "\n"


def _format_text_batch_summary(result: dict[str, Any], title: str) -> str:
    """Create a human-readable batch summary string."""
    lines: list[str] = []
    lines.append(f"{title} Results")
    lines.append("")
    lines.append(f"  Total files: {result.get('total', 0)}")
    lines.append(f"  Successful: {result.get('successful', 0)}")
    lines.append(f"  Failed: {result.get('failed', 0)}")

    errors = result.get("errors") or []
    if errors:
        lines.append("")
        lines.append("Errors:")
        for err in errors[:25]:
            f = err.get("file", "unknown")
            msg = err.get("error", "unknown error")
            lines.append(f"  {f}: {msg}")
        if len(errors) > 25:
            lines.append(f"  ... and {len(errors) - 25} more")

    return "\n".join(lines) + "\n"


async def review_command(
    file_path: str | None = None,
    files: list[str] | None = None,
    pattern: str | None = None,
    output_format: str = "json",
    max_workers: int = 4,
    output_file: str | None = None,
    fail_under: float | None = None,
):
    """
    Review code file(s) (supports both *review and review commands).
    
    Supports single file (backward compatible) or batch processing.
    """
    feedback = get_feedback()
    output_format = _infer_output_format(output_format, output_file)
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

            # Output handling (stdout vs file)
            if output_file:
                if output_format == "json":
                    output_content = format_json(result)
                elif output_format == "markdown":
                    output_content = format_markdown(result)
                elif output_format == "html":
                    output_content = format_html(result, title="Code Review")
                else:
                    output_content = _format_text_review_result(result)
                _write_output(output_file, output_content)
                feedback.success(f"Results written to {output_file}")
            else:
                if output_format == "json":
                    feedback.output_result(result, message="Review completed successfully", warnings=None)
                elif output_format in ("markdown", "html"):
                    # Print raw content to stdout
                    output_content = (
                        format_markdown(result)
                        if output_format == "markdown"
                        else format_html(result, title="Code Review")
                    )
                    print(output_content)
                else:
                    feedback.success("Review completed")
                    print(_format_text_review_result(result))

            # CI-style failure handling
            if fail_under is not None:
                scoring = result.get("scoring") or {}
                overall = float(scoring.get("overall_score", 0.0))
                if overall < fail_under:
                    sys.exit(1)
            elif result.get("passed") is False:
                # If the agent evaluated a threshold and failed, return non-zero (useful in CI)
                sys.exit(1)
        else:
            # Batch processing
            result = await _process_file_batch(reviewer, resolved_files, "review", max_workers)
            feedback.clear_progress()
            
            if output_file:
                if output_format == "json":
                    output_content = format_json(result)
                elif output_format == "markdown":
                    output_content = format_markdown(result.get("files", []))
                elif output_format == "html":
                    output_content = format_html(result.get("files", []), title="Batch Code Review")
                else:
                    output_content = _format_text_batch_summary(result, title="Batch Review")
                _write_output(output_file, output_content)
                feedback.success(f"Results written to {output_file}")
            else:
                if output_format == "json":
                    feedback.output_result(
                        result,
                        message=f"Review completed: {result['successful']}/{result['total']} files successful",
                    )
                elif output_format in ("markdown", "html"):
                    output_content = (
                        format_markdown(result.get("files", []))
                        if output_format == "markdown"
                        else format_html(result.get("files", []), title="Batch Code Review")
                    )
                    print(output_content)
                else:
                    feedback.success(f"Review completed: {result['successful']}/{result['total']} files successful")
                    print(_format_text_batch_summary(result, title="Batch Review"))

            # Fail if any file failed, or if fail_under is set and any score < threshold
            if fail_under is not None:
                for file_result in result.get("files", []):
                    scoring = file_result.get("scoring") or {}
                    overall = float(scoring.get("overall_score", 0.0))
                    if overall < fail_under:
                        sys.exit(1)
            if int(result.get("failed", 0)) > 0:
                sys.exit(1)
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

    exclude_dir_names = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "dist",
        "build",
        "htmlcov",
        "reports",
        ".tapps-agents",
        "tapps_agents.egg-info",
        ".egg-info",
    }
    allowed_suffixes = {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".java",
        ".go",
        ".rs",
        ".yaml",
        ".yml",
        ".json",
        ".md",
        ".dockerfile",
    }

    def _is_excluded(path: Path) -> bool:
        return any(part in exclude_dir_names for part in path.parts)

    def _discover_from_dir(root: Path, max_files: int = 5000) -> list[Path]:
        discovered: list[Path] = []
        for pat in ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.java", "*.go", "*.rs", "*.yaml", "*.yml"]:
            if len(discovered) >= max_files:
                break
            for p in root.rglob(pat):
                if len(discovered) >= max_files:
                    break
                if _is_excluded(p):
                    continue
                if p.is_file() and p.suffix.lower() in allowed_suffixes:
                    discovered.append(p)
        return discovered
    
    # Handle glob pattern
    if pattern:
        cwd = Path.cwd()
        matched = [p for p in cwd.glob(pattern) if p.is_file() and not _is_excluded(p)]
        resolved_files.extend(matched)
    
    # Handle explicit file list
    if files:
        for file_path in files:
            # Support passing glob patterns directly as positional args (e.g. "src/**/*.py")
            if any(ch in file_path for ch in ["*", "?", "["]):
                for p in Path.cwd().glob(file_path):
                    if p.is_file() and not _is_excluded(p):
                        resolved_files.append(p)
                continue

            path = Path(file_path)
            if not path.is_absolute():
                path = Path.cwd() / path
            if path.exists() and path.is_dir():
                resolved_files.extend(_discover_from_dir(path))
            elif path.exists():
                if path.is_file() and (path.suffix.lower() in allowed_suffixes or path.suffix == ""):
                    resolved_files.append(path)
            else:
                # Try relative to cwd
                cwd_path = Path.cwd() / file_path
                if cwd_path.exists() and cwd_path.is_dir():
                    resolved_files.extend(_discover_from_dir(cwd_path))
                elif cwd_path.exists():
                    if cwd_path.is_file() and (cwd_path.suffix.lower() in allowed_suffixes or cwd_path.suffix == ""):
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
    fail_under: float | None = None,
):
    """
    Score code file(s) (supports both *score and score commands).
    
    Supports single file (backward compatible) or batch processing.
    """
    feedback = get_feedback()
    output_format = _infer_output_format(output_format, output_file)
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
            
            # Format and output result
            if output_format == "json":
                output_content = format_json(result)
            elif output_format == "markdown":
                output_content = format_markdown(result)
            elif output_format == "html":
                output_content = format_html(result, title="Code Quality Scores")
            else:  # text
                output_content = _format_text_review_result(result)
            
            # Write to file or stdout
            if output_file:
                _write_output(output_file, output_content)
                feedback.success(f"Results written to {output_file}")
            else:
                if output_format == "json":
                    feedback.output_result(result, message="Scoring completed", warnings=None)
                elif output_format in ("markdown", "html"):
                    print(output_content)
                else:
                    feedback.success("Scoring completed")
                    print(output_content)

            if fail_under is not None:
                scoring = result.get("scoring") or {}
                overall = float(scoring.get("overall_score", 0.0))
                if overall < fail_under:
                    sys.exit(1)
        else:
            # Batch processing
            result = await _process_file_batch(reviewer, resolved_files, "score", max_workers)
            feedback.clear_progress()
            
            # Format and output result
            if output_format == "json":
                output_content = format_json(result)
            elif output_format == "markdown":
                output_content = format_markdown(result['files'])
            elif output_format == "html":
                output_content = format_html(result['files'], title="Batch Code Quality Scores")
            else:  # text
                output_content = _format_text_batch_summary(result, title="Batch Score")
            
            # Write to file or stdout
            if output_file:
                _write_output(output_file, output_content)
                feedback.success(f"Results written to {output_file}")
            else:
                if output_format == "json":
                    feedback.output_result(result, message=f"Scoring completed: {result['successful']}/{result['total']} files successful")
                elif output_format in ("markdown", "html"):
                    print(output_content)
                else:
                    feedback.success(f"Scoring completed: {result['successful']}/{result['total']} files successful")
                    print(output_content)

            if fail_under is not None:
                for file_result in result.get("files", []):
                    scoring = file_result.get("scoring") or {}
                    overall = float(scoring.get("overall_score", 0.0))
                    if overall < fail_under:
                        sys.exit(1)
            if int(result.get("failed", 0)) > 0:
                sys.exit(1)
    finally:
        await reviewer.close()


async def lint_command(
    file_path: str | None = None,
    files: list[str] | None = None,
    pattern: str | None = None,
    output_format: str = "json",
    max_workers: int = 4,
    output_file: str | None = None,
    fail_on_issues: bool = False,
) -> None:
    """Run linting on file(s) with consistent async execution and output handling."""
    feedback = get_feedback()
    output_format = _infer_output_format(output_format, output_file)
    feedback.format_type = output_format

    if file_path and not files and not pattern:
        files = [file_path]

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

    feedback.start_operation("Lint")
    feedback.info(
        f"Linting {resolved_files[0]}..." if len(resolved_files) == 1 else f"Linting {len(resolved_files)} files (max {max_workers} concurrent)..."
    )

    reviewer = ReviewerAgent()
    try:
        await reviewer.activate()

        if len(resolved_files) == 1:
            result = await reviewer.run("lint", file=str(resolved_files[0]))
            check_result_error(result)
            feedback.clear_progress()

            if output_file:
                if output_format == "json":
                    output_content = format_json(result)
                elif output_format == "markdown":
                    output_content = format_markdown(result)
                elif output_format == "html":
                    output_content = format_html(result, title="Linting Results")
                else:
                    output_content = _format_text_review_result(result)
                _write_output(output_file, output_content)
                feedback.success(f"Results written to {output_file}")
            else:
                if output_format == "json":
                    feedback.output_result(result, message="Linting completed")
                elif output_format in ("markdown", "html"):
                    print(
                        format_markdown(result)
                        if output_format == "markdown"
                        else format_html(result, title="Linting Results")
                    )
                else:
                    feedback.success("Linting completed")
                    print(_format_text_review_result(result))

            if fail_on_issues and int(result.get("issue_count", 0)) > 0:
                sys.exit(1)
        else:
            result = await _process_file_batch(reviewer, resolved_files, "lint", max_workers)
            feedback.clear_progress()

            if output_file:
                if output_format == "json":
                    output_content = format_json(result)
                elif output_format == "markdown":
                    output_content = format_markdown(result.get("files", []))
                elif output_format == "html":
                    output_content = format_html(result.get("files", []), title="Batch Linting Results")
                else:
                    output_content = _format_text_batch_summary(result, title="Batch Lint")
                _write_output(output_file, output_content)
                feedback.success(f"Results written to {output_file}")
            else:
                if output_format == "json":
                    feedback.output_result(
                        result,
                        message=f"Linting completed: {result['successful']}/{result['total']} files successful",
                    )
                elif output_format in ("markdown", "html"):
                    print(
                        format_markdown(result.get("files", []))
                        if output_format == "markdown"
                        else format_html(result.get("files", []), title="Batch Linting Results")
                    )
                else:
                    feedback.success(f"Linting completed: {result['successful']}/{result['total']} files successful")
                    print(_format_text_batch_summary(result, title="Batch Lint"))

            if fail_on_issues:
                for file_result in result.get("files", []):
                    if int(file_result.get("issue_count", 0)) > 0:
                        sys.exit(1)
            if int(result.get("failed", 0)) > 0:
                sys.exit(1)
    finally:
        await reviewer.close()


async def type_check_command(
    file_path: str | None = None,
    files: list[str] | None = None,
    pattern: str | None = None,
    output_format: str = "json",
    max_workers: int = 4,
    output_file: str | None = None,
    fail_on_issues: bool = False,
) -> None:
    """Run type-checking on file(s) with consistent async execution and output handling."""
    feedback = get_feedback()
    output_format = _infer_output_format(output_format, output_file)
    feedback.format_type = output_format

    if file_path and not files and not pattern:
        files = [file_path]

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

    feedback.start_operation("Type Check")
    feedback.info(
        f"Type checking {resolved_files[0]}..." if len(resolved_files) == 1 else f"Type checking {len(resolved_files)} files (max {max_workers} concurrent)..."
    )

    reviewer = ReviewerAgent()
    try:
        await reviewer.activate()

        if len(resolved_files) == 1:
            result = await reviewer.run("type-check", file=str(resolved_files[0]))
            check_result_error(result)
            feedback.clear_progress()

            if output_file:
                if output_format == "json":
                    output_content = format_json(result)
                elif output_format == "markdown":
                    output_content = format_markdown(result)
                elif output_format == "html":
                    output_content = format_html(result, title="Type Check Results")
                else:
                    output_content = _format_text_review_result(result)
                _write_output(output_file, output_content)
                feedback.success(f"Results written to {output_file}")
            else:
                if output_format == "json":
                    feedback.output_result(result, message="Type checking completed")
                elif output_format in ("markdown", "html"):
                    print(
                        format_markdown(result)
                        if output_format == "markdown"
                        else format_html(result, title="Type Check Results")
                    )
                else:
                    feedback.success("Type checking completed")
                    print(_format_text_review_result(result))

            if fail_on_issues and int(result.get("error_count", 0)) > 0:
                sys.exit(1)
        else:
            result = await _process_file_batch(reviewer, resolved_files, "type-check", max_workers)
            feedback.clear_progress()

            if output_file:
                if output_format == "json":
                    output_content = format_json(result)
                elif output_format == "markdown":
                    output_content = format_markdown(result.get("files", []))
                elif output_format == "html":
                    output_content = format_html(result.get("files", []), title="Batch Type Check Results")
                else:
                    output_content = _format_text_batch_summary(result, title="Batch Type Check")
                _write_output(output_file, output_content)
                feedback.success(f"Results written to {output_file}")
            else:
                if output_format == "json":
                    feedback.output_result(
                        result,
                        message=f"Type checking completed: {result['successful']}/{result['total']} files successful",
                    )
                elif output_format in ("markdown", "html"):
                    print(
                        format_markdown(result.get("files", []))
                        if output_format == "markdown"
                        else format_html(result.get("files", []), title="Batch Type Check Results")
                    )
                else:
                    feedback.success(f"Type checking completed: {result['successful']}/{result['total']} files successful")
                    print(_format_text_batch_summary(result, title="Batch Type Check"))

            if fail_on_issues:
                for file_result in result.get("files", []):
                    if int(file_result.get("error_count", 0)) > 0 or len(file_result.get("errors", []) or []) > 0:
                        sys.exit(1)
            if int(result.get("failed", 0)) > 0:
                sys.exit(1)
    finally:
        await reviewer.close()


async def docs_command(
    library: str,
    topic: str | None = None,
    mode: str = "code",
    page: int = 1,
    output_format: str = "json",
    no_cache: bool = False,
) -> None:
    """
    Get library documentation from Context7 (supports both *docs and docs commands).
    
    Uses KB-first lookup with automatic fallback to Context7 API.
    """
    feedback = get_feedback()
    feedback.format_type = output_format
    feedback.start_operation("Get Documentation")
    
    query_desc = f"{library}"
    if topic:
        query_desc += f" ({topic})"
    feedback.info(f"Fetching documentation for {query_desc}...")
    
    reviewer = ReviewerAgent()
    try:
        await reviewer.activate()
        
        result = await reviewer.run(
            "docs",
            library=library,
            topic=topic,
            mode=mode,
            page=page,
            no_cache=no_cache,
        )
        
        check_result_error(result)
        feedback.clear_progress()
        
        # Format output based on format type
        if output_format == "json":
            feedback.output_result(result, message="Documentation retrieved successfully")
        elif output_format == "markdown":
            content = result.get("content", "")
            if content:
                print(content)
            else:
                feedback.warning("No documentation content found")
        else:  # text
            content = result.get("content", "")
            if content:
                print(content)
            else:
                feedback.warning("No documentation content found")
                
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
    output_file = getattr(args, "output", None)
    
    # Backward compatibility: support 'file' attribute for single file
    single_file = getattr(args, "file", None)
    if single_file and not files:
        files = [single_file]

    try:
        if command == "review":
            fail_under = getattr(args, "fail_under", None)
            run_async_command(
                review_command(
                    file_path=single_file,
                    files=files,
                    pattern=pattern,
                    output_format=output_format,
                    max_workers=max_workers,
                    output_file=output_file,
                    fail_under=fail_under,
                )
            )
        elif command == "score":
            fail_under = getattr(args, "fail_under", None)
            run_async_command(
                score_command(
                    file_path=single_file,
                    files=files,
                    pattern=pattern,
                    output_format=output_format,
                    max_workers=max_workers,
                    output_file=output_file,
                    fail_under=fail_under,
                )
            )
        elif command == "lint":
            fail_on_issues = bool(getattr(args, "fail_on_issues", False))
            run_async_command(
                lint_command(
                    file_path=single_file,
                    files=files,
                    pattern=pattern,
                    output_format=output_format,
                    max_workers=max_workers,
                    output_file=output_file,
                    fail_on_issues=fail_on_issues,
                )
            )
        elif command == "type-check":
            fail_on_issues = bool(getattr(args, "fail_on_issues", False))
            run_async_command(
                type_check_command(
                    file_path=single_file,
                    files=files,
                    pattern=pattern,
                    output_format=output_format,
                    max_workers=max_workers,
                    output_file=output_file,
                    fail_on_issues=fail_on_issues,
                )
            )
        elif command == "report":
            feedback.start_operation("Report Generation", "Analyzing project quality...")
            formats = getattr(args, "formats", ["all"])
            if "all" in formats:
                format_type = "all"
            else:
                format_type = ",".join(formats)
            
            # Show initial progress
            feedback.running("Discovering files...", step=1, total_steps=4)
            
            reviewer = ReviewerAgent()
            result = run_async_command(
                run_report(reviewer, args.target, format_type, getattr(args, "output_dir", None))
            )
            check_result_error(result)
            feedback.clear_progress()
            
            # Extract report paths from result for better feedback
            report_paths = []
            if isinstance(result, dict):
                if "reports" in result and isinstance(result["reports"], dict):
                    # Reports is a dict like {"json": "path", "markdown": "path", ...}
                    report_paths = list(result["reports"].values())
                elif "reports" in result and isinstance(result["reports"], list):
                    report_paths = result["reports"]
                elif "data" in result and isinstance(result["data"], dict):
                    if "reports" in result["data"]:
                        if isinstance(result["data"]["reports"], dict):
                            report_paths = list(result["data"]["reports"].values())
                        elif isinstance(result["data"]["reports"], list):
                            report_paths = result["data"]["reports"]
            
            summary = {}
            if report_paths:
                summary["reports_generated"] = len(report_paths)
                if len(report_paths) <= 5:  # Only show paths if not too many
                    summary["report_files"] = report_paths
            
            feedback.output_result(result, message="Report generated successfully", warnings=None)
        elif command == "duplication":
            feedback.start_operation("Duplication Check")
            feedback.info(f"Checking for code duplication in {args.target}...")
            reviewer = ReviewerAgent()
            result = run_async_command(run_duplication(reviewer, args.target))
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
            reviewer = ReviewerAgent()
            result = run_async_command(
                run_analyze_project(
                    reviewer,
                    getattr(args, "project_root", None),
                    include_comparison=not getattr(args, "no_comparison", False),
                )
            )
            check_result_error(result)
            feedback.clear_progress()
            feedback.output_result(result, message="Project analysis completed")
        elif command == "analyze-services":
            feedback.start_operation("Service Analysis")
            feedback.info("Analyzing services...")
            services = getattr(args, "services", None)
            reviewer = ReviewerAgent()
            result = run_async_command(
                run_analyze_services(
                    reviewer,
                    services if services else None,
                    getattr(args, "project_root", None),
                    include_comparison=not getattr(args, "no_comparison", False),
                )
            )
            check_result_error(result)
            feedback.clear_progress()
            feedback.output_result(result, message="Service analysis completed")
        elif command == "docs":
            run_async_command(
                docs_command(
                    library=getattr(args, "library"),
                    topic=getattr(args, "topic", None),
                    mode=getattr(args, "mode", "code"),
                    page=getattr(args, "page", 1),
                    output_format=output_format,
                    no_cache=bool(getattr(args, "no_cache", False)),
                )
            )
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("reviewer")
            feedback.output_result(help_text)
    finally:
        # Each command manages its own agent lifecycle; nothing to close here.
        pass


async def run_report(reviewer: ReviewerAgent, target: str, format_type: str, output_dir: str | None) -> dict[str, Any]:
    try:
        await reviewer.activate()
        return await reviewer.run("report", target=target, format=format_type, output_dir=output_dir)
    finally:
        await reviewer.close()


async def run_duplication(reviewer: ReviewerAgent, target: str) -> dict[str, Any]:
    try:
        await reviewer.activate()
        return await reviewer.run("duplication", file=target)
    finally:
        await reviewer.close()


async def run_analyze_project(reviewer: ReviewerAgent, project_root: str | None, include_comparison: bool) -> dict[str, Any]:
    try:
        await reviewer.activate()
        return await reviewer.run(
            "analyze-project",
            project_root=project_root,
            include_comparison=include_comparison,
        )
    finally:
        await reviewer.close()


async def run_analyze_services(
    reviewer: ReviewerAgent,
    services: list[str] | None,
    project_root: str | None,
    include_comparison: bool,
) -> dict[str, Any]:
    try:
        await reviewer.activate()
        return await reviewer.run(
            "analyze-services",
            services=services,
            project_root=project_root,
            include_comparison=include_comparison,
        )
    finally:
        await reviewer.close()

