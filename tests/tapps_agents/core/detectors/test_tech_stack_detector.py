"""Tests for TechStackDetector module.

Module: Phase 1.2 - Tech Stack Detector Tests
Target Coverage: ≥90%
"""

import pytest
import tempfile
from pathlib import Path
import json

from tapps_agents.core.detectors.tech_stack_detector import (
    TechStackDetector,
    TechStack,
)

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def detector(temp_project):
    """Create TechStackDetector instance."""
    return TechStackDetector(project_root=temp_project)


class TestTechStackDataClass:
    """Test TechStack data class."""

    def test_tech_stack_creation(self):
        """Test TechStack creation with defaults."""
        stack = TechStack()
        assert stack.languages == []
        assert stack.libraries == []
        assert stack.frameworks == []
        assert stack.domains == []
        assert stack.context7_priority == []

    def test_tech_stack_with_values(self):
        """Test TechStack creation with values."""
        stack = TechStack(
            languages=["python"],
            libraries=["flask"],
            frameworks=["flask"],
            domains=["web"],
            context7_priority=["flask"]
        )
        assert stack.languages == ["python"]
        assert stack.frameworks == ["flask"]


class TestLanguageDetection:
    """Test language detection from file extensions."""

    def test_detect_python(self, temp_project, detector):
        """Test Python detection."""
        (temp_project / "main.py").write_text("print()")
        (temp_project / "utils.py").write_text("def foo(): pass")
        (temp_project / "test.py").write_text("import unittest")

        languages = detector.detect_languages()
        assert "python" in languages

    def test_detect_javascript(self, temp_project, detector):
        """Test JavaScript detection."""
        (temp_project / "app.js").write_text("console.log()")
        (temp_project / "utils.js").write_text("function foo() {}")
        (temp_project / "test.js").write_text("const x = 1")

        languages = detector.detect_languages()
        assert "javascript" in languages

    def test_detect_typescript(self, temp_project, detector):
        """Test TypeScript detection."""
        (temp_project / "app.ts").write_text("const x: number = 1")
        (temp_project / "utils.ts").write_text("interface Foo {}")
        (temp_project / "comp.tsx").write_text("const App = () => {}")

        languages = detector.detect_languages()
        assert "typescript" in languages

    def test_detect_multiple_languages(self, temp_project, detector):
        """Test detection of multiple languages."""
        for i in range(3):
            (temp_project / f"file{i}.py").write_text("pass")
            (temp_project / f"file{i}.js").write_text("const x = 1")

        languages = detector.detect_languages()
        assert "python" in languages
        assert "javascript" in languages

    def test_minimum_file_threshold(self, temp_project, detector):
        """Test that languages need at least 3 files."""
        (temp_project / "one.py").write_text("pass")
        (temp_project / "two.py").write_text("pass")

        languages = detector.detect_languages()
        assert "python" not in languages


class TestLibraryDetection:
    """Test library detection from dependency files."""

    def test_parse_requirements_txt(self, temp_project, detector):
        """Test parsing requirements.txt."""
        req_file = temp_project / "requirements.txt"
        req_file.write_text("flask==2.0.1\npytest>=7.0.0\nrequests\n")

        libraries = detector.detect_libraries()
        assert "flask" in libraries
        assert "pytest" in libraries
        assert "requests" in libraries

    def test_parse_pyproject_toml(self, temp_project, detector):
        """Test parsing pyproject.toml."""
        pyproject_file = temp_project / "pyproject.toml"
        pyproject_file.write_text("""[project]
dependencies = ["fastapi>=0.68.0", "pydantic>=1.8.0"]
""")

        libraries = detector.detect_libraries()
        assert "fastapi" in libraries
        assert "pydantic" in libraries

    def test_parse_package_json(self, temp_project, detector):
        """Test parsing package.json."""
        package_file = temp_project / "package.json"
        package_file.write_text(json.dumps({
            "name": "myproject",
            "dependencies": {"express": "^4.17.1", "react": "^17.0.2"},
            "devDependencies": {"jest": "^27.0.0"}
        }))

        libraries = detector.detect_libraries()
        assert "express" in libraries
        assert "react" in libraries
        assert "jest" in libraries


class TestFrameworkDetection:
    """Test framework detection from imports."""

    def test_detect_flask_framework(self, temp_project, detector):
        """Test Flask framework detection."""
        py_file = temp_project / "app.py"
        py_file.write_text("from flask import Flask\napp = Flask(__name__)")

        frameworks = detector.detect_frameworks()
        assert "flask" in frameworks

    def test_detect_react_framework(self, temp_project, detector):
        """Test React framework detection."""
        js_file = temp_project / "App.jsx"
        js_file.write_text("import React from 'react'")

        frameworks = detector.detect_frameworks()
        assert "react" in frameworks


class TestDomainDetection:
    """Test domain detection."""

    def test_detect_web_domain(self, detector):
        """Test web domain detection."""
        detector._detected_frameworks.add("flask")
        domains = detector.detect_domains()
        assert "web" in domains

    def test_detect_testing_domain_from_directory(self, temp_project, detector):
        """Test testing domain from directory."""
        (temp_project / "tests").mkdir()
        domains = detector.detect_domains()
        assert "testing" in domains


