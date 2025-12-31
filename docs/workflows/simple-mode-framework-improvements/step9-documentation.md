# Step 9: Documentation

**Date:** January 16, 2025  
**Workflow:** Full SDLC - Framework Improvements Based on Usage Analysis  
**Step:** Documentation  
**Agent:** @documenter

## Executive Summary

This document provides comprehensive API documentation and usage examples for the implemented framework improvements: CodeValidator, ModulePathSanitizer, and enhanced Simple Mode intent detection.

## API Documentation

### 1. CodeValidator API

**Location:** `tapps_agents.core.code_validator`

**Purpose:** Validates generated code for syntax errors before writing to files.

#### Classes

##### `ValidationResult`

Result of code validation.

```python
@dataclass
class ValidationResult:
    is_valid: bool
    error_message: str | None = None
    error_line: int | None = None
    error_column: int | None = None
    error_type: str | None = None
    suggested_fix: str | None = None
    language: str = "python"
```

**Fields:**
- `is_valid` (bool): Whether the code is valid (no syntax errors)
- `error_message` (str | None): Error message if validation failed
- `error_line` (int | None): Line number where error occurred (1-indexed)
- `error_column` (int | None): Column number where error occurred (1-indexed)
- `error_type` (str | None): Type of error (e.g., 'SyntaxError', 'IndentationError')
- `suggested_fix` (str | None): Suggested fix for the error (if available)
- `language` (str): Language of the validated code

##### `CodeValidator`

Validates generated code for syntax errors.

```python
class CodeValidator:
    def validate(
        self,
        code: str,
        language: str = "python",
        file_path: str | Path | None = None,
    ) -> ValidationResult:
        """Validate code for syntax errors."""
    
    def validate_python(
        self,
        code: str,
        file_path: str | Path | None = None,
    ) -> ValidationResult:
        """Validate Python code syntax using ast.parse."""
    
    def suggest_fix(
        self,
        error: SyntaxError | Exception,
        code: str,
    ) -> str | None:
        """Suggest a fix for a syntax error."""
```

#### Usage Examples

**Basic Validation:**
```python
from tapps_agents.core.code_validator import CodeValidator

validator = CodeValidator()

# Validate Python code
code = """
def hello():
    print("world")
"""
result = validator.validate_python(code)
if result.is_valid:
    print("Code is valid!")
else:
    print(f"Syntax error at line {result.error_line}: {result.error_message}")
    if result.suggested_fix:
        print(f"Suggested fix: {result.suggested_fix}")
```

**Error Handling:**
```python
# Invalid code
invalid_code = "def hello( print('world')"
result = validator.validate_python(invalid_code)
if not result.is_valid:
    print(f"Error: {result.error_type}")
    print(f"Line: {result.error_line}, Column: {result.error_column}")
    print(f"Message: {result.error_message}")
    if result.suggested_fix:
        print(f"Fix: {result.suggested_fix}")
```

**With File Path:**
```python
result = validator.validate_python(code, file_path="src/app.py")
# Better error messages with file context
```

### 2. ModulePathSanitizer API

**Location:** `tapps_agents.core.module_path_sanitizer`

**Purpose:** Sanitizes module paths for Python imports (replaces hyphens with underscores).

#### Classes

##### `ModulePathSanitizer`

Sanitizes module paths for Python imports.

```python
class ModulePathSanitizer:
    def sanitize_module_path(self, path: str) -> str:
        """Sanitize module path for Python imports."""
    
    def sanitize_import_statement(self, import_stmt: str) -> str:
        """Sanitize an import statement."""
    
    def sanitize_imports_in_code(self, code: str) -> str:
        """Sanitize all import statements in code."""
    
    def is_valid_python_identifier(self, identifier: str) -> bool:
        """Check if a string is a valid Python identifier."""
```

#### Usage Examples

**Module Path Sanitization:**
```python
from tapps_agents.core.module_path_sanitizer import ModulePathSanitizer

sanitizer = ModulePathSanitizer()

# Sanitize module path
path = "services.ai-automation-service-new"
sanitized = sanitizer.sanitize_module_path(path)
# Result: "services.ai_automation_service_new"
```

**Import Statement Sanitization:**
```python
# Sanitize import statement
import_stmt = "from services.ai-automation-service-new.src.database import *"
sanitized = sanitizer.sanitize_import_statement(import_stmt)
# Result: "from services.ai_automation_service_new.src.database import *"
```

