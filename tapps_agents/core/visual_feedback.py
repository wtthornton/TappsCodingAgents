"""
Visual Feedback System for UI/UX Iterative Refinement

Provides visual analysis, comparison, and pattern learning for UI generation.
"""

import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .hardware_profiler import HardwareProfile, HardwareProfiler

logger = logging.getLogger(__name__)


class RenderingMode(Enum):
    """Rendering mode based on hardware capabilities."""

    LIGHTWEIGHT = "lightweight"  # Minimal analysis for NUC
    STANDARD = "standard"  # Balanced analysis for development machines
    FULL = "full"  # Full analysis for workstations


class VisualElementType(Enum):
    """Types of visual elements."""

    BUTTON = "button"
    TEXT = "text"
    IMAGE = "image"
    INPUT = "input"
    CONTAINER = "container"
    NAVIGATION = "navigation"
    HEADER = "header"
    FOOTER = "footer"
    SIDEBAR = "sidebar"
    MODAL = "modal"
    CARD = "card"
    LIST = "list"
    GRID = "grid"


@dataclass
class VisualElement:
    """Represents a visual element in the UI."""

    element_type: VisualElementType
    position: tuple[float, float]  # (x, y)
    size: tuple[float, float]  # (width, height)
    text: str | None = None
    color: str | None = None
    background_color: str | None = None
    font_size: float | None = None
    z_index: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LayoutMetrics:
    """Layout analysis metrics."""

    spacing_consistency: float  # 0.0 to 1.0
    alignment_score: float  # 0.0 to 1.0
    visual_hierarchy: float  # 0.0 to 1.0
    whitespace_balance: float  # 0.0 to 1.0
    grid_consistency: float  # 0.0 to 1.0
    issues: list[str] = field(default_factory=list)


@dataclass
class AccessibilityMetrics:
    """Accessibility analysis metrics."""

    color_contrast_score: float  # 0.0 to 1.0
    keyboard_navigable: bool
    screen_reader_compatible: bool
    aria_labels_present: bool
    focus_indicators_present: bool
    issues: list[str] = field(default_factory=list)


@dataclass
class VisualFeedback:
    """Visual feedback data structure."""

    timestamp: datetime
    iteration: int
    screenshot_path: str | None = None
    layout_metrics: LayoutMetrics | None = None
    accessibility_metrics: AccessibilityMetrics | None = None
    visual_elements: list[VisualElement] = field(default_factory=list)
    user_interactions: list[dict[str, Any]] = field(default_factory=list)
    quality_score: float = 0.0  # 0.0 to 1.0
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["visual_elements"] = [
            {**asdict(elem), "element_type": elem.element_type.value}
            for elem in self.visual_elements
        ]
        return data


