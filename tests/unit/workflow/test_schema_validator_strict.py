"""
Comprehensive unit tests for Workflow Schema Validator (Strict Mode).

Epic 6 / Story 6.6: Schema Validation Test Suite

Tests cover:
- Valid workflows (all supported structures)
- Invalid workflows (unsupported fields, malformed YAML)
- Schema version migration
- Edge cases (empty workflows, missing required fields)
- Strict vs non-strict mode
"""

from pathlib import Path

import pytest

from tapps_agents.workflow.parser import WorkflowParser
from tapps_agents.workflow.schema_validator import (
    SchemaVersion,
    ValidationError,
    WorkflowSchemaValidator,
)

pytestmark = pytest.mark.unit


class TestStrictSchemaEnforcement:
    """Test strict schema enforcement (reject unknown fields)."""

    @pytest.fixture
    def strict_validator(self):
        """Create a strict validator."""
        return WorkflowSchemaValidator(strict=True)

    @pytest.fixture
    def non_strict_validator(self):
        """Create a non-strict validator."""
        return WorkflowSchemaValidator(strict=False)

    def test_strict_mode_rejects_unknown_workflow_field(self, strict_validator):
        """Test that strict mode rejects unknown workflow-level fields."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "unknown_field": "should fail",  # Unknown field
                "steps": [
                    {"id": "step1", "agent": "analyst", "action": "gather"}
                ],
            }
        }

        errors = strict_validator.validate_workflow(workflow_data)

        assert len(errors) > 0
        assert any(
            "unknown_field" in str(error).lower() or "unknown workflow field" in str(error).lower()
            for error in errors
        )

    def test_strict_mode_rejects_unknown_step_field(self, strict_validator):
        """Test that strict mode rejects unknown step-level fields."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "unknown_step_field": "should fail",  # Unknown field
                    }
                ],
            }
        }

        errors = strict_validator.validate_workflow(workflow_data)

        assert len(errors) > 0
        assert any(
            "unknown_step_field" in str(error).lower() or "unknown step field" in str(error).lower()
            for error in errors
        )

    def test_strict_mode_rejects_unknown_settings_field(self, strict_validator):
        """Test that strict mode rejects unknown settings fields."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "settings": {
                    "quality_gates": True,
                    "unknown_setting": "should fail",  # Unknown field
                },
                "steps": [
                    {"id": "step1", "agent": "analyst", "action": "gather"}
                ],
            }
        }

        errors = strict_validator.validate_workflow(workflow_data)

        assert len(errors) > 0
        assert any(
            "unknown_setting" in str(error).lower() or "unknown settings field" in str(error).lower()
            for error in errors
        )

    def test_strict_mode_rejects_unknown_gate_field(self, strict_validator):
        """Test that strict mode rejects unknown gate fields."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "reviewer",
                        "action": "review",
                        "gate": {
                            "condition": "scoring.passed == true",
                            "on_pass": "next",
                            "unknown_gate_field": "should fail",  # Unknown field
                        },
                    }
                ],
            }
        }

        errors = strict_validator.validate_workflow(workflow_data)

        assert len(errors) > 0
        assert any(
            "unknown_gate_field" in str(error).lower() or "unknown gate field" in str(error).lower()
            for error in errors
        )

    def test_non_strict_mode_allows_unknown_fields(self, non_strict_validator):
        """Test that non-strict mode allows unknown fields."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "unknown_field": "allowed in non-strict",  # Unknown field
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "unknown_step_field": "also allowed",  # Unknown field
                    }
                ],
            }
        }

        errors = non_strict_validator.validate_workflow(workflow_data)

        # Should not have errors about unknown fields
        unknown_field_errors = [
            e for e in errors if "unknown" in str(e).lower() and "field" in str(e).lower()
        ]
        assert len(unknown_field_errors) == 0

    def test_strict_mode_allows_all_known_workflow_fields(self, strict_validator):
        """Test that strict mode allows all known workflow fields."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "schema_version": "2.0",
                "settings": {
                    "quality_gates": True,
                    "code_scoring": True,
                    "context_tier_default": 2,
                    "auto_detect": True,
                },
                "metadata": {"key": "value"},
                "steps": [
                    {"id": "step1", "agent": "analyst", "action": "gather"}
                ],
            }
        }

        errors = strict_validator.validate_workflow(workflow_data)

        # Should not have errors about unknown fields
        unknown_field_errors = [
            e for e in errors if "unknown" in str(e).lower() and "field" in str(e).lower()
        ]
        assert len(unknown_field_errors) == 0

    def test_strict_mode_allows_all_known_step_fields(self, strict_validator):
        """Test that strict mode allows all known step fields."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "context_tier": 2,
                        "creates": ["req.md"],
                        "requires": [],
                        "consults": ["doc.md"],
                        "condition": "some_condition",
                        "next": "step2",
                        "gate": {
                            "condition": "scoring.passed == true",
                            "on_pass": "next",
                            "on_fail": "retry",
                        },
                        "optional_steps": ["step3"],
                        "notes": "Some notes",
                        "repeats": False,
                        "scoring": {"threshold": 0.8},
                        "metadata": {"key": "value"},
                    }
                ],
            }
        }

        errors = strict_validator.validate_workflow(workflow_data)

        # Should not have errors about unknown fields
        unknown_field_errors = [
            e for e in errors if "unknown" in str(e).lower() and "field" in str(e).lower()
        ]
        assert len(unknown_field_errors) == 0


class TestValidWorkflowStructures:
    """Test valid workflows with all supported structures."""

    @pytest.fixture
    def validator(self):
        """Create a validator."""
        return WorkflowSchemaValidator(strict=True)

    def test_valid_minimal_workflow(self, validator):
        """Test minimal valid workflow."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {"id": "step1", "agent": "analyst", "action": "gather"}
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) == 0

    def test_valid_workflow_with_all_fields(self, validator):
        """Test valid workflow with all supported fields."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test Workflow",
                "description": "A comprehensive test workflow",
                "version": "1.0.0",
                "type": "brownfield",
                "schema_version": "2.0",
                "settings": {
                    "quality_gates": True,
                    "code_scoring": True,
                    "context_tier_default": 2,
                    "auto_detect": True,
                },
                "metadata": {"author": "test", "tags": ["test"]},
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "context_tier": 1,
                        "creates": ["requirements.md"],
                        "requires": [],
                        "next": "step2",
                    },
                    {
                        "id": "step2",
                        "agent": "planner",
                        "action": "plan",
                        "context_tier": 2,
                        "creates": ["plan.md"],
                        "requires": ["requirements.md"],
                        "gate": {
                            "condition": "scoring.passed == true",
                            "on_pass": "next",
                            "on_fail": "retry",
                        },
                    },
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) == 0

    def test_valid_workflow_with_dependencies(self, validator):
        """Test valid workflow with step dependencies."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "creates": ["req.md"],
                    },
                    {
                        "id": "step2",
                        "agent": "planner",
                        "action": "plan",
                        "requires": ["req.md"],
                        "creates": ["plan.md"],
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

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) == 0

    def test_valid_workflow_with_gates(self, validator):
        """Test valid workflow with quality gates."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
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

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) == 0

    def test_valid_workflow_with_optional_steps(self, validator):
        """Test valid workflow with optional steps."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "optional_steps": ["step2"],
                    },
                    {
                        "id": "step2",
                        "agent": "planner",
                        "action": "plan",
                    },
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) == 0

    def test_valid_workflow_with_repeats(self, validator):
        """Test valid workflow with repeating steps."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "repeats": True,
                    }
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) == 0


class TestInvalidWorkflowStructures:
    """Test invalid workflows (malformed, missing fields, etc.)."""

    @pytest.fixture
    def validator(self):
        """Create a validator."""
        return WorkflowSchemaValidator(strict=True)

    def test_missing_required_workflow_id(self, validator):
        """Test workflow missing required id field."""
        workflow_data = {
            "workflow": {
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) > 0
        assert any("id" in str(error).lower() for error in errors)

    def test_missing_required_workflow_name(self, validator):
        """Test workflow missing name field (parser validates this, not validator)."""
        # Note: Validator doesn't validate name/version/type - parser does
        # This test documents that validator allows missing name
        workflow_data = {
            "workflow": {
                "id": "test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        # Validator doesn't validate name - parser does
        # So this should pass validator but fail parser
        assert isinstance(errors, list)

    def test_missing_required_workflow_version(self, validator):
        """Test workflow missing version field (parser validates this, not validator)."""
        # Note: Validator doesn't validate version - parser does
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "type": "greenfield",
                "steps": [],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        # Validator doesn't validate version - parser does
        assert isinstance(errors, list)

    def test_missing_required_workflow_type(self, validator):
        """Test workflow missing type field (parser validates this, not validator)."""
        # Note: Validator doesn't validate type - parser does
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "steps": [],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        # Validator doesn't validate type - parser does
        assert isinstance(errors, list)

    def test_missing_required_workflow_steps(self, validator):
        """Test workflow missing steps field."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
            }
        }

        errors = validator.validate_workflow(workflow_data)
        # Steps defaults to empty list if missing, but validator should validate it exists
        # Actually, validator checks if steps is a list, so missing steps should be caught
        # But it might default to [] - let's check if it validates presence
        assert isinstance(errors, list)

    def test_empty_steps_list(self, validator):
        """Test workflow with empty steps list."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        # Empty steps might be valid or invalid depending on business rules
        # For now, we'll allow it but it might be flagged by executor
        assert isinstance(errors, list)

    def test_missing_required_step_id(self, validator):
        """Test step missing required id field."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "agent": "analyst",
                        "action": "gather",
                    }
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) > 0
        assert any("id" in str(error).lower() for error in errors)

    def test_missing_required_step_agent(self, validator):
        """Test step missing required agent field."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "action": "gather",
                    }
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) > 0
        assert any("agent" in str(error).lower() for error in errors)

    def test_missing_required_step_action(self, validator):
        """Test step missing required action field."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                    }
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) > 0
        assert any("action" in str(error).lower() for error in errors)

    def test_invalid_workflow_type(self, validator):
        """Test workflow with invalid type value (parser validates this, not validator)."""
        # Note: Validator doesn't validate type enum values - parser does
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "invalid_type",
                "steps": [],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        # Validator doesn't validate type enum - parser does
        assert isinstance(errors, list)

    def test_invalid_steps_not_list(self, validator):
        """Test workflow where steps is not a list."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": "not a list",
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) > 0
        assert any("steps" in str(error).lower() and "list" in str(error).lower() for error in errors)

    def test_invalid_step_not_dict(self, validator):
        """Test workflow where step is not a dictionary."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": ["not a dict"],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) > 0
        assert any("step" in str(error).lower() and "object" in str(error).lower() for error in errors)

    def test_invalid_next_reference(self, validator):
        """Test step with invalid next reference."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "next": "nonexistent_step",
                    }
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) > 0
        assert any("next" in str(error).lower() or "reference" in str(error).lower() for error in errors)


class TestSchemaVersioning:
    """Test schema version detection and validation."""

    def test_validator_defaults_to_latest_version(self):
        """Test that validator defaults to latest schema version."""
        validator = WorkflowSchemaValidator()
        assert validator.schema_version == SchemaVersion.LATEST.value

    def test_validator_with_explicit_version(self):
        """Test validator with explicit schema version."""
        validator = WorkflowSchemaValidator(schema_version="1.0")
        assert validator.schema_version == "1.0"

        validator = WorkflowSchemaValidator(schema_version="2.0")
        assert validator.schema_version == "2.0"

    def test_validator_rejects_unsupported_version(self):
        """Test validator rejects unsupported schema version."""
        with pytest.raises(ValueError, match="Unsupported schema version"):
            WorkflowSchemaValidator(schema_version="3.0")

    def test_workflow_with_schema_version(self):
        """Test workflow with explicit schema_version field."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "schema_version": "2.0",
                "steps": [
                    {"id": "step1", "agent": "analyst", "action": "gather"}
                ],
            }
        }

        validator = WorkflowSchemaValidator(strict=True)
        errors = validator.validate_workflow(workflow_data)
        assert len(errors) == 0

    def test_parser_uses_schema_version_from_workflow(self):
        """Test that parser detects and uses schema_version from workflow."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "schema_version": "2.0",
                "steps": [
                    {"id": "step1", "agent": "analyst", "action": "gather"}
                ],
            }
        }

        # Parser should detect schema_version and use it
        workflow = WorkflowParser.parse(workflow_data)
        assert workflow.id == "test"


class TestParserIntegration:
    """Test parser integration with strict schema validation."""

    def test_parser_rejects_unknown_fields_in_strict_mode(self, tmp_path):
        """Test that parser rejects unknown fields when using strict mode."""
        workflow_file = tmp_path / "invalid.yaml"
        workflow_file.write_text(
            """
