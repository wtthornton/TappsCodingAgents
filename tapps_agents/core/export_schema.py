"""
Export Schema

Defines and validates export data format.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Export schema version
SCHEMA_VERSION = "1.0"


@dataclass
class ValidationResult:
    """Schema validation result."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    schema_version: str

    def __post_init__(self):
        """Initialize lists if None."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "schema_version": self.schema_version,
        }


class ExportSchema:
    """Defines and validates export data format."""

    SCHEMA_VERSION = SCHEMA_VERSION

    @staticmethod
    def get_schema(version: str = "1.0") -> dict[str, Any]:
        """
        Get JSON schema for specified version.

        Args:
            version: Schema version (default: "1.0")

        Returns:
            JSON schema dictionary
        """
        if version == "1.0":
            return {
                "type": "object",
                "required": ["export_metadata"],
                "properties": {
                    "export_metadata": {
                        "type": "object",
                        "required": [
                            "export_timestamp",
                            "framework_version",
                            "export_version",
                            "schema_version",
                        ],
                        "properties": {
                            "export_timestamp": {"type": "string"},
                            "framework_version": {"type": "string"},
                            "export_version": {"type": "string"},
                            "schema_version": {"type": "string"},
                            "project_hash": {"type": "string"},
                            "anonymization_applied": {"type": "boolean"},
                            "privacy_notice": {"type": "string"},
                        },
                    },
                    "capability_metrics": {"type": "object"},
                    "pattern_statistics": {"type": "object"},
                    "learning_effectiveness": {"type": "object"},
                    "analytics_data": {"type": "object"},
                },
            }
        else:
            raise ValueError(f"Unknown schema version: {version}")

    @staticmethod
    def validate(
        data: dict[str, Any], version: str = "1.0"
    ) -> ValidationResult:
        """
        Validate export data against schema.

        Args:
            data: Export data dictionary
            version: Schema version to validate against

        Returns:
            ValidationResult instance
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Basic structure validation
        if not isinstance(data, dict):
            return ValidationResult(
                valid=False,
                errors=["Export data must be a dictionary"],
                warnings=[],
                schema_version=version,
            )

        # Check required fields
        if "export_metadata" not in data:
            errors.append("Missing required field: export_metadata")

        # Validate export_metadata
        if "export_metadata" in data:
            metadata = data["export_metadata"]
            if not isinstance(metadata, dict):
                errors.append("export_metadata must be a dictionary")
            else:
                required_fields = [
                    "export_timestamp",
                    "framework_version",
                    "export_version",
                    "schema_version",
                ]
                for field in required_fields:
                    if field not in metadata:
                        errors.append(
                            f"Missing required field in export_metadata: {field}"
                        )

        # Check optional fields (warn if missing but don't fail)
        optional_fields = [
            "capability_metrics",
            "pattern_statistics",
            "learning_effectiveness",
            "analytics_data",
        ]
        for field in optional_fields:
            if field not in data:
                warnings.append(f"Optional field missing: {field}")

        # Validate schema version matches
        if "export_metadata" in data and isinstance(data["export_metadata"], dict):
            if data["export_metadata"].get("schema_version") != version:
                warnings.append(
                    f"Schema version mismatch: expected {version}, "
                    f"got {data['export_metadata'].get('schema_version')}"
                )

        valid = len(errors) == 0
        return ValidationResult(
            valid=valid, errors=errors, warnings=warnings, schema_version=version
        )

    @staticmethod
    def migrate(
        data: dict[str, Any], from_version: str, to_version: str
    ) -> dict[str, Any]:
        """
        Migrate export data between schema versions.

        Args:
            data: Export data dictionary
            from_version: Source schema version
            to_version: Target schema version

        Returns:
            Migrated export data

        Note:
            Currently only version 1.0 is supported.
            Migration logic will be added as new versions are introduced.
        """
        if from_version == to_version:
            return data

        if from_version == "1.0" and to_version == "1.0":
            return data

        raise ValueError(
            f"Migration from {from_version} to {to_version} not yet supported"
        )

    @staticmethod
    def get_latest_version() -> str:
        """
        Get latest schema version.

        Returns:
            Latest schema version string
        """
        return SCHEMA_VERSION
