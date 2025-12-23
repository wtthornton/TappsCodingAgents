"""
Natural Language Handler - Process natural language commands for Simple Mode.

Intercepts natural language commands, parses them, and routes to appropriate orchestrators.
Works both in CLI mode and Cursor Skills mode.
"""

from pathlib import Path
from typing import Any

from tapps_agents.core.config import ProjectConfig, load_config
from .intent_parser import Intent, IntentParser, IntentType
from .orchestrators import (
    BuildOrchestrator,
    EpicOrchestrator,
    FixOrchestrator,
    ReviewOrchestrator,
    TestOrchestrator,
)
from .variations import normalize_command


class SimpleModeHandler:
    """Handler for natural language commands in Simple Mode."""

    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
    ):
        """
        Initialize Simple Mode handler.

        Args:
            project_root: Project root directory
            config: Optional project configuration
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or load_config()
        self.intent_parser = IntentParser()

        # Initialize orchestrators
        self.orchestrators = {
            IntentType.BUILD: BuildOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.REVIEW: ReviewOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.FIX: FixOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.TEST: TestOrchestrator(
                project_root=self.project_root, config=self.config
            ),
            IntentType.EPIC: EpicOrchestrator(
                project_root=self.project_root, config=self.config
            ),
        }

    async def handle(self, command: str) -> dict[str, Any]:
        """
        Handle a natural language command.

        Args:
            command: User's natural language command

        Returns:
            Dictionary with execution results
        """
        # Normalize command (expand synonyms)
        normalized = normalize_command(command)

        # Parse intent
        intent = self.intent_parser.parse(normalized)

        # Check if Simple Mode is enabled
        if not self.config.simple_mode.enabled:
            return {
                "success": False,
                "error": "Simple Mode is disabled. Enable it in .tapps-agents/config.yaml",
            }

        # Route to appropriate orchestrator
        orchestrator = self.orchestrators.get(intent.type)
        if not orchestrator:
            return {
                "success": False,
                "error": f"Unknown intent type: {intent.type}. Try: build, review, fix, or test",
                "intent": intent.type.value,
                "confidence": intent.confidence,
            }

        # Execute orchestrator
        try:
            result = await orchestrator.execute(intent, intent.parameters)
            result["intent"] = intent.type.value
            result["confidence"] = intent.confidence
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "intent": intent.type.value,
            }

    def is_simple_mode_enabled(self) -> bool:
        """Check if Simple Mode is enabled."""
        return self.config.simple_mode.enabled

