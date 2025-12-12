"""
Unit tests for Workflow Parser.
"""

from pathlib import Path

import pytest

from tapps_agents.workflow import WorkflowParser, WorkflowType


@pytest.mark.unit
class TestWorkflowParser:
    """Test cases for WorkflowParser."""

    @pytest.fixture
    def sample_workflow_dict(self):
        """Sample workflow dictionary."""
        return {
            "workflow": {
                "id": "test-workflow",
                "name": "Test Workflow",
                "description": "A test workflow",
                "version": "1.0.0",
                "type": "greenfield",
                "settings": {
                    "quality_gates": True,
                    "code_scoring": True,
                    "context_tier_default": 2,
                },
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "context_tier": 1,
                        "creates": ["file1.md"],
                        "requires": [],
                        "next": "step2",
                    },
                    {
                        "id": "step2",
                        "agent": "planner",
                        "action": "plan",
                        "context_tier": 2,
                        "creates": ["plan.md"],
                        "requires": ["file1.md"],
                        "next": "step3",
                    },
                ],
            }
        }

    def test_parse_workflow(self, sample_workflow_dict):
        """Test parsing a workflow from dictionary."""
        workflow = WorkflowParser.parse(sample_workflow_dict)

        assert workflow.id == "test-workflow"
        assert workflow.name == "Test Workflow"
        assert workflow.version == "1.0.0"
        assert workflow.type == WorkflowType.GREENFIELD
        assert len(workflow.steps) == 2

    def test_parse_workflow_settings(self, sample_workflow_dict):
        """Test parsing workflow settings."""
        workflow = WorkflowParser.parse(sample_workflow_dict)

        assert workflow.settings.quality_gates is True
        assert workflow.settings.code_scoring is True
        assert workflow.settings.context_tier_default == 2

    def test_parse_workflow_steps(self, sample_workflow_dict):
        """Test parsing workflow steps."""
        workflow = WorkflowParser.parse(sample_workflow_dict)

        assert len(workflow.steps) == 2
        step1 = workflow.steps[0]
        assert step1.id == "step1"
        assert step1.agent == "analyst"
        assert step1.action == "gather"
        assert step1.context_tier == 1
        assert "file1.md" in step1.creates

    def test_parse_workflow_file(self, sample_workflow_dict, tmp_path: Path):
        """Test parsing workflow from file."""
        import yaml

        workflow_file = tmp_path / "workflow.yaml"
        with open(workflow_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_workflow_dict, f)

        workflow = WorkflowParser.parse_file(workflow_file)

        assert workflow.id == "test-workflow"
        assert len(workflow.steps) == 2

    def test_parse_workflow_type_brownfield(self):
        """Test parsing brownfield workflow type."""
        workflow_dict = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "brownfield",
                "steps": [],
            }
        }

        workflow = WorkflowParser.parse(workflow_dict)
        assert workflow.type == WorkflowType.BROWNFIELD

    def test_parse_step_with_gate(self):
        """Test parsing step with gate condition."""
        workflow_dict = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "review",
                        "agent": "reviewer",
                        "action": "review",
                        "gate": {
                            "condition": "scoring.passed == true",
                            "on_pass": "next",
                            "on_fail": "retry",
                        },
                    }
                ],
            }
        }

        workflow = WorkflowParser.parse(workflow_dict)
        step = workflow.steps[0]
        assert step.gate is not None
        assert step.gate["condition"] == "scoring.passed == true"

    def test_parse_step_required_fields(self):
        """Test that required fields are validated."""
        workflow_dict = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "step1"
                        # Missing agent and action
                    }
                ],
            }
        }

        with pytest.raises(ValueError, match="Step must have id, agent, and action"):
            WorkflowParser.parse(workflow_dict)