**Code Sanitization:**
```python
# Sanitize all imports in code
code = """
from services.ai-automation-service-new.src.database import *
import services.ai-automation-service-new.src.models
"""
sanitized = sanitizer.sanitize_imports_in_code(code)
# All hyphens replaced with underscores
```

**Identifier Validation:**
```python
# Check if identifier is valid
assert sanitizer.is_valid_python_identifier("hello_world") is True
assert sanitizer.is_valid_python_identifier("hello-world") is False
```

### 3. Enhanced IntentParser API

**Location:** `tapps_agents.simple_mode.intent_parser`

**Purpose:** Detects Simple Mode intent and forces Simple Mode workflow when requested.

#### Classes

##### `IntentParser`

Parse natural language input into structured intents.

```python
class IntentParser:
    def detect_simple_mode_intent(self, text: str) -> bool:
        """Detect if user wants Simple Mode."""
    
    def parse(self, input_text: str) -> Intent:
        """Parse natural language input into a structured intent."""
```

#### Usage Examples

**Simple Mode Intent Detection:**
```python
from tapps_agents.simple_mode.intent_parser import IntentParser

parser = IntentParser()

# Detect Simple Mode intent
if parser.detect_simple_mode_intent("@simple-mode build feature"):
    print("Simple Mode intent detected!")

# Parse with Simple Mode detection
intent = parser.parse("@simple-mode build user authentication")
# intent.parameters["force_simple_mode"] == True
```

### 4. Enhanced SimpleModeHandler API

**Location:** `tapps_agents.simple_mode.nl_handler`

**Purpose:** Forces Simple Mode workflow when Simple Mode intent is detected.

#### Classes

##### `SimpleModeHandler`

Handler for natural language commands in Simple Mode.

```python
class SimpleModeHandler:
    async def handle(self, command: str) -> dict[str, Any]:
        """Handle a natural language command."""
    
    def is_simple_mode_available(self) -> bool:
        """Check if Simple Mode is available and enabled."""
```

#### Usage Examples

**Simple Mode Handling:**
```python
from tapps_agents.simple_mode.nl_handler import SimpleModeHandler

handler = SimpleModeHandler()

# Check availability
if not handler.is_simple_mode_available():
    print("Simple Mode not available. Run: tapps-agents simple-mode on")

# Handle command with Simple Mode intent
result = await handler.handle("@simple-mode build user authentication")
if result.get("simple_mode_forced"):
    print("Simple Mode workflow was forced!")
```

## Integration Examples

### Using CodeValidator in Code Generation

```python
from tapps_agents.core.code_validator import CodeValidator
from tapps_agents.core.module_path_sanitizer import ModulePathSanitizer

validator = CodeValidator()
sanitizer = ModulePathSanitizer()

# Generate code
generated_code = generate_code_from_specification(...)

# Sanitize module paths
generated_code = sanitizer.sanitize_imports_in_code(generated_code)

# Validate code
result = validator.validate_python(generated_code)
if not result.is_valid:
    # Handle validation error
    raise ValueError(f"Generated code has syntax errors: {result.error_message}")

# Write code (only if valid)
path.write_text(generated_code, encoding="utf-8")
```

### Using ModulePathSanitizer in Test Generation

```python
from tapps_agents.core.module_path_sanitizer import ModulePathSanitizer

sanitizer = ModulePathSanitizer()

# Extract module path from source file
module_path = extract_module_path(source_file)

# Sanitize module path
sanitized_path = sanitizer.sanitize_module_path(module_path)

# Use in test import
test_code = f"""
from {sanitized_path} import *
"""
```

### Using Simple Mode Intent Detection

```python
from tapps_agents.simple_mode.intent_parser import IntentParser
from tapps_agents.simple_mode.nl_handler import SimpleModeHandler

parser = IntentParser()
handler = SimpleModeHandler()

# Check for Simple Mode intent
user_input = "@simple-mode build feature"
if parser.detect_simple_mode_intent(user_input):
    # Force Simple Mode workflow
    result = await handler.handle(user_input)
    if result.get("simple_mode_forced"):
        print("Simple Mode workflow executed!")
```

## Migration Guide

### For Existing Code

**No breaking changes** - all changes are additive and backward compatible.

### For New Code

1. **Use CodeValidator** when generating code:
   ```python
   from tapps_agents.core.code_validator import CodeValidator
   validator = CodeValidator()
   result = validator.validate_python(generated_code)
   ```

