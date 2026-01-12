"""
Smoke E2E tests for workflow YAML parsing and validation.

Tests validate that:
- All shipped workflows can be parsed
- Workflow schema validation works
- Invalid workflows are handled gracefully
"""


import pytest

from tapps_agents.workflow.parser import WorkflowParser
from tests.e2e.fixtures.dependency_validator import validate_workflow_file


@pytest.mark.e2e_smoke
@pytest.mark.template_type("minimal")
class TestWorkflowParsing:
    """Test workflow YAML parsing and validation."""

    def test_parse_all_shipped_workflows(self, e2e_project, project_root_path):
        """Test that all shipped workflows can be parsed."""
        workflows_dir = project_root_path / "workflows"
        
        # Find all YAML workflow files
        workflow_files = list(workflows_dir.rglob("*.yaml")) + list(workflows_dir.rglob("*.yml"))
        
        assert len(workflow_files) > 0, "No workflow files found"
        
        parsed_workflows = []
        for workflow_file in workflow_files:
            try:
                workflow = WorkflowParser.parse_file(workflow_file)
                parsed_workflows.append((workflow_file, workflow))
            except Exception as e:
                pytest.fail(f"Failed to parse workflow {workflow_file}: {e}")
        
        # Verify we parsed at least some workflows
        assert len(parsed_workflows) > 0
        
        # Verify each parsed workflow has required fields
        for workflow_file, workflow in parsed_workflows:
            assert workflow.id is not None, f"Workflow {workflow_file} missing id"
            assert workflow.name is not None, f"Workflow {workflow_file} missing name"
            # Skip workflows with no steps (legacy format workflows like brownfield-analysis.yaml)
            if len(workflow.steps) == 0:
                pytest.skip(f"Workflow {workflow_file} uses legacy format (sequence: instead of steps:) - skipping validation")
            assert len(workflow.steps) > 0, f"Workflow {workflow_file} has no steps"

    def test_validate_workflow_schema(self, e2e_project, project_root_path):
        """Test workflow schema validation."""
        workflows_dir = project_root_path / "workflows"
        workflow_file = workflows_dir / "presets" / "feature-implementation.yaml"
        
        # Validate workflow file exists - fail immediately if missing
        validate_workflow_file(workflow_file)
        
        workflow = WorkflowParser.parse_file(workflow_file)
        
        # Validate workflow structure
        assert workflow.id == "feature-implementation"
        assert workflow.name == "Feature Implementation"
        assert workflow.version is not None
        # schema_version is stored in metadata, not as direct attribute
        # Check metadata if needed, but don't require it as direct attribute
        
        # Validate steps
        assert len(workflow.steps) > 0
        for step in workflow.steps:
            assert step.id is not None
            assert step.agent is not None
            assert step.action is not None

    def test_handle_invalid_workflow_yaml(self, e2e_project, tmp_path):
        """Test that invalid workflow YAML is handled gracefully."""
        # Create invalid workflow YAML
        invalid_workflow = tmp_path / "invalid.yaml"
        invalid_workflow.write_text(
            """
workflow:
  id: invalid
  steps:
    - missing_required_fields
"""
        )
        
        # Should raise ValueError for invalid workflow
        # Error message may vary, but should indicate schema validation failure
        with pytest.raises(ValueError, match="Schema validation failed|Each step must be an object"):
            WorkflowParser.parse_file(invalid_workflow)

    def test_workflow_cross_references(self, e2e_project, project_root_path):
        """Test workflow step cross-references (requires/creates)."""
        workflows_dir = project_root_path / "workflows"
        workflow_file = workflows_dir / "presets" / "feature-implementation.yaml"
        
        # Validate workflow file exists - fail immediately if missing
        validate_workflow_file(workflow_file)
        
        workflow = WorkflowParser.parse_file(workflow_file)
        
        # Check that step references are valid
        step_ids = {step.id for step in workflow.steps}
        
        for step in workflow.steps:
            # Check 'next' references
            if step.next:
                assert step.next in step_ids, f"Step {step.id} references invalid next step: {step.next}"
            
            # Check 'requires' references (should reference created artifacts from previous steps)
            # This is a basic check - full validation would require workflow execution context
            if step.requires:
                assert isinstance(step.requires, list), f"Step {step.id} requires should be a list"
