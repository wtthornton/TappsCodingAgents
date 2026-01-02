# Step 4: Component Design - Phase 1: Critical Fixes

**Generated**: 2025-01-16  
**Workflow**: Build - Phase 1 Critical Fixes Implementation  
**Agent**: @designer

---

## Component Design Specifications

### 1. CommandValidator Class

**Location**: `tapps_agents/cli/validators/command_validator.py`

**Design**:
```python
@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    suggestions: list[str]
    examples: list[str]

class CommandValidator:
    """Validates CLI command arguments before execution."""
    
    def validate_build_command(self, args) -> ValidationResult:
        """Validate simple-mode build command arguments."""
        errors = []
        suggestions = []
        examples = []
        
        # Validate --prompt is provided and not empty
        prompt = getattr(args, 'prompt', None)
        if not prompt:
            errors.append("--prompt argument is required")
            suggestions.append("Provide --prompt with feature description")
            examples.append('tapps-agents simple-mode build --prompt "Add user authentication"')
        elif not prompt.strip():
            errors.append("--prompt cannot be empty")
            suggestions.append("Provide a non-empty feature description")
            examples.append('tapps-agents simple-mode build --prompt "Add login endpoint"')
        
        # Validate --file path if provided
        file_path = getattr(args, 'file', None)
        if file_path:
            path = Path(file_path)
            if not path.exists() and not path.parent.exists():
                errors.append(f"File path does not exist: {file_path}")
                suggestions.append("Provide valid file path or omit --file to create new file")
                examples.append('tapps-agents simple-mode build --prompt "..." --file src/api/auth.py')
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            suggestions=suggestions,
            examples=examples
        )
```

---

### 2. ErrorFormatter Class

**Location**: `tapps_agents/cli/utils/error_formatter.py`

**Design**:
```python
class ErrorFormatter:
    """Formats errors with structured, actionable messages."""
    
    def format_error(
        self,
        error: Exception,
        error_type: str,
        context: dict[str, Any] | None = None
    ) -> str:
        """Format error with structure: Error | Context | Suggestion | Example."""
        error_msg = str(error)
        context_info = self._format_context(context or {})
        suggestion = self._generate_suggestion(error_type, error_msg, context)
        example = self._generate_example(error_type, context)
        
        return f"""Error: {error_type} - {error_msg}

Context: {context_info}

Suggestion: {suggestion}

Example: {example}"""
    
    def format_validation_error(self, result: ValidationResult) -> str:
        """Format validation errors."""
        error_msg = "\n".join(f"  - {e}" for e in result.errors)
        suggestion_msg = "\n".join(f"  - {s}" for s in result.suggestions)
        example_msg = "\n".join(f"  {e}" for e in result.examples)
        
        return f"""Validation Error

Errors:
{error_msg}

Suggestions:
{suggestion_msg}

Examples:
{example_msg}"""
```

---

### 3. HelpGenerator Class

**Location**: `tapps_agents/cli/utils/help_generator.py`

**Design**:
```python
class HelpGenerator:
    """Generates comprehensive help text for commands."""
    
    def generate_build_help(self) -> str:
        """Generate help text for simple-mode build command."""
        return """Build new features using the Simple Mode build workflow.

WORKFLOW STEPS:
  1. Enhance prompt (requirements analysis)
  2. Create user stories
  3. Design architecture
  4. Design API/data models
  5. Implement code
  6. Review code quality
  7. Generate tests

EXAMPLES:
  # Basic usage
  tapps-agents simple-mode build --prompt "Add user authentication"

  # With target file
  tapps-agents simple-mode build --prompt "Add login endpoint" --file src/api/auth.py

  # Fast mode (skip documentation steps 1-4)
  tapps-agents simple-mode build --prompt "Quick feature" --fast

  # Automated mode (no prompts)
  tapps-agents simple-mode build --prompt "Feature" --auto

OPTIONS:
  --prompt, -p    Feature description (required)
  --file          Target file path (optional)
  --fast          Skip documentation steps 1-4 for faster execution
  --auto          Enable fully automated execution mode"""
```

---

### 4. Command Parser Fixes

**Location**: `tapps_agents/cli/parsers/top_level.py`

**Design Changes**:
1. Fix help text formatting TypeError (likely in help text template)
2. Integrate CommandValidator into parser
3. Use ErrorFormatter for validation errors
4. Use HelpGenerator for help text

**Integration Pattern**:
```python
# In parser setup
simple_mode_build_parser.add_argument(
    "--prompt", "-p",
    required=True,
    help="Natural language description of the feature to build",
)

# In command handler (simple_mode.py)
def handle_simple_mode_build(args: object) -> None:
    # Validate arguments
    validator = CommandValidator()
    validation_result = validator.validate_build_command(args)
    
    if not validation_result.valid:
        formatter = ErrorFormatter()
        error_msg = formatter.format_validation_error(validation_result)
        feedback.error(
            "Validation failed",
            error_code="validation_error",
            context={"errors": validation_result.errors},
            exit_code=2,
        )
        print(error_msg)
        return
    
    # Continue with workflow execution...
```

---

## Error Message Templates

### Validation Error Template
```
Error: Validation Error

Errors:
  - [error 1]
  - [error 2]

Suggestions:
  - [suggestion 1]
  - [suggestion 2]

Examples:
  [example 1]
  [example 2]
```

### Execution Error Template
```
Error: [Error Type] - [Error Message]

Context:
  - Command: [command]
  - Step: [step if applicable]
  - Configuration: [config details if relevant]

Suggestion: [How to fix]

Example: [Command example]
```

---

## Integration Points

### With Command Parser
- Validator called before command handler
- Errors formatted and displayed
- Help text generated dynamically

### With Feedback System
- Errors integrated with existing feedback system
- Consistent error formatting
- Error codes for programmatic handling

### With Configuration
- Validate configuration state
- Check required config values
- Provide config-related error messages

---

## Testing Strategy

### Unit Tests
- CommandValidator: Test all validation scenarios
- ErrorFormatter: Test error formatting for all error types
- HelpGenerator: Test help text generation

### Integration Tests
- End-to-end command execution
- Error handling flow
- Help text display

---

## Success Criteria

- ✅ Command executes without TypeError
- ✅ Validation errors are clear and actionable
- ✅ Help text is comprehensive
- ✅ Error messages follow structured format
- ✅ All existing functionality still works
