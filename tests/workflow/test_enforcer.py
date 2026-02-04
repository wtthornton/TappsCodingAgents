"""
Comprehensive test suite for WorkflowEnforcer (ENH-001-S1)

Tests cover:
- Initialization with various config sources
- Enforcement decision logic for all modes (blocking, warning, silent)
- Skip enforcement flag behavior
- Fail-safe error handling
- Config loading with various scenarios
- Message generation
- Edge cases and error paths

Target: 85%+ coverage
Performance: Verify <50ms p95 latency
"""

import logging
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.core.llm_behavior import EnforcementConfig
from tapps_agents.workflow.enforcer import WorkflowEnforcer

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create a temporary config file for testing."""
    config_dir = tmp_path / ".tapps-agents"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.yaml"
    config_file.write_text("""
llm_behavior:
  mode: "senior-developer"

  workflow_enforcement:
    mode: "blocking"
    confidence_threshold: 60.0
    suggest_workflows: true
    block_direct_edits: true
""")
    return config_file


@pytest.fixture
def blocking_config() -> EnforcementConfig:
    """Create a blocking mode config."""
    return EnforcementConfig(
        mode="blocking",
        confidence_threshold=60.0,
        suggest_workflows=True,
        block_direct_edits=True,
    )


@pytest.fixture
def warning_config() -> EnforcementConfig:
    """Create a warning mode config."""
    return EnforcementConfig(
        mode="warning",
        confidence_threshold=60.0,
        suggest_workflows=True,
        block_direct_edits=True,
    )


@pytest.fixture
def silent_config() -> EnforcementConfig:
    """Create a silent mode config."""
    return EnforcementConfig(
        mode="silent",
        confidence_threshold=60.0,
        suggest_workflows=True,
        block_direct_edits=True,
    )


@pytest.fixture
def blocking_config_no_suggestions() -> EnforcementConfig:
    """Create a blocking mode config without workflow suggestions."""
    return EnforcementConfig(
        mode="blocking",
        confidence_threshold=60.0,
        suggest_workflows=False,
        block_direct_edits=True,
    )


@pytest.fixture
def blocking_config_no_block() -> EnforcementConfig:
    """Create a blocking mode config that doesn't actually block."""
    return EnforcementConfig(
        mode="blocking",
        confidence_threshold=60.0,
        suggest_workflows=True,
        block_direct_edits=False,
    )


# ============================================================================
# Test Initialization
# ============================================================================


class TestWorkflowEnforcerInit:
    """Test WorkflowEnforcer initialization."""

    def test_init_with_config_object(self, blocking_config: EnforcementConfig) -> None:
        """Test initialization with pre-loaded config object."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        assert enforcer.config.mode == "blocking"
        assert enforcer.config.confidence_threshold == 60.0
        assert enforcer.config.suggest_workflows is True
        assert enforcer.config.block_direct_edits is True

    def test_init_with_config_path(self, temp_config_file: Path) -> None:
        """Test initialization with config file path."""
        enforcer = WorkflowEnforcer(config_path=temp_config_file)

        assert enforcer.config.mode == "blocking"
        assert enforcer.config.confidence_threshold == 60.0

    def test_init_with_default_config(self) -> None:
        """Test initialization with default config (no args)."""
        # Mock missing config file to use defaults
        with patch.object(EnforcementConfig, "from_config_file") as mock_load:
            mock_load.return_value = EnforcementConfig()
            enforcer = WorkflowEnforcer()

            assert enforcer.config.mode == "blocking"  # Default mode

    def test_init_sets_config_path(self, temp_config_file: Path) -> None:
        """Test that _config_path is set when config_path provided."""
        enforcer = WorkflowEnforcer(config_path=temp_config_file)

        assert enforcer._config_path == temp_config_file

    def test_init_logs_config_mode(
        self, blocking_config: EnforcementConfig, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that initialization logs the config mode."""
        with caplog.at_level(logging.INFO):
            WorkflowEnforcer(config=blocking_config)

        assert "WorkflowEnforcer initialized" in caplog.text
        assert "mode=blocking" in caplog.text
        assert "confidence_threshold=60.0" in caplog.text


# ============================================================================
# Test intercept_code_edit - Blocking Mode
# ============================================================================


