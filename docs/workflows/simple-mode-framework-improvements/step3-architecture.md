# Step 3: Architecture Design

**Date:** January 16, 2025  
**Workflow:** Full SDLC - Framework Improvements Based on Usage Analysis  
**Step:** Architecture Design  
**Agent:** @architect

## Executive Summary

This document describes the architecture for implementing the critical framework improvements: Simple Mode intent detection, code generation validation, module path sanitization, and workflow enforcement.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Request Layer                         │
│  (Cursor Skills / CLI / Natural Language)                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Simple Mode Intent Detection                      │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ IntentParser (Enhanced)                              │    │
│  │  - detect_simple_mode_intent()                       │    │
│  │  - force_simple_mode_workflow()                       │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Code Generation Layer                             │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ TestGenerator    │  │ ImplementerAgent  │                │
│  │  + validation    │  │  + validation    │                │
│  └────────┬─────────┘  └────────┬─────────┘                │
│           │                      │                            │
│           └──────────┬───────────┘                           │
│                      ▼                                        │
│           ┌──────────────────────┐                            │
│           │ CodeValidator        │                            │
│           │  - validate_syntax() │                            │
│           │  - fix_errors()     │                            │
│           └──────────────────────┘                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Module Path Sanitization                         │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ModulePathSanitizer                                  │    │
│  │  - sanitize_module_path()                            │    │
│  │  - sanitize_import_statement()                       │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Workflow Enforcement                             │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ WorkflowEnforcer                                     │    │
│  │  - detect_workflow_task()                           │    │
│  │  - suggest_simple_mode()                             │    │
│  │  - warn_bypass()                                     │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Enhanced Intent Parser

**Location:** `tapps_agents/simple_mode/intent_parser.py`

**Changes:**
- Add `detect_simple_mode_intent()` method
- Add Simple Mode keyword detection
- Add confidence scoring for Simple Mode intent
- Update `parse()` to check for Simple Mode keywords first

**Design:**
```python
class IntentParser:
    def __init__(self):
        # Existing keyword mappings...
        
        # Simple Mode intent keywords
        self.simple_mode_keywords = [
            "@simple-mode", "simple mode", "use simple mode",
            "simple-mode", "@simple_mode", "simple_mode"
        ]
    
    def detect_simple_mode_intent(self, text: str) -> bool:
        """Detect if user wants Simple Mode."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.simple_mode_keywords)
    
    def parse(self, input_text: str) -> Intent:
        # Check for Simple Mode intent first
        if self.detect_simple_mode_intent(input_text):
            # Force Simple Mode workflow
            return Intent(
                type=IntentType.BUILD,  # or detected type
                confidence=1.0,
                parameters={"force_simple_mode": True},
                original_input=input_text,
            )
        # ... existing parsing logic
```

### 2. Code Validator Utility

**Location:** `tapps_agents/core/code_validator.py` (NEW)

**Purpose:** Validate generated code for syntax errors before writing to files.

**Design:**
```python
import ast
from enum import Enum
from typing import Any

class ValidationResult:
    """Result of code validation."""
    is_valid: bool
    error_message: str | None
    error_line: int | None
    error_type: str | None
    suggested_fix: str | None

class CodeValidator:
    """Validates generated code for syntax errors."""
    
    def validate_python(self, code: str) -> ValidationResult:
        """Validate Python code syntax."""
        try:
            ast.parse(code)
            return ValidationResult(
                is_valid=True,
                error_message=None,
                error_line=None,
                error_type=None,
                suggested_fix=None,
            )
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                error_message=str(e),
                error_line=e.lineno,
                error_type="SyntaxError",
                suggested_fix=self._suggest_fix(e),
            )
    
    def validate_typescript(self, code: str) -> ValidationResult:
        """Validate TypeScript code syntax."""
        # Use TypeScript compiler or parser
        # ...
    
    def _suggest_fix(self, error: SyntaxError) -> str | None:
        """Suggest fix for syntax error."""
        # Common fixes:
        # - Missing colon
        # - Unclosed brackets
        # - Invalid import syntax
        # ...
```

