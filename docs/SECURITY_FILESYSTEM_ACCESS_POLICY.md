# Filesystem Access Policy

This document defines the filesystem access policy for TappsCodingAgents agents. All agents must adhere to these rules to ensure security and prevent unauthorized file access.

## Policy Overview

Agents are restricted to specific allowed root directories. All file operations (read, write, create, delete) must be validated to ensure they occur within these allowed boundaries.

## Allowed Roots

### 1. Project Root Directory

**Definition**: The project root is the directory containing the `.tapps-agents/` configuration directory, or the current working directory if no `.tapps-agents/` directory exists.

**Allowed Operations**:
- **Read**: Agents may read any file within the project root and its subdirectories
- **Write**: Agents may write to files within the project root and its subdirectories
- **Create**: Agents may create new files and directories within the project root
- **Delete**: Agents may delete files and directories within the project root (with appropriate safeguards)

**Use Cases**:
- Reading source code files for analysis
- Writing generated code, documentation, or reports
- Creating temporary files for processing
- Modifying project files as part of implementation tasks

### 2. `.tapps-agents/` Directory

**Definition**: The `.tapps-agents/` directory is a special directory used for:
- Configuration files (`config.yaml`, `domains.md`, `experts.yaml`)
- Workflow state and worktrees
- Agent artifacts and reports
- Knowledge base caches
- Session data

**Allowed Operations**:
- **Read**: Agents may read any file within `.tapps-agents/` and its subdirectories
- **Write**: Agents may write to files within `.tapps-agents/` and its subdirectories
- **Create**: Agents may create new files and directories within `.tapps-agents/`
- **Delete**: Agents may delete files and directories within `.tapps-agents/` (with appropriate safeguards)

**Use Cases**:
- Reading and writing configuration files
- Managing workflow state
- Storing agent-generated artifacts
- Caching knowledge base data
- Storing session information

**Security Note**: The `.tapps-agents/` directory may contain sensitive data (API keys, session data). Access is restricted to the framework and should not be exposed to external processes.

## Temporary and Test Paths

### Temporary Files

Temporary files created during agent operations should be:
- Created within the project root or `.tapps-agents/` directory
- Cleaned up after use when possible
- Subject to the same path validation rules

### Test Files

Test files created by pytest or other testing frameworks are allowed when:
- Created in pytest temporary directories (detected by `pytest` and `tmp_path` in the resolved path)
- Used for unit or integration testing
- Automatically cleaned up by the test framework

**Note**: Test-specific exceptions are handled by the path validation system to allow legitimate test operations.

## Path Validation Rules

### 1. Path Resolution

All paths must be resolved to their absolute, canonical form before validation:
- Use `Path.resolve()` to normalize paths
- Handle symlinks appropriately (resolved paths follow symlinks)
- Normalize path separators (Windows vs Unix)

### 2. Root Boundary Check

A path is considered valid if:
- The resolved path is within the project root, OR
- The resolved path is within `.tapps-agents/`, OR
- The path is a legitimate test temporary path (pytest)

### 3. Traversal Prevention

The following patterns are blocked:
- Path traversal sequences: `..`, `../`, `..\\`
- URL-encoded traversal: `%2e%2e`, `%2f`, `%5c`
- Absolute paths that escape allowed roots
- Symlinks that resolve outside allowed roots

### 4. File Size Limits

In addition to path validation, file operations are subject to size limits:
- Default maximum file size: 10 MB (configurable per agent)
- Large files may be rejected to prevent resource exhaustion

## Implementation

### Centralized Path Validator

Path validation is implemented in `tapps_agents/core/path_validator.py` and used by all agents through the `BaseAgent._validate_path()` method.

### Validation Flow

1. **Input**: Agent receives a file path (string or Path object)
2. **Resolution**: Path is resolved to absolute, canonical form
3. **Root Check**: Resolved path is checked against allowed roots
4. **Traversal Check**: Path is checked for traversal patterns
5. **Size Check**: File size is validated (for existing files)
6. **Result**: Validation passes or raises `ValueError` with descriptive error message

### Error Messages

When path validation fails, agents receive clear error messages:
- `"Path traversal detected: {path}"` - Traversal attempt blocked
- `"Path outside allowed roots: {path}"` - Path escapes allowed boundaries
- `"File too large: {size} bytes (max {max_size} bytes)"` - Size limit exceeded
- `"File not found: {path}"` - File does not exist (for read operations)

## Developer Guidelines

### For Agent Developers

1. **Always use `_validate_path()`**: Use the base class method for all file operations
2. **Resolve paths early**: Convert relative paths to absolute paths before validation
3. **Handle errors gracefully**: Provide clear error messages when validation fails
4. **Document exceptions**: If an agent needs special path handling, document it clearly

### For Framework Users

1. **Understand boundaries**: Know that agents can only access project files and `.tapps-agents/`
2. **Configure appropriately**: Use `.tapps-agents/config.yaml` for agent configuration
3. **Review agent operations**: Review agent-generated files before committing
4. **Report issues**: Report any path validation issues or unexpected behavior

## Security Considerations

### Least Privilege

Agents operate with minimal filesystem access:
- Cannot access files outside the project
- Cannot access system directories
- Cannot access other user's files
- Cannot access parent directories of the project root

### Defense in Depth

Multiple layers of protection:
1. **Path validation** at the framework level
2. **Root-based checks** using resolved paths
3. **Pattern detection** for traversal attempts
4. **Size limits** to prevent resource exhaustion

### Audit and Monitoring

Path validation failures are logged and can be monitored:
- Validation errors are raised as exceptions
- Failed operations are logged with context
- CI/CD systems can detect and alert on validation failures

## Exceptions and Escape Hatches

### Explicit Bypasses

If an agent requires access outside the normal boundaries:
1. **Document the requirement**: Explain why the bypass is needed
2. **Use explicit configuration**: Require explicit user configuration to enable
3. **Warn users**: Clearly warn users about security implications
4. **Review carefully**: Security review required for any bypass mechanism

### Configuration-Based Overrides

Future enhancements may include:
- Configurable allowed paths in `config.yaml`
- Per-agent path restrictions
- Read-only vs read-write permissions
- Temporary path allowlists

**Note**: These features are not currently implemented. All agents use the standard policy.

## Related Documentation

- [Security Policy](../SECURITY.md) - Overall security policy
- [Configuration Guide](CONFIGURATION.md) - Configuration file structure
- [Developer Guide](DEVELOPER_GUIDE.md) - Agent development guidelines

## Policy Version

**Version**: 1.0  
**Last Updated**: December 2025  
**Status**: Active

