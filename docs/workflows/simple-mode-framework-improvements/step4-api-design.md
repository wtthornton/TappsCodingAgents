# Step 4: API Design

**Date:** January 16, 2025  
**Workflow:** Full SDLC - Framework Improvements Based on Usage Analysis  
**Step:** API Design  
**Agent:** @designer

## Executive Summary

This document specifies the API interfaces for the new utilities: CodeValidator, ModulePathSanitizer, and enhanced IntentParser. All APIs follow existing TappsCodingAgents patterns and conventions.

## 1. CodeValidator API

### Location
`tapps_agents/core/code_validator.py`

### Class: `ValidationResult`

```python
@dataclass
class ValidationResult:
    """Result of code validation."""
    
    is_valid: bool
    """Whether the code is valid (no syntax errors)."""
    
    error_message: str | None = None
    """Error message if validation failed."""
    
    error_line: int | None = None
    """Line number where error occurred (1-indexed)."""
    
    error_column: int | None = None
    """Column number where error occurred (1-indexed)."""
    
    error_type: str | None = None
    """Type of error (e.g., 'SyntaxError', 'IndentationError')."""
    
    suggested_fix: str | None = None
    """Suggested fix for the error (if available)."""
    
    language: str = "python"
    """Language of the validated code."""
```

### Class: `CodeValidator`

```python
class CodeValidator:
    """
    Validates generated code for syntax errors before writing to files.
    
    Supports:
    - Python (using ast.parse)
    - TypeScript (using TypeScript compiler)
    - JavaScript (using esprima or similar)
    """
    
    def __init__(self):
        """Initialize code validator."""
        pass
    
    def validate(
        self,
        code: str,
        language: str = "python",
        file_path: str | Path | None = None,
    ) -> ValidationResult:
        """
        Validate code for syntax errors.
        
        Args:
            code: Code string to validate
            language: Language of the code (python, typescript, javascript)
            file_path: Optional file path for better error messages
        
        Returns:
            ValidationResult with validation status and error details
        
        Examples:
            >>> validator = CodeValidator()
            >>> result = validator.validate("def hello(): print('world')")
            >>> result.is_valid
            True
            
            >>> result = validator.validate("def hello( print('world')")
            >>> result.is_valid
            False
            >>> result.error_type
            'SyntaxError'
        """
        pass
    
    def validate_python(
        self,
        code: str,
        file_path: str | Path | None = None,
    ) -> ValidationResult:
        """
        Validate Python code syntax using ast.parse.
        
        Args:
            code: Python code string to validate
            file_path: Optional file path for better error messages
        
        Returns:
            ValidationResult with validation status
        
        Raises:
            ValueError: If code is empty or None
        """
        pass
    
    def validate_typescript(
        self,
        code: str,
        file_path: str | Path | None = None,
    ) -> ValidationResult:
        """
        Validate TypeScript code syntax.
        
        Args:
            code: TypeScript code string to validate
            file_path: Optional file path for better error messages
        
        Returns:
            ValidationResult with validation status
        
        Note:
            Requires TypeScript compiler (tsc) or parser library.
        """
        pass
    
    def validate_javascript(
        self,
        code: str,
        file_path: str | Path | None = None,
    ) -> ValidationResult:
        """
        Validate JavaScript code syntax.
        
        Args:
            code: JavaScript code string to validate
            file_path: Optional file path for better error messages
        
        Returns:
            ValidationResult with validation status
        """
        pass
    
    def suggest_fix(
        self,
        error: SyntaxError | Exception,
        code: str,
    ) -> str | None:
        """
        Suggest a fix for a syntax error.
        
        Args:
            error: The syntax error exception
            code: The code that caused the error
        
        Returns:
            Suggested fix string, or None if no suggestion available
        
        Examples:
            >>> validator = CodeValidator()
            >>> error = SyntaxError("invalid syntax", ("<string>", 1, 5, "def hello("))
            >>> fix = validator.suggest_fix(error, "def hello(")
            >>> fix
            "Missing closing parenthesis: def hello():"
        """
        pass
```

### Usage Examples

```python
from tapps_agents.core.code_validator import CodeValidator, ValidationResult

# Initialize validator
validator = CodeValidator()

# Validate Python code
result = validator.validate_python("def hello(): print('world')")
if result.is_valid:
    print("Code is valid!")
else:
    print(f"Syntax error at line {result.error_line}: {result.error_message}")
    if result.suggested_fix:
        print(f"Suggested fix: {result.suggested_fix}")

# Validate with file path (better error messages)
result = validator.validate_python(
    code="def hello(",
    file_path="src/hello.py",
)
```

