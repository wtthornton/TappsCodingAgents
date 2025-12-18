"""
Error Handling and Ambiguity Resolution for Natural Language Parsing

Handles parsing errors and resolves ambiguous workflow requests.
Epic 9 / Story 9.6: Error Handling and Ambiguity Resolution
"""

import logging
from dataclasses import dataclass
from enum import Enum

from .nlp_parser import WorkflowIntent, WorkflowIntentResult

logger = logging.getLogger(__name__)


class ParseErrorType(Enum):
    """Types of parsing errors."""

    PARSING_ERROR = "parsing_error"  # Cannot extract intent
    NO_MATCH = "no_match"  # No workflow matches
    AMBIGUOUS_MATCH = "ambiguous_match"  # Multiple workflows match
    INVALID_INPUT = "invalid_input"  # Input format invalid


@dataclass
class ParseError:
    """Parsing error information."""

    error_type: ParseErrorType
    message: str
    suggestions: list[str] | None = None
    cli_command: str | None = None


class AmbiguityResolver:
    """Resolves ambiguous workflow requests."""

    def __init__(self, confidence_gap_threshold: float = 0.2):
        """
        Initialize ambiguity resolver.

        Args:
            confidence_gap_threshold: Minimum confidence gap for auto-selection
        """
        self.confidence_gap_threshold = confidence_gap_threshold

    def resolve_ambiguity(
        self, intent_result: WorkflowIntentResult, workflow_intent: WorkflowIntent
    ) -> tuple[str | None, str]:
        """
        Resolve ambiguous workflow request.

        Args:
            intent_result: Intent detection result
            workflow_intent: Workflow intent with alternatives

        Returns:
            Tuple of (selected_workflow_name, resolution_strategy)
        """
        if not intent_result.ambiguity_flag:
            return intent_result.workflow_name, "auto"

        # Check if we can auto-select based on confidence gap
        if workflow_intent.alternative_matches:
            best_confidence = workflow_intent.confidence
            second_best_confidence = workflow_intent.alternative_matches[0][1] if workflow_intent.alternative_matches else 0.0

            confidence_gap = best_confidence - second_best_confidence

            if confidence_gap >= self.confidence_gap_threshold:
                return workflow_intent.workflow_name, "auto_select"

        # Ambiguous - need user clarification
        return None, "clarify"

    def format_ambiguity_prompt(self, workflow_intent: WorkflowIntent) -> str:
        """
        Format ambiguity resolution prompt for user.

        Args:
            workflow_intent: Workflow intent with alternatives

        Returns:
            Formatted prompt message
        """
        lines = []
        lines.append("Multiple workflows match your request:")
        lines.append("")

        # Show primary match
        if workflow_intent.workflow_name:
            lines.append(f"1. {workflow_intent.workflow_name} (confidence: {workflow_intent.confidence:.1%})")
            lines.append("")

        # Show alternatives
        if workflow_intent.alternative_matches:
            for i, (workflow_name, confidence) in enumerate(workflow_intent.alternative_matches[:3], 2):
                lines.append(f"{i}. {workflow_name} (confidence: {confidence:.1%})")
                lines.append("")

        lines.append("Please select a workflow number or type the workflow name:")

        return "\n".join(lines)


class ErrorHandler:
    """Handles parsing errors gracefully."""

    def __init__(self):
        """Initialize error handler."""
        pass

    def handle_error(
        self, error_type: ParseErrorType, intent_result: WorkflowIntentResult | None = None, workflow_intent: WorkflowIntent | None = None
    ) -> ParseError:
        """
        Handle parsing error and generate user-friendly error message.

        Args:
            error_type: Type of error
            intent_result: Intent result if available
            workflow_intent: Workflow intent if available

        Returns:
            ParseError with error information and suggestions
        """
        if error_type == ParseErrorType.NO_MATCH:
            return self._handle_no_match(intent_result)
        elif error_type == ParseErrorType.AMBIGUOUS_MATCH:
            return self._handle_ambiguous_match(workflow_intent)
        elif error_type == ParseErrorType.INVALID_INPUT:
            return self._handle_invalid_input()
        else:
            return self._handle_parsing_error()

    def _handle_no_match(self, intent_result: WorkflowIntentResult | None) -> ParseError:
        """Handle case where no workflow matches."""
        suggestions = intent_result.suggestions if intent_result else []

        # Generate CLI command suggestion
        if intent_result and intent_result.workflow_type:
            cli_command = f"python -m tapps_agents.cli workflow {intent_result.workflow_type}"
        else:
            cli_command = "python -m tapps_agents.cli workflow list"

        return ParseError(
            error_type=ParseErrorType.NO_MATCH,
            message="No workflow matches your request. Try one of the suggestions below or use CLI commands.",
            suggestions=suggestions,
            cli_command=cli_command,
        )

    def _handle_ambiguous_match(self, workflow_intent: WorkflowIntent | None) -> ParseError:
        """Handle ambiguous workflow match."""
        suggestions = []
        if workflow_intent and workflow_intent.alternative_matches:
            suggestions = [name for name, _ in workflow_intent.alternative_matches[:3]]

        return ParseError(
            error_type=ParseErrorType.AMBIGUOUS_MATCH,
            message="Multiple workflows match your request. Please select one:",
            suggestions=suggestions,
        )

    def _handle_invalid_input(self) -> ParseError:
        """Handle invalid input format."""
        return ParseError(
            error_type=ParseErrorType.INVALID_INPUT,
            message="Invalid input format. Please try again with a clearer request.",
            suggestions=["run rapid development", "execute full SDLC", "start maintenance workflow"],
        )

    def _handle_parsing_error(self) -> ParseError:
        """Handle general parsing error."""
        return ParseError(
            error_type=ParseErrorType.PARSING_ERROR,
            message="Could not parse your request. Please try rephrasing or use CLI commands.",
            cli_command="python -m tapps_agents.cli workflow list",
        )

    def format_error(self, error: ParseError) -> str:
        """
        Format error message for display.

        Args:
            error: ParseError to format

        Returns:
            Formatted error message
        """
        lines = []
        lines.append("Error: " + error.message)
        lines.append("")

        if error.suggestions:
            lines.append("Suggestions:")
            for i, suggestion in enumerate(error.suggestions[:5], 1):
                lines.append(f"  {i}. {suggestion}")
            lines.append("")

        if error.cli_command:
            lines.append(f"CLI Command: {error.cli_command}")
            lines.append("")

        return "\n".join(lines)

