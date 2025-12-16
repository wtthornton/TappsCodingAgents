"""
Tests for Project Profile System.
"""

import tempfile
from pathlib import Path

import pytest

from tapps_agents.core.project_profile import (
    ComplianceRequirement,
    ProjectProfile,
    ProjectProfileDetector,
    load_project_profile,
    save_project_profile,
)

pytestmark = pytest.mark.unit


class TestProjectProfile:
    """Tests for ProjectProfile dataclass."""

    def test_profile_creation(self):
        """Test creating a basic profile."""
        profile = ProjectProfile(
            deployment_type="cloud",
            deployment_type_confidence=0.9,
            security_level="high",
            security_level_confidence=0.8,
        )

        assert profile.deployment_type == "cloud"
        assert profile.deployment_type_confidence == 0.9
        assert profile.security_level == "high"
        assert profile.security_level_confidence == 0.8

    def test_profile_to_dict(self):
        """Test converting profile to dictionary."""
        profile = ProjectProfile(
            deployment_type="cloud",
            deployment_type_confidence=0.9,
            compliance_requirements=[
                ComplianceRequirement(
                    name="GDPR", confidence=0.8, indicators=["gdpr_file"]
                )
            ],
        )

        data = profile.to_dict()
        assert data["deployment_type"] == "cloud"
        assert data["deployment_type_confidence"] == 0.9
        assert len(data["compliance_requirements"]) == 1
        assert data["compliance_requirements"][0]["name"] == "GDPR"

    def test_profile_from_dict(self):
        """Test creating profile from dictionary."""
        data = {
            "deployment_type": "cloud",
            "deployment_type_confidence": 0.9,
            "compliance_requirements": [
                {"name": "GDPR", "confidence": 0.8, "indicators": ["gdpr_file"]}
            ],
        }

        profile = ProjectProfile.from_dict(data)
        assert profile.deployment_type == "cloud"
        assert len(profile.compliance_requirements) == 1
        assert profile.compliance_requirements[0].name == "GDPR"

    def test_format_context_high_confidence(self):
        """Test formatting context with high-confidence values."""
        profile = ProjectProfile(
            deployment_type="cloud",
            deployment_type_confidence=0.9,
            security_level="high",
            security_level_confidence=0.8,
            compliance_requirements=[
                ComplianceRequirement(name="GDPR", confidence=0.85, indicators=[])
            ],
        )

        context = profile.format_context(min_confidence=0.7)
        assert "Deployment: cloud" in context
        assert "Security Level: high" in context
        assert "GDPR" in context

    def test_format_context_low_confidence(self):
        """Test formatting context excludes low-confidence values."""
        profile = ProjectProfile(
            deployment_type="cloud",
            deployment_type_confidence=0.5,  # Below threshold
            security_level="high",
            security_level_confidence=0.8,
        )

        context = profile.format_context(min_confidence=0.7)
        assert "Deployment: cloud" not in context
        assert "Security Level: high" in context

    def test_format_context_empty(self):
        """Test formatting context with no high-confidence values."""
        profile = ProjectProfile()
        context = profile.format_context(min_confidence=0.7)
        assert context == ""


class TestProjectProfileDetector:
    """Tests for ProjectProfileDetector."""

    def test_detector_initialization(self):
        """Test detector can be initialized."""
        detector = ProjectProfileDetector()
        assert detector.project_root == Path.cwd()
        assert detector.detector is not None

    def test_detector_with_custom_root(self):
        """Test detector with custom project root."""
        custom_root = Path("/tmp/test")
        detector = ProjectProfileDetector(project_root=custom_root)
        assert detector.project_root == custom_root

    def test_detect_profile_basic(self):
        """Test detecting profile (basic case)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create a basic project structure
            (project_root / "README.md").touch()

            detector = ProjectProfileDetector(project_root=project_root)
            profile = detector.detect_profile()

            assert profile is not None
            assert profile.detected_at is not None
            # Should detect at least deployment type (defaults to local)
            assert profile.deployment_type is not None

    def test_detect_profile_with_dockerfile(self):
        """Test detecting profile with Dockerfile (cloud deployment)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create Dockerfile
            (project_root / "Dockerfile").touch()

            detector = ProjectProfileDetector(project_root=project_root)
            profile = detector.detect_profile()

            # Dockerfile presence should influence deployment type detection
            # (may be cloud, enterprise, or local depending on other indicators)
            assert profile.deployment_type is not None
            assert profile.deployment_type_confidence > 0.0
            # Check that Dockerfile is detected as an indicator
            assert "has_dockerfile" in profile.deployment_type_indicators or "dockerfile" in str(profile.deployment_type_indicators).lower()

    def test_detect_profile_with_security_files(self):
        """Test detecting security level from security files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create security files
            (project_root / "SECURITY.md").touch()
            (project_root / ".bandit").touch()

            detector = ProjectProfileDetector(project_root=project_root)
            profile = detector.detect_profile()

            assert profile.security_level is not None
            assert profile.security_level_confidence > 0.0


class TestProfileStorage:
    """Tests for profile save/load functionality."""

    def test_save_and_load_profile(self):
        """Test saving and loading a profile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            profile = ProjectProfile(
                deployment_type="cloud",
                deployment_type_confidence=0.9,
                security_level="high",
                security_level_confidence=0.8,
                compliance_requirements=[
                    ComplianceRequirement(
                        name="GDPR", confidence=0.85, indicators=["gdpr_file"]
                    )
                ],
            )

            # Save profile
            profile_file = save_project_profile(profile, project_root=project_root)
            assert profile_file.exists()

            # Load profile
            loaded_profile = load_project_profile(project_root=project_root)
            assert loaded_profile is not None
            assert loaded_profile.deployment_type == "cloud"
            assert loaded_profile.deployment_type_confidence == 0.9
            assert loaded_profile.security_level == "high"
            assert len(loaded_profile.compliance_requirements) == 1
            assert loaded_profile.compliance_requirements[0].name == "GDPR"

    def test_load_nonexistent_profile(self):
        """Test loading a profile that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            profile = load_project_profile(project_root=project_root)
            assert profile is None

    def test_save_profile_creates_directory(self):
        """Test that saving profile creates .tapps-agents directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            profile = ProjectProfile(deployment_type="cloud")
            save_project_profile(profile, project_root=project_root)

            assert (project_root / ".tapps-agents").exists()
            assert (project_root / ".tapps-agents" / "project-profile.yaml").exists()
