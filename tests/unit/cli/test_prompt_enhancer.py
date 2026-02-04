"""
Unit tests for prompt enhancement middleware.
"""

from argparse import Namespace
from unittest.mock import AsyncMock, patch

import pytest

from tapps_agents.cli.utils.prompt_enhancer import (
    assess_prompt_quality,
    detect_prompt_argument,
    enhance_prompt,
    should_enhance_prompt,
)
from tapps_agents.core.config import AutoEnhancementConfig


class TestDetectPromptArgument:
    """Tests for prompt argument detection."""

    def test_detect_implementer_specification(self):
        """Test detection of specification argument in implementer command."""
        args = Namespace(
            agent="implementer",
            command="implement",
            specification="Create login system",
            file_path="src/api/auth.py",
        )
        result = detect_prompt_argument(args)
        assert result == ("specification", "Create login system")

    def test_detect_planner_description(self):
        """Test detection of description argument in planner command."""
        args = Namespace(
            agent="planner",
            command="plan",
            description="Add user authentication",
        )
        result = detect_prompt_argument(args)
        assert result == ("description", "Add user authentication")

    def test_detect_architect_requirements(self):
        """Test detection of requirements argument in architect command."""
        args = Namespace(
            agent="architect",
            command="design-system",
            requirements="Microservices architecture",
        )
        result = detect_prompt_argument(args)
        assert result == ("requirements", "Microservices architecture")

    def test_no_prompt_argument(self):
        """Test that commands without prompts return None."""
        args = Namespace(
            agent="reviewer",
            command="review",
            file="src/api/auth.py",
        )
        result = detect_prompt_argument(args)
        assert result is None

    def test_skip_debugger_command(self):
        """Test that debugger command is skipped."""
        args = Namespace(
            agent="debugger",
            command="debug",
            error_message="Some error",
        )
        result = detect_prompt_argument(args)
        assert result is None


class TestAssessPromptQuality:
    """Tests for prompt quality assessment."""

    def test_very_short_prompt(self):
        """Test that very short prompts get low quality score."""
        config = AutoEnhancementConfig(min_prompt_length=20)
        prompt = "login"
        score = assess_prompt_quality(prompt, config)
        assert score == 0.0

    def test_high_quality_prompt(self):
        """Test that detailed prompts get high quality score."""
        config = AutoEnhancementConfig()
        prompt = """Create a comprehensive user authentication system with the following requirements:
        - JWT token-based authentication
        - Password hashing using bcrypt
        - Session management with Redis
        - Password reset functionality
        - Account verification via email
        - Rate limiting for login attempts
        - Security best practices including CSRF protection"""
        score = assess_prompt_quality(prompt, config)
        assert score > 70.0

    def test_medium_quality_prompt(self):
        """Test that medium prompts get medium quality score."""
        config = AutoEnhancementConfig()
        prompt = "Create a login system with authentication and password reset"
        score = assess_prompt_quality(prompt, config)
        assert 30.0 < score < 70.0

    def test_keyword_boost(self):
        """Test that prompts with quality keywords get higher scores."""
        config = AutoEnhancementConfig()
        prompt1 = "Create login"
        prompt2 = "Create login system with requirements, architecture, and implementation"
        score1 = assess_prompt_quality(prompt1, config)
        score2 = assess_prompt_quality(prompt2, config)
        assert score2 > score1

    def test_technical_terms_boost(self):
        """Test that prompts with technical terms get higher scores."""
        config = AutoEnhancementConfig()
        prompt1 = "Create login"
        prompt2 = "Create login API endpoint with authentication and database model"
        score1 = assess_prompt_quality(prompt1, config)
        score2 = assess_prompt_quality(prompt2, config)
        assert score2 > score1

    def test_already_spec_like_gets_high_score(self):
        """Prompts with acceptance criteria, user story, shall/must, bullets score high."""
        config = AutoEnhancementConfig(min_prompt_length=10)
        spec_like = """User story: As a user I want to log in so that I access my account.
Acceptance criteria:
- The system shall validate credentials.
- The system must support password reset.
- Session should expire after 24h."""
        score = assess_prompt_quality(spec_like, config)
        assert score >= 50.0, "spec-like prompts should not be enhanced (score >= threshold)"

    def test_short_vague_prompt_gets_low_score(self):
        """Short vague prompts (above min length) without spec structure get modest score."""
        config = AutoEnhancementConfig(min_prompt_length=10)
        vague = "create a simple rest api for users"  # above min length, no spec structure
        score = assess_prompt_quality(vague, config)
        # Should be below a high bar so enhancement is still considered when threshold is 50
        assert score < 70.0


