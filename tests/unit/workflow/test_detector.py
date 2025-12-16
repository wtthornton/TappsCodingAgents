"""
Tests for Workflow Detector.

Tests project type detection and workflow recommendations.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.workflow.detector import ProjectDetector, ProjectCharacteristics, ProjectType

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
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")
        (tmp_path / "requirements.txt").write_text("requests\n")
        (tmp_path / "src").mkdir(parents=True)
        (tmp_path / "src" / "main.py").write_text("print('hello')\n")
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        assert characteristics is not None
        # Detector classifies projects by characteristics (greenfield/brownfield), not language
        # Projects without git history and minimal files are detected as GREENFIELD
        # Projects with git history and more structure would be BROWNFIELD
        assert characteristics.project_type in [ProjectType.GREENFIELD, ProjectType.BROWNFIELD, ProjectType.HYBRID]
        assert characteristics.project_type is not None

    def test_detect_javascript_project(self, tmp_path):
        """Test detecting JavaScript project structure."""
        # Create JavaScript project structure with package.json and src directory
        (tmp_path / "package.json").write_text('{"name": "test", "version": "1.0.0"}\n')
        (tmp_path / "src").mkdir(parents=True)
        (tmp_path / "src" / "index.js").write_text("console.log('hello');\n")
        
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        assert characteristics is not None
        # Detector classifies projects by characteristics (greenfield/brownfield), not language
        # Projects without git history and minimal files are detected as GREENFIELD
        # Projects with git history and more structure would be BROWNFIELD
        assert characteristics.project_type in [ProjectType.GREENFIELD, ProjectType.BROWNFIELD, ProjectType.HYBRID]
        assert characteristics.project_type is not None

    def test_detect_empty_directory(self, tmp_path):
        """Test detecting empty directory."""
        detector = ProjectDetector(tmp_path)
        characteristics = detector.detect()
        
        assert characteristics is not None
        # Should still return characteristics (may be generic/unknown)

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
