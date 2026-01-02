"""
Unit tests for ExportSchema
"""
import pytest

from tapps_agents.core.export_schema import ExportSchema, ValidationResult

pytestmark = pytest.mark.unit


class TestExportSchema:
    """Tests for ExportSchema class."""

    def test_get_schema_v1_0(self):
        """Test schema retrieval for v1.0."""
        schema = ExportSchema.get_schema("1.0")
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "export_metadata" in schema["required"]

    def test_get_schema_unknown_version(self):
        """Test unknown version error."""
        with pytest.raises(ValueError, match="Unknown schema version"):
            ExportSchema.get_schema("2.0")

    def test_validate_valid_data(self):
        """Test validation of valid data."""
        data = {
            "export_metadata": {
                "export_timestamp": "2026-01-01T00:00:00Z",
                "framework_version": "3.2.9",
                "export_version": "1.0",
                "schema_version": "1.0",
            },
            "capability_metrics": {},
            "pattern_statistics": {},
        }
        result = ExportSchema.validate(data)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_missing_metadata(self):
        """Test validation with missing metadata."""
        data = {"capability_metrics": {}}
        result = ExportSchema.validate(data)
        assert result.valid is False
        assert len(result.errors) > 0
        assert any("export_metadata" in error for error in result.errors)

    def test_validate_missing_required_fields(self):
        """Test validation with missing required fields."""
        data = {
            "export_metadata": {
                "export_timestamp": "2026-01-01T00:00:00Z",
                # Missing framework_version, export_version, schema_version
            }
        }
        result = ExportSchema.validate(data)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_schema_version_mismatch(self):
        """Test schema version mismatch warning."""
        data = {
            "export_metadata": {
                "export_timestamp": "2026-01-01T00:00:00Z",
                "framework_version": "3.2.9",
                "export_version": "1.0",
                "schema_version": "2.0",  # Mismatch
            }
        }
        result = ExportSchema.validate(data, version="1.0")
        assert result.valid is True  # Still valid, just warning
        assert len(result.warnings) > 0
        assert any("version mismatch" in warning.lower() for warning in result.warnings)

    def test_validate_optional_fields(self):
        """Test optional fields handling."""
        data = {
            "export_metadata": {
                "export_timestamp": "2026-01-01T00:00:00Z",
                "framework_version": "3.2.9",
                "export_version": "1.0",
                "schema_version": "1.0",
            }
            # Missing optional fields (capability_metrics, etc.)
        }
        result = ExportSchema.validate(data)
        assert result.valid is True
        assert len(result.warnings) > 0  # Should warn about missing optional fields

    def test_migrate_same_version(self):
        """Test migration with same version."""
        data = {"test": "data"}
        result = ExportSchema.migrate(data, "1.0", "1.0")
        assert result == data  # Should return unchanged

    def test_migrate_unsupported(self):
        """Test unsupported migration error."""
        with pytest.raises(ValueError, match="not yet supported"):
            ExportSchema.migrate({}, "1.0", "2.0")

    def test_get_latest_version(self):
        """Test latest version retrieval."""
        version = ExportSchema.get_latest_version()
        assert version == "1.0"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_to_dict(self):
        """Test ValidationResult.to_dict() converts to dictionary."""
        result = ValidationResult(
            valid=True,
            errors=["error1"],
            warnings=["warning1"],
            schema_version="1.0",
        )
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["valid"] is True
        assert data["errors"] == ["error1"]
        assert data["warnings"] == ["warning1"]
