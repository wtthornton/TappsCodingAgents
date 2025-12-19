"""
Cursor Skill Helper - Utilities for invoking Cursor Skills.

This module provides helpers for working with Cursor Skills in workflow execution.
Since Cursor doesn't have a direct programmatic API for Skills, this module
creates command files and instructions that can be used by Background Agents
or manually executed in Cursor chat.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def create_skill_command_file(
    command: str,
    worktree_path: Path,
    workflow_id: str | None = None,
    step_id: str | None = None,
    expected_artifacts: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    """
    Create a Skill command file with structured metadata (webMCP pattern).

    This function creates both:
    1. A simple command file (`.cursor-skill-command.txt`) for backward compatibility
    2. A structured metadata file (`.cursor-skill-metadata.json`) with workflow context

    Args:
        command: The Skill command (e.g., "@analyst gather-requirements ...")
        worktree_path: Path to the worktree where the command should be executed
        workflow_id: Optional workflow ID for tracking
        step_id: Optional step ID for tracking
        expected_artifacts: List of expected artifact file paths (relative to worktree)
        metadata: Optional additional metadata dictionary

    Returns:
        Tuple of (command_file_path, metadata_file_path)
    """
    # Existing command file (backward compatible)
    command_file = worktree_path / ".cursor-skill-command.txt"
    
    # Create a structured command file (maintains backward compatibility)
    command_data = {
        "command": command,
        "workflow_id": workflow_id,
        "step_id": step_id,
        "worktree_path": str(worktree_path),
        "instructions": (
            "This command can be executed in Cursor by:\n"
            "1. Copying the 'command' field below into Cursor chat\n"
            "2. Or using a Background Agent configured to read this file\n"
            "3. Or manually executing the command in the worktree directory"
        ),
    }
    
    # Write JSON format (backward compatible)
    command_file.write_text(json.dumps(command_data, indent=2), encoding="utf-8")
    
    # Also write a simple text version for easy copying
    simple_file = worktree_path / ".cursor-skill-command-simple.txt"
    simple_file.write_text(command, encoding="utf-8")
    
    # New structured metadata file (webMCP pattern)
    metadata_file = worktree_path / ".cursor-skill-metadata.json"
    structured_data = {
        "version": "1.0",
        "type": "skill_command",
        "command": command,
        "workflow_context": {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "expected_artifacts": expected_artifacts or [],
        },
        "interaction_pattern": {
            "mode": "async",
            "completion_detection": "status_file_and_artifacts",
            "progress_updates": True,
            "error_handling": "retry_with_backoff",
        },
        "metadata": metadata or {},
        "timestamp": datetime.now().isoformat(),
    }
    metadata_file.write_text(
        json.dumps(structured_data, indent=2), encoding="utf-8"
    )
    
    return command_file, metadata_file


def create_skill_execution_instructions(
    worktree_path: Path,
    command: str,
    expected_artifacts: list[str] | None = None,
) -> Path:
    """
    Create execution instructions for a Skill command.

    Args:
        worktree_path: Path to the worktree
        command: The Skill command
        expected_artifacts: List of expected artifact file paths

    Returns:
        Path to the instructions file
    """
    instructions_file = worktree_path / ".cursor-skill-instructions.md"
    
    instructions = f"""# Cursor Skill Execution Instructions

## Command to Execute

Copy and paste this command into Cursor chat:

```
{command}
```

## Expected Results

After execution, the following artifacts should be created:

"""
    
    if expected_artifacts:
        for artifact in expected_artifacts:
            instructions += f"- `{artifact}`\n"
    else:
        instructions += "- Check the worktree directory for generated files\n"
    
    instructions += f"""
## Worktree Location

All work is done in: `{worktree_path}`

## Next Steps

