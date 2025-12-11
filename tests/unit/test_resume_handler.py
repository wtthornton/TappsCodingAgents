"""
Unit tests for Resume Handler.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from tapps_agents.core.resume_handler import (
    ResumeHandler,
    ArtifactValidator,
    ContextRestorer
)
from tapps_agents.core.checkpoint_manager import CheckpointManager, TaskCheckpoint
from tapps_agents.core.task_state import TaskState
from tapps_agents.core.hardware_profiler import HardwareProfile


class TestArtifactValidator:
    """Tests for ArtifactValidator."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory with test files."""
        temp = tempfile.mkdtemp()
        temp_path = Path(temp)
        
        # Create some test files
        (temp_path / "file1.txt").write_text("content1")
        (temp_path / "file2.txt").write_text("content2")
        
        yield temp_path
        shutil.rmtree(temp)
    
    def test_validate_artifacts(self, temp_dir):
        """Test artifact validation."""
        artifacts = ["file1.txt", "file2.txt", "missing.txt"]
        results = ArtifactValidator.validate_artifacts(artifacts, temp_dir)
        
        assert results["file1.txt"] is True
        assert results["file2.txt"] is True
        assert results["missing.txt"] is False
    
    def test_all_artifacts_exist(self, temp_dir):
        """Test all artifacts exist check."""
        artifacts = ["file1.txt", "file2.txt"]
        assert ArtifactValidator.all_artifacts_exist(artifacts, temp_dir)
        
        artifacts = ["file1.txt", "missing.txt"]
        assert not ArtifactValidator.all_artifacts_exist(artifacts, temp_dir)
    
    def test_empty_artifacts(self, temp_dir):
        """Test empty artifacts list."""
        assert ArtifactValidator.all_artifacts_exist([], temp_dir)


class TestContextRestorer:
    """Tests for ContextRestorer."""
    
    def test_restore_context(self):
        """Test context restoration."""
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="paused",
            progress=0.5,
            checkpoint_time=datetime.utcnow(),
            context={"key": "value", "nested": {"data": 123}}
        )
        
        context = ContextRestorer.restore_context(checkpoint)
        
        assert context["key"] == "value"
        assert context["nested"]["data"] == 123
        assert "_checkpoint_metadata" in context
        assert context["_checkpoint_metadata"]["task_id"] == "test-task"


class TestResumeHandler:
    """Tests for ResumeHandler."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    @pytest.fixture
    def checkpoint_manager(self, temp_dir):
        """Create checkpoint manager."""
        return CheckpointManager(storage_dir=temp_dir)
    
    @pytest.fixture
    def resume_handler(self, temp_dir, checkpoint_manager):
        """Create resume handler."""
        return ResumeHandler(checkpoint_manager=checkpoint_manager, project_root=temp_dir)
    
    def test_can_resume_no_checkpoint(self, resume_handler):
        """Test can_resume with no checkpoint."""
        can_resume, reason = resume_handler.can_resume("nonexistent-task")
        assert not can_resume
        assert "No checkpoint found" in reason
    
    def test_can_resume_valid_checkpoint(self, resume_handler, checkpoint_manager):
        """Test can_resume with valid checkpoint."""
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="paused",
            progress=0.5,
            checkpoint_time=datetime.utcnow(),
            artifacts=[]
        )
        checkpoint.checksum = checkpoint.calculate_checksum()
        checkpoint_manager.storage.save(checkpoint)
        
        can_resume, reason = resume_handler.can_resume("test-task")
        assert can_resume
        assert reason is None
    
    def test_can_resume_invalid_state(self, resume_handler, checkpoint_manager):
        """Test can_resume with invalid state."""
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="completed",
            progress=1.0,
            checkpoint_time=datetime.utcnow()
        )
        checkpoint.checksum = checkpoint.calculate_checksum()
        checkpoint_manager.storage.save(checkpoint)
        
        can_resume, reason = resume_handler.can_resume("test-task")
        assert not can_resume
        assert "does not allow resumption" in reason
    
    def test_prepare_resume(self, resume_handler, checkpoint_manager):
        """Test prepare_resume."""
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="paused",
            progress=0.5,
            checkpoint_time=datetime.utcnow(),
            context={"key": "value"},
            artifacts=[]
        )
        checkpoint.checksum = checkpoint.calculate_checksum()
        checkpoint_manager.storage.save(checkpoint)
        
        resume_data = resume_handler.prepare_resume("test-task")
        
        assert resume_data["checkpoint"].task_id == "test-task"
        assert resume_data["progress"] == 0.5
        assert resume_data["context"]["key"] == "value"
        assert resume_data["state_manager"].current_state == TaskState.RUNNING
    
    def test_prepare_resume_missing_artifacts(self, resume_handler, checkpoint_manager, temp_dir):
        """Test prepare_resume with missing artifacts."""
        checkpoint = TaskCheckpoint(
            task_id="test-task",
            agent_id="test-agent",
            command="test command",
            state="paused",
            progress=0.5,
            checkpoint_time=datetime.utcnow(),
            artifacts=["missing-file.txt"]
        )
        checkpoint.checksum = checkpoint.calculate_checksum()
        checkpoint_manager.storage.save(checkpoint)
        
        with pytest.raises(ValueError, match="Cannot resume"):
            resume_handler.prepare_resume("test-task")
    
    def test_list_resumable_tasks(self, resume_handler, checkpoint_manager):
        """Test listing resumable tasks."""
        # Create resumable checkpoint
        checkpoint1 = TaskCheckpoint(
            task_id="task-1",
            agent_id="test-agent",
            command="test command",
            state="paused",
            progress=0.5,
            checkpoint_time=datetime.utcnow(),
            artifacts=[]
        )
        checkpoint1.checksum = checkpoint1.calculate_checksum()
        checkpoint_manager.storage.save(checkpoint1)
        
        # Create non-resumable checkpoint (completed)
        checkpoint2 = TaskCheckpoint(
            task_id="task-2",
            agent_id="test-agent",
            command="test command",
            state="completed",
            progress=1.0,
            checkpoint_time=datetime.utcnow(),
            artifacts=[]
        )
        checkpoint2.checksum = checkpoint2.calculate_checksum()
        checkpoint_manager.storage.save(checkpoint2)
        
        resumable = resume_handler.list_resumable_tasks()
        assert len(resumable) == 1
        assert resumable[0]["task_id"] == "task-1"

