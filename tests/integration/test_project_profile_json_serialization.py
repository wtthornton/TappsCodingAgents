"""
Integration test for ProjectProfile JSON serialization fix.

This test verifies that ProjectProfile and ComplianceRequirement objects
can be properly serialized to JSON when stored in workflow state variables.
This fixes the issue: "Object of type ComplianceRequirement is not JSON serializable"
"""

import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tapps_agents.core.project_profile import (
    ComplianceRequirement,
    ProjectProfile,
)
from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.models import WorkflowState
from tapps_agents.workflow.state_manager import (
    AdvancedStateManager,
    StateValidator,
)

pytestmark = pytest.mark.integration


class TestProjectProfileJsonSerialization:
    """Integration tests for ProjectProfile JSON serialization."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def state_manager(self, temp_dir):
        """Create state manager instance."""
        return AdvancedStateManager(temp_dir / "state", compression=False)

    @pytest.fixture
    def project_profile_with_compliance(self):
        """Create a ProjectProfile with ComplianceRequirement objects."""
        return ProjectProfile(
            deployment_type="cloud",
            deployment_type_confidence=0.9,
            security_level="high",
            security_level_confidence=0.8,
            tenancy="multi-tenant",
            tenancy_confidence=0.85,
            user_scale="enterprise",
            user_scale_confidence=0.9,
            compliance_requirements=[
                ComplianceRequirement(
                    name="GDPR",
                    confidence=0.95,
                    indicators=["gdpr_compliance.md", "data_protection.yaml"],
                ),
                ComplianceRequirement(
                    name="SOC2",
                    confidence=0.88,
                    indicators=["security_audit.md"],
                ),
                ComplianceRequirement(
                    name="HIPAA",
                    confidence=0.75,
                    indicators=["health_data.md"],
                ),
            ],
            detected_at=datetime.now(UTC).isoformat(),
        )

    def test_state_manager_saves_profile_in_variables(
        self, state_manager, project_profile_with_compliance, temp_dir
    ):
        """Test that AdvancedStateManager can save state with ProjectProfile in variables."""
        # Create state with ProjectProfile in variables (as dict via to_dict)
        state = WorkflowState(
            workflow_id="test-workflow-profile",
            started_at=datetime.now(),
            current_step="step1",
            completed_steps=[],
            skipped_steps=[],
            artifacts={},
            variables={
                "user_prompt": "Test prompt",
                "project_profile": project_profile_with_compliance.to_dict(),
            },
            status="running",
        )

        # This should not raise "Object of type ComplianceRequirement is not JSON serializable"
        workflow_path = temp_dir / "workflow.yaml"
        state_path = state_manager.save_state(state, workflow_path)

        assert state_path.exists()
        assert state_path.suffix == ".json"

        # Verify we can load it back
        loaded_state, metadata = state_manager.load_state(
            workflow_id="test-workflow-profile"
        )
        assert loaded_state.workflow_id == "test-workflow-profile"
        assert "project_profile" in loaded_state.variables
        profile_dict = loaded_state.variables["project_profile"]
        assert isinstance(profile_dict, dict)
        assert profile_dict["deployment_type"] == "cloud"
        assert len(profile_dict["compliance_requirements"]) == 3

    def test_state_manager_with_profile_object_in_variables(
        self, state_manager, project_profile_with_compliance, temp_dir
    ):
        """
        Test that AdvancedStateManager handles ProjectProfile object directly in variables.
        
        This tests the fix for when a ProfileProfile object (not dict) gets into variables.
        """
        # Create state with ProjectProfile OBJECT in variables (this should be handled by our fix)
        state = WorkflowState(
            workflow_id="test-workflow-profile-object",
            started_at=datetime.now(),
            current_step="step1",
            completed_steps=[],
            skipped_steps=[],
            artifacts={},
            variables={
                "user_prompt": "Test prompt",
                "project_profile": project_profile_with_compliance,  # Object, not dict
            },
            status="running",
        )

        # This should not raise "Object of type ComplianceRequirement is not JSON serializable"
        # Our fix should convert the ProjectProfile to dict during serialization
        workflow_path = temp_dir / "workflow.yaml"
        state_path = state_manager.save_state(state, workflow_path)

        assert state_path.exists()

        # Verify we can load it back
        loaded_state, metadata = state_manager.load_state(
            workflow_id="test-workflow-profile-object"
        )
        assert loaded_state.workflow_id == "test-workflow-profile-object"
        assert "project_profile" in loaded_state.variables

    def test_checksum_calculation_with_profile(
        self, project_profile_with_compliance
    ):
        """Test that checksum calculation works with ProjectProfile in variables."""
        # Create state data with ProjectProfile as dict
        state_data = {
            "workflow_id": "test-checksum",
            "current_step": "step1",
            "completed_steps": ["step0"],
            "skipped_steps": [],
            "status": "running",
            "variables": {
                "project_profile": project_profile_with_compliance.to_dict(),
            },
        }

        # This should not raise JSON serialization error
        checksum = StateValidator.calculate_checksum(state_data)
        assert len(checksum) == 64  # SHA256 hex digest
        assert isinstance(checksum, str)

        # Same data should produce same checksum
        checksum2 = StateValidator.calculate_checksum(state_data)
        assert checksum == checksum2

    def test_checksum_calculation_with_profile_object(
        self, project_profile_with_compliance
    ):
        """Test that checksum calculation works with ProjectProfile object in variables."""
        # Create state data with ProjectProfile as OBJECT (not dict)
        state_data = {
            "workflow_id": "test-checksum-object",
            "current_step": "step1",
            "completed_steps": ["step0"],
            "skipped_steps": [],
            "status": "running",
            "variables": {
                "project_profile": project_profile_with_compliance,  # Object
            },
        }

        # This should not raise JSON serialization error
        # Our fix should convert it to dict during checksum calculation
        checksum = StateValidator.calculate_checksum(state_data)
        assert len(checksum) == 64
        assert isinstance(checksum, str)

    def test_workflow_executor_state_serialization(
        self, project_profile_with_compliance, temp_dir
    ):
        """Test that WorkflowExecutor can serialize state with ProjectProfile."""
        executor = WorkflowExecutor(
            project_root=temp_dir,
            auto_detect=False,
            advanced_state=True,
            auto_mode=False,
        )

        # Create state with ProjectProfile
        from tapps_agents.workflow.models import WorkflowState

        state = WorkflowState(
            workflow_id="test-executor-profile",
            started_at=datetime.now(),
            current_step="step1",
            completed_steps=[],
            skipped_steps=[],
            artifacts={},
            variables={
                "user_prompt": "Test prompt",
                "project_profile": project_profile_with_compliance.to_dict(),
            },
            status="running",
        )

        executor.state = state

        # This should not raise JSON serialization error
        state_path = executor.save_state()
        assert state_path is not None
        assert state_path.exists()

    def test_nested_compliance_requirements_serialization(
        self, state_manager, temp_dir
    ):
        """Test serialization with nested compliance requirements in profile dict."""
        # Create a complex profile with multiple compliance requirements
        profile_dict = {
            "deployment_type": "enterprise",
            "deployment_type_confidence": 0.95,
            "security_level": "critical",
            "security_level_confidence": 0.98,
            "compliance_requirements": [
                {
                    "name": "GDPR",
                    "confidence": 0.99,
                    "indicators": ["gdpr.md", "privacy_policy.md"],
                },
                {
                    "name": "SOC2",
                    "confidence": 0.97,
                    "indicators": ["security_audit.md"],
                },
                {
                    "name": "PCI-DSS",
                    "confidence": 0.92,
                    "indicators": ["payment_processing.md"],
                },
            ],
        }

        state = WorkflowState(
            workflow_id="test-nested-compliance",
            started_at=datetime.now(),
            current_step="step1",
            completed_steps=[],
            skipped_steps=[],
            artifacts={},
            variables={
                "project_profile": profile_dict,
                "other_data": "test",
            },
            status="running",
        )

        # This should not raise JSON serialization error
        workflow_path = temp_dir / "workflow.yaml"
        state_path = state_manager.save_state(state, workflow_path)
        assert state_path.exists()

        # Verify loading works
        loaded_state, metadata = state_manager.load_state(
            workflow_id="test-nested-compliance"
        )
        assert loaded_state.workflow_id == "test-nested-compliance"
        profile_loaded = loaded_state.variables["project_profile"]
        assert len(profile_loaded["compliance_requirements"]) == 3
        assert profile_loaded["compliance_requirements"][0]["name"] == "GDPR"

    def test_workflow_executor_state_to_dict_with_profile(
        self, project_profile_with_compliance
    ):
        """Test WorkflowExecutor._state_to_dict handles ProjectProfile correctly."""
        executor = WorkflowExecutor(auto_detect=False)

        state = WorkflowState(
            workflow_id="test-to-dict",
            started_at=datetime.now(),
            current_step="step1",
            completed_steps=[],
            skipped_steps=[],
            artifacts={},
            variables={
                "project_profile": project_profile_with_compliance.to_dict(),
            },
            status="running",
        )

        # This should not raise JSON serialization error
        state_dict = executor._state_to_dict(state)

        # Verify structure
        assert "variables" in state_dict
        assert "project_profile" in state_dict["variables"]
        profile_dict = state_dict["variables"]["project_profile"]
        assert isinstance(profile_dict, dict)
        assert "compliance_requirements" in profile_dict
        assert isinstance(profile_dict["compliance_requirements"], list)
        assert len(profile_dict["compliance_requirements"]) == 3

        # Verify it's JSON serializable
        import json

        json_str = json.dumps(state_dict, indent=2)
        assert len(json_str) > 0
        # Verify we can parse it back
        parsed = json.loads(json_str)
        assert parsed["variables"]["project_profile"]["deployment_type"] == "cloud"

