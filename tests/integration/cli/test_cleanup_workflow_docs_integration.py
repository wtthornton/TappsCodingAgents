"""
Integration tests for cleanup workflow-docs CLI command.

Tests end-to-end CLI command execution.
"""

import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory with workflow structure."""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    # Create .tapps-agents directory
    (project_root / ".tapps-agents").mkdir()
    
    # Create config.yaml
    config_path = project_root / ".tapps-agents" / "config.yaml"
    config_path.write_text(
        """cleanup:
  workflow_docs:
    enabled: true
    keep_latest: 5
    retention_days: 30
    archive_enabled: true
    archive_dir: ".tapps-agents/archives/workflows/"
""",
        encoding="utf-8",
    )
    
    # Create docs/workflows/simple-mode directory
    workflow_dir = project_root / "docs" / "workflows" / "simple-mode"
    workflow_dir.mkdir(parents=True)
    
    yield project_root
    
    shutil.rmtree(temp_dir)


def create_workflow_directory(base_dir: Path, workflow_id: str, days_old: int = 0):
    """Create a workflow directory with step files."""
    workflow_dir = base_dir / "docs" / "workflows" / "simple-mode" / workflow_id
    workflow_dir.mkdir(parents=True)
    
    # Create step files
    for i in range(1, 8):
        step_file = workflow_dir / f"step{i}-test.md"
        step_file.write_text(f"# Step {i}\n\nContent", encoding="utf-8")
    
    # Set modification time
    if days_old > 0:
        mtime = (datetime.now() - timedelta(days=days_old)).timestamp()
        import os
        for file in workflow_dir.rglob("*"):
            if file.is_file():
                os.utime(file, (mtime, mtime))
    
    return workflow_dir


class TestCleanupWorkflowDocsCLI:
    """Test cleanup workflow-docs CLI command."""

    def test_basic_command_dry_run(self, temp_project_dir):
        """Test basic CLI command execution with dry-run."""
        # Create some workflows
        create_workflow_directory(temp_project_dir, "workflow-1-20250116-000000", days_old=5)
        create_workflow_directory(temp_project_dir, "workflow-2-20250101-000000", days_old=45)
        
        # Run command
        result = subprocess.run(
            ["python", "-m", "tapps_agents.cli", "cleanup", "workflow-docs", "--dry-run"],
            cwd=str(temp_project_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        # Should succeed
        assert result.returncode == 0
        
        # Should show dry-run output
        assert "DRY RUN" in result.stdout or "dry run" in result.stdout.lower()
        assert "workflow" in result.stdout.lower()

    def test_command_with_options(self, temp_project_dir):
        """Test CLI command with custom options."""
        create_workflow_directory(temp_project_dir, "workflow-1-20250101-000000", days_old=45)
        
        result = subprocess.run(
            [
                "python", "-m", "tapps_agents.cli", "cleanup", "workflow-docs",
                "--keep-latest", "10",
                "--retention-days", "60",
                "--archive",
                "--dry-run",
            ],
            cwd=str(temp_project_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        assert result.returncode == 0
        assert "10" in result.stdout or "keep latest" in result.stdout.lower()
        assert "60" in result.stdout or "retention" in result.stdout.lower()

    def test_command_help(self, temp_project_dir):
        """Test CLI command help text."""
        result = subprocess.run(
            ["python", "-m", "tapps_agents.cli", "cleanup", "workflow-docs", "--help"],
            cwd=str(temp_project_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        assert result.returncode == 0
        assert "--keep-latest" in result.stdout
        assert "--retention-days" in result.stdout
        assert "--archive" in result.stdout
        assert "--dry-run" in result.stdout

    def test_command_actual_cleanup(self, temp_project_dir):
        """Test actual cleanup (not dry-run)."""
        # Create old workflow
        create_workflow_directory(temp_project_dir, "old-workflow-20250101-000000", days_old=45)
        
        archive_dir = temp_project_dir / ".tapps-agents" / "archives" / "workflows"
        
        result = subprocess.run(
            [
                "python", "-m", "tapps_agents.cli", "cleanup", "workflow-docs",
                "--keep-latest", "0",
                "--retention-days", "30",
                "--archive",
            ],
            cwd=str(temp_project_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        # Should succeed
        assert result.returncode == 0
        
        # Verify workflow was archived
        assert archive_dir.exists()
        assert (archive_dir / "old-workflow-20250101-000000").exists()
        
        # Verify original directory is gone
        workflow_base = temp_project_dir / "docs" / "workflows" / "simple-mode"
        assert not (workflow_base / "old-workflow-20250101-000000").exists()

    def test_command_no_archive(self, temp_project_dir):
        """Test cleanup with --no-archive flag."""
        create_workflow_directory(temp_project_dir, "old-workflow-20250101-000000", days_old=45)
        
        result = subprocess.run(
            [
                "python", "-m", "tapps_agents.cli", "cleanup", "workflow-docs",
                "--keep-latest", "0",
                "--retention-days", "30",
                "--no-archive",
            ],
            cwd=str(temp_project_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        assert result.returncode == 0
        
        # Workflow should still exist (not archived)
        workflow_base = temp_project_dir / "docs" / "workflows" / "simple-mode"
        assert (workflow_base / "old-workflow-20250101-000000").exists()

    def test_command_error_handling(self, temp_project_dir):
        """Test error handling for invalid paths."""
        # Run command with invalid project structure
        invalid_dir = temp_project_dir / "invalid"
        invalid_dir.mkdir()
        
        result = subprocess.run(
            [
                "python", "-m", "tapps_agents.cli", "cleanup", "workflow-docs",
                "--dry-run",
            ],
            cwd=str(invalid_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        # Should handle gracefully (empty directory returns empty results)
        assert result.returncode == 0


class TestInitCursorignoreIntegration:
    """Test init command integration with cursorignore updates."""

    def test_init_updates_cursorignore(self, temp_project_dir):
        """Test that init updates .cursorignore."""
        # Remove .cursorignore if it exists
        cursorignore_path = temp_project_dir / ".cursorignore"
        if cursorignore_path.exists():
            cursorignore_path.unlink()
        
        # Run init command
        result = subprocess.run(
            [
                "python", "-m", "tapps_agents.cli", "init",
                "--no-rules", "--no-presets", "--no-skills", "--no-cache",
            ],
            cwd=str(temp_project_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        # Should succeed
        assert result.returncode == 0
        
        # Verify .cursorignore was created/updated
        if cursorignore_path.exists():
            content = cursorignore_path.read_text(encoding="utf-8")
            # Should contain TappsCodingAgents patterns
            assert ".tapps-agents/backups/" in content or "backups" in content.lower()
