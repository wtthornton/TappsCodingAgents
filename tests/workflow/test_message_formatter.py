"""
Tests for MessageFormatter - ENH-001-S3

Tests for the message formatting system including:
- Blocking and warning message formatting
- CLI and IDE output formats
- Configurable emoji support
- Workflow-specific benefits
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.workflow.intent_detector import WorkflowType
from tapps_agents.workflow.message_formatter import (
    MessageConfig,
    MessageFormatter,
    OutputFormat,
    WORKFLOW_BENEFITS,
)


class TestMessageFormatter:
    """Tests for MessageFormatter class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        formatter = MessageFormatter()
        assert formatter.config.use_emoji is True
        assert formatter.config.output_format == OutputFormat.CLI
        assert formatter.config.show_benefits is True
        assert formatter.config.show_override is True

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = MessageConfig(
            use_emoji=False,
            output_format=OutputFormat.IDE,
            show_benefits=False,
            show_override=False,
        )
        formatter = MessageFormatter(config=config)
        assert formatter.config.use_emoji is False
        assert formatter.config.output_format == OutputFormat.IDE


class TestBlockingMessage:
    """Tests for blocking message formatting."""

    def test_blocking_message_contains_file_path(self):
        """Test blocking message includes file path."""
        formatter = MessageFormatter()
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add login feature",
            file_path=Path("src/auth.py"),
            confidence=85.0,
        )
        assert "src/auth.py" in msg

    def test_blocking_message_contains_workflow(self):
        """Test blocking message includes workflow command."""
        formatter = MessageFormatter()
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add login feature",
            file_path=Path("src/auth.py"),
            confidence=85.0,
        )
        assert "*build" in msg
        assert "@simple-mode" in msg

    def test_blocking_message_contains_confidence(self):
        """Test blocking message includes confidence percentage."""
        formatter = MessageFormatter()
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.FIX,
            user_intent="Fix bug",
            file_path=Path("src/api.py"),
            confidence=72.5,
        )
        assert "72%" in msg or "73%" in msg  # Allow for rounding

    def test_blocking_message_contains_user_intent(self):
        """Test blocking message includes user intent."""
        formatter = MessageFormatter()
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add authentication system",
            file_path=Path("src/auth.py"),
            confidence=90.0,
        )
        assert "Add authentication system" in msg

    def test_blocking_message_default_intent(self):
        """Test blocking message uses default intent when empty."""
        formatter = MessageFormatter()
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="",
            file_path=Path("src/api.py"),
            confidence=80.0,
        )
        assert "Implement feature" in msg

    def test_blocking_message_contains_benefits(self):
        """Test blocking message includes workflow benefits."""
        formatter = MessageFormatter()
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add feature",
            file_path=Path("src/feature.py"),
            confidence=85.0,
        )
        assert "80%+ coverage" in msg or "testing" in msg.lower()

    def test_blocking_message_contains_override(self):
        """Test blocking message includes override instructions."""
        formatter = MessageFormatter()
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add feature",
            file_path=Path("src/feature.py"),
            confidence=85.0,
        )
        assert "--skip-enforcement" in msg

    def test_blocking_message_with_emoji(self):
        """Test blocking message includes emoji when enabled."""
        config = MessageConfig(use_emoji=True)
        formatter = MessageFormatter(config=config)
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add feature",
            file_path=Path("src/feature.py"),
            confidence=85.0,
        )
        assert "\u26a0" in msg  # Warning emoji

    def test_blocking_message_without_emoji(self):
        """Test blocking message excludes emoji when disabled."""
        config = MessageConfig(use_emoji=False)
        formatter = MessageFormatter(config=config)
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add feature",
            file_path=Path("src/feature.py"),
            confidence=85.0,
        )
        assert "\u26a0" not in msg


