"""
Output Contracts for TappsCodingAgents.

Defines standard output formats and contracts for automatic output passing
between agents in workflows.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentOutputContract:
    """
    Contract defining expected output format from an agent.
    
    Used to validate and transform outputs for automatic passing
    to next agent in workflow.
    """

    agent_name: str
    command: str
    required_fields: list[str]
    optional_fields: list[str] = field(default_factory=list)
    field_types: dict[str, type] = field(default_factory=dict)
    transformations: dict[str, str] = field(default_factory=dict)  # field_name -> target_agent.field_name

    def validate(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate output against contract.
        
        Args:
            output: Agent output dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        for field_name in self.required_fields:
            if field_name not in output:
                errors.append(f"Missing required field: {field_name}")

        # Check field types if specified
        for field_name, expected_type in self.field_types.items():
            if field_name in output:
                if not isinstance(output[field_name], expected_type):
                    errors.append(
                        f"Field {field_name} has wrong type: expected {expected_type.__name__}, got {type(output[field_name]).__name__}"
                    )

        return len(errors) == 0, errors

    def transform_for_next_agent(
        self, output: dict[str, Any], target_agent: str
    ) -> dict[str, Any]:
        """
        Transform output for next agent in workflow.
        
        Args:
            output: Current agent output
            target_agent: Next agent name
            
        Returns:
            Transformed output dictionary
        """
        transformed = {}

        # Apply transformations
        for source_field, target_mapping in self.transformations.items():
            if source_field in output:
                # Format: "target_agent.field_name" or just "field_name"
                if "." in target_mapping:
                    target_agent_name, target_field = target_mapping.split(".", 1)
                    if target_agent_name == target_agent:
                        transformed[target_field] = output[source_field]
                else:
                    transformed[target_mapping] = output[source_field]

        # Copy remaining fields
        for key, value in output.items():
            if key not in self.transformations:
                transformed[key] = value

        return transformed


class OutputContractRegistry:
    """
    Registry of output contracts for all agents.
    
    Defines standard contracts and provides transformation utilities.
    """

    def __init__(self):
        """Initialize registry with default contracts."""
        self.contracts: dict[tuple[str, str], AgentOutputContract] = {}

        # Register default contracts
        self._register_default_contracts()

    def _register_default_contracts(self) -> None:
        """Register default output contracts."""
        # Planner -> Architect
        self.register(
            AgentOutputContract(
                agent_name="planner",
                command="plan",
                required_fields=["user_stories", "description"],
                optional_fields=["requirements", "dependencies", "estimates"],
                transformations={
                    "user_stories": "architect.requirements",
                    "description": "architect.context",
                    "requirements": "architect.requirements",
                },
            )
        )

        # Planner -> Designer
        self.register(
            AgentOutputContract(
                agent_name="planner",
                command="plan",
                required_fields=["user_stories"],
                optional_fields=["description", "requirements"],
                transformations={
                    "user_stories": "designer.requirements",
                    "description": "designer.requirements",
                },
            )
        )

        # Enhancer -> Planner
        self.register(
            AgentOutputContract(
                agent_name="enhancer",
                command="enhance",
                required_fields=["enhanced_prompt"],
                optional_fields=["analysis", "requirements", "architecture"],
                transformations={
                    "enhanced_prompt": "planner.description",
                    "requirements": "planner.requirements",
                },
            )
        )

        # Architect -> Designer
        self.register(
            AgentOutputContract(
                agent_name="architect",
                command="design-system",
                required_fields=["components"],
                optional_fields=["architecture", "technology_stack"],
                transformations={
                    "components": "designer.context",
                    "architecture": "designer.context",
                },
            )
        )

        # Designer -> Implementer
        self.register(
            AgentOutputContract(
                agent_name="designer",
                command="design-api",
                required_fields=["endpoints", "data_models"],
                optional_fields=["specification"],
                transformations={
                    "specification": "implementer.specification",
                    "endpoints": "implementer.context",
                    "data_models": "implementer.context",
                },
            )
        )

        # Architect -> Implementer
        self.register(
            AgentOutputContract(
                agent_name="architect",
                command="design-system",
                required_fields=["components"],
                optional_fields=["architecture"],
                transformations={
                    "architecture": "implementer.context",
                    "components": "implementer.context",
                },
            )
        )

        # Implementer -> Reviewer
        self.register(
            AgentOutputContract(
                agent_name="implementer",
                command="implement",
                required_fields=["file_path"],
                optional_fields=["code", "specification"],
                transformations={
                    "file_path": "reviewer.file",
                },
            )
        )

        # Implementer -> Tester
        self.register(
            AgentOutputContract(
                agent_name="implementer",
                command="implement",
                required_fields=["file_path"],
                optional_fields=["code"],
                transformations={
                    "file_path": "tester.file",
                },
            )
        )

    def register(self, contract: AgentOutputContract) -> None:
        """
        Register an output contract.
        
        Args:
            contract: Contract to register
        """
        key = (contract.agent_name, contract.command)
        self.contracts[key] = contract

    def get_contract(self, agent_name: str, command: str) -> AgentOutputContract | None:
        """
        Get contract for agent/command.
        
        Args:
            agent_name: Agent name
            command: Command name
            
        Returns:
            Contract if found, None otherwise
        """
        return self.contracts.get((agent_name, command))

    def validate_output(
        self, agent_name: str, command: str, output: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        Validate output against contract.
        
        Args:
            agent_name: Agent name
            command: Command name
            output: Output to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        contract = self.get_contract(agent_name, command)
        if not contract:
            # No contract defined - assume valid
            return True, []

        return contract.validate(output)

    def transform_for_next_agent(
        self,
        source_agent: str,
        source_command: str,
        output: dict[str, Any],
        target_agent: str,
    ) -> dict[str, Any]:
        """
        Transform output for next agent.
        
        Args:
            source_agent: Source agent name
            source_command: Source command name
            output: Source agent output
            target_agent: Target agent name
            
        Returns:
            Transformed output dictionary
        """
        contract = self.get_contract(source_agent, source_command)
        if not contract:
            # No contract - return output as-is
            return output

        return contract.transform_for_next_agent(output, target_agent)


# Global registry instance
_registry: OutputContractRegistry | None = None


def get_output_contract_registry() -> OutputContractRegistry:
    """Get or create global output contract registry."""
    global _registry
    if _registry is None:
        _registry = OutputContractRegistry()
    return _registry
