"""
Evaluator Agent - Evaluates TappsCodingAgents framework effectiveness.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
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

    async def activate(self, project_root: Path | None = None, offline_mode: bool = False):
        """Activate the evaluator agent."""
        await super().activate(project_root, offline_mode=offline_mode)
        self._project_root = project_root or Path.cwd()
        
        # Initialize analyzers
        self.usage_analyzer = UsageAnalyzer()
        self.workflow_analyzer = WorkflowAnalyzer()
        self.quality_analyzer = QualityAnalyzer()
        self.report_generator = ReportGenerator(project_root=self._project_root, config=self.config)

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
        ]

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute evaluator commands.
        
        Commands:
        - evaluate: Run full evaluation
        - evaluate-workflow <workflow_id>: Evaluate specific workflow
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

    async def close(self) -> None:
        """Cleanup resources."""
        await super().close()
        # Analyzers don't require cleanup