**Integration Points:**
- `TestGenerator.prepare_unit_tests()` - Validate before creating instruction
- `ImplementerAgent.implement()` - Validate before writing file
- `TestGenerator._generate_test_code()` - Validate generated test code

### 3. Module Path Sanitizer Utility

**Location:** `tapps_agents/core/module_path_sanitizer.py` (NEW)

**Purpose:** Sanitize module paths to replace invalid characters (hyphens, special chars) with valid Python identifiers.

**Design:**
```python
import re
from pathlib import Path

class ModulePathSanitizer:
    """Sanitizes module paths for Python imports."""
    
    def sanitize_module_path(self, path: str) -> str:
        """
        Sanitize module path for Python imports.
        
        Args:
            path: Module path (e.g., "services.ai-automation-service-new.src.database")
        
        Returns:
            Sanitized path (e.g., "services.ai_automation_service_new.src.database")
        """
        # Replace hyphens with underscores
        sanitized = path.replace("-", "_")
        
        # Remove invalid characters (keep only alphanumeric, dots, underscores)
        sanitized = re.sub(r'[^a-zA-Z0-9_.]', '_', sanitized)
        
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        return sanitized
    
    def sanitize_import_statement(self, import_stmt: str) -> str:
        """
        Sanitize an import statement.
        
        Args:
            import_stmt: Import statement (e.g., "from services.ai-automation-service-new.src.database import *")
        
        Returns:
            Sanitized import statement
        """
        # Extract module path from import statement
        # Pattern: "from <module_path> import ..."
        pattern = r'from\s+([^\s]+)\s+import'
        match = re.search(pattern, import_stmt)
        if match:
            module_path = match.group(1)
            sanitized_path = self.sanitize_module_path(module_path)
            return import_stmt.replace(module_path, sanitized_path)
        return import_stmt
```

**Integration Points:**
- `TestGenerator.prepare_unit_tests()` - Sanitize module paths in test imports
- `TestGenerator._generate_test_code()` - Sanitize import statements
- Any code generation that creates import statements

### 4. Enhanced Simple Mode Handler

**Location:** `tapps_agents/simple_mode/nl_handler.py`

**Changes:**
- Check for Simple Mode intent before parsing
- Force Simple Mode workflow when detected
- Provide clear error if Simple Mode not available

**Design:**
```python
class SimpleModeHandler:
    async def handle(self, command: str) -> dict[str, Any]:
        # Check for Simple Mode intent
        if self.intent_parser.detect_simple_mode_intent(command):
            # Force Simple Mode workflow
            if not self.config.simple_mode.enabled:
                return {
                    "success": False,
                    "error": "Simple Mode requested but not available. Install with: `tapps-agents init`",
                    "suggestion": "Run: tapps-agents simple-mode on",
                }
            
            # Parse intent with Simple Mode forced
            intent = self.intent_parser.parse(command)
            intent.parameters["force_simple_mode"] = True
            
            # Execute with Simple Mode orchestrator
            orchestrator = self.orchestrators.get(intent.type)
            if not orchestrator:
                return {
                    "success": False,
                    "error": f"Unknown intent type: {intent.type}",
                }
            
            result = await orchestrator.execute(intent, intent.parameters)
            result["simple_mode_forced"] = True
            return result
        
        # ... existing handling logic
```

### 5. Workflow Enforcer

**Location:** `tapps_agents/simple_mode/workflow_enforcer.py` (NEW)

**Purpose:** Detect workflow-style tasks and suggest/enforce Simple Mode usage.