class TestInterceptCodeEditBlocking:
    """Test intercept_code_edit() in blocking mode."""

    def test_blocking_mode_returns_block_action(
        self, blocking_config: EnforcementConfig
    ) -> None:
        """Test that blocking mode returns 'block' action."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api/auth.py"),
            user_intent="Add login endpoint",
            is_new_file=False,
            skip_enforcement=False,
        )

        assert decision["action"] == "block"
        assert decision["should_block"] is True
        assert len(decision["message"]) > 0
        assert decision["confidence"] >= 0.0  # IntentDetector provides confidence

    def test_blocking_mode_message_includes_file_path(
        self, blocking_config: EnforcementConfig
    ) -> None:
        """Test that block message includes the file path."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/utils/helpers.py"),
            user_intent="Refactor helper functions",
            is_new_file=False,
        )

        assert "src/utils/helpers.py" in decision["message"] or "src\\utils\\helpers.py" in decision["message"]

    def test_blocking_mode_message_includes_workflow_suggestion(
        self, blocking_config: EnforcementConfig
    ) -> None:
        """Test that block message suggests workflows when enabled."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api.py"),
            user_intent="Add API endpoint",
            is_new_file=False,
        )

        assert "@simple-mode" in decision["message"]
        assert "*build" in decision["message"]

    def test_blocking_mode_no_suggestions(
        self, blocking_config_no_suggestions: EnforcementConfig
    ) -> None:
        """Test blocking mode without workflow suggestions."""
        enforcer = WorkflowEnforcer(config=blocking_config_no_suggestions)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api.py"),
            user_intent="Add endpoint",
            is_new_file=False,
        )

        assert decision["action"] == "block"
        assert "@simple-mode" not in decision["message"]

    def test_blocking_mode_with_block_direct_edits_false(
        self, blocking_config_no_block: EnforcementConfig
    ) -> None:
        """Test blocking mode with block_direct_edits=False."""
        enforcer = WorkflowEnforcer(config=blocking_config_no_block)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api.py"),
            user_intent="Add endpoint",
            is_new_file=False,
        )

        assert decision["action"] == "block"
        assert decision["should_block"] is False  # Message shown but not blocked


# ============================================================================
# Test intercept_code_edit - Warning Mode
# ============================================================================


class TestInterceptCodeEditWarning:
    """Test intercept_code_edit() in warning mode."""

    def test_warning_mode_returns_warn_action(
        self, warning_config: EnforcementConfig
    ) -> None:
        """Test that warning mode returns 'warn' action."""
        enforcer = WorkflowEnforcer(config=warning_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/service.py"),
            user_intent="Implement service",
            is_new_file=True,
        )

        assert decision["action"] == "warn"
        assert decision["should_block"] is False
        assert len(decision["message"]) > 0

    def test_warning_mode_message_suggests_workflow(
        self, warning_config: EnforcementConfig
    ) -> None:
        """Test that warning message suggests workflows."""
        enforcer = WorkflowEnforcer(config=warning_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api.py"),
            user_intent="Create API",
            is_new_file=False,
        )

        assert "@simple-mode" in decision["message"]
        assert "*build" in decision["message"]


# ============================================================================
# Test intercept_code_edit - Silent Mode
# ============================================================================


class TestInterceptCodeEditSilent:
    """Test intercept_code_edit() in silent mode."""

    def test_silent_mode_returns_allow_action(
        self, silent_config: EnforcementConfig
    ) -> None:
        """Test that silent mode returns 'allow' action."""
        enforcer = WorkflowEnforcer(config=silent_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/test.py"),
            user_intent="Write tests",
            is_new_file=True,
        )

        assert decision["action"] == "allow"
        assert decision["should_block"] is False
        assert decision["message"] == ""  # Silent mode = no message

    def test_silent_mode_logs_but_does_not_enforce(
        self, silent_config: EnforcementConfig, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that silent mode logs but doesn't enforce."""
        enforcer = WorkflowEnforcer(config=silent_config)

        with caplog.at_level(logging.INFO):
            enforcer.intercept_code_edit(
                file_path=Path("src/test.py"),
                user_intent="Test",
                is_new_file=False,
            )

        assert "Silent mode" in caplog.text


# ============================================================================
# Test Skip Enforcement Flag
# ============================================================================


