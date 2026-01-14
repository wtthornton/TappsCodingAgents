"""
Story Evaluator - Quality scoring and validation for user stories.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StoryQualityScore:
    """User story quality score breakdown (INVEST criteria)."""

    independent: float = 0.0  # 0-100: Can story be developed independently?
    negotiable: float = 0.0  # 0-100: Is story open to discussion?
    valuable: float = 0.0  # 0-100: Does story deliver value?
    estimable: float = 0.0  # 0-100: Can story be estimated?
    small: float = 0.0  # 0-100: Is story appropriately sized?
    testable: float = 0.0  # 0-100: Can story be tested?
    overall: float = 0.0  # Weighted average

    issues: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class StoryValidationResult:
    """Result of story validation."""

    is_valid: bool
    score: StoryQualityScore
    missing_elements: list[str] = field(default_factory=list)
    weak_acceptance_criteria: list[str] = field(default_factory=list)
    dependency_issues: list[str] = field(default_factory=list)


class StoryEvaluator:
    """Evaluates user story quality using INVEST criteria."""

    # INVEST weights (equal weighting)
    INDEPENDENT_WEIGHT = 1.0 / 6.0
    NEGOTIABLE_WEIGHT = 1.0 / 6.0
    VALUABLE_WEIGHT = 1.0 / 6.0
    ESTIMABLE_WEIGHT = 1.0 / 6.0
    SMALL_WEIGHT = 1.0 / 6.0
    TESTABLE_WEIGHT = 1.0 / 6.0

    EXCELLENT_THRESHOLD = 80.0
    GOOD_THRESHOLD = 70.0
    ACCEPTABLE_THRESHOLD = 60.0

    def evaluate(self, story: dict[str, Any]) -> StoryQualityScore:
        """
        Evaluate story quality using INVEST criteria.

        Args:
            story: Story dict with structure:
                - title: str
                - description: str (As a... I want... So that...)
                - acceptance_criteria: list[str]
                - story_points: int (optional)
                - dependencies: list[str] (optional)
                - priority: str (optional)

        Returns:
            StoryQualityScore with detailed breakdown
        """
        score = StoryQualityScore()

        score.independent = self._evaluate_independent(story)
        score.negotiable = self._evaluate_negotiable(story)
        score.valuable = self._evaluate_valuable(story)
        score.estimable = self._evaluate_estimable(story)
        score.small = self._evaluate_small(story)
        score.testable = self._evaluate_testable(story)

        # Calculate weighted overall score
        score.overall = (
            score.independent * self.INDEPENDENT_WEIGHT
            + score.negotiable * self.NEGOTIABLE_WEIGHT
            + score.valuable * self.VALUABLE_WEIGHT
            + score.estimable * self.ESTIMABLE_WEIGHT
            + score.small * self.SMALL_WEIGHT
            + score.testable * self.TESTABLE_WEIGHT
        )

        # Generate feedback
        score.issues = self._identify_issues(story, score)
        score.strengths = self._identify_strengths(story, score)
        score.recommendations = self._generate_recommendations(score)

        return score

    def validate(self, story: dict[str, Any]) -> StoryValidationResult:
        """
        Validate story for completeness and quality.

        Args:
            story: Story dict

        Returns:
            StoryValidationResult with validation status
        """
        score = self.evaluate(story)

        missing_elements = []
        weak_acceptance = []
        dependency_issues = []

        # Check for required elements
        if not story.get("title"):
            missing_elements.append("Title")
        if not story.get("description"):
            missing_elements.append("Description")
        if not story.get("acceptance_criteria"):
            missing_elements.append("Acceptance criteria")

        # Check acceptance criteria quality
        acceptance = story.get("acceptance_criteria", [])
        for criterion in acceptance:
            if isinstance(criterion, str):
                if len(criterion) < 20:  # Too short
                    weak_acceptance.append(criterion[:50])
                if not self._is_testable_criterion(criterion):
                    weak_acceptance.append(criterion[:50])

        # Check for dependency issues
        dependencies = story.get("dependencies", [])
        if len(dependencies) > 3:
            dependency_issues.append(f"Too many dependencies ({len(dependencies)}) - may not be independent")

        is_valid = (
            score.overall >= self.ACCEPTABLE_THRESHOLD
            and len(missing_elements) == 0
            and score.testable >= 60.0
        )

        return StoryValidationResult(
            is_valid=is_valid,
            score=score,
            missing_elements=missing_elements,
            weak_acceptance_criteria=weak_acceptance,
            dependency_issues=dependency_issues,
        )

    def _evaluate_independent(self, story: dict[str, Any]) -> float:
        """Evaluate if story is independent (0-100)."""
        score = 100.0

        # Check for dependencies
        dependencies = story.get("dependencies", [])
        if dependencies:
            # Few dependencies = minor deduction
            if len(dependencies) <= 2:
                score -= 20.0
            # Many dependencies = major deduction
            else:
                score -= 50.0

        # Check if story description mentions other stories
        description = story.get("description", "").lower()
        if "after story" in description or "depends on" in description:
            score -= 30.0

        return max(0.0, score)

    def _evaluate_negotiable(self, story: dict[str, Any]) -> float:
        """Evaluate if story is negotiable (0-100)."""
        score = 80.0  # Default: stories are generally negotiable

        description = story.get("description", "").lower()
        title = story.get("title", "").lower()

        # Check for overly prescriptive language
        prescriptive = ["must", "shall", "exactly", "precisely", "only"]
        prescriptive_count = sum(1 for word in prescriptive if word in description or word in title)

        if prescriptive_count > 3:
            score -= 30.0
        elif prescriptive_count > 1:
            score -= 15.0

        # Check for implementation details (should be negotiable)
        tech_details = ["using", "with", "via", "through"]
        if any(word in description for word in tech_details):
            # Some tech details OK, but too many reduce negotiability
            tech_count = sum(1 for word in tech_details if word in description)
            if tech_count > 2:
                score -= 20.0

        return max(0.0, score)

    def _evaluate_valuable(self, story: dict[str, Any]) -> float:
        """Evaluate if story delivers value (0-100)."""
        score = 0.0

        description = story.get("description", "")
        if not description:
            return 0.0

        # Check for "So that..." clause (value statement)
        if "so that" in description.lower():
            score += 50.0
            # Check if value is clear
            so_that_part = description.lower().split("so that")[-1] if "so that" in description.lower() else ""
            if len(so_that_part.strip()) > 20:
                score += 30.0

        # Check for user role (As a...)
        if re.search(r"as a\s+\w+", description.lower()):
            score += 20.0

        # Check for business value indicators
        value_words = ["improve", "enable", "allow", "provide", "increase", "reduce", "save"]
        if any(word in description.lower() for word in value_words):
            score += 10.0

        return min(100.0, score)

    def _evaluate_estimable(self, story: dict[str, Any]) -> float:
        """Evaluate if story can be estimated (0-100)."""
        score = 0.0

        # Has story points = estimable
        if story.get("story_points"):
            score += 60.0
            # Story points in reasonable range (1-13)
            points = story.get("story_points", 0)
            if 1 <= points <= 13:
                score += 20.0
            elif points > 13:
                score -= 20.0  # Too large to estimate accurately

        # Has acceptance criteria = more estimable
        acceptance = story.get("acceptance_criteria", [])
        if acceptance:
            score += 20.0
            if len(acceptance) >= 3:
                score += 10.0

        # Clear description helps estimation
        description = story.get("description", "")
        if description and len(description) > 50:
            score += 10.0

        return min(100.0, score)

    def _evaluate_small(self, story: dict[str, Any]) -> float:
        """Evaluate if story is appropriately sized (0-100)."""
        score = 100.0

        # Check story points
        points = story.get("story_points", 0)
        if points > 8:
            score -= 40.0  # Too large
        elif points > 5:
            score -= 20.0  # Large but acceptable

        # Check acceptance criteria count
        acceptance = story.get("acceptance_criteria", [])
        if len(acceptance) > 7:
            score -= 30.0  # Too many acceptance criteria = too large
        elif len(acceptance) > 5:
            score -= 15.0

        # Check description length (very long = might be too large)
        description = story.get("description", "")
        if len(description) > 500:
            score -= 20.0

        return max(0.0, score)

    def _evaluate_testable(self, story: dict[str, Any]) -> float:
        """Evaluate if story is testable (0-100)."""
        score = 0.0

        # Has acceptance criteria = testable
        acceptance = story.get("acceptance_criteria", [])
        if acceptance:
            score += 50.0

            # Check quality of acceptance criteria
            testable_count = 0
            for criterion in acceptance:
                if isinstance(criterion, str):
                    if self._is_testable_criterion(criterion):
                        testable_count += 1

            if testable_count > 0:
                testable_ratio = testable_count / len(acceptance)
                score += testable_ratio * 50.0
        else:
            # No acceptance criteria = not testable
            return 0.0

        # Clear description helps testability
        description = story.get("description", "")
        if description and "as a" in description.lower() and "i want" in description.lower():
            score += 20.0

        return min(100.0, score)

    def _is_testable_criterion(self, criterion: str) -> bool:
        """Check if acceptance criterion is testable."""
        criterion_lower = criterion.lower()

        # Testable criteria have:
        # - Specific conditions
        # - Observable outcomes
        # - Measurable results

        testable_indicators = [
            "when",
            "then",
            "should",
            "must",
            "will",
            "displays",
            "shows",
            "returns",
            "validates",
            "verifies",
            "checks",
        ]

        has_indicator = any(indicator in criterion_lower for indicator in testable_indicators)

        # Check for measurable outcomes
        measurable = any(
            word in criterion_lower
            for word in ["seconds", "milliseconds", "users", "requests", "percentage", "%", "times"]
        )

        return has_indicator or measurable or len(criterion) > 30  # Longer = more likely testable

    def _identify_issues(self, story: dict[str, Any], score: StoryQualityScore) -> list[str]:
        """Identify issues in story."""
        issues = []

        if score.independent < 60.0:
            issues.append("Story has too many dependencies - not independent")

        if score.valuable < 60.0:
            issues.append("Story value is unclear - missing 'So that...' clause")

        if score.estimable < 60.0:
            issues.append("Story cannot be estimated - missing story points or details")

        if score.small < 60.0:
            issues.append("Story is too large - consider breaking down")

        if score.testable < 60.0:
            issues.append("Story is not testable - missing or weak acceptance criteria")

        acceptance = story.get("acceptance_criteria", [])
        if len(acceptance) < 2:
            issues.append("Story has insufficient acceptance criteria")

        return issues

    def _identify_strengths(self, story: dict[str, Any], score: StoryQualityScore) -> list[str]:
        """Identify strengths in story."""
        strengths = []

        if score.independent >= 80.0:
            strengths.append("Story is independent - can be developed standalone")

        if score.valuable >= 80.0:
            strengths.append("Clear value proposition")

        if score.estimable >= 80.0:
            strengths.append("Well-estimated with story points")

        if score.small >= 80.0:
            strengths.append("Appropriately sized")

        if score.testable >= 80.0:
            strengths.append("Well-defined acceptance criteria")

        acceptance = story.get("acceptance_criteria", [])
        if len(acceptance) >= 3:
            strengths.append("Comprehensive acceptance criteria")

        return strengths

    def _generate_recommendations(self, score: StoryQualityScore) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if score.independent < 70.0:
            recommendations.append("Reduce dependencies or split into multiple stories")

        if score.valuable < 70.0:
            recommendations.append("Add 'So that...' clause to clarify value")

        if score.estimable < 70.0:
            recommendations.append("Add story points and more detailed description")

        if score.small < 70.0:
            recommendations.append("Break story into smaller stories")

        if score.testable < 70.0:
            recommendations.append("Add more detailed, testable acceptance criteria")
            recommendations.append("Use Given-When-Then format for acceptance criteria")

        return recommendations
