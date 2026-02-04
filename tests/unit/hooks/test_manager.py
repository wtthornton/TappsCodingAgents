"""
Unit tests for tapps_agents.hooks.manager: registration, triggering, matcher logic.
"""

import sys

import pytest

from tapps_agents.hooks.config import HookDefinition, HooksConfig
from tapps_agents.hooks.events import (
    PostToolUseEvent,
    SessionStartEvent,
    UserPromptSubmitEvent,
    WorkflowCompleteEvent,
)
from tapps_agents.hooks.manager import HookManager


@pytest.mark.unit
class TestHookManagerRegistration:
    """Manager loads and registers hooks by event type."""

    def test_empty_config_no_hooks(self) -> None:
        """Empty config yields no hooks for any event."""
        mgr = HookManager(config=HooksConfig(hooks={}))
        results = mgr.trigger("UserPromptSubmit", UserPromptSubmitEvent(prompt="hi", project_root="/tmp"))
        assert results == []

    def test_trigger_invokes_hook_with_payload_env(self) -> None:
        """Trigger runs hook with env from payload.to_env()."""
        hook = HookDefinition(name="echo-prompt", command="echo ok")
        config = HooksConfig(hooks={"UserPromptSubmit": [hook]})
        mgr = HookManager(config=config)
        payload = UserPromptSubmitEvent(prompt="hello", project_root="/proj")
        results = mgr.trigger("UserPromptSubmit", payload)
        assert len(results) == 1
        assert results[0].success
        assert "ok" in results[0].stdout

    def test_disabled_hook_not_run(self) -> None:
        """Hooks with enabled=False are not executed."""
        hook = HookDefinition(name="disabled", command="echo no", enabled=False)
        config = HooksConfig(hooks={"SessionStart": [hook]})
        mgr = HookManager(config=config)
        payload = SessionStartEvent(session_id="s1", project_root="/p")
        results = mgr.trigger("SessionStart", payload)
        assert len(results) == 0


@pytest.mark.unit
class TestPostToolUseFiltering:
    """PostToolUse matcher and file_patterns filter which hooks run."""

    def test_matcher_filters_by_tool_name(self) -> None:
        """Only hooks whose matcher matches tool_name are run."""
        match_write = HookDefinition(name="on-write", command="echo write", matcher="Write|Edit")
        config = HooksConfig(hooks={"PostToolUse": [match_write]})
        mgr = HookManager(config=config)
        payload = PostToolUseEvent(
            file_path="/p/foo.py",
            file_paths=["/p/foo.py"],
            tool_name="Write",
            project_root="/p",
        )
        results = mgr.trigger("PostToolUse", payload, tool_name="Write", file_path="/p/foo.py")
        assert len(results) == 1
        results_no_match = mgr.trigger("PostToolUse", payload, tool_name="Read", file_path="/p/foo.py")
        assert len(results_no_match) == 0

    def test_file_patterns_filter_by_path(self) -> None:
        """Only hooks whose file_patterns match the file are run."""
        py_only = HookDefinition(
            name="py-only",
            command="echo py",
            file_patterns=["*.py"],
        )
        config = HooksConfig(hooks={"PostToolUse": [py_only]})
        mgr = HookManager(config=config)
        payload = PostToolUseEvent(
            file_path="/p/foo.py",
            file_paths=["/p/foo.py"],
            tool_name="Write",
            project_root="/p",
        )
        results_py = mgr.trigger("PostToolUse", payload, tool_name="Write", file_path="/p/foo.py")
        assert len(results_py) == 1
        results_js = mgr.trigger("PostToolUse", payload, tool_name="Write", file_path="/p/foo.js")
        assert len(results_js) == 0

    def test_no_matcher_or_pattern_runs_all_enabled(self) -> None:
        """Hooks without matcher/file_patterns run for any PostToolUse."""
        hook = HookDefinition(name="any", command="echo any")
        config = HooksConfig(hooks={"PostToolUse": [hook]})
        mgr = HookManager(config=config)
        payload = PostToolUseEvent(
            file_path="/p/x.txt",
            file_paths=[],
            tool_name="Read",
            project_root="/p",
        )
        results = mgr.trigger("PostToolUse", payload, tool_name="Read", file_path="/p/x.txt")
        assert len(results) == 1


@pytest.mark.unit
class TestTriggerEventTypes:
    """Trigger works for all five event types."""

    def test_workflow_complete_payload_env(self) -> None:
        """WorkflowCompleteEvent provides workflow_type, id, status in env."""
        if sys.platform == "win32":
            cmd = 'python -c "import os; print(os.environ.get(\'TAPPS_WORKFLOW_TYPE\',\'\'), os.environ.get(\'TAPPS_WORKFLOW_STATUS\',\'\'))"'
        else:
            cmd = 'python -c "import os; print(os.environ.get(\'TAPPS_WORKFLOW_TYPE\',\'\'), os.environ.get(\'TAPPS_WORKFLOW_STATUS\',\'\'))"'
        hook = HookDefinition(name="wf", command=cmd)
        config = HooksConfig(hooks={"WorkflowComplete": [hook]})
        mgr = HookManager(config=config)
        payload = WorkflowCompleteEvent(
            workflow_type="build",
            workflow_id="w1",
            status="completed",
            project_root="/p",
        )
        results = mgr.trigger("WorkflowComplete", payload)
        assert len(results) == 1
        assert results[0].success
        assert "build" in results[0].stdout and "completed" in results[0].stdout

    def test_fail_on_error_raises_on_nonzero_exit(self) -> None:
        """When hook has fail_on_error=True and returns non-zero, trigger raises."""
        hook = HookDefinition(name="strict", command="exit 1", fail_on_error=True)
        if sys.platform == "win32":
            hook = HookDefinition(name="strict", command="python -c \"import sys; sys.exit(1)\"", fail_on_error=True)
        config = HooksConfig(hooks={"SessionStart": [hook]})
        mgr = HookManager(config=config)
        payload = SessionStartEvent(session_id="s1", project_root="/p")
        with pytest.raises(RuntimeError, match="fail_on_error"):
            mgr.trigger("SessionStart", payload)
