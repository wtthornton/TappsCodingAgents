"""
Reviewer agent command handlers

Performance-optimized with:
- Result caching for 90%+ speedup on unchanged files
- Streaming progress for batch operations
- Async I/O for better concurrency
"""
import asyncio
import sys
import time
from pathlib import Path
from typing import Any

from ...agents.reviewer.agent import ReviewerAgent
from ...agents.reviewer.cache import get_reviewer_cache, ReviewerResultCache
from ..base import normalize_command, run_async_command
from ..feedback import get_feedback, ProgressTracker
from .common import check_result_error, format_json_output
from ..formatters import format_json, format_markdown, format_html

# Use cache version from the cache module for consistency
REVIEWER_CACHE_VERSION = ReviewerResultCache.CACHE_VERSION


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
        
        # P1 Improvement: Show linting and type checking scores with issue counts
        linting_score = scoring.get('linting_score', 0.0)
        linting_count = scoring.get('linting_issue_count', 0)
        type_score = scoring.get('type_checking_score', 0.0)
        type_count = scoring.get('type_issue_count', 0)
        
        linting_suffix = f" ({linting_count} issues)" if linting_count > 0 else ""
        type_suffix = f" ({type_count} issues)" if type_count > 0 else ""
        
        lines.append(f"  Linting: {linting_score:.1f}/10{linting_suffix}")
        lines.append(f"  Type Checking: {type_score:.1f}/10{type_suffix}")
        
        if "threshold" in result:
            lines.append(f"  Threshold: {result.get('threshold')}")
        if "passed" in result:
            lines.append(f"  Status: {'Passed' if result.get('passed') else 'Failed'}")
        
        # P1 Improvement: Show actual linting issues
        linting_issues = scoring.get('linting_issues', [])
        if linting_issues:
            lines.append("")
            lines.append(f"Linting Issues ({len(linting_issues)}):")
            for issue in linting_issues[:10]:  # Show top 10
                code = issue.get('code', '???')
                msg = issue.get('message', 'Unknown issue')
                line = issue.get('line', 0)
                lines.append(f"  Line {line}: [{code}] {msg}")
            if len(linting_issues) > 10:
                lines.append(f"  ... and {len(linting_issues) - 10} more")
        
        # P1 Improvement: Show actual type checking issues
        type_issues = scoring.get('type_issues', [])
        if type_issues:
            lines.append("")
            lines.append(f"Type Issues ({len(type_issues)}):")
            for issue in type_issues[:10]:  # Show top 10
                msg = issue.get('message', 'Unknown issue')
                line = issue.get('line', 0)
                error_code = issue.get('error_code', '')
                code_suffix = f" [{error_code}]" if error_code else ""
                lines.append(f"  Line {line}: {msg}{code_suffix}")
            if len(type_issues) > 10:
                lines.append(f"  ... and {len(type_issues) - 10} more")

    feedback = result.get("feedback") or {}
    
    # Handle feedback structure: could be instruction object or parsed feedback
    feedback_text = None
    feedback_summary = None
    
    # Check if feedback is an instruction object (Cursor Skills format)
    if isinstance(feedback, dict):
        if "instruction" in feedback:
            # Extract prompt from instruction as fallback
            instruction = feedback.get("instruction", {})
            feedback_text = instruction.get("prompt", "")
            # Try to get actual feedback if it was executed
            if "summary" in feedback:
                feedback_summary = feedback.get("summary")
            elif "feedback_text" in feedback:
                feedback_text = feedback.get("feedback_text")
        elif "summary" in feedback:
            feedback_summary = feedback.get("summary")
        elif "feedback_text" in feedback:
            feedback_text = feedback.get("feedback_text")
    
    # Parse feedback text if available
    if feedback_text and not feedback_summary:
        from ...agents.reviewer.feedback_generator import FeedbackGenerator
        parsed = FeedbackGenerator.parse_feedback_text(feedback_text)
        feedback_summary = parsed.get("summary") or feedback_text[:500]
        
        # Display structured feedback with priorities
        if parsed.get("security_concerns") or parsed.get("critical_issues") or parsed.get("improvements"):
            lines.append("")
            lines.append("Feedback:")
            if feedback_summary:
                lines.append(feedback_summary)
                lines.append("")
            
            # Security concerns (highest priority)
            if parsed.get("security_concerns"):
                lines.append("🔒 Security Concerns:")
                for concern in parsed["security_concerns"][:5]:  # Top 5
                    lines.append(f"  • {concern}")
                lines.append("")
            
            # Critical issues
            if parsed.get("critical_issues"):
                lines.append("⚠️ Critical Issues:")
                for issue in parsed["critical_issues"][:5]:  # Top 5
                    lines.append(f"  • {issue}")
                lines.append("")
            
            # Improvements
            if parsed.get("improvements"):
                lines.append("💡 Improvements:")
                for improvement in parsed["improvements"][:5]:  # Top 5
                    lines.append(f"  • {improvement}")
                lines.append("")
            
            # Style suggestions (only if no other feedback)
            if not (parsed.get("security_concerns") or parsed.get("critical_issues") or parsed.get("improvements")):
                if parsed.get("style_suggestions"):
                    lines.append("📝 Style Suggestions:")
                    for suggestion in parsed["style_suggestions"][:5]:
                        lines.append(f"  • {suggestion}")
                    lines.append("")
        else:
            # Fallback: just show summary
            if feedback_summary:
                lines.append("")
                lines.append("Feedback:")
                lines.append(feedback_summary)
    elif feedback_summary:
        # Direct summary available
        lines.append("")
        lines.append("Feedback:")
        lines.append(str(feedback_summary))

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
    verbose_output: bool = False,
):
    """
    Review code file(s) (supports both *review and review commands).
    
    Supports single file (backward compatible) or batch processing.
    """
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    from ...core.network_errors import NetworkRequiredError, NetworkOptionalError
    from ..base import handle_network_error
    
    feedback = get_feedback()
    output_format = _infer_output_format(output_format, output_file)
    feedback.format_type = output_format
    
    # Check network requirement
    requirement = CommandClassifier.get_network_requirement("reviewer", "review")
    offline_mode = False
    
    if requirement == CommandNetworkRequirement.OFFLINE:
        offline_mode = True
    elif requirement == CommandNetworkRequirement.OPTIONAL:
        # Try offline first if network unavailable
        if not NetworkDetector.is_network_available():
            offline_mode = True
            feedback.info("Network unavailable, continuing in offline mode with reduced functionality")
    else:
        # Network required - check availability
        if not NetworkDetector.is_network_available():
            try:
                raise NetworkRequiredError(
                    operation_name="reviewer review",
                    message="Network is required for this command"
                )
            except NetworkRequiredError as e:
                handle_network_error(e, format_type=output_format)
                return
    
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
    cache = get_reviewer_cache()
    
    try:
        # Activate agent (load configs, etc.)
        if feedback.verbosity.value == "verbose":
            feedback.info("Initializing ReviewerAgent...")
        await reviewer.activate(offline_mode=offline_mode)

        # Single file - use existing flow for backward compatibility
        if len(resolved_files) == 1:
            file_path_obj = resolved_files[0]
            
            # Execute review command (with caching)
            if feedback.verbosity.value == "verbose":
                feedback.info("Running code analysis...")
            
            # Check cache first
            cached_result = await cache.get_cached_result(
                file_path_obj, "review", REVIEWER_CACHE_VERSION
            )
            if cached_result is not None:
                result = cached_result
                feedback.info("Using cached result (file unchanged)")
            else:
                result = await reviewer.run("review", file=str(file_path_obj))
                check_result_error(result)
                # Cache the result
                await cache.save_result(
                    file_path_obj, "review", REVIEWER_CACHE_VERSION, result
                )
            
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
                    feedback.output_result(result, message="Review completed successfully", warnings=None, compact=not verbose_output)
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
                        compact=not verbose_output,
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

    def _discover_from_dir(root: Path, max_files: int = 200) -> list[Path]:
        """
        Discover code files from a directory.
        
        Args:
            root: Directory to search
            max_files: Maximum number of files to discover (default: 200)
            
        Returns:
            List of discovered file paths
        """
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
        matched = []
        for p in cwd.glob(pattern):
            if len(matched) >= 200:  # Limit pattern matches to prevent too many files
                break
            if p.is_file() and not _is_excluded(p):
                matched.append(p)
        resolved_files.extend(matched)
    
    # Handle explicit file list
    if files:
        for file_path in files:
            # Support passing glob patterns directly as positional args (e.g. "src/**/*.py")
            if any(ch in file_path for ch in ["*", "?", "["]):
                matched_count = 0
                for p in Path.cwd().glob(file_path):
                    if matched_count >= 200:  # Limit glob matches to prevent too many files
                        break
                    if p.is_file() and not _is_excluded(p):
                        resolved_files.append(p)
                        matched_count += 1
                continue

            path = Path(file_path)
            if not path.is_absolute():
                # Use resolve() to properly normalize path and eliminate directory duplication
                path = (Path.cwd() / path).resolve()
            if path.exists() and path.is_dir():
                resolved_files.extend(_discover_from_dir(path))
            elif path.exists():
                if path.is_file() and (path.suffix.lower() in allowed_suffixes or path.suffix == ""):
                    resolved_files.append(path)
            else:
                # Try relative to cwd (with proper resolution to eliminate duplication)
                cwd_path = (Path.cwd() / file_path).resolve()
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
    
    # Warn if too many files discovered
    if len(unique_files) > 200:
        from ..feedback import get_feedback
        feedback = get_feedback()
        feedback.warning(
            f"Large number of files discovered ({len(unique_files)}). Processing may take a while. "
            f"Consider using --pattern to target specific files or directories. "
            f"Only the first 200 files will be processed."
        )
        # Limit to 200 files to prevent connection errors
        unique_files = unique_files[:200]
    
    return unique_files


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.is_open = False
    
    def record_success(self) -> None:
        """Record successful operation."""
        self.failure_count = 0
        self.is_open = False
    
    def record_failure(self) -> None:
        """Record failure and check if circuit should open."""
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            self.last_failure_time = time.time()
    
    def should_allow(self) -> bool:
        """Check if operation should be allowed."""
        if not self.is_open:
            return True
        
        # Check if reset timeout has passed
        if self.last_failure_time:
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.reset_timeout:
                self.is_open = False
                self.failure_count = 0
                return True
        
        return False


