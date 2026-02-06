"""
Epic Workflow Orchestrator

Executes Epic stories in dependency order with progress tracking and quality gates.
"""

import asyncio
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from ..beads import is_available, run_bd
from ..core.config import ProjectConfig, load_config
from ..workflow.executor import WorkflowExecutor
from ..workflow.parser import WorkflowParser
from .beads_sync import sync_epic_to_beads
from .models import EpicDocument, Story, StoryStatus
from .parser import EpicParser
from .state_manager import EpicStateManager

logger = logging.getLogger(__name__)


class EpicOrchestrator:
    """
    Orchestrates execution of Epic stories in dependency order.

    Features:
    - Dependency resolution (topological sort)
    - Progress tracking across all stories
    - Quality gate enforcement
    - Automatic loopback on quality failures
    - Epic completion reporting
    """

    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
        quality_threshold: float = 70.0,
        critical_service_threshold: float = 80.0,
        enforce_quality_gates: bool = True,
    ):
        """
        Initialize Epic orchestrator.

        Args:
            project_root: Root directory of the project
            config: Project configuration (loaded if None)
            quality_threshold: Minimum quality score for stories (default: 70)
            critical_service_threshold: Minimum quality score for critical services (default: 80)
            enforce_quality_gates: Whether to enforce quality gates (default: True)
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or load_config(self.project_root)
        self.parser = EpicParser(project_root=self.project_root)
        self.quality_threshold = quality_threshold
        self.critical_service_threshold = critical_service_threshold
        self.enforce_quality_gates = enforce_quality_gates

        # Execution state
        self.epic: EpicDocument | None = None
        self.execution_order: list[Story] = []
        self.execution_results: dict[str, dict[str, Any]] = {}
        self.workflow_executor: WorkflowExecutor | None = None
        self._story_to_bd: dict[str, str] = {}
        self._epic_parent_bd_id: str | None = None

        # State persistence (Phase 1.1)
        self.state_manager = EpicStateManager(project_root=self.project_root)
        self._epic_state: dict[str, Any] | None = None

    def load_epic(self, epic_path: Path | str) -> EpicDocument:
        """
        Load and parse an Epic document.

        Args:
            epic_path: Path to Epic markdown file

        Returns:
            Parsed EpicDocument
        """
        self.epic = self.parser.parse(epic_path)
        self.execution_order = self.parser.topological_sort(self.epic)
        logger.info(
            f"Loaded Epic {self.epic.epic_number}: {self.epic.title} "
            f"({len(self.epic.stories)} stories)"
        )

        # Optional: sync epic to Beads when enabled
        if self.config.beads.enabled and self.config.beads.sync_epic:
            from ..beads import require_beads

            try:
                require_beads(self.config, self.project_root)
            except Exception as e:
                logger.error("beads required check failed: %s", e)
                raise
        if (
            self.config.beads.enabled
            and self.config.beads.sync_epic
            and is_available(self.project_root)
        ):
            try:

                def _run_bd(args: list[str], cwd: Path | None = None) -> Any:
                    return run_bd(self.project_root, args, cwd=cwd)

                self._story_to_bd, self._epic_parent_bd_id = sync_epic_to_beads(
                    self.epic, self.project_root, _run_bd, create_parent=True
                )
            except Exception as e:
                logger.warning("beads epic sync failed: %s", e)
                self._story_to_bd = {}
                self._epic_parent_bd_id = None
        else:
            self._story_to_bd = {}
            self._epic_parent_bd_id = None

        # Initialize or load epic state for persistence
        epic_id = f"epic-{self.epic.epic_number}"
        existing_state = self.state_manager.load_state(epic_id)
        if existing_state:
            # Check for content drift
            if self.epic.file_path:
                content = self.epic.file_path.read_text(encoding="utf-8")
                if self.state_manager.check_content_drift(existing_state, content):
                    logger.warning(
                        "Epic content has changed since last run. "
                        "State may be stale. Proceeding with updated content."
                    )
            self._epic_state = existing_state
        else:
            # Create fresh state
            story_states = [
                {
                    "story_id": s.story_id,
                    "title": s.title,
                    "status": "pending",
                    "artifacts": [],
                    "quality_scores": {},
                    "retry_count": 0,
                }
                for s in self.epic.stories
            ]
            content = ""
            if self.epic.file_path:
                content = self.epic.file_path.read_text(encoding="utf-8")
            self._epic_state = self.state_manager.create_initial_state(
                epic_id=epic_id,
                epic_title=self.epic.title,
                epic_path=str(self.epic.file_path or ""),
                epic_content=content,
                stories=story_states,
                execution_order=[s.story_id for s in self.execution_order],
            )
            self.state_manager.save_state(self._epic_state)

        return self.epic

    def _is_framework_epic(self) -> bool:
        """Check if this Epic targets framework code (tapps_agents/)."""
        if not self.epic:
            return False
        for story in self.epic.stories:
            text = f"{story.title} {story.description}".lower()
            if "tapps_agents/" in text or "tapps_agents\\" in text:
                return True
        return False

    async def execute_epic(
        self,
        epic_path: Path | str | None = None,
        max_iterations: int = 3,
        auto_mode: bool = False,
        approved: bool = False,
        story_workflow_mode: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute all stories in the Epic in dependency order.

        Args:
            epic_path: Path to Epic document (if not already loaded)
            max_iterations: Maximum iterations for quality gate loopback
            auto_mode: Whether to run in fully automated mode
            approved: If True, skip approval prompt
            story_workflow_mode: Override workflow mode ('story-only' or 'full')

        Returns:
            Execution report with results for each story
        """
        if epic_path:
            self.load_epic(epic_path)

        if not self.epic:
            raise ValueError("No Epic loaded. Call load_epic() first or provide epic_path.")

        # Resolve story workflow mode
        if story_workflow_mode is None:
            story_workflow_mode = self.config.epic.story_workflow_mode
        # Framework Epics default to full workflow (Phase 2.4)
        if self._is_framework_epic() and story_workflow_mode == "story-only":
            logger.info("Framework Epic detected — using full workflow mode")
            story_workflow_mode = "full"

        # Approval gate (Phase 2.2)
        if not approved and not auto_mode:
            logger.info(
                "Epic %s: %s (%d stories). Approval required (use --approved or --auto to skip).",
                self.epic.epic_number,
                self.epic.title,
                len(self.execution_order),
            )

        logger.info(
            "Starting Epic %s execution: %d stories (mode=%s)",
            self.epic.epic_number,
            len(self.execution_order),
            story_workflow_mode,
        )

        # Initialize workflow executor
        self.workflow_executor = WorkflowExecutor(
            project_root=self.project_root,
            auto_mode=auto_mode,
        )

        # Skip already-completed stories on resume (Phase 1.1)
        completed_ids: set[str] = set()
        if self._epic_state:
            completed_ids = self.state_manager.get_completed_story_ids(self._epic_state)
            if completed_ids:
                logger.info("Resuming: skipping %d completed stories", len(completed_ids))

        # Execute stories: sequential or parallel waves (Phase 3)
        parallel_strategy = self.config.epic.parallel_strategy
        if parallel_strategy == "agent-teams" and len(self.execution_order) > 1:
            # Agent Teams strategy: delegate parallel waves to Claude Code Agent Teams
            await self._execute_agent_teams_or_fallback(
                completed_ids=completed_ids,
                max_iterations=max_iterations,
                story_workflow_mode=story_workflow_mode,
            )
        elif parallel_strategy == "asyncio" and len(self.execution_order) > 1:
            await self._execute_parallel_waves(
                completed_ids=completed_ids,
                max_iterations=max_iterations,
                story_workflow_mode=story_workflow_mode,
            )
        else:
            # Sequential execution (default)
            for story in self.execution_order:
                if story.story_id in completed_ids:
                    logger.info("Skipping completed story %s", story.story_id)
                    continue

                epic_id = f"epic-{self.epic.epic_number}"
                prior_work = self.state_manager.build_prior_work_context(
                    epic_id, last_k=self.config.epic.memory_last_k
                )

                await self._execute_story(
                    story,
                    max_iterations=max_iterations,
                    story_workflow_mode=story_workflow_mode,
                    prior_work_context=prior_work,
                )

        # Close Epic parent bd issue when sync created one
        if self._epic_parent_bd_id:
            try:
                run_bd(self.project_root, ["close", self._epic_parent_bd_id])
            except Exception as e:
                logger.warning("beads close epic parent %s: %s", self._epic_parent_bd_id, e)

        # Generate completion report
        report = self._generate_completion_report()

        # Write session handoff (Phase 4.2)
        if self._epic_state and self.config.epic.auto_handoff:
            epic_id = f"epic-{self.epic.epic_number}"
            self.state_manager.write_handoff(epic_id, self._epic_state)

        logger.info(
            "Epic %s execution complete: %.1f%% complete",
            self.epic.epic_number,
            self.epic.completion_percentage(),
        )

        return report

    async def _execute_story(
        self,
        story: Story,
        max_iterations: int = 3,
        story_workflow_mode: str = "story-only",
        prior_work_context: str = "",
    ) -> dict[str, Any]:
        """
        Execute a single story with quality gates.

        Args:
            story: Story to execute
            max_iterations: Maximum iterations for quality loopback
            story_workflow_mode: 'story-only' or 'full'
            prior_work_context: Prior work text to inject

        Returns:
            Execution result
        """
        logger.info(f"Executing {story.full_id}: {story.title}")

        # Mark story as in progress
        story.status = StoryStatus.IN_PROGRESS

        result: dict[str, Any] = {
            "story_id": story.story_id,
            "title": story.title,
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "iterations": [],
        }

        try:
            # Create workflow for story execution
            workflow_yaml = self._create_story_workflow(story, mode=story_workflow_mode)

            # Parse and execute workflow
            workflow = WorkflowParser.parse_yaml(workflow_yaml)

            # Execute with quality gate loopback
            iteration = 0
            quality_passed = False

            while iteration < max_iterations and not quality_passed:
                iteration += 1
                logger.info(
                    f"Story {story.story_id} iteration {iteration}/{max_iterations}"
                )

                # Execute workflow step
                if not self.workflow_executor.state:
                    self.workflow_executor.user_prompt = (
                        f"{story.title}: {story.description}"
                    )
                    self.workflow_executor.start(workflow=workflow)
                    # Wire story into state so handlers get full Epic context
                    self.workflow_executor.state.variables["description"] = (
                        f"{story.title}: {story.description}"
                    )
                    self.workflow_executor.state.variables["story_description"] = (
                        story.description or ""
                    )
                    self.workflow_executor.state.variables["user_prompt"] = (
                        f"{story.title}: {story.description}"
                    )
                    # Wire acceptance criteria for story-only workflow
                    if story.acceptance_criteria:
                        ac_text = "\n".join(
                            f"- {ac.description}" for ac in story.acceptance_criteria
                        )
                        self.workflow_executor.state.variables["acceptance_criteria"] = ac_text
                    # Wire prior work context (Phase 4.1)
                    if prior_work_context:
                        self.workflow_executor.state.variables["epic_prior_work"] = prior_work_context

                workflow_state = await self.workflow_executor.execute(
                    workflow=workflow, max_steps=50
                )

                # Check quality gates if enforcement is enabled
                if self.enforce_quality_gates:
                    quality_result = await self._check_quality_gates(story)

                    iteration_result = {
                        "iteration": iteration,
                        "workflow_status": workflow_state.status,
                        "quality_passed": quality_result["passed"],
                        "quality_scores": quality_result.get("scores", {}),
                    }

                    result["iterations"].append(iteration_result)

                    if quality_result["passed"]:
                        quality_passed = True
                        logger.info(
                            f"Story {story.story_id} quality gates passed "
                            f"(score: {quality_result.get('overall_score', 'N/A')})"
                        )
                    else:
                        logger.warning(
                            f"Story {story.story_id} quality gates failed. "
                            f"Iteration {iteration}/{max_iterations}"
                        )
                        if iteration < max_iterations:
                            # Trigger improvement loopback
                            await self._trigger_improvement_loopback(
                                story, quality_result
                            )
                else:
                    quality_passed = True  # Skip quality checks

            # Mark story as done if quality passed
            if quality_passed:
                story.status = StoryStatus.DONE
                result["status"] = "done"
                result["completed_at"] = datetime.now().isoformat()
            else:
                story.status = StoryStatus.FAILED
                result["status"] = "failed"
                result["error"] = "Quality gates failed after max iterations"

        except (OSError, RuntimeError, ValueError, KeyError) as e:
            logger.error(f"Error executing story {story.story_id}: {e}", exc_info=True)
            story.status = StoryStatus.FAILED
            result["status"] = "failed"
            result["error"] = str(e)
        except Exception as e:
            logger.error(
                f"Unexpected error executing story {story.story_id}: {type(e).__name__}: {e}",
                exc_info=True,
            )
            story.status = StoryStatus.FAILED
            result["status"] = "failed"
            result["error"] = str(e)

        # Optional: close or cancel bd issue when beads enabled and we have a mapping
        if self.config.beads.enabled and self._story_to_bd:
            bd_id = self._story_to_bd.get(story.story_id)
            if bd_id:
                try:
                    if story.status == StoryStatus.FAILED:
                        try:
                            r = run_bd(
                                self.project_root,
                                ["update", bd_id, "--status", "cancelled"],
                                capture_output=True,
                            )
                            if r.returncode != 0:
                                run_bd(self.project_root, ["close", bd_id])
                        except Exception:
                            run_bd(self.project_root, ["close", bd_id])
                    else:
                        run_bd(self.project_root, ["close", bd_id])
                except Exception as e:
                    logger.warning("beads close %s failed: %s", bd_id, e)

        self.execution_results[story.story_id] = result

        # Persist state after each story (Phase 1.1)
        if self._epic_state and self.epic:
            epic_id = f"epic-{self.epic.epic_number}"
            self.state_manager.update_story_state(
                self._epic_state,
                story_id=story.story_id,
                status=result["status"],
                quality_scores=result.get("iterations", [{}])[-1].get("quality_scores") if result.get("iterations") else None,
                artifacts=result.get("artifacts", []),
                retry_count=len(result.get("iterations", [])),
            )
            self.state_manager.save_state(self._epic_state)

            # Append to memory (Phase 4.1)
            summary = f"{story.title} — {result['status']}"
            self.state_manager.append_memory(
                epic_id=epic_id,
                story_id=story.story_id,
                title=story.title,
                files_changed=result.get("artifacts", []),
                summary=summary,
                quality_scores=result.get("iterations", [{}])[-1].get("quality_scores") if result.get("iterations") else None,
            )

        return result

    # ── Phase 3: Parallel Wave Execution ─────────────────────────────

    def _compute_waves(self, stories: list[Story], completed_ids: set[str]) -> list[list[Story]]:
        """Partition stories into waves based on dependency order."""
        remaining = [s for s in stories if s.story_id not in completed_ids]
        done: set[str] = set(completed_ids)
        waves: list[list[Story]] = []

        while remaining:
            wave = [s for s in remaining if all(d in done for d in s.dependencies)]
            if not wave:
                # Deadlock: remaining stories have unmet deps; run them sequentially
                wave = remaining[:1]
            waves.append(wave)
            for s in wave:
                done.add(s.story_id)
            remaining = [s for s in remaining if s.story_id not in done]

        return waves

    def _detect_file_overlap(self, wave: list[Story]) -> list[tuple[str, str]]:
        """Detect potential file overlaps within a wave (Phase 3.1)."""
        # Infer target files from story title/description
        story_files: dict[str, set[str]] = {}
        for s in wave:
            files: set[str] = set()
            text = f"{s.title} {s.description}"
            # Extract paths that look like file references
            for word in text.split():
                if ("/" in word or "\\" in word) and "." in word.split("/")[-1]:
                    files.add(word.strip(".,;:()\"'"))
            story_files[s.story_id] = files

        overlaps: list[tuple[str, str]] = []
        story_ids = list(story_files.keys())
        for i in range(len(story_ids)):
            for j in range(i + 1, len(story_ids)):
                common = story_files[story_ids[i]] & story_files[story_ids[j]]
                if common:
                    overlaps.append((story_ids[i], story_ids[j]))
        return overlaps

    async def _execute_parallel_waves(
        self,
        completed_ids: set[str],
        max_iterations: int = 3,
        story_workflow_mode: str = "story-only",
    ) -> None:
        """Execute stories in parallel waves (asyncio-based)."""
        waves = self._compute_waves(self.execution_order, completed_ids)
        max_parallel = self.config.epic.max_parallel_stories

        for wave_num, wave in enumerate(waves, 1):
            logger.info("Wave %d: %d stories", wave_num, len(wave))

            # File overlap detection (Phase 3.1)
            if self.config.epic.detect_file_overlap and len(wave) > 1:
                overlaps = self._detect_file_overlap(wave)
                if overlaps:
                    if self.config.epic.strict_parallel:
                        logger.warning(
                            "File overlap detected in wave %d: %s — falling back to sequential",
                            wave_num,
                            overlaps,
                        )
                        # Fall back to sequential for this wave
                        for story in wave:
                            epic_id = f"epic-{self.epic.epic_number}"
                            prior_work = self.state_manager.build_prior_work_context(
                                epic_id, last_k=self.config.epic.memory_last_k
                            )
                            await self._execute_story(
                                story,
                                max_iterations=max_iterations,
                                story_workflow_mode=story_workflow_mode,
                                prior_work_context=prior_work,
                            )
                        continue
                    else:
                        logger.warning("File overlap detected in wave %d: %s (warn only)", wave_num, overlaps)

            # Execute wave stories in parallel (bounded concurrency)
            semaphore = asyncio.Semaphore(max_parallel)

            async def _run_story(story: Story) -> None:
                async with semaphore:
                    epic_id = f"epic-{self.epic.epic_number}"
                    prior_work = self.state_manager.build_prior_work_context(
                        epic_id, last_k=self.config.epic.memory_last_k
                    )
                    await self._execute_story(
                        story,
                        max_iterations=max_iterations,
                        story_workflow_mode=story_workflow_mode,
                        prior_work_context=prior_work,
                    )

            await asyncio.gather(*[_run_story(s) for s in wave])

    # ── Phase 3+: Agent Teams Strategy (stub) ────────────────────────

    async def _execute_agent_teams_or_fallback(
        self,
        completed_ids: set[str],
        max_iterations: int = 3,
        story_workflow_mode: str = "story-only",
    ) -> None:
        """Execute stories using Claude Code Agent Teams, falling back to asyncio.

        The Agent Teams strategy delegates parallel wave execution to the
        Claude Code experimental Agent Teams SDK.  Because the SDK is still
        experimental, this method validates the prerequisites and gracefully
        falls back to the asyncio-based parallel wave executor when they are
        not met.

        Prerequisites:
            1. ``claude`` CLI must be on ``PATH`` (checked via *shutil.which*).
            2. The environment variable
               ``CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`` must be set to ``"1"``.

        When both conditions are satisfied a log message is emitted indicating
        that Agent Teams execution *would* be used, then falls back to asyncio
        (the actual SDK wiring is deferred to a future release).
        """
        claude_available = shutil.which("claude") is not None
        agent_teams_enabled = os.environ.get(
            "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"
        ) == "1"

        if claude_available and agent_teams_enabled:
            logger.info(
                "Agent Teams execution prerequisites met (claude CLI found, "
                "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1). "
                "Actual Agent Teams SDK integration is pending — "
                "falling back to asyncio parallel waves."
            )
        elif not claude_available:
            logger.warning(
                "parallel_strategy is 'agent-teams' but 'claude' CLI was not "
                "found on PATH. Falling back to asyncio parallel wave execution."
            )
        else:
            logger.warning(
                "parallel_strategy is 'agent-teams' but environment variable "
                "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS is not set to '1'. "
                "Falling back to asyncio parallel wave execution."
            )

        # Fall back to asyncio-based parallel waves in all cases for now
        await self._execute_parallel_waves(
            completed_ids=completed_ids,
            max_iterations=max_iterations,
            story_workflow_mode=story_workflow_mode,
        )

    def _create_story_workflow(self, story: Story, mode: str = "story-only") -> str:
        """
        Create a workflow YAML for story execution.

        Args:
            story: Story to create workflow for
            mode: 'story-only' (implement->review->test) or 'full' (enhance->plan->implement->review->test)

        Returns:
            Workflow YAML string
        """
        # Escape quotes in description for YAML
        safe_desc = (story.description or "").replace('"', '\\"')

        if mode == "story-only":
            # Story-only: implement → review → test (Phase 2.1)
            workflow = f"""workflow:
  id: story-{story.story_id}
  name: "Story {story.story_id}: {story.title}"
  description: "{safe_desc}"
  version: "1.0.0"
  type: greenfield
  auto_detect: false

  settings:
    quality_gates: true
    code_scoring: true
    context_tier_default: 2

  steps:
    - id: implement
      agent: implementer
      action: implement
      context_tier: 3
      requires: []
      next: review

    - id: review
      agent: reviewer
      action: review
      context_tier: 2
      requires:
        - implement
      scoring:
        enabled: true
        thresholds:
          overall_min: {self.quality_threshold}
          security_min: 7.0
          maintainability_min: 7.0
      gate:
        condition: "scoring.passed == true"
        on_pass: test
        on_fail: implement
      next: test

    - id: test
      agent: tester
      action: test
      context_tier: 2
      requires:
        - implement
      next: complete

    - id: complete
      agent: orchestrator
      action: finalize
      context_tier: 1
"""
        else:
            # Full workflow: enhance → plan → implement → review → test
            workflow = f"""workflow:
  id: story-{story.story_id}
  name: "Story {story.story_id}: {story.title}"
  description: "{safe_desc}"
  version: "1.0.0"
  type: greenfield
  auto_detect: false

  settings:
    quality_gates: true
    code_scoring: true
    context_tier_default: 2

  steps:
    - id: enhance
      agent: enhancer
      action: enhance
      context_tier: 1
      requires: []
      next: plan

    - id: plan
      agent: planner
      action: plan
      context_tier: 1
      requires:
        - enhance
      next: implement

    - id: implement
      agent: implementer
      action: implement
      context_tier: 3
      requires:
        - plan
      next: review

    - id: review
      agent: reviewer
      action: review
      context_tier: 2
      requires:
        - implement
      scoring:
        enabled: true
        thresholds:
          overall_min: {self.quality_threshold}
          security_min: 7.0
          maintainability_min: 7.0
      gate:
        condition: "scoring.passed == true"
        on_pass: test
        on_fail: implement
      next: test

    - id: test
      agent: tester
      action: test
      context_tier: 2
      requires:
        - implement
      next: complete

    - id: complete
      agent: orchestrator
      action: finalize
      context_tier: 1
"""
        return workflow

    async def _check_quality_gates(self, story: Story) -> dict[str, Any]:
        """
        Check quality gates for a story using actual review scores.

        Extracts reviewer scores from the workflow executor state and
        evaluates them against configured quality thresholds.

        Args:
            story: Story to check

        Returns:
            Quality gate result with scores and pass/fail status
        """
        from ..quality.quality_gates import QualityGate, QualityThresholds

        # Determine threshold (critical services get higher threshold)
        threshold = (
            self.critical_service_threshold
            if self._is_critical_service(story)
            else self.quality_threshold
        )

        thresholds = QualityThresholds(
            overall_min=threshold / 10.0,  # Convert 0-100 to 0-10 scale
            security_min=7.0 if not self._is_critical_service(story) else 8.5,
        )

        quality_gate = QualityGate(thresholds=thresholds)

        # Try to extract reviewer scores from workflow state
        if self.workflow_executor and self.workflow_executor.state:
            state_vars = self.workflow_executor.state.variables

            # Check for gate_last result (set by executor after review step)
            gate_last = state_vars.get("gate_last", {})
            if gate_last:
                return {
                    "passed": gate_last.get("passed", False),
                    "overall_score": gate_last.get("scoring", {}).get(
                        "overall_score", 0
                    ),
                    "scores": gate_last.get("scoring", {}),
                    "gate_result": gate_last.get("gate_result", {}),
                }

            # Fallback: use reviewer_result directly
            reviewer_result = state_vars.get("reviewer_result", {})
            if reviewer_result:
                gate_result = quality_gate.evaluate_from_review_result(
                    reviewer_result, thresholds
                )
                return {
                    "passed": gate_result.passed,
                    "overall_score": gate_result.scores.get("overall_score", 0),
                    "scores": gate_result.scores,
                    "gate_result": gate_result.to_dict(),
                }

        # No review data available — fail if quality gates are enforced
        logger.warning(
            f"Story {story.story_id}: No reviewer scores available for quality gate evaluation"
        )
        return {
            "passed": not self.enforce_quality_gates,
            "overall_score": 0,
            "scores": {},
            "error": "No reviewer scores available",
        }

    def _is_critical_service(self, story: Story) -> bool:
        """Check if story is for a critical service."""
        # Simple heuristic: check if title/description mentions critical terms
        critical_terms = ["auth", "security", "payment", "database", "api gateway"]
        text = (story.title + " " + story.description).lower()
        return any(term in text for term in critical_terms)

    async def _trigger_improvement_loopback(
        self, story: Story, quality_result: dict[str, Any]
    ) -> None:
        """
        Trigger improvement loopback when quality gates fail.

        Args:
            story: Story that failed quality gates
            quality_result: Quality gate result (may include "file", "target_file", "issues")
        """
        logger.info("Triggering improvement loopback for story %s", story.story_id)

        issues = quality_result.get("issues", [])
        target = quality_result.get("file") or quality_result.get("target_file")
        if target:
            target_path = Path(target) if isinstance(target, str) else target
            if not target_path.is_absolute():
                target_path = self.project_root / target_path
            if target_path.exists():
                try:
                    from ..agents.improver.agent import ImproverAgent

                    agent = ImproverAgent(config=self.config)
                    await agent.activate(
                        project_root=self.project_root, offline_mode=True
                    )
                    focus = "; ".join(issues[:15]) if issues else "Address quality gate failures"
                    await agent.run(
                        "improve-quality",
                        file_path=str(target_path),
                        focus=focus,
                        auto_apply=False,
                        preview=False,
                    )
                except Exception as e:
                    logger.warning("Improver invocation failed for story %s: %s", story.story_id, e)
            else:
                logger.warning("Target file does not exist: %s", target_path)
        else:
            logger.info("Quality issues to address (no target file): %s", issues[:5])

    def _generate_completion_report(self) -> dict[str, Any]:
        """
        Generate Epic completion report.

        Returns:
            Report with execution summary
        """
        if not self.epic:
            raise ValueError("No Epic loaded.")

        done_stories = self.epic.get_stories_by_status(StoryStatus.DONE)
        failed_stories = self.epic.get_stories_by_status(StoryStatus.FAILED)
        in_progress_stories = self.epic.get_stories_by_status(StoryStatus.IN_PROGRESS)

        report = {
            "epic_number": self.epic.epic_number,
            "epic_title": self.epic.title,
            "completion_percentage": self.epic.completion_percentage(),
            "total_stories": len(self.epic.stories),
            "done_stories": len(done_stories),
            "failed_stories": len(failed_stories),
            "in_progress_stories": len(in_progress_stories),
            "is_complete": self.epic.is_complete(),
            "stories": [
                {
                    "story_id": s.story_id,
                    "title": s.title,
                    "status": s.status.value,
                    "result": self.execution_results.get(s.story_id, {}),
                }
                for s in self.epic.stories
            ],
            "execution_order": [s.story_id for s in self.execution_order],
            "generated_at": datetime.now().isoformat(),
        }

        return report

    def save_report(self, output_path: Path | None = None) -> Path:
        """
        Save completion report to file.

        Args:
            output_path: Path to save report (defaults to epic directory)

        Returns:
            Path where report was saved
        """
        report = self._generate_completion_report()

        if not output_path:
            if self.epic and self.epic.file_path:
                output_path = self.epic.file_path.parent / f"epic-{self.epic.epic_number}-report.json"
            else:
                output_path = self.project_root / "epic-report.json"

        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info(f"Epic report saved to {output_path}")

        return output_path

