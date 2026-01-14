"""
Workflow Validator - Validates consistency across workflow artifacts (requirements → stories → design → implementation).
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyIssue:
    """A consistency issue found across artifacts."""

    artifact_type: str  # "requirements", "story", "design", "implementation"
    artifact_id: str
    issue_type: str  # "missing", "inconsistent", "conflicting"
    description: str
    severity: str = "medium"  # "critical", "high", "medium", "low"
    related_artifacts: list[str] = field(default_factory=list)


@dataclass
class WorkflowValidationResult:
    """Result of workflow artifact validation."""

    is_consistent: bool
    consistency_score: float = 0.0  # 0-100
    issues: list[ConsistencyIssue] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class WorkflowValidator:
    """Validates consistency across workflow artifacts."""

    def validate_workflow_artifacts(
        self,
        requirements: dict[str, Any] | None = None,
        stories: list[dict[str, Any]] | None = None,
        architecture: dict[str, Any] | None = None,
        api_design: dict[str, Any] | None = None,
        implementation_files: list[str] | None = None,
    ) -> WorkflowValidationResult:
        """
        Validate consistency across workflow artifacts.

        Args:
            requirements: Requirements document
            stories: List of user stories
            architecture: Architecture document
            api_design: API design document
            implementation_files: List of implementation file paths

        Returns:
            WorkflowValidationResult
        """
        result = WorkflowValidationResult(is_consistent=True)
        issues = []
        gaps = []

        # Check requirements → stories consistency
        if requirements and stories:
            req_story_issues = self._check_requirements_stories_consistency(requirements, stories)
            issues.extend(req_story_issues)

        # Check stories → architecture consistency
        if stories and architecture:
            story_arch_issues = self._check_stories_architecture_consistency(stories, architecture)
            issues.extend(story_arch_issues)

        # Check architecture → API design consistency
        if architecture and api_design:
            arch_api_issues = self._check_architecture_api_consistency(architecture, api_design)
            issues.extend(arch_api_issues)

        # Check for gaps
        if requirements and not stories:
            gaps.append("Requirements exist but no stories found")
        if stories and not architecture:
            gaps.append("Stories exist but no architecture found")
        if architecture and not api_design:
            gaps.append("Architecture exists but no API design found")

        result.issues = issues
        result.gaps = gaps

        # Calculate consistency score
        total_checks = 10  # Approximate number of checks
        passed_checks = total_checks - len(issues)
        result.consistency_score = (passed_checks / total_checks) * 100.0 if total_checks > 0 else 0.0

        result.is_consistent = result.consistency_score >= 70.0 and len(gaps) == 0

        # Generate recommendations
        if result.gaps:
            result.recommendations.append("Fill gaps in workflow artifacts")
        if result.consistency_score < 70.0:
            result.recommendations.append("Improve consistency across artifacts")
        if any(issue.severity == "critical" for issue in issues):
            result.recommendations.append("Address critical consistency issues")

        return result

    def _check_requirements_stories_consistency(
        self, requirements: dict[str, Any], stories: list[dict[str, Any]]
    ) -> list[ConsistencyIssue]:
        """Check consistency between requirements and stories."""
        issues = []

        func_reqs = requirements.get("functional_requirements", [])
        req_keywords = set()
        for req in func_reqs:
            if isinstance(req, dict):
                req_text = req.get("description", "")
            else:
                req_text = str(req)
            req_keywords.update(req_text.lower().split())

        # Check if stories cover requirements
        story_keywords = set()
        for story in stories:
            story_text = str(story).lower()
            story_keywords.update(story_text.split())

        # Check for missing coverage
        if len(req_keywords) > 0:
            coverage_ratio = len(story_keywords & req_keywords) / len(req_keywords)
            if coverage_ratio < 0.5:
                issues.append(
                    ConsistencyIssue(
                        artifact_type="story",
                        artifact_id="all",
                        issue_type="missing",
                        description=f"Stories only cover {coverage_ratio*100:.1f}% of requirement keywords",
                        severity="high",
                    )
                )

        return issues

    def _check_stories_architecture_consistency(
        self, stories: list[dict[str, Any]], architecture: dict[str, Any]
    ) -> list[ConsistencyIssue]:
        """Check consistency between stories and architecture."""
        issues = []

        # Extract story keywords
        story_keywords = set()
        for story in stories:
            story_text = str(story).lower()
            story_keywords.update(story_text.split())

        # Extract architecture keywords
        arch_text = str(architecture).lower()
        arch_keywords = set(arch_text.split())

        # Check coverage
        if len(story_keywords) > 0:
            coverage_ratio = len(arch_keywords & story_keywords) / len(story_keywords)
            if coverage_ratio < 0.5:
                issues.append(
                    ConsistencyIssue(
                        artifact_type="architecture",
                        artifact_id="all",
                        issue_type="inconsistent",
                        description=f"Architecture only covers {coverage_ratio*100:.1f}% of story keywords",
                        severity="high",
                    )
                )

        return issues

    def _check_architecture_api_consistency(
        self, architecture: dict[str, Any], api_design: dict[str, Any]
    ) -> list[ConsistencyIssue]:
        """Check consistency between architecture and API design."""
        issues = []

        # Check if API design aligns with architecture components
        components = architecture.get("components", [])
        endpoints = api_design.get("endpoints", [])

        # Simple check: if architecture has components, API should have endpoints
        if components and not endpoints:
            issues.append(
                ConsistencyIssue(
                    artifact_type="api_design",
                    artifact_id="all",
                    issue_type="missing",
                    description="Architecture has components but API design has no endpoints",
                    severity="high",
                )
            )

        return issues
