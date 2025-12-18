"""
Confirmation Handler for Workflow Execution

Handles confirmation step before workflow execution.
Epic 9 / Story 9.4: Confirmation and Execution
"""


from .models import Workflow
from .nlp_parser import WorkflowIntentResult


class ConfirmationHandler:
    """Handles workflow execution confirmation."""

    def __init__(self, auto_mode: bool = False, confidence_threshold: float = 0.8):
        """
        Initialize confirmation handler.

        Args:
            auto_mode: If True, skip confirmation for high-confidence matches
            confidence_threshold: Confidence threshold for auto-mode bypass
        """
        self.auto_mode = auto_mode
        self.confidence_threshold = confidence_threshold

    def format_confirmation(self, workflow: Workflow, intent_result: WorkflowIntentResult) -> str:
        """
        Format confirmation message for display.

        Args:
            workflow: Workflow to be executed
            intent_result: Intent detection result

        Returns:
            Formatted confirmation message
        """
        lines = []
        lines.append("=" * 60)
        lines.append("Workflow Execution Confirmation")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Workflow: {workflow.name}")
        if workflow.description:
            lines.append(f"Description: {workflow.description}")
        lines.append(f"Steps: {len(workflow.steps)}")
        lines.append("")

        # Show parameters if any
        if intent_result.parameters:
            lines.append("Parameters:")
            for key, value in intent_result.parameters.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # Show confidence if below threshold
        if intent_result.confidence < self.confidence_threshold:
            lines.append(f"Confidence: {intent_result.confidence:.1%} (low)")
            lines.append("")

        lines.append("Proceed with execution? [y/N]: ")

        return "\n".join(lines)

    def should_skip_confirmation(self, intent_result: WorkflowIntentResult) -> bool:
        """
        Determine if confirmation should be skipped.

        Args:
            intent_result: Intent detection result

        Returns:
            True if confirmation should be skipped
        """
        if not self.auto_mode:
            return False

        return intent_result.confidence >= self.confidence_threshold

    def parse_confirmation(self, response: str) -> bool:
        """
        Parse user confirmation response.

        Args:
            response: User response (yes/y/proceed or no/n/cancel)

        Returns:
            True if confirmed, False if cancelled
        """
        response_lower = response.strip().lower()

        if response_lower in ("y", "yes", "proceed", "go", "ok", "okay"):
            return True

        return False

