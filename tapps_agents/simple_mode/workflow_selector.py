"""Workflow selector for intelligent workflow selection."""

from dataclasses import dataclass
from enum import Enum

from .prompt_analyzer import PromptAnalysis


class WorkflowType(Enum):
    """Available workflow types."""
    BUILD = "build"
    VALIDATE = "validate"
    QUICK_WINS = "quick_wins"
    FIX = "fix"
    REVIEW = "review"
    TEST = "test"
    REFACTOR = "refactor"


@dataclass
class WorkflowSelection:
    """Workflow selection result."""
    workflow_type: WorkflowType
    preset: str
    estimated_duration: str
    estimated_tokens: int
    rationale: str
    confidence: float


class WorkflowSelector:
    """Select optimal workflow based on task characteristics."""

    def select(
        self,
        analysis: PromptAnalysis,
        command: str | None = None
    ) -> WorkflowSelection:
        """
        Select optimal workflow.

        Decision factors:
        1. Existing code quality
        2. Task complexity
        3. Risk level
        4. Explicit command override

        Args:
            analysis: Prompt analysis result
            command: Optional explicit command

        Returns:
            WorkflowSelection with recommendation
        """
        # Factor 1: Check for existing code
        if analysis.has_existing_code:
            # Check if existing code is good
            quality_hint = None
            if analysis.existing_code_refs:
                quality_hint = analysis.existing_code_refs[0].quality_hint

            if quality_hint == "excellent" or analysis.mentions_compare:
                # Validation workflow
                return WorkflowSelection(
                    workflow_type=WorkflowType.VALIDATE,
                    preset="validation",
                    estimated_duration="15 min",
                    estimated_tokens=15000,
                    rationale="Existing code excellent + comparison requested → validation",
                    confidence=0.9
                )

        # Factor 2: Check task intent
        if analysis.primary_intent.value == "optimize":
            # Quick wins workflow
            return WorkflowSelection(
                workflow_type=WorkflowType.QUICK_WINS,
                preset="minimal",
                estimated_duration="10 min",
                estimated_tokens=8000,
                rationale="Optimization task → quick wins workflow",
                confidence=0.85
            )

        # Factor 3: Check for fix intent
        if analysis.primary_intent.value == "fix":
            return WorkflowSelection(
                workflow_type=WorkflowType.FIX,
                preset="minimal",
                estimated_duration="8 min",
                estimated_tokens=6000,
                rationale="Bug fix → fix workflow",
                confidence=0.9
            )

        # Factor 4: Check for review intent
        if analysis.primary_intent.value == "review":
            return WorkflowSelection(
                workflow_type=WorkflowType.REVIEW,
                preset="standard",
                estimated_duration="12 min",
                estimated_tokens=10000,
                rationale="Code review → review workflow",
                confidence=0.9
            )

        # Factor 5: Check for test intent
        if analysis.primary_intent.value == "test":
            return WorkflowSelection(
                workflow_type=WorkflowType.TEST,
                preset="standard",
                estimated_duration="15 min",
                estimated_tokens=12000,
                rationale="Test generation → test workflow",
                confidence=0.9
            )

        # Factor 6: Check for refactor intent
        if analysis.primary_intent.value == "refactor":
            return WorkflowSelection(
                workflow_type=WorkflowType.REFACTOR,
                preset="standard",
                estimated_duration="18 min",
                estimated_tokens=15000,
                rationale="Refactoring → refactor workflow",
                confidence=0.85
            )

        # Factor 7: Check complexity for preset selection
        if analysis.complexity.value == "minimal":
            # Minimal preset
            return WorkflowSelection(
                workflow_type=WorkflowType.BUILD,
                preset="minimal",
                estimated_duration="5 min",
                estimated_tokens=5000,
                rationale="Low complexity → minimal preset",
                confidence=0.8
            )

        # Factor 8: Check for comprehensive complexity
        if analysis.complexity.value == "comprehensive":
            return WorkflowSelection(
                workflow_type=WorkflowType.BUILD,
                preset="comprehensive",
                estimated_duration="45 min",
                estimated_tokens=60000,
                rationale="High complexity → comprehensive preset",
                confidence=0.8
            )

        # Default: Standard build
        return WorkflowSelection(
            workflow_type=WorkflowType.BUILD,
            preset="standard",
            estimated_duration="20 min",
            estimated_tokens=30000,
            rationale="Standard feature → standard workflow",
            confidence=0.75
        )
