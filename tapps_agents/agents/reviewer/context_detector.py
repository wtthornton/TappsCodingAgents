"""
File context detection for context-aware quality gates.

Phase 6 (P1): Detect if files are new, modified, or existing to apply appropriate quality thresholds.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Time thresholds for file age (in days)
NEW_FILE_THRESHOLD_DAYS = 7  # Files created within 7 days are considered "new"


@dataclass
class FileContext:
    """File context information for quality gate decisions."""

    status: str  # "new", "modified", or "existing"
    age_days: float | None = None  # Age of file in days (if determinable)
    git_status: str | None = None  # Git status (untracked, modified, tracked)
    confidence: float = 1.0  # Confidence in context detection (0.0-1.0)

    def is_new(self) -> bool:
        """Check if file is considered new."""
        return self.status == "new"

    def is_modified(self) -> bool:
        """Check if file is considered modified."""
        return self.status == "modified"

    def is_existing(self) -> bool:
        """Check if file is considered existing (unchanged)."""
        return self.status == "existing"


class FileContextDetector:
    """Detect file context (new, modified, or existing) for quality gate decisions."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize context detector.

        Args:
            project_root: Optional project root path (auto-detected if not provided)
        """
        self.project_root = project_root or self._find_project_root()
        self._has_git = self._check_git_available()

    def _find_project_root(self) -> Path | None:
        """Find project root by looking for .git directory."""
        current = Path.cwd()
        for _ in range(10):  # Max 10 levels up
            if (current / ".git").exists():
                return current
            if current.parent == current:
                break
            current = current.parent
        return None

    def _check_git_available(self) -> bool:
        """Check if git is available in PATH."""
        try:
            subprocess.run(
                [sys.executable, "-m", "git", "--version"],
                capture_output=True,
                timeout=5,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def detect_context(self, file_path: Path) -> FileContext:
        """
        Detect file context (new, modified, or existing).

        Phase 6 (P1): Context-aware quality gates.

        Args:
            file_path: Path to the file to analyze

        Returns:
            FileContext with status and metadata
        """
        # Try git-based detection first (most accurate)
        if self._has_git and self.project_root:
            try:
                git_context = self._detect_via_git(file_path)
                if git_context:
                    return git_context
            except Exception:
                # Fallback to file-based detection if git fails
                pass

        # Fallback to file metadata-based detection
        return self._detect_via_file_metadata(file_path)

    def _detect_via_git(self, file_path: Path) -> FileContext | None:
        """Detect file context using git status."""
        if not self.project_root:
            return None

        try:
            # Get relative path from project root
            try:
                rel_path = file_path.relative_to(self.project_root)
            except ValueError:
                # File not in project root
                return None

            # Run git status for this file
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", str(rel_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return None

            status_line = result.stdout.strip()
            if not status_line:
                # File is tracked and unmodified
                return FileContext(
                    status="existing",
                    git_status="tracked",
                    confidence=1.0,
                )

            # Parse git status output
            # Format: XY filename
            # X = index status, Y = working tree status
            # ?? = untracked (new file)
            # M  = modified in working tree
            # A  = added to index
            # M  = modified in index

            status_code = status_line[:2]
            if status_code == "??":
                # Untracked file (new)
                return FileContext(
                    status="new",
                    git_status="untracked",
                    confidence=1.0,
                )
            elif "M" in status_code or "A" in status_code:
                # Modified or added file
                return FileContext(
                    status="modified",
                    git_status=status_code,
                    confidence=1.0,
                )

            # Default to existing if status unclear
            return FileContext(
                status="existing",
                git_status=status_code,
                confidence=0.8,
            )

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _detect_via_file_metadata(self, file_path: Path) -> FileContext:
        """
        Detect file context using file metadata (creation/modification time).

        Less accurate than git but works when git is not available.
        """
        if not file_path.exists():
            # File doesn't exist (shouldn't happen in practice)
            return FileContext(status="new", confidence=0.5)

        try:
            # Get file modification time
            mtime = file_path.stat().st_mtime
            file_age = (datetime.now().timestamp() - mtime) / (24 * 60 * 60)  # Age in days

            # Files created within threshold are considered "new"
            if file_age <= NEW_FILE_THRESHOLD_DAYS:
                return FileContext(
                    status="new",
                    age_days=file_age,
                    confidence=0.7,  # Lower confidence for file-based detection
                )

            # Older files are considered "existing"
            return FileContext(
                status="existing",
                age_days=file_age,
                confidence=0.7,
            )

        except Exception:
            # Fallback to "existing" if we can't determine
            return FileContext(status="existing", confidence=0.5)
