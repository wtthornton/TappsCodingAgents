"""
Tests for pluggable gates.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.quality.gates.approval_gate import ApprovalGate
from tapps_agents.quality.gates.base import BaseGate, GateResult, GateSeverity
from tapps_agents.quality.gates.policy_gate import PolicyGate
from tapps_agents.quality.gates.registry import GateRegistry
from tapps_agents.quality.gates.security_gate import SecurityGate
from tapps_agents.workflow.models import WorkflowState


def test_base_gate_interface():
    """Test base gate interface."""
    class TestGate(BaseGate):
        def evaluate(self, context):
            return GateResult(
                passed=True,
                severity=GateSeverity.INFO,
                message="Test passed",
            )
    
    gate = TestGate()
    result = gate.evaluate({})
    assert result.passed is True
    assert result.severity == GateSeverity.INFO


def test_security_gate():
    """Test security gate."""
    gate = SecurityGate()
    
    # Test with clean content
    result = gate.evaluate({"content": "def hello(): pass"})
    assert result.passed is True
    
    # Test with secret
    result = gate.evaluate({"content": "api_key = 'sk-1234567890abcdef'"})
    assert result.passed is False
    assert result.severity == GateSeverity.CRITICAL


def test_policy_gate():
    """Test policy gate."""
    gate = PolicyGate(config={"enabled_policies": []})
    
    result = gate.evaluate({"workflow_id": "test"})
    assert result.passed is True


def test_approval_gate_auto_approve():
    """Test approval gate with auto-approve."""
    gate = ApprovalGate(config={"auto_approve": True})
    
    result = gate.evaluate({
        "workflow_id": "test",
        "step_id": "step1",
    })
    assert result.passed is True
    assert "Auto-approved" in result.message


def test_approval_gate_pending(tmp_path):
    """Test approval gate with pending approval."""
    gate = ApprovalGate(config={
        "approval_dir": str(tmp_path / "approvals"),
        "auto_approve": False,
        "async_mode": False,
    })
    
    result = gate.evaluate({
        "workflow_id": "test",
        "step_id": "step1",
    })
    assert result.passed is False
    assert "Pending approval" in result.message


def test_gate_registry():
    """Test gate registry."""
    registry = GateRegistry()
    
    # Check built-in gates
    assert registry.get("security") is not None
    assert registry.get("policy") is not None
    assert registry.get("approval") is not None
    
    # Test getting non-existent gate
    assert registry.get("nonexistent") is None


def test_gate_registry_evaluate_gates():
    """Test evaluating multiple gates."""
    registry = GateRegistry()
    
    context = {
        "workflow_id": "test",
        "step_id": "step1",
        "content": "def hello(): pass",
    }
    
    results = registry.evaluate_gates(["security", "policy"], context)
    
    assert "all_passed" in results
    assert "gate_results" in results
    assert "security" in results["gate_results"]
    assert "policy" in results["gate_results"]


def test_gate_registry_custom_gates(tmp_path):
    """Test loading custom gates."""
    gates_dir = tmp_path / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a custom gate file
    custom_gate = gates_dir / "custom_gate.py"
    custom_gate.write_text("""
from tapps_agents.quality.gates.base import BaseGate, GateResult, GateSeverity

class CustomGate(BaseGate):
    def evaluate(self, context):
        return GateResult(
            passed=True,
            severity=GateSeverity.INFO,
            message="Custom gate passed",
        )
