"""
Background Quality Agent - Executes quality analysis as a Background Agent.

This module provides a Background Agent wrapper around the Reviewer Agent
that produces versioned, machine-readable quality artifacts.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from ..agents.reviewer.agent import ReviewerAgent
from ..core.config import load_config
from .quality_artifact import QualityArtifact, ToolResult


class BackgroundQualityAgent:
    """
    Background Quality Agent that runs quality analysis and produces artifacts.

    Epic 2 / Story 2.1: Background Cloud Agents - Quality & Testing
    """

    def __init__(
        self,
        worktree_path: Path,
        correlation_id: str | None = None,
        timeout_seconds: float = 600.0,
    ):
        """
        Initialize Background Quality Agent.

        Args:
            worktree_path: Path to worktree where analysis should run
            correlation_id: Optional correlation ID for tracking
            timeout_seconds: Maximum execution time in seconds
        """
        self.worktree_path = Path(worktree_path)
        self.correlation_id = correlation_id
        self.timeout_seconds = timeout_seconds
        self.config = load_config()
        self.reviewer_agent: ReviewerAgent | None = None
        self._cancelled = False

    async def run_quality_analysis(
        self,
        target_path: Path | None = None,
    ) -> QualityArtifact:
        """
        Run quality analysis and produce artifact.

        Args:
            target_path: Optional specific file or directory to analyze

        Returns:
            QualityArtifact with analysis results
        """
        artifact = QualityArtifact(
            worktree_path=str(self.worktree_path),
            correlation_id=self.correlation_id,
        )

        try:
            # Initialize reviewer agent
            self.reviewer_agent = ReviewerAgent(config=self.config)
            await self.reviewer_agent.activate(project_root=self.worktree_path)

            # Change to worktree directory for analysis
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(self.worktree_path)

                artifact.status = "running"

                # Run quality checks with timeout
                await asyncio.wait_for(
                    self._run_quality_checks(artifact, target_path),
                    timeout=self.timeout_seconds,
                )

                artifact.mark_completed()

            finally:
                os.chdir(original_cwd)
                if self.reviewer_agent:
                    await self.reviewer_agent.close()

        except TimeoutError:
            artifact.mark_timeout()
        except asyncio.CancelledError:
            artifact.mark_cancelled()
        except Exception as e:
            artifact.mark_failed(str(e))

        # Write artifact to worktree
        self._write_artifact(artifact)

        return artifact

    async def _run_quality_checks(
        self,
        artifact: QualityArtifact,
        target_path: Path | None = None,
    ) -> None:
        """Run individual quality checks."""
        if self._cancelled:
            artifact.mark_cancelled()
            return

        # Determine target for analysis
        if target_path:
            analysis_target = Path(target_path)
        else:
            analysis_target = self.worktree_path

        # 1. Linting (Ruff)
        await self._run_linting(artifact, analysis_target)

        if self._cancelled:
            artifact.mark_cancelled()
            return

        # 2. Type checking (mypy)
        await self._run_type_checking(artifact, analysis_target)

        if self._cancelled:
            artifact.mark_cancelled()
            return

        # 3. Security analysis (Bandit via scorer)
        await self._run_security_analysis(artifact, analysis_target)

        if self._cancelled:
            artifact.mark_cancelled()
            return

        # 4. Complexity analysis
        await self._run_complexity_analysis(artifact, analysis_target)

        if self._cancelled:
            artifact.mark_cancelled()
            return

        # 5. Duplication check (jscpd)
        await self._run_duplication_check(artifact, analysis_target)

    async def _run_linting(
        self, artifact: QualityArtifact, target: Path
    ) -> None:
        """Run linting analysis."""
        if not self.reviewer_agent:
            return

        try:
            # Find Python files to lint
            if target.is_file() and target.suffix == ".py":
                files_to_lint = [target]
            elif target.is_dir():
                files_to_lint = list(target.rglob("*.py"))[:10]  # Limit to 10 files
            else:
                files_to_lint = []

            if not files_to_lint:
                tool_result = ToolResult(
                    tool_name="ruff",
                    available=False,
                    status="unavailable",
                    error_message="No Python files found to lint",
                )
                artifact.add_tool_result("ruff", tool_result)
                return

            # Run linting on first file (representative)
            lint_result = await self.reviewer_agent.lint_file(files_to_lint[0])

            tool_result = ToolResult(
                tool_name="ruff",
                available=lint_result.get("tool") == "ruff",
                status="success" if lint_result.get("tool") == "ruff" else "unavailable",
                issues=lint_result.get("issues", []),
                issue_count=lint_result.get("issue_count", 0),
                error_count=lint_result.get("error_count", 0),
                warning_count=lint_result.get("warning_count", 0),
            )

            # Store score
            artifact.scores["linting"] = lint_result.get("linting_score", 10.0)

            artifact.add_tool_result("ruff", tool_result)

        except Exception as e:
            tool_result = ToolResult(
                tool_name="ruff",
                available=False,
                status="error",
                error_message=str(e),
            )
            artifact.add_tool_result("ruff", tool_result)

    async def _run_type_checking(
        self, artifact: QualityArtifact, target: Path
    ) -> None:
        """Run type checking analysis."""
        if not self.reviewer_agent:
            return

        try:
            # Find Python files to type check
            if target.is_file() and target.suffix == ".py":
                files_to_check = [target]
            elif target.is_dir():
                files_to_check = list(target.rglob("*.py"))[:10]  # Limit to 10 files
            else:
                files_to_check = []

            if not files_to_check:
                tool_result = ToolResult(
                    tool_name="mypy",
                    available=False,
                    status="unavailable",
                    error_message="No Python files found to type check",
                )
                artifact.add_tool_result("mypy", tool_result)
                return

            # Run type checking on first file
            type_result = await self.reviewer_agent.type_check_file(files_to_check[0])

            tool_result = ToolResult(
                tool_name="mypy",
                available=type_result.get("tool") == "mypy",
                status="success" if type_result.get("tool") == "mypy" else "unavailable",
                issues=type_result.get("errors", []),
                issue_count=type_result.get("error_count", 0),
                error_count=type_result.get("error_count", 0),
            )

            # Store score
            artifact.scores["type_checking"] = type_result.get(
                "type_checking_score", 10.0
            )

            artifact.add_tool_result("mypy", tool_result)

        except Exception as e:
            tool_result = ToolResult(
                tool_name="mypy",
                available=False,
                status="error",
                error_message=str(e),
            )
            artifact.add_tool_result("mypy", tool_result)

    async def _run_security_analysis(
        self, artifact: QualityArtifact, target: Path
    ) -> None:
        """Run security analysis."""
        if not self.reviewer_agent:
            return

        try:
            # Use scorer's security analysis
            if target.is_file() and target.suffix == ".py":
                code = target.read_text(encoding="utf-8")
                scores = self.reviewer_agent.scorer.score_file(target, code)
                security_score = scores.get("security_score", 10.0)
            else:
                # For directories, analyze a representative file
                py_files = list(target.rglob("*.py"))[:1] if target.is_dir() else []
                if py_files:
                    code = py_files[0].read_text(encoding="utf-8")
                    scores = self.reviewer_agent.scorer.score_file(py_files[0], code)
                    security_score = scores.get("security_score", 10.0)
                else:
                    security_score = 10.0

            tool_result = ToolResult(
                tool_name="security",
                available=True,
                status="success",
                issue_count=0,  # Would need to extract from scorer
            )

            artifact.scores["security"] = security_score
            artifact.add_tool_result("security", tool_result)

        except Exception as e:
            tool_result = ToolResult(
                tool_name="security",
                available=False,
                status="error",
                error_message=str(e),
            )
            artifact.add_tool_result("security", tool_result)

    async def _run_complexity_analysis(
        self, artifact: QualityArtifact, target: Path
    ) -> None:
        """Run complexity analysis."""
        if not self.reviewer_agent:
            return

        try:
            # Use scorer's complexity analysis
            if target.is_file() and target.suffix == ".py":
                code = target.read_text(encoding="utf-8")
                scores = self.reviewer_agent.scorer.score_file(target, code)
                complexity_score = scores.get("complexity_score", 10.0)
            else:
                # For directories, analyze a representative file
                py_files = list(target.rglob("*.py"))[:1] if target.is_dir() else []
                if py_files:
                    code = py_files[0].read_text(encoding="utf-8")
                    scores = self.reviewer_agent.scorer.score_file(py_files[0], code)
                    complexity_score = scores.get("complexity_score", 10.0)
                else:
                    complexity_score = 10.0

            tool_result = ToolResult(
                tool_name="complexity",
                available=True,
                status="success",
            )

            artifact.scores["complexity"] = complexity_score
            artifact.add_tool_result("complexity", tool_result)

        except Exception as e:
            tool_result = ToolResult(
                tool_name="complexity",
                available=False,
                status="error",
                error_message=str(e),
            )
            artifact.add_tool_result("complexity", tool_result)

    async def _run_duplication_check(
        self, artifact: QualityArtifact, target: Path
    ) -> None:
        """Run duplication check."""
        if not self.reviewer_agent:
            return

        try:
            dup_result = await self.reviewer_agent.check_duplication(target)

            tool_result = ToolResult(
                tool_name="jscpd",
                available=dup_result.get("available", False),
                status="success" if dup_result.get("available") else "unavailable",
                issue_count=0,  # Duplication is a percentage, not issue count
            )

            # Store duplication score
            artifact.scores["duplication"] = dup_result.get(
                "duplication_score", 10.0
            )

            artifact.add_tool_result("jscpd", tool_result)

        except Exception as e:
            tool_result = ToolResult(
                tool_name="jscpd",
                available=False,
                status="error",
                error_message=str(e),
            )
            artifact.add_tool_result("jscpd", tool_result)

    def _write_artifact(self, artifact: QualityArtifact) -> None:
        """Write artifact to worktree."""
        reports_dir = self.worktree_path / "reports" / "quality"
        reports_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = reports_dir / "quality-report.json"
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(artifact.to_dict(), f, indent=2)

    def cancel(self) -> None:
        """Cancel running analysis."""
        self._cancelled = True
