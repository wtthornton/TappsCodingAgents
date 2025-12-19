"""
Comprehensive tests for Workflow Detector.

Tests project type detection, deployment type, compliance, security, tenancy,
user scale, and workflow recommendations.
"""

import pytest

from tapps_agents.workflow.detector import (
    ProjectDetector,
    ProjectType,
    WorkflowTrack,
)

pytestmark = pytest.mark.unit


class TestProjectDetector:
    """Tests for ProjectDetector."""

    def test_detector_init(self, tmp_path):
        """Test ProjectDetector initialization."""
        detector = ProjectDetector(tmp_path)
        assert detector.project_root == tmp_path

    def test_detect_python_project(self, tmp_path):
        """Test detecting Python project structure."""
        # Create Python project structure with package files and src directory
        # Add enough brownfield indicators to ensure BROWNFIELD detection
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")
        (tmp_path / "requirements.txt").write_text("requests\n")
        (tmp_path / "src").mkdir(parents=True)
        (tmp_path / "src" / "main.py").write_text("print('hello')\n")
        # Add .git to ensure brownfield detection (has_git_history indicator)
        (tmp_path / ".git").mkdir()
        # Add tests directory (has_tests indicator)
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("def test_something(): pass\n")
        # Add more files to avoid minimal_files indicator
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text(f"content {i}\n")
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        assert characteristics is not None, "Detector should return characteristics"
        # Python project with setup.py, requirements.txt, src/, .git, tests/, and multiple files
        # should be detected as BROWNFIELD (brownfield_score >= 0.45)
        assert characteristics.project_type == ProjectType.BROWNFIELD, \
            f"Python project with package files, src/, .git, tests/, and multiple files should be BROWNFIELD, " \
            f"got {characteristics.project_type}. Indicators: {characteristics.indicators}"
        assert characteristics.workflow_track is not None, \
            "Workflow track should be set"
        assert characteristics.confidence > 0.0, \
            f"Confidence should be positive, got {characteristics.confidence}"

    def test_detect_javascript_project(self, tmp_path):
        """Test detecting JavaScript project structure."""
        # Create JavaScript project structure with package.json and src directory
        # Add enough brownfield indicators to ensure BROWNFIELD detection
        (tmp_path / "package.json").write_text('{"name": "test", "version": "1.0.0"}\n')
        (tmp_path / "src").mkdir(parents=True)
        (tmp_path / "src" / "index.js").write_text("console.log('hello');\n")
        # Add .git to ensure brownfield detection (has_git_history indicator)
        (tmp_path / ".git").mkdir()
        # Add tests directory (has_tests indicator)
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_index.js").write_text("test('something', () => {});\n")
        # Add more files to avoid minimal_files indicator
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text(f"content {i}\n")
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        assert characteristics is not None, "Detector should return characteristics"
        # JavaScript project with package.json, src/, .git, tests/, and multiple files
        # should be detected as BROWNFIELD (brownfield_score >= 0.45)
        assert characteristics.project_type == ProjectType.BROWNFIELD, \
            f"JavaScript project with package.json, src/, .git, tests/, and multiple files should be BROWNFIELD, " \
            f"got {characteristics.project_type}. Indicators: {characteristics.indicators}"
        assert characteristics.workflow_track is not None, \
            "Workflow track should be set"
        assert characteristics.confidence > 0.0, \
            f"Confidence should be positive, got {characteristics.confidence}"

    def test_detect_empty_directory(self, tmp_path):
        """Test detecting empty directory."""
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        assert characteristics is not None, "Detector should return characteristics even for empty directory"
        # Empty directory should be detected as GREENFIELD
        # (no src, no package files, no git, minimal files = greenfield indicators)
        assert characteristics.project_type == ProjectType.GREENFIELD, \
            f"Empty directory should be detected as GREENFIELD, got {characteristics.project_type}"
        assert characteristics.workflow_track is not None, \
            "Workflow track should be set"
        assert characteristics.confidence > 0.0, \
            f"Confidence should be positive, got {characteristics.confidence}"

    def test_detect_mixed_project(self, tmp_path):
        """Test detecting project with multiple languages."""
        # Create mixed project
        (tmp_path / "package.json").write_text('{"name": "test"}\n')
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")
        (tmp_path / "src").mkdir(parents=True)
        (tmp_path / "src" / "main.py").write_text("print('hello')\n")
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        assert characteristics is not None
        # Should detect one or both languages

    def test_detect_has_tests(self, tmp_path):
        """Test detecting test directories."""
        # Create project with tests
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("def test_something():\n    pass\n")
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        assert characteristics is not None
        # May have test-related flags

    def test_detect_has_docs(self, tmp_path):
        """Test detecting documentation."""
        # Create project with docs
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "README.md").write_text("# Documentation\n")
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        assert characteristics is not None

    def test_detect_greenfield_project(self, tmp_path):
        """Test detecting greenfield project."""
        # Minimal project - no src, no package files, no git, few files
        (tmp_path / "file1.txt").write_text("content")
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        assert characteristics.project_type == ProjectType.GREENFIELD
        assert characteristics.workflow_track == WorkflowTrack.BMAD_METHOD

    def test_detect_brownfield_project(self, tmp_path):
        """Test detecting brownfield project."""
        # Full project structure
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "src").mkdir()
        (tmp_path / ".git").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "README.md").write_text("# Project")
        for i in range(10):
            (tmp_path / f"file{i}.txt").write_text("content")
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        assert characteristics.project_type == ProjectType.BROWNFIELD
        assert characteristics.confidence > 0.0

    def test_detect_with_compliance_indicators(self, tmp_path):
        """Test detecting project with compliance indicators."""
        (tmp_path / "compliance").mkdir()
        (tmp_path / "compliance" / "SOC2.md").write_text("# SOC2")
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "src").mkdir()
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        # Should upgrade to Enterprise track
        assert characteristics.workflow_track == WorkflowTrack.ENTERPRISE
        assert "has_compliance" in characteristics.indicators

    def test_detect_from_context_quick_fix(self, tmp_path):
        """Test detecting quick-fix from user context."""
        detector = ProjectDetector(tmp_path)
        
        characteristics = detector.detect_from_context(
            user_query="fix bug in login",
            file_count=2,
            scope_description="bug fix"
        )
        
        assert characteristics.project_type == ProjectType.QUICK_FIX
        assert characteristics.workflow_track == WorkflowTrack.QUICK_FLOW
        assert characteristics.confidence >= 0.6

    def test_detect_from_context_small_scope(self, tmp_path):
        """Test detecting quick-fix from small scope."""
        detector = ProjectDetector(tmp_path)
        
        characteristics = detector.detect_from_context(
            user_query="update config",
            file_count=1,
        )
        
        assert characteristics.project_type == ProjectType.QUICK_FIX
        assert characteristics.workflow_track == WorkflowTrack.QUICK_FLOW

    def test_detect_from_context_large_scope(self, tmp_path):
        """Test detecting standard workflow for large scope."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "src").mkdir()
        
        detector = ProjectDetector(tmp_path)
        
        characteristics = detector.detect_from_context(
            user_query="implement new feature",
            file_count=20,
        )
        
        # Should use standard detection, not quick-fix
        assert characteristics.project_type != ProjectType.QUICK_FIX

    def test_get_recommended_workflow_quick_flow(self, tmp_path):
        """Test getting recommended workflow for quick flow."""
        detector = ProjectDetector(tmp_path)
        
        characteristics = detector.detect_from_context(
            user_query="fix bug",
            file_count=1,
        )
        
        workflow = detector.get_recommended_workflow(characteristics)
        assert workflow == "quick-fix"

    def test_get_recommended_workflow_enterprise(self, tmp_path):
        """Test getting recommended workflow for enterprise."""
        (tmp_path / "compliance").mkdir()
        (tmp_path / "k8s").mkdir()
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        workflow = detector.get_recommended_workflow(characteristics)
        assert workflow == "enterprise-development"

    def test_get_recommended_workflow_greenfield(self, tmp_path):
        """Test getting recommended workflow for greenfield."""
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        if characteristics.project_type == ProjectType.GREENFIELD:
            workflow = detector.get_recommended_workflow(characteristics)
            assert workflow == "greenfield-development"

    def test_get_recommended_workflow_brownfield(self, tmp_path):
        """Test getting recommended workflow for brownfield."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "src").mkdir()
        (tmp_path / ".git").mkdir()
        (tmp_path / "tests").mkdir()
        for i in range(10):
            (tmp_path / f"file{i}.txt").write_text("content")
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        if characteristics.project_type == ProjectType.BROWNFIELD:
            workflow = detector.get_recommended_workflow(characteristics)
            assert workflow == "brownfield-development"


