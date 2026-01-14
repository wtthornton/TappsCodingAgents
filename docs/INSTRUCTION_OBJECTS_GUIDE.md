# Instruction Objects Guide

**Date:** 2026-01-16  
**Status:** Complete

## Overview

Instruction objects are structured data models that agents prepare for execution via Cursor Skills. They provide a standardized way to pass execution instructions between agents and to Cursor Skills.

## Instruction Types

### CodeGenerationInstruction

Used for code generation tasks.

**Fields:**
- `specification`: Description of code to generate
- `file_path`: Optional target file path
- `context`: Optional context information
- `language`: Programming language (e.g., "python", "typescript")
- `expert_guidance`: Optional expert consultation results
- `context7_docs`: Optional Context7 documentation

**Example:**
```python
from tapps_agents.core.instructions import CodeGenerationInstruction

instruction = CodeGenerationInstruction(
    specification="Create a user authentication service",
    file_path=Path("src/auth.py"),
    context="FastAPI application",
    language="python",
    expert_guidance={"security": "Use bcrypt for password hashing"},
)

# Convert to Cursor Skill command
skill_cmd = instruction.to_skill_command()
# Result: '@implementer implement --file "src/auth.py" "Create a user authentication service"'

# Convert to CLI command
cli_cmd = instruction.to_cli_command()
# Result: 'tapps-agents implementer implement --file "src/auth.py" "Create a user authentication service"'

# Create execution directive
directive = instruction.to_execution_directive()
# Returns dict with _cursor_execution_directive and instruction data
```

### TestGenerationInstruction

Used for test generation tasks.

**Fields:**
- `target_file`: File to generate tests for
- `test_framework`: Test framework (e.g., "pytest", "jest")
- `coverage_requirements`: Optional coverage requirements

**Example:**
```python
from tapps_agents.core.instructions import TestGenerationInstruction

instruction = TestGenerationInstruction(
    target_file="src/auth.py",
    test_framework="pytest",
    coverage_requirements={"minimum": 80},
)

skill_cmd = instruction.to_skill_command()
# Result: '@tester test --file "src/auth.py" --framework "pytest"'
```

### DocumentationInstruction

Used for documentation generation tasks.

**Fields:**
- `target_file`: File to document
- `output_dir`: Optional output directory
- `docstring_format`: Format (e.g., "google", "numpy")
- `include_examples`: Whether to include examples

**Example:**
```python
from tapps_agents.core.instructions import DocumentationInstruction

instruction = DocumentationInstruction(
    target_file="src/auth.py",
    output_dir="docs/api",
    docstring_format="google",
    include_examples=True,
)
```

### ErrorAnalysisInstruction

Used for error analysis and debugging.

**Fields:**
- `error_message`: Error message text
- `stack_trace`: Optional stack trace
- `context_lines`: Number of context lines to include

**Example:**
```python
from tapps_agents.core.instructions import ErrorAnalysisInstruction

instruction = ErrorAnalysisInstruction(
    error_message="KeyError: 'user_id'",
    stack_trace="Traceback (most recent call last)...",
    context_lines=10,
)
```

### GenericInstruction

Used for generic agent commands.

**Fields:**
- `agent_name`: Name of the agent
- `command`: Command to execute
- `prompt`: Prompt/description
- `parameters`: Dictionary of parameters

**Example:**
```python
from tapps_agents.core.instructions import GenericInstruction

instruction = GenericInstruction(
    agent_name="planner",
    command="plan",
    prompt="Create a plan for user authentication feature",
    parameters={"epic": "auth", "priority": "high"},
)
```

## Using Instruction Objects

### In Agent Code

Agents can create and return instruction objects:

```python
async def run(self, command: str, **kwargs) -> dict[str, Any]:
    if command == "plan":
        # Create instruction
        instruction = GenericInstruction(
            agent_name="planner",
            command="plan",
            prompt=kwargs.get("description"),
            parameters={},
        )
        
        # Wrap in result with execution directive
        return self.wrap_instruction_result(instruction, auto_execute=False)
```

### Auto-Execution Mode

Enable auto-execution to automatically execute instructions:

```python
# In agent code
result = self.wrap_instruction_result(instruction, auto_execute=True)

# The result will include:
# {
#     "_cursor_execution_directive": {
#         "action": "execute_instruction",
#         "auto_execute": True,
#         "skill_command": "@planner plan ...",
#         ...
#     },
#     ...
# }
```

### Execution Directives

Execution directives provide metadata about how to execute instructions:

```python
directive = instruction.to_execution_directive()

# Returns:
# {
#     "_cursor_execution_directive": {
#         "action": "execute_instruction",
#         "type": "code_generation",
#         "description": "Generate python code: ...",
#         "skill_command": "@implementer implement ...",
#         "cli_command": "tapps-agents implementer implement ...",
#         "ready_to_execute": True,
#         "requires_review": False,
#     },
#     "instruction": {...}
# }
```

## Output Formatting

### Formatting Results

Use the `format_result` method to format agent results:

```python
# In agent code
result = await self.some_operation()

# Format as JSON
json_output = self.format_result(result, command="plan", output_format="json")

# Format as Markdown
markdown_output = self.format_result(result, command="plan", output_format="markdown")

# Save to file
output_path = self.format_result(
    result,
    command="plan",
    output_format="markdown",
    output_file="docs/plan.md",
)
```

### Supported Formats

- **json**: Structured JSON output
- **text**: Human-readable text format
- **markdown**: Markdown format with headers and formatting
- **yaml**: YAML format

## Best Practices

1. **Always include execution directives** when returning instruction objects
2. **Use auto-execute sparingly** - only for safe, well-tested operations
3. **Provide clear descriptions** in instruction objects
4. **Include both skill and CLI commands** for flexibility
5. **Format outputs consistently** using the unified output formatter

## Migration Guide

### Before (Old Way)

```python
# Agent returns raw instruction dict
return {
    "instruction": {
        "agent": "implementer",
        "command": "implement",
        "specification": "...",
    }
}
```

### After (New Way)

```python
# Agent creates instruction object
from tapps_agents.core.instructions import CodeGenerationInstruction

instruction = CodeGenerationInstruction(
    specification="...",
    file_path=Path("src/file.py"),
    language="python",
)

# Wrap with execution directive
return self.wrap_instruction_result(instruction)
```

## Examples

See the following files for complete examples:
- `tapps_agents/agents/ops/agent.py` - Uses GenericInstruction
- `tapps_agents/agents/implementer/agent.py` - Uses CodeGenerationInstruction
- `tapps_agents/agents/planner/agent.py` - Returns instruction objects

## Related Documentation

- [Output Formats Guide](OUTPUT_FORMATS_GUIDE.md) - Complete output formatting reference
- [Command Reference](../.cursor/rules/command-reference.mdc) - All available commands
- [Agent Capabilities](../.cursor/rules/agent-capabilities.mdc) - Agent capabilities