## 2. ModulePathSanitizer API

### Location
`tapps_agents/core/module_path_sanitizer.py`

### Class: `ModulePathSanitizer`

```python
class ModulePathSanitizer:
    """
    Sanitizes module paths for Python imports.
    
    Replaces invalid characters (hyphens, special chars) with valid
    Python identifiers (underscores).
    
    Examples:
        >>> sanitizer = ModulePathSanitizer()
        >>> sanitizer.sanitize_module_path("services.ai-automation-service-new.src.database")
        'services.ai_automation_service_new.src.database'
        
        >>> sanitizer.sanitize_import_statement("from services.ai-automation-service-new.src.database import *")
        'from services.ai_automation_service_new.src.database import *'
    """
    
    def __init__(self):
        """Initialize module path sanitizer."""
        pass
    
    def sanitize_module_path(self, path: str) -> str:
        """
        Sanitize module path for Python imports.
        
        Args:
            path: Module path (e.g., "services.ai-automation-service-new.src.database")
        
        Returns:
            Sanitized path (e.g., "services.ai_automation_service_new.src.database")
        
        Rules:
        - Replace hyphens (-) with underscores (_)
        - Remove invalid characters (keep only alphanumeric, dots, underscores)
        - Remove consecutive underscores
        - Remove leading/trailing underscores
        
        Examples:
            >>> sanitizer = ModulePathSanitizer()
            >>> sanitizer.sanitize_module_path("services.ai-automation-service-new")
            'services.ai_automation_service_new'
            
            >>> sanitizer.sanitize_module_path("services.ai-automation-service-new.src.database")
            'services.ai_automation_service_new.src.database'
            
            >>> sanitizer.sanitize_module_path("services.ai-automation-service-new.src.database.__init__")
            'services.ai_automation_service_new.src.database.__init__'
        """
        pass
    
    def sanitize_import_statement(self, import_stmt: str) -> str:
        """
        Sanitize an import statement.
        
        Args:
            import_stmt: Import statement (e.g., "from services.ai-automation-service-new.src.database import *")
        
        Returns:
            Sanitized import statement
        
        Examples:
            >>> sanitizer = ModulePathSanitizer()
            >>> sanitizer.sanitize_import_statement("from services.ai-automation-service-new.src.database import *")
            'from services.ai_automation_service_new.src.database import *'
            
            >>> sanitizer.sanitize_import_statement("import services.ai-automation-service-new.src.database")
            'import services.ai_automation_service_new.src.database'
        """
        pass
    
    def sanitize_imports_in_code(self, code: str) -> str:
        """
        Sanitize all import statements in code.
        
        Args:
            code: Code string containing import statements
        
        Returns:
            Code with sanitized import statements
        
        Examples:
            >>> sanitizer = ModulePathSanitizer()
            >>> code = '''
            ... from services.ai-automation-service-new.src.database import *
            ... import services.ai-automation-service-new.src.models
            ... '''
            >>> sanitized = sanitizer.sanitize_imports_in_code(code)
            >>> "ai_automation_service_new" in sanitized
            True
        """
        pass
    
    def is_valid_python_identifier(self, identifier: str) -> bool:
        """
        Check if a string is a valid Python identifier.
        
        Args:
            identifier: String to check
        
        Returns:
            True if valid Python identifier, False otherwise
        
        Examples:
            >>> sanitizer = ModulePathSanitizer()
            >>> sanitizer.is_valid_python_identifier("hello_world")
            True
            >>> sanitizer.is_valid_python_identifier("hello-world")
            False
            >>> sanitizer.is_valid_python_identifier("123hello")
            False
        """
        pass
```

### Usage Examples

```python
from tapps_agents.core.module_path_sanitizer import ModulePathSanitizer

# Initialize sanitizer
sanitizer = ModulePathSanitizer()

# Sanitize module path
path = "services.ai-automation-service-new.src.database"
sanitized = sanitizer.sanitize_module_path(path)
# Result: "services.ai_automation_service_new.src.database"

# Sanitize import statement
import_stmt = "from services.ai-automation-service-new.src.database import *"
sanitized_stmt = sanitizer.sanitize_import_statement(import_stmt)
# Result: "from services.ai_automation_service_new.src.database import *"

# Sanitize all imports in code
code = """
from services.ai-automation-service-new.src.database import *
import services.ai-automation-service-new.src.models
"""
sanitized_code = sanitizer.sanitize_imports_in_code(code)
```

## 3. Enhanced IntentParser API

### Location
`tapps_agents/simple_mode/intent_parser.py`

### Enhanced Methods

