# Step 7: Testing

**Date:** January 16, 2025  
**Workflow:** Full SDLC - Framework Improvements Based on Usage Analysis  
**Step:** Testing  
**Agent:** @tester

## Executive Summary

This document outlines the testing strategy and test cases for the implemented framework improvements: CodeValidator, ModulePathSanitizer, and enhanced Simple Mode intent detection.

## Testing Strategy

### Test Coverage Target

- **Overall Coverage:** ≥80% (framework code requirement)
- **Critical Paths:** 100% coverage
- **Edge Cases:** Comprehensive coverage
- **Integration Tests:** All integration points covered

### Test Structure

```
tests/
├── unit/
│   ├── core/
│   │   ├── test_code_validator.py          # NEW
│   │   └── test_module_path_sanitizer.py   # NEW
│   └── simple_mode/
│       ├── test_intent_parser_enhanced.py   # NEW
│       └── test_nl_handler_enhanced.py     # NEW
├── integration/
│   └── simple_mode/
│       └── test_simple_mode_intent_detection.py  # NEW
└── e2e/
    └── test_framework_improvements_workflow.py    # NEW
```

## Unit Tests

### 1. CodeValidator Tests (`tests/unit/core/test_code_validator.py`)

**Test Cases:**

#### 1.1 ValidationResult Tests
- [ ] Test ValidationResult creation with valid code
- [ ] Test ValidationResult creation with invalid code
- [ ] Test ValidationResult with all error fields populated

#### 1.2 Python Validation Tests
- [ ] Test `validate_python()` with valid Python code
- [ ] Test `validate_python()` with syntax error (missing colon)
- [ ] Test `validate_python()` with syntax error (unclosed parenthesis)
- [ ] Test `validate_python()` with indentation error
- [ ] Test `validate_python()` with invalid import syntax
- [ ] Test `validate_python()` with empty code
- [ ] Test `validate_python()` with None code
- [ ] Test `validate_python()` with file_path parameter

#### 1.3 Error Suggestion Tests
- [ ] Test `suggest_fix()` for missing closing parenthesis
- [ ] Test `suggest_fix()` for missing colon
- [ ] Test `suggest_fix()` for indentation error
- [ ] Test `suggest_fix()` for invalid import syntax
- [ ] Test `suggest_fix()` with non-SyntaxError exception

#### 1.4 Language Support Tests
- [ ] Test `validate()` with language="python"
- [ ] Test `validate()` with language="typescript" (stubbed)
- [ ] Test `validate()` with language="javascript" (stubbed)
- [ ] Test `validate()` with unknown language

**Target Coverage:** ≥90%

### 2. ModulePathSanitizer Tests (`tests/unit/core/test_module_path_sanitizer.py`)

**Test Cases:**

#### 2.1 Module Path Sanitization Tests
- [ ] Test `sanitize_module_path()` with hyphens (basic case)
- [ ] Test `sanitize_module_path()` with multiple hyphens
- [ ] Test `sanitize_module_path()` with special characters
- [ ] Test `sanitize_module_path()` with `__init__` (preserved)
- [ ] Test `sanitize_module_path()` with `__main__` (preserved)
- [ ] Test `sanitize_module_path()` with consecutive underscores
- [ ] Test `sanitize_module_path()` with leading/trailing underscores
- [ ] Test `sanitize_module_path()` with empty string
- [ ] Test `sanitize_module_path()` with None

#### 2.2 Import Statement Sanitization Tests
- [ ] Test `sanitize_import_statement()` with "from ... import" pattern
- [ ] Test `sanitize_import_statement()` with "import ..." pattern
- [ ] Test `sanitize_import_statement()` with hyphens in module path
- [ ] Test `sanitize_import_statement()` with special characters
- [ ] Test `sanitize_import_statement()` with invalid pattern (no change)

#### 2.3 Code Sanitization Tests
- [ ] Test `sanitize_imports_in_code()` with single import
- [ ] Test `sanitize_imports_in_code()` with multiple imports
- [ ] Test `sanitize_imports_in_code()` with mixed code and imports
- [ ] Test `sanitize_imports_in_code()` with no imports
- [ ] Test `sanitize_imports_in_code()` with empty code

#### 2.4 Identifier Validation Tests
- [ ] Test `is_valid_python_identifier()` with valid identifier
- [ ] Test `is_valid_python_identifier()` with hyphen (invalid)
- [ ] Test `is_valid_python_identifier()` with leading number (invalid)
- [ ] Test `is_valid_python_identifier()` with special characters (invalid)
- [ ] Test `is_valid_python_identifier()` with empty string

**Target Coverage:** ≥90%

### 3. Enhanced IntentParser Tests (`tests/unit/simple_mode/test_intent_parser_enhanced.py`)

**Test Cases:**

#### 3.1 Simple Mode Intent Detection Tests
- [ ] Test `detect_simple_mode_intent()` with "@simple-mode"
- [ ] Test `detect_simple_mode_intent()` with "simple mode"
- [ ] Test `detect_simple_mode_intent()` with "use simple mode"
- [ ] Test `detect_simple_mode_intent()` with "@simple_mode"
- [ ] Test `detect_simple_mode_intent()` with "simple_mode"
- [ ] Test `detect_simple_mode_intent()` with case variations
- [ ] Test `detect_simple_mode_intent()` with false positives (no match)
- [ ] Test `detect_simple_mode_intent()` with empty string

