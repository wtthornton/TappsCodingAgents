"""
Cursor Skill Helper - Utilities for invoking Cursor Skills.

This module provides helpers for working with Cursor Skills in workflow execution.
Since Cursor doesn't have a direct programmatic API for Skills, this module
creates command files and instructions that can be used by Background Agents
or manually executed in Cursor chat.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def redact_secrets_from_text(text: str) -> str:
    """
    Redact potentially sensitive information from text (API keys, tokens, passwords).
    
    This is used to prevent accidental exposure of secrets in coordination files
    that may be persisted or shared. Implements a "minimum necessary" policy:
    only redacts obvious secrets, not all data.
    
    Args:
        text: Text that may contain secrets
        
    Returns:
        Text with secrets redacted
    """
    if not text:
        return text
    
    # Redact API keys (common patterns: sk-..., pk-..., api_key=..., API key: ..., --api_key value)
    # First, catch standalone sk-/pk- patterns (e.g., sk-test123, including in command-line args)
    text = re.sub(r'\b(sk|pk)-[A-Za-z0-9]{10,}', r'\1-***REDACTED***', text, flags=re.IGNORECASE)
    # Then catch key=value patterns
    text = re.sub(r'\b(sk|pk|api_key|apikey)=[^\s&"\'`]+', r'\1=***REDACTED***', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(api\s+key|api_key|apikey):\s*[A-Za-z0-9_-]{20,}', r'\1: ***REDACTED***', text, flags=re.IGNORECASE)
    # Command-line arguments: --api_key value, --api_key=value, or --api_key="value" (catch remaining values, but not already redacted)
    def redact_api_key_arg(match):
        value = match.group(1)
        if 'REDACTED' in value:
            return match.group(0)  # Already redacted, don't change
        return '--api_key ***REDACTED***'
    text = re.sub(r'--api[_-]?key(?:\s+|=)((?:"[^"]*"|\'[^\']*\'|[^\s"\'`]+))', redact_api_key_arg, text, flags=re.IGNORECASE)
    
    # Redact passwords
    text = re.sub(r'\b(password|pwd|passwd)=[^\s&"\'`]+', r'\1=***REDACTED***', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(password|pwd|passwd):\s*[^\s"\'`]+', r'\1: ***REDACTED***', text, flags=re.IGNORECASE)
    # Command-line arguments: --password value, --pwd value, --password=value, or --pwd="value"
    text = re.sub(r'--(?:password|pwd|passwd)(?:\s+|=)(?:"[^"]*"|\'[^\']*\'|[^\s"\'`]+)', r'--password ***REDACTED***', text, flags=re.IGNORECASE)
    
    # Redact tokens
    text = re.sub(r'\b(token|auth|bearer)\s+[A-Za-z0-9_-]{20,}', r'\1 ***REDACTED***', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(token|auth|bearer):\s*[A-Za-z0-9_-]{20,}', r'\1: ***REDACTED***', text, flags=re.IGNORECASE)
    # Command-line arguments: --token value, --auth value, --token=value, or --auth="value"
    text = re.sub(r'--(?:token|auth)(?:\s+|=)(?:"[^"]*"|\'[^\']*\'|[^\s"\'`]+)', r'--token ***REDACTED***', text, flags=re.IGNORECASE)
    
    # Redact AWS keys
    text = re.sub(r'\b(AKIA[0-9A-Z]{16})\b', r'***REDACTED***', text)
    text = re.sub(r'\baws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*["\']?[a-zA-Z0-9/+=]{40}["\']?', r'aws_secret_access_key=***REDACTED***', text, flags=re.IGNORECASE)
    
    # Redact private keys (PEM format)
    text = re.sub(r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(RSA\s+)?PRIVATE\s+KEY-----', r'-----BEGIN PRIVATE KEY-----\n***REDACTED***\n-----END PRIVATE KEY-----', text)
    
    return text


def minimize_content(content: str, max_length: int = 5000) -> str:
    """
    Minimize content by truncating if too long (minimum necessary persistence).
    
    For very long prompts or content, store a reference/ID instead of full content
    when possible.
    
    Args:
        content: Content to minimize
        max_length: Maximum length before truncation (default: 5000 chars)
        
    Returns:
        Minimized content (truncated with note if needed)
    """
    if not content:
        return content
    
    if len(content) <= max_length:
        return content
    
    # Truncate and add note
    truncated = content[:max_length]
    return f"{truncated}\n\n[... Content truncated for persistence (total length: {len(content)} chars) ...]"


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
    # Redact secrets from command before persisting
    redacted_command = redact_secrets_from_text(command)
    
    # Create correlation metadata header
    correlation_metadata = {
        "workflow_id": workflow_id,
        "step_id": step_id,
        "created_at": datetime.now().isoformat(),
        "expected_artifacts": expected_artifacts or [],
    }
    
    # Existing command file (backward compatible)
    command_file = worktree_path / ".cursor-skill-command.txt"
    
    # Create a structured command file (maintains backward compatibility)
    # Use redacted command for persistence, but include original if different
    command_data = {
        "command": redacted_command,
        "correlation": correlation_metadata,
        "worktree_path": str(worktree_path),
        "instructions": (
            "This command can be executed in Cursor by:\n"
            "1. Copying the 'command' field below into Cursor chat\n"
            "2. Or using a Background Agent configured to read this file\n"
            "3. Or manually executing the command in the worktree directory"
        ),
        "note": "Command has been redacted to remove secrets. Original command contains same structure.",
    }
    
    # If redaction changed the command, note it (but don't store original secrets)
    if redacted_command != command:
        command_data["redaction_applied"] = True
        command_data["original_length"] = len(command)
    
    # Write JSON format (backward compatible)
    command_file.write_text(json.dumps(command_data, indent=2), encoding="utf-8")
    
    # Also write a simple text version for easy copying (redacted)
    simple_file = worktree_path / ".cursor-skill-command-simple.txt"
    simple_file.write_text(redacted_command, encoding="utf-8")
    
    # New structured metadata file (webMCP pattern)
    metadata_file = worktree_path / ".cursor-skill-metadata.json"
    structured_data = {
        "version": "1.0",
        "type": "skill_command",
        "command": redacted_command,  # Use redacted command
        "correlation": correlation_metadata,
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
    
    # Note if redaction was applied
    if redacted_command != command:
        structured_data["redaction_applied"] = True
    
    metadata_file.write_text(
        json.dumps(structured_data, indent=2), encoding="utf-8"
    )
    
    return command_file, metadata_file


def create_skill_execution_instructions(
    worktree_path: Path,
    command: str,
    expected_artifacts: list[str] | None = None,
    workflow_id: str | None = None,
    step_id: str | None = None,
) -> Path:
    """
    Create execution instructions for a Skill command.

    Args:
        worktree_path: Path to the worktree
        command: The Skill command (will be redacted)
        expected_artifacts: List of expected artifact file paths
        workflow_id: Optional workflow ID for correlation
        step_id: Optional step ID for correlation

    Returns:
        Path to the instructions file
    """
    instructions_file = worktree_path / ".cursor-skill-instructions.md"
    
    # Redact secrets from command in instructions
    redacted_command = redact_secrets_from_text(command)
    
    instructions = f"""# Cursor Skill Execution Instructions