```python
class IntentParser:
    """Parse natural language input into structured intents."""
    
    # ... existing methods ...
    
    def detect_simple_mode_intent(self, text: str) -> bool:
        """
        Detect if user wants Simple Mode.
        
        Args:
            text: User input text
        
        Returns:
            True if Simple Mode intent detected, False otherwise
        
        Examples:
            >>> parser = IntentParser()
            >>> parser.detect_simple_mode_intent("@simple-mode build feature")
            True
            >>> parser.detect_simple_mode_intent("use simple mode to create api")
            True
            >>> parser.detect_simple_mode_intent("build feature")
            False
        """
        pass
    
    def parse(self, input_text: str) -> Intent:
        """
        Parse natural language input into a structured intent.
        
        Enhanced to detect Simple Mode intent and force Simple Mode workflow.
        
        Args:
            input_text: User's natural language command
        
        Returns:
            Intent object with type, confidence, and parameters
        
        Changes:
        - Checks for Simple Mode intent first
        - Sets force_simple_mode=True in parameters if detected
        - Returns Intent with confidence=1.0 for explicit Simple Mode requests
        """
        pass
```

### Usage Examples

```python
from tapps_agents.simple_mode.intent_parser import IntentParser

# Initialize parser
parser = IntentParser()

# Detect Simple Mode intent
if parser.detect_simple_mode_intent("@simple-mode build feature"):
    print("Simple Mode intent detected!")

# Parse with Simple Mode detection
intent = parser.parse("@simple-mode build user authentication")
# intent.parameters["force_simple_mode"] == True
# intent.confidence == 1.0
```

## 4. Enhanced SimpleModeHandler API

### Location
`tapps_agents/simple_mode/nl_handler.py`

### Enhanced Methods

```python
class SimpleModeHandler:
    """Handler for natural language commands in Simple Mode."""
    
    # ... existing methods ...
    
    async def handle(self, command: str) -> dict[str, Any]:
        """
        Handle a natural language command.
        
        Enhanced to detect and force Simple Mode when requested.
        
        Args:
            command: User's natural language command
        
        Returns:
            Dictionary with execution results
        
        Changes:
        - Checks for Simple Mode intent before parsing
        - Forces Simple Mode workflow when detected
        - Provides clear error if Simple Mode not available
        - Sets simple_mode_forced=True in result if forced
        """
        pass
    
    def is_simple_mode_available(self) -> bool:
        """
        Check if Simple Mode is available and enabled.
        
        Returns:
            True if Simple Mode is available, False otherwise
        """
        pass
```

### Usage Examples

```python
from tapps_agents.simple_mode.nl_handler import SimpleModeHandler

# Initialize handler
handler = SimpleModeHandler()

# Check availability
if not handler.is_simple_mode_available():
    print("Simple Mode not available. Run: tapps-agents simple-mode on")

# Handle command with Simple Mode intent
result = await handler.handle("@simple-mode build user authentication")
if result.get("simple_mode_forced"):
    print("Simple Mode workflow was forced!")
```

## 5. WorkflowEnforcer API

### Location
`tapps_agents/simple_mode/workflow_enforcer.py` (NEW)

### Class: `WorkflowEnforcer`

```python
class WorkflowEnforcer:
    """
    Enforces Simple Mode workflow usage when appropriate.
    
    Detects workflow-style tasks and suggests/enforces Simple Mode usage.
    """
    
    def __init__(self, config: ProjectConfig | None = None):
        """
        Initialize workflow enforcer.
        
        Args:
            config: Optional project configuration
        """
        pass
    
    def detect_workflow_task(self, command: str) -> bool:
        """
        Detect if command is a workflow-style task.
        
        Args:
            command: User command text
        
        Returns:
            True if workflow task detected, False otherwise
        
        Examples:
            >>> enforcer = WorkflowEnforcer()
            >>> enforcer.detect_workflow_task("build user authentication")
            True
            >>> enforcer.detect_workflow_task("fix the error in auth.py")
            True
            >>> enforcer.detect_workflow_task("what is the weather?")
            False
        """
        pass
    
    def suggest_simple_mode(
        self,
        command: str,
    ) -> dict[str, Any]:
        """
        Suggest Simple Mode for workflow-style tasks.
        
        Args:
            command: User command text
        
        Returns:
            Dictionary with suggestion details
        
        Examples:
            >>> enforcer = WorkflowEnforcer()
            >>> result = enforcer.suggest_simple_mode("build user authentication")
            >>> result["suggest_simple_mode"]
            True
            >>> result["command_suggestion"]
            '@simple-mode *build "user authentication"'
        """
        pass
    
    def warn_bypass(
        self,
        command: str,
        used_cli: bool = True,
    ) -> dict[str, Any]:
        """
        Warn when workflow is bypassed.
        
        Args:
            command: User command text
            used_cli: Whether CLI was used instead of Simple Mode
        
        Returns:
            Dictionary with warning details
        
        Examples:
            >>> enforcer = WorkflowEnforcer()
            >>> result = enforcer.warn_bypass("build feature", used_cli=True)
            >>> result["warning"]
            True
            >>> result["message"]
            '⚠️ Workflow-style task detected but CLI used. Consider using Simple Mode...'
        """
        pass
```

