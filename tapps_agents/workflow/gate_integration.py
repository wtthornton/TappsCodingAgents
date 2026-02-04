"""
Gate Integration

Integrates pluggable gates with workflow engine.
"""

from __future__ import annotations

import logging
from typing import Any

from ..quality.gates.registry import GateRegistry, get_gate_registry
from .models import WorkflowState, WorkflowStep

logger = logging.getLogger(__name__)


class GateIntegration:
    """
    Integrates pluggable gates with workflow execution.
    
    Supports:
    - Multiple gates per step
    - Gate chaining (all must pass)
    - Gate configuration from workflow YAML
    """

    def __init__(self, registry: GateRegistry | None = None):
        """
        Initialize gate integration.

        Args:
            registry: Optional gate registry (uses global registry if not provided)
        """
        self.registry = registry or get_gate_registry()

    def evaluate_step_gates(
        self,
        step: WorkflowStep,
        state: WorkflowState,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate all gates for a workflow step.

        Args:
            step: Workflow step
            state: Workflow state
            context: Additional context

        Returns:
            Gate evaluation results
        """
        # Validate inputs
        if not step:
            logger.warning("Invalid step: step is None")
            return {
                "all_passed": False,
                "gate_results": {},
                "failures": [{"gate": "validation", "message": "Step is None", "severity": "error"}],
                "warnings": [],
            }

        if not state:
            logger.warning("Invalid state: state is None")
            return {
                "all_passed": False,
                "gate_results": {},
                "failures": [{"gate": "validation", "message": "State is None", "severity": "error"}],
                "warnings": [],
            }

        # Build context
        gate_context = {
            "workflow_id": state.workflow_id,
            "step_id": step.id,
            "agent": step.agent,
            "action": step.action,
            **(context or {}),
        }

        # Get gates from step configuration
        gates_config = step.metadata.get("gates", []) if step.metadata else []
        
        # Also check legacy gate configuration
        if step.gate and not gates_config:
            # Convert legacy gate to new format
            gates_config = [{"name": "quality", "config": step.gate}]

        if not gates_config:
            # No gates configured
            return {
                "all_passed": True,
                "gate_results": {},
                "failures": [],
                "warnings": [],
            }

        # Validate and extract gate configurations
        gate_names = []
        gate_configs: dict[str, dict[str, Any]] = {}
        
        for gate_config in gates_config:
            if isinstance(gate_config, str):
                # Simple gate name - validate it exists
                if not gate_config.strip():
                    logger.warning("Empty gate name in configuration, skipping")
                    continue
                if self.registry.get(gate_config):
                    gate_names.append(gate_config)
                else:
                    logger.warning(f"Gate not found: {gate_config}")
            elif isinstance(gate_config, dict):
                # Gate with configuration
                gate_name = gate_config.get("name") or gate_config.get("gate")
                if not gate_name:
                    logger.warning("Invalid gate config: missing name")
                    continue
                
                if not self.registry.get(gate_name):
                    logger.warning(f"Gate not found: {gate_name}")
                    continue
                
                # Validate config structure
                config = gate_config.get("config", {})
                if config and not isinstance(config, dict):
                    logger.warning(f"Invalid gate config for {gate_name}: config must be dict")
                    continue
                
                gate_names.append(gate_name)
                if config:
                    gate_configs[gate_name] = config
            else:
                logger.warning(f"Invalid gate config type: {type(gate_config)}")

        if not gate_names:
            # No valid gates found
            return {
                "all_passed": True,
                "gate_results": {},
                "failures": [],
                "warnings": [],
            }

        # Load gates with configs
        for gate_name in gate_names:
            if gate_name in gate_configs:
                try:
                    self.registry.load_gate(gate_name, gate_configs[gate_name])
                except Exception as e:
                    logger.warning(f"Failed to load gate {gate_name} with config: {e}")

        # Evaluate all gates
        try:
            results = self.registry.evaluate_gates(gate_names, gate_context)
        except Exception as e:
            logger.error(f"Error evaluating gates: {e}", exc_info=True)
            return {
                "all_passed": False,
                "gate_results": {},
                "failures": [{"gate": "evaluation", "message": f"Gate evaluation failed: {str(e)}", "severity": "error"}],
                "warnings": [],
            }

        return results

    def should_block_step(
        self,
        step: WorkflowStep,
        state: WorkflowState,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str | None]:
        """
        Determine if step should be blocked based on gate evaluation.

        Args:
            step: Workflow step
            state: Workflow state
            context: Additional context

        Returns:
            Tuple of (should_block, reason_if_blocked)
        """
        results = self.evaluate_step_gates(step, state, context)

        if not results["all_passed"]:
            # Check if any failures are blocking
            failures = results.get("failures", [])
            if failures:
                # Block on critical/error failures
                blocking_failures = [
                    f for f in failures
                    if f.get("severity") in ("error", "critical")
                ]
                if blocking_failures:
                    reasons = [f["message"] for f in blocking_failures]
                    return True, "; ".join(reasons)

        return False, None
