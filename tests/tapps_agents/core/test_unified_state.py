"""
Tests for unified_state.py
"""

import json
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.core.unified_state import UnifiedState, UnifiedStateManager


class TestUnifiedState:
    """Test UnifiedState class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        state = UnifiedState("test-task-1")
        
        assert state.task_id == "test-task-1"
        assert state.workflow_id == "test-task-1"
        assert state.status == "initialized"
        assert state.start_time > 0
        assert len(state.steps) == 0
        assert state.result is None
        assert state.error is None
        assert "created_at" in state.metadata

    def test_init_custom(self):
        """Test initialization with custom parameters."""
        start_time = time.time() - 10.0
        state = UnifiedState(
            "test-task-2",
            workflow_id="workflow-1",
            start_time=start_time,
        )
        
        assert state.task_id == "test-task-2"
        assert state.workflow_id == "workflow-1"
        assert state.start_time == start_time

    def test_add_step(self):
        """Test adding a step."""
        state = UnifiedState("test-task-1")
        
        state.add_step("step1", "in_progress", "Starting step 1")
        
        assert len(state.steps) == 1
        assert state.steps[0]["step"] == "step1"
        assert state.steps[0]["status"] == "in_progress"
        assert state.steps[0]["message"] == "Starting step 1"
        assert state.status == "in_progress"
        assert "timestamp" in state.steps[0]
        assert "elapsed_seconds" in state.steps[0]

    def test_add_step_with_data(self):
        """Test adding a step with additional data."""
        state = UnifiedState("test-task-1")
        
        data = {"files_processed": 5, "lines": 100}
        state.add_step("step1", "completed", "Step completed", data)
        
        assert state.steps[0]["data"] == data

    def test_set_result(self):
        """Test setting result."""
        state = UnifiedState("test-task-1")
        
        result = {"success": True, "output": "test output"}
        state.set_result(result)
        
        assert state.result == result
        assert state.status == "completed"
        assert len(state.steps) > 0
        assert state.steps[-1]["step"] == "task_complete"

    def test_set_error(self):
        """Test setting error."""
        state = UnifiedState("test-task-1")
        
        state.set_error("Test error message")
        
        assert state.error is not None
        assert state.error["error"] == "Test error message"
        assert state.status == "failed"
        assert state.steps[-1]["step"] == "task_failed"

    def test_set_error_with_data(self):
        """Test setting error with additional data."""
        state = UnifiedState("test-task-1")
        
        error_data = {"code": 500, "traceback": "..."}
        state.set_error("Test error", error_data)
        
        assert state.error["error"] == "Test error"
        assert state.error["code"] == 500
        assert state.error["traceback"] == "..."

    def test_set_workflow_state(self):
        """Test setting workflow state."""
        state = UnifiedState("test-task-1")
        
        workflow_state = {"current_step": 3, "total_steps": 5}
        state.set_workflow_state(workflow_state)
        
        assert state.workflow_state == workflow_state

    def test_to_dict(self):
        """Test conversion to dictionary."""
        state = UnifiedState("test-task-1")
        state.add_step("step1", "in_progress")
        state.set_result({"success": True})
        
        data = state.to_dict()
        
        assert data["task_id"] == "test-task-1"
        assert data["status"] == "completed"
        assert len(data["steps"]) > 0
        assert data["result"] == {"success": True}
        assert "start_time" in data
        assert "current_time" in data
        assert "elapsed_seconds" in data

    def test_from_dict(self):
        """Test creation from dictionary."""
        original_state = UnifiedState("test-task-1")
        original_state.add_step("step1", "completed")
        original_state.set_result({"success": True})
        
        data = original_state.to_dict()
        restored_state = UnifiedState.from_dict(data)
        
        assert restored_state.task_id == original_state.task_id
        assert restored_state.status == original_state.status
        assert len(restored_state.steps) == len(original_state.steps)
        assert restored_state.result == original_state.result


class TestUnifiedStateManager:
    """Test UnifiedStateManager class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            manager = UnifiedStateManager(state_dir=state_dir)
            
            assert manager.state_dir == state_dir
            assert state_dir.exists()

    def test_get_state_file(self):
        """Test getting state file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            manager = UnifiedStateManager(state_dir=state_dir)
            
            state_file = manager.get_state_file("test-task-1")
            
            assert state_file.parent == state_dir
            assert state_file.name == "test-task-1.json"

    def test_create_state(self):
        """Test creating a new state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            manager = UnifiedStateManager(state_dir=state_dir)
            
            # Create state manually (UnifiedStateManager doesn't have create_state method)
            state = UnifiedState("test-task-1")
            manager.save_state(state)
            
            assert isinstance(state, UnifiedState)
            assert state.task_id == "test-task-1"
            assert manager.get_state_file("test-task-1").exists()

    def test_save_state(self):
        """Test saving state to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            manager = UnifiedStateManager(state_dir=state_dir)
            
            state = UnifiedState("test-task-1")
            state.add_step("step1", "completed")
            
            state_file = manager.save_state(state)
            
            assert state_file.exists()
            with open(state_file, encoding="utf-8") as f:
                saved_data = json.load(f)
            assert saved_data["task_id"] == "test-task-1"
            assert len(saved_data["steps"]) == 1

    def test_load_state(self):
        """Test loading state from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            manager = UnifiedStateManager(state_dir=state_dir)
            
            # Create and save state
            original_state = UnifiedState("test-task-1")
            original_state.add_step("step1", "completed")
            manager.save_state(original_state)
            
            # Load state
            loaded_state = manager.load_state("test-task-1")
            
            assert loaded_state is not None
            assert loaded_state.task_id == original_state.task_id
            assert len(loaded_state.steps) == len(original_state.steps)

    def test_load_state_not_found(self):
        """Test loading non-existent state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            manager = UnifiedStateManager(state_dir=state_dir)
            
            loaded_state = manager.load_state("non-existent")
            
            assert loaded_state is None

    def test_get_all_states(self):
        """Test getting all states."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            manager = UnifiedStateManager(state_dir=state_dir)
            
            # Create and save multiple states
            state1 = UnifiedState("task-1")
            state2 = UnifiedState("task-2")
            state3 = UnifiedState("task-3")
            manager.save_state(state1)
            manager.save_state(state2)
            manager.save_state(state3)
            
            states = manager.list_states()
            
            assert len(states) == 3
            task_ids = {s.task_id for s in states}
            assert task_ids == {"task-1", "task-2", "task-3"}

    def test_cleanup_old_states(self):
        """Test cleaning up old states."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            manager = UnifiedStateManager(state_dir=state_dir)
            
            # Create and save states
            state1 = UnifiedState("task-1")
            state2 = UnifiedState("task-2")
            manager.save_state(state1)
            manager.save_state(state2)
            
            # Modify timestamps to make one old
            state1_file = manager.get_state_file("task-1")
            old_time = time.time() - (35 * 24 * 60 * 60)  # 35 days ago
            state1_file.touch()
            import os
            os.utime(state1_file, (old_time, old_time))
            
            # Cleanup states older than 30 days
            cleaned = manager.cleanup_old_states(older_than_days=30)
            
            assert cleaned == 1
            assert not state1_file.exists()
            assert manager.get_state_file("task-2").exists()
