"""Workflow execution metrics tracking."""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class WorkflowMetrics:
    """Workflow execution metrics."""
    workflow_id: str
    workflow_type: str
    start_time: float
    end_time: float
    total_duration: float  # seconds
    total_tokens: int
    steps_completed: int
    steps_skipped: int
    stopped_early: bool
    value_delivered: str
    success: bool
    error_message: str | None = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata if None."""
        if self.metadata is None:
            self.metadata = {}


class WorkflowMetricsTracker:
    """Track workflow execution metrics."""

    def __init__(self, metrics_dir: Path | None = None):
        """
        Initialize metrics tracker.

        Args:
            metrics_dir: Directory to store metrics (default: .tapps-agents/metrics)
        """
        self.metrics_dir = metrics_dir or Path.cwd() / ".tapps-agents" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.active_workflows: dict[str, dict[str, Any]] = {}

    def start_workflow(
        self,
        workflow_id: str,
        workflow_type: str,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Start tracking a workflow.

        Args:
            workflow_id: Unique workflow identifier
            workflow_type: Type of workflow (build, validate, etc.)
            metadata: Optional metadata about the workflow
        """
        self.active_workflows[workflow_id] = {
            "workflow_type": workflow_type,
            "start_time": time.time(),
            "steps_completed": 0,
            "steps_skipped": 0,
            "tokens_used": 0,
            "stopped_early": False,
            "metadata": metadata or {}
        }

    def record_step(
        self,
        workflow_id: str,
        step_name: str,
        tokens_used: int = 0,
        skipped: bool = False
    ) -> None:
        """
        Record a workflow step.

        Args:
            workflow_id: Workflow identifier
            step_name: Name of the step
            tokens_used: Tokens consumed in this step
            skipped: Whether the step was skipped
        """
        if workflow_id not in self.active_workflows:
            return

        workflow = self.active_workflows[workflow_id]

        if skipped:
            workflow["steps_skipped"] += 1
        else:
            workflow["steps_completed"] += 1

        workflow["tokens_used"] += tokens_used

        # Record step details
        if "steps" not in workflow:
            workflow["steps"] = []

        workflow["steps"].append({
            "name": step_name,
            "timestamp": time.time(),
            "tokens": tokens_used,
            "skipped": skipped
        })

    def stop_early(self, workflow_id: str, reason: str) -> None:
        """
        Mark workflow as stopped early.

        Args:
            workflow_id: Workflow identifier
            reason: Reason for early stop
        """
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]["stopped_early"] = True
            self.active_workflows[workflow_id]["stop_reason"] = reason

    def complete_workflow(
        self,
        workflow_id: str,
        success: bool,
        value_delivered: str,
        error_message: str | None = None
    ) -> WorkflowMetrics:
        """
        Complete workflow tracking and generate metrics.

        Args:
            workflow_id: Workflow identifier
            success: Whether workflow completed successfully
            value_delivered: Description of value delivered
            error_message: Optional error message if failed

        Returns:
            WorkflowMetrics object
        """
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.active_workflows[workflow_id]
        end_time = time.time()

        metrics = WorkflowMetrics(
            workflow_id=workflow_id,
            workflow_type=workflow["workflow_type"],
            start_time=workflow["start_time"],
            end_time=end_time,
            total_duration=end_time - workflow["start_time"],
            total_tokens=workflow["tokens_used"],
            steps_completed=workflow["steps_completed"],
            steps_skipped=workflow["steps_skipped"],
            stopped_early=workflow["stopped_early"],
            value_delivered=value_delivered,
            success=success,
            error_message=error_message,
            metadata=workflow["metadata"]
        )

        # Save metrics
        self._save_metrics(metrics)

        # Remove from active workflows
        del self.active_workflows[workflow_id]

        return metrics

    def _save_metrics(self, metrics: WorkflowMetrics) -> None:
        """Save metrics to file."""
        date_str = datetime.fromtimestamp(metrics.start_time).strftime("%Y-%m-%d")
        metrics_file = self.metrics_dir / f"workflow-metrics-{date_str}.jsonl"

        # Append metrics as JSON line
        with open(metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metrics)) + "\n")

    def load_metrics(
        self,
        workflow_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> list[WorkflowMetrics]:
        """
        Load historical metrics.

        Args:
            workflow_type: Optional filter by workflow type
            start_date: Optional filter by start date
            end_date: Optional filter by end date

        Returns:
            List of WorkflowMetrics
        """
        all_metrics: list[WorkflowMetrics] = []

        # Read all metrics files
        for metrics_file in self.metrics_dir.glob("workflow-metrics-*.jsonl"):
            with open(metrics_file, encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        metrics = WorkflowMetrics(**data)

                        # Apply filters
                        if workflow_type and metrics.workflow_type != workflow_type:
                            continue

                        metric_time = datetime.fromtimestamp(metrics.start_time)
                        if start_date and metric_time < start_date:
                            continue
                        if end_date and metric_time > end_date:
                            continue

                        all_metrics.append(metrics)
                    except (json.JSONDecodeError, TypeError):
                        continue

        return all_metrics

    def generate_dashboard(self, metrics: WorkflowMetrics) -> str:
        """
        Generate metrics dashboard.

        Args:
            metrics: Workflow metrics

        Returns:
            Formatted dashboard string
        """
        # Calculate efficiency metrics
        time_saved_pct = self._calculate_time_saved(metrics)
        tokens_saved = self._calculate_tokens_saved(metrics)

        dashboard = f"""
📊 Simple Mode Workflow Metrics

**Workflow:** {metrics.workflow_type}
**Duration:** {metrics.total_duration:.1f}s ({metrics.total_duration / 60:.1f} min)
**Tokens Used:** {metrics.total_tokens:,}
**Steps:** {metrics.steps_completed} completed, {metrics.steps_skipped} skipped
**Success:** {'✅ Yes' if metrics.success else '❌ No'}

**Efficiency:**
- Time Saved: {time_saved_pct}% (vs baseline)
- Tokens Saved: {tokens_saved:,} (vs full workflow)
- Steps Skipped: {metrics.steps_skipped}

**Outcome:** {metrics.value_delivered}
""".strip()

        if metrics.error_message:
            dashboard += f"\n\n**Error:** {metrics.error_message}"

        if metrics.stopped_early:
            dashboard += "\n\n⚡ Workflow optimized: Stopped early (intelligent step skipping)"

        return dashboard

    def _calculate_time_saved(self, metrics: WorkflowMetrics) -> int:
        """Calculate percentage time saved vs baseline."""
        # Baseline durations (hypothetical)
        baselines = {
            "build": 1800,  # 30 min
            "validate": 900,  # 15 min
            "quick-wins": 360,  # 6 min
            "fix": 600,  # 10 min
            "review": 720,  # 12 min
        }

        baseline = baselines.get(metrics.workflow_type, 1200)
        if baseline == 0:
            return 0

        saved = max(0, (baseline - metrics.total_duration) / baseline * 100)
        return int(saved)

    def _calculate_tokens_saved(self, metrics: WorkflowMetrics) -> int:
        """Calculate tokens saved from skipped steps."""
        # Average tokens per step
        avg_tokens_per_step = 10000

        return metrics.steps_skipped * avg_tokens_per_step

    def get_summary_stats(
        self,
        workflow_type: str | None = None,
        days: int = 7
    ) -> dict[str, Any]:
        """
        Get summary statistics for recent workflows.

        Args:
            workflow_type: Optional filter by workflow type
            days: Number of days to include

        Returns:
            Summary statistics dictionary
        """
        from datetime import timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        metrics_list = self.load_metrics(
            workflow_type=workflow_type,
            start_date=start_date,
            end_date=end_date
        )

        if not metrics_list:
            return {
                "total_workflows": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "total_tokens": 0,
                "avg_steps": 0.0
            }

        total_workflows = len(metrics_list)
        successful = sum(1 for m in metrics_list if m.success)
        total_duration = sum(m.total_duration for m in metrics_list)
        total_tokens = sum(m.total_tokens for m in metrics_list)
        total_steps = sum(m.steps_completed for m in metrics_list)

        return {
            "total_workflows": total_workflows,
            "success_rate": (successful / total_workflows * 100) if total_workflows > 0 else 0.0,
            "avg_duration": total_duration / total_workflows if total_workflows > 0 else 0.0,
            "total_tokens": total_tokens,
            "avg_tokens": total_tokens / total_workflows if total_workflows > 0 else 0,
            "avg_steps": total_steps / total_workflows if total_workflows > 0 else 0.0
        }
