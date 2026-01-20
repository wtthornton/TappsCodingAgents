"""
Artifact Helper - Utilities for emitting artifacts from agents.

This module provides helper functions for agents to emit versioned artifacts
in a consistent manner.
"""

from __future__ import annotations

import json
from pathlib import Path

from .code_artifact import CodeArtifact
from .design_artifact import DesignArtifact
from .enhancement_artifact import EnhancementArtifact
from .planning_artifact import PlanningArtifact
from .review_artifact import ReviewArtifact


def write_artifact(
    artifact: (
        CodeArtifact
        | DesignArtifact
        | ReviewArtifact
        | PlanningArtifact
        | EnhancementArtifact
    ),
    worktree_path: Path | None = None,
    artifact_dir: Path | None = None,
    *,
    provenance: dict | None = None,
) -> Path:
    """
    Write an artifact to disk in a deterministic location.

    Args:
        artifact: The artifact to write
        worktree_path: Optional worktree path (for background agents)
        artifact_dir: Optional custom artifact directory
        provenance: Optional dict with skill_name, command, step_id, workflow_id, timestamp

    Returns:
        Path to the written artifact file
    """
    # Determine artifact directory
    if artifact_dir:
        output_dir = Path(artifact_dir)
    elif worktree_path:
        output_dir = Path(worktree_path) / ".tapps-agents" / "artifacts"
    else:
        # Use project root detection instead of current working directory
        from ..core.path_validator import PathValidator
        validator = PathValidator()
        output_dir = validator.project_root / ".tapps-agents" / "artifacts"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate artifact filename
    artifact_type = artifact.__class__.__name__.replace("Artifact", "").lower()
    timestamp = artifact.timestamp.replace(":", "-").split(".")[0]
    correlation_id = artifact.correlation_id or "default"
    filename = f"{artifact_type}-{correlation_id}-{timestamp}.json"

    artifact_path = output_dir / filename

    # Plan 2.2: path allowlist for writes
    try:
        from ..core.config import load_config
        from ..core.path_validator import PathValidator, assert_write_allowed

        proot = PathValidator().project_root
        cfg = load_config()
        aw = getattr(getattr(cfg, "guardrails", None), "allowed_paths_write", None) or []
        assert_write_allowed(artifact_path, proot, aw)
    except Exception:  # pylint: disable=broad-except
        pass  # backward compat: if guardrails not configured, allow

    # Write JSON artifact
    # Use model_dump for Pydantic models, fall back to to_dict for backward compatibility
    if hasattr(artifact, "model_dump"):
        artifact_dict = artifact.model_dump(mode="json", exclude_none=False)
    else:
        artifact_dict = artifact.to_dict()
    if provenance:
        artifact_dict.setdefault("metadata", {})["provenance"] = provenance
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(artifact_dict, f, indent=2)

    # Optionally write markdown summary
    markdown_path = artifact_path.with_suffix(".md")
    markdown_content = _generate_markdown_summary(artifact)
    if markdown_content:
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    return artifact_path


def _generate_markdown_summary(
    artifact: (
        CodeArtifact
        | DesignArtifact
        | ReviewArtifact
        | PlanningArtifact
        | EnhancementArtifact
    ),
) -> str:
    """Generate a human-readable markdown summary of an artifact."""
    lines = [f"# {artifact.__class__.__name__}", ""]

    # Common fields
    # Handle status enum (Pydantic models) or string (legacy)
    status_value = artifact.status
    if hasattr(status_value, "value"):
        status_value = status_value.value
    lines.append(f"**Status**: {status_value}")
    lines.append(f"**Timestamp**: {artifact.timestamp}")
    if artifact.correlation_id:
        lines.append(f"**Correlation ID**: {artifact.correlation_id}")
    lines.append("")

    # Type-specific summaries
    if isinstance(artifact, CodeArtifact):
        lines.append("## Code Changes")
        lines.append(f"- Files Modified: {artifact.total_files_modified}")
        lines.append(f"- Lines Added: {artifact.total_lines_added}")
        lines.append(f"- Lines Removed: {artifact.total_lines_removed}")
        if artifact.review_passed is not None:
            lines.append(f"- Review Passed: {artifact.review_passed}")
            if artifact.review_score:
                lines.append(f"- Review Score: {artifact.review_score:.1f}")

    elif isinstance(artifact, DesignArtifact):
        lines.append("## Architecture")
        if artifact.architecture_style:
            lines.append(f"- **Style**: {artifact.architecture_style}")
        lines.append(f"- **Components**: {len(artifact.components)}")
        if artifact.technology_stack:
            lines.append(f"- **Technologies**: {', '.join(artifact.technology_stack)}")

    elif isinstance(artifact, ReviewArtifact):
        lines.append("## Review Results")
        if artifact.overall_score is not None:
            lines.append(f"- **Overall Score**: {artifact.overall_score:.1f}/100")
        if artifact.decision:
            lines.append(f"- **Decision**: {artifact.decision}")
        if artifact.passed is not None:
            lines.append(f"- **Passed**: {artifact.passed}")
        lines.append(f"- **Comments**: {len(artifact.comments)}")
        lines.append(f"- **Security Findings**: {len(artifact.security_findings)}")

    elif isinstance(artifact, PlanningArtifact):
        lines.append("## Planning Results")
        lines.append(f"- **Total Stories**: {artifact.total_stories}")
        if artifact.total_estimated_hours:
            lines.append(f"- **Estimated Hours**: {artifact.total_estimated_hours:.1f}")
        lines.append(f"- **High Priority**: {artifact.high_priority_stories}")

    elif isinstance(artifact, EnhancementArtifact):
        lines.append("## Enhancement Results")
        lines.append(f"- **Original Prompt**: {artifact.original_prompt[:100]}...")
        lines.append(f"- **Enhanced Prompt**: {artifact.enhanced_prompt[:100]}...")
        lines.append(f"- **Stages Completed**: {len(artifact.stages)}")

    # Error information
    if artifact.error:
        lines.append("")
        lines.append("## Error")
        lines.append(f"```\n{artifact.error}\n```")

    return "\n".join(lines)


def load_artifact(artifact_path: Path) -> (
    CodeArtifact | DesignArtifact | ReviewArtifact | PlanningArtifact | EnhancementArtifact
):
    """
    Load an artifact from disk.

    Args:
        artifact_path: Path to artifact JSON file

    Returns:
        Loaded artifact object
    """
    with open(artifact_path, encoding="utf-8") as f:
        data = json.load(f)

    # Determine artifact type from schema or filename
    data.get("schema_version", "1.0")
    filename = artifact_path.name.lower()

    if "code" in filename or "CodeArtifact" in str(type(data)):
        return CodeArtifact.from_dict(data)
    elif "design" in filename or "DesignArtifact" in str(type(data)):
        return DesignArtifact.from_dict(data)
    elif "review" in filename or "ReviewArtifact" in str(type(data)):
        return ReviewArtifact.from_dict(data)
    elif "planning" in filename or "PlanningArtifact" in str(type(data)):
        return PlanningArtifact.from_dict(data)
    elif "enhancement" in filename or "EnhancementArtifact" in str(type(data)):
        return EnhancementArtifact.from_dict(data)
    else:
        raise ValueError(f"Unknown artifact type: {artifact_path}")
