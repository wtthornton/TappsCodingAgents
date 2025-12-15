"""
Integration tests for Visual Feedback System (Phase 2.4).
"""

import tempfile
from pathlib import Path

import pytest

from tapps_agents.agents.designer.visual_designer import (
    IterativeRefinement,
    RefinementConfig,
)
from tapps_agents.core.browser_controller import BrowserController
from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.visual_feedback import (
    UIComparator,
    VisualAnalyzer,
    VisualElement,
    VisualElementType,
    VisualFeedbackCollector,
    VisualPatternLearner,
)

pytestmark = pytest.mark.integration


class TestVisualFeedbackIntegration:
    """Integration tests for visual feedback system."""

    @pytest.mark.asyncio
    async def test_end_to_end_refinement_workflow(self):
        """Test complete refinement workflow."""
        # Setup
        config = RefinementConfig(
            max_iterations=3,
            quality_threshold=0.5,  # Low threshold for testing
            min_improvement=0.01,
        )
        refinement = IterativeRefinement(
            hardware_profile=HardwareProfile.NUC,  # Use NUC for cloud rendering
            config=config,
        )

        initial_html = """
        <html>
        <body>
            <button>Click Me</button>
            <input type="text">
        </body>
        </html>
        """

        requirements = {"feature_description": "Test feature"}

        # Define simple refinement callback
        async def refine_callback(html, feedback, suggestions, reqs):
            # Simple refinement: add ARIA label if suggested
            if any("ARIA" in s for s in suggestions):
                return html.replace("<button>", '<button aria-label="Click button">')
            return html

        # Run refinement
        result = await refinement.refine_ui(
            initial_html, requirements, refinement_callback=refine_callback
        )

        # Verify
        assert result is not None
        assert result.iteration >= 1
        assert 0.0 <= result.quality_score <= 1.0

        # Get summary
        summary = refinement.get_refinement_summary()
        assert summary["iterations"] >= 1
        assert "final_quality" in summary

        # Cleanup
        refinement.stop_browser()

    def test_browser_controller_with_visual_analysis(self):
        """Test browser controller integration with visual analysis."""
        controller = BrowserController(hardware_profile=HardwareProfile.NUC)
        controller.start()

        try:
            # Load HTML
            html = """
            <html>
            <body>
                <h1>Test Page</h1>
                <button id="btn1">Button 1</button>
                <button id="btn2">Button 2</button>
            </body>
            </html>
            """
            controller.load_html(html)

            # Capture screenshot
            with tempfile.TemporaryDirectory() as tmpdir:
                screenshot_path = str(Path(tmpdir) / "test.png")
                controller.capture_screenshot(screenshot_path)
                assert Path(screenshot_path).exists()

            # Simulate interactions
            controller.click("#btn1")
            controller.click("#btn2")

            # Verify interactions recorded
            history = controller.get_interaction_history()
            assert len(history) == 2
            assert all(e.event_type == "click" for e in history)

        finally:
            controller.stop()

    def test_visual_analysis_with_browser_content(self):
        """Test visual analysis with browser-rendered content."""
        collector = VisualFeedbackCollector()
        analyzer = VisualAnalyzer()

        # Create elements (simulating extracted from browser)
        elements = [
            VisualElement(
                element_type=VisualElementType.BUTTON,
                position=(10.0, 20.0),
                size=(100.0, 40.0),
                text="Button 1",
            ),
            VisualElement(
                element_type=VisualElementType.BUTTON,
                position=(120.0, 20.0),
                size=(100.0, 40.0),
                text="Button 2",
            ),
        ]

        # Analyze
        layout_metrics = analyzer.analyze_layout(elements)
        accessibility_metrics = analyzer.analyze_accessibility(
            elements, html_content="<html><body><button>Button</button></body></html>"
        )

        # Calculate quality
        quality_score = analyzer.calculate_quality_score(
            layout_metrics, accessibility_metrics
        )

        # Collect feedback
        feedback = collector.collect_feedback(iteration=1, visual_elements=elements)
        feedback.layout_metrics = layout_metrics
        feedback.accessibility_metrics = accessibility_metrics
        feedback.quality_score = quality_score

        # Verify
        assert feedback.quality_score == quality_score
        assert feedback.layout_metrics is not None
        assert feedback.accessibility_metrics is not None

    def test_iteration_comparison_workflow(self):
        """Test comparing iterations in refinement workflow."""
        collector = VisualFeedbackCollector()
        comparator = UIComparator()
        analyzer = VisualAnalyzer()

        # Create elements for iteration 1
        elements1 = [
            VisualElement(
                element_type=VisualElementType.BUTTON,
                position=(10.0, 20.0),
                size=(100.0, 40.0),
            )
        ]

        layout1 = analyzer.analyze_layout(elements1)
        acc1 = analyzer.analyze_accessibility(elements1)
        quality1 = analyzer.calculate_quality_score(layout1, acc1)

        feedback1 = collector.collect_feedback(iteration=1, visual_elements=elements1)
        feedback1.layout_metrics = layout1
        feedback1.accessibility_metrics = acc1
        feedback1.quality_score = quality1

        # Create elements for iteration 2 (improved)
        elements2 = [
            VisualElement(
                element_type=VisualElementType.BUTTON,
                position=(10.0, 20.0),
                size=(120.0, 50.0),  # Larger, better hierarchy
            ),
            VisualElement(
                element_type=VisualElementType.TEXT,
                position=(10.0, 80.0),
                size=(200.0, 30.0),
            ),
        ]

        layout2 = analyzer.analyze_layout(elements2)
        acc2 = analyzer.analyze_accessibility(elements2)
        quality2 = analyzer.calculate_quality_score(layout2, acc2)

        feedback2 = collector.collect_feedback(iteration=2, visual_elements=elements2)
        feedback2.layout_metrics = layout2
        feedback2.accessibility_metrics = acc2
        feedback2.quality_score = quality2

        # Compare
        comparison = comparator.compare_iterations(feedback1, feedback2)

        # Verify comparison
        assert "improvements" in comparison
        assert "regressions" in comparison
        assert "quality_delta" in comparison
        assert comparison["quality_delta"] == quality2 - quality1

    def test_pattern_learning_integration(self):
        """Test pattern learning integration with feedback."""
        learner = VisualPatternLearner()
        analyzer = VisualAnalyzer()
        collector = VisualFeedbackCollector()

        # Create multiple feedback items with good patterns
        for i in range(3):
            elements = [
                VisualElement(
                    element_type=VisualElementType.BUTTON,
                    position=(10.0, 20.0 + i * 60),
                    size=(100.0, 40.0),
                )
            ]

            layout = analyzer.analyze_layout(elements)
            acc = analyzer.analyze_accessibility(elements)
            quality = analyzer.calculate_quality_score(layout, acc)

            feedback = collector.collect_feedback(
                iteration=i + 1, visual_elements=elements
            )
            feedback.layout_metrics = layout
            feedback.accessibility_metrics = acc
            feedback.quality_score = quality

            # Learn from feedback
            learner.learn_from_feedback(feedback)

        # Get recommendations
        recommendations = learner.get_recommendations()

        # Verify learning occurred
        assert len(learner.patterns) > 0
        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_hardware_aware_rendering(self):
        """Test hardware-aware rendering modes."""
        # Test NUC (cloud rendering)
        refinement_nuc = IterativeRefinement(hardware_profile=HardwareProfile.NUC)
        assert refinement_nuc.browser_controller is None
        result = refinement_nuc.start_browser()
        assert result is True  # Cloud rendering always succeeds
        assert refinement_nuc.browser_controller is not None
        assert refinement_nuc.browser_controller.rendering_mode.value == "cloud"
        refinement_nuc.stop_browser()

        # Test Workstation (local rendering)
        refinement_ws = IterativeRefinement(
            hardware_profile=HardwareProfile.WORKSTATION
        )
        assert refinement_ws.visual_analyzer.rendering_mode.value in [
            "standard",
            "full",
        ]

        # Test different analyzer modes
        analyzer_nuc = VisualAnalyzer(hardware_profile=HardwareProfile.NUC)
        assert analyzer_nuc.rendering_mode.value == "lightweight"

        analyzer_ws = VisualAnalyzer(hardware_profile=HardwareProfile.WORKSTATION)
        assert analyzer_ws.rendering_mode.value == "full"