def is_retryable_error(error: Exception) -> bool:
    """
    Check if error is retryable (connection-related).
    
    Implements error taxonomy to distinguish between:
    - Retryable: Transient issues (network timeouts, connection errors)
    - Non-retryable: Permanent issues (file not found, invalid input)
    
    Based on best practices for AI agent error handling.
    
    Args:
        error: Exception to check
        
    Returns:
        True if error is retryable (connection-related)
    """
    retryable_types = (
        ConnectionError,
        TimeoutError,
        OSError,
    )
    
    # Check for requests library errors
    try:
        import requests
        retryable_types = retryable_types + (
            requests.exceptions.RequestException,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout,
        )
    except ImportError:
        pass
    
    # Check for aiohttp errors (common in async Python)
    try:
        import aiohttp
        retryable_types = retryable_types + (
            aiohttp.ClientError,
            aiohttp.ClientConnectionError,
            aiohttp.ClientConnectorError,
            aiohttp.ServerTimeoutError,
        )
    except ImportError:
        pass
    
    error_str = str(error).lower()
    retryable_keywords = [
        "connection",
        "timeout",
        "network",
        "unreachable",
        "refused",
        "reset",
        "connection error",
        "connection failed",
        "temporary failure",
        "service unavailable",
        "rate limit",  # Rate limits are often temporary
    ]
    
    # Non-retryable keywords (permanent errors)
    non_retryable_keywords = [
        "file not found",
        "permission denied",
        "invalid",
        "malformed",
        "syntax error",
    ]
    
    # Check for non-retryable errors first
    if any(keyword in error_str for keyword in non_retryable_keywords):
        return False
    
    return (
        isinstance(error, retryable_types) or
        any(keyword in error_str for keyword in retryable_keywords)
    )


