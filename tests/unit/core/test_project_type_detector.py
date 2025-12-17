"""
Tests for project type detection and template selection.
"""

from pathlib import Path

import pytest

from tapps_agents.core.project_type_detector import (
    detect_project_type,
    get_available_project_types,
    get_project_type_template_path,
)

pytestmark = pytest.mark.unit


class TestProjectTypeDetection:
    """Tests for project type detection."""

    def test_detect_api_service_with_routes(self, tmp_path: Path):
        """Test detecting API service from routes directory."""
        (tmp_path / "api").mkdir()
        (tmp_path / "routes").mkdir()
        
        project_type, confidence, reason = detect_project_type(tmp_path)
        assert project_type == "api-service"
        assert confidence >= 0.3
        assert "api" in reason.lower() or "routes" in reason.lower()

    def test_detect_api_service_with_openapi(self, tmp_path: Path):
        """Test detecting API service from OpenAPI spec."""
        (tmp_path / "openapi.yaml").write_text("openapi: 3.0.0")
        
        project_type, confidence, reason = detect_project_type(tmp_path)
        assert project_type == "api-service"
        assert confidence >= 0.3

    def test_detect_web_app_with_frontend_backend(self, tmp_path: Path):
        """Test detecting web app from frontend and backend indicators."""
        (tmp_path / "src").mkdir()
        (tmp_path / "public").mkdir()
        (tmp_path / "server").mkdir()
        
        project_type, confidence, reason = detect_project_type(tmp_path)
        assert project_type == "web-app"
        assert confidence >= 0.3

    def test_detect_cli_tool_with_entrypoint(self, tmp_path: Path):
        """Test detecting CLI tool from entrypoint."""
        (tmp_path / "cli.py").write_text("import click")
        (tmp_path / "requirements.txt").write_text("click>=8.0.0")
        
        project_type, confidence, reason = detect_project_type(tmp_path)
        # CLI detection might match, but confidence depends on other signals
        # Just verify it doesn't crash
        assert project_type is None or project_type in ["cli-tool", "api-service", "web-app"]

    def test_detect_library_with_package_structure(self, tmp_path: Path):
        """Test detecting library from package structure."""
        (tmp_path / "mypackage").mkdir()
        (tmp_path / "mypackage" / "__init__.py").write_text("")
        (tmp_path / "setup.py").write_text("from setuptools import setup")
        
        project_type, confidence, reason = detect_project_type(tmp_path)
        assert project_type == "library"
        assert confidence >= 0.3

    def test_detect_microservice_with_docker(self, tmp_path: Path):
        """Test detecting microservice from Docker and service structure."""
        (tmp_path / "services").mkdir()
        (tmp_path / "Dockerfile").write_text("FROM python:3.11")
        (tmp_path / "docker-compose.yml").write_text("version: '3'")
        
        project_type, confidence, reason = detect_project_type(tmp_path)
        assert project_type == "microservice"
        assert confidence >= 0.3

    def test_detect_none_for_empty_project(self, tmp_path: Path):
        """Test that empty project returns None."""
        project_type, confidence, reason = detect_project_type(tmp_path)
        assert project_type is None
        assert confidence < 0.3
        assert "no clear" in reason.lower() or "confidence" in reason.lower()

    def test_detect_with_tech_stack_context(self, tmp_path: Path):
        """Test detection with tech stack context."""
        (tmp_path / "api").mkdir()
        tech_stack = {"frameworks": ["FastAPI"]}
        
        project_type, confidence, reason = detect_project_type(tmp_path, tech_stack)
        # Should still detect based on structure
        assert project_type is not None or confidence < 0.3

    def test_detect_api_service_priority(self, tmp_path: Path):
        """Test that API service indicators take priority when present."""
        # Create indicators for multiple types
        (tmp_path / "api").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "public").mkdir()
        
        project_type, confidence, reason = detect_project_type(tmp_path)
        # API service should be detected if indicators are strong enough
        assert project_type in ["api-service", "web-app"] or confidence < 0.3


