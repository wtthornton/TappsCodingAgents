"""
Automatic Output Passing for Workflows.

Provides utilities to automatically pass outputs between workflow steps
using output contracts.
"""

from typing import Any

from ..core.output_contracts import get_output_contract_registry


class WorkflowOutputPasser:
    """
    Handles automatic output passing between workflow steps.
    
    Uses output contracts to validate and transform outputs for
    automatic passing to next agents in workflow.
    """

    def __init__(self, state: Any):
        """
        Initialize output passer.
        
        Args:
            state: WorkflowState instance
        """
        self.state = state
        self.registry = get_output_contract_registry()

    def store_agent_output(
        self,
        step_id: str,
        agent_name: str,
        command: str,
        output: dict[str, Any],
    ) -> None:
        """
        Store agent output in workflow state with validation.
        
        Args:
            step_id: Step ID that produced the output
            agent_name: Agent name
            command: Command that was executed
            output: Agent output dictionary
        """
        # Validate output against contract
        is_valid, errors = self.registry.validate_output(agent_name, command, output)
        
        if not is_valid:
            # Log warnings but still store output
            if hasattr(self.state, 'logger') and self.state.logger:
                self.state.logger.warning(
                    f"Output validation failed for {agent_name}.{command}: {errors}",
                    step_id=step_id,
                )

        # Store output in state variables
        if "agent_outputs" not in self.state.variables:
            self.state.variables["agent_outputs"] = {}

        self.state.variables["agent_outputs"][step_id] = {
            "agent": agent_name,
            "command": command,
            "output": output,
            "valid": is_valid,
            "errors": errors if not is_valid else [],
        }

        # Also store in agent-specific key for easy access
        agent_key = f"{agent_name}_result"
        self.state.variables[agent_key] = output

    def get_output_for_next_agent(
        self,
        source_step_id: str,
        target_agent: str,
        target_command: str,
    ) -> dict[str, Any]:
        """
        Get transformed output for next agent in workflow.
        
        Args:
            source_step_id: Source step ID
            target_agent: Target agent name
            target_command: Target command name
            
        Returns:
            Transformed output dictionary ready for target agent
        """
        # Get source output
        agent_outputs = self.state.variables.get("agent_outputs", {})
        if source_step_id not in agent_outputs:
            return {}

        source_data = agent_outputs[source_step_id]
        source_agent = source_data["agent"]
        source_command = source_data["command"]
        source_output = source_data["output"]

        # Transform output for target agent
        transformed = self.registry.transform_for_next_agent(
            source_agent=source_agent,
            source_command=source_command,
            output=source_output,
            target_agent=target_agent,
        )

        return transformed

    def prepare_agent_inputs(
        self,
        step_id: str,
        agent_name: str,
        command: str,
        base_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Prepare inputs for agent by including outputs from previous steps.
        
        Args:
            step_id: Current step ID
            agent_name: Agent name
            command: Command name
            base_inputs: Base input parameters
            
        Returns:
            Enhanced inputs with outputs from previous steps
        """
        enhanced_inputs = base_inputs.copy()

        # Get current step to find dependencies
        if not hasattr(self.state, 'workflow') or not self.state.workflow:
            return enhanced_inputs

        current_step = None
        for step in self.state.workflow.steps:
            if step.id == step_id:
                current_step = step
                break

        if not current_step:
            return enhanced_inputs

        # Find previous steps that this step depends on
        previous_steps = []
        for step in self.state.workflow.steps:
            # Check if current step requires artifacts from this step
            if step.id != step_id and step.id in self.state.completed_steps:
                # Check if current step depends on this step
                if current_step.requires:
                    for req_artifact in current_step.requires:
                        # Check if previous step creates this artifact
                        if step.creates and req_artifact in step.creates:
                            previous_steps.append(step)

        # Get outputs from previous steps and merge
        for prev_step in previous_steps:
            # Find the agent that executed this step
            prev_agent = prev_step.agent if hasattr(prev_step, 'agent') else None
            prev_action = prev_step.action if hasattr(prev_step, 'action') else None

            if prev_agent and prev_action:
                transformed = self.get_output_for_next_agent(
                    source_step_id=prev_step.id,
                    target_agent=agent_name,
                    target_command=command,
                )

                # Merge transformed output into inputs
                # Use agent name as prefix to avoid conflicts
                for key, value in transformed.items():
                    # Only add if not already in base_inputs
                    if key not in enhanced_inputs:
                        enhanced_inputs[key] = value
                    # Also add with agent prefix for explicit access
                    prefixed_key = f"{prev_agent}_{key}"
                    if prefixed_key not in enhanced_inputs:
                        enhanced_inputs[prefixed_key] = value

        return enhanced_inputs

    def aggregate_outputs(self, step_ids: list[str]) -> dict[str, Any]:
        """
        Aggregate outputs from multiple steps.
        
        Args:
            step_ids: List of step IDs to aggregate
            
        Returns:
            Aggregated output dictionary
        """
        aggregated = {
            "steps": [],
            "outputs": {},
            "errors": [],
        }

        agent_outputs = self.state.variables.get("agent_outputs", {})

        for step_id in step_ids:
            if step_id in agent_outputs:
                step_data = agent_outputs[step_id]
                aggregated["steps"].append({
                    "step_id": step_id,
                    "agent": step_data["agent"],
                    "command": step_data["command"],
                    "valid": step_data["valid"],
                })
                aggregated["outputs"][step_id] = step_data["output"]
                if not step_data["valid"]:
                    aggregated["errors"].extend(step_data["errors"])

        return aggregated
