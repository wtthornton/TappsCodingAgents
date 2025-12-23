# Step 1: Enhanced Prompt - Security Module Tests

**Generated:** January 2026  
**Workflow:** Build Workflow for Security Test Implementation  
**Target:** `tapps_agents/context7/security.py`

## Original Prompt

Create comprehensive unit tests for the security module (`tapps_agents/context7/security.py`) to achieve full test coverage for API key management, security auditing, and compliance verification. The module currently has 0% test coverage according to PROJECT_ANALYSIS_2026.md.

## Enhanced Prompt

### Requirements Analysis

**Functional Requirements:**
1. Test API key encryption/decryption with and without cryptography library
2. Test master key creation, loading, and management
3. Test API key storage (encrypted and unencrypted modes)
4. Test API key retrieval with proper decryption
5. Test API key deletion functionality
6. Test security audit functionality (file permissions, environment variables, crypto availability)
7. Test compliance verification (SOC 2, data retention, audit logging)
8. Test error handling for decryption failures, missing keys, permission errors
9. Test Windows compatibility (chmod operations that may fail)
10. Test edge cases (empty keys file, corrupted data, invalid encrypted keys)

**Non-Functional Requirements:**
- Test execution time: < 5 seconds for full suite
- Test isolation: Each test must use temporary directories
- Test reliability: Tests must work on both Windows and Unix systems
- Test coverage target: 90%+ for security-critical code
- Test maintainability: Clear test names, good documentation

### Architecture Guidance

**Test Structure:**
```
tests/unit/context7/test_security.py
├── TestAPIKeyManager
│   ├── Initialization tests
│   ├── Master key management tests
│   ├── Encryption/decryption tests (with and without crypto)
│   ├── Storage tests (encrypted/unencrypted)
│   ├── Retrieval tests (success/failure cases)
│   ├── Deletion tests
│   └── Edge case tests
├── TestSecurityAuditor
│   ├── Initialization tests
│   ├── Audit functionality tests
│   ├── Permission checking tests
│   ├── Environment variable detection tests
│   ├── Compliance verification tests
│   └── Edge case tests
└── TestDataClasses
    ├── SecurityAuditResult tests
    └── ComplianceStatus tests
```

**Testing Patterns:**
- Use pytest fixtures for temporary directories
- Mock cryptography.Fernet when testing without crypto
- Use patch decorators for environment variables
- Test both success and failure paths
- Test Windows compatibility (skip chmod assertions if not supported)

### Quality Standards

**Security Standards:**
- All credential handling must be tested
- Encryption/decryption must have comprehensive tests
- File permission checks must be validated
- Error handling must prevent information leakage

**Code Quality Standards:**
- Test code must follow project style (Ruff formatting)
- Tests must be type-annotated
- Tests must have descriptive docstrings
- Test coverage must exceed 90% for security module

**Test Quality Standards:**
- Each test must be independent
- Tests must clean up after themselves
- Tests must use meaningful assertions
- Tests must validate both positive and negative cases

### Implementation Strategy

**Phase 1: API Key Manager Tests**
1. Test initialization with custom config directory
2. Test master key creation and loading
3. Test encryption with crypto available
4. Test encryption fallback without crypto (SHA256 hash)
5. Test decryption with crypto available
6. Test decryption failure without crypto
7. Test storing encrypted keys
8. Test storing unencrypted keys
9. Test loading encrypted keys
10. Test loading unencrypted keys
11. Test loading non-existent keys
12. Test decryption failure handling (corrupted data)
13. Test key deletion
14. Test empty keys file handling

**Phase 2: Security Auditor Tests**
1. Test initialization
2. Test audit with crypto available
3. Test audit without crypto (warnings)
4. Test environment variable detection
5. Test file permission checking (with Windows compatibility)
6. Test cache directory permission checking
7. Test compliance status verification
8. Test audit result structure
9. Test SOC 2 compliance logic

**Phase 3: Data Class Tests**
1. Test SecurityAuditResult.to_dict()
2. Test ComplianceStatus.to_dict()
3. Test create_security_auditor convenience function

**Phase 4: Integration Tests**
1. Test full encryption/decryption cycle
2. Test audit with real file system operations
3. Test error recovery scenarios

## Codebase Context

**Existing Test File:** `tests/unit/context7/test_security.py` (already exists with basic tests)
**Coverage Gap:** Critical edge cases, error handling, Windows compatibility, master key management

**Related Modules:**
- `tapps_agents/context7/security.py` - Source module (288 lines)
- Uses: cryptography.Fernet, yaml, pathlib, os, hashlib
- Dependencies: pytest, unittest.mock

**Project Patterns:**
- Tests use `pytest.mark.unit` marker
- Tests use `tmp_path` fixture for isolation
- Tests use `@patch` decorators for mocking
- Windows compatibility handled with try/except for chmod

