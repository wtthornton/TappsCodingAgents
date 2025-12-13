"""
Cursor-Native Workflow Executor.

This module provides a Cursor-native execution model that uses Cursor Skills
and Background Agents instead of MAL for LLM operations.
"""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - fixed args, no shell
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.project_profile import (
    ProjectProfile,
    ProjectProfileDetector,
    load_project_profile,
    save_project_profile,
)
from ..core.runtime_mode import RuntimeMode, detect_runtime_mode, is_cursor_mode
from .models import Artifact, StepExecution, Workflow, WorkflowState, WorkflowStep
from .skill_invoker import SkillInvoker
from .state_manager import AdvancedStateManager
from .worktree_manager import WorktreeManager


class CursorWorkflowExecutor:
    """
    Cursor-native workflow executor that uses Skills and Background Agents.
    
    This executor is used when running in Cursor mode (TAPPS_AGENTS_MODE=cursor).
    It invokes Cursor Skills instead of using MAL for LLM operations.
    """

    def __init__(
        self,
        project_root: Path | None = None,
        expert_registry: Any | None = None,
        auto_mode: bool = False,
    ):
        """
        Initialize Cursor-native workflow executor.

        Args:
            project_root: Root directory for the project
            expert_registry: Optional ExpertRegistry instance for expert consultation
            auto_mode: Whether to run in fully automated mode (no prompts)
        """
        if not is_cursor_mode():
            raise RuntimeError(
                "CursorWorkflowExecutor can only be used in Cursor mode. "
                "Use WorkflowExecutor for headless mode."
            )

        self.project_root = project_root or Path.cwd()
        self.state: WorkflowState | None = None
        self.workflow: Workflow | None = None
        self.expert_registry = expert_registry
        self.auto_mode = auto_mode
        self.skill_invoker = SkillInvoker(
            project_root=self.project_root, use_api=True
        )
        self.worktree_manager = WorktreeManager(project_root=self.project_root)
        self.project_profile: ProjectProfile | None = None
        
        # Initialize state manager
        state_dir = self._state_dir()
        self.state_manager = AdvancedStateManager(state_dir, compression=False)

    def _state_dir(self) -> Path:
        """Get state directory path."""
        return self.project_root / ".tapps-agents" / "workflow-state"

    def _profile_project(self) -> None:
        """
        Perform project profiling before workflow execution.
        
        Loads existing profile if available, otherwise detects and saves a new one.
        The profile is stored in workflow state and passed to all Skills via context.
        """
        # Try to load existing profile first
        self.project_profile = load_project_profile(project_root=self.project_root)
        
        # If no profile exists, detect and save it
        if not self.project_profile:
            detector = ProjectProfileDetector(project_root=self.project_root)
            self.project_profile = detector.detect_profile()
            save_project_profile(profile=self.project_profile, project_root=self.project_root)

    def start(
        self,
        workflow: Workflow,
        user_prompt: str | None = None,
    ) -> WorkflowState:
        """
        Start a new workflow execution.

        Args:
            workflow: Workflow to execute
            user_prompt: Optional user prompt for the workflow

        Returns:
            Initial workflow state
        """
        self.workflow = workflow
        workflow_id = f"{workflow.id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Perform project profiling before workflow execution
        self._profile_project()

        self.state = WorkflowState(
            workflow_id=workflow_id,
            started_at=datetime.now(),
            current_step=workflow.steps[0].id if workflow.steps else None,
            status="running",
            variables={
                "user_prompt": user_prompt or "",
                "project_profile": self.project_profile.to_dict() if self.project_profile else None,
                "workflow_name": workflow.name,  # Store in variables for reference
            },
        )

        self.save_state()
        return self.state

    def save_state(self) -> None:
        """Save workflow state to disk."""
        if not self.state:
            return

        state_file = self._state_dir() / f"{self.state.workflow_id}.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        state_dict = {
            "workflow_id": self.state.workflow_id,
            "status": self.state.status,
            "current_step": self.state.current_step,
            "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
            "completed_steps": self.state.completed_steps,
            "skipped_steps": self.state.skipped_steps,
            "variables": self.state.variables,
            "artifacts": {
                name: {
                    "name": a.name,
                    "path": a.path,
                    "status": a.status,
                    "created_by": a.created_by,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "metadata": a.metadata,
                }
                for name, a in self.state.artifacts.items()
            },
            "step_executions": [
                {
                    "step_id": se.step_id,
                    "agent": se.agent,
                    "action": se.action,
                    "started_at": se.started_at.isoformat() if se.started_at else None,
                    "completed_at": se.completed_at.isoformat() if se.completed_at else None,
                    "duration_seconds": se.duration_seconds,
                    "status": se.status,
                    "error": se.error,
                }
                for se in self.state.step_executions
            ],
            "error": self.state.error,
        }

        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)

        # Also save to history
        history_dir = state_file.parent / "history"
        history_dir.mkdir(exist_ok=True)
        history_file = history_dir / state_file.name
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)

    async def run(
        self,
        workflow: Workflow | None = None,
        target_file: str | None = None,
        max_steps: int = 100,
    ) -> WorkflowState:
        """
        Run workflow to completion.

        Args:
            workflow: Workflow to execute (if not already loaded)
            target_file: Optional target file path
            max_steps: Maximum number of steps to execute

        Returns:
            Final workflow state
        """
        if workflow:
            self.workflow = workflow
        if not self.workflow:
            raise ValueError(
                "No workflow loaded. Call start() or pass workflow."
            )

        # Ensure we have a state
        if not self.state or self.state.workflow_id != self.workflow.id:
            self.start(workflow=self.workflow)

        # Establish target file
        target_path: Path | None = None
        if target_file:
            target_path = (
                (self.project_root / target_file)
                if not Path(target_file).is_absolute()
                else Path(target_file)
            )
        else:
            target_path = self._default_target_file()

        if target_path and self.state:
            self.state.variables["target_file"] = str(target_path)

        steps_executed = 0
        while (
            self.state
            and self.workflow
            and self.state.status == "running"
            and self.state.current_step
        ):
            if steps_executed >= max_steps:
                self.state.status = "failed"
                self.state.error = f"Max steps exceeded ({max_steps}). Aborting."
                self.save_state()
                break

            step = self.get_current_step()
            if not step:
                self.state.status = "failed"
                self.state.error = f"Unknown current step: {self.state.current_step}"
                self.save_state()
                break

            try:
                await self._execute_step(step=step, target_path=target_path)
            except Exception as e:
                self.state.status = "failed"
                self.state.error = str(e)
                self.save_state()
                break

            steps_executed += 1

        if not self.state:
            raise RuntimeError("Workflow state lost during execution")

        # Mark as completed if no error
        if self.state.status == "running":
            self.state.status = "completed"
            self.save_state()

        return self.state

    def get_current_step(self) -> WorkflowStep | None:
        """Get the current workflow step."""
        if not self.workflow or not self.state:
            return None

        for step in self.workflow.steps:
            if step.id == self.state.current_step:
                return step
        return None

    def _default_target_file(self) -> Path | None:
        """Get default target file path."""
        # Try common locations
        candidates = [
            self.project_root / "src" / "app.py",
            self.project_root / "app.py",
            self.project_root / "main.py",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    async def _execute_step(
        self, step: WorkflowStep, target_path: Path | None
    ) -> None:
        """
        Execute a single workflow step using Cursor Skills.

        Args:
            step: Workflow step to execute
            target_path: Optional target file path
        """
        if not self.state or not self.workflow:
            raise ValueError("Workflow not started")

        action = self._normalize_action(step.action)
        agent_name = (step.agent or "").strip().lower()

        # Create step execution tracking
        step_execution = StepExecution(
            step_id=step.id,
            agent=agent_name,
            action=action,
            started_at=datetime.now(),
        )
        self.state.step_executions.append(step_execution)

        try:
            # Create worktree for this step
            worktree_name = f"workflow-{self.state.workflow_id}-step-{step.id}"
            worktree_path = await self.worktree_manager.create_worktree(
                worktree_name=worktree_name
            )

            # Copy artifacts from previous steps to worktree
            artifacts_list = list(self.state.artifacts.values())
            await self.worktree_manager.copy_artifacts(
                worktree_path=worktree_path,
                artifacts=artifacts_list,
            )

            # Invoke Skill via SkillInvoker
            result = await self.skill_invoker.invoke_skill(
                agent_name=agent_name,
                action=action,
                step=step,
                target_path=target_path,
                worktree_path=worktree_path,
                state=self.state,
            )

            # Extract artifacts from worktree
            artifacts = await self.worktree_manager.extract_artifacts(
                worktree_path=worktree_path,
                step=step,
            )

            # Update state with artifacts
            for artifact in artifacts:
                self.state.artifacts[artifact.name] = artifact

            # Update step execution
            step_execution.completed_at = datetime.now()
            step_execution.status = "completed"
            step_execution.result = result

            # Advance to next step
            self._advance_step()

        except Exception as e:
            step_execution.completed_at = datetime.now()
            step_execution.status = "failed"
            step_execution.error = str(e)
            raise

        finally:
            self.save_state()

    def _normalize_action(self, action: str) -> str:
        """Normalize action name."""
        return action.replace("_", "-").lower()

    def _advance_step(self) -> None:
        """Advance to the next workflow step."""
        if not self.workflow or not self.state:
            return

        current_index = None
        for i, step in enumerate(self.workflow.steps):
            if step.id == self.state.current_step:
                current_index = i
                break

        if current_index is None:
            self.state.status = "failed"
            self.state.error = f"Current step {self.state.current_step} not found"
            return

        # Move to next step
        if current_index + 1 < len(self.workflow.steps):
            self.state.current_step = self.workflow.steps[current_index + 1].id
        else:
            # All steps completed
            self.state.status = "completed"
            self.state.completed_at = datetime.now()
            self.state.current_step = None

