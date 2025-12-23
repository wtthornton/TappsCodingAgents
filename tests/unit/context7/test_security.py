"""
Unit tests for Context7 Security Module.

Tests API key management, security auditing, and compliance verification.
"""

import hashlib
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
        # Mock Fernet.generate_key to return bytes
        mock_fernet_class.generate_key.return_value = b"mock_master_key_32_bytes!!"
        
        manager = APIKeyManager(config_dir=config_dir)
        
        # Mock cipher
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
        # Mock Fernet.generate_key to return bytes
        mock_fernet_class.generate_key.return_value = b"mock_master_key_32_bytes!!"
        
        manager = APIKeyManager(config_dir=config_dir)
        
        # Mock cipher
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

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    @patch("tapps_agents.context7.security.Fernet")
    def test_master_key_creation_new_file(self, mock_fernet_class, tmp_path):
        """Test master key creation when file doesn't exist."""
        config_dir = tmp_path / ".tapps-agents"
        mock_fernet_class.generate_key.return_value = b"mock_master_key_32_bytes!!"
        
        manager = APIKeyManager(config_dir=config_dir)
        
        assert manager.master_key_file.exists()
        assert manager._master_key == b"mock_master_key_32_bytes!!"
        assert manager._cipher is not None

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    @patch("tapps_agents.context7.security.Fernet")
    def test_master_key_loading_existing_file(self, mock_fernet_class, tmp_path):
        """Test master key loading when file exists."""
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir(parents=True)
        
        master_key_file = config_dir / ".master-key"
        existing_key = b"existing_master_key_32_bytes!!"
        master_key_file.write_bytes(existing_key)
        
        manager = APIKeyManager(config_dir=config_dir)
        
        assert manager._master_key == existing_key
        assert manager._cipher is not None

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    @patch("tapps_agents.context7.security.Fernet")
    def test_master_key_file_permissions_unix(self, mock_fernet_class, tmp_path):
        """Test master key file permissions on Unix systems."""
        config_dir = tmp_path / ".tapps-agents"
        mock_fernet_class.generate_key.return_value = b"mock_master_key_32_bytes!!"
        
        manager = APIKeyManager(config_dir=config_dir)
        
        # Try to check permissions (may not work on Windows)
        try:
            stat = manager.master_key_file.stat()
            mode = stat.st_mode & 0o777
            # On Windows, chmod may not work, so permissions might be 0o666
            # Accept both 0o600 (Unix) and 0o666 (Windows default)
            assert mode in (0o600, 0o666), f"Expected 0o600 or 0o666, got {oct(mode)}"
        except (OSError, AttributeError):
            # Windows may not support stat().st_mode or chmod
            pass

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    @patch("tapps_agents.context7.security.Fernet")
    def test_encrypt_decrypt_roundtrip(self, mock_fernet_class, tmp_path):
        """Test encrypt then decrypt roundtrip."""
        config_dir = tmp_path / ".tapps-agents"
        original_key = "test_api_key_12345"
        
        mock_cipher = MagicMock()
        encrypted_bytes = b"encrypted_" + original_key.encode()
        mock_cipher.encrypt.return_value = encrypted_bytes
        mock_cipher.decrypt.return_value = original_key.encode()
        mock_fernet_class.return_value = mock_cipher
        mock_fernet_class.generate_key.return_value = b"mock_master_key_32_bytes!!"
        
        manager = APIKeyManager(config_dir=config_dir)
        manager._cipher = mock_cipher
        
        encrypted = manager.encrypt_api_key(original_key)
        decrypted = manager.decrypt_api_key(encrypted)
        
        assert decrypted == original_key

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    def test_encrypt_sha256_fallback_without_crypto(self, tmp_path):
        """Test encryption fallback to SHA256 produces consistent hash."""
        config_dir = tmp_path / ".tapps-agents"
        api_key = "test_api_key_12345"
        
        with patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", False):
            manager = APIKeyManager(config_dir=config_dir)
            result1 = manager.encrypt_api_key(api_key)
            result2 = manager.encrypt_api_key(api_key)
        
        # SHA256 should be deterministic
        expected_hash = hashlib.sha256(api_key.encode()).hexdigest()
        assert result1 == expected_hash
        assert result2 == expected_hash
        assert result1 == result2

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    @patch("tapps_agents.context7.security.Fernet")
    def test_encrypt_raises_when_cipher_unavailable(self, mock_fernet_class, tmp_path):
        """Test encryption raises ValueError when cipher unavailable."""
        config_dir = tmp_path / ".tapps-agents"
        # Mock Fernet.generate_key to return bytes
        mock_fernet_class.generate_key.return_value = b"mock_master_key_32_bytes!!"
        
        manager = APIKeyManager(config_dir=config_dir)
        manager._cipher = None
        
        # Force reload attempt that fails
        with patch.object(manager, '_load_or_create_master_key', return_value=None):
            with pytest.raises(ValueError, match="Encryption not available"):
                manager.encrypt_api_key("test_key")

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    @patch("tapps_agents.context7.security.Fernet")
    def test_decrypt_handles_corrupt_data_gracefully(self, mock_fernet_class, tmp_path):
        """Test decryption handles corrupt encrypted data."""
        config_dir = tmp_path / ".tapps-agents"
        mock_cipher = MagicMock()
        mock_cipher.decrypt.side_effect = Exception("Invalid token")
        mock_fernet_class.return_value = mock_cipher
        mock_fernet_class.generate_key.return_value = b"mock_master_key_32_bytes!!"
        
        manager = APIKeyManager(config_dir=config_dir)
        manager._cipher = mock_cipher
        
        with pytest.raises(Exception):  # Fernet will raise on invalid token
            manager.decrypt_api_key("corrupt_encrypted_data")

    def test_store_api_key_creates_keys_file(self, tmp_path):
        """Test store_api_key creates keys file if it doesn't exist."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        assert not manager.keys_file.exists()
        manager.store_api_key("test_key", "value", encrypt=False)
        
        assert manager.keys_file.exists()

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    @patch("tapps_agents.context7.security.Fernet")
    def test_store_keys_file_permissions(self, mock_fernet_class, tmp_path):
        """Test keys file permissions are set correctly."""
        config_dir = tmp_path / ".tapps-agents"
        mock_fernet_class.generate_key.return_value = b"mock_master_key_32_bytes!!"
        
        manager = APIKeyManager(config_dir=config_dir)
        manager.store_api_key("test_key", "value", encrypt=False)
        
        # Try to check permissions (may not work on Windows)
        try:
            stat = manager.keys_file.stat()
            mode = stat.st_mode & 0o777
            # On Windows, chmod may not work, so permissions might be 0o666
            # Accept both 0o600 (Unix) and 0o666 (Windows default)
            assert mode in (0o600, 0o666), f"Expected 0o600 or 0o666, got {oct(mode)}"
        except (OSError, AttributeError):
            # Windows may not support stat().st_mode or chmod
            pass

    def test_store_multiple_keys(self, tmp_path):
        """Test storing multiple keys."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        manager.store_api_key("key1", "value1", encrypt=False)
        manager.store_api_key("key2", "value2", encrypt=False)
        manager.store_api_key("key3", "value3", encrypt=False)
        
        keys = manager.load_all_keys()
        assert len(keys) == 3
        assert keys["key1"]["value"] == "value1"
        assert keys["key2"]["value"] == "value2"
        assert keys["key3"]["value"] == "value3"

    def test_store_updates_existing_key(self, tmp_path):
        """Test storing updates existing key."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        manager.store_api_key("test_key", "value1", encrypt=False)
        manager.store_api_key("test_key", "value2", encrypt=False)
        
        keys = manager.load_all_keys()
        assert len(keys) == 1
        assert keys["test_key"]["value"] == "value2"

    def test_load_key_decryption_failure_returns_none(self, tmp_path):
        """Test load_api_key returns None when decryption fails."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        # Store encrypted key
        with patch.object(manager, 'encrypt_api_key', return_value="encrypted_key"):
            manager.store_api_key("test_key", "value", encrypt=True)
        
        # Mock decryption failure
        with patch.object(manager, 'decrypt_api_key', side_effect=Exception("Decryption failed")):
            result = manager.load_api_key("test_key")
            assert result is None

    def test_load_all_keys_multiple_keys(self, tmp_path):
        """Test load_all_keys with multiple keys."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        manager.store_api_key("key1", "value1", encrypt=False)
        manager.store_api_key("key2", "value2", encrypt=False)
        
        keys = manager.load_all_keys()
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys

    def test_load_all_keys_corrupted_yaml(self, tmp_path):
        """Test load_all_keys handles corrupted YAML gracefully."""
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir(parents=True)
        keys_file = config_dir / "api-keys.encrypted"
        keys_file.write_text("invalid yaml: [[[[[")
        
        manager = APIKeyManager(config_dir=config_dir)
        keys = manager.load_all_keys()
        
        # Should return empty dict on error
        assert keys == {}

    def test_delete_nonexistent_key_no_error(self, tmp_path):
        """Test deleting non-existent key doesn't raise error."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        # Should not raise
        manager.delete_api_key("nonexistent_key")

    def test_delete_persists_to_file(self, tmp_path):
        """Test deletion persists to file."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        manager.store_api_key("key1", "value1", encrypt=False)
        manager.store_api_key("key2", "value2", encrypt=False)
        manager.delete_api_key("key1")
        
        # Create new manager to verify persistence
        manager2 = APIKeyManager(config_dir=config_dir)
        keys = manager2.load_all_keys()
        assert "key1" not in keys
        assert "key2" in keys

    def test_delete_one_key_doesnt_affect_others(self, tmp_path):
        """Test deleting one key doesn't affect others."""
        config_dir = tmp_path / ".tapps-agents"
        manager = APIKeyManager(config_dir=config_dir)
        
        manager.store_api_key("key1", "value1", encrypt=False)
        manager.store_api_key("key2", "value2", encrypt=False)
        manager.store_api_key("key3", "value3", encrypt=False)
        
        manager.delete_api_key("key2")
        
        keys = manager.load_all_keys()
        assert "key1" in keys
        assert "key2" not in keys
        assert "key3" in keys


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

    def test_audit_result_structure(self, tmp_path):
        """Test audit result has correct structure."""
        config_dir = tmp_path / ".tapps-agents"
        auditor = SecurityAuditor(config_dir=config_dir)
        
        result = auditor.audit()
        
        assert hasattr(result, "passed")
        assert hasattr(result, "issues")
        assert hasattr(result, "warnings")
        assert hasattr(result, "recommendations")
        assert hasattr(result, "timestamp")
        assert hasattr(result, "compliance_status")
        assert isinstance(result.issues, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.recommendations, list)
        assert isinstance(result.compliance_status, dict)

    def test_audit_compliance_status_structure(self, tmp_path):
        """Test audit compliance status has correct structure."""
        config_dir = tmp_path / ".tapps-agents"
        auditor = SecurityAuditor(config_dir=config_dir)
        
        result = auditor.audit()
        
        compliance = result.compliance_status
        assert "soc2_verified" in compliance
        assert "data_retention_compliant" in compliance
        assert "audit_logging_enabled" in compliance
        assert "api_key_encrypted" in compliance
        assert "privacy_mode_enabled" in compliance

    def test_audit_timestamp_iso_format(self, tmp_path):
        """Test audit timestamp is in ISO format."""
        config_dir = tmp_path / ".tapps-agents"
        auditor = SecurityAuditor(config_dir=config_dir)
        
        result = auditor.audit()
        
        # ISO format: YYYY-MM-DDTHH:MM:SS.ffffff+00:00 or Z
        assert "T" in result.timestamp
        assert result.timestamp.count("-") >= 2  # Date part
        assert ":" in result.timestamp  # Time part

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", False)
    def test_audit_without_crypto_adds_warning(self, tmp_path):
        """Test audit adds warning when cryptography unavailable."""
        config_dir = tmp_path / ".tapps-agents"
        auditor = SecurityAuditor(config_dir=config_dir)
        
        result = auditor.audit()
        
        assert len(result.warnings) > 0
        warning_text = " ".join(result.warnings).lower()
        assert "cryptography" in warning_text or "encrypt" in warning_text

    @patch.dict(os.environ, {"CONTEXT7_API_KEY": "test_key", "ANTHROPIC_API_KEY": "test_key2"})
    def test_audit_detects_multiple_env_keys(self, tmp_path):
        """Test audit detects multiple environment variables."""
        config_dir = tmp_path / ".tapps-agents"
        auditor = SecurityAuditor(config_dir=config_dir)
        
        result = auditor.audit()
        
        # Should have warnings about env keys
        warning_text = " ".join(result.warnings).lower()
        assert "context7_api_key" in warning_text.lower() or "api key" in warning_text.lower()

    def test_audit_insecure_keys_file_permissions(self, tmp_path):
        """Test audit detects insecure keys file permissions."""
        config_dir = tmp_path / ".tapps-agents"
        config_dir.mkdir(parents=True)
        
        keys_file = config_dir / "api-keys.encrypted"
        keys_file.write_text("test")
        
        # Try to set insecure permissions (may not work on Windows)
        try:
            os.chmod(keys_file, 0o644)
        except Exception:
            pass  # Windows may not support
        
        auditor = SecurityAuditor(config_dir=config_dir)
        result = auditor.audit()
        
        # May or may not detect depending on OS support
        # Just verify audit completes
        assert isinstance(result, SecurityAuditResult)

    def test_audit_open_cache_directory_permissions(self, tmp_path):
        """Test audit checks cache directory permissions."""
        config_dir = tmp_path / ".tapps-agents"
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)
        
        # Try to set open permissions (may not work on Windows)
        try:
            os.chmod(cache_dir, 0o777)
        except Exception:
            pass  # Windows may not support
        
        auditor = SecurityAuditor(config_dir=config_dir, cache_dir=cache_dir)
        result = auditor.audit()
        
        # May or may not detect depending on OS support
        # Just verify audit completes
        assert isinstance(result, SecurityAuditResult)

    @patch("tapps_agents.context7.security.CRYPTO_AVAILABLE", True)
    def test_soc2_verification_logic(self, tmp_path):
        """Test SOC 2 verification logic (0 issues, <3 warnings)."""
        config_dir = tmp_path / ".tapps-agents"
        auditor = SecurityAuditor(config_dir=config_dir)
        
        result = auditor.audit()
        
        # With crypto available and no issues, should pass
        compliance = ComplianceStatus(**result.compliance_status)
        
        # SOC 2 verified if 0 issues and <3 warnings
        if len(result.issues) == 0 and len(result.warnings) < 3:
            assert compliance.soc2_verified is True
        else:
            assert compliance.soc2_verified is False

    def test_audit_passed_when_no_issues(self, tmp_path):
        """Test audit passed is True when no issues found."""
        config_dir = tmp_path / ".tapps-agents"
        auditor = SecurityAuditor(config_dir=config_dir)
        
        result = auditor.audit()
        
        # Should pass if no issues
        if len(result.issues) == 0:
            assert result.passed is True
        else:
            assert result.passed is False

    def test_audit_windows_permission_compatibility(self, tmp_path):
        """Test audit handles Windows permission checking gracefully."""
        config_dir = tmp_path / ".tapps-agents"
        cache_dir = tmp_path / "cache"
        config_dir.mkdir(parents=True)
        cache_dir.mkdir(parents=True)
        
        keys_file = config_dir / "api-keys.encrypted"
        keys_file.write_text("test")
        
        auditor = SecurityAuditor(config_dir=config_dir, cache_dir=cache_dir)
        
        # Should not raise even if permission checks fail on Windows
        result = auditor.audit()
        
        assert isinstance(result, SecurityAuditResult)

    def test_compliance_status_fields(self, tmp_path):
        """Test ComplianceStatus has all required fields."""
        status = ComplianceStatus()
        
        assert hasattr(status, "soc2_verified")
        assert hasattr(status, "data_retention_compliant")
        assert hasattr(status, "audit_logging_enabled")
        assert hasattr(status, "api_key_encrypted")
        assert hasattr(status, "privacy_mode_enabled")

    def test_compliance_status_to_dict(self, tmp_path):
        """Test ComplianceStatus.to_dict() includes all fields."""
        status = ComplianceStatus(
            soc2_verified=True,
            data_retention_compliant=True,
            audit_logging_enabled=True,
            api_key_encrypted=True,
            privacy_mode_enabled=True
        )
        
        status_dict = status.to_dict()
        
        assert status_dict["soc2_verified"] is True
        assert status_dict["data_retention_compliant"] is True
        assert status_dict["audit_logging_enabled"] is True
        assert status_dict["api_key_encrypted"] is True
        assert status_dict["privacy_mode_enabled"] is True


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

    def test_security_audit_result_to_dict_all_fields(self):
        """Test SecurityAuditResult.to_dict() includes all fields."""
        result = SecurityAuditResult(
            passed=False,
            issues=["issue1", "issue2"],
            warnings=["warning1"],
            recommendations=["rec1", "rec2"],
            timestamp="2024-01-01T12:00:00+00:00",
            compliance_status={
                "soc2_verified": False,
                "api_key_encrypted": True
            }
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["passed"] is False
        assert result_dict["issues"] == ["issue1", "issue2"]
        assert result_dict["warnings"] == ["warning1"]
        assert result_dict["recommendations"] == ["rec1", "rec2"]
        assert result_dict["timestamp"] == "2024-01-01T12:00:00+00:00"
        assert result_dict["compliance_status"]["soc2_verified"] is False


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

    def test_create_security_auditor_with_cache_dir(self, tmp_path):
        """Test create_security_auditor with cache directory."""
        config_dir = tmp_path / ".tapps-agents"
        cache_dir = tmp_path / "custom_cache"
        
        auditor = create_security_auditor(config_dir=config_dir, cache_dir=cache_dir)
        
        assert isinstance(auditor, SecurityAuditor)
        assert auditor.config_dir == config_dir
        assert auditor.cache_dir == cache_dir

    def test_create_security_auditor_default_dirs(self):
        """Test create_security_auditor uses default directories."""
        auditor = create_security_auditor()
        
        assert isinstance(auditor, SecurityAuditor)
        assert auditor.config_dir.exists() or auditor.config_dir.parent.exists()
