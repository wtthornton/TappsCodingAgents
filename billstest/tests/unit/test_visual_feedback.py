"""
Unit tests for Visual Feedback System (Phase 2.1).
"""

from datetime import UTC, datetime

import pytest

from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.visual_feedback import (
    AccessibilityMetrics,
    LayoutMetrics,
    RenderingMode,
    UIComparator,
    VisualAnalyzer,
    VisualElement,
    VisualElementType,
    VisualFeedback,
    VisualFeedbackCollector,
    VisualPatternLearner,
)

pytestmark = pytest.mark.unit


class TestVisualFeedbackCollector:
    """Test VisualFeedbackCollector functionality."""

    def test_initialization_default_profile(self):
        """Test collector initialization with default profile."""
        collector = VisualFeedbackCollector()
        assert collector.hardware_profile is not None
        assert collector.rendering_mode in [
            RenderingMode.LIGHTWEIGHT,
            RenderingMode.STANDARD,
            RenderingMode.FULL,
        ]
        assert len(collector.feedback_history) == 0

    def test_initialization_nuc_profile(self):
        """Test collector initialization with NUC profile."""
        collector = VisualFeedbackCollector(hardware_profile=HardwareProfile.NUC)
        assert collector.hardware_profile == HardwareProfile.NUC
        assert collector.rendering_mode == RenderingMode.LIGHTWEIGHT

    def test_initialization_workstation_profile(self):
        """Test collector initialization with workstation profile."""
        collector = VisualFeedbackCollector(
            hardware_profile=HardwareProfile.WORKSTATION
        )
        assert collector.hardware_profile == HardwareProfile.WORKSTATION
        assert collector.rendering_mode == RenderingMode.FULL

    def test_collect_feedback(self):
        """Test collecting feedback."""
        collector = VisualFeedbackCollector()

        elements = [
            VisualElement(
                element_type=VisualElementType.BUTTON,
                position=(10.0, 20.0),
                size=(100.0, 40.0),
                text="Click me",
            )
        ]

        feedback = collector.collect_feedback(
            iteration=1,
            screenshot_path="/path/to/screenshot.png",
            visual_elements=elements,
            user_interactions=[{"type": "click", "element": "button"}],
            metadata={"test": True},
        )

        assert feedback.iteration == 1
        assert feedback.screenshot_path == "/path/to/screenshot.png"
        assert len(feedback.visual_elements) == 1
        assert len(feedback.user_interactions) == 1
        assert feedback.metadata["test"] is True
        assert len(collector.feedback_history) == 1

    def test_get_feedback_history(self):
        """Test getting feedback history."""
        collector = VisualFeedbackCollector()

        for i in range(5):
            collector.collect_feedback(iteration=i)

        history = collector.get_feedback_history()
        assert len(history) == 5

        limited = collector.get_feedback_history(limit=3)
        assert len(limited) == 3
        assert limited[0].iteration == 2  # Last 3 items

    def test_clear_history(self):
        """Test clearing feedback history."""
        collector = VisualFeedbackCollector()

        for i in range(3):
            collector.collect_feedback(iteration=i)

        assert len(collector.feedback_history) == 3
        collector.clear_history()
        assert len(collector.feedback_history) == 0


