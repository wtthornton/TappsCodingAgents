"""
Unit tests for BrownfieldAnalyzer
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from tapps_agents.core.brownfield_analyzer import BrownfieldAnalyzer, BrownfieldAnalysisResult
from tapps_agents.experts.domain_detector import DomainStackDetector, DomainMapping, StackDetectionResult


@pytest.fixture
def sample_project_root(tmp_path: Path) -> Path:
    """Create a sample project structure."""
    # Create Python project files
    (tmp_path / "requirements.txt").write_text("fastapi==0.100.0\npytest==7.4.0\npydantic==2.0.0")
    (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
dependencies = ["fastapi", "pytest"]
""")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("# FastAPI app")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("# Tests")
    return tmp_path


@pytest.fixture
def mock_domain_detector():
    """Create a mock DomainStackDetector."""
    detector = Mock(spec=DomainStackDetector)
    detector.detect.return_value = StackDetectionResult(
        detected_domains=[
            DomainMapping(
                domain="python",
                confidence=0.9,
                signals=[],
                reasoning="Detected via dependency signals"
            ),
            DomainMapping(
                domain="api-design-integration",
                confidence=0.8,
                signals=[],
                reasoning="Detected via framework signals"
            ),
        ],
        primary_language="python",
        primary_framework="fastapi",
        build_tools=[],
        ci_tools=[],
        all_signals=[],
    )
    return detector


