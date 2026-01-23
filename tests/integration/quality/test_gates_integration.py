"""
Integration tests for pluggable gates system.

Tests gate evaluation in real workflow contexts and error handling.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.quality.gates.approval_gate import ApprovalGate
from tapps_agents.quality.gates.base import BaseGate
from tapps_agents.quality.gates.policy_gate import PolicyGate
from tapps_agents.quality.gates.registry import GateRegistry
from tapps_agents.quality.gates.security_gate import SecurityGate
from tapps_agents.workflow.gate_integration import GateIntegration
from tapps_agents.workflow.models import WorkflowStep, WorkflowState


@pytest.fixture
def workflow_context() -> dict:
    """Create a realistic workflow context."""
    return {
        "workflow_id": "test-workflow-123",
        "step_id": "implement-step",
        "agent": "implementer",
        "action": "implement",
        "content": "def hello(): pass",
        "file_path": "src/main.py",
    }


def test_gate_evaluation_in_workflow_context(workflow_context):
    """Test gate evaluation in actual workflow context."""
    registry = GateRegistry()
    
    results = registry.evaluate_gates(["security", "policy"], workflow_context)
    
    assert "all_passed" in results
    assert "gate_results" in results
    assert "security" in results["gate_results"]
    assert "policy" in results["gate_results"]


def test_gate_chaining_all_must_pass(workflow_context):
    """Test that all gates must pass in chained evaluation."""
    registry = GateRegistry()
    
    # Create context with secret (security gate will fail)
    context_with_secret = workflow_context.copy()
    context_with_secret["content"] = "api_key = 'sk-1234567890'"
    
    results = registry.evaluate_gates(["security", "policy"], context_with_secret)
    
    # Security gate should fail
    assert results["all_passed"] is False
    assert len(results["failures"]) > 0


def test_gate_integration_with_workflow_step(workflow_context):
    """Test gate integration with actual workflow step."""
    integration = GateIntegration()
    
    step = WorkflowStep(
        id="test-step",
        agent="implementer",
        action="implement",
    )
    step.metadata = {
        "gates": [
            "security",
            {"name": "policy", "config": {"check_gdpr": False}},
        ]
    }
    
    state = WorkflowState(workflow_id=workflow_context["workflow_id"], status="running")
    
    results = integration.evaluate_step_gates(step, state, workflow_context)
    
    assert "all_passed" in results
    assert "gate_results" in results
    assert len(results["gate_results"]) == 2


def test_gate_error_handling_propagation(workflow_context):
    """Test that gate errors are handled and don't crash workflow."""
    # Create a gate that raises exception
    class FailingGate(SecurityGate):
        def evaluate(self, context):
            raise Exception("Gate evaluation error")
    
    registry = GateRegistry()
    registry.register("failing", FailingGate())
    
    results = registry.evaluate_gates(["failing"], workflow_context)
    
    # Should handle error gracefully
    assert results["all_passed"] is False
    assert "failing" in results["gate_results"]
    assert "error" in results["gate_results"]["failing"]


def test_approval_gate_workflow_integration(tmp_path: Path):
    """Test approval gate in workflow context."""
    gate = ApprovalGate(config={
        "approval_dir": str(tmp_path / "approvals"),
        "auto_approve": False,
    })
    
    context = {
        "workflow_id": "test-workflow",
        "step_id": "deploy-step",
    }
    
    result = gate.evaluate(context)
    
    # Should create approval request
    assert result.passed is False
    assert "Pending approval" in result.message or "request" in result.message.lower()
    
    # Check approval file was created
    approval_files = list((tmp_path / "approvals").glob("*.json"))
    assert len(approval_files) > 0


def test_security_gate_file_scanning_integration(tmp_path: Path):
    """Test security gate with real file scanning."""
    test_file = tmp_path / "test_secret.py"
    test_file.write_text("api_key = 'sk-1234567890abcdef'\npassword = 'secret123'")
    
    gate = SecurityGate()
    
    result = gate.evaluate({
        "file_path": str(test_file),
    })
    
    # Should detect secrets
    assert result.passed is False
    assert result.severity.value in ("error", "critical")


def test_policy_gate_custom_policy_integration(tmp_path: Path):
    """Test policy gate with custom policy file."""
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir(parents=True, exist_ok=True)
    
    # Create custom policy
    policy_file = policy_dir / "custom-policy.json"
    policy_file.write_text(json.dumps({
        "name": "custom-policy",
        "rules": [
            {
                "type": "file_pattern",
                "pattern": "*.secret",
                "allowed": False,
            }
        ]
    }))
    
    gate = PolicyGate(config={
        "policy_dir": str(policy_dir),
        "enabled_policies": ["custom-policy"],
    })
    
    result = gate.evaluate({
        "workflow_id": "test",
        "file_path": "config.secret",
    })
    
    # Should evaluate custom policy
    assert isinstance(result, type(gate.evaluate({})))  # Should return GateResult


def test_gate_registry_multiple_gates_integration(workflow_context):
    """Test evaluating multiple gates together."""
    registry = GateRegistry()
    
    # Evaluate all three built-in gates
    results = registry.evaluate_gates(
        ["security", "policy", "approval"],
        workflow_context
    )
    
    assert len(results["gate_results"]) == 3
    assert "security" in results["gate_results"]
    assert "policy" in results["gate_results"]
    assert "approval" in results["gate_results"]


def test_gate_integration_invalid_step_config():
    """Test gate integration with invalid step configuration."""
    integration = GateIntegration()
    
    step = WorkflowStep(
        id="test-step",
        agent="test",
        action="test",
    )
    step.metadata = {
        "gates": [
            "nonexistent_gate",  # Gate doesn't exist
            {"invalid": "config"},  # Invalid config structure
        ]
    }
    
    state = WorkflowState(workflow_id="test", status="running")
    
    # Should handle gracefully
    results = integration.evaluate_step_gates(step, state, {})
    
    assert isinstance(results, dict)
    assert "gate_results" in results
