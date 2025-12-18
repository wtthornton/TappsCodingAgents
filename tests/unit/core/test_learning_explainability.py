"""
Unit tests for learning explainability system.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from tapps_agents.core.learning_explainability import (
    DecisionReasoningLogger,
    DecisionLog,
    PatternSelectionExplainer,
    LearningImpactReporter,
)
from tapps_agents.core.agent_learning import CodePattern


class TestDecisionReasoningLogger:
    """Test DecisionReasoningLogger functionality."""

    def test_init(self):
        """Test DecisionReasoningLogger initialization."""
        logger = DecisionReasoningLogger()
        assert logger is not None
        assert len(logger.decision_logs) == 0
        assert logger.max_logs == 1000

    def test_log_decision(self):
        """Test logging a decision."""
        logger = DecisionReasoningLogger()

        decision_id = logger.log_decision(
            decision_type="pattern_extraction_threshold",
            reasoning="High confidence from learned experience",
            sources=["learned_experience"],
            confidence=0.85,
            outcome=0.75,
            context={"task_id": "test_1"},
        )

        assert decision_id is not None
        assert len(logger.decision_logs) == 1
        assert logger.decision_logs[0].decision_id == decision_id
        assert logger.decision_logs[0].decision_type == "pattern_extraction_threshold"

    def test_get_decision_history(self):
        """Test retrieving decision history."""
        logger = DecisionReasoningLogger()

        # Log some decisions
        logger.log_decision(
            decision_type="threshold",
            reasoning="Test 1",
            sources=["source1"],
            confidence=0.8,
            outcome="result1",
        )
        logger.log_decision(
            decision_type="threshold",
            reasoning="Test 2",
            sources=["source2"],
            confidence=0.9,
            outcome="result2",
        )
        logger.log_decision(
            decision_type="other",
            reasoning="Test 3",
            sources=["source3"],
            confidence=0.7,
            outcome="result3",
        )

        # Get all decisions
        all_decisions = logger.get_decision_history()
        assert len(all_decisions) == 3

        # Filter by type
        threshold_decisions = logger.get_decision_history(decision_type="threshold")
        assert len(threshold_decisions) == 2

        # Limit results
        limited = logger.get_decision_history(limit=2)
        assert len(limited) == 2

    def test_explain_decision(self):
        """Test explaining a decision."""
        logger = DecisionReasoningLogger()

        decision_id = logger.log_decision(
            decision_type="test_decision",
            reasoning="Test reasoning",
            sources=["learned_experience"],
            confidence=0.85,
            outcome="test_outcome",
            context={"key": "value"},
        )

        explanation = logger.explain_decision(decision_id)

        assert explanation is not None
        assert explanation["decision_id"] == decision_id
        assert explanation["reasoning"] == "Test reasoning"
        assert "explanation" in explanation

    def test_explain_decision_not_found(self):
        """Test explaining a non-existent decision."""
        logger = DecisionReasoningLogger()

        explanation = logger.explain_decision("nonexistent_id")
        assert explanation is None

    def test_get_decision_statistics(self):
        """Test getting decision statistics."""
        logger = DecisionReasoningLogger()

        # Log some decisions
        logger.log_decision(
            decision_type="type1",
            reasoning="Test",
            sources=["source1"],
            confidence=0.8,
            outcome="outcome1",
        )
        logger.log_decision(
            decision_type="type1",
            reasoning="Test",
            sources=["source2"],
            confidence=0.9,
            outcome="outcome2",
        )

        stats = logger.get_decision_statistics()

        assert stats["total_decisions"] == 2
        assert stats["by_type"]["type1"] == 2
        assert stats["average_confidence"] > 0.0

    def test_max_logs_limit(self):
        """Test that max_logs limit is enforced."""
        logger = DecisionReasoningLogger()
        logger.max_logs = 5

        # Log more than max_logs
        for i in range(10):
            logger.log_decision(
                decision_type="test",
                reasoning=f"Test {i}",
                sources=["source"],
                confidence=0.8,
                outcome=f"outcome{i}",
            )

        assert len(logger.decision_logs) == 5  # Should be limited


class TestPatternSelectionExplainer:
    """Test PatternSelectionExplainer functionality."""

    def test_init(self):
        """Test PatternSelectionExplainer initialization."""
        explainer = PatternSelectionExplainer()
        assert explainer is not None

    def test_explain_pattern_selection(self):
        """Test explaining pattern selection."""
        explainer = PatternSelectionExplainer()

        patterns = [
            CodePattern(
                pattern_id="pattern_1",
                pattern_type="function",
                code_snippet="def test():\n    pass",
                context="Test function",
                quality_score=0.9,
                usage_count=5,
                success_rate=0.95,
                learned_from=["task_1"],
                security_score=8.0,
            ),
            CodePattern(
                pattern_id="pattern_2",
                pattern_type="class",
                code_snippet="class Test:\n    pass",
                context="Test class",
                quality_score=0.8,
                usage_count=3,
                success_rate=0.85,
                learned_from=["task_2"],
                security_score=7.5,
            ),
        ]

        explanation = explainer.explain_pattern_selection(
            selected_patterns=patterns,
            context="test context",
        )

        assert explanation["selected_count"] == 2
        assert len(explanation["patterns"]) == 2
        assert "explanation" in explanation

    def test_explain_pattern_selection_empty(self):
        """Test explaining empty pattern selection."""
        explainer = PatternSelectionExplainer()

        explanation = explainer.explain_pattern_selection(
            selected_patterns=[],
            context="test",
        )

        assert explanation["selected_count"] == 0
        assert explanation["explanation"] == "No patterns selected for this context."

    def test_explain_pattern_relevance(self):
        """Test explaining pattern relevance."""
        explainer = PatternSelectionExplainer()

        pattern = CodePattern(
            pattern_id="pattern_1",
            pattern_type="function",
            code_snippet="def test():\n    pass",
            context="Test function",
            quality_score=0.9,
            usage_count=5,
            success_rate=0.95,
            learned_from=["task_1"],
            security_score=8.0,
        )

        explanation = explainer.explain_pattern_relevance(
            pattern=pattern,
            context="test context",
        )

        assert "relevance_score" in explanation
        assert "factors" in explanation
        assert "explanation" in explanation

    def test_compare_patterns(self):
        """Test comparing patterns."""
        explainer = PatternSelectionExplainer()

        patterns = [
            CodePattern(
                pattern_id="pattern_1",
                pattern_type="function",
                code_snippet="def test1():\n    pass",
                context="Test 1",
                quality_score=0.9,
                usage_count=5,
                success_rate=0.95,
                learned_from=["task_1"],
                security_score=8.0,
            ),
            CodePattern(
                pattern_id="pattern_2",
                pattern_type="function",
                code_snippet="def test2():\n    pass",
                context="Test 2",
                quality_score=0.7,
                usage_count=2,
                success_rate=0.80,
                learned_from=["task_2"],
                security_score=6.0,
            ),
        ]

        comparison = explainer.compare_patterns(patterns)

        assert len(comparison["patterns"]) == 2
        assert "comparison" in comparison
        # Should be sorted by quality + security
        assert comparison["patterns"][0]["quality_score"] >= comparison["patterns"][1]["quality_score"]

    def test_get_pattern_justification(self):
        """Test getting pattern justification."""
        explainer = PatternSelectionExplainer()

        pattern = CodePattern(
            pattern_id="pattern_1",
            pattern_type="function",
            code_snippet="def test():\n    pass",
            context="Test function",
            quality_score=0.9,
            usage_count=5,
            success_rate=0.95,
            learned_from=["task_1"],
            security_score=8.0,
        )

        justification = explainer.get_pattern_justification(
            pattern=pattern,
            context="test context",
        )

        assert isinstance(justification, str)
        assert "pattern_1" in justification
        assert "quality" in justification.lower()


class TestLearningImpactReporter:
    """Test LearningImpactReporter functionality."""

    def test_init(self):
        """Test LearningImpactReporter initialization."""
        reporter = LearningImpactReporter()
        assert reporter is not None
        assert len(reporter.impact_history) == 0

    def test_generate_impact_report(self):
        """Test generating impact report."""
        reporter = LearningImpactReporter()

        before_metrics = {
            "quality_score": 0.7,
            "success_rate": 0.8,
            "usage_count": 10,
        }
        after_metrics = {
            "quality_score": 0.85,
            "success_rate": 0.9,
            "usage_count": 15,
        }

        report = reporter.generate_impact_report(
            capability_id="test_capability",
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            learning_session_id="session_1",
        )

        assert report["capability_id"] == "test_capability"
        assert "improvements" in report
        assert "overall_improvement" in report
        assert "effectiveness" in report
        assert len(reporter.impact_history) == 1

    def test_track_improvement(self):
        """Test tracking improvement."""
        reporter = LearningImpactReporter()

        tracking = reporter.track_improvement(
            capability_id="test_capability",
            metric_name="quality_score",
            before_value=0.7,
            after_value=0.85,
        )

        assert tracking["capability_id"] == "test_capability"
        assert tracking["metric"] == "quality_score"
        assert tracking["before"] == 0.7
        assert tracking["after"] == 0.85
        assert tracking["improvement"] > 0

    def test_get_learning_effectiveness(self):
        """Test getting learning effectiveness."""
        reporter = LearningImpactReporter()

        # Generate some reports
        reporter.generate_impact_report(
            capability_id="test_capability",
            before_metrics={"quality_score": 0.7},
            after_metrics={"quality_score": 0.8},
        )
        reporter.generate_impact_report(
            capability_id="test_capability",
            before_metrics={"quality_score": 0.8},
            after_metrics={"quality_score": 0.9},
        )

        effectiveness = reporter.get_learning_effectiveness(
            capability_id="test_capability"
        )

        assert effectiveness["total_sessions"] == 2
        assert "average_improvement" in effectiveness
        assert "effectiveness_score" in effectiveness

    def test_export_report_markdown(self):
        """Test exporting report as markdown."""
        reporter = LearningImpactReporter()

        report = reporter.generate_impact_report(
            capability_id="test_capability",
            before_metrics={"quality_score": 0.7},
            after_metrics={"quality_score": 0.85},
        )

        markdown = reporter.export_report(report, format="markdown")

        assert isinstance(markdown, str)
        assert "Learning Impact Report" in markdown
        assert "test_capability" in markdown

    def test_export_report_json(self):
        """Test exporting report as JSON."""
        reporter = LearningImpactReporter()

        report = reporter.generate_impact_report(
            capability_id="test_capability",
            before_metrics={"quality_score": 0.7},
            after_metrics={"quality_score": 0.85},
        )

        json_str = reporter.export_report(report, format="json")

        assert isinstance(json_str, str)
        assert "test_capability" in json_str

