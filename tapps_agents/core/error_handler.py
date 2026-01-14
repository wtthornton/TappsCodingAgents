"""
Enhanced Error Handling for TappsCodingAgents.

Provides:
- Error classification
- Descriptive error messages
- Recovery suggestions
- Service availability handling
"""

from dataclasses import dataclass
from typing import Any

from .command_registry import get_registry


@dataclass
class ErrorCategory:
    """Error category with recovery suggestions."""

    name: str
    description: str
    recoverable: bool
    suggestions: list[str]
    documentation_url: str | None = None


class ErrorHandler:
    """
    Enhanced error handler with classification and recovery suggestions.
    """

    # Error categories
    COMMAND_ERROR = ErrorCategory(
        name="command_error",
        description="Command not found or invalid",
        recoverable=True,
        suggestions=[
            "Check command spelling",
            "Use 'tapps-agents <agent> help' to see available commands",
            "Try fuzzy matching suggestions",
        ],
    )

    VALIDATION_ERROR = ErrorCategory(
        name="validation_error",
        description="Input validation failed",
        recoverable=True,
        suggestions=[
            "Check required parameters",
            "Verify file paths exist",
            "Check parameter formats",
        ],
    )

    NETWORK_ERROR = ErrorCategory(
        name="network_error",
        description="Network request failed",
        recoverable=True,
        suggestions=[
            "Check internet connection",
            "Verify service URLs",
            "Retry with exponential backoff",
        ],
    )

    TIMEOUT_ERROR = ErrorCategory(
        name="timeout_error",
        description="Operation timed out",
        recoverable=True,
        suggestions=[
            "Increase timeout value",
            "Check service availability",
            "Retry operation",
        ],
    )

    SERVICE_UNAVAILABLE = ErrorCategory(
        name="service_unavailable",
        description="External service unavailable",
        recoverable=True,
        suggestions=[
            "Check service status",
            "Verify configuration",
            "Use offline mode if available",
        ],
    )

    PERMISSION_ERROR = ErrorCategory(
        name="permission_error",
        description="Permission denied",
        recoverable=False,
        suggestions=[
            "Check file permissions",
            "Verify write access",
            "Run with appropriate permissions",
        ],
    )

    CONFIGURATION_ERROR = ErrorCategory(
        name="configuration_error",
        description="Configuration invalid or missing",
        recoverable=True,
        suggestions=[
            "Run 'tapps-agents init' to set up configuration",
            "Check .tapps-agents/config.yaml",
            "Verify required settings",
        ],
    )

    @staticmethod
    def classify_error(error: Exception) -> ErrorCategory:
        """
        Classify error into category.
        
        Args:
            error: Exception to classify
            
        Returns:
            ErrorCategory
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()

        # Network errors
        if any(keyword in error_msg for keyword in ["connection", "network", "dns", "timeout"]):
            if "timeout" in error_msg:
                return ErrorHandler.TIMEOUT_ERROR
            return ErrorHandler.NETWORK_ERROR

        # Service unavailable
        if any(keyword in error_msg for keyword in ["unavailable", "503", "502", "504"]):
            return ErrorHandler.SERVICE_UNAVAILABLE

        # Permission errors
        if any(keyword in error_msg for keyword in ["permission", "access denied", "forbidden"]):
            return ErrorHandler.PERMISSION_ERROR

        # Configuration errors
        if any(keyword in error_msg for keyword in ["config", "configuration", "missing", "invalid"]):
            return ErrorHandler.CONFIGURATION_ERROR

        # Validation errors
        if any(keyword in error_msg for keyword in ["validation", "invalid", "required", "missing"]):
            return ErrorHandler.VALIDATION_ERROR

        # Command errors
        if any(keyword in error_msg for keyword in ["command", "unknown", "not found"]):
            return ErrorHandler.COMMAND_ERROR

        # Default to validation error
        return ErrorHandler.VALIDATION_ERROR

    @staticmethod
    def format_error(
        error: Exception,
        context: dict[str, Any] | None = None,
        command: str | None = None,
        agent: str | None = None,
    ) -> dict[str, Any]:
        """
        Format error with classification and suggestions.
        
        Args:
            error: Exception to format
            context: Optional context information
            command: Optional command that failed
            agent: Optional agent name
            
        Returns:
            Formatted error dictionary
        """
        category = ErrorHandler.classify_error(error)
        error_type = type(error).__name__
        error_msg = str(error)

        # Get command suggestions if it's a command error
        suggestions = category.suggestions.copy()
        if category == ErrorHandler.COMMAND_ERROR and command:
            registry = get_registry()
            cmd_suggestions = registry.get_suggestions(command, agent)
            if cmd_suggestions.get("suggestions"):
                suggestions.insert(0, f"Did you mean: {', '.join(cmd_suggestions['suggestions'])}?")

        # Build error message
        message = f"{category.description}: {error_msg}"
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            message += f" (Context: {context_str})"

        return {
            "error": True,
            "error_type": error_type,
            "error_message": message,
            "category": category.name,
            "recoverable": category.recoverable,
            "suggestions": suggestions,
            "documentation": category.documentation_url,
            "context": context or {},
        }

    @staticmethod
    def format_service_unavailable(
        service_name: str,
        error: Exception,
        fallback_available: bool = False,
    ) -> dict[str, Any]:
        """
        Format service unavailable error with fallback options.
        
        Args:
            service_name: Name of unavailable service
            error: Exception that occurred
            fallback_available: Whether fallback mode is available
            
        Returns:
            Formatted error dictionary
        """
        suggestions = [
            f"Check {service_name} service status",
            f"Verify {service_name} configuration",
        ]

        if fallback_available:
            suggestions.append(f"Use offline mode (some features may be limited)")

        return {
            "error": True,
            "error_type": "ServiceUnavailableError",
            "error_message": f"{service_name} is not available: {str(error)}",
            "category": "service_unavailable",
            "recoverable": True,
            "suggestions": suggestions,
            "service": service_name,
            "fallback_available": fallback_available,
        }

    @staticmethod
    def format_command_error(
        command: str,
        agent: str | None = None,
        available_commands: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Format command error with suggestions.
        
        Args:
            command: Unknown command
            agent: Optional agent name
            available_commands: Optional list of available commands
            
        Returns:
            Formatted error dictionary
        """
        registry = get_registry()
        suggestions_data = registry.get_suggestions(command, agent)

        error_msg = suggestions_data["message"]
        if available_commands and not suggestions_data.get("suggestions"):
            error_msg += f"\nAvailable commands: {', '.join(available_commands[:10])}"

        return {
            "error": True,
            "error_type": "CommandError",
            "error_message": error_msg,
            "category": "command_error",
            "recoverable": True,
            "suggestions": suggestions_data.get("suggestions", []),
            "available_commands": available_commands or [],
        }
