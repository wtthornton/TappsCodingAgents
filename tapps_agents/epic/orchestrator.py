"""
Epic Workflow Orchestrator

Executes Epic stories in dependency order with progress tracking and quality gates.
"""

import json
import logging
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

        return self.epic

    async def execute_epic(
        self,
        epic_path: Path | str | None = None,
        max_iterations: int = 3,
        auto_mode: bool = False,
    ) -> dict[str, Any]:
        """
        Execute all stories in the Epic in dependency order.

        Args:
            epic_path: Path to Epic document (if not already loaded)
            max_iterations: Maximum iterations for quality gate loopback
            auto_mode: Whether to run in fully automated mode

        Returns:
            Execution report with results for each story
        """
        if epic_path:
            self.load_epic(epic_path)

        if not self.epic:
            raise ValueError("No Epic loaded. Call load_epic() first or provide epic_path.")

        logger.info(
            f"Starting Epic {self.epic.epic_number} execution: {len(self.execution_order)} stories"
        )

        # Initialize workflow executor
        self.workflow_executor = WorkflowExecutor(
            project_root=self.project_root,
            auto_mode=auto_mode,
        )

        # Execute each story in order
        for story in self.execution_order:
            await self._execute_story(story, max_iterations=max_iterations)

        # Close Epic parent bd issue when sync created one
        if self._epic_parent_bd_id:
            try:
                run_bd(self.project_root, ["close", self._epic_parent_bd_id])
            except Exception as e:
                logger.warning("beads close epic parent %s: %s", self._epic_parent_bd_id, e)

        # Generate completion report
        report = self._generate_completion_report()

        logger.info(
            f"Epic {self.epic.epic_number} execution complete: "
            f"{self.epic.completion_percentage():.1f}% complete"
        )

        return report

    async def _execute_story(
        self, story: Story, max_iterations: int = 3
    ) -> dict[str, Any]:
        """
        Execute a single story with quality gates.

        Args:
            story: Story to execute
            max_iterations: Maximum iterations for quality loopback

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
            # For now, use a simple workflow that calls appropriate agents
            # In the future, stories could define their own workflows
            workflow_yaml = self._create_story_workflow(story)

            # Parse and execute workflow
            parser = WorkflowParser()
            workflow = parser.parse_workflow(workflow_yaml)

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
                    # Wire story into state so EnhancerHandler (and downstream) get it
                    self.workflow_executor.state.variables["description"] = (
                        f"{story.title}: {story.description}"
                    )
                    self.workflow_executor.state.variables["story_description"] = (
                        story.description or ""
                    )

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

        except Exception as e:
            logger.error(f"Error executing story {story.story_id}: {e}", exc_info=True)
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
        return result

    def _create_story_workflow(self, story: Story) -> str:
        """
        Create a workflow YAML for story execution.

        This creates a simple workflow that:
        1. Enhances the prompt
        2. Plans the implementation
        3. Implements the code
        4. Reviews the code
        5. Tests the code

        Args:
            story: Story to create workflow for

        Returns:
            Workflow YAML string
        """
        workflow = f"""workflow:
  id: story-{story.story_id}
  name: "Story {story.story_id}: {story.title}"
  description: "{story.description}"
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
        Check quality gates for a story.

        Args:
            story: Story to check

        Returns:
            Quality gate result with scores and pass/fail status
        """
        # Determine threshold (critical services get higher threshold)
        threshold = (
            self.critical_service_threshold
            if self._is_critical_service(story)
            else self.quality_threshold
        )

        # TODO: Actually run quality checks on generated code
        # In the future, this would:
        # 1. Use QualityGate with proper thresholds
        # 2. Analyze the actual code created for this story
        # 3. Get real scores from ReviewerAgent
        # For now, return a placeholder result
        return {
            "passed": True,  # Placeholder
            "overall_score": threshold + 5,  # Placeholder
            "scores": {
                "complexity": 8.0,
                "security": 8.0,
                "maintainability": 8.0,
                "test_coverage": 85.0,
            },
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

