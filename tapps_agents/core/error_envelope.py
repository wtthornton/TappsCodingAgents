"""
Error envelope system for consistent error handling across agents and workflows.

Epic 7 / Story 7.2: Robust Error Handling
"""

import re
from dataclasses import dataclass
from typing import Any

from .exceptions import (
    AgentError,
    AgentFileNotFoundError,
    ConfigurationError,
    Context7UnavailableError,
    FileOperationError,
    MALDisabledInCursorModeError,
    MALError,
    WorkflowExecutionError,
)


@dataclass
class ErrorEnvelope:
    """
    Standard error envelope for agent results and workflow step failures.
    
    Provides machine-readable fields and human-readable messages with
    correlation identifiers for traceability.
    """

    code: str
    message: str
    category: str
    details: dict[str, Any] | None = None
    workflow_id: str | None = None
    step_id: str | None = None
    agent: str | None = None
    correlation_id: str | None = None
    recoverable: bool = False
    retry_after: int | None = None  # seconds

    def to_dict(self) -> dict[str, Any]:
        """Convert error envelope to dictionary."""
        result: dict[str, Any] = {
            "error": {
                "code": self.code,
                "message": self.message,
                "category": self.category,
            }
        }

        if self.details:
            result["error"]["details"] = self.details

        if self.workflow_id:
            result["workflow_id"] = self.workflow_id
        if self.step_id:
            result["step_id"] = self.step_id
        if self.agent:
            result["agent"] = self.agent
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id

        if self.recoverable:
            result["error"]["recoverable"] = True
        if self.retry_after:
            result["error"]["retry_after"] = self.retry_after

        return result

    def to_user_message(self) -> str:
        """
        Generate user-friendly error message with actionable guidance.
        
        Returns:
            Human-readable error message with next steps
        """
        parts = [self.message]

        if self.recoverable:
            parts.append("This error may be recoverable.")
            if self.retry_after:
                parts.append(f"You can retry after {self.retry_after} seconds.")

        # Add category-specific guidance
        guidance = self._get_category_guidance()
        if guidance:
            parts.append(guidance)

        # Add correlation info for debugging
        if self.workflow_id or self.step_id:
            correlation_parts = []
            if self.workflow_id:
                correlation_parts.append(f"workflow_id={self.workflow_id}")
            if self.step_id:
                correlation_parts.append(f"step_id={self.step_id}")
            if correlation_parts:
                parts.append(f"Reference: {', '.join(correlation_parts)}")

        return " ".join(parts)

    def _get_category_guidance(self) -> str | None:
        """Get category-specific guidance message."""
        guidance_map = {
            "configuration": "Check your configuration file (.tapps-agents/config.yaml) and environment variables.",
            "external_dependency": "Verify that external services are available and credentials are correct.",
            "validation": "Review the input parameters and ensure they meet the required format.",
            "execution": "Check logs for detailed error information. This may indicate a bug or unexpected condition.",
            "permission": "Verify file permissions and that you have access to the required resources.",
            "timeout": "The operation took too long. Consider increasing timeout settings or optimizing the operation.",
        }
        return guidance_map.get(self.category)