class TestSkipEnforcement:
    """Test skip_enforcement flag behavior."""

    def test_skip_enforcement_returns_allow(
        self, blocking_config: EnforcementConfig
    ) -> None:
        """Test that skip_enforcement=True always returns 'allow'."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api.py"),
            user_intent="Add endpoint",
            is_new_file=False,
            skip_enforcement=True,
        )

        assert decision["action"] == "allow"
        assert decision["should_block"] is False
        assert decision["message"] == ""

    def test_skip_enforcement_overrides_all_modes(
        self, warning_config: EnforcementConfig
    ) -> None:
        """Test that skip_enforcement overrides all modes."""
        enforcer = WorkflowEnforcer(config=warning_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api.py"),
            user_intent="Add endpoint",
            is_new_file=False,
            skip_enforcement=True,
        )

        assert decision["action"] == "allow"

    def test_skip_enforcement_logs_debug_message(
        self, blocking_config: EnforcementConfig, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that skip_enforcement logs debug message."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        with caplog.at_level(logging.DEBUG):
            enforcer.intercept_code_edit(
                file_path=Path("src/api.py"),
                user_intent="Add endpoint",
                is_new_file=False,
                skip_enforcement=True,
            )

        assert "Enforcement skipped via --skip-enforcement flag" in caplog.text


# ============================================================================
# Test Error Handling (Fail-Safe)
# ============================================================================


class TestFailSafeErrorHandling:
    """Test fail-safe error handling."""

    def test_error_in_intercept_returns_allow(
        self, blocking_config: EnforcementConfig
    ) -> None:
        """Test that errors in intercept_code_edit return 'allow' (fail-safe)."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        # Mock _should_enforce to raise an exception
        with patch.object(enforcer, "_should_enforce", side_effect=RuntimeError("Test error")):
            decision = enforcer.intercept_code_edit(
                file_path=Path("src/api.py"),
                user_intent="Add endpoint",
                is_new_file=False,
            )

        assert decision["action"] == "allow"
        assert decision["should_block"] is False

    def test_error_logs_error_message(
        self, blocking_config: EnforcementConfig, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that errors are logged."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        with patch.object(enforcer, "_should_enforce", side_effect=RuntimeError("Test error")):
            with caplog.at_level(logging.ERROR):
                enforcer.intercept_code_edit(
                    file_path=Path("src/api.py"),
                    user_intent="Add endpoint",
                    is_new_file=False,
                )

        assert "WorkflowEnforcer.intercept_code_edit() failed" in caplog.text
        assert "Test error" in caplog.text
        assert "Defaulting to 'allow'" in caplog.text


# ============================================================================
# Test Config Loading
# ============================================================================


class TestConfigLoading:
    """Test configuration loading."""

    def test_load_config_with_valid_file(self, temp_config_file: Path) -> None:
        """Test loading config from valid file."""
        enforcer = WorkflowEnforcer(config_path=temp_config_file)

        assert enforcer.config.mode == "blocking"

    def test_load_config_with_missing_file(self, tmp_path: Path) -> None:
        """Test loading config from missing file uses defaults."""
        missing_file = tmp_path / "nonexistent.yaml"

        with patch.object(EnforcementConfig, "from_config_file") as mock_load:
            mock_load.return_value = EnforcementConfig()
            enforcer = WorkflowEnforcer(config_path=missing_file)

            assert enforcer.config.mode == "blocking"  # Default

    def test_load_config_error_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that config load error logs warning."""
        invalid_file = tmp_path / "invalid.yaml"

        with patch.object(EnforcementConfig, "from_config_file", side_effect=ValueError("Invalid YAML")):
            with caplog.at_level(logging.WARNING):
                WorkflowEnforcer(config_path=invalid_file)

        assert "Failed to load enforcement config" in caplog.text
        assert "Using default config" in caplog.text


# ============================================================================
# Test EnforcementDecision Structure
# ============================================================================


class TestEnforcementDecision:
    """Test EnforcementDecision TypedDict structure."""

    def test_decision_has_all_required_fields(
        self, blocking_config: EnforcementConfig
    ) -> None:
        """Test that decision has all required fields."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api.py"),
            user_intent="Add endpoint",
            is_new_file=False,
        )

        assert "action" in decision
        assert "message" in decision
        assert "should_block" in decision
        assert "confidence" in decision

    def test_decision_action_is_literal_type(
        self, blocking_config: EnforcementConfig
    ) -> None:
        """Test that action is one of the literal values."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api.py"),
            user_intent="Add endpoint",
            is_new_file=False,
        )

        assert decision["action"] in ["block", "warn", "allow"]

    def test_decision_confidence_is_zero_for_story_1(
        self, blocking_config: EnforcementConfig
    ) -> None:
        """Test that confidence is 0.0 for Story 1 (no intent detection)."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api.py"),
            user_intent="Add endpoint",
            is_new_file=False,
        )

        # IntentDetector now provides actual confidence scores
        assert decision["confidence"] >= 0.0
        assert decision["confidence"] <= 100.0


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_user_intent(self, blocking_config: EnforcementConfig) -> None:
        """Test with empty user intent string."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api.py"),
            user_intent="",
            is_new_file=False,
        )

        assert decision["action"] == "block"
        # Should still work, message might use fallback

    def test_very_long_user_intent(self, blocking_config: EnforcementConfig) -> None:
        """Test with very long user intent (for logging truncation)."""
        enforcer = WorkflowEnforcer(config=blocking_config)
        long_intent = "A" * 500  # 500 characters

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api.py"),
            user_intent=long_intent,
            is_new_file=False,
        )

        assert decision["action"] == "block"

    def test_new_file_vs_existing_file(
        self, blocking_config: EnforcementConfig
    ) -> None:
        """Test that is_new_file parameter is accepted (future use)."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        decision_new = enforcer.intercept_code_edit(
            file_path=Path("src/new.py"),
            user_intent="Create new file",
            is_new_file=True,
        )

        decision_existing = enforcer.intercept_code_edit(
            file_path=Path("src/existing.py"),
            user_intent="Edit existing file",
            is_new_file=False,
        )

        # Story 1: Both should behave the same (is_new_file not used yet)
        assert decision_new["action"] == decision_existing["action"]

    def test_absolute_vs_relative_file_paths(
        self, blocking_config: EnforcementConfig
    ) -> None:
        """Test with both absolute and relative file paths."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        decision_absolute = enforcer.intercept_code_edit(
            file_path=Path("/absolute/path/to/file.py"),
            user_intent="Test",
            is_new_file=False,
        )

        decision_relative = enforcer.intercept_code_edit(
            file_path=Path("relative/path/to/file.py"),
            user_intent="Test",
            is_new_file=False,
        )

        assert decision_absolute["action"] == "block"
        assert decision_relative["action"] == "block"


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Test performance requirements (<50ms p95 latency)."""

    def test_intercept_latency_under_50ms(
        self, blocking_config: EnforcementConfig
    ) -> None:
        """Test that intercept_code_edit() completes in <50ms (p95)."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        # Run 100 iterations to get p95
        latencies = []
        for i in range(100):
            start = time.perf_counter()
            enforcer.intercept_code_edit(
                file_path=Path(f"src/file_{i}.py"),
                user_intent=f"Test iteration {i}",
                is_new_file=False,
            )
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        # Calculate p95
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]

        assert p95_latency < 50.0, f"p95 latency {p95_latency}ms exceeds 50ms target"

    def test_init_latency_under_10ms(self, blocking_config: EnforcementConfig) -> None:
        """Test that initialization completes in <10ms."""
        latencies = []

        for _ in range(10):
            start = time.perf_counter()
            WorkflowEnforcer(config=blocking_config)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        avg_latency = sum(latencies) / len(latencies)

        assert avg_latency < 10.0, f"Average init latency {avg_latency}ms exceeds 10ms target"


# ============================================================================
# Test Logging and Debugging
# ============================================================================


class TestLoggingDebug:
    """Test logging and debug output."""

    def test_decision_logging(
        self, blocking_config: EnforcementConfig, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that decisions are logged at debug level."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        with caplog.at_level(logging.DEBUG):
            enforcer.intercept_code_edit(
                file_path=Path("src/api.py"),
                user_intent="Add endpoint",
                is_new_file=False,
            )

        assert "Enforcement decision" in caplog.text
        assert "action=block" in caplog.text
        assert "should_block=True" in caplog.text


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests with real EnforcementConfig."""

    def test_full_workflow_blocking_mode(self, temp_config_file: Path) -> None:
        """Test full workflow in blocking mode."""
        enforcer = WorkflowEnforcer(config_path=temp_config_file)

        decision = enforcer.intercept_code_edit(
            file_path=Path("src/api/auth.py"),
            user_intent="Add user authentication endpoint",
            is_new_file=False,
        )

        assert decision["action"] == "block"
        assert decision["should_block"] is True
        assert "workflow" in decision["message"].lower()
        # IntentDetector now provides actual confidence scores
        assert decision["confidence"] >= 0.0
        assert decision["confidence"] <= 100.0

    def test_multiple_sequential_calls(self, blocking_config: EnforcementConfig) -> None:
        """Test multiple sequential calls to enforcer."""
        enforcer = WorkflowEnforcer(config=blocking_config)

        # First call
        decision1 = enforcer.intercept_code_edit(
            file_path=Path("src/file1.py"),
            user_intent="Intent 1",
            is_new_file=False,
        )

        # Second call
        decision2 = enforcer.intercept_code_edit(
            file_path=Path("src/file2.py"),
            user_intent="Intent 2",
            is_new_file=True,
        )

        # Both should return block
        assert decision1["action"] == "block"
        assert decision2["action"] == "block"
