"""
Unit tests for MarkdownPlanningScorer - EPIC-53 RP-003.
"""

from pathlib import Path

import pytest

from tapps_agents.agents.reviewer.markdown_planning_scorer import MarkdownPlanningScorer

pytestmark = pytest.mark.unit


class TestMarkdownPlanningScorer:
    """Tests for MarkdownPlanningScorer."""

    def test_score_file_returns_all_required_keys(self):
        """Score dict includes overall_score, structure, completeness, traceability, format, metrics."""
        scorer = MarkdownPlanningScorer()
        doc = """## Purpose
Test document.
## Scope
In scope.
## Goals
Goal 1.
## Phase 1
- [ ] Task 1
"""
        result = scorer.score_file(Path("doc.md"), doc)
        assert "overall_score" in result
        assert "structure_score" in result
        assert "completeness_score" in result
        assert "traceability_score" in result
        assert "format_score" in result
        assert "metrics" in result

    def test_score_file_structure_with_standard_sections(self):
        """Structure score is high when Purpose, Scope, Goals, Phase are present."""
        scorer = MarkdownPlanningScorer()
        doc = """## Purpose
PRD purpose.
## Scope
In scope.
## Goals
Goal 1, Goal 2.
## Phase 1
Content.
"""
        result = scorer.score_file(Path("doc.md"), doc)
        assert result["structure_score"] >= 70
        assert result["overall_score"] > 0

    def test_score_file_structure_missing_sections(self):
        """Structure score is low when standard sections are missing."""
        scorer = MarkdownPlanningScorer()
        doc = "Plain text with no headings."
        result = scorer.score_file(Path("doc.md"), doc)
        assert result["structure_score"] == 0.0

    def test_score_file_completeness_penalizes_tbd(self):
        """Completeness score penalizes TBD/TODO placeholders."""
        scorer = MarkdownPlanningScorer()
        doc = """## Purpose
TBD
## Scope
TODO: fill
TBD TBD TBD TBD TBD
"""
        result = scorer.score_file(Path("doc.md"), doc)
        assert result["completeness_score"] < 100.0

    def test_score_file_traceability_with_links(self):
        """Traceability score rewards internal links."""
        scorer = MarkdownPlanningScorer()
        doc = """## Purpose
See [plan](docs/plan.md) and [section](#scope).
## Scope
Content.
"""
        result = scorer.score_file(Path("doc.md"), doc)
        assert result["traceability_score"] > 0

    def test_score_file_traceability_no_links(self):
        """Traceability score is 0 with no links."""
        scorer = MarkdownPlanningScorer()
        doc = "No links here."
        result = scorer.score_file(Path("doc.md"), doc)
        assert result["traceability_score"] == 0.0

    def test_score_file_format_with_headings_and_lists(self):
        """Format score rewards headings, lists, tables."""
        scorer = MarkdownPlanningScorer()
        doc = """## Section 1
- Item 1
- Item 2
| Col | Val |
|-----|-----|
| A   | 1   |
"""
        result = scorer.score_file(Path("doc.md"), doc)
        assert result["format_score"] > 0

    def test_score_file_overall_not_fallback_50(self):
        """Overall score is not the generic 50.0 fallback for planning docs."""
        scorer = MarkdownPlanningScorer()
        doc = """## Purpose
Purpose.
## Scope
Scope.
## Goals
Goals.
## Phase 1
- [ ] Task 1
- [ ] Task 2
[Link](path.md)
"""
        result = scorer.score_file(Path("doc.md"), doc)
        assert result["overall_score"] != 50.0
        assert 0 <= result["overall_score"] <= 100

    def test_metrics_includes_issues_and_strengths(self):
        """Metrics dict includes issues and strengths."""
        scorer = MarkdownPlanningScorer()
        doc = """## Purpose
Good doc.
## Scope
In scope.
"""
        result = scorer.score_file(Path("doc.md"), doc)
        assert "issues" in result["metrics"]
        assert "strengths" in result["metrics"]
        assert isinstance(result["metrics"]["issues"], list)
        assert isinstance(result["metrics"]["strengths"], list)
