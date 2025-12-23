"""
Dockerfile Analyzer

Analyzes Dockerfiles for common issues (Python path, WORKDIR, COPY order).
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DockerfileIssue:
    """Represents an issue found in a Dockerfile."""

    issue_type: str
    line_number: int
    description: str
    severity: str  # low, medium, high, critical
    suggested_fix: str
    confidence: float = 0.0


class DockerfileAnalyzer:
    """
    Analyzes Dockerfiles for common issues.

    Detects:
    - ModuleNotFoundError: No module named 'src' (WORKDIR/Python path)
    - COPY before WORKDIR
    - Missing 'python -m' prefix for uvicorn
    - Incorrect PYTHONPATH
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize Dockerfile analyzer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path.cwd()

    def analyze(self, dockerfile_path: Path | str) -> list[DockerfileIssue]:
        """
        Analyze a Dockerfile for issues.

        Args:
            dockerfile_path: Path to Dockerfile

        Returns:
            List of identified issues
        """
        dockerfile = Path(dockerfile_path)
        if not dockerfile.is_absolute():
            dockerfile = self.project_root / dockerfile

        if not dockerfile.exists():
            raise FileNotFoundError(f"Dockerfile not found: {dockerfile}")

        content = dockerfile.read_text(encoding="utf-8")
        lines = content.split("\n")

        issues: list[DockerfileIssue] = []

        # Check for WORKDIR/Python path issues
        workdir_line = None
        copy_lines: list[tuple[int, str]] = []
        python_cmd_line = None

        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()

            if line_stripped.startswith("WORKDIR"):
                workdir_line = i
            elif line_stripped.startswith("COPY"):
                copy_lines.append((i, line_stripped))
            elif "uvicorn" in line_stripped or "python" in line_stripped:
                if "CMD" in line_stripped or "ENTRYPOINT" in line_stripped:
                    python_cmd_line = i

        # Issue: COPY before WORKDIR
        if workdir_line and copy_lines:
            for copy_line_num, _ in copy_lines:
                if copy_line_num < workdir_line:
                    issues.append(
                        DockerfileIssue(
                            issue_type="copy_before_workdir",
                            line_number=copy_line_num,
                            description="COPY command appears before WORKDIR",
                            severity="high",
                            suggested_fix="Move WORKDIR before COPY commands",
                            confidence=0.9,
                        )
                    )

        # Issue: Missing 'python -m' for uvicorn
        if python_cmd_line:
            cmd_line = lines[python_cmd_line - 1]
            if "uvicorn" in cmd_line and "python -m" not in cmd_line:
                issues.append(
                    DockerfileIssue(
                        issue_type="missing_python_m",
                        line_number=python_cmd_line,
                        description="uvicorn command missing 'python -m' prefix",
                        severity="high",
                        suggested_fix="Use 'python -m uvicorn' instead of 'uvicorn'",
                        confidence=0.95,
                    )
                )

        # Issue: Incorrect PYTHONPATH
        pythonpath_set = False
        for i, line in enumerate(lines, 1):
            if "PYTHONPATH" in line and "=" in line:
                pythonpath_set = True
                # Check if PYTHONPATH is set incorrectly
                if "/app" not in line and "/src" not in line:
                    issues.append(
                        DockerfileIssue(
                            issue_type="incorrect_pythonpath",
                            line_number=i,
                            description="PYTHONPATH may be set incorrectly",
                            severity="medium",
                            suggested_fix="Set PYTHONPATH to include /app or /src",
                            confidence=0.7,
                        )
                    )

        # Issue: Potential ModuleNotFoundError for 'src'
        if workdir_line:
            workdir_value = lines[workdir_line - 1].split()[1] if len(lines[workdir_line - 1].split()) > 1 else ""
            if workdir_value and "src" not in workdir_value:
                # Check if code is in src/ but WORKDIR doesn't account for it
                for copy_line_num, copy_line in copy_lines:
                    if "src/" in copy_line and workdir_value != "/app/src":
                        issues.append(
                            DockerfileIssue(
                                issue_type="python_path_mismatch",
                                line_number=workdir_line,
                                description="WORKDIR may not match source structure",
                                severity="critical",
                                suggested_fix=f"Set WORKDIR to match source structure or adjust PYTHONPATH",
                                confidence=0.85,
                            )
                        )

        return issues

    def suggest_fixes(self, issues: list[DockerfileIssue]) -> dict[str, Any]:
        """
        Suggest fixes for Dockerfile issues.

        Args:
            issues: List of issues

        Returns:
            Suggested fixes
        """
        fixes: dict[str, Any] = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
        }

        for issue in issues:
            fix_info = {
                "issue": issue.description,
                "line": issue.line_number,
                "fix": issue.suggested_fix,
                "confidence": issue.confidence,
            }

            if issue.severity in ["critical", "high"]:
                fixes["high_priority"].append(fix_info)
            elif issue.severity == "medium":
                fixes["medium_priority"].append(fix_info)
            else:
                fixes["low_priority"].append(fix_info)

        return fixes

