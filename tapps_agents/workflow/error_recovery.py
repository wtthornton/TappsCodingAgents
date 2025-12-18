"""
Error Recovery and Suggestion System

Epic 14: Error Recovery and Suggestions
Provides intelligent error analysis, recovery suggestions, and automatic retry with learning.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..core.error_envelope import ErrorEnvelope, ErrorEnvelopeBuilder

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"  # Minor issue, workflow can continue
    MEDIUM = "medium"  # Moderate issue, may need attention
    HIGH = "high"  # Significant issue, workflow may be blocked
    CRITICAL = "critical"  # Critical issue, workflow must stop


class ErrorType(Enum):
    """Detailed error types for better categorization."""

    # Configuration errors
    MISSING_CONFIG = "missing_config"
    INVALID_CONFIG = "invalid_config"
    ENV_VAR_MISSING = "env_var_missing"
    
    # File system errors
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    DISK_FULL = "disk_full"
    PATH_INVALID = "path_invalid"
    
    # Network/external errors
    CONNECTION_ERROR = "connection_error"
    TIMEOUT = "timeout"
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMIT = "rate_limit"
    
    # Validation errors
    INVALID_INPUT = "invalid_input"
    MISSING_REQUIRED = "missing_required"
    TYPE_MISMATCH = "type_mismatch"
    
    # Execution errors
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    IMPORT_ERROR = "import_error"
    DEPENDENCY_MISSING = "dependency_missing"
    
    # Workflow-specific errors
    STEP_FAILED = "step_failed"
    GATE_FAILED = "gate_failed"
    DEPENDENCY_BLOCKED = "dependency_blocked"
    
    # Unknown
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information about when/where an error occurred."""

    workflow_id: str | None = None
    step_id: str | None = None
    agent: str | None = None
    action: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    step_number: int | None = None
    total_steps: int | None = None
    workflow_status: str | None = None
    recent_changes: list[str] = field(default_factory=list)
    environment: dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorAnalysis:
    """Comprehensive error analysis."""

    error_envelope: ErrorEnvelope
    error_type: ErrorType
    severity: ErrorSeverity
    context: ErrorContext
    pattern_match: str | None = None  # Matched error pattern
    similar_errors: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoverySuggestion:
    """A recovery suggestion with ranking and explanation."""

    action: str  # What to do
    description: str  # Detailed description
    confidence: float  # 0.0-1.0 confidence score
    explanation: str  # Why this suggestion
    steps: list[str] = field(default_factory=list)  # Step-by-step instructions
    requires_manual: bool = False  # Whether manual intervention is needed
    metadata: dict[str, Any] = field(default_factory=dict)