""")
    
    registry = GateRegistry()
    registry.load_custom_gates(gates_dir)
    
    # Custom gate should be loaded (though we can't easily test it without importing)
    # This test mainly verifies the loading doesn't crash


def test_security_gate_missing_context():
    """Test security gate with missing context."""
    gate = SecurityGate()
    
    # Test with None context
    result = gate.evaluate(None)  # type: ignore
    assert result.passed is False
    assert result.severity.value == "error"
    
    # Test with empty context
    result = gate.evaluate({})
    # Should pass (no content to check)
    assert result.passed is True


def test_security_gate_invalid_file_path():
    """Test security gate with invalid file path."""
    gate = SecurityGate()
    
    result = gate.evaluate({
        "file_path": "/nonexistent/path/to/file.py",
        "content": "def hello(): pass",
    })
    
    # Should handle invalid path gracefully
    assert isinstance(result, GateResult)


def test_security_gate_scan_error(tmp_path):
    """Test security gate when secret scanner raises exception."""
    gate = SecurityGate()
    
    # Mock secret scanner to raise exception
    with patch.object(gate.secret_scanner, "scan_file", side_effect=Exception("Scanner error")):
        result = gate.evaluate({
            "file_path": str(tmp_path / "test.py"),
            "content": "def hello(): pass",
        })
        
        # Should handle error gracefully
        assert isinstance(result, GateResult)
        assert result.passed is True  # Should pass if scanner fails


def test_policy_gate_missing_policy_file(tmp_path):
    """Test policy gate when policy file is missing."""
    gate = PolicyGate(config={
        "policy_dir": str(tmp_path / "policies"),
        "enabled_policies": ["nonexistent-policy"],
    })
    
    result = gate.evaluate({"workflow_id": "test"})
    
    # Should handle missing policy gracefully
    assert isinstance(result, GateResult)
    # Policy check should pass (file not found is not a violation)


def test_policy_gate_invalid_policy_json(tmp_path):
    """Test policy gate with corrupt policy JSON."""
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir(parents=True, exist_ok=True)
    
    # Create invalid JSON file
    policy_file = policy_dir / "invalid-policy.json"
    policy_file.write_text("invalid json content")
    
    gate = PolicyGate(config={
        "policy_dir": str(policy_dir),
        "enabled_policies": ["invalid-policy"],
    })
    
    result = gate.evaluate({"workflow_id": "test"})
    
    # Should handle invalid JSON gracefully
    assert isinstance(result, GateResult)
    # Should not crash, may pass or fail depending on implementation


def test_approval_gate_missing_workflow_id(tmp_path):
    """Test approval gate with missing workflow_id."""
    gate = ApprovalGate(config={
        "approval_dir": str(tmp_path / "approvals"),
    })
    
    result = gate.evaluate({
        "step_id": "step1",
        # Missing workflow_id
    })
    
    assert result.passed is False
    assert "workflow_id" in result.message.lower() or "missing" in result.message.lower()


def test_approval_gate_corrupt_approval_file(tmp_path):
    """Test approval gate with corrupt approval file."""
    approval_dir = tmp_path / "approvals"
    approval_dir.mkdir(parents=True, exist_ok=True)
    
    # Create corrupt JSON file
    corrupt_file = approval_dir / "corrupt-approval.json"
    corrupt_file.write_text("invalid json")
    
    gate = ApprovalGate(config={
        "approval_dir": str(approval_dir),
    })
    
    result = gate.evaluate({
        "workflow_id": "test",
        "step_id": "step1",
    })
    
    # Should handle corrupt file gracefully
    assert isinstance(result, GateResult)


def test_gate_registry_nonexistent_gate():
    """Test gate registry with nonexistent gate."""
    registry = GateRegistry()
    
    result = registry.get("nonexistent_gate")
    assert result is None


def test_gate_registry_evaluation_error():
    """Test gate registry when gate evaluation raises exception."""
    registry = GateRegistry()
    
    # Create a gate that raises exception
    class FailingGate(BaseGate):
        def evaluate(self, context):
            raise Exception("Evaluation error")
    
    registry.register("failing", FailingGate())
    
    results = registry.evaluate_gates(["failing"], {"workflow_id": "test", "step_id": "step1"})
    
    assert results["all_passed"] is False
    assert "failing" in results["gate_results"]
    assert "error" in results["gate_results"]["failing"]


def test_gate_integration_invalid_step():
    """Test gate integration with invalid step configuration."""
    from tapps_agents.workflow.gate_integration import GateIntegration
    from tapps_agents.workflow.models import WorkflowStep, WorkflowState
    
    integration = GateIntegration()
    
    # Test with None step
    result = integration.evaluate_step_gates(None, WorkflowState(workflow_id="test", status="running"), {})  # type: ignore
    assert result["all_passed"] is False
    
    # Test with invalid gate configuration
    step = WorkflowStep(id="step1", agent="test", action="test")
    step.metadata = {"gates": [{"invalid": "config"}]}  # Missing name
    
    state = WorkflowState(workflow_id="test", status="running")
    result = integration.evaluate_step_gates(step, state, {})
    
    # Should handle invalid config gracefully
    assert isinstance(result, dict)
    assert "gate_results" in result
