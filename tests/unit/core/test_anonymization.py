"""
Unit tests for AnonymizationPipeline
"""
import json
from unittest.mock import MagicMock

import pytest

from tapps_agents.core.anonymization import (
    AnonymizationPipeline,
    AnonymizationReport,
)

pytestmark = pytest.mark.unit


class TestAnonymizationReport:
    """Tests for AnonymizationReport dataclass."""

    def test_to_dict(self):
        """Test AnonymizationReport.to_dict() converts to dictionary."""
        report = AnonymizationReport(
            paths_anonymized=5,
            identifiers_hashed=10,
            code_snippets_removed=3,
            context_data_removed=2,
            data_points_aggregated=1,
            anonymization_complete=True,
            warnings=["test warning"],
        )
        result = report.to_dict()
        assert isinstance(result, dict)
        assert result["paths_anonymized"] == 5
        assert result["identifiers_hashed"] == 10
        assert result["warnings"] == ["test warning"]


class TestAnonymizationPipeline:
    """Tests for AnonymizationPipeline class."""

    @pytest.fixture
    def pipeline(self):
        """Create AnonymizationPipeline instance."""
        return AnonymizationPipeline()

    def test_anonymize_path_basic(self, pipeline):
        """Test basic path anonymization."""
        result = pipeline.anonymize_path("src/api/auth.py")
        assert result == "**/*.py"
        assert pipeline.report.paths_anonymized == 1

    def test_anonymize_path_windows(self, pipeline):
        """Test Windows path anonymization."""
        result = pipeline.anonymize_path("C:\\project\\src\\main.py")
        assert result == "**/*.py"
        assert pipeline.report.paths_anonymized == 1

    def test_anonymize_path_unix(self, pipeline):
        """Test Unix path anonymization."""
        result = pipeline.anonymize_path("/home/user/project/src/main.py")
        assert result == "**/*.py"
        assert pipeline.report.paths_anonymized == 1

    def test_anonymize_path_no_extension(self, pipeline):
        """Test path without extension."""
        result = pipeline.anonymize_path("src/main")
        assert result == "**/*"
        assert pipeline.report.paths_anonymized == 1

    def test_hash_identifier(self, pipeline):
        """Test identifier hashing."""
        result = pipeline.hash_identifier("test-capability-123")
        assert result.startswith("hash_")
        assert len(result) > 10  # Should be hashed
        assert pipeline.report.identifiers_hashed == 1

    def test_hash_identifier_consistency(self, pipeline):
        """Test consistent hashing with same salt."""
        result1 = pipeline.hash_identifier("test-id")
        result2 = pipeline.hash_identifier("test-id")
        assert result1 == result2  # Same input should produce same hash

    def test_remove_code_snippets(self, pipeline):
        """Test code snippet removal."""
        data = {
            "code_snippet": "def test(): pass",
            "other_data": "keep this",
            "nested": {"code": "remove this", "keep": "this"},
        }
        result = pipeline.remove_code_snippets(data)
        assert "code_snippet" not in result
        assert "other_data" in result
        assert "code" not in result["nested"]
        assert "keep" in result["nested"]
        assert pipeline.report.code_snippets_removed >= 1

    def test_remove_code_snippets_nested(self, pipeline):
        """Test nested code snippet removal."""
        data = {
            "level1": {
                "level2": {
                    "code_snippet": "def test(): pass",
                    "keep": "this",
                }
            }
        }
        result = pipeline.remove_code_snippets(data)
        assert "code_snippet" not in result["level1"]["level2"]
        assert "keep" in result["level1"]["level2"]

    def test_anonymize_context(self, pipeline):
        """Test context anonymization."""
        context = {
            "agent_id": "reviewer",
            "command": "review",
            "timestamp": "2026-01-01",
            "sensitive": "remove this",
        }
        result = pipeline.anonymize_context(context)
        assert "agent_id" in result
        assert "command" in result
        assert "sensitive" not in result
        assert pipeline.report.context_data_removed == 1

    def test_anonymize_export_data(self, pipeline):
        """Test complete export data anonymization."""
        export_data = {
            "capability_metrics": {
                "capabilities": [
                    {"capability_id": "test-1", "refinement_history": [{"data": "sensitive"}]}
                ]
            },
            "pattern_statistics": {},
            "learning_effectiveness": {},
            "analytics_data": {"system": {}, "sensitive": "remove"},
        }
        result = pipeline.anonymize_export_data(export_data)
        # Check that capability IDs are hashed
        if "capability_metrics" in result and "capabilities" in result["capability_metrics"]:
            for cap in result["capability_metrics"]["capabilities"]:
                if "capability_id" in cap:
                    assert cap["capability_id"].startswith("hash_")
        # Check that refinement_history is removed
        if "capability_metrics" in result and "capabilities" in result["capability_metrics"]:
            for cap in result["capability_metrics"]["capabilities"]:
                assert "refinement_history" not in cap
        # Check that sensitive analytics data is removed
        if "analytics_data" in result:
            assert "sensitive" not in result["analytics_data"]

    def test_validate_anonymization(self, pipeline):
        """Test anonymization validation."""
        original = {"code": "def test(): pass", "path": "C:\\project\\file.py"}
        anonymized = {"code": "removed", "path": "**/*.py"}
        report = pipeline.validate_anonymization(original, anonymized)
        assert isinstance(report, AnonymizationReport)

    def test_generate_report(self, pipeline):
        """Test report generation."""
        # Perform some anonymization operations
        pipeline.anonymize_path("test.py")
        pipeline.hash_identifier("test-id")
        report = pipeline.generate_report()
        assert isinstance(report, AnonymizationReport)
        assert report.paths_anonymized == 1
        assert report.identifiers_hashed == 1
