"""
Background Testing Agent - Executes testing as a Background Agent.

This module provides a Background Agent wrapper around the Tester Agent
that produces versioned, machine-readable testing artifacts.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from ..agents.tester.agent import TesterAgent
from ..core.config import load_config
from .testing_artifact import CoverageSummary, TestingArtifact, TestResult


class BackgroundTestingAgent:
    """
    Background Testing Agent that runs tests and produces artifacts.

    Epic 2 / Story 2.1: Background Cloud Agents - Quality & Testing
    """

    def __init__(
        self,
        worktree_path: Path,
        correlation_id: str | None = None,
        timeout_seconds: float = 600.0,
    ):
        """
        Initialize Background Testing Agent.

        Args:
            worktree_path: Path to worktree where tests should run
            correlation_id: Optional correlation ID for tracking
            timeout_seconds: Maximum execution time in seconds
        """
        self.worktree_path = Path(worktree_path)
        self.correlation_id = correlation_id
        self.timeout_seconds = timeout_seconds
        self.config = load_config()
        self.tester_agent: TesterAgent | None = None
        self._cancelled = False

    async def run_tests(
        self,
        test_path: Path | None = None,
        coverage: bool = True,
    ) -> TestingArtifact:
        """
        Run tests and produce artifact.

        Args:
            test_path: Optional specific test file or directory to run
            coverage: Whether to include coverage analysis

        Returns:
            TestingArtifact with test results
        """
        artifact = TestingArtifact(
            worktree_path=str(self.worktree_path),
            correlation_id=self.correlation_id,
            coverage_enabled=coverage,
        )

        try:
            # Initialize tester agent
            self.tester_agent = TesterAgent(config=self.config)
            await self.tester_agent.activate(project_root=self.worktree_path)

            # Change to worktree directory for test execution
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(self.worktree_path)

                artifact.status = "running"

                # Run tests with timeout
                await asyncio.wait_for(
                    self._execute_tests(artifact, test_path, coverage),
                    timeout=self.timeout_seconds,
                )

                artifact.mark_completed()

            finally:
                os.chdir(original_cwd)
                if self.tester_agent:
                    await self.tester_agent.close()

        except asyncio.TimeoutError:
            artifact.mark_timeout()
        except asyncio.CancelledError:
            artifact.mark_cancelled()
        except Exception as e:
            artifact.mark_failed(str(e))

        # Write artifact to worktree
        self._write_artifact(artifact)

        return artifact

    async def _execute_tests(
        self,
        artifact: TestingArtifact,
        test_path: Path | None = None,
        coverage: bool = True,
    ) -> None:
        """Execute tests and populate artifact."""
        if self._cancelled:
            artifact.mark_cancelled()
            return

        if not self.tester_agent:
            artifact.mark_not_run("Tester agent not initialized")
            return

        # Determine test path
        if test_path:
            test_target = Path(test_path)
        else:
            # Default to tests directory
            test_target = self.worktree_path / "tests"
            if not test_target.exists():
                artifact.mark_not_run(f"Test directory not found: {test_target}")
                return

        # Check if pytest is available
        import shutil

        if not shutil.which("pytest"):
            artifact.mark_not_run("pytest not available in environment")
            return

        # Run tests
        try:
            run_result = await self.tester_agent._run_pytest(
                test_path=test_target if test_target.exists() else None,
                coverage=coverage,
            )

            # Populate artifact from results
            artifact.return_code = run_result.get("return_code", -1)
            artifact.stdout = run_result.get("stdout")
            artifact.stderr = run_result.get("stderr")

            if run_result.get("success"):
                # Parse test summary
                summary = run_result.get("summary", {})
                artifact.total_tests = summary.get("count", 0)
                status = summary.get("status", "unknown").lower()

                if status == "passed":
                    artifact.passed_tests = artifact.total_tests
                    artifact.failed_tests = 0
                elif status == "failed":
                    artifact.failed_tests = artifact.total_tests
                    artifact.passed_tests = 0
                else:
                    # Parse from stdout if available
                    import re

                    if artifact.stdout:
                        passed_match = re.search(
                            r"(\d+) passed", artifact.stdout, re.IGNORECASE
                        )
                        failed_match = re.search(
                            r"(\d+) failed", artifact.stdout, re.IGNORECASE
                        )
                        skipped_match = re.search(
                            r"(\d+) skipped", artifact.stdout, re.IGNORECASE
                        )

                        if passed_match:
                            artifact.passed_tests = int(passed_match.group(1))
                        if failed_match:
                            artifact.failed_tests = int(failed_match.group(1))
                        if skipped_match:
                            artifact.skipped_tests = int(skipped_match.group(1))

                        artifact.total_tests = (
                            artifact.passed_tests
                            + artifact.failed_tests
                            + artifact.skipped_tests
                        )

                # Parse coverage if available
                if coverage:
                    coverage_data = run_result.get("coverage")
                    if coverage_data:
                        artifact.coverage = CoverageSummary(
                            total_lines=coverage_data.get("num_statements", 0),
                            covered_lines=coverage_data.get("covered_lines", 0),
                            coverage_percentage=coverage_data.get("percent_covered", 0.0),
                            branch_coverage=coverage_data.get("percent_covered_branches"),
                            statement_coverage=coverage_data.get("percent_covered", 0.0),
                        )

            else:
                # Test execution failed
                error_msg = run_result.get("error", "Test execution failed")
                artifact.mark_failed(error_msg)

        except Exception as e:
            artifact.mark_failed(str(e))

    def _write_artifact(self, artifact: TestingArtifact) -> None:
        """Write artifact to worktree."""
        reports_dir = self.worktree_path / "reports" / "tests"
        reports_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = reports_dir / "test-report.json"
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(artifact.to_dict(), f, indent=2)

        # Also write coverage summary if available
        if artifact.coverage:
            from dataclasses import asdict
            coverage_path = reports_dir / "coverage-summary.json"
            with open(coverage_path, "w", encoding="utf-8") as f:
                json.dump(asdict(artifact.coverage), f, indent=2)

    def cancel(self) -> None:
        """Cancel running tests."""
        self._cancelled = True
