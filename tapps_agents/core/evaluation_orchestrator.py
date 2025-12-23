"""
Evaluation orchestrator for multi-dimensional evaluation.

Coordinates multiple evaluators and aggregates results.
"""

import logging
from pathlib import Path
from typing import Any

from .evaluation_models import EvaluationResult, IssueManifest
from .evaluators.architectural_evaluator import ArchitecturalEvaluator
from .evaluators.behavioral_evaluator import BehavioralEvaluator
from .evaluators.performance_profile_evaluator import PerformanceProfileEvaluator
from .evaluators.security_posture_evaluator import SecurityPostureEvaluator
from .evaluators.spec_compliance_evaluator import SpecComplianceEvaluator

logger = logging.getLogger(__name__)


class EvaluationOrchestrator:
    """
    Orchestrates multi-dimensional evaluation using multiple evaluators.
    
    Coordinates evaluation, aggregates results, and generates reports.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize evaluation orchestrator.
        
        Args:
            config: Optional configuration for evaluators
        """
        self.config = config or {}
        self.evaluators = self._initialize_evaluators()

    def _initialize_evaluators(self) -> list[Any]:
        """Initialize all available evaluators."""
        evaluators = []
        
        # Behavioral evaluator
        if self.config.get("behavioral", {}).get("enabled", True):
            evaluators.append(BehavioralEvaluator())
        
        # Spec compliance evaluator
        if self.config.get("spec_compliance", {}).get("enabled", True):
            workflow_state = self.config.get("workflow_state")
            evaluators.append(SpecComplianceEvaluator(workflow_state=workflow_state))
        
        # Architectural evaluator
        if self.config.get("architectural", {}).get("enabled", True):
            pattern_catalog = self.config.get("pattern_catalog", {})
            evaluators.append(ArchitecturalEvaluator(pattern_catalog=pattern_catalog))
        
        # Security posture evaluator
        if self.config.get("security_posture", {}).get("enabled", True):
            evaluators.append(SecurityPostureEvaluator())
        
        # Performance profile evaluator
        if self.config.get("performance_profile", {}).get("enabled", True):
            evaluators.append(PerformanceProfileEvaluator())
        
        return evaluators

    def evaluate(
        self,
        target: Path | str,
        scores: dict[str, float] | None = None,
        context: dict[str, Any] | None = None,
    ) -> EvaluationResult:
        """
        Perform comprehensive evaluation.
        
        Args:
            target: File path or identifier to evaluate
            scores: Optional quality scores (from scoring system)
            context: Optional context for evaluation
            
        Returns:
            EvaluationResult with aggregated scores and issues
        """
        target_path = Path(target) if isinstance(target, str) else target
        all_issues = IssueManifest()
        
        # Run all applicable evaluators
        for evaluator in self.evaluators:
            if evaluator.is_applicable(target_path):
                try:
                    evaluator_issues = evaluator.evaluate(target_path, context)
                    all_issues = all_issues.merge(evaluator_issues)
                except Exception as e:
                    logger.warning(f"Error in {evaluator.get_name()} evaluator: {e}")
        
        # Deduplicate and prioritize issues
        all_issues = all_issues.deduplicate()
        all_issues = all_issues.prioritize()
        
        # Calculate overall score from issues (if scores not provided)
        if scores is None:
            scores = self._calculate_scores_from_issues(all_issues)
        
        overall_score = scores.get("overall_score", 0.0)
        
        # Create evaluation result
        result = EvaluationResult(
            overall_score=overall_score,
            scores=scores,
            issues=all_issues,
            metadata={
                "evaluators_run": [e.get_name() for e in self.evaluators],
                "target": str(target_path),
            },
        )
        
        return result

    def _calculate_scores_from_issues(
        self, issues: IssueManifest
    ) -> dict[str, float]:
        """Calculate quality scores from issues (simplified)."""
        scores: dict[str, float] = {}
        
        # Start with perfect scores
        overall = 100.0
        security = 10.0
        maintainability = 10.0
        performance = 10.0
        
        # Deduct points based on issues
        severity_penalties = {
            "critical": 5.0,
            "high": 2.0,
            "medium": 1.0,
            "low": 0.5,
        }
        
        for issue in issues.issues:
            penalty = severity_penalties.get(issue.severity.value, 0.0)
            overall -= penalty
            
            if issue.category.value == "security":
                security -= penalty * 0.5
            elif issue.category.value == "maintainability":
                maintainability -= penalty * 0.5
            elif issue.category.value == "performance":
                performance -= penalty * 0.5
        
        scores["overall_score"] = max(0.0, overall)
        scores["security_score"] = max(0.0, min(10.0, security))
        scores["maintainability_score"] = max(0.0, min(10.0, maintainability))
        scores["performance_score"] = max(0.0, min(10.0, performance))
        
        return scores

    def generate_report(
        self, result: EvaluationResult, format: str = "markdown"
    ) -> str:
        """
        Generate evaluation report.
        
        Args:
            result: Evaluation result
            format: Report format (markdown, json, html)
            
        Returns:
            Report as string
        """
        if format == "json":
            import json
            return json.dumps(result.to_dict(), indent=2)
        
        elif format == "html":
            # Generate HTML report
            html = f"""<!DOCTYPE html>
<html>
<head><title>Evaluation Report</title></head>
<body>
<h1>Evaluation Report</h1>
<h2>Overall Score: {result.overall_score:.1f}/100</h2>
<h2>Issues Found: {len(result.issues.issues)}</h2>
<h3>By Severity:</h3>
<ul>
"""
            counts = result.issues.count_by_severity()
            for severity, count in counts.items():
                html += f"<li>{severity.value}: {count}</li>\n"
            
            html += """</ul>
<h3>Issues:</h3>
<ul>
"""
            for issue in result.issues.issues[:20]:  # Limit to first 20
                html += f"<li><strong>{issue.id}</strong>: {issue.evidence[:100]}...</li>\n"
            
            html += """</ul>
</body>
</html>
"""
            return html
        
        else:  # markdown
            report = f"""# Evaluation Report

## Overall Score: {result.overall_score:.1f}/100

## Scores

"""
            for key, value in result.scores.items():
                report += f"- **{key}**: {value:.2f}\n"
            
            report += f"\n## Issues Found: {len(result.issues.issues)}\n\n"
            
            counts = result.issues.count_by_severity()
            report += "### By Severity\n\n"
            for severity, count in counts.items():
                report += f"- {severity.value}: {count}\n"
            
            report += "\n### Critical Issues\n\n"
            for issue in result.issues.get_critical_issues()[:10]:
                report += f"- **{issue.id}**: {issue.evidence}\n"
            
            return report