#### 3.2 Enhanced Parse Tests
- [ ] Test `parse()` sets `force_simple_mode=True` when detected
- [ ] Test `parse()` with Simple Mode intent + build keywords
- [ ] Test `parse()` with Simple Mode intent + review keywords
- [ ] Test `parse()` with Simple Mode intent + fix keywords
- [ ] Test `parse()` preserves other intent parameters

**Target Coverage:** ≥85%

### 4. Enhanced SimpleModeHandler Tests (`tests/unit/simple_mode/test_nl_handler_enhanced.py`)

**Test Cases:**

#### 4.1 Simple Mode Forcing Tests
- [ ] Test `handle()` forces Simple Mode when intent detected
- [ ] Test `handle()` returns error if Simple Mode not available
- [ ] Test `handle()` sets `simple_mode_forced=True` in result
- [ ] Test `handle()` with Simple Mode enabled
- [ ] Test `handle()` with Simple Mode disabled

#### 4.2 Availability Tests
- [ ] Test `is_simple_mode_available()` returns True when enabled
- [ ] Test `is_simple_mode_available()` returns False when disabled

**Target Coverage:** ≥80%

## Integration Tests

### 5. Simple Mode Intent Detection Integration (`tests/integration/simple_mode/test_simple_mode_intent_detection.py`)

**Test Cases:**

- [ ] Test complete flow: user input → intent detection → Simple Mode forcing → orchestrator execution
- [ ] Test Simple Mode intent with build workflow
- [ ] Test Simple Mode intent with review workflow
- [ ] Test Simple Mode intent with fix workflow
- [ ] Test error handling when Simple Mode not available

**Target Coverage:** ≥75%

## E2E Tests

### 6. Framework Improvements Workflow (`tests/e2e/test_framework_improvements_workflow.py`)

**Test Cases:**

- [ ] Test complete workflow: Simple Mode intent → code generation → validation → sanitization
- [ ] Test code generation with validation (catches syntax errors)
- [ ] Test test generation with module path sanitization
- [ ] Test error handling and user feedback

**Target Coverage:** ≥70%

## Test Implementation Status

### ✅ Test Files Created

- [ ] `tests/unit/core/test_code_validator.py`
- [ ] `tests/unit/core/test_module_path_sanitizer.py`
- [ ] `tests/unit/simple_mode/test_intent_parser_enhanced.py`
- [ ] `tests/unit/simple_mode/test_nl_handler_enhanced.py`
- [ ] `tests/integration/simple_mode/test_simple_mode_intent_detection.py`
- [ ] `tests/e2e/test_framework_improvements_workflow.py`

### ⏳ Test Implementation Pending

All test files need to be created and implemented. This is the next step after this planning document.

## Test Execution

### Running Tests

```bash
# Run all unit tests
pytest tests/unit/core/test_code_validator.py -v
pytest tests/unit/core/test_module_path_sanitizer.py -v
pytest tests/unit/simple_mode/ -v

# Run integration tests
pytest tests/integration/simple_mode/ -v

# Run E2E tests
pytest tests/e2e/test_framework_improvements_workflow.py -v

# Run with coverage
pytest --cov=tapps_agents.core.code_validator --cov=tapps_agents.core.module_path_sanitizer --cov=tapps_agents.simple_mode --cov-report=html
```

### Coverage Targets

- **CodeValidator:** ≥90%
- **ModulePathSanitizer:** ≥90%
- **IntentParser (enhanced):** ≥85%
- **SimpleModeHandler (enhanced):** ≥80%
- **Overall:** ≥80%

## Test Data

### Sample Code for Validation Tests

```python
# Valid Python code
VALID_CODE = """
def hello():
    print("world")
"""

# Invalid Python code (missing colon)
INVALID_CODE_MISSING_COLON = """
def hello()
    print("world")
"""

# Invalid Python code (unclosed parenthesis)
INVALID_CODE_UNCLOSED_PAREN = """
def hello(
    print("world")
"""

# Invalid import (hyphens)
INVALID_IMPORT = """
from services.ai-automation-service-new.src.database import *
"""
```

### Sample Module Paths for Sanitization Tests

```python
# Test cases
TEST_PATHS = [
    ("services.ai-automation-service-new", "services.ai_automation_service_new"),
    ("services.ai-automation-service-new.src.database", "services.ai_automation_service_new.src.database"),
    ("services.ai-automation-service-new.src.database.__init__", "services.ai_automation_service_new.src.database.__init__"),
    ("test-module-123", "test_module_123"),
]
```

## Next Steps

1. **Create test files** with test structure
2. **Implement unit tests** for all utilities
3. **Implement integration tests** for Simple Mode
4. **Implement E2E tests** for complete workflow
5. **Run tests and verify coverage** ≥80%
6. **Fix any failing tests**
7. **Update test documentation**

## Success Criteria

- ✅ All test files created
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ All E2E tests passing
- ✅ Coverage ≥80% for all modules
- ✅ No test failures or warnings

---

**Document Version:** 1.0  
**Last Updated:** January 16, 2025  
**Status:** Test Planning Complete - Ready for Test Implementation
