"""
Issue schema definitions for validation and serialization.

Provides JSON schema for issues and serialization utilities.
"""

import json
from pathlib import Path
from typing import Any

from .evaluation_models import Issue, IssueManifest

# JSON Schema for Issue
ISSUE_SCHEMA = {
    "type": "object",
    "required": ["id", "severity", "category", "evidence", "repro", "suggested_fix", "owner_step"],
    "properties": {
        "id": {"type": "string"},
        "severity": {
            "type": "string",
            "enum": ["critical", "high", "medium", "low"],
        },
        "category": {
            "type": "string",
            "enum": [
                "security",
                "performance",
                "maintainability",
                "correctness",
                "compliance",
                "ux",
                "architecture",
                "testing",
                "documentation",
            ],
        },
        "evidence": {"type": "string"},
        "repro": {"type": "string"},
        "suggested_fix": {"type": "string"},
        "owner_step": {"type": "string"},
        "traceability": {"type": "object"},
        "file_path": {"type": ["string", "null"]},
        "line_number": {"type": ["integer", "null"]},
        "created_at": {"type": "string"},
        "resolved": {"type": "boolean"},
        "resolved_at": {"type": ["string", "null"]},
    },
}

# JSON Schema for IssueManifest
ISSUE_MANIFEST_SCHEMA = {
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": ISSUE_SCHEMA,
        },
        "summary": {
            "type": "object",
            "properties": {
                "total": {"type": "integer"},
                "by_severity": {"type": "object"},
            },
        },
    },
}


def validate_issue(issue_data: dict[str, Any]) -> tuple[bool, str | None]:
    """
    Validate issue data against schema.
    
    Args:
        issue_data: Issue data dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    required_fields = ["id", "severity", "category", "evidence", "repro", "suggested_fix", "owner_step"]
    for field in required_fields:
        if field not in issue_data:
            return False, f"Missing required field: {field}"
    
    # Check enum values
    valid_severities = ["critical", "high", "medium", "low"]
    if issue_data["severity"] not in valid_severities:
        return False, f"Invalid severity: {issue_data['severity']}"
    
    valid_categories = [
        "security",
        "performance",
        "maintainability",
        "correctness",
        "compliance",
        "ux",
        "architecture",
        "testing",
        "documentation",
    ]
    if issue_data["category"] not in valid_categories:
        return False, f"Invalid category: {issue_data['category']}"
    
    return True, None


def serialize_issue(issue: Issue) -> dict[str, Any]:
    """Serialize Issue to dictionary."""
    return issue.to_dict()


def deserialize_issue(data: dict[str, Any]) -> Issue:
    """Deserialize dictionary to Issue."""
    return Issue.from_dict(data)


def serialize_manifest(manifest: IssueManifest) -> dict[str, Any]:
    """Serialize IssueManifest to dictionary."""
    return manifest.to_dict()


def deserialize_manifest(data: dict[str, Any]) -> IssueManifest:
    """Deserialize dictionary to IssueManifest."""
    return IssueManifest.from_dict(data)


def export_issues_json(manifest: IssueManifest, file_path: Path) -> None:
    """Export issues to JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2, ensure_ascii=False)


def import_issues_json(file_path: Path) -> IssueManifest:
    """Import issues from JSON file."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    return IssueManifest.from_dict(data)