class TestProjectDetectorDeploymentType:
    """Tests for detect_deployment_type method."""

    def test_detect_deployment_type_enterprise(self, tmp_path):
        """Test detecting enterprise deployment."""
        (tmp_path / "k8s").mkdir()
        (tmp_path / "compliance").mkdir()
        
        detector = ProjectDetector(tmp_path)
        deployment_type, confidence, indicators = detector.detect_deployment_type()
        
        assert deployment_type == "enterprise"
        assert confidence >= 0.5
        assert "has_kubernetes" in indicators or "has_compliance" in indicators

    def test_detect_deployment_type_cloud(self, tmp_path):
        """Test detecting cloud deployment."""
        (tmp_path / "Dockerfile").write_text("FROM python:3.9")
        (tmp_path / "docker-compose.yml").write_text("version: '3'")
        (tmp_path / "terraform").mkdir()
        
        detector = ProjectDetector(tmp_path)
        deployment_type, confidence, indicators = detector.detect_deployment_type()
        
        assert deployment_type == "cloud"
        assert confidence >= 0.3
        assert "has_dockerfile" in indicators or "has_terraform" in indicators

    def test_detect_deployment_type_local(self, tmp_path):
        """Test detecting local deployment."""
        detector = ProjectDetector(tmp_path)
        deployment_type, confidence, indicators = detector.detect_deployment_type()
        
        assert deployment_type == "local"
        assert confidence > 0.0
        assert "no_cloud_infrastructure" in indicators

    def test_detect_deployment_type_helm(self, tmp_path):
        """Test detecting enterprise with Helm."""
        (tmp_path / "Chart.yaml").write_text("name: app")
        (tmp_path / "values.yaml").write_text("replicas: 1")
        
        detector = ProjectDetector(tmp_path)
        deployment_type, confidence, indicators = detector.detect_deployment_type()
        
        assert "has_helm" in indicators