**Design:**
```python
class WorkflowEnforcer:
    """Enforces Simple Mode workflow usage when appropriate."""
    
    def __init__(self, config: ProjectConfig):
        self.config = config
        self.workflow_keywords = [
            "build", "create", "implement", "develop",
            "fix", "debug", "resolve",
            "review", "analyze", "check",
            "test", "generate tests",
        ]
    
    def detect_workflow_task(self, command: str) -> bool:
        """Detect if command is a workflow-style task."""
        command_lower = command.lower()
        return any(keyword in command_lower for keyword in self.workflow_keywords)
    
    def suggest_simple_mode(self, command: str) -> dict[str, Any]:
        """Suggest Simple Mode for workflow-style tasks."""
        if self.detect_workflow_task(command):
            return {
                "suggest_simple_mode": True,
                "message": "This looks like a workflow task. Consider using: @simple-mode *build \"...\"",
                "command_suggestion": self._generate_suggestion(command),
            }
        return {"suggest_simple_mode": False}
    
    def warn_bypass(self, command: str, used_cli: bool = True) -> dict[str, Any]:
        """Warn when workflow is bypassed."""
        if used_cli and self.detect_workflow_task(command):
            return {
                "warning": True,
                "message": "⚠️ Workflow-style task detected but CLI used. Consider using Simple Mode for better orchestration.",
                "suggestion": "Use: @simple-mode *build \"...\"",
            }
        return {"warning": False}
```

### 6. Enhanced Implementer Agent

**Location:** `tapps_agents/agents/implementer/agent.py`

**Changes:**
- Add code validation before writing
- Add module path sanitization for imports
- Write code directly (not just return instructions)

**Design:**
```python
from tapps_agents.core.code_validator import CodeValidator
from tapps_agents.core.module_path_sanitizer import ModulePathSanitizer

class ImplementerAgent:
    def __init__(self, ...):
        # ... existing init
        self.code_validator = CodeValidator()
        self.path_sanitizer = ModulePathSanitizer()
    
    async def implement(self, specification: str, file_path: str, ...):
        # ... existing code generation logic
        
        # Sanitize module paths in generated code
        generated_code = self.path_sanitizer.sanitize_import_statements(generated_code)
        
        # Validate generated code
        validation_result = self.code_validator.validate_python(generated_code)
        if not validation_result.is_valid:
            # Attempt to fix common errors
            generated_code = self._fix_code_errors(generated_code, validation_result)
            
            # Re-validate
            validation_result = self.code_validator.validate_python(generated_code)
            if not validation_result.is_valid:
                return {
                    "error": f"Generated code has syntax errors: {validation_result.error_message}",
                    "error_line": validation_result.error_line,
                    "suggested_fix": validation_result.suggested_fix,
                }
        
        # Write code directly (not just return instruction)
        path.write_text(generated_code, encoding="utf-8")
        
        return {
            "type": "implement",
            "file": str(path),
            "code": generated_code,
            "validated": True,
        }
```

### 7. Enhanced Test Generator

**Location:** `tapps_agents/agents/tester/test_generator.py`

**Changes:**
- Add code validation before creating test files
- Add module path sanitization for test imports
- Validate generated test code

**Design:**
```python
from tapps_agents.core.code_validator import CodeValidator
from tapps_agents.core.module_path_sanitizer import ModulePathSanitizer

class TestGenerator:
    def __init__(self):
        # ... existing init
        self.code_validator = CodeValidator()
        self.path_sanitizer = ModulePathSanitizer()
    
    def prepare_unit_tests(self, code_path: Path, ...):
        # ... existing logic
        
        # Sanitize module path for imports
        module_path = self._extract_module_path(code_path)
        sanitized_path = self.path_sanitizer.sanitize_module_path(module_path)
        
        # Use sanitized path in test generation instruction
        # ...
    
    def _generate_test_code(self, ...) -> str:
        """Generate test code with validation."""
        # Generate test code
        test_code = self._generate_code(...)
        
        # Sanitize import statements
        test_code = self.path_sanitizer.sanitize_import_statement(test_code)
        
        # Validate generated code
        validation_result = self.code_validator.validate_python(test_code)
        if not validation_result.is_valid:
            # Fix or regenerate
            test_code = self._fix_test_code(test_code, validation_result)
        
        return test_code
```

## Data Flow

### Simple Mode Intent Detection Flow