async def _process_file_batch(
    reviewer: ReviewerAgent,
    files: list[Path],
    command: str,
    max_workers: int = 4,
) -> dict[str, Any]:
    """
    Process multiple files concurrently in batches with retry logic and circuit breaker.
    
    Performance optimizations:
    - Result caching for 90%+ speedup on unchanged files
    - Circuit breaker to prevent cascading failures
    - Retry logic with exponential backoff
    
    Args:
        reviewer: ReviewerAgent instance
        files: List of file paths to process
        command: Command to run ('score', 'review', 'lint', 'type-check')
        max_workers: Maximum concurrent operations
        
    Returns:
        Dictionary with aggregated results
    """
    from ..feedback import get_feedback
    feedback = get_feedback()
    cache = get_reviewer_cache()
    
    # Configuration
    BATCH_SIZE = 10  # Process 10 files per batch
    MAX_CONCURRENT = max(1, min(max_workers, 2))  # Limit to max 2 concurrent
    BATCH_DELAY = 1.0  # Delay between batches
    FILE_DELAY = 0.2  # Small delay between individual files
    MAX_RETRIES = 3  # Maximum retry attempts for connection errors
    RETRY_BACKOFF_BASE = 2.0  # Exponential backoff base
    MAX_RETRY_BACKOFF = 10.0  # Maximum backoff time in seconds
    RETRY_TIMEOUT = 120.0  # Timeout per retry attempt (2 minutes)
    
    # Track cache statistics for this batch
    cache_hits = 0
    cache_misses = 0
    
    # Progress tracking for long operations
    total_files = len(files)
    processed_count = 0
    start_time = asyncio.get_event_loop().time()
    last_progress_update = start_time
    PROGRESS_UPDATE_INTERVAL = 5.0  # Update progress every 5 seconds for long operations
    
    # Initialize circuit breaker
    circuit_breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60.0)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    async def process_single_file(file_path: Path) -> tuple[Path, dict[str, Any]]:
        """Process a single file with caching, retry logic, circuit breaker, and semaphore limiting."""
        nonlocal cache_hits, cache_misses
        
        # Check cache first (before circuit breaker)
        cached_result = await cache.get_cached_result(
            file_path, command, REVIEWER_CACHE_VERSION
        )
        if cached_result is not None:
            cache_hits += 1
            cached_result["_from_cache"] = True
            return (file_path, cached_result)
        
        cache_misses += 1
        
        # Check circuit breaker before processing
        if not circuit_breaker.should_allow():
            return (file_path, {
                "error": "Circuit breaker open - too many failures",
                "file": str(file_path),
                "circuit_breaker": True
            })
        
        async with semaphore:
            await asyncio.sleep(FILE_DELAY)
            
            # Retry logic for connection errors with per-attempt timeout
            last_error: Exception | None = None
            RETRY_TIMEOUT = 120.0  # 2 minutes per retry attempt
            
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    # Wrap each retry attempt in a timeout to prevent hanging
                    result = await asyncio.wait_for(
                        reviewer.run(command, file=str(file_path)),
                        timeout=RETRY_TIMEOUT
                    )
                    # Ensure result is always a dict (defensive check)
                    if not isinstance(result, dict):
                        return (file_path, {
                            "error": f"Unexpected result type: {type(result).__name__}. Result: {str(result)[:200]}",
                            "file": str(file_path)
                        })
                    
                    # Success - record in circuit breaker and cache result
                    circuit_breaker.record_success()
                    
                    # Cache successful results (non-error results only)
                    if "error" not in result:
                        await cache.save_result(
                            file_path, command, REVIEWER_CACHE_VERSION, result
                        )
                    
                    return (file_path, result)
                    
                except asyncio.TimeoutError:
                    # Per-attempt timeout - treat as retryable connection issue
                    last_error = TimeoutError(f"Operation timed out after {RETRY_TIMEOUT}s")
                    if attempt < MAX_RETRIES:
                        backoff = min(RETRY_BACKOFF_BASE ** attempt, MAX_RETRY_BACKOFF)
                        if feedback.verbosity.value == "verbose":
                            feedback.info(
                                f"Retrying {file_path.name} after timeout "
                                f"(attempt {attempt + 1}/{MAX_RETRIES}, backoff {backoff:.1f}s)..."
                            )
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        circuit_breaker.record_failure()
                        return (file_path, {
                            "error": f"Operation timed out after {RETRY_TIMEOUT}s (attempt {attempt}/{MAX_RETRIES})",
                            "file": str(file_path),
                            "retryable": True,
                            "attempts": attempt,
                            "timeout": True
                        })
                    
                except Exception as e:
                    last_error = e
                    
                    # Check if error is retryable
                    if is_retryable_error(e) and attempt < MAX_RETRIES:
                        # Exponential backoff
                        backoff = min(RETRY_BACKOFF_BASE ** attempt, MAX_RETRY_BACKOFF)
                        if feedback.verbosity.value == "verbose":
                            feedback.info(
                                f"Retrying {file_path.name} after connection error "
                                f"(attempt {attempt + 1}/{MAX_RETRIES}, backoff {backoff:.1f}s)..."
                            )
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        # Non-retryable error or max retries reached
                        if is_retryable_error(e):
                            circuit_breaker.record_failure()
                        return (file_path, {
                            "error": str(e),
                            "file": str(file_path),
                            "retryable": is_retryable_error(e),
                            "attempts": attempt,
                            "error_type": type(e).__name__
                        })
            
            # All retries exhausted
            circuit_breaker.record_failure()
            return (file_path, {
                "error": f"Failed after {MAX_RETRIES} attempts: {str(last_error)}",
                "file": str(file_path),
                "retryable": True,
                "attempts": MAX_RETRIES,
                "error_type": type(last_error).__name__ if last_error else "Unknown"
            })
    
    # Process files in batches with circuit breaker protection
    all_results = []
    total_batches = (len(files) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_idx in range(total_batches):
        # Check circuit breaker before processing batch
        if not circuit_breaker.should_allow():
            remaining_count = len(files) - batch_idx * BATCH_SIZE
            feedback.warning(
                f"Circuit breaker open - skipping remaining {remaining_count} files "
                f"(too many connection failures)"
            )
            # Mark remaining files as failed
            for remaining_file in files[batch_idx * BATCH_SIZE:]:
                all_results.append((remaining_file, {
                    "error": "Circuit breaker open - skipped due to too many failures",
                    "file": str(remaining_file),
                    "circuit_breaker": True
                }))
            break
        
        start_idx = batch_idx * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(files))
        batch_files = files[start_idx:end_idx]
        
        if total_batches > 1:
            feedback.info(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_files)} files)...")
        
        # Process files in batch with limited concurrency and progress updates
        # Create tasks for the batch, but semaphore limits concurrent execution
        batch_tasks = [process_single_file(f) for f in batch_files]
        
        # Add progress tracking for long operations
        async def process_with_progress():
            """Process batch with periodic progress updates."""
            nonlocal processed_count, last_progress_update
            
            # Create a wrapper that updates progress
            async def process_and_track(task):
                result = await task
                processed_count += 1
                
                # Update progress every 5 seconds for operations >10 seconds
                current_time = asyncio.get_event_loop().time()
                elapsed = current_time - start_time
                
                if elapsed > 10.0:  # Only show progress for operations >10 seconds
                    if current_time - last_progress_update >= PROGRESS_UPDATE_INTERVAL:
                        percent = (processed_count / total_files * 100) if total_files > 0 else 0
                        feedback.info(
                            f"Reviewing files: {processed_count}/{total_files} ({percent:.1f}%) "
                            f"- {elapsed:.1f}s elapsed"
                        )
                        last_progress_update = current_time
                
                return result
            
            # Process all tasks with progress tracking
            tracked_tasks = [process_and_track(task) for task in batch_tasks]
            return await asyncio.gather(*tracked_tasks, return_exceptions=True)
        
        batch_results = await process_with_progress()
        all_results.extend(batch_results)
        
        # Delay between batches to avoid overwhelming connections
        if batch_idx < total_batches - 1:  # Don't delay after last batch
            await asyncio.sleep(BATCH_DELAY)
    
    results = all_results
    
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
        
        # Defensive check: ensure file_result is a dict
        if not isinstance(file_result, dict):
            aggregated["failed"] += 1
            aggregated["errors"].append({
                "file": str(file_path),
                "error": f"Unexpected result type: {type(file_result).__name__}. Result: {str(file_result)[:200]}"
            })
            continue
        
        if "error" in file_result:
            aggregated["failed"] += 1
            aggregated["errors"].append({
                "file": str(file_path),
                "error": file_result.get("error", "Unknown error")
            })
        else:
            aggregated["successful"] += 1
        
        file_entry: dict[str, Any] = {
            "file": str(file_path),
        }
        file_entry.update(file_result)
        aggregated["files"].append(file_entry)
    
    aggregated["total"] = len(files)
    
    # Add cache statistics to help users understand performance gains
    aggregated["_cache_stats"] = {
        "hits": cache_hits,
        "misses": cache_misses,
        "hit_rate": f"{(cache_hits / len(files) * 100):.1f}%" if files else "0.0%"
    }
    
    # Log cache statistics if verbose
    if feedback.verbosity.value == "verbose" and cache_hits > 0:
        feedback.info(
            f"Cache stats: {cache_hits} hits, {cache_misses} misses "
            f"({cache_hits / len(files) * 100:.1f}% hit rate)"
        )
    
    return aggregated


