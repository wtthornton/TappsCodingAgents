"""
Message Formatter - ENH-001-S3

Formats enforcement messages for the Workflow Enforcement System.
Provides rich, context-aware messages for blocking and warning modes
with support for CLI and IDE output formats.

Design Principles:
    - Separation of Concerns: Message formatting separate from enforcement logic
    - Configurable: Emoji support, output format selection
    - Context-Aware: Messages tailored to detected workflow type
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

from tapps_agents.workflow.intent_detector import WorkflowType

logger = logging.getLogger(__name__)


class OutputFormat(StrEnum):
    """Output format for messages."""

    CLI = "cli"
    IDE = "ide"


@dataclass
class MessageConfig:
    """Configuration for message formatting."""

    use_emoji: bool = True
    output_format: OutputFormat = OutputFormat.CLI
    show_benefits: bool = True
    show_override: bool = True


# Workflow-specific benefits
WORKFLOW_BENEFITS: dict[WorkflowType, list[str]] = {
    WorkflowType.BUILD: [
        "Automatic testing (80%+ coverage)",
        "Quality gates (75+ score required)",
        "Comprehensive documentation",
        "Early bug detection",
    ],
    WorkflowType.FIX: [
        "Root cause analysis",
        "Regression test generation",
        "Fix verification",
        "Related issue detection",
    ],
    WorkflowType.REFACTOR: [
        "Behavior preservation tests",
        "Code quality improvement",
        "Technical debt reduction",
        "Safe incremental changes",
    ],
    WorkflowType.REVIEW: [
        "Security vulnerability detection",
        "Code quality scoring",
        "Best practice suggestions",
        "Maintainability analysis",
    ],
}


class MessageFormatter:
    """
    Formats enforcement messages for workflow enforcement system.

    Provides rich, context-aware messages for blocking and warning modes
    with configurable emoji support and output format selection.
    """

    def __init__(self, config: MessageConfig | None = None) -> None:
        """Initialize formatter with optional configuration."""
        self.config = config or MessageConfig()

    def format_blocking_message(
        self,
        workflow: WorkflowType,
        user_intent: str,
        file_path: Path,
        confidence: float,
    ) -> str:
        """
        Format blocking mode message with benefits and override instructions.

        Args:
            workflow: Detected workflow type
            user_intent: User's intent description
            file_path: Path to file being edited
            confidence: Detection confidence (0-100)

        Returns:
            Formatted blocking message
        """
        emoji = self._get_emoji("block") if self.config.use_emoji else ""
        intent_display = user_intent or "Implement feature"
        path_display = Path(file_path).as_posix()

        lines = [
            f"{emoji}Direct file edit blocked: {path_display}".strip(),
            "",
            f"Detected intent: {workflow.value} (confidence: {confidence:.0f}%)",
            "",
        ]

        if self.config.show_benefits:
            lines.append("TappsCodingAgents workflows provide:")
            for benefit in self._get_workflow_benefits(workflow):
                bullet = "  * " if self.config.output_format == OutputFormat.IDE else "  - "
                lines.append(f"{bullet}{benefit}")
            lines.append("")

        lines.append("Suggested workflow:")
        lines.append(f'  @simple-mode {workflow.value} "{intent_display}"')
        lines.append("")

        if self.config.show_override:
            lines.extend(self._get_override_instructions())

        return "\n".join(lines)

    def format_warning_message(
        self,
        workflow: WorkflowType,
        user_intent: str,
        confidence: float,
    ) -> str:
        """
        Format warning mode message (lighter suggestion).

        Args:
            workflow: Detected workflow type
            user_intent: User's intent description
            confidence: Detection confidence (0-100)

        Returns:
            Formatted warning message
        """
        emoji = self._get_emoji("warn") if self.config.use_emoji else ""
        intent_display = user_intent or "Implement feature"

        lines = [
            f"{emoji}Consider using a workflow (confidence: {confidence:.0f}%)".strip(),
            f'Suggested: @simple-mode {workflow.value} "{intent_display}"',
            "(Proceeding with direct edit...)",
        ]

        return "\n".join(lines)

    def format_allow_message(self) -> str:
        """Format allow message (empty for silent mode)."""
        return ""

    def _get_emoji(self, action: Literal["block", "warn", "allow"]) -> str:
        """Get emoji for action type."""
        emojis = {
            "block": "\u26a0\ufe0f ",  # Warning sign
            "warn": "\U0001f4a1 ",  # Light bulb
            "allow": "\u2705 ",  # Check mark
        }
        return emojis.get(action, "")

    def _get_workflow_benefits(self, workflow: WorkflowType) -> list[str]:
        """Get benefits list for workflow type."""
        return WORKFLOW_BENEFITS.get(workflow, WORKFLOW_BENEFITS[WorkflowType.BUILD])

    def _get_override_instructions(self) -> list[str]:
        """Get override instructions based on output format."""
        if self.config.output_format == OutputFormat.IDE:
            return [
                "To bypass enforcement:",
                "  * Use --skip-enforcement flag",
                "  * Or set enforcement.mode: silent in config",
            ]
        return [
            "To bypass enforcement:",
            "  - Use --skip-enforcement flag",
            "  - Or set enforcement.mode: silent in .tapps-agents/config.yaml",
        ]
