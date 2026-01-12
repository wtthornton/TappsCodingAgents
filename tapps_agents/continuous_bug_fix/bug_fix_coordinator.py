"""
Bug Fix Coordinator - Coordinates bug fixing using FixOrchestrator.
"""

import logging
from pathlib import Path
from typing import Any

from ..core.config import ProjectConfig, load_config
from ..simple_mode.intent_parser import Intent, IntentType
from ..simple_mode.orchestrators.fix_orchestrator import FixOrchestrator

from .bug_finder import BugInfo

logger = logging.getLogger(__name__)


class BugFixCoordinator:
    """Coordinates bug fixing using FixOrchestrator."""

    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
    ) -> None:
        """
        Initialize BugFixCoordinator.

        Args:
            project_root: Project root directory
            config: Project configuration
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or load_config()
        self.fix_orchestrator = FixOrchestrator(
            project_root=self.project_root,
            config=self.config,
        )

    async def fix_bug(
        self,
        bug: BugInfo,
    ) -> dict[str, Any]:
        """
        Fix a single bug using FixOrchestrator.

        Args:
            bug: BugInfo object with bug details

        Returns:
            Dictionary with:
                - success: bool
                - result: FixOrchestrator result dict
                - error: str | None (if failed)
        """
        try:
            # Create intent from bug description
            intent = Intent(
                type=IntentType.FIX,
                original_input=bug.error_message,
                confidence=1.0,
                parameters={"file": bug.file_path, "error": bug.error_message},
            )

            # Prepare parameters for FixOrchestrator
            parameters = {
                "files": [bug.file_path],
                "error_message": bug.error_message,
                "auto_commit": False,  # We handle commits separately
            }

            # Execute fix orchestrator
            result = await self.fix_orchestrator.execute(intent, parameters)

            return {
                "success": result.get("success", False),
                "result": result,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Error fixing bug in {bug.file_path}: {e}", exc_info=True)
            return {
                "success": False,
                "result": None,
                "error": str(e),
            }

    async def verify_fix(
        self,
        bug: BugInfo,
        test_path: str | None = None,
    ) -> bool:
        """
        Re-run tests to verify bug is fixed.

        Args:
            bug: BugInfo object with bug details
            test_path: Test directory or file to run

        Returns:
            True if bug is fixed (test passes), False otherwise
        """
        # Import here to avoid circular dependency
        from .bug_finder import BugFinder

        finder = BugFinder(project_root=self.project_root, config=self.config)
        bugs = await finder.find_bugs(test_path=test_path or "tests/")

        # Check if this specific bug is still present
        for found_bug in bugs:
            if (
                found_bug.file_path == bug.file_path
                and found_bug.test_name == bug.test_name
                and found_bug.test_file == bug.test_file
            ):
                return False  # Bug still exists

        return True  # Bug not found, assume fixed
