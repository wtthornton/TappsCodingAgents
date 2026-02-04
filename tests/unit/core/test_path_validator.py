"""
Security regression tests for path validation.

Tests cover:
- Path traversal attempts (.., encoded variants)
- Absolute path escapes
- Root boundary enforcement
- File size limits
"""

from pathlib import Path

import pytest

from tapps_agents.core.path_validator import (
    PathValidationError,
    PathValidator,
    reset_path_validator,
)


class TestPathValidator:
    """Test path validation security features."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create a temporary project root with .tapps-agents/ directory."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".tapps-agents").mkdir()
        return project

    @pytest.fixture
    def validator(self, project_root):
        """Create a path validator instance."""
        return PathValidator(project_root)

    @pytest.fixture
    def test_file(self, project_root):
        """Create a test file within project root."""
        test_file = project_root / "test.txt"
        test_file.write_text("test content")
        return test_file

    def test_valid_path_within_project_root(self, validator, test_file):
        """Test that valid paths within project root are allowed."""
        result = validator.validate_read_path(test_file)
        assert result == test_file.resolve()

    def test_valid_path_within_tapps_agents(self, validator, project_root):
        """Test that paths within .tapps-agents/ are allowed."""
        config_file = project_root / ".tapps-agents" / "config.yaml"
        config_file.write_text("test: true")
        result = validator.validate_read_path(config_file)
        assert result == config_file.resolve()

    def test_path_traversal_blocked(self, validator, project_root, tmp_path):
        """Test that path traversal attempts are blocked."""
        # Create a file outside project root
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("outside")

        # Try to access it via traversal
        traversal_path = project_root / ".." / "outside.txt"
        with pytest.raises(PathValidationError, match="Path traversal detected"):
            validator.validate_read_path(traversal_path)

    def test_absolute_path_escape_blocked(self, validator, tmp_path):
        """Test that absolute paths outside allowed roots are blocked."""
        # Create a file outside project root
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("outside")

        with pytest.raises(PathValidationError, match="Path outside allowed roots"):
            validator.validate_read_path(outside_file)

    def test_url_encoded_traversal_blocked(self, validator, project_root):
        """Test that URL-encoded traversal attempts are blocked."""
        # Try %2e%2e (URL-encoded ..)
        suspicious_path = project_root / "test%2e%2e%2foutside.txt"
        with pytest.raises(PathValidationError, match="Suspicious path pattern"):
            validator.validate_read_path(suspicious_path)

    def test_percent_encoded_slash_blocked(self, validator, project_root):
        """Test that URL-encoded slashes are blocked."""
        suspicious_path = project_root / "test%2foutside.txt"
        with pytest.raises(PathValidationError, match="Suspicious path pattern"):
            validator.validate_read_path(suspicious_path)

    def test_percent_encoded_backslash_blocked(self, validator, project_root):
        """Test that URL-encoded backslashes are blocked."""
        suspicious_path = project_root / "test%5coutside.txt"
        with pytest.raises(PathValidationError, match="Suspicious path pattern"):
            validator.validate_read_path(suspicious_path)

    def test_file_size_limit_enforced(self, validator, project_root):
        """Test that file size limits are enforced."""
        # Create a large file
        large_file = project_root / "large.txt"
        large_file.write_bytes(b"x" * (11 * 1024 * 1024))  # 11 MB

        with pytest.raises(PathValidationError, match="File too large"):
            validator.validate_read_path(large_file, max_file_size=10 * 1024 * 1024)

    def test_file_size_limit_allowed(self, validator, project_root):
        """Test that files within size limit are allowed."""
        # Create a file within size limit
        small_file = project_root / "small.txt"
        small_file.write_bytes(b"x" * (5 * 1024 * 1024))  # 5 MB

        result = validator.validate_read_path(small_file, max_file_size=10 * 1024 * 1024)
        assert result == small_file.resolve()

    def test_nonexistent_file_raises_error(self, validator, project_root):
        """Test that nonexistent files raise FileNotFoundError."""
        nonexistent = project_root / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            validator.validate_read_path(nonexistent)

    def test_nonexistent_file_allowed_for_write(self, validator, project_root):
        """Test that nonexistent files are allowed for write operations."""
        new_file = project_root / "new.txt"
        result = validator.validate_write_path(new_file)
        assert result == new_file.resolve()

    def test_test_path_allowed(self, validator):
        """Test that pytest temporary paths are allowed."""
        # Create a path that looks like a pytest tmp_path
        test_path = Path("/tmp/pytest-of-user/pytest-123/tmp_path/test.txt")
        # This should not raise an error (even if file doesn't exist)
        # Note: This test may need adjustment based on actual test environment
        # For now, we'll test the pattern matching logic
        assert validator._is_test_path(test_path)

    def test_symlink_resolution(self, validator, project_root, tmp_path):
        """Test that symlinks are resolved and checked against allowed roots."""
        # Create a file outside project
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("outside")

        # Create a symlink inside project pointing outside
        symlink = project_root / "link.txt"
        try:
            symlink.symlink_to(outside_file)
            # Symlink should be blocked because it resolves outside allowed roots
            with pytest.raises(PathValidationError, match="Path outside allowed roots"):
                validator.validate_read_path(symlink)
        except OSError:
            # Symlinks may not be supported on all platforms
            pytest.skip("Symlinks not supported on this platform")

    def test_relative_path_resolution(self, validator, project_root, test_file):
        """Test that relative paths are resolved correctly."""
        # Change to a subdirectory
        subdir = project_root / "subdir"
        subdir.mkdir()

        # Use relative path
        relative_path = Path("..") / "test.txt"
        # This should resolve to test_file and be allowed
        result = validator.validate_read_path(relative_path)
        assert result == test_file.resolve()

    def test_nested_traversal_blocked(self, validator, project_root):
        """Test that nested traversal attempts are blocked."""
        # Try multiple levels of traversal
        traversal_path = project_root / "a" / ".." / ".." / ".." / "etc" / "passwd"
        with pytest.raises(PathValidationError):
            validator.validate_read_path(traversal_path)

    def test_case_insensitive_pattern_detection(self, validator, project_root):
        """Test that pattern detection is case-insensitive."""
        # Try uppercase encoded patterns
        suspicious_path = project_root / "test%2E%2E%2Foutside.txt"
        with pytest.raises(PathValidationError, match="Suspicious path pattern"):
            validator.validate_read_path(suspicious_path)

    def test_auto_detect_project_root(self, tmp_path):
        """Test that project root is auto-detected from .tapps-agents/."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".tapps-agents").mkdir()
        test_file = project / "test.txt"
        test_file.write_text("test")

        # Create validator without explicit project root
        validator = PathValidator()
        # Change to project directory
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = validator.validate_read_path(test_file)
            assert result == test_file.resolve()
        finally:
            os.chdir(old_cwd)

    def test_write_path_validation(self, validator, project_root):
        """Test that write paths are validated correctly."""
        # New file should be allowed
        new_file = project_root / "new_file.txt"
        result = validator.validate_write_path(new_file)
        assert result == new_file.resolve()

        # File outside project should be blocked
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            outside_file = Path(tmpdir) / "outside.txt"
            with pytest.raises(PathValidationError, match="Path outside allowed roots"):
                validator.validate_write_path(outside_file)


