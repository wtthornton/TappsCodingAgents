"""
Structured network error classes following Cursor CLI 2025 patterns.

These error classes provide:
- UUID request IDs matching Cursor CLI format
- Operation context for debugging
- Structured error format compatible with Cursor CLI JSON output
- Actionable guidance for users
"""
import uuid
from typing import Any


class NetworkError(Exception):
    """Base class for network errors following Cursor CLI error patterns.
    
    Matches Cursor CLI 2025 error format with:
    - UUID request IDs
    - Operation context
    - Structured error format
    - Actionable guidance
    """
    
    def __init__(
        self,
        operation_name: str,
        request_id: str | None = None,
        session_id: str | None = None,
        original_error: Exception | None = None,
        details: dict[str, Any] | None = None,
        message: str | None = None,
    ):
        """Initialize network error.
        
        Args:
            operation_name: Name of the operation that failed
            request_id: Optional request ID (UUID format). Auto-generated if not provided.
            session_id: Optional session ID for correlation
            original_error: Original exception that caused this error
            details: Additional error details dictionary
            message: Optional custom error message (overrides default message building)
        """
        self.operation_name = operation_name
        self.request_id = request_id or str(uuid.uuid4())
        self.session_id = session_id
        self.original_error = original_error
        self.details = details or {}
        
        # Build message
        if message:
            error_message = message
        else:
            error_message = self._build_message()
        
        super().__init__(error_message)
    
    def _build_message(self) -> str:
        """Build user-friendly error message matching Cursor CLI format."""
        parts = ["Connection Error"]
        parts.append(f"Connection failed during '{self.operation_name}' operation.")
        
        if self.original_error:
            parts.append(f"Error: {str(self.original_error)}")
        
        parts.append(f"Request ID: {self.request_id}")
        
        if self.session_id:
            parts.append(f"Session ID: {self.session_id}")
        
        parts.append("\nIf the problem persists, please check your internet connection or VPN.")
        
        return "\n".join(parts)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output (Cursor CLI format).
        
        Matches Cursor CLI JSON error structure:
        {
            "type": "error",
            "subtype": "connection_error",
            "is_error": true,
            "operation": "...",
            "message": "...",
            "request_id": "...",
            "session_id": "...",
            "details": {...}
        }
        """
        return {
            "type": "error",
            "subtype": "connection_error",
            "is_error": True,
            "operation": self.operation_name,
            "message": str(self),
            "request_id": self.request_id,
            "session_id": self.session_id,
            "details": self.details,
        }


class NetworkRequiredError(NetworkError):
    """Raised when network is required but unavailable."""
    
    def _build_message(self) -> str:
        """Build error message with network requirement context."""
        msg = super()._build_message()
        return (
            msg +
            "\n\nThis command requires network access. "
            "Please ensure you have an active internet connection."
        )


class NetworkOptionalError(NetworkError):
    """Raised when optional network operation fails."""
    
    def _build_message(self) -> str:
        """Build error message indicating offline fallback."""
        msg = super()._build_message()
        return (
            msg +
            "\n\nThis operation works offline with reduced functionality. "
            "Continuing in offline mode."
        )

