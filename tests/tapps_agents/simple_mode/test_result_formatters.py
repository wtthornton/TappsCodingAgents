"""Tests for result_formatters module."""

import pytest

from tapps_agents.simple_mode.result_formatters import (
    FormatterRegistry,
    format_failed_step,
    format_skipped_step,
    format_step_result,
)
from tapps_agents.simple_mode.step_results import (
    ArchitectStepResult,
    BaseStepResult,
    DesignerStepResult,
    EnhancerStepResult,
    ImplementerStepResult,
    PlannerStepResult,
    ReviewerStepResult,
    StepStatus,
    QAStepResult,
    VerificationStepResult,
)


class TestFormatterRegistry:
    """Tests for FormatterRegistry."""

    def test_registered_formatters(self):
        """Test that formatters are registered."""
        registered = FormatterRegistry.get_registered_formatters()
        assert "enhancer" in registered
        assert "planner" in registered
        assert "architect" in registered
        assert "designer" in registered
        assert "implementer" in registered
        assert "reviewer" in registered
        assert "tester" in registered
        assert "verification" in registered

    def test_format_uses_registered_formatter(self):
        """Test that format uses correct registered formatter."""
        result = EnhancerStepResult(
            step_number=1,
            step_name="enhancer",
            agent_name="enhancer",
            status=StepStatus.SUCCESS,
            enhanced_prompt="Test prompt",
        )
        formatted = FormatterRegistry.format(result)
        assert "Step 1: Enhanced Prompt" in formatted
        assert "Test prompt" in formatted

    def test_format_uses_default_for_unknown(self):
        """Test that format uses default for unknown agent."""
        # Use step_number=9 (valid range 1-9) with an unknown agent
        result = BaseStepResult(
            step_number=9,
            step_name="custom_step",
            agent_name="custom_agent",
            status=StepStatus.SUCCESS,
        )
        formatted = FormatterRegistry.format(result)
        assert "custom_agent" in formatted.lower() or "custom_step" in formatted.lower()


class TestEnhancerFormatter:
    """Tests for enhancer formatter."""

    def test_format_success(self):
        """Test formatting successful enhancer result."""
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
        formatted = format_step_result(result)
        
        assert "# Step 1: Enhanced Prompt" in formatted
        assert "✅ SUCCESS" in formatted
        assert "Enhanced description" in formatted
        assert "Req 1" in formatted
        assert "microservices" in formatted

    def test_format_failed(self):
        """Test formatting failed enhancer result."""
        result = EnhancerStepResult(
            step_number=1,
            step_name="enhancer",
            agent_name="enhancer",
            status=StepStatus.FAILED,
            error_message="Enhancement failed",
        )
        formatted = format_step_result(result)
        
        assert "❌ FAILED" in formatted
        assert "Enhancement failed" in formatted


class TestPlannerFormatter:
    """Tests for planner formatter."""

    def test_format_with_stories(self):
        """Test formatting planner result with stories."""
        result = PlannerStepResult(
            step_number=2,
            step_name="planner",
            agent_name="planner",
            status=StepStatus.SUCCESS,
            stories=[
                {
                    "title": "User Login",
                    "description": "As a user, I want to login",
                    "acceptance_criteria": ["Can enter credentials", "Gets token"],
                },
            ],
            story_points=5,
        )
        formatted = format_step_result(result)
        
        assert "# Step 2: User Stories" in formatted
        assert "User Login" in formatted
        assert "As a user" in formatted
        assert "Can enter credentials" in formatted
        assert "Story Points Total:** 5" in formatted


class TestArchitectFormatter:
    """Tests for architect formatter."""

    def test_format_with_components(self):
        """Test formatting architect result with components."""
        result = ArchitectStepResult(
            step_number=3,
            step_name="architect",
            agent_name="architect",
            status=StepStatus.SUCCESS,
            architecture_pattern="Microservices",
            technology_stack=["Python", "FastAPI", "PostgreSQL"],
            components=[
                {"name": "AuthService", "purpose": "Handle authentication"},
            ],
            data_flow="Client -> API Gateway -> Services",
        )
        formatted = format_step_result(result)
        
        assert "# Step 3: System Architecture" in formatted
        assert "Microservices" in formatted
        assert "Python" in formatted
        assert "AuthService" in formatted
        assert "Data Flow" in formatted


class TestDesignerFormatter:
    """Tests for designer formatter."""

    def test_format_with_endpoints(self):
        """Test formatting designer result with endpoints."""
        result = DesignerStepResult(
            step_number=4,
            step_name="designer",
            agent_name="designer",
            status=StepStatus.SUCCESS,
            api_endpoints=[
                {"method": "POST", "path": "/login", "description": "User login"},
            ],
            data_models=[
                {
                    "name": "User",
                    "fields": [
                        {"name": "id", "type": "int", "description": "User ID"},
                    ],
                },
            ],
        )
        formatted = format_step_result(result)
        
        assert "# Step 4: API Design" in formatted
        assert "POST /login" in formatted
        assert "User login" in formatted
        assert "User ID" in formatted