class TestBrownfieldAnalyzer:
    """Test cases for BrownfieldAnalyzer"""

    def test_init(self, sample_project_root, mock_domain_detector):
        """Test analyzer initialization."""
        analyzer = BrownfieldAnalyzer(
            project_root=sample_project_root,
            domain_detector=mock_domain_detector
        )
        assert analyzer.project_root == sample_project_root.resolve()
        assert analyzer.domain_detector == mock_domain_detector

    def test_init_without_detector(self, sample_project_root):
        """Test analyzer initialization without domain detector."""
        analyzer = BrownfieldAnalyzer(project_root=sample_project_root)
        assert analyzer.project_root == sample_project_root.resolve()
        assert analyzer.domain_detector is not None
        assert isinstance(analyzer.domain_detector, DomainStackDetector)

    def test_detect_languages_python(self, sample_project_root, mock_domain_detector):
        """Test language detection for Python project."""
        analyzer = BrownfieldAnalyzer(
            project_root=sample_project_root,
            domain_detector=mock_domain_detector
        )
        languages = analyzer.detect_languages()
        assert "python" in languages

    def test_detect_languages_from_requirements(self, tmp_path, mock_domain_detector):
        """Test language detection from requirements.txt."""
        (tmp_path / "requirements.txt").write_text("fastapi\npytest")
        analyzer = BrownfieldAnalyzer(
            project_root=tmp_path,
            domain_detector=mock_domain_detector
        )
        languages = analyzer.detect_languages()
        assert "python" in languages

    def test_detect_languages_from_pyproject(self, tmp_path, mock_domain_detector):
        """Test language detection from pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("[project]\ndependencies = []")
        analyzer = BrownfieldAnalyzer(
            project_root=tmp_path,
            domain_detector=mock_domain_detector
        )
        languages = analyzer.detect_languages()
        assert "python" in languages

    def test_detect_languages_nodejs(self, tmp_path, mock_domain_detector):
        """Test language detection for Node.js project."""
        (tmp_path / "package.json").write_text('{"dependencies": {"react": "^18.0.0"}}')
        analyzer = BrownfieldAnalyzer(
            project_root=tmp_path,
            domain_detector=mock_domain_detector
        )
        languages = analyzer.detect_languages()
        assert "javascript" in languages

    def test_detect_languages_typescript(self, tmp_path, mock_domain_detector):
        """Test language detection for TypeScript project."""
        (tmp_path / "package.json").write_text('{"dependencies": {"react": "^18.0.0"}}')
        (tmp_path / "tsconfig.json").write_text("{}")
        analyzer = BrownfieldAnalyzer(
            project_root=tmp_path,
            domain_detector=mock_domain_detector
        )
        languages = analyzer.detect_languages()
        assert "typescript" in languages
        assert "javascript" not in languages  # TypeScript replaces JavaScript

    def test_detect_frameworks(self, sample_project_root, mock_domain_detector):
        """Test framework detection."""
        analyzer = BrownfieldAnalyzer(
            project_root=sample_project_root,
            domain_detector=mock_domain_detector
        )
        frameworks = analyzer.detect_frameworks()
        assert "fastapi" in frameworks

    def test_detect_frameworks_from_files(self, tmp_path, mock_domain_detector):
        """Test framework detection from config files."""
        (tmp_path / "next.config.js").write_text("module.exports = {}")
        (tmp_path / "package.json").write_text('{"dependencies": {"next": "^13.0.0"}}')
        analyzer = BrownfieldAnalyzer(
            project_root=tmp_path,
            domain_detector=mock_domain_detector
        )
        frameworks = analyzer.detect_frameworks()
        assert "nextjs" in frameworks

    def test_detect_dependencies_python(self, sample_project_root, mock_domain_detector):
        """Test dependency detection from requirements.txt."""
        analyzer = BrownfieldAnalyzer(
            project_root=sample_project_root,
            domain_detector=mock_domain_detector
        )
        dependencies = analyzer.detect_dependencies()
        assert "fastapi" in dependencies
        assert "pytest" in dependencies
        assert "pydantic" in dependencies

    def test_detect_dependencies_pyproject(self, tmp_path, mock_domain_detector):
        """Test dependency detection from pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("""
[project]
dependencies = ["fastapi>=0.100.0", "pytest==7.4.0"]
""")
        analyzer = BrownfieldAnalyzer(
            project_root=tmp_path,
            domain_detector=mock_domain_detector
        )
        dependencies = analyzer.detect_dependencies()
        assert "fastapi" in dependencies
        assert "pytest" in dependencies

    def test_detect_dependencies_nodejs(self, tmp_path, mock_domain_detector):
        """Test dependency detection from package.json."""
        (tmp_path / "package.json").write_text("""
{
  "dependencies": {
    "react": "^18.0.0",
    "typescript": "^5.0.0"
  },
  "devDependencies": {
    "jest": "^29.0.0"
  }
}
""")
        analyzer = BrownfieldAnalyzer(
            project_root=tmp_path,
            domain_detector=mock_domain_detector
        )
        dependencies = analyzer.detect_dependencies()
        assert "react" in dependencies
        assert "typescript" in dependencies
        assert "jest" in dependencies

    @pytest.mark.asyncio
    async def test_analyze_complete(self, sample_project_root, mock_domain_detector):
        """Test complete analysis workflow."""
        analyzer = BrownfieldAnalyzer(
            project_root=sample_project_root,
            domain_detector=mock_domain_detector
        )
        result = await analyzer.analyze()
        
        assert isinstance(result, BrownfieldAnalysisResult)
        assert result.project_root == sample_project_root.resolve()
        assert "python" in result.languages
        assert "fastapi" in result.frameworks
        assert len(result.dependencies) > 0
        assert len(result.domains) > 0
        assert result.analysis_metadata["primary_language"] == "python"
        assert result.analysis_metadata["primary_framework"] == "fastapi"

    @pytest.mark.asyncio
    async def test_analyze_empty_project(self, tmp_path):
        """Test analysis of empty project."""
        analyzer = BrownfieldAnalyzer(project_root=tmp_path)
        result = await analyzer.analyze()
        
        assert isinstance(result, BrownfieldAnalysisResult)
        assert result.project_root == tmp_path.resolve()
        assert len(result.languages) == 0
        assert len(result.frameworks) == 0
        assert len(result.dependencies) == 0

    def test_detect_dependencies_handles_errors(self, tmp_path, mock_domain_detector):
        """Test that dependency detection handles file read errors gracefully."""
        # Create invalid requirements.txt
        (tmp_path / "requirements.txt").write_bytes(b"\xff\xfe")  # Invalid UTF-8
        analyzer = BrownfieldAnalyzer(
            project_root=tmp_path,
            domain_detector=mock_domain_detector
        )
        # Should not raise exception
        dependencies = analyzer.detect_dependencies()
        assert isinstance(dependencies, list)