class TestPathValidatorIntegration:
    """Integration tests for path validator with BaseAgent."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create a temporary project root."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".tapps-agents").mkdir()
        return project

    def test_base_agent_uses_validator(self, project_root):
        """Test that BaseAgent._validate_path uses the centralized validator."""
        from tapps_agents.core.agent_base import BaseAgent
        from tapps_agents.core.config import ProjectConfig

        # Create a minimal agent instance
        class TestAgent(BaseAgent):
            async def run(self, command: str, **kwargs):
                return {}

        agent = TestAgent("test", "Test Agent", config=ProjectConfig())
        agent._project_root = project_root

        # Create a test file
        test_file = project_root / "test.txt"
        test_file.write_text("test")

        # Should validate successfully
        agent._validate_path(test_file)

        # Should raise error for traversal
        traversal_path = project_root / ".." / "outside.txt"
        with pytest.raises(ValueError, match="Path traversal"):
            agent._validate_path(traversal_path)


class TestPathValidatorEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_path_raises_error(self):
        """Test that invalid paths raise appropriate errors."""
        validator = PathValidator()

        # Try to validate a path with invalid characters (platform-dependent)
        # This test may need adjustment based on platform
        invalid_path = Path("\x00invalid")
        with pytest.raises((PathValidationError, OSError, RuntimeError)):
            validator.validate_read_path(invalid_path)

    def test_empty_path_handling(self, tmp_path):
        """Test that empty paths are handled correctly."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".tapps-agents").mkdir()

        validator = PathValidator(project)
        empty_path = Path("")

        with pytest.raises((PathValidationError, FileNotFoundError)):
            validator.validate_read_path(empty_path)

    def test_reset_global_validator(self):
        """Test that global validator can be reset."""
        reset_path_validator()
        from tapps_agents.core.path_validator import _global_validator

        assert _global_validator is None


