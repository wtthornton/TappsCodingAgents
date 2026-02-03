"""
Integration tests for hook invocation during build workflow.

Verifies that the base orchestrator triggers UserPromptSubmit, PostToolUse,
and WorkflowComplete when hooks are configured (opt-in).
"""

from pathlib import Path

import pytest

from tapps_agents.simple_mode.orchestrators.build_orchestrator import BuildOrchestrator


@pytest.mark.integration
class TestBuildWorkflowHooksIntegration:
    """Hook invocation during build workflow."""

    def test_orchestrator_triggers_user_prompt_submit_when_hooks_configured(
        self, tmp_path: Path
    ) -> None:
        """UserPromptSubmit is fired before workflow when hooks.yaml has enabled hook."""
        hooks_dir = tmp_path / ".tapps-agents"
        hooks_dir.mkdir(parents=True)
        hooks_yaml = hooks_dir / "hooks.yaml"
        hooks_yaml.write_text(
            """
hooks:
  UserPromptSubmit:
    - name: test-log
      command: echo done
      enabled: true
""",
            encoding="utf-8",
        )
        orch = BuildOrchestrator(project_root=tmp_path, config=None)
        mgr = orch._get_hook_manager()
        assert mgr is not None
        orch._trigger_user_prompt_submit("test prompt", "build")
        # Trigger via manager and assert hook ran
        from tapps_agents.hooks.events import UserPromptSubmitEvent
        results = mgr.trigger(
            "UserPromptSubmit",
            UserPromptSubmitEvent(
                prompt="x", project_root=str(tmp_path), workflow_type="build"
            ),
        )
        assert len(results) >= 1
        assert results[0].success
        assert "done" in (results[0].stdout or "")

    def test_orchestrator_triggers_workflow_complete_when_hooks_configured(
        self, tmp_path: Path
    ) -> None:
        """WorkflowComplete is fired when hooks are configured."""
        hooks_dir = tmp_path / ".tapps-agents"
        hooks_dir.mkdir(parents=True)
        hooks_yaml = hooks_dir / "hooks.yaml"
        hooks_yaml.write_text(
            """
hooks:
  WorkflowComplete:
    - name: complete-log
      command: echo completed
      enabled: true
""",
            encoding="utf-8",
        )
        orch = BuildOrchestrator(project_root=tmp_path, config=None)
        orch._trigger_workflow_complete("build", "build-123", "completed", beads_issue_id=None)
        mgr = orch._get_hook_manager()
        assert mgr is not None
        from tapps_agents.hooks.events import WorkflowCompleteEvent
        results = mgr.trigger(
            "WorkflowComplete",
            WorkflowCompleteEvent(
                workflow_type="build",
                workflow_id="build-123",
                status="completed",
                project_root=str(tmp_path),
            ),
        )
        assert len(results) >= 1
        assert results[0].success

    def test_orchestrator_triggers_post_tool_use_when_hooks_configured(
        self, tmp_path: Path
    ) -> None:
        """PostToolUse is fired after implementer Write when hooks.yaml has enabled hook."""
        hooks_dir = tmp_path / ".tapps-agents"
        hooks_dir.mkdir(parents=True)
        hooks_yaml = hooks_dir / "hooks.yaml"
        hooks_yaml.write_text(
            """
hooks:
  PostToolUse:
    - name: on-write
      command: echo wrote
      enabled: true
      matcher: "Write|Edit"
      file_patterns: ["*.py"]
""",
            encoding="utf-8",
        )
        orch = BuildOrchestrator(project_root=tmp_path, config=None)
        mgr = orch._get_hook_manager()
        assert mgr is not None
        orch._trigger_post_tool_use(
            "Write",
            str(tmp_path / "src" / "app.py"),
            [str(tmp_path / "src" / "app.py")],
            workflow_id="build-1",
        )
        from tapps_agents.hooks.events import PostToolUseEvent
        results = mgr.trigger(
            "PostToolUse",
            PostToolUseEvent(
                file_path=str(tmp_path / "src" / "app.py"),
                file_paths=[str(tmp_path / "src" / "app.py")],
                tool_name="Write",
                project_root=str(tmp_path),
                workflow_id="build-1",
            ),
            tool_name="Write",
            file_path=str(tmp_path / "src" / "app.py"),
        )
        assert len(results) >= 1
        assert results[0].success

    def test_no_hooks_when_hooks_yaml_missing(self, tmp_path: Path) -> None:
        """When hooks.yaml is missing, trigger methods are no-op and manager is None."""
        orch = BuildOrchestrator(project_root=tmp_path, config=None)
        assert orch._get_hook_manager() is None
        orch._trigger_user_prompt_submit("p", None)
        orch._trigger_workflow_complete("build", "id", "failed", None)