1. Execute the command in Cursor chat
2. Wait for the Skill to complete
3. Verify that expected artifacts are created
4. The workflow executor will detect completion when artifacts are present
"""
    
    instructions_file.write_text(instructions, encoding="utf-8")
    return instructions_file


def check_skill_completion(
    worktree_path: Path,
    expected_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    """
    Check if a Skill command has completed by looking for expected artifacts.

    Args:
        worktree_path: Path to the worktree
        expected_artifacts: List of expected artifact file paths (relative to worktree)

    Returns:
        Dictionary with completion status and found artifacts
    """
    result = {
        "completed": False,
        "found_artifacts": [],
        "missing_artifacts": [],
        "worktree_path": str(worktree_path),
    }
    
    if not expected_artifacts:
        # If no expected artifacts, check for common ones
        common_artifacts = [
            "requirements.md",
            "stories",
            "architecture.md",
            "api-specs",
            "src",
            "tests",
            "docs",
        ]
        expected_artifacts = common_artifacts
    
    for artifact_path in expected_artifacts:
        full_path = worktree_path / artifact_path
        if full_path.exists():
            result["found_artifacts"].append(artifact_path)
        else:
            result["missing_artifacts"].append(artifact_path)
    
    # Check for background agent artifacts (quality/testing)
    quality_report = worktree_path / "reports" / "quality" / "quality-report.json"
    test_report = worktree_path / "reports" / "tests" / "test-report.json"
    
    if quality_report.exists():
        result["found_artifacts"].append("reports/quality/quality-report.json")
    if test_report.exists():
        result["found_artifacts"].append("reports/tests/test-report.json")
    
    # Consider complete if at least one expected artifact exists
    # or if a completion marker exists
    completion_marker = worktree_path / ".skill-completed.txt"
    if completion_marker.exists() or result["found_artifacts"]:
        result["completed"] = True
    
    return result


def read_skill_metadata(worktree_path: Path) -> dict[str, Any] | None:
    """
    Read structured metadata from a worktree.

    Args:
        worktree_path: Path to the worktree containing metadata

    Returns:
        Dictionary with metadata if found, None otherwise
    """
    metadata_file = worktree_path / ".cursor-skill-metadata.json"
    
    if not metadata_file.exists():
        return None
    
    try:
        metadata_content = metadata_file.read_text(encoding="utf-8")
        return json.loads(metadata_content)
    except (json.JSONDecodeError, OSError) as e:
        # Log error but don't fail - metadata is optional
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to read skill metadata from {metadata_file}: {e}")
        return None


def get_expected_artifacts_from_metadata(worktree_path: Path) -> list[str]:
    """
    Extract expected artifacts from metadata file.

    Args:
        worktree_path: Path to the worktree containing metadata

    Returns:
        List of expected artifact paths, empty list if metadata not found
    """
    metadata = read_skill_metadata(worktree_path)
    if not metadata:
        return []
    
    workflow_context = metadata.get("workflow_context", {})
    return workflow_context.get("expected_artifacts", [])


def write_structured_status_file(
    status_file: Path,
    status: str,
    progress: dict[str, Any] | None = None,
    partial_results: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
    artifacts: list[str] | None = None,
    output: str | None = None,
    metadata: dict[str, Any] | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> None:
    """
    Write structured status file (Phase 4 - Enhanced format).

    This function creates a structured status file that includes:
    - Progress updates (percentage, current step, message)
    - Partial results (artifacts, output)
    - Error details (message, code, retryable, retry_count)
    - Metadata (workflow_id, step_id, command)

    Args:
        status_file: Path to status file to write
        status: Status string ("running", "completed", "failed", "pending")
        progress: Optional progress information
        partial_results: Optional partial results
        error: Optional error information
        artifacts: Optional list of artifact paths
        output: Optional execution output
        metadata: Optional metadata (workflow_id, step_id, command)
        started_at: Optional ISO datetime string for start time
        completed_at: Optional ISO datetime string for completion time
    """
    status_data = {
        "version": "1.0",
        "status": status,
    }
    
    if started_at:
        status_data["started_at"] = started_at
    if completed_at:
        status_data["completed_at"] = completed_at
    
    if progress:
        status_data["progress"] = progress
    
    if partial_results:
        status_data["partial_results"] = partial_results
    
    if error:
        status_data["error"] = error
    
    if artifacts:
        status_data["artifacts"] = artifacts
    
    if output:
        status_data["output"] = output
    
    if metadata:
        status_data["metadata"] = metadata
    
    status_file.write_text(
        json.dumps(status_data, indent=2), encoding="utf-8"
    )