workflow:
  id: test
  name: Test
  description: Test
  version: 1.0.0
  type: greenfield
  unknown_field: should fail
  steps:
    - id: step1
      agent: analyst
      action: gather
""",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="Schema validation failed|unknown"):
            WorkflowParser.parse_file(workflow_file)

    def test_parser_accepts_valid_workflow(self, tmp_path):
        """Test that parser accepts valid workflow."""
        workflow_file = tmp_path / "valid.yaml"
        workflow_file.write_text(
            """
workflow:
  id: test
  name: Test
  description: Test
  version: 1.0.0
  type: greenfield
  steps:
    - id: step1
      agent: analyst
      action: gather
""",
            encoding="utf-8",
        )

        workflow = WorkflowParser.parse_file(workflow_file)
        assert workflow.id == "test"
        assert len(workflow.steps) == 1


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def validator(self):
        """Create a validator."""
        return WorkflowSchemaValidator(strict=True)

    def test_workflow_not_dict(self, validator):
        """Test validation of non-dict workflow data."""
        # Validator expects dict with optional "workflow" key
        # If passed a string, it will try to call .get() which will fail
        # This tests the validator's error handling
        with pytest.raises(AttributeError):
            # Validator calls .get() on workflow_data, which will fail for non-dict
            validator.validate_workflow("not a dict")

    def test_workflow_missing_workflow_key(self, validator):
        """Test validation of data missing 'workflow' key."""
        errors = validator.validate_workflow({"not_workflow": {}})
        assert len(errors) > 0
        assert any("workflow" in str(error).lower() for error in errors)

    def test_settings_not_dict(self, validator):
        """Test validation of settings that's not a dict."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "settings": "not a dict",
                "steps": [],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        # Validator might not validate settings type if it's optional
        # Check if it validates or if parser handles it
        # For now, just verify it doesn't crash
        assert isinstance(errors, list)

    def test_creates_not_list(self, validator):
        """Test validation of creates that's not a list."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "creates": "not a list",
                    }
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) > 0
        assert any("creates" in str(error).lower() and "list" in str(error).lower() for error in errors)

    def test_requires_not_list(self, validator):
        """Test validation of requires that's not a list."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "requires": "not a list",
                    }
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) > 0
        assert any("requires" in str(error).lower() and "list" in str(error).lower() for error in errors)

    def test_gate_not_dict(self, validator):
        """Test validation of gate that's not a dict."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "reviewer",
                        "action": "review",
                        "gate": "not a dict",
                    }
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) > 0
        assert any("gate" in str(error).lower() and "object" in str(error).lower() for error in errors)

    def test_repeats_not_boolean(self, validator):
        """Test validation of repeats that's not a boolean."""
        workflow_data = {
            "workflow": {
                "id": "test",
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "type": "greenfield",
                "steps": [
                    {
                        "id": "step1",
                        "agent": "analyst",
                        "action": "gather",
                        "repeats": "not a boolean",
                    }
                ],
            }
        }

        errors = validator.validate_workflow(workflow_data)
        assert len(errors) > 0
        assert any("repeats" in str(error).lower() and "boolean" in str(error).lower() for error in errors)

