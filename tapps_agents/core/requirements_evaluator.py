"""
Requirements Evaluator - Quality scoring and validation for requirements.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RequirementsQualityScore:
    """Requirements quality score breakdown."""

    completeness: float = 0.0  # 0-100: Are all necessary requirements captured?
    clarity: float = 0.0  # 0-100: Are requirements clear and unambiguous?
    testability: float = 0.0  # 0-100: Can requirements be tested/validated?
    traceability: float = 0.0  # 0-100: Are requirements linked to stories/tests?
    feasibility: float = 0.0  # 0-100: Are requirements technically feasible?
    overall: float = 0.0  # Weighted average

    issues: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class RequirementsValidationResult:
    """Result of requirements validation."""

    is_valid: bool
    score: RequirementsQualityScore
    missing_elements: list[str] = field(default_factory=list)
    ambiguous_requirements: list[str] = field(default_factory=list)
    untestable_requirements: list[str] = field(default_factory=list)


class RequirementsEvaluator:
    """Evaluates requirements quality and completeness."""

    COMPLETENESS_WEIGHT = 0.25
    CLARITY_WEIGHT = 0.25
    TESTABILITY_WEIGHT = 0.20
    TRACEABILITY_WEIGHT = 0.15
    FEASIBILITY_WEIGHT = 0.15

    EXCELLENT_THRESHOLD = 80.0
    GOOD_THRESHOLD = 70.0
    ACCEPTABLE_THRESHOLD = 60.0

    def evaluate(self, requirements: dict[str, Any]) -> RequirementsQualityScore:
        """
        Evaluate requirements quality.

        Args:
            requirements: Requirements document/dict with structure:
                - functional_requirements: list
                - non_functional_requirements: list
                - constraints: list
                - assumptions: list
                - acceptance_criteria: list (optional)

        Returns:
            RequirementsQualityScore with detailed breakdown
        """
        score = RequirementsQualityScore()

        # Evaluate completeness
        score.completeness = self._evaluate_completeness(requirements)
        score.clarity = self._evaluate_clarity(requirements)
        score.testability = self._evaluate_testability(requirements)
        score.traceability = self._evaluate_traceability(requirements)
        score.feasibility = self._evaluate_feasibility(requirements)

        # Calculate weighted overall score
        score.overall = (
            score.completeness * self.COMPLETENESS_WEIGHT
            + score.clarity * self.CLARITY_WEIGHT
            + score.testability * self.TESTABILITY_WEIGHT
            + score.traceability * self.TRACEABILITY_WEIGHT
            + score.feasibility * self.FEASIBILITY_WEIGHT
        )

        # Generate feedback
        score.issues = self._identify_issues(requirements, score)
        score.strengths = self._identify_strengths(requirements, score)
        score.recommendations = self._generate_recommendations(score)

        return score

    def validate(self, requirements: dict[str, Any]) -> RequirementsValidationResult:
        """
        Validate requirements for completeness and quality.

        Args:
            requirements: Requirements document/dict

        Returns:
            RequirementsValidationResult with validation status
        """
        score = self.evaluate(requirements)

        # Check for critical issues
        missing_elements = []
        ambiguous = []
        untestable = []

        # Check for missing functional requirements
        func_reqs = requirements.get("functional_requirements", [])
        if not func_reqs:
            missing_elements.append("Functional requirements")

        # Check for missing NFRs
        nfr_reqs = requirements.get("non_functional_requirements", [])
        if not nfr_reqs:
            missing_elements.append("Non-functional requirements")

        # Check for ambiguous requirements
        for req in func_reqs:
            if isinstance(req, dict):
                desc = req.get("description", "")
            else:
                desc = str(req)
            if self._is_ambiguous(desc):
                ambiguous.append(desc[:100] + "..." if len(desc) > 100 else desc)

        # Check for untestable requirements
        for req in func_reqs:
            if isinstance(req, dict):
                desc = req.get("description", "")
            else:
                desc = str(req)
            if not self._is_testable(desc):
                untestable.append(desc[:100] + "..." if len(desc) > 100 else desc)

        is_valid = (
            score.overall >= self.ACCEPTABLE_THRESHOLD
            and len(missing_elements) == 0
            and len(ambiguous) == 0
        )

        return RequirementsValidationResult(
            is_valid=is_valid,
            score=score,
            missing_elements=missing_elements,
            ambiguous_requirements=ambiguous,
            untestable_requirements=untestable,
        )

    def _evaluate_completeness(self, requirements: dict[str, Any]) -> float:
        """Evaluate requirements completeness (0-100)."""
        score = 0.0
        max_score = 100.0

        # Functional requirements (30 points)
        func_reqs = requirements.get("functional_requirements", [])
        if func_reqs:
            score += 30.0
            if len(func_reqs) >= 3:  # At least 3 functional requirements
                score += 10.0

        # Non-functional requirements (25 points)
        nfr_reqs = requirements.get("non_functional_requirements", [])
        if nfr_reqs:
            score += 25.0
            # Check for key NFR categories
            nfr_text = " ".join(str(r) for r in nfr_reqs).lower()
            if "performance" in nfr_text or "speed" in nfr_text:
                score += 5.0
            if "security" in nfr_text:
                score += 5.0
            if "scalability" in nfr_text:
                score += 5.0

        # Constraints (15 points)
        constraints = requirements.get("constraints", [])
        if constraints:
            score += 15.0

        # Assumptions (10 points)
        assumptions = requirements.get("assumptions", [])
        if assumptions:
            score += 10.0

        # Acceptance criteria (20 points)
        acceptance = requirements.get("acceptance_criteria", [])
        if acceptance:
            score += 20.0
            if len(acceptance) >= 3:
                score += 5.0

        return min(score, max_score)

    def _evaluate_clarity(self, requirements: dict[str, Any]) -> float:
        """Evaluate requirements clarity (0-100)."""
        score = 100.0
        deductions = 0.0

        # Check functional requirements clarity
        func_reqs = requirements.get("functional_requirements", [])
        for req in func_reqs:
            if isinstance(req, dict):
                desc = req.get("description", "")
            else:
                desc = str(req)

            # Deduct for ambiguity indicators
            if self._is_ambiguous(desc):
                deductions += 10.0
            if len(desc) < 20:  # Too short
                deductions += 5.0
            if len(desc) > 500:  # Too long (might be unclear)
                deductions += 5.0

        # Check for vague words
        vague_words = ["maybe", "perhaps", "might", "could", "should", "nice to have"]
        all_text = " ".join(str(r) for r in func_reqs).lower()
        for word in vague_words:
            if word in all_text:
                deductions += 3.0

        return max(0.0, score - deductions)

    def _evaluate_testability(self, requirements: dict[str, Any]) -> float:
        """Evaluate requirements testability (0-100)."""
        score = 0.0
        func_reqs = requirements.get("functional_requirements", [])

        if not func_reqs:
            return 0.0

        testable_count = 0
        for req in func_reqs:
            if isinstance(req, dict):
                desc = req.get("description", "")
            else:
                desc = str(req)
            if self._is_testable(desc):
                testable_count += 1

        # Percentage of testable requirements
        testable_ratio = testable_count / len(func_reqs)
        score = testable_ratio * 100.0

        # Bonus for acceptance criteria
        acceptance = requirements.get("acceptance_criteria", [])
        if acceptance:
            score = min(100.0, score + 20.0)

        return score

    def _evaluate_traceability(self, requirements: dict[str, Any]) -> float:
        """Evaluate requirements traceability (0-100)."""
        score = 0.0

        # Check for story links
        func_reqs = requirements.get("functional_requirements", [])
        linked_count = 0

        for req in func_reqs:
            if isinstance(req, dict):
                # Check for story_id, story_link, or related_stories
                if any(
                    key in req
                    for key in ["story_id", "story_link", "related_stories", "linked_to"]
                ):
                    linked_count += 1

        if func_reqs:
            score = (linked_count / len(func_reqs)) * 100.0

        # Bonus for test links
        for req in func_reqs:
            if isinstance(req, dict):
                if "test_cases" in req or "test_links" in req:
                    score = min(100.0, score + 10.0)
                    break

        return min(100.0, score)

    def _evaluate_feasibility(self, requirements: dict[str, Any]) -> float:
        """Evaluate requirements technical feasibility (0-100)."""
        # Default to 80 (assume feasible unless obvious issues)
        score = 80.0

        func_reqs = requirements.get("functional_requirements", [])
        all_text = " ".join(str(r) for r in func_reqs).lower()

        # Check for impossible/unrealistic requirements
        impossible_indicators = [
            "instantaneous",
            "zero latency",
            "infinite",
            "perfect",
            "100% uptime",
            "no errors",
        ]
        for indicator in impossible_indicators:
            if indicator in all_text:
                score -= 15.0

        # Check for vague technical requirements
        vague_tech = ["fast", "quick", "efficient", "scalable"]  # Without specifics
        vague_count = sum(1 for word in vague_tech if word in all_text)
        if vague_count > 3:
            score -= 10.0

        return max(0.0, score)

    def _is_ambiguous(self, text: str) -> bool:
        """Check if requirement text is ambiguous."""
        ambiguous_indicators = [
            "maybe",
            "perhaps",
            "might",
            "could",
            "should consider",
            "nice to have",
            "if possible",
            "as needed",
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in ambiguous_indicators)

    def _is_testable(self, text: str) -> bool:
        """Check if requirement is testable."""
        # Testable requirements have:
        # - Specific actions/behaviors
        # - Measurable outcomes
        # - Clear success criteria

        testable_indicators = [
            "must",
            "shall",
            "will",
            "should",
            "validates",
            "verifies",
            "checks",
            "returns",
            "displays",
            "saves",
            "creates",
            "deletes",
            "updates",
        ]

        text_lower = text.lower()
        has_action = any(indicator in text_lower for indicator in testable_indicators)

        # Check for measurable criteria
        measurable = any(
            word in text_lower
            for word in ["seconds", "milliseconds", "users", "requests", "percentage", "%"]
        )

        return has_action or measurable

    def _identify_issues(self, requirements: dict[str, Any], score: RequirementsQualityScore) -> list[str]:
        """Identify issues in requirements."""
        issues = []

        if score.completeness < 60.0:
            issues.append("Requirements are incomplete - missing key elements")

        if score.clarity < 60.0:
            issues.append("Requirements lack clarity - ambiguous or vague statements")

        if score.testability < 60.0:
            issues.append("Requirements are not testable - missing measurable criteria")

        if score.traceability < 50.0:
            issues.append("Requirements lack traceability - not linked to stories/tests")

        if score.feasibility < 60.0:
            issues.append("Requirements may not be technically feasible")

        func_reqs = requirements.get("functional_requirements", [])
        if len(func_reqs) < 2:
            issues.append("Too few functional requirements - may be incomplete")

        return issues

    def _identify_strengths(self, requirements: dict[str, Any], score: RequirementsQualityScore) -> list[str]:
        """Identify strengths in requirements."""
        strengths = []

        if score.completeness >= 80.0:
            strengths.append("Comprehensive requirements coverage")

        if score.clarity >= 80.0:
            strengths.append("Clear and unambiguous requirements")

        if score.testability >= 80.0:
            strengths.append("Well-defined testable requirements")

        if score.traceability >= 70.0:
            strengths.append("Good traceability to stories/tests")

        acceptance = requirements.get("acceptance_criteria", [])
        if len(acceptance) >= 3:
            strengths.append("Detailed acceptance criteria")

        return strengths

    def _generate_recommendations(self, score: RequirementsQualityScore) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if score.completeness < 70.0:
            recommendations.append("Add missing functional or non-functional requirements")
            recommendations.append("Document constraints and assumptions")

        if score.clarity < 70.0:
            recommendations.append("Remove ambiguous language (maybe, perhaps, could)")
            recommendations.append("Use specific, measurable language")

        if score.testability < 70.0:
            recommendations.append("Add measurable acceptance criteria")
            recommendations.append("Define clear success/failure conditions")

        if score.traceability < 60.0:
            recommendations.append("Link requirements to user stories")
            recommendations.append("Create traceability matrix")

        if score.feasibility < 70.0:
            recommendations.append("Review technical feasibility with architecture team")
            recommendations.append("Clarify vague technical requirements")

        return recommendations
