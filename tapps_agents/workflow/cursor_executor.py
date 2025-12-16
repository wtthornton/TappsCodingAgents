"""
Cursor-Native Workflow Executor.

This module provides a Cursor-native execution model that uses Cursor Skills
and Background Agents instead of MAL for LLM operations.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.project_profile import (
    ProjectProfile,
    ProjectProfileDetector,
    load_project_profile,
    save_project_profile,
)
from ..core.runtime_mode import is_cursor_mode
from .logging_helper import WorkflowLogger
from .models import Artifact, StepExecution, Workflow, WorkflowState, WorkflowStep
from .parallel_executor import ParallelStepExecutor
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
        self.parallel_executor = ParallelStepExecutor(max_parallel=8, default_timeout_seconds=3600.0)
        self.logger: WorkflowLogger | None = None  # Initialized in start() with workflow_id
        
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
        # Use consistent workflow_id format: {workflow.id}-{timestamp}
        workflow_id = f"{workflow.id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Initialize logger with workflow_id for correlation
        self.logger = WorkflowLogger(workflow_id=workflow_id)

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

        self.logger.info(
            "Workflow started",
            workflow_name=workflow.name,
            workflow_version=workflow.version,
            step_count=len(workflow.steps),
        )
        self.save_state()
        return self.state

    def save_state(self) -> None:
        """Save workflow state to disk."""
        if not self.state:
            return

        def _make_json_serializable(obj: Any) -> Any:
            """Recursively convert objects to JSON-serializable format."""
            # Handle ProjectProfile objects
            if hasattr(obj, "to_dict") and hasattr(obj, "compliance_requirements"):
                try:
                    from ..core.project_profile import ProjectProfile
                    if isinstance(obj, ProjectProfile):
                        return obj.to_dict()
                except (ImportError, AttributeError):
                    pass
            
            # Handle ComplianceRequirement objects
            if hasattr(obj, "name") and hasattr(obj, "confidence") and hasattr(obj, "indicators"):
                try:
                    from ..core.project_profile import ComplianceRequirement
                    if isinstance(obj, ComplianceRequirement):
                        return asdict(obj)
                except (ImportError, AttributeError):
                    pass
            
            # Handle dictionaries recursively
            if isinstance(obj, dict):
                return {k: _make_json_serializable(v) for k, v in obj.items()}
            
            # Handle lists recursively
            if isinstance(obj, list):
                return [_make_json_serializable(item) for item in obj]
            
            # Handle other non-serializable types
            try:
                import json
                json.dumps(obj)
                return obj
            except (TypeError, ValueError):
                # For non-serializable types, convert to string as fallback
                return str(obj)

        state_file = self._state_dir() / f"{self.state.workflow_id}.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert variables to JSON-serializable format
        variables = self.state.variables or {}
        serializable_variables = _make_json_serializable(variables)

        # Convert to dict for JSON serialization
        state_dict = {
            "workflow_id": self.state.workflow_id,
            "status": self.state.status,
            "current_step": self.state.current_step,
            "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
            "completed_steps": self.state.completed_steps,
            "skipped_steps": self.state.skipped_steps,
            "variables": serializable_variables,
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
        if not self.state or not self.state.workflow_id.startswith(f"{self.workflow.id}-"):
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

        # Use parallel execution for independent steps
        steps_executed = 0
        completed_step_ids = set(self.state.completed_steps)
        running_step_ids: set[str] = set()

        while (
            self.state
            and self.workflow
            and self.state.status == "running"
        ):
            if steps_executed >= max_steps:
                self.state.status = "failed"
                self.state.error = f"Max steps exceeded ({max_steps}). Aborting."
                self.save_state()
                break

            # Find steps ready to execute (dependencies met)
            available_artifacts = set(self.state.artifacts.keys())
            ready_steps = self.parallel_executor.find_ready_steps(
                workflow_steps=self.workflow.steps,
                completed_step_ids=completed_step_ids,
                running_step_ids=running_step_ids,
                available_artifacts=available_artifacts,
            )

            if not ready_steps:
                # No ready steps - check if workflow is complete or blocked
                if len(completed_step_ids) >= len(self.workflow.steps):
                    self.state.status = "completed"
                    self.state.current_step = None
                    self.save_state()
                    break
                else:
                    # Workflow is blocked (dependencies not met)
                    self.state.status = "failed"
                    self.state.error = "Workflow blocked: no ready steps and workflow not complete"
                    self.save_state()
                    break

            # Execute ready steps in parallel
            running_step_ids.update(step.id for step in ready_steps)
            
            async def execute_step_wrapper(step: WorkflowStep) -> dict[str, Any]:
                """Wrapper to adapt _execute_step_for_parallel to parallel executor interface."""
                artifacts = await self._execute_step_for_parallel(step=step, target_path=target_path)
                return artifacts or {}

            try:
                results = await self.parallel_executor.execute_parallel(
                    steps=ready_steps,
                    execute_fn=execute_step_wrapper,
                    state=self.state,
                )

                # Process results and update state
                for result in results:
                    step_logger = self.logger.with_context(
                        step_id=result.step.id,
                        agent=result.step.agent,
                    ) if self.logger else None
                    
                    if result.error:
                        # Step failed - mark as failed and stop workflow
                        self.state.status = "failed"
                        self.state.error = f"Step {result.step.id} failed: {result.error}"
                        if step_logger:
                            step_logger.error(
                                "Step execution failed",
                                error=str(result.error),
                                action=result.step.action,
                            )
                        self.save_state()
                        break
                    
                    # Mark step as completed
                    completed_step_ids.add(result.step.id)
                    running_step_ids.discard(result.step.id)
                    
                    if step_logger:
                        step_logger.info(
                            "Step completed",
                            action=result.step.action,
                            duration_seconds=result.step_execution.duration_seconds,
                            artifact_count=len(result.artifacts) if result.artifacts else 0,
                        )
                    
                    # Update artifacts from result
                    if result.artifacts and isinstance(result.artifacts, dict):
                        for art_name, art_data in result.artifacts.items():
                            if isinstance(art_data, dict):
                                artifact = Artifact(
                                    name=art_data.get("name", art_name),
                                    path=art_data.get("path", ""),
                                    status="complete",
                                    created_by=result.step.id,
                                    created_at=datetime.now(),
                                    metadata=art_data.get("metadata", {}),
                                )
                                self.state.artifacts[artifact.name] = artifact

                steps_executed += len(ready_steps)
                self.save_state()

            except Exception as e:
                self.state.status = "failed"
                self.state.error = str(e)
                if self.logger:
                    self.logger.error(
                        "Workflow execution failed",
                        error=str(e),
                        exc_info=True,
                    )
                self.save_state()
                break

        if not self.state:
            raise RuntimeError("Workflow state lost during execution")

        # Mark as completed if no error
        if self.state.status == "running":
            self.state.status = "completed"
            if self.logger:
                self.logger.info(
                    "Workflow completed",
                    completed_steps=len(completed_step_ids),
                    total_steps=len(self.workflow.steps) if self.workflow else 0,
                )
            self.save_state()

        # Best-effort cleanup of worktrees created during this run
        try:
            await self.worktree_manager.cleanup_all()
        except Exception:
            pass

        return self.state

    async def _execute_step_for_parallel(
        self, step: WorkflowStep, target_path: Path | None
    ) -> dict[str, dict[str, Any]] | None:
        """
        Execute a single workflow step using Cursor Skills and return artifacts (for parallel execution).
        
        This is similar to _execute_step but returns artifacts instead of updating state.
        State updates (step_execution tracking) are handled by ParallelStepExecutor.
        """
        if not self.state or not self.workflow:
            raise ValueError("Workflow not started")

        action = self._normalize_action(step.action)
        agent_name = (step.agent or "").strip().lower()

        # Handle completion/finalization steps that don't require agent execution
        if agent_name == "orchestrator" and action in ["finalize", "complete"]:
            # Return empty artifacts for completion steps
            return {}

        try:
            # Create worktree for this step
            worktree_name = self._worktree_name_for_step(step.id)
            worktree_path = await self.worktree_manager.create_worktree(
                worktree_name=worktree_name
            )

            # Copy artifacts from previous steps to worktree
            artifacts_list = list(self.state.artifacts.values())
            await self.worktree_manager.copy_artifacts(
                worktree_path=worktree_path,
                artifacts=artifacts_list,
            )

            # Invoke Skill via SkillInvoker (creates command files for Background Agents)
            await self.skill_invoker.invoke_skill(
                agent_name=agent_name,
                action=action,
                step=step,
                target_path=target_path,
                worktree_path=worktree_path,
                state=self.state,
            )

            # Wait for Skill to complete (Background Agents execute automatically)
            import asyncio

            from .cursor_skill_helper import check_skill_completion
            
            max_wait_time = 3600  # 1 hour max wait
            poll_interval = 2  # Check every 2 seconds
            elapsed = 0
            
            print(f"Waiting for {agent_name}/{action} to complete...")
            while elapsed < max_wait_time:
                completion_status = check_skill_completion(
                    worktree_path=worktree_path,
                    expected_artifacts=step.creates,
                )
                
                if completion_status["completed"]:
                    print(f"✓ {agent_name}/{action} completed - found artifacts: {completion_status['found_artifacts']}")
                    break
                
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                
                # Print progress every 10 seconds
                if elapsed % 10 == 0:
                    print(f"  Still waiting... ({elapsed}s elapsed)")
            else:
                raise TimeoutError(
                    f"Skill {agent_name}/{action} did not complete within {max_wait_time}s. "
                    f"Expected artifacts: {step.creates}, Missing: {completion_status.get('missing_artifacts', [])}"
                )

            # Extract artifacts from worktree
            artifacts = await self.worktree_manager.extract_artifacts(
                worktree_path=worktree_path,
                step=step,
            )

            # Convert artifacts to dict format
            artifacts_dict: dict[str, dict[str, Any]] = {}
            for artifact in artifacts:
                artifacts_dict[artifact.name] = {
                    "name": artifact.name,
                    "path": artifact.path,
                    "status": artifact.status,
                    "created_by": artifact.created_by,
                    "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                    "metadata": artifact.metadata or {},
                }

            # Remove the worktree on success (keep on failure for debugging)
            try:
                await self.worktree_manager.remove_worktree(worktree_name)
            except Exception:
                pass

            return artifacts_dict if artifacts_dict else None

        except Exception:
            # Re-raise exception - ParallelStepExecutor will handle it
            raise

    def _worktree_name_for_step(self, step_id: str) -> str:
        """
        Deterministic, collision-resistant worktree name for a workflow step.

        Keeps names short/safe for Windows while still traceable back to workflow+step.
        """
        if not self.state:
            raise ValueError("Workflow not started")
        raw = f"workflow-{self.state.workflow_id}-step-{step_id}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]
        base = f"{raw}-{digest}"
        return WorktreeManager._sanitize_component(base, max_len=80)

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

        # Handle completion/finalization steps that don't require agent execution
        if agent_name == "orchestrator" and action in ["finalize", "complete"]:
            # Mark step as completed without executing an agent
            step_execution = StepExecution(
                step_id=step.id,
                agent=agent_name,
                action=action,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                status="completed",
            )
            self.state.step_executions.append(step_execution)
            self._advance_step()
            self.save_state()
            return

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
            worktree_name = self._worktree_name_for_step(step.id)
            worktree_path = await self.worktree_manager.create_worktree(
                worktree_name=worktree_name
            )

            # Copy artifacts from previous steps to worktree
            artifacts_list = list(self.state.artifacts.values())
            await self.worktree_manager.copy_artifacts(
                worktree_path=worktree_path,
                artifacts=artifacts_list,
            )

            # Invoke Skill via SkillInvoker (creates command files for Background Agents)
            result = await self.skill_invoker.invoke_skill(
                agent_name=agent_name,
                action=action,
                step=step,
                target_path=target_path,
                worktree_path=worktree_path,
                state=self.state,
            )

            # Wait for Skill to complete (Background Agents execute automatically)
            # Poll for artifacts or completion marker
            import asyncio

            from .cursor_skill_helper import check_skill_completion
            
            max_wait_time = 3600  # 1 hour max wait
            poll_interval = 2  # Check every 2 seconds
            elapsed = 0
            
            print(f"Waiting for {agent_name}/{action} to complete...")
            while elapsed < max_wait_time:
                completion_status = check_skill_completion(
                    worktree_path=worktree_path,
                    expected_artifacts=step.creates,
                )
                
                if completion_status["completed"]:
                    print(f"✓ {agent_name}/{action} completed - found artifacts: {completion_status['found_artifacts']}")
                    break
                
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                
                # Print progress every 10 seconds
                if elapsed % 10 == 0:
                    print(f"  Still waiting... ({elapsed}s elapsed)")
            else:
                raise TimeoutError(
                    f"Skill {agent_name}/{action} did not complete within {max_wait_time}s. "
                    f"Expected artifacts: {step.creates}, Missing: {completion_status.get('missing_artifacts', [])}"
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

            # Remove the worktree on success (keep on failure for debugging)
            try:
                await self.worktree_manager.remove_worktree(worktree_name)
            except Exception:
                pass

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