class ErrorAnalyzer:
    """
    Analyzes errors to understand why they occurred and categorize them.
    
    Epic 14: Story 14.1
    """

    def __init__(self):
        """Initialize error analyzer."""
        self.patterns = self._load_error_patterns()

    def analyze(
        self,
        error: Exception | ErrorEnvelope | str,
        context: ErrorContext | None = None,
    ) -> ErrorAnalysis:
        """
        Analyze an error and return comprehensive analysis.

        Args:
            error: Exception, ErrorEnvelope, or error message string
            context: Optional context about when/where error occurred

        Returns:
            ErrorAnalysis with categorization, severity, and pattern matching
        """
        # Convert to ErrorEnvelope if needed
        if isinstance(error, ErrorEnvelope):
            envelope = error
        elif isinstance(error, Exception):
            envelope = ErrorEnvelopeBuilder.from_exception(error)
        else:
            # String error message
            envelope = ErrorEnvelope(
                code="unknown_error",
                message=str(error),
                category="execution",
            )

        # Create context if not provided
        if context is None:
            context = ErrorContext(
                workflow_id=envelope.workflow_id,
                step_id=envelope.step_id,
                agent=envelope.agent,
            )

        # Determine error type
        error_type = self._determine_error_type(envelope, error if isinstance(error, Exception) else None)

        # Determine severity
        severity = self._determine_severity(envelope, error_type)

        # Pattern matching
        pattern_match = self._match_pattern(envelope)

        # Find similar errors (for learning)
        similar_errors = self._find_similar_errors(envelope, pattern_match)

        return ErrorAnalysis(
            error_envelope=envelope,
            error_type=error_type,
            severity=severity,
            context=context,
            pattern_match=pattern_match,
            similar_errors=similar_errors,
        )

    def _determine_error_type(
        self, envelope: ErrorEnvelope, exc: Exception | None
    ) -> ErrorType:
        """Determine detailed error type."""
        # Check error code first
        code = envelope.code.lower()
        message = envelope.message.lower()

        # Configuration errors
        if "config" in code or "config" in message:
            if "missing" in message or "not found" in message:
                return ErrorType.MISSING_CONFIG
            return ErrorType.INVALID_CONFIG
        if "env" in code or "environment" in message:
            return ErrorType.ENV_VAR_MISSING

        # File system errors
        if "file_not_found" in code or "file not found" in message:
            return ErrorType.FILE_NOT_FOUND
        if "permission" in code or "permission" in message:
            return ErrorType.PERMISSION_DENIED
        if "disk full" in message or "no space" in message:
            return ErrorType.DISK_FULL
        if "invalid path" in message or "path not found" in message:
            return ErrorType.PATH_INVALID

        # Network errors
        if "connection" in code or "connection" in message:
            return ErrorType.CONNECTION_ERROR
        if "timeout" in code or "timeout" in message:
            return ErrorType.TIMEOUT
        if "unavailable" in message or "503" in message:
            return ErrorType.SERVICE_UNAVAILABLE
        if "rate limit" in message or "429" in message:
            return ErrorType.RATE_LIMIT

        # Validation errors
        if "validation" in code or "invalid" in message:
            if "required" in message or "missing" in message:
                return ErrorType.MISSING_REQUIRED
            if "type" in message:
                return ErrorType.TYPE_MISMATCH
            return ErrorType.INVALID_INPUT

        # Execution errors
        if exc:
            if isinstance(exc, SyntaxError):
                return ErrorType.SYNTAX_ERROR
            if isinstance(exc, ImportError):
                return ErrorType.IMPORT_ERROR
            if isinstance(exc, RuntimeError):
                return ErrorType.RUNTIME_ERROR

        if "import" in message or "module not found" in message:
            return ErrorType.IMPORT_ERROR
        if "dependency" in message or "package not found" in message:
            return ErrorType.DEPENDENCY_MISSING
        if "syntax" in message:
            return ErrorType.SYNTAX_ERROR

        # Workflow-specific
        if "step" in code and "failed" in message:
            return ErrorType.STEP_FAILED
        if "gate" in code or "gate" in message:
            return ErrorType.GATE_FAILED
        if "dependency" in code and "blocked" in message:
            return ErrorType.DEPENDENCY_BLOCKED

        return ErrorType.UNKNOWN

    def _determine_severity(
        self, envelope: ErrorEnvelope, error_type: ErrorType
    ) -> ErrorSeverity:
        """Determine error severity."""
        # Critical errors
        if error_type in (
            ErrorType.DISK_FULL,
            ErrorType.DEPENDENCY_BLOCKED,
        ):
            return ErrorSeverity.CRITICAL

        # High severity
        if error_type in (
            ErrorType.SYNTAX_ERROR,
            ErrorType.IMPORT_ERROR,
            ErrorType.STEP_FAILED,
            ErrorType.GATE_FAILED,
        ):
            return ErrorSeverity.HIGH

        # Medium severity
        if error_type in (
            ErrorType.CONNECTION_ERROR,
            ErrorType.SERVICE_UNAVAILABLE,
            ErrorType.TIMEOUT,
            ErrorType.INVALID_CONFIG,
        ):
            return ErrorSeverity.MEDIUM

        # Low severity (often recoverable)
        if error_type in (
            ErrorType.RATE_LIMIT,
            ErrorType.TIMEOUT,
            ErrorType.FILE_NOT_FOUND,
            ErrorType.PERMISSION_DENIED,
        ) and envelope.recoverable:
            return ErrorSeverity.LOW

        return ErrorSeverity.MEDIUM

    def _load_error_patterns(self) -> dict[str, dict[str, Any]]:
        """Load error patterns for matching."""
        # Common error patterns with regex
        return {
            "file_not_found": {
                "pattern": r"file.*not found|no such file|file does not exist",
                "type": ErrorType.FILE_NOT_FOUND,
            },
            "permission_denied": {
                "pattern": r"permission denied|access denied|permission error",
                "type": ErrorType.PERMISSION_DENIED,
            },
            "connection_error": {
                "pattern": r"connection.*refused|connection.*failed|could not connect",
                "type": ErrorType.CONNECTION_ERROR,
            },
            "timeout": {
                "pattern": r"timeout|timed out|operation.*too long",
                "type": ErrorType.TIMEOUT,
            },
            "import_error": {
                "pattern": r"no module named|import.*error|cannot import",
                "type": ErrorType.IMPORT_ERROR,
            },
            "syntax_error": {
                "pattern": r"syntax error|invalid syntax|parse error",
                "type": ErrorType.SYNTAX_ERROR,
            },
        }

    def _match_pattern(self, envelope: ErrorEnvelope) -> str | None:
        """Match error against known patterns."""
        message = envelope.message.lower()
        for pattern_name, pattern_info in self.patterns.items():
            if re.search(pattern_info["pattern"], message, re.IGNORECASE):
                return pattern_name
        return None

    def _find_similar_errors(
        self, envelope: ErrorEnvelope, pattern: str | None
    ) -> list[dict[str, Any]]:
        """Find similar errors from history (for learning)."""
        # This would query error history database
        # For now, return empty list
        return []


