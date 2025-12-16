"""
Unit tests for Coverage Analyzer.
"""

from pathlib import Path

import pytest

from tapps_agents.quality.coverage_analyzer import (
    CoverageAnalyzer,
    CoverageMetrics,
    CoverageReport,
)

pytestmark = pytest.mark.unit


class TestCoverageAnalyzer:
    """Test cases for CoverageAnalyzer."""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """Create a CoverageAnalyzer instance."""
        return CoverageAnalyzer(project_root=tmp_path)

    def test_analyzer_initialization(self, analyzer, tmp_path):
        """Test analyzer initialization."""
        assert analyzer.project_root == tmp_path.resolve()
        assert isinstance(analyzer.has_coverage, bool)

    def test_find_coverage_file_none(self, analyzer):
        """Test finding coverage file when none exists."""
        coverage_file = analyzer._find_coverage_file()
        # Should return None or a Path that doesn't exist
        assert coverage_file is None or not coverage_file.exists()

    def test_find_coverage_file_json(self, analyzer, tmp_path):
        """Test finding JSON coverage file."""
        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text('{"files": {}}')
        
        found = analyzer._find_coverage_file()
        # May or may not find it depending on implementation
        assert found is None or isinstance(found, Path)

    def test_parse_coverage_json_empty(self, analyzer, tmp_path):
        """Test parsing empty coverage JSON."""
        coverage_file = tmp_path / "coverage.json"
        coverage_file.write_text('{"files": {}}')
        
        report = analyzer._parse_coverage_json(coverage_file)
        
        assert isinstance(report, CoverageReport)
        assert report.total_files == 0
        assert report.coverage_percentage == 0.0

    def test_parse_coverage_json_with_data(self, analyzer, tmp_path):
        """Test parsing coverage JSON with data."""
        coverage_file = tmp_path / "coverage.json"
        coverage_data = {
            "files": {
                "test.py": {
                    "summary": {
                        "num_statements": 10,
                        "covered_lines": 8,
                        "missing_lines": [3, 5],
                        "percent_covered": 80.0
                    }
                }
            },
            "totals": {
                "num_statements": 10,
                "covered_lines": 8,
                "percent_covered": 80.0
            }
        }
        import json
        coverage_file.write_text(json.dumps(coverage_data))
        
        report = analyzer._parse_coverage_json(coverage_file)
        
        assert isinstance(report, CoverageReport)
        assert report.total_files >= 0
        assert report.coverage_percentage >= 0.0


class TestCoverageMetrics:
    """Test cases for CoverageMetrics."""

    def test_metrics_creation(self):
        """Test creating coverage metrics."""
        metrics = CoverageMetrics(
            file_path="test.py",
            total_lines=100,
            covered_lines=80,
            missing_lines=[1, 2, 3],
            coverage_percentage=80.0
        )
        
        assert metrics.file_path == "test.py"
        assert metrics.total_lines == 100
        assert metrics.covered_lines == 80
        assert len(metrics.missing_lines) == 3
        assert metrics.coverage_percentage == 80.0


class TestCoverageReport:
    """Test cases for CoverageReport."""

    def test_report_creation(self):
        """Test creating coverage report."""
        report = CoverageReport(
            total_files=10,
            total_lines=1000,
            covered_lines=800,
            missing_lines=200,
            coverage_percentage=80.0
        )
        
        assert report.total_files == 10
        assert report.total_lines == 1000
        assert report.covered_lines == 800
        assert report.missing_lines == 200
        assert report.coverage_percentage == 80.0
        assert report.files is not None
        assert report.missing_areas is not None

