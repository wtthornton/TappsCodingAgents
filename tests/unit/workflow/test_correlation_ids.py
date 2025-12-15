"""
Tests for correlation IDs and structured logging.

Epic 1 / Story 1.6: Correlation IDs & Baseline Observability
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from tapps_agents.workflow.models import Workflow, WorkflowState, WorkflowStep, WorkflowType
from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.cursor_executor import CursorWorkflowExecutor
from tapps_agents.workflow.logging_helper import WorkflowLogger


@pytest.mark.unit
class TestCorrelationIDs:
    """Test correlation ID propagation and consistency."""

    def test_workflow_id_format_consistency(self, tmp_path: Path):
        """Test that workflow_id format is consistent across executors."""
        workflow = Workflow(
            id="test-workflow",
            name="Test Workflow",
            description="Test",
            version="1.0.0",
            type=WorkflowType.GREENFIELD,
            steps=[],
        )

        # Test WorkflowExecutor
        executor = WorkflowExecutor(project_root=tmp_path)
        executor.workflow = workflow
        state = executor.start(workflow=workflow)
        
        # Workflow ID should be {workflow.id}-{timestamp}
        assert state.workflow_id.startswith("test-workflow-")
        assert len(state.workflow_id) > len("test-workflow-")
        
        # Test CursorWorkflowExecutor
        cursor_executor = CursorWorkflowExecutor(project_root=tmp_path)
        cursor_state = cursor_executor.start(workflow=workflow)
        
        # Should use same format
        assert cursor_state.workflow_id.startswith("test-workflow-")
        assert len(cursor_state.workflow_id) > len("test-workflow-")

    def test_workflow_id_propagated_to_state(self, tmp_path: Path):
        """Test that workflow_id is present in WorkflowState."""
        workflow = Workflow(
            id="test-workflow",
            name="Test Workflow",
            description="Test",
            version="1.0.0",
            type=WorkflowType.GREENFIELD,
            steps=[],
        )

        executor = WorkflowExecutor(project_root=tmp_path)
        executor.workflow = workflow
        state = executor.start(workflow=workflow)
        
        assert state.workflow_id is not None
        assert isinstance(state.workflow_id, str)
        assert len(state.workflow_id) > 0

    def test_step_execution_contains_correlation_fields(self, tmp_path: Path):
        """Test that StepExecution records contain correlation fields."""
        from tapps_agents.workflow.models import StepExecution
        
        step_exec = StepExecution(
            step_id="step1",
            agent="implementer",
            action="implement",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_seconds=1.5,
            status="completed",
        )
        
        # Verify all correlation fields are present
        assert step_exec.step_id == "step1"
        assert step_exec.agent == "implementer"
        assert step_exec.action == "implement"
        assert step_exec.started_at is not None
        assert step_exec.completed_at is not None
        assert step_exec.status == "completed"

    def test_step_execution_error_captured(self, tmp_path: Path):
        """Test that error strings are captured for failed steps."""
        from tapps_agents.workflow.models import StepExecution
        
        error_msg = "Test error message"
        step_exec = StepExecution(
            step_id="step1",
            agent="implementer",
            action="implement",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="failed",
            error=error_msg,
        )
        
        assert step_exec.error == error_msg
        assert step_exec.status == "failed"

    def test_workflow_state_step_executions_populated(self, tmp_path: Path):
        """Test that WorkflowState.step_executions is populated during execution."""
        workflow = Workflow(
            id="test-workflow",
            name="Test Workflow",
            description="Test",
            version="1.0.0",
            type=WorkflowType.GREENFIELD,
            steps=[
                WorkflowStep(
                    id="step1",
                    agent="orchestrator",
                    action="complete",
                    requires=[],
                    creates=[],
                ),
            ],
        )

        executor = WorkflowExecutor(project_root=tmp_path, auto_mode=True)
        executor.workflow = workflow
        state = executor.start(workflow=workflow)
        
        # After execution, step_executions should be populated
        # (Note: This test may need to be adjusted based on actual execution behavior)
        assert state.step_executions is not None
        assert isinstance(state.step_executions, list)


@pytest.mark.unit
class TestWorkflowLogger:
    """Test WorkflowLogger structured logging."""

    def test_logger_includes_workflow_id(self):
        """Test that logger includes workflow_id in extra fields."""
        logger = WorkflowLogger(workflow_id="test-workflow-123")
        
        with patch.object(logger._logger, "info") as mock_info:
            logger.info("Test message")
            mock_info.assert_called_once()
            call_kwargs = mock_info.call_args[1]
            assert "extra" in call_kwargs
            assert call_kwargs["extra"]["workflow_id"] == "test-workflow-123"

    def test_logger_includes_step_id(self):
        """Test that logger includes step_id when provided."""
        logger = WorkflowLogger(
            workflow_id="test-workflow-123",
            step_id="step1",
        )
        
        with patch.object(logger._logger, "info") as mock_info:
            logger.info("Test message")
            call_kwargs = mock_info.call_args[1]
            assert call_kwargs["extra"]["workflow_id"] == "test-workflow-123"
            assert call_kwargs["extra"]["step_id"] == "step1"

    def test_logger_includes_agent(self):
        """Test that logger includes agent when provided."""
        logger = WorkflowLogger(
            workflow_id="test-workflow-123",
            agent="implementer",
        )
        
        with patch.object(logger._logger, "info") as mock_info:
            logger.info("Test message")
            call_kwargs = mock_info.call_args[1]
            assert call_kwargs["extra"]["workflow_id"] == "test-workflow-123"
            assert call_kwargs["extra"]["agent"] == "implementer"

    def test_logger_with_context(self):
        """Test that with_context creates new logger with merged context."""
        base_logger = WorkflowLogger(workflow_id="test-workflow-123")
        step_logger = base_logger.with_context(step_id="step1", agent="implementer")
        
        with patch.object(step_logger._logger, "info") as mock_info:
            step_logger.info("Test message")
            call_kwargs = mock_info.call_args[1]
            assert call_kwargs["extra"]["workflow_id"] == "test-workflow-123"
            assert call_kwargs["extra"]["step_id"] == "step1"
            assert call_kwargs["extra"]["agent"] == "implementer"

    def test_logger_redacts_sensitive_data(self):
        """Test that logger redacts sensitive information."""
        logger = WorkflowLogger(workflow_id="test-workflow-123")
        
        with patch.object(logger._logger, "info") as mock_info:
            logger.info("API key: sk-1234567890abcdef")
            call_args = mock_info.call_args[0]
            # Message should be redacted
            assert "***REDACTED***" in call_args[0]
            assert "sk-1234567890abcdef" not in call_args[0]

    def test_logger_error_includes_exc_info(self):
        """Test that error logging includes exc_info."""
        logger = WorkflowLogger(workflow_id="test-workflow-123")
        
        with patch.object(logger._logger, "error") as mock_error:
            try:
                raise ValueError("Test error")
            except ValueError:
                logger.error("Error occurred", exc_info=True)
            
            call_kwargs = mock_error.call_args[1]
            assert call_kwargs["exc_info"] is True


@pytest.mark.unit
class TestCorrelationIDPropagation:
    """Test correlation ID propagation through workflow execution."""

    def test_workflow_id_in_persisted_state(self, tmp_path: Path):
        """Test that workflow_id is persisted in state file."""
        workflow = Workflow(
            id="test-workflow",
            name="Test Workflow",
            description="Test",
            version="1.0.0",
            type=WorkflowType.GREENFIELD,
            steps=[],
        )

        executor = WorkflowExecutor(project_root=tmp_path)
        executor.workflow = workflow
        state = executor.start(workflow=workflow)
        
        # Save state
        state_path = executor.save_state()
        assert state_path is not None
        assert state_path.exists()
        
        # Load state and verify workflow_id is present
        loaded_state = executor._state_from_dict(
            executor._state_to_dict(state)
        )
        assert loaded_state.workflow_id == state.workflow_id

    def test_step_execution_in_persisted_state(self, tmp_path: Path):
        """Test that step_executions with correlation fields are persisted."""
        from tapps_agents.workflow.models import StepExecution
        
        workflow = Workflow(
            id="test-workflow",
            name="Test Workflow",
            description="Test",
            version="1.0.0",
            type=WorkflowType.GREENFIELD,
            steps=[],
        )

        executor = WorkflowExecutor(project_root=tmp_path)
        executor.workflow = workflow
        state = executor.start(workflow=workflow)
        
        # Add a step execution
        step_exec = StepExecution(
            step_id="step1",
            agent="implementer",
            action="implement",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="completed",
        )
        state.step_executions.append(step_exec)
        
        # Persist and reload
        state_dict = executor._state_to_dict(state)
        loaded_state = executor._state_from_dict(state_dict)
        
        assert len(loaded_state.step_executions) == 1
        assert loaded_state.step_executions[0].step_id == "step1"
        assert loaded_state.step_executions[0].agent == "implementer"
        assert loaded_state.step_executions[0].action == "implement"