class RecoverySuggestionEngine:
    """
    Generates recovery suggestions based on error analysis.
    
    Epic 14: Story 14.2
    """

    def __init__(self, learning_data_path: Path | None = None):
        """
        Initialize recovery suggestion engine.

        Args:
            learning_data_path: Path to learning data file
        """
        self.learning_data_path = learning_data_path or Path(
            ".tapps-agents/error_learning.json"
        )
        self.learning_data = self._load_learning_data()
        self.suggestion_db = self._load_suggestion_database()

    def generate_suggestions(
        self, analysis: ErrorAnalysis, max_suggestions: int = 5
    ) -> list[RecoverySuggestion]:
        """
        Generate recovery suggestions for an error.

        Args:
            analysis: Error analysis
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of recovery suggestions ranked by confidence
        """
        suggestions = []

        # Get suggestions from database
        db_suggestions = self.suggestion_db.get(analysis.error_type.value, [])
        for suggestion_data in db_suggestions:
            confidence = self._calculate_confidence(
                suggestion_data, analysis, self.learning_data
            )
            suggestions.append(
                RecoverySuggestion(
                    action=suggestion_data["action"],
                    description=suggestion_data["description"],
                    confidence=confidence,
                    explanation=suggestion_data.get("explanation", ""),
                    steps=suggestion_data.get("steps", []),
                    requires_manual=suggestion_data.get("requires_manual", False),
                )
            )

        # Add generic suggestions if no specific ones found
        if not suggestions:
            suggestions.extend(self._generate_generic_suggestions(analysis))

        # Sort by confidence (highest first)
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        return suggestions[:max_suggestions]

    def _load_suggestion_database(self) -> dict[str, list[dict[str, Any]]]:
        """Load suggestion database with common errors and fixes."""
        return {
            ErrorType.FILE_NOT_FOUND.value: [
                {
                    "action": "Check file path",
                    "description": "Verify the file path is correct and the file exists",
                    "explanation": "The file may have been moved, deleted, or the path is incorrect",
                    "steps": [
                        "Check if the file exists at the specified path",
                        "Verify file permissions",
                        "Check if the path is relative vs absolute",
                    ],
                    "requires_manual": False,
                },
                {
                    "action": "Create missing file",
                    "description": "Create the file if it's expected to exist",
                    "explanation": "The file may be required but doesn't exist yet",
                    "steps": [
                        "Check if the file should be created",
                        "Create the file with appropriate content",
                        "Retry the operation",
                    ],
                    "requires_manual": True,
                },
            ],
            ErrorType.PERMISSION_DENIED.value: [
                {
                    "action": "Fix file permissions",
                    "description": "Check and fix file/directory permissions",
                    "explanation": "The operation requires permissions that are not available",
                    "steps": [
                        "Check file permissions (chmod)",
                        "Check directory permissions",
                        "Verify user has required access",
                    ],
                    "requires_manual": True,
                },
            ],
            ErrorType.CONNECTION_ERROR.value: [
                {
                    "action": "Check network connection",
                    "description": "Verify network connectivity and service availability",
                    "explanation": "The service may be temporarily unavailable",
                    "steps": [
                        "Check internet connection",
                        "Verify service is running",
                        "Check firewall settings",
                    ],
                    "requires_manual": False,
                },
                {
                    "action": "Retry with backoff",
                    "description": "Retry the operation after a short delay",
                    "explanation": "Connection errors are often transient",
                    "steps": [
                        "Wait a few seconds",
                        "Retry the operation",
                    ],
                    "requires_manual": False,
                },
            ],
            ErrorType.TIMEOUT.value: [
                {
                    "action": "Increase timeout",
                    "description": "Increase the timeout setting for the operation",
                    "explanation": "The operation may need more time to complete",
                    "steps": [
                        "Check current timeout setting",
                        "Increase timeout value",
                        "Retry the operation",
                    ],
                    "requires_manual": False,
                },
                {
                    "action": "Optimize operation",
                    "description": "Optimize the operation to complete faster",
                    "explanation": "The operation may be too slow",
                    "steps": [
                        "Review operation complexity",
                        "Optimize slow parts",
                        "Consider breaking into smaller operations",
                    ],
                    "requires_manual": True,
                },
            ],
            ErrorType.IMPORT_ERROR.value: [
                {
                    "action": "Install missing dependency",
                    "description": "Install the required Python package",
                    "explanation": "The module is not installed or not in Python path",
                    "steps": [
                        "Check if package is installed (pip list)",
                        "Install missing package (pip install)",
                        "Verify Python path includes package location",
                    ],
                    "requires_manual": False,
                },
            ],
            ErrorType.SYNTAX_ERROR.value: [
                {
                    "action": "Fix syntax error",
                    "description": "Review and fix the syntax error in the code",
                    "explanation": "There is a syntax error in the code that needs to be fixed",
                    "steps": [
                        "Check error message for file and line number",
                        "Review code at that location",
                        "Fix syntax error",
                    ],
                    "requires_manual": True,
                },
            ],
            ErrorType.MISSING_CONFIG.value: [
                {
                    "action": "Add missing configuration",
                    "description": "Add the required configuration value",
                    "explanation": "A required configuration value is missing",
                    "steps": [
                        "Check configuration file",
                        "Add missing configuration value",
                        "Verify configuration format",
                    ],
                    "requires_manual": True,
                },
            ],
        }

    def _generate_generic_suggestions(
        self, analysis: ErrorAnalysis
    ) -> list[RecoverySuggestion]:
        """Generate generic suggestions when no specific ones are available."""
        suggestions = []

        if analysis.error_envelope.recoverable:
            suggestions.append(
                RecoverySuggestion(
                    action="Retry operation",
                    description="The error may be transient, try again",
                    confidence=0.5,
                    explanation="This error is marked as recoverable",
                    steps=["Wait a moment", "Retry the operation"],
                    requires_manual=False,
                )
            )

        suggestions.append(
            RecoverySuggestion(
                action="Check logs",
                description="Review detailed error logs for more information",
                confidence=0.3,
                explanation="Logs may contain additional context about the error",
                steps=[
                    "Check workflow logs",
                    "Review error details",
                    "Look for related errors",
                ],
                requires_manual=True,
            )
        )

        return suggestions

    def _calculate_confidence(
        self,
        suggestion_data: dict[str, Any],
        analysis: ErrorAnalysis,
        learning_data: dict[str, Any],
    ) -> float:
        """Calculate confidence score for a suggestion."""
        base_confidence = suggestion_data.get("base_confidence", 0.7)

        # Boost confidence if we've seen this pattern before and suggestion worked
        pattern_key = analysis.pattern_match or analysis.error_type.value
        if pattern_key in learning_data.get("successful_suggestions", {}):
            success_rate = learning_data["successful_suggestions"][pattern_key].get(
                suggestion_data["action"], 0.0
            )
            base_confidence = min(1.0, base_confidence + success_rate * 0.2)

        return base_confidence

    def _load_learning_data(self) -> dict[str, Any]:
        """Load learning data from file."""
        if self.learning_data_path.exists():
            try:
                with open(self.learning_data_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load learning data: {e}")
        return {
            "successful_suggestions": {},
            "error_patterns": {},
        }

    def record_suggestion_feedback(
        self,
        analysis: ErrorAnalysis,
        suggestion: RecoverySuggestion,
        worked: bool,
    ) -> None:
        """
        Record feedback about whether a suggestion worked.

        Args:
            analysis: Error analysis
            suggestion: Suggestion that was tried
            worked: Whether the suggestion worked
        """
        pattern_key = analysis.pattern_match or analysis.error_type.value
        action_key = suggestion.action

        if "successful_suggestions" not in self.learning_data:
            self.learning_data["successful_suggestions"] = {}

        if pattern_key not in self.learning_data["successful_suggestions"]:
            self.learning_data["successful_suggestions"][pattern_key] = {}

        if action_key not in self.learning_data["successful_suggestions"][pattern_key]:
            self.learning_data["successful_suggestions"][pattern_key][action_key] = {
                "attempts": 0,
                "successes": 0,
                "rate": 0.0,
            }

        stats = self.learning_data["successful_suggestions"][pattern_key][action_key]
        stats["attempts"] += 1
        if worked:
            stats["successes"] += 1
        stats["rate"] = stats["successes"] / stats["attempts"]

        # Save learning data
        self.learning_data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.learning_data_path, "w") as f:
            json.dump(self.learning_data, f, indent=2)


