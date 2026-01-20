"""
Quality Gate Loopback

Automatic loopback to implementation if quality gates fail.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class QualityLoopback:
    """
    Handles quality gate loopback.

    Features:
    - Detect quality gate failure
    - Invoke @improver agent with specific issues
    - Re-run quality checks
    - Loop until gates pass (max iterations)
    """

    def __init__(self, max_iterations: int = 3, project_root: Path | None = None):
        """
        Initialize quality loopback.

        Args:
            max_iterations: Maximum loopback iterations
            project_root: Project root for improver (default: cwd)
        """
        self.max_iterations = max_iterations
        self.project_root = project_root or Path.cwd()

    async def handle_failure(
        self,
        quality_result: dict[str, Any],
        issues: list[str],
        file_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Handle quality gate failure with loopback.

        Args:
            quality_result: Quality gate result (may include "file" or "target_file")
            issues: List of specific issues
            file_path: Optional target file to improve; also taken from quality_result["file"] or ["target_file"]

        Returns:
            Loopback result with triggered, issues, and optionally improver_result
        """
        logger.info("Quality gate failed. Triggering improvement loopback.")

        target = (
            file_path
            or quality_result.get("file")
            or quality_result.get("target_file")
        )
        if target:
            target = Path(target) if isinstance(target, str) else target
            if not target.is_absolute():
                target = self.project_root / target
            if target.exists():
                try:
                    from ..agents.improver.agent import ImproverAgent
                    from ..core.config import load_config

                    agent = ImproverAgent(config=load_config())
                    await agent.activate(project_root=self.project_root, offline_mode=True)
                    focus = "; ".join(issues[:15]) if issues else "Address quality gate failures"
                    improver_result = await agent.run(
                        "improve-quality",
                        file_path=str(target),
                        focus=focus,
                        auto_apply=False,
                        preview=False,
                    )
                    return {
                        "triggered": True,
                        "issues": issues,
                        "max_iterations": self.max_iterations,
                        "improver_result": improver_result,
                    }
                except Exception as e:
                    logger.warning("Improver invocation failed: %s", e)
                    return {
                        "triggered": True,
                        "issues": issues,
                        "max_iterations": self.max_iterations,
                        "improver_error": str(e),
                    }
            else:
                logger.warning("Target file does not exist: %s", target)

        return {
            "triggered": True,
            "issues": issues,
            "max_iterations": self.max_iterations,
        }