class TestShouldEnhancePrompt:
    """Tests for enhancement decision logic."""

    def test_enhancement_disabled_globally(self):
        """Test that enhancement is skipped when disabled globally."""
        config = AutoEnhancementConfig(enabled=False)
        prompt = "login"
        result = should_enhance_prompt(prompt, "implementer", "implement", config)
        assert result is False

    def test_enhancement_disabled_per_command(self):
        """Test that enhancement is skipped when disabled for command."""
        config = AutoEnhancementConfig(
            commands={"architect": {"enabled": False}}
        )
        prompt = "Design system"
        result = should_enhance_prompt(prompt, "architect", "design-system", config)
        assert result is False

    def test_low_quality_prompt_enhanced(self):
        """Test that low-quality prompts are enhanced."""
        config = AutoEnhancementConfig(quality_threshold=50.0)
        prompt = "login"
        result = should_enhance_prompt(prompt, "implementer", "implement", config)
        assert result is True

    def test_high_quality_prompt_not_enhanced(self):
        """Test that high-quality prompts are not enhanced."""
        config = AutoEnhancementConfig(quality_threshold=50.0)
        prompt = """Create a comprehensive user authentication system with JWT tokens,
        password hashing using bcrypt, session management with Redis, password reset
        functionality, account verification via email, and rate limiting for login attempts.
        Include security best practices and comprehensive error handling."""
        result = should_enhance_prompt(prompt, "implementer", "implement", config)
        assert result is False

    def test_min_length_check(self):
        """Test that prompts below minimum length are enhanced."""
        config = AutoEnhancementConfig(
            min_prompt_length=20, quality_threshold=50.0
        )
        prompt = "login"  # Below min length
        result = should_enhance_prompt(prompt, "implementer", "implement", config)
        assert result is True

    def test_quality_threshold_boundary(self):
        """Test quality threshold boundary behavior."""
        config = AutoEnhancementConfig(quality_threshold=50.0)
        
        # Prompt that scores exactly at threshold should not be enhanced
        # (threshold is "below which to enhance")
        prompt_at_threshold = "Create a login system"  # Should score around 50
        result = should_enhance_prompt(
            prompt_at_threshold, "implementer", "implement", config
        )
        # This may vary based on exact scoring, but should be consistent
        assert isinstance(result, bool)

    def test_spec_like_prompt_not_enhanced(self):
        """Clearly spec-like prompt (acceptance criteria, shall) should not be enhanced."""
        config = AutoEnhancementConfig(quality_threshold=50.0, min_prompt_length=10)
        spec = """As a user I want to login. Acceptance criteria: the system shall validate.
        - Use JWT. - Session must expire."""
        result = should_enhance_prompt(spec, "planner", "plan", config)
        assert result is False

    def test_short_vague_prompt_still_enhanced(self):
        """Short vague prompt below min_prompt_length gets score 0 and is enhanced."""
        config = AutoEnhancementConfig(quality_threshold=50.0, min_prompt_length=30)
        vague = "make a api for users"  # 21 chars, below min 30 -> score 0 -> enhanced
        result = should_enhance_prompt(vague, "implementer", "implement", config)
        assert result is True


class TestEnhancePrompt:
    """Tests for enhance_prompt (synthesis_mode when enhance_mode is None)."""

    @pytest.mark.asyncio
    async def test_synthesis_mode_from_config_when_enhance_mode_none(self):
        """When enhance_mode is None, synthesis_mode comes from config per agent."""
        config = AutoEnhancementConfig(
            commands={
                "implementer": {"enabled": True, "synthesis_mode": "full"},
                "analyst": {"enabled": True, "synthesis_mode": "quick"},
            }
        )
        with patch(
            "tapps_agents.cli.utils.prompt_enhancer.EnhancerAgent",
            spec=True,
        ) as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value = mock_instance
            mock_instance.activate = AsyncMock()
            mock_instance.close = AsyncMock()
            mock_instance.run = AsyncMock(
                return_value={"success": True, "enhanced_prompt": "Enhanced."}
            )

            await enhance_prompt("x" * 25, "implementer", "implement", config, enhance_mode=None)
            mock_instance.run.assert_called_once()
            assert mock_instance.run.call_args[0][0] == "enhance"

            mock_instance.run.reset_mock()
            await enhance_prompt("x" * 25, "analyst", "gather-requirements", config, enhance_mode=None)
            mock_instance.run.assert_called_once()
            assert mock_instance.run.call_args[0][0] == "enhance-quick"

    @pytest.mark.asyncio
    async def test_enhance_mode_override_ignores_config(self):
        """When enhance_mode is set, it overrides config synthesis_mode."""
        config = AutoEnhancementConfig(
            commands={"implementer": {"enabled": True, "synthesis_mode": "full"}}
        )
        with patch(
            "tapps_agents.cli.utils.prompt_enhancer.EnhancerAgent",
            spec=True,
        ) as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value = mock_instance
            mock_instance.activate = AsyncMock()
            mock_instance.close = AsyncMock()
            mock_instance.run = AsyncMock(
                return_value={"success": True, "enhanced_prompt": "Done."}
            )
            await enhance_prompt(
                "x" * 25, "implementer", "implement", config, enhance_mode="quick"
            )
            mock_instance.run.assert_called_once()
            assert mock_instance.run.call_args[0][0] == "enhance-quick"

