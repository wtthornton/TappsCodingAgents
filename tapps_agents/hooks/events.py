"""
Hook event definitions.

Defines the five hook events with data structures and serialization for
type-safe use across the hook system: UserPromptSubmit, PostToolUse,
SessionStart, SessionEnd, WorkflowComplete.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class HookEventType(StrEnum):
    """Supported hook event types."""

    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    POST_TOOL_USE = "PostToolUse"
    SESSION_START = "SessionStart"
    SESSION_END = "SessionEnd"
    WORKFLOW_COMPLETE = "WorkflowComplete"


@dataclass(frozen=True)
class UserPromptSubmitEvent:
    """Payload for UserPromptSubmit - before workflow starts."""

    prompt: str
    project_root: str
    workflow_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logging and context injection."""
        return asdict(self)

    def to_env(self) -> dict[str, str]:
        """Environment variables for hook execution."""
        d: dict[str, str] = {"TAPPS_PROMPT": self.prompt, "TAPPS_PROJECT_ROOT": self.project_root}
        if self.workflow_type:
            d["TAPPS_WORKFLOW_TYPE"] = self.workflow_type
        return d


@dataclass(frozen=True)
class PostToolUseEvent:
    """Payload for PostToolUse - after Write/Edit completes."""

    file_path: str | None
    file_paths: list[str]
    tool_name: str
    project_root: str
    workflow_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logging and context injection."""
        return asdict(self)

    def to_env(self) -> dict[str, str]:
        """Environment variables for hook execution."""
        d: dict[str, str] = {
            "TAPPS_FILE_PATH": self.file_path or "",
            "TAPPS_FILE_PATHS": " ".join(self.file_paths),
            "TAPPS_TOOL_NAME": self.tool_name,
            "TAPPS_PROJECT_ROOT": self.project_root,
        }
        if self.workflow_id:
            d["TAPPS_WORKFLOW_ID"] = self.workflow_id
        return d


@dataclass(frozen=True)
class SessionStartEvent:
    """Payload for SessionStart - CLI/Cursor session begins."""

    session_id: str
    project_root: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logging and context injection."""
        return asdict(self)

    def to_env(self) -> dict[str, str]:
        """Environment variables for hook execution."""
        return {
            "TAPPS_SESSION_ID": self.session_id,
            "TAPPS_PROJECT_ROOT": self.project_root,
        }


@dataclass(frozen=True)
class SessionEndEvent:
    """Payload for SessionEnd - session ends."""

    session_id: str
    project_root: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logging and context injection."""
        return asdict(self)

    def to_env(self) -> dict[str, str]:
        """Environment variables for hook execution."""
        return {
            "TAPPS_SESSION_ID": self.session_id,
            "TAPPS_PROJECT_ROOT": self.project_root,
        }


@dataclass(frozen=True)
class WorkflowCompleteEvent:
    """Payload for WorkflowComplete - after workflow success/fail."""

    workflow_type: str
    workflow_id: str
    status: str  # completed, failed, cancelled
    project_root: str
    beads_issue_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logging and context injection."""
        return asdict(self)

    def to_env(self) -> dict[str, str]:
        """Environment variables for hook execution."""
        d: dict[str, str] = {
            "TAPPS_WORKFLOW_TYPE": self.workflow_type,
            "TAPPS_WORKFLOW_ID": self.workflow_id,
            "TAPPS_WORKFLOW_STATUS": self.status,
            "TAPPS_PROJECT_ROOT": self.project_root,
        }
        if self.beads_issue_id:
            d["TAPPS_BEADS_ISSUE_ID"] = self.beads_issue_id
        return d
