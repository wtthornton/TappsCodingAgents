"""
Centralized feedback system for CLI commands.

Provides consistent, user-friendly output with support for quiet, normal, and verbose modes.
All CLI commands should use this module instead of direct print() calls.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# Try to import version, with fallback to importlib.metadata
try:
    from .. import __version__ as PACKAGE_VERSION
except (ImportError, AttributeError):
    # Fallback: use importlib.metadata (standard library, Python 3.8+)
    try:
        from importlib.metadata import version
        PACKAGE_VERSION = version("tapps-agents")
    except Exception:
        # Last resort: try reading from __init__.py directly
        try:
            import importlib.util
            import pathlib
            init_path = pathlib.Path(__file__).parent.parent / "__init__.py"
            if init_path.exists():
                spec = importlib.util.spec_from_file_location("tapps_agents_init", init_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    PACKAGE_VERSION = getattr(module, "__version__", "unknown")
                else:
                    PACKAGE_VERSION = "unknown"
            else:
                PACKAGE_VERSION = "unknown"
        except Exception:
            PACKAGE_VERSION = "unknown"


class VerbosityLevel(Enum):
    """Verbosity levels for CLI output."""
    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"


class ProgressMode(Enum):
    """Progress rendering modes for CLI output."""

    AUTO = "auto"
    OFF = "off"
    PLAIN = "plain"
    RICH = "rich"


def _is_interactive_tty() -> bool:
    """
    Best-effort detection of an interactive TTY.

    Notes:
    - We treat stderr as the "UI" stream for progress.
    - On CI / non-interactive sessions we default to non-animated output.
    """

    try:
        return bool(sys.stderr.isatty())
    except Exception:
        return False


def _env_truthy(name: str) -> bool:
    val = os.environ.get(name)
    if val is None:
        return False
    return val.strip().lower() not in {"0", "false", "no", "off", ""}


def _should_disable_animated_progress() -> bool:
    """
    Prefer deterministic output on CI/log files, and honor common env flags.

    References (patterns widely used by modern CLIs):
    - NO_COLOR: disable color
    - CI/GITHUB_ACTIONS: reduce animation/noise
    - TAPPS_PROGRESS=off: explicit disable
    """

    if _env_truthy("CI") or _env_truthy("GITHUB_ACTIONS"):
        return True
    if _env_truthy("TAPPS_NO_PROGRESS") or _env_truthy("NO_PROGRESS"):
        return True
    progress_env = os.environ.get("TAPPS_PROGRESS", "").strip().lower()
    if progress_env in {"off", "0", "false", "no"}:
        return True
    return False


class _PlainSpinner:
    """A tiny spinner that advances on each render call (no background thread)."""

    _frames = "|/-\\"

    def __init__(self) -> None:
        self._i = 0

    def next(self) -> str:
        ch = self._frames[self._i % len(self._frames)]
        self._i += 1
        return ch


class _RichProgressRenderer:
    """
    Rich-based renderer that supports:
    - Indeterminate spinner (Status)
    - Determinate progress bar (Progress + Live)

    This is intentionally lightweight and driven by explicit update() calls,
    so it works without threads and plays nicely with existing code paths.
    """

    def __init__(self) -> None:
        from rich.console import Console
        from rich.live import Live
        from rich.progress import (
            BarColumn,
            Progress,
            SpinnerColumn,
            TaskProgressColumn,
            TextColumn,
            TimeElapsedColumn,
            TimeRemainingColumn,
        )
        from rich.status import Status

        self._Console = Console
        self._Live = Live
        self._Progress = Progress
        self._Status = Status

        self._BarColumn = BarColumn
        self._SpinnerColumn = SpinnerColumn
        self._TextColumn = TextColumn
        self._TaskProgressColumn = TaskProgressColumn
        self._TimeElapsedColumn = TimeElapsedColumn
        self._TimeRemainingColumn = TimeRemainingColumn

        self._console = Console(stderr=True, highlight=False, soft_wrap=True)

        self._status: Status | None = None
        self._progress: Progress | None = None
        self._live: Live | None = None
        self._task_id: int | None = None

    def update(
        self,
        message: str,
        percentage: int | None,
        show_progress_bar: bool,
    ) -> None:
        if show_progress_bar and percentage is not None:
            self._stop_status()
            self._ensure_progress()
            assert self._progress is not None
            assert self._task_id is not None

            pct = max(0, min(100, int(percentage)))
            self._progress.update(self._task_id, description=message, completed=pct)
            return

        # Indeterminate / spinner-only
        self._stop_progress()
        self._ensure_status(message)
        assert self._status is not None
        self._status.update(status=message)

    def clear(self) -> None:
        self._stop_status()
        self._stop_progress()

    def _ensure_status(self, message: str) -> None:
        if self._status is None:
            self._status = self._console.status(message, spinner="dots")
            self._status.start()

    def _stop_status(self) -> None:
        if self._status is not None:
            try:
                self._status.stop()
            finally:
                self._status = None

    def _ensure_progress(self) -> None:
        if self._progress is None:
            # “2025 modern” defaults: clean, minimal, informative.
            self._progress = self._Progress(
                self._SpinnerColumn(style="cyan"),
                self._TextColumn("[bold]{task.description}"),
                self._BarColumn(bar_width=24, complete_style="cyan", finished_style="green"),
                self._TaskProgressColumn(),
                self._TimeElapsedColumn(),
                self._TimeRemainingColumn(compact=True),
                console=self._console,
            )
            self._task_id = self._progress.add_task("Working…", total=100, completed=0)

        if self._live is None:
            self._live = self._Live(self._progress, console=self._console, refresh_per_second=12)
            self._live.start()

    def _stop_progress(self) -> None:
        if self._live is not None:
            try:
                self._live.stop()
            finally:
                self._live = None

        self._progress = None
        self._task_id = None


class ProgressTracker:
    """Tracks progress for multi-step operations."""
    
    def __init__(
        self,
        total_steps: int,
        operation_name: str = "Operation",
        feedback_manager: "FeedbackManager | None" = None,
    ):
        """
        Initialize progress tracker.
        
        Args:
            total_steps: Total number of steps
            operation_name: Name of the operation
            feedback_manager: FeedbackManager instance for output
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.feedback = feedback_manager or FeedbackManager.get_instance()
        self.start_time = time.time()
        self.last_update_time = 0
        self.update_interval = 1.0  # Minimum seconds between updates
        
    def update(self, step: int | None = None, message: str | None = None) -> None:
        """
        Update progress.
        
        Args:
            step: Current step number (if None, increments by 1)
            message: Optional message for this step
        """
        if step is not None:
            self.current_step = step
        else:
            self.current_step += 1
            
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Throttle updates
        if current_time - self.last_update_time < self.update_interval:
            return
            
        self.last_update_time = current_time
        
        percentage = int((self.current_step / self.total_steps) * 100) if self.total_steps > 0 else 0
        
        # Determine if we should show progress based on elapsed time
        if elapsed < 5:
            # Quick operation - no progress bar needed
            if self.feedback.verbosity == VerbosityLevel.VERBOSE:
                self.feedback.progress(
                    f"{self.operation_name}... (step {self.current_step}/{self.total_steps})",
                    show_progress_bar=False,
                )
        elif elapsed < 30:
            # Medium operation - simple progress
            self.feedback.progress(
                f"{self.operation_name}... (step {self.current_step}/{self.total_steps})",
                show_progress_bar=False,
            )
        else:
            # Long operation - detailed progress bar
            self.feedback.progress(
                f"{self.operation_name}... (step {self.current_step}/{self.total_steps})",
                percentage=percentage,
                show_progress_bar=True,
            )
    
    def complete(self, message: str | None = None) -> None:
        """
        Mark progress as complete.
        
        Args:
            message: Optional completion message
        """
        self.current_step = self.total_steps
        elapsed = time.time() - self.start_time
        if message:
            self.feedback.success(f"{self.operation_name} completed: {message} (took {elapsed:.1f}s)")
        else:
            self.feedback.success(f"{self.operation_name} completed (took {elapsed:.1f}s)")


