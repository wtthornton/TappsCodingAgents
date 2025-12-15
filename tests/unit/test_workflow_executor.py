"""
Unit tests for Workflow Executor.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from tapps_agents.experts.expert_registry import ConsultationResult
from tapps_agents.workflow import (
    WorkflowExecutor,
    WorkflowParser,
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
                        "next": "step2",
                    },
                    {
                        "id": "step2",
                        "agent": "planner",
                        "action": "plan",
                        "creates": ["plan.md"],
                        "requires": ["file1.md"],
                        "next": "step3",
                    },
                    {
                        "id": "step3",
                        "agent": "implementer",
                        "action": "implement",
                        "requires": ["plan.md"],
                    },
                ],
            }
        }

    @pytest.fixture
    def executor(self, tmp_path: Path, monkeypatch):
        """Create a WorkflowExecutor instance."""
        # Preserve workflow ID for tests
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
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
        executor.mark_step_complete(
            artifacts=[{"name": "file1.md", "path": "file1.md", "metadata": {}}]
        )

        # Step 2 should be able to proceed now
        assert executor.can_proceed() is True

    def test_mark_step_complete(self, executor, sample_workflow_dict):
        """Test marking a step as complete."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)

        executor.mark_step_complete(
            artifacts=[{"name": "file1.md", "path": "file1.md"}]
        )

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
                        "requires": [],
                    }
                ],
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

    def test_step_requires_expert_consultation_with_consults(
        self, executor, sample_workflow_dict
    ):
        """Test step_requires_expert_consultation when step has consults configured."""
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
                        "consults": ["expert-security", "expert-performance"],
                    }
                ],
            }
        }
        workflow = WorkflowParser.parse(workflow_dict)
        executor.start(workflow)

        assert executor.step_requires_expert_consultation() is True

    def test_step_requires_expert_consultation_without_consults(
        self, executor, sample_workflow_dict
    ):
        """Test step_requires_expert_consultation when step has no consults."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)

        assert executor.step_requires_expert_consultation() is False

    def test_step_requires_expert_consultation_no_step(self, executor):
        """Test step_requires_expert_consultation when no step is available."""
        assert executor.step_requires_expert_consultation() is False

    @pytest.mark.asyncio
    async def test_consult_experts_for_step_with_consults(self, executor, tmp_path):
        """Test consult_experts_for_step when step has consults configured."""
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
                        "consults": ["expert-security"],
                        "notes": "Security review needed",
                    }
                ],
            }
        }
        workflow = WorkflowParser.parse(workflow_dict)
        executor.start(workflow)

        # Create mock expert registry
        mock_registry = Mock()
        mock_result = ConsultationResult(
            domain="security",
            query="Security review needed",
            weighted_answer="Use secure protocols",
            confidence=0.9,
            agreement_level=0.95,
            confidence_threshold=0.7,
            primary_expert="expert-security",
            all_experts_agreed=True,
            responses=[
                {
                    "expert_id": "expert-security",
                    "expert_name": "Security Expert",
                    "answer": "Use secure protocols",
                    "confidence": 0.9,
                    "sources": [],
                }
            ],
        )
        mock_registry.consult = AsyncMock(return_value=mock_result)
        executor.expert_registry = mock_registry

        # Consult experts for step
        result = await executor.consult_experts_for_step()

        assert result is not None
        assert result["domain"] == "security"
        assert result["experts_consulted"] == ["expert-security"]
        assert result["weighted_answer"] == "Use secure protocols"
        assert result["confidence"] == 0.9

        # Verify consultation was stored in state
        assert "expert_consultations" in executor.state.variables
        assert "step1" in executor.state.variables["expert_consultations"]

    @pytest.mark.asyncio
    async def test_consult_experts_for_step_without_consults(
        self, executor, sample_workflow_dict
    ):
        """Test consult_experts_for_step when step has no consults."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)

        result = await executor.consult_experts_for_step()

        assert result is None

    @pytest.mark.asyncio
    async def test_consult_experts_for_step_with_custom_query(self, executor, tmp_path):
        """Test consult_experts_for_step with custom query."""
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
                        "consults": ["expert-security"],
                    }
                ],
            }
        }
        workflow = WorkflowParser.parse(workflow_dict)
        executor.start(workflow)

        # Create mock expert registry
        mock_registry = Mock()
        mock_result = ConsultationResult(
            domain="security",
            query="What security measures should I take?",
            weighted_answer="Custom answer",
            confidence=0.8,
            agreement_level=0.9,
            confidence_threshold=0.7,
            primary_expert="expert-security",
            all_experts_agreed=True,
            responses=[],
        )
        mock_registry.consult = AsyncMock(return_value=mock_result)
        executor.expert_registry = mock_registry

        # Consult with custom query
        custom_query = "What security measures should I take?"
        result = await executor.consult_experts_for_step(query=custom_query)

        assert result is not None
        assert result["query"] == custom_query
        mock_registry.consult.assert_called_once()
        call_args = mock_registry.consult.call_args
        assert call_args[1]["query"] == custom_query

    @pytest.mark.asyncio
    async def test_consult_experts_for_step_no_registry(self, executor, tmp_path):
        """Test consult_experts_for_step raises error when registry not available."""
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
                        "consults": ["expert-security"],
                    }
                ],
            }
        }
        workflow = WorkflowParser.parse(workflow_dict)
        executor.start(workflow)
        executor.expert_registry = None

        with pytest.raises(ValueError, match="expert_registry not available"):
            await executor.consult_experts_for_step()

    @pytest.mark.asyncio
    async def test_consult_experts_manual(self, executor, tmp_path):
        """Test manual consult_experts method."""
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
                        "consults": ["expert-security"],
                    }
                ],
            }
        }
        workflow = WorkflowParser.parse(workflow_dict)
        executor.start(workflow)

        # Create mock expert registry
        mock_registry = Mock()
        mock_result = ConsultationResult(
            domain="security",
            query="What should I do?",
            weighted_answer="Manual consultation answer",
            confidence=0.85,
            agreement_level=0.9,
            confidence_threshold=0.7,
            primary_expert="expert-security",
            all_experts_agreed=True,
            responses=[],
        )
        mock_registry.consult = AsyncMock(return_value=mock_result)
        executor.expert_registry = mock_registry

        # Manual consultation
        result = await executor.consult_experts(
            query="What should I do?", domain="security"
        )

        assert result is not None
        assert result["query"] == "What should I do?"
        assert result["domain"] == "security"
        assert result["experts_consulted"] == ["expert-security"]

    def test_get_status_includes_expert_registry_available(
        self, executor, sample_workflow_dict
    ):
        """Test that get_status includes expert_registry_available flag."""
        workflow = WorkflowParser.parse(sample_workflow_dict)
        executor.start(workflow)

        status = executor.get_status()
        assert "expert_registry_available" in status
        assert status["expert_registry_available"] is False

        # With registry
        executor.expert_registry = Mock()
        status = executor.get_status()
        assert status["expert_registry_available"] is True