class VisualFeedbackCollector:
    """Collects visual feedback from generated UIs."""

    def __init__(self, hardware_profile: HardwareProfile | None = None):
        """
        Initialize visual feedback collector.

        Args:
            hardware_profile: Hardware profile for optimization
        """
        self.hardware_profile = hardware_profile or HardwareProfiler().detect_profile()
        self.rendering_mode = self._get_rendering_mode()
        self.feedback_history: list[VisualFeedback] = []

    def _get_rendering_mode(self) -> RenderingMode:
        """Rendering mode. Workstation-like default (hardware taxonomy removed)."""
        return RenderingMode.FULL

    def collect_feedback(
        self,
        iteration: int,
        screenshot_path: str | None = None,
        visual_elements: list[VisualElement] | None = None,
        user_interactions: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> VisualFeedback:
        """
        Collect visual feedback for an iteration.

        Args:
            iteration: Iteration number
            screenshot_path: Path to screenshot
            visual_elements: List of visual elements
            user_interactions: List of user interactions
            metadata: Additional metadata

        Returns:
            VisualFeedback object
        """
        feedback = VisualFeedback(
            timestamp=datetime.now(UTC),
            iteration=iteration,
            screenshot_path=screenshot_path,
            visual_elements=visual_elements or [],
            user_interactions=user_interactions or [],
            metadata=metadata or {},
        )

        self.feedback_history.append(feedback)
        return feedback

    def get_feedback_history(self, limit: int | None = None) -> list[VisualFeedback]:
        """
        Get feedback history.

        Args:
            limit: Maximum number of feedback items to return

        Returns:
            List of VisualFeedback objects
        """
        if limit:
            return self.feedback_history[-limit:]
        return self.feedback_history.copy()

    def clear_history(self):
        """Clear feedback history."""
        self.feedback_history.clear()


class VisualAnalyzer:
    """Analyzes visual elements and layout."""

    def __init__(self, hardware_profile: HardwareProfile | None = None):
        """
        Initialize visual analyzer.

        Args:
            hardware_profile: Hardware profile for optimization
        """
        self.hardware_profile = hardware_profile or HardwareProfiler().detect_profile()
        self.rendering_mode = self._get_rendering_mode()

    def _get_rendering_mode(self) -> RenderingMode:
        """Rendering mode. Workstation-like default (hardware taxonomy removed)."""
        return RenderingMode.FULL

    def analyze_layout(
        self,
        visual_elements: list[VisualElement],
        design_spec: dict[str, Any] | None = None,
    ) -> LayoutMetrics:
        """
        Analyze layout quality.

        Args:
            visual_elements: List of visual elements
            design_spec: Optional design specification

        Returns:
            LayoutMetrics object
        """
        if not visual_elements:
            return LayoutMetrics(
                spacing_consistency=0.0,
                alignment_score=0.0,
                visual_hierarchy=0.0,
                whitespace_balance=0.0,
                grid_consistency=0.0,
                issues=["No visual elements found"],
            )

        # Lightweight mode: Basic analysis only
        if self.rendering_mode == RenderingMode.LIGHTWEIGHT:
            return self._analyze_layout_lightweight(visual_elements)

        # Standard/Full mode: Detailed analysis
        return self._analyze_layout_detailed(visual_elements, design_spec)

    def _analyze_layout_lightweight(
        self, elements: list[VisualElement]
    ) -> LayoutMetrics:
        """Lightweight layout analysis for NUC devices."""
        if len(elements) < 2:
            return LayoutMetrics(
                spacing_consistency=0.5,
                alignment_score=0.5,
                visual_hierarchy=0.5,
                whitespace_balance=0.5,
                grid_consistency=0.5,
                issues=["Insufficient elements for analysis"],
            )

        # Basic spacing check
        spacing_scores = []
        for i in range(len(elements) - 1):
            elem1 = elements[i]
            elem2 = elements[i + 1]
            distance = abs(elem1.position[1] - elem2.position[1])
            spacing_scores.append(1.0 if distance > 0 else 0.0)

        spacing_consistency = (
            sum(spacing_scores) / len(spacing_scores) if spacing_scores else 0.5
        )

        return LayoutMetrics(
            spacing_consistency=spacing_consistency,
            alignment_score=0.7,  # Simplified
            visual_hierarchy=0.6,  # Simplified
            whitespace_balance=0.6,  # Simplified
            grid_consistency=0.7,  # Simplified
            issues=[],
        )

    def _analyze_layout_detailed(
        self, elements: list[VisualElement], design_spec: dict[str, Any] | None
    ) -> LayoutMetrics:
        """Detailed layout analysis for workstations."""
        issues = []

        # Spacing consistency
        spacing_scores = []
        for i in range(len(elements) - 1):
            elem1 = elements[i]
            elem2 = elements[i + 1]
            if abs(elem1.position[0] - elem2.position[0]) < 10:  # Same column
                distance = abs(elem1.position[1] + elem1.size[1] - elem2.position[1])
                if distance < 5:
                    spacing_scores.append(0.0)
                    issues.append(f"Elements {i} and {i+1} are too close")
                elif distance > 100:
                    spacing_scores.append(0.5)
                    issues.append(f"Elements {i} and {i+1} have excessive spacing")
                else:
                    spacing_scores.append(1.0)

        spacing_consistency = (
            sum(spacing_scores) / len(spacing_scores) if spacing_scores else 0.7
        )

        # Alignment score
        x_positions = [elem.position[0] for elem in elements]
        y_positions = [elem.position[1] for elem in elements]

        x_alignment = (
            1.0 - (max(x_positions) - min(x_positions)) / 1000.0 if x_positions else 0.5
        )
        y_alignment = (
            1.0 - (max(y_positions) - min(y_positions)) / 1000.0 if y_positions else 0.5
        )
        alignment_score = (x_alignment + y_alignment) / 2.0

        # Visual hierarchy (based on size and z-index)
        sizes = [elem.size[0] * elem.size[1] for elem in elements]
        if sizes:
            max_size = max(sizes)
            hierarchy_scores = [size / max_size for size in sizes]
            visual_hierarchy = sum(hierarchy_scores) / len(hierarchy_scores)
        else:
            visual_hierarchy = 0.5

        # Whitespace balance (simplified)
        total_area = sum(elem.size[0] * elem.size[1] for elem in elements)
        whitespace_balance = min(1.0, total_area / 100000.0)  # Simplified calculation

        # Grid consistency
        grid_scores = []
        for i in range(len(elements) - 1):
            for j in range(i + 1, len(elements)):
                elem1 = elements[i]
                elem2 = elements[j]
                # Check if aligned on grid
                x_diff = abs(elem1.position[0] - elem2.position[0])
                y_diff = abs(elem1.position[1] - elem2.position[1])
                if x_diff < 10 or y_diff < 10:
                    grid_scores.append(1.0)
                else:
                    grid_scores.append(0.5)

        grid_consistency = sum(grid_scores) / len(grid_scores) if grid_scores else 0.7

        return LayoutMetrics(
            spacing_consistency=max(0.0, min(1.0, spacing_consistency)),
            alignment_score=max(0.0, min(1.0, alignment_score)),
            visual_hierarchy=max(0.0, min(1.0, visual_hierarchy)),
            whitespace_balance=max(0.0, min(1.0, whitespace_balance)),
            grid_consistency=max(0.0, min(1.0, grid_consistency)),
            issues=issues[:10],  # Limit issues
        )

    def analyze_accessibility(
        self, visual_elements: list[VisualElement], html_content: str | None = None
    ) -> AccessibilityMetrics:
        """
        Analyze accessibility features.

        Args:
            visual_elements: List of visual elements
            html_content: Optional HTML content for deeper analysis

        Returns:
            AccessibilityMetrics object
        """
        issues = []

        # Lightweight mode: Basic checks only
        if self.rendering_mode == RenderingMode.LIGHTWEIGHT:
            return AccessibilityMetrics(
                color_contrast_score=0.7,  # Simplified
                keyboard_navigable=True,  # Assume yes
                screen_reader_compatible=True,  # Assume yes
                aria_labels_present=False,  # Unknown
                focus_indicators_present=False,  # Unknown
                issues=["Lightweight mode: Limited accessibility analysis"],
            )

        # Standard/Full mode: Detailed analysis
        color_contrast_score = 0.8  # Simplified - would use actual contrast calculation
        keyboard_navigable = True
        screen_reader_compatible = True

        # Check for ARIA labels in HTML
        aria_labels_present = False
        if html_content:
            aria_labels_present = (
                "aria-label" in html_content or "aria-labelledby" in html_content
            )

        # Check for focus indicators
        focus_indicators_present = False
        if html_content:
            focus_indicators_present = (
                ":focus" in html_content or "focus-visible" in html_content
            )

        if not aria_labels_present:
            issues.append("Missing ARIA labels for screen readers")
        if not focus_indicators_present:
            issues.append("Missing focus indicators for keyboard navigation")

        return AccessibilityMetrics(
            color_contrast_score=max(0.0, min(1.0, color_contrast_score)),
            keyboard_navigable=keyboard_navigable,
            screen_reader_compatible=screen_reader_compatible,
            aria_labels_present=aria_labels_present,
            focus_indicators_present=focus_indicators_present,
            issues=issues,
        )

    def calculate_quality_score(
        self,
        layout_metrics: LayoutMetrics,
        accessibility_metrics: AccessibilityMetrics,
        weights: dict[str, float] | None = None,
    ) -> float:
        """
        Calculate overall quality score.

        Args:
            layout_metrics: Layout analysis metrics
            accessibility_metrics: Accessibility analysis metrics
            weights: Optional weights for different metrics

        Returns:
            Quality score from 0.0 to 1.0
        """
        if weights is None:
            weights = {"layout": 0.6, "accessibility": 0.4}

        layout_score = (
            layout_metrics.spacing_consistency * 0.2
            + layout_metrics.alignment_score * 0.2
            + layout_metrics.visual_hierarchy * 0.2
            + layout_metrics.whitespace_balance * 0.2
            + layout_metrics.grid_consistency * 0.2
        )

        accessibility_score = (
            accessibility_metrics.color_contrast_score * 0.3
            + (1.0 if accessibility_metrics.keyboard_navigable else 0.0) * 0.2
            + (1.0 if accessibility_metrics.screen_reader_compatible else 0.0) * 0.2
            + (1.0 if accessibility_metrics.aria_labels_present else 0.0) * 0.15
            + (1.0 if accessibility_metrics.focus_indicators_present else 0.0) * 0.15
        )

        quality_score = layout_score * weights.get(
            "layout", 0.6
        ) + accessibility_score * weights.get("accessibility", 0.4)

        return max(0.0, min(1.0, quality_score))


class UIComparator:
    """Compares UI iterations for improvements."""

    def __init__(self):
        """Initialize UI comparator."""
        pass

    def compare_iterations(
        self, previous: VisualFeedback, current: VisualFeedback
    ) -> dict[str, Any]:
        """
        Compare two iterations to identify improvements.

        Args:
            previous: Previous iteration feedback
            current: Current iteration feedback

        Returns:
            Comparison results
        """
        improvements = []
        regressions = []
        unchanged = []

        # Compare quality scores
        if current.quality_score > previous.quality_score:
            improvements.append(
                f"Quality score improved from {previous.quality_score:.2f} to {current.quality_score:.2f}"
            )
        elif current.quality_score < previous.quality_score:
            regressions.append(
                f"Quality score decreased from {previous.quality_score:.2f} to {current.quality_score:.2f}"
            )
        else:
            unchanged.append("Quality score unchanged")

        # Compare layout metrics
        if previous.layout_metrics and current.layout_metrics:
            prev_layout = previous.layout_metrics
            curr_layout = current.layout_metrics

            if curr_layout.spacing_consistency > prev_layout.spacing_consistency:
                improvements.append("Spacing consistency improved")
            elif curr_layout.spacing_consistency < prev_layout.spacing_consistency:
                regressions.append("Spacing consistency decreased")

            if curr_layout.alignment_score > prev_layout.alignment_score:
                improvements.append("Alignment score improved")
            elif curr_layout.alignment_score < prev_layout.alignment_score:
                regressions.append("Alignment score decreased")

            if curr_layout.visual_hierarchy > prev_layout.visual_hierarchy:
                improvements.append("Visual hierarchy improved")
            elif curr_layout.visual_hierarchy < prev_layout.visual_hierarchy:
                regressions.append("Visual hierarchy decreased")

        # Compare accessibility metrics
        if previous.accessibility_metrics and current.accessibility_metrics:
            prev_acc = previous.accessibility_metrics
            curr_acc = current.accessibility_metrics

            if curr_acc.color_contrast_score > prev_acc.color_contrast_score:
                improvements.append("Color contrast improved")
            elif curr_acc.color_contrast_score < prev_acc.color_contrast_score:
                regressions.append("Color contrast decreased")

            if curr_acc.keyboard_navigable and not prev_acc.keyboard_navigable:
                improvements.append("Keyboard navigation added")
            elif not curr_acc.keyboard_navigable and prev_acc.keyboard_navigable:
                regressions.append("Keyboard navigation removed")

        # Compare issues
        if len(current.issues) < len(previous.issues):
            improvements.append(
                f"Reduced issues from {len(previous.issues)} to {len(current.issues)}"
            )
        elif len(current.issues) > len(previous.issues):
            regressions.append(
                f"Increased issues from {len(previous.issues)} to {len(current.issues)}"
            )

        return {
            "improvements": improvements,
            "regressions": regressions,
            "unchanged": unchanged,
            "quality_delta": current.quality_score - previous.quality_score,
            "iteration_delta": current.iteration - previous.iteration,
        }

    def get_improvement_trend(
        self, feedback_history: list[VisualFeedback]
    ) -> dict[str, Any]:
        """
        Analyze improvement trend across multiple iterations.

        Args:
            feedback_history: List of feedback items

        Returns:
            Trend analysis
        """
        if len(feedback_history) < 2:
            return {
                "trend": "insufficient_data",
                "average_improvement": 0.0,
                "iterations": len(feedback_history),
            }

        quality_scores = [fb.quality_score for fb in feedback_history]
        improvements = []

        for i in range(1, len(quality_scores)):
            delta = quality_scores[i] - quality_scores[i - 1]
            improvements.append(delta)

        average_improvement = (
            sum(improvements) / len(improvements) if improvements else 0.0
        )

        if average_improvement > 0.05:
            trend = "improving"
        elif average_improvement < -0.05:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "average_improvement": average_improvement,
            "iterations": len(feedback_history),
            "quality_scores": quality_scores,
            "final_quality": quality_scores[-1] if quality_scores else 0.0,
        }


