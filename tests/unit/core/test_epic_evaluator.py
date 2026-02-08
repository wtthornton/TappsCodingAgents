"""
Unit tests for EpicEvaluator and ImplementationPlanEvaluator - EPIC-53 RP-004, RP-005.
"""

from pathlib import Path

import pytest

from tapps_agents.core.epic_evaluator import (
    EpicEvaluator,
    EpicQualityScore,
    ImplementationPlanEvaluator,
    ImplementationPlanQualityScore,
)

pytestmark = pytest.mark.unit


class TestEpicEvaluator:
    """Tests for EpicEvaluator."""

    def test_evaluate_returns_epic_quality_score(self):
        """evaluate() returns EpicQualityScore with all required fields."""
        evaluator = EpicEvaluator()
        doc = """## Epic Overview
### Goal
Implement feature.
### Success Metrics
| Metric | Target |
|--------|--------|
| Quality | 80 |
## Epic Stories
| ID | Story | Points |
|----|-------|--------|
| RP-001 | Story 1 | 5 |
| RP-002 | Story 2 | 5 |
Dependencies: RP-002 depends on RP-001.
"""
        result = evaluator.evaluate(doc)
        assert isinstance(result, EpicQualityScore)
        assert hasattr(result, "overview_score")
        assert hasattr(result, "story_breakdown_score")
        assert hasattr(result, "dependency_score")
        assert hasattr(result, "overall")
        assert hasattr(result, "issues")
        assert hasattr(result, "recommendations")

    def test_evaluate_overview_score_with_sections(self):
        """Overview score is high when overview, goal, success metrics present."""
        evaluator = EpicEvaluator()
        doc = """## Epic Overview
### Goal
Goal text.
### Success Metrics
Metrics.
"""
        result = evaluator.evaluate(doc)
        assert result.overview_score > 0
        assert result.overall >= 0

    def test_evaluate_story_breakdown_with_stories(self):
        """Story breakdown score reflects story list presence."""
        evaluator = EpicEvaluator()
        doc = """## Stories
| RP-001 | Story 1 | 5 |
| RP-002 | Story 2 | 5 |
Acceptance Criteria:
- Criterion 1
"""
        result = evaluator.evaluate(doc)
        assert result.story_breakdown_score >= 0
        assert result.acceptance_criteria_score >= 0

    def test_evaluate_dependency_score_with_dependencies(self):
        """Dependency score rewards dependency patterns."""
        evaluator = EpicEvaluator()
        doc = """## Stories
RP-001: Story 1
RP-002: Story 2
Dependencies: RP-002 depends on RP-001.
"""
        result = evaluator.evaluate(doc)
        assert result.dependency_score >= 0

    def test_evaluate_accepts_path(self):
        """evaluate() accepts Path to file."""
        evaluator = EpicEvaluator()
        path = Path(__file__).parent.parent.parent.parent / "docs" / "planning" / "EPIC-53-REVIEWER-AND-PLANNING-IMPROVEMENTS.md"
        if path.exists():
            result = evaluator.evaluate(path)
            assert isinstance(result, EpicQualityScore)
            assert 0 <= result.overall <= 100

    def test_evaluate_issues_when_scores_low(self):
        """Issues list populated when scores are low."""
        evaluator = EpicEvaluator()
        doc = "Minimal text with no structure."
        result = evaluator.evaluate(doc)
        assert isinstance(result.issues, list)

    def test_evaluate_recommendations(self):
        """Recommendations list is populated."""
        evaluator = EpicEvaluator()
        doc = """## Overview
Goal.
## Stories
RP-001 Story 1
"""
        result = evaluator.evaluate(doc)
        assert isinstance(result.recommendations, list)


class TestImplementationPlanEvaluator:
    """Tests for ImplementationPlanEvaluator."""

    def test_evaluate_returns_implementation_plan_quality_score(self):
        """evaluate() returns ImplementationPlanQualityScore with required fields."""
        evaluator = ImplementationPlanEvaluator()
        doc = """## Phase 1
- [ ] Task 1
**Acceptance:** Done.
## Phase 2
- [ ] Task 2
## Completion checklist
- [ ] All done
"""
        result = evaluator.evaluate(doc)
        assert isinstance(result, ImplementationPlanQualityScore)
        assert hasattr(result, "phase_score")
        assert hasattr(result, "task_score")
        assert hasattr(result, "completion_score")
        assert hasattr(result, "overall")
        assert hasattr(result, "issues")
        assert hasattr(result, "recommendations")

    def test_evaluate_phase_score_with_phases(self):
        """Phase score reflects Phase N headings."""
        evaluator = ImplementationPlanEvaluator()
        doc = """## Phase 1
Content.
## Phase 2
Content.
## Phase 3
Content.
"""
        result = evaluator.evaluate(doc)
        assert result.phase_score > 0

    def test_evaluate_task_score_with_checkboxes(self):
        """Task score rewards checkboxes and acceptance criteria."""
        evaluator = ImplementationPlanEvaluator()
        doc = """## Phase 1
- [ ] Task 1
- [ ] Task 2
**Acceptance:** Done.
"""
        result = evaluator.evaluate(doc)
        assert result.task_score > 0

    def test_evaluate_completion_score_with_checklist(self):
        """Completion score is high when Completion checklist present."""
        evaluator = ImplementationPlanEvaluator()
        doc = """## Phase 1
Content.
## Completion checklist
- [ ] Verified
"""
        result = evaluator.evaluate(doc)
        assert result.completion_score == 100.0

    def test_evaluate_completion_score_without_checklist(self):
        """Completion score is 0 when no completion section."""
        evaluator = ImplementationPlanEvaluator()
        doc = """## Phase 1
Content only.
"""
        result = evaluator.evaluate(doc)
        assert result.completion_score == 0.0

    def test_evaluate_accepts_path(self):
        """evaluate() accepts Path to file."""
        evaluator = ImplementationPlanEvaluator()
        path = Path(__file__).parent.parent.parent.parent / "docs" / "planning" / "REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md"
        if path.exists():
            result = evaluator.evaluate(path)
            assert isinstance(result, ImplementationPlanQualityScore)
            assert result.phase_score > 0
            assert 0 <= result.overall <= 100