## Correlation Metadata

- **Workflow ID**: {workflow_id or 'N/A'}
- **Step ID**: {step_id or 'N/A'}
- **Created At**: {datetime.now().isoformat()}

## Command to Execute

Copy and paste this command into Cursor chat:

```
{redacted_command}
```

"""
    
    if redacted_command != command:
        instructions += "> **Note**: Command has been redacted to remove secrets. Execute in your environment with actual values.\n\n"
    
    instructions += "## Expected Results\n\nAfter execution, the following artifacts should be created:\n\n"
    
    if expected_artifacts:
        for artifact in expected_artifacts:
            instructions += f"- `{artifact}`\n"
    else:
        instructions += "- Check the worktree directory for generated files\n"
    
    instructions += f"""
## Worktree Location

All work is done in: `{worktree_path}`

## Troubleshooting

If the step fails or times out:
1. Check the failure marker at: `.tapps-agents/workflows/markers/{workflow_id or 'WORKFLOW_ID'}/step-{step_id or 'STEP_ID'}/FAILED.json`
2. Verify expected artifacts were created
3. Check the command file: `.cursor-skill-command.txt`

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
    workflow_id: str | None = None,
    step_id: str | None = None,
) -> dict[str, Any]:
    """
    Check if a Skill command has completed by looking for expected artifacts.

    Args:
        worktree_path: Path to the worktree
        expected_artifacts: List of expected artifact file paths (relative to worktree)
        workflow_id: Optional workflow ID for marker location reference
        step_id: Optional step ID for marker location reference

    Returns:
        Dictionary with completion status, found artifacts, and marker locations
    """
    result = {
        "completed": False,
        "found_artifacts": [],
        "missing_artifacts": [],
        "worktree_path": str(worktree_path),
        "marker_locations": {},
    }
    
    # Check for DONE/FAILED markers in marker directory
    if workflow_id and step_id:
        project_root = worktree_path
        # Try to find project root by looking for .tapps-agents
        while project_root != project_root.parent:
            if (project_root / ".tapps-agents").exists():
                break
            project_root = project_root.parent
        
        marker_dir = (
            project_root
            / ".tapps-agents"
            / "workflows"
            / "markers"
            / workflow_id
            / f"step-{step_id}"
        )
        done_marker = marker_dir / "DONE.json"
        failed_marker = marker_dir / "FAILED.json"
        
        if done_marker.exists():
            result["completed"] = True
            result["completion_type"] = "marker"
            result["marker_locations"]["done"] = str(done_marker)
            # Try to read marker for artifact info
            try:
                marker_data = json.loads(done_marker.read_text(encoding="utf-8"))
                result["found_artifacts"] = marker_data.get("found_artifacts", [])
                result["expected_artifacts"] = marker_data.get("expected_artifacts", [])
            except Exception:
                pass
            return result
        elif failed_marker.exists():
            result["completed"] = True  # Technically completed (with failure)
            result["completion_type"] = "failed_marker"
            result["marker_locations"]["failed"] = str(failed_marker)
            # Try to read marker for error info
            try:
                marker_data = json.loads(failed_marker.read_text(encoding="utf-8"))
                result["error"] = marker_data.get("error", "Unknown error")
                result["error_type"] = marker_data.get("error_type")
                result["found_artifacts"] = marker_data.get("found_artifacts", [])
                result["expected_artifacts"] = marker_data.get("expected_artifacts", [])
            except Exception:
                pass
            return result
    
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
    
    # Check artifact files with last modified times
    artifact_details = []
    for artifact_path in expected_artifacts:
        full_path = worktree_path / artifact_path
        if full_path.exists():
            result["found_artifacts"].append(artifact_path)
            try:
                mtime = full_path.stat().st_mtime
                artifact_details.append({
                    "path": artifact_path,
                    "exists": True,
                    "last_modified": datetime.fromtimestamp(mtime).isoformat(),
                })
            except OSError:
                artifact_details.append({
                    "path": artifact_path,
                    "exists": True,
                    "last_modified": None,
                })
        else:
            result["missing_artifacts"].append(artifact_path)
            artifact_details.append({
                "path": artifact_path,
                "exists": False,
            })
    
    result["artifact_details"] = artifact_details
    
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
        result["completion_type"] = "artifacts"
    
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

