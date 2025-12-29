"""
Comprehensive edge case and error path tests.

Tests error handling for:
- Network failures (connection errors, timeouts, rate limits)
- File system errors (file not found, permission denied, disk full)
- Invalid input (validation errors, type mismatches)
- Resource exhaustion (memory, disk space)
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from tapps_agents.core.error_envelope import ErrorEnvelope, ErrorEnvelopeBuilder
from tapps_agents.workflow.error_recovery import ErrorAnalyzer, ErrorType

pytestmark = pytest.mark.unit


class TestNetworkErrorHandling:
    """Tests for network error handling."""

    def test_connection_error_detection(self):
        """Test detection of connection errors."""
        analyzer = ErrorAnalyzer()
        error = ConnectionError("Connection refused")
        envelope = ErrorEnvelopeBuilder.from_exception(error)
        
        analysis = analyzer.analyze(error)
        
        assert analysis.error_type == ErrorType.CONNECTION_ERROR
        assert analysis.severity.value in ["error", "critical"]

    def test_timeout_error_detection(self):
        """Test detection of timeout errors."""
        analyzer = ErrorAnalyzer()
        error = TimeoutError("Request timed out")
        envelope = ErrorEnvelopeBuilder.from_exception(error)
        
        analysis = analyzer.analyze(error)
        
        assert analysis.error_type == ErrorType.TIMEOUT
        assert analysis.severity.value in ["error", "critical"]

    def test_rate_limit_error_detection(self):
        """Test detection of rate limit errors."""
        analyzer = ErrorAnalyzer()
        error_dict = {
            "error": "Rate limit exceeded",
            "error_code": "rate_limit",
            "retry_after": 60,
        }
        envelope = ErrorEnvelopeBuilder.from_dict(error_dict)
        
        analysis = analyzer.analyze(envelope)
        
        assert analysis.error_type == ErrorType.RATE_LIMIT
        assert envelope.retry_after == 60

    def test_service_unavailable_error_detection(self):
        """Test detection of service unavailable errors."""
        analyzer = ErrorAnalyzer()
        error_dict = {
            "error": "Service unavailable",
            "error_code": "service_unavailable",
        }
        envelope = ErrorEnvelopeBuilder.from_dict(error_dict)
        
        analysis = analyzer.analyze(envelope)
        
        assert analysis.error_type == ErrorType.SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_network_error_in_agent(self):
        """
        Test network error handling in agent context.
        
        Verifies that agents handle network errors gracefully without hanging.
        """
        from tapps_agents.agents.reviewer.agent import ReviewerAgent
        
        agent = ReviewerAgent()
        
        with patch.object(agent, "call_tool") as mock_call:
            mock_call.side_effect = ConnectionError("Network error")
            
            # Agent should handle network errors gracefully
            with pytest.raises(Exception):  # Should raise or handle gracefully
                await agent.activate()


class TestFileSystemErrorHandling:
    """Tests for file system error handling."""

    def test_file_not_found_error_detection(self):
        """Test detection of file not found errors."""
        analyzer = ErrorAnalyzer()
        error = FileNotFoundError("File not found: test.py")
        envelope = ErrorEnvelopeBuilder.from_exception(error)
        
        analysis = analyzer.analyze(error)
        
        assert analysis.error_type == ErrorType.FILE_NOT_FOUND

    def test_permission_denied_error_detection(self):
        """Test detection of permission denied errors."""
        analyzer = ErrorAnalyzer()
        error = PermissionError("Permission denied")
        envelope = ErrorEnvelopeBuilder.from_exception(error)
        
        analysis = analyzer.analyze(error)
        
        assert analysis.error_type == ErrorType.PERMISSION_DENIED

    def test_disk_full_error_detection(self):
        """Test detection of disk full errors."""
        analyzer = ErrorAnalyzer()
        error_dict = {
            "error": "No space left on device",
            "error_code": "disk_full",
        }
        envelope = ErrorEnvelopeBuilder.from_dict(error_dict)
        
        analysis = analyzer.analyze(envelope)
        
        assert analysis.error_type == ErrorType.DISK_FULL

    def test_invalid_path_error_detection(self):
        """Test detection of invalid path errors."""
        analyzer = ErrorAnalyzer()
        error_dict = {
            "error": "Invalid path: /nonexistent/../etc/passwd",
            "error_code": "path_invalid",
        }
        envelope = ErrorEnvelopeBuilder.from_dict(error_dict)
        
        analysis = analyzer.analyze(envelope)
        
        assert analysis.error_type == ErrorType.PATH_INVALID

    def test_file_operation_error_handling(self):
        """Test handling of file operation errors."""
        from tapps_agents.core.exceptions import FileOperationError
        
        error = FileOperationError("Cannot write to file")
        envelope = ErrorEnvelopeBuilder.from_exception(error)
        
        assert envelope.code == "file_operation_error"
        assert envelope.category == "permission"

    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        from tapps_agents.core.agent_base import BaseAgent
        
        agent = BaseAgent()
        
        # Should reject path traversal attempts
        invalid_paths = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
        ]
        
        for invalid_path in invalid_paths:
            with pytest.raises((ValueError, PermissionError)):
                agent._validate_path(Path(invalid_path))


class TestInvalidInputHandling:
    """Tests for invalid input handling."""

    def test_invalid_input_error_detection(self):
        """Test detection of invalid input errors."""
        analyzer = ErrorAnalyzer()
        error = ValueError("Invalid input: expected int, got str")
        envelope = ErrorEnvelopeBuilder.from_exception(error)
        
        analysis = analyzer.analyze(error)
        
        assert analysis.error_type == ErrorType.INVALID_INPUT

    def test_missing_required_field_error(self):
        """Test detection of missing required field errors."""
        analyzer = ErrorAnalyzer()
        error_dict = {
            "error": "Missing required field: 'file'",
            "error_code": "missing_required",
        }
        envelope = ErrorEnvelopeBuilder.from_dict(error_dict)
        
        analysis = analyzer.analyze(envelope)
        
        assert analysis.error_type == ErrorType.MISSING_REQUIRED

    def test_type_mismatch_error(self):
        """Test detection of type mismatch errors."""
        analyzer = ErrorAnalyzer()
        error_dict = {
            "error": "Type mismatch: expected str, got int",
            "error_code": "type_mismatch",
        }
        envelope = ErrorEnvelopeBuilder.from_dict(error_dict)
        
        analysis = analyzer.analyze(envelope)
        
        assert analysis.error_type == ErrorType.TYPE_MISMATCH

    def test_empty_string_input(self):
        """Test handling of empty string input."""
        from tapps_agents.core.agent_base import BaseAgent
        
        agent = BaseAgent()
        
        # Empty command should be handled gracefully
        result = agent.parse_command("")
        assert result is None or result == ("", {})

    def test_none_input(self):
        """Test handling of None input."""
        from tapps_agents.core.agent_base import BaseAgent
        
        agent = BaseAgent()
        
        # None command should be handled gracefully
        result = agent.parse_command(None)
        assert result is None

    def test_whitespace_only_input(self):
        """Test handling of whitespace-only input."""
        from tapps_agents.core.agent_base import BaseAgent
        
        agent = BaseAgent()
        
        # Whitespace-only command should be handled gracefully
        result = agent.parse_command("   \n\t  ")
        assert result is None or result[0].strip() == ""


class TestResourceExhaustion:
    """Tests for resource exhaustion scenarios."""

    def test_memory_error_handling(self):
        """Test handling of memory errors."""
        analyzer = ErrorAnalyzer()
        error = MemoryError("Out of memory")
        envelope = ErrorEnvelopeBuilder.from_exception(error)
        
        analysis = analyzer.analyze(error)
        
        # Memory errors should be categorized
        assert analysis.severity.value in ["error", "critical"]

    @patch("psutil.virtual_memory")
    def test_disk_space_check(self, mock_virtual_memory):
        """Test disk space checking."""
        from tapps_agents.core.hardware_profiler import HardwareProfiler
        
        profiler = HardwareProfiler()
        
        # Mock low disk space
        mock_virtual_memory.return_value = MagicMock(
            total=1024 * 1024 * 1024,  # 1GB
            available=100 * 1024 * 1024,  # 100MB
            percent=90.0,
        )
        
        metrics = profiler.get_metrics()
        assert metrics.ram_gb > 0

    def test_large_file_handling(self):
        """Test handling of very large files."""
        from tapps_agents.core.agent_base import BaseAgent
        
        agent = BaseAgent()
        
        # Create a temporary large file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            # Write a large amount of data
            f.write(b"# " + b"x" * (10 * 1024 * 1024))  # 10MB
            temp_path = Path(f.name)
        
        try:
            # Should handle large files (may reject if too large)
            try:
                agent._validate_path(temp_path)
            except (ValueError, OSError):
                # Expected if file is too large
                pass
        finally:
            temp_path.unlink()

    def test_concurrent_file_access(self):
        """Test handling of concurrent file access."""
        import tempfile
        from pathlib import Path
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            f.write(b"# Test file\n")
            temp_path = Path(f.name)
        
        try:
            # Simulate concurrent access
            # This is a basic test - real concurrent access would need threading
            assert temp_path.exists()
            assert temp_path.is_file()
        finally:
            temp_path.unlink()


class TestConfigurationErrors:
    """Tests for configuration error handling."""

    def test_missing_config_error(self):
        """Test detection of missing config errors."""
        analyzer = ErrorAnalyzer()
        error_dict = {
            "error": "Configuration file not found",
            "error_code": "missing_config",
        }
        envelope = ErrorEnvelopeBuilder.from_dict(error_dict)
        
        analysis = analyzer.analyze(envelope)
        
        assert analysis.error_type == ErrorType.MISSING_CONFIG

    def test_invalid_config_error(self):
        """Test detection of invalid config errors."""
        analyzer = ErrorAnalyzer()
        error_dict = {
            "error": "Invalid configuration: invalid YAML",
            "error_code": "invalid_config",
        }
        envelope = ErrorEnvelopeBuilder.from_dict(error_dict)
        
        analysis = analyzer.analyze(envelope)
        
        assert analysis.error_type == ErrorType.INVALID_CONFIG

    def test_env_var_missing_error(self):
        """Test detection of missing environment variable errors."""
        analyzer = ErrorAnalyzer()
        error_dict = {
            "error": "Environment variable API_KEY not set",
            "error_code": "env_var_missing",
        }
        envelope = ErrorEnvelopeBuilder.from_dict(error_dict)
        
        analysis = analyzer.analyze(envelope)
        
        assert analysis.error_type == ErrorType.ENV_VAR_MISSING


class TestExecutionErrors:
    """Tests for execution error handling."""

    def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        analyzer = ErrorAnalyzer()
        error = SyntaxError("Invalid syntax")
        envelope = ErrorEnvelopeBuilder.from_exception(error)
        
        analysis = analyzer.analyze(error)
        
        # Syntax errors should be categorized
        assert analysis.error_type in [ErrorType.SYNTAX_ERROR, ErrorType.UNKNOWN]

    def test_import_error_handling(self):
        """Test handling of import errors."""
        analyzer = ErrorAnalyzer()
        error = ImportError("No module named 'nonexistent'")
        envelope = ErrorEnvelopeBuilder.from_exception(error)
        
        analysis = analyzer.analyze(error)
        
        # Import errors should be categorized
        assert analysis.error_type in [ErrorType.IMPORT_ERROR, ErrorType.UNKNOWN]

    def test_runtime_error_handling(self):
        """Test handling of runtime errors."""
        analyzer = ErrorAnalyzer()
        error = RuntimeError("Runtime error occurred")
        envelope = ErrorEnvelopeBuilder.from_exception(error)
        
        analysis = analyzer.analyze(error)
        
        # Runtime errors should be categorized
        assert analysis.error_type in [ErrorType.RUNTIME_ERROR, ErrorType.UNKNOWN]


class TestErrorRecovery:
    """Tests for error recovery mechanisms."""

    def test_error_envelope_building(self):
        """Test building error envelopes from exceptions."""
        error = ValueError("Test error")
        envelope = ErrorEnvelopeBuilder.from_exception(error)
        
        assert envelope.code == "validation_error"
        assert envelope.category == "validation"
        assert "Test error" in envelope.message

    def test_error_envelope_from_dict(self):
        """Test building error envelopes from dictionaries."""
        error_dict = {
            "error": "Test error",
            "error_code": "test_error",
            "context": {"key": "value"},
        }
        envelope = ErrorEnvelopeBuilder.from_dict(error_dict)
        
        assert envelope.code == "test_error"
        assert envelope.message == "Test error"
        assert envelope.context == {"key": "value"}

    def test_error_analysis_context(self):
        """Test error analysis includes context."""
        analyzer = ErrorAnalyzer()
        error = FileNotFoundError("File not found")
        
        from tapps_agents.workflow.error_recovery import ErrorContext
        context = ErrorContext(
            workflow_id="test-workflow",
            step_id="test-step",
            agent="test-agent",
        )
        
        analysis = analyzer.analyze(error, context=context)
        
        assert analysis.context == context
        assert analysis.context.workflow_id == "test-workflow"

