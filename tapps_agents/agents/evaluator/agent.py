"""
Evaluator Agent - Evaluates TappsCodingAgents framework effectiveness.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.external_feedback_models import (
    ExternalFeedbackData,
    FeedbackContext,
    FeedbackMetrics,
)
from ...core.external_feedback_storage import ExternalFeedbackStorage
from .quality_analyzer import QualityAnalyzer
from .report_generator import ReportGenerator
from .usage_analyzer import UsageAnalyzer
from .workflow_analyzer import WorkflowAnalyzer


class EvaluatorAgent(BaseAgent):
    """
    Evaluator Agent - Evaluates TappsCodingAgents framework effectiveness.
    
    Provides analysis of:
    - Command usage patterns (CLI vs Cursor Skills vs Simple Mode)
    - Workflow adherence (did users follow intended workflows?)
    - Code quality metrics
    - Actionable recommendations for continuous improvement
    """

    def __init__(self, config: ProjectConfig | None = None):
        super().__init__(
            agent_id="evaluator",
            agent_name="Evaluator Agent",
            config=config
        )
        if config is None:
            config = load_config()
        self.config = config
        
        # Analyzers (lazy initialization)
        self.usage_analyzer: UsageAnalyzer | None = None
        self.workflow_analyzer: WorkflowAnalyzer | None = None
        self.quality_analyzer: QualityAnalyzer | None = None
        self.report_generator: ReportGenerator | None = None
        self._project_root: Path | None = None
        self._feedback_storage: ExternalFeedbackStorage | None = None

    async def activate(self, project_root: Path | None = None, offline_mode: bool = False):
        """Activate the evaluator agent."""
        await super().activate(project_root, offline_mode=offline_mode)
        self._project_root = project_root or Path.cwd()
        
        # Initialize analyzers
        self.usage_analyzer = UsageAnalyzer()
        self.workflow_analyzer = WorkflowAnalyzer()
        self.quality_analyzer = QualityAnalyzer()
        self.report_generator = ReportGenerator(project_root=self._project_root, config=self.config)
        self._feedback_storage = ExternalFeedbackStorage(project_root=self._project_root)

    def get_commands(self) -> list[dict[str, str]]:
        """Return available commands for evaluator agent."""
        base_commands = super().get_commands()
        return base_commands + [
            {
                "command": "*evaluate",
                "description": "Evaluate framework effectiveness",
            },
            {
                "command": "*evaluate-workflow",
                "description": "Evaluate specific workflow",
            },
            {
                "command": "*submit-feedback",
                "description": "Submit external feedback about framework performance",
            },
            {
                "command": "*get-feedback",
                "description": "Retrieve feedback by ID",
            },
            {
                "command": "*list-feedback",
                "description": "List feedback entries with optional filtering",
            },
        ]

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute evaluator commands.
        
        Commands:
        - evaluate: Run full evaluation
        - evaluate-workflow <workflow_id>: Evaluate specific workflow
        - submit-feedback: Submit external feedback about framework performance
        - get-feedback <feedback_id>: Retrieve feedback by ID
        - list-feedback: List feedback entries with optional filtering
        - help: Show help
        """
        command = command.lstrip("*")
        
        if command == "help":
            return {"type": "help", "content": self.format_help()}
        elif command == "evaluate":
            workflow_id = kwargs.get("workflow_id")
            return await self._evaluate(workflow_id=workflow_id)
        elif command == "evaluate-workflow":
            workflow_id = kwargs.get("workflow_id")
            if not workflow_id:
                return {"error": "workflow_id is required"}
            return await self._evaluate_workflow(workflow_id)
        elif command == "submit-feedback":
            return await self._handle_submit_feedback(**kwargs)
        elif command == "get-feedback":
            feedback_id = kwargs.get("feedback_id")
            if not feedback_id:
                return {"error": "feedback_id is required"}
            return await self._handle_get_feedback(feedback_id)
        elif command == "list-feedback":
            return await self._handle_list_feedback(**kwargs)
        else:
            return {"error": f"Unknown command: {command}"}

    async def _evaluate(self, workflow_id: str | None = None) -> dict[str, Any]:
        """
        Run full evaluation.
        
        Args:
            workflow_id: Optional workflow ID to evaluate
            
        Returns:
            Dictionary with evaluation results
        """
        if not self.usage_analyzer:
            await self.activate()
        
        # Collect data sources
        workflow_state = None
        if workflow_id and self._project_root:
            workflow_state = self._load_workflow_state(workflow_id)
        
        # Run analyzers
        usage_data = self.usage_analyzer.analyze_usage(workflow_state=workflow_state)
        workflow_data = None
        quality_data = None
        
        if workflow_state:
            workflow_data = self.workflow_analyzer.analyze_workflow(
                workflow_id=workflow_id or "unknown",
                workflow_state=workflow_state
            )
            quality_data = self.quality_analyzer.analyze_quality(
                workflow_state=workflow_state
            )
        
        # Generate report
        report = self.report_generator.generate_report(
            usage_data=usage_data,
            workflow_data=workflow_data,
            quality_data=quality_data
        )
        
        # Save report
        output_path = self._save_report(report, workflow_id)
        
        return {
            "success": True,
            "report": report,
            "output_file": str(output_path),
            "usage_data": usage_data,
            "workflow_data": workflow_data,
            "quality_data": quality_data,
        }

    async def _evaluate_workflow(self, workflow_id: str) -> dict[str, Any]:
        """
        Evaluate specific workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Dictionary with workflow evaluation results
        """
        if not self.workflow_analyzer:
            await self.activate()
        
        # Load workflow state
        workflow_state = self._load_workflow_state(workflow_id)
        if not workflow_state:
            return {"error": f"Workflow {workflow_id} not found"}
        
        # Analyze workflow
        workflow_data = self.workflow_analyzer.analyze_workflow(
            workflow_id=workflow_id,
            workflow_state=workflow_state
        )
        
        # Analyze quality if available
        quality_data = self.quality_analyzer.analyze_quality(
            workflow_state=workflow_state
        )
        
        # Generate report
        usage_data = self.usage_analyzer.analyze_usage(workflow_state=workflow_state)
        report = self.report_generator.generate_report(
            usage_data=usage_data,
            workflow_data=workflow_data,
            quality_data=quality_data
        )
        
        # Save report
        output_path = self._save_report(report, workflow_id)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "report": report,
            "output_file": str(output_path),
            "workflow_data": workflow_data,
            "quality_data": quality_data,
        }

    def _load_workflow_state(self, workflow_id: str) -> dict[str, Any] | None:
        """Load workflow state from file system."""
        if not self._project_root:
            return None
        
        # Try to find workflow state file
        state_paths = [
            self._project_root / ".tapps-agents" / "worktrees" / f"{workflow_id}" / "state.json",
            self._project_root / ".tapps-agents" / "workflows" / f"{workflow_id}.json",
        ]
        
        for state_path in state_paths:
            if state_path.exists():
                try:
                    return json.loads(state_path.read_text(encoding="utf-8"))
                except Exception:
                    continue
        
        return None

    def _save_report(self, report: str, workflow_id: str | None = None) -> Path:
        """Save evaluation report to file."""
        if not self._project_root:
            self._project_root = Path.cwd()
        
        # Create output directory
        output_dir = self._project_root / ".tapps-agents" / "evaluations"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        if workflow_id:
            filename = f"evaluation-{workflow_id}-{timestamp}.md"
        else:
            filename = f"evaluation-{timestamp}.md"
        
        output_path = output_dir / filename
        
        # Save report
        output_path.write_text(report, encoding="utf-8")
        
        return output_path

    async def _handle_submit_feedback(
        self,
        performance_ratings: dict[str, float],
        suggestions: list[str],
        context: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Handle feedback submission from external projects.

        Args:
            performance_ratings: Dictionary of metric names to ratings
            suggestions: List of improvement suggestions
            context: Optional context information
            metrics: Optional performance metrics
            project_id: Optional project identifier

        Returns:
            Dictionary with submission result
        """
        if not self._feedback_storage:
            await self.activate()

        try:
            # Build feedback context
            feedback_context = None
            if context:
                feedback_context = FeedbackContext(**context)

            # Build feedback metrics
            feedback_metrics = None
            if metrics:
                feedback_metrics = FeedbackMetrics(**metrics)

            # Create feedback data
            feedback_data = ExternalFeedbackData(
                performance_ratings=performance_ratings,
                suggestions=suggestions,
                context=feedback_context,
                metrics=feedback_metrics,
                project_id=project_id,
            )

            # Save feedback
            file_path = self._feedback_storage.save_feedback(feedback_data)

            return {
                "success": True,
                "feedback_id": feedback_data.feedback_id,
                "message": "Feedback submitted successfully",
                "timestamp": feedback_data.timestamp.isoformat(),
                "file_path": str(file_path),
            }
        except ValueError as e:
            return {"error": f"Validation error: {e!s}"}
        except Exception as e:
            return {"error": f"Failed to submit feedback: {e!s}"}

    async def _handle_get_feedback(self, feedback_id: str) -> dict[str, Any]:
        """
        Handle feedback retrieval by ID.

        Args:
            feedback_id: Feedback UUID

        Returns:
            Dictionary with feedback data
        """
        if not self._feedback_storage:
            await self.activate()

        feedback = self._feedback_storage.load_feedback(feedback_id)
        if not feedback:
            return {"error": f"Feedback not found: {feedback_id}"}

        return {
            "success": True,
            "feedback": feedback.to_dict(),
        }

    async def _handle_list_feedback(
        self,
        workflow_id: str | None = None,
        agent_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Handle feedback listing with optional filtering.

        Args:
            workflow_id: Filter by workflow ID
            agent_id: Filter by agent ID
            start_date: Filter by start date (ISO format string)
            end_date: Filter by end date (ISO format string)
            limit: Maximum number of entries

        Returns:
            Dictionary with feedback list
        """
        if not self._feedback_storage:
            await self.activate()

        # Parse dates
        start_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                return {"error": f"Invalid start_date format: {start_date}"}

        end_dt = None
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                return {"error": f"Invalid end_date format: {end_date}"}

        feedback_entries = self._feedback_storage.list_feedback(
            workflow_id=workflow_id,
            agent_id=agent_id,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit,
        )

        return {
            "success": True,
            "count": len(feedback_entries),
            "feedback": [entry.to_dict() for entry in feedback_entries],
        }

    async def submit_feedback(
        self,
        performance_ratings: dict[str, float],
        suggestions: list[str],
        context: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Submit feedback about TappsCodingAgents performance (public API method).

        Args:
            performance_ratings: Dictionary of metric names to ratings (typically 1.0-10.0)
            suggestions: List of improvement suggestions
            context: Optional context information (workflow_id, agent_id, task_type, etc.)
            metrics: Optional performance metrics (execution_time_seconds, quality_score, etc.)
            project_id: Optional project identifier

        Returns:
            Dictionary with submission result containing feedback_id

        Example:
            ```python
            result = await evaluator.submit_feedback(
                performance_ratings={"overall": 8.5, "usability": 7.0},
                suggestions=["Improve error messages"],
                context={"workflow_id": "workflow-123", "agent_id": "reviewer"},
                project_id="my-project-v1.0"
            )
            print(f"Feedback ID: {result['feedback_id']}")
            ```
        """
        return await self._handle_submit_feedback(
            performance_ratings=performance_ratings,
            suggestions=suggestions,
            context=context,
            metrics=metrics,
            project_id=project_id,
        )

    async def close(self) -> None:
        """Cleanup resources."""
        await super().close()
        # Analyzers don't require cleanup
