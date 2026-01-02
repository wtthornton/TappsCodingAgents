"""
Anonymization Pipeline

Anonymizes learning data for privacy protection.
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AnonymizationReport:
    """Report on anonymization process."""

    paths_anonymized: int = 0
    identifiers_hashed: int = 0
    code_snippets_removed: int = 0
    context_data_removed: int = 0
    data_points_aggregated: int = 0
    anonymization_complete: bool = True
    warnings: list[str] = None

    def __post_init__(self):
        """Initialize warnings list."""
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "paths_anonymized": self.paths_anonymized,
            "identifiers_hashed": self.identifiers_hashed,
            "code_snippets_removed": self.code_snippets_removed,
            "context_data_removed": self.context_data_removed,
            "data_points_aggregated": self.data_points_aggregated,
            "anonymization_complete": self.anonymization_complete,
            "warnings": self.warnings,
        }


class AnonymizationPipeline:
    """Anonymizes learning data for privacy."""

    def __init__(
        self,
        hash_salt: str | None = None,
        preserve_aggregates: bool = True,
    ):
        """
        Initialize anonymization pipeline.

        Args:
            hash_salt: Optional salt for hashing (for consistent hashing)
            preserve_aggregates: Whether to preserve aggregated data
        """
        self.hash_salt = hash_salt or "tapps-agents-anonymization"
        self.preserve_aggregates = preserve_aggregates
        self.report = AnonymizationReport()

    def anonymize_path(self, path: str) -> str:
        """
        Anonymize file paths (replace with generic patterns).

        Args:
            path: File path to anonymize

        Returns:
            Anonymized path pattern
        """
        if not path or not isinstance(path, str):
            return path

        # Replace specific paths with generic patterns
        # e.g., "src/api/auth.py" -> "src/**/*.py"
        # e.g., "C:\\project\\src\\main.py" -> "src/**/*.py"

        # Extract file extension
        try:
            ext = Path(path).suffix
            if ext:
                # Replace with generic pattern
                result = f"**/*{ext}"
            else:
                result = "**/*"
        except Exception:
            result = "**/*"

        self.report.paths_anonymized += 1
        return result

    def hash_identifier(self, identifier: str) -> str:
        """
        Hash identifier using SHA-256.

        Args:
            identifier: Identifier to hash

        Returns:
            Hashed identifier (first 16 characters)
        """
        if not identifier or not isinstance(identifier, str):
            return identifier

        hash_obj = hashlib.sha256(
            f"{self.hash_salt}{identifier}".encode()
        )
        hashed = hash_obj.hexdigest()[:16]
        self.report.identifiers_hashed += 1
        return f"hash_{hashed}"

    def remove_code_snippets(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Remove code snippets from data.

        Args:
            data: Data dictionary

        Returns:
            Data with code snippets removed
        """
        if not isinstance(data, dict):
            return data

        result = data.copy()
        keys_to_remove = [
            "code_snippet",
            "code",
            "source_code",
            "pattern_code",
            "snippet",
        ]

        for key in keys_to_remove:
            if key in result:
                del result[key]
                self.report.code_snippets_removed += 1

        # Recursively process nested dictionaries
        for key, value in result.items():
            if isinstance(value, dict):
                result[key] = self.remove_code_snippets(value)
            elif isinstance(value, list):
                result[key] = [
                    self.remove_code_snippets(item) if isinstance(item, dict) else item
                    for item in value
                ]

        return result

    def anonymize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Anonymize context data.

        Args:
            context: Context dictionary

        Returns:
            Anonymized context
        """
        if not isinstance(context, dict):
            return context

        result = {}
        # Only keep generic context, remove specific details
        safe_keys = ["agent_id", "command", "timestamp"]
        for key in safe_keys:
            if key in context:
                result[key] = context[key]

        self.report.context_data_removed += 1
        return result

    def anonymize_export_data(
        self, export_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Anonymize complete export data.

        Args:
            export_data: Complete export data dictionary

        Returns:
            Anonymized export data
        """
        if not isinstance(export_data, dict):
            return export_data

        result = export_data.copy()

        # Remove code snippets
        result = self.remove_code_snippets(result)

        # Anonymize capability IDs
        if "capability_metrics" in result:
            capabilities = result["capability_metrics"]
            if isinstance(capabilities, dict) and "capabilities" in capabilities:
                for cap in capabilities["capabilities"]:
                    if isinstance(cap, dict) and "capability_id" in cap:
                        cap["capability_id"] = self.hash_identifier(
                            cap["capability_id"]
                        )

        # Remove refinement history (contains sensitive details)
        if "capability_metrics" in result:
            capabilities = result["capability_metrics"]
            if isinstance(capabilities, dict) and "capabilities" in capabilities:
                for cap in capabilities["capabilities"]:
                    if isinstance(cap, dict):
                        cap.pop("refinement_history", None)
                        cap.pop("metadata", None)

        # Anonymize task IDs in pattern statistics
        if "pattern_statistics" in result:
            # Pattern statistics are already aggregated, but check for any IDs
            pass

        # Remove sensitive analytics data
        if "analytics_data" in result:
            analytics = result["analytics_data"]
            if isinstance(analytics, dict):
                # Keep only aggregated metrics, remove detailed data
                safe_keys = ["system", "trends"]
                result["analytics_data"] = {
                    k: v for k, v in analytics.items() if k in safe_keys
                }

        return result

    def validate_anonymization(
        self, original: dict[str, Any], anonymized: dict[str, Any]
    ) -> AnonymizationReport:
        """
        Validate anonymization completeness.

        Args:
            original: Original data
            anonymized: Anonymized data

        Returns:
            AnonymizationReport with validation results
        """
        # Check for code snippets
        original_str = json.dumps(original) if isinstance(original, dict) else str(original)
        if "def " in original_str or "class " in original_str:
            if "def " in json.dumps(anonymized) or "class " in json.dumps(anonymized):
                self.report.warnings.append(
                    "Potential code snippets found in anonymized data"
                )

        # Check for absolute paths
        if "C:\\" in original_str or "/home/" in original_str:
            anonymized_str = json.dumps(anonymized) if isinstance(anonymized, dict) else str(anonymized)
            if "C:\\" in anonymized_str or "/home/" in anonymized_str:
                self.report.warnings.append(
                    "Potential absolute paths found in anonymized data"
                )

        return self.report

    def generate_report(self) -> AnonymizationReport:
        """
        Generate anonymization report.

        Returns:
            AnonymizationReport instance
        """
        return self.report
