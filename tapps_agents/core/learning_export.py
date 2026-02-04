"""
Learning Data Export System

Enables users to export learning data from the self-improvement system
for feedback and framework improvement.
"""

import gzip
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .analytics_dashboard import AnalyticsDashboard
from .capability_registry import CapabilityRegistry
from .export_schema import ExportSchema
from .learning_dashboard import LearningDashboard

logger = logging.getLogger(__name__)


@dataclass
class ExportMetadata:
    """Export metadata."""

    export_timestamp: str
    framework_version: str
    export_version: str
    schema_version: str
    project_hash: str
    anonymization_applied: bool
    privacy_notice: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "export_timestamp": self.export_timestamp,
            "framework_version": self.framework_version,
            "export_version": self.export_version,
            "schema_version": self.schema_version,
            "project_hash": self.project_hash,
            "anonymization_applied": self.anonymization_applied,
            "privacy_notice": self.privacy_notice,
        }


class LearningDataExporter:
    """Collects and exports learning data from all learning system components."""

    def __init__(
        self,
        project_root: Path | None = None,
        learning_dashboard: LearningDashboard | None = None,
        capability_registry: CapabilityRegistry | None = None,
        analytics_dashboard: AnalyticsDashboard | None = None,
    ):
        """
        Initialize exporter with learning system components.

        Args:
            project_root: Project root directory
            learning_dashboard: Optional LearningDashboard instance
            capability_registry: Optional CapabilityRegistry instance
            analytics_dashboard: Optional AnalyticsDashboard instance
        """
        self.project_root = project_root or Path.cwd()
        self.learning_dashboard = learning_dashboard
        self.capability_registry = capability_registry
        self.analytics_dashboard = analytics_dashboard

        # Try to initialize components if not provided
        if self.capability_registry is None:
            try:
                self.capability_registry = CapabilityRegistry()
            except Exception as e:
                logger.warning(f"Could not initialize CapabilityRegistry: {e}")

        if self.learning_dashboard is None and self.capability_registry:
            try:
                self.learning_dashboard = LearningDashboard(
                    capability_registry=self.capability_registry
                )
            except Exception as e:
                logger.warning(f"Could not initialize LearningDashboard: {e}")

        if self.analytics_dashboard is None:
            try:
                self.analytics_dashboard = AnalyticsDashboard()
            except Exception as e:
                logger.warning(f"Could not initialize AnalyticsDashboard: {e}")

    def collect_capability_metrics(
        self, capability_id: str | None = None
    ) -> dict[str, Any]:
        """
        Collect capability metrics from CapabilityRegistry.

        Args:
            capability_id: Optional filter by capability

        Returns:
            Capability metrics dictionary
        """
        if not self.learning_dashboard:
            return {"error": "LearningDashboard not available"}

        try:
            return self.learning_dashboard.get_capability_metrics(
                capability_id=capability_id
            )
        except Exception as e:
            logger.error(f"Error collecting capability metrics: {e}")
            return {"error": str(e)}

    def collect_pattern_statistics(self) -> dict[str, Any]:
        """
        Collect pattern statistics from PatternExtractor.

        Returns:
            Pattern statistics dictionary
        """
        if not self.learning_dashboard:
            return {"error": "LearningDashboard not available"}

        try:
            return self.learning_dashboard.get_pattern_statistics()
        except Exception as e:
            logger.error(f"Error collecting pattern statistics: {e}")
            return {"error": str(e)}

    def collect_learning_effectiveness(self) -> dict[str, Any]:
        """
        Collect learning effectiveness data from meta-learning components.

        Returns:
            Learning effectiveness dictionary
        """
        if not self.learning_dashboard:
            return {"error": "LearningDashboard not available"}

        try:
            effectiveness = {}
            if self.learning_dashboard.impact_reporter:
                effectiveness = (
                    self.learning_dashboard.impact_reporter.get_learning_effectiveness()
                )
            return effectiveness
        except Exception as e:
            logger.error(f"Error collecting learning effectiveness: {e}")
            return {"error": str(e)}

    def collect_analytics_data(self) -> dict[str, Any]:
        """
        Collect analytics data from AnalyticsDashboard.

        Returns:
            Analytics data dictionary
        """
        if not self.analytics_dashboard:
            return {"error": "AnalyticsDashboard not available"}

        try:
            return self.analytics_dashboard.get_dashboard_data()
        except Exception as e:
            logger.error(f"Error collecting analytics data: {e}")
            return {"error": str(e)}

    def collect_all_data(self) -> dict[str, Any]:
        """
        Collect all learning data from all components.

        Returns:
            Complete learning data dictionary
        """
        data: dict[str, Any] = {
            "capability_metrics": self.collect_capability_metrics(),
            "pattern_statistics": self.collect_pattern_statistics(),
            "learning_effectiveness": self.collect_learning_effectiveness(),
            "analytics_data": self.collect_analytics_data(),
        }

        return data

    def get_export_metadata(self) -> ExportMetadata:
        """
        Get export metadata (timestamp, version, etc.).

        Returns:
            ExportMetadata instance
        """
        # Get framework version
        try:
            from .. import __version__

            framework_version = __version__
        except Exception:
            framework_version = "unknown"

        # Generate project hash (anonymized identifier)
        project_hash = hashlib.sha256(
            str(self.project_root).encode()
        ).hexdigest()[:16]

        return ExportMetadata(
            export_timestamp=datetime.now(UTC).isoformat(),
            framework_version=framework_version,
            export_version="1.0",
            schema_version="1.0",
            project_hash=project_hash,
            anonymization_applied=True,
            privacy_notice="Exported data is anonymized and contains no sensitive information. Code snippets and project-specific paths have been removed.",
        )

    def export(
        self,
        output_path: Path | None = None,
        anonymize: bool = True,
        compress: bool = False,
        format: str = "json",
    ) -> Path:
        """
        Export learning data to file.

        Args:
            output_path: Output file path (default: .tapps-agents/exports/learning-export-{timestamp}.json)
            anonymize: Whether to anonymize data (default: True)
            compress: Whether to compress export (default: False)
            format: Export format (default: "json")

        Returns:
            Path to exported file
        """
        # Determine output path
        if output_path is None:
            export_dir = self.project_root / ".tapps-agents" / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
            extension = ".json.gz" if compress else ".json"
            output_path = export_dir / f"learning-export-{timestamp}{extension}"

        # Collect all data
        logger.info("Collecting learning data...")
        data = self.collect_all_data()

        # Anonymize if requested
        if anonymize:
            logger.info("Anonymizing data...")
            from .anonymization import AnonymizationPipeline

            pipeline = AnonymizationPipeline()
            data = pipeline.anonymize_export_data(data)

        # Add export metadata
        metadata = self.get_export_metadata()
        metadata.anonymization_applied = anonymize

        export_data: dict[str, Any] = {
            "export_metadata": metadata.to_dict(),
            **data,
        }

        # Validate against schema
        logger.info("Validating export data...")
        validation_result = ExportSchema.validate(export_data)
        if not validation_result.valid:
            logger.warning(f"Validation warnings: {validation_result.warnings}")
            if validation_result.errors:
                raise ValueError(
                    f"Export validation failed: {validation_result.errors}"
                )

        # Write to file
        logger.info(f"Writing export to {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if compress:
            with gzip.open(output_path, "wt", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)

        logger.info(f"Export completed: {output_path}")
        return output_path
