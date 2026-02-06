"""
Visual Designer Agent - Enhanced designer with visual feedback and iterative refinement.
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...core.browser_controller import BrowserController, BrowserType
from ...core.hardware_profiler import HardwareProfile, HardwareProfiler
from ...core.visual_feedback import (
    UIComparator,
    VisualAnalyzer,
    VisualElement,
    VisualElementType,
    VisualFeedback,
    VisualFeedbackCollector,
    VisualPatternLearner,
)
from .agent import DesignerAgent

logger = logging.getLogger(__name__)


@dataclass
class IterationResult:
    """Result of a single iteration."""

    iteration: int
    html_content: str
    feedback: VisualFeedback
    quality_score: float
    improvements: list[str]
    regressions: list[str]
    should_continue: bool


@dataclass
class RefinementConfig:
    """Configuration for iterative refinement."""

    max_iterations: int = 5
    quality_threshold: float = 0.8
    min_improvement: float = 0.05  # Minimum improvement to continue
    screenshot_dir: str | None = None
    enable_accessibility_check: bool = True
    enable_layout_analysis: bool = True


class IterativeRefinement:
    """Manages iterative UI refinement loop."""

    def __init__(
        self,
        hardware_profile: HardwareProfile | None = None,
        config: RefinementConfig | None = None,
    ):
        """
        Initialize iterative refinement.

        Args:
            hardware_profile: Hardware profile for optimization
            config: Refinement configuration
        """
        self.hardware_profile = hardware_profile or HardwareProfiler().detect_profile()
        self.config = config or RefinementConfig()

        self.feedback_collector = VisualFeedbackCollector(
            hardware_profile=self.hardware_profile
        )
        self.visual_analyzer = VisualAnalyzer(hardware_profile=self.hardware_profile)
        self.ui_comparator = UIComparator()
        self.pattern_learner = VisualPatternLearner()

        self.browser_controller: BrowserController | None = None
        self.iteration_history: list[IterationResult] = []

    def start_browser(self) -> bool:
        """Start browser controller."""
        if self.browser_controller is None:
            self.browser_controller = BrowserController(
                hardware_profile=self.hardware_profile,
                browser_type=BrowserType.CHROMIUM,
                headless=True,
            )
        return self.browser_controller.start()

    def stop_browser(self):
        """Stop browser controller."""
        if self.browser_controller:
            self.browser_controller.stop()
            self.browser_controller = None

    def _load_and_capture_iteration(
        self, current_html: str, iteration: int
    ) -> tuple[bool, str | None]:
        """Load HTML in browser and capture screenshot."""
        browser_controller = self.browser_controller
        if not browser_controller:
            return False, None

        # Load HTML in browser
        if not browser_controller.load_html(current_html):
            logger.error(f"Failed to load HTML in iteration {iteration}")
            return False, None

        # Capture screenshot
        screenshot_path = None
        if self.config.screenshot_dir:
            screenshot_path = str(
                Path(self.config.screenshot_dir) / f"iteration_{iteration}.png"
            )
            browser_controller.capture_screenshot(screenshot_path)

        return True, screenshot_path

    def _analyze_ui_quality(
        self, current_html: str, visual_elements: list[VisualElement], requirements: dict[str, Any]
    ) -> tuple[Any, Any, float]:
        """Analyze layout, accessibility, and calculate quality score."""
        # Analyze layout
        layout_metrics = None
        if self.config.enable_layout_analysis:
            layout_metrics = self.visual_analyzer.analyze_layout(
                visual_elements, design_spec=requirements.get("design_spec")
            )

        # Analyze accessibility
        accessibility_metrics = None
        if self.config.enable_accessibility_check:
            accessibility_metrics = self.visual_analyzer.analyze_accessibility(
                visual_elements, html_content=current_html
            )

        # Calculate quality score
        quality_score = 0.0
        if layout_metrics and accessibility_metrics:
            quality_score = self.visual_analyzer.calculate_quality_score(
                layout_metrics, accessibility_metrics
            )
        elif layout_metrics:
            # Simplified score if only layout available
            quality_score = (
                layout_metrics.spacing_consistency * 0.2
                + layout_metrics.alignment_score * 0.2
                + layout_metrics.visual_hierarchy * 0.2
                + layout_metrics.whitespace_balance * 0.2
                + layout_metrics.grid_consistency * 0.2
            )

        return layout_metrics, accessibility_metrics, quality_score

    def _generate_ui_suggestions(
        self, layout_metrics: Any, accessibility_metrics: Any
    ) -> list[str]:
        """Generate suggestions based on layout and accessibility metrics."""
        suggestions = []
        if layout_metrics:
            if layout_metrics.spacing_consistency < 0.7:
                suggestions.append("Improve spacing consistency")
            if layout_metrics.alignment_score < 0.7:
                suggestions.append("Improve element alignment")
            if layout_metrics.visual_hierarchy < 0.7:
                suggestions.append("Enhance visual hierarchy")

        if accessibility_metrics:
            if not accessibility_metrics.aria_labels_present:
                suggestions.append("Add ARIA labels for screen readers")
            if not accessibility_metrics.focus_indicators_present:
                suggestions.append("Add focus indicators for keyboard navigation")
            if accessibility_metrics.color_contrast_score < 0.7:
                suggestions.append("Improve color contrast")

        return suggestions

    def _compare_with_previous_iteration(
        self, iteration: int, feedback: VisualFeedback
    ) -> tuple[list[str], list[str]]:
        """Compare current iteration with previous iteration."""
        improvements = []
        regressions = []
        if iteration > 1:
            previous_feedback = self.feedback_collector.get_feedback_history(limit=1)[0]
            comparison = self.ui_comparator.compare_iterations(previous_feedback, feedback)
            improvements = comparison["improvements"]
            regressions = comparison["regressions"]
        return improvements, regressions

    def _create_iteration_result(
        self,
        iteration: int,
        current_html: str,
        feedback: VisualFeedback,
        quality_score: float,
        improvements: list[str],
        regressions: list[str],
    ) -> IterationResult:
        """Create iteration result."""
        return IterationResult(
            iteration=iteration,
            html_content=current_html,
            feedback=feedback,
            quality_score=quality_score,
            improvements=improvements,
            regressions=regressions,
            should_continue=self._should_continue_iteration(
                quality_score, improvements, iteration
            ),
        )

    async def _refine_html_if_needed(
        self,
        current_html: str,
        feedback: VisualFeedback,
        suggestions: list[str],
        requirements: dict[str, Any],
        refinement_callback: (
            Callable[[str, VisualFeedback, list[str], dict[str, Any]], Awaitable[str]]
            | None
        ),
    ) -> tuple[str, bool]:
        """Refine HTML using callback if provided."""
        if not refinement_callback:
            return current_html, False

        try:
            refined_html = await refinement_callback(
                current_html, feedback, suggestions, requirements
            )
            if refined_html and refined_html != current_html:
                return refined_html, True
            else:
                logger.warning("Refinement callback did not produce new HTML")
                return current_html, False
        except Exception as e:
            logger.error(f"Refinement callback failed: {e}")
            return current_html, False

    async def refine_ui(
        self,
        initial_html: str,
        requirements: dict[str, Any],
        refinement_callback: (
            Callable[[str, VisualFeedback, list[str], dict[str, Any]], Awaitable[str]]
            | None
        ) = None,
    ) -> IterationResult | None:
        """
        Refine UI through iterative feedback loop.

        Args:
            initial_html: Initial HTML content
            requirements: Design requirements
            refinement_callback: Optional callback to generate refined HTML

        Returns:
            Final iteration result
        """
        if not self.browser_controller:
            if not self.start_browser():
                logger.error("Failed to start browser")
                return None
        # start_browser() initializes browser_controller on success
        if self.browser_controller is None:
            logger.error("Browser controller is not available after start")
            return None

        current_html = initial_html
        iteration = 0

        while iteration < self.config.max_iterations:
            iteration += 1
            logger.info(f"Starting iteration {iteration}")

            # Load HTML and capture screenshot
            success, screenshot_path = self._load_and_capture_iteration(
                current_html, iteration
            )
            if not success:
                break

            # Extract visual elements
            visual_elements = self._extract_visual_elements(current_html)

            # Analyze UI quality
            layout_metrics, accessibility_metrics, quality_score = (
                self._analyze_ui_quality(current_html, visual_elements, requirements)
            )

            # Collect feedback
            feedback = self.feedback_collector.collect_feedback(
                iteration=iteration,
                screenshot_path=screenshot_path,
                visual_elements=visual_elements,
                metadata={"html_length": len(current_html)},
            )
            feedback.layout_metrics = layout_metrics
            feedback.accessibility_metrics = accessibility_metrics
            feedback.quality_score = quality_score

            # Generate suggestions
            suggestions = self._generate_ui_suggestions(
                layout_metrics, accessibility_metrics
            )
            feedback.suggestions = suggestions
            feedback.issues = (layout_metrics.issues if layout_metrics else []) + (
                accessibility_metrics.issues if accessibility_metrics else []
            )

            # Compare with previous iteration
            improvements, regressions = self._compare_with_previous_iteration(
                iteration, feedback
            )

            # Learn from feedback
            self.pattern_learner.learn_from_feedback(feedback)

            # Create iteration result
            result = self._create_iteration_result(
                iteration,
                current_html,
                feedback,
                quality_score,
                improvements,
                regressions,
            )

            self.iteration_history.append(result)

            logger.info(f"Iteration {iteration} complete. Quality: {quality_score:.2f}")

            # Check if we should continue
            if not result.should_continue:
                logger.info(
                    "Stopping refinement. Quality threshold met or max iterations reached."
                )
                break

            # Generate refined HTML if callback provided
            refined_html, should_continue = await self._refine_html_if_needed(
                current_html, feedback, suggestions, requirements, refinement_callback
            )
            if not should_continue:
                break
            current_html = refined_html

        return self.iteration_history[-1] if self.iteration_history else None

    def _should_continue_iteration(
        self, quality_score: float, improvements: list[str], iteration: int
    ) -> bool:
        """
        Determine if refinement should continue.

        Args:
            quality_score: Current quality score
            improvements: List of improvements from comparison
            iteration: Current iteration number

        Returns:
            True if should continue, False otherwise
        """
        # Stop if max iterations reached
        if iteration >= self.config.max_iterations:
            return False

        # Stop if quality threshold met
        if quality_score >= self.config.quality_threshold:
            return False

        # Stop if no improvements and quality is not improving
        if iteration > 1 and len(improvements) == 0:
            # Check if quality is improving
            if len(self.iteration_history) >= 2:
                prev_score = self.iteration_history[-2].quality_score
                if quality_score - prev_score < self.config.min_improvement:
                    return False

        return True

    def _extract_visual_elements(self, html_content: str) -> list[VisualElement]:
        """
        Extract visual elements from HTML (simplified).

        In a real implementation, this would parse the DOM and extract
        actual element positions, sizes, and styles.

        Args:
            html_content: HTML content

        Returns:
            List of visual elements
        """
        # Simplified extraction - would use actual DOM parsing
        elements = []

        # Count common elements
        button_count = html_content.count("<button") + html_content.count("<Button")
        input_count = html_content.count("<input") + html_content.count("<Input")
        text_count = (
            html_content.count("<p")
            + html_content.count("<h1")
            + html_content.count("<h2")
        )

        # Create placeholder elements
        y_pos = 20.0
        for i in range(min(button_count, 5)):
            elements.append(
                VisualElement(
                    element_type=VisualElementType.BUTTON,
                    position=(10.0, y_pos),
                    size=(100.0, 40.0),
                    text=f"Button {i+1}",
                )
            )
            y_pos += 60.0

        for _i in range(min(input_count, 5)):
            elements.append(
                VisualElement(
                    element_type=VisualElementType.INPUT,
                    position=(10.0, y_pos),
                    size=(200.0, 40.0),
                )
            )
            y_pos += 60.0

        for i in range(min(text_count, 5)):
            elements.append(
                VisualElement(
                    element_type=VisualElementType.TEXT,
                    position=(10.0, y_pos),
                    size=(300.0, 30.0),
                    text=f"Text {i+1}",
                )
            )
            y_pos += 50.0

        return elements

    def get_refinement_summary(self) -> dict[str, Any]:
        """
        Get summary of refinement process.

        Returns:
            Refinement summary
        """
        if not self.iteration_history:
            return {
                "iterations": 0,
                "final_quality": 0.0,
                "improvement_trend": "no_data",
            }

        final_result = self.iteration_history[-1]
        initial_quality = (
            self.iteration_history[0].quality_score
            if len(self.iteration_history) > 1
            else final_result.quality_score
        )

        trend = self.ui_comparator.get_improvement_trend(
            [r.feedback for r in self.iteration_history]
        )

        return {
            "iterations": len(self.iteration_history),
            "initial_quality": initial_quality,
            "final_quality": final_result.quality_score,
            "quality_improvement": final_result.quality_score - initial_quality,
            "improvement_trend": trend["trend"],
            "average_improvement": trend.get("average_improvement", 0.0),
            "recommendations": self.pattern_learner.get_recommendations(),
        }


class VisualDesignerAgent(DesignerAgent):
    """Enhanced designer agent with visual feedback capabilities."""

    def __init__(self, *args, **kwargs):
        """Initialize visual designer agent."""
        super().__init__(*args, **kwargs)

        self.hardware_profile = HardwareProfiler().detect_profile()
        self.iterative_refinement = IterativeRefinement(
            hardware_profile=self.hardware_profile
        )

    def get_commands(self) -> list[dict[str, str]]:
        """Return available commands including visual design."""
        base_commands = super().get_commands()
        return base_commands + [
            {
                "command": "*visual-design",
                "description": "Design UI with visual feedback and iterative refinement",
            }
        ]

    async def run(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute command including visual design."""
        command = command.lstrip("*")

        if command == "visual-design":
            feature_description = kwargs.get("feature_description", "")
            user_stories = kwargs.get("user_stories", [])
            max_iterations = kwargs.get("max_iterations", 5)
            quality_threshold = kwargs.get("quality_threshold", 0.8)
            output_file = kwargs.get("output_file")

            return await self._visual_design(
                feature_description,
                user_stories,
                max_iterations,
                quality_threshold,
                output_file,
            )

        # Delegate to parent for other commands
        return await super().run(f"*{command}", **kwargs)

    async def _visual_design(
        self,
        feature_description: str,
        user_stories: list[str],
        max_iterations: int,
        quality_threshold: float,
        output_file: str | None,
    ) -> dict[str, Any]:
        """
        Design UI with visual feedback and iterative refinement.

        Args:
            feature_description: Feature description
            user_stories: User stories
            max_iterations: Maximum refinement iterations
            quality_threshold: Quality threshold to stop refinement
            output_file: Optional output file path

        Returns:
            Design result with visual feedback
        """
        if not feature_description:
            return {"error": "feature_description is required"}

        # Configure refinement
        self.iterative_refinement.config.max_iterations = max_iterations
        self.iterative_refinement.config.quality_threshold = quality_threshold

        # Generate initial UI design using parent's design-ui command
        initial_design = await self._design_ui(
            feature_description, user_stories, output_file=None
        )

        if "error" in initial_design:
            return initial_design

        # Extract HTML from design (simplified - would parse actual design output)
        initial_html = self._extract_html_from_design(initial_design)

        # Define refinement callback
        async def refine_callback(html, feedback, suggestions, requirements):
            """Callback to refine HTML based on feedback."""
            # In real implementation, would use LLM to refine HTML
            # For now, return original HTML (would be enhanced with feedback)
            logger.info(f"Refining HTML based on {len(suggestions)} suggestions")
            return html  # Placeholder

        # Run iterative refinement
        requirements = {
            "feature_description": feature_description,
            "user_stories": user_stories,
            "design_spec": initial_design.get("design_spec"),
        }

        try:
            result = await self.iterative_refinement.refine_ui(
                initial_html, requirements, refinement_callback=refine_callback
            )

            if not result:
                return {"error": "Refinement failed"}

            # Get refinement summary
            summary = self.iterative_refinement.get_refinement_summary()

            # Save final HTML if output file specified
            if output_file:
                Path(output_file).write_text(result.html_content, encoding="utf-8")

            return {
                "type": "visual_design",
                "iterations": summary["iterations"],
                "initial_quality": summary["initial_quality"],
                "final_quality": summary["final_quality"],
                "quality_improvement": summary["quality_improvement"],
                "improvement_trend": summary["improvement_trend"],
                "recommendations": summary["recommendations"],
                "html_content": result.html_content,
                "output_file": output_file,
            }
        finally:
            # Clean up browser
            self.iterative_refinement.stop_browser()

    def _extract_html_from_design(self, design: dict[str, Any]) -> str:
        """
        Extract HTML from design output (simplified).

        Args:
            design: Design output dictionary

        Returns:
            HTML content
        """
        # In real implementation, would parse design output to extract HTML
        # For now, return a simple placeholder HTML
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Generated UI</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                button { padding: 10px 20px; margin: 10px; }
                input { padding: 8px; margin: 10px; width: 200px; }
            </style>
        </head>
        <body>
            <h1>Generated UI</h1>
            <button>Click Me</button>
            <input type="text" placeholder="Enter text">
            <p>This is a generated UI based on the design specifications.</p>
        </body>
        </html>
        """
