"""
Cursor-Native Workflow Executor.

This module provides a Cursor-native execution model that uses Cursor Skills
and direct execution for LLM operations.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator

from ..core.project_profile import (
    ProjectProfile,
    ProjectProfileDetector,
    load_project_profile,
    save_project_profile,
)
from ..core.runtime_mode import is_cursor_mode
from .auto_progression import AutoProgressionManager, ProgressionAction
from .checkpoint_manager import (
    CheckpointConfig,
    CheckpointFrequency,
    WorkflowCheckpointManager,
)
from .error_recovery import ErrorContext, ErrorRecoveryManager
from .logging_helper import WorkflowLogger
from .event_bus import FileBasedEventBus
from .events import EventType, WorkflowEvent
from .models import Artifact, StepExecution, Workflow, WorkflowState, WorkflowStep
from .parallel_executor import ParallelStepExecutor
from .progress_manager import ProgressUpdateManager
from .skill_invoker import SkillInvoker
from .state_manager import AdvancedStateManager
from .state_persistence_config import StatePersistenceConfigManager
from .worktree_manager import WorktreeManager
from .marker_writer import MarkerWriter


class CursorWorkflowExecutor:
    """
    Cursor-native workflow executor that uses Skills and Background Agents.
    
    This executor is used when running in Cursor mode (TAPPS_AGENTS_MODE=cursor).
    It invokes Cursor Skills for LLM operations.
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
        self.progress_manager: ProgressUpdateManager | None = None  # Initialized in start() with workflow
        
        # Initialize event bus for event-driven communication (Phase 2)
        self.event_bus = FileBasedEventBus(project_root=self.project_root)
        
        # Initialize auto-progression manager (Epic 10)
        auto_progression_enabled = os.getenv("TAPPS_AGENTS_AUTO_PROGRESSION", "true").lower() == "true"
        self.auto_progression = AutoProgressionManager(
            auto_progression_enabled=auto_progression_enabled,
            auto_retry_enabled=True,
            max_retries=3,
        )
        
        # Initialize error recovery manager (Epic 14)
        error_recovery_enabled = os.getenv("TAPPS_AGENTS_ERROR_RECOVERY", "true").lower() == "true"
        self.error_recovery = ErrorRecoveryManager(
            enable_auto_retry=error_recovery_enabled,
            max_retries=3,
        ) if error_recovery_enabled else None
        
        # Initialize state persistence configuration manager (Epic 12 - Story 12.6)
        self.state_config_manager = StatePersistenceConfigManager(project_root=self.project_root)
        
        # Initialize checkpoint manager (Epic 12)
        # Use configuration from state persistence config if available
        state_config = self.state_config_manager.config
        if state_config and state_config.checkpoint:
            checkpoint_frequency = state_config.checkpoint.mode
            checkpoint_interval = state_config.checkpoint.interval
            checkpoint_enabled = state_config.checkpoint.enabled
        else:
            # Fall back to environment variables
            checkpoint_frequency = os.getenv("TAPPS_AGENTS_CHECKPOINT_FREQUENCY", "every_step")
            checkpoint_interval = int(os.getenv("TAPPS_AGENTS_CHECKPOINT_INTERVAL", "1"))
            checkpoint_enabled = os.getenv("TAPPS_AGENTS_CHECKPOINT_ENABLED", "true").lower() == "true"
        
        try:
            frequency = CheckpointFrequency(checkpoint_frequency)
        except ValueError:
            frequency = CheckpointFrequency.EVERY_STEP
        
        checkpoint_config = CheckpointConfig(
            frequency=frequency,
            interval=checkpoint_interval,
            enabled=checkpoint_enabled,
        )
        self.checkpoint_manager = WorkflowCheckpointManager(config=checkpoint_config)
        
        # Initialize state manager
        # Use storage location from config
        if state_config and state_config.enabled:
            state_dir = self.state_config_manager.get_storage_path()
            compression = state_config.compression
        else:
            state_dir = self._state_dir()
            compression = False
        self.state_manager = AdvancedStateManager(state_dir, compression=compression)
        
        # Initialize Background Agent auto-executor (Epic 7)
        # Load config to check if auto-execution is enabled
        # Default to True for better user experience (can be overridden by config)
        from ..core.config import load_config
        config = load_config()
        
        # If auto_mode is True (from --auto flag), force enable auto-execution
        # Otherwise use config setting (defaults to True)
        if auto_mode:
            self.auto_execution_enabled = True
            # Log that --auto flag is forcing auto-execution
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"Auto-execution FORCED ENABLED by --auto flag (overriding config)",
                extra={"auto_mode": True, "auto_execution_enabled": True}
            )
        else:
            self.auto_execution_enabled = config.workflow.auto_execution_enabled if config.workflow.auto_execution_enabled is not None else True
        
        # Background Agent auto-executor removed - always use direct execution/Skills
        
        # Initialize marker writer for durable step completion tracking
        self.marker_writer = MarkerWriter(project_root=self.project_root)

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

    async def start(
        self,
        workflow: Workflow,
        user_prompt: str | None = None,
    ) -> WorkflowState:
        """
        Start a new workflow execution.
        
        Also executes state cleanup if configured for "on_startup" schedule.

        Args:
            workflow: Workflow to execute
            user_prompt: Optional user prompt for the workflow

        Returns:
            Initial workflow state
        """
        # Execute cleanup on startup if configured (Epic 12 - Story 12.6)
        if self.state_config_manager.config and self.state_config_manager.config.cleanup:
            if self.state_config_manager.config.cleanup.cleanup_schedule == "on_startup":
                cleanup_result = self.state_config_manager.execute_cleanup()
                if self.logger:
                    self.logger.info(
                        f"State cleanup on startup: {cleanup_result}",
                        cleanup_result=cleanup_result,
                    )
        
        self.workflow = workflow
        
        # Check workflow metadata for auto-execution override (per-workflow config)
        # If auto_mode is True (from --auto flag), force enable auto-execution
        if self.auto_mode:
            self.auto_execution_enabled_workflow = True
            if self.logger:
                self.logger.info(
                    "Auto-execution FORCED ENABLED for this workflow by --auto flag",
                    extra={
                        "auto_mode": True,
                        "auto_execution_enabled_workflow": True,
                        "auto_execution_enabled": self.auto_execution_enabled,
                    }
                )
        elif workflow.metadata and "auto_execution" in workflow.metadata:
            self.auto_execution_enabled_workflow = bool(workflow.metadata["auto_execution"])
            if self.logger:
                self.logger.info(
                    f"Auto-execution set from workflow metadata: {self.auto_execution_enabled_workflow}",
                    extra={
                        "auto_execution_enabled_workflow": self.auto_execution_enabled_workflow,
                        "auto_execution_enabled": self.auto_execution_enabled,
                    }
                )
        else:
            self.auto_execution_enabled_workflow = None  # Use global config
        
        # Background Agent auto-executor removed - always use direct execution/Skills
        
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

        # Generate and save execution plan (Epic 6 - Story 6.7)
        try:
            from .execution_plan import generate_execution_plan, save_execution_plan
            execution_plan = generate_execution_plan(workflow)
            state_dir = self._state_dir()
            plan_path = save_execution_plan(execution_plan, state_dir, workflow_id)
            if self.logger:
                self.logger.info(
                    f"Execution plan generated: {plan_path}",
                    execution_plan_path=str(plan_path),
                )
        except Exception as e:
            # Don't fail workflow start if execution plan generation fails
            if self.logger:
                self.logger.warning(f"Failed to generate execution plan: {e}")

        self.logger.info(
            "Workflow started",
            workflow_name=workflow.name,
            workflow_version=workflow.version,
            step_count=len(workflow.steps),
        )
        
        # Publish workflow started event (Phase 2)
        await self.event_bus.publish(
            WorkflowEvent(
                event_type=EventType.WORKFLOW_STARTED,
                workflow_id=workflow_id,
                step_id=None,
                data={
                    "workflow_name": workflow.name,
                    "workflow_version": workflow.version,
                    "step_count": len(workflow.steps),
                    "user_prompt": user_prompt or "",
                },
                timestamp=datetime.now(),
                correlation_id=workflow_id,
            )
        )
        
        # Initialize progress update manager
        self.progress_manager = ProgressUpdateManager(
            workflow=workflow,
            state=self.state,
            project_root=self.project_root,
            enable_updates=True,
        )
        # Connect event bus to status monitor (Phase 2)
        if self.progress_manager.status_monitor:
            self.progress_manager.status_monitor.event_bus = self.event_bus
        # Start progress monitoring (non-blocking)
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.progress_manager.start())
        except RuntimeError:
            # No running event loop - progress manager will start when event loop is available
            pass
        
        self.save_state()
        
        # Generate task manifest (Epic 7)
        self._generate_manifest()
        
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

        from .file_utils import atomic_write_json
        
        atomic_write_json(state_file, state_dict, indent=2)

        # Also save to history
        history_dir = state_file.parent / "history"
        history_dir.mkdir(exist_ok=True)
        history_file = history_dir / state_file.name
        atomic_write_json(history_file, state_dict, indent=2)
        
        # Generate task manifest (Epic 7)
        self._generate_manifest()

    def _generate_manifest(self) -> None:
        """
        Generate and save task manifest (Epic 7).
        
        Generates manifest on workflow start, step completion, and state save.
        """
        if not self.workflow or not self.state:
            return
        
        try:
            from .manifest import generate_manifest, save_manifest, sync_manifest_to_project_root
            
            # Generate manifest
            manifest_content = generate_manifest(self.workflow, self.state)
            
            # Save to state directory
            state_dir = self._state_dir()
            manifest_path = save_manifest(manifest_content, state_dir, self.state.workflow_id)
            
            # Optional: Sync to project root if configured
            sync_enabled = os.getenv("TAPPS_AGENTS_MANIFEST_SYNC", "false").lower() == "true"
            if sync_enabled:
                sync_path = sync_manifest_to_project_root(manifest_content, self.project_root)
                if self.logger:
                    self.logger.debug(
                        "Task manifest synced to project root",
                        manifest_path=str(manifest_path),
                        sync_path=str(sync_path),
                    )
            elif self.logger:
                self.logger.debug(
                    "Task manifest generated",
                    manifest_path=str(manifest_path),
                )
        except Exception as e:
            # Don't fail workflow if manifest generation fails
            if self.logger:
                self.logger.warning(
                    "Failed to generate task manifest",
                    error=str(e),
                )

    async def run(
        self,
        workflow: Workflow | None = None,
        target_file: str | None = None,
        max_steps: int = 100,
    ) -> WorkflowState:
        """
        Run workflow to completion with timeout protection.

        Args:
            workflow: Workflow to execute (if not already loaded)
            target_file: Optional target file path
            max_steps: Maximum number of steps to execute

        Returns:
            Final workflow state
        """
        from tapps_agents.core.config import load_config
        import asyncio
        from datetime import datetime
        
        config = load_config()
        # Use 2x step timeout for overall workflow timeout (default: 2 hours)
        workflow_timeout = getattr(config.workflow, 'timeout_seconds', 3600.0) * 2
        
        async def _run_workflow_inner() -> WorkflowState:
            """Inner function to wrap actual execution for timeout protection."""
            # Initialize execution
            target_path = await self._initialize_run(workflow, target_file)
            
            # Log workflow start
            start_time = datetime.now()
            if self.logger:
                self.logger.info(
                    "Starting workflow execution",
                    extra={
                        "workflow_id": self.state.workflow_id if self.state else None,
                        "workflow_name": workflow.name if workflow else (self.workflow.name if self.workflow else None),
                        "max_steps": max_steps,
                        "total_steps": len(workflow.steps) if workflow else (len(self.workflow.steps) if self.workflow else 0),
                        "workflow_timeout": workflow_timeout,
                    }
                )
            
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
                    self._handle_max_steps_exceeded(max_steps)
                    break

                # Find steps ready to execute (dependencies met)
                ready_steps = self._find_ready_steps(
                    completed_step_ids, running_step_ids
                )

                if not ready_steps:
                    if self._handle_no_ready_steps(completed_step_ids):
                        break
                    continue

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
                    should_break = await self._process_parallel_results(
                        results, completed_step_ids, running_step_ids
                    )
                    if should_break:
                        break

                    steps_executed += len(ready_steps)
                    self.save_state()
                    
                    # Generate task manifest after step completion (Epic 7)
                    self._generate_manifest()
                    
                    # Log progress every 10 steps
                    if steps_executed % 10 == 0 and self.logger:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        self.logger.info(
                            f"Workflow progress: {steps_executed} steps executed in {elapsed:.1f}s",
                            extra={
                                "steps_executed": steps_executed,
                                "completed_steps": len(completed_step_ids),
                                "total_steps": len(self.workflow.steps),
                                "elapsed_seconds": elapsed,
                            }
                        )

                except Exception as e:
                    self._handle_execution_error(e)
                    break

            return await self._finalize_run(completed_step_ids)
        
        # Wrap execution with timeout
        try:
            return await asyncio.wait_for(
                _run_workflow_inner(),
                timeout=workflow_timeout
            )
        except asyncio.TimeoutError:
            if self.state:
                self.state.status = "failed"
                self.state.error = f"Workflow timeout after {workflow_timeout}s"
                self.save_state()
                if self.logger:
                    self.logger.error(
                        f"Workflow execution exceeded {workflow_timeout}s timeout",
                        extra={
                            "workflow_id": self.state.workflow_id,
                            "timeout_seconds": workflow_timeout,
                        }
                    )
            raise TimeoutError(
                f"Workflow execution exceeded {workflow_timeout}s timeout. "
                f"Increase timeout in config (workflow.timeout_seconds) or check for blocking operations."
            )

    async def _initialize_run(
        self,
        workflow: Workflow | None,
        target_file: str | None,
    ) -> Path | None:
        """Initialize workflow execution with validation and return target path."""
        if workflow:
            self.workflow = workflow
        if not self.workflow:
            raise ValueError(
                "No workflow loaded. Call start() or pass workflow."
            )

        # Validate workflow has steps
        if not self.workflow.steps:
            raise ValueError("Workflow has no steps to execute")

        # Ensure we have a state
        if not self.state or not self.state.workflow_id.startswith(f"{self.workflow.id}-"):
            await self.start(workflow=self.workflow)

        # Validate first step can be executed (no dependencies)
        first_step = self.workflow.steps[0]
        if not first_step.requires:  # No dependencies
            # First step should always be ready
            if self.logger:
                self.logger.info(
                    f"First step {first_step.id} has no dependencies - ready to execute",
                    extra={
                        "step_id": first_step.id,
                        "agent": first_step.agent,
                        "action": first_step.action,
                    }
                )

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

        return target_path

    def _handle_max_steps_exceeded(self, max_steps: int) -> None:
        """Handle max steps exceeded."""
        self.state.status = "failed"
        self.state.error = f"Max steps exceeded ({max_steps}). Aborting."
        self.save_state()

    def get_workflow_health(self) -> dict[str, Any]:
        """
        Get workflow health diagnostics.
        
        Returns:
            Dictionary with workflow health information including:
            - status: Current workflow status
            - elapsed_seconds: Time since workflow started
            - completed_steps: Number of completed steps
            - total_steps: Total number of steps
            - progress_percent: Percentage of steps completed
            - time_since_last_step: Seconds since last step completed
            - is_stuck: Whether workflow appears to be stuck (no progress in 5 minutes)
            - current_step: Current step ID
            - error: Error message if any
        """
        if not self.state:
            return {"status": "not_started", "message": "Workflow not started"}
        
        elapsed = (
            (datetime.now() - self.state.started_at).total_seconds() 
            if self.state.started_at else 0
        )
        completed = len(self.state.completed_steps)
        total = len(self.workflow.steps) if self.workflow else 0
        
        # Check if stuck (no progress in last 5 minutes)
        last_step_time = None
        if self.state.step_executions:
            completed_times = [
                se.completed_at for se in self.state.step_executions 
                if se.completed_at
            ]
            if completed_times:
                last_step_time = max(completed_times)
        
        if not last_step_time:
            last_step_time = self.state.started_at
        
        time_since_last_step = (
            (datetime.now() - last_step_time).total_seconds() 
            if last_step_time else elapsed
        )
        is_stuck = time_since_last_step > 300  # 5 minutes
        
        return {
            "status": self.state.status,
            "elapsed_seconds": elapsed,
            "completed_steps": completed,
            "total_steps": total,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
            "time_since_last_step": time_since_last_step,
            "is_stuck": is_stuck,
            "current_step": self.state.current_step,
            "error": self.state.error,
        }

    def _find_ready_steps(
        self,
        completed_step_ids: set[str],
        running_step_ids: set[str],
    ) -> list[WorkflowStep]:
        """Find steps ready to execute (dependencies met)."""
        available_artifacts = set(self.state.artifacts.keys())
        return self.parallel_executor.find_ready_steps(
            workflow_steps=self.workflow.steps,
            completed_step_ids=completed_step_ids,
            running_step_ids=running_step_ids,
            available_artifacts=available_artifacts,
        )

    def _handle_no_ready_steps(self, completed_step_ids: set[str]) -> bool:
        """Handle case when no steps are ready with better diagnostics. Returns True if workflow should stop."""
        if len(completed_step_ids) >= len(self.workflow.steps):
            # Workflow is complete
            self.state.status = "completed"
            self.state.current_step = None
            self.save_state()
            return True
        else:
            # Workflow is blocked - provide diagnostics
            available_artifacts = set(self.state.artifacts.keys())
            pending_steps = [
                s for s in self.workflow.steps 
                if s.id not in completed_step_ids
            ]
            
            # Check what's blocking
            blocking_info = []
            for step in pending_steps:
                missing = [req for req in (step.requires or []) if req not in available_artifacts]
                if missing:
                    blocking_info.append(f"Step {step.id} ({step.agent}/{step.action}): missing {missing}")
            
            error_msg = (
                f"Workflow blocked: no ready steps and workflow not complete. "
                f"Completed: {len(completed_step_ids)}/{len(self.workflow.steps)}. "
                f"Blocking issues: {blocking_info if blocking_info else 'Unknown - check step dependencies'}"
            )
            
            self.state.status = "failed"
            self.state.error = error_msg
            self.save_state()
            
            # Log detailed diagnostics
            if self.logger:
                self.logger.error(
                    "Workflow blocked - no ready steps",
                    extra={
                        "completed_steps": list(completed_step_ids),
                        "pending_steps": [s.id for s in pending_steps],
                        "available_artifacts": list(available_artifacts),
                        "blocking_info": blocking_info,
                    }
                )
            
            return True

    async def _process_parallel_results(
        self,
        results: list[Any],
        completed_step_ids: set[str],
        running_step_ids: set[str],
    ) -> bool:
        """
        Process results from parallel execution.
        Returns True if workflow should stop (failed or aborted).
        """
        for result in results:
            step_logger = self.logger.with_context(
                step_id=result.step.id,
                agent=result.step.agent,
            ) if self.logger else None
            
            if result.error:
                should_break = await self._handle_step_error(
                    result, step_logger, completed_step_ids, running_step_ids
                )
                if should_break:
                    return True
                continue
            
            # Handle successful step completion
            await self._handle_step_success(
                result, step_logger, completed_step_ids, running_step_ids
            )
        
        return False

    async def _handle_step_error(
        self,
        result: Any,
        step_logger: Any,
        completed_step_ids: set[str],
        running_step_ids: set[str],
    ) -> bool:
        """Handle step error. Returns True if workflow should stop."""
        # Publish step failed event (Phase 2)
        await self.event_bus.publish(
            WorkflowEvent(
                event_type=EventType.STEP_FAILED,
                workflow_id=self.state.workflow_id,
                step_id=result.step.id,
                data={
                    "agent": result.step.agent,
                    "action": result.step.action,
                    "error": str(result.error),
                    "attempts": getattr(result, "attempts", 1),
                },
                timestamp=datetime.now(),
                correlation_id=f"{self.state.workflow_id}:{result.step.id}",
            )
        )
        
        # Step failed - use error recovery and auto-progression (Epic 14)
        error_context = ErrorContext(
            workflow_id=self.state.workflow_id,
            step_id=result.step.id,
            agent=result.step.agent,
            action=result.step.action,
            step_number=None,
            total_steps=len(self.workflow.steps),
            workflow_status=self.state.status,
        )
        
        # Handle error with recovery manager (Epic 14)
        recovery_result = None
        user_friendly_error = None
        if self.error_recovery:
            recovery_result = self.error_recovery.handle_error(
                error=result.error,
                context=error_context,
                attempt=getattr(result, "attempts", 1),
            )
            
            # Store user-friendly message (can't modify frozen dataclass)
            if recovery_result.get("user_message"):
                user_friendly_error = recovery_result["user_message"]
        
        if self.auto_progression.should_auto_progress():
            # Get review result if this was a reviewer step
            review_result = None
            if result.step.agent == "reviewer":
                review_result = self.state.variables.get("reviewer_result")
            
            decision = self.auto_progression.handle_step_completion(
                step=result.step,
                state=self.state,
                step_execution=result.step_execution,
                review_result=review_result,
            )
            
            if decision.action == ProgressionAction.RETRY:
                # Retry the step - remove from completed and add back to ready
                completed_step_ids.discard(result.step.id)
                running_step_ids.discard(result.step.id)
                # Apply backoff if specified
                if decision.metadata.get("backoff_seconds"):
                    await asyncio.sleep(decision.metadata["backoff_seconds"])
                if step_logger:
                    step_logger.info(
                        f"Retrying step {result.step.id} (attempt {decision.retry_count})",
                    )
                return False
            elif decision.action == ProgressionAction.SKIP:
                # Skip this step
                completed_step_ids.add(result.step.id)
                running_step_ids.discard(result.step.id)
                if result.step.id not in self.state.skipped_steps:
                    self.state.skipped_steps.append(result.step.id)
                if step_logger:
                    step_logger.warning(
                        f"Skipping step {result.step.id}: {decision.reason}",
                    )
                return False
            elif decision.action == ProgressionAction.ABORT:
                # Abort workflow
                self.state.status = "failed"
                self.state.error = decision.reason
                if step_logger:
                    step_logger.error(
                        f"Workflow aborted: {decision.reason}",
                    )
                
                # Publish workflow failed event (Phase 2)
                await self.event_bus.publish(
                    WorkflowEvent(
                        event_type=EventType.WORKFLOW_FAILED,
                        workflow_id=self.state.workflow_id,
                        step_id=result.step.id,
                        data={
                            "error": decision.reason,
                            "step_id": result.step.id,
                        },
                        timestamp=datetime.now(),
                        correlation_id=f"{self.state.workflow_id}:{result.step.id}",
                    )
                )
                
                self.save_state()
                if self.progress_manager:
                    await self.progress_manager.send_workflow_failed(decision.reason)
                    await self.progress_manager.stop()
                return True
            elif decision.action == ProgressionAction.CONTINUE:
                # Continue despite error (recoverable)
                completed_step_ids.add(result.step.id)
                running_step_ids.discard(result.step.id)
                if step_logger:
                    step_logger.warning(
                        f"Step {result.step.id} failed but continuing: {decision.reason}",
                    )
                return False
        
        # Fallback: mark as failed and stop workflow (if auto-progression disabled)
        # Use user-friendly error message if available
        error_message = user_friendly_error if user_friendly_error else str(result.error)
        self.state.status = "failed"
        self.state.error = f"Step {result.step.id} failed: {error_message}"
        if step_logger:
            step_logger.error(
                "Step execution failed",
                error=error_message,
                action=result.step.action,
            )
        
        # Publish workflow failed event (Phase 2)
        await self.event_bus.publish(
            WorkflowEvent(
                event_type=EventType.WORKFLOW_FAILED,
                workflow_id=self.state.workflow_id,
                step_id=result.step.id,
                data={
                    "error": error_message,
                    "step_id": result.step.id,
                },
                timestamp=datetime.now(),
                correlation_id=f"{self.state.workflow_id}:{result.step.id}",
            )
        )
        
        self.save_state()
        
        # Send failure update
        if self.progress_manager:
            await self.progress_manager.send_workflow_failed(
                error_message
            )
            await self.progress_manager.stop()
        return True

    async def _handle_step_success(
        self,
        result: Any,
        step_logger: Any,
        completed_step_ids: set[str],
        running_step_ids: set[str],
    ) -> None:
        """Handle successful step completion."""
        # Mark step as completed
        completed_step_ids.add(result.step.id)
        running_step_ids.discard(result.step.id)
        
        # Get review result if this was a reviewer step (for gate evaluation)
        review_result = None
        if result.step.agent == "reviewer":
            review_result = self.state.variables.get("reviewer_result")
        
        # Publish step completed event (Phase 2)
        await self.event_bus.publish(
            WorkflowEvent(
                event_type=EventType.STEP_COMPLETED,
                workflow_id=self.state.workflow_id,
                step_id=result.step.id,
                data={
                    "agent": result.step.agent,
                    "action": result.step.action,
                    "duration_seconds": result.step_execution.duration_seconds,
                    "artifact_count": len(result.artifacts) if result.artifacts else 0,
                },
                timestamp=datetime.now(),
                correlation_id=f"{self.state.workflow_id}:{result.step.id}",
            )
        )
        
        # Publish artifact created events (Phase 2)
        if result.artifacts:
            for artifact_name, artifact_data in result.artifacts.items():
                await self.event_bus.publish(
                    WorkflowEvent(
                        event_type=EventType.ARTIFACT_CREATED,
                        workflow_id=self.state.workflow_id,
                        step_id=result.step.id,
                        data={
                            "artifact_name": artifact_name,
                            "artifact_path": artifact_data.get("path", ""),
                            "created_by": result.step.id,
                        },
                        timestamp=datetime.now(),
                        correlation_id=f"{self.state.workflow_id}:{result.step.id}",
                    )
                )
        
        # Use auto-progression to handle step completion and gate evaluation
        if self.auto_progression.should_auto_progress():
            decision = self.auto_progression.handle_step_completion(
                step=result.step,
                state=self.state,
                step_execution=result.step_execution,
                review_result=review_result,
            )
            
            # Update current step based on gate decision if needed
            if decision.next_step_id:
                self.state.current_step = decision.next_step_id
            
            if step_logger:
                step_logger.info(
                    f"Step completed: {decision.reason}",
                    action=result.step.action,
                    duration_seconds=result.step_execution.duration_seconds,
                    artifact_count=len(result.artifacts) if result.artifacts else 0,
                    next_step=decision.next_step_id,
                )
        else:
            if step_logger:
                step_logger.info(
                    "Step completed",
                    action=result.step.action,
                    duration_seconds=result.step_execution.duration_seconds,
                    artifact_count=len(result.artifacts) if result.artifacts else 0,
                )
        
        # Send step completed update (Epic 11: Include gate result for quality dashboard)
        is_gate_step = result.step.agent == "reviewer" and result.step.gate is not None
        if self.progress_manager:
            # Extract gate result if this was a reviewer step
            gate_result = None
            if result.step.agent == "reviewer" and review_result:
                # Get gate result from state variables (set by auto-progression)
                gate_last = self.state.variables.get("gate_last", {})
                if gate_last:
                    gate_result = gate_last
                    
                    # Publish gate evaluated event (Phase 2)
                    await self.event_bus.publish(
                        WorkflowEvent(
                            event_type=EventType.GATE_EVALUATED,
                            workflow_id=self.state.workflow_id,
                            step_id=result.step.id,
                            data={
                                "gate_result": gate_result,
                                "passed": gate_result.get("passed", False),
                            },
                            timestamp=datetime.now(),
                            correlation_id=f"{self.state.workflow_id}:{result.step.id}",
                        )
                    )
            
            await self.progress_manager.send_step_completed(
                step_id=result.step.id,
                agent=result.step.agent,
                action=result.step.action,
                duration=result.step_execution.duration_seconds,
                gate_result=gate_result,
            )
        
        # Epic 12: Automatic checkpointing after step completion
        if self.checkpoint_manager.should_checkpoint(
            step=result.step,
            state=self.state,
            is_gate_step=is_gate_step,
        ):
            # Enhance state with checkpoint metadata before saving
            checkpoint_metadata = self.checkpoint_manager.get_checkpoint_metadata(
                state=self.state,
                step=result.step,
            )
            # Store metadata in state variables for persistence
            if "_checkpoint_metadata" not in self.state.variables:
                self.state.variables["_checkpoint_metadata"] = {}
            self.state.variables["_checkpoint_metadata"].update(checkpoint_metadata)
            
            # Save checkpoint
            self.save_state()
            self.checkpoint_manager.record_checkpoint(result.step.id)
            
            if self.logger:
                self.logger.info(
                    f"Checkpoint created after step {result.step.id}",
                    checkpoint_metadata=checkpoint_metadata,
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

    def _handle_execution_error(self, error: Exception) -> None:
        """Handle execution error."""
        self.state.status = "failed"
        self.state.error = str(error)
        if self.logger:
            self.logger.error(
                "Workflow execution failed",
                error=str(error),
                exc_info=True,
            )
        self.save_state()

    async def _finalize_run(self, completed_step_ids: set[str]) -> WorkflowState:
        """Finalize workflow execution and return final state."""
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
            
            # Publish workflow completed event (Phase 2)
            await self.event_bus.publish(
                WorkflowEvent(
                    event_type=EventType.WORKFLOW_COMPLETED,
                    workflow_id=self.state.workflow_id,
                    step_id=None,
                    data={
                        "completed_steps": len(completed_step_ids),
                        "total_steps": len(self.workflow.steps) if self.workflow else 0,
                    },
                    timestamp=datetime.now(),
                    correlation_id=self.state.workflow_id,
                )
            )
            
            self.save_state()
            
            # Send completion summary
            if self.progress_manager:
                await self.progress_manager.send_workflow_completed()
                await self.progress_manager.stop()

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

        # Publish step started event (Phase 2)
        await self.event_bus.publish(
            WorkflowEvent(
                event_type=EventType.STEP_STARTED,
                workflow_id=self.state.workflow_id,
                step_id=step.id,
                data={
                    "agent": agent_name,
                    "action": action,
                    "step_id": step.id,
                },
                timestamp=datetime.now(),
                correlation_id=f"{self.state.workflow_id}:{step.id}",
            )
        )

        # Handle completion/finalization steps that don't require agent execution
        if agent_name == "orchestrator" and action in ["finalize", "complete"]:
            # Return empty artifacts for completion steps
            return {}

        # Track step start time for duration calculation
        step_started_at = datetime.now()
        
        # Use context manager for worktree lifecycle (guaranteed cleanup)
        async with self._worktree_context(step) as worktree_path:
            worktree_name = self._worktree_name_for_step(step.id)
            
            # Background Agent auto-execution removed - always use skill_invoker
            try:
                # Invoke Skill via SkillInvoker (direct execution or Cursor Skills)
                from ..core.unicode_safe import safe_print
                safe_print(f"\n[EXEC] Executing {agent_name}/{action}...", flush=True)
                await self.skill_invoker.invoke_skill(
                        agent_name=agent_name,
                        action=action,
                        step=step,
                        target_path=target_path,
                        worktree_path=worktree_path,
                        state=self.state,
                    )
                # Skill invoker handles execution (direct execution or Cursor Skills)
                # Artifacts are extracted after completion

                # Extract artifacts from worktree
                    artifacts = await self.worktree_manager.extract_artifacts(
                        worktree_path=worktree_path,
                        step=step,
                    )

                    # Convert artifacts to dict format
                    artifacts_dict: dict[str, dict[str, Any]] = {}
                    found_artifact_paths = []
                    for artifact in artifacts:
                        artifacts_dict[artifact.name] = {
                            "name": artifact.name,
                            "path": artifact.path,
                            "status": artifact.status,
                            "created_by": artifact.created_by,
                            "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
                            "metadata": artifact.metadata or {},
                        }
                        found_artifact_paths.append(artifact.path)

                    # Write DONE marker for successful completion
                    step_completed_at = datetime.now()
                    duration = (step_completed_at - step_started_at).total_seconds()
                    
                    marker_path = self.marker_writer.write_done_marker(
                        workflow_id=self.state.workflow_id,
                        step_id=step.id,
                        agent=agent_name,
                        action=action,
                        worktree_name=worktree_name,
                        worktree_path=str(worktree_path),
                        expected_artifacts=step.creates or [],
                        found_artifacts=found_artifact_paths,
                        duration_seconds=duration,
                        started_at=step_started_at,
                        completed_at=step_completed_at,
                    )
                    
                    if self.logger:
                        self.logger.debug(
                            f"DONE marker written for step {step.id}",
                            marker_path=str(marker_path),
                        )

                    # Worktree cleanup is handled by context manager
                    return artifacts_dict if artifacts_dict else None
                
            except (TimeoutError, RuntimeError) as e:
                # Write FAILED marker for timeout or execution errors
                step_failed_at = datetime.now()
                duration = (step_failed_at - step_started_at).total_seconds()
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Try to get completion status if available (for missing artifacts)
                found_artifact_paths = []
                try:
                    from .cursor_skill_helper import check_skill_completion
                    completion_status = check_skill_completion(
                        worktree_path=worktree_path,
                        expected_artifacts=step.creates or [],
                    )
                    found_artifact_paths = completion_status.get("found_artifacts", [])
                except Exception:
                    pass
                
                marker_path = self.marker_writer.write_failed_marker(
                    workflow_id=self.state.workflow_id,
                    step_id=step.id,
                    agent=agent_name,
                    action=action,
                    error=error_msg,
                    worktree_name=worktree_name,
                    worktree_path=str(worktree_path),
                    expected_artifacts=step.creates or [],
                    found_artifacts=found_artifact_paths,
                    duration_seconds=duration,
                    started_at=step_started_at,
                    failed_at=step_failed_at,
                    error_type=error_type,
                    metadata={
                        "marker_location": f".tapps-agents/workflows/markers/{self.state.workflow_id}/step-{step.id}/FAILED.json",
                    },
                )
                
                if self.logger:
                    self.logger.warning(
                        f"FAILED marker written for step {step.id}",
                        marker_path=str(marker_path),
                        error=error_msg,
                    )
                
                # Include marker location in error message for better troubleshooting
                from ..core.unicode_safe import safe_print
                safe_print(
                    f"\n[INFO] Failure marker written to: {marker_path}",
                    flush=True,
                )
                
                # Re-raise the exception
                raise
            except Exception as e:
                # Write FAILED marker for unexpected errors
                step_failed_at = datetime.now()
                duration = (step_failed_at - step_started_at).total_seconds()
                error_type = type(e).__name__
                error_msg = str(e)
                
                marker_path = self.marker_writer.write_failed_marker(
                    workflow_id=self.state.workflow_id,
                    step_id=step.id,
                    agent=agent_name,
                    action=action,
                    error=error_msg,
                    worktree_name=worktree_name,
                    worktree_path=str(worktree_path) if 'worktree_path' in locals() else None,
                    expected_artifacts=step.creates or [],
                    found_artifacts=[],
                    duration_seconds=duration,
                    started_at=step_started_at,
                    failed_at=step_failed_at,
                    error_type=error_type,
                    metadata={
                        "marker_location": f".tapps-agents/workflows/markers/{self.state.workflow_id}/step-{step.id}/FAILED.json",
                    },
                )
                
                if self.logger:
                    self.logger.error(
                        f"FAILED marker written for step {step.id} (unexpected error)",
                        marker_path=str(marker_path),
                        error=error_msg,
                        exc_info=True,
                    )
                
                # Re-raise the exception
                raise

    @asynccontextmanager
    async def _worktree_context(
        self, step: WorkflowStep
    ) -> AsyncIterator[Path]:
        """
        Context manager for worktree lifecycle management.
        
        Ensures worktree is properly cleaned up even on cancellation or exceptions.
        This is a 2025 best practice for resource management in async code.
        
        Args:
            step: Workflow step that needs a worktree
            
        Yields:
            Path to the worktree
            
        Example:
            async with self._worktree_context(step) as worktree_path:
                # Use worktree_path here
                # Worktree automatically cleaned up on exit
        """
        worktree_name = self._worktree_name_for_step(step.id)
        worktree_path: Path | None = None
        
        try:
            # Create worktree
            worktree_path = await self.worktree_manager.create_worktree(
                worktree_name=worktree_name
            )
            
            # Copy artifacts from previous steps to worktree
            artifacts_list = list(self.state.artifacts.values())
            await self.worktree_manager.copy_artifacts(
                worktree_path=worktree_path,
                artifacts=artifacts_list,
            )
            
            # Yield worktree path
            yield worktree_path
            
        finally:
            # Always cleanup, even on cancellation or exception
            if worktree_path:
                try:
                    # Determine if we should delete the branch based on configuration
                    from ..core.config import load_config
                    config = load_config()
                    should_delete = (
                        config.workflow.branch_cleanup.delete_branches_on_cleanup
                        if (
                            config.workflow.branch_cleanup
                            and config.workflow.branch_cleanup.enabled
                        )
                        else True  # Default to True for backward compatibility (same as parameter default)
                    )
                    await self.worktree_manager.remove_worktree(
                        worktree_name, delete_branch=should_delete
                    )
                except Exception as e:
                    # Log but don't raise - cleanup failures shouldn't break workflow
                    if self.logger:
                        self.logger.warning(
                            f"Failed to cleanup worktree {worktree_name}: {e}",
                            step_id=step.id,
                        )

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
                    from ..core.unicode_safe import safe_print
                    safe_print(f"[OK] {agent_name}/{action} completed - found artifacts: {completion_status['found_artifacts']}")
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
                # Determine if we should delete the branch based on configuration
                from ..core.config import load_config
                config = load_config()
                should_delete = (
                    config.workflow.branch_cleanup.delete_branches_on_cleanup
                    if (
                        config.workflow.branch_cleanup
                        and config.workflow.branch_cleanup.enabled
                    )
                    else True  # Default to True for backward compatibility
                )
                await self.worktree_manager.remove_worktree(
                    worktree_name, delete_branch=should_delete
                )
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
    
    def _get_step_params(self, step: WorkflowStep, target_path: Path | None) -> dict[str, Any]:
        """
        Extract parameters for step execution.
        
        Args:
            step: Workflow step
            target_path: Optional target file path
            
        Returns:
            Dictionary of parameters for command building
        """
        params: dict[str, Any] = {}
        
        # Add target file if provided
        if target_path:
            params["target_file"] = str(target_path.relative_to(self.project_root))
        
        # Add step metadata
        if step.metadata:
            params.update(step.metadata)
        
        # Add workflow variables
        if self.state and self.state.variables:
            # Include relevant variables (avoid exposing everything)
            if "user_prompt" in self.state.variables:
                params["user_prompt"] = self.state.variables["user_prompt"]
            if "target_file" in self.state.variables:
                params["target_file"] = self.state.variables["target_file"]
        
        return params

    def _advance_step(self) -> None:
        """Advance to the next workflow step."""
        if not self.workflow or not self.state:
            return

        # Use auto-progression if enabled
        if self.auto_progression.should_auto_progress():
            current_step = self.get_current_step()
            if current_step:
                # Get progression decision
                step_execution = next(
                    (se for se in self.state.step_executions if se.step_id == current_step.id),
                    None
                )
                if step_execution:
                    review_result = None
                    if current_step.agent == "reviewer":
                        review_result = self.state.variables.get("reviewer_result")
                    
                    decision = self.auto_progression.handle_step_completion(
                        step=current_step,
                        state=self.state,
                        step_execution=step_execution,
                        review_result=review_result,
                    )
                    
                    next_step_id = self.auto_progression.get_next_step_id(
                        step=current_step,
                        decision=decision,
                        workflow_steps=self.workflow.steps,
                    )
                    
                    if next_step_id:
                        self.state.current_step = next_step_id
                    else:
                        # Workflow complete
                        self.state.status = "completed"
                        self.state.completed_at = datetime.now()
                        self.state.current_step = None
                    return

        # Fallback to sequential progression
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

    def get_progression_status(self) -> dict[str, Any]:
        """
        Get current progression status and visibility information.
        
        Returns:
            Dictionary with progression status
        """
        if not self.workflow or not self.state:
            return {"status": "not_started"}
        
        return self.auto_progression.get_progression_status(
            state=self.state,
            workflow_steps=self.workflow.steps,
        )

    def get_progression_history(self, step_id: str | None = None) -> list[dict[str, Any]]:
        """
        Get progression history.
        
        Args:
            step_id: Optional step ID to filter by
            
        Returns:
            List of progression history entries
        """
        history = self.auto_progression.get_progression_history(step_id=step_id)
        return [
            {
                "step_id": h.step_id,
                "timestamp": h.timestamp.isoformat(),
                "action": h.action.value,
                "reason": h.reason,
                "gate_result": h.gate_result,
                "metadata": h.metadata,
            }
            for h in history
        ]

    def pause_workflow(self) -> None:
        """
        Pause workflow execution.
        
        Epic 10: Progression Control
        """
        if not self.state:
            raise ValueError("Workflow not started")
        
        if self.state.status == "running":
            self.state.status = "paused"
            self.save_state()
            if self.logger:
                self.logger.info("Workflow paused by user")
            self.auto_progression.record_progression(
                step_id=self.state.current_step or "unknown",
                action=ProgressionAction.PAUSE,
                reason="Workflow paused by user",
            )

    def resume_workflow(self) -> None:
        """
        Resume paused workflow execution.
        
        Epic 10: Progression Control
        """
        if not self.state:
            raise ValueError("Workflow not started")
        
        if self.state.status == "paused":
            self.state.status = "running"
            self.save_state()
            if self.logger:
                self.logger.info("Workflow resumed by user")
            self.auto_progression.record_progression(
                step_id=self.state.current_step or "unknown",
                action=ProgressionAction.CONTINUE,
                reason="Workflow resumed by user",
            )

    def skip_step(self, step_id: str | None = None) -> None:
        """
        Skip a workflow step.
        
        Args:
            step_id: Step ID to skip (defaults to current step)
        
        Epic 10: Progression Control
        """
        if not self.state or not self.workflow:
            raise ValueError("Workflow not started")
        
        step_id = step_id or self.state.current_step
        if not step_id:
            raise ValueError("No step to skip")
        
        # Find the step
        step = next((s for s in self.workflow.steps if s.id == step_id), None)
        if not step:
            raise ValueError(f"Step {step_id} not found")
        
        # Record skip in progression history
        self.auto_progression.record_progression(
            step_id=step_id,
            action=ProgressionAction.SKIP,
            reason="Step skipped by user",
        )
        
        # Advance to next step
        if step.next:
            self.state.current_step = step.next
            self.save_state()
            if self.logger:
                self.logger.info(f"Step {step_id} skipped, advancing to {step.next}")
        else:
            # No next step - workflow complete
            self.state.status = "completed"
            self.state.completed_at = datetime.now()
            self.state.current_step = None
            self.save_state()
            if self.logger:
                self.logger.info(f"Step {step_id} skipped, workflow completed")