class TestWarningMessage:
    """Tests for warning message formatting."""

    def test_warning_message_contains_workflow(self):
        """Test warning message includes workflow suggestion."""
        formatter = MessageFormatter()
        msg = formatter.format_warning_message(
            workflow=WorkflowType.REFACTOR,
            user_intent="Clean up code",
            confidence=65.0,
        )
        assert "*refactor" in msg
        assert "@simple-mode" in msg

    def test_warning_message_contains_confidence(self):
        """Test warning message includes confidence."""
        formatter = MessageFormatter()
        msg = formatter.format_warning_message(
            workflow=WorkflowType.FIX,
            user_intent="Fix bug",
            confidence=70.0,
        )
        assert "70%" in msg

    def test_warning_message_indicates_proceeding(self):
        """Test warning message indicates edit will proceed."""
        formatter = MessageFormatter()
        msg = formatter.format_warning_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add feature",
            confidence=75.0,
        )
        assert "Proceeding" in msg or "proceeding" in msg

    def test_warning_message_with_emoji(self):
        """Test warning message includes light bulb emoji."""
        config = MessageConfig(use_emoji=True)
        formatter = MessageFormatter(config=config)
        msg = formatter.format_warning_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add feature",
            confidence=75.0,
        )
        assert "\U0001f4a1" in msg  # Light bulb emoji


class TestAllowMessage:
    """Tests for allow message formatting."""

    def test_allow_message_is_empty(self):
        """Test allow message returns empty string."""
        formatter = MessageFormatter()
        msg = formatter.format_allow_message()
        assert msg == ""


class TestOutputFormats:
    """Tests for CLI and IDE output formats."""

    def test_cli_format_uses_dashes(self):
        """Test CLI format uses dash bullets."""
        config = MessageConfig(output_format=OutputFormat.CLI)
        formatter = MessageFormatter(config=config)
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add feature",
            file_path=Path("src/feature.py"),
            confidence=85.0,
        )
        assert "  - " in msg

    def test_ide_format_uses_asterisks(self):
        """Test IDE format uses asterisk bullets."""
        config = MessageConfig(output_format=OutputFormat.IDE)
        formatter = MessageFormatter(config=config)
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add feature",
            file_path=Path("src/feature.py"),
            confidence=85.0,
        )
        assert "  * " in msg


class TestWorkflowBenefits:
    """Tests for workflow-specific benefits."""

    def test_build_benefits(self):
        """Test BUILD workflow has correct benefits."""
        assert WorkflowType.BUILD in WORKFLOW_BENEFITS
        benefits = WORKFLOW_BENEFITS[WorkflowType.BUILD]
        assert len(benefits) >= 3
        assert any("test" in b.lower() for b in benefits)

    def test_fix_benefits(self):
        """Test FIX workflow has correct benefits."""
        assert WorkflowType.FIX in WORKFLOW_BENEFITS
        benefits = WORKFLOW_BENEFITS[WorkflowType.FIX]
        assert len(benefits) >= 3

    def test_refactor_benefits(self):
        """Test REFACTOR workflow has correct benefits."""
        assert WorkflowType.REFACTOR in WORKFLOW_BENEFITS
        benefits = WORKFLOW_BENEFITS[WorkflowType.REFACTOR]
        assert len(benefits) >= 3

    def test_review_benefits(self):
        """Test REVIEW workflow has correct benefits."""
        assert WorkflowType.REVIEW in WORKFLOW_BENEFITS
        benefits = WORKFLOW_BENEFITS[WorkflowType.REVIEW]
        assert len(benefits) >= 3
        assert any("security" in b.lower() for b in benefits)

    def test_all_workflow_types_have_benefits(self):
        """Test all workflow types have defined benefits."""
        for workflow in WorkflowType:
            assert workflow in WORKFLOW_BENEFITS
            assert len(WORKFLOW_BENEFITS[workflow]) > 0


class TestConfigOptions:
    """Tests for configuration options."""

    def test_hide_benefits(self):
        """Test benefits can be hidden."""
        config = MessageConfig(show_benefits=False)
        formatter = MessageFormatter(config=config)
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add feature",
            file_path=Path("src/feature.py"),
            confidence=85.0,
        )
        # Should not contain the benefits list header
        assert "TappsCodingAgents workflows provide:" not in msg

    def test_hide_override(self):
        """Test override instructions can be hidden."""
        config = MessageConfig(show_override=False)
        formatter = MessageFormatter(config=config)
        msg = formatter.format_blocking_message(
            workflow=WorkflowType.BUILD,
            user_intent="Add feature",
            file_path=Path("src/feature.py"),
            confidence=85.0,
        )
        assert "--skip-enforcement" not in msg
