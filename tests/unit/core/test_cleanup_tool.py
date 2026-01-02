"""
Unit tests for CleanupTool workflow documentation cleanup.

Tests for IDE Clutter Management feature.
"""

import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tapps_agents.core.cleanup_tool import CleanupTool
from tapps_agents.core.config import ProjectConfig, WorkflowDocsCleanupConfig

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory."""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    # Create .tapps-agents directory
    (project_root / ".tapps-agents").mkdir()
    
    # Create docs/workflows/simple-mode directory
    workflow_dir = project_root / "docs" / "workflows" / "simple-mode"
    workflow_dir.mkdir(parents=True)
    
    yield project_root
    
    shutil.rmtree(temp_dir)


@pytest.fixture
def cleanup_tool(temp_project_dir):
    """Create CleanupTool instance."""
    config = ProjectConfig()
    return CleanupTool(project_root=temp_project_dir, config=config)


def create_workflow_directory(base_dir: Path, workflow_id: str, days_old: int = 0) -> Path:
    """Create a workflow directory with step files."""
    workflow_dir = base_dir / "docs" / "workflows" / "simple-mode" / workflow_id
    workflow_dir.mkdir(parents=True)
    
    # Create step files
    for i in range(1, 8):
        step_file = workflow_dir / f"step{i}-test.md"
        step_file.write_text(f"# Step {i}\n\nContent for step {i}", encoding="utf-8")
    
    # Set modification time to days_old days ago
    if days_old > 0:
        mtime = (datetime.now() - timedelta(days=days_old)).timestamp()
        for file in workflow_dir.rglob("*"):
            if file.is_file():
                # Touch file with old timestamp
                import os
                os.utime(file, (mtime, mtime))
    
    return workflow_dir


class TestCleanupWorkflowDocs:
    """Test cleanup_workflow_docs() method."""

    def test_empty_directory(self, cleanup_tool):
        """Test cleanup with no workflow directories."""
        results = cleanup_tool.cleanup_workflow_docs(dry_run=True)
        
        assert results["archived"] == 0
        assert results["kept"] == 0
        assert results["total_size_mb"] == 0.0
        assert results["archived_workflows"] == []
        assert results["kept_workflows"] == []
        assert results["dry_run"] is True
        assert results["errors"] == []

    def test_keeps_latest_workflows(self, cleanup_tool, temp_project_dir):
        """Test that latest N workflows are kept."""
        # Create 10 workflow directories
        for i in range(10):
            create_workflow_directory(
                temp_project_dir,
                f"workflow-{i:02d}-20250116-000000",
                days_old=i * 5  # Each 5 days older
            )
        
        results = cleanup_tool.cleanup_workflow_docs(
            keep_latest=5,
            retention_days=30,
            archive_dir=None,  # Disable archival
            dry_run=True,
        )
        
        assert results["kept"] == 5
        assert len(results["kept_workflows"]) == 5
        # Should keep the 5 newest (workflow-09 through workflow-05)
        assert "workflow-09-20250116-000000" in results["kept_workflows"]

    def test_archives_old_workflows(self, cleanup_tool, temp_project_dir):
        """Test archival of old workflows."""
        # Create workflows with different ages
        create_workflow_directory(temp_project_dir, "recent-20250116-000000", days_old=5)
        create_workflow_directory(temp_project_dir, "old-20250101-000000", days_old=45)
        create_workflow_directory(temp_project_dir, "very-old-20241201-000000", days_old=75)
        
        archive_dir = temp_project_dir / ".tapps-agents" / "archives" / "workflows"
        
        results = cleanup_tool.cleanup_workflow_docs(
            keep_latest=1,
            retention_days=30,
            archive_dir=archive_dir,
            dry_run=False,
        )
        
        # Recent workflow should be kept
        assert results["kept"] == 1
        assert "recent-20250116-000000" in results["kept_workflows"]
        
        # Old workflows should be archived
        assert results["archived"] == 2
        assert "old-20250101-000000" in results["archived_workflows"]
        assert "very-old-20241201-000000" in results["archived_workflows"]
        
        # Verify archived workflows exist in archive directory
        assert (archive_dir / "old-20250101-000000").exists()
        assert (archive_dir / "very-old-20241201-000000").exists()
        
        # Verify original directories are gone
        workflow_base = temp_project_dir / "docs" / "workflows" / "simple-mode"
        assert not (workflow_base / "old-20250101-000000").exists()
        assert not (workflow_base / "very-old-20241201-000000").exists()

    def test_dry_run_mode(self, cleanup_tool, temp_project_dir):
        """Test dry-run mode doesn't modify files."""
        create_workflow_directory(temp_project_dir, "test-20250101-000000", days_old=45)
        
        archive_dir = temp_project_dir / ".tapps-agents" / "archives" / "workflows"
        
        results = cleanup_tool.cleanup_workflow_docs(
            keep_latest=0,
            retention_days=30,
            archive_dir=archive_dir,
            dry_run=True,
        )
        
        assert results["dry_run"] is True
        assert results["archived"] == 1
        
        # Verify no files were actually moved
        workflow_base = temp_project_dir / "docs" / "workflows" / "simple-mode"
        assert (workflow_base / "test-20250101-000000").exists()
        assert not archive_dir.exists()

    def test_no_archive_disabled(self, cleanup_tool, temp_project_dir):
        """Test cleanup with archival disabled."""
        create_workflow_directory(temp_project_dir, "old-20250101-000000", days_old=45)
        
        results = cleanup_tool.cleanup_workflow_docs(
            keep_latest=0,
            retention_days=30,
            archive_dir=None,  # Archive disabled
            dry_run=False,
        )
        
        # Workflow should still be visible (not archived)
        workflow_base = temp_project_dir / "docs" / "workflows" / "simple-mode"
        assert (workflow_base / "old-20250101-000000").exists()
        assert results["archived"] == 0

    def test_excludes_special_directories(self, cleanup_tool, temp_project_dir):
        """Test that special directories are excluded."""
        workflow_base = temp_project_dir / "docs" / "workflows" / "simple-mode"
        
        # Create special directories
        (workflow_base / "latest").mkdir()
        (workflow_base / "latest" / "step1.md").write_text("# Latest", encoding="utf-8")
        
        (workflow_base / "README.md").write_text("# README", encoding="utf-8")
        
        # Create normal workflow
        create_workflow_directory(temp_project_dir, "normal-20250116-000000")
        
        results = cleanup_tool.cleanup_workflow_docs(dry_run=True)
        
        # Should only process normal workflow, not special directories
        assert "latest" not in results["kept_workflows"]
        assert "normal-20250116-000000" in results["kept_workflows"]

    def test_error_handling_permission_error(self, cleanup_tool, temp_project_dir):
        """Test graceful handling of permission errors."""
        create_workflow_directory(temp_project_dir, "test-20250101-000000", days_old=45)
        
        archive_dir = temp_project_dir / ".tapps-agents" / "archives" / "workflows"
        
        # Mock shutil.copytree to raise PermissionError
        with patch("shutil.copytree", side_effect=PermissionError("Access denied")):
            results = cleanup_tool.cleanup_workflow_docs(
                keep_latest=0,
                retention_days=30,
                archive_dir=archive_dir,
                dry_run=False,
            )
        
        # Should have error in results but continue
        assert len(results["errors"]) > 0
        assert any("PermissionError" in error or "Access denied" in error for error in results["errors"])

    def test_calculates_size_correctly(self, cleanup_tool, temp_project_dir):
        """Test that size calculation is correct."""
        workflow_dir = create_workflow_directory(temp_project_dir, "test-20250101-000000", days_old=45)
        
        # Calculate expected size
        expected_size = sum(
            f.stat().st_size
            for f in workflow_dir.rglob("*")
            if f.is_file()
        )
        
        archive_dir = temp_project_dir / ".tapps-agents" / "archives" / "workflows"
        
        results = cleanup_tool.cleanup_workflow_docs(
            keep_latest=0,
            retention_days=30,
            archive_dir=archive_dir,
            dry_run=False,
        )
        
        # Size should be approximately correct (allow for small differences)
        assert abs(results["total_size_mb"] - (expected_size / 1024 / 1024)) < 0.1

    def test_cleanup_all_includes_workflow_docs(self, cleanup_tool, temp_project_dir):
        """Test that cleanup_all() includes workflow docs cleanup."""
        create_workflow_directory(temp_project_dir, "test-20250101-000000", days_old=45)
        
        # Configure cleanup
        cleanup_tool.config.cleanup.workflow_docs.enabled = True
        cleanup_tool.config.cleanup.workflow_docs.keep_latest = 0
        cleanup_tool.config.cleanup.workflow_docs.retention_days = 30
        cleanup_tool.config.cleanup.workflow_docs.archive_enabled = True
        
        results = cleanup_tool.cleanup_all(
            workflow_keep_latest=0,
            workflow_retention_days=30,
            workflow_archive=True,
            dry_run=True,
        )
        
        assert "workflow_docs" in results
        assert results["workflow_docs"]["archived"] == 1


