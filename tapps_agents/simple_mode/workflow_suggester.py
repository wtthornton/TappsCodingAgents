"""
Workflow Suggester - Proactive workflow suggestions based on user intent.

Detects when users are about to do direct edits and suggests appropriate
Simple Mode workflows instead.
"""

from dataclasses import dataclass
from typing import Any

from ..simple_mode.intent_parser import IntentParser, IntentType


@dataclass
class WorkflowSuggestion:
    """A workflow suggestion with benefits and command."""

    workflow_command: str
    workflow_type: str
    benefits: list[str]
    confidence: float
    reason: str


class WorkflowSuggester:
    """
    Suggest Simple Mode workflows based on user intent.
    
    Analyzes user input to detect when a workflow would be beneficial
    and provides proactive suggestions.
    """

    def __init__(self):
        """Initialize workflow suggester."""
        self.intent_parser = IntentParser()

    def suggest_workflow(self, user_input: str, context: dict[str, Any] | None = None) -> WorkflowSuggestion | None:
        """
        Suggest a workflow based on user input.
        
        Args:
            user_input: User's natural language input
            context: Optional context (file paths, project type, etc.)
            
        Returns:
            WorkflowSuggestion if a workflow is recommended, None otherwise
        """
        if not user_input or not user_input.strip():
            return None

        context = context or {}
        
        # Parse intent
        intent = self.intent_parser.parse(user_input)
        
        # Check if intent suggests a workflow
        if intent.type == IntentType.UNKNOWN:
            return None
        
        # Detect hybrid "review + fix" intent
        user_input_lower = user_input.lower()
        has_review = (
            intent.type == IntentType.REVIEW
            or "review" in user_input_lower
            or intent.compare_to_codebase
        )
        has_fix = intent.type == IntentType.FIX or "fix" in user_input_lower
        
        if has_review and has_fix:
            return WorkflowSuggestion(
                workflow_command=(
                    '@simple-mode *review <file>  # Then: @simple-mode *fix <file> "issues from review"'
                ),
                workflow_type="review-then-fix",
                benefits=[
                    "Comprehensive quality analysis first",
                    "Targeted fixes based on review feedback",
                    "Quality gates after fixes",
                    "Full traceability from review to fix",
                ],
                confidence=0.85,
                reason="Review + fix hybrid request detected",
            )
        
        # Map intent to workflow command
        workflow_mapping = {
            IntentType.BUILD: {
                "command": f'@simple-mode *build "{user_input}"',
                "type": "build",
                "benefits": [
                    "Automatic test generation (80%+ coverage)",
                    "Quality gate enforcement (75+ score required)",
                    "Comprehensive documentation",
                    "Early bug detection with systematic review",
                    "Full traceability (requirements → implementation)",
                ],
                "reason": "New feature implementation detected",
            },
            IntentType.FIX: {
                "command": f'@simple-mode *fix <file> "{user_input}"',
                "type": "fix",
                "benefits": [
                    "Systematic root cause analysis",
                    "Automatic test verification",
                    "Quality review before fix",
                ],
                "reason": "Bug fix or error resolution detected",
            },
            IntentType.REVIEW: {
                "command": f'@simple-mode *review <file>',
                "type": "review",
                "benefits": [
                    "Comprehensive quality scores (5 metrics)",
                    "Actionable improvement suggestions",
                    "Security analysis",
                ],
                "reason": "Code review request detected",
            },
            IntentType.TEST: {
                "command": f'@simple-mode *test <file>',
                "type": "test",
                "benefits": [
                    "Comprehensive test generation",
                    "Coverage analysis",
                    "Test framework detection",
                ],
                "reason": "Test generation request detected",
            },
            IntentType.REFACTOR: {
                "command": f'@simple-mode *refactor <file>',
                "type": "refactor",
                "benefits": [
                    "Pattern detection and modernization",
                    "Quality validation after refactoring",
                    "Test updates",
                ],
                "reason": "Code refactoring request detected",
            },
        }
        
        workflow_info = workflow_mapping.get(intent.type)
        if not workflow_info:
            return None
        
        # Calculate confidence based on intent confidence
        confidence = intent.confidence
        
        # Adjust confidence based on context
        if context.get("has_existing_files"):
            # If files already exist, might be modification vs new feature
            if intent.type == IntentType.BUILD:
                confidence *= 0.9  # Slightly lower confidence
        
        return WorkflowSuggestion(
            workflow_command=workflow_info["command"],
            workflow_type=workflow_info["type"],
            benefits=workflow_info["benefits"],
            confidence=confidence,
            reason=workflow_info["reason"],
        )

    def format_suggestion(self, suggestion: WorkflowSuggestion) -> str:
        """
        Format a workflow suggestion as a user-friendly message.
        
        Args:
            suggestion: Workflow suggestion to format
            
        Returns:
            Formatted suggestion message
        """
        lines = [
            "🤖 **Workflow Suggestion**",
            "",
            f"For {suggestion.reason}, consider using:",
            "",
            f"```",
            f"{suggestion.workflow_command}",
            f"```",
            "",
            "**Benefits:**",
        ]
        
        for benefit in suggestion.benefits:
            lines.append(f"✅ {benefit}")
        
        lines.extend([
            "",
            "Would you like me to proceed with the workflow?",
            "[Yes, use workflow] [No, direct edit]",
        ])
        
        return "\n".join(lines)

    def should_suggest(self, user_input: str, context: dict[str, Any] | None = None) -> bool:
        """
        Determine if a workflow should be suggested.
        
        Args:
            user_input: User's natural language input
            context: Optional context
            
        Returns:
            True if workflow should be suggested, False otherwise
        """
        suggestion = self.suggest_workflow(user_input, context)
        
        if not suggestion:
            return False
        
        # Only suggest if confidence is high enough
        return suggestion.confidence >= 0.6