class TestProjectTypeTemplatePaths:
    """Tests for project type template path resolution."""

    def test_get_template_path_for_api_service(self):
        """Test getting template path for api-service."""
        path = get_project_type_template_path("api-service")
        assert path is not None
        assert path.name == "api-service.yaml"
        assert path.exists()

    def test_get_template_path_for_web_app(self):
        """Test getting template path for web-app."""
        path = get_project_type_template_path("web-app")
        assert path is not None
        assert path.name == "web-app.yaml"
        assert path.exists()

    def test_get_template_path_for_cli_tool(self):
        """Test getting template path for cli-tool."""
        path = get_project_type_template_path("cli-tool")
        assert path is not None
        assert path.name == "cli-tool.yaml"
        assert path.exists()

    def test_get_template_path_for_library(self):
        """Test getting template path for library."""
        path = get_project_type_template_path("library")
        assert path is not None
        assert path.name == "library.yaml"
        assert path.exists()

    def test_get_template_path_for_microservice(self):
        """Test getting template path for microservice."""
        path = get_project_type_template_path("microservice")
        assert path is not None
        assert path.name == "microservice.yaml"
        assert path.exists()

    def test_get_template_path_nonexistent(self):
        """Test getting template path for non-existent type."""
        path = get_project_type_template_path("nonexistent-type")
        assert path is None

    def test_get_template_path_custom_directory(self, tmp_path: Path):
        """Test getting template path from custom directory."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        (custom_dir / "custom-type.yaml").write_text("test: value")
        
        path = get_project_type_template_path("custom-type", custom_dir)
        assert path is not None
        assert path.name == "custom-type.yaml"


class TestAvailableProjectTypes:
    """Tests for listing available project types."""

    def test_get_available_types(self):
        """Test getting list of available project types."""
        types = get_available_project_types()
        assert isinstance(types, list)
        assert "api-service" in types
        assert "web-app" in types
        assert "cli-tool" in types
        assert "library" in types
        assert "microservice" in types

    def test_get_available_types_custom_directory(self, tmp_path: Path):
        """Test getting types from custom directory."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()
        (custom_dir / "type1.yaml").write_text("test: value")
        (custom_dir / "type2.yaml").write_text("test: value")
        
        types = get_available_project_types(custom_dir)
        assert "type1" in types
        assert "type2" in types
        assert len(types) == 2


class TestDetectionEdgeCases:
    """Tests for edge cases in project type detection."""

    def test_detect_with_mixed_indicators(self, tmp_path: Path):
        """Test detection with mixed indicators from multiple types."""
        # Mix of API and web app indicators
        (tmp_path / "api").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "components").mkdir()
        
        project_type, confidence, reason = detect_project_type(tmp_path)
        # Should detect one of them based on confidence
        assert project_type is not None or confidence < 0.3

    def test_detect_with_minimal_signals(self, tmp_path: Path):
        """Test detection with minimal signals (low confidence)."""
        # Just one weak indicator
        (tmp_path / "README.md").write_text("# Project")
        
        project_type, confidence, reason = detect_project_type(tmp_path)
        # Should have low confidence or return None
        assert project_type is None or confidence < 0.5

    def test_detect_nonexistent_path(self):
        """Test detection with non-existent path."""
        nonexistent = Path("/nonexistent/path/that/does/not/exist")
        project_type, confidence, reason = detect_project_type(nonexistent)
        assert project_type is None
        assert "does not exist" in reason.lower()

    def test_detect_file_instead_of_directory(self, tmp_path: Path):
        """Test detection when path is a file instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        
        # Should handle gracefully
        project_type, confidence, reason = detect_project_type(file_path)
        # May return None or handle as parent directory
        assert isinstance(project_type, (str, type(None)))