class TestUpdateCursorignorePatterns:
    """Test _update_cursorignore_patterns() function."""

    def test_missing_file(self, temp_project_dir):
        """Test creating .cursorignore if missing."""
        from tapps_agents.cli.commands.top_level import _update_cursorignore_patterns
        
        result = _update_cursorignore_patterns(temp_project_dir)
        
        assert result["updated"] is True
        assert len(result["patterns_added"]) == 3
        
        # Verify file was created
        cursorignore_path = temp_project_dir / ".cursorignore"
        assert cursorignore_path.exists()
        
        content = cursorignore_path.read_text(encoding="utf-8")
        assert ".tapps-agents/backups/" in content
        assert ".tapps-agents/archives/" in content
        assert ".tapps-agents/artifacts/" in content

    def test_existing_patterns_preserved(self, temp_project_dir):
        """Test that existing patterns are preserved."""
        from tapps_agents.cli.commands.top_level import _update_cursorignore_patterns
        
        cursorignore_path = temp_project_dir / ".cursorignore"
        cursorignore_path.write_text(
            "# Existing patterns\n.venv/\n__pycache__/\n",
            encoding="utf-8",
        )
        
        result = _update_cursorignore_patterns(temp_project_dir)
        
        assert result["updated"] is True
        
        # Verify existing content preserved
        content = cursorignore_path.read_text(encoding="utf-8")
        assert ".venv/" in content
        assert "__pycache__/" in content
        assert ".tapps-agents/backups/" in content

    def test_all_patterns_present(self, temp_project_dir):
        """Test idempotency when all patterns exist."""
        from tapps_agents.cli.commands.top_level import _update_cursorignore_patterns
        
        cursorignore_path = temp_project_dir / ".cursorignore"
        cursorignore_path.write_text(
            ".tapps-agents/backups/\n.tapps-agents/archives/\n.tapps-agents/artifacts/\n",
            encoding="utf-8",
        )
        
        result = _update_cursorignore_patterns(temp_project_dir)
        
        assert result["updated"] is False
        assert len(result["patterns_added"]) == 0
        assert len(result["patterns_existing"]) == 3


