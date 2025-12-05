# Improver Agent Skills

The Improver Agent is responsible for **code refactoring**, **performance optimization**, and **quality improvements**.

## Commands

All commands are prefixed with `*` when called via the CLI.

### `*refactor [file_path] [instruction]`
- **Description**: Refactors existing code to improve structure, readability, and maintainability while preserving functionality.
- **Usage**: `tapps improver *refactor src/calculator.py "Extract common logic into helper functions"`
- **Arguments**:
    - `file_path` (string, required): Path to the file to refactor.
    - `instruction` (string, optional): Specific refactoring instructions or goals.
- **Output**: Success message confirming refactoring completion.

### `*optimize [file_path] [type]`
- **Description**: Optimizes code for performance, memory usage, or both.
- **Usage**: `tapps improver *optimize src/data_processor.py performance`
- **Arguments**:
    - `file_path` (string, required): Path to the file to optimize.
    - `type` (string, optional): Type of optimization (`performance`, `memory`, or `both`). Defaults to `performance`.
- **Output**: Success message with optimization type and completion status.

### `*improve-quality [file_path]`
- **Description**: Improves overall code quality by applying best practices, design patterns, and style improvements.
- **Usage**: `tapps improver *improve-quality src/api.py`
- **Arguments**:
    - `file_path` (string, required): Path to the file to improve.
- **Output**: Success message confirming quality improvements.

### `*help`
- **Description**: Displays this help message.
- **Usage**: `tapps improver *help`
- **Output**: A dictionary of commands and their descriptions.

## Permissions

The Improver Agent has `Read`, `Write`, `Edit`, `Grep`, and `Glob` permissions. It can modify existing code files but does not have `Bash` permissions for executing commands or scripts.

## Workflow Integration

The Improver Agent typically works in coordination with:
- **Reviewer Agent**: Receives code review feedback and applies improvements
- **Implementer Agent**: Enhances generated code before final review
- **Orchestrator Agent**: Participates in quality improvement workflows

## Use Cases

1. **Code Refactoring**: Improve code structure without changing functionality
2. **Performance Tuning**: Optimize slow or resource-intensive code
3. **Quality Enhancement**: Apply best practices and design patterns
4. **Technical Debt Reduction**: Modernize legacy code patterns
5. **Code Standardization**: Ensure consistency across codebase

