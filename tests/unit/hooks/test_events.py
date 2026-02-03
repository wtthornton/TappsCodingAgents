"""
Unit tests for tapps_agents.hooks.events: event creation and serialization.
"""

import pytest

from tapps_agents.hooks.events import (
    HookEventType,
    PostToolUseEvent,
    SessionEndEvent,
    SessionStartEvent,
    UserPromptSubmitEvent,
    WorkflowCompleteEvent,
)


@pytest.mark.unit
class TestHookEventType:
    """Tests for HookEventType enum."""

    def test_five_event_types(self) -> None:
        """All five supported events are defined."""
        assert HookEventType.USER_PROMPT_SUBMIT.value == "UserPromptSubmit"
        assert HookEventType.POST_TOOL_USE.value == "PostToolUse"
        assert HookEventType.SESSION_START.value == "SessionStart"
        assert HookEventType.SESSION_END.value == "SessionEnd"
        assert HookEventType.WORKFLOW_COMPLETE.value == "WorkflowComplete"


@pytest.mark.unit
class TestUserPromptSubmitEvent:
    """Tests for UserPromptSubmitEvent."""

    def test_creation_and_serialization(self) -> None:
        """Event creates and serializes correctly."""
        e = UserPromptSubmitEvent(
            prompt="Add auth",
            project_root="/proj",
            workflow_type="build",
        )
        d = e.to_dict()
        assert d["prompt"] == "Add auth"
        assert d["project_root"] == "/proj"
        assert d["workflow_type"] == "build"

    def test_to_env(self) -> None:
        """to_env returns correct TAPPS_* variables."""
        e = UserPromptSubmitEvent(prompt="test", project_root="/root")
        env = e.to_env()
        assert env["TAPPS_PROMPT"] == "test"
        assert env["TAPPS_PROJECT_ROOT"] == "/root"


@pytest.mark.unit
class TestPostToolUseEvent:
    """Tests for PostToolUseEvent."""

    def test_creation_and_serialization(self) -> None:
        """Event creates and serializes correctly."""
        e = PostToolUseEvent(
            file_path="/proj/src/a.py",
            file_paths=["/proj/src/a.py"],
            tool_name="Write",
            project_root="/proj",
        )
        d = e.to_dict()
        assert d["file_path"] == "/proj/src/a.py"
        assert d["tool_name"] == "Write"

    def test_to_env_file_paths(self) -> None:
        """file_paths joined with space in TAPPS_FILE_PATHS."""
        e = PostToolUseEvent(
            file_path="/a.py",
            file_paths=["/a.py", "/b.py"],
            tool_name="Edit",
            project_root="/proj",
        )
        env = e.to_env()
        assert env["TAPPS_FILE_PATH"] == "/a.py"
        assert env["TAPPS_FILE_PATHS"] == "/a.py /b.py"
        assert env["TAPPS_TOOL_NAME"] == "Edit"


@pytest.mark.unit
class TestSessionStartEvent:
    """Tests for SessionStartEvent."""

    def test_creation_and_serialization(self) -> None:
        """Event creates and serializes correctly."""
        e = SessionStartEvent(session_id="sess-123", project_root="/proj")
        d = e.to_dict()
        assert d["session_id"] == "sess-123"
        assert d["project_root"] == "/proj"

    def test_to_env(self) -> None:
        """to_env includes TAPPS_SESSION_ID."""
        e = SessionStartEvent(session_id="uuid-here", project_root="/root")
        env = e.to_env()
        assert env["TAPPS_SESSION_ID"] == "uuid-here"
        assert env["TAPPS_PROJECT_ROOT"] == "/root"


@pytest.mark.unit
class TestSessionEndEvent:
    """Tests for SessionEndEvent."""

    def test_creation_and_serialization(self) -> None:
        """Event creates and serializes correctly."""
        e = SessionEndEvent(session_id="sess-456", project_root="/proj")
        d = e.to_dict()
        assert d["session_id"] == "sess-456"
        assert d["project_root"] == "/proj"

    def test_to_env(self) -> None:
        """to_env includes TAPPS_SESSION_ID."""
        e = SessionEndEvent(session_id="end-uuid", project_root="/root")
        env = e.to_env()
        assert env["TAPPS_SESSION_ID"] == "end-uuid"


@pytest.mark.unit
class TestWorkflowCompleteEvent:
    """Tests for WorkflowCompleteEvent."""

    def test_creation_and_serialization(self) -> None:
        """Event creates and serializes correctly."""
        e = WorkflowCompleteEvent(
            workflow_type="build",
            workflow_id="wf-789",
            status="completed",
            project_root="/proj",
            beads_issue_id="bd-abc",
        )
        d = e.to_dict()
        assert d["workflow_type"] == "build"
        assert d["workflow_id"] == "wf-789"
        assert d["status"] == "completed"
        assert d["beads_issue_id"] == "bd-abc"

    def test_to_env_includes_beads_when_set(self) -> None:
        """TAPPS_BEADS_ISSUE_ID included when beads_issue_id set."""
        e = WorkflowCompleteEvent(
            workflow_type="fix",
            workflow_id="w1",
            status="failed",
            project_root="/r",
            beads_issue_id="bd-x",
        )
        env = e.to_env()
        assert env["TAPPS_BEADS_ISSUE_ID"] == "bd-x"
        assert env["TAPPS_WORKFLOW_TYPE"] == "fix"

    def test_to_env_omits_beads_when_none(self) -> None:
        """TAPPS_BEADS_ISSUE_ID omitted when beads_issue_id is None."""
        e = WorkflowCompleteEvent(
            workflow_type="build",
            workflow_id="w2",
            status="completed",
            project_root="/r",
        )
        env = e.to_env()
        assert "TAPPS_BEADS_ISSUE_ID" not in env
