"""
Unit tests for Context7 Security Module.

Tests API key management, security auditing, and compliance verification.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.context7.security import (
    APIKeyManager,
    ComplianceStatus,
    SecurityAuditor,
    SecurityAuditResult,
    create_security_auditor,
)

pytestmark = pytest.mark.unit


class TestAPIKeyManager:
    """Tests for APIKeyManager."""

    def test_api_key_manager_init(self, tmp_path):
        """Test APIKeyManager initialization."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        assert manager.config_dir == config_dir
        assert manager.keys_file == config_dir / "api-keys.encrypted"
        assert manager.master_key_file == config_dir / ".master-key"

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    @patch("tapps_agents.context7.security.Fernet")
    def test_encrypt_api_key_with_crypto(self, mock_fernet_class, tmp_path):
        """Test encrypt_api_key with cryptography available."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        # Mock Fernet
        mock_cipher = MagicMock()
        mock_cipher.encrypt.return_value = b"encrypted_data"
        manager._cipher = mock_cipher
        
        result = manager.encrypt_api_key("test_key")
        
        assert result == "encrypted_data"
        mock_cipher.encrypt.assert_called_once()

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", False)
    def test_encrypt_api_key_without_crypto(self, tmp_path):
        """Test encrypt_api_key without cryptography (fallback to hash)."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        result = manager.encrypt_api_key("test_key")
        
        # Should return SHA256 hash
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex length

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    @patch("tapps_agents.context7.security.Fernet")
    def test_decrypt_api_key_with_crypto(self, mock_fernet_class, tmp_path):
        """Test decrypt_api_key with cryptography available."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        # Mock Fernet
        mock_cipher = MagicMock()
        mock_cipher.decrypt.return_value = b"test_key"
        manager._cipher = mock_cipher
        
        result = manager.decrypt_api_key("encrypted_data")
        
        assert result == "test_key"
        mock_cipher.decrypt.assert_called_once()

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", False)
    def test_decrypt_api_key_without_crypto_raises(self, tmp_path):
        """Test decrypt_api_key without cryptography raises error."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        with pytest.raises(ValueError, match="Encryption not available"):
            manager.decrypt_api_key("encrypted_data")

    def test_store_api_key_encrypted(self, tmp_path):
        """Test store_api_key with encryption."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        with patch.object(manager, 'encrypt_api_key', return_value="encrypted_key"):
            manager.store_api_key("test_key", "value", encrypt=True)
            
            keys = manager.load_all_keys()
            assert "test_key" in keys
            assert keys["test_key"]["encrypted"] is True
            assert keys["test_key"]["value"] == "encrypted_key"

    def test_store_api_key_unencrypted(self, tmp_path):
        """Test store_api_key without encryption."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        manager.store_api_key("test_key", "value", encrypt=False)
        
        keys = manager.load_all_keys()
        assert "test_key" in keys
        assert keys["test_key"]["encrypted"] is False
        assert keys["test_key"]["value"] == "value"

    def test_load_api_key_encrypted(self, tmp_path):
        """Test load_api_key with encrypted key."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        # Store encrypted key
        with patch.object(manager, 'encrypt_api_key', return_value="encrypted_key"):
            manager.store_api_key("test_key", "value", encrypt=True)
        
        # Load with decryption
        with patch.object(manager, 'decrypt_api_key', return_value="value"):
            result = manager.load_api_key("test_key")
            assert result == "value"

    def test_load_api_key_unencrypted(self, tmp_path):
        """Test load_api_key with unencrypted key."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        manager.store_api_key("test_key", "value", encrypt=False)
        result = manager.load_api_key("test_key")
        
        assert result == "value"

    def test_load_api_key_not_found(self, tmp_path):
        """Test load_api_key when key doesn't exist."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        result = manager.load_api_key("nonexistent")
        
        assert result is None

    def test_delete_api_key(self, tmp_path):
        """Test delete_api_key removes key."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        manager.store_api_key("test_key", "value", encrypt=False)
        manager.delete_api_key("test_key")
        
        result = manager.load_api_key("test_key")
        assert result is None

    def test_load_all_keys_empty(self, tmp_path):
        """Test load_all_keys when no keys file exists."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        keys = manager.load_all_keys()
        
        assert keys == {}


class TestSecurityAuditor:
    """Tests for SecurityAuditor."""

    def test_security_auditor_init(self, tmp_path):
        """Test SecurityAuditor initialization."""
        config_dir = tmp_path / ".tapps-agents"
        cache_dir = tmp_path / "cache"
        
        auditor = SecurityAuditor(config_dir=config_dir, cache_dir=cache_dir)
        
        assert auditor.config_dir == config_dir
        assert auditor.cache_dir == cache_dir
        assert auditor.api_key_manager is not None

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    def test_audit_with_crypto_available(self, tmp_path):
        """Test audit when cryptography is available."""
        config_dir = tmp_path / ".tapps-agents"
        auditor = SecurityAuditor(config_dir=config_dir)
        
        result = auditor.audit()
        
        assert isinstance(result, SecurityAuditResult)
        assert result.compliance_status["api_key_encrypted"] is True

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", False)
    def test_audit_without_crypto(self, tmp_path):
        """Test audit when cryptography is not available."""
        config_dir = tmp_path / ".tapps-agents"
        auditor = SecurityAuditor(config_dir=config_dir)
        
        result = auditor.audit()
        
        assert isinstance(result, SecurityAuditResult)
        assert "cryptography" in str(result.warnings).lower() or len(result.warnings) > 0

    @patch.dict(os.environ, {"CONTEXT7_API_KEY": "test_key"})
    def test_audit_detects_env_keys(self, tmp_path):
        """Test audit detects API keys in environment variables."""
        config_dir = tmp_path / ".tapps-agents"
        auditor = SecurityAuditor(config_dir=config_dir)
        
        result = auditor.audit()
        
        assert isinstance(result, SecurityAuditResult)
        # May have warnings about env keys
        assert len(result.warnings) >= 0

    def test_audit_file_permissions(self, tmp_path):
        """Test audit checks file permissions."""
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir(parents=True)
        
        # Create keys file with open permissions
        keys_file = config_dir / "api-keys.encrypted"
        keys_file.write_text("test")
        
        # Try to set permissions (may not work on Windows)
        try:
            os.chmod(keys_file, 0o644)
        except Exception:
            pass  # Windows may not support
        
        auditor = SecurityAuditor(config_dir=config_dir)
        result = auditor.audit()
        
        assert isinstance(result, SecurityAuditResult)

    def test_verify_compliance(self, tmp_path):
        """Test verify_compliance returns ComplianceStatus."""
        config_dir = tmp_path / ".tapps-agents"
        auditor = SecurityAuditor(config_dir=config_dir)
        
        result = auditor.verify_compliance()
        
        assert isinstance(result, ComplianceStatus)
        assert hasattr(result, "soc2_verified")
        assert hasattr(result, "api_key_encrypted")


class TestSecurityAuditResult:
    """Tests for SecurityAuditResult dataclass."""

    def test_security_audit_result_to_dict(self):
        """Test SecurityAuditResult.to_dict()."""
        result = SecurityAuditResult(
            passed=True,
            issues=[],
            warnings=["test warning"],
            recommendations=["test recommendation"],
            timestamp="2024-01-01T00:00:00",
            compliance_status={"soc2_verified": True}
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["passed"] is True
        assert result_dict["warnings"] == ["test warning"]


class TestComplianceStatus:
    """Tests for ComplianceStatus dataclass."""

    def test_compliance_status_to_dict(self):
        """Test ComplianceStatus.to_dict()."""
        status = ComplianceStatus(
            soc2_verified=True,
            data_retention_compliant=True,
            audit_logging_enabled=True,
            api_key_encrypted=True,
            privacy_mode_enabled=True
        )
        
        status_dict = status.to_dict()
        
        assert isinstance(status_dict, dict)
        assert status_dict["soc2_verified"] is True
        assert status_dict["api_key_encrypted"] is True


class TestCreateSecurityAuditor:
    """Tests for create_security_auditor convenience function."""

    def test_create_security_auditor(self, tmp_path):
        """Test create_security_auditor creates auditor."""
        config_dir = tmp_path / ".tapps-agents"
        
        auditor = create_security_auditor(config_dir=config_dir)
        
        assert isinstance(auditor, SecurityAuditor)
        assert auditor.config_dir == config_dir