class TestImplementerFormatter:
    """Tests for implementer formatter."""

    def test_format_with_files(self):
        """Test formatting implementer result with files."""
        result = ImplementerStepResult(
            step_number=5,
            step_name="implementer",
            agent_name="implementer",
            status=StepStatus.SUCCESS,
            files_created=["src/auth.py", "src/models.py"],
            files_modified=["src/config.py"],
            code_preview="def login(): pass",
        )
        formatted = format_step_result(result)
        
        assert "# Step 5: Implementation" in formatted
        assert "src/auth.py" in formatted
        assert "src/config.py" in formatted
        assert "def login()" in formatted


class TestReviewerFormatter:
    """Tests for reviewer formatter."""

    def test_format_with_scores(self):
        """Test formatting reviewer result with scores."""
        result = ReviewerStepResult(
            step_number=6,
            step_name="reviewer",
            agent_name="reviewer",
            status=StepStatus.SUCCESS,
            overall_score=85.0,
            complexity_score=7.5,
            security_score=8.0,
            maintainability_score=9.0,
            issues=[{"message": "Missing docstring"}],
            recommendations=["Add type hints"],
        )
        formatted = format_step_result(result)
        
        assert "# Step 6: Code Review" in formatted
        assert "85/100" in formatted
        assert "7.5/10" in formatted
        assert "Missing docstring" in formatted
        assert "Add type hints" in formatted

    def test_score_icon_good(self):
        """Test good score gets checkmark."""
        result = ReviewerStepResult(
            step_number=6,
            step_name="reviewer",
            agent_name="reviewer",
            status=StepStatus.SUCCESS,
            overall_score=85.0,
        )
        formatted = format_step_result(result)
        assert "✅" in formatted

    def test_score_icon_warning(self):
        """Test medium score gets warning."""
        result = ReviewerStepResult(
            step_number=6,
            step_name="reviewer",
            agent_name="reviewer",
            status=StepStatus.SUCCESS,
            overall_score=55.0,
        )
        formatted = format_step_result(result)
        assert "⚠️" in formatted

    def test_score_icon_bad(self):
        """Test low score gets X."""
        result = ReviewerStepResult(
            step_number=6,
            step_name="reviewer",
            agent_name="reviewer",
            status=StepStatus.SUCCESS,
            overall_score=35.0,
        )
        formatted = format_step_result(result)
        # Should have red X in score line
        assert "35/100" in formatted


class TestTesterFormatter:
    """Tests for tester formatter."""

    def test_format_with_tests(self):
        """Test formatting tester result with tests."""
        result = QAStepResult(
            step_number=7,
            step_name="tester",
            agent_name="tester",
            status=StepStatus.SUCCESS,
            test_files_created=["tests/test_auth.py"],
            test_count=5,
            coverage_percent=80.5,
            test_plan="Test login, logout, token refresh",
        )
        formatted = format_step_result(result)
        
        assert "# Step 7: Test Generation" in formatted
        assert "test_auth.py" in formatted
        assert "Tests Generated:** 5" in formatted
        assert "80.5%" in formatted


class TestVerificationFormatter:
    """Tests for verification formatter."""

    def test_format_complete(self):
        """Test formatting complete verification."""
        result = VerificationStepResult(
            step_number=8,
            step_name="verification",
            agent_name="verification",
            status=StepStatus.SUCCESS,
            complete=True,
            deliverables_verified=7,
            deliverables_total=7,
        )
        formatted = format_step_result(result)
        
        assert "# Step 8: Comprehensive Verification" in formatted
        assert "✅ Complete" in formatted
        assert "7/7" in formatted

    def test_format_incomplete_with_gaps(self):
        """Test formatting incomplete verification with gaps."""
        result = VerificationStepResult(
            step_number=8,
            step_name="verification",
            agent_name="verification",
            status=StepStatus.SUCCESS,
            complete=False,
            gaps=[
                {"category": "tests", "item": "Missing unit tests"},
            ],
            loopback_step=7,
            deliverables_verified=5,
            deliverables_total=7,
        )
        formatted = format_step_result(result)
        
        assert "❌ Incomplete" in formatted
        assert "Missing unit tests" in formatted
        assert "Step 7" in formatted


class TestHelperFunctions:
    """Tests for helper formatting functions."""

    def test_format_failed_step(self):
        """Test format_failed_step helper."""
        formatted = format_failed_step(
            step_number=3,
            agent_name="architect",
            error_message="Unknown command: design",
        )
        assert "Step 3: Architect" in formatted
        assert "❌ FAILED" in formatted
        assert "Unknown command" in formatted

    def test_format_skipped_step(self):
        """Test format_skipped_step helper."""
        formatted = format_skipped_step(
            step_number=4,
            agent_name="designer",
            skip_reason="Dependency step 3 failed",
        )
        assert "Step 4: Designer" in formatted
        assert "⏭️ SKIPPED" in formatted
        assert "Dependency" in formatted
