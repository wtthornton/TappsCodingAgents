"""
Unit tests for LearningDataExporter
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from tapps_agents.core.learning_export import ExportMetadata, LearningDataExporter

pytestmark = pytest.mark.unit


class TestExportMetadata:
    """Tests for ExportMetadata dataclass."""

    def test_to_dict(self):
        """Test ExportMetadata.to_dict() converts to dictionary."""
        metadata = ExportMetadata(
            export_timestamp="2026-01-01T00:00:00Z",
            framework_version="3.2.9",
            export_version="1.0",
            schema_version="1.0",
            project_hash="abc123",
            anonymization_applied=True,
            privacy_notice="Test notice",
        )
        result = metadata.to_dict()
        assert isinstance(result, dict)
        assert result["export_timestamp"] == "2026-01-01T00:00:00Z"
        assert result["framework_version"] == "3.2.9"
        assert result["anonymization_applied"] is True


class TestLearningDataExporter:
    """Tests for LearningDataExporter class."""

    @pytest.fixture
    def mock_learning_dashboard(self):
        """Create mock LearningDashboard."""
        dashboard = MagicMock()
        dashboard.get_capability_metrics.return_value = {
            "total_capabilities": 2,
            "capabilities": [
                {"capability_id": "test-1", "success_rate": 0.9},
                {"capability_id": "test-2", "success_rate": 0.8},
            ],
        }
        dashboard.get_pattern_statistics.return_value = {
            "total_patterns": 5,
            "total_anti_patterns": 1,
        }
        dashboard.impact_reporter = MagicMock()
        dashboard.impact_reporter.get_learning_effectiveness.return_value = {
            "roi": 1.5,
        }
        return dashboard

    @pytest.fixture
    def mock_capability_registry(self):
        """Create mock CapabilityRegistry."""
        registry = MagicMock()
        registry.metrics = {}
        return registry

    @pytest.fixture
    def mock_analytics_dashboard(self):
        """Create mock AnalyticsDashboard."""
        dashboard = MagicMock()
        dashboard.get_dashboard_data.return_value = {
            "system": {"status": "healthy"},
            "agents": {},
        }
        return dashboard

    @pytest.fixture
    def exporter(
        self, mock_learning_dashboard, mock_capability_registry, mock_analytics_dashboard
    ):
        """Create LearningDataExporter instance."""
        return LearningDataExporter(
            project_root=Path.cwd(),
            learning_dashboard=mock_learning_dashboard,
            capability_registry=mock_capability_registry,
            analytics_dashboard=mock_analytics_dashboard,
        )

    def test_init_with_components(self, exporter):
        """Test initialization with provided components."""
        assert exporter.learning_dashboard is not None
        assert exporter.capability_registry is not None
        assert exporter.analytics_dashboard is not None

    def test_init_without_components(self):
        """Test auto-initialization when components not provided."""
        with patch("tapps_agents.core.learning_export.CapabilityRegistry") as mock_registry:
            with patch("tapps_agents.core.learning_export.LearningDashboard") as mock_dashboard:
                with patch("tapps_agents.core.learning_export.AnalyticsDashboard") as mock_analytics:
                    exporter = LearningDataExporter(project_root=Path.cwd())
                    # Components should be initialized
                    assert exporter.capability_registry is not None or exporter.learning_dashboard is not None

    def test_collect_capability_metrics(self, exporter, mock_learning_dashboard):
        """Test capability metrics collection."""
        result = exporter.collect_capability_metrics()
        assert "total_capabilities" in result or "error" in result
        mock_learning_dashboard.get_capability_metrics.assert_called_once()

    def test_collect_capability_metrics_filtered(self, exporter, mock_learning_dashboard):
        """Test filtering by capability ID."""
        exporter.collect_capability_metrics(capability_id="test-1")
        mock_learning_dashboard.get_capability_metrics.assert_called_once_with(
            capability_id="test-1"
        )

    def test_collect_pattern_statistics(self, exporter, mock_learning_dashboard):
        """Test pattern statistics collection."""
        result = exporter.collect_pattern_statistics()
        assert "total_patterns" in result or "error" in result
        mock_learning_dashboard.get_pattern_statistics.assert_called_once()

    def test_collect_learning_effectiveness(self, exporter, mock_learning_dashboard):
        """Test learning effectiveness collection."""
        result = exporter.collect_learning_effectiveness()
        assert isinstance(result, dict)

    def test_collect_analytics_data(self, exporter, mock_analytics_dashboard):
        """Test analytics data collection."""
        result = exporter.collect_analytics_data()
        assert "system" in result or "error" in result
        mock_analytics_dashboard.get_dashboard_data.assert_called_once()

    def test_collect_all_data(self, exporter):
        """Test complete data collection."""
        result = exporter.collect_all_data()
        assert "capability_metrics" in result
        assert "pattern_statistics" in result
        assert "learning_effectiveness" in result
        assert "analytics_data" in result

    def test_get_export_metadata(self, exporter):
        """Test metadata generation."""
        metadata = exporter.get_export_metadata()
        assert isinstance(metadata, ExportMetadata)
        assert metadata.framework_version is not None
        assert metadata.export_timestamp is not None
        assert metadata.project_hash is not None

    def test_export_basic(self, exporter):
        """Test basic export (no anonymization)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-export.json"
            result_path = exporter.export(
                output_path=output_path, anonymize=False, compress=False
            )
            assert result_path == output_path
            assert output_path.exists()
            # Verify JSON is valid
            with open(output_path, encoding="utf-8") as f:
                data = json.load(f)
            assert "export_metadata" in data

    def test_export_with_anonymization(self, exporter):
        """Test export with anonymization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-export.json"
            # Patch where AnonymizationPipeline is imported (inside the export method)
            with patch("tapps_agents.core.anonymization.AnonymizationPipeline") as mock_pipeline_class:
                mock_instance = MagicMock()
                mock_instance.anonymize_export_data.return_value = {
                    "capability_metrics": {},
                    "pattern_statistics": {},
                    "learning_effectiveness": {},
                    "analytics_data": {},
                }
                mock_pipeline_class.return_value = mock_instance
                result_path = exporter.export(
                    output_path=output_path, anonymize=True, compress=False
                )
                assert result_path == output_path
                assert output_path.exists()
                # Verify anonymization was called
                mock_instance.anonymize_export_data.assert_called_once()

    def test_export_compressed(self, exporter):
        """Test compressed export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-export.json.gz"
            result_path = exporter.export(
                output_path=output_path, anonymize=False, compress=True
            )
            assert result_path == output_path
            assert output_path.exists()
            # Verify it's actually compressed (gzip magic bytes)
            with open(output_path, "rb") as f:
                assert f.read(2) == b"\x1f\x8b"  # Gzip magic bytes

    def test_export_custom_path(self, exporter):
        """Test custom output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "custom" / "export.json"
            result_path = exporter.export(
                output_path=custom_path, anonymize=False, compress=False
            )
            assert result_path == custom_path
            assert custom_path.exists()
            assert custom_path.parent.exists()

    def test_export_missing_components(self):
        """Test graceful handling of missing components."""
        exporter = LearningDataExporter(project_root=Path.cwd())
        # Should not raise error even if components are missing
        result = exporter.collect_all_data()
        assert isinstance(result, dict)

    def test_export_validation_failure(self, exporter):
        """Test validation error handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-export.json"
            with patch("tapps_agents.core.learning_export.ExportSchema.validate") as mock_validate:
                from tapps_agents.core.export_schema import ValidationResult

                mock_validate.return_value = ValidationResult(
                    valid=False,
                    errors=["Missing required field"],
                    warnings=[],
                    schema_version="1.0",
                )
                with pytest.raises(ValueError, match="Export validation failed"):
                    exporter.export(output_path=output_path, anonymize=False)