class TestVisualAnalyzer:
    """Test VisualAnalyzer functionality."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = VisualAnalyzer()
        assert analyzer.hardware_profile is not None
        assert analyzer.rendering_mode in [
            RenderingMode.LIGHTWEIGHT,
            RenderingMode.STANDARD,
            RenderingMode.FULL,
        ]

    def test_analyze_layout_empty_elements(self):
        """Test layout analysis with empty elements."""
        analyzer = VisualAnalyzer()
        metrics = analyzer.analyze_layout([])

        assert metrics.spacing_consistency == 0.0
        assert metrics.alignment_score == 0.0
        assert len(metrics.issues) > 0

    def test_analyze_layout_lightweight(self):
        """Test lightweight layout analysis."""
        analyzer = VisualAnalyzer(hardware_profile=HardwareProfile.NUC)

        elements = [
            VisualElement(
                element_type=VisualElementType.BUTTON,
                position=(10.0, 20.0),
                size=(100.0, 40.0),
            ),
            VisualElement(
                element_type=VisualElementType.TEXT,
                position=(10.0, 70.0),
                size=(200.0, 30.0),
            ),
        ]

        metrics = analyzer.analyze_layout(elements)

        assert 0.0 <= metrics.spacing_consistency <= 1.0
        assert 0.0 <= metrics.alignment_score <= 1.0
        assert 0.0 <= metrics.visual_hierarchy <= 1.0

    def test_analyze_layout_detailed(self):
        """Test detailed layout analysis."""
        analyzer = VisualAnalyzer(hardware_profile=HardwareProfile.WORKSTATION)

        elements = [
            VisualElement(
                element_type=VisualElementType.BUTTON,
                position=(10.0, 20.0),
                size=(100.0, 40.0),
            ),
            VisualElement(
                element_type=VisualElementType.TEXT,
                position=(10.0, 70.0),  # 10px spacing
                size=(200.0, 30.0),
            ),
            VisualElement(
                element_type=VisualElementType.INPUT,
                position=(10.0, 110.0),  # 10px spacing
                size=(200.0, 40.0),
            ),
        ]

        metrics = analyzer.analyze_layout(elements)

        assert 0.0 <= metrics.spacing_consistency <= 1.0
        assert 0.0 <= metrics.alignment_score <= 1.0
        assert 0.0 <= metrics.visual_hierarchy <= 1.0
        assert 0.0 <= metrics.whitespace_balance <= 1.0
        assert 0.0 <= metrics.grid_consistency <= 1.0

    def test_analyze_accessibility_lightweight(self):
        """Test lightweight accessibility analysis."""
        analyzer = VisualAnalyzer(hardware_profile=HardwareProfile.NUC)

        elements = [
            VisualElement(
                element_type=VisualElementType.BUTTON,
                position=(10.0, 20.0),
                size=(100.0, 40.0),
            )
        ]

        metrics = analyzer.analyze_accessibility(elements)

        assert 0.0 <= metrics.color_contrast_score <= 1.0
        assert isinstance(metrics.keyboard_navigable, bool)
        assert isinstance(metrics.screen_reader_compatible, bool)

    def test_analyze_accessibility_detailed(self):
        """Test detailed accessibility analysis."""
        analyzer = VisualAnalyzer(hardware_profile=HardwareProfile.WORKSTATION)

        elements = [
            VisualElement(
                element_type=VisualElementType.BUTTON,
                position=(10.0, 20.0),
                size=(100.0, 40.0),
            )
        ]

        html_with_aria = '<button aria-label="Submit">Submit</button>'
        metrics = analyzer.analyze_accessibility(elements, html_content=html_with_aria)

        assert 0.0 <= metrics.color_contrast_score <= 1.0
        assert metrics.aria_labels_present is True

    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        analyzer = VisualAnalyzer()

        layout_metrics = LayoutMetrics(
            spacing_consistency=0.8,
            alignment_score=0.9,
            visual_hierarchy=0.7,
            whitespace_balance=0.8,
            grid_consistency=0.85,
        )

        accessibility_metrics = AccessibilityMetrics(
            color_contrast_score=0.9,
            keyboard_navigable=True,
            screen_reader_compatible=True,
            aria_labels_present=True,
            focus_indicators_present=True,
        )

        score = analyzer.calculate_quality_score(layout_metrics, accessibility_metrics)

        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Should be high with good metrics

    def test_calculate_quality_score_custom_weights(self):
        """Test quality score with custom weights."""
        analyzer = VisualAnalyzer()

        layout_metrics = LayoutMetrics(
            spacing_consistency=0.5,
            alignment_score=0.5,
            visual_hierarchy=0.5,
            whitespace_balance=0.5,
            grid_consistency=0.5,
        )

        accessibility_metrics = AccessibilityMetrics(
            color_contrast_score=1.0,
            keyboard_navigable=True,
            screen_reader_compatible=True,
            aria_labels_present=True,
            focus_indicators_present=True,
        )

        # Weight accessibility more
        score = analyzer.calculate_quality_score(
            layout_metrics,
            accessibility_metrics,
            weights={"layout": 0.3, "accessibility": 0.7},
        )

        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Should be high due to accessibility weight


class TestUIComparator:
    """Test UIComparator functionality."""

    def test_compare_iterations_improvement(self):
        """Test comparing iterations with improvement."""
        comparator = UIComparator()

        previous = VisualFeedback(
            timestamp=datetime.now(UTC),
            iteration=1,
            quality_score=0.6,
            layout_metrics=LayoutMetrics(
                spacing_consistency=0.5,
                alignment_score=0.5,
                visual_hierarchy=0.5,
                whitespace_balance=0.5,
                grid_consistency=0.5,
            ),
            accessibility_metrics=AccessibilityMetrics(
                color_contrast_score=0.5,
                keyboard_navigable=False,
                screen_reader_compatible=False,
                aria_labels_present=False,
                focus_indicators_present=False,
            ),
        )

        current = VisualFeedback(
            timestamp=datetime.now(UTC),
            iteration=2,
            quality_score=0.8,
            layout_metrics=LayoutMetrics(
                spacing_consistency=0.8,
                alignment_score=0.8,
                visual_hierarchy=0.8,
                whitespace_balance=0.8,
                grid_consistency=0.8,
            ),
            accessibility_metrics=AccessibilityMetrics(
                color_contrast_score=0.9,
                keyboard_navigable=True,
                screen_reader_compatible=True,
                aria_labels_present=True,
                focus_indicators_present=True,
            ),
        )

        result = comparator.compare_iterations(previous, current)

        assert len(result["improvements"]) > 0
        assert result["quality_delta"] > 0

    def test_compare_iterations_regression(self):
        """Test comparing iterations with regression."""
        comparator = UIComparator()

        previous = VisualFeedback(
            timestamp=datetime.now(UTC),
            iteration=1,
            quality_score=0.8,
            issues=[],
        )

        current = VisualFeedback(
            timestamp=datetime.now(UTC),
            iteration=2,
            quality_score=0.6,
            issues=["Issue 1", "Issue 2"],
        )

        result = comparator.compare_iterations(previous, current)

        assert len(result["regressions"]) > 0
        assert result["quality_delta"] < 0

    def test_get_improvement_trend_improving(self):
        """Test getting improvement trend."""
        comparator = UIComparator()

        feedback_history = [
            VisualFeedback(
                timestamp=datetime.now(UTC),
                iteration=i,
                quality_score=0.5 + (i * 0.1),
            )
            for i in range(1, 6)
        ]

        trend = comparator.get_improvement_trend(feedback_history)

        assert trend["trend"] == "improving"
        assert trend["average_improvement"] > 0
        assert trend["iterations"] == 5

    def test_get_improvement_trend_insufficient_data(self):
        """Test trend with insufficient data."""
        comparator = UIComparator()

        feedback_history = [
            VisualFeedback(timestamp=datetime.now(UTC), iteration=1, quality_score=0.5)
        ]

        trend = comparator.get_improvement_trend(feedback_history)

        assert trend["trend"] == "insufficient_data"
        assert trend["iterations"] == 1


class TestVisualPatternLearner:
    """Test VisualPatternLearner functionality."""

    def test_learn_from_feedback(self):
        """Test learning from feedback."""
        learner = VisualPatternLearner()

        feedback = VisualFeedback(
            timestamp=datetime.now(UTC),
            iteration=1,
            layout_metrics=LayoutMetrics(
                spacing_consistency=0.9,
                alignment_score=0.9,
                visual_hierarchy=0.8,
                whitespace_balance=0.8,
                grid_consistency=0.8,
            ),
            accessibility_metrics=AccessibilityMetrics(
                color_contrast_score=0.9,
                keyboard_navigable=True,
                screen_reader_compatible=True,
                aria_labels_present=True,
                focus_indicators_present=True,
            ),
        )

        learner.learn_from_feedback(feedback)

        assert len(learner.feedback_history) == 1
        assert learner.patterns.get("high_spacing_consistency", 0) > 0
        assert learner.patterns.get("high_alignment", 0) > 0

    def test_get_recommendations(self):
        """Test getting recommendations."""
        learner = VisualPatternLearner()

        # Add multiple feedback items with good patterns
        for i in range(6):
            feedback = VisualFeedback(
                timestamp=datetime.now(UTC),
                iteration=i,
                layout_metrics=LayoutMetrics(
                    spacing_consistency=0.9,
                    alignment_score=0.9,
                    visual_hierarchy=0.8,
                    whitespace_balance=0.8,
                    grid_consistency=0.8,
                ),
                accessibility_metrics=AccessibilityMetrics(
                    color_contrast_score=0.9,
                    keyboard_navigable=True,
                    screen_reader_compatible=True,
                    aria_labels_present=True,
                    focus_indicators_present=True,
                ),
            )
            learner.learn_from_feedback(feedback)

        recommendations = learner.get_recommendations()

        assert len(recommendations) > 0
        assert any("spacing" in rec.lower() for rec in recommendations)

    def test_clear_patterns(self):
        """Test clearing patterns."""
        learner = VisualPatternLearner()

        feedback = VisualFeedback(
            timestamp=datetime.now(UTC),
            iteration=1,
            layout_metrics=LayoutMetrics(
                spacing_consistency=0.9,
                alignment_score=0.9,
                visual_hierarchy=0.8,
                whitespace_balance=0.8,
                grid_consistency=0.8,
            ),
        )

        learner.learn_from_feedback(feedback)
        assert len(learner.feedback_history) > 0

        learner.clear_patterns()
        assert len(learner.feedback_history) == 0
        assert len(learner.patterns) == 0
