"""
Tests for workflow recommend command.

Tests the interactive CLI command for workflow recommendation.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.cli.commands.top_level import (
    _estimate_time,
    _is_ambiguous,
    handle_workflow_recommend_command,
)
from tapps_agents.workflow.detector import ProjectCharacteristics, ProjectType, WorkflowTrack
from tapps_agents.workflow.recommender import WorkflowRecommendation


@pytest.fixture
def mock_recommendation():
    """Create a mock workflow recommendation."""
    return WorkflowRecommendation(
        workflow_file="brownfield-fullstack",
        workflow=None,
        track=WorkflowTrack.BMAD_METHOD,
        confidence=0.85,
        characteristics=ProjectCharacteristics(
            project_type=ProjectType.BROWNFIELD,
            workflow_track=WorkflowTrack.BMAD_METHOD,
            confidence=0.85,
            indicators={},
            recommendations=["Use BMad Method workflow"],
        ),
        alternative_workflows=["quick-fix", "enterprise-fullstack"],
        message="📋 **BMad Method** workflow recommended\nConfidence: 85%\nProject Type: brownfield",
    )


@pytest.fixture
def mock_low_confidence_recommendation():
    """Create a mock recommendation with low confidence."""
    return WorkflowRecommendation(
        workflow_file="brownfield-fullstack",
        workflow=None,
        track=WorkflowTrack.BMAD_METHOD,
        confidence=0.5,
        characteristics=ProjectCharacteristics(
            project_type=ProjectType.UNKNOWN,
            workflow_track=WorkflowTrack.BMAD_METHOD,
            confidence=0.5,
            indicators={},
            recommendations=[],
        ),
        alternative_workflows=["quick-fix", "enterprise-fullstack", "greenfield-api", "rapid-dev"],
        message="📋 **BMad Method** workflow recommended\nConfidence: 50%",
    )


@pytest.mark.unit
class TestWorkflowRecommendCommand:
    """Tests for workflow recommend command."""

    def test_is_ambiguous_low_confidence(self, mock_low_confidence_recommendation):
        """Test ambiguity detection for low confidence."""
        assert _is_ambiguous(mock_low_confidence_recommendation) is True

    def test_is_ambiguous_high_confidence(self, mock_recommendation):
        """Test ambiguity detection for high confidence."""
        assert _is_ambiguous(mock_recommendation) is False

    def test_is_ambiguous_many_alternatives(self):
        """Test ambiguity detection for many alternatives."""
        rec = WorkflowRecommendation(
            workflow_file="test",
            workflow=None,
            track=WorkflowTrack.BMAD_METHOD,
            confidence=0.8,
            characteristics=ProjectCharacteristics(
                project_type=ProjectType.BROWNFIELD,
                workflow_track=WorkflowTrack.BMAD_METHOD,
                confidence=0.8,
                indicators={},
                recommendations=[],
            ),
            alternative_workflows=["alt1", "alt2", "alt3", "alt4", "alt5"],
            message="Test",
        )
        assert _is_ambiguous(rec) is True

    def test_estimate_time_quick_flow(self):
        """Test time estimation for quick flow."""
        estimate = _estimate_time("quick-fix", WorkflowTrack.QUICK_FLOW)
        assert "5-15" in estimate or "minutes" in estimate

    def test_estimate_time_bmad_method(self):
        """Test time estimation for BMad method."""
        estimate = _estimate_time("brownfield-fullstack", WorkflowTrack.BMAD_METHOD)
        assert "15-30" in estimate or "minutes" in estimate

    def test_estimate_time_enterprise(self):
        """Test time estimation for enterprise."""
        estimate = _estimate_time("enterprise-fullstack", WorkflowTrack.ENTERPRISE)
        assert "30-60" in estimate or "minutes" in estimate

    def test_estimate_time_unknown(self):
        """Test time estimation for unknown workflow."""
        estimate = _estimate_time(None, WorkflowTrack.BMAD_METHOD)
        assert estimate == "Unknown" or "15-30" in estimate

    @patch("tapps_agents.workflow.recommender.WorkflowRecommender")
    @patch("sys.stdout")
    def test_recommend_command_json_output(self, mock_stdout, mock_recommender_class, mock_recommendation):
        """Test recommend command with JSON output."""
        mock_recommender = MagicMock()
        mock_recommender.recommend.return_value = mock_recommendation
        mock_recommender_class.return_value = mock_recommender

        args = MagicMock()
        args.non_interactive = True
        args.format = "json"
        args.auto_load = False

        handle_workflow_recommend_command(args)

        # Verify recommender was called
        mock_recommender.recommend.assert_called_once_with(auto_load=False)

    @patch("tapps_agents.workflow.recommender.WorkflowRecommender")
    @patch("sys.stdout")
    def test_recommend_command_text_output(self, mock_stdout, mock_recommender_class, mock_recommendation):
        """Test recommend command with text output."""
        mock_recommender = MagicMock()
        mock_recommender.recommend.return_value = mock_recommendation
        mock_recommender_class.return_value = mock_recommender

        args = MagicMock()
        args.non_interactive = True
        args.format = "text"
        args.auto_load = False

        handle_workflow_recommend_command(args)

        # Verify recommender was called
        mock_recommender.recommend.assert_called_once_with(auto_load=False)

    @patch("tapps_agents.workflow.recommender.WorkflowRecommender")
    @patch("builtins.input")
    def test_recommend_command_interactive_qa(self, mock_input, mock_recommender_class, mock_low_confidence_recommendation):
        """Test recommend command with interactive Q&A for ambiguous cases."""
        mock_recommender = MagicMock()
        mock_recommender.recommend.return_value = mock_low_confidence_recommendation
        mock_recommender_class.return_value = mock_recommender

        # Simulate user answering Q&A questions
        mock_input.side_effect = ["2", "2", "2", "n"]  # scope=2, time=2, docs=2, no confirmation

        args = MagicMock()
        args.non_interactive = False
        args.format = "text"
        args.auto_load = False

        handle_workflow_recommend_command(args)

        # Verify Q&A was triggered (input called multiple times)
        assert mock_input.call_count >= 3

    @patch("tapps_agents.workflow.recommender.WorkflowRecommender")
    def test_recommend_command_error_handling(self, mock_recommender_class):
        """Test error handling in recommend command."""
        mock_recommender = MagicMock()
        mock_recommender.recommend.side_effect = Exception("Test error")
        mock_recommender_class.return_value = mock_recommender

        args = MagicMock()
        args.non_interactive = True
        args.format = "text"
        args.auto_load = False

        with pytest.raises(SystemExit):
            handle_workflow_recommend_command(args)

