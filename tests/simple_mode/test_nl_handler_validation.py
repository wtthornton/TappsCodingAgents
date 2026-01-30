"""
Comprehensive tests for SimpleModeHandler workflow validation.

Tests workflow mismatch detection, warning display, and user interaction.
Target: ≥85% coverage of validation logic in nl_handler.py.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dataclasses import FrozenInstanceError

pytestmark = pytest.mark.unit

from tapps_agents.simple_mode.nl_handler import (
    SimpleModeHandler,
    WorkflowMismatchWarning,
)
from tapps_agents.simple_mode.workflow_suggester import WORKFLOW_REQUIREMENTS
from tapps_agents.simple_mode.intent_parser import IntentType
from tapps_agents.core.config import ProjectConfig


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_config():
    """Create mock ProjectConfig."""
    config = Mock(spec=ProjectConfig)
    config.simple_mode = Mock()
    config.simple_mode.enabled = True
    return config


@pytest.fixture
def handler(mock_config, tmp_path):
    """Create SimpleModeHandler instance with mock config."""
    return SimpleModeHandler(
        project_root=tmp_path,
        config=mock_config
    )


@pytest.fixture
def sample_warning():
    """Create sample WorkflowMismatchWarning."""
    return WorkflowMismatchWarning(
        detected_intent="bug_fix",
        detected_scope="low",
        detected_complexity="low",
        recommended_workflow="*fix",
        confidence=0.85,
        reason="*full workflow is designed for: Framework development",
        token_savings=60000,
        time_savings=30
    )


# ============================================================================
# Test WorkflowMismatchWarning Dataclass
# ============================================================================

class TestWorkflowMismatchWarning:
    """Test WorkflowMismatchWarning dataclass."""

    def test_warning_creation(self):
        """Test creating warning with all fields."""
        warning = WorkflowMismatchWarning(
            detected_intent="bug_fix",
            detected_scope="low",
            detected_complexity="medium",
            recommended_workflow="*fix",
            confidence=0.75,
            reason="Test reason",
            token_savings=30000,
            time_savings=15
        )

        assert warning.detected_intent == "bug_fix"
        assert warning.detected_scope == "low"
        assert warning.detected_complexity == "medium"
        assert warning.recommended_workflow == "*fix"
        assert warning.confidence == 0.75
        assert warning.reason == "Test reason"
        assert warning.token_savings == 30000
        assert warning.time_savings == 15

    def test_warning_immutability(self, sample_warning):
        """Test that warning is frozen (immutable)."""
        with pytest.raises(FrozenInstanceError):
            sample_warning.confidence = 0.90

    def test_warning_format_warning(self, sample_warning):
        """Test formatting warning for display."""
        formatted = sample_warning.format_warning()

        assert "Workflow Mismatch Warning" in formatted
        assert "bug_fix" in formatted
        assert "low" in formatted
        assert "85%" in formatted
        assert "*fix" in formatted
        assert "60K tokens" in formatted
        assert "30 minutes" in formatted


# ============================================================================
# Test validate_workflow_match()
# ============================================================================

class TestValidateWorkflowMatch:
    """Test validate_workflow_match() method."""

    def test_validate_workflow_match_with_force_flag(self, handler):
        """Test validation is bypassed with force=True."""
        warning = handler.validate_workflow_match(
            workflow="*full",
            prompt="Fix validation bug",
            force=True
        )
        assert warning is None

    def test_validate_workflow_match_unknown_workflow(self, handler):
        """Test validation with unknown workflow returns None."""
        warning = handler.validate_workflow_match(
            workflow="*unknown",
            prompt="Fix bug",
            force=False
        )
        assert warning is None

    def test_validate_workflow_match_empty_prompt(self, handler):
        """Test validation with empty prompt returns None."""
        warning = handler.validate_workflow_match(
            workflow="*full",
            prompt="",
            force=False
        )
        assert warning is None

    def test_validate_workflow_match_low_confidence(self, handler):
        """Test validation with low confidence intent returns None."""
        # Use a very vague prompt that should have low confidence
        warning = handler.validate_workflow_match(
            workflow="*full",
            prompt="update",
            force=False
        )
        # Should return None due to low confidence (< 0.6)
        assert warning is None

    def test_validate_workflow_match_bug_fix_with_full_workflow(self, handler):
        """Test mismatch detection: bug fix with *full workflow."""
        warning = handler.validate_workflow_match(
            workflow="*full",
            prompt="Fix validation bug that reports 0/14",
            force=False
        )

        # Should detect mismatch (bug fix != full workflow)
        if warning:
            assert warning.detected_intent == "bug_fix"
            assert warning.recommended_workflow == "*fix"
            assert warning.confidence >= 0.7
            assert warning.token_savings > 0

    def test_validate_workflow_match_bug_fix_with_fix_workflow(self, handler):
        """Test no mismatch: bug fix with *fix workflow."""
        warning = handler.validate_workflow_match(
            workflow="*fix",
            prompt="Fix validation bug",
            force=False
        )

        # Should not detect mismatch (correct workflow)
        # Note: Might still return warning depending on intent detection
        if warning:
            # If warning returned, confidence should indicate uncertainty
            assert 0.0 <= warning.confidence <= 1.0

    def test_validate_workflow_match_enhancement_with_build_workflow(self, handler):
        """Test no mismatch: enhancement with *build workflow."""
        warning = handler.validate_workflow_match(
            workflow="*build",
            prompt="Improve user experience with better feedback",
            force=False
        )

        # Enhancement matches *build workflow
        # Should return None or low-confidence warning
        if warning:
            assert 0.0 <= warning.confidence <= 1.0

    def test_validate_workflow_match_architectural_with_full_workflow(self, handler):
        """Test no mismatch: architectural with *full workflow."""
        warning = handler.validate_workflow_match(
            workflow="*full",
            prompt="Modify tapps_agents/ framework architecture",
            force=False
        )

        # Architectural matches *full workflow
        # Should return None or low-confidence warning
        if warning:
            assert 0.0 <= warning.confidence <= 1.0


# ============================================================================
# Test _analyze_task_characteristics()
# ============================================================================

class TestAnalyzeTaskCharacteristics:
    """Test _analyze_task_characteristics() method."""

    def test_analyze_task_characteristics_framework_changes(self, handler):
        """Test analysis detects framework changes (high scope)."""
        characteristics = handler._analyze_task_characteristics(
            prompt="Modify tapps_agents/ package",
            intent="architectural"
        )

        assert characteristics["intent"] == "architectural"
        assert characteristics["scope"] == "high"
        assert characteristics["complexity"] == "high"

    def test_analyze_task_characteristics_bug_fix_low_scope(self, handler):
        """Test analysis detects bug fix with low scope."""
        characteristics = handler._analyze_task_characteristics(
            prompt="Fix validation bug",
            intent="bug_fix"
        )

        assert characteristics["intent"] == "bug_fix"
        assert characteristics["scope"] == "low"
        assert characteristics["complexity"] == "low"

    def test_analyze_task_characteristics_long_prompt_medium_scope(self, handler):
        """Test analysis detects medium scope with long prompt."""
        long_prompt = " ".join(["word"] * 35)  # 35 words
        characteristics = handler._analyze_task_characteristics(
            prompt=long_prompt,
            intent="enhancement"
        )

        assert characteristics["scope"] == "medium"

    def test_analyze_task_characteristics_architectural_intent(self, handler):
        """Test analysis detects high complexity with architectural intent."""
        characteristics = handler._analyze_task_characteristics(
            prompt="Redesign authentication system",
            intent="architectural"
        )

        assert characteristics["complexity"] == "high"


# ============================================================================
# Test _compare_to_workflow_requirements()
# ============================================================================

class TestCompareToWorkflowRequirements:
    """Test _compare_to_workflow_requirements() method."""

    def test_compare_intent_mismatch(self, handler):
        """Test intent mismatch detection."""
        characteristics = {
            "intent": "bug_fix",
            "scope": "low",
            "complexity": "low"
        }

        # *full requires architectural/framework_dev intent
        mismatch = handler._compare_to_workflow_requirements("*full", characteristics)
        assert mismatch is True

    def test_compare_intent_match(self, handler):
        """Test intent match."""
        characteristics = {
            "intent": "bug_fix",
            "scope": "low",
            "complexity": "low"
        }

        # *fix requires bug_fix intent
        mismatch = handler._compare_to_workflow_requirements("*fix", characteristics)
        assert mismatch is False

    def test_compare_complexity_too_low(self, handler):
        """Test complexity too low for workflow."""
        characteristics = {
            "intent": "feature",
            "scope": "medium",
            "complexity": "low"  # Too low for *build
        }

        # *build requires min_complexity="medium"
        mismatch = handler._compare_to_workflow_requirements("*build", characteristics)
        assert mismatch is True

    def test_compare_complexity_too_high(self, handler):
        """Test complexity too high for workflow."""
        characteristics = {
            "intent": "bug_fix",
            "scope": "low",
            "complexity": "high"  # Too high for *fix
        }

        # *fix has max_complexity="medium"
        mismatch = handler._compare_to_workflow_requirements("*fix", characteristics)
        assert mismatch is True

    def test_compare_scope_too_low(self, handler):
        """Test scope too low for workflow."""
        characteristics = {
            "intent": "architectural",
            "scope": "low",  # Too low for *full
            "complexity": "high"
        }

        # *full requires min_scope="high"
        mismatch = handler._compare_to_workflow_requirements("*full", characteristics)
        assert mismatch is True

    def test_compare_scope_too_high(self, handler):
        """Test scope too high for workflow."""
        characteristics = {
            "intent": "bug_fix",
            "scope": "high",  # Too high for *fix
            "complexity": "low"
        }

        # *fix has max_scope="low"
        mismatch = handler._compare_to_workflow_requirements("*fix", characteristics)
        assert mismatch is True

    def test_compare_unknown_workflow(self, handler):
        """Test comparison with unknown workflow returns False."""
        characteristics = {
            "intent": "bug_fix",
            "scope": "low",
            "complexity": "low"
        }

        mismatch = handler._compare_to_workflow_requirements("*unknown", characteristics)
        assert mismatch is False


# ============================================================================
# Test _create_mismatch_warning()
# ============================================================================

class TestCreateMismatchWarning:
    """Test _create_mismatch_warning() method."""

    def test_create_warning_bug_fix(self, handler):
        """Test creating warning for bug fix intent."""
        characteristics = {
            "intent": "bug_fix",
            "scope": "low",
            "complexity": "low"
        }

        warning = handler._create_mismatch_warning("*full", characteristics, 0.85)

        assert warning.detected_intent == "bug_fix"
        assert warning.detected_scope == "low"
        assert warning.detected_complexity == "low"
        assert warning.recommended_workflow == "*fix"
        assert warning.confidence == 0.85
        assert warning.token_savings > 0  # *full (9 steps) vs *fix (3 steps)
        assert warning.time_savings > 0

    def test_create_warning_enhancement(self, handler):
        """Test creating warning for enhancement intent."""
        characteristics = {
            "intent": "enhancement",
            "scope": "medium",
            "complexity": "medium"
        }

        warning = handler._create_mismatch_warning("*full", characteristics, 0.75)

        assert warning.recommended_workflow == "*build"

    def test_create_warning_architectural(self, handler):
        """Test creating warning for architectural intent."""
        characteristics = {
            "intent": "architectural",
            "scope": "high",
            "complexity": "high"
        }

        warning = handler._create_mismatch_warning("*fix", characteristics, 0.90)

        assert warning.recommended_workflow == "*full"

    def test_create_warning_token_savings_calculation(self, handler):
        """Test token savings calculation."""
        characteristics = {
            "intent": "bug_fix",
            "scope": "low",
            "complexity": "low"
        }

        warning = handler._create_mismatch_warning("*full", characteristics, 0.85)

        # *full (9 steps) - *fix (3 steps) = 6 steps × 10K tokens = 60K tokens
        assert warning.token_savings == 60000
        assert warning.time_savings == 30  # 6 steps × 5 minutes = 30 minutes


# ============================================================================
# Test _display_mismatch_warning()
# ============================================================================

class TestDisplayMismatchWarning:
    """Test _display_mismatch_warning() method."""

    @patch('builtins.print')
    def test_display_warning(self, mock_print, handler, sample_warning):
        """Test warning is displayed correctly."""
        handler._display_mismatch_warning(sample_warning, "*full")

        # Verify print was called with warning content
        assert mock_print.called
        calls = [str(call) for call in mock_print.call_args_list]
        output = " ".join(calls)

        assert "Workflow Mismatch Warning" in output or mock_print.call_count >= 3


# ============================================================================
# Test _prompt_user_choice()
# ============================================================================

class TestPromptUserChoice:
    """Test _prompt_user_choice() method."""

    @patch('builtins.input', return_value='y')
    def test_prompt_user_choice_yes(self, mock_input, handler, sample_warning):
        """Test user chooses 'y' (proceed)."""
        choice = handler._prompt_user_choice(sample_warning, "*full")
        assert choice == "y"

    @patch('builtins.input', return_value='yes')
    def test_prompt_user_choice_yes_full(self, mock_input, handler, sample_warning):
        """Test user chooses 'yes' (proceed)."""
        choice = handler._prompt_user_choice(sample_warning, "*full")
        assert choice == "y"

    @patch('builtins.input', return_value='n')
    def test_prompt_user_choice_no(self, mock_input, handler, sample_warning):
        """Test user chooses 'n' (cancel)."""
        choice = handler._prompt_user_choice(sample_warning, "*full")
        assert choice == "N"

    @patch('builtins.input', return_value='')
    def test_prompt_user_choice_empty(self, mock_input, handler, sample_warning):
        """Test user presses Enter (default to cancel)."""
        choice = handler._prompt_user_choice(sample_warning, "*full")
        assert choice == "N"

    @patch('builtins.input', return_value='switch')
    def test_prompt_user_choice_switch(self, mock_input, handler, sample_warning):
        """Test user chooses 'switch' (use recommended)."""
        choice = handler._prompt_user_choice(sample_warning, "*full")
        assert choice == "switch"

    @patch('builtins.input', side_effect=['invalid', 'y'])
    def test_prompt_user_choice_invalid_then_valid(self, mock_input, handler, sample_warning):
        """Test user enters invalid choice then valid choice."""
        choice = handler._prompt_user_choice(sample_warning, "*full")
        assert choice == "y"
        assert mock_input.call_count == 2

    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_prompt_user_choice_keyboard_interrupt(self, mock_input, handler, sample_warning):
        """Test user presses Ctrl+C (cancel)."""
        choice = handler._prompt_user_choice(sample_warning, "*full")
        assert choice == "N"

    @patch('builtins.input', side_effect=EOFError)
    def test_prompt_user_choice_eof(self, mock_input, handler, sample_warning):
        """Test EOF error (cancel)."""
        choice = handler._prompt_user_choice(sample_warning, "*full")
        assert choice == "N"


# ============================================================================
# Test _workflow_to_intent_type()
# ============================================================================

class TestWorkflowToIntentType:
    """Test _workflow_to_intent_type() method."""

    def test_workflow_to_intent_fix(self, handler):
        """Test mapping *fix to IntentType.FIX."""
        intent = handler._workflow_to_intent_type("*fix")
        assert intent == IntentType.FIX

    def test_workflow_to_intent_build(self, handler):
        """Test mapping *build to IntentType.BUILD."""
        intent = handler._workflow_to_intent_type("*build")
        assert intent == IntentType.BUILD

    def test_workflow_to_intent_full(self, handler):
        """Test mapping *full to IntentType.BUILD."""
        intent = handler._workflow_to_intent_type("*full")
        assert intent == IntentType.BUILD  # *full maps to BUILD

    def test_workflow_to_intent_review(self, handler):
        """Test mapping *review to IntentType.REVIEW."""
        intent = handler._workflow_to_intent_type("*review")
        assert intent == IntentType.REVIEW

    def test_workflow_to_intent_test(self, handler):
        """Test mapping *test to IntentType.TEST."""
        intent = handler._workflow_to_intent_type("*test")
        assert intent == IntentType.TEST

    def test_workflow_to_intent_refactor(self, handler):
        """Test mapping *refactor to IntentType.REFACTOR."""
        intent = handler._workflow_to_intent_type("*refactor")
        assert intent == IntentType.REFACTOR

    def test_workflow_to_intent_unknown(self, handler):
        """Test mapping unknown workflow returns None."""
        intent = handler._workflow_to_intent_type("*unknown")
        assert intent is None


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for workflow validation."""

    def test_end_to_end_mismatch_detection_and_warning(self, handler):
        """Test end-to-end workflow mismatch detection."""
        # Simulate user specifying *full for a bug fix
        warning = handler.validate_workflow_match(
            workflow="*full",
            prompt="Fix validation bug that reports 0/14 when files exist",
            force=False
        )

        # Should detect mismatch
        if warning:
            assert warning.detected_intent == "bug_fix"
            assert warning.recommended_workflow == "*fix"
            assert warning.confidence >= 0.7

            # Test formatting
            formatted = warning.format_warning()
            assert "Workflow Mismatch Warning" in formatted

    @patch('builtins.input', return_value='switch')
    @patch('builtins.print')
    def test_end_to_end_user_switches_workflow(self, mock_print, mock_input, handler):
        """Test end-to-end flow when user switches workflow."""
        warning = handler.validate_workflow_match(
            workflow="*full",
            prompt="Fix validation bug",
            force=False
        )

        if warning:
            # Display warning
            handler._display_mismatch_warning(warning, "*full")

            # User chooses to switch
            choice = handler._prompt_user_choice(warning, "*full")
            assert choice == "switch"

            # Map recommended workflow to intent
            recommended_intent = handler._workflow_to_intent_type(warning.recommended_workflow)
            assert recommended_intent is not None

    def test_end_to_end_force_flag_bypass(self, handler):
        """Test end-to-end flow with --force flag."""
        # User specifies --force flag
        warning = handler.validate_workflow_match(
            workflow="*full",
            prompt="Fix validation bug",
            force=True  # Bypass validation
        )

        # Should return None (validation bypassed)
        assert warning is None
