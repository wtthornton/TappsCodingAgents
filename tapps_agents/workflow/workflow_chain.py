"""
Workflow Chaining Utilities for TappsCodingAgents.

Provides automatic workflow chains and workflow templates.
"""

from typing import Any


class WorkflowChain:
    """
    Defines automatic workflow chains for common scenarios.
    
    Chains automatically configure workflows with proper agent sequencing
    and output passing.
    """

    # Predefined workflow chains
    ENHANCER_TO_PLANNER = [
        {"agent": "enhancer", "command": "enhance"},
        {"agent": "planner", "command": "plan"},
    ]

    PLANNER_TO_ARCHITECT = [
        {"agent": "planner", "command": "plan"},
        {"agent": "architect", "command": "design-system"},
    ]

    ARCHITECT_TO_DESIGNER = [
        {"agent": "architect", "command": "design-system"},
        {"agent": "designer", "command": "design-api"},
    ]

    DESIGNER_TO_IMPLEMENTER = [
        {"agent": "designer", "command": "design-api"},
        {"agent": "implementer", "command": "implement"},
    ]

    FULL_BUILD_CHAIN = [
        {"agent": "enhancer", "command": "enhance"},
        {"agent": "planner", "command": "plan"},
        {"agent": "architect", "command": "design-system"},
        {"agent": "designer", "command": "design-api"},
        {"agent": "implementer", "command": "implement"},
        {"agent": "reviewer", "command": "review"},
        {"agent": "tester", "command": "test"},
    ]

    @staticmethod
    def create_chain_config(chain_name: str, prompt: str) -> dict[str, Any]:
        """
        Create workflow configuration from chain.
        
        Args:
            chain_name: Name of predefined chain
            prompt: User prompt/description
            
        Returns:
            Workflow configuration dictionary
        """
        chains = {
            "enhancer-to-planner": WorkflowChain.ENHANCER_TO_PLANNER,
            "planner-to-architect": WorkflowChain.PLANNER_TO_ARCHITECT,
            "architect-to-designer": WorkflowChain.ARCHITECT_TO_DESIGNER,
            "designer-to-implementer": WorkflowChain.DESIGNER_TO_IMPLEMENTER,
            "full-build": WorkflowChain.FULL_BUILD_CHAIN,
        }

        chain = chains.get(chain_name.lower())
        if not chain:
            raise ValueError(f"Unknown chain: {chain_name}")

        # Create workflow steps from chain
        steps = []
        for i, link in enumerate(chain):
            step_id = f"step-{i+1}"
            next_id = f"step-{i+2}" if i < len(chain) - 1 else None

            step = {
                "id": step_id,
                "agent": link["agent"],
                "action": link["command"],
                "next": next_id,
                "requires": [f"step-{i}"] if i > 0 else [],
                "creates": [f"{link['agent']}_output"],
            }
            steps.append(step)

        return {
            "id": f"chain-{chain_name}",
            "name": f"{chain_name.title()} Chain",
            "description": f"Automatic workflow chain: {chain_name}",
            "prompt": prompt,
            "steps": steps,
        }
