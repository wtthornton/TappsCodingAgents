"""
Unit tests for Visual Designer Agent (Phase 2.3).
"""

from datetime import UTC
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tapps_agents.agents.designer.visual_designer import (
    IterationResult,
    IterativeRefinement,
    RefinementConfig,
    VisualDesignerAgent,
)
from tapps_agents.core.hardware_profiler import HardwareProfile

pytestmark = pytest.mark.unit


class TestIterativeRefinement:
    """Test IterativeRefinement functionality."""

    def test_initialization(self):
        """Test refinement initialization."""
        refinement = IterativeRefinement()
        assert refinement.hardware_profile is not None
        assert refinement.config is not None
        assert refinement.feedback_collector is not None
        assert refinement.visual_analyzer is not None
        assert refinement.ui_comparator is not None
        assert refinement.pattern_learner is not None

    def test_initialization_custom_config(self):
        """Test refinement with custom config."""
        config = RefinementConfig(
            max_iterations=10, quality_threshold=0.9, min_improvement=0.1
        )
        refinement = IterativeRefinement(config=config)
        assert refinement.config.max_iterations == 10
        assert refinement.config.quality_threshold == 0.9
        assert refinement.config.min_improvement == 0.1

    def test_start_browser(self):
        """Test starting browser."""
        refinement = IterativeRefinement(hardware_profile=HardwareProfile.NUC)
        result = refinement.start_browser()
        assert result is True  # Cloud rendering always succeeds
        assert refinement.browser_controller is not None

    def test_stop_browser(self):
        """Test stopping browser."""
        refinement = IterativeRefinement(hardware_profile=HardwareProfile.NUC)
        refinement.start_browser()
        refinement.stop_browser()
        assert refinement.browser_controller is None

    @pytest.mark.asyncio
    async def test_refine_ui_single_iteration(self):
        """Test UI refinement with single iteration."""
        refinement = IterativeRefinement(
            hardware_profile=HardwareProfile.NUC,
            config=RefinementConfig(max_iterations=1),
        )

        initial_html = "<html><body><button>Click</button></body></html>"
        requirements = {"feature_description": "Test feature"}

        result = await refinement.refine_ui(initial_html, requirements)

        assert result is not None
        assert result.iteration == 1
        assert result.html_content == initial_html
        assert 0.0 <= result.quality_score <= 1.0
        assert len(refinement.iteration_history) == 1

    @pytest.mark.asyncio
    async def test_refine_ui_with_callback(self):
        """Test UI refinement with refinement callback."""
        refinement = IterativeRefinement(
            hardware_profile=HardwareProfile.NUC,
            config=RefinementConfig(max_iterations=2),
        )

        initial_html = "<html><body><button>Click</button></body></html>"
        requirements = {"feature_description": "Test feature"}

        refined_html = "<html><body><button>Click</button><p>Improved</p></body></html>"

        async def refine_callback(html, feedback, suggestions, reqs):
            return refined_html

        result = await refinement.refine_ui(
            initial_html, requirements, refinement_callback=refine_callback
        )

        assert result is not None
        assert result.iteration >= 1
        assert len(refinement.iteration_history) >= 1

    @pytest.mark.asyncio
    async def test_refine_ui_quality_threshold(self):
        """Test UI refinement stopping at quality threshold."""
        refinement = IterativeRefinement(
            hardware_profile=HardwareProfile.NUC,
            config=RefinementConfig(
                max_iterations=5, quality_threshold=0.5  # Low threshold
            ),
        )

        initial_html = "<html><body><button>Click</button></body></html>"
        requirements = {"feature_description": "Test feature"}

        result = await refinement.refine_ui(initial_html, requirements)

        assert result is not None
        # Should stop early if quality threshold is met

    def test_should_continue_iteration_max_reached(self):
        """Test should_continue when max iterations reached."""
        refinement = IterativeRefinement(config=RefinementConfig(max_iterations=3))

        should_continue = refinement._should_continue_iteration(
            quality_score=0.5, improvements=[], iteration=3
        )

        assert should_continue is False

    def test_should_continue_iteration_quality_met(self):
        """Test should_continue when quality threshold met."""
        refinement = IterativeRefinement(config=RefinementConfig(quality_threshold=0.8))

        should_continue = refinement._should_continue_iteration(
            quality_score=0.85, improvements=[], iteration=1
        )

        assert should_continue is False

    def test_should_continue_iteration_improving(self):
        """Test should_continue when quality is improving."""
        refinement = IterativeRefinement(
            config=RefinementConfig(max_iterations=5, quality_threshold=0.9)
        )

        # Add some iteration history
        refinement.iteration_history.append(
            IterationResult(
                iteration=1,
                html_content="<html></html>",
                feedback=Mock(quality_score=0.5),
                quality_score=0.5,
                improvements=[],
                regressions=[],
                should_continue=True,
            )
        )

        should_continue = refinement._should_continue_iteration(
            quality_score=0.6, improvements=["Improved spacing"], iteration=2
        )

        assert should_continue is True

    def test_extract_visual_elements(self):
        """Test extracting visual elements from HTML."""
        refinement = IterativeRefinement()

        html = """
        <html>
        <body>
            <button>Button 1</button>
            <button>Button 2</button>
            <input type="text">
            <p>Text content</p>
        </body>
        </html>
        """

        elements = refinement._extract_visual_elements(html)

        assert len(elements) > 0
        assert any(elem.element_type.value == "button" for elem in elements)

    def test_get_refinement_summary_no_iterations(self):
        """Test getting summary with no iterations."""
        refinement = IterativeRefinement()
        summary = refinement.get_refinement_summary()

        assert summary["iterations"] == 0
        assert summary["final_quality"] == 0.0
        assert summary["improvement_trend"] == "no_data"

    def test_get_refinement_summary_with_iterations(self):
        """Test getting summary with iterations."""
        refinement = IterativeRefinement()

        # Add mock iteration results
        from datetime import datetime

        from tapps_agents.core.visual_feedback import VisualFeedback

        for i in range(3):
            feedback = VisualFeedback(
                timestamp=datetime.now(UTC),
                iteration=i + 1,
                quality_score=0.5 + (i * 0.1),
            )
            result = IterationResult(
                iteration=i + 1,
                html_content=f"<html>Iteration {i+1}</html>",
                feedback=feedback,
                quality_score=0.5 + (i * 0.1),
                improvements=[],
                regressions=[],
                should_continue=True,
            )
            refinement.iteration_history.append(result)

        summary = refinement.get_refinement_summary()

        assert summary["iterations"] == 3
        assert summary["final_quality"] == 0.7
        assert summary["initial_quality"] == 0.5
        assert (
            abs(summary["quality_improvement"] - 0.2) < 0.01
        )  # Floating point comparison


