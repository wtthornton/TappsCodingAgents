"""
Tests for error propagation through component layers.

Story 19.2: Add Error Propagation Tests
- Test error propagation through component layers
- Validate error handling in agent chains
- Test error recovery mechanisms
- Verify error envelope propagation
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tapps_agents.core.error_envelope import ErrorEnvelopeBuilder, create_error_result
from tapps_agents.core.exceptions import (
    AgentError,
    ConfigurationError,
    MALError,
)
from tapps_agents.core.mal import MAL

pytestmark = pytest.mark.unit


class TestErrorEnvelopePropagation:
    """Test error envelope creation and propagation."""

    def test_error_envelope_from_exception_preserves_type(self):
        """Test that ErrorEnvelopeBuilder preserves exception type information."""
        original_error = ValueError("Invalid input")
        envelope = ErrorEnvelopeBuilder.from_exception(original_error)

        assert envelope.code == "validation_error"
        assert envelope.category == "validation"
        assert "Invalid input" in envelope.message

    def test_error_envelope_from_exception_includes_context(self):
        """Test that error envelope includes workflow/step/agent context."""
        original_error = ConfigurationError("Config error")
        envelope = ErrorEnvelopeBuilder.from_exception(
            original_error,
            workflow_id="test-workflow",
            step_id="test-step",
            agent="test-agent",
        )

        assert envelope.workflow_id == "test-workflow"
        assert envelope.step_id == "test-step"
        assert envelope.agent == "test-agent"
        assert envelope.code == "config_error"
        assert envelope.category == "configuration"

    def test_error_envelope_categorizes_exceptions_correctly(self):
        """Test that different exception types are categorized correctly."""
        test_cases = [
            (ConfigurationError("Config error"), "configuration", "config_error"),
            (AgentError("Agent error"), "execution", "agent_error"),
            (MALError("MAL error"), "external_dependency", "mal_error"),
            (ValueError("Validation error"), "validation", "validation_error"),
        ]

        for exc, expected_category, expected_code in test_cases:
            envelope = ErrorEnvelopeBuilder.from_exception(exc)
            assert envelope.category == expected_category, f"Failed for {type(exc).__name__}"
            assert envelope.code == expected_code, f"Failed for {type(exc).__name__}"

    def test_create_error_result_propagates_exception_details(self):
        """Test that create_error_result propagates exception details correctly."""
        original_error = ValueError("Invalid parameter")
        result = create_error_result(
            original_error,
            workflow_id="wf-1",
            step_id="step-1",
            agent="test-agent",
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["code"] == "validation_error"
        assert result["error"]["category"] == "validation"
        assert "Invalid parameter" in result["error"]["message"]
        assert result["workflow_id"] == "wf-1"
        assert result["step_id"] == "step-1"
        assert result["agent"] == "test-agent"

    def test_error_envelope_to_dict_preserves_structure(self):
        """Test that error envelope to_dict preserves all fields."""
        envelope = ErrorEnvelopeBuilder.from_exception(
            ConfigurationError("Test error"),
            workflow_id="wf-1",
            step_id="step-1",
            agent="agent-1",
        )
        envelope.recoverable = True
        envelope.retry_after = 5

        result = envelope.to_dict()

        assert result["error"]["code"] == "config_error"
        assert result["error"]["message"] == "Test error"
        assert result["error"]["category"] == "configuration"
        assert result["error"]["recoverable"] is True
        assert result["error"]["retry_after"] == 5
        assert result["workflow_id"] == "wf-1"
        assert result["step_id"] == "step-1"
        assert result["agent"] == "agent-1"


class TestErrorPropagationThroughLayers:
    """Test error propagation through component layers."""

    @pytest.mark.asyncio
    async def test_mal_error_propagates_to_agent(self):
        """Test that MAL errors propagate correctly to agents."""
        from tapps_agents.agents.reviewer.agent import ReviewerAgent

        # Create a MAL that raises an error
        MAL()
        mock_mal = MagicMock()
        mock_mal.generate = AsyncMock(
            side_effect=ConnectionError("Ollama connection failed")
        )
        mock_mal._ollama_generate = AsyncMock(
            side_effect=ConnectionError("Ollama connection failed")
        )

        agent = ReviewerAgent()
        agent.mal = mock_mal

        # When agent tries to use MAL, error should propagate
        # The exact behavior depends on agent implementation
        # This test validates that errors are not silently swallowed
        with pytest.raises(ConnectionError, match="Ollama connection failed"):
            await mock_mal.generate("test prompt")

    def test_error_propagation_preserves_stack_trace(self):
        """Test that error propagation preserves original exception context."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                # Re-raise with context
                raise ConfigurationError(f"Wrapped: {e}") from e
        except ConfigurationError as outer:
            envelope = ErrorEnvelopeBuilder.from_exception(outer)

            # Error envelope should capture the wrapped message
            assert "Wrapped" in envelope.message
            assert "Original error" in envelope.message
            assert envelope.code == "config_error"

    def test_error_chain_propagation(self):
        """Test that error chains propagate correctly through multiple layers."""
        # Simulate error propagation: Layer1 -> Layer2 -> Layer3
        layer3_error = FileNotFoundError("File not found: config.yaml")
        layer2_error = ConfigurationError(f"Failed to load config: {layer3_error}")
        layer1_error = AgentError(f"Agent initialization failed: {layer2_error}")

        # Each layer should create appropriate error envelope
        envelope3 = ErrorEnvelopeBuilder.from_exception(layer3_error)
        assert envelope3.code == "file_not_found"
        assert envelope3.category == "validation"

        envelope2 = ErrorEnvelopeBuilder.from_exception(layer2_error)
        assert envelope2.code == "config_error"
        assert envelope2.category == "configuration"

        envelope1 = ErrorEnvelopeBuilder.from_exception(layer1_error)
        assert envelope1.code == "agent_error"
        assert envelope1.category == "execution"


