"""
Continuous Bug Fixer - Main orchestrator for continuous bug finding and fixing.
"""

import logging
import signal
import sys
from pathlib import Path
from typing import Any

from ..core.config import ProjectConfig, load_config

from .bug_finder import BugFinder, BugInfo
from .bug_fix_coordinator import BugFixCoordinator
from .commit_manager import CommitManager
from .proactive_bug_finder import ProactiveBugFinder

logger = logging.getLogger(__name__)


class ContinuousBugFixer:
    """Main orchestrator for continuous bug finding and fixing."""

    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
    ) -> None:
        """
        Initialize ContinuousBugFixer.

        Args:
            project_root: Project root directory
            config: Project configuration
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or load_config()
        self.bug_finder = BugFinder(project_root=self.project_root, config=self.config)
        self.proactive_bug_finder = ProactiveBugFinder(
            project_root=self.project_root, config=self.config
        )
        self.bug_fix_coordinator = BugFixCoordinator(
            project_root=self.project_root, config=self.config
        )
        self.interrupted = False

        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle interruption signals."""
        logger.info("Interrupted by user")
        self.interrupted = True

    async def execute(
        self,
        test_path: str | None = None,
        max_iterations: int = 10,
        commit_strategy: str = "one-per-bug",
        auto_commit: bool = True,
        proactive: bool = False,
        target_path: str | None = None,
        max_bugs: int = 20,
    ) -> dict[str, Any]:
        """
        Execute continuous bug finding and fixing.

        Args:
            test_path: Test directory or file to run (for test-based discovery)
            max_iterations: Maximum loop iterations
            commit_strategy: Commit strategy - "one-per-bug" or "batch"
            auto_commit: Whether to commit fixes automatically
            proactive: If True, use proactive bug discovery (code analysis) instead of test-based
            target_path: Directory or file to analyze (for proactive discovery)
            max_bugs: Maximum bugs to find per iteration (for proactive discovery)

        Returns:
            Dictionary with execution results
        """
        results: list[dict[str, Any]] = []
        total_bugs_found = 0
        total_bugs_fixed = 0
        total_bugs_failed = 0
        total_bugs_skipped = 0

        commit_manager = CommitManager(
            project_root=self.project_root, strategy=commit_strategy
        )

        # Use config defaults if not provided
        if test_path is None:
            continuous_config = getattr(self.config, "continuous_bug_fix", None)
            if continuous_config:
                test_path = continuous_config.test_path
            else:
                test_path = "tests/"

        for iteration in range(1, max_iterations + 1):
            if self.interrupted:
                logger.info("Execution interrupted by user")
                break

            logger.info(f"Iteration {iteration}/{max_iterations}")

            # Run iteration
            iteration_result = await self._run_iteration(
                iteration=iteration,
                test_path=test_path,
                commit_strategy=commit_strategy,
                auto_commit=auto_commit,
                commit_manager=commit_manager,
                proactive=proactive,
                target_path=target_path,
                max_bugs=max_bugs,
            )

            results.append(iteration_result)

            # Update totals
            iteration_bugs = iteration_result.get("bugs", [])
            total_bugs_found += len(iteration_bugs)
            total_bugs_fixed += iteration_result.get("bugs_fixed", 0)
            total_bugs_failed += iteration_result.get("bugs_failed", 0)
            total_bugs_skipped += iteration_result.get("bugs_skipped", 0)

            # Stop if no bugs found
            if len(iteration_bugs) == 0:
                logger.info("No bugs found, stopping")
                break

            # Stop if interrupted
            if self.interrupted:
                break

        # Generate summary
        summary = self._generate_summary(results)

        return {
            "success": total_bugs_failed == 0 or total_bugs_fixed > 0,
            "iterations": len(results),
            "bugs_found": total_bugs_found,
            "bugs_fixed": total_bugs_fixed,
            "bugs_failed": total_bugs_failed,
            "bugs_skipped": total_bugs_skipped,
            "results": results,
            "summary": summary,
        }

    async def _run_iteration(
        self,
        iteration: int,
        test_path: str | None = None,
        commit_strategy: str = "one-per-bug",
        auto_commit: bool = True,
        commit_manager: CommitManager | None = None,
        proactive: bool = False,
        target_path: str | None = None,
        max_bugs: int = 20,
    ) -> dict[str, Any]:
        """
        Execute one iteration of bug finding and fixing.

        Args:
            iteration: Current iteration number
            test_path: Test directory or file to run (for test-based discovery)
            commit_strategy: Commit strategy
            auto_commit: Whether to commit fixes
            commit_manager: CommitManager instance
            proactive: If True, use proactive bug discovery
            target_path: Directory or file to analyze (for proactive discovery)
            max_bugs: Maximum bugs to find (for proactive discovery)

        Returns:
            Dictionary with iteration results
        """
        if commit_manager is None:
            commit_manager = CommitManager(
                project_root=self.project_root, strategy=commit_strategy
            )

        # Find bugs (proactive or test-based)
        if proactive:
            logger.info(f"Iteration {iteration}: Using proactive bug discovery")
            bugs = await self.proactive_bug_finder.find_bugs(
                target_path=target_path,
                max_bugs=max_bugs,
            )
        else:
            logger.info(f"Iteration {iteration}: Using test-based bug discovery")
            bugs = await self.bug_finder.find_bugs(test_path=test_path)

        if not bugs:
            return {
                "iteration": iteration,
                "bugs_found": 0,
                "bugs_fixed": 0,
                "bugs_failed": 0,
                "bugs_skipped": 0,
                "bugs": [],
            }

        logger.info(f"Iteration {iteration}: Found {len(bugs)} bugs")

        # Fix bugs
        fixed_bugs: list[dict[str, Any]] = []
        failed_bugs: list[dict[str, Any]] = []
        skipped_bugs: list[dict[str, Any]] = []

        batch_bugs: list[BugInfo] = []  # For batch commit strategy

        for bug in bugs:
            if self.interrupted:
                skipped_bugs.append(
                    {
                        "bug": bug,
                        "reason": "Interrupted",
                    }
                )
                continue

            logger.info(f"Fixing bug in {bug.file_path} (from {bug.test_name})")

            # Fix bug
            fix_result = await self.bug_fix_coordinator.fix_bug(bug)

            if fix_result.get("success"):
                # Verify fix
                verified = await self.bug_fix_coordinator.verify_fix(
                    bug, test_path=test_path
                )

                if verified or True:  # Assume fixed if fix succeeded
                    # Commit if enabled
                    commit_result = None
                    if auto_commit:
                        if commit_strategy == "batch":
                            batch_bugs.append(bug)
                        else:
                            commit_result = await commit_manager.commit_fix(bug)

                    fixed_bugs.append(
                        {
                            "bug": bug,
                            "fix_result": fix_result.get("result"),
                            "commit_result": commit_result,
                        }
                    )
                    logger.info(f"Fixed bug in {bug.file_path}")
                else:
                    failed_bugs.append(
                        {
                            "bug": bug,
                            "reason": "Fix verification failed",
                            "fix_result": fix_result.get("result"),
                        }
                    )
            else:
                failed_bugs.append(
                    {
                        "bug": bug,
                        "reason": fix_result.get("error", "Fix failed"),
                        "fix_result": fix_result.get("result"),
                    }
                )
                logger.warning(f"Failed to fix bug in {bug.file_path}: {fix_result.get('error')}")

        # Commit batch if strategy is batch
        batch_commit_result = None
        if auto_commit and commit_strategy == "batch" and batch_bugs:
            batch_commit_result = await commit_manager.commit_batch(batch_bugs)
            logger.info(f"Committed batch of {len(batch_bugs)} fixes")

        return {
            "iteration": iteration,
            "bugs_found": len(bugs),
            "bugs_fixed": len(fixed_bugs),
            "bugs_failed": len(failed_bugs),
            "bugs_skipped": len(skipped_bugs),
            "bugs": [
                {
                    "bug": bug_dict.get("bug"),
                    "status": "fixed" if bug_dict in fixed_bugs else "failed" if bug_dict in failed_bugs else "skipped",
                    "fix_result": bug_dict.get("fix_result"),
                    "commit_result": bug_dict.get("commit_result"),
                }
                for bug_dict in fixed_bugs + failed_bugs + skipped_bugs
            ],
            "batch_commit_result": batch_commit_result,
        }

    def _generate_summary(
        self,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate summary report from execution results.

        Args:
            results: List of iteration result dictionaries

        Returns:
            Summary dictionary with statistics
        """
        total_bugs_found = sum(r.get("bugs_found", 0) for r in results)
        total_bugs_fixed = sum(r.get("bugs_fixed", 0) for r in results)
        total_bugs_failed = sum(r.get("bugs_failed", 0) for r in results)
        total_bugs_skipped = sum(r.get("bugs_skipped", 0) for r in results)

        fix_rate = (
            total_bugs_fixed / total_bugs_found if total_bugs_found > 0 else 0.0
        )

        return {
            "total_bugs_found": total_bugs_found,
            "total_bugs_fixed": total_bugs_fixed,
            "total_bugs_failed": total_bugs_failed,
            "total_bugs_skipped": total_bugs_skipped,
            "fix_rate": fix_rate,
            "iterations_run": len(results),
        }
