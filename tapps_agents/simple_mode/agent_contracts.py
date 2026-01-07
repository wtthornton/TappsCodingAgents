"""
Agent Contract Definitions and Validator.

Pydantic v2 contracts for type-safe agent task validation.
Ensures correct parameters are passed to agents before execution.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field, model_validator


@runtime_checkable
class AgentTask(Protocol):
    """Protocol for agent task structure (Python 3.8+ structural subtyping)."""

    agent_id: str
    agent: str
    command: str
    args: dict[str, Any]


class CommandContract(BaseModel):
    """Contract for a single agent command."""

    required_params: list[str] = Field(default_factory=list)
    optional_params: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_no_overlap(self):
        """Ensure required and optional don't overlap."""
        overlap = set(self.required_params) & set(self.optional_params)
        if overlap:
            msg = f"Parameters cannot be both required and optional: {overlap}"
            raise ValueError(msg)
        return self


class AgentContract(BaseModel):
    """Contract for an agent's commands."""

    agent_name: str
    commands: dict[str, CommandContract]


class ValidationResult(BaseModel):
    """Result of contract validation."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# Define contracts for agents used in build workflow
ENHANCER_CONTRACT = AgentContract(
    agent_name="enhancer",
    commands={
        "enhance": CommandContract(
            required_params=["prompt"],
            optional_params=["output_format", "context"],
        ),
        "enhance-quick": CommandContract(
            required_params=["prompt"],
            optional_params=["output_format"],
        ),
    },
)

PLANNER_CONTRACT = AgentContract(
    agent_name="planner",
    commands={
        "create-story": CommandContract(
            required_params=["description"],
            optional_params=["epic", "priority", "context"],
        ),
        "plan": CommandContract(
            required_params=["description"],
            optional_params=["context"],
        ),
    },
)

ARCHITECT_CONTRACT = AgentContract(
    agent_name="architect",
    commands={
        "design-system": CommandContract(
            required_params=["requirements"],
            optional_params=["context", "output_file"],
        ),
        "create-diagram": CommandContract(
            required_params=["architecture_description"],
            optional_params=["diagram_type", "output_file"],
        ),
        "select-technology": CommandContract(
            required_params=["component_description"],
            optional_params=["requirements", "constraints"],
        ),
        "design-security": CommandContract(
            required_params=["system_description"],
            optional_params=["threat_model"],
        ),
        "define-boundaries": CommandContract(
            required_params=["system_description"],
            optional_params=["context"],
        ),
    },
)

DESIGNER_CONTRACT = AgentContract(
    agent_name="designer",
    commands={
        "design-api": CommandContract(
            required_params=["requirements"],
            optional_params=["api_type", "output_file"],
        ),
        "design-data-model": CommandContract(
            required_params=["requirements"],
            optional_params=["data_source", "output_file"],
        ),
        "design-ui": CommandContract(
            required_params=["feature_description"],
            optional_params=["user_stories", "output_file"],
        ),
        "create-wireframe": CommandContract(
            required_params=["screen_description"],
            optional_params=["wireframe_type", "output_file"],
        ),
        "define-design-system": CommandContract(
            required_params=["project_description"],
            optional_params=["brand_guidelines", "output_file"],
        ),
    },
)

IMPLEMENTER_CONTRACT = AgentContract(
    agent_name="implementer",
    commands={
        "implement": CommandContract(
            required_params=["specification", "file_path"],
            optional_params=["context", "language"],
        ),
        "generate-code": CommandContract(
            required_params=["specification"],
            optional_params=["file_path", "context", "language"],
        ),
        "refactor": CommandContract(
            required_params=["file_path", "instruction"],
            optional_params=["preview"],
        ),
    },
)

REVIEWER_CONTRACT = AgentContract(
    agent_name="reviewer",
    commands={
        "review": CommandContract(
            required_params=[],  # Can review current file
            optional_params=["file", "files", "pattern"],
        ),
        "score": CommandContract(
            required_params=[],  # Can score current file
            optional_params=["file", "files", "pattern"],
        ),
        "lint": CommandContract(
            required_params=[],
            optional_params=["file", "files", "pattern"],
        ),
        "type-check": CommandContract(
            required_params=[],
            optional_params=["file", "files", "pattern"],
        ),
        "security-scan": CommandContract(
            required_params=[],
            optional_params=["file", "files", "pattern"],
        ),
    },
)

TESTER_CONTRACT = AgentContract(
    agent_name="tester",
    commands={
        "test": CommandContract(
            required_params=[],  # Can test current file
            optional_params=["file", "integration", "coverage"],
        ),
        "generate-tests": CommandContract(
            required_params=[],
            optional_params=["file", "integration"],
        ),
        "run-tests": CommandContract(
            required_params=[],
            optional_params=["coverage"],
        ),
    },
)

# All contracts indexed by agent name
AGENT_CONTRACTS: dict[str, AgentContract] = {
    "enhancer": ENHANCER_CONTRACT,
    "planner": PLANNER_CONTRACT,
    "architect": ARCHITECT_CONTRACT,
    "designer": DESIGNER_CONTRACT,
    "implementer": IMPLEMENTER_CONTRACT,
    "reviewer": REVIEWER_CONTRACT,
    "tester": TESTER_CONTRACT,
}


class AgentContractValidator:
    """Validates agent tasks against contracts before execution."""

    def __init__(self, contracts: dict[str, AgentContract] | None = None):
        """Initialize validator with contracts.

        Args:
            contracts: Optional custom contracts (defaults to AGENT_CONTRACTS)
        """
        self.contracts = contracts or AGENT_CONTRACTS

    def validate_task(self, task: dict[str, Any]) -> ValidationResult:
        """Validate task parameters against contract.

        Args:
            task: Task dictionary with agent, command, and args

        Returns:
            ValidationResult with errors and warnings
        """
        errors: list[str] = []
        warnings: list[str] = []

        agent_name = task.get("agent")
        command = task.get("command", "").lstrip("*")
        args = task.get("args", {})

        if not agent_name:
            errors.append("Task missing 'agent' field")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        if not command:
            errors.append(f"Task for agent '{agent_name}' missing 'command' field")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Check if we have a contract for this agent
        if agent_name not in self.contracts:
            warnings.append(f"No contract defined for agent: {agent_name}")
            return ValidationResult(valid=True, warnings=warnings)

        contract = self.contracts[agent_name]

        # Check if command is valid
        if command not in contract.commands:
            available_commands = list(contract.commands.keys())
            errors.append(
                f"Unknown command '{command}' for agent '{agent_name}'. "
                f"Available commands: {available_commands}"
            )
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        cmd_contract = contract.commands[command]

        # Check required params
        for param in cmd_contract.required_params:
            if param not in args or args[param] is None or args[param] == "":
                errors.append(
                    f"Missing required parameter '{param}' for {agent_name}.{command}"
                )

        # Check for unexpected params (warning only)
        all_known_params = set(cmd_contract.required_params) | set(
            cmd_contract.optional_params
        )
        for param in args:
            if param not in all_known_params:
                warnings.append(
                    f"Unexpected parameter '{param}' for {agent_name}.{command}"
                )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_tasks(self, tasks: list[dict[str, Any]]) -> ValidationResult:
        """Validate multiple tasks.

        Args:
            tasks: List of task dictionaries

        Returns:
            Aggregated ValidationResult
        """
        all_errors: list[str] = []
        all_warnings: list[str] = []

        for i, task in enumerate(tasks):
            result = self.validate_task(task)
            # Add task index to errors for context
            for error in result.errors:
                all_errors.append(f"Task {i}: {error}")
            for warning in result.warnings:
                all_warnings.append(f"Task {i}: {warning}")

        return ValidationResult(
            valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
        )

    def suggest_fix(self, task: dict[str, Any]) -> dict[str, Any] | None:
        """Suggest a fix for a task with validation errors.

        Args:
            task: Task dictionary that failed validation

        Returns:
            Fixed task dictionary or None if no fix available
        """
        agent_name = task.get("agent")
        command = task.get("command", "").lstrip("*")

        if not agent_name or agent_name not in self.contracts:
            return None

        contract = self.contracts[agent_name]

        # Check for command mismatch (common issue)
        if command not in contract.commands:
            # Try to find similar command
            for valid_cmd in contract.commands:
                if command.replace("-", "") in valid_cmd.replace("-", "") or \
                   valid_cmd.replace("-", "") in command.replace("-", ""):
                    # Found similar command, suggest fix
                    fixed_task = task.copy()
                    fixed_task["command"] = valid_cmd
                    return fixed_task

        return None

    def get_required_params(self, agent_name: str, command: str) -> list[str]:
        """Get required parameters for an agent command.

        Args:
            agent_name: Name of the agent
            command: Command name (with or without *)

        Returns:
            List of required parameter names
        """
        command = command.lstrip("*")
        if agent_name not in self.contracts:
            return []
        contract = self.contracts[agent_name]
        if command not in contract.commands:
            return []
        return contract.commands[command].required_params
