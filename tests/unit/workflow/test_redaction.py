"""
Unit tests for secret redaction in coordination files.

Tests redaction of API keys, tokens, passwords, and other secrets.
"""

from __future__ import annotations

import pytest

from tapps_agents.workflow.cursor_skill_helper import redact_secrets_from_text

pytestmark = pytest.mark.unit


class TestRedaction:
    """Test secret redaction functionality."""

    def test_redact_api_key_patterns(self):
        """Test redaction of API key patterns."""
        text = '--api_key sk-1234567890abcdefghij --apikey="test-key-123"'
        redacted = redact_secrets_from_text(text)
        
        assert "sk-***REDACTED***" in redacted or "sk-***REDACTED***" in redacted.replace(" ", "")
        assert "***REDACTED***" in redacted
        assert "sk-1234567890abcdefghij" not in redacted

    def test_redact_password_patterns(self):
        """Test redaction of password patterns."""
        text = '--password mySecretPassword123 --pwd="anotherPass"'
        redacted = redact_secrets_from_text(text)
        
        assert "***REDACTED***" in redacted
        assert "mySecretPassword123" not in redacted
        assert "anotherPass" not in redacted

    def test_redact_token_patterns(self):
        """Test redaction of token patterns."""
        text = '--token bearer_token_12345 --auth token_abcdef'
        redacted = redact_secrets_from_text(text)
        
        assert "***REDACTED***" in redacted
        assert "bearer_token_12345" not in redacted
        assert "token_abcdef" not in redacted

    def test_redact_aws_keys(self):
        """Test redaction of AWS access keys."""
        text = '--aws_key AKIAIOSFODNN7EXAMPLE'
        redacted = redact_secrets_from_text(text)
        
        assert "***REDACTED***" in redacted
        assert "AKIAIOSFODNN7EXAMPLE" not in redacted

    def test_redact_private_keys(self):
        """Test redaction of private keys."""
        private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
-----END PRIVATE KEY-----"""
        redacted = redact_secrets_from_text(private_key)
        
        assert "***REDACTED***" in redacted
        assert "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC" not in redacted

    def test_no_redaction_for_normal_text(self):
        """Test that normal text is not redacted."""
        text = "This is a normal command with --file path/to/file and --option value"
        redacted = redact_secrets_from_text(text)
        
        assert redacted == text  # No redaction needed

    def test_redaction_preserves_structure(self):
        """Test that redaction preserves command structure."""
        text = '@reviewer review --file src/main.py --api_key sk-test123'
        redacted = redact_secrets_from_text(text)
        
        assert "@reviewer" in redacted
        assert "--file src/main.py" in redacted
        assert "sk-test123" not in redacted
        assert "api_key" in redacted or "***REDACTED***" in redacted

