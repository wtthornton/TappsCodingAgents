"""
Centralized feedback system for CLI commands.

Provides consistent, user-friendly output with support for quiet, normal, and verbose modes.
All CLI commands should use this module instead of direct print() calls.
"""
import json
import sys
import time
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .. import __version__ as PACKAGE_VERSION


class VerbosityLevel(Enum):
    """Verbosity levels for CLI output."""
    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"


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
    
    def __init__(self):
        """Initialize feedback manager."""
        self.verbosity = FeedbackManager._verbosity
        self.format_type = FeedbackManager._format_type
        self.operation_start_time: float | None = None
        
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
            
        if self.format_type == "json":
            # JSON format - typically not used for info messages, but available
            output = {
                "type": "info",
                "message": message,
            }
            if details:
                output["details"] = details
            print(json.dumps(output), file=sys.stderr)
        else:
            # Text format
            prefix = "[INFO] " if self.verbosity == VerbosityLevel.VERBOSE else ""
            print(f"{prefix}{message}", file=sys.stderr)
            if details and self.verbosity == VerbosityLevel.VERBOSE:
                for key, value in details.items():
                    print(f"  {key}: {value}", file=sys.stderr)
    
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
            print(json.dumps(output, indent=2))
        else:
            # Text format
            print(f"[OK] {message}", file=sys.stderr)
            if summary and self.verbosity != VerbosityLevel.QUIET:
                for key, value in summary.items():
                    print(f"  {key}: {value}", file=sys.stderr)
            # Data goes to stdout for parsing
            if data and self.verbosity == VerbosityLevel.QUIET:
                print(json.dumps(data, indent=2))
    
    def warning(self, message: str, remediation: str | None = None) -> None:
        """
        Output warning message.
        
        Args:
            message: Warning message
            remediation: Optional remediation suggestion
        """
        if self.verbosity == VerbosityLevel.QUIET:
            return
            
        if self.format_type == "json":
            output = {
                "type": "warning",
                "message": message,
            }
            if remediation:
                output["remediation"] = remediation
            print(json.dumps(output), file=sys.stderr)
        else:
            # Text format
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
            print(json.dumps(output, indent=2), file=sys.stderr)
        else:
            # Text format
            print(f"[ERROR] Error: {message}", file=sys.stderr)
            if context:
                for key, value in context.items():
                    print(f"  {key}: {value}", file=sys.stderr)
            if remediation:
                print(f"  Suggestion: {remediation}", file=sys.stderr)
        
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
            
        if self.format_type == "json":
            # Progress updates typically not in JSON format
            # But if needed, output to stderr
            output = {
                "type": "progress",
                "message": message,
            }
            if percentage is not None:
                output["percentage"] = percentage
            print(json.dumps(output), file=sys.stderr)
        else:
            # Text format - use ASCII-safe characters for Windows compatibility
            from ..core.unicode_safe import safe_print, safe_format_progress_bar
            if show_progress_bar and percentage is not None:
                bar = safe_format_progress_bar(percentage, width=30)
                safe_print(f"-> {message} {bar}", file=sys.stderr, end="\r")
                sys.stderr.flush()
            else:
                safe_print(f"-> {message}", file=sys.stderr, end="\r")
                sys.stderr.flush()
    
    def clear_progress(self) -> None:
        """Clear the current progress line."""
        if self.verbosity != VerbosityLevel.QUIET:
            print("", file=sys.stderr)  # New line to clear progress
    
    def output_result(
        self,
        data: dict[str, Any] | str,
        message: str | None = None,
        warnings: list[str] | None = None,
    ) -> None:
        """
        Output final result data.
        
        Args:
            data: Result data (dict for JSON, str for text)
            message: Optional summary message
            warnings: Optional list of warnings
        """
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
    
    def start_operation(self, operation_name: str) -> None:
        """
        Start timing an operation.
        
        Args:
            operation_name: Name of the operation
        """
        self.operation_start_time = time.time()
        if self.verbosity == VerbosityLevel.VERBOSE:
            self.info(f"Starting {operation_name}...")
    
    def get_duration_ms(self) -> int | None:
        """Get operation duration in milliseconds."""
        if self.operation_start_time:
            return int((time.time() - self.operation_start_time) * 1000)
        return None


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
) -> None:
    """Output final result data."""
    get_feedback().output_result(data, message, warnings)