class TestWorkflowDocsCleanupConfig:
    """Test WorkflowDocsCleanupConfig validation."""

    def test_default_values(self):
        """Test default configuration values."""
        config = WorkflowDocsCleanupConfig()
        
        assert config.enabled is True
        assert config.keep_latest == 5
        assert config.retention_days == 30
        assert config.archive_enabled is True
        assert config.archive_dir == Path(".tapps-agents/archives/workflows/")
        assert config.exclude_patterns == []

    def test_validation_keep_latest_bounds(self):
        """Test keep_latest validation bounds."""
        # Should accept values 1-100
        config1 = WorkflowDocsCleanupConfig(keep_latest=1)
        assert config1.keep_latest == 1
        
        config2 = WorkflowDocsCleanupConfig(keep_latest=100)
        assert config2.keep_latest == 100
        
        # Should reject values outside bounds
        with pytest.raises(Exception):  # Pydantic validation error
            WorkflowDocsCleanupConfig(keep_latest=0)
        
        with pytest.raises(Exception):
            WorkflowDocsCleanupConfig(keep_latest=101)

    def test_validation_retention_days(self):
        """Test retention_days validation."""
        config = WorkflowDocsCleanupConfig(retention_days=1)
        assert config.retention_days == 1
        
        with pytest.raises(Exception):
            WorkflowDocsCleanupConfig(retention_days=0)