class ErrorRecoveryManager:
    """
    Manages error recovery with suggestions and automatic retry.
    
    Epic 14: Stories 14.1-14.5
    """

    def __init__(
        self,
        enable_auto_retry: bool = True,
        max_retries: int = 3,
        learning_data_path: Path | None = None,
    ):
        """
        Initialize error recovery manager.

        Args:
            enable_auto_retry: Whether to enable automatic retry
            max_retries: Maximum retry attempts
            learning_data_path: Path to learning data file
        """
        self.enable_auto_retry = enable_auto_retry
        self.max_retries = max_retries
        self.analyzer = ErrorAnalyzer()
        self.suggestion_engine = RecoverySuggestionEngine(learning_data_path)

    def handle_error(
        self,
        error: Exception | ErrorEnvelope | str,
        context: ErrorContext | None = None,
        attempt: int = 1,
    ) -> dict[str, Any]:
        """
        Handle an error with analysis and suggestions.

        Args:
            error: Error to handle
            context: Error context
            attempt: Current attempt number

        Returns:
            Dictionary with analysis, suggestions, and recovery plan
        """
        # Analyze error
        analysis = self.analyzer.analyze(error, context)

        # Generate suggestions
        suggestions = self.suggestion_engine.generate_suggestions(analysis)

        # Determine if should retry
        should_retry = self._should_retry(analysis, attempt, suggestions)

        # Format user-friendly message
        user_message = self._format_user_message(analysis, suggestions)

        return {
            "analysis": analysis,
            "suggestions": suggestions,
            "should_retry": should_retry,
            "user_message": user_message,
            "retry_after": self._calculate_retry_delay(attempt) if should_retry else None,
        }

    def _should_retry(
        self,
        analysis: ErrorAnalysis,
        attempt: int,
        suggestions: list[RecoverySuggestion],
    ) -> bool:
        """Determine if error should be retried."""
        if not self.enable_auto_retry:
            return False

        if attempt >= self.max_retries:
            return False

        # Don't retry critical errors
        if analysis.severity == ErrorSeverity.CRITICAL:
            return False

        # Retry if error is recoverable and we have suggestions
        if analysis.error_envelope.recoverable:
            # Check if we have auto-applicable suggestions
            auto_suggestions = [s for s in suggestions if not s.requires_manual]
            if auto_suggestions:
                return True

        # Retry transient errors
        if analysis.error_type in (
            ErrorType.CONNECTION_ERROR,
            ErrorType.TIMEOUT,
            ErrorType.SERVICE_UNAVAILABLE,
            ErrorType.RATE_LIMIT,
        ):
            return True

        return False

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        base_delay = 2.0
        max_delay = 60.0
        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
        return delay

    def _format_user_message(
        self,
        analysis: ErrorAnalysis,
        suggestions: list[RecoverySuggestion],
    ) -> str:
        """
        Format user-friendly error message.

        Epic 14: Story 14.4
        """
        lines = []

        # Simplified error message
        error_msg = analysis.error_envelope.message
        # Remove technical jargon
        error_msg = self._simplify_message(error_msg)

        lines.append(f"**Error:** {error_msg}")
        lines.append("")

        # Add context
        if analysis.context.step_id:
            lines.append(f"**Step:** {analysis.context.step_id}")
        if analysis.context.agent:
            lines.append(f"**Agent:** {analysis.context.agent}")

        lines.append("")

        # Add suggestions
        if suggestions:
            lines.append("**Suggested Actions:**")
            for i, suggestion in enumerate(suggestions[:3], 1):
                lines.append(f"{i}. **{suggestion.action}**")
                lines.append(f"   {suggestion.description}")
                if suggestion.explanation:
                    lines.append(f"   *Why:* {suggestion.explanation}")
                if suggestion.steps:
                    lines.append("   *Steps:*")
                    for step in suggestion.steps:
                        lines.append(f"     - {step}")
                lines.append("")

        return "\n".join(lines)

    def _simplify_message(self, message: str) -> str:
        """Simplify error message by removing technical jargon."""
        # Replace common technical terms with simpler ones
        replacements = {
            r"FileNotFoundError": "File not found",
            r"PermissionError": "Permission denied",
            r"ConnectionError": "Connection failed",
            r"TimeoutError": "Operation timed out",
            r"ImportError": "Module not found",
            r"SyntaxError": "Syntax error in code",
            r"ValueError": "Invalid value",
            r"KeyError": "Missing key",
            r"AttributeError": "Attribute not found",
        }

        for pattern, replacement in replacements.items():
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

        return message

