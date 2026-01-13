"""
Proactive Bug Finder - Detects bugs by analyzing code using LLM and static analysis.

This module provides proactive bug discovery without requiring test failures.
It analyzes source code files to find potential bugs, security vulnerabilities,
type issues, and edge cases.
"""

import logging
from pathlib import Path
from typing import Any

from ..agents.reviewer.agent import ReviewerAgent
from ..core.config import ProjectConfig, load_config
from .bug_finder import BugInfo

logger = logging.getLogger(__name__)


class ProactiveBugFinder:
    """Finds bugs by proactively analyzing code using reviewer agent and static analysis."""

    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
    ) -> None:
        """
        Initialize ProactiveBugFinder.

        Args:
            project_root: Project root directory (default: current directory)
            config: Project configuration (optional)
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or load_config()
        self.reviewer_agent = None  # Lazy initialization

    async def _get_reviewer_agent(self) -> ReviewerAgent:
        """Get or create reviewer agent instance."""
        if self.reviewer_agent is None:
            self.reviewer_agent = ReviewerAgent()
            await self.reviewer_agent.activate(project_root=self.project_root)
        return self.reviewer_agent

    async def find_bugs(
        self,
        target_path: str | None = None,
        max_bugs: int = 20,
        file_pattern: str = "**/*.py",
    ) -> list[BugInfo]:
        """
        Analyze code and return list of potential bugs found.

        Args:
            target_path: Directory or file to analyze (default: project root)
            max_bugs: Maximum number of bugs to find (default: 20)
            file_pattern: Glob pattern to match files (default: **/*.py)

        Returns:
            List of BugInfo objects representing detected bugs
        """
        # Determine target path
        if target_path is None:
            target_path = str(self.project_root)
        target_path_obj = Path(target_path)

        # Collect Python files to analyze
        files_to_analyze = self._collect_files(target_path_obj, file_pattern)
        if not files_to_analyze:
            logger.warning(f"No files found matching pattern {file_pattern} in {target_path}")
            return []

        logger.info(f"Analyzing {len(files_to_analyze)} files for potential bugs...")

        # Analyze files and collect bugs
        bugs: list[BugInfo] = []
        reviewer = await self._get_reviewer_agent()

        # Analyze files (limit to prevent timeout)
        max_files = min(50, len(files_to_analyze))  # Limit to 50 files per run
        for file_path in files_to_analyze[:max_files]:
            if len(bugs) >= max_bugs:
                break

            try:
                file_bugs = await self._analyze_file(reviewer, file_path)
                bugs.extend(file_bugs)
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}", exc_info=True)
                continue

        logger.info(f"Found {len(bugs)} potential bugs from code analysis")
        return bugs[:max_bugs]  # Return up to max_bugs

    def _collect_files(
        self,
        target_path: Path,
        pattern: str,
    ) -> list[Path]:
        """
        Collect files to analyze based on pattern.

        Args:
            target_path: Target directory or file
            pattern: Glob pattern to match files

        Returns:
            List of file paths to analyze
        """
        files: list[Path] = []

        if target_path.is_file():
            # Single file
            if target_path.suffix == ".py":
                files.append(target_path)
        else:
            # Directory - use glob pattern
            files.extend(target_path.glob(pattern))

        # Filter out test files, virtual environments, and build artifacts
        filtered_files = []
        exclude_patterns = [
            "test_",
            "/tests/",
            "/test/",
            "__pycache__",
            ".venv",
            "venv",
            ".pytest_cache",
            ".tox",
            "build",
            "dist",
            ".eggs",
        ]

        for file_path in files:
            file_str = str(file_path)
            # Skip if matches exclude pattern
            if any(pattern in file_str for pattern in exclude_patterns):
                continue
            # Only include Python files
            if file_path.suffix == ".py":
                filtered_files.append(file_path)

        return filtered_files

    async def _analyze_file(
        self,
        reviewer: ReviewerAgent,
        file_path: Path,
    ) -> list[BugInfo]:
        """
        Analyze a single file and extract potential bugs.

        Args:
            reviewer: ReviewerAgent instance
            file_path: File to analyze

        Returns:
            List of BugInfo objects found in the file
        """
        bugs: list[BugInfo] = []

        try:
            # Use reviewer agent to analyze the file
            # Review with scoring and LLM feedback to get bug findings
            review_result = await reviewer.review_file(
                file_path=file_path,
                include_scoring=True,
                include_llm_feedback=True,
            )

            # Extract bugs from review result
            file_bugs = self._extract_bugs_from_review(review_result, file_path)
            bugs.extend(file_bugs)

        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")
            # Return empty list on error

        return bugs

    def _extract_bugs_from_review(
        self,
        review_result: dict[str, Any],
        file_path: Path,
    ) -> list[BugInfo]:
        """
        Extract bug information from reviewer result.

        Args:
            review_result: Result dictionary from reviewer agent
            file_path: File that was reviewed

        Returns:
            List of BugInfo objects
        """
        bugs: list[BugInfo] = []

        # Make path relative to project root
        try:
            if file_path.is_absolute():
                rel_path = str(file_path.relative_to(self.project_root))
            else:
                rel_path = str(file_path)
        except ValueError:
            rel_path = str(file_path)

        # Extract issues from review result
        issues = review_result.get("issues", [])
        feedback_raw = review_result.get("feedback", "")
        scores = review_result.get("scores", {})

        # Handle feedback - can be string or dict
        feedback_text = ""
        if isinstance(feedback_raw, str):
            feedback_text = feedback_raw
        elif isinstance(feedback_raw, dict):
            # Extract text from dict (may have 'text' or 'message' key)
            feedback_text = feedback_raw.get("text", feedback_raw.get("message", str(feedback_raw)))

        # Check if there are security issues
        security_score = scores.get("security", {}).get("score", 10.0)
        if security_score < 7.0:
            bugs.append(
                BugInfo(
                    file_path=rel_path,
                    error_message=f"Security vulnerability detected (score: {security_score}/10). Review security issues in this file.",
                    test_name="proactive_security_scan",
                    test_file="proactive_analysis",
                    line_number=None,
                )
            )

        # Extract specific issues from issues list
        if issues:
            for issue in issues[:5]:  # Limit to 5 issues per file
                issue_type = issue.get("type", "unknown")
                issue_msg = issue.get("message", "Issue detected")
                line_num = issue.get("line", None)

                bugs.append(
                    BugInfo(
                        file_path=rel_path,
                        error_message=f"[{issue_type}] {issue_msg}",
                        test_name="proactive_code_analysis",
                        test_file="proactive_analysis",
                        line_number=line_num,
                    )
                )

        # If no structured issues but feedback exists, parse feedback for bug mentions
        elif feedback_text and len(bugs) == 0:
            # Use LLM feedback to identify potential bugs
            # Look for common bug indicators in feedback
            bug_keywords = [
                "bug",
                "error",
                "vulnerability",
                "issue",
                "problem",
                "incorrect",
                "wrong",
                "missing",
                "broken",
                "fails",
            ]

            feedback_lower = feedback_text.lower()
            if any(keyword in feedback_lower for keyword in bug_keywords):
                # Extract relevant section of feedback
                feedback_snippet = feedback_text[:300]  # First 300 chars

                bugs.append(
                    BugInfo(
                        file_path=rel_path,
                        error_message=f"Potential issue detected: {feedback_snippet}",
                        test_name="proactive_code_review",
                        test_file="proactive_analysis",
                        line_number=None,
                    )
                )

        return bugs