class TestProjectDetectorCompliance:
    """Tests for detect_compliance_requirements method."""

    def test_detect_compliance_gdpr(self, tmp_path):
        """Test detecting GDPR compliance."""
        (tmp_path / "gdpr").mkdir()
        
        detector = ProjectDetector(tmp_path)
        requirements = detector.detect_compliance_requirements()
        
        gdpr_reqs = [r for r in requirements if r[0] == "GDPR"]
        assert len(gdpr_reqs) > 0
        assert gdpr_reqs[0][1] > 0.0  # confidence > 0

    def test_detect_compliance_hipaa(self, tmp_path):
        """Test detecting HIPAA compliance."""
        (tmp_path / "HIPAA.md").write_text("# HIPAA")
        
        detector = ProjectDetector(tmp_path)
        requirements = detector.detect_compliance_requirements()
        
        hipaa_reqs = [r for r in requirements if r[0] == "HIPAA"]
        assert len(hipaa_reqs) > 0

    def test_detect_compliance_soc2(self, tmp_path):
        """Test detecting SOC2 compliance."""
        (tmp_path / "compliance").mkdir()
        (tmp_path / "compliance" / "soc2.md").write_text("# SOC2")
        
        detector = ProjectDetector(tmp_path)
        requirements = detector.detect_compliance_requirements()
        
        soc2_reqs = [r for r in requirements if r[0] == "SOC2"]
        assert len(soc2_reqs) > 0

    def test_detect_compliance_multiple(self, tmp_path):
        """Test detecting multiple compliance requirements."""
        (tmp_path / "GDPR.md").write_text("# GDPR")
        (tmp_path / "HIPAA.md").write_text("# HIPAA")
        (tmp_path / "compliance").mkdir()
        (tmp_path / "compliance" / "pci.md").write_text("# PCI")
        
        detector = ProjectDetector(tmp_path)
        requirements = detector.detect_compliance_requirements()
        
        assert len(requirements) >= 2


