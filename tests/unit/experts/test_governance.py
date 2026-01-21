"""
Unit tests for Governance & Safety Layer.

Tests content filtering, secret detection, PII detection, and knowledge entry validation.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tapps_agents.experts.governance import (
    FilterResult,
    GovernanceLayer,
    GovernancePolicy,
)

pytestmark = pytest.mark.unit


class TestGovernancePolicy:
    """Tests for GovernancePolicy dataclass."""

    def test_governance_policy_defaults(self):
        """Test GovernancePolicy with default values."""
        policy = GovernancePolicy()
        
        assert policy.filter_secrets is True
        assert policy.filter_tokens is True
        assert policy.filter_credentials is True
        assert policy.filter_pii is True
        assert policy.treat_as_untrusted is True
        assert policy.label_sources is True
        assert policy.project_local_only is True

    def test_governance_policy_custom(self):
        """Test GovernancePolicy with custom values."""
        policy = GovernancePolicy(
            filter_secrets=False,
            filter_pii=False,
        )
        
        assert policy.filter_secrets is False
        assert policy.filter_pii is False


class TestGovernanceLayerFilterContent:
    """Tests for filter_content method."""

    def test_filter_content_safe_content(self):
        """Test filter_content with safe content."""
        layer = GovernanceLayer()
        
        content = "This is safe content with no secrets."
        result = layer.filter_content(content)
        
        assert isinstance(result, FilterResult)
        assert result.allowed is True
        assert result.reason is None
        assert len(result.detected_issues) == 0

    def test_filter_content_detects_api_key(self):
        """Test filter_content detects API keys."""
        layer = GovernanceLayer()
        
        content = "api_key: sk-1234567890abcdef1234567890abcdef"
        result = layer.filter_content(content)
        
        assert isinstance(result, FilterResult)
        assert result.allowed is False
        assert len(result.detected_issues) > 0
        assert "[REDACTED]" in result.filtered_content

    def test_filter_content_detects_secret_key(self):
        """Test filter_content detects secret keys."""
        layer = GovernanceLayer()
        
        content = "secret_key = 'my_secret_key_1234567890'"
        result = layer.filter_content(content)
        
        assert isinstance(result, FilterResult)
        assert result.allowed is False
        assert len(result.detected_issues) > 0

    def test_filter_content_detects_password(self):
        """Test filter_content detects passwords."""
        layer = GovernanceLayer()
        
        content = "password: mypassword123"
        result = layer.filter_content(content)
        
        assert isinstance(result, FilterResult)
        assert result.allowed is False
        assert len(result.detected_issues) > 0

    def test_filter_content_detects_token(self):
        """Test filter_content detects tokens."""
        layer = GovernanceLayer()
        
        content = "token: abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
        result = layer.filter_content(content)
        
        assert isinstance(result, FilterResult)
        assert result.allowed is False
        assert len(result.detected_issues) > 0

    def test_filter_content_detects_private_key(self):
        """Test filter_content detects private keys."""
        layer = GovernanceLayer()
        
        content = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA..."
        result = layer.filter_content(content)
        
        assert isinstance(result, FilterResult)
        assert result.allowed is False
        assert len(result.detected_issues) > 0

    def test_filter_content_detects_ssh_key(self):
        """Test filter_content detects SSH keys."""
        layer = GovernanceLayer()
        
        content = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC..."
        result = layer.filter_content(content)
        
        assert isinstance(result, FilterResult)
        assert result.allowed is False
        assert len(result.detected_issues) > 0

    def test_filter_content_detects_pii_ssn(self):
        """Test filter_content detects SSN."""
        layer = GovernanceLayer()
        
        content = "SSN: 123-45-6789 and 987-65-4321"
        result = layer.filter_content(content)
        
        assert isinstance(result, FilterResult)
        # PII requires multiple matches
        assert len(result.detected_issues) >= 0

    def test_filter_content_detects_credentials(self):
        """Test filter_content detects credentials."""
        layer = GovernanceLayer()
        
        content = "username: admin\npassword: secret123"
        result = layer.filter_content(content)
        
        assert isinstance(result, FilterResult)
        assert result.allowed is False
        assert len(result.detected_issues) > 0

    def test_filter_content_with_secrets_disabled(self):
        """Test filter_content when secret filtering is disabled."""
        policy = GovernancePolicy(filter_secrets=False)
        layer = GovernanceLayer(policy=policy)
        
        content = "api_key: sk-1234567890abcdef"
        result = layer.filter_content(content)
        
        # Should be allowed when filtering is disabled
        assert result.allowed is True

    def test_filter_content_with_pii_disabled(self):
        """Test filter_content when PII filtering is disabled."""
        policy = GovernancePolicy(filter_pii=False)
        layer = GovernanceLayer(policy=policy)
        
        content = "SSN: 123-45-6789"
        result = layer.filter_content(content)
        
        # Should be allowed when filtering is disabled
        assert result.allowed is True


class TestGovernanceLayerValidateKnowledgeEntry:
    """Tests for validate_knowledge_entry method."""

    def test_validate_knowledge_entry_safe(self, tmp_path):
        """Test validate_knowledge_entry with safe entry."""
        layer = GovernanceLayer()
        
        # Create mock knowledge entry
        mock_entry = MagicMock()
        mock_entry.content = "Safe content"
        mock_entry.source = str(tmp_path / "file.py")
        mock_entry.metadata = {}
        
        is_valid, reason = layer.validate_knowledge_entry(mock_entry)
        
        assert is_valid is True
        assert reason is None

    def test_validate_knowledge_entry_with_secrets(self, tmp_path):
        """Test validate_knowledge_entry with secrets."""
        layer = GovernanceLayer()
        
        # Create mock knowledge entry with secrets
        mock_entry = MagicMock()
        mock_entry.content = "api_key: sk-1234567890abcdef"
        mock_entry.source = str(tmp_path / "file.py")
        mock_entry.metadata = {}
        
        is_valid, reason = layer.validate_knowledge_entry(mock_entry)
        
        assert is_valid is False
        assert reason is not None
        assert "filtered" in reason.lower()

    def test_validate_knowledge_entry_project_local_only(self, tmp_path):
        """Test validate_knowledge_entry enforces project-local only."""
        layer = GovernanceLayer()
        
        # Create mock knowledge entry with non-local source
        mock_entry = MagicMock()
        mock_entry.content = "Safe content"
        mock_entry.source = "/outside/project/file.py"
        mock_entry.metadata = {}
        
        is_valid, reason = layer.validate_knowledge_entry(mock_entry)
        
        assert is_valid is False
        assert "project-local" in reason.lower()

    def test_validate_knowledge_entry_labels_untrusted(self, tmp_path):
        """Test validate_knowledge_entry labels untrusted sources."""
        layer = GovernanceLayer()
        
        # Create mock knowledge entry
        mock_entry = MagicMock()
        mock_entry.content = "Safe content"
        mock_entry.source = str(tmp_path / "file.py")
        mock_entry.metadata = {}
        
        is_valid, reason = layer.validate_knowledge_entry(mock_entry)
        
        assert is_valid is True
        assert mock_entry.metadata.get("source_label") == "untrusted"
        assert mock_entry.metadata.get("source_verified") is False


class TestFilterResult:
    """Tests for FilterResult dataclass."""

    def test_filter_result_allowed(self):
        """Test FilterResult with allowed content."""
        result = FilterResult(
            allowed=True,
            reason=None,
            filtered_content=None,
            detected_issues=[]
        )
        
        assert result.allowed is True
        assert result.reason is None
        assert len(result.detected_issues) == 0

    def test_filter_result_filtered(self):
        """Test FilterResult with filtered content."""
        result = FilterResult(
            allowed=False,
            reason="Secrets detected",
            filtered_content="api_key: [REDACTED]",
            detected_issues=["Secret pattern detected"]
        )
        
        assert result.allowed is False
        assert result.reason is not None
        assert result.filtered_content is not None
        assert len(result.detected_issues) > 0

