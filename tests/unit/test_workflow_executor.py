"""
Unit tests for Workflow Executor.
"""

import pytest
from pathlib import Path
from datetime import datetime

from tapps_agents.workflow import (
    WorkflowParser,
    WorkflowExecutor,
    Workflow,
    WorkflowStep,
)


@pytest.mark.unit
class TestWorkflowExecutor:
    """Test cases for WorkflowExecutor."""
    
    @pytest.fixture
    def sample_workflow_dict(self):
        """Sample workflow dictionary."""
        return {
            "workflow": {
                "id": "test-workflow",
                "name": "Test Workflow",
                "description": "Test",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "creates": ["file1.md"],
                        "requires": [],
                        "next": "step2"
                    },
                    {
                        "id": "step2",
                        "agent": "planner",
                        "action": "plan",
                        "creates": ["plan.md"],
                        "requires": ["file1.md"],
                        "next": "step3"
                    },
                    {
                        "id": "step3",
                        "agent": "implementer",
                        "action": "implement",
                        "requires": ["plan.md"]
                    }
                ]
            }
        }
    
    @pytest.fixture
    def executor(self, tmp_path: Path):
        """Create a WorkflowExecutor instance."""
        return WorkflowExecutor(project_root=tmp_path)
    
    def test_start_workflow(self, executor, sample_workflow_dict):
        """Test starting a workflow."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        state = executor.start(workflow)
        
        assert state.workflow_id == "test-workflow"
        assert state.status == "running"
        assert state.current_step == "step1"
    
    def test_get_current_step(self, executor, sample_workflow_dict):
        """Test getting current step."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)
        
        current_step = executor.get_current_step()
        assert current_step is not None
        assert current_step.id == "step1"
        assert current_step.agent == "analyst"
    
    def test_get_next_step(self, executor, sample_workflow_dict):
        """Test getting next step."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)
        
        next_step = executor.get_next_step()
        assert next_step is not None
        assert next_step.id == "step2"
    
    def test_can_proceed_no_requirements(self, executor, sample_workflow_dict):
        """Test can_proceed when step has no requirements."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)
        
        # Step 1 has no requirements, should be able to proceed
        assert executor.can_proceed() is True
    
    def test_can_proceed_missing_artifact(self, executor, sample_workflow_dict):
        """Test can_proceed when required artifact is missing."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)
        
        # Mark step1 as complete but don't create the artifact
        executor.mark_step_complete()
        
        # Step 2 requires file1.md, but it wasn't created
        assert executor.can_proceed() is False
    
    def test_can_proceed_with_artifacts(self, executor, sample_workflow_dict):
        """Test can_proceed when artifacts exist."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)
        
        # Complete step1 with artifact
        executor.mark_step_complete(artifacts=[{
            "name": "file1.md",
            "path": "file1.md",
            "metadata": {}
        }])
        
        # Step 2 should be able to proceed now
        assert executor.can_proceed() is True
    
    def test_mark_step_complete(self, executor, sample_workflow_dict):
        """Test marking a step as complete."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)
        
        executor.mark_step_complete(artifacts=[{
            "name": "file1.md",
            "path": "file1.md"
        }])
        
        state = executor.state
        assert "step1" in state.completed_steps
        assert "file1.md" in state.artifacts
        assert state.current_step == "step2"
    
    def test_mark_step_complete_final_step(self, executor):
        """Test marking final step as complete."""
        workflow_dict = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "requires": []
                    }
                ]
            }
        }
        
        workflow = WorkflowParser.parse(workflow_dict)
        executor.start(workflow)
        
        executor.mark_step_complete()
        
        assert executor.state.status == "completed"
        assert executor.state.current_step is None
    
    def test_skip_step(self, executor, sample_workflow_dict):
        """Test skipping a step."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)
        
        executor.skip_step("step1")
        
        assert "step1" in executor.state.skipped_steps
        assert executor.state.current_step == "step2"
    
    def test_get_status(self, executor, sample_workflow_dict):
        """Test getting workflow status."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)
        
        status = executor.get_status()
        
        assert status["workflow_id"] == "test-workflow"
        assert status["status"] == "running"
        assert status["current_step"] == "step1"
        assert status["current_step_details"]["agent"] == "analyst"
        assert status["can_proceed"] is True

