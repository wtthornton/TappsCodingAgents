"""
Workflow Executor - Execute YAML workflow definitions.
"""

import json
import os
import shutil
import subprocess  # nosec B404 - fixed args, no shell
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.error_envelope import ErrorEnvelopeBuilder
from ..core.runtime_mode import is_cursor_mode
from ..quality.quality_gates import QualityGate, QualityThresholds
from .event_log import WorkflowEventLog
from .logging_helper import WorkflowLogger
from .models import Artifact, StepExecution, Workflow, WorkflowState, WorkflowStep
from .parallel_executor import ParallelStepExecutor
from .parser import WorkflowParser
from .progress_monitor import WorkflowProgressMonitor
from .recommender import WorkflowRecommendation, WorkflowRecommender
from .state_manager import AdvancedStateManager
from .timeline import generate_timeline, save_timeline


class WorkflowExecutor:
    """Executor for workflow definitions."""

    def __init__(
        self,
        project_root: Path | None = None,
        expert_registry: Any | None = None,
        auto_detect: bool = True,
        advanced_state: bool = True,
        auto_mode: bool = False,
    ):
        """
        Initialize workflow executor.

        Args:
            project_root: Root directory for the project
            expert_registry: Optional ExpertRegistry instance for expert consultation
            auto_detect: Whether to enable automatic workflow detection and recommendation
            advanced_state: Whether to use advanced state management (validation, migration, recovery)
            auto_mode: Whether to run in fully automated mode (no prompts)
        """
        self.project_root = project_root or Path.cwd()
        self.state: WorkflowState | None = None
        self.workflow: Workflow | None = None
        self._workflow_path: Path | None = None
        self.expert_registry = expert_registry
        self.auto_detect = auto_detect
        self.advanced_state = advanced_state
        self.auto_mode = auto_mode
        self.user_prompt: str | None = None
        self.recommender: WorkflowRecommender | None = None
        self.state_manager: AdvancedStateManager | None = None
        self.parallel_executor = ParallelStepExecutor(max_parallel=8, default_timeout_seconds=3600.0)
        self.logger: WorkflowLogger | None = None  # Initialized in start() with workflow_id

        # Initialize advanced state manager if enabled
        if self.advanced_state:
            state_dir = self._state_dir()
            self.state_manager = AdvancedStateManager(state_dir, compression=False)
        else:
            self.state_manager = None

        # Initialize event log
        state_dir = self._state_dir()
        events_dir = state_dir / "events"
        self.event_log = WorkflowEventLog(events_dir)

        if auto_detect:
            self.recommender = WorkflowRecommender(
                project_root=self.project_root,
                workflows_dir=self.project_root / "workflows",
            )

    def recommend_workflow(
        self,
        user_query: str | None = None,
        file_count: int | None = None,
        scope_description: str | None = None,
    ) -> WorkflowRecommendation:
        """
        Recommend a workflow based on project characteristics.

        Args:
            user_query: User's query or request
            file_count: Estimated number of files to change
            scope_description: Description of the change scope

        Returns:
            WorkflowRecommendation with recommendation details

        Raises:
            ValueError: If auto_detect is disabled
        """
        if not self.auto_detect or not self.recommender:
            raise ValueError(
                "Auto-detection is disabled. Enable auto_detect in __init__ or use load_workflow()"
            )

        return self.recommender.recommend(
            user_query=user_query,
            file_count=file_count,
            scope_description=scope_description,
            auto_load=True,
        )

    def load_workflow(self, workflow_path: Path) -> Workflow:
        """
        Load a workflow from file.

        Args:
            workflow_path: Path to workflow YAML file

        Returns:
            Loaded Workflow object
        """
        self._workflow_path = workflow_path
        self.workflow = WorkflowParser.parse_file(workflow_path)
        return self.workflow

    def start(self, workflow: Workflow | None = None) -> WorkflowState:
        """
        Start workflow execution.

        Args:
            workflow: Workflow to execute (if not already loaded)

        Returns:
            Initial workflow state
        """
        if workflow:
            self.workflow = workflow

        if not self.workflow:
            raise ValueError("No workflow loaded. Call load_workflow() first.")

        # Use consistent workflow_id format: {workflow.id}-{timestamp}
        # This matches CursorWorkflowExecutor format for consistency
        # For tests, preserve original ID if TAPPS_AGENTS_PRESERVE_WORKFLOW_ID is set
        if os.getenv("TAPPS_AGENTS_PRESERVE_WORKFLOW_ID", "false").lower() == "true":
            workflow_id = self.workflow.id
        else:
            workflow_id = f"{self.workflow.id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Initialize logger with workflow_id for correlation and trace context
        # Check for structured logging config
        structured_logging = os.getenv("TAPPS_AGENTS_STRUCTURED_LOGGING", "false").lower() == "true"
        self.logger = WorkflowLogger(
            workflow_id=workflow_id,
            structured_output=structured_logging,
        )

        self.state = WorkflowState(
            workflow_id=workflow_id,
            started_at=datetime.now(),
            current_step=self.workflow.steps[0].id if self.workflow.steps else None,
            status="running",
        )

        # Store user prompt if provided
        if self.user_prompt:
            self.state.variables["user_prompt"] = self.user_prompt

        # Persist workflow path for resumption
        if self._workflow_path:
            self.state.variables["_workflow_path"] = str(self._workflow_path)

        self.logger.info(
            "Workflow started",
            workflow_name=self.workflow.name,
            workflow_version=self.workflow.version,
            step_count=len(self.workflow.steps),
        )

        # Emit workflow_start event
        self.event_log.emit_event(
            event_type="workflow_start",
            workflow_id=workflow_id,
            status="running",
            metadata={
                "workflow_name": self.workflow.name,
                "workflow_version": self.workflow.version,
                "step_count": len(self.workflow.steps),
            },
        )

        self.save_state()

        return self.state

    @staticmethod
    def _normalize_action(action: str) -> str:
        return action.replace("-", "_").strip().lower()

    def _default_target_file(self) -> Path | None:
        """
        Best-effort default target selection for demos.

        For `workflow hotfix` / quick-start docs, we default to `example_bug.py` if present.
        """
        candidate = self.project_root / "example_bug.py"
        return candidate if candidate.exists() else None

    def _capture_python_exception(
        self, file_path: Path
    ) -> tuple[str | None, str | None]:
        """
        Run a python file and capture its exception output (best-effort).

        Returns:
            (error_message, stack_trace)
        """
        try:
            result = subprocess.run(  # nosec B603 - fixed args, no shell
                [sys.executable, str(file_path)],
                capture_output=True,
                text=True,
                cwd=str(file_path.parent),
                timeout=30,
                check=False,
            )
            stderr = (result.stderr or "").strip()
            if not stderr:
                return None, None

            # Heuristic: last non-empty line is typically "XError: msg"
            lines = [ln for ln in stderr.splitlines() if ln.strip()]
            error_message = lines[-1] if lines else None
            return error_message, stderr
        except Exception:
            return None, None

    async def execute(
        self,
        workflow: Workflow | None = None,
        target_file: str | None = None,
        max_steps: int = 50,
    ) -> WorkflowState:
        """
        Execute a workflow end-to-end.

        Why this exists:
        - `start()` only initializes/persists workflow state.
        - The original CLI called `start()` and then stopped, leaving status as "running".

        This method runs the current step, records artifacts, advances to next,
        and repeats until completion/failure.
        
        If running in Cursor mode, delegates to CursorWorkflowExecutor.
        """
        # Route to Cursor executor if in Cursor mode
        if is_cursor_mode():
            from .cursor_executor import CursorWorkflowExecutor
            
            cursor_executor = CursorWorkflowExecutor(
                project_root=self.project_root,
                expert_registry=self.expert_registry,
                auto_mode=self.auto_mode,
            )
            
            # Load workflow if provided
            if workflow:
                cursor_executor.workflow = workflow
            elif self.workflow:
                cursor_executor.workflow = self.workflow
            else:
                raise ValueError(
                    "No workflow loaded. Call load_workflow() or pass workflow."
                )
            
            # Start workflow if needed
            if not cursor_executor.state:
                user_prompt = self.user_prompt or self.state.variables.get("user_prompt") if self.state else None
                cursor_executor.start(workflow=cursor_executor.workflow, user_prompt=user_prompt)
            
            # Execute workflow
            return await cursor_executor.run(
                workflow=None,  # Already loaded
                target_file=target_file,
                max_steps=max_steps,
            )
        
        # Continue with original MAL-based execution for headless mode
        if workflow:
            self.workflow = workflow
        if not self.workflow:
            raise ValueError(
                "No workflow loaded. Call load_workflow() or pass workflow."
            )

        # Ensure we have a state
        if not self.state or self.state.workflow_id != self.workflow.id:
            self.start(workflow=self.workflow)

        # Establish target file (best-effort for demo workflows)
        target_path: Path | None
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
                # Emit workflow_end event
                self.event_log.emit_event(
                    event_type="workflow_end",
                    workflow_id=self.state.workflow_id,
                    status="failed",
                    error=self.state.error,
                )
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
                    # Emit workflow_end event
                    self.event_log.emit_event(
                        event_type="workflow_end",
                        workflow_id=self.state.workflow_id,
                        status="completed",
                    )
                    self.save_state()
                    break
                else:
                    # Workflow is blocked (dependencies not met)
                    self.state.status = "failed"
                    self.state.error = "Workflow blocked: no ready steps and workflow not complete"
                    # Emit workflow_end event
                    self.event_log.emit_event(
                        event_type="workflow_end",
                        workflow_id=self.state.workflow_id,
                        status="failed",
                        error=self.state.error,
                    )
                    self.save_state()
                    break

            # Execute ready steps in parallel
            running_step_ids.update(step.id for step in ready_steps)
            
            # Emit step_start events
            for step in ready_steps:
                self.event_log.emit_event(
                    event_type="step_start",
                    workflow_id=self.state.workflow_id,
                    step_id=step.id,
                    agent=step.agent,
                    action=step.action,
                    status="running",
                )
            
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
                        # Step failed - emit event and mark as failed
                        self.event_log.emit_event(
                            event_type="step_fail",
                            workflow_id=self.state.workflow_id,
                            step_id=result.step.id,
                            agent=result.step.agent,
                            action=result.step.action,
                            status="failed",
                            error=str(result.error),
                        )
                        # Mark as failed and stop workflow
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
                    
                    # Prepare artifact summaries for event
                    artifact_summaries = {}
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
                                artifact_summaries[artifact.name] = {
                                    "path": artifact.path,
                                    "status": artifact.status,
                                }
                    
                    # Emit step_finish event
                    self.event_log.emit_event(
                        event_type="step_finish",
                        workflow_id=self.state.workflow_id,
                        step_id=result.step.id,
                        agent=result.step.agent,
                        action=result.step.action,
                        status="completed",
                        artifacts=artifact_summaries,
                    )
                    
                    if step_logger:
                        step_logger.info(
                            "Step completed",
                            action=result.step.action,
                            duration_seconds=result.step_execution.duration_seconds,
                            artifact_count=len(result.artifacts) if result.artifacts else 0,
                        )
                    
                    # Handle gate evaluation for reviewer steps
                    if result.step.agent == "reviewer" and result.step.gate:
                        gate = result.step.gate
                        gate_last = self.state.variables.get("gate_last", {})
                        if gate_last.get("step") == result.step.id:
                            passed = gate_last.get("passed", False)
                            on_pass = gate.get("on_pass") or gate.get("on-pass")
                            on_fail = gate.get("on_fail") or gate.get("on-fail")
                            
                            # Update current step based on gate result
                            if passed and on_pass:
                                self.state.current_step = on_pass
                            elif (not passed) and on_fail:
                                self.state.current_step = on_fail
                            
                            # Note: Gate-based step advancement handled in next iteration
                            # when finding ready steps

                steps_executed += len(ready_steps)
                self.save_state()

            except Exception as e:
                self.state.status = "failed"
                envelope = ErrorEnvelopeBuilder.from_exception(
                    e,
                    workflow_id=self.state.workflow_id,
                )
                self.state.error = envelope.to_user_message()
                # Emit workflow_end event
                self.event_log.emit_event(
                    event_type="workflow_end",
                    workflow_id=self.state.workflow_id,
                    status="failed",
                    error=str(e),
                )
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
        
        # Generate timeline if workflow completed
        if self.state.status == "completed" and self.workflow:
            if self.logger:
                self.logger.info(
                    "Workflow completed",
                    completed_steps=len(completed_step_ids),
                    total_steps=len(self.workflow.steps),
                )
            try:
                timeline = generate_timeline(self.state, self.workflow)
                timeline_path = self.project_root / "project-timeline.md"
                save_timeline(timeline, timeline_path, format="markdown")
                print(f"\nTimeline saved to: {timeline_path}")
            except Exception as e:
                print(f"Warning: Failed to generate timeline: {e}", file=sys.stderr)
        
        return self.state

    async def _execute_step_for_parallel(
        self, step: WorkflowStep, target_path: Path | None
    ) -> dict[str, dict[str, Any]] | None:
        """
        Execute a single workflow step and return artifacts (for parallel execution).
        
        This is similar to _execute_step but returns artifacts instead of updating state.
        State updates (step_execution tracking) are handled by ParallelStepExecutor.
        """
        if not self.state or not self.workflow:
            raise ValueError("Workflow not started")

        action = self._normalize_action(step.action)
        agent_name = (step.agent or "").strip().lower()

        # ---- Helper: dynamic agent import + run ----
        async def run_agent(agent: str, command: str, **kwargs: Any) -> dict[str, Any]:
            module = __import__(f"tapps_agents.agents.{agent}.agent", fromlist=["*"])
            class_name = f"{agent.title()}Agent"
            agent_cls = getattr(module, class_name)
            instance = agent_cls()
            await instance.activate(self.project_root)
            try:
                return await instance.run(command, **kwargs)
            finally:
                # Close agent if it has a close method
                if hasattr(instance, 'close'):
                    await instance.close()

        created_artifacts: list[dict[str, Any]] = []

        try:
            # ---- Step execution mappings (same as _execute_step) ----
            if agent_name == "debugger" and action in {
                "analyze_error",
                "analyze-error",
                "analyze",
            }:
                if not target_path or not target_path.exists():
                    raise ValueError(
                        "Debugger step requires a target file. Provide --file <path> (or ensure example_bug.py exists)."
                    )

                error_message, stack_trace = self._capture_python_exception(target_path)
                if not error_message:
                    error_message = f"Bug(s) reported in {target_path.name} (no runtime traceback captured)."

                debug_result = await run_agent(
                    "debugger",
                    "analyze-error",
                    error_message=error_message,
                    stack_trace=stack_trace,
                )
                self.state.variables["debugger_result"] = debug_result

                if "debug-report.md" in (step.creates or []):
                    report_path = self.project_root / "debug-report.md"
                    report_lines = [
                        "# Debug Report",
                        "",
                        f"## Target: `{target_path}`",
                        "",
                        "## Error message",
                        "```",
                        error_message or "",
                        "```",
                    ]
                    if stack_trace:
                        report_lines += ["", "## Stack trace", "```", stack_trace, "```"]
                    report_lines += [
                        "",
                        "## Analysis (DebuggerAgent)",
                        "```json",
                        json.dumps(debug_result, indent=2),
                        "```",
                    ]
                    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
                    created_artifacts.append(
                        {"name": "debug-report.md", "path": str(report_path)}
                    )

            elif agent_name == "implementer" and action in {
                "write_code",
                "fix",
                "implement",
            }:
                from .models import WorkflowType
                workflow_type = getattr(self.workflow, "type", None) if self.workflow else None
                is_greenfield = (
                    workflow_type == WorkflowType.GREENFIELD
                    or (isinstance(workflow_type, str) and workflow_type.lower() == "greenfield")
                    or (hasattr(workflow_type, "value") and workflow_type.value == "greenfield")
                )
                user_prompt = self.state.variables.get("user_prompt", "")

                if is_greenfield and (not target_path or not target_path.exists()):
                    requirements_path = self.project_root / "requirements.md"
                    architecture_path = self.project_root / "architecture.md"
                    
                    spec_parts = []
                    if user_prompt:
                        spec_parts.append(user_prompt)
                    if requirements_path.exists():
                        req_content = requirements_path.read_text(encoding='utf-8')
                        spec_parts.append(f"\n\nRequirements:\n{req_content[:3000]}")
                    if architecture_path.exists():
                        arch_content = architecture_path.read_text(encoding='utf-8')
                        spec_parts.append(f"\n\nArchitecture:\n{arch_content[:3000]}")
                    
                    specification = "\n".join(spec_parts) or "Create the application based on requirements and architecture"
                    
                    stories_dir = self.project_root / "stories"
                    context_parts = []
                    if stories_dir.exists():
                        story_files = list(stories_dir.glob("*.md"))
                        if story_files:
                            context_parts.append("User Stories:")
                            for story_file in story_files[:5]:
                                context_parts.append(story_file.read_text(encoding='utf-8')[:500])
                    context = "\n\n".join(context_parts) if context_parts else None
                    
                    output_dir = self.project_root / "src"
                    if step.creates:
                        for create_item in step.creates:
                            if create_item.endswith("/") or create_item.endswith("\\"):
                                output_dir = self.project_root / create_item.rstrip("/\\")
                                break
                    
                    output_dir.mkdir(parents=True, exist_ok=True)
                    main_file = output_dir / "app.py"
                    
                    implement_result = await run_agent(
                        "implementer",
                        "implement",
                        specification=specification,
                        file_path=str(main_file),
                        context=context,
                    )
                    self.state.variables["implementer_result"] = implement_result
                    self.state.variables["target_file"] = str(main_file)
                    created_artifacts.append(
                        {"name": "src/", "path": str(output_dir)}
                    )
                    
                elif target_path and target_path.exists():
                    debug_report_path = self.project_root / "debug-report.md"
                    debug_context = (
                        debug_report_path.read_text(encoding="utf-8")
                        if debug_report_path.exists()
                        else ""
                    )
                    instruction = (
                        f"Fix the bugs in {target_path.name}. "
                        "Add robust input validation and handle missing keys safely. "
                        "Do not change behavior beyond fixing the crashes.\n\n"
                        "Context:\n"
                        f"{debug_context[:4000]}"
                    )

                    fix_result = await run_agent(
                        "implementer",
                        "refactor",
                        file=str(target_path),
                        instruction=instruction,
                    )
                    self.state.variables["implementer_result"] = fix_result

                    if "fixed-code/" in (step.creates or []):
                        fixed_dir = self.project_root / "fixed-code"
                        fixed_dir.mkdir(parents=True, exist_ok=True)
                        fixed_copy = fixed_dir / target_path.name
                        shutil.copy2(target_path, fixed_copy)
                        self.state.variables["fixed_file"] = str(fixed_copy)
                        created_artifacts.append(
                            {"name": "fixed-code/", "path": str(fixed_dir)}
                        )
                else:
                    raise ValueError(
                        "Implementer step requires either a target file for brownfield projects "
                        "or a greenfield workflow type for new projects."
                    )

            elif agent_name == "reviewer" and action in {"review_code", "review", "score"}:
                fixed_file = self.state.variables.get("fixed_file")
                implementer_file = self.state.variables.get("target_file")
                review_target = None
                
                if fixed_file:
                    review_target = Path(fixed_file)
                elif implementer_file:
                    review_target = Path(implementer_file)
                elif target_path:
                    review_target = target_path
                
                if not review_target or not review_target.exists():
                    raise ValueError("Reviewer step requires a target file to review.")

                review_result = await run_agent(
                    "reviewer", "score", file=str(review_target)
                )
                self.state.variables["reviewer_result"] = review_result

                # Note: Gate evaluation handled separately in parallel execution flow
                gate = step.gate or {}
                if gate:
                    # Extract scoring thresholds from step configuration
                    scoring_config = step.metadata.get("scoring", {}) if step.metadata else {}
                    thresholds_config = scoring_config.get("thresholds", {}) if scoring_config else {}
                    
                    # Create quality thresholds from step config or use defaults
                    thresholds = QualityThresholds.from_dict(thresholds_config)
                    
                    # Extract scores from review result
                    scores = review_result.get("scores", {})
                    if not scores:
                        scoring = review_result.get("scoring", {})
                        if scoring:
                            scores = scoring.get("scores", {})
                    
                    # Evaluate quality gate
                    quality_gate = QualityGate(thresholds=thresholds)
                    gate_result = quality_gate.evaluate_from_review_result(review_result, thresholds)
                    
                    passed = gate_result.passed
                    self.state.variables["gate_last"] = {
                        "step": step.id,
                        "passed": passed,
                        "scoring": scores,
                        "gate_result": gate_result.to_dict(),
                    }

            elif agent_name == "tester" and action in {"write_tests", "test"}:
                fixed_file = self.state.variables.get("fixed_file")
                implementer_file = self.state.variables.get("target_file")
                test_target = None
                
                if fixed_file:
                    test_target = Path(fixed_file)
                elif implementer_file:
                    test_target = Path(implementer_file)
                elif target_path:
                    test_target = target_path
                
                if not test_target or not test_target.exists():
                    raise ValueError("Tester step requires a target file to test.")

                test_result = await run_agent("tester", "test", file=str(test_target))
                self.state.variables["tester_result"] = test_result

                if "tests/" in (step.creates or []):
                    tests_dir = self.project_root / "tests"
                    created_artifacts.append({"name": "tests/", "path": str(tests_dir)})

            elif agent_name == "orchestrator" and action in {"finalize", "complete"}:
                pass

            elif agent_name == "analyst" and action in {"gather_requirements", "gather-requirements", "analyze"}:
                user_prompt = self.state.variables.get("user_prompt", "")
                if not user_prompt and not self.auto_mode:
                    user_prompt = "Generate requirements for this project"
                
                requirements_result = await run_agent(
                    "analyst",
                    "gather-requirements",
                    description=user_prompt,
                    output_file="requirements.md"
                )
                self.state.variables["analyst_result"] = requirements_result
                
                if "requirements.md" in (step.creates or []):
                    req_path = self.project_root / "requirements.md"
                    if req_path.exists():
                        created_artifacts.append({"name": "requirements.md", "path": str(req_path)})

            elif agent_name == "planner" and action in {"create_stories", "create-stories", "plan", "breakdown"}:
                requirements_path = self.project_root / "requirements.md"
                requirements = requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else ""
                
                plan_description = requirements if requirements else "Create user stories for this project"
                
                planner_result = await run_agent(
                    "planner",
                    "plan",
                    description=plan_description
                )
                self.state.variables["planner_result"] = planner_result
                
                stories_dir = self.project_root / "stories"
                stories_dir.mkdir(parents=True, exist_ok=True)
                
                if "stories/" in (step.creates or []):
                    if stories_dir.exists():
                        created_artifacts.append({"name": "stories/", "path": str(stories_dir)})

            elif agent_name == "architect" and action in {"design_system", "design-system", "design_architecture"}:
                requirements_path = self.project_root / "requirements.md"
                requirements = requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else ""
                stories_dir = self.project_root / "stories"
                
                context_parts = []
                if stories_dir.exists():
                    story_files = list(stories_dir.glob("*.md"))
                    if story_files:
                        context_parts.append("User Stories:")
                        for story_file in story_files[:10]:
                            context_parts.append(story_file.read_text(encoding="utf-8")[:1000])
                context = "\n\n".join(context_parts) if context_parts else ""
                
                architect_result = await run_agent(
                    "architect",
                    "design-system",
                    requirements=requirements,
                    context=context,
                    output_file="architecture.md"
                )
                self.state.variables["architect_result"] = architect_result
                
                if "architecture.md" in (step.creates or []):
                    arch_path = self.project_root / "architecture.md"
                    if arch_path.exists():
                        created_artifacts.append({"name": "architecture.md", "path": str(arch_path)})

            elif agent_name == "designer" and action in {"api_design", "api-design", "design_api"}:
                requirements_path = self.project_root / "requirements.md"
                requirements = requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else ""
                arch_path = self.project_root / "architecture.md"
                architecture = arch_path.read_text(encoding="utf-8") if arch_path.exists() else ""
                
                api_requirements = f"{requirements}\n\nArchitecture:\n{architecture}" if architecture else requirements
                
                designer_result = await run_agent(
                    "designer",
                    "design-api",
                    requirements=api_requirements
                )
                self.state.variables["designer_result"] = designer_result
                
                if "api-design.md" in (step.creates or []):
                    api_design_path = self.project_root / "api-design.md"
                    if api_design_path.exists():
                        created_artifacts.append({"name": "api-design.md", "path": str(api_design_path)})

            elif agent_name == "ops" and action in {"security_scan", "security-scan", "audit"}:
                ops_result = await run_agent(
                    "ops",
                    "security-scan",
                    project_root=str(self.project_root)
                )
                self.state.variables["ops_result"] = ops_result
                
                if "security-report.md" in (step.creates or []):
                    security_path = self.project_root / "security-report.md"
                    if security_path.exists():
                        created_artifacts.append({"name": "security-report.md", "path": str(security_path)})

            elif agent_name == "documenter" and action in {"generate_docs", "generate-docs", "document", "generate_project_docs", "generate-project-docs"}:
                # Support both single-file and project-level documentation
                if action in {"generate_project_docs", "generate-project-docs"}:
                    # Project-level documentation
                    output_dir = step.metadata.get("output_dir") if step.metadata else None
                    output_format = step.metadata.get("output_format", "markdown") if step.metadata else "markdown"
                    
                    doc_result = await run_agent(
                        "documenter",
                        "generate-project-docs",
                        project_root=str(self.project_root),
                        output_dir=output_dir,
                        output_format=output_format,
                    )
                    self.state.variables["documenter_result"] = doc_result
                    
                    # Capture docs/api/ directory as artifact
                    docs_api_dir = self.project_root / "docs" / "api"
                    if docs_api_dir.exists():
                        created_artifacts.append({"name": "docs/api/", "path": str(docs_api_dir)})
                else:
                    # Single-file documentation (backward compatible)
                    requirements_path = self.project_root / "requirements.md"
                    requirements = requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else ""
                    
                    doc_result = await run_agent(
                        "documenter",
                        "generate-docs",
                        requirements=requirements,
                        project_root=str(self.project_root)
                    )
                    self.state.variables["documenter_result"] = doc_result
                    
                    if "docs/" in (step.creates or []):
                        docs_dir = self.project_root / "docs"
                        if docs_dir.exists():
                            created_artifacts.append({"name": "docs/", "path": str(docs_dir)})

            else:
                # Unknown mapping: return empty artifacts
                return {}

            # Return artifacts as dict keyed by artifact name
            artifacts_dict: dict[str, dict[str, Any]] = {}
            for art in created_artifacts:
                artifacts_dict[art["name"]] = art
            return artifacts_dict if artifacts_dict else None

        except Exception:
            # Re-raise exception - ParallelStepExecutor will handle it
            raise

    async def _execute_step(self, step: WorkflowStep, target_path: Path | None) -> None:
        """
        Execute a single workflow step and advance state.

        This is intentionally pragmatic: it supports the shipped preset workflows
        by mapping `step.action` to each agent's real CLI/API commands.
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

        # ---- Helper: dynamic agent import + run ----
        async def run_agent(agent: str, command: str, **kwargs: Any) -> dict[str, Any]:
            module = __import__(f"tapps_agents.agents.{agent}.agent", fromlist=["*"])
            class_name = f"{agent.title()}Agent"
            agent_cls = getattr(module, class_name)
            instance = agent_cls()
            await instance.activate(self.project_root)
            try:
                return await instance.run(command, **kwargs)
            finally:
                # Close agent if it has a close method
                if hasattr(instance, 'close'):
                    await instance.close()

        created_artifacts: list[dict[str, Any]] = []

        try:
            # ---- Step execution mappings ----
            if agent_name == "debugger" and action in {
                "analyze_error",
                "analyze-error",
                "analyze",
            }:
                if not target_path or not target_path.exists():
                    raise ValueError(
                        "Debugger step requires a target file. Provide --file <path> (or ensure example_bug.py exists)."
                    )

                error_message, stack_trace = self._capture_python_exception(target_path)
                if not error_message:
                    # Fall back to a generic message for static analysis
                    error_message = f"Bug(s) reported in {target_path.name} (no runtime traceback captured)."

                debug_result = await run_agent(
                    "debugger",
                    "analyze-error",
                    error_message=error_message,
                    stack_trace=stack_trace,
                )
                self.state.variables["debugger_result"] = debug_result

                # Write debug report artifact if requested
                if "debug-report.md" in (step.creates or []):
                    report_path = self.project_root / "debug-report.md"
                    report_lines = [
                        "# Debug Report",
                        "",
                        f"## Target: `{target_path}`",
                        "",
                        "## Error message",
                        "```",
                        error_message or "",
                        "```",
                    ]
                    if stack_trace:
                        report_lines += ["", "## Stack trace", "```", stack_trace, "```"]
                    report_lines += [
                        "",
                        "## Analysis (DebuggerAgent)",
                        "```json",
                        json.dumps(debug_result, indent=2),
                        "```",
                    ]
                    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
                    created_artifacts.append(
                        {"name": "debug-report.md", "path": str(report_path)}
                    )

            elif agent_name == "implementer" and action in {
                "write_code",
                "fix",
                "implement",
            }:
                # Check if this is a greenfield project (new project from scratch)
                from .models import WorkflowType
                workflow_type = getattr(self.workflow, "type", None) if self.workflow else None
                is_greenfield = (
                    workflow_type == WorkflowType.GREENFIELD
                    or (isinstance(workflow_type, str) and workflow_type.lower() == "greenfield")
                    or (hasattr(workflow_type, "value") and workflow_type.value == "greenfield")
                )
                user_prompt = self.state.variables.get("user_prompt", "")

                if is_greenfield and (not target_path or not target_path.exists()):
                    # Greenfield project: create new code from scratch
                    # Use requirements and architecture from previous steps
                    requirements_path = self.project_root / "requirements.md"
                    architecture_path = self.project_root / "architecture.md"
                    
                    # Build implementation specification
                    spec_parts = []
                    if user_prompt:
                        spec_parts.append(user_prompt)
                    if requirements_path.exists():
                        req_content = requirements_path.read_text(encoding='utf-8')
                        spec_parts.append(f"\n\nRequirements:\n{req_content[:3000]}")
                    if architecture_path.exists():
                        arch_content = architecture_path.read_text(encoding='utf-8')
                        spec_parts.append(f"\n\nArchitecture:\n{arch_content[:3000]}")
                    
                    specification = "\n".join(spec_parts) or "Create the application based on requirements and architecture"
                    
                    # Build context from stories if available
                    stories_dir = self.project_root / "stories"
                    context_parts = []
                    if stories_dir.exists():
                        story_files = list(stories_dir.glob("*.md"))
                        if story_files:
                            context_parts.append("User Stories:")
                            for story_file in story_files[:5]:  # Limit to first 5 stories
                                context_parts.append(story_file.read_text(encoding='utf-8')[:500])
                    context = "\n\n".join(context_parts) if context_parts else None
                    
                    # Determine output directory and main file from step.creates
                    output_dir = self.project_root / "src"
                    if step.creates:
                        for create_item in step.creates:
                            if create_item.endswith("/") or create_item.endswith("\\"):
                                output_dir = self.project_root / create_item.rstrip("/\\")
                                break
                    
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create main application file
                    main_file = output_dir / "app.py"
                    
                    # Use implement command for greenfield projects
                    implement_result = await run_agent(
                        "implementer",
                        "implement",
                        specification=specification,
                        file_path=str(main_file),
                        context=context,
                    )
                    self.state.variables["implementer_result"] = implement_result
                    self.state.variables["target_file"] = str(main_file)
                    created_artifacts.append(
                        {"name": "src/", "path": str(output_dir)}
                    )
                    
                elif target_path and target_path.exists():
                    # Brownfield project: refactor existing code
                    debug_report_path = self.project_root / "debug-report.md"
                    debug_context = (
                        debug_report_path.read_text(encoding="utf-8")
                        if debug_report_path.exists()
                        else ""
                    )
                    instruction = (
                        f"Fix the bugs in {target_path.name}. "
                        "Add robust input validation and handle missing keys safely. "
                        "Do not change behavior beyond fixing the crashes.\n\n"
                        "Context:\n"
                        f"{debug_context[:4000]}"
                    )

                    fix_result = await run_agent(
                        "implementer",
                        "refactor",
                        file=str(target_path),
                        instruction=instruction,
                    )
                    self.state.variables["implementer_result"] = fix_result

                    # Create fixed-code/ artifact if requested by preset
                    if "fixed-code/" in (step.creates or []):
                        fixed_dir = self.project_root / "fixed-code"
                        fixed_dir.mkdir(parents=True, exist_ok=True)
                        fixed_copy = fixed_dir / target_path.name
                        shutil.copy2(target_path, fixed_copy)
                        self.state.variables["fixed_file"] = str(fixed_copy)
                        created_artifacts.append(
                            {"name": "fixed-code/", "path": str(fixed_dir)}
                        )
                else:
                    raise ValueError(
                        "Implementer step requires either a target file for brownfield projects "
                        "or a greenfield workflow type for new projects."
                    )

            elif agent_name == "reviewer" and action in {"review_code", "review", "score"}:
                # Prefer the fixed copy if available, then check implementer result, then target_path
                fixed_file = self.state.variables.get("fixed_file")
                implementer_file = self.state.variables.get("target_file")
                review_target = None
                
                if fixed_file:
                    review_target = Path(fixed_file)
                elif implementer_file:
                    review_target = Path(implementer_file)
                elif target_path:
                    review_target = target_path
                
                if not review_target or not review_target.exists():
                    raise ValueError("Reviewer step requires a target file to review.")

                review_result = await run_agent(
                    "reviewer", "score", file=str(review_target)
                )
                self.state.variables["reviewer_result"] = review_result

                # Evaluate gate if configured
                gate = step.gate or {}
                if gate:
                    # Extract scoring thresholds from step configuration
                    scoring_config = step.metadata.get("scoring", {}) if step.metadata else {}
                    thresholds_config = scoring_config.get("thresholds", {}) if scoring_config else {}
                    
                    # Create quality thresholds from step config or use defaults
                    thresholds = QualityThresholds.from_dict(thresholds_config)
                    
                    # Extract scores from review result
                    scores = review_result.get("scores", {})
                    if not scores:
                        scoring = review_result.get("scoring", {})
                        if scoring:
                            scores = scoring.get("scores", {})
                    
                    # Evaluate quality gate
                    quality_gate = QualityGate(thresholds=thresholds)
                    gate_result = quality_gate.evaluate_from_review_result(review_result, thresholds)
                    
                    passed = gate_result.passed
                    self.state.variables["gate_last"] = {
                        "step": step.id,
                        "passed": passed,
                        "scoring": scores,
                        "gate_result": gate_result.to_dict(),
                    }
                    on_pass = gate.get("on_pass") or gate.get("on-pass")
                    on_fail = gate.get("on_fail") or gate.get("on-fail")

                    # Mark review complete, but override next step based on gate decision
                    self.mark_step_complete(
                        step_id=step.id, artifacts=created_artifacts or None
                    )
                    if passed and on_pass:
                        self.state.current_step = on_pass
                    elif (not passed) and on_fail:
                        self.state.current_step = on_fail
                    self.save_state()
                    return

            elif agent_name == "tester" and action in {"write_tests", "test"}:
                # Prefer the fixed copy if available, then check implementer result, then target_path
                fixed_file = self.state.variables.get("fixed_file")
                implementer_file = self.state.variables.get("target_file")
                test_target = None
                
                if fixed_file:
                    test_target = Path(fixed_file)
                elif implementer_file:
                    test_target = Path(implementer_file)
                elif target_path:
                    test_target = target_path
                
                if not test_target or not test_target.exists():
                    raise ValueError("Tester step requires a target file to test.")

                test_result = await run_agent("tester", "test", file=str(test_target))
                self.state.variables["tester_result"] = test_result

                if "tests/" in (step.creates or []):
                    tests_dir = self.project_root / "tests"
                    created_artifacts.append({"name": "tests/", "path": str(tests_dir)})

            elif agent_name == "orchestrator" and action in {"finalize", "complete"}:
                # Nothing to do other than marking completion.
                pass

            elif agent_name == "analyst" and action in {"gather_requirements", "gather-requirements", "analyze"}:
                user_prompt = self.state.variables.get("user_prompt", "")
                if not user_prompt and not self.auto_mode:
                    # In non-auto mode, could prompt user, but for now use generic
                    user_prompt = "Generate requirements for this project"
                
                requirements_result = await run_agent(
                    "analyst",
                    "gather-requirements",
                    description=user_prompt,
                    output_file="requirements.md"
                )
                self.state.variables["analyst_result"] = requirements_result
                
                # Create requirements.md artifact if requested
                if "requirements.md" in (step.creates or []):
                    req_path = self.project_root / "requirements.md"
                    # Analyst agent should have created this, but verify
                    if req_path.exists():
                        created_artifacts.append({"name": "requirements.md", "path": str(req_path)})

            elif agent_name == "planner" and action in {"create_stories", "create-stories", "plan", "breakdown"}:
                requirements_path = self.project_root / "requirements.md"
                requirements = requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else ""
                
                # Use "plan" command which creates a plan with multiple stories
                # The plan command accepts description parameter
                plan_description = requirements if requirements else "Create user stories for this project"
                
                planner_result = await run_agent(
                    "planner",
                    "plan",
                    description=plan_description
                )
                self.state.variables["planner_result"] = planner_result
                
                # Create stories directory if it doesn't exist
                stories_dir = self.project_root / "stories"
                stories_dir.mkdir(parents=True, exist_ok=True)
                
                if "stories/" in (step.creates or []):
                    if stories_dir.exists():
                        created_artifacts.append({"name": "stories/", "path": str(stories_dir)})

            elif agent_name == "architect" and action in {"design_system", "design-system", "design_architecture"}:
                requirements_path = self.project_root / "requirements.md"
                requirements = requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else ""
                stories_dir = self.project_root / "stories"
                
                # Build context from stories if available
                context_parts = []
                if stories_dir.exists():
                    story_files = list(stories_dir.glob("*.md"))
                    if story_files:
                        context_parts.append("User Stories:")
                        for story_file in story_files[:10]:  # Limit to first 10 stories
                            context_parts.append(story_file.read_text(encoding="utf-8")[:1000])
                context = "\n\n".join(context_parts) if context_parts else ""
                
                architect_result = await run_agent(
                    "architect",
                    "design-system",
                    requirements=requirements,
                    context=context,
                    output_file="architecture.md"
                )
                self.state.variables["architect_result"] = architect_result
                
                if "architecture.md" in (step.creates or []):
                    arch_path = self.project_root / "architecture.md"
                    if arch_path.exists():
                        created_artifacts.append({"name": "architecture.md", "path": str(arch_path)})

            elif agent_name == "designer" and action in {"api_design", "api-design", "design_api"}:
                requirements_path = self.project_root / "requirements.md"
                requirements = requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else ""
                arch_path = self.project_root / "architecture.md"
                architecture = arch_path.read_text(encoding="utf-8") if arch_path.exists() else ""
                
                # Combine requirements and architecture for the design-api command
                # The design-api command expects requirements parameter
                api_requirements = f"{requirements}\n\nArchitecture:\n{architecture}" if architecture else requirements
                
                designer_result = await run_agent(
                    "designer",
                    "design-api",
                    requirements=api_requirements
                )
                self.state.variables["designer_result"] = designer_result
                
                if "api-design.md" in (step.creates or []):
                    api_design_path = self.project_root / "api-design.md"
                    if api_design_path.exists():
                        created_artifacts.append({"name": "api-design.md", "path": str(api_design_path)})

            elif agent_name == "ops" and action in {"security_scan", "security-scan", "audit"}:
                # Ops agent security scan
                ops_result = await run_agent(
                    "ops",
                    "security-scan",
                    project_root=str(self.project_root)
                )
                self.state.variables["ops_result"] = ops_result
                
                if "security-report.md" in (step.creates or []):
                    security_path = self.project_root / "security-report.md"
                    if security_path.exists():
                        created_artifacts.append({"name": "security-report.md", "path": str(security_path)})

            elif agent_name == "documenter" and action in {"generate_docs", "generate-docs", "document", "generate_project_docs", "generate-project-docs"}:
                # Support both single-file and project-level documentation
                if action in {"generate_project_docs", "generate-project-docs"}:
                    # Project-level documentation
                    output_dir = step.metadata.get("output_dir") if step.metadata else None
                    output_format = step.metadata.get("output_format", "markdown") if step.metadata else "markdown"
                    
                    doc_result = await run_agent(
                        "documenter",
                        "generate-project-docs",
                        project_root=str(self.project_root),
                        output_dir=output_dir,
                        output_format=output_format,
                    )
                    self.state.variables["documenter_result"] = doc_result
                    
                    # Capture docs/api/ directory as artifact
                    docs_api_dir = self.project_root / "docs" / "api"
                    if docs_api_dir.exists():
                        created_artifacts.append({"name": "docs/api/", "path": str(docs_api_dir)})
                else:
                    # Single-file documentation (backward compatible)
                    requirements_path = self.project_root / "requirements.md"
                    requirements = requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else ""
                    
                    doc_result = await run_agent(
                        "documenter",
                        "generate-docs",
                        requirements=requirements,
                        project_root=str(self.project_root)
                    )
                    self.state.variables["documenter_result"] = doc_result
                    
                    if "docs/" in (step.creates or []):
                        docs_dir = self.project_root / "docs"
                        if docs_dir.exists():
                            created_artifacts.append({"name": "docs/", "path": str(docs_dir)})

            else:
                # Unknown mapping: mark as skipped rather than hard-failing (best-effort).
                # This keeps the executor resilient as presets evolve.
                step_execution.status = "skipped"
                step_execution.completed_at = datetime.now()
                step_execution.duration_seconds = 0.0
                self.skip_step(step.id)
                return

            # Mark step execution as completed
            step_execution.completed_at = datetime.now()
            step_execution.duration_seconds = (
                step_execution.completed_at - step_execution.started_at
            ).total_seconds()
            step_execution.status = "completed"

            # Default: mark step complete and advance to its `next`
            self.mark_step_complete(step_id=step.id, artifacts=created_artifacts or None)

        except Exception as e:
            # Mark step execution as failed
            step_execution.completed_at = datetime.now()
            step_execution.duration_seconds = (
                step_execution.completed_at - step_execution.started_at
            ).total_seconds()
            step_execution.status = "failed"
            envelope = ErrorEnvelopeBuilder.from_exception(
                e,
                workflow_id=self.state.workflow_id if self.state else None,
                step_id=step.id,
                agent=step.agent or "",
            )
            step_execution.error = envelope.to_user_message()
            raise

    def get_current_step(self) -> WorkflowStep | None:
        """Get the current workflow step."""
        if not self.state or not self.workflow:
            return None

        current_step_id = self.state.current_step
        if not current_step_id:
            return None

        for step in self.workflow.steps:
            if step.id == current_step_id:
                return step

        return None

    def get_next_step(self) -> WorkflowStep | None:
        """Get the next workflow step after the current one."""
        current_step = self.get_current_step()
        if not current_step or not current_step.next:
            return None
        if not self.workflow:
            return None

        for step in self.workflow.steps:
            if step.id == current_step.next:
                return step

        return None

    def can_proceed(self) -> bool:
        """Check if workflow can proceed to next step."""
        if not self.state or not self.workflow:
            return False

        current_step = self.get_current_step()
        if not current_step:
            return False

        # Check if required artifacts exist
        for artifact_name in current_step.requires:
            if artifact_name not in self.state.artifacts:
                return False

            artifact = self.state.artifacts[artifact_name]
            if artifact.status != "complete":
                return False

        return True

    def mark_step_complete(
        self,
        step_id: str | None = None,
        artifacts: list[dict[str, Any]] | None = None,
    ):
        """
        Mark a step as complete.

        Args:
            step_id: Step ID (defaults to current step)
            artifacts: List of artifact information dictionaries
        """
        if not self.state:
            raise ValueError("Workflow not started")
        if not self.workflow:
            raise ValueError("No workflow loaded. Call load_workflow() first.")

        step_id = step_id or self.state.current_step
        if not step_id:
            raise ValueError("No step to complete")

        # Mark step as completed
        if step_id not in self.state.completed_steps:
            self.state.completed_steps.append(step_id)

        # Add artifacts
        if artifacts:
            for art_data in artifacts:
                artifact = Artifact(
                    name=art_data.get("name", ""),
                    path=art_data.get("path", ""),
                    status="complete",
                    created_by=step_id,
                    created_at=datetime.now(),
                    metadata=art_data.get("metadata", {}),
                )
                self.state.artifacts[artifact.name] = artifact

        # Move to next step
        current_step = None
        for step in self.workflow.steps:
            if step.id == step_id:
                current_step = step
                break

        if current_step and current_step.next:
            self.state.current_step = current_step.next
        else:
            # Workflow complete
            self.state.current_step = None
            self.state.status = "completed"

        self.save_state()

    def skip_step(self, step_id: str):
        """Skip a step."""
        if not self.state:
            raise ValueError("Workflow not started")
        if not self.workflow:
            raise ValueError("No workflow loaded. Call load_workflow() first.")

        if step_id not in self.state.skipped_steps:
            self.state.skipped_steps.append(step_id)

        # Find the step and move to next
        for step in self.workflow.steps:
            if step.id == step_id and step.next:
                self.state.current_step = step.next
                break

        self.save_state()

    def _state_dir(self) -> Path:
        """Directory for persisted workflow state."""
        return self.project_root / ".tapps-agents" / "workflow-state"

    def _state_path_for(self, workflow_id: str) -> Path:
        return self._state_dir() / f"workflow-{workflow_id}.json"

    def _last_state_path(self) -> Path:
        return self._state_dir() / "last.json"

    @staticmethod
    def _artifact_to_dict(artifact: Artifact) -> dict[str, Any]:
        return {
            "name": artifact.name,
            "path": artifact.path,
            "status": artifact.status,
            "created_by": artifact.created_by,
            "created_at": (
                artifact.created_at.isoformat() if artifact.created_at else None
            ),
            "metadata": artifact.metadata or {},
        }

    @staticmethod
    def _artifact_from_dict(data: dict[str, Any]) -> Artifact:
        created_at = data.get("created_at")
        return Artifact(
            name=data.get("name", ""),
            path=data.get("path", ""),
            status=data.get("status", "pending"),
            created_by=data.get("created_by"),
            created_at=datetime.fromisoformat(created_at) if created_at else None,
            metadata=data.get("metadata", {}) or {},
        )

    @staticmethod
    def _step_execution_to_dict(step_exec: StepExecution) -> dict[str, Any]:
        return {
            "step_id": step_exec.step_id,
            "agent": step_exec.agent,
            "action": step_exec.action,
            "started_at": step_exec.started_at.isoformat(),
            "completed_at": (
                step_exec.completed_at.isoformat() if step_exec.completed_at else None
            ),
            "duration_seconds": step_exec.duration_seconds,
            "status": step_exec.status,
            "error": step_exec.error,
        }

    @staticmethod
    def _step_execution_from_dict(data: dict[str, Any]) -> StepExecution:
        started_at = datetime.fromisoformat(data["started_at"])
        completed_at = (
            datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None
        )
        return StepExecution(
            step_id=data["step_id"],
            agent=data["agent"],
            action=data["action"],
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=data.get("duration_seconds"),
            status=data.get("status", "running"),
            error=data.get("error"),
        )

    def _state_to_dict(self, state: WorkflowState) -> dict[str, Any]:
        def _make_json_serializable(obj: Any) -> Any:
            """Recursively convert objects to JSON-serializable format."""
            # Handle ProjectProfile objects
            if hasattr(obj, "to_dict") and hasattr(obj, "compliance_requirements"):
                # This is likely a ProjectProfile object
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
                json.dumps(obj)
                return obj
            except (TypeError, ValueError):
                # For non-serializable types, convert to string as fallback
                return str(obj)

        artifacts = {
            k: self._artifact_to_dict(v) for k, v in (state.artifacts or {}).items()
        }
        step_executions = [
            self._step_execution_to_dict(se) for se in (state.step_executions or [])
        ]
        
        # Convert variables to JSON-serializable format
        variables = state.variables or {}
        serializable_variables = _make_json_serializable(variables)
        
        return {
            "workflow_id": state.workflow_id,
            "started_at": state.started_at.isoformat(),
            "current_step": state.current_step,
            "completed_steps": list(state.completed_steps or []),
            "skipped_steps": list(state.skipped_steps or []),
            "artifacts": artifacts,
            "variables": serializable_variables,
            "status": state.status,
            "error": state.error,
            "step_executions": step_executions,
        }

    def _state_from_dict(self, data: dict[str, Any]) -> WorkflowState:
        artifacts_data = data.get("artifacts", {}) or {}
        artifacts = {k: self._artifact_from_dict(v) for k, v in artifacts_data.items()}
        started_at = datetime.fromisoformat(data["started_at"])
        step_executions_data = data.get("step_executions", []) or []
        step_executions = [
            self._step_execution_from_dict(se_data) for se_data in step_executions_data
        ]
        return WorkflowState(
            workflow_id=data["workflow_id"],
            started_at=started_at,
            current_step=data.get("current_step"),
            completed_steps=data.get("completed_steps", []) or [],
            skipped_steps=data.get("skipped_steps", []) or [],
            artifacts=artifacts,
            variables=data.get("variables", {}) or {},
            status=data.get("status", "running"),
            error=data.get("error"),
            step_executions=step_executions,
        )

    def save_state(self) -> Path | None:
        """
        Persist current workflow state (best-effort).

        Uses advanced state management if enabled, otherwise falls back to basic persistence.

        Returns:
            Path to the saved state file, or None if nothing was saved.
        """
        if not self.state:
            return None

        try:
            # Use advanced state manager if available
            if self.state_manager:
                return self.state_manager.save_state(self.state, self._workflow_path)

            # Fallback to basic persistence
            state_dir = self._state_dir()
            state_dir.mkdir(parents=True, exist_ok=True)
            state_path = self._state_path_for(self.state.workflow_id)

            data = self._state_to_dict(self.state)
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            # Update last pointer for easy resume
            last_data = {
                "workflow_id": self.state.workflow_id,
                "state_file": str(state_path),
                "saved_at": datetime.now().isoformat(),
                "workflow_path": data.get("variables", {}).get("_workflow_path"),
            }
            with open(self._last_state_path(), "w", encoding="utf-8") as f:
                json.dump(last_data, f, indent=2)

            return state_path
        except Exception:
            return None

    def load_last_state(self, validate: bool = True) -> WorkflowState:
        """
        Load the most recently persisted workflow state and attach it to this executor.

        Uses advanced state management if enabled, with validation and migration support.

        Args:
            validate: Whether to validate state integrity (only used with advanced state)

        This also attempts to reload the workflow YAML referenced by state variables.
        """
        # Use advanced state manager if available
        if self.state_manager:
            try:
                state, metadata = self.state_manager.load_state(validate=validate)

                # Reload workflow if we have a path
                if metadata.workflow_path:
                    candidate = Path(metadata.workflow_path)
                    if not candidate.is_absolute():
                        candidate = self.project_root / candidate
                    if candidate.exists():
                        self.load_workflow(candidate)

                self.state = state
                return state
            except FileNotFoundError:
                # Fall through to basic loading if advanced manager fails
                pass

        # Fallback to basic loading
        last_path = self._last_state_path()
        if not last_path.exists():
            raise FileNotFoundError("No persisted workflow state found to resume")

        last_data = json.loads(last_path.read_text(encoding="utf-8"))
        state_file = last_data.get("state_file")
        if not state_file:
            raise ValueError("Invalid last state pointer (missing state_file)")

        state_path = Path(state_file)
        if not state_path.is_absolute():
            state_path = self.project_root / state_path
        if not state_path.exists():
            raise FileNotFoundError(
                f"Persisted workflow state file not found: {state_path}"
            )

        data = json.loads(state_path.read_text(encoding="utf-8"))
        state = self._state_from_dict(data)

        # Reload workflow if we have a path
        workflow_path = (state.variables or {}).get("_workflow_path")
        if workflow_path:
            candidate = Path(workflow_path)
            if not candidate.is_absolute():
                candidate = self.project_root / candidate
            if candidate.exists():
                self.load_workflow(candidate)

        self.state = state
        return state

    def step_requires_expert_consultation(
        self, step: WorkflowStep | None = None
    ) -> bool:
        """
        Check if a step requires expert consultation.

        Args:
            step: Optional workflow step (defaults to current step)

        Returns:
            True if step has experts configured in 'consults' field
        """
        step = step or self.get_current_step()
        if not step:
            return False

        return bool(step.consults and len(step.consults) > 0)

    async def consult_experts_for_step(
        self, query: str | None = None, step: WorkflowStep | None = None
    ) -> dict[str, Any] | None:
        """
        Automatically consult experts for a step if it has 'consults' configured.

        This is a convenience method that:
        1. Checks if the step has experts configured
        2. Generates a context-aware query if none provided
        3. Consults the experts automatically
        4. Returns the consultation result

        Args:
            query: Optional query (auto-generated from step context if not provided)
            step: Optional workflow step (defaults to current step)

        Returns:
            Consultation result dict if experts were consulted, None otherwise

        Raises:
            ValueError: If expert registry not available but step requires consultation
        """
        step = step or self.get_current_step()
        if not step:
            return None

        # Check if step requires expert consultation
        if not self.step_requires_expert_consultation(step):
            return None

        # Ensure expert registry is available
        if not self.expert_registry:
            raise ValueError(
                f"Step '{step.id}' requires expert consultation (consults: {step.consults}), "
                "but expert_registry not available. Provide expert_registry in WorkflowExecutor.__init__."
            )

        # Generate query if not provided
        if not query:
            # Build context-aware query from step information
            query_parts = [f"Agent: {step.agent}", f"Action: {step.action}"]
            if step.notes:
                query_parts.append(f"Context: {step.notes}")
            if step.metadata:
                context_info = step.metadata.get(
                    "context", step.metadata.get("description")
                )
                if context_info:
                    query_parts.append(f"Additional context: {context_info}")

            query = (
                "Please provide expert guidance for this workflow step: "
                + " | ".join(query_parts)
            )

        # Determine domain from expert IDs
        expert_ids = step.consults
        domain = "general"
        if expert_ids:
            # Extract domain from first expert ID (experts follow pattern: expert-{domain})
            first_expert = expert_ids[0]
            if first_expert.startswith("expert-"):
                domain = first_expert.replace("expert-", "")
            else:
                # Try to infer from expert ID format
                domain = (
                    first_expert.split("-")[-1] if "-" in first_expert else "general"
                )

        # Consult experts via registry
        consultation_result = await self.expert_registry.consult(
            query=query,
            domain=domain,
            include_all=True,  # Consult all experts for weighted decision
        )

        # Store consultation in workflow state for reference
        if self.state:
            if "expert_consultations" not in self.state.variables:
                self.state.variables["expert_consultations"] = {}
            self.state.variables["expert_consultations"][step.id] = {
                "query": query,
                "domain": domain,
                "experts_consulted": expert_ids,
                "weighted_answer": consultation_result.weighted_answer,
                "confidence": consultation_result.confidence,
                "consulted_at": datetime.now().isoformat(),
            }

        return {
            "query": query,
            "domain": domain,
            "experts_consulted": expert_ids,
            "weighted_answer": consultation_result.weighted_answer,
            "confidence": consultation_result.confidence,
            "agreement_level": consultation_result.agreement_level,
            "primary_expert": consultation_result.primary_expert,
            "all_experts_agreed": consultation_result.all_experts_agreed,
            "responses": consultation_result.responses,
        }

    async def consult_experts(
        self,
        query: str,
        domain: str | None = None,
        step: WorkflowStep | None = None,
    ) -> dict[str, Any]:
        """
        Consult experts for the current step.

        Args:
            query: The question or request for domain knowledge
            domain: Optional domain context (extracted from step if not provided)
            step: Optional workflow step (defaults to current step)

        Returns:
            Consultation result from expert registry

        Raises:
            ValueError: If expert registry not available or no experts to consult
        """
        if not self.expert_registry:
            raise ValueError(
                "Expert registry not available. Provide expert_registry in __init__."
            )

        step = step or self.get_current_step()
        if not step:
            raise ValueError("No current step available for expert consultation.")

        # Get experts to consult from step
        expert_ids = step.consults
        if not expert_ids:
            raise ValueError(
                f"Step '{step.id}' has no experts configured in 'consults' field."
            )

        # Determine domain from step or use provided domain
        if not domain:
            # Try to infer domain from expert ID or step metadata
            if expert_ids:
                # Assume first expert's domain (experts follow pattern: expert-{domain})
                first_expert = expert_ids[0]
                if first_expert.startswith("expert-"):
                    domain = first_expert.replace("expert-", "")
                else:
                    domain = "general"
            else:
                domain = "general"

        # Consult experts via registry
        # The registry handles weighted aggregation
        consultation_result = await self.expert_registry.consult(
            query=query,
            domain=domain,
            include_all=True,  # Consult all experts for weighted decision
        )

        return {
            "query": query,
            "domain": domain,
            "experts_consulted": expert_ids,
            "weighted_answer": consultation_result.weighted_answer,
            "confidence": consultation_result.confidence,
            "agreement_level": consultation_result.agreement_level,
            "primary_expert": consultation_result.primary_expert,
            "all_experts_agreed": consultation_result.all_experts_agreed,
            "responses": consultation_result.responses,
        }

    def get_status(self) -> dict[str, Any]:
        """Get workflow execution status."""
        if not self.state:
            return {"status": "not_started"}

        current_step = self.get_current_step()

        return {
            "workflow_id": self.state.workflow_id,
            "status": self.state.status,
            "current_step": self.state.current_step,
            "current_step_details": (
                {
                    "id": current_step.id if current_step else None,
                    "agent": current_step.agent if current_step else None,
                    "action": current_step.action if current_step else None,
                    "consults": current_step.consults if current_step else [],
                }
                if current_step
                else None
            ),
            "completed_steps": self.state.completed_steps,
            "skipped_steps": self.state.skipped_steps,
            "artifacts_count": len(self.state.artifacts),
            "can_proceed": self.can_proceed(),
            "expert_registry_available": self.expert_registry is not None,
        }

    def get_progress(self) -> dict[str, Any]:
        """
        Get detailed progress report for the workflow.

        Returns:
            Dictionary with progress metrics, history, and recommendations
        """
        if not self.state or not self.workflow:
            return {"status": "not_started", "message": "Workflow not started"}

        monitor = WorkflowProgressMonitor(
            workflow=self.workflow,
            state=self.state,
            event_log=self.event_log,
        )
        return monitor.get_progress_report()