class TestVisualDesignerAgent:
    """Test VisualDesignerAgent functionality."""

    @pytest.fixture
    def agent(self):
        """Create a visual designer agent instance."""
        with patch(
            "tapps_agents.agents.designer.visual_designer.DesignerAgent.__init__"
        ):
            agent = VisualDesignerAgent()
            agent.mal = Mock()
            agent.config = Mock()
            agent.expert_registry = None
            return agent

    def test_initialization(self, agent):
        """Test agent initialization."""
        assert agent.hardware_profile is not None
        assert agent.iterative_refinement is not None

    def test_get_commands(self, agent):
        """Test getting commands including visual-design."""
        commands = agent.get_commands()
        command_dict = {cmd["command"]: cmd["description"] for cmd in commands}
        assert "*visual-design" in command_dict

    @pytest.mark.asyncio
    async def test_visual_design_missing_description(self, agent):
        """Test visual design with missing description."""
        result = await agent._visual_design(
            feature_description="",
            user_stories=[],
            max_iterations=5,
            quality_threshold=0.8,
            output_file=None,
        )

        assert "error" in result

    @pytest.mark.asyncio
    async def test_visual_design_success(self, agent):
        """Test successful visual design."""
        # Mock parent's _design_ui method
        agent._design_ui = AsyncMock(
            return_value={
                "type": "ui_design",
                "design_spec": {"components": ["button", "input"]},
            }
        )

        # Mock browser controller
        mock_browser = Mock()
        mock_browser.load_html = Mock(return_value=True)
        mock_browser.capture_screenshot = Mock(return_value=True)
        agent.iterative_refinement.browser_controller = mock_browser

        result = await agent._visual_design(
            feature_description="Test feature",
            user_stories=["As a user", "I want to test"],
            max_iterations=2,
            quality_threshold=0.8,
            output_file=None,
        )

        assert "type" in result
        assert result["type"] == "visual_design"
        assert "iterations" in result
        assert "final_quality" in result

    def test_extract_html_from_design(self, agent):
        """Test extracting HTML from design."""
        design = {"type": "ui_design", "components": ["button", "input"]}

        html = agent._extract_html_from_design(design)

        assert "<html>" in html
        assert "<body>" in html