### Usage Examples

```python
from tapps_agents.simple_mode.workflow_enforcer import WorkflowEnforcer

# Initialize enforcer
enforcer = WorkflowEnforcer()

# Detect workflow task
if enforcer.detect_workflow_task("build user authentication"):
    suggestion = enforcer.suggest_simple_mode("build user authentication")
    if suggestion["suggest_simple_mode"]:
        print(suggestion["message"])
        print(f"Try: {suggestion['command_suggestion']}")

# Warn about bypass
warning = enforcer.warn_bypass("build feature", used_cli=True)
if warning["warning"]:
    print(warning["message"])
```

## 6. Integration APIs

### ImplementerAgent Integration

```python
from tapps_agents.core.code_validator import CodeValidator
from tapps_agents.core.module_path_sanitizer import ModulePathSanitizer

class ImplementerAgent:
    def __init__(self, ...):
        # ... existing init
        self.code_validator = CodeValidator()
        self.path_sanitizer = ModulePathSanitizer()
    
    async def implement(self, specification: str, file_path: str, ...):
        # Generate code
        generated_code = await self._generate_code(...)
        
        # Sanitize module paths
        generated_code = self.path_sanitizer.sanitize_imports_in_code(generated_code)
        
        # Validate code
        validation_result = self.code_validator.validate_python(generated_code)
        if not validation_result.is_valid:
            # Handle validation error
            return {
                "error": f"Generated code has syntax errors: {validation_result.error_message}",
                "error_line": validation_result.error_line,
                "suggested_fix": validation_result.suggested_fix,
            }
        
        # Write code directly
        path.write_text(generated_code, encoding="utf-8")
        
        return {
            "type": "implement",
            "file": str(path),
            "validated": True,
        }
```

### TestGenerator Integration

```python
from tapps_agents.core.code_validator import CodeValidator
from tapps_agents.core.module_path_sanitizer import ModulePathSanitizer

class TestGenerator:
    def __init__(self):
        # ... existing init
        self.code_validator = CodeValidator()
        self.path_sanitizer = ModulePathSanitizer()
    
    def prepare_unit_tests(self, code_path: Path, ...):
        # Extract module path
        module_path = self._extract_module_path(code_path)
        
        # Sanitize module path
        sanitized_path = self.path_sanitizer.sanitize_module_path(module_path)
        
        # Use sanitized path in test generation
        # ...
    
    def _generate_test_code(self, ...) -> str:
        # Generate test code
        test_code = self._generate_code(...)
        
        # Sanitize imports
        test_code = self.path_sanitizer.sanitize_imports_in_code(test_code)
        
        # Validate code
        validation_result = self.code_validator.validate_python(test_code)
        if not validation_result.is_valid:
            # Fix or regenerate
            test_code = self._fix_test_code(test_code, validation_result)
        
        return test_code
```

## Error Handling

All APIs follow existing TappsCodingAgents error handling patterns:

1. **Validation Errors:** Return `ValidationResult` with error details
2. **Sanitization Errors:** Return sanitized string (never raise exceptions)
3. **Intent Detection Errors:** Return `Intent` with `confidence=0.0` and `type=UNKNOWN`
4. **Workflow Errors:** Return dictionary with `success=False` and error message

## Configuration

All new features are configurable via `.tapps-agents/config.yaml`:

```yaml
simple_mode:
  enabled: true
  force_on_intent: true  # Force Simple Mode when intent detected
  enforce_workflows: true  # Enforce workflow usage

code_generation:
  validate_before_write: true  # Validate code before writing
  sanitize_module_paths: true  # Sanitize module paths in imports
  auto_fix_errors: true  # Attempt to fix common errors automatically
```

## Next Steps

1. **Step 5:** Implement utilities and integrations
2. **Step 6:** Review and quality check
3. **Step 7:** Generate and run tests
4. **Step 8:** Security scan
5. **Step 9:** Document API

---

**Document Version:** 1.0  
**Last Updated:** January 16, 2025  
**Status:** Complete - Ready for Implementation Phase
