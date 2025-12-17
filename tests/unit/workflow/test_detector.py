"""
Tests for Workflow Detector.

Tests project type detection and workflow recommendations.
"""


import pytest

from tapps_agents.workflow.detector import ProjectDetector, ProjectType

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
