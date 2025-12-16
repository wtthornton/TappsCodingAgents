"""
E2E harness utilities for creating isolated test projects, capturing artifacts,
and managing test environments.

Provides:
- Project creation utilities
- Artifact capture and assertion
- Cleanup utilities
- Correlation ID generation
- State snapshot capture
- Failure bundle assembly
"""

import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .project_templates import TemplateType, create_template

# Configure logging for E2E tests
logger = logging.getLogger(__name__)


def generate_correlation_id() -> str:
    """
    Generate a unique correlation ID for an E2E test run.

    Returns:
        Unique correlation ID string
    """
    return f"e2e-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def create_test_project(template_type: TemplateType, tmp_path: Path) -> Path:
    """
    Create an isolated test project using a template.

    Args:
        template_type: Type of template to use (minimal, small, medium)
        tmp_path: Temporary directory path (from pytest tmp_path fixture)

    Returns:
        Path to the created project directory
    """
    project_name = f"test_project_{template_type}"
    project_path = tmp_path / project_name
    return create_template(template_type, project_path)


def capture_artifacts(
    project_path: Path,
    test_name: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """
    Capture artifacts from a test project for debugging.

    Captures:
    - Logs from .tapps-agents/logs/ (if exists)
    - Workflow state from .tapps-agents/workflow-state/ (if exists)
    - Produced artifacts from project root
    - State snapshots

    Args:
        project_path: Path to the test project
        test_name: Name of the test (for artifact organization)
        correlation_id: Optional correlation ID (generated if not provided)

    Returns:
        Dictionary containing artifact paths and metadata
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()

    artifacts: dict[str, Any] = {
        "correlation_id": correlation_id,
        "test_name": test_name,
        "project_path": str(project_path),
        "captured_at": datetime.now().isoformat(),
        "logs": [],
        "state_snapshots": [],
        "artifacts": [],
        "timeline": [],
    }

    config_dir = project_path / ".tapps-agents"

    # Capture logs
    logs_dir = config_dir / "logs"
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            artifacts["logs"].append(str(log_file.relative_to(project_path)))

    # Capture workflow state
    state_dir = config_dir / "workflow-state"
    if state_dir.exists():
        for state_file in state_dir.glob("*.json"):
            artifacts["state_snapshots"].append(str(state_file.relative_to(project_path)))

    # Capture produced artifacts (files created during test)
    # Look for common artifact patterns
    artifact_patterns = [
        "*.md",  # Documentation
        "*.yaml",  # Config files
        "*.yml",  # Config files
        "*.json",  # Data files
        "*.py",  # Generated code
    ]

    for pattern in artifact_patterns:
        for artifact_file in project_path.rglob(pattern):
            # Skip hidden directories and test files
            if any(part.startswith(".") for part in artifact_file.parts):
                if ".tapps-agents" not in artifact_file.parts:
                    continue
            if artifact_file.name.startswith("test_"):
                continue
            artifacts["artifacts"].append(str(artifact_file.relative_to(project_path)))

    return artifacts


def assert_artifact_exists(project_path: Path, artifact_path: str) -> None:
    """
    Assert that an artifact exists at the specified path.

    Args:
        project_path: Root path of the test project
        artifact_path: Relative path to the artifact from project root

    Raises:
        AssertionError: If artifact does not exist
    """
    full_path = project_path / artifact_path
    assert full_path.exists(), f"Artifact not found: {artifact_path} (full path: {full_path})"


def assert_artifact_content(project_path: Path, artifact_path: str, expected_content: str) -> None:
    """
    Assert that an artifact contains expected content.

    Args:
        project_path: Root path of the test project
        artifact_path: Relative path to the artifact from project root
        expected_content: Expected content (substring match)

    Raises:
        AssertionError: If artifact does not exist or doesn't contain expected content
    """
    full_path = project_path / artifact_path
    assert full_path.exists(), f"Artifact not found: {artifact_path}"
    actual_content = full_path.read_text(encoding="utf-8")
    assert expected_content in actual_content, (
        f"Artifact {artifact_path} does not contain expected content.\n"
        f"Expected (substring): {expected_content}\n"
        f"Actual content length: {len(actual_content)}"
    )


def assert_json_artifact_shape(
    project_path: Path,
    artifact_path: str,
    required_keys: list[str],
) -> dict[str, Any]:
    """
    Assert that a JSON artifact exists and has the required shape.

    Args:
        project_path: Root path of the test project
        artifact_path: Relative path to the JSON artifact from project root
        required_keys: List of required top-level keys

    Returns:
        Parsed JSON content

    Raises:
        AssertionError: If artifact does not exist, is invalid JSON, or missing required keys
    """
    full_path = project_path / artifact_path
    assert full_path.exists(), f"JSON artifact not found: {artifact_path}"

    try:
        content = json.loads(full_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON in artifact {artifact_path}: {e}") from e

    missing_keys = [key for key in required_keys if key not in content]
    assert not missing_keys, (
        f"JSON artifact {artifact_path} missing required keys: {missing_keys}\n"
        f"Found keys: {list(content.keys())}"
    )

    return content


def cleanup_project(project_path: Path) -> None:
    """
    Clean up a test project directory (idempotent).

    Args:
        project_path: Path to the project directory to clean up
    """
    if not project_path.exists():
        return

    try:
        # Remove the entire project directory
        shutil.rmtree(project_path, ignore_errors=True)
    except Exception as e:
        logger.warning(f"Error cleaning up project {project_path}: {e}")


def capture_state_snapshot(project_path: Path, snapshot_name: str) -> dict[str, Any]:
    """
    Capture a state snapshot at a specific point in test execution.

    Args:
        project_path: Path to the test project
        snapshot_name: Name for this snapshot

    Returns:
        Dictionary containing snapshot data
    """
    snapshot: dict[str, Any] = {
        "name": snapshot_name,
        "timestamp": datetime.now().isoformat(),
        "project_structure": {},
        "workflow_state": None,
    }

    # Capture project structure (key files/directories)
    key_paths = [
        ".tapps-agents",
        ".tapps-agents/workflow-state",
        ".tapps-agents/worktrees",
        ".tapps-agents/logs",
    ]

    for key_path in key_paths:
        full_path = project_path / key_path
        if full_path.exists():
            if full_path.is_dir():
                snapshot["project_structure"][key_path] = {
                    "type": "directory",
                    "exists": True,
                    "files": [f.name for f in full_path.iterdir() if f.is_file()],
                }
            else:
                snapshot["project_structure"][key_path] = {
                    "type": "file",
                    "exists": True,
                    "size": full_path.stat().st_size,
                }

    # Capture workflow state if it exists
    state_dir = project_path / ".tapps-agents" / "workflow-state"
    if state_dir.exists():
        state_files = list(state_dir.glob("*.json"))
        if state_files:
            # Load the most recent state file
            latest_state = max(state_files, key=lambda p: p.stat().st_mtime)
            try:
                snapshot["workflow_state"] = json.loads(latest_state.read_text(encoding="utf-8"))
            except Exception as e:
                snapshot["workflow_state"] = {"error": f"Failed to load state: {e}"}

    return snapshot


def create_failure_bundle(
    project_path: Path,
    test_name: str,
    correlation_id: str,
    error: Exception | None = None,
    snapshots: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Create a failure bundle with all debugging information.

    Args:
        project_path: Path to the test project
        test_name: Name of the test that failed
        correlation_id: Correlation ID for this test run
        error: Optional exception that caused the failure
        snapshots: Optional list of state snapshots captured during test

    Returns:
        Dictionary containing complete failure bundle
    """
    bundle: dict[str, Any] = {
        "correlation_id": correlation_id,
        "test_name": test_name,
        "failed_at": datetime.now().isoformat(),
        "project_path": str(project_path),
        "error": {
            "type": type(error).__name__ if error else None,
            "message": str(error) if error else None,
        },
        "artifacts": capture_artifacts(project_path, test_name, correlation_id),
        "snapshots": snapshots or [],
    }

    return bundle


def redact_secrets(content: str, secrets: list[str] | None = None) -> str:
    """
    Redact secrets from content (for safe logging/artifact capture).

    Args:
        content: Content to redact
        secrets: Optional list of secret values to redact (defaults to common patterns)

    Returns:
        Content with secrets redacted
    """
    if secrets is None:
        # Default patterns to redact
        secrets = []

    redacted = content

    # Redact API keys (common patterns)
    import re

    # Redact patterns like: "api_key": "value" or api_key=value
    redacted = re.sub(r'("api[_-]?key"\s*[:=]\s*")[^"]+(")', r'\1[REDACTED]\2', redacted, flags=re.IGNORECASE)
    redacted = re.sub(r'(api[_-]?key\s*=\s*)[^\s]+', r'\1[REDACTED]', redacted, flags=re.IGNORECASE)

    # Redact specific secrets if provided
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")

    return redacted