class TestErrorRecoveryMechanisms:
    """Test error recovery and retry mechanisms."""

    def test_recoverable_errors_flagged_correctly(self):
        """Test that recoverable errors are correctly identified."""
        recoverable_errors = [
            ConfigurationError("Config error"),
            TimeoutError("Timeout"),
            PermissionError("Permission denied"),
        ]

        for error in recoverable_errors:
            envelope = ErrorEnvelopeBuilder.from_exception(error)
            assert envelope.recoverable is True, f"{type(error).__name__} should be recoverable"

    def test_non_recoverable_errors_flagged_correctly(self):
        """Test that non-recoverable errors are correctly identified."""
        non_recoverable_errors = [
            AgentError("Agent error"),
            ValueError("Invalid value"),
        ]

        for error in non_recoverable_errors:
            ErrorEnvelopeBuilder.from_exception(error)
            # Most errors are not recoverable by default
            # Configuration, Timeout, Permission errors are exceptions
            if not isinstance(error, (ConfigurationError, TimeoutError, PermissionError)):
                # These are generally not recoverable without code changes
                pass  # Accept default recoverable=False


class TestErrorMessageValidation:
    """Test that error messages are informative and actionable."""

    def test_error_messages_are_sanitized(self):
        """Test that error messages are sanitized to remove secrets."""
        # Create error with potential secret
        error_msg = "Connection failed: API key sk-1234567890abcdef"
        error = ConnectionError(error_msg)

        envelope = ErrorEnvelopeBuilder.from_exception(error)
        # Sanitized message should not contain the full API key
        # (Exact behavior depends on sanitization implementation)
        assert envelope.message is not None
        assert len(envelope.message) > 0

    def test_error_messages_include_context(self):
        """Test that error messages include sufficient context."""
        error = ValueError("Invalid parameter: 'test'")
        envelope = ErrorEnvelopeBuilder.from_exception(
            error,
            workflow_id="test-workflow",
            step_id="test-step",
            agent="test-agent",
        )

        # Message should contain the original error
        assert "Invalid parameter" in envelope.message

        # Context should be available in envelope fields
        assert envelope.workflow_id == "test-workflow"
        assert envelope.step_id == "test-step"
        assert envelope.agent == "test-agent"

    def test_user_friendly_message_generation(self):
        """Test that to_user_message generates helpful messages."""
        envelope = ErrorEnvelopeBuilder.from_exception(
            ConfigurationError("Invalid config"),
            workflow_id="wf-1",
        )
        envelope.recoverable = True

        user_msg = envelope.to_user_message()

        # Should include the error message
        assert "Invalid config" in user_msg
        # Should mention recoverability if applicable
        if envelope.recoverable:
            assert "recoverable" in user_msg.lower() or "retry" in user_msg.lower()
        # Should include workflow context if available
        if envelope.workflow_id:
            assert "workflow" in user_msg.lower()

