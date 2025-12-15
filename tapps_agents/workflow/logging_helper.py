"""
Structured logging helper for workflow execution with correlation IDs.

Epic 1 / Story 1.6: Correlation IDs & Baseline Observability
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class WorkflowLogger:
    """
    Structured logger that automatically includes correlation fields.
    
    Ensures all workflow-related logs include workflow_id, step_id, and agent
    for traceability across multi-agent execution.
    """

    def __init__(
        self,
        workflow_id: str | None = None,
        step_id: str | None = None,
        agent: str | None = None,
        base_logger: logging.Logger | None = None,
    ):
        """
        Initialize workflow logger with correlation context.

        Args:
            workflow_id: Workflow execution ID
            step_id: Current step ID (optional)
            agent: Current agent name (optional)
            base_logger: Base logger to use (defaults to module logger)
        """
        self.workflow_id = workflow_id
        self.step_id = step_id
        self.agent = agent
        self._logger = base_logger or logger

    def _extra(self, **kwargs: Any) -> dict[str, Any]:
        """Build extra dict with correlation fields."""
        extra: dict[str, Any] = {}
        if self.workflow_id:
            extra["workflow_id"] = self.workflow_id
        if self.step_id:
            extra["step_id"] = self.step_id
        if self.agent:
            extra["agent"] = self.agent
        extra.update(kwargs)
        return extra

    def _redact_sensitive(self, message: str) -> str:
        """
        Redact potentially sensitive information from log messages.
        
        This is a basic implementation. For production, consider:
        - API keys (patterns like `sk-...`, `api_key=...`)
        - Passwords (patterns like `password=...`, `pwd=...`)
        - Tokens (patterns like `token=...`, `auth=...`)
        - File paths that might contain user names
        
        Returns:
            Message with sensitive data redacted
        """
        # Basic redaction - replace common patterns
        import re
        
        # Redact API keys (common patterns: sk-..., pk-..., api_key=..., API key: ...)
        message = re.sub(r'\b(sk|pk|api_key|apikey)=[^\s&]+', r'\1=***REDACTED***', message, flags=re.IGNORECASE)
        message = re.sub(r'\b(api\s+key|api_key|apikey):\s*[A-Za-z0-9_-]{10,}', r'\1: ***REDACTED***', message, flags=re.IGNORECASE)
        message = re.sub(r'\b(sk|pk)-[A-Za-z0-9]{20,}', r'\1-***REDACTED***', message, flags=re.IGNORECASE)
        
        # Redact passwords
        message = re.sub(r'\b(password|pwd|passwd)=[^\s&]+', r'\1=***REDACTED***', message, flags=re.IGNORECASE)
        message = re.sub(r'\b(password|pwd|passwd):\s*[^\s]+', r'\1: ***REDACTED***', message, flags=re.IGNORECASE)
        
        # Redact tokens
        message = re.sub(r'\b(token|auth|bearer)\s+[A-Za-z0-9_-]{20,}', r'\1 ***REDACTED***', message, flags=re.IGNORECASE)
        message = re.sub(r'\b(token|auth|bearer):\s*[A-Za-z0-9_-]{20,}', r'\1: ***REDACTED***', message, flags=re.IGNORECASE)
        
        return message

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with correlation fields."""
        redacted = self._redact_sensitive(message)
        self._logger.debug(redacted, extra=self._extra(**kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with correlation fields."""
        redacted = self._redact_sensitive(message)
        self._logger.info(redacted, extra=self._extra(**kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with correlation fields."""
        redacted = self._redact_sensitive(message)
        self._logger.warning(redacted, extra=self._extra(**kwargs))

    def error(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log error message with correlation fields."""
        redacted = self._redact_sensitive(message)
        self._logger.error(redacted, exc_info=exc_info, extra=self._extra(**kwargs))

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message with correlation fields."""
        redacted = self._redact_sensitive(message)
        self._logger.critical(redacted, extra=self._extra(**kwargs))

    def with_context(
        self,
        step_id: str | None = None,
        agent: str | None = None,
    ) -> "WorkflowLogger":
        """
        Create a new logger instance with additional context.

        Args:
            step_id: Step ID to add to context
            agent: Agent name to add to context

        Returns:
            New WorkflowLogger instance with merged context
        """
        return WorkflowLogger(
            workflow_id=self.workflow_id,
            step_id=step_id or self.step_id,
            agent=agent or self.agent,
            base_logger=self._logger,
        )
