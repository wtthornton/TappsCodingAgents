"""Tests for agent_contracts module."""

import pytest

from tapps_agents.simple_mode.agent_contracts import (
    AGENT_CONTRACTS,
    ARCHITECT_CONTRACT,
    DESIGNER_CONTRACT,
    IMPLEMENTER_CONTRACT,
    AgentContractValidator,
    CommandContract,
)


class TestCommandContract:
    """Tests for CommandContract model."""

    def test_create_basic(self):
        """Test creating basic command contract."""
        contract = CommandContract(
            required_params=["param1"],
            optional_params=["param2"],
        )
        assert "param1" in contract.required_params
        assert "param2" in contract.optional_params

    def test_no_overlap_validation(self):
        """Test that required and optional can't overlap."""
        with pytest.raises(ValueError, match="cannot be both required and optional"):
            CommandContract(
                required_params=["param1"],
                optional_params=["param1"],
            )


class TestAgentContract:
    """Tests for AgentContract model."""

    def test_architect_contract(self):
        """Test architect contract definition."""
        assert ARCHITECT_CONTRACT.agent_name == "architect"
        assert "design-system" in ARCHITECT_CONTRACT.commands
        
        design_cmd = ARCHITECT_CONTRACT.commands["design-system"]
        assert "requirements" in design_cmd.required_params

    def test_designer_contract(self):
        """Test designer contract definition."""
        assert DESIGNER_CONTRACT.agent_name == "designer"
        assert "design-api" in DESIGNER_CONTRACT.commands
        
        api_cmd = DESIGNER_CONTRACT.commands["design-api"]
        assert "requirements" in api_cmd.required_params

    def test_implementer_contract(self):
        """Test implementer contract definition."""
        assert IMPLEMENTER_CONTRACT.agent_name == "implementer"
        assert "implement" in IMPLEMENTER_CONTRACT.commands
        
        impl_cmd = IMPLEMENTER_CONTRACT.commands["implement"]
        assert "specification" in impl_cmd.required_params
        assert "file_path" in impl_cmd.required_params


class TestAgentContractValidator:
    """Tests for AgentContractValidator."""

    def test_validate_valid_task(self):
        """Test validating a valid task."""
        validator = AgentContractValidator()
        task = {
            "agent": "architect",
            "command": "design-system",
            "args": {"requirements": "Build a REST API"},
        }
        result = validator.validate_task(task)
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_missing_required_param(self):
        """Test validating task with missing required param."""
        validator = AgentContractValidator()
        task = {
            "agent": "architect",
            "command": "design-system",
            "args": {},  # Missing 'requirements'
        }
        result = validator.validate_task(task)
        assert not result.valid
        assert any("requirements" in err for err in result.errors)

    def test_validate_unknown_command(self):
        """Test validating task with unknown command."""
        validator = AgentContractValidator()
        task = {
            "agent": "architect",
            "command": "design",  # Wrong command - should be "design-system"
            "args": {"requirements": "test"},
        }
        result = validator.validate_task(task)
        assert not result.valid
        assert any("Unknown command" in err for err in result.errors)

    def test_validate_unknown_agent(self):
        """Test validating task with unknown agent."""
        validator = AgentContractValidator()
        task = {
            "agent": "unknown_agent",
            "command": "some_command",
            "args": {},
        }
        result = validator.validate_task(task)
        # Should be valid but with warning
        assert result.valid
        assert any("No contract defined" in warn for warn in result.warnings)

    def test_validate_tasks_batch(self):
        """Test validating multiple tasks."""
        validator = AgentContractValidator()
        tasks = [
            {
                "agent": "architect",
                "command": "design-system",
                "args": {"requirements": "test"},
            },
            {
                "agent": "designer",
                "command": "design-api",
                "args": {},  # Missing requirements
            },
        ]
        result = validator.validate_tasks(tasks)
        assert not result.valid
        assert any("Task 1" in err for err in result.errors)

    def test_validate_empty_args(self):
        """Test validating task with empty string arg."""
        validator = AgentContractValidator()
        task = {
            "agent": "architect",
            "command": "design-system",
            "args": {"requirements": ""},  # Empty string
        }
        result = validator.validate_task(task)
        assert not result.valid
        assert any("requirements" in err for err in result.errors)

    def test_get_required_params(self):
        """Test getting required params for command."""
        validator = AgentContractValidator()
        params = validator.get_required_params("implementer", "implement")
        assert "specification" in params
        assert "file_path" in params

    def test_get_required_params_unknown(self):
        """Test getting required params for unknown command."""
        validator = AgentContractValidator()
        params = validator.get_required_params("unknown", "unknown")
        assert params == []

    def test_all_contracts_loaded(self):
        """Test that all expected contracts are loaded."""
        assert "enhancer" in AGENT_CONTRACTS
        assert "planner" in AGENT_CONTRACTS
        assert "architect" in AGENT_CONTRACTS
        assert "designer" in AGENT_CONTRACTS
        assert "implementer" in AGENT_CONTRACTS
        assert "reviewer" in AGENT_CONTRACTS
        assert "tester" in AGENT_CONTRACTS