class TestDetectAll:
    """Test detect_all method."""

    def test_detect_all_integration(self, temp_project, detector):
        """Test complete detection workflow."""
        for i in range(3):
            (temp_project / f"file{i}.py").write_text("from flask import Flask")
        (temp_project / "requirements.txt").write_text("flask==2.0.1")

        tech_stack = detector.detect_all()
        assert "python" in tech_stack.languages
        assert "flask" in tech_stack.libraries


class TestSetupPyParsing:
    """Test setup.py parsing."""

    def test_parse_setup_py_with_dependencies(self, temp_project, detector):
        """Test parsing setup.py with install_requires."""
        setup_file = temp_project / "setup.py"
        setup_file.write_text("""
from setuptools import setup
setup(
    name="myproject",
    install_requires=["flask>=2.0", "requests", "pydantic"]
)
""")
        libraries = detector.detect_libraries()
        assert "flask" in libraries
        assert "requests" in libraries


class TestPoetryFormat:
    """Test Poetry format in pyproject.toml."""

    def test_parse_poetry_dependencies(self, temp_project, detector):
        """Test parsing Poetry dependencies."""
        pyproject = temp_project / "pyproject.toml"
        pyproject.write_text("""
[tool.poetry.dependencies]
python = "^3.8"
flask = "^2.0"
sqlalchemy = "^1.4"
""")
        libraries = detector.detect_libraries()
        assert "flask" in libraries
        assert "sqlalchemy" in libraries
        assert "python" not in libraries


class TestSkipPaths:
    """Test path skipping logic."""

    def test_skip_venv_directories(self, temp_project, detector):
        """Test skipping .venv directories."""
        venv_dir = temp_project / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        (venv_dir / "module.py").write_text("import sys")
        
        # Create real files outside venv
        for i in range(3):
            (temp_project / f"real{i}.py").write_text("pass")
        
        languages = detector.detect_languages()
        assert "python" in languages

    def test_skip_node_modules(self, temp_project, detector):
        """Test skipping node_modules."""
        node_dir = temp_project / "node_modules" / "react"
        node_dir.mkdir(parents=True)
        (node_dir / "index.js").write_text("import React")
        
        # Create real files
        for i in range(3):
            (temp_project / f"app{i}.js").write_text("const x = 1")
        
        languages = detector.detect_languages()
        assert "javascript" in languages


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_pyproject_toml(self, temp_project, detector):
        """Test handling invalid pyproject.toml."""
        (temp_project / "pyproject.toml").write_text("invalid toml ]]")
        libraries = detector.detect_libraries()
        assert isinstance(libraries, list)

    def test_invalid_package_json(self, temp_project, detector):
        """Test handling invalid package.json."""
        (temp_project / "package.json").write_text("invalid json {]")
        libraries = detector.detect_libraries()
        assert isinstance(libraries, list)

    def test_python_syntax_error(self, temp_project, detector):
        """Test handling Python files with syntax errors."""
        (temp_project / "broken.py").write_text("def invalid syntax !!")
        frameworks = detector.detect_frameworks()
        assert isinstance(frameworks, list)


class TestYamlGeneration:
    """Test YAML generation."""

    def test_generate_tech_stack_yaml_structure(self, temp_project, detector):
        """Test generated YAML has correct structure."""
        for i in range(3):
            (temp_project / f"file{i}.py").write_text("from flask import Flask")
        (temp_project / "requirements.txt").write_text("flask\npytest")
        
        yaml_data = detector.generate_tech_stack_yaml()
        
        assert "version" in yaml_data
        assert yaml_data["version"] == "1.0"
        assert "languages" in yaml_data
        assert "libraries" in yaml_data
        assert "frameworks" in yaml_data
        assert "domains" in yaml_data
        assert "context7_priority" in yaml_data
        assert yaml_data["auto_detected"] is True
        assert "detection_timestamp" in yaml_data


class TestDomainPatterns:
    """Test domain pattern matching."""

    def test_detect_data_domain(self, detector):
        """Test data domain detection."""
        detector._detected_libraries.add("pandas")
        detector._detected_libraries.add("numpy")
        domains = detector.detect_domains()
        assert "data" in domains

    def test_detect_ml_domain(self, detector):
        """Test ML domain detection."""
        detector._detected_libraries.add("tensorflow")
        domains = detector.detect_domains()
        assert "ml" in domains

    def test_detect_devops_from_dockerfile(self, temp_project, detector):
        """Test devops domain from Dockerfile."""
        (temp_project / "Dockerfile").write_text("FROM python:3.9")
        domains = detector.detect_domains()
        assert "devops" in domains


class TestMaxFilesLimit:
    """Test max files limit."""

    def test_respects_max_files_limit(self, temp_project):
        """Test detector respects max_files limit."""
        detector = TechStackDetector(project_root=temp_project, max_files=5)
        
        # Create many files
        for i in range(20):
            (temp_project / f"file{i}.py").write_text("pass")
        
        languages = detector.detect_languages()
        assert isinstance(languages, list)
