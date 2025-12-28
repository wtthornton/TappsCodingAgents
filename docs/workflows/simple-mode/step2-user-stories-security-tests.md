# Step 2: User Stories - Security Module Tests

**Generated:** January 2026  
**Workflow:** Build Workflow for Security Test Implementation

## User Stories

### Story 1: Master Key Management Tests
**Story Points:** 3  
**Priority:** High  
**Acceptance Criteria:**
- ✅ Test master key creation when file doesn't exist
- ✅ Test master key loading when file exists
- ✅ Test master key file permissions (0o600) on Unix systems
- ✅ Test Windows compatibility (chmod may fail gracefully)
- ✅ Test cipher initialization after master key load

**Test Cases:**
- `test_master_key_creation_new_file`
- `test_master_key_loading_existing_file`
- `test_master_key_file_permissions_unix`
- `test_master_key_chmod_windows_graceful`

---

### Story 2: Encryption/Decryption Tests
**Story Points:** 5  
**Priority:** Critical  
**Acceptance Criteria:**
- ✅ Test encryption with cryptography available
- ✅ Test encryption fallback (SHA256) without cryptography
- ✅ Test decryption with cryptography available
- ✅ Test decryption raises error without cryptography
- ✅ Test encryption/decryption roundtrip (encrypt then decrypt)
- ✅ Test decryption failure with corrupted data
- ✅ Test decryption failure with invalid encrypted string

**Test Cases:**
- `test_encrypt_with_crypto_available`
- `test_encrypt_fallback_sha256_without_crypto`
- `test_decrypt_with_crypto_available`
- `test_decrypt_raises_without_crypto`
- `test_encrypt_decrypt_roundtrip`
- `test_decrypt_failure_corrupted_data`
- `test_decrypt_failure_invalid_string`

---

### Story 3: API Key Storage Tests
**Story Points:** 3  
**Priority:** High  
**Acceptance Criteria:**
- ✅ Test storing encrypted API key
- ✅ Test storing unencrypted API key
- ✅ Test keys file creation on first store
- ✅ Test keys file permissions (0o600) on Unix
- ✅ Test Windows compatibility for file permissions
- ✅ Test storing multiple keys
- ✅ Test storing updates existing key

**Test Cases:**
- `test_store_encrypted_api_key`
- `test_store_unencrypted_api_key`
- `test_store_creates_keys_file`
- `test_store_keys_file_permissions`
- `test_store_multiple_keys`
- `test_store_updates_existing_key`

---

### Story 4: API Key Retrieval Tests
**Story Points:** 4  
**Priority:** High  
**Acceptance Criteria:**
- ✅ Test loading encrypted key (with decryption)
- ✅ Test loading unencrypted key (direct return)
- ✅ Test loading non-existent key (returns None)
- ✅ Test loading key with decryption failure (returns None gracefully)
- ✅ Test loading all keys (empty file)
- ✅ Test loading all keys (multiple keys)
- ✅ Test loading corrupted YAML file (graceful handling)

**Test Cases:**
- `test_load_encrypted_key_with_decryption`
- `test_load_unencrypted_key_direct`
- `test_load_nonexistent_key_returns_none`
- `test_load_key_decryption_failure_returns_none`
- `test_load_all_keys_empty_file`
- `test_load_all_keys_multiple_keys`
- `test_load_all_keys_corrupted_yaml`

---

### Story 5: API Key Deletion Tests
**Story Points:** 2  
**Priority:** Medium  
**Acceptance Criteria:**
- ✅ Test deleting existing key
- ✅ Test deleting non-existent key (no error)
- ✅ Test deletion persists to file
- ✅ Test deleting one key doesn't affect others

**Test Cases:**
- `test_delete_existing_key`
- `test_delete_nonexistent_key_no_error`
- `test_delete_persists_to_file`
- `test_delete_one_key_doesnt_affect_others`

---

### Story 6: Security Audit Tests
**Story Points:** 5  
**Priority:** High  
**Acceptance Criteria:**
- ✅ Test audit with cryptography available (compliance = True)
- ✅ Test audit without cryptography (warnings present)
- ✅ Test audit detects environment variables (CONTEXT7_API_KEY, etc.)
- ✅ Test audit checks API keys file permissions (insecure = issue)
- ✅ Test audit checks cache directory permissions (open = warning)
- ✅ Test audit result structure (passed, issues, warnings, recommendations)
- ✅ Test audit compliance status structure
- ✅ Test audit timestamp is ISO format
- ✅ Test Windows compatibility for permission checks

**Test Cases:**
- `test_audit_with_crypto_available_compliance`
- `test_audit_without_crypto_warnings`
- `test_audit_detects_env_variables`
- `test_audit_insecure_keys_file_permissions`
- `test_audit_open_cache_directory_permissions`
- `test_audit_result_structure`
- `test_audit_compliance_status_structure`
- `test_audit_timestamp_iso_format`
- `test_audit_windows_permission_compatibility`

---

### Story 7: Compliance Verification Tests
**Story Points:** 3  
**Priority:** Medium  
**Acceptance Criteria:**
- ✅ Test verify_compliance returns ComplianceStatus
- ✅ Test SOC 2 verification logic (0 issues, <3 warnings)
- ✅ Test compliance status fields (soc2_verified, api_key_encrypted, etc.)
- ✅ Test compliance status to_dict() conversion

**Test Cases:**
- `test_verify_compliance_returns_status`
- `test_soc2_verification_logic`
- `test_compliance_status_fields`
- `test_compliance_status_to_dict`

---

### Story 8: Data Class Tests
**Story Points:** 2  
**Priority:** Low  
**Acceptance Criteria:**
- ✅ Test SecurityAuditResult.to_dict() includes all fields
- ✅ Test ComplianceStatus.to_dict() includes all fields
- ✅ Test create_security_auditor convenience function

**Test Cases:**
- `test_security_audit_result_to_dict_all_fields`
- `test_compliance_status_to_dict_all_fields`
- `test_create_security_auditor_function`

---

### Story 9: Error Handling Tests
**Story Points:** 4  
**Priority:** High  
**Acceptance Criteria:**
- ✅ Test encryption raises ValueError when cipher unavailable
- ✅ Test decryption raises ValueError when cryptography unavailable
- ✅ Test decryption handles corrupt encrypted data gracefully
- ✅ Test load_api_key handles decryption exceptions (returns None)
- ✅ Test load_all_keys handles file read errors (returns empty dict)
- ✅ Test chmod errors don't break functionality (Windows)

**Test Cases:**
- `test_encrypt_raises_when_cipher_unavailable`
- `test_decrypt_raises_when_crypto_unavailable`
- `test_decrypt_handles_corrupt_data_gracefully`
- `test_load_key_handles_decryption_exceptions`
- `test_load_all_keys_handles_file_errors`
- `test_chmod_errors_dont_break_functionality`

---

## Summary

**Total Story Points:** 31  
**Total Test Cases:** ~45 tests  
**Estimated Effort:** 2-3 days (as per PROJECT_ANALYSIS_2026.md)

**Priority Breakdown:**
- Critical: 1 story (Encryption/Decryption)
- High: 6 stories
- Medium: 2 stories
- Low: 1 story