class TestProjectDetectorSecurity:
    """Tests for detect_security_level method."""

    def test_detect_security_level_high(self, tmp_path):
        """Test detecting high security level."""
        (tmp_path / ".security").mkdir()
        (tmp_path / "security.md").write_text("# Security")
        (tmp_path / ".bandit").write_text("config")
        (tmp_path / ".safety").write_text("config")
        
        detector = ProjectDetector(tmp_path)
        level, confidence, indicators = detector.detect_security_level()
        
        assert level == "high"
        assert confidence >= 0.8
        assert len(indicators) >= 3

    def test_detect_security_level_standard(self, tmp_path):
        """Test detecting standard security level."""
        (tmp_path / "security.md").write_text("# Security")
        (tmp_path / ".bandit").write_text("config")
        
        detector = ProjectDetector(tmp_path)
        level, confidence, indicators = detector.detect_security_level()
        
        assert level == "standard"
        assert confidence >= 0.6

    def test_detect_security_level_basic(self, tmp_path):
        """Test detecting basic security level."""
        detector = ProjectDetector(tmp_path)
        level, confidence, indicators = detector.detect_security_level()
        
        assert level == "basic"
        assert confidence == 0.5
        assert "no_security_files" in indicators


class TestProjectDetectorTenancy:
    """Tests for detect_tenancy method."""

    def test_detect_tenancy_multi_tenant(self, tmp_path):
        """Test detecting multi-tenant architecture."""
        (tmp_path / "src").mkdir()
        code_file = tmp_path / "src" / "main.py"
        code_file.write_text("tenant_id = '123'\nmulti_tenant = True\n")
        
        detector = ProjectDetector(tmp_path)
        tenancy, confidence, indicators = detector.detect_tenancy()
        
        assert tenancy == "multi-tenant"
        assert confidence >= 0.6
        assert len(indicators) > 0

    def test_detect_tenancy_single_tenant(self, tmp_path):
        """Test detecting single-tenant architecture."""
        (tmp_path / "src").mkdir()
        code_file = tmp_path / "src" / "main.py"
        code_file.write_text("def hello():\n    print('hello')\n")
        
        detector = ProjectDetector(tmp_path)
        tenancy, confidence, indicators = detector.detect_tenancy()
        
        assert tenancy == "single-tenant"
        assert confidence >= 0.7
        assert "no_tenant_patterns_found" in indicators

    def test_detect_tenancy_skips_large_files(self, tmp_path):
        """Test that large files are skipped in tenancy detection."""
        (tmp_path / "src").mkdir()
        # Create a large file (>1MB)
        large_file = tmp_path / "src" / "large.py"
        large_file.write_text("x" * 1_100_000)  # >1MB
        
        detector = ProjectDetector(tmp_path)
        tenancy, confidence, indicators = detector.detect_tenancy()
        
        # Should still work, just skip large file
        assert tenancy is not None