async def score_command(
    file_path: str | None = None,
    files: list[str] | None = None,
    pattern: str | None = None,
    output_format: str = "json",
    max_workers: int = 4,
    output_file: str | None = None,
    fail_under: float | None = None,
    verbose_output: bool = False,
    explain: bool = False,
):
    """
    Score code file(s) (supports both *score and score commands).
    
    Supports single file (backward compatible) or batch processing.
    """
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    
    feedback = get_feedback()
    output_format = _infer_output_format(output_format, output_file)
    feedback.format_type = output_format
    
    # Check network requirement - score is offline
    requirement = CommandClassifier.get_network_requirement("reviewer", "score")
    offline_mode = (requirement == CommandNetworkRequirement.OFFLINE)
    
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
    cache = get_reviewer_cache()
    
    try:
        await reviewer.activate(offline_mode=offline_mode)
        
        # Single file - use existing flow for backward compatibility
        if len(resolved_files) == 1:
            file_path_obj = resolved_files[0]
            
            # Check cache first
            cached_result = await cache.get_cached_result(
                file_path_obj, "score", REVIEWER_CACHE_VERSION
            )
            if cached_result is not None:
                result = cached_result
                feedback.info("Using cached result (file unchanged)")
            else:
                result = await reviewer.run("score", file=str(file_path_obj), explain=explain)
                check_result_error(result)
                # Cache the result
                await cache.save_result(
                    file_path_obj, "score", REVIEWER_CACHE_VERSION, result
                )
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
                    feedback.output_result(result, message="Scoring completed", warnings=None, compact=not verbose_output)
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
                    feedback.output_result(result, message=f"Scoring completed: {result['successful']}/{result['total']} files successful", compact=not verbose_output)
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
    verbose_output: bool = False,
    isolated: bool = False,
) -> None:
    """Run linting on file(s) with consistent async execution and output handling."""
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    
    feedback = get_feedback()
    output_format = _infer_output_format(output_format, output_file)
    feedback.format_type = output_format

    # Check network requirement - lint is offline
    requirement = CommandClassifier.get_network_requirement("reviewer", "lint")
    offline_mode = (requirement == CommandNetworkRequirement.OFFLINE)

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
    cache = get_reviewer_cache()
    
    try:
        await reviewer.activate(offline_mode=offline_mode)

        if len(resolved_files) == 1:
            file_path_obj = resolved_files[0]
            
            # Check cache first
            cached_result = await cache.get_cached_result(
                file_path_obj, "lint", REVIEWER_CACHE_VERSION
            )
            if cached_result is not None:
                result = cached_result
                feedback.info("Using cached result (file unchanged)")
            else:
                result = await reviewer.run("lint", file=str(file_path_obj), isolated=isolated)
                check_result_error(result)
                # Cache the result (only if not isolated, as isolated results may differ)
                if not isolated:
                    await cache.save_result(
                        file_path_obj, "lint", REVIEWER_CACHE_VERSION, result
                    )
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
                    feedback.output_result(result, message="Linting completed", compact=not verbose_output)
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

            # Defensive check: ensure result is a dict
            if not isinstance(result, dict):
                feedback.error(
                    f"Unexpected result type from batch processing: {type(result).__name__}",
                    error_code="invalid_result_type",
                    context={"result_type": type(result).__name__, "result_preview": str(result)[:200]},
                    exit_code=1,
                )
                return

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
                        message=f"Linting completed: {result.get('successful', 0)}/{result.get('total', 0)} files successful",
                        compact=not verbose_output,
                    )
                elif output_format in ("markdown", "html"):
                    print(
                        format_markdown(result.get("files", []))
                        if output_format == "markdown"
                        else format_html(result.get("files", []), title="Batch Linting Results")
                    )
                else:
                    feedback.success(f"Linting completed: {result.get('successful', 0)}/{result.get('total', 0)} files successful")
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
    verbose_output: bool = False,
) -> None:
    """Run type-checking on file(s) with consistent async execution and output handling."""
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    
    feedback = get_feedback()
    output_format = _infer_output_format(output_format, output_file)
    feedback.format_type = output_format

    # Check network requirement - type-check is offline
    requirement = CommandClassifier.get_network_requirement("reviewer", "type-check")
    offline_mode = (requirement == CommandNetworkRequirement.OFFLINE)

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
    cache = get_reviewer_cache()
    
    try:
        await reviewer.activate(offline_mode=offline_mode)

        if len(resolved_files) == 1:
            file_path_obj = resolved_files[0]
            
            # Check cache first
            cached_result = await cache.get_cached_result(
                file_path_obj, "type-check", REVIEWER_CACHE_VERSION
            )
            if cached_result is not None:
                result = cached_result
                feedback.info("Using cached result (file unchanged)")
            else:
                result = await reviewer.run("type-check", file=str(file_path_obj))
                check_result_error(result)
                # Cache the result
                await cache.save_result(
                    file_path_obj, "type-check", REVIEWER_CACHE_VERSION, result
                )
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
                    feedback.output_result(result, message="Type checking completed", compact=not verbose_output)
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
                        compact=not verbose_output,
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
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    
    feedback = get_feedback()
    feedback.format_type = output_format
    feedback.start_operation("Get Documentation")
    
    # Check network requirement - docs is optional (can use cache)
    requirement = CommandClassifier.get_network_requirement("reviewer", "docs")
    offline_mode = False
    
    if requirement == CommandNetworkRequirement.OPTIONAL:
        # Try offline first if network unavailable
        if not NetworkDetector.is_network_available():
            offline_mode = True
            feedback.info("Network unavailable, using cached documentation if available")
    
    query_desc = f"{library}"
    if topic:
        query_desc += f" ({topic})"
    feedback.info(f"Fetching documentation for {query_desc}...")
    
    reviewer = ReviewerAgent()
    try:
        await reviewer.activate(offline_mode=offline_mode)
        
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
            verbose_output = bool(getattr(args, "verbose_output", False))
            run_async_command(
                review_command(
                    file_path=single_file,
                    files=files,
                    pattern=pattern,
                    output_format=output_format,
                    max_workers=max_workers,
                    output_file=output_file,
                    fail_under=fail_under,
                    verbose_output=verbose_output,
                )
            )
        elif command == "score":
            fail_under = getattr(args, "fail_under", None)
            verbose_output = bool(getattr(args, "verbose_output", False))
            explain = bool(getattr(args, "explain", False))
            run_async_command(
                score_command(
                    file_path=single_file,
                    files=files,
                    pattern=pattern,
                    output_format=output_format,
                    max_workers=max_workers,
                    output_file=output_file,
                    fail_under=fail_under,
                    verbose_output=verbose_output,
                    explain=explain,
                )
            )
        elif command == "lint":
            fail_on_issues = bool(getattr(args, "fail_on_issues", False))
            verbose_output = bool(getattr(args, "verbose_output", False))
            isolated = bool(getattr(args, "isolated", False))
            run_async_command(
                lint_command(
                    file_path=single_file,
                    files=files,
                    pattern=pattern,
                    output_format=output_format,
                    max_workers=max_workers,
                    output_file=output_file,
                    fail_on_issues=fail_on_issues,
                    verbose_output=verbose_output,
                    isolated=isolated,
                )
            )
        elif command == "type-check":
            fail_on_issues = bool(getattr(args, "fail_on_issues", False))
            verbose_output = bool(getattr(args, "verbose_output", False))
            run_async_command(
                type_check_command(
                    file_path=single_file,
                    files=files,
                    pattern=pattern,
                    output_format=output_format,
                    max_workers=max_workers,
                    output_file=output_file,
                    fail_on_issues=fail_on_issues,
                    verbose_output=verbose_output,
                )
            )
        elif command == "report":
            from ..command_classifier import CommandClassifier, CommandNetworkRequirement
            from ..network_detection import NetworkDetector
            from ...core.network_errors import NetworkRequiredError
            from ..base import handle_network_error
            
            requirement = CommandClassifier.get_network_requirement("reviewer", "report")
            if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
                try:
                    raise NetworkRequiredError(
                        operation_name="reviewer report",
                        message="Network is required for this command"
                    )
                except NetworkRequiredError as e:
                    handle_network_error(e, format_type=output_format)
                    return
            
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
            
            verbose_output = bool(getattr(args, "verbose_output", False))
            feedback.output_result(result, message="Report generated successfully", warnings=None, compact=not verbose_output)
        elif command == "duplication":
            # Duplication check is offline - no network check needed
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
            # Project analysis may need network - check if required
            from ..command_classifier import CommandClassifier, CommandNetworkRequirement
            from ..network_detection import NetworkDetector
            from ...core.network_errors import NetworkRequiredError
            from ..base import handle_network_error
            
            requirement = CommandClassifier.get_network_requirement("reviewer", "analyze-project")
            if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
                try:
                    raise NetworkRequiredError(
                        operation_name="reviewer analyze-project",
                        message="Network is required for this command"
                    )
                except NetworkRequiredError as e:
                    handle_network_error(e, format_type=output_format)
                    return
            
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
            verbose_output = bool(getattr(args, "verbose_output", False))
            feedback.output_result(result, message="Project analysis completed", compact=not verbose_output)
        elif command == "analyze-services":
            # Service analysis may need network - check if required
            from ..command_classifier import CommandClassifier, CommandNetworkRequirement
            from ..network_detection import NetworkDetector
            from ...core.network_errors import NetworkRequiredError
            from ..base import handle_network_error
            
            requirement = CommandClassifier.get_network_requirement("reviewer", "analyze-services")
            if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
                try:
                    raise NetworkRequiredError(
                        operation_name="reviewer analyze-services",
                        message="Network is required for this command"
                    )
                except NetworkRequiredError as e:
                    handle_network_error(e, format_type=output_format)
                    return
            
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
            verbose_output = bool(getattr(args, "verbose_output", False))
            feedback.output_result(result, message="Service analysis completed", compact=not verbose_output)
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
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    
    # Report generation may need network for some features, but can work offline
    requirement = CommandClassifier.get_network_requirement("reviewer", "report")
    offline_mode = (requirement == CommandNetworkRequirement.OFFLINE)
    
    try:
        await reviewer.activate(offline_mode=offline_mode)
        return await reviewer.run("report", target=target, format=format_type, output_dir=output_dir)
    finally:
        await reviewer.close()


