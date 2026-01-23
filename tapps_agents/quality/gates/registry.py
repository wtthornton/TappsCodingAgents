"""
Gate Registry

Manages registration and discovery of pluggable gates.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Any

from .approval_gate import ApprovalGate
from .base import BaseGate
from .exceptions import GateNotFoundError
from .policy_gate import PolicyGate
from .security_gate import SecurityGate

logger = logging.getLogger(__name__)


class GateRegistry:
    """
    Registry for managing pluggable gates.
    
    Supports:
    - Built-in gates (security, policy, approval)
    - Custom gate plugins
    - Gate configuration loading
    """

    def __init__(self):
        """Initialize gate registry."""
        self._gates: dict[str, BaseGate] = {}
        self._register_builtin_gates()

    def _register_builtin_gates(self) -> None:
        """Register built-in gates."""
        # Security gate
        self.register("security", SecurityGate())
        
        # Policy gate
        self.register("policy", PolicyGate())
        
        # Approval gate
        self.register("approval", ApprovalGate())

    def register(self, name: str, gate: BaseGate) -> None:
        """
        Register a gate.

        Args:
            name: Gate name
            gate: Gate instance
        """
        self._gates[name] = gate
        logger.debug(f"Registered gate: {name}")

    def get(self, name: str) -> BaseGate | None:
        """
        Get a gate by name.

        Args:
            name: Gate name

        Returns:
            Gate instance or None if not found
        """
        return self._gates.get(name)

    def get_all(self) -> dict[str, BaseGate]:
        """
        Get all registered gates.

        Returns:
            Dictionary of gate name -> gate instance
        """
        return self._gates.copy()

    def load_gate(self, name: str, config: dict[str, Any] | None = None) -> BaseGate | None:
        """
        Load a gate by name with optional configuration.

        Args:
            name: Gate name
            config: Optional configuration

        Returns:
            Gate instance or None if not found
        """
        gate = self.get(name)
        if gate and config:
            # Re-instantiate with config
            gate_class = type(gate)
            gate = gate_class(config=config)
            self.register(name, gate)
        return gate

    def load_custom_gates(self, gates_dir: Path | None = None) -> None:
        """
        Load custom gates from directory.

        Args:
            gates_dir: Directory containing custom gate modules (default: .tapps-agents/gates/)
        """
        if gates_dir is None:
            gates_dir = Path(".tapps-agents/gates")
        
        if not gates_dir.exists():
            return
        
        # Look for Python modules in gates directory
        for gate_file in gates_dir.glob("*.py"):
            if gate_file.name.startswith("_") or gate_file.name == "__init__.py":
                continue
            
            try:
                # Import gate module
                module_name = gate_file.stem
                spec = importlib.util.spec_from_file_location(module_name, gate_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for gate class
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseGate)
                            and attr != BaseGate
                        ):
                            gate_instance = attr()
                            gate_name = gate_file.stem
                            self.register(gate_name, gate_instance)
                            logger.info(f"Loaded custom gate: {gate_name}")
            except Exception as e:
                logger.warning(f"Failed to load custom gate from {gate_file}: {e}")

    def evaluate_gates(
        self, gate_names: list[str], context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Evaluate multiple gates.

        Args:
            gate_names: List of gate names to evaluate
            context: Context dictionary

        Returns:
            Dictionary with gate results
        """
        # Validate inputs
        if not gate_names:
            return {
                "all_passed": True,
                "gate_results": {},
                "failures": [],
                "warnings": [],
            }

        if not context or not isinstance(context, dict):
            return {
                "all_passed": False,
                "gate_results": {},
                "failures": [{
                    "gate": "validation",
                    "message": "Invalid context: context must be a dictionary",
                    "severity": "error",
                }],
                "warnings": [],
            }

        results: dict[str, Any] = {
            "all_passed": True,
            "gate_results": {},
            "failures": [],
            "warnings": [],
        }

        for gate_name in gate_names:
            if not gate_name or not isinstance(gate_name, str):
                logger.warning(f"Invalid gate name: {gate_name}, skipping")
                continue

            gate = self.get(gate_name)
            if not gate:
                logger.warning(f"Gate not found: {gate_name}")
                results["gate_results"][gate_name] = {
                    "error": f"Gate not found: {gate_name}",
                }
                results["all_passed"] = False
                continue

            try:
                result = gate.evaluate(context)
                results["gate_results"][gate_name] = result.to_dict()
                
                if not result.passed:
                    results["all_passed"] = False
                    if result.severity.value in ("error", "critical"):
                        results["failures"].append({
                            "gate": gate_name,
                            "message": result.message,
                            "severity": result.severity.value,
                        })
                    else:
                        results["warnings"].append({
                            "gate": gate_name,
                            "message": result.message,
                            "severity": result.severity.value,
                        })
            except Exception as e:
                logger.error(f"Error evaluating gate {gate_name}: {e}", exc_info=True)
                results["gate_results"][gate_name] = {
                    "error": str(e),
                }
                results["all_passed"] = False
                results["failures"].append({
                    "gate": gate_name,
                    "message": f"Gate evaluation exception: {str(e)}",
                    "severity": "error",
                })

        return results


# Global registry instance
_registry: GateRegistry | None = None


def get_gate_registry() -> GateRegistry:
    """Get or create global gate registry."""
    global _registry
    if _registry is None:
        _registry = GateRegistry()
    return _registry