class ErrorEnvelopeBuilder:
    """Helper class for building error envelopes from exceptions and errors."""

    @staticmethod
    def from_exception(
        exc: Exception,
        workflow_id: str | None = None,
        step_id: str | None = None,
        agent: str | None = None,
        correlation_id: str | None = None,
    ) -> ErrorEnvelope:
        """
        Create error envelope from an exception.

        Args:
            exc: Exception to convert
            workflow_id: Optional workflow ID for correlation
            step_id: Optional step ID for correlation
            agent: Optional agent name for correlation
            correlation_id: Optional correlation ID

        Returns:
            ErrorEnvelope instance
        """
        # Determine error category and code
        category, code = ErrorEnvelopeBuilder._categorize_exception(exc)

        # Sanitize error message (remove secrets)
        message = ErrorEnvelopeBuilder._sanitize_message(str(exc))

        # Determine if error is recoverable
        recoverable = ErrorEnvelopeBuilder._is_recoverable(exc)

        return ErrorEnvelope(
            code=code,
            message=message,
            category=category,
            workflow_id=workflow_id,
            step_id=step_id,
            agent=agent,
            correlation_id=correlation_id,
            recoverable=recoverable,
        )

    @staticmethod
    def from_dict(
        error_dict: dict[str, Any],
        workflow_id: str | None = None,
        step_id: str | None = None,
        agent: str | None = None,
    ) -> ErrorEnvelope:
        """
        Create error envelope from a dictionary (e.g., from agent result).

        Args:
            error_dict: Dictionary containing error information
            workflow_id: Optional workflow ID for correlation
            step_id: Optional step ID for correlation
            agent: Optional agent name for correlation

        Returns:
            ErrorEnvelope instance
        """
        error_info = error_dict.get("error", error_dict)

        code = error_info.get("code", "unknown_error")
        message = ErrorEnvelopeBuilder._sanitize_message(
            error_info.get("message", "An unknown error occurred")
        )
        category = error_info.get("category", "execution")

        return ErrorEnvelope(
            code=code,
            message=message,
            category=category,
            details=error_info.get("details"),
            workflow_id=workflow_id or error_info.get("workflow_id"),
            step_id=step_id or error_info.get("step_id"),
            agent=agent or error_info.get("agent"),
            correlation_id=error_info.get("correlation_id"),
            recoverable=error_info.get("recoverable", False),
            retry_after=error_info.get("retry_after"),
        )

    @staticmethod
    def _categorize_exception(exc: Exception) -> tuple[str, str]:
        """
        Categorize exception and generate error code.

        Returns:
            Tuple of (category, code)
        """
        if isinstance(exc, ConfigurationError):
            return ("configuration", "config_error")
        elif isinstance(exc, Context7UnavailableError):
            return ("external_dependency", "context7_unavailable")
        elif isinstance(exc, MALDisabledInCursorModeError):
            return ("configuration", "mal_disabled_cursor_mode")
        elif isinstance(exc, WorkflowExecutionError):
            return ("execution", "workflow_execution_error")
        elif isinstance(exc, AgentError):
            return ("execution", "agent_error")
        elif isinstance(exc, AgentFileNotFoundError):
            # Check custom exception before FileOperationError (its parent)
            return ("validation", "file_not_found")
        elif isinstance(exc, FileOperationError):
            return ("permission", "file_operation_error")
        elif isinstance(exc, MALError):
            return ("external_dependency", "mal_error")
        elif isinstance(exc, TimeoutError):
            return ("timeout", "timeout_error")
        elif isinstance(exc, PermissionError):
            return ("permission", "permission_error")
        elif isinstance(exc, ValueError):
            return ("validation", "validation_error")
        elif isinstance(exc, FileNotFoundError):
            # Handle built-in FileNotFoundError (from stdlib)
            return ("validation", "file_not_found")
        else:
            return ("execution", "unknown_error")

    @staticmethod
    def _sanitize_message(message: str) -> str:
        """
        Sanitize error message to remove secrets and sensitive information.

        Args:
            message: Original error message

        Returns:
            Sanitized message
        """
        # Redact API keys (common patterns: sk-..., pk-..., api_key=..., API key: ...)
        message = re.sub(
            r"\b(sk|pk|api_key|apikey)=[^\s&]+",
            r"\1=***REDACTED***",
            message,
            flags=re.IGNORECASE,
        )
        message = re.sub(
            r"\b(api\s+key|api_key|apikey):\s*[A-Za-z0-9_-]{10,}",
            r"\1: ***REDACTED***",
            message,
            flags=re.IGNORECASE,
        )
        message = re.sub(
            r"\b(sk|pk)-[A-Za-z0-9]{20,}",
            r"\1-***REDACTED***",
            message,
            flags=re.IGNORECASE,
        )

        # Redact passwords
        message = re.sub(
            r"\b(password|pwd|passwd)=[^\s&]+",
            r"\1=***REDACTED***",
            message,
            flags=re.IGNORECASE,
        )
        message = re.sub(
            r"\b(password|pwd|passwd):\s*[^\s]+",
            r"\1: ***REDACTED***",
            message,
            flags=re.IGNORECASE,
        )

        # Redact tokens
        message = re.sub(
            r"\b(token|auth|bearer)\s+[A-Za-z0-9_-]{20,}",
            r"\1 ***REDACTED***",
            message,
            flags=re.IGNORECASE,
        )
        message = re.sub(
            r"\b(token|auth|bearer):\s*[A-Za-z0-9_-]{20,}",
            r"\1: ***REDACTED***",
            message,
            flags=re.IGNORECASE,
        )

        # Redact file paths that might contain usernames (basic heuristic)
        # This is conservative - only redacts paths with common username patterns
        message = re.sub(
            r"/home/[^/\s]+|C:\\Users\\[^\\\s]+",
            r"***REDACTED_PATH***",
            message,
            flags=re.IGNORECASE,
        )

        return message

    @staticmethod
    def _is_recoverable(exc: Exception) -> bool:
        """
        Determine if an exception represents a recoverable error.

        Args:
            exc: Exception to check

        Returns:
            True if error is recoverable, False otherwise
        """
        # Configuration errors are often recoverable (fix config and retry)
        if isinstance(exc, ConfigurationError):
            return True

        # External dependency errors may be recoverable (service may come back)
        if isinstance(exc, (Context7UnavailableError, MALError)):
            return True

        # Timeout errors are often recoverable
        if isinstance(exc, TimeoutError):
            return True

        # Permission errors may be recoverable (fix permissions)
        if isinstance(exc, PermissionError):
            return True

        # File not found may be recoverable (create file)
        # Handle both custom and built-in FileNotFoundError
        if isinstance(exc, (AgentFileNotFoundError, FileNotFoundError)):
            return True

        # Most other errors are not recoverable without code changes
        return False


def create_error_result(
    error: Exception | str | dict[str, Any],
    workflow_id: str | None = None,
    step_id: str | None = None,
    agent: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a standardized error result dictionary.

    This is a convenience function for agents to return structured errors.

    Args:
        error: Exception, error message string, or error dictionary
        workflow_id: Optional workflow ID for correlation
        step_id: Optional step ID for correlation
        agent: Optional agent name for correlation
        correlation_id: Optional correlation ID

    Returns:
        Dictionary with error envelope and success=False
    """
    if isinstance(error, Exception):
        envelope = ErrorEnvelopeBuilder.from_exception(
            error,
            workflow_id=workflow_id,
            step_id=step_id,
            agent=agent,
            correlation_id=correlation_id,
        )
    elif isinstance(error, dict):
        envelope = ErrorEnvelopeBuilder.from_dict(
            error,
            workflow_id=workflow_id,
            step_id=step_id,
            agent=agent,
        )
    else:
        # String error message
        envelope = ErrorEnvelope(
            code="error",
            message=ErrorEnvelopeBuilder._sanitize_message(str(error)),
            category="execution",
            workflow_id=workflow_id,
            step_id=step_id,
            agent=agent,
            correlation_id=correlation_id,
        )

    result = envelope.to_dict()
    result["success"] = False
    return result
