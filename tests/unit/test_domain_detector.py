"""
Tests for Domain/Stack Detector.
"""

import json
import tempfile
from pathlib import Path

import pytest

from tapps_agents.experts.domain_detector import DomainStackDetector, RepoSignal, StackDetectionResult


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


def test_domain_detector_initialization(temp_project):
    """Test Domain Stack Detector initialization."""
    detector = DomainStackDetector(project_root=temp_project)
    assert detector.project_root == temp_project


def test_detect_python_project(temp_project):
    """Test detection of Python project."""
    # Create Python project files
    (temp_project / "requirements.txt").write_text("django==4.2.0\npytest==7.0.0\n")
    (temp_project / "main.py").write_text("# Python code")

    detector = DomainStackDetector(project_root=temp_project)
    result = detector.detect()

    assert result is not None
    assert result.primary_language == "python"
    assert len(result.detected_domains) > 0
    # Should detect testing domain from pytest
    testing_domains = [d.domain for d in result.detected_domains if "testing" in d.domain]
    assert len(testing_domains) > 0


def test_detect_nodejs_project(temp_project):
    """Test detection of Node.js/TypeScript project."""
    # Create package.json
    package_json = {
        "name": "test-project",
        "dependencies": {
            "react": "^18.0.0",
            "jest": "^29.0.0",
        },
    }
    (temp_project / "package.json").write_text(json.dumps(package_json))
    (temp_project / "src" / "index.tsx").parent.mkdir(parents=True)
    (temp_project / "src" / "index.tsx").write_text("// TypeScript code")

    detector = DomainStackDetector(project_root=temp_project)
    result = detector.detect()

    assert result is not None
    assert result.primary_language == "typescript"
    # Should detect user-experience domain from React
    ux_domains = [d.domain for d in result.detected_domains if "user-experience" in d.domain]
    assert len(ux_domains) > 0


def test_detect_docker_project(temp_project):
    """Test detection of Docker/Kubernetes project."""
    (temp_project / "Dockerfile").write_text("FROM python:3.11")
    (temp_project / "k8s").mkdir()
    (temp_project / "k8s" / "deployment.yaml").write_text("apiVersion: v1")

    detector = DomainStackDetector(project_root=temp_project)
    result = detector.detect()

    assert result is not None
    # Should detect cloud-infrastructure domain
    infra_domains = [
        d.domain for d in result.detected_domains if "cloud-infrastructure" in d.domain
    ]
    assert len(infra_domains) > 0


def test_detect_api_project(temp_project):
    """Test detection of API/service project."""
    (temp_project / "api").mkdir()
    (temp_project / "api" / "routes.py").write_text("# API routes")

    detector = DomainStackDetector(project_root=temp_project)
    result = detector.detect()

    assert result is not None
    # Should detect api-design-integration domain
    api_domains = [
        d.domain for d in result.detected_domains if "api-design-integration" in d.domain
    ]
    assert len(api_domains) > 0


def test_detect_ci_workflows(temp_project):
    """Test detection of CI workflows."""
    (temp_project / ".github" / "workflows").mkdir(parents=True)
    (temp_project / ".github" / "workflows" / "ci.yml").write_text("name: CI")

    detector = DomainStackDetector(project_root=temp_project)
    result = detector.detect()

    assert result is not None
    assert "github-actions" in result.ci_tools


def test_map_signal_to_domains(temp_project):
    """Test signal to domain mapping."""
    detector = DomainStackDetector(project_root=temp_project)

    # Test React dependency
    react_signal = RepoSignal(
        signal_type="dependency",
        source="package.json",
        value="react",
        confidence=1.0,
    )
    domains = detector._map_signal_to_domains(react_signal)
    assert "user-experience" in domains
    assert "testing" in domains

    # Test Django dependency
    django_signal = RepoSignal(
        signal_type="dependency",
        source="requirements.txt",
        value="django",
        confidence=1.0,
    )
    domains = detector._map_signal_to_domains(django_signal)
    assert "api-design-integration" in domains
    assert "database-data-management" in domains


def test_extract_primary_language(temp_project):
    """Test primary language extraction."""
    detector = DomainStackDetector(project_root=temp_project)

    signals = [
        RepoSignal(signal_type="file_structure", source="*.py", value="python", confidence=1.0),
        RepoSignal(signal_type="file_structure", source="*.ts", value="typescript", confidence=1.0),
        RepoSignal(signal_type="file_structure", source="*.py", value="python", confidence=1.0),
    ]

    primary_language = detector._extract_primary_language(signals)
    assert primary_language == "python"


def test_detect_empty_project(temp_project):
    """Test detection on empty project."""
    detector = DomainStackDetector(project_root=temp_project)
    result = detector.detect()

    assert result is not None
    assert isinstance(result, StackDetectionResult)
    assert len(result.detected_domains) >= 0  # May have some default domains