class TestRedactionSecurity:
    """Test that sensitive data is properly redacted from logs and artifacts."""

    def test_error_envelope_redacts_api_keys(self):
        """Test that ErrorEnvelope redacts API keys from error messages."""
        from tapps_agents.core.error_envelope import ErrorEnvelopeBuilder

        # Create error message with API key
        message = "API key: sk-1234567890abcdef1234567890abcdef"
        sanitized = ErrorEnvelopeBuilder._sanitize_message(message)

        assert "sk-1234567890abcdef1234567890abcdef" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_error_envelope_redacts_passwords(self):
        """Test that ErrorEnvelope redacts passwords from error messages."""
        from tapps_agents.core.error_envelope import ErrorEnvelopeBuilder

        # Create error message with password
        message = "password=secret123"
        sanitized = ErrorEnvelopeBuilder._sanitize_message(message)

        assert "secret123" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_error_envelope_redacts_tokens(self):
        """Test that ErrorEnvelope redacts tokens from error messages."""
        from tapps_agents.core.error_envelope import ErrorEnvelopeBuilder

        # Create error message with token
        message = "Bearer token: abc123def456ghi789"
        sanitized = ErrorEnvelopeBuilder._sanitize_message(message)

        assert "abc123def456ghi789" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_workflow_logger_redacts_sensitive_data(self):
        """Test that WorkflowLogger redacts sensitive data."""
        import logging

        from tapps_agents.workflow.logging_helper import WorkflowLogger

        logger = WorkflowLogger(logging.getLogger("test"))

        # Test redaction method directly
        message = "api_key=sk-1234567890abcdef"
        redacted = logger._redact_sensitive(message)

        assert "sk-1234567890abcdef" not in redacted
        assert "***REDACTED***" in redacted

    def test_e2e_harness_redacts_secrets(self):
        """Test that E2E harness redacts secrets from content."""
        from tests.e2e.fixtures.e2e_harness import redact_secrets

        # Test API key redaction
        content = '{"api_key": "sk-1234567890abcdef"}'
        redacted = redact_secrets(content)

        assert "sk-1234567890abcdef" not in redacted
        assert "[REDACTED]" in redacted

    def test_e2e_harness_redacts_custom_secrets(self):
        """Test that E2E harness redacts custom secrets."""
        from tests.e2e.fixtures.e2e_harness import redact_secrets

        content = "My secret is secret123 and another is abc456"
        redacted = redact_secrets(content, secrets=["secret123", "abc456"])

        assert "secret123" not in redacted
        assert "abc456" not in redacted
        assert "[REDACTED]" in redacted

    def test_ci_artifacts_redaction_applied(self):
        """Test that CI artifacts are redacted before upload."""
        # This is an integration test - verify that redaction is called
        # when collecting artifacts
        from tests.e2e.fixtures.ci_artifacts import redact_secrets

        # Test that redaction function works
        content = '{"api_key": "sk-test123"}'
        redacted = redact_secrets(content)

        assert "sk-test123" not in redacted
        assert "[REDACTED]" in redacted or '"api_key"' in redacted

