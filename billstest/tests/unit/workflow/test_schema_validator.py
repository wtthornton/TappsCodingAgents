"""
Unit tests for Schema Validator.
"""

from pathlib import Path

import pytest

from tapps_agents.workflow.schema_validator import (
    SchemaVersion,
    ValidationError,
    WorkflowSchemaValidator,
)

pytestmark = pytest.mark.unit


class TestWorkflowSchemaValidator:
    """Test cases for WorkflowSchemaValidator."""

    @pytest.fixture
    def validator(self):
        """Create a WorkflowSchemaValidator instance."""
        return WorkflowSchemaValidator()

    def test_validator_initialization(self, validator):
        """Test validator initialization."""
        assert validator.schema_version == SchemaVersion.LATEST.value

    def test_validator_custom_version(self):
        """Test validator with custom schema version."""
        validator = WorkflowSchemaValidator(schema_version="1.0")
        assert validator.schema_version == "1.0"

    def test_validator_unsupported_version(self):
        """Test validator with unsupported version."""
        with pytest.raises(ValueError, match="Unsupported schema version"):
            WorkflowSchemaValidator(schema_version="3.0")

    def test_validate_workflow_valid(self, validator):
        """Test validating a valid workflow."""
        workflow_data = {
            "workflow": {
                "id": "test-workflow",
                "name": "Test Workflow",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "analyze",
                        "requires": [],
                        "creates": ["req"]
                    }
                ]
            }
        }
        
        errors = validator.validate_workflow(workflow_data)
        
        assert len(errors) == 0

    def test_validate_workflow_missing_id(self, validator):
        """Test validating workflow with missing id."""
        workflow_data = {
            "workflow": {
                "name": "Test Workflow",
                "version": "1.0.0"
            }
        }
        
        errors = validator.validate_workflow(workflow_data)
        
        assert len(errors) > 0
        assert any("id" in str(error).lower() for error in errors)

    def test_validate_workflow_missing_steps(self, validator):
        """Test validating workflow with missing steps."""
        workflow_data = {
            "workflow": {
                "id": "test-workflow",
                "name": "Test Workflow",
                "version": "1.0.0"
            }
        }
        
        errors = validator.validate_workflow(workflow_data)
        
        assert len(errors) > 0
        assert any("steps" in str(error).lower() for error in errors)

    def test_validate_workflow_invalid_step(self, validator):
        """Test validating workflow with invalid step."""
        workflow_data = {
            "workflow": {
                "id": "test-workflow",
                "name": "Test Workflow",
                "version": "1.0.0",
                "steps": [
                    {
                        # Missing required fields
                        "agent": "analyst"
                    }
                ]
            }
        }
        
        errors = validator.validate_workflow(workflow_data)
        
        assert len(errors) > 0

    def test_validate_workflow_not_dict(self, validator):
        """Test validating workflow that's not a dict."""
        workflow_data = "not a workflow"
        
        errors = validator.validate_workflow(workflow_data)
        
        assert len(errors) > 0
        assert any("object" in str(error).lower() or "mapping" in str(error).lower() for error in errors)


class TestValidationError:
    """Test cases for ValidationError."""

    def test_validation_error_creation(self):
        """Test creating a validation error."""
        error = ValidationError(
            field="id",
            message="Required field missing",
            file_path=Path("test.yaml"),
            step_id="step1"
        )
        
        assert error.field == "id"
        assert error.message == "Required field missing"
        assert error.file_path == Path("test.yaml")
        assert error.step_id == "step1"

    def test_validation_error_str(self):
        """Test validation error string representation."""
        error = ValidationError(
            field="id",
            message="Required field missing",
            file_path=Path("test.yaml"),
            step_id="step1"
        )
        
        error_str = str(error)
        assert "test.yaml" in error_str
        assert "step1" in error_str
        assert "id" in error_str
        assert "Required field missing" in error_str

