"""
Unit tests for workflow resume command handler.

Tests the handle_workflow_resume_command function and related CLI functionality.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from tapps_agents.cli.commands.top_level import handle_workflow_resume_command
from tapps_agents.workflow.executor import WorkflowExecutor
from tapps_agents.workflow.models import WorkflowState
from tapps_agents.workflow.parser import WorkflowParser

pytestmark = pytest.mark.unit


class TestWorkflowResumeCommand:
    """Test workflow resume command handler."""

    @pytest.fixture
    def tmp_workflow_file(self, tmp_path: Path) -> Path:
        """Create a temporary workflow file for testing."""
        workflow_file = tmp_path / "test_workflow.yaml"
        workflow_file.write_text(
            """
workflow:
  id: test-workflow
  name: Test Workflow
  description: Test workflow for resume command
  version: 1.0.0
  schema_version: "2.0"
  type: brownfield
  steps:
    - id: step1
      agent: planner
      action: plan
      next: step2
    - id: step2
      agent: implementer
      action: implement
""",
            encoding="utf-8",
        )
        return workflow_file

    @pytest.fixture
    def mock_args(self) -> Mock:
        """Create mock args object."""
        args = Mock()
        args.workflow_id = None
        args.validate = True
        args.max_steps = 50
        return args

    def test_resume_from_last_state_success(
        self, tmp_path: Path, tmp_workflow_file: Path, mock_args: Mock, monkeypatch
    ):
        """Test successful resume from last state."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        monkeypatch.chdir(tmp_path)

        # Create executor and start workflow
        executor1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
        executor1.load_workflow(tmp_workflow_file)
        state1 = executor1.start()
        executor1.save_state()

        # Mock run_async_command to avoid actual execution
        with patch("tapps_agents.cli.commands.top_level.run_async_command") as mock_run:
            final_state = WorkflowState(
                workflow_id=state1.workflow_id,
                started_at=state1.started_at,
                current_step=None,
                status="completed",
                completed_steps=["step1", "step2"],
            )
            mock_run.return_value = final_state

            # Capture stdout
            with patch("sys.stdout") as mock_stdout, patch("sys.exit") as mock_exit:
                handle_workflow_resume_command(mock_args)

                # Verify run_async_command was called
                assert mock_run.called
                call_args = mock_run.call_args
                assert call_args is not None
                # The first argument should be a coroutine from executor.execute()
                import inspect
                coro = call_args[0][0]
                assert inspect.iscoroutine(coro) or inspect.iscoroutinefunction(coro)

                # Verify no exit was called (success case)
                mock_exit.assert_not_called()

    def test_resume_with_specific_workflow_id(
        self, tmp_path: Path, tmp_workflow_file: Path, mock_args: Mock, monkeypatch
    ):
        """Test resume with specific workflow ID."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        monkeypatch.chdir(tmp_path)

        # Create executor and start workflow
        executor1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
        executor1.load_workflow(tmp_workflow_file)
        state1 = executor1.start()
        executor1.save_state()

        mock_args.workflow_id = state1.workflow_id

        # Mock run_async_command
        with patch("tapps_agents.cli.commands.top_level.run_async_command") as mock_run:
            final_state = WorkflowState(
                workflow_id=state1.workflow_id,
                started_at=state1.started_at,
                current_step=None,
                status="completed",
            )
            mock_run.return_value = final_state

            with patch("sys.stdout"), patch("sys.exit") as mock_exit:
                handle_workflow_resume_command(mock_args)

                # Verify execute was called
                assert mock_run.called
                mock_exit.assert_not_called()

    def test_resume_paused_workflow(
        self, tmp_path: Path, tmp_workflow_file: Path, mock_args: Mock, monkeypatch
    ):
        """Test resume of paused workflow."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        monkeypatch.chdir(tmp_path)

        # Create executor and start workflow
        executor1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
        executor1.load_workflow(tmp_workflow_file)
        state1 = executor1.start()
        # Pause workflow
        executor1.pause_workflow()
        executor1.save_state()

        # Mock run_async_command
        with patch("tapps_agents.cli.commands.top_level.run_async_command") as mock_run:
            final_state = WorkflowState(
                workflow_id=state1.workflow_id,
                started_at=state1.started_at,
                current_step="step2",
                status="running",
            )
            mock_run.return_value = final_state

            with patch("sys.stdout"), patch("sys.exit") as mock_exit:
                handle_workflow_resume_command(mock_args)

                # Verify execute was called
                assert mock_run.called
                mock_exit.assert_not_called()

    def test_resume_failed_workflow(
        self, tmp_path: Path, tmp_workflow_file: Path, mock_args: Mock, monkeypatch
    ):
        """Test resume of previously failed workflow."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        monkeypatch.chdir(tmp_path)

        # Create executor and start workflow
        executor1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
        executor1.load_workflow(tmp_workflow_file)
        state1 = executor1.start()
        # Mark as failed
        executor1.state.status = "failed"
        executor1.state.error = "Test error"
        executor1.save_state()

        # Mock run_async_command
        with patch("tapps_agents.cli.commands.top_level.run_async_command") as mock_run:
            final_state = WorkflowState(
                workflow_id=state1.workflow_id,
                started_at=state1.started_at,
                current_step="step2",
                status="completed",
            )
            mock_run.return_value = final_state

            with patch("sys.stdout"), patch("sys.stderr") as mock_stderr, patch(
                "sys.exit"
            ) as mock_exit:
                handle_workflow_resume_command(mock_args)

                # Verify warning was printed
                assert mock_stderr.write.called
                # Verify execute was called
                assert mock_run.called
                mock_exit.assert_not_called()

    def test_resume_completed_workflow(
        self, tmp_path: Path, tmp_workflow_file: Path, mock_args: Mock, monkeypatch
    ):
        """Test resume of already completed workflow."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        monkeypatch.chdir(tmp_path)

        # Create executor and start workflow
        executor1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
        executor1.load_workflow(tmp_workflow_file)
        state1 = executor1.start()
        # Mark as completed
        executor1.state.status = "completed"
        executor1.save_state()

        with patch("sys.stdout") as mock_stdout, patch("sys.exit") as mock_exit:
            handle_workflow_resume_command(mock_args)

            # Should exit early without calling execute
            mock_exit.assert_not_called()
            # Should print completion message
            assert mock_stdout.write.called

    def test_resume_no_state_found(self, tmp_path: Path, mock_args: Mock, monkeypatch):
        """Test resume when no state is found."""
        monkeypatch.chdir(tmp_path)

        with patch("sys.stderr") as mock_stderr, patch("sys.exit") as mock_exit:
            handle_workflow_resume_command(mock_args)

            # Should exit with error
            mock_exit.assert_called_once_with(1)
            # Should print error message
            assert mock_stderr.write.called

    def test_resume_missing_workflow_file(
        self, tmp_path: Path, tmp_workflow_file: Path, mock_args: Mock, monkeypatch
    ):
        """Test resume when workflow file is missing."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        monkeypatch.chdir(tmp_path)

        # Create executor and start workflow
        executor1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
        executor1.load_workflow(tmp_workflow_file)
        state1 = executor1.start()
        executor1.save_state()

        # Delete workflow file
        tmp_workflow_file.unlink()

        with patch("sys.stderr") as mock_stderr, patch("sys.exit") as mock_exit:
            handle_workflow_resume_command(mock_args)

            # Should exit with error
            mock_exit.assert_called_once_with(1)
            # Should print error message
            assert mock_stderr.write.called

    def test_resume_with_max_steps(
        self, tmp_path: Path, tmp_workflow_file: Path, mock_args: Mock, monkeypatch
    ):
        """Test resume with max_steps parameter."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        monkeypatch.chdir(tmp_path)

        # Create executor and start workflow
        executor1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
        executor1.load_workflow(tmp_workflow_file)
        state1 = executor1.start()
        executor1.save_state()

        mock_args.max_steps = 10

        # Mock run_async_command
        with patch("tapps_agents.cli.commands.top_level.run_async_command") as mock_run:
            final_state = WorkflowState(
                workflow_id=state1.workflow_id,
                started_at=state1.started_at,
                current_step="step2",
                status="running",
            )
            mock_run.return_value = final_state

            with patch("sys.stdout"), patch("sys.exit"):
                handle_workflow_resume_command(mock_args)

                # Verify execute was called with max_steps
                assert mock_run.called
                # The execute method should be called with max_steps=10
                # We can't directly verify this without inspecting the coroutine,
                # but we can verify the call was made

    def test_resume_with_target_file(
        self, tmp_path: Path, tmp_workflow_file: Path, mock_args: Mock, monkeypatch
    ):
        """Test resume with target file from state."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        monkeypatch.chdir(tmp_path)

        # Create executor and start workflow
        executor1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
        executor1.load_workflow(tmp_workflow_file)
        state1 = executor1.start()
        # Set target file in state
        executor1.state.variables["target_file"] = "test_file.py"
        executor1.save_state()

        # Mock run_async_command
        with patch("tapps_agents.cli.commands.top_level.run_async_command") as mock_run:
            final_state = WorkflowState(
                workflow_id=state1.workflow_id,
                started_at=state1.started_at,
                current_step=None,
                status="completed",
            )
            mock_run.return_value = final_state

            with patch("sys.stdout"), patch("sys.exit"):
                handle_workflow_resume_command(mock_args)

                # Verify execute was called
                assert mock_run.called

    def test_resume_workflow_fails_during_execution(
        self, tmp_path: Path, tmp_workflow_file: Path, mock_args: Mock, monkeypatch
    ):
        """Test resume when workflow fails during execution."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        monkeypatch.chdir(tmp_path)

        # Create executor and start workflow
        executor1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
        executor1.load_workflow(tmp_workflow_file)
        state1 = executor1.start()
        executor1.save_state()

        # Mock execute to return failed state
        with patch("tapps_agents.cli.commands.top_level.asyncio.run") as mock_run:
            final_state = WorkflowState(
                workflow_id=state1.workflow_id,
                started_at=state1.started_at,
                current_step="step2",
                status="failed",
                error="Execution failed",
            )
            mock_run.return_value = final_state

            with patch("sys.stderr") as mock_stderr, patch("sys.exit") as mock_exit:
                handle_workflow_resume_command(mock_args)

                # Should exit with error
                mock_exit.assert_called_once_with(1)
                # Should print error message
                assert mock_stderr.write.called

    def test_resume_with_validation_disabled(
        self, tmp_path: Path, tmp_workflow_file: Path, mock_args: Mock, monkeypatch
    ):
        """Test resume with validation disabled."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        monkeypatch.chdir(tmp_path)

        # Create executor and start workflow
        executor1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
        executor1.load_workflow(tmp_workflow_file)
        state1 = executor1.start()
        executor1.save_state()

        mock_args.validate = False

        # Mock run_async_command
        with patch("tapps_agents.cli.commands.top_level.run_async_command") as mock_run:
            final_state = WorkflowState(
                workflow_id=state1.workflow_id,
                started_at=state1.started_at,
                current_step=None,
                status="completed",
            )
            mock_run.return_value = final_state

            with patch("sys.stdout"), patch("sys.exit"):
                handle_workflow_resume_command(mock_args)

                # Verify execute was called
                assert mock_run.called

    def test_resume_handles_exception(
        self, tmp_path: Path, tmp_workflow_file: Path, mock_args: Mock, monkeypatch
    ):
        """Test resume handles exceptions gracefully."""
        monkeypatch.setenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "true")
        monkeypatch.chdir(tmp_path)

        # Create executor and start workflow
        executor1 = WorkflowExecutor(project_root=tmp_path, auto_detect=False)
        executor1.load_workflow(tmp_workflow_file)
        state1 = executor1.start()
        executor1.save_state()

        # Mock execute to raise exception
        with patch("tapps_agents.cli.commands.top_level.asyncio.run") as mock_run:
            mock_run.side_effect = RuntimeError("Test exception")

            with patch("sys.stderr") as mock_stderr, patch("sys.exit") as mock_exit, patch(
                "traceback.print_exc"
            ):
                handle_workflow_resume_command(mock_args)

                # Should exit with error
                mock_exit.assert_called_once_with(1)
                # Should print error message
                assert mock_stderr.write.called

