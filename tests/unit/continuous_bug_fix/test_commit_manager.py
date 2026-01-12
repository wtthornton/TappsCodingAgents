"""
Unit tests for CommitManager.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.continuous_bug_fix.bug_finder import BugInfo
from tapps_agents.continuous_bug_fix.commit_manager import CommitManager

pytestmark = pytest.mark.unit


class TestCommitManager:
    """Test CommitManager functionality."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create a temporary project root."""
        return tmp_path

    @pytest.fixture
    def bug_info(self):
        """Create a sample BugInfo."""
        return BugInfo(
            file_path="src/main.py",
            error_message="TypeError: unsupported operand type",
            test_name="test_function",
            test_file="tests/test_main.py",
            line_number=42,
        )

    @pytest.fixture
    def commit_manager(self, project_root):
        """Create a CommitManager instance."""
        return CommitManager(project_root=project_root, strategy="one-per-bug")

    def test_commit_manager_initialization(self, project_root):
        """Test CommitManager can be initialized."""
        manager = CommitManager(project_root=project_root, strategy="one-per-bug")
        assert manager.project_root == project_root
        assert manager.strategy == "one-per-bug"

    def test_generate_commit_message(self, commit_manager, bug_info):
        """Test commit message generation."""
        message = commit_manager._generate_commit_message(bug_info)
        assert "Fix:" in message
        assert bug_info.error_message.split("\n")[0] in message or bug_info.test_name in message

    def test_generate_batch_commit_message(self, commit_manager, bug_info):
        """Test batch commit message generation."""
        bugs = [bug_info, bug_info]  # Two bugs
        message = commit_manager._generate_batch_commit_message(bugs)
        assert "Fix:" in message
        assert "2 bugs" in message.lower() or "2" in message

    @pytest.mark.asyncio
    @patch("tapps_agents.continuous_bug_fix.commit_manager.is_git_repository")
    async def test_commit_fix_not_git_repository(self, mock_is_git, commit_manager, bug_info):
        """Test commit_fix when not in a git repository."""
        mock_is_git.return_value = False

        result = await commit_manager.commit_fix(bug_info)

        assert result["success"] is False
        assert "Not a git repository" in result["error"]

    @pytest.mark.asyncio
    @patch("tapps_agents.continuous_bug_fix.commit_manager.is_git_repository")
    @patch("tapps_agents.continuous_bug_fix.commit_manager.get_current_branch")
    @patch("tapps_agents.continuous_bug_fix.commit_manager.commit_changes")
    async def test_commit_fix_success(
        self, mock_commit, mock_branch, mock_is_git, commit_manager, bug_info
    ):
        """Test successful commit."""
        mock_is_git.return_value = True
        mock_branch.return_value = "main"
        mock_commit.return_value = "abc123"

        result = await commit_manager.commit_fix(bug_info)

        assert result["success"] is True
        assert result["commit_hash"] == "abc123"
        assert result["branch"] == "main"
        mock_commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("tapps_agents.continuous_bug_fix.commit_manager.is_git_repository")
    @patch("tapps_agents.continuous_bug_fix.commit_manager.commit_changes")
    async def test_commit_fix_error(self, mock_commit, mock_is_git, commit_manager, bug_info):
        """Test commit_fix when commit fails."""
        mock_is_git.return_value = True
        mock_commit.side_effect = Exception("Git error")

        result = await commit_manager.commit_fix(bug_info)

        assert result["success"] is False
        assert "error" in result