class VisualPatternLearner:
    """Learns visual patterns from feedback."""

    def __init__(self):
        """Initialize visual pattern learner."""
        self.patterns: dict[str, Any] = {}
        self.feedback_history: list[VisualFeedback] = []

    def learn_from_feedback(self, feedback: VisualFeedback):
        """
        Learn patterns from feedback.

        Args:
            feedback: Visual feedback to learn from
        """
        self.feedback_history.append(feedback)

        # Extract patterns from layout metrics
        if feedback.layout_metrics:
            layout = feedback.layout_metrics
            if layout.spacing_consistency > 0.8:
                self.patterns["high_spacing_consistency"] = (
                    self.patterns.get("high_spacing_consistency", 0) + 1
                )
            if layout.alignment_score > 0.8:
                self.patterns["high_alignment"] = (
                    self.patterns.get("high_alignment", 0) + 1
                )

        # Extract patterns from accessibility
        if feedback.accessibility_metrics:
            acc = feedback.accessibility_metrics
            if acc.color_contrast_score > 0.8:
                self.patterns["good_contrast"] = (
                    self.patterns.get("good_contrast", 0) + 1
                )
            if acc.keyboard_navigable:
                self.patterns["keyboard_navigable"] = (
                    self.patterns.get("keyboard_navigable", 0) + 1
                )

    def get_recommendations(self) -> list[str]:
        """
        Get recommendations based on learned patterns.

        Returns:
            List of recommendations
        """
        recommendations = []

        if self.patterns.get("high_spacing_consistency", 0) > 5:
            recommendations.append("Maintain consistent spacing patterns")

        if self.patterns.get("high_alignment", 0) > 5:
            recommendations.append("Continue using aligned layouts")

        if self.patterns.get("good_contrast", 0) > 5:
            recommendations.append("Maintain good color contrast")

        if self.patterns.get("keyboard_navigable", 0) < 3:
            recommendations.append("Improve keyboard navigation support")

        return recommendations

    def clear_patterns(self):
        """Clear learned patterns."""
        self.patterns.clear()
        self.feedback_history.clear()
