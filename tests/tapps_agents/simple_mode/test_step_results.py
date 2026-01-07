"""Tests for step_results module."""

import pytest

from tapps_agents.simple_mode.step_results import (
    ArchitectStepResult,
    BaseStepResult,
    DesignerStepResult,
    EnhancerStepResult,
    ImplementerStepResult,
    PlannerStepResult,
    ReviewerStepResult,
    StepResultParser,
    StepStatus,
    QAStepResult,
    VerificationStepResult,
)


class TestStepStatus:
    """Tests for StepStatus enum."""

    def test_status_values(self):
        """Test all status values exist."""
        assert StepStatus.SUCCESS.value == "success"
        assert StepStatus.FAILED.value == "failed"
        assert StepStatus.SKIPPED.value == "skipped"
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.RUNNING.value == "running"


class TestBaseStepResult:
    """Tests for BaseStepResult model."""

    def test_create_minimal(self):
        """Test creating result with minimal fields."""
        result = BaseStepResult(
            step_number=1,
            step_name="test",
            agent_name="test_agent",
        )
        assert result.step_number == 1
        assert result.step_name == "test"
        assert result.status == StepStatus.PENDING

    def test_create_with_all_fields(self):
        """Test creating result with all fields."""
        result = BaseStepResult(
            step_number=1,
            step_name="test",
            agent_name="test_agent",
            status=StepStatus.SUCCESS,
            duration_seconds=1.5,
            error_message=None,
        )
        assert result.status == StepStatus.SUCCESS
        assert result.duration_seconds == 1.5

    def test_step_number_validation(self):
        """Test step number validation."""
        # Valid range
        result = BaseStepResult(
            step_number=1,
            step_name="test",
            agent_name="test_agent",
        )
        assert result.step_number == 1

        # Step 9 should be valid
        result = BaseStepResult(
            step_number=9,
            step_name="test",
            agent_name="test_agent",
        )
        assert result.step_number == 9


class TestEnhancerStepResult:
    """Tests for EnhancerStepResult model."""

    def test_create_with_enhancement_data(self):
        """Test creating enhancer result with enhancement data."""
        result = EnhancerStepResult(
            step_number=1,
            step_name="enhancer",
            agent_name="enhancer",
            status=StepStatus.SUCCESS,
            enhanced_prompt="Enhanced description",
            requirements=["Req 1", "Req 2"],
            architecture_guidance="Use microservices",
            quality_standards="Follow PEP8",
        )
        assert result.enhanced_prompt == "Enhanced description"
        assert len(result.requirements) == 2
        assert result.architecture_guidance == "Use microservices"


class TestPlannerStepResult:
    """Tests for PlannerStepResult model."""

    def test_create_with_stories(self):
        """Test creating planner result with user stories."""
        result = PlannerStepResult(
            step_number=2,
            step_name="planner",
            agent_name="planner",
            status=StepStatus.SUCCESS,
            stories=[
                {"title": "Story 1", "description": "Desc 1"},
                {"title": "Story 2", "description": "Desc 2"},
            ],
            story_points=5,
        )
        assert len(result.stories) == 2
        assert result.story_points == 5

    def test_stories_validation_adds_title(self):
        """Test that validation adds title to stories without one."""
        result = PlannerStepResult(
            step_number=2,
            step_name="planner",
            agent_name="planner",
            stories=[{"description": "No title story"}],
        )
        # Validator should add default title
        assert result.stories[0].get("title") == "Untitled Story"


class TestReviewerStepResult:
    """Tests for ReviewerStepResult model."""

    def test_create_with_scores(self):
        """Test creating reviewer result with quality scores."""
        result = ReviewerStepResult(
            step_number=6,
            step_name="reviewer",
            agent_name="reviewer",
            status=StepStatus.SUCCESS,
            overall_score=85.0,
            complexity_score=7.5,
            security_score=8.0,
            maintainability_score=9.0,
            issues=[{"message": "Issue 1"}],
            recommendations=["Use type hints"],
        )
        assert result.overall_score == 85.0
        assert result.complexity_score == 7.5
        assert len(result.issues) == 1

    def test_score_validation_range(self):
        """Test score validation ranges."""
        result = ReviewerStepResult(
            step_number=6,
            step_name="reviewer",
            agent_name="reviewer",
            overall_score=100.0,  # Max value
            complexity_score=10.0,  # Max value
        )
        assert result.overall_score == 100.0
        assert result.complexity_score == 10.0


class TestStepResultParser:
    """Tests for StepResultParser."""

    def test_parse_success_result(self):
        """Test parsing successful agent result."""
        raw = {
            "result": {
                "enhanced_prompt": "Enhanced",
                "requirements": ["Req 1"],
            }
        }
        result = StepResultParser.parse("enhancer", raw, 1)
        assert result.status == StepStatus.SUCCESS
        assert result.agent_name == "enhancer"

    def test_parse_error_result(self):
        """Test parsing error agent result."""
        raw = {
            "result": {
                "error": "Unknown command: design"
            }
        }
        result = StepResultParser.parse("architect", raw, 3)
        assert result.status == StepStatus.FAILED
        assert "Unknown command" in result.error_message

    def test_parse_string_result(self):
        """Test parsing string result."""
        raw = {
            "result": "Some output text"
        }
        result = StepResultParser.parse("unknown", raw, 1)
        assert result.status == StepStatus.SUCCESS

    def test_create_failed_result(self):
        """Test creating failed result helper."""
        result = StepResultParser.create_failed_result(
            agent_name="architect",
            step_number=3,
            error_message="Test error",
        )
        assert result.status == StepStatus.FAILED
        assert result.error_message == "Test error"
        assert isinstance(result, ArchitectStepResult)

    def test_create_skipped_result(self):
        """Test creating skipped result helper."""
        result = StepResultParser.create_skipped_result(
            agent_name="designer",
            step_number=4,
            skip_reason="Dependency failed",
        )
        assert result.status == StepStatus.SKIPPED
        assert "Dependency failed" in result.error_message
        assert isinstance(result, DesignerStepResult)
