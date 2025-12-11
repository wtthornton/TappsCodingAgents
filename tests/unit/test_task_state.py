"""
Unit tests for Task State Management.
"""

import pytest
from datetime import datetime

from tapps_agents.core.task_state import TaskState, TaskStateManager, StateTransition


class TestTaskState:
    """Tests for TaskState enum."""
    
    def test_task_state_values(self):
        """Test TaskState enum values."""
        assert TaskState.INITIALIZED.value == "initialized"
        assert TaskState.RUNNING.value == "running"
        assert TaskState.PAUSED.value == "paused"
        assert TaskState.COMPLETED.value == "completed"


class TestTaskStateManager:
    """Tests for TaskStateManager."""
    
    def test_initial_state(self):
        """Test initial state."""
        manager = TaskStateManager("test-task")
        assert manager.current_state == TaskState.INITIALIZED
        assert len(manager.transitions) == 1
    
    def test_valid_transition(self):
        """Test valid state transition."""
        manager = TaskStateManager("test-task")
        assert manager.transition(TaskState.RUNNING, "Starting task")
        assert manager.current_state == TaskState.RUNNING
        assert len(manager.transitions) == 2
    
    def test_invalid_transition(self):
        """Test invalid state transition."""
        manager = TaskStateManager("test-task")
        with pytest.raises(ValueError, match="Invalid state transition"):
            manager.transition(TaskState.COMPLETED)  # Cannot go directly from INITIALIZED to COMPLETED
    
    def test_state_transitions(self):
        """Test complete state transition flow."""
        manager = TaskStateManager("test-task")
        
        # INITIALIZED -> RUNNING
        manager.transition(TaskState.RUNNING, "Starting")
        assert manager.current_state == TaskState.RUNNING
        
        # RUNNING -> CHECKPOINTED
        manager.transition(TaskState.CHECKPOINTED, "Checkpointing")
        assert manager.current_state == TaskState.CHECKPOINTED
        
        # CHECKPOINTED -> RUNNING
        manager.transition(TaskState.RUNNING, "Resuming")
        assert manager.current_state == TaskState.RUNNING
        
        # RUNNING -> COMPLETED
        manager.transition(TaskState.COMPLETED, "Done")
        assert manager.current_state == TaskState.COMPLETED
    
    def test_can_transition(self):
        """Test can_transition method."""
        manager = TaskStateManager("test-task")
        
        assert manager.can_transition(TaskState.RUNNING)
        assert not manager.can_transition(TaskState.COMPLETED)
    
    def test_is_terminal(self):
        """Test is_terminal method."""
        manager = TaskStateManager("test-task")
        assert not manager.is_terminal()
        
        manager.transition(TaskState.RUNNING)
        manager.transition(TaskState.COMPLETED)
        assert manager.is_terminal()
    
    def test_can_resume(self):
        """Test can_resume method."""
        manager = TaskStateManager("test-task")
        manager.transition(TaskState.RUNNING)
        manager.transition(TaskState.PAUSED)
        assert manager.can_resume()
        
        manager = TaskStateManager("test-task")
        manager.transition(TaskState.RUNNING)
        manager.transition(TaskState.CHECKPOINTED)
        assert manager.can_resume()
        
        manager = TaskStateManager("test-task")
        manager.transition(TaskState.RUNNING)
        manager.transition(TaskState.COMPLETED)
        assert not manager.can_resume()
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        manager = TaskStateManager("test-task")
        manager.transition(TaskState.RUNNING, "Starting")
        
        data = manager.to_dict()
        assert data["task_id"] == "test-task"
        assert data["current_state"] == "running"
        assert len(data["transitions"]) == 2
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        manager = TaskStateManager("test-task")
        manager.transition(TaskState.RUNNING, "Starting")
        manager.transition(TaskState.PAUSED, "Pausing")
        
        data = manager.to_dict()
        restored = TaskStateManager.from_dict(data)
        
        assert restored.task_id == "test-task"
        assert restored.current_state == TaskState.PAUSED
        assert len(restored.transitions) == 3
    
    def test_state_history(self):
        """Test state history retrieval."""
        manager = TaskStateManager("test-task")
        manager.transition(TaskState.RUNNING)
        manager.transition(TaskState.PAUSED)
        
        history = manager.get_state_history()
        assert len(history) == 3
        assert history[0].to_state == TaskState.INITIALIZED
        assert history[1].to_state == TaskState.RUNNING
        assert history[2].to_state == TaskState.PAUSED

