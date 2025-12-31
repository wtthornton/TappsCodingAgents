"""
Report Generator - Generates structured markdown reports.
"""

from pathlib import Path
from typing import Any

from .priority_evaluator import HistoryTracker, PriorityEvaluator, PriorityResult


class ReportGenerator:
    """
    Generates structured markdown reports.
    
    Combines analyzer outputs into actionable report with:
    - Executive summary
    - Usage statistics
    - Workflow adherence
    - Quality metrics
    - Prioritized recommendations
    """
    
    def __init__(self, project_root: Path | None = None, config: Any | None = None):
        """
        Initialize report generator.
        
        Args:
            project_root: Project root directory for history tracking
            config: Project configuration
        """
        self.project_root = project_root or Path.cwd()
        self.config = config
        self.priority_evaluator = PriorityEvaluator(config=config, project_root=self.project_root)
        self.history_tracker = HistoryTracker(project_root=self.project_root)

    def generate_report(
        self,
        usage_data: dict[str, Any],
        workflow_data: dict[str, Any] | None = None,
        quality_data: dict[str, Any] | None = None
    ) -> str:
        """
        Generate markdown report from analyzer outputs.
        
        Args:
            usage_data: Output from UsageAnalyzer
            workflow_data: Output from WorkflowAnalyzer (optional)
            quality_data: Output from QualityAnalyzer (optional)
        
        Returns:
            Markdown report as string
        """
        # Build report sections
        sections = []
        
        # Title
        sections.append("# TappsCodingAgents Evaluation Report\n")
        
        # Executive Summary
        sections.append(self._generate_executive_summary(
            usage_data, workflow_data, quality_data
        ))
        
        # Usage Statistics
        sections.append(self._generate_usage_section(usage_data))
        
        # Workflow Adherence (if available)
        if workflow_data:
            sections.append(self._generate_workflow_section(workflow_data))
        
        # Quality Metrics (if available)
        if quality_data:
            sections.append(self._generate_quality_section(quality_data))
        
        # Recommendations
        recommendations = self._collect_recommendations(
            usage_data, workflow_data, quality_data
        )
        prioritized = self.prioritize_recommendations(
            recommendations,
            quality_data=quality_data,
            workflow_data=workflow_data,
            usage_data=usage_data
        )
        sections.append(self._generate_recommendations_section(prioritized))
        
        return "\n\n".join(sections)

    def _generate_executive_summary(
        self,
        usage_data: dict[str, Any],
        workflow_data: dict[str, Any] | None,
        quality_data: dict[str, Any] | None
    ) -> str:
        """Generate executive summary section."""
        lines = ["## Executive Summary (TL;DR)\n"]
        
        # Quick stats
        stats = usage_data.get("statistics", {})
        total_commands = stats.get("total_commands", 0)
        simple_mode = stats.get("simple_mode", 0)
        
        lines.append(f"- **Total Commands Executed:** {total_commands}")
        lines.append(f"- **Simple Mode Usage:** {simple_mode} ({simple_mode/total_commands*100:.1f}%)" if total_commands > 0 else "- **Simple Mode Usage:** 0")
        
        # Top recommendations
        recommendations = self._collect_recommendations(usage_data, workflow_data, quality_data)
        prioritized = self.prioritize_recommendations(
            recommendations,
            quality_data=quality_data,
            workflow_data=workflow_data,
            usage_data=usage_data,
            track_history=False  # Don't track in summary
        )
        top_3 = prioritized.get("priority_1", [])[:3]
        
        if top_3:
            lines.append("\n**Top 3 Recommendations:**")
            for i, rec in enumerate(top_3, 1):
                lines.append(f"{i}. {rec.get('recommendation', 'N/A')}")
        
        return "\n".join(lines)

    def _generate_usage_section(self, usage_data: dict[str, Any]) -> str:
        """Generate usage statistics section."""
        lines = ["## Usage Statistics\n"]
        
        stats = usage_data.get("statistics", {})
        total = stats.get("total_commands", 0)
        
        if total == 0:
            lines.append("No command usage data available.")
            return "\n".join(lines)
        
        lines.append(f"- **Total Commands:** {total}")
        lines.append(f"- **CLI Commands:** {stats.get('cli_commands', 0)}")
        lines.append(f"- **Cursor Skills:** {stats.get('cursor_skills', 0)}")
        lines.append(f"- **Simple Mode:** {stats.get('simple_mode', 0)}")
        lines.append(f"- **Success Rate:** {stats.get('command_success_rate', 0.0):.1%}")
        
        # Agent usage
        agent_usage = stats.get("agent_usage", {})
        if agent_usage:
            lines.append("\n**Agent Usage:**")
            for agent, count in sorted(agent_usage.items(), key=lambda x: x[1], reverse=True)[:10]:
                lines.append(f"- {agent}: {count}")
        
        return "\n".join(lines)

    def _generate_workflow_section(self, workflow_data: dict[str, Any]) -> str:
        """Generate workflow adherence section."""
        lines = ["## Workflow Adherence\n"]
        
        workflow_id = workflow_data.get("workflow_id", "unknown")
        step_analysis = workflow_data.get("step_analysis", {})
        artifact_analysis = workflow_data.get("artifact_analysis", {})
        
        lines.append(f"- **Workflow ID:** {workflow_id}")
        lines.append(f"- **Steps Executed:** {step_analysis.get('steps_executed', 0)}/{step_analysis.get('steps_required', 0)}")
        lines.append(f"- **Completion Rate:** {step_analysis.get('completion_rate', 0.0):.1%}")
        lines.append(f"- **Artifacts Created:** {len(artifact_analysis.get('artifacts_created', []))}/{len(artifact_analysis.get('artifacts_expected', []))}")
        
        # Deviations
        deviations = workflow_data.get("deviations", [])
        if deviations:
            lines.append("\n**Deviations Identified:**")
            for dev in deviations:
                lines.append(f"- {dev.get('description', 'N/A')}")
        
        return "\n".join(lines)

    def _generate_quality_section(self, quality_data: dict[str, Any]) -> str:
        """Generate quality metrics section."""
        lines = ["## Quality Metrics\n"]
        
        scores = quality_data.get("scores", {})
        if scores:
            overall = scores.get("overall", 0.0)
            lines.append(f"- **Overall Score:** {overall:.1f}/100")
            
            for metric, score in scores.items():
                if metric != "overall":
                    lines.append(f"- **{metric.capitalize()}:** {score:.1f}/10")
        
        # Issues
        issues = quality_data.get("issues", [])
        if issues:
            lines.append("\n**Quality Issues:**")
            for issue in issues[:10]:  # Limit to top 10
                lines.append(f"- {issue.get('metric', 'N/A')}: {issue.get('score', 0.0):.1f} (threshold: {issue.get('threshold', 0.0):.1f})")
        
        return "\n".join(lines)

    def _collect_recommendations(
        self,
        usage_data: dict[str, Any],
        workflow_data: dict[str, Any] | None,
        quality_data: dict[str, Any] | None
    ) -> list[dict]:
        """Collect all recommendations from analyzers."""
        recommendations = []
        
        # From usage data
        usage_recs = usage_data.get("recommendations", [])
        recommendations.extend(usage_recs)
        
        # From workflow data
        if workflow_data:
            workflow_recs = workflow_data.get("recommendations", [])
            recommendations.extend(workflow_recs)
        
        # From quality data
        if quality_data:
            quality_recs = quality_data.get("recommendations", [])
            recommendations.extend(quality_recs)
        
        return recommendations

    def prioritize_recommendations(
        self,
        recommendations: list[dict],
        quality_data: dict[str, Any] | None = None,
        workflow_data: dict[str, Any] | None = None,
        usage_data: dict[str, Any] | None = None,
        track_history: bool = True
    ) -> dict[str, list[dict]]:
        """
        Prioritize recommendations using objective evaluation.
        
        Uses PriorityEvaluator for consistent, independent priority assignment.
        
        Args:
            recommendations: List of recommendation dictionaries
            quality_data: Quality analysis data (optional)
            workflow_data: Workflow analysis data (optional)
            usage_data: Usage analysis data (optional)
            track_history: Whether to track evaluation in history (default: True)
        
        Returns:
            Dictionary with prioritized recommendations grouped by priority level
        """
        prioritized_results: list[PriorityResult] = []
        recommendation_metadata = []
        
        for rec in recommendations:
            result = self.priority_evaluator.evaluate(
                recommendation=rec,
                quality_data=quality_data,
                workflow_data=workflow_data,
                usage_data=usage_data
            )
            prioritized_results.append(result)
            recommendation_metadata.append({
                "id": rec.get("id"),
                "description": rec.get("description", rec.get("recommendation", ""))
            })
        
        # Track in history if enabled
        if track_history and self.priority_evaluator.enable_history:
            try:
                evaluation_id = f"eval-{quality_data.get('evaluation_id', 'unknown')}" if quality_data else "eval-unknown"
                self.history_tracker.track(
                    evaluation_id=evaluation_id,
                    recommendations=prioritized_results,
                    metadata={
                        "recommendations": recommendation_metadata,
                        "evaluation_date": quality_data.get("evaluation_date") if quality_data else None
                    }
                )
            except Exception:
                # Don't fail if history tracking fails
                pass
        
        # Group by priority
        priority_1 = []
        priority_2 = []
        priority_3 = []
        priority_4 = []
        
        for i, rec in enumerate(recommendations):
            result = prioritized_results[i]
            enhanced_rec = {
                **rec,
                "priority": result.priority,
                "priority_score": result.score,
                "priority_factors": result.factors,
                "priority_rationale": result.rationale
            }
            
            if result.priority == "critical":
                priority_1.append(enhanced_rec)
            elif result.priority == "high":
                priority_2.append(enhanced_rec)
            elif result.priority == "medium":
                priority_3.append(enhanced_rec)
            else:  # low
                priority_4.append(enhanced_rec)
        
        return {
            "priority_1": priority_1,
            "priority_2": priority_2,
            "priority_3": priority_3,
            "priority_4": priority_4,
        }

    def _generate_recommendations_section(
        self,
        prioritized: dict[str, list[dict]]
    ) -> str:
        """Generate recommendations section."""
        lines = ["## Recommendations\n"]
        
        for priority_level in ["priority_1", "priority_2", "priority_3", "priority_4"]:
            recs = prioritized.get(priority_level, [])
            if not recs:
                continue
            
            # Format priority name
            priority_name = priority_level.replace("_", " ").title()
            if priority_level == "priority_1":
                priority_name = "Priority 1 (Critical)"
            elif priority_level == "priority_2":
                priority_name = "Priority 2 (High)"
            elif priority_level == "priority_3":
                priority_name = "Priority 3 (Medium)"
            else:
                priority_name = "Priority 4 (Low)"
            
            lines.append(f"### {priority_name}\n")
            
            for rec in recs:
                description = rec.get("description", rec.get("recommendation", "N/A"))
                recommendation = rec.get("recommendation", "N/A")
                priority_score = rec.get("priority_score", 0.0)
                priority_rationale = rec.get("priority_rationale", "")
                
                lines.append(f"- **{description}**")
                lines.append(f"  - Recommendation: {recommendation}")
                lines.append(f"  - Priority Score: {priority_score:.2f}/10.0")
                if priority_rationale:
                    lines.append(f"  - Rationale: {priority_rationale}")
                lines.append("")
        
        return "\n".join(lines)