class FeedbackManager:
    """Manages CLI feedback output with verbosity control."""
    
    _instance: "FeedbackManager | None" = None
    _verbosity: VerbosityLevel = VerbosityLevel.NORMAL
    _format_type: str = "text"
    _progress_mode: ProgressMode = ProgressMode.AUTO
    
    def __init__(self):
        """Initialize feedback manager."""
        self.verbosity = FeedbackManager._verbosity
        self.format_type = FeedbackManager._format_type
        self.progress_mode = FeedbackManager._progress_mode
        self.operation_start_time: float | None = None

        self._plain_spinner = _PlainSpinner()
        self._rich: _RichProgressRenderer | None = None
        self._heartbeat: Any | None = None  # ProgressHeartbeat instance
        
    @classmethod
    def get_instance(cls) -> "FeedbackManager":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def set_verbosity(cls, verbosity: VerbosityLevel) -> None:
        """Set global verbosity level."""
        cls._verbosity = verbosity
        if cls._instance:
            cls._instance.verbosity = verbosity
    
    @classmethod
    def set_format(cls, format_type: str) -> None:
        """Set global output format."""
        cls._format_type = format_type
        if cls._instance:
            cls._instance.format_type = format_type

    @classmethod
    def set_progress_mode(cls, progress_mode: ProgressMode) -> None:
        """Set global progress rendering mode."""
        cls._progress_mode = progress_mode
        if cls._instance:
            cls._instance.progress_mode = progress_mode
    
    @classmethod
    def get_verbosity(cls) -> VerbosityLevel:
        """Get current verbosity level."""
        return cls._verbosity
    
    def info(self, message: str, details: dict[str, Any] | None = None) -> None:
        """
        Output informational message.
        
        Args:
            message: Message text
            details: Optional additional details
        """
        if self.verbosity == VerbosityLevel.QUIET:
            return
            
        # Status messages always go to stderr as plain text (even in JSON mode)
        # This prevents PowerShell from trying to parse JSON status messages
        # Only final results go to stdout as JSON
        prefix = "[INFO] " if self.verbosity == VerbosityLevel.VERBOSE else ""
        print(f"{prefix}{message}", file=sys.stderr)
        if details and self.verbosity == VerbosityLevel.VERBOSE:
            for key, value in details.items():
                print(f"  {key}: {value}", file=sys.stderr)
    
    def _stop_heartbeat(self) -> None:
        """Stop the heartbeat if it's running."""
        if self._heartbeat:
            try:
                self._heartbeat.stop()
            except Exception:
                pass
            finally:
                self._heartbeat = None
    
    def success(
        self,
        message: str,
        data: dict[str, Any] | None = None,
        summary: dict[str, Any] | None = None,
    ) -> None:
        """
        Output success message.
        
        Args:
            message: Success message
            data: Optional result data
            summary: Optional summary metrics
        """
        if self.verbosity == VerbosityLevel.QUIET and data is None:
            return
            
        # Stop heartbeat when operation completes
        self._stop_heartbeat()
        
        # Calculate duration
        duration_str = ""
        if self.operation_start_time:
            duration = time.time() - self.operation_start_time
            if duration < 1:
                duration_str = f" ({duration*1000:.0f}ms)"
            elif duration < 60:
                duration_str = f" ({duration:.1f}s)"
            else:
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                duration_str = f" ({minutes}m {seconds}s)"
        
        if self.format_type == "json":
            output = {
                "success": True,
                "message": message,
            }
            if data:
                output["data"] = data
            if summary:
                output["summary"] = summary
            if self.operation_start_time:
                duration_ms = int((time.time() - self.operation_start_time) * 1000)
                output["metadata"] = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "duration_ms": duration_ms,
                    "version": PACKAGE_VERSION,
                }
            # Show success indicator to stderr, then JSON result to stdout
            if self.verbosity != VerbosityLevel.QUIET:
                print(f"[SUCCESS] {message}{duration_str}", file=sys.stderr)
            print(json.dumps(output, indent=2), file=sys.stdout)
            sys.stdout.flush()
        else:
            # Text format
            print(f"[SUCCESS] {message}{duration_str}", file=sys.stderr)
            if summary and self.verbosity != VerbosityLevel.QUIET:
                for key, value in summary.items():
                    print(f"  {key}: {value}", file=sys.stderr)
            # Data goes to stdout for parsing (only in quiet mode or if explicitly requested)
            if data and self.verbosity == VerbosityLevel.QUIET:
                print(json.dumps(data, indent=2), file=sys.stdout)
                sys.stdout.flush()
    
    def warning(self, message: str, remediation: str | None = None) -> None:
        """
        Output warning message.
        
        Args:
            message: Warning message
            remediation: Optional remediation suggestion
        """
        if self.verbosity == VerbosityLevel.QUIET:
            return
            
        # Warnings always go to stderr as plain text (even in JSON mode)
        print(f"[WARN] Warning: {message}", file=sys.stderr)
        if remediation:
            print(f"  Suggestion: {remediation}", file=sys.stderr)
    
    def error(
        self,
        message: str,
        error_code: str = "error",
        context: dict[str, Any] | None = None,
        remediation: str | None = None,
        exit_code: int = 1,
    ) -> None:
        """
        Output error message and exit.
        
        Args:
            message: Error message
            error_code: Error code identifier
            context: Optional context details
            remediation: Optional remediation suggestion
            exit_code: Exit code to use
        """
        # Stop heartbeat on error
        self._stop_heartbeat()
        
        # Enhanced diagnostics for path-related errors
        is_path_error = (
            "path" in error_code.lower() or
            "path.relative()" in message or
            "relative path" in message.lower() or
            "absolute path" in message.lower()
        )
        
        # Errors always go to stderr as plain text for visibility
        # In JSON mode, also output structured error to stdout for parsing
        print(f"[ERROR] {error_code}: {message}", file=sys.stderr)
        
        # Enhanced context display for path errors
        if context:
            if is_path_error:
                print("\nPath Error Details:", file=sys.stderr)
                # Show received path if available
                if "received_path" in context or "path" in context:
                    received = context.get("received_path") or context.get("path", "unknown")
                    print(f"  Received: {received}", file=sys.stderr)
                # Show project root if available
                if "project_root" in context:
                    print(f"  Project root: {context['project_root']}", file=sys.stderr)
                # Show expected format
                if "expected_format" in context:
                    print(f"  Expected: {context['expected_format']}", file=sys.stderr)
                # Show other context
                for key, value in context.items():
                    if key not in ("received_path", "path", "project_root", "expected_format"):
                        print(f"  {key}: {value}", file=sys.stderr)
            else:
                # Standard context display
                for key, value in context.items():
                    print(f"  {key}: {value}", file=sys.stderr)
        
        if remediation:
            print(f"  Suggestion: {remediation}", file=sys.stderr)
        
        # Additional path error guidance
        if is_path_error and not remediation:
            print("\nPath Error Guidance:", file=sys.stderr)
            print("  • Use relative paths: 'src/file.py' instead of absolute paths", file=sys.stderr)
            print("  • Run commands from project root directory", file=sys.stderr)
            print("  • Paths are automatically normalized - try again", file=sys.stderr)
        
        if self.format_type == "json":
            output = {
                "success": False,
                "error": {
                    "code": error_code,
                    "message": message,
                },
            }
            if context:
                output["error"]["context"] = context
            if remediation:
                output["error"]["remediation"] = remediation
            print(json.dumps(output, indent=2), file=sys.stdout)
            sys.stdout.flush()
        
        sys.exit(exit_code)
    
    def progress(
        self,
        message: str,
        percentage: int | None = None,
        show_progress_bar: bool = False,
    ) -> None:
        """
        Output progress message.
        
        Args:
            message: Progress message
            percentage: Optional percentage (0-100)
            show_progress_bar: Whether to show progress bar
        """
        if self.verbosity == VerbosityLevel.QUIET:
            return
            
        # Progress updates always go to stderr as plain text (even in JSON mode)
        # This prevents PowerShell from trying to parse JSON progress messages
        # Only final results go to stdout as JSON
        mode = self._resolve_progress_mode()
        if mode == ProgressMode.OFF:
            return

        if mode == ProgressMode.RICH:
            try:
                if self._rich is None:
                    self._rich = _RichProgressRenderer()
                self._rich.update(message, percentage, show_progress_bar)
                return
            except Exception:
                # Never fail a command due to progress rendering.
                self._rich = None
                mode = ProgressMode.PLAIN

        # Plain text fallback - use ASCII-safe characters for Windows compatibility
        from ..core.unicode_safe import safe_print, safe_format_progress_bar

        spinner = self._plain_spinner.next()
        if show_progress_bar and percentage is not None:
            bar = safe_format_progress_bar(percentage, width=24)
            safe_print(f"{spinner} {message} {bar}", file=sys.stderr, end="\r")
            sys.stderr.flush()
        else:
            safe_print(f"{spinner} {message}", file=sys.stderr, end="\r")
            sys.stderr.flush()
    
    def clear_progress(self) -> None:
        """Clear the current progress line."""
        if self.verbosity != VerbosityLevel.QUIET:
            if self._rich is not None:
                try:
                    self._rich.clear()
                except Exception:
                    pass
                finally:
                    self._rich = None
            print("", file=sys.stderr)  # New line to clear progress

    def _resolve_progress_mode(self) -> ProgressMode:
        """
        Decide which progress renderer to use for this invocation.

        Rules:
        - JSON output: keep progress as JSON events (handled earlier)
        - Quiet: already handled earlier
        - OFF: explicit disable
        - AUTO: Rich when interactive TTY and not on CI / explicitly disabled
        """

        mode = self.progress_mode
        if mode == ProgressMode.AUTO:
            if not _is_interactive_tty() or _should_disable_animated_progress():
                return ProgressMode.PLAIN
            return ProgressMode.RICH
        return mode
    
    def output_result(
        self,
        data: dict[str, Any] | str,
        message: str | None = None,
        warnings: list[str] | None = None,
        compact: bool = True,  # Default to compact mode to prevent Cursor crashes
        **kwargs: Any,  # Accept additional kwargs for backward compatibility
    ) -> None:
        """
        Output final result data.
        
        Args:
            data: Result data (dict for JSON, str for text)
            message: Optional summary message
            warnings: Optional list of warnings
            compact: If True (default), remove verbose debug data to prevent large output
        """
        # Apply output compaction to prevent overwhelming Cursor's terminal
        # Large outputs can cause Cursor to crash with "Connection Error"
        if compact and isinstance(data, dict):
            from .output_compactor import clean_debug_output, limit_output_size
            data = clean_debug_output(data)
            data = limit_output_size(data)
        
        if self.format_type == "json":
            output: dict[str, Any] = {
                "success": True,
            }
            if message:
                output["message"] = message
            if isinstance(data, dict):
                output["data"] = data
            else:
                output["data"] = {"content": data}
            if warnings:
                output["warnings"] = warnings
            if self.operation_start_time:
                duration_ms = int((time.time() - self.operation_start_time) * 1000)
                output["metadata"] = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "duration_ms": duration_ms,
                    "version": PACKAGE_VERSION,
                }
            
            # Issue 8 Fix: Detect instruction objects and add Cursor AI execution directive
            # When an instruction object is present, add clear directives for Cursor AI
            data_dict = output.get("data", {})
            if isinstance(data_dict, dict) and "instruction" in data_dict:
                instruction = data_dict.get("instruction", {})
                
                # Extract file path - handle different instruction types:
                # 1. TestGenerationInstruction: target_file (test file path for tester instructions)
                # 2. CodeGenerationInstruction: file_path
                # 3. GenericInstruction: parameters.file_path
                # 4. Tester agent result: test_file (test file path, not source)
                # 5. Fallback: file from data_dict
                # Note: For tester instructions, target_file points to test file (not source file)
                # TODO: Store source file path in tester agent result for better traceability
                file_path = (
                    instruction.get("target_file") or  # TestGenerationInstruction (test file)
                    instruction.get("file_path") or  # CodeGenerationInstruction
                    data_dict.get("test_file") or  # Tester agent result (test file)
                    instruction.get("parameters", {}).get("file_path") or  # GenericInstruction
                    data_dict.get("file") or  # Fallback
                    "unknown"
                )
                command = instruction.get("command", "improve")
                agent_name = instruction.get("agent_name", "improver")
                
                # Print clear text directive to stderr BEFORE JSON (Cursor AI sees this in chat)
                # This helps Cursor AI recognize that it should execute the instruction
                print("\n" + "=" * 80, file=sys.stderr)
                print("⚠️  CURSOR AI: EXECUTION REQUIRED", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                print(f"\nThis command returned an instruction object that YOU MUST EXECUTE.", file=sys.stderr)
                print(f"\nDO NOT just return this JSON - you must:", file=sys.stderr)
                print(f"  1. Read the file: {file_path}", file=sys.stderr)
                print(f"  2. Extract the 'prompt' field from the instruction object below", file=sys.stderr)
                print(f"  3. Use that prompt as your directive to improve/refactor/optimize the code", file=sys.stderr)
                print(f"  4. Actually edit the file with improvements", file=sys.stderr)
                print(f"  5. Explain what improvements you made and why", file=sys.stderr)
                print(f"\nThe instruction is in: data.instruction.prompt", file=sys.stderr)
                print(f"Execute using: @{agent_name} *{command} or follow the prompt directly.", file=sys.stderr)
                print("=" * 80 + "\n", file=sys.stderr)
                sys.stderr.flush()
                
                # Also add execution directive in JSON for programmatic use
                output["_cursor_execution_directive"] = {
                    "action": "execute_instruction",
                    "description": "This result contains an instruction object that must be executed. DO NOT just return this JSON - you must execute the instruction by improving the code.",
                    "steps": [
                        f"1. Read the file: {file_path}",
                        "2. Extract the 'prompt' field from data.instruction as your improvement directive",
                        "3. Actually improve/refactor/optimize the code by editing the file according to the prompt",
                        "4. Apply all improvements (best practices, type hints, documentation, etc.)",
                        "5. Explain what improvements you made and why",
                    ],
                    "critical": "DO NOT just return this instruction object - you must execute it by improving the code!",
                }
            
            # JSON output always goes to stdout
            print(json.dumps(output, indent=2), file=sys.stdout)
            sys.stdout.flush()
        else:
            # Text format
            if message and self.verbosity != VerbosityLevel.QUIET:
                print(f"\n{message}", file=sys.stderr)
                sys.stderr.flush()
            if warnings and self.verbosity != VerbosityLevel.QUIET:
                for warning in warnings:
                    print(f"[WARN] {warning}", file=sys.stderr)
                sys.stderr.flush()
            # Data goes to stdout
            if isinstance(data, dict):
                # For text mode, format dict nicely
                if self.verbosity == VerbosityLevel.QUIET:
                    # In quiet mode, just output minimal data
                    print(json.dumps(data, indent=2), file=sys.stdout)
                else:
                    # Format for readability
                    for key, value in data.items():
                        if isinstance(value, (dict, list)):
                            print(f"{key}:", file=sys.stdout)
                            print(json.dumps(value, indent=2), file=sys.stdout)
                        else:
                            print(f"{key}: {value}", file=sys.stdout)
            else:
                print(data, file=sys.stdout)
            sys.stdout.flush()
    
    def start_operation(self, operation_name: str, description: str | None = None) -> None:
        """
        Start timing an operation and optionally start a heartbeat.
        
        Args:
            operation_name: Name of the operation
            description: Optional description of what the operation does
        """
        self.operation_start_time = time.time()
        
        # Always show clear START indicator (unless quiet mode)
        if self.verbosity != VerbosityLevel.QUIET:
            if description:
                self.info(f"[START] {operation_name} - {description}")
            else:
                self.info(f"[START] {operation_name}...")
        
        # Start heartbeat for long-running operations (after 2 seconds)
        if self.verbosity != VerbosityLevel.QUIET:
            try:
                from .progress_heartbeat import ProgressHeartbeat
                self._heartbeat = ProgressHeartbeat(
                    message=f"{operation_name}...",
                    start_delay=2.0,
                    update_interval=1.0,
                    feedback_manager=self,
                )
                self._heartbeat.start()
            except Exception:
                # Don't fail if heartbeat can't start
                self._heartbeat = None
    
    def get_duration_ms(self) -> int | None:
        """Get operation duration in milliseconds."""
        if self.operation_start_time:
            return int((time.time() - self.operation_start_time) * 1000)
        return None
    
    def running(self, message: str, step: int | None = None, total_steps: int | None = None) -> None:
        """
        Output running status message.
        
        Args:
            message: Running status message
            step: Current step number (optional)
            total_steps: Total number of steps (optional)
        """
        if self.verbosity == VerbosityLevel.QUIET:
            return
        
        # Format step information if provided
        step_info = ""
        if step is not None and total_steps is not None:
            step_info = f" (step {step}/{total_steps})"
        elif step is not None:
            step_info = f" (step {step})"
        
        # Running status always goes to stderr as plain text
        print(f"[RUNNING] {message}{step_info}", file=sys.stderr)


def suggest_simple_mode(
    task_type: str,
    description: str | None = None,
    file_path: str | None = None,
) -> None:
    """
    Suggest using @simple-mode for better outcomes.
    
    Call this at the start of CLI commands that could benefit from workflow orchestration.
    
    Args:
        task_type: Type of task - "build", "fix", "review", "test", "refactor"
        description: Optional description for the task
        file_path: Optional file path for the task
    """
    feedback = FeedbackManager.get_instance()
    
    # Don't show in quiet mode
    if feedback.verbosity == VerbosityLevel.QUIET:
        return
    
    # Build the suggestion message
    commands = {
        "build": f'@simple-mode *build "{description or "your feature description"}"',
        "implement": f'@simple-mode *build "{description or "your feature description"}"',
        "fix": f'@simple-mode *fix {file_path or "<file>"} "{description or "error description"}"',
        "debug": f'@simple-mode *fix {file_path or "<file>"} "{description or "error description"}"',
        "review": f'@simple-mode *review {file_path or "<file>"}',
        "test": f'@simple-mode *test {file_path or "<file>"}',
        "refactor": f'@simple-mode *refactor {file_path or "<file>"}',
    }
    
    simple_mode_cmd = commands.get(task_type, f'@simple-mode *build "{description or "your task"}"')
    
    # Print tip box
    print(file=sys.stderr)
    print("╭" + "─" * 68 + "╮", file=sys.stderr)
    print("│  TIP: For better outcomes, use @simple-mode in Cursor IDE          │", file=sys.stderr)
    print("│                                                                    │", file=sys.stderr)
    # Truncate command if too long
    if len(simple_mode_cmd) > 60:
        display_cmd = simple_mode_cmd[:57] + "..."
    else:
        display_cmd = simple_mode_cmd
    print(f"│    {display_cmd:<62} │", file=sys.stderr)
    print("│                                                                    │", file=sys.stderr)
    print("│  This orchestrates a complete workflow with quality gates.        │", file=sys.stderr)
    print("╰" + "─" * 68 + "╯", file=sys.stderr)
    print(file=sys.stderr)


# Convenience functions for easy access
def get_feedback() -> FeedbackManager:
    """Get the feedback manager instance."""
    return FeedbackManager.get_instance()


def info(message: str, details: dict[str, Any] | None = None) -> None:
    """Output informational message."""
    get_feedback().info(message, details)


def success(
    message: str,
    data: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
) -> None:
    """Output success message."""
    get_feedback().success(message, data, summary)


def warning(message: str, remediation: str | None = None) -> None:
    """Output warning message."""
    get_feedback().warning(message, remediation)


def error(
    message: str,
    error_code: str = "error",
    context: dict[str, Any] | None = None,
    remediation: str | None = None,
    exit_code: int = 1,
) -> None:
    """Output error message and exit."""
    get_feedback().error(message, error_code, context, remediation, exit_code)


def progress(
    message: str,
    percentage: int | None = None,
    show_progress_bar: bool = False,
) -> None:
    """Output progress message."""
    get_feedback().progress(message, percentage, show_progress_bar)


def clear_progress() -> None:
    """Clear the current progress line."""
    get_feedback().clear_progress()


def output_result(
    data: dict[str, Any] | str,
    message: str | None = None,
    warnings: list[str] | None = None,
    compact: bool = True,
) -> None:
    """Output final result data."""
    get_feedback().output_result(data, message, warnings, compact=compact)

