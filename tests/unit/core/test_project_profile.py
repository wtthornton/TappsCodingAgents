"""
Unit tests for Project Profile system.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import yaml

from tapps_agents.core.project_profile import (
    ProjectProfile,
    ComplianceRequirement,
    ProjectProfileDetector,
    save_project_profile,
    load_project_profile,
)
from tapps_agents.workflow.detector import ProjectDetector


@pytest.mark.unit
class TestComplianceRequirement:
    """Test ComplianceRequirement dataclass."""
    
    def test_create_compliance_requirement(self):
        """Test creating a compliance requirement."""
        req = ComplianceRequirement(
            name="GDPR",
            confidence=0.9,
            indicators=["gdpr.md", "compliance/gdpr"]
        )
        assert req.name == "GDPR"
        assert req.confidence == 0.9
        assert len(req.indicators) == 2
        assert "gdpr.md" in req.indicators


@pytest.mark.unit
class TestProjectProfile:
    """Test ProjectProfile dataclass."""
    
    def test_create_empty_profile(self):
        """Test creating an empty profile."""
        profile = ProjectProfile()
        assert profile.deployment_type is None
        assert profile.tenancy is None
        assert profile.user_scale is None
        assert profile.compliance_requirements == []
        assert profile.security_level is None
    
    def test_create_profile_with_values(self):
        """Test creating a profile with values."""
        profile = ProjectProfile(
            deployment_type="cloud",
            tenancy="multi",
            user_scale="thousands",
            security_level="high"
        )
        assert profile.deployment_type == "cloud"
        assert profile.tenancy == "multi"
        assert profile.user_scale == "thousands"
        assert profile.security_level == "high"
    
    def test_profile_with_compliance(self):
        """Test profile with compliance requirements."""
        compliance = [
            ComplianceRequirement(name="GDPR", confidence=0.9, indicators=["gdpr.md"]),
            ComplianceRequirement(name="HIPAA", confidence=0.8, indicators=["hipaa.md"])
        ]
        profile = ProjectProfile(compliance_requirements=compliance)
        assert len(profile.compliance_requirements) == 2
        assert profile.compliance_requirements[0].name == "GDPR"
        assert profile.compliance_requirements[1].name == "HIPAA"


@pytest.mark.unit
class TestProjectProfileDetector:
    """Test ProjectProfileDetector."""
    
    def test_detect_empty_project(self):
        """Test detection on empty project."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            detector = ProjectProfileDetector(project_root)
            profile = detector.detect()
            
            # Should detect something (even if minimal)
            assert isinstance(profile, ProjectProfile)
            # Empty project might not detect deployment type
            assert profile.deployment_type in [None, "local"]
    
    def test_detect_cloud_deployment(self):
        """Test detection of cloud deployment."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # Create Docker file
            (project_root / "Dockerfile").write_text("FROM python:3.9")
            # Create docker-compose
            (project_root / "docker-compose.yml").write_text("version: '3'")
            
            detector = ProjectProfileDetector(project_root)
            profile = detector.detect()
            
            assert profile.deployment_type == "cloud"
    
    def test_detect_enterprise_deployment(self):
        """Test detection of enterprise deployment."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # Create Kubernetes files
            (project_root / "k8s").mkdir()
            (project_root / "k8s" / "deployment.yaml").touch()
            # Create Helm chart
            (project_root / "helm").mkdir()
            (project_root / "helm" / "Chart.yaml").touch()
            
            detector = ProjectProfileDetector(project_root)
            profile = detector.detect()
            
            assert profile.deployment_type == "enterprise"
    
    def test_detect_compliance_requirements(self):
        """Test detection of compliance requirements."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # Create GDPR file
            (project_root / "GDPR.md").write_text("GDPR compliance documentation")
            # Create HIPAA directory
            (project_root / "compliance").mkdir()
            (project_root / "compliance" / "HIPAA.md").write_text("HIPAA compliance")
            
            detector = ProjectProfileDetector(project_root)
            profile = detector.detect()
            
            assert len(profile.compliance_requirements) >= 1
            compliance_names = [req.name for req in profile.compliance_requirements]
            assert "GDPR" in compliance_names or "HIPAA" in compliance_names
    
    def test_detect_security_level(self):
        """Test detection of security level."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # Create security files
            (project_root / "security.md").write_text("Security documentation")
            (project_root / ".security").mkdir()
            (project_root / ".security" / "policies.md").touch()
            
            detector = ProjectProfileDetector(project_root)
            profile = detector.detect()
            
            assert profile.security_level in ["medium", "high"]
    
    def test_detect_local_deployment(self):
        """Test detection of local deployment (no cloud indicators)."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # Create simple Python project
            (project_root / "main.py").write_text("print('hello')")
            (project_root / "requirements.txt").write_text("requests==2.28.0")
            
            detector = ProjectProfileDetector(project_root)
            profile = detector.detect()
            
            # Should detect as local (or None if no indicators)
            assert profile.deployment_type in [None, "local"]


@pytest.mark.unit
class TestProjectProfileStorage:
    """Test project profile save/load functions."""
    
    def test_save_and_load_profile(self):
        """Test saving and loading a profile."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_dir = project_root / ".tapps-agents"
            config_dir.mkdir()
            
            # Create a profile
            profile = ProjectProfile(
                deployment_type="cloud",
                tenancy="multi",
                user_scale="thousands",
                security_level="high",
                compliance_requirements=[
                    ComplianceRequirement(
                        name="GDPR",
                        confidence=0.9,
                        indicators=["gdpr.md"]
                    )
                ]
            )
            
            # Save profile
            save_project_profile(profile, project_root)
            profile_path = config_dir / "project_profile.yaml"
            assert profile_path.exists()
            
            # Load profile
            loaded_profile = load_project_profile(project_root)
            assert loaded_profile is not None
            assert loaded_profile.deployment_type == "cloud"
            assert loaded_profile.tenancy == "multi"
            assert loaded_profile.user_scale == "thousands"
            assert loaded_profile.security_level == "high"
            assert len(loaded_profile.compliance_requirements) == 1
            assert loaded_profile.compliance_requirements[0].name == "GDPR"
    
    def test_load_nonexistent_profile(self):
        """Test loading a profile that doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            loaded_profile = load_project_profile(project_root)
            assert loaded_profile is None
    
    def test_save_profile_creates_config_dir(self):
        """Test that saving creates .tapps-agents directory if needed."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # Don't create .tapps-agents directory
            
            profile = ProjectProfile(deployment_type="cloud")
            save_project_profile(profile, project_root)
            
            config_dir = project_root / ".tapps-agents"
            assert config_dir.exists()
            assert (config_dir / "project_profile.yaml").exists()
    
    def test_profile_serialization(self):
        """Test that profile can be serialized to YAML and back."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_dir = project_root / ".tapps-agents"
            config_dir.mkdir()
            
            # Create profile with all fields
            original_profile = ProjectProfile(
                deployment_type="enterprise",
                tenancy="multi",
                user_scale="thousands",
                security_level="high",
                compliance_requirements=[
                    ComplianceRequirement(name="SOC2", confidence=0.95, indicators=["soc2.md"]),
                    ComplianceRequirement(name="ISO27001", confidence=0.85, indicators=["iso.md"])
                ]
            )
            
            # Save and load
            save_project_profile(original_profile, project_root)
            loaded_profile = load_project_profile(project_root)
            
            # Verify all fields
            assert loaded_profile.deployment_type == original_profile.deployment_type
            assert loaded_profile.tenancy == original_profile.tenancy
            assert loaded_profile.user_scale == original_profile.user_scale
            assert loaded_profile.security_level == original_profile.security_level
            assert len(loaded_profile.compliance_requirements) == 2
            assert loaded_profile.compliance_requirements[0].name == "SOC2"
            assert loaded_profile.compliance_requirements[1].name == "ISO27001"

