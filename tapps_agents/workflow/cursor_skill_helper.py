"""
Cursor Skill Helper - Utilities for invoking Cursor Skills.

This module provides helpers for working with Cursor Skills in workflow execution.
Since Cursor doesn't have a direct programmatic API for Skills, this module
creates command files and instructions that can be used by Background Agents
or manually executed in Cursor chat.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def create_skill_command_file(
    command: str,
    worktree_path: Path,
    workflow_id: str | None = None,
    step_id: str | None = None,
) -> Path:
    """
    Create a Skill command file that can be executed by Cursor.

    This file contains the command in a format that can be:
    1. Copied into Cursor chat
    2. Used by Background Agents
    3. Processed by helper scripts

    Args:
        command: The Skill command (e.g., "@analyst gather-requirements ...")
        worktree_path: Path to the worktree where the command should be executed
        workflow_id: Optional workflow ID for tracking
        step_id: Optional step ID for tracking

    Returns:
        Path to the created command file
    """
    command_file = worktree_path / ".cursor-skill-command.txt"
    
    # Create a structured command file
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
    
    # Write JSON format
    command_file.write_text(json.dumps(command_data, indent=2), encoding="utf-8")
    
    # Also write a simple text version for easy copying
    simple_file = worktree_path / ".cursor-skill-command-simple.txt"
    simple_file.write_text(command, encoding="utf-8")
    
    return command_file


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