async def run_duplication(reviewer: ReviewerAgent, target: str) -> dict[str, Any]:
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    
    # Duplication check is offline (local analysis)
    requirement = CommandClassifier.get_network_requirement("reviewer", "duplication")
    offline_mode = (requirement == CommandNetworkRequirement.OFFLINE)
    
    try:
        await reviewer.activate(offline_mode=offline_mode)
        return await reviewer.run("duplication", file=target)
    finally:
        await reviewer.close()


async def run_analyze_project(reviewer: ReviewerAgent, project_root: str | None, include_comparison: bool) -> dict[str, Any]:
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    
    # Project analysis may need network for some features, but can work offline
    requirement = CommandClassifier.get_network_requirement("reviewer", "analyze-project")
    offline_mode = (requirement == CommandNetworkRequirement.OFFLINE)
    
    try:
        await reviewer.activate(offline_mode=offline_mode)
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
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    
    # Service analysis may need network for some features, but can work offline
    requirement = CommandClassifier.get_network_requirement("reviewer", "analyze-services")
    offline_mode = (requirement == CommandNetworkRequirement.OFFLINE)
    
    try:
        await reviewer.activate(offline_mode=offline_mode)
        return await reviewer.run(
            "analyze-services",
            services=services,
            project_root=project_root,
            include_comparison=include_comparison,
        )
    finally:
        await reviewer.close()

