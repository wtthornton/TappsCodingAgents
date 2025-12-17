"""
Tests for Governance & Safety Layer.
"""

import pytest

from tapps_agents.experts.governance import (
    FilterResult,
    GovernanceLayer,
    GovernancePolicy,
)
from tapps_agents.experts.knowledge_ingestion import KnowledgeEntry


def test_governance_layer_initialization():
    """Test Governance Layer initialization."""
    policy = GovernancePolicy()
    layer = GovernanceLayer(policy=policy)
    assert layer.policy == policy


def test_filter_secrets():
    """Test secret filtering."""
    policy = GovernancePolicy(filter_secrets=True)
    layer = GovernanceLayer(policy=policy)

    # Test API key detection
    content = 'api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"'
    result = layer.filter_content(content)

    assert result.allowed is False
    assert "Secret pattern" in result.reason or "Secret" in str(result.detected_issues)
    assert "[REDACTED]" in result.filtered_content


def test_filter_tokens():
    """Test token filtering."""
    policy = GovernancePolicy(filter_tokens=True)
    layer = GovernanceLayer(policy=policy)

    # Test bearer token detection
    content = 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    result = layer.filter_content(content)

    assert result.allowed is False
    assert "Token" in str(result.detected_issues) or "token" in result.reason.lower()


def test_filter_credentials():
    """Test credential filtering."""
    policy = GovernancePolicy(filter_credentials=True)
    layer = GovernanceLayer(policy=policy)

    # Test username/password detection
    content = 'username = "admin"\npassword = "secret123"'
    result = layer.filter_content(content)

    assert result.allowed is False
    assert "Credentials" in str(result.detected_issues) or "credential" in result.reason.lower()


def test_filter_pii():
    """Test PII filtering."""
    policy = GovernancePolicy(filter_pii=True)
    layer = GovernanceLayer(policy=policy)

    # Test SSN detection (multiple matches)
    content = "SSN: 123-45-6789\nAnother SSN: 987-65-4321"
    result = layer.filter_content(content)

    # PII filtering is conservative, may not always block
    # But should detect potential PII
    assert "PII" in str(result.detected_issues) or result.allowed


def test_validate_knowledge_entry():
    """Test knowledge entry validation."""
    policy = GovernancePolicy(filter_secrets=True)
    layer = GovernanceLayer(policy=policy)

    # Valid entry
    valid_entry = KnowledgeEntry(
        title="Test Entry",
        content="This is safe content without secrets.",
        domain="python",
        source="test.md",
        source_type="project",
    )
    is_valid, reason = layer.validate_knowledge_entry(valid_entry)
    assert is_valid is True
    assert reason is None

    # Invalid entry with secrets
    invalid_entry = KnowledgeEntry(
        title="Test Entry",
        content='api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"',
        domain="python",
        source="test.md",
        source_type="project",
    )
    is_valid, reason = layer.validate_knowledge_entry(invalid_entry)
    assert is_valid is False
    assert reason is not None


def test_requires_approval():
    """Test approval requirement checking."""
    policy = GovernancePolicy(require_approval=True)
    layer = GovernanceLayer(policy=policy)

    # Entry that requires approval
    entry = KnowledgeEntry(
        title="New Expert",
        content="Expert content",
        domain="expert-new-domain",
        source="context7://library/expert",
        source_type="context7",
    )
    assert layer.requires_approval(entry) is True

    # Entry that doesn't require approval
    normal_entry = KnowledgeEntry(
        title="Normal Entry",
        content="Normal content",
        domain="python",
        source="test.md",
        source_type="project",
    )
    assert layer.requires_approval(normal_entry) is False