```
User Input: "@simple-mode build feature"
    │
    ▼
IntentParser.detect_simple_mode_intent()
    │
    ▼ (detected: True)
IntentParser.parse() → Intent(force_simple_mode=True)
    │
    ▼
SimpleModeHandler.handle() → Check Simple Mode enabled
    │
    ▼ (enabled: True)
BuildOrchestrator.execute()
    │
    ▼
Workflow execution with quality gates
```

### Code Generation with Validation Flow

```
Code Generation Request
    │
    ▼
Generate Code (LLM/Cursor Skills)
    │
    ▼
ModulePathSanitizer.sanitize_import_statements()
    │
    ▼
CodeValidator.validate_python()
    │
    ├─ Valid → Write to file
    └─ Invalid → Fix errors → Re-validate → Write to file
```

## Integration Points

### 1. Intent Parser Integration
- **File:** `tapps_agents/simple_mode/intent_parser.py`
- **Changes:** Add Simple Mode keyword detection
- **Impact:** Low (additive changes)

### 2. Simple Mode Handler Integration
- **File:** `tapps_agents/simple_mode/nl_handler.py`
- **Changes:** Check for Simple Mode intent, force workflow
- **Impact:** Low (additive changes)

### 3. Code Validator Integration
- **Files:** 
  - `tapps_agents/agents/implementer/agent.py`
  - `tapps_agents/agents/tester/test_generator.py`
- **Changes:** Validate code before writing
- **Impact:** Medium (requires validation logic)

### 4. Module Path Sanitizer Integration
- **Files:**
  - `tapps_agents/agents/tester/test_generator.py`
  - `tapps_agents/agents/implementer/agent.py`
- **Changes:** Sanitize module paths in imports
- **Impact:** Low (utility class integration)

## Performance Considerations

1. **Code Validation:** 
   - Use `ast.parse()` for Python (fast, < 10ms for typical files)
   - Cache validation results for identical code
   - Async validation for large files

2. **Module Path Sanitization:**
   - Simple regex operations (< 1ms)
   - No caching needed (deterministic)

3. **Intent Detection:**
   - Keyword matching (< 1ms)
   - No caching needed (stateless)

## Security Considerations

1. **Code Validation:**
   - Only validate syntax, don't execute code
   - Use `ast.parse()` (safe, no execution)
   - Limit validation to file size (< 10MB)

2. **Module Path Sanitization:**
   - Prevent path traversal
   - Validate sanitized paths
   - Use existing `PathValidator` for file operations

## Testing Strategy

1. **Unit Tests:**
   - `CodeValidator` - Test validation for various syntax errors
   - `ModulePathSanitizer` - Test sanitization for various path formats
   - `IntentParser` - Test Simple Mode intent detection
   - `WorkflowEnforcer` - Test workflow detection and suggestions

2. **Integration Tests:**
   - Test code generation with validation
   - Test test generation with sanitization
   - Test Simple Mode workflow enforcement

3. **E2E Tests:**
   - Test complete workflow with Simple Mode intent
   - Test code generation with validation and sanitization

## Migration Strategy

1. **Backward Compatibility:**
   - All changes are additive (no breaking changes)
   - Existing CLI commands continue to work
   - Simple Mode detection is opt-in (doesn't break existing behavior)

2. **Feature Flags:**
   - Add config option: `simple_mode.force_on_intent` (default: True)
   - Add config option: `code_generation.validate_before_write` (default: True)
   - Add config option: `code_generation.sanitize_module_paths` (default: True)

3. **Gradual Rollout:**
   - Phase 1: Add utilities (CodeValidator, ModulePathSanitizer)
   - Phase 2: Integrate into agents
   - Phase 3: Enable Simple Mode intent detection
   - Phase 4: Enable workflow enforcement

## Next Steps

1. **Step 4:** Design API specifications for new utilities
2. **Step 5:** Implement utilities and integrations
3. **Step 6:** Review and quality check
4. **Step 7:** Generate and run tests
5. **Step 8:** Security scan
6. **Step 9:** Document API

---

**Document Version:** 1.0  
**Last Updated:** January 16, 2025  
**Status:** Complete - Ready for API Design Phase
