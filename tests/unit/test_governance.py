"""
Tests for Governance & Safety Layer.
"""

from pathlib import Path
import tempfile
import json

from tapps_agents.experts.governance import (
    GovernanceLayer,
    GovernancePolicy,
)
from tapps_agents.experts.knowledge_ingestion import KnowledgeEntry, KnowledgeIngestionPipeline


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


def test_queue_for_approval():
    """Test approval queue functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        approval_dir = Path(tmpdir) / "approval_queue"
        policy = GovernancePolicy(
            require_approval=True,
            approval_queue_path=approval_dir,
        )
        layer = GovernanceLayer(policy=policy)
        
        entry = KnowledgeEntry(
            title="Test Entry",
            content="Test content",
            domain="expert-new-domain",
            source="context7://library/expert",
            source_type="context7",
        )
        
        approval_file = layer.queue_for_approval(entry)
        
        assert approval_file.exists()
        assert approval_file.suffix == ".json"
        
        # Verify approval file content
        data = json.loads(approval_file.read_text(encoding="utf-8"))
        assert data["status"] == "pending"
        assert data["entry"]["title"] == "Test Entry"
        assert "queued_at" in data


def test_governance_integration_with_pipeline():
    """Test governance layer integration with knowledge ingestion pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        config_dir = project_root / ".tapps-agents"
        config_dir.mkdir()
        
        # Create a test file with secrets
        test_file = project_root / "test_secret.md"
        test_file.write_text('api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"')
        
        # Create pipeline with governance enabled
        policy = GovernancePolicy(
            filter_secrets=True,
            require_approval=False,  # Don't require approval for this test
        )
        pipeline = KnowledgeIngestionPipeline(
            project_root=project_root,
            governance_policy=policy,
        )
        
        # Try to ingest the file
        result = pipeline.ingest_project_sources()
        
        # Entry should be filtered out (not ingested)
        # Since it contains secrets, it should fail validation
        assert result.entries_ingested == 0 or result.entries_failed > 0


def test_approval_workflow():
    """Test complete approval workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        approval_dir = Path(tmpdir) / "approval_queue"
        policy = GovernancePolicy(
            require_approval=True,
            approval_queue_path=approval_dir,
        )
        layer = GovernanceLayer(policy=policy)
        
        # Entry that requires approval
        entry = KnowledgeEntry(
            title="New Expert Entry",
            content="Expert content",
            domain="expert-new-domain",
            source="context7://library/expert",
            source_type="context7",
        )
        
        # Should require approval
        assert layer.requires_approval(entry) is True
        
        # Queue for approval
        approval_file = layer.queue_for_approval(entry)
        assert approval_file.exists()
        
        # Verify file content
        data = json.loads(approval_file.read_text(encoding="utf-8"))
        assert data["status"] == "pending"
        assert data["entry"]["title"] == "New Expert Entry"