2. **Use ModulePathSanitizer** when creating imports:
   ```python
   from tapps_agents.core.module_path_sanitizer import ModulePathSanitizer
   sanitizer = ModulePathSanitizer()
   sanitized = sanitizer.sanitize_module_path(module_path)
   ```

3. **Check for Simple Mode intent** when processing user input:
   ```python
   from tapps_agents.simple_mode.intent_parser import IntentParser
   parser = IntentParser()
   if parser.detect_simple_mode_intent(user_input):
       # Force Simple Mode workflow
   ```

## Best Practices

### Code Validation

1. **Always validate before writing:**
   ```python
   result = validator.validate_python(code)
   if not result.is_valid:
       # Don't write invalid code
       return {"error": result.error_message}
   ```

2. **Use file paths for better errors:**
   ```python
   result = validator.validate_python(code, file_path="src/app.py")
   ```

3. **Check suggested fixes:**
   ```python
   if result.suggested_fix:
       # Try to apply fix automatically
   ```

### Module Path Sanitization

1. **Sanitize before creating imports:**
   ```python
   sanitized = sanitizer.sanitize_module_path(module_path)
   import_stmt = f"from {sanitized} import *"
   ```

2. **Sanitize entire code blocks:**
   ```python
   sanitized_code = sanitizer.sanitize_imports_in_code(code)
   ```

3. **Validate identifiers:**
   ```python
   if not sanitizer.is_valid_python_identifier(identifier):
       # Fix identifier
   ```

### Simple Mode Intent Detection

1. **Check intent before parsing:**
   ```python
   if parser.detect_simple_mode_intent(user_input):
       # Force Simple Mode
   ```

2. **Respect user intent:**
   ```python
   if intent.parameters.get("force_simple_mode"):
       # Don't fall back to CLI
   ```

3. **Provide clear errors:**
   ```python
   if not handler.is_simple_mode_available():
       return {"error": "Simple Mode not available. Run: tapps-agents simple-mode on"}
   ```

## Troubleshooting

### Code Validation Issues

**Problem:** Validation returns `is_valid=False` but code looks correct.

**Solution:**
- Check error message and line number
- Verify Python version compatibility
- Check for hidden characters or encoding issues

**Problem:** Suggested fix is not helpful.

**Solution:**
- The fix suggestion is a best-effort attempt
- Use error message and line number for manual fixing
- Consider regenerating code if validation fails

### Module Path Sanitization Issues

**Problem:** Sanitized path doesn't match actual module structure.

**Solution:**
- Verify actual module structure in file system
- Check if module uses hyphens in directory names
- Consider using relative imports instead

**Problem:** Special identifiers (`__init__`) are being modified.

**Solution:**
- The sanitizer preserves `__init__` and `__main__`
- If other special identifiers are modified, report as bug

### Simple Mode Intent Detection Issues

**Problem:** Simple Mode intent not detected.

**Solution:**
- Check keyword spelling: "@simple-mode", "simple mode", "use simple mode"
- Case insensitive, but must match exactly
- Check if Simple Mode is enabled in config

**Problem:** Simple Mode forced but workflow doesn't execute.

**Solution:**
- Check if Simple Mode is enabled: `handler.is_simple_mode_available()`
- Verify orchestrators are initialized
- Check error messages in result

## Related Documentation

- **Architecture:** `docs/workflows/simple-mode-framework-improvements/step3-architecture.md`
- **API Design:** `docs/workflows/simple-mode-framework-improvements/step4-api-design.md`
- **Implementation:** `docs/workflows/simple-mode-framework-improvements/step5-implementation.md`
- **Code Review:** `docs/workflows/simple-mode-framework-improvements/step6-review.md`
- **Testing:** `docs/workflows/simple-mode-framework-improvements/step7-testing.md`
- **Security:** `docs/workflows/simple-mode-framework-improvements/step8-security-scan.md`

## Next Steps

1. **Agent Integration:** Integrate utilities into ImplementerAgent and TestGenerator
2. **Workflow Enforcement:** Implement WorkflowEnforcer utility
3. **Workflow Artifacts:** Implement workflow artifact generation
4. **Error Messages:** Improve error message formatting

---

**Document Version:** 1.0  
**Last Updated:** January 16, 2025  
**Status:** Documentation Complete - Ready for Production