class TestProjectDetectorUserScale:
    """Tests for detect_user_scale method."""

    def test_detect_user_scale_enterprise(self, tmp_path):
        """Test detecting enterprise user scale."""
        (tmp_path / "k8s").mkdir()
        (tmp_path / "nginx.conf").write_text("upstream backend {}")
        (tmp_path / "oauth").mkdir()
        
        detector = ProjectDetector(tmp_path)
        scale, confidence, indicators = detector.detect_user_scale()
        
        assert scale == "enterprise"
        assert confidence >= 0.6

    def test_detect_user_scale_department(self, tmp_path):
        """Test detecting department user scale."""
        (tmp_path / "redis.conf").write_text("port 6379")
        (tmp_path / "rabbitmq").mkdir()
        
        detector = ProjectDetector(tmp_path)
        scale, confidence, indicators = detector.detect_user_scale()
        
        assert scale == "department"
        assert confidence >= 0.3

    def test_detect_user_scale_small_team(self, tmp_path):
        """Test detecting small-team user scale."""
        (tmp_path / "Dockerfile").write_text("FROM python:3.9")
        (tmp_path / "postgres").mkdir()
        
        detector = ProjectDetector(tmp_path)
        scale, confidence, indicators = detector.detect_user_scale()
        
        assert scale == "small-team"
        assert confidence >= 0.3

    def test_detect_user_scale_default(self, tmp_path):
        """Test default user scale detection."""
        detector = ProjectDetector(tmp_path)
        scale, confidence, indicators = detector.detect_user_scale()
        
        assert scale == "small-team"
        assert confidence == 0.5
        assert "default_small_team" in indicators


class TestProjectDetectorHelpers:
    """Tests for helper methods."""

    def test_has_package_files(self, tmp_path):
        """Test _has_package_files helper."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        
        detector = ProjectDetector(tmp_path)
        assert detector._has_package_files(tmp_path) is True

    def test_has_package_files_pyproject(self, tmp_path):
        """Test _has_package_files with pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        
        detector = ProjectDetector(tmp_path)
        assert detector._has_package_files(tmp_path) is True

    def test_has_compliance_files(self, tmp_path):
        """Test _has_compliance_files helper."""
        (tmp_path / "compliance").mkdir()
        
        detector = ProjectDetector(tmp_path)
        assert detector._has_compliance_files(tmp_path) is True

    def test_has_security_files(self, tmp_path):
        """Test _has_security_files helper."""
        (tmp_path / "security.md").write_text("# Security")
        
        detector = ProjectDetector(tmp_path)
        assert detector._has_security_files(tmp_path) is True

    def test_has_multiple_domains(self, tmp_path):
        """Test _has_multiple_domains helper."""
        (tmp_path / ".tapps-agents").mkdir()
        domains_file = tmp_path / ".tapps-agents" / "domains.md"
        domains_file.write_text("### Domain 1:\n### Domain 2:\n### Domain 3:")
        
        detector = ProjectDetector(tmp_path)
        assert detector._has_multiple_domains(tmp_path) is True

    def test_has_multiple_domains_single(self, tmp_path):
        """Test _has_multiple_domains with single domain."""
        (tmp_path / ".tapps-agents").mkdir()
        domains_file = tmp_path / ".tapps-agents" / "domains.md"
        domains_file.write_text("### Domain 1:")
        
        detector = ProjectDetector(tmp_path)
        assert detector._has_multiple_domains(tmp_path) is False

    def test_is_large_codebase(self, tmp_path):
        """Test _is_large_codebase helper."""
        (tmp_path / "src").mkdir()
        # Create many code files
        for i in range(1100):
            (tmp_path / "src" / f"file{i}.py").write_text("pass\n")
        
        detector = ProjectDetector(tmp_path)
        assert detector._is_large_codebase(tmp_path) is True

    def test_is_large_codebase_small(self, tmp_path):
        """Test _is_large_codebase with small codebase."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("pass\n")
        
        detector = ProjectDetector(tmp_path)
        assert detector._is_large_codebase(tmp_path) is False
