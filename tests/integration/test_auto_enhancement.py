"""
Integration tests for auto-enhancement in both Cursor and headless modes.
"""

import os
import pytest
from argparse import Namespace
from unittest.mock import AsyncMock, MagicMock, patch

from tapps_agents.cli.utils.prompt_enhancer import (
    enhance_prompt_if_needed,
    should_enhance_prompt,
)
from tapps_agents.core.config import AutoEnhancementConfig, ProjectConfig


class TestAutoEnhancementIntegration:
    """Integration tests for auto-enhancement."""

    def test_enhancement_skipped_when_disabled(self):
        """Test that enhancement is skipped when disabled."""
        config = AutoEnhancementConfig(enabled=False)
        args = Namespace(
            agent="implementer",
            command="implement",
            specification="Create login",
            file_path="src/api/auth.py",
        )
        result = enhance_prompt_if_needed(args, config)
        assert result.specification == "Create login"  # Unchanged

    def test_enhancement_skipped_with_no_enhance_flag(self):
        """Test that --no-enhance flag disables enhancement."""
        config = AutoEnhancementConfig(enabled=True)
        args = Namespace(
            agent="implementer",
            command="implement",
            specification="Create login",
            file_path="src/api/auth.py",
            no_enhance=True,
        )
        result = enhance_prompt_if_needed(args, config)
        assert result.specification == "Create login"  # Unchanged

    def test_enhancement_skipped_for_high_quality_prompt(self):
        """Test that high-quality prompts are not enhanced."""
        config = AutoEnhancementConfig(
            enabled=True, quality_threshold=50.0, min_prompt_length=20
        )
        args = Namespace(
            agent="implementer",
            command="implement",
            specification="Create a comprehensive user authentication system with JWT tokens, password hashing using bcrypt, session management with Redis, password reset functionality, account verification via email, and rate limiting for login attempts",
            file_path="src/api/auth.py",
        )
        result = enhance_prompt_if_needed(args, config)
        # High-quality prompt should not be enhanced
        assert "comprehensive" in result.specification

    @pytest.mark.asyncio
    async def test_enhancement_triggered_for_low_quality_prompt(self):
        """Test that low-quality prompts trigger enhancement."""
        config = AutoEnhancementConfig(
            enabled=True, quality_threshold=50.0, min_prompt_length=20
        )
        
        # Mock the enhancer agent
        with patch(
            "tapps_agents.cli.utils.prompt_enhancer.EnhancerAgent"
        ) as mock_enhancer_class:
            mock_enhancer = MagicMock()
            mock_enhancer.activate = AsyncMock()
            mock_enhancer.run = AsyncMock(
                return_value={
                    "success": True,
                    "enhanced_prompt": "Enhanced: Create login system",
                }
            )
            mock_enhancer_class.return_value = mock_enhancer

            args = Namespace(
                agent="implementer",
                command="implement",
                specification="login",
                file_path="src/api/auth.py",
            )
            result = enhance_prompt_if_needed(args, config)
            # Should have attempted enhancement
            assert mock_enhancer.run.called

    def test_force_enhancement_flag(self):
        """Test that --enhance flag forces enhancement."""
        config = AutoEnhancementConfig(
            enabled=True, quality_threshold=50.0, min_prompt_length=20
        )
        
        with patch(
            "tapps_agents.cli.utils.prompt_enhancer.EnhancerAgent"
        ) as mock_enhancer_class:
            mock_enhancer = MagicMock()
            mock_enhancer.activate = AsyncMock()
            mock_enhancer.run = AsyncMock(
                return_value={
                    "success": True,
                    "enhanced_prompt": "Enhanced prompt",
                }
            )
            mock_enhancer_class.return_value = mock_enhancer

            args = Namespace(
                agent="implementer",
                command="implement",
                specification="Create a comprehensive user authentication system with JWT tokens, password hashing using bcrypt, session management with Redis",
                file_path="src/api/auth.py",
                enhance=True,  # Force enhancement
            )
            result = enhance_prompt_if_needed(args, config)
            # Should have attempted enhancement despite high quality
            assert mock_enhancer.run.called

    def test_enhance_mode_override(self):
        """Test that --enhance-mode flag overrides config."""
        config = AutoEnhancementConfig(
            enabled=True,
            commands={"implementer": {"synthesis_mode": "full"}},
        )
        
        with patch(
            "tapps_agents.cli.utils.prompt_enhancer.EnhancerAgent"
        ) as mock_enhancer_class:
            mock_enhancer = MagicMock()
            mock_enhancer.activate = AsyncMock()
            mock_enhancer.run = AsyncMock(
                return_value={
                    "success": True,
                    "enhanced_prompt": "Enhanced prompt",
                }
            )
            mock_enhancer_class.return_value = mock_enhancer

            args = Namespace(
                agent="implementer",
                command="implement",
                specification="login",
                file_path="src/api/auth.py",
                enhance_mode="quick",  # Override to quick
            )
            result = enhance_prompt_if_needed(args, config)
            # Should use quick mode
            mock_enhancer.run.assert_called()
            call_args = mock_enhancer.run.call_args
            assert call_args[0][0] == "enhance-quick"  # Quick mode

    def test_cursor_mode_synthesis(self):
        """Test that Cursor mode returns structured data for synthesis."""
        # Set Cursor mode
        os.environ["TAPPS_AGENTS_MODE"] = "cursor"
        
        try:
            config = AutoEnhancementConfig(enabled=True)
            
            with patch(
                "tapps_agents.cli.utils.prompt_enhancer.EnhancerAgent"
            ) as mock_enhancer_class:
                mock_enhancer = MagicMock()
                mock_enhancer.activate = AsyncMock()
                mock_enhancer.run = AsyncMock(
                    return_value={
                        "success": True,
                        "instruction": {
                            "agent_name": "enhancer",
                            "command": "synthesize-prompt",
                            "prompt": "Synthesize...",
                            "parameters": {},
                        },
                        "skill_command": "@enhancer *synthesize-prompt ...",
                        "synthesis_data": {
                            "original_prompt": "login",
                            "stages": {},
                            "format": "markdown",
                        },
                    }
                )
                mock_enhancer_class.return_value = mock_enhancer

                args = Namespace(
                    agent="implementer",
                    command="implement",
                    specification="login",
                    file_path="src/api/auth.py",
                )
                result = enhance_prompt_if_needed(args, config)
                # In Cursor mode, should return original prompt
                # (synthesis happens via Cursor Skills)
                assert result.specification == "login"
        finally:
            # Clean up
            if "TAPPS_AGENTS_MODE" in os.environ:
                del os.environ["TAPPS_AGENTS_MODE"]

    def test_headless_mode_synthesis(self):
        """Test that headless mode uses MAL for synthesis."""
        # Set headless mode
        os.environ["TAPPS_AGENTS_MODE"] = "headless"
        
        try:
            config = AutoEnhancementConfig(enabled=True)
            
            with patch(
                "tapps_agents.cli.utils.prompt_enhancer.EnhancerAgent"
            ) as mock_enhancer_class, patch(
                "tapps_agents.agents.enhancer.agent.MAL"
            ) as mock_mal_class:
                mock_enhancer = MagicMock()
                mock_enhancer.activate = AsyncMock()
                mock_enhancer.run = AsyncMock(
                    return_value={
                        "success": True,
                        "enhanced_prompt": "Enhanced: Create login system",
                    }
                )
                mock_enhancer_class.return_value = mock_enhancer

                args = Namespace(
                    agent="implementer",
                    command="implement",
                    specification="login",
                    file_path="src/api/auth.py",
                )
                result = enhance_prompt_if_needed(args, config)
                # Should have attempted enhancement
                assert mock_enhancer.run.called
        finally:
            # Clean up
            if "TAPPS_AGENTS_MODE" in os.environ:
                del os.environ["TAPPS_AGENTS_MODE"]

    def test_per_command_configuration(self):
        """Test that per-command configuration is respected."""
        config = AutoEnhancementConfig(
            enabled=True,
            commands={
                "implementer": {"enabled": True, "synthesis_mode": "full"},
                "planner": {"enabled": True, "synthesis_mode": "quick"},
                "architect": {"enabled": False},
            },
        )
        
        # Test implementer (enabled)
        args1 = Namespace(
            agent="implementer",
            command="implement",
            specification="login",
            file_path="src/api/auth.py",
        )
        result1 = should_enhance_prompt("login", "implementer", "implement", config)
        assert result1 is True

        # Test architect (disabled)
        args2 = Namespace(
            agent="architect",
            command="design-system",
            requirements="Design system",
        )
        result2 = should_enhance_prompt(
            "Design system", "architect", "design-system", config
        )
        assert result2 is False

