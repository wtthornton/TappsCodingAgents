"""
Change Impact Analyzer - Analyzes impact of requirement changes on stories, designs, and implementation.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChangeImpact:
    """Impact of a requirement change."""

    requirement_id: str
    change_type: str  # "added", "modified", "removed"
    affected_stories: list[str] = field(default_factory=list)
    affected_designs: list[str] = field(default_factory=list)
    affected_implementations: list[str] = field(default_factory=list)
    severity: str = "medium"  # "critical", "high", "medium", "low"
    impact_description: str = ""


@dataclass
class ChangeImpactReport:
    """Report of change impacts."""

    changes: list[ChangeImpact] = field(default_factory=list)
    total_affected_stories: int = 0
    total_affected_designs: int = 0
    total_affected_implementations: int = 0
    critical_changes: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class ChangeImpactAnalyzer:
    """Analyzes impact of requirement changes."""

    def __init__(self, traceability_matrix_path: Path | None = None):
        """
        Initialize change impact analyzer.

        Args:
            traceability_matrix_path: Path to traceability matrix file
        """
        self.traceability_matrix_path = traceability_matrix_path

    def analyze_change_impact(
        self,
        old_requirements: dict[str, Any],
        new_requirements: dict[str, Any],
        traceability_matrix: Any | None = None,
    ) -> ChangeImpactReport:
        """
        Analyze impact of requirement changes.

        Args:
            old_requirements: Original requirements
            new_requirements: Updated requirements
            traceability_matrix: Optional traceability matrix for linking

        Returns:
            ChangeImpactReport with affected artifacts
        """
        report = ChangeImpactReport()

        old_func_reqs = {self._get_req_id(i, req): req for i, req in enumerate(old_requirements.get("functional_requirements", []))}
        new_func_reqs = {self._get_req_id(i, req): req for i, req in enumerate(new_requirements.get("functional_requirements", []))}

        # Find added requirements
        added_reqs = set(new_func_reqs.keys()) - set(old_func_reqs.keys())
        for req_id in added_reqs:
            impact = ChangeImpact(
                requirement_id=req_id,
                change_type="added",
                severity="medium",
                impact_description="New requirement added",
            )
            report.changes.append(impact)

        # Find removed requirements
        removed_reqs = set(old_func_reqs.keys()) - set(new_func_reqs.keys())
        for req_id in removed_reqs:
            impact = ChangeImpact(
                requirement_id=req_id,
                change_type="removed",
                severity="high",
                impact_description="Requirement removed - may break existing functionality",
            )
            # Find affected artifacts using traceability
            if traceability_matrix:
                trace = traceability_matrix.get_requirement_trace(req_id)
                impact.affected_stories = trace.get("stories", [])
                impact.affected_designs = trace.get("designs", [])
                impact.affected_implementations = trace.get("implementations", [])
            report.changes.append(impact)
            if impact.affected_implementations:
                report.critical_changes.append(f"Requirement {req_id} removed - affects implementation")

        # Find modified requirements
        common_reqs = set(old_func_reqs.keys()) & set(new_func_reqs.keys())
        for req_id in common_reqs:
            old_req = old_func_reqs[req_id]
            new_req = new_func_reqs[req_id]
            if self._requirements_differ(old_req, new_req):
                impact = ChangeImpact(
                    requirement_id=req_id,
                    change_type="modified",
                    severity=self._assess_change_severity(old_req, new_req),
                    impact_description="Requirement modified",
                )
                # Find affected artifacts
                if traceability_matrix:
                    trace = traceability_matrix.get_requirement_trace(req_id)
                    impact.affected_stories = trace.get("stories", [])
                    impact.affected_designs = trace.get("designs", [])
                    impact.affected_implementations = trace.get("implementations", [])
                report.changes.append(impact)
                if impact.severity == "critical" and impact.affected_implementations:
                    report.critical_changes.append(f"Requirement {req_id} modified - critical change affects implementation")

        # Calculate totals
        all_affected_stories = set()
        all_affected_designs = set()
        all_affected_implementations = set()

        for change in report.changes:
            all_affected_stories.update(change.affected_stories)
            all_affected_designs.update(change.affected_designs)
            all_affected_implementations.update(change.affected_implementations)

        report.total_affected_stories = len(all_affected_stories)
        report.total_affected_designs = len(all_affected_designs)
        report.total_affected_implementations = len(all_affected_implementations)

        # Generate recommendations
        if report.critical_changes:
            report.recommendations.append("Review critical changes immediately - may require code changes")
        if report.total_affected_implementations > 0:
            report.recommendations.append(f"Update {report.total_affected_implementations} implementation(s)")
        if report.total_affected_designs > 0:
            report.recommendations.append(f"Review {report.total_affected_designs} design(s) for updates")
        if report.total_affected_stories > 0:
            report.recommendations.append(f"Update {report.total_affected_stories} story/stories")

        return report

    def _get_req_id(self, index: int, req: Any) -> str:
        """Get requirement ID from requirement dict or generate one."""
        if isinstance(req, dict):
            return req.get("id", f"req-{index+1}")
        return f"req-{index+1}"

    def _requirements_differ(self, old_req: Any, new_req: Any) -> bool:
        """Check if requirements differ."""
        old_text = str(old_req).lower()
        new_text = str(new_req).lower()

        # Simple text comparison (could be enhanced with semantic similarity)
        return old_text != new_text

    def _assess_change_severity(self, old_req: Any, new_req: Any) -> str:
        """Assess severity of requirement change."""
        old_text = str(old_req).lower()
        new_text = str(new_req).lower()

        # Check for major changes
        old_words = set(old_text.split())
        new_words = set(new_text.split())

        # Calculate change ratio
        removed_words = old_words - new_words
        added_words = new_words - old_words
        total_words = len(old_words | new_words)

        if total_words == 0:
            return "low"

        change_ratio = (len(removed_words) + len(added_words)) / total_words

        if change_ratio > 0.5:
            return "critical"
        elif change_ratio > 0.3:
            return "high"
        elif change_ratio > 0.1:
            return "medium"
        else:
            return "low"
