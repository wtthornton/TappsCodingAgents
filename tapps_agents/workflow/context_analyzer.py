"""
Context Analyzer for Workflow Suggestions

Analyzes project context to provide relevant workflow suggestions.
Epic 9 / Story 9.3: Context-Aware Suggestions
"""

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """Project context information."""

    recent_changes: list[str] = field(default_factory=list)  # Modified files
    branch_name: str | None = None
    project_type: str | None = None
    has_git: bool = False
    modified_files_count: int = 0
    tech_stack: dict[str, Any] | None = None
    # Epic 13: Enhanced context
    recent_commits: list[dict[str, Any]] = field(default_factory=list)  # Recent commit information
    pr_context: dict[str, Any] | None = None  # PR/branch context
    file_types: dict[str, int] = field(default_factory=dict)  # File type distribution


class ContextAnalyzer:
    """Analyzes project context for workflow suggestions."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize context analyzer.

        Args:
            project_root: Project root directory (defaults to current directory)
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()

    def analyze(self) -> ProjectContext:
        """
        Analyze project context.

        Returns:
            ProjectContext with analyzed information
        """
        context = ProjectContext()

        # Check for git
        context.has_git = self._check_git_available()

        if context.has_git:
            try:
                context.branch_name = self._get_branch_name()
                context.recent_changes = self._get_recent_changes()
                context.modified_files_count = len(context.recent_changes) if context.recent_changes else 0
                # Epic 13: Enhanced git analysis
                context.recent_commits = self._get_recent_commits()
                context.pr_context = self._analyze_pr_context(context.branch_name)
            except Exception as e:
                logger.warning(f"Failed to analyze git context: {e}")

        # Detect project type
        context.project_type = self._detect_project_type()
        
        # Epic 13: Analyze file types
        if context.recent_changes:
            context.file_types = self._analyze_file_types(context.recent_changes)

        return context

    def _check_git_available(self) -> bool:
        """Check if git is available and project is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.project_root,
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False

    def _get_branch_name(self) -> str | None:
        """Get current git branch name."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return None

    def _get_recent_changes(self) -> list[str]:
        """Get list of recently modified files."""
        try:
            # Get modified files from git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                files = []
                for line in result.stdout.strip().split("\n"):
                    if line:
                        # Extract filename (after status codes)
                        file_path = line[3:].strip()
                        if file_path:
                            files.append(file_path)
                return files[:20]  # Limit to 20 files
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return []

    def _detect_project_type(self) -> str | None:
        """Detect project type from files and structure."""
        # Check for common project indicators
        if (self.project_root / "package.json").exists():
            return "javascript"
        if (self.project_root / "pyproject.toml").exists() or (self.project_root / "requirements.txt").exists():
            return "python"
        if (self.project_root / "Cargo.toml").exists():
            return "rust"
        if (self.project_root / "go.mod").exists():
            return "go"
        if (self.project_root / "pom.xml").exists() or (self.project_root / "build.gradle").exists():
            return "java"
        return None

    def _get_recent_commits(self, limit: int = 5) -> list[dict[str, Any]]:
        """Get recent commit information (Epic 13)."""
        try:
            result = subprocess.run(
                ["git", "log", f"-{limit}", "--pretty=format:%H|%s|%an|%ad", "--date=iso"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0:
                commits = []
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split("|", 3)
                        if len(parts) >= 3:
                            commits.append({
                                "hash": parts[0][:8],
                                "message": parts[1],
                                "author": parts[2],
                                "date": parts[3] if len(parts) > 3 else None,
                            })
                return commits
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return []

    def _analyze_pr_context(self, branch_name: str | None) -> dict[str, Any] | None:
        """Analyze PR context from branch name (Epic 13)."""
        if not branch_name:
            return None

        context = {"branch_name": branch_name}
        
        # Check if branch suggests PR context
        branch_lower = branch_name.lower()
        if "pr" in branch_lower or "pull" in branch_lower:
            context["is_pr_branch"] = True
        if "feature" in branch_lower or "feat" in branch_lower:
            context["branch_type"] = "feature"
        elif "fix" in branch_lower or "bug" in branch_lower:
            context["branch_type"] = "fix"
        elif "hotfix" in branch_lower:
            context["branch_type"] = "hotfix"
        elif "refactor" in branch_lower:
            context["branch_type"] = "refactor"
        else:
            context["branch_type"] = "other"

        return context

    def _analyze_file_types(self, files: list[str]) -> dict[str, int]:
        """Analyze file type distribution (Epic 13)."""
        types = {
            "code": 0,
            "test": 0,
            "doc": 0,
            "config": 0,
            "data": 0,
        }
        
        for file in files:
            file_lower = file.lower()
            if any(ext in file_lower for ext in [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"]):
                types["code"] += 1
            elif "test" in file_lower or "spec" in file_lower:
                types["test"] += 1
            elif any(ext in file_lower for ext in [".md", ".txt", ".rst", ".adoc"]):
                types["doc"] += 1
            elif any(ext in file_lower for ext in [".json", ".yaml", ".yml", ".toml", ".ini", ".conf"]):
                types["config"] += 1
            elif any(ext in file_lower for ext in [".csv", ".json", ".xml", ".sql"]):
                types["data"] += 1
            else:
                types["code"] += 1  # Default to code
        
        return types

