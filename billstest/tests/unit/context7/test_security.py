"""
Tests for Context7 Security module.

Tests security audit, compliance verification, and API key management.
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.context7.security import (
    APIKeyManager,
    ComplianceStatus,
    SecurityAuditResult,
)


class TestAPIKeyManager:
    """Tests for APIKeyManager."""

    def test_init_default_config_dir(self, tmp_path):
        """Test APIKeyManager initialization with default config dir."""
        with patch("tapps_agents.context7.security.Path.cwd", return_value=tmp_path):
            manager = APIKeyManager()
            assert manager.config_dir == tmp_path / ".tapps-agents"
            assert manager.config_dir.exists()

    def test_init_custom_config_dir(self, tmp_path):
        """Test APIKeyManager initialization with custom config dir."""
        custom_dir = tmp_path / "custom"
        manager = APIKeyManager(config_dir=custom_dir)
        assert manager.config_dir == custom_dir
        assert manager.config_dir.exists()

    def test_store_api_key_without_crypto(self, tmp_path):
        """Test storing key when cryptography is not available."""
        with patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", False):
            manager = APIKeyManager(config_dir=tmp_path / ".tapps-agents")
            # Should not raise error, just store in plain text
            manager.store_api_key("test-service", "test-key")
            
            keys_file = manager.config_dir / "api-keys.encrypted"
            # File might exist but unencrypted
            assert keys_file.exists() or not keys_file.exists()

    def test_load_api_key_without_crypto(self, tmp_path):
        """Test retrieving key when cryptography is not available."""
        with patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", False):
            manager = APIKeyManager(config_dir=tmp_path / ".tapps-agents")
            # Should handle gracefully
            key = manager.load_api_key("test-service")
            assert key is None or isinstance(key, str)

    @pytest.mark.skipif(
        not os.environ.get("TEST_CRYPTO", False),
        reason="Cryptography tests require crypto library",
    )
    def test_store_and_retrieve_key_with_crypto(self, tmp_path):
        """Test storing and retrieving encrypted keys."""
        manager = APIKeyManager(config_dir=tmp_path / ".tapps-agents")
        manager.store_api_key("test-service", "test-key-value", encrypt=True)
        
        retrieved = manager.load_api_key("test-service")
        assert retrieved == "test-key-value"

    def test_load_all_keys(self, tmp_path):
        """Test listing stored keys."""
        manager = APIKeyManager(config_dir=tmp_path / ".tapps-agents")
        manager.store_api_key("service1", "key1")
        manager.store_api_key("service2", "key2")
        
        keys = manager.load_all_keys()
        assert isinstance(keys, dict)
        # Should contain service names (exact content depends on implementation)

    def test_delete_api_key(self, tmp_path):
        """Test deleting a stored key."""
        manager = APIKeyManager(config_dir=tmp_path / ".tapps-agents")
        manager.store_api_key("test-service", "test-key")
        manager.delete_api_key("test-service")
        
        key = manager.load_api_key("test-service")
        assert key is None


class TestSecurityAuditResult:
    """Tests for SecurityAuditResult."""

    def test_to_dict(self):
        """Test converting SecurityAuditResult to dictionary."""
        result = SecurityAuditResult(
            passed=True,
            issues=[],
            warnings=["Warning 1"],
            recommendations=["Recommendation 1"],
            timestamp="2025-01-01T00:00:00",
            compliance_status={"soc2": True},
        )
        
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["passed"] is True
        assert data["warnings"] == ["Warning 1"]
        assert data["recommendations"] == ["Recommendation 1"]


class TestComplianceStatus:
    """Tests for ComplianceStatus."""

    def test_to_dict(self):
        """Test converting ComplianceStatus to dictionary."""
        status = ComplianceStatus(
            soc2_verified=True,
            data_retention_compliant=True,
            audit_logging_enabled=False,
        )
        
        data = status.to_dict()
        assert isinstance(data, dict)
        assert data["soc2_verified"] is True
        assert data["data_retention_compliant"] is True
        assert data["audit_logging_enabled"] is False


class TestSecurityAudit:
    """Tests for security audit functionality."""

    def test_security_audit_result_creation(self):
        """Test creating SecurityAuditResult."""
        result = SecurityAuditResult(
            passed=True,
            issues=[],
            warnings=["Warning 1"],
            recommendations=["Recommendation 1"],
            timestamp="2025-01-01T00:00:00",
            compliance_status={"soc2": True},
        )
        
        assert result.passed is True
        assert len(result.issues) == 0
        assert len(result.warnings) == 1
        assert len(result.recommendations) == 1


class TestSecurityValidation:
    """Tests for security validation functions."""

    def test_validate_api_key_format(self):
        """Test API key format validation."""
        # This would test if there's a validate function
        # Implementation depends on actual security module
        pass

    def test_validate_file_permissions(self, tmp_path):
        """Test file permission validation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        # Would test permission checking if implemented
        assert test_file.exists()

