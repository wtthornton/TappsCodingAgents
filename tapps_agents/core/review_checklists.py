"""
Review Checklists - Structured review checklists for requirements, stories, and architecture.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ReviewItem:
    """A single review checklist item."""

    category: str
    item: str
    checked: bool = False
    notes: str = ""
    severity: str = "medium"  # "critical", "high", "medium", "low"


@dataclass
class ReviewResult:
    """Result of a review with checklist scoring."""

    overall_score: float = 0.0  # 0-100
    items_checked: int = 0
    items_total: int = 0
    critical_issues: list[str] = field(default_factory=list)
    high_issues: list[str] = field(default_factory=list)
    medium_issues: list[str] = field(default_factory=list)
    low_issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    checklist_items: list[ReviewItem] = field(default_factory=list)


class RequirementsReviewChecklist:
    """Review checklist for requirements."""

    def get_checklist(self) -> list[ReviewItem]:
        """Get requirements review checklist."""
        return [
            ReviewItem("Completeness", "All functional requirements are documented", severity="critical"),
            ReviewItem("Completeness", "Non-functional requirements (NFRs) are specified", severity="critical"),
            ReviewItem("Completeness", "Technical constraints are identified", severity="high"),
            ReviewItem("Completeness", "Assumptions are documented", severity="medium"),
            ReviewItem("Clarity", "Requirements are unambiguous and clear", severity="critical"),
            ReviewItem("Clarity", "No vague or ambiguous language (maybe, perhaps, could)", severity="high"),
            ReviewItem("Clarity", "Requirements use specific, measurable language", severity="high"),
            ReviewItem("Testability", "Each requirement has acceptance criteria", severity="critical"),
            ReviewItem("Testability", "Requirements are testable/verifiable", severity="high"),
            ReviewItem("Testability", "Success criteria are defined", severity="high"),
            ReviewItem("Traceability", "Requirements are linked to user stories", severity="high"),
            ReviewItem("Traceability", "Requirements can be traced to tests", severity="medium"),
            ReviewItem("Feasibility", "Requirements are technically feasible", severity="high"),
            ReviewItem("Feasibility", "No impossible or unrealistic requirements", severity="critical"),
            ReviewItem("Feasibility", "Technical approach is viable", severity="medium"),
            ReviewItem("Consistency", "No conflicting requirements", severity="critical"),
            ReviewItem("Consistency", "Terminology is consistent throughout", severity="medium"),
            ReviewItem("Prioritization", "Requirements are prioritized", severity="medium"),
            ReviewItem("Prioritization", "Critical requirements are identified", severity="high"),
        ]

    def review(self, requirements: dict[str, Any]) -> ReviewResult:
        """Review requirements against checklist."""
        checklist = self.get_checklist()
        result = ReviewResult(items_total=len(checklist))
        result.checklist_items = checklist

        # Evaluate each item
        func_reqs = requirements.get("functional_requirements", [])
        nfr_reqs = requirements.get("non_functional_requirements", [])
        constraints = requirements.get("constraints", [])
        assumptions = requirements.get("assumptions", [])

        for item in checklist:
            checked = False
            issue = ""

            if item.category == "Completeness":
                if "functional requirements" in item.item.lower():
                    checked = len(func_reqs) > 0
                    if not checked:
                        issue = "No functional requirements documented"
                elif "non-functional" in item.item.lower():
                    checked = len(nfr_reqs) > 0
                    if not checked:
                        issue = "No non-functional requirements specified"
                elif "constraints" in item.item.lower():
                    checked = len(constraints) > 0
                elif "assumptions" in item.item.lower():
                    checked = len(assumptions) > 0

            elif item.category == "Clarity":
                all_text = " ".join(str(r) for r in func_reqs).lower()
                if "unambiguous" in item.item.lower():
                    vague_words = ["maybe", "perhaps", "might", "could", "should consider"]
                    checked = not any(word in all_text for word in vague_words)
                    if not checked:
                        issue = "Vague language found in requirements"
                elif "specific" in item.item.lower():
                    checked = len(all_text) > 100  # Has substantial content
                    if not checked:
                        issue = "Requirements lack specificity"

            elif item.category == "Testability":
                acceptance = requirements.get("acceptance_criteria", [])
                if "acceptance criteria" in item.item.lower():
                    checked = len(acceptance) > 0
                    if not checked:
                        issue = "No acceptance criteria defined"
                elif "testable" in item.item.lower():
                    # Check if requirements have testable language
                    testable_indicators = ["must", "shall", "will", "should", "validates", "verifies"]
                    all_text = " ".join(str(r) for r in func_reqs).lower()
                    checked = any(indicator in all_text for indicator in testable_indicators)
                    if not checked:
                        issue = "Requirements lack testable language"

            elif item.category == "Traceability":
                # Check for links
                linked_count = 0
                for req in func_reqs:
                    if isinstance(req, dict):
                        if any(key in req for key in ["story_id", "story_link", "related_stories"]):
                            linked_count += 1
                checked = linked_count > 0
                if not checked:
                    issue = "Requirements not linked to stories"

            elif item.category == "Feasibility":
                all_text = " ".join(str(r) for r in func_reqs).lower()
                impossible = ["instantaneous", "zero latency", "infinite", "perfect", "100% uptime"]
                checked = not any(word in all_text for word in impossible)
                if not checked:
                    issue = "Impossible requirements detected"

            elif item.category == "Consistency":
                # Basic consistency check
                checked = True  # Would need more sophisticated analysis
                if "conflicting" in item.item.lower():
                    # Check for contradictions (simplified)
                    checked = True  # Placeholder

            elif item.category == "Prioritization":
                prioritized_count = 0
                for req in func_reqs:
                    if isinstance(req, dict):
                        if "priority" in req or "importance" in req:
                            prioritized_count += 1
                checked = prioritized_count > 0
                if not checked:
                    issue = "Requirements not prioritized"

            item.checked = checked
            if checked:
                result.items_checked += 1
            else:
                if issue:
                    if item.severity == "critical":
                        result.critical_issues.append(f"{item.category}: {issue}")
                    elif item.severity == "high":
                        result.high_issues.append(f"{item.category}: {issue}")
                    elif item.severity == "medium":
                        result.medium_issues.append(f"{item.category}: {issue}")
                    else:
                        result.low_issues.append(f"{item.category}: {issue}")

        # Calculate overall score
        if result.items_total > 0:
            result.overall_score = (result.items_checked / result.items_total) * 100.0

        # Generate recommendations
        if result.critical_issues:
            result.recommendations.append("Address critical issues immediately")
        if result.high_issues:
            result.recommendations.append("Resolve high-priority issues before proceeding")
        if result.overall_score < 70.0:
            result.recommendations.append("Overall score below threshold - review and improve requirements")

        return result


class StoryReviewChecklist:
    """Review checklist for user stories."""

    def get_checklist(self) -> list[ReviewItem]:
        """Get story review checklist (INVEST-based)."""
        return [
            ReviewItem("INVEST", "Story is Independent (can be developed standalone)", severity="high"),
            ReviewItem("INVEST", "Story is Negotiable (details can be discussed)", severity="medium"),
            ReviewItem("INVEST", "Story is Valuable (delivers user/business value)", severity="critical"),
            ReviewItem("INVEST", "Story is Estimable (can be sized)", severity="high"),
            ReviewItem("INVEST", "Story is Small (appropriately sized)", severity="high"),
            ReviewItem("INVEST", "Story is Testable (has clear acceptance criteria)", severity="critical"),
            ReviewItem("Format", "Story follows 'As a... I want... So that...' format", severity="high"),
            ReviewItem("Format", "Story has clear title", severity="medium"),
            ReviewItem("Acceptance Criteria", "At least 2-3 acceptance criteria defined", severity="critical"),
            ReviewItem("Acceptance Criteria", "Acceptance criteria are testable", severity="high"),
            ReviewItem("Acceptance Criteria", "Acceptance criteria use Given-When-Then format", severity="medium"),
            ReviewItem("Dependencies", "Dependencies are identified", severity="high"),
            ReviewItem("Dependencies", "Story has minimal dependencies (< 3)", severity="medium"),
            ReviewItem("Estimation", "Story points assigned (Fibonacci: 1, 2, 3, 5, 8, 13)", severity="high"),
            ReviewItem("Estimation", "Story points are reasonable for scope", severity="medium"),
            ReviewItem("Value", "'So that...' clause clearly states value", severity="critical"),
            ReviewItem("Value", "Story aligns with business goals", severity="medium"),
        ]

    def review(self, story: dict[str, Any]) -> ReviewResult:
        """Review story against checklist."""
        checklist = self.get_checklist()
        result = ReviewResult(items_total=len(checklist))
        result.checklist_items = checklist

        description = story.get("description", "")
        acceptance = story.get("acceptance_criteria", [])
        dependencies = story.get("dependencies", [])
        story_points = story.get("story_points", 0)

        for item in checklist:
            checked = False
            issue = ""

            if item.category == "INVEST":
                if "Independent" in item.item:
                    checked = len(dependencies) <= 2
                    if not checked:
                        issue = f"Too many dependencies ({len(dependencies)})"
                elif "Negotiable" in item.item:
                    prescriptive = ["must", "shall", "exactly", "precisely"]
                    checked = not any(word in description.lower() for word in prescriptive)
                    if not checked:
                        issue = "Story is too prescriptive"
                elif "Valuable" in item.item:
                    checked = "so that" in description.lower()
                    if not checked:
                        issue = "Missing 'So that...' value clause"
                elif "Estimable" in item.item:
                    checked = story_points > 0
                    if not checked:
                        issue = "No story points assigned"
                elif "Small" in item.item:
                    checked = 1 <= story_points <= 8
                    if not checked:
                        issue = f"Story too large ({story_points} points)"
                elif "Testable" in item.item:
                    checked = len(acceptance) >= 2
                    if not checked:
                        issue = "Insufficient acceptance criteria"

            elif item.category == "Format":
                if "As a" in item.item:
                    checked = "as a" in description.lower() and "i want" in description.lower()
                    if not checked:
                        issue = "Story doesn't follow standard format"
                elif "title" in item.item.lower():
                    checked = bool(story.get("title"))
                    if not checked:
                        issue = "Story missing title"

            elif item.category == "Acceptance Criteria":
                if "2-3" in item.item:
                    checked = 2 <= len(acceptance) <= 7
                    if not checked:
                        issue = f"Acceptance criteria count: {len(acceptance)} (expected 2-7)"
                elif "testable" in item.item.lower():
                    testable_count = sum(1 for ac in acceptance if self._is_testable(ac))
                    checked = testable_count > 0
                    if not checked:
                        issue = "Acceptance criteria not testable"
                elif "Given-When-Then" in item.item:
                    gwt_count = sum(1 for ac in acceptance if self._has_gwt_format(ac))
                    checked = gwt_count > 0
                    if not checked:
                        issue = "Acceptance criteria should use Given-When-Then format"

            elif item.category == "Dependencies":
                if "identified" in item.item.lower():
                    checked = True  # Dependencies list exists
                elif "minimal" in item.item.lower():
                    checked = len(dependencies) < 3
                    if not checked:
                        issue = f"Too many dependencies: {len(dependencies)}"

            elif item.category == "Estimation":
                if "assigned" in item.item.lower():
                    checked = story_points > 0
                    if not checked:
                        issue = "Story points not assigned"
                elif "reasonable" in item.item.lower():
                    checked = 1 <= story_points <= 13
                    if not checked:
                        issue = f"Story points out of range: {story_points}"

            elif item.category == "Value":
                if "So that" in item.item:
                    checked = "so that" in description.lower()
                    if not checked:
                        issue = "Missing value statement ('So that...')"

            item.checked = checked
            if checked:
                result.items_checked += 1
            else:
                if issue:
                    if item.severity == "critical":
                        result.critical_issues.append(f"{item.category}: {issue}")
                    elif item.severity == "high":
                        result.high_issues.append(f"{item.category}: {issue}")
                    elif item.severity == "medium":
                        result.medium_issues.append(f"{item.category}: {issue}")
                    else:
                        result.low_issues.append(f"{item.category}: {issue}")

        # Calculate overall score
        if result.items_total > 0:
            result.overall_score = (result.items_checked / result.items_total) * 100.0

        # Generate recommendations
        if result.critical_issues:
            result.recommendations.append("Address critical issues before development")
        if result.high_issues:
            result.recommendations.append("Resolve high-priority issues")
        if result.overall_score < 70.0:
            result.recommendations.append("Story quality below threshold - improve before proceeding")

        return result

    def _is_testable(self, criterion: str) -> bool:
        """Check if acceptance criterion is testable."""
        testable_indicators = ["when", "then", "should", "must", "will", "displays", "returns", "validates"]
        return any(indicator in criterion.lower() for indicator in testable_indicators)

    def _has_gwt_format(self, criterion: str) -> bool:
        """Check if acceptance criterion uses Given-When-Then format."""
        criterion_lower = criterion.lower()
        return "given" in criterion_lower and ("when" in criterion_lower or "then" in criterion_lower)


class ArchitectureReviewChecklist:
    """Review checklist for architecture."""

    def get_checklist(self) -> list[ReviewItem]:
        """Get architecture review checklist."""
        return [
            ReviewItem("Requirements Alignment", "All functional requirements are addressed", severity="critical"),
            ReviewItem("Requirements Alignment", "Non-functional requirements are addressed", severity="critical"),
            ReviewItem("Requirements Alignment", "Performance requirements have solutions", severity="high"),
            ReviewItem("Requirements Alignment", "Security requirements have controls", severity="critical"),
            ReviewItem("Architecture Fundamentals", "System components are clearly defined", severity="critical"),
            ReviewItem("Architecture Fundamentals", "Component interactions are documented", severity="high"),
            ReviewItem("Architecture Fundamentals", "Data flow is described", severity="high"),
            ReviewItem("Architecture Fundamentals", "System boundaries are defined", severity="high"),
            ReviewItem("Scalability", "Scalability approach is defined", severity="high"),
            ReviewItem("Scalability", "Load handling strategy is specified", severity="medium"),
            ReviewItem("Security", "Authentication approach is defined", severity="critical"),
            ReviewItem("Security", "Authorization model is specified", severity="critical"),
            ReviewItem("Security", "Data protection measures are addressed", severity="critical"),
            ReviewItem("Technology", "Technology stack is selected and justified", severity="high"),
            ReviewItem("Technology", "Technology choices align with requirements", severity="high"),
            ReviewItem("Patterns", "Architectural patterns are identified", severity="medium"),
            ReviewItem("Patterns", "Patterns are appropriate for requirements", severity="medium"),
            ReviewItem("Documentation", "Architecture diagrams are provided", severity="medium"),
            ReviewItem("Documentation", "Key decisions are documented", severity="medium"),
        ]

    def review(self, architecture: dict[str, Any]) -> ReviewResult:
        """Review architecture against checklist."""
        checklist = self.get_checklist()
        result = ReviewResult(items_total=len(checklist))
        result.checklist_items = checklist

        arch_text = str(architecture).lower()
        components = architecture.get("components", [])
        patterns = architecture.get("patterns", [])

        for item in checklist:
            checked = False
            issue = ""

            if item.category == "Requirements Alignment":
                if "functional" in item.item.lower():
                    checked = len(components) > 0  # Has components = addresses requirements
                    if not checked:
                        issue = "No components defined"
                elif "non-functional" in item.item.lower():
                    checked = "security" in arch_text or "performance" in arch_text or "scalability" in arch_text
                    if not checked:
                        issue = "NFRs not addressed"
                elif "performance" in item.item.lower():
                    checked = "performance" in arch_text or "speed" in arch_text or "latency" in arch_text
                    if not checked:
                        issue = "Performance not addressed"
                elif "security" in item.item.lower():
                    checked = "security" in arch_text or "auth" in arch_text
                    if not checked:
                        issue = "Security not addressed"

            elif item.category == "Architecture Fundamentals":
                if "components" in item.item.lower():
                    checked = len(components) > 0
                    if not checked:
                        issue = "No components defined"
                elif "interactions" in item.item.lower():
                    checked = "interaction" in arch_text or "communication" in arch_text or "api" in arch_text
                    if not checked:
                        issue = "Component interactions not documented"
                elif "data flow" in item.item.lower():
                    checked = "data flow" in arch_text or "data" in arch_text
                    if not checked:
                        issue = "Data flow not described"
                elif "boundaries" in item.item.lower():
                    checked = "boundary" in arch_text or "interface" in arch_text
                    if not checked:
                        issue = "System boundaries not defined"

            elif item.category == "Scalability":
                checked = "scal" in arch_text or "scale" in arch_text or "load" in arch_text
                if not checked:
                    issue = "Scalability not addressed"

            elif item.category == "Security":
                if "authentication" in item.item.lower():
                    checked = "auth" in arch_text
                    if not checked:
                        issue = "Authentication not defined"
                elif "authorization" in item.item.lower():
                    checked = "authorization" in arch_text or "permission" in arch_text
                    if not checked:
                        issue = "Authorization not specified"
                elif "data protection" in item.item.lower():
                    checked = "encrypt" in arch_text or "protection" in arch_text or "secure" in arch_text
                    if not checked:
                        issue = "Data protection not addressed"

            elif item.category == "Technology":
                tech_stack = architecture.get("technology_stack", [])
                checked = len(tech_stack) > 0 or "technology" in arch_text
                if not checked:
                    issue = "Technology stack not specified"

            elif item.category == "Patterns":
                checked = len(patterns) > 0 or "pattern" in arch_text
                if not checked:
                    issue = "Architectural patterns not identified"

            elif item.category == "Documentation":
                checked = "diagram" in arch_text or "documentation" in arch_text
                if not checked:
                    issue = "Architecture documentation missing"

            item.checked = checked
            if checked:
                result.items_checked += 1
            else:
                if issue:
                    if item.severity == "critical":
                        result.critical_issues.append(f"{item.category}: {issue}")
                    elif item.severity == "high":
                        result.high_issues.append(f"{item.category}: {issue}")
                    elif item.severity == "medium":
                        result.medium_issues.append(f"{item.category}: {issue}")
                    else:
                        result.low_issues.append(f"{item.category}: {issue}")

        # Calculate overall score
        if result.items_total > 0:
            result.overall_score = (result.items_checked / result.items_total) * 100.0

        # Generate recommendations
        if result.critical_issues:
            result.recommendations.append("Address critical architecture issues immediately")
        if result.high_issues:
            result.recommendations.append("Resolve high-priority architecture concerns")
        if result.overall_score < 75.0:
            result.recommendations.append("Architecture quality below threshold - review and improve")

        return result
